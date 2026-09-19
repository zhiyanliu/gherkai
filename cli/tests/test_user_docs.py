"""仓库内用户文档的护栏：`docs/user-guide/**`、根 `README.md`、`CHANGELOG.md`（ADR 0045 决策一 / 六；产品面口径同 ADR 0039）。

这些页面在 GitHub 上渲染、有仓库上下文，所以**允许相对链接**——但每个相对链接必须指向真实存在的文件；
读者是使用者与替使用者操作的 agent，所以**零内部指代**（禁词表与包 README 共用同一张 `_doc_rules.FORBIDDEN`），
且不把读者引到 contributor 侧 AI agent 的文档（ADR / CONTEXT / CLAUDE.md / journey / ai-eng）——那些不是给他们读的。
用词还要跟上词表：`CONTEXT.md` 已给出规范名的旧名（`_doc_rules.RETIRED_TERMS`）一个不留，两份清单逐词同源。
另外 owner 表与页面文件一一对应：表里列的页必须存在、目录里的页必须登记，差集法两向都查。
图统一用 archify（ADR 0045 决策七）：`docs/diagrams/` 里 JSON 图源与导出 SVG 成对入库、图源零内部指代；
正文不再有 ```mermaid 块（两套图形态并存即漂移的开始）。
`test_default_model_ids_match_the_engine_constants` 的扫描面多带上随包 agent skill：默认模型 id 的披露面
横跨用户文档与 skill，真值在引擎常量，两边一起对着常量校才是完整差集（ADR 0044「现值」）。
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
from _doc_rules import (COLLOQUIAL, FORBIDDEN, REPO, RETIRED_TERMS, RETIRED_TERMS_WORDS,
                        changelog_unreleased, skill_markdown_files)

USER_GUIDE = REPO / "docs" / "user-guide"
DIAGRAMS = REPO / "docs" / "diagrams"
ALL_DOCS = [REPO / "README.md", REPO / "CONTRIBUTING.md"] + sorted((REPO / "docs").rglob("*.md"))
USER_DOCS = sorted(USER_GUIDE.glob("*.md")) + [REPO / "README.md", REPO / "CHANGELOG.md"]

LINK = re.compile(r"\]\(([^)\s]+)\)")
BUILDER_ONLY = re.compile(r"(^|/)(docs/adr|docs/journey|docs/ai-eng)(/|$)|(^|/)(CONTEXT\.md|CLAUDE\.md)$")


def _rel(p: Path) -> str:
    return str(p.relative_to(REPO))


@pytest.mark.parametrize("doc", USER_DOCS, ids=_rel)
def test_user_doc_has_no_internal_references(doc: Path):
    """内部指代扫全篇；口头语 / 用词表（含量词「档」）在 CHANGELOG 上只扫未发布段。

    豁免理由见 `_doc_rules.changelog_unreleased`：已发行节是发行当时的原话，不回溯改写。
    """
    text = doc.read_text(encoding="utf-8")
    scanned = changelog_unreleased(text) if doc.name == "CHANGELOG.md" else text
    cutoff = len(scanned.splitlines())  # 口头语表扫到这一行为止（截断保前缀，故行号与原文一致）
    hits = [f"{_rel(doc)}:{i}: {line.strip()[:120]}" for i, line in enumerate(text.splitlines(), 1)
            if FORBIDDEN.search(line) or (i <= cutoff and COLLOQUIAL.search(line))]
    assert not hits, "用户文档面向使用者：不写 ADR 编号 / 决策号 / 内部机制名 / 口头语：\n" + "\n".join(hits)


@pytest.mark.parametrize("doc", USER_DOCS, ids=_rel)
def test_user_doc_uses_current_terminology(doc: Path):
    """退役旧名一个不留：词表给了规范名的旧词若留在使用者面，同一概念在文档里就有两个名字。

    CHANGELOG 只查「未发布」段（见 `_doc_rules.changelog_unreleased`）——已发行节是发行当时的原话。
    """
    text = doc.read_text(encoding="utf-8")
    scanned = changelog_unreleased(text) if doc.name == "CHANGELOG.md" else text
    hits = [f"{_rel(doc)}:{i}: {line.strip()[:120]}" for i, line in enumerate(scanned.splitlines(), 1)
            if RETIRED_TERMS.search(line)]
    assert not hits, "用户文档里还有已退役的旧名，换成 CONTEXT.md 词表里的规范名：\n" + "\n".join(hits)


def test_retired_terms_are_all_in_the_glossary():
    """护栏的退役词表 ⊆ 词表各条的 `_Avoid_`：两份清单同源，禁词才有「规范名是什么」的出处。

    差集单向即够：`_Avoid_` 比护栏宽（不少旧名只在 AI 侧文档里留着、未列入使用者面禁词），
    反向差集会把那批正常项报成红。
    """
    glossary = REPO / "CONTEXT.md"
    avoid = [line for line in glossary.read_text(encoding="utf-8").splitlines() if line.startswith("_Avoid_")]
    assert avoid, "CONTEXT.md 里扫不到 `_Avoid_` 行——词表格式换了？先修扫描面，别让护栏空转"
    orphans = [w for w in RETIRED_TERMS_WORDS if not any(w in line for line in avoid)]
    assert not orphans, ("这些词在 `_doc_rules.RETIRED_TERMS_WORDS` 里禁着，但 CONTEXT.md 没有哪条把它列进 "
                         f"`_Avoid_`（先在词表对应条落下旧名，规范名才有出处）：{orphans}")


@pytest.mark.parametrize("doc", USER_DOCS, ids=_rel)
def test_user_doc_links_resolve_and_stay_in_user_land(doc: Path):
    text = doc.read_text(encoding="utf-8")
    broken, leaks = [], []
    for i, line in enumerate(text.splitlines(), 1):
        for target in LINK.findall(line):
            if re.match(r"[a-z][a-z0-9+.-]*:", target) or target.startswith("#"):
                continue  # 外部 URL / 页内锚点
            path_part = target.split("#", 1)[0]
            resolved = (doc.parent / path_part).resolve()
            if not resolved.exists():
                broken.append(f"{_rel(doc)}:{i}: {target}")
                continue
            if BUILDER_ONLY.search(str(resolved.relative_to(REPO)).replace("\\", "/")):
                leaks.append(f"{_rel(doc)}:{i}: {target}")
    assert not broken, "相对链接指向不存在的文件：\n" + "\n".join(broken)
    assert not leaks, "用户文档不把读者引到 contributor 侧 AI agent 的文档（ADR / CONTEXT / CLAUDE.md / journey / ai-eng）：\n" + "\n".join(leaks)


def test_user_guide_index_matches_directory():
    """owner 表（docs/user-guide/README.md）与目录里的页一一对应：两向差集。"""
    index = (USER_GUIDE / "README.md").read_text(encoding="utf-8")
    listed = set(re.findall(r"\]\(\./([a-z0-9-]+\.md)\)", index))
    present = {p.name for p in USER_GUIDE.glob("*.md")} - {"README.md"}
    assert listed == present, f"owner 表列了但目录没有：{sorted(listed - present)}；目录有但表里没登记：{sorted(present - listed)}"


def test_diagram_sources_and_exports_come_in_pairs():
    """docs/diagrams/<name>.json（图源）与 <name>.svg（导出）成对：缺任一半即漂（HTML 不入库，由 JSON 现场构建）。"""
    jsons = {p.stem for p in DIAGRAMS.glob("*.json")}
    svgs = {p.stem for p in DIAGRAMS.glob("*.svg")}
    assert jsons == svgs, f"有图源没导出：{sorted(jsons - svgs)}；有导出没图源：{sorted(svgs - jsons)}"
    assert (DIAGRAMS / "index.html").is_file(), "缺 docs/diagrams/index.html（Pages 站点首页）"


def test_published_interactive_html_is_tracked_and_indexed():
    """交互 HTML 只对发布到 Pages 的图入库：git 跟踪的每个 <name>.html 必须有同名图源，且在 index.html 里有链接
    （发布 = .gitignore 白名单 + index 链接 + HTML 入库，三者同 commit）。"""
    import subprocess
    tracked = subprocess.run(["git", "-C", str(REPO), "ls-files", "docs/diagrams/*.html"], capture_output=True, text=True, check=True).stdout.split()
    published = {Path(t).stem for t in tracked if Path(t).name != "index.html"}
    index = (DIAGRAMS / "index.html").read_text(encoding="utf-8")
    linked = set(re.findall(r'href="\./([a-z0-9-]+)\.html"', index))
    jsons = {p.stem for p in DIAGRAMS.glob("*.json")}
    assert published <= jsons, f"入库的交互 HTML 没有图源：{sorted(published - jsons)}"
    assert published == linked, f"入库了但 index.html 没链：{sorted(published - linked)}；index 链了但没入库：{sorted(linked - published)}"


@pytest.mark.parametrize("spec", sorted(DIAGRAMS.glob("*.json")), ids=lambda p: p.name)
def test_diagram_source_has_no_internal_references(spec: Path):
    """图源里的文字会原样进 SVG / 站点，读者含使用者：零 ADR 编号 / 决策号 / 内部机制名 / 退役旧名。"""
    text = spec.read_text(encoding="utf-8")
    hits = [f"{_rel(spec)}:{i}: {line.strip()[:120]}" for i, line in enumerate(text.splitlines(), 1)
            if FORBIDDEN.search(line) or COLLOQUIAL.search(line) or RETIRED_TERMS.search(line)]
    assert not hits, ("图源不得含内部指代、口头语 / 隐喻或退役旧名（图上的字读者直接看到，改图源后记得重导 SVG）：\n"
                      + "\n".join(hits))


def test_no_mermaid_blocks_remain():
    """图统一 archify：正文里不再有 ```mermaid 块（README / CONTRIBUTING / docs/**）。"""
    hits = [f"{_rel(doc)}:{i}" for doc in ALL_DOCS for i, line in enumerate(doc.read_text(encoding="utf-8").splitlines(), 1)
            if line.strip().startswith("```mermaid")]
    assert not hits, "仍有 mermaid 块，按 ADR 0045 决策七 转成 docs/diagrams 的 archify 图：\n" + "\n".join(hits)


