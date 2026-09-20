"""repo 内 code 注释与 docstring 的措辞护栏（ADR 0045 决策六：注释与 docstring 是人读层）。

注释随 code 长期存在、读者是 contributor，此前却不在任何护栏的扫描面内——用户可见字符串归 `test_user_facing_messages.py`、
文档归 `test_user_docs.py` / `test_skill.py` / `test_package_readmes.py`，注释层的退役旧名、口头语与 ADR 式缩写只能靠
定期复盘用人眼找（code-health 第 5 轮一次抓出约 50 处退役名、约 600 处缩写）。本文件把三张规则套到注释与 docstring 上：
`COLLOQUIAL`（口头语与决策六形态②的自造复合词）、`RETIRED_TERMS_IN_CODE`（词表退役名，去掉与 Stream 事件批写法相同的「批」义三词）、`SYMBOL_PREDICATE` 与
`NUMERIC_SHORTHAND`（决策六形态①③的启发式）。抽取见 `_doc_rules.comment_units`。

扫描面：全部生产包、测试、spike、tools、评测脚本、发布链脚本与 workflow、hook、Dockerfile；排除定义禁词表的护栏文件
自身（它们把这些词当数据）。箭头不在此禁：注释里表顺序与因果合法。
"""
from __future__ import annotations

from pathlib import Path

import pytest
from _doc_rules import (COLLOQUIAL, NUMERIC_SHORTHAND, REPO, RETIRED_TERMS_IN_CODE, SYMBOL_PREDICATE,
                        comment_units)

_ROOTS = [
    "core", "runtime", "cli", "deploy_aws", "engines/novaact", "engines/midscene/src", "engines/midscene/spikes",
    "tools", "skills/gherkai-evals", ".github", ".claude/hooks",
]
_SUFFIXES = {".py", ".mts", ".ts", ".mjs", ".sh", ".yml"}
_SKIP_DIRS = {".venv", "node_modules", "dist", "__pycache__", ".pytest_cache", "graphify-out"}
# 定义禁词表 / 讨论这些词本身的文件：把它们当数据、不当措辞。
_SELF = {
    "cli/tests/_doc_rules.py", "cli/tests/test_user_facing_messages.py", "cli/tests/test_user_docs.py",
    "cli/tests/test_skill.py", "cli/tests/test_package_readmes.py", "cli/tests/test_code_comments.py",
    "cli/tests/test_technical_docs.py", "tools/render_skill_contract.py",
}


def _files() -> list[Path]:
    out: list[Path] = []
    for root in _ROOTS:
        base = REPO / root
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if not p.is_file() or _SKIP_DIRS & set(p.parts):
                continue
            rel = str(p.relative_to(REPO))
            if (p.suffix in _SUFFIXES or p.name == "Dockerfile") and rel not in _SELF:
                out.append(p)
    for p in REPO.glob("engines/*/Dockerfile"):
        if p not in out:
            out.append(p)
    return sorted(out)


def _rel(p: Path) -> str:
    return str(p.relative_to(REPO))


def test_scan_face_is_not_empty():
    files = _files()
    assert len(files) > 100, f"扫描面只剩 {len(files)} 个文件——目录搬家了？先修 _ROOTS，别让护栏空转"


@pytest.mark.parametrize("path", _files(), ids=_rel)
def test_comments_follow_the_written_register(path: Path):
    """注释与 docstring：无口头语 / 自造复合词、无退役旧名、不把 = 当谓语、不写「退 N」。"""
    hits = []
    for line_no, text in comment_units(path):
        if COLLOQUIAL.search(text):
            hits.append(f"{_rel(path)}:{line_no}: 口头语或自造复合词 · {text.strip()[:110]}")
        if RETIRED_TERMS_IN_CODE.search(text):
            hits.append(f"{_rel(path)}:{line_no}: 退役旧名 · {text.strip()[:110]}")
        if SYMBOL_PREDICATE.search(text):
            hits.append(f"{_rel(path)}:{line_no}: 符号当谓语 · {text.strip()[:110]}")
        if NUMERIC_SHORTHAND.search(text):
            hits.append(f"{_rel(path)}:{line_no}: 省略中心词的「退 N」 · {text.strip()[:110]}")
    assert not hits, ("注释与 docstring 是人读层，按 ADR 0045 决策六写完整词与完整句（规范名见 CONTEXT.md）：\n"
                      + "\n".join(hits))
