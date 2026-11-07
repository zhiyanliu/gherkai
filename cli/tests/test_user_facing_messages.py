"""护栏：产品面文案不带内部指代，也不带 markdown 强调记号（CLAUDE.md「代码纪律」同名条的机器执行体）。

**约定**：凡能到用户终端/日志的文字——`--help`/description/epilog、`print`/stderr 提示、warning、
展示给用户的异常消息、worker 与 Lambda 的日志行——**不写** ADR 编号、决策号、内部机制名（决策与理由：ADR 0039）
（不变量 / 定位链 / 被拒方案 / 重议闸门 / 实测项 / 接缝契约 / 模块头 / 组合根装配 / 执行令牌 / 终结核对…）、内部函数名。
使用者手里没有仓库：这些指代对他是噪声甚至误导。文案只说**发生了什么、为什么（产品语言一句）、怎么办**。

**指针不是删掉，是搬家**：contributor 要的设计判据留在紧邻的注释或 docstring 里（那才是给读 code 的人/AI 看的），
所以本护栏**只扫非 docstring 的字符串字面量**，注释与 docstring 里的 ADR 指针一律放行、且鼓励保留。

覆盖面：五个生产包的 `.py`（AST 扫字面量）+ Midscene worker 的 `.mts` 源（去注释后扫行），外加 `features/steps/` 的
确定性 step 模板（两种语言都扫：用户文档让使用方把它复制进自己的项目，里面的字面量随之成为使用方看到的文字）。
测试自身的字面量不在扫描面内（测试不面向使用者）。开发者契约型异常（只在内部 code 误用内部 API 时抛，
永不因用户输入触发）可留一句点名内部符号的短诊断——但不带 ADR/决策字样，故同样能过本护栏。

**第二条规则管格式**：同一扫描面上，字面量不写 markdown 强调记号（成对的 `**…**`）。终端与日志不渲染 markdown，
人读输出也不解析标记语法，使用者看到的是原样的星号；需要强调时改用措辞（如以「注意：」开头、单独成句）。
反引号包住的命令、选项与路径不受这条限制。它是单独的一条正则 `EMPHASIS` 配单独的测试函数，不并入 `FORBIDDEN`
（管格式不管用词，失败提示与改法都不同），也不进 `cli/tests/_doc_rules.py`（那里的扫描面是 markdown、注释与 docstring，
`**` 在三者里都是正当的强调）。判定单位是单个字符串字面量：Python 侧取自 AST，f-string 按整串判定（插值处代入一个普通
文字字符，是启发式，误判走例外登记）；`.mts` 侧对整份源码做一遍词法扫描，分清字符串字面量、注释与正则字面量后逐个
字面量判定（禁词表那条在 `.mts` 侧仍按去注释后的行判定）。决策与理由：ADR 0039 面一与护栏节。
"""
from __future__ import annotations

import ast
import functools
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

# 生产包（含 CLI 前端、runtime 组合根、部署 provider + 其 Lambda、core、Nova worker）与 steps/ 模板
PY_ROOTS = (
    "cli/gherkai_cli",
    "runtime/gherkai_runtime",
    "deploy_aws/gherkai_deploy_aws",
    "core/gherkai_core",
    "engines/novaact/gherkai_worker_novaact",
    "features/steps",
)
MTS_ROOTS = ("engines/midscene/src", "features/steps")