@pytest.mark.parametrize("spec", sorted(DIAGRAMS.glob("*.json")), ids=lambda p: p.name)
def test_diagram_exports_match_their_sources(spec: Path):
    """导出的 SVG 末尾带 `gherkai:source-sha256=<sha256(json)>` 指纹（tools/build_diagrams.mjs 写入）：
    改了 JSON 图源没重导 SVG 在 CI 里就红（mtime 在 git checkout 后无意义，故用内容指纹）。"""
    import hashlib
    svg = spec.with_suffix(".svg")
    assert svg.is_file(), f"缺 {svg.name}"
    want = hashlib.sha256(spec.read_bytes()).hexdigest()
    tail = svg.read_bytes()[-200:].decode("utf-8", "replace")
    m = re.search(r"gherkai:source-sha256=([0-9a-f]{64})", tail)
    assert m, f"{svg.name} 末尾没有图源指纹——用 tools/build_diagrams.mjs 重导（不要手工改 SVG）"
    assert m.group(1) == want, f"{svg.name} 是旧图源导出的：运行 node tools/build_diagrams.mjs docs/diagrams/{spec.name}"


def test_diagram_skill_points_at_the_method():
    """作图入口 = 项目级 skill `.claude/skills/doc-diagram/SKILL.md`，它只指向方法文档 docs/ai-eng/diagram-authoring.md 与
    构建脚本，不复述规则（规则单一真源在方法文档；ADR 0045 决策七）。"""
    skill = REPO / ".claude" / "skills" / "doc-diagram" / "SKILL.md"
    method = REPO / "docs" / "ai-eng" / "diagram-authoring.md"
    assert skill.is_file() and method.is_file(), "缺作图 skill 入口或方法文档"
    body = skill.read_text(encoding="utf-8")
    assert "docs/ai-eng/diagram-authoring.md" in body and "tools/build_diagrams.mjs" in body, "skill 须指向方法文档与构建脚本"
    assert body.count("\n") < 12, "skill 入口只放指令与指针（不复述方法，免同步漂移）"


