"""ADR、journey 与长期文档的机械卫生项（CLAUDE.md 文档纪律里能逐行判定的那几条，此前每轮 doc-health 靠人查）。

- 每篇 ADR 第 3 行是标准 Status 头，枚举只有 Accepted / Superseded-by / Partially-superseded-by / Draft / Historical；
- 「被取代」链双向：Status 头点名 NNNN，NNNN 那篇必须回指本篇编号（doc-health 第 7 轮曾一轮三处同犯反向链缺口）；
- `docs/` 下文件名全是英文 kebab-case，`docs/adr/` 与 `docs/journey/` 带四位编号且各自不复用；
- `docs/journey/` 每份首行声明 `> 类型:`；
- 长期文档与 AI 侧文档不指向具体的 journey 文件、不写裸 WP 编号（悬空指针红线）；AI 侧文档也不用决策六形态②的自造复合词。
规则与扫描面在 `_doc_rules`；同一束由 hook 在写完即查（ADR 0046）。
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest
from _doc_rules import REPO, ai_side_docs, long_term_docs, prose_lines, scan, BARE_WP, DANGLING_JOURNEY

ADR_DIR = REPO / "docs" / "adr"
JOURNEY_DIR = REPO / "docs" / "journey"
STATUS = re.compile(r"^> \*\*Status:\*\* (Accepted|Draft|Historical|Superseded-by|Partially-superseded-by)\b")
NUMBERED = re.compile(r"^\d{4}-[a-z0-9]+(?:-[a-z0-9]+)*\.md$")
KEBAB = re.compile(r"^[a-z0-9]+(?:[.-][a-z0-9]+)*\.(md|json|svg|html|png)$")
# 约定俗成的全大写入口文件（CLAUDE.md 文档纪律「文档文件名」条的唯一例外）。
UPPER_OK = {"README.md", "REFERENCES.md"}


def _rel(p: Path) -> str:
    return str(p.relative_to(REPO))


def _adrs() -> list[Path]:
    return sorted(ADR_DIR.glob("*.md"))


def _status_line(adr: Path) -> str:
    lines = adr.read_text(encoding="utf-8").splitlines()
    return lines[2] if len(lines) > 2 else ""


@pytest.mark.parametrize("adr", _adrs(), ids=lambda p: p.name[:4])
def test_adr_has_standard_status_head(adr: Path):
    line = _status_line(adr)
    assert STATUS.match(line), f"{adr.name} 第 3 行不是标准 Status 头（Accepted / Superseded-by NNNN / Partially-superseded-by NNNN / Draft / Historical）：{line[:80]!r}"


def _superseders(status_line: str) -> list[str]:
    """Status 头里点名的取代方编号（只看 superseded-by 之后、到第一个注解分隔符为止那一段）。"""
    m = re.search(r"superseded-by\s+(.*)$", status_line, re.I)
    if not m:
        return []
    head = re.split(r"——|—|（|\(|：|:", m.group(1), maxsplit=1)[0]
    return re.findall(r"\b(\d{4})\b", head)


@pytest.mark.parametrize("adr", _adrs(), ids=lambda p: p.name[:4])
def test_superseded_links_are_bidirectional(adr: Path):
    """被取代方点了谁，谁就得回指它——机械差集，不靠读。"""
    mine = adr.name[:4]
    missing = []
    for other in _superseders(_status_line(adr)):
        targets = sorted(ADR_DIR.glob(f"{other}-*.md"))
        if not targets:
            missing.append(f"{adr.name} 的 Status 头指向不存在的 ADR {other}")
            continue
        text = targets[0].read_text(encoding="utf-8")
        if not re.search(rf"\b{mine}\b", text):
            missing.append(f"{adr.name} 被 {targets[0].name} 取代，但后者全文没有回指 {mine}（反向链缺口）")
    assert not missing, "\n".join(missing)


def _tracked_docs() -> list[str]:
    out = subprocess.run(["git", "ls-files", "docs"], cwd=REPO, check=True, capture_output=True, text=True).stdout
    return out.split()


def test_docs_filenames_are_kebab_case():
    bad = []
    for rel in _tracked_docs():
        name = Path(rel).name
        if name in UPPER_OK:
            continue
        if rel.startswith(("docs/adr/", "docs/journey/")):
            if not NUMBERED.match(name):
                bad.append(rel)
        elif not KEBAB.match(name):
            bad.append(rel)
    assert not bad, "docs/ 下文件名须是英文 kebab-case（ADR / journey 带四位编号）：\n" + "\n".join(bad)


@pytest.mark.parametrize("folder", ["adr", "journey"])
def test_numbered_docs_do_not_reuse_numbers(folder: str):
    d = REPO / "docs" / folder
    if not d.exists():
        return
    seen: dict[str, str] = {}
    dup = []
    for p in sorted(d.glob("*.md")):
        n = p.name[:4]
        if n in seen:
            dup.append(f"{folder}/{p.name} 与 {seen[n]} 编号重复")
        seen[n] = p.name
    assert not dup, "\n".join(dup)


def test_journey_files_declare_their_type():
    if not JOURNEY_DIR.exists():
        return
    bad = [p.name for p in sorted(JOURNEY_DIR.glob("*.md"))
           if not p.read_text(encoding="utf-8").lstrip().startswith("> 类型:")]
    assert not bad, "docs/journey/ 里每份首行要有 `> 类型:` 头（进度总纲 / 调查记录 / 待批报告 …）：" + ", ".join(bad)


@pytest.mark.parametrize("doc", long_term_docs(), ids=_rel)
def test_long_term_docs_have_no_dangling_pointers(doc: Path):
    """长期文档只指稳定物：不链具体的 journey 文件、不写裸 WP 编号（代码块与行内代码不算）。"""
    hits = [f"{_rel(doc)}:{i}: {line.strip()[:110]}" for i, line in prose_lines(doc.read_text(encoding="utf-8"))
            if DANGLING_JOURNEY.search(line) or BARE_WP.search(line)]
    assert not hits, "长期文档里的悬空指针（吸收后即断）——把证据内联、血缘写成自明的事件描述：\n" + "\n".join(hits)


@pytest.mark.parametrize("doc", ai_side_docs(), ids=_rel)
def test_ai_side_docs_avoid_coined_compounds(doc: Path):
    """AI 侧文档口吻放开，但决策六形态②的自造复合词全仓不用（歧义不是效率）；讨论这些词本身的文档除外。"""
    hits = [f"{_rel(doc)}:{line_no}: {label} · {text}" for line_no, label, text in scan("ai-doc", doc)]
    assert not hits, "\n".join(hits)
