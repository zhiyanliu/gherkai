"""人读文本的规则、扫描面与抽取器：护栏三层共用的**单一事实源**（ADR 0046）。

内容三类：①规则——内部指代表 FORBIDDEN、口吻表 COLLOQUIAL（含 ADR 0045 决策六形态②的自造复合词 COINAGES）、词表退役名
RETIRED_TERMS（注释层用去掉「批」义三词的 RETIRED_TERMS_IN_CODE）、决策六形态①③的启发式 SYMBOL_PREDICATE /
NUMERIC_SHORTHAND / ARROW、悬空指针形态 DANGLING_JOURNEY / BARE_WP / MACHINE_COORDINATE（本机坐标：全仓 markdown 与 code 注释都拦）、
相对链接 RELATIVE_LINK、Release 固定块里未锁定 tag 的仓库链接 UNPINNED_BLOB、已知机器根 MACHINE_ROOTS；
②扫描面——user_docs（含演示材料；措辞规则的适用范围由 wording_scope 截取：CHANGELOG 已发行节与定稿口播稿 final_transcript
豁免）/ package_pages（包 README 与 Release 正文的固定块）/ technical_docs / ai_side_docs / code_comment_files /
diagram_sources / skill_markdown_files / long_term_docs / all_markdown（本机坐标规则适用的全仓已跟踪 markdown），与 classify(path)；
③抽取器——prose_lines（markdown 正文，剥代码块与行内代码）、comment_units（注释与 docstring 原文，comment_blocks 按段分组）、
comment_prose_lines（注释与 docstring 的正文，同样剥代码块与行内代码）、skill 的命令 token 抽取。scan(kind, path, only_lines)
按面套规则束。

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
COLLOQUIAL = re.compile(r"帽子不是人|烧钱|锁步|lockstep|烙进|烙好|烙成|烙在|逃生舱|旋钮|(?<!访)问(?:不|得)到|跑(?!」)"
                        r"|(?<![文归存])档(?![案期])"
                        r"|" + _COINAGES)

# 已退役的旧名：CONTEXT.md 词表给了规范名、旧名列进该条 `_Avoid_` 的那批，使用者面一个都不许再出现。
# 与 COLLOQUIAL 分表是因为判据不同——那张管「口吻」（口头语 / 隐喻，永久禁），这张管「用词版本」（旧名 →
# 规范名，随词表增删）。逐词与词表同源由 `test_user_docs.test_retired_terms_are_all_in_the_glossary` 守：
# 往这里加词必须先在 CONTEXT.md 对应词条的 `_Avoid_` 里落下，免得护栏与词表各自演化。
# 退役后端简称的「… 档」形态（`cloud 档` / `本机档` …）不在此重列：已由 `COLLOQUIAL` 的量词「档」通则兜住。
# 一次 run 的「批」义旧名是「本批」「这一批」「整批」三项。同词条 `_Avoid_` 里的「批次」与裸「一批」不进表：
# 前者在事件流语境下指 DynamoDB Stream 一次投递的事件批、后者有「一组用例 / 一组文件」的正当用法，正则分不出两义。
RETIRED_TERMS_WORDS = (
    "跑法", "抢传", "确定性锚点", "大脑", "穿刺", "骨架验证用例", "版本单旋钮", "无状态跑批", "在跑 run",
    "逃生舱", "供给包", "提交方", "技能包", "建造者 AI", "AI coding agent", "维护者",
    "本批", "这一批", "整批",
    "深层链接", "深链", "隧道预热", "设备会话", "真机会话",
)
RETIRED_TERMS = re.compile("|".join(re.escape(w) for w in RETIRED_TERMS_WORDS))
# 注释与 docstring 用的退役表去掉「批」义三词：Lambda 与 Stream 侧的注释里「本批 / 整批」指 DynamoDB Stream 一次投递的
# 事件批（「本批重试耗尽后整批丢弃」），是机制义、不是 Run 的旧名，正则分不出两义；注释里指一次 run 的「整批」交
# code-health 复盘的术语维度人判（ADR 0045 决策八：AI 侧与注释只换作为术语名的短语）。
_BATCH_WORDS = {"本批", "这一批", "整批"}
RETIRED_TERMS_IN_CODE = re.compile("|".join(re.escape(w) for w in RETIRED_TERMS_WORDS if w not in _BATCH_WORDS))

_CHANGELOG_RELEASED = re.compile(r"^## \[\d", re.M)  # 第一个已发行版本节的标题（`## [Unreleased]` 不匹配）


def changelog_unreleased(text: str) -> str:
    """CHANGELOG 交给退役词表与口头语表扫的部分，即第一个已发行版本节之前的内容。

    已发行节是**发行当时的原话**：改词表不回溯改写它，否则变更记录与使用者当年读到的说明不符。
    截断保留前面的原始行，故调用方 `enumerate` 出的行号与原文一致。**内部指代那张表仍扫全篇**
    （那是发行时就不该写的东西，不因过了一个版本而免责）；口头语表进这条豁免是因为它现在也管用词
    （量词「档」，见 `COLLOQUIAL`）——用词规则是事后新立的，回溯扫已发行节只会拦出按规矩改不了的历史。
    """
    m = _CHANGELOG_RELEASED.search(text)
    return text[:m.start()] if m else text


# 演示材料的口播稿（ADR 0045 决策六「演示材料的定稿口播稿」条）：文件名对应同目录 manifest.json 里记它 SHA-256 的键。
PRESENTATIONS = REPO / "docs" / "presentations"
TRANSCRIPT_MANIFEST_KEYS = {"narration.md": "narration_sha256", "speaker-notes.md": "speaker_notes_sha256"}


def final_transcript(path: Path) -> bool:
    """口播稿是否仍是定稿原文：文件当前 SHA-256 等于同目录 `manifest.json` 所记的值。

    定稿原文已配音、已出字幕，改字就得重新配音，故与 CHANGELOG 已发行节一样不回溯改写，免扫口吻表与形态①③启发式
    （退役表、内部指代、悬空指针、相对链接、本机坐标照扫）。豁免绑在那一版文字上：口播一经改写、尚未重新配音并更新
    manifest，哈希就不等，整份照扫。manifest 缺失、读不出或没有对应的键，都按「不是定稿」处理。
    """
    import hashlib
    import json
    key = TRANSCRIPT_MANIFEST_KEYS.get(path.name)
    if key is None:
        return False
    try:
        recorded = json.loads((path.parent / "manifest.json").read_text(encoding="utf-8")).get(key)
        return recorded == hashlib.sha256(path.read_bytes()).hexdigest()
    except (OSError, ValueError, AttributeError):
        return False


def wording_scope(path: Path, text: str) -> str:
    """用户文档里交给口吻表与形态①③启发式扫的部分：CHANGELOG 截到第一个已发行节之前，定稿口播稿整份豁免（空串），
    其余页面全文。截断只保留前缀，故调用方 `enumerate` 出的行号与原文一致；内部指代与本机坐标另扫全文。退役表只豁免
    CHANGELOG 已发行节：`scan` 在定稿口播稿上另对全文补扫退役表。"""
    if path.name == "CHANGELOG.md":
        return changelog_unreleased(text)
    if final_transcript(path):
        return ""
    return text


# `](../x)` / `](./x)` / `](foo.md)` / `](references/foo.md)`：PyPI/npm 页面与 skill 安装态都渲染不出仓库的目录树。
RELATIVE_LINK = re.compile(r"\]\((?:\.\.?/|(?![a-z][a-z0-9+.-]*:|#)[^)\s]+\.md)")

# ── ADR 0045 决策六形态①③：符号当谓语与省略中心词的数字缩写 ─────────────────────
# 决策六把三种漏进人读层的 AI 侧缩写立为口吻规则：②的固定词已进上面的 COLLOQUIAL；①③是形态、不是固定词，只能靶向
# 启发式：中文字紧邻 `=`（含全角）即视为把等号当「是 / 即」用；「退 <数字>」即省了中心词「退出码」。扫描前先剥掉代码块
# 与行内代码（markdown 用 `prose_lines`，注释与 docstring 用 `comment_prose_lines`）——代码里的赋值、命令示例、JSON 片段
# 本来就该是符号。≠ / ⊆ 在中文正文里没有合法用法，直接禁。箭头只在用户文档与 skill 正文里禁（技术文档与注释允许它表顺序与
# 因果），故单独一条。
SYMBOL_PREDICATE = re.compile(r"[一-鿿]\s*[=＝]\s|\s[=＝]\s*[一-鿿]|(?<!绿)≠(?!对)|[⊆∈∧∨⇒«»]")  # 「绿≠对」是 CLAUDE.md 立的判据名，放行；≥ / ≤ 是数值比较、不算
NUMERIC_SHORTHAND = re.compile(r"退\s?[0-9]+(?![0-9.\-])")   # 「退出码 2」不命中：退 后面是 出
ARROW = re.compile(r"→")

_FENCE = re.compile(r"^\s*(```|~~~)")
CODE_SPAN = re.compile(r"`([^`\n]+)`")  # 单行反引号代码跨（跨行的不是命令写法，不收）；正文抽取剥它，skill 的命令 token 抽取收它


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


# 注释与 docstring 的抽取（`scan("code", …)` 用）：Python 走 tokenize + ast（注释与三种 docstring），
# TS / JS 走遮蔽字符串后的 // 与 /* */，shell / YAML / Dockerfile 走行内 #。返回 (行号, 文本) 列表。
_JS_STRING = re.compile(r"'(?:\\.|[^'\\\n])*'|\"(?:\\.|[^\"\\\n])*\"|`(?:\\.|[^`\\])*`", re.S)
_HASH_COMMENT = re.compile(r"(?<![\"'])#(.*)$")


def _consecutive_runs(units: list[tuple[int, str]]) -> list[list[tuple[int, str]]]:
    """按行号把有序的注释行切成段：与上一行行号相同或相邻即同一段。"""
    runs: list[list[tuple[int, str]]] = []
    for unit in units:
        if runs and unit[0] - runs[-1][-1][0] <= 1:
            runs[-1].append(unit)
        else:
            runs.append([unit])
    return runs


def comment_blocks(path: Path) -> list[list[tuple[int, str]]]:
    """注释与 docstring 按段分组，每段是一组 (行号, 文本)：一个 docstring 一段，行号相连的注释行一段（连续的 `#` / `//`
    行、一个 `/* … */` 块）。分段让围栏代码块的起止只在同一段内配对（见 `comment_prose_lines`）。"""
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
            return _consecutive_runs(out)
        blocks = _consecutive_runs(out)
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                doc = ast.get_docstring(node, clean=False)
                if doc:
                    first = node.body[0].lineno if node.body else 1
                    blocks.append([(first + k, line) for k, line in enumerate(doc.splitlines())])
        return blocks
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
        return _consecutive_runs(out)
    for i, line in enumerate(text.splitlines(), 1):  # .sh / .yml / Dockerfile
        m = _HASH_COMMENT.search(line)
        if m and not line.lstrip().startswith("#!"):
            out.append((i, m.group(1)))
    return _consecutive_runs(out)


def comment_units(path: Path) -> list[tuple[int, str]]:
    """注释与 docstring 的原文行（`comment_blocks` 展平）。"""
    return [unit for block in comment_blocks(path) for unit in block]


_COMMENT_LEADER = re.compile(r"^\s*[#*]*")  # 判围栏前去掉的行首注释记号：`#` 注释的井号、`/* … */` 块内续行的星号


def comment_prose_lines(path: Path) -> list[tuple[int, str]]:
    """注释与 docstring 的正文行：每段内跳过围栏代码块、行内反引号代码替换为空格（与 `prose_lines` 对 markdown 的处理一致），
    行号与原文一致。

    只给决策六形态①③的启发式用：代码示例里的 `=` 与「退 N」本来就是符号。口吻表、退役旧名、悬空指针与本机坐标扫原文
    （`comment_units`）：本机坐标多半写在反引号里，剥掉就漏。围栏只在同一段内配对，一段里没闭合的围栏不会吞掉下一段。
    TS / JS 注释里的反引号在抽取时已随字符串遮蔽一并换成空格，这一步对它们不再起作用。
    """
    out: list[tuple[int, str]] = []
    for block in comment_blocks(path):
        in_fence = False
        for line_no, line in block:
            if _FENCE.match(_COMMENT_LEADER.sub("", line, count=1)):
                in_fence = not in_fence
                continue
            if not in_fence:
                out.append((line_no, CODE_SPAN.sub(" ", line)))
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
# 的形态（`journey/NNNN-…`），提到目录本身（「过程产物放 docs/journey/」）是合法的分层描述。仓库路径与相对路径都认：
# `docs/journey/NNNN-`、从 docs/ 下的文件出发的 `../journey/NNNN-` 与 `./journey/NNNN-`，以及行首或标点之后的
# `journey/NNNN-`；前面紧挨字母、数字、`_` 或 `-` 的不认，那是别的目录名（`my-journey/`、`user_journey/`）。
# journey 文件之间的互链不受影响：journey 不在长期文档的扫描面里，归类为只拦本机坐标的 other-md。
DANGLING_JOURNEY = re.compile(r"(?<![A-Za-z0-9_-])journey/\d{4}-")
BARE_WP = re.compile(r"\bWP-?\d+[A-Za-z]?(?:-\d+)?\b")
# 本机坐标：产出机器个人目录下的绝对路径与本地 clone 目录名——只在那台机器上成立，对别的 contributor 是悬空的，文件一律写
# repo 相对路径。与 MACHINE_ROOTS 分开：那组根服务于「录制机产物里的任何绝对路径」（含 /tmp、/app 这类容器内路径），这里只认
# 个人目录与 clone 名——容器布局（`/tmp/gherkai-run/<run_id>`、`/app`）是设计事实、允许写进文档。全仓 markdown（含 journey
# 与工具说明，扫原文含行内代码——路径多半就写在反引号里）与 code 注释都拦；journey 虽是暂存区、也在公开仓库里被人读。
CLONE_DIR_NAMES = ("yaozhou",)  # 仓库名是 gherkai；曾用的本地 clone 目录名不进任何文件
# 形态：POSIX 个人目录 `/Users/<名>/`、`/home/<名>/`（名字可含非 ASCII；前面不能是字母数字或 `/`，否则 `https://x.com/home/alice/`
# 这类 URL 路径会误报）、Windows `C:\Users\<名>\`（盘符与 users 不分大小写、反斜杠可写成转义的两个）、clone 目录名。
MACHINE_COORDINATE = re.compile(
    r"(?<![A-Za-z0-9/])(?:file://)?(?:/Users|/home)/[^/\\\s`\"']+/"
    r"|(?i:[A-Za-z]:\\{1,2}Users\\{1,2}[^\\\s`\"']+\\{1,2})"
    r"|(?<![A-Za-z0-9_-])(?:" + "|".join(re.escape(n) for n in CLONE_DIR_NAMES) + r")(?![A-Za-z0-9_-])"
)

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
    """用户文档：user guide、根 README、CHANGELOG 与演示材料（ADR 0045 决策一）。"""
    return (sorted((REPO / "docs" / "user-guide").glob("*.md")) + [REPO / "README.md", REPO / "CHANGELOG.md"]
            + sorted(PRESENTATIONS.rglob("*.md")))


# 包页面：没有仓库上下文的使用者面——各发行包的长描述（逐字上 PyPI / npm）与 GitHub Release 正文的固定块
# （`.github/scripts/release_notes.py render` 把占位符代入真值后接在 CHANGELOG 本版节之后）。
PY_PACKAGES = ("cli", "core", "runtime", "deploy_aws", "engines/novaact")
NPM_PACKAGES = ("engines/midscene",)
RELEASE_FOOTER = REPO / ".github" / "release_body_footer.md"
# 扫 Release 固定块时代入的样例值：护栏扫的是读者看到的渲染形态；键即模板必须带的占位符。
RELEASE_FOOTER_SAMPLE = {"{{VERSION}}": "9.9.9", "{{OWNER}}": "o", "{{REPO}}": "r"}
# Release 正文里指向仓库文件的链接锁定 tag（`blob/v<版本>/`），本版说明与它链到的文档同版；`blob/HEAD/` 会随默认分支变化。
UNPINNED_BLOB = re.compile(r"blob/HEAD/")


def package_pages() -> list[Path]:
    """包页面的文件：各 Python 包 pyproject `readme` 指向的文件、npm 包 `files` 里列了的 README.md，加 Release 正文的固定块。

    缺字段或文件不存在的包不收、也不在这里报错：classify 每次编辑都调它，hook 不能因一份改到一半的 pyproject 卡住编辑；
    「每个包都带 README」由 `test_package_readmes.py` 断言。
    """
    import json
    import tomllib
    pages: list[Path] = []
    for pkg in PY_PACKAGES:
        try:
            meta = tomllib.loads((REPO / pkg / "pyproject.toml").read_text(encoding="utf-8"))
        except (OSError, tomllib.TOMLDecodeError):
            continue
        readme = meta.get("project", {}).get("readme")
        readme = readme.get("file") if isinstance(readme, dict) else readme
        if readme:
            pages.append(REPO / pkg / readme)
    for pkg in NPM_PACKAGES:
        try:
            pj = json.loads((REPO / pkg / "package.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if "README.md" in pj.get("files", []):
            pages.append(REPO / pkg / "README.md")
    pages.append(RELEASE_FOOTER)
    return [p for p in pages if p.is_file()]


def technical_docs() -> list[Path]:
    docs = [REPO / "CONTRIBUTING.md", REPO / ".github" / "workflows" / "README.md", REPO / "docs" / "README.md",
            REPO / "core" / "tests" / "README.md", REPO / "skills" / "README.md"]
    docs += sorted((REPO / "docs" / "internals").glob("*.md"))
    docs += sorted(REPO.glob("*/DEVELOPMENT.md")) + sorted(REPO.glob("engines/*/DEVELOPMENT.md"))
    docs += sorted((REPO / "tools").glob("*.md")) + sorted((REPO / "tools").glob("*/*.md"))  # 工具手册与 tools/<name>/ 下的说明
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


def all_markdown() -> list[Path]:
    """全仓**已跟踪**的 markdown（本机坐标护栏的适用面：含 docs/journey/ 与 tools/ 下的说明）。按 git 清单取，忽略规则里的
    产物目录（评测工作区、依赖、构建产物）自然不在内；拿不到 git 时退回文件系统遍历加目录排除。"""
    import subprocess
    try:
        out = subprocess.run(["git", "-C", str(REPO), "ls-files", "-z", "--", "*.md"], capture_output=True, check=True)
        files = [REPO / f for f in out.stdout.decode("utf-8").split("\0") if f]
    except (OSError, subprocess.CalledProcessError):
        files = [p for p in REPO.rglob("*.md") if not (_SKIP_DIRS & set(p.parts)) and ".git" not in p.parts]
    return sorted(p for p in files if p.exists() and not (_SKIP_DIRS & set(p.parts)))


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
    """把一个文件归到某个人读面（返回 None 表示不在任何护栏扫描面内）。"""
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
    if p in package_pages():
        return "package-page"
    if p.suffix == ".md" and not (_SKIP_DIRS & set(p.parts)):
        return "other-md"  # journey 与各处说明：不套口吻规则，只拦本机坐标
    return None


def _js_comment_raw_lines(text: str) -> list[tuple[int, str]]:
    """TS / JS 注释的原文（不遮蔽字符串）：`//` 之后的部分，以及 `/* … */` 块内的行。只给本机坐标这类不受字符串干扰的规则用。"""
    out: list[tuple[int, str]] = []
    in_block = False
    for i, line in enumerate(text.splitlines(), 1):
        if in_block:
            end = line.find("*/")
            out.append((i, line if end < 0 else line[:end]))
            if end >= 0:
                in_block = False
            continue
        start = line.find("/*")
        if start >= 0:
            end = line.find("*/", start + 2)
            out.append((i, line[start:] if end < 0 else line[start:end]))
            in_block = end < 0
            continue
        pos = line.find("//")
        if pos >= 0 and not re.search(r"[A-Za-z]:$", line[:pos]):  # 排除 `https://` 这类 URL 里的 `//`
            out.append((i, line[pos + 2:]))
    return out


def scan(kind: str, path: Path, only_lines: set[int] | None = None) -> list[tuple[int, str, str]]:
    """按人读面的规则束扫一个文件，返回 (行号, 类别, 原文)。only_lines 给了就只报这些行（hook 的「只报本次改动的行」）。"""
    p = path if path.is_absolute() else REPO / path
    text = p.read_text(encoding="utf-8", errors="replace")
    if kind == "package-page" and p == RELEASE_FOOTER:
        for placeholder, sample in RELEASE_FOOTER_SAMPLE.items():  # 扫渲染后的形态；占位符都在行内，行号不变
            text = text.replace(placeholder, sample)
    hits: list[tuple[int, str, str]] = []
    seen: set[tuple[int, str]] = set()  # 同一行同一类别只报一次（两条抽取路径可能都覆盖到同一行）

    def add(line_no: int, label: str, line: str) -> None:
        if (only_lines is None or line_no in only_lines) and (line_no, label) not in seen:
            seen.add((line_no, label))
            hits.append((line_no, label, line.strip()[:110]))

    def apply(units, rules):
        for line_no, line in units:
            for label, rx in rules:
                if rx.search(line):
                    add(line_no, label, line)

    shorthand = (("符号当谓语", SYMBOL_PREDICATE), ("省略中心词的「退 N」", NUMERIC_SHORTHAND))
    wording = (("口头语或自造复合词", COLLOQUIAL),) + shorthand
    pointers = (("指向 journey 文件的悬空指针", DANGLING_JOURNEY), ("裸 WP 编号", BARE_WP))
    coords = (("本机坐标（个人目录下的绝对路径或 clone 目录名）", MACHINE_COORDINATE),)
    raw_lines = [(i, line) for i, line in enumerate(text.splitlines(), 1)]
    if kind != "code":
        apply(raw_lines, coords)  # markdown 扫原文含行内代码与代码块：路径多半就写在反引号里
    if kind == "code":
        # 形态①③扫剥掉代码块与行内代码后的正文，其余规则扫注释原文（本机坐标多半写在反引号里，剥掉就漏）
        apply(comment_units(p), (("口头语或自造复合词", COLLOQUIAL), ("退役旧名", RETIRED_TERMS_IN_CODE)) + pointers + coords)
        apply(comment_prose_lines(p), shorthand)
        if p.suffix in {".mts", ".ts", ".mjs", ".js"}:
            # comment_units 先遮蔽字符串再找注释，注释里反引号包着的路径会被一并遮掉——本机坐标另按注释原文扫一遍
            apply(_js_comment_raw_lines(text), coords)
    elif kind == "technical-doc":
        apply(prose_lines(text), wording + (("退役旧名", RETIRED_TERMS),) + pointers)
    elif kind in {"user-doc", "skill", "package-page"}:
        scanned = wording_scope(p, text) if kind == "user-doc" else text
        body_start = 0
        if kind == "skill":
            lines = text.splitlines()
            if lines and lines[0].strip() == "---" and "---" in lines[1:]:
                body_start = lines.index("---", 1) + 1
        apply(raw_lines, (("内部指代", FORBIDDEN),))  # 扫全篇：CHANGELOG 已发行节也不豁免内部指代
        apply([(i, l) for i, l in enumerate(scanned.splitlines(), 1) if i > body_start],
              (("口头语或自造复合词", COLLOQUIAL), ("退役旧名", RETIRED_TERMS)))
        apply(prose_lines(scanned, skip_frontmatter=(kind == "skill")), shorthand + (("正文箭头", ARROW),) + pointers)
        if kind == "user-doc" and final_transcript(p):  # 定稿口播稿：口吻表与形态①③免扫，退役表与悬空指针仍扫全文
            apply(raw_lines, (("退役旧名", RETIRED_TERMS),))
            apply(prose_lines(text), pointers)
        if kind == "package-page":
            apply(raw_lines, (("相对链接（包页面与 Release 页面上是死链）", RELATIVE_LINK),))
            if p == RELEASE_FOOTER:
                apply(raw_lines, (("未锁定 tag 的仓库链接（blob/HEAD/）", UNPINNED_BLOB),))
    elif kind == "ai-doc":
        rules = pointers if _rel(p) in COINAGE_DISCUSSION else pointers + (("自造二字复合词", COINAGES),)
        apply(prose_lines(text), rules)
    elif kind == "diagram":
        apply([(i, line) for i, line in enumerate(text.splitlines(), 1)],
              (("内部指代", FORBIDDEN), ("口头语或自造复合词", COLLOQUIAL), ("退役旧名", RETIRED_TERMS),
               ("符号当谓语", SYMBOL_PREDICATE), ("省略中心词的「退 N」", NUMERIC_SHORTHAND)))
    # kind == "other-md"：只有上面的本机坐标一束
    return hits


# ── skill 扫描面与命令 token 抽取（代码跨正则 CODE_SPAN 与正文抽取共用，定义在 prose_lines 旁）──────────────

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

    `words` 是 `gherkai` 之后、第一个 flag 之前的裸词（子命令与位置参数占位符混在一起，由调用方按自己那份
    parser 解析出子命令路径）；`flags` 是该跨内**全部** `--flag`（已去掉 `=值` 与收尾标点）。
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