# ── 默认模型 id：从 code 常量校用户面（ADR 0044「现值」）────────────────────────────────────

NOVA_CONSTANTS = REPO / "engines" / "novaact" / "gherkai_worker_novaact" / "lib" / "constants.py"
MIDSCENE_CONSTANTS = REPO / "engines" / "midscene" / "src" / "lib" / "agentcore-sigv4.mts"

# 模型 id 的书写形态，按引擎分。只认**完整 id**：Midscene 家族推断表里的片段（`openai.gpt-6` /
# `qwen.qwen3-vl`）与不带版本的别名（`nova-act-preview`）不是默认值的候选，进扫描面只会制造假红。
MODEL_ID_SHAPES = {
    "novaact": re.compile(r"nova-act-v[0-9][0-9a-z.-]*"),
    "midscene": re.compile(r"(?:us|eu|apac|global)\.openai\.[a-z0-9][a-z0-9.-]*"
                           r"|(?:(?:us|eu|apac|global)\.)?qwen\.qwen3-vl-[0-9a-z-]+"),
}
# 「这个 id 不是在讲默认」的框定词：替代值（换成 / 设为 / 例如）与历史值（原默认 / 曾 / 此前）。
NON_DEFAULT_MARKERS = re.compile(r"换成|换到|改成|设为|设成|原默认|原来的|此前|曾|不再|如\s*`")
_MARKER_WINDOW = 16          # 框定词只在紧贴 id 前的这么多字里才算（同一行更远处的词管的是别的 id）
_CLAUSE_END = re.compile(r"[，。；：|]")   # 从句边界：框定词管不过它（「、」是列举分隔、不切）
_LIST_SEP_ONLY = re.compile(r"[`、,，/或\s]*")  # 列举分隔符：`A`、`B` 里的 B 沿用 A 的框定


