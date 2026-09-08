"""护栏：产品面文案不带内部指代（CLAUDE.md「代码纪律」同名条的机器执行体）。

**约定**：凡能到用户终端/日志的文字——`--help`/description/epilog、`print`/stderr 提示、warning、
展示给用户的异常消息、worker 与 Lambda 的日志行——**不写** ADR 编号、决策号、内部机制名
（不变量 / 定位链 / 被拒方案 / 重议闸门 / 实测项 / 接缝契约 / 模块头 / 组合根装配…）、内部函数名。
使用者手里没有仓库：这些指代对他是噪声甚至误导。文案只说**发生了什么、为什么（产品语言一句）、怎么办**。

**指针不是删掉，是搬家**：维护者要的设计判据留在紧邻的注释或 docstring 里（那才是给读 code 的人/AI 看的），
所以本护栏**只扫非 docstring 的字符串字面量**，注释与 docstring 里的 ADR 指针一律放行、且鼓励保留。

覆盖面：五个生产包的 `.py`（AST 扫字面量）+ Midscene worker 的 `.mts` 源（去注释后扫行）。
测试自身的字面量不在扫描面内（测试不面向使用者）。开发者契约型异常（只在内部 code 误用内部 API 时抛，
永不因用户输入触发）可留一句点名内部符号的短诊断——但不带 ADR/决策字样，故同样能过本护栏。
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# 生产包（含 CLI 皮、runtime 组合根、部署 provider + 其 Lambda、core、Nova worker）
PY_ROOTS = (
    "cli/gherkai_cli",
    "runtime/gherkai_runtime",
    "deploy_aws/gherkai_deploy_aws",
    "core/gherkai_core",
    "engines/novaact/gherkai_worker_novaact",
)
MTS_ROOT = "engines/midscene/src"

# 内部指代的形态：ADR 编号 / 决策·决定编号 / 内部机制名 / 内部函数名
FORBIDDEN = re.compile(
    r"ADR\s*\d{4}"
    r"|决策\s*[0-9A-Za-z]"
    r"|决定\s*[一二三四五六七八九十0-9]"
    r"|不变量|定位链|实测项|被拒方案|重议闸门|接缝契约|模块头|组合根装配"
    r"|_require_vpc"
)
# .mts 侧去注释后按行扫（TS 无 docstring 概念，注释即注释）——禁词与 Python 侧同一张表，别让 TS 侧更松
FORBIDDEN_TS = ("ADR", "决策", "不变量", "定位链", "实测项", "被拒方案", "重议闸门", "接缝契约", "模块头", "组合根装配")


def _docstring_node_ids(tree: ast.AST) -> set[int]:
    """module / class / def 的 docstring 常量节点 id——放行面（指针的合法归宿）。"""
    ids: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            body = node.body
            if (body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant)
                    and isinstance(body[0].value.value, str)):
                ids.add(id(body[0].value))
    return ids


def _scan_python() -> list[str]:
    hits: list[str] = []
    for root in PY_ROOTS:
        base = REPO_ROOT / root
        assert base.is_dir(), f"扫描面失效：{root} 不存在（包搬家了？请更新 PY_ROOTS，别让护栏静默空扫）"
        for path in sorted(base.rglob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            docs = _docstring_node_ids(tree)
            for node in ast.walk(tree):
                if (isinstance(node, ast.Constant) and isinstance(node.value, str)
                        and id(node) not in docs and FORBIDDEN.search(node.value)):
                    rel = path.relative_to(REPO_ROOT)
                    hits.append(f"{rel}:{node.lineno}: {node.value.strip()[:100]!r}")
    return hits


def _strip_ts_comments(src: str) -> list[tuple[int, str]]:
    """去掉 `/* */`（保行号：注释体换成等量换行）与行尾 `//` 之后的内容 → [(行号, 剩余代码)]。

    切 `//` 是朴素的（不解析字符串字面量），故 `"…// ADR …"` 这种把指代写在字面量里的 `//` 之后会漏——
    刻意接受：本护栏与文案纪律的执行工具同一套判据，宁可朴素也不引入 TS 解析依赖。
    """
    src = re.sub(r"/\*.*?\*/", lambda m: "\n" * m.group(0).count("\n"), src, flags=re.S)
    return [(i, line.split("//", 1)[0]) for i, line in enumerate(src.splitlines(), 1)]


def _scan_midscene() -> list[str]:
    hits: list[str] = []
    base = REPO_ROOT / MTS_ROOT
    assert base.is_dir(), f"扫描面失效：{MTS_ROOT} 不存在（包搬家了？请更新 MTS_ROOT）"
    for path in sorted(base.rglob("*.mts")):
        if path.name.endswith(".test.mts"):
            continue
        for lineno, code in _strip_ts_comments(path.read_text(encoding="utf-8")):
            if any(bad in code for bad in FORBIDDEN_TS):
                hits.append(f"{path.relative_to(REPO_ROOT)}:{lineno}: {code.strip()[:100]!r}")
    return hits


def test_no_internal_pointers_in_user_facing_text():
    """五个生产包的非 docstring 字面量 + Midscene 源的非注释行：一处内部指代都不许有。"""
    hits = _scan_python() + _scan_midscene()
    assert not hits, (
        "产品面文案带了内部指代（使用者手里没有仓库）。改成「发生了什么 / 一句产品语言的为什么 / 怎么办」，"
        "设计判据搬进紧邻的注释或 docstring：\n  " + "\n  ".join(hits)
    )
