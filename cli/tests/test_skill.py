"""agent skill 的护栏（ADR 0043 决策六；fixture 三条见决策七）。

skill 是**产品面**：它随 wheel 发行、由 `skill install` 整目录拷进使用方项目，读者是没有本仓库的 AI agent。
故同受 ADR 0039 约束（零内部指代、链接只用绝对 URL），且它写出的每个子命令 / flag / JSON 键都要对得上
CLI 的真值集——skill 教错一个 flag，agent 会照着打、错在使用方那边才现形。

skill 文案是 markdown，`test_user_facing_messages.py` 只扫 Python 字面量（给它加一个无 `.py` 的目录会
**静默空扫**），故另立本文件；`skill install` 自身的提示 / 错误是 Python 字面量，由那只扫描器自动覆盖。

真值集三处，一处都不靠人读：
- 命令面 = `_build_parser()` 的 `_actions` / `_SubParsersAction.choices` 递归展开（走 argparse 私有 API，
  先例 = `deploy_aws/tests/test_provider.py` 的全集护栏）；
- JSON 键 = `docs/internals/cli-json-contract.md` 的字段记载（表 + 那几段散文，见 `_documented_keys`）；
- 转换副本 = `tools/render_skill_contract.py` 的纯函数 `transform`。

`deploy` / `destroy` 那批 token 不在这里比：provider 住 `[deploy-aws]` optional extra、只有部署方装，
前端的测试不该强依赖它——对照面在 `deploy_aws/tests/test_skill_deploy_tokens.py`。
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

import pytest
from _doc_rules import (
    COLLOQUIAL,
    FORBIDDEN,
    PROVIDER_ONLY_FLAGS,
    RELATIVE_LINK,
    RETIRED_TERMS,
    REPO,
    SKILL_ROOT,
    bare_flags,
    extract_command_spans,
    is_placeholder,
    skill_markdown_files,
)

from gherkai_cli import __main__ as cli_main

CONTRACT_SOURCE = REPO / "docs" / "internals" / "cli-json-contract.md"
CONTRACT_COPY = SKILL_ROOT / "references" / "cli-json-contract.md"
FIXTURES = REPO / "skills" / "gherkai-evals" / "fixtures"

# ── 命令面真值集 ────────────────────────────────────────────────────────────


def _parser_nodes() -> dict[tuple[str, ...], set[str]]:
    """子命令路径 → 该 parser 节点上声明的 `--flag` 集。`()` = 主 parser。"""
    nodes: dict[tuple[str, ...], set[str]] = {}

    def walk(parser: argparse.ArgumentParser, path: tuple[str, ...]) -> None:
        nodes[path] = {s for a in parser._actions for s in a.option_strings if s.startswith("--")}
        for action in parser._actions:
            if isinstance(action, argparse._SubParsersAction):
                for name, sub in action.choices.items():
                    walk(sub, path + (name,))

    walk(cli_main._build_parser(), ())
    return nodes


NODES = _parser_nodes()
ALL_FLAGS = {f for flags in NODES.values() for f in flags}
TOP_LEVEL = {p[0] for p in NODES if len(p) == 1}
# 排他性断言用的归属表：flag → 它出现在哪些**顶层**子命令的子树里。隐藏内部动词（`_reconcile` /
# `_tunnel_watch`，help=SUPPRESS）不算——它们不在使用者面上，不该让一句「仅 run」变红。
OWNERS = {
    flag: {top for top in TOP_LEVEL if not top.startswith("_")
           and any(flag in flags for path, flags in NODES.items() if path[:1] == (top,))}
    for flag in ALL_FLAGS
}


def _resolve(words: tuple[str, ...]) -> tuple[str, ...] | None:
    """裸词序列 → 子命令路径。第一个词不是已知子命令且不是占位符 → None（拼错的子命令）。"""
    if words and is_placeholder(words[0]):
        return None
    path: tuple[str, ...] = ()
    for word in words:
        if path + (word,) in NODES:
            path += (word,)
        else:
            break  # 位置参数（`login.feature` / `<run_id>`）：路径到此为止
    if words and not path:
        return None
    return path


def _allowed_flags(path: tuple[str, ...]) -> set[str]:
    """路径上（含各级祖先）声明的 flag 全集——`deploy --prefix p push-worker …` 这种父层给法是合法的。"""
    return {f for i in range(len(path) + 1) for f in NODES[path[:i]]}


# ── (a) 产品面文案与指针形态 ────────────────────────────────────────────────

GITHUB_URL = re.compile(r"https://github\.com/zhiyanliu/gherkai(?P<rest>[^\s)\]<>，。；]*)")
# 只允许指向仓库内容的三种锁定写法（ADR 0039 面二的发行物约定）：不绑分支名，HEAD 或 tag。
GITHUB_OK = re.compile(r"^(?:|/|/blob/HEAD/.+|/tree/HEAD/.*|/tree/v[^/]+/.*)$")


def test_scan_face_is_not_empty():
    """扫描面为空即红：目录搬家 / 后缀写错不能让下面几条静默变绿。"""
    files = skill_markdown_files()
    assert files, f"{SKILL_ROOT} 下扫不到任何 .md——skill 目录搬家了？先修扫描面，别让护栏空转"
    assert (SKILL_ROOT / "SKILL.md") in files


@pytest.mark.parametrize("md", skill_markdown_files(), ids=lambda p: str(p.relative_to(SKILL_ROOT)))
def test_skill_markdown_is_product_facing(md: Path):
    """零内部指代：skill 落在使用方项目里，ADR 编号 / 决策号 / 内部机制名对那边的 agent 是噪声。

    用词同受词表约束：已退役的旧名（`_doc_rules.RETIRED_TERMS`）不许出现在正文。
    """
    lines = md.read_text(encoding="utf-8").splitlines()
    # frontmatter 的 description 是触发匹配用的：里面转述用户口语（如「跑测试」）是有意的，口头语与旧名两表只扫正文。
    body_start = (lines.index("---", 1) + 1) if lines and lines[0].strip() == "---" and "---" in lines[1:] else 0
    hits = [f"{md.relative_to(REPO)}:{i}: {line.strip()[:120]}"
            for i, line in enumerate(lines, 1)
            if FORBIDDEN.search(line)
            or (i > body_start and (COLLOQUIAL.search(line) or RETIRED_TERMS.search(line)))]
    assert not hits, ("skill 随包发到使用方项目，不得含内部指代、口头语或退役旧名（改产品语言，设计指针留在 ADR）：\n"
                      + "\n".join(hits))


@pytest.mark.parametrize("md", skill_markdown_files(), ids=lambda p: str(p.relative_to(SKILL_ROOT)))
def test_skill_markdown_has_no_relative_links(md: Path):
    """markdown 相对链接一律禁：出 skill 的（`](../…)`）在安装态必死；skill 内的（`](references/x.md)`）虽活，
    但统一禁掉才能与包 README 共用同一份正则。**跨文件指针写反引号裸路径**（`` `references/engines.md` ``）——
    agent 读的是路径、不是超链接。"""
    hits = [f"{md.relative_to(REPO)}:{i}: {line.strip()[:120]}"
            for i, line in enumerate(md.read_text(encoding="utf-8").splitlines(), 1) if RELATIVE_LINK.search(line)]
    assert not hits, ("skill 里的 markdown 相对链接在使用方项目里是死链——跨文件指针改反引号裸路径，"
                      "指仓库内容改绝对 URL：\n" + "\n".join(hits))


@pytest.mark.parametrize("md", skill_markdown_files(), ids=lambda p: str(p.relative_to(SKILL_ROOT)))
def test_github_urls_are_pinned_to_head_or_tag(md: Path):
    """指本仓库的 URL 只用 `blob/HEAD/` / `tree/HEAD/` / `tree/v…/`（裸仓库首页不指内容，也放行）：
    绑分支名的链接会随分支改名烂掉，而使用方拿到的是一份拷贝、修不了。"""
    bad = []
    for i, line in enumerate(md.read_text(encoding="utf-8").splitlines(), 1):
        for m in GITHUB_URL.finditer(line):
            if not GITHUB_OK.match(m.group("rest")):
                bad.append(f"{md.relative_to(REPO)}:{i}: {m.group(0)}")
    assert not bad, "指仓库内容的 URL 只允许 blob/HEAD/ 、tree/HEAD/ 、tree/v<版本>/ 三种形态：\n" + "\n".join(bad)


# ── (b) 命令面真值：成对比对 + 排他性反向断言 ───────────────────────────────


def _all_command_spans():
    return [span for md in skill_markdown_files()
            for span in extract_command_spans(md.read_text(encoding="utf-8"), md)]


def test_skill_mentions_commands_at_all():
    """成对比对的扫描面也不能空：一条 `gherkai …` 都抽不到，说明抽取器与写法脱节了。"""
    assert _all_command_spans(), "skill 里抽不到任何 `gherkai …` 代码跨——抽取器与 skill 的写法脱节了"


def test_flags_are_attached_to_the_right_subcommand():
    """只认**同一个反引号代码跨**内的 `gherkai <子命令> … --flag` 组合，逐对对照该 subparser 的真 flag 集。
    挂错子命令即红（`gherkai submit --json` 这类错误 agent 会照打）。"""
    problems = []
    for span in _all_command_spans():
        path = _resolve(span.words)
        if path is None:
            if span.words and not is_placeholder(span.words[0]):
                problems.append(f"{span.path.relative_to(REPO)}:{span.line}: `{span.span}` 的子命令"
                                f" {span.words[0]!r} 不存在")
            continue  # `gherkai <命令> --help` 这类占位符写法：无子命令可比，flag 走弱断言
        if path[:1] in (("deploy",), ("destroy",)):
            continue  # provider 侧：flag 在 provider 未加载时不在主 parser 上，见模块 docstring
        allowed = _allowed_flags(path)
        for flag in span.flags:
            if flag not in allowed:
                problems.append(f"{span.path.relative_to(REPO)}:{span.line}: `{span.span}`——"
                                f"{flag} 不是 `gherkai {' '.join(path)}` 的 flag")
    assert not problems, "skill 里的子命令/flag 组合对不上真 parser：\n" + "\n".join(problems)


# skill 里也会写别的工具的命令行（装 CLI、build 镜像、装 skill）。这两张表把它们排除在 gherkai 真值集之外：
# 整条命令行按首 token 认（`uvx --from … gherkai …`），落单的 flag 显式登记（登记制：加新的要有人过一眼）。
FOREIGN_PROGRAMS = frozenset({"uvx", "uv", "npx", "npm", "pip", "pipx", "docker", "podman",
                              "python", "python3", "node", "export", "unset", "git"})
FOREIGN_TOOL_FLAGS = frozenset({"--platform"})  # docker build 的架构 flag


def test_bare_flags_exist_somewhere():
    """散落的裸 `--flag`（不在 `gherkai …` 跨里的）只做弱断言：至少得是个真存在的 flag（打错字即红）。"""
    unknown = sorted({f"{path.relative_to(REPO)}:{line}: `{span}` 里的 {flag}"
                      for path in skill_markdown_files()
                      for flag, line, span in bare_flags(path.read_text(encoding="utf-8"))
                      if (span.split() or [""])[0] not in FOREIGN_PROGRAMS
                      and flag not in ALL_FLAGS and flag not in PROVIDER_ONLY_FLAGS
                      and flag not in FOREIGN_TOOL_FLAGS})
    assert not unknown, ("这些 flag 在 CLI 里不存在（provider 侧的见 PROVIDER_ONLY_FLAGS，别的工具的见 "
                         "FOREIGN_TOOL_FLAGS）：\n" + "\n".join(unknown))


# 排他性反向断言。成对比对对排他错误是**隐形**的——`(run, --json)` 存在即绿，哪怕 `--json` 同时挂在别处；
# 这条才挡「把 run 独有的选项写成两边都有」。
#
# **书写约定**（skill 里的排他声明按这三种形态之一写，护栏按同序解析）：
#   ① 散文/列头：「仅 `run` = `--fail-fast` / `--quiet`」——标记之后到最近的 `；` / `）` / `|` / 行尾之间的 flag；
#   ② 括注在 flag 之后：「`--worker-variant`（仅 `run` / `submit`）」——标记前**紧邻的那一个** flag；
#   ③ 表格行：「| 仅 `submit` | `--tunnel-ttl` | 说明… |」——标记所在单元格的**下一格**里的 flag
#      （「说明」格不算，否则 `只在 cloud + --expose-local 时有意义` 这种举例会被误当成排他声明）。
# 三档按 ①→②→③ 取第一个能取到 flag 的：① 空且标记前有 flag → ②；都没有 → ③。
# 「仅 `a` / `b`」表示这批 flag 恰好属这几个子命令（归属集相等，不是包含）。
EXCLUSIVE_CLAIM = re.compile(r"仅\s*(?P<subs>`[a-z][a-z0-9-]*`(?:\s*/\s*`[a-z][a-z0-9-]*`)*)")
FLAG_IN_TEXT = re.compile(r"--[A-Za-z][A-Za-z0-9-]*")


def _claimed_flags(line: str, marker_start: int, marker_end: int) -> set[str]:
    forward = re.split(r"[；;）)|]", line[marker_end:])[0]
    if flags := set(FLAG_IN_TEXT.findall(forward)):
        return flags                                    # ① 散文形态
    before = FLAG_IN_TEXT.findall(line[:marker_start])
    if before:
        return {before[-1]}                             # ② 括注在 flag 之后
    cells = line.split("|")
    for n, cell in enumerate(cells[:-1]):                # ③ 表格行：标记所在格的下一格
        offset = sum(len(c) + 1 for c in cells[:n])
        if offset <= marker_start < offset + len(cell):
            return set(FLAG_IN_TEXT.findall(cells[n + 1]))
    return set()


def test_exclusive_claims_are_true():
    problems = []
    for md in skill_markdown_files():
        for i, line in enumerate(md.read_text(encoding="utf-8").splitlines(), 1):
            for m in EXCLUSIVE_CLAIM.finditer(line):
                subs = set(re.findall(r"`([a-z][a-z0-9-]*)`", m.group("subs")))
                if not subs & TOP_LEVEL:
                    continue  # 「仅 `local` 档」这类不是子命令排他声明，本约定不管
                if unknown := sorted(subs - TOP_LEVEL):
                    problems.append(f"{md.relative_to(REPO)}:{i}: 「仅 …」里没有这些子命令：{unknown}")
                    continue
                for flag in _claimed_flags(line, m.start(), m.end()):
                    owners = OWNERS.get(flag)
                    if owners is None:
                        problems.append(f"{md.relative_to(REPO)}:{i}: 「仅 {sorted(subs)}」段里的 {flag} 不存在")
                    elif owners != subs:
                        problems.append(f"{md.relative_to(REPO)}:{i}: 「仅 {sorted(subs)}」不成立——"
                                        f"{flag} 属于 {sorted(owners)}")
    assert not problems, "「仅 <子命令>」的排他声明与真 parser 不符：\n" + "\n".join(problems)


# ── (c) JSON 键对照 ────────────────────────────────────────────────────────

KEY_TOKEN = re.compile(r"^[a-z][a-z0-9_]*$")  # 形如 JSON 键：天然排除 flag（含 `-`）、路径（含 `/` `.`）、URI（含 `:`）

# 契约页以**散文**记载、不在任何字段表里的真键（页里的位置在注释里点明；进了表也不必删这里）。
# 与下面的「非键」表分开，是为了不让人把真键登记成非键——那会把真正的漂移一起放过。
PROSE_DOCUMENTED_KEYS = frozenset({
    # run_meta 那段散文（契约页「顶层 = RunResult + run_meta + artifacts」之后的 `run_meta`（definition）段）
    "created_at", "max_concurrency", "steps_dir", "worker_variant", "worker_task_defs", "extra_http_headers",
    # plan / run 的 `steps[].deterministic` 三态那段
    "conflict",
})

# 形如键但不是键的 token：引擎名、状态值、错误码、doctor 的段名与项名、目录名、子命令名、JSON 字面量。
# 命中未登记的即红，逼人显式登记（写 skill 时随手加一个反引号词，很容易实际是把键名记错了）。
NON_KEY_TOKENS = frozenset({
    # 引擎名
    "novaact", "midscene",
    # skill 正文里举的 scope 通名反例（教人别用的名字，不是键）
    "login", "smoke",
    # 状态 / 判定值
    "passed", "failed", "error", "skipped", "aborted", "pending", "running", "queued",
    # error_type / evidence_missing / report_refs.kind / pending_cleanup.reason 的取值
    "assertion_failed", "engine_error", "network_error", "timeout", "aborted_by_stop",
    "no_ref", "unreadable", "unsupported_schema", "summary", "report", "trajectory",
    "retired", "orphan",
    # doctor 的 section / name 取值
    "cli", "engines", "steps", "aws", "backend", "provider", "resources", "identity",
    "region", "reachability", "any", "node", "cdk", "load", "dir",
    # flag 的取值（`--vpc` 三档 / `--pointer`）与默认 variant 名
    "default", "new", "yes", "no", "base",
    # 子命令名 / 目录名 / 文件名片段
    "run", "plan", "submit", "status", "explain", "doctor", "install", "skill", "jobs", "reports", "references",
    "deploy", "destroy",
    # JSON 字面量
    "null", "true", "false",
})


def _documented_keys() -> set[str]:
    """契约页记载的字段名。取「字段表里（任一列）+『顶层…』/『每项…』散文里」的反引号 token，
    再按键形状过滤——ADR 拒绝「全页反引号超集」的理由是它混入 flag 与路径，键形状把这两类整个滤掉。
    只取首列不够：`report_refs[]` 的 `kind`/`ref`/`label`、`votes` 的 `yes`/`total`、`scenarios[]` 的
    `argument`/`content`/`rows` 都记在「含义」列里，只认首列会把这些真键判成没写。"""
    keys: set[str] = set()

    def collect(text: str) -> None:
        for token in re.findall(r"`([^`]+)`", text):
            for part in re.split(r"\s*/\s*", token):
                part = part.split(".")[-1].rstrip("[]")
                if KEY_TOKEN.match(part):
                    keys.add(part)

    for line in CONTRACT_SOURCE.read_text(encoding="utf-8").splitlines():
        if line.startswith("|") and not re.fullmatch(r"\|[\s:|-]+\|?", line.strip()):
            collect(line)
        elif "顶层" in line or "每项" in line:
            collect(line)
    assert len(keys) > 50, f"契约页里只抽到 {len(keys)} 个字段名——抽取规则与页面形态脱节了"
    return keys | PROSE_DOCUMENTED_KEYS


def test_key_shaped_tokens_are_documented_keys():
    """skill 里形如 JSON 键的反引号 token 必须是契约页记载的键，否则显式登记成非键。
    挡的是「把 `record_missing` 写成 `records_missing`」这类 agent 会照着解析的错。"""
    documented = _documented_keys()
    unknown = []
    for md in skill_markdown_files():
        for i, line in enumerate(md.read_text(encoding="utf-8").splitlines(), 1):
            for token in re.findall(r"`([^`]+)`", line):
                if KEY_TOKEN.match(token) and token not in documented and token not in NON_KEY_TOKENS:
                    unknown.append(f"{md.relative_to(REPO)}:{i}: `{token}`")
    assert not unknown, ("这些 token 形如 JSON 键但契约页没记：真键 → 先写进 docs/internals/cli-json-contract.md；"
                         "不是键（引擎名/状态值/目录名…）→ 登记进 NON_KEY_TOKENS：\n" + "\n".join(sorted(set(unknown))))


# ── (d) 转换副本 ───────────────────────────────────────────────────────────


def test_contract_copy_equals_transform_of_source():
    """副本必须逐字节等于 `transform(手写源)`：改了源没重新运行生成器即红（副本不是第二事实源，是渲染产物）。"""
    sys.path.insert(0, str(REPO / "tools"))
    import render_skill_contract as renderer

    assert CONTRACT_COPY.is_file(), f"缺副本 {CONTRACT_COPY.relative_to(REPO)}——运行 tools/render_skill_contract.py"
    expected = renderer.transform(CONTRACT_SOURCE.read_text(encoding="utf-8"))
    assert CONTRACT_COPY.read_text(encoding="utf-8") == expected, (
        "skill 里的契约副本与源页不同步——运行 `python3 tools/render_skill_contract.py` 重渲染"
    )


def test_rewrite_tables_are_all_used():
    """转换器的两张改写表（指针 / 禁词）里每条都得在源页命中：命中零次说明源页改了措辞、替换悄悄失效。
    `transform` 自己会为此抛异常，这里显式运行一次，让失败落在护栏而不是发布链上。"""
    sys.path.insert(0, str(REPO / "tools"))
    import render_skill_contract as renderer

    source = CONTRACT_SOURCE.read_text(encoding="utf-8")
    for old in list(renderer.POINTER_REWRITES) + list(renderer.FORBIDDEN_REWRITES):
        assert old in source, f"改写表里这条在契约页里找不到（措辞变了？）：{old!r}"
    renderer.transform(source)  # 未登记的禁词 / 相对链接 / 仓库内路径会在这里抛


# ── (e) 目录白名单 ─────────────────────────────────────────────────────────


def test_skill_directory_whitelist():
    """`SKILL.md` + `references/` +（按需）`scripts/`，别的一律红——挡评测资产悄悄长回发行树里
    （两条安装路径都是整目录递归拷贝，排除名单由安装器硬编码、使用方改不了）。
    `.gherkai-skill-version` 是安装态产物，包内不得有，故不在白名单里。"""
    allowed_top = {"SKILL.md", "references", "scripts"}
    extra = sorted(p.name for p in SKILL_ROOT.iterdir() if p.name not in allowed_top and p.name != "__pycache__")
    assert not extra, f"skill 目录只允许 {sorted(allowed_top)}，多出：{extra}（评测资产放仓库根 skills/gherkai-evals/）"
    bad = sorted(str(p.relative_to(SKILL_ROOT)) for p in (SKILL_ROOT / "references").rglob("*")
                 if p.is_file() and p.suffix != ".md")
    assert not bad, f"references/ 下只放 markdown：{bad}"
    assert not (SKILL_ROOT / ".gherkai-skill-version").exists(), "版本标记是安装态产物，包内不该有"


# ── (f) 形态（Agent Skills 规范硬约束的本地复刻）────────────────────────────

NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def _frontmatter_and_body(text: str) -> tuple[dict[str, str], str]:
    """极简 frontmatter 解析（不引 yaml：dev 依赖里没有，为一条护栏引一个包不值）。
    支持 `key: 单行值`、引号值，以及 `key: >-` / `key: |` 折叠块（description 优化循环容易写成折叠块）。"""
    lines = text.splitlines()
    assert lines and lines[0].strip() == "---", "SKILL.md 必须以 `---` frontmatter 开头（宿主靠它发现 skill）"
    end = next(i for i, ln in enumerate(lines[1:], 1) if ln.strip() == "---")
    fields: dict[str, str] = {}
    key = None
    for raw in lines[1:end]:
        m = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", raw)
        if m:
            key, value = m.group(1), m.group(2).strip()
            fields[key] = "" if value in (">", ">-", "|", "|-") else value.strip("'\"")
        elif key and raw.strip():
            fields[key] = (fields[key] + " " + raw.strip()).strip()
    return fields, "\n".join(lines[end + 1:])


def test_skill_form_limits():
    """`name` 形态且等于目录名（安装目标目录名由它派生）；`description` 非空 ≤ 1024（description 优化循环
    天然把它写长，这条是刹车）；正文 ≤ 500 行**且** ≤ 12000 字符（行数管结构、字符数管上下文成本；
    超了往 `references/` 挪，不压行）。"""
    fields, body = _frontmatter_and_body((SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8"))
    name = fields.get("name", "")
    assert NAME_RE.match(name) and 1 <= len(name) <= 64, f"frontmatter name 形态不合规：{name!r}"
    assert name == SKILL_ROOT.name, f"frontmatter name {name!r} 必须等于目录名 {SKILL_ROOT.name!r}"
    desc = fields.get("description", "")
    assert desc, "frontmatter description 不能空——它承担全部「何时用」，宿主的隐式触发只看它"
    assert len(desc) <= 1024, f"description {len(desc)} 字符 > 1024（规范硬上限）"
    assert len(body.splitlines()) <= 500, f"SKILL.md 正文 {len(body.splitlines())} 行 > 500——往 references/ 挪"
    assert len(body) <= 12000, f"SKILL.md 正文 {len(body)} 字符 > 12000——往 references/ 挪"


# ── (g)(h)(i) 评测 fixture：ignore 行为、git 跟踪、可搬迁 ────────────────────

# `.gitignore` 的派生品段会静默吞掉 fixture 里实际运行产出的文件，且是**部分**吞（Nova 的 evidence 截图不在规则内）
# ——比全缺更难发现。反白名单 + 其后重列的密钥规则由这两组探针**行为式**核：两向都测才同时挡住
# 「新规则排到反白名单之后」与「收紧句被删」两种回归。探针路径无需真实存在（`--no-index`）。
PROBE_NOT_IGNORED = ("reports/x.json", "screenshots/y.jpg", "a.log", "a.report.html", ".env.example")
PROBE_IGNORED = (".env", ".env.local", "z.pem", "z.key", ".aws/config", "credentials")


def _is_ignored(rel: str) -> bool:
    proc = subprocess.run(["git", "check-ignore", "-q", "--no-index", "--", rel],
                          cwd=REPO, capture_output=True, text=True)
    assert proc.returncode in (0, 1), f"git check-ignore 失败（{proc.returncode}）：{proc.stderr.strip()}"
    return proc.returncode == 0


@pytest.mark.parametrize("rel", PROBE_NOT_IGNORED)
def test_fixture_derived_artifact_shapes_are_not_ignored(rel: str):
    probe = f"skills/gherkai-evals/fixtures/_probe/{rel}"
    assert not _is_ignored(probe), (f"{probe} 被 .gitignore 吞了——fixture 里实际运行产出的文件必须入库；"
                                   "检查派生品段之后的 `!skills/gherkai-evals/fixtures/**` 反白名单还在不在")


@pytest.mark.parametrize("rel", PROBE_IGNORED)
def test_fixture_secret_shapes_stay_ignored(rel: str):
    probe = f"skills/gherkai-evals/fixtures/_probe/{rel}"
    assert _is_ignored(probe), (f"{probe} 没被忽略——反白名单把密钥规则一起放开了；"
                                "反白名单之后必须重列密钥规则（以 .gitignore 密钥块为准，逐条对照）")


def _fixture_files() -> list[Path]:
    # __pycache__ 不是 fixture 内容：本机对 fixture 运行一次 plan / list-deterministic，worker 就会在 steps/ 下编译出 .pyc
    return [p for p in FIXTURES.rglob("*") if p.is_file() and "__pycache__" not in p.parts] if FIXTURES.is_dir() else []


def test_every_fixture_file_is_tracked():
    """提交前抓漏：磁盘上 `fixtures/**` 每个文件都在 `git ls-files` 里（干净克隆上恒绿，不是 CI 的唯一防线——
    行为式 ignore 断言才是）。"""
    files = _fixture_files()
    if not files:
        pytest.skip("还没有 fixture")
    tracked = set(subprocess.run(["git", "ls-files", "-z", "skills/gherkai-evals/fixtures"],
                                 cwd=REPO, capture_output=True, text=True, check=True).stdout.split("\0")) - {""}
    # 两种成因分开报：被忽略 = 真缺陷（改 .gitignore）；只是还没 add = 提交前的正常提醒。
    missing = [f"{rel}（{'被 .gitignore 忽略' if _is_ignored(rel) else '还没 git add'}）"
               for p in files if (rel := str(p.relative_to(REPO))) not in tracked]
    assert not missing, "这些 fixture 文件不在 git 里（被忽略的先修 .gitignore，`git add -f` 救不回打包）：\n" + "\n".join(sorted(missing))


# fixture 可搬迁契约的兜底：逐文件枚举字段总会漏新字段，这条按不变量兜——文本里出现的绝对路径必须是
# 占位符形态 `{{FIXTURE_ROOT}}/…`（评测前由 materialize 换成舞台目录）。
# 判据 = 已知机器根（本机 / Linux / 容器常见根）。曾试过「JSON 里以 `/` 打头的字符串值一律算路径」：
# 假红——step 原文 `Then 页面地址匹配 "/wiki/OpenAI"` 会以转义字串嵌进 run_meta / jobs，URL 路径与机器路径
# 在形态上分不开，只有根目录名能分。录制机换了新根就补进这张表（materialize.py 的 snapshot 漏扫用同一组根）。
ABSOLUTE_PATH = re.compile(
    r"(?:file://)?/(?:Users|home|private|var|tmp|opt|Volumes|root|mnt|srv|app|workspace|work|data|etc|usr|nix|run)/[^\s\"'\\]*")
TEXT_SUFFIXES = {".json", ".md", ".txt", ".html", ".feature", ".py", ".ts", ".mts", ".log", ".csv", ".yml", ".yaml"}


def test_fixtures_carry_no_absolute_paths():
    files = [p for p in _fixture_files() if p.suffix in TEXT_SUFFIXES]
    if not files:
        pytest.skip("还没有 fixture 文本文件")
    hits = []
    for path in files:
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            for m in ABSOLUTE_PATH.finditer(line):
                hits.append(f"{path.relative_to(REPO)}:{i}: {m.group(0)[:120]}")
    assert not hits, ("fixture 里不得有产出机器的绝对路径（换成 `{{FIXTURE_ROOT}}` 占位符，评测前物化）：\n"
                      + "\n".join(hits))


def test_sync_hook_is_wired_for_the_contract_copy():
    """项目级 Claude Code hook 把「改源即重渲染副本」前移到编辑时刻（ADR 0043 决策四「同步手段与护栏分工」）：
    settings.json 的 PostToolUse 必须挂着 .claude/hooks/sync-derived.sh，脚本存在、可执行、且真的调用渲染器的 --check 与重渲染。
    护栏本身（本文件的等值断言）不因 hook 而放松。"""
    import json as _json
    import os as _os
    settings = _json.loads((REPO / ".claude" / "settings.json").read_text(encoding="utf-8"))
    post = settings.get("hooks", {}).get("PostToolUse", [])
    entries = [e for e in post if any("sync-derived.sh" in h.get("command", "") for h in e.get("hooks", []))]
    assert entries, "settings.json 的 PostToolUse 没挂 .claude/hooks/sync-derived.sh"
    matchers = " ".join(e.get("matcher", "") for e in entries)
    for tool in ("Edit", "Write", "Bash"):
        assert tool in matchers, f"sync-derived hook 的 matcher 缺 {tool}（Bash 里改文件也要覆盖）"
    script = REPO / ".claude" / "hooks" / "sync-derived.sh"
    assert script.is_file() and _os.access(script, _os.X_OK), "缺 .claude/hooks/sync-derived.sh 或不可执行"
    body = script.read_text(encoding="utf-8")
    assert "render_skill_contract.py --check" in body and "render_skill_contract.py 2>&1" in body, "hook 脚本须先 --check 再重渲染"
    assert "additionalContext" in body, "hook 须经 additionalContext 把结果告诉 agent"