def _default_model_claims(line: str, shape: re.Pattern[str]) -> list[str]:
    """一行里被当成「默认模型」讲的那些 id。

    判据反着来——**没有非默认框定即算默认语境**：描述默认值的写法太多（「默认模型」「默认值是」
    「默认锁定」「改为」、表格里干脆只有一列表头写着默认），逐种正则必漏；替代值与历史值反而总带
    明确的框定词，枚举得完。漏判的方向因此是「多查一处」而不是「漏查一处」。
    """
    out, pos, framed = [], 0, False
    for m in shape.finditer(line):
        gap = line[pos:m.start()]
        near = _CLAUSE_END.split(gap)[-1][-_MARKER_WINDOW:]   # 同一从句内、紧贴 id 前的那一小段
        if NON_DEFAULT_MARKERS.search(near):
            framed = True
        elif not _LIST_SEP_ONLY.fullmatch(gap):
            framed = False       # 隔着实义文字 = 新的一句，框定不延续
        if not framed:
            out.append(m.group(0).rstrip(".-"))
        pos = m.end()
    return out


def _default_model_ids() -> dict[str, str]:
    """两引擎的默认模型 id = 各自 code 常量的缺省值（env 覆盖的那一半与文档无关）。"""
    nova = re.search(r"""MODEL_ID\s*=\s*os\.environ\.get\(\s*["']NOVA_MODEL_ID["']\s*,\s*["']([^"']+)["']""",
                     NOVA_CONSTANTS.read_text(encoding="utf-8"))
    midscene = re.search(r"""export const DEFAULT_MODEL\s*=\s*["']([^"']+)["']""",
                         MIDSCENE_CONSTANTS.read_text(encoding="utf-8"))
    assert nova and midscene, ("取不到引擎默认模型常量（常量写法变了？）——先修这里的抽取式，"
                              f"别让护栏空转：{_rel(NOVA_CONSTANTS)} / {_rel(MIDSCENE_CONSTANTS)}")
    return {"novaact": nova.group(1), "midscene": midscene.group(1)}


def test_default_model_ids_match_the_engine_constants():
    """换默认模型时漏改某份用户面文档即红：默认模型 id 的真值是引擎常量，披露面有十来处、靠人一次改齐。

    扫描面 = 用户文档（CHANGELOG 只扫未发布段，已发行节是发行当时的原话）+ 随包 agent skill；
    新增披露面（新页面、skill 新 reference）自动进面，不必维护清单。历史值与替代值由框定词放行，
    见 `_default_model_claims`。code 侧另有两引擎各自的单测把默认常量钉在字面量上作升级闸门
    （midscene 的 `DEFAULT_MODEL` 断言、nova 的 `--capabilities` 自报断言，换默认得连它们一起改），
    本护栏只管文档面跟上常量，两层不重叠。
    """
    defaults = _default_model_ids()
    surfaces: list[tuple[Path, str]] = []
    for doc in USER_DOCS:
        text = doc.read_text(encoding="utf-8")
        surfaces.append((doc, changelog_unreleased(text) if doc.name == "CHANGELOG.md" else text))
    skills = skill_markdown_files()
    surfaces += [(p, p.read_text(encoding="utf-8")) for p in skills]

    stale: list[str] = []
    stated: dict[str, set[Path]] = {engine: set() for engine in MODEL_ID_SHAPES}
    for path, text in surfaces:
        for i, line in enumerate(text.splitlines(), 1):
            for engine, shape in MODEL_ID_SHAPES.items():
                for model_id in _default_model_claims(line, shape):
                    if model_id == defaults[engine]:
                        stated[engine].add(path)
                    else:
                        stale.append(f"{_rel(path)}:{i}: {model_id}（{engine} 现默认 = {defaults[engine]}）: "
                                     f"{line.strip()[:100]}")
    assert not stale, ("这些地方把旧模型 id 当默认在讲（换默认时漏改，或该给它「原默认 / 换成 / 例如」的框定）：\n"
                       + "\n".join(stale))

    blind = [f"{engine} 的默认 id {defaults[engine]} 在{where}一处都没出现"
             for engine in MODEL_ID_SHAPES
             for where, group in (("用户文档", set(USER_DOCS)), ("随包 skill", set(skills)))
             if not (stated[engine] & group)]
    assert not blind, "护栏空转（默认模型 id 的披露面消失了？先确认是有意删除，再改扫描面）：\n" + "\n".join(blind)
