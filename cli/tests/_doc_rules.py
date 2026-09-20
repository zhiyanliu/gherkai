"""人读文本的规则、扫描面与抽取器：护栏三层共用的**单一事实源**（ADR 0046）。

内容三类：①规则——内部指代表 FORBIDDEN、口吻表 COLLOQUIAL（含 ADR 0045 决策六形态②的自造复合词 COINAGES）、词表退役名
RETIRED_TERMS（注释层用去掉「批」义三词的 RETIRED_TERMS_IN_CODE）、决策六形态①③的启发式 SYMBOL_PREDICATE /
NUMERIC_SHORTHAND / ARROW、悬空指针形态 DANGLING_JOURNEY / BARE_WP、相对链接 RELATIVE_LINK、已知机器根 MACHINE_ROOTS；
②扫描面——user_docs / technical_docs / ai_side_docs / code_comment_files / diagram_sources / skill_markdown_files /
long_term_docs，与 classify(path)；③抽取器——prose_lines（markdown 正文，剥代码块与行内代码）、comment_units（注释与
docstring）、skill 的命令 token 抽取。scan(kind, path, only_lines) 按面套规则束。

消费方三处，同源才不会各自漂：`cli/tests/test_*.py` 各面的护栏（CI 兜底）、`tools/doc_rules_check.py`（Claude Code 的
写完即查 hook 与提交闸门，人类 contributor 的可选 git pre-commit）、`tools/render_skill_contract.py`（契约副本转换器的自查）；
`deploy_aws/tests/test_skill_deploy_tokens.py` 与 `skills/gherkai-evals/materialize.py` 另复用命令 token 抽取与机器根。
判据与理由各归其 ADR：产品文案 0039、分层与口吻 0045 决策一 / 三 / 六、词表 0045 决策八、skill 0043 决策六。

放 `cli/tests/` 而非 `tools/`：它只服务护栏、不是运行期或开发期工具；仓库外的消费方显式把这个目录加进 `sys.path` 来复用——
宁可让它们多两行 import，也不要两份会漂的禁词表 / 抽取器 / 根集。往这里加规则的顺序见 CONTRIBUTING.md「护栏三层」段。
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import NamedTuple

REPO = Path(__file__).resolve().parents[2]
SKILL_ROOT = REPO / "cli" / "gherkai_cli" / "skills" / "gherkai"

# ── 文案规则 ────────────────────────────────────────────────────────────────

# 内部指代：ADR 编号 / 决策号 / 内部机制名。读者是「装了包、没有仓库的人」，这些词对他们是噪声。
FORBIDDEN = re.compile(
    r"\bADR\b"                       # ADR 编号 / 「见 ADR」
    r"|决策\s*[0-9A-Za-z]"            # 决策 N
    r"|不变量|定位链|被拒方案|重议闸门|实测项|接缝契约|模块头|组合根"
)

# 口头语 / 隐喻（ADR 0045 决策六）：给人读的文档与产品文案不用；「跑」作动词禁用，只放行提及词「跑」（后接 `」`）。
# 末项管量词「档」：作取值 / 级别 / 类别 / 情形 / 后端义一律不用（照句意写「取值 / 级别 / 判定 / 情形 / 后端」），
# 只放行「文档 / 归档 / 存档 / 档案 / 档期」这类固定词。它是用词规则而非口吻规则，故 CHANGELOG 已发行节
# 随退役词表一起豁免（见 `changelog_unreleased`）。
# ADR 0045 决策六形态②：自造二字复合词与「码」缩略——歧义不是效率，AI 侧文档也不用（排版学义的「同形字符」与「协同调度」放行）。
_COINAGES = r"同形(?!字)|同款|同律|(?<!协)同调|同口径|归码|退码|网络码|专用码|非零码|此码"
COINAGES = re.compile(_COINAGES)
COLLOQUIAL = re.compile(r"帽子不是人|烧钱|锁步|lockstep|烙进|烙好|烙成|烙在|逃生舱|旋钮|跑(?!」)"
                        r"|(?<![文归存])档(?![案期])"
                        r"|" + _COINAGES)

# 已退役的旧名：CONTEXT.md 词表给了规范名、旧名列进该条 `_Avoid_` 的那批，使用者面一个都不许再出现。
# 与 COLLOQUIAL 分表是因为判据不同——那张管「口吻」（口头语 / 隐喻，永久禁），这张管「用词版本」（旧名 →
# 规范名，随词表增删）。逐词与词表同源由 `test_user_docs.test_retired_terms_are_all_in_the_glossary` 守：
# 往这里加词必须先在 CONTEXT.md 对应词条的 `_Avoid_` 里落下，免得护栏与词表各自演化。
# 退役后端简称的「… 档」形态（`cloud 档` / `本机档` …）不在此重列：已由 `COLLOQUIAL` 的量词「档」通则兜住。
# 一次 run 的「批」义旧名收在末三项。同词条 `_Avoid_` 里的「批次」与裸「一批」不进表：前者在事件流语境下
# 指 DynamoDB Stream 一次投递的事件批、后者有「一组用例 / 一组文件」的正当用法，正则分不出两义。
RETIRED_TERMS_WORDS = (
    "跑法", "抢传", "确定性锚点", "大脑", "穿刺", "骨架验证用例", "版本单旋钮", "无状态跑批", "在跑 run",
    "逃生舱", "供给包", "提交方", "技能包", "建造者 AI", "AI coding agent", "维护者",
    "本批", "这一批", "整批",
)
RETIRED_TERMS = re.compile("|".join(re.escape(w) for w in RETIRED_TERMS_WORDS))
# 注释与 docstring 用的退役表去掉「批」义三词：Lambda 与 Stream 侧的注释里「本批 / 整批」指 DynamoDB Stream 一次投递的
# 事件批（「本批重试耗尽后整批丢弃」），是机制义、不是 Run 的旧名，正则分不出两义；注释里指一次 run 的「整批」交
# code-health 复盘的术语维度人判（ADR 0045 决策八：AI 侧与注释只换作为术语名的短语）。
_BATCH_WORDS = {"本批", "这一批", "整批"}
RETIRED_TERMS_IN_CODE = re.compile("|".join(re.escape(w) for w in RETIRED_TERMS_WORDS if w not in _BATCH_WORDS))

_CHANGELOG_RELEASED = re.compile(r"^## \[\d", re.M)  # 第一个已发行版本节的标题（`## [Unreleased]` 不匹配）


def changelog_unreleased(text: str) -> str:
    """CHANGELOG 交给退役词表与口头语表扫的部分 = 截到第一个已发行版本节之前。

    已发行节是**发行当时的原话**：改词表不回溯改写它，否则变更记录与使用者当年读到的说明不符。
    截断保留前面的原始行，故调用方 `enumerate` 出的行号与原文一致。**内部指代那张表仍扫全篇**
    （那是发行时就不该写的东西，不因过了一个版本而免责）；口头语表进这条豁免是因为它现在也管用词
    （量词「档」，见 `COLLOQUIAL`）——用词规则是事后新立的，回溯扫已发行节只会拦出按规矩改不了的历史。
    """
    m = _CHANGELOG_RELEASED.search(text)
    return text[:m.start()] if m else text


# `](../x)` / `](./x)` / `](foo.md)` / `](references/foo.md)`：PyPI/npm 页面与 skill 安装态都渲染不出仓库的目录树。
RELATIVE_LINK = re.compile(r"\]\((?:\.\.?/|(?![a-z][a-z0-9+.-]*:|#)[^)\s]+\.md)")

# ── ADR 0045 决策六形态①③：符号当谓语与省略中心词的数字缩写 ─────────────────────
# 决策六把三种漏进人读层的 AI 侧缩写立为口吻规则：②的固定词已进上面的 COLLOQUIAL；①③是形态、不是固定词，只能靶向
# 启发式：中文字紧邻 `=`（含全角）即视为把等号当「是 / 即」用；「退 <数字>」即省了中心词「退出码」。扫描前先剥掉代码块
# 与行内代码（`prose_lines`）——代码里的赋值、命令示例、JSON 片段本来就该是符号。≠ / ⊆ 在中文正文里没有合法用法，
# 直接禁。箭头只在用户文档与 skill 正文里禁（技术文档与注释允许它表顺序与因果），故单独一条。
SYMBOL_PREDICATE = re.compile(r"[一-鿿]\s*[=＝]\s|\s[=＝]\s*[一-鿿]|(?<!绿)≠(?!对)|[⊆∈∧∨⇒«»]")  # 「绿≠对」是 CLAUDE.md 立的判据名，放行；≥ / ≤ 是数值比较、不算
NUMERIC_SHORTHAND = re.compile(r"退\s?[0-9]+(?![0-9.\-])")   # 「退出码 2」不命中：退 后面是 出
ARROW = re.compile(r"→")

_FENCE = re.compile(r"^\s*(```|~~~)")


def prose_lines(text: str, *, skip_frontmatter: bool = False) -> list[tuple[int, str]]:
    """markdown 的正文行：剥掉围栏代码块、行内反引号代码，可选剥掉 YAML frontmatter；行号与原文一致。

    表格行保留（表格里的字也是人读的）；HTML 注释不另处理（本仓库文档不用它）。
    """
    lines = text.splitlines()
    start = 0
    if skip_frontmatter and lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                start = i + 1
                break
    out: list[tuple[int, str]] = []
    in_fence = False
    for i, line in enumerate(lines[start:], start + 1):
        if _FENCE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        out.append((i, CODE_SPAN.sub(" ", line)))
    return out


# 注释与 docstring 的抽取（`test_code_comments.py` 用）：Python 走 tokenize + ast（注释与三种 docstring），
# TS / JS 走遮蔽字符串后的 // 与 /* */，shell / YAML / Dockerfile 走行内 #。返回 (行号, 文本) 列表。
_JS_STRING = re.compile(r"'(?:\\.|[^'\\\n])*'|\"(?:\\.|[^\"\\\n])*\"|`(?:\\.|[^`\\])*`", re.S)
_HASH_COMMENT = re.compile(r"(?<![\"'])#(.*)$")


def comment_units(path: Path) -> list[tuple[int, str]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    suffix = path.suffix
    out: list[tuple[int, str]] = []
    if suffix == ".py":
        import ast
        import io
        import tokenize
        try:
            for tok in tokenize.generate_tokens(io.StringIO(text).readline):
                if tok.type == tokenize.COMMENT:
                    out.append((tok.start[0], tok.string))
            tree = ast.parse(text)
        except (SyntaxError, tokenize.TokenError):
            return out
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                doc = ast.get_docstring(node, clean=False)
                if doc:
                    first = node.body[0].lineno if node.body else 1
                    for k, line in enumerate(doc.splitlines()):
                        out.append((first + k, line))
        return out
    if suffix in {".mts", ".ts", ".mjs", ".js"}:
        masked = _JS_STRING.sub(lambda m: " " * len(m.group(0)), text)
        in_block = False
        for i, line in enumerate(masked.splitlines(), 1):
            rest = line
            while rest:
                if in_block:
                    end = rest.find("*/")
                    if end < 0:
                        out.append((i, rest))
                        break
                    out.append((i, rest[:end]))
                    rest = rest[end + 2:]
                    in_block = False
                    continue
                s1, s2 = rest.find("//"), rest.find("/*")
                if s1 < 0 and s2 < 0:
                    break
                if s2 < 0 or (0 <= s1 < s2):
                    out.append((i, rest[s1 + 2:]))
                    break
                in_block = True
                rest = rest[s2 + 2:]
        return out
    for i, line in enumerate(text.splitlines(), 1):  # .sh / .yml / Dockerfile
        m = _HASH_COMMENT.search(line)
        if m and not line.lstrip().startswith("#!"):
            out.append((i, m.group(1)))
    return out


# ── 机器绝对路径的判据 ──────────────────────────────────────────────────────

# 已知机器根（本机 / Linux / 容器上常见的一级目录）：`(?:file://)?/<根>/` 即判定为产出机器的绝对路径。
# 为什么只认这组根、不认「以 `/` 打头的字符串」：step 原文（`Then 页面地址匹配 "/wiki/OpenAI"`）会以转义字串
# 嵌进运行元信息与判定明细，URL 路径与机器路径在形态上分不开，只有根目录名能分。录制机出现新的根就补这里。
MACHINE_ROOTS = ("Users", "home", "private", "var", "tmp", "opt", "Volumes", "root", "mnt", "srv", "app",
                 "workspace", "work", "data", "etc", "usr", "nix", "run")
MACHINE_ROOT = re.compile(rf"(?:file://)?/(?:{'|'.join(MACHINE_ROOTS)})/")

# ── 悬空指针（CLAUDE.md 文档纪律「悬空指针红线」）──────────────────────────────
# 长期文档与 code 注释只指稳定物：指向某份 journey 文件的链接、裸 WP 编号在被吸收后都会悬空。只认「指向具体文件」
# 的形态（`docs/journey/NNNN-…`），提到目录本身（「过程产物放 docs/journey/」）是合法的分层描述。
DANGLING_JOURNEY = re.compile(r"docs/journey/\d{4}-")
BARE_WP = re.compile(r"\bWP-?\d+[A-Za-z]?(?:-\d+)?\b")

# ── 扫描面与规则束（测试与 tools/doc_rules_check.py 的单一事实源）────────────────
# 每个人读面一束规则；hook 与提交闸门按 classify() 把改动文件映射到同一束，写完即查、提交前再查（ADR 0046）。
PY_ROOTS_FOR_COMMENTS = (
    "core", "runtime", "cli", "deploy_aws", "engines/novaact", "engines/midscene/src", "engines/midscene/spikes",
    "tools", "skills/gherkai-evals", ".github", ".claude/hooks",
)
CODE_SUFFIXES = frozenset({".py", ".mts", ".ts", ".mjs", ".sh", ".yml"})
_SKIP_DIRS = frozenset({".venv", "node_modules", "dist", "__pycache__", ".pytest_cache", "graphify-out"})
# 定义禁词表 / 把这些词当数据讨论的文件，不扫自己。
SELF_FILES = frozenset({
    "cli/tests/_doc_rules.py", "cli/tests/test_user_facing_messages.py", "cli/tests/test_user_docs.py",
    "cli/tests/test_skill.py", "cli/tests/test_package_readmes.py", "cli/tests/test_code_comments.py",
    "cli/tests/test_technical_docs.py", "cli/tests/test_adr_hygiene.py", "cli/tests/test_context_glossary.py",
    "tools/render_skill_contract.py", "tools/doc_rules_check.py",
})


def _rel(p: Path) -> str:
    return str(p.relative_to(REPO)) if p.is_absolute() else str(p)


def user_docs() -> list[Path]:
    return sorted((REPO / "docs" / "user-guide").glob("*.md")) + [REPO / "README.md", REPO / "CHANGELOG.md"]


def technical_docs() -> list[Path]:
    docs = [REPO / "CONTRIBUTING.md", REPO / ".github" / "workflows" / "README.md", REPO / "docs" / "README.md",
            REPO / "core" / "tests" / "README.md", REPO / "skills" / "README.md",
            REPO / "engines" / "midscene" / "spikes" / "SIGV4-FETCH-RECIPE.md"]
    docs += sorted((REPO / "docs" / "internals").glob("*.md"))
    docs += sorted(REPO.glob("*/DEVELOPMENT.md")) + sorted(REPO.glob("engines/*/DEVELOPMENT.md"))
    docs += sorted((REPO / "tools").glob("*.md"))
    return sorted({p for p in docs if p.exists()})


def diagram_sources() -> list[Path]:
    return sorted((REPO / "docs" / "diagrams").glob("*.json"))


def long_term_docs() -> list[Path]:
    """寿命长、只许指稳定物的文档（悬空指针红线的适用面）。"""
    docs = [REPO / "CONTEXT.md", REPO / "CLAUDE.md", REPO / "README.md", REPO / "CONTRIBUTING.md"]
    docs += sorted((REPO / "docs" / "adr").glob("*.md")) + sorted((REPO / "docs" / "internals").glob("*.md"))
    docs += sorted((REPO / "docs" / "user-guide").glob("*.md")) + sorted((REPO / "docs" / "ai-eng").glob("*.md"))
    docs += sorted(REPO.glob("*/DEVELOPMENT.md")) + sorted(REPO.glob("engines/*/DEVELOPMENT.md"))
    return sorted({p for p in docs if p.exists()})


def ai_side_docs() -> list[Path]:
    """contributor 侧 AI agent 文档：口吻放开，但形态②的自造词与悬空指针照样不许（ADR 0045 决策六 / 悬空指针红线）。"""
    docs = [REPO / "CONTEXT.md", REPO / "CLAUDE.md"]
    docs += sorted((REPO / "docs" / "adr").glob("*.md")) + sorted((REPO / "docs" / "ai-eng").glob("*.md"))
    docs += sorted((REPO / ".claude" / "commands").glob("*.md"))
    return sorted({p for p in docs if p.exists()})


# 讨论这些词本身的文档：形态②的自造词在它们里是反例列举，不算使用。
COINAGE_DISCUSSION = frozenset({
    "docs/adr/0045-documentation-layering-and-placement.md", "docs/ai-eng/doc-health-review.md",
    "docs/ai-eng/code-health-review.md",
})


def code_comment_files() -> list[Path]:
    out: list[Path] = []
    for root in PY_ROOTS_FOR_COMMENTS:
        base = REPO / root
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if not p.is_file() or _SKIP_DIRS & set(p.parts):
                continue
            if (p.suffix in CODE_SUFFIXES or p.name == "Dockerfile") and _rel(p) not in SELF_FILES:
                out.append(p)
    for p in REPO.glob("engines/*/Dockerfile"):
        if p not in out:
            out.append(p)
    return sorted(set(out))


def classify(path: Path) -> str | None:
    """把一个文件归到某个人读面（None = 不在任何护栏扫描面内）。"""
    p = path if path.is_absolute() else REPO / path
    rel = _rel(p)
    if rel in SELF_FILES:
        return None
    if p.suffix == ".md" and SKILL_ROOT in p.parents:
        return "skill"
    if p in diagram_sources():
        return "diagram"
    if p in user_docs():
        return "user-doc"
    if p in technical_docs():
        return "technical-doc"
    if p in ai_side_docs():
        return "ai-doc"
    if (p.suffix in CODE_SUFFIXES or p.name == "Dockerfile") and not (_SKIP_DIRS & set(p.parts)):
        if any(_rel(p).startswith(root + "/") for root in PY_ROOTS_FOR_COMMENTS):
            return "code"
    return None


def scan(kind: str, path: Path, only_lines: set[int] | None = None) -> list[tuple[int, str, str]]:
    """按人读面的规则束扫一个文件，返回 (行号, 类别, 原文)。only_lines 给了就只报这些行（hook 的「只报本次改动的行」）。"""
    p = path if path.is_absolute() else REPO / path
    text = p.read_text(encoding="utf-8", errors="replace")
    hits: list[tuple[int, str, str]] = []

    def add(line_no: int, label: str, line: str) -> None:
        if only_lines is None or line_no in only_lines:
            hits.append((line_no, label, line.strip()[:110]))

    def apply(units, rules):
        for line_no, line in units:
            for label, rx in rules:
                if rx.search(line):
                    add(line_no, label, line)

    wording = (("口头语或自造复合词", COLLOQUIAL), ("符号当谓语", SYMBOL_PREDICATE),
               ("省略中心词的「退 N」", NUMERIC_SHORTHAND))
    pointers = (("指向 journey 文件的悬空指针", DANGLING_JOURNEY), ("裸 WP 编号", BARE_WP))
    if kind == "code":
        apply(comment_units(p), wording + (("退役旧名", RETIRED_TERMS_IN_CODE),) + pointers)
    elif kind == "technical-doc":
        apply(prose_lines(text), wording + (("退役旧名", RETIRED_TERMS),) + pointers)
    elif kind in {"user-doc", "skill"}:
        scanned = changelog_unreleased(text) if p.name == "CHANGELOG.md" else text
        body_start = 0
        if kind == "skill":
            lines = text.splitlines()
            if lines and lines[0].strip() == "---" and "---" in lines[1:]:
                body_start = lines.index("---", 1) + 1
        all_lines = [(i, line) for i, line in enumerate(scanned.splitlines(), 1)]
        apply(all_lines, (("内部指代", FORBIDDEN),))
        apply([(i, l) for i, l in all_lines if i > body_start],
              (("口头语或自造复合词", COLLOQUIAL), ("退役旧名", RETIRED_TERMS)))
        apply(prose_lines(scanned, skip_frontmatter=(kind == "skill")),
              (("符号当谓语", SYMBOL_PREDICATE), ("省略中心词的「退 N」", NUMERIC_SHORTHAND), ("正文箭头", ARROW))
              + pointers)
    elif kind == "ai-doc":
        rules = pointers if _rel(p) in COINAGE_DISCUSSION else pointers + (("自造二字复合词", COINAGES),)
        apply(prose_lines(text), rules)
    elif kind == "diagram":
        apply([(i, line) for i, line in enumerate(text.splitlines(), 1)],
              (("内部指代", FORBIDDEN), ("口头语或自造复合词", COLLOQUIAL), ("退役旧名", RETIRED_TERMS),
               ("符号当谓语", SYMBOL_PREDICATE), ("省略中心词的「退 N」", NUMERIC_SHORTHAND)))
    return hits


# ── skill 扫描面与命令 token 抽取 ───────────────────────────────────────────

CODE_SPAN = re.compile(r"`([^`\n]+)`")  # 单行反引号代码跨（跨行的不是命令写法，不收）

# provider 侧才有的 flag：贴在 `gherkai deploy` / `destroy` 上，provider 未加载时主 parser 上不存在。
# `cli/tests` 的裸 flag 弱断言对它们放行（不 import provider——它住 `[deploy-aws]` optional extra、只有部署方装），
# 真实性由 `deploy_aws/tests/test_skill_deploy_tokens.py` 对着 provider 真 parser 断：那边还断言本表每一项都真在
# provider 上，防它退化成万能旁路。
PROVIDER_ONLY_FLAGS = frozenset({
    "--vpc", "--stop-timeout", "--refresh-context", "--container-engine", "--variant", "--set-default", "--yes",
})

# 命令 token 的收尾标点（中文正文里 flag 常紧跟标点）与 flag 形态。
_FLAG = re.compile(r"^--[A-Za-z][A-Za-z0-9-]*")


def skill_markdown_files() -> list[Path]:
    """skill 目录下全部 markdown（含契约副本——转换后它本就不含内部指代，无例外）。"""
    return sorted(SKILL_ROOT.rglob("*.md"))


class CommandSpan(NamedTuple):
    """一个 `gherkai …` 代码跨的拆解结果。

    `words` = `gherkai` 之后、第一个 flag 之前的裸词（子命令与位置参数占位符混在一起，由调用方按自己那份
    parser 解析出子命令路径）；`flags` = 该跨内**全部** `--flag`（已去掉 `=值` 与收尾标点）。
    只认同一个代码跨内的组合：跨越两个跨（`` `gherkai run` 加上 `--tunnel-ttl` ``）不构成「这个 flag 挂这个
    子命令」的断言素材，散落的裸 flag 另做弱断言。
    """

    words: tuple[str, ...]
    flags: tuple[str, ...]
    span: str
    path: Path
    line: int


def extract_command_spans(text: str, path: Path) -> list[CommandSpan]:
    """抽出 `gherkai …` 形态的代码跨。行号按跨在原文里的位置算，报错时能直接点到人。"""
    out: list[CommandSpan] = []
    for line_no, line in enumerate(text.splitlines(), 1):
        for span in CODE_SPAN.findall(line):
            tokens = span.split()
            if not tokens or tokens[0] != "gherkai":
                continue
            words: list[str] = []
            for tok in tokens[1:]:
                if tok.startswith("-"):
                    break
                words.append(tok)
            flags = tuple(f for f in (clean_flag(t) for t in tokens[1:]) if f)
            out.append(CommandSpan(tuple(words), flags, span, path, line_no))
    return out


def bare_flags(text: str) -> list[tuple[str, int, str]]:
    """代码跨里出现的全部 `--flag`（含 `gherkai …` 跨内的），→ (flag, 行号, 跨原文)。弱断言用。"""
    out: list[tuple[str, int, str]] = []
    for line_no, line in enumerate(text.splitlines(), 1):
        for span in CODE_SPAN.findall(line):
            for tok in span.split():
                flag = clean_flag(tok)
                if flag:
                    out.append((flag, line_no, span))
    return out


def clean_flag(token: str) -> str | None:
    """`--scope=<id>，` → `--scope`；不是 flag 则 None。`--` 单独出现（参数分隔符）不算 flag。"""
    m = _FLAG.match(token)
    return m.group(0) if m else None


def is_placeholder(word: str) -> bool:
    """`<命令>` / `…` / `[<scope_id>]` 这类占位符不是子命令名，解析路径时跳过、不当拼错。"""
    return (not word) or word[0] in "<[$" or set(word) <= set(".…")
