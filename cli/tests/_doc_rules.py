"""使用者面 markdown 的共享规则与扫描器：多处护栏共用的**单一事实源**。

消费方五处，同源才不会各自漂（扫的都是「发到仓库外、读者没有仓库上下文」的文字，判据同一条——
CLAUDE.md 代码纪律「产品面文案不带内部指代」+ 文档纪律「README / DEVELOPMENT 分层」；决策与理由见
ADR 0039、ADR 0043 决策六）：

- `test_package_readmes.py`：进包的 README / Summary / GitHub Release 正文 footer（禁词 + 退役旧名 + 相对链接）；
- `test_user_docs.py`：仓库内用户文档（`docs/user-guide/**` / 根 README / CHANGELOG）与 `docs/diagrams/` 图源
  （禁词 + 退役旧名；相对链接另查可达性）；
- `test_skill.py`：随 wheel 发行、由 `skill install` 拷进使用方项目的 agent skill markdown（全部规则）；
- `deploy_aws/tests/test_skill_deploy_tokens.py`：skill 里 `deploy` / `destroy` 那批命令 token 对照 provider
  真 parser（provider 住 optional extra、`cli/tests` 不许 import 它，故对照面分在两处、抽取器共用）；
- `tools/render_skill_contract.py`：契约页 → skill 副本的转换器，用禁词表自查有没有漏改的词。

放 `cli/tests/` 而非 `tools/`：它只服务护栏、不是运行期或开发期工具；仓库外的两个消费方（provider 测试、
转换器）显式把这个目录加进 `sys.path` 来复用——宁可让它们多两行 import，也不要两份会漂的禁词表 / 抽取器。
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
COLLOQUIAL = re.compile(r"帽子不是人|烧钱|锁步|lockstep|烙进|烙好|烙成|烙在|逃生舱|旋钮|跑(?!」)")

# 已退役的旧名：CONTEXT.md 词表给了规范名、旧名列进该条 `_Avoid_` 的那批，使用者面一个都不许再出现。
# 与 COLLOQUIAL 分表是因为判据不同——那张管「口吻」（口头语 / 隐喻，永久禁），这张管「用词版本」（旧名 →
# 规范名，随词表增删）。逐词与词表同源由 `test_user_docs.test_retired_terms_are_all_in_the_glossary` 守：
# 往这里加词必须先在 CONTEXT.md 对应词条的 `_Avoid_` 里落下，免得护栏与词表各自演化。
RETIRED_TERMS_WORDS = (
    "跑法", "抢传", "确定性锚点", "大脑", "穿刺", "骨架验证用例", "版本单旋钮", "无状态跑批", "在跑 run",
    "逃生舱", "供给包", "提交方", "技能包", "建造者 AI", "AI coding agent",
    "维护者", "本机档", "云端档", "cloud 档", "local 档",
)
RETIRED_TERMS = re.compile("|".join(re.escape(w) for w in RETIRED_TERMS_WORDS))

_CHANGELOG_RELEASED = re.compile(r"^## \[\d", re.M)  # 第一个已发行版本节的标题（`## [Unreleased]` 不匹配）


def changelog_unreleased(text: str) -> str:
    """CHANGELOG 交给退役词表扫的部分 = 截到第一个已发行版本节之前。

    已发行节是**发行当时的原话**：改词表不回溯改写它，否则变更记录与使用者当年读到的说明不符。
    截断保留前面的原始行，故调用方 `enumerate` 出的行号与原文一致。内部指代 / 口头语两张表仍扫全篇
    （那是发行时就不该写的东西，不因过了一个版本而免责）。
    """
    m = _CHANGELOG_RELEASED.search(text)
    return text[:m.start()] if m else text


# `](../x)` / `](./x)` / `](foo.md)` / `](references/foo.md)`：PyPI/npm 页面与 skill 安装态都渲染不出仓库的目录树。
RELATIVE_LINK = re.compile(r"\]\((?:\.\.?/|(?![a-z][a-z0-9+.-]*:|#)[^)\s]+\.md)")

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
