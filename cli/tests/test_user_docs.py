"""仓库内用户文档的护栏：`docs/user-guide/**`、根 `README.md`、`CHANGELOG.md`（ADR 0045 决策一 / 六；产品面口径同 ADR 0039）。

这些页面在 GitHub 上渲染、有仓库上下文，所以**允许相对链接**——但每个相对链接必须指向真实存在的文件；
读者是使用者与替使用者操作的 agent，所以**零内部指代**（禁词表与包 README 共用同一张 `_doc_rules.FORBIDDEN`），
且不把读者引到 contributor 侧 AI agent 的文档（ADR / CONTEXT / CLAUDE.md / journey / ai-eng）——那些不是给他们读的。
用词还要跟上词表：`CONTEXT.md` 已给出规范名的旧名（`_doc_rules.RETIRED_TERMS`）一个不留，两份清单逐词同源。
另外 owner 表与页面文件一一对应：表里列的页必须存在、目录里的页必须登记，差集法两向都查。
图统一用 archify（ADR 0045 决策七）：`docs/diagrams/` 里 JSON 图源与导出 SVG 成对入库、图源零内部指代；
正文不再有 ```mermaid 块（两套图形态并存即漂移的开始）。
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
from _doc_rules import COLLOQUIAL, FORBIDDEN, RETIRED_TERMS, RETIRED_TERMS_WORDS, changelog_unreleased

REPO = Path(__file__).resolve().parents[2]
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
    text = doc.read_text(encoding="utf-8")
    hits = [f"{_rel(doc)}:{i}: {line.strip()[:120]}" for i, line in enumerate(text.splitlines(), 1)
            if FORBIDDEN.search(line) or COLLOQUIAL.search(line)]
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