# 内部指代的形态：ADR 编号 / 决策·决定编号 / 内部机制名 / 内部函数名
FORBIDDEN = re.compile(
    r"ADR\s*\d{4}"
    r"|决策\s*[0-9A-Za-z]"
    r"|决定\s*[一二三四五六七八九十0-9]"
    r"|推进器|宿主"  # 内部机制名（ADR 0034 的 advancer/host 词条）：产品面只说「后端/云端/进程」
    r"|无状态批量运行|事件驱动链"  # contributor 词表术语与机制描述（ADR 0034）：产品面只说「后台运行 / 云端后台运行」
    r"|不变量|定位链|实测项|被拒方案|重议闸门|接缝契约|模块头|组合根装配|窄腰"
    # 设备会话与命令执行的内部机制名（ADR 0051 决策 3、5，ADR 0052 决策 2、6）：产品面只说发生了什么，如「在等待时间之后才
    # 返回」「这一步可能已执行也可能未执行」。待核尝试一族禁两种写法：名词「待核尝试」与动作短语「记为待核」（含「不再记为待核」
    # 「登记为待核」），后者曾写进 worker 日志、复核时才发现；日志改说发生了什么，如「已按结果未知上报」「请按这个会话名核对」。
    # 裸词「待核」仍不禁，「记为待核」后面紧跟「对」的也放行：两者都会误拦「待核对的会话」「记为待核对」这类正常产品句
    r"|生命周期通道|执行令牌|命令守卫|终结四阶段|终结核对|结果未知标志|待核尝试|记为待核(?!对)"
    r"|preflight|per-run|\btick\b|清理\s*pass|武装|防御扫"  # 机制名 / 施工行话：产品面只说「提交前检查 / 本机后台进程 / 推进 / 清理」
    r"|best-effort|抢传|flush\s*兜底|不带\s*ref"  # 上传/收尾的失败语义行话：产品面只说「未能上传 + 不影响什么」
    r"|逃生舱|烙进|烙在|烙成|烙好|旋钮|(?<!访)问(?:不|得)到"  # 比喻 / 口头语（ADR 0045 决策六）：产品面只说「跳过 / 构建进镜像 / 选项 / 取不到」
    # 量词「档」：作取值 / 级别 / 类别 / 情形 / 后端义一律不用（照句意写「取值 / 级别 / 判定 / 情形 / 后端」；
    # 退役的后端简称 `cloud 档` / `本机档` 也由本条兜住），只放行「文档 / 归档 / 存档 / 档案 / 档期」这类固定词。
    r"|(?<![文归存])档(?![案期])"
    r"|跑法|确定性锚点|技能包"  # 已退役的旧名（规范名见 CONTEXT.md 词表）：改说「执行方式 / 执行后端 / 确定性 step / agent skill」
    r"|_require_vpc"
    r"|替换\s*WorkerSg"  # CDK construct 名进了叙事（stack.py 里作 construct id 的字面量是合法的，只抓成句形态）：产品面只说「worker 的网络 / 安全组」
)
# .mts 侧去注释后按行扫（TS 无 docstring 概念，注释即注释）——禁词与 Python 侧**同一张表**（复用上面的 FORBIDDEN，
# 别让 TS 侧更松），外加两个裸子串收得更严：TS 侧没有「ADR 0034」「决策 3」之外的合法用法，出现即错。
FORBIDDEN_TS_BARE = ("ADR", "决策")

# markdown 强调记号（ADR 0039 面一与护栏节）：两组 `**` 之间夹一段不含星号、不跨行、首尾都不是空白或 `/` 的文字。
# 只对单个字符串字面量的内容匹配，字面量之外的代码不进判定面，`.mts` 里的幂运算符因此不论留不留空格都不命中。
# 三类排除各有来由：脱敏掩码（代码里的 `***`、`***@`，以及 `****` 这类纯星号串）只有一串连续的星号，没有夹在两组星号
# 之间的文字；首尾的空白排除与 markdown 自身的规则一致，字面量里写出的 `2 ** n` 因此不命中；glob 与 XCUITest 类链查询的
# `**/` 路径段紧挨 `/`。已知盲区：用 `+` 拼接出成对星号的写法（每个字面量单独判定，两段各只有一组星号）与成对星号
# 分在两行的多行字符串（形态不跨行）不命中。
EMPHASIS = re.compile(r"\*\*(?![\s*/])[^*\n]*?(?<![\s*/])\*\*")
# f-string 与 `.mts` 模板字符串整串判定时插值处代入的文字，须是一个普通文字字符：代入空串会让 `f"**{name}**"` 变成
# 纯星号串、被当作掩码放过。这一代入是启发式，插值的运行时值无法静态确定：`f"**{chr(42)}**"` 运行时只有五颗星，代入后
# 成为 `**x**`、被误判为强调；`f"{a}***{b}***"` 与 `"ab***cd***"` 一样，形态与 `***强调***` 无从区分，同样命中。
# 这几类情形走下面的例外登记，不为它们放宽正则。
INTERPOLATION_PLACEHOLDER = "x"
# 强调记号的例外登记，键是（仓库相对路径, 常量名），值注明理由。只收两种情形：只写进 markdown 文件、不到终端与日志的
# 字面量（注明写入去处）；运行时的值不含强调、只是被上面的插值代入误判的字面量（注明运行时的实际形态）。常量名在 Python
# 侧取赋值语句的目标变量名（`NAME = …` 或 `NAME: T = …`），在 `.mts` 侧取字面量起始行上、位于它之前的最后一个
# `const` / `let` / `var` 声明的名字；字面量不在赋值语句里时先提成具名常量再登记。登记项找不到对应的字面量时测试失败，
# 过期的登记须删除。目前没有需要登记的字面量。
EMPHASIS_ALLOWED: dict[tuple[str, str], str] = {}


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


@functools.cache
def _python_files() -> tuple[tuple[str, ast.Module], ...]:
    """PY_ROOTS 下全部 `.py` 的（仓库相对路径, 语法树）；两条规则共用，每个文件只解析一次。"""
    files: list[tuple[str, ast.Module]] = []
    for root in PY_ROOTS:
        base = REPO_ROOT / root
        assert base.is_dir(), f"扫描面失效：{root} 不存在（包搬家了？请更新 PY_ROOTS，别让护栏静默空扫）"
        for path in sorted(base.rglob("*.py")):
            files.append((path.relative_to(REPO_ROOT).as_posix(), ast.parse(path.read_text(encoding="utf-8"))))
    return tuple(files)


def _scan_python() -> list[str]:
    hits: list[str] = []
    for rel, tree in _python_files():
        docs = _docstring_node_ids(tree)
        for node in ast.walk(tree):
            if (isinstance(node, ast.Constant) and isinstance(node.value, str)
                    and id(node) not in docs and FORBIDDEN.search(node.value)):
                hits.append(f"{rel}:{node.lineno}: {node.value.strip()[:100]!r}")
    return hits


def _strip_ts_comments(src: str) -> list[tuple[int, str]]:
    """去掉 `/* */`（保行号：注释体换成等量换行）与行尾 `//` 之后的内容 → [(行号, 剩余代码)]，供禁词表按行判定。

    切 `//` 是朴素的（不识别字符串字面量），故 `"…// ADR …"` 这种把指代写在字面量里的 `//` 之后会漏，这一盲区是刻意
    接受的。强调记号那条用 _ts_literals 的词法扫描逐个字面量判定；禁词表这条连字面量之外的代码一并判定、维持按行，
    改用词法扫描去注释能补上这处盲区，但可能扫出新的真实命中，须先核对再切换。
    """
    src = re.sub(r"/\*.*?\*/", lambda m: "\n" * m.group(0).count("\n"), src, flags=re.S)
    return [(i, line.split("//", 1)[0]) for i, line in enumerate(src.splitlines(), 1)]


def _mts_files() -> list[tuple[str, str]]:
    """MTS_ROOTS 下非测试 `.mts` 的（仓库相对路径, 源码文本）。"""
    files: list[tuple[str, str]] = []
    for root in MTS_ROOTS:
        base = REPO_ROOT / root
        assert base.is_dir(), f"扫描面失效：{root} 不存在（包搬家了？请更新 MTS_ROOTS）"
        for path in sorted(base.rglob("*.mts")):
            if not path.name.endswith(".test.mts"):
                files.append((path.relative_to(REPO_ROOT).as_posix(), path.read_text(encoding="utf-8")))
    return files


def _scan_mts() -> list[str]:
    hits: list[str] = []
    for rel, src in _mts_files():
        for lineno, code in _strip_ts_comments(src):
            if FORBIDDEN.search(code) or any(bad in code for bad in FORBIDDEN_TS_BARE):
                hits.append(f"{rel}:{lineno}: {code.strip()[:100]!r}")
    return hits


def _assigned_names(tree: ast.AST) -> dict[int, str]:
    """节点 id 到所在赋值语句目标变量名的映射（只认单个裸名目标），供强调记号的例外登记按常量名查。"""
    names: dict[int, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            target, value = node.targets[0].id, node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.value is not None:
            target, value = node.target.id, node.value
        else:
            continue
        for sub in ast.walk(value):
            names[id(sub)] = target
    return names


def _python_emphasis_hits(tree: ast.Module) -> list[tuple[int, str | None, str]]:
    """一棵语法树里带强调记号的非 docstring 字面量：（行号, 所在赋值的常量名或 None, 判定文本）。

    f-string 按整串判定，常量段原样拼接、插值处代入 INTERPOLATION_PLACEHOLDER，其常量段不再单独判定：
    `f"**{name}**"` 的两组星号分在插值两侧，逐段判定会漏掉。这一代入是启发式，已知误判见 INTERPOLATION_PLACEHOLDER 旁注。
    """
    docs = _docstring_node_ids(tree)
    names = _assigned_names(tree)
    fstring_parts = {id(v) for n in ast.walk(tree) if isinstance(n, ast.JoinedStr) for v in n.values}
    hits: list[tuple[int, str | None, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.JoinedStr):
            text = "".join(v.value if isinstance(v, ast.Constant) else INTERPOLATION_PLACEHOLDER for v in node.values)
        elif (isinstance(node, ast.Constant) and isinstance(node.value, str)
                and id(node) not in docs and id(node) not in fstring_parts):
            text = node.value
        else:
            continue
        if EMPHASIS.search(text):
            hits.append((node.lineno, names.get(id(node)), text))
    return hits


_TS_DECLARED_NAME = re.compile(r"\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)")
# `.mts` 词法扫描里其后接表达式的关键字：前一个记号是它们时，`/` 是正则字面量的开头而不是除号。若按普通标识符处理，
# `return /"/.test(s)` 里的正则会被当成除号，其中的引号随之开启一个并不存在的字面量。
_TS_EXPR_KEYWORDS = frozenset({
    "await", "case", "delete", "do", "else", "in", "instanceof", "new", "of", "return", "throw", "typeof", "void",
    "yield",
})
_TS_IDENT = re.compile(r"(?:[^\W\d]|\$)[\w$]*")
_TS_NUMBER = re.compile(r"\d[\w.]*")
_TS_REGEX_FLAGS = re.compile(r"[A-Za-z]*")


def _ts_literals(src: str) -> list[tuple[int, str]]:
    """一遍词法扫描取出 `.mts` 源码里的全部字符串字面量，按出现位置排序：[(起始偏移, 判定文本)]。

    字符串字面量、注释与正则字面量在同一遍里识别：字面量与正则字面量里的 `//`、`/*`、`*/` 是内容，注释里的引号也不
    开启字面量；首行的 `#!` 按注释处理。单引号与双引号字面量取两个引号之间的源码原文；模板字符串按整个字面量取，
    `${…}` 处代入 INTERPOLATION_PLACEHOLDER，其中的表达式按代码继续识别，嵌套在里面的字面量单独列出。正则字面量与
    除号按前一个记号区分：前一个记号是标识符（_TS_EXPR_KEYWORDS 除外）、数字、字面量、`)` 或 `]` 时视作除号，其余情形
    视作正则字面量的开头。这是词法上的启发式，不解析 TypeScript 语法。
    """
    found: list[tuple[int, str]] = []
    start = 0
    if src.startswith("#!"):
        start = src.find("\n") if "\n" in src else len(src)
    _ts_scan_code(src, start, found, nested=False)
    return sorted(found)


def _ts_scan_code(src: str, i: int, found: list[tuple[int, str]], *, nested: bool) -> int:
    """从偏移 i 起按代码识别记号、把字面量记入 found，返回结束处之后的偏移。

    nested 为真时是模板字符串里的 `${…}`，在与它配对的 `}` 处结束。
    """
    n = len(src)
    operand = False  # 前一个记号能否作除号的左操作数
    depth = 0
    while i < n:
        c = src[i]
        if c.isspace():
            i += 1
        elif src.startswith("//", i):
            end = src.find("\n", i)
            i = n if end < 0 else end
        elif src.startswith("/*", i):
            end = src.find("*/", i + 2)
            i = n if end < 0 else end + 2
        elif c in "'\"":
            i, operand = _ts_scan_quoted(src, i, found), True
        elif c == "`":
            i, operand = _ts_scan_template(src, i, found), True
        elif c == "/" and not operand and (end := _ts_regex_end(src, i)) is not None:
            i, operand = end, True
        elif m := (_TS_IDENT.match(src, i) or _TS_NUMBER.match(src, i)):
            i, operand = m.end(), m.group() not in _TS_EXPR_KEYWORDS
        else:
            if nested and c == "{":
                depth += 1
            elif nested and c == "}":
                if depth == 0:
                    return i + 1
                depth -= 1
            i, operand = i + 1, c in ")]"
    return n


def _ts_scan_quoted(src: str, i: int, found: list[tuple[int, str]]) -> int:
    """偏移 i 处的单引号或双引号字面量：记入两个引号之间的原文，返回闭合引号之后的偏移（未闭合时止于行尾）。"""
    quote, j = src[i], i + 1
    while j < len(src) and src[j] not in (quote, "\n"):
        j += 2 if src[j] == "\\" else 1
    found.append((i, src[i + 1:j]))
    return j + 1 if src[j:j + 1] == quote else j


def _ts_scan_template(src: str, i: int, found: list[tuple[int, str]]) -> int:
    """偏移 i 处的模板字符串：整串记入，`${…}` 处代入 INTERPOLATION_PLACEHOLDER，返回闭合反引号之后的偏移。"""
    parts: list[str] = []
    start = j = i + 1
    while j < len(src) and src[j] != "`":
        if src[j] == "\\":
            j += 2
        elif src.startswith("${", j):
            parts += [src[start:j], INTERPOLATION_PLACEHOLDER]
            start = j = _ts_scan_code(src, j + 2, found, nested=True)
        else:
            j += 1
    parts.append(src[start:j])
    found.append((i, "".join(parts)))
    return j + 1


def _ts_regex_end(src: str, i: int) -> int | None:
    """偏移 i 处的正则字面量（含 flags）之后的偏移；到行尾仍未闭合时返回 None，这个 `/` 改按除号处理。"""
    j, in_class = i + 1, False
    while j < len(src) and src[j] != "\n":
        c = src[j]
        if c == "\\":
            j += 1
        elif c == "[":
            in_class = True
        elif c == "]":
            in_class = False
        elif c == "/" and not in_class:
            return _TS_REGEX_FLAGS.match(src, j + 1).end()
        j += 1
    return None


def _mts_emphasis_hits(src: str) -> list[tuple[int, str | None, str]]:
    """一份 `.mts` 源码里带强调记号的字符串字面量：（起始行号, 起始行上位于它之前的最后一个声明的名字或 None, 判定文本）。

    逐个字面量判定（字面量取自 _ts_literals），字面量之外的代码不进判定面：按整行判定会把相邻两个字面量之间的代码
    当成强调正文，`const masks = ["***", "***"];` 里两个掩码之间的 `", "` 恰好满足形态。
    """
    hits: list[tuple[int, str | None, str]] = []
    for offset, text in _ts_literals(src):
        if EMPHASIS.search(text):
            declared = _TS_DECLARED_NAME.findall(src, src.rfind("\n", 0, offset) + 1, offset)
            hits.append((src.count("\n", 0, offset) + 1, declared[-1] if declared else None, text))
    return hits


def test_no_internal_pointers_in_user_facing_text():
    """五个生产包与 steps/ 模板的非 docstring 字面量 + Midscene 源与 steps/ 模板的非注释行：一处内部指代都不许有。"""
    hits = _scan_python() + _scan_mts()
    assert not hits, (
        "产品面文案带了内部指代（使用者手里没有仓库）。改成「发生了什么 / 一句产品语言的为什么 / 怎么办」，"
        "设计判据搬进紧邻的注释或 docstring：\n  " + "\n  ".join(hits)
    )


def test_no_markdown_emphasis_in_user_facing_text():
    """同一扫描面上不许有成对的 `**…**`：终端与日志不渲染 markdown，使用者看到的是原样的星号。"""
    found: list[tuple[str, str | None, int, str]] = []
    for rel, tree in _python_files():
        found += [(rel, name, lineno, text) for lineno, name, text in _python_emphasis_hits(tree)]
    for rel, src in _mts_files():
        found += [(rel, name, lineno, text) for lineno, name, text in _mts_emphasis_hits(src)]
    hits = [f"{rel}:{lineno}: {text.strip()[:100]!r}" for rel, name, lineno, text in found
            if name is None or (rel, name) not in EMPHASIS_ALLOWED]
    assert not hits, (
        "用户可见字符串里有 markdown 强调记号（成对的 `**…**`），终端与日志不渲染 markdown、使用者看到的是原样的星号。"
        "删掉星号，需要强调时改用措辞（如以「注意：」开头、单独成句）。只写进 markdown 文件、不到终端与日志的字面量，"
        "或运行时的值不含强调、只是被插值代入误判的字面量，按文件与常量名登记进 EMPHASIS_ALLOWED 并注明理由：\n  "
        + "\n  ".join(hits)
    )
    stale = sorted(set(EMPHASIS_ALLOWED) - {(rel, name) for rel, name, _, _ in found})
    assert not stale, f"EMPHASIS_ALLOWED 里这些登记已找不到带强调记号的字面量，请删除：{stale}"


@pytest.mark.parametrize("text, hit", [
    ("**注意**", True),
    ("请先 **build** 镜像", True),
    ("***", False),                # 脱敏掩码：只有一串连续的星号
    ("***@", False),
    ("****", False),
    ("2 ** n ** 3", False),        # 字面量里写出的幂运算表达式，两侧留空格
    ("**/A/**/B", False),          # XCUITest 类链查询与 glob 里的 `**/` 路径段
    ("src/**/a/**", False),
    ("**/*.feature", False),
    # 只有一端紧挨空白或 `/` 的写法，分别核对首尾两侧的排除：上面的成对写法两端对称，少了任一侧的排除也照样不命中
    ("x ** y**2", False),
    ("x**2 + y ** 2", False),
    ("**/build**", False),
    ("a**b/**", False),
    ("ab***cd***", True),          # 已知误判：两串星号之间夹着文字，形态与 `***强调***` 无从区分，走例外登记
])
def test_emphasis_shape(text: str, hit: bool):
    """强调记号的形态：成对的 `**` 夹着文字才命中，掩码、幂运算符与 `**/` 路径段不命中。"""
    assert bool(EMPHASIS.search(text)) is hit, text


@pytest.mark.parametrize("source, hit", [
    ('f"**{x}**"', True),                        # 两组星号分在插值两侧，按整串判定才拦得到
    ('msg = f"请先 **{step}** 再提交"', True),
    ('msg = "**注意**"', True),
    ('f"{x}***{y}"', False),                     # 插值之间的掩码
    ('"""**docstring 里的强调放行**"""', False),
    # 插值代入造成的已知误判，走例外登记：运行时只有五颗星，代入后成为 `**x**`；两串星号之间夹着插值
    ('f"**{chr(42)}**"', True),
    ('f"{a}***{b}***"', True),
])
def test_emphasis_in_python_literals(source: str, hit: bool):
    """Python 侧的判定面：f-string 按整串判定（插值代入是启发式，已知误判也逐条固定），docstring 放行。"""
    assert bool(_python_emphasis_hits(ast.parse(source))) is hit, source


def test_emphasis_in_fstring_reported_once():
    """f-string 只按整串报一次，常量段里自带的成对星号不再单独报。"""
    assert len(_python_emphasis_hits(ast.parse('f"**注意** {x}"'))) == 1


@pytest.mark.parametrize("source, literals", [
    ('log("https://x", "**注意**");', ["https://x", "**注意**"]),     # 字面量里的 `//` 是内容，不是注释
    ("export const Q = `**/${A}/**/${B}`;", ["**/x/**/x"]),          # 类链查询里的 `/**/` 原样保留
    ('const g = "a/*b*/c"; // "d"', ["a/*b*/c"]),                    # 字面量里的 `/* */` 原样保留，注释里的引号不开启字面量
    ("/* it's */ log('ok');", ["ok"]),
    ("""const s = "a\\"b", t = 'it\\'s';""", ['a\\"b', "it\\'s"]),   # 转义的引号不闭合字面量
    ("log(`a ${f(`b ${c}`)} d`);", ["a x d", "b x"]),                # 嵌套的模板字符串单独列出
    ("log(`${ {k: '}'}.k }`);", ["x", "}"]),                          # `${…}` 在与它配对的 `}` 处结束
    ("const R = /'/g, s = 'y';", ["y"]),                            # 正则字面量里的撇号不开启字面量
    ('const R = /[/"]/g, s = "y";', ["y"]),                          # 字符类里的 `/` 不闭合正则字面量
    ('return /"/.test(s) ? "y" : "n";', ["y", "n"]),
    ("#!/usr/bin/env -S node --title='a b'\nlog('ok');", ["ok"]),   # 首行的 `#!` 按注释处理
])
def test_ts_literal_extraction(source: str, literals: list[str]):
    """`.mts` 词法扫描取出的字面量：注释与正则字面量不算字面量，字面量里形如注释的内容原样保留。"""
    assert [text for _, text in _ts_literals(source)] == literals


@pytest.mark.parametrize("source, hit", [
    ('log("请先 **build** 镜像");', True),
    ("log(`请先 **${step}** 再提交`);", True),                       # 两组星号分在插值两侧，按整个模板字符串判定
    ('log(`共 ${n} 项${n > 1 ? "，**注意**" : ""}`);', True),        # 嵌套在 `${…}` 里的字面量单独判定
    ("const y = 2 ** n ** 3;", False),
    ("const z = a**b**c;", False),                                   # 幂运算符在字面量之外，不留空格也不命中
    ('const masks = ["***", "***"];', False),                        # 两个掩码同在一行：两个字面量之间的代码不进判定面
    ("export const Q = `**/${A}/**/${B}`;", False),
    ("// **注释里的强调放行**", False),
    ("/** **JSDoc 里的强调放行** */", False),
    ('log("https://x", "**注意**");', True),                         # 字面量里的 `//` 不开启行注释
    ('const g = "src/*.ts"; log("**注意**"); // */', True),          # 字面量里的 `/*` 不开启块注释
    ("// it's\nlog(\"**注意**\");", True),                          # 注释里的撇号不开启字面量
    ("const R = /'/g; log(\"**注意**\");", True),                    # 正则字面量里只有一个撇号或一个双引号
    ('const R = /"/g; log("**注意**");', True),
    ('const R = /[/"]/g; log("**注意**");', True),
    ('if (s) return /"/.test(s) ? "**注意**" : "";', True),          # 紧跟在 `return` 之后的正则字面量
    ('x = typeof /"/ === "object" ? "**注意**" : "";', True),
    ('const r = n / 2, s = "/"; log("**注意**");', True),            # 标识符、`)`、`]` 之后的 `/` 是除号
    ('const r = (a + b) / 2, s = "/"; log("**注意**");', True),
    ('const r = a[i] / 2, s = "/"; log("**注意**");', True),
    ("const m = `${a}***${b}***`;", True),                           # 已知误判：插值之间夹着三颗星，走例外登记
])
def test_emphasis_in_mts_literals(source: str, hit: bool):
    """`.mts` 侧的判定面：一遍词法扫描后逐个字符串字面量判定，注释、正则字面量与字面量之外的代码都不进判定面。"""
    assert bool(_mts_emphasis_hits(source)) is hit, source


def test_emphasis_hits_carry_constant_name_for_registration():
    """例外登记按常量名查：Python 侧取赋值目标，`.mts` 侧取字面量起始行上、位于它之前的声明的名字。"""
    assert [name for _, name, _ in _python_emphasis_hits(ast.parse('MSG: str = f"**{x}**"'))] == ["MSG"]
    assert [(line, name) for line, name, _ in _mts_emphasis_hits('const A = 1;\nexport const MSG = "**注意**";')] == [
        (2, "MSG")]
    assert [name for _, name, _ in _mts_emphasis_hits('log("**注意**"); const B = 1;')] == [None]


@pytest.mark.parametrize("text, hit", [
    ("这次尝试记为待核", True),
    ("Create 晚到的结果不再记为待核，只记一行日志", True),   # 曾进了 worker 日志的那种写法
    ("结果未知的请求登记为待核", True),
    ("还有 1 个待核尝试", True),
    ("待核对的会话", False),                                   # 正常产品句
    ("这台设备记为待核对", False),
    ("待核", False),                                           # 裸词刻意不禁
])
def test_forbidden_shape_for_pending_attempt_wording(text: str, hit: bool):
    """待核尝试一族的禁用形态：「待核尝试」与「记为待核」命中，「待核对」与裸词「待核」不命中。"""
    assert bool(FORBIDDEN.search(text)) is hit, text
