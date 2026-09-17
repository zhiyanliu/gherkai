"""仓库内用户文档的护栏：`docs/user-guide/**`、根 `README.md`、`CHANGELOG.md`（ADR 0045 决策一 / 六；产品面口径同 ADR 0039）。

这些页面在 GitHub 上渲染、有仓库上下文，所以**允许相对链接**——但每个相对链接必须指向真实存在的文件；
读者是使用者与替使用者操作的 agent，所以**零内部指代**（禁词表与包 README 共用同一张 `_doc_rules.FORBIDDEN`），
且不把读者引到建造者 AI 的文档（ADR / CONTEXT / CLAUDE.md / journey / ai-eng）——那些不是给他们读的。
另外 owner 表与页面文件一一对应：表里列的页必须存在、目录里的页必须登记，差集法两向都查。
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
from _doc_rules import FORBIDDEN

REPO = Path(__file__).resolve().parents[2]
USER_GUIDE = REPO / "docs" / "user-guide"
USER_DOCS = sorted(USER_GUIDE.glob("*.md")) + [REPO / "README.md", REPO / "CHANGELOG.md"]

LINK = re.compile(r"\]\(([^)\s]+)\)")
BUILDER_ONLY = re.compile(r"(^|/)(docs/adr|docs/journey|docs/ai-eng)(/|$)|(^|/)(CONTEXT\.md|CLAUDE\.md)$")
COLLOQUIAL = re.compile(r"帽子不是人|烧钱|锁步|lockstep")  # 已定改掉的口头语 / 隐喻 / 晦涩术语（ADR 0045 决策六）


def _rel(p: Path) -> str:
    return str(p.relative_to(REPO))


@pytest.mark.parametrize("doc", USER_DOCS, ids=_rel)
def test_user_doc_has_no_internal_references(doc: Path):
    text = doc.read_text(encoding="utf-8")
    hits = [f"{_rel(doc)}:{i}: {line.strip()[:120]}" for i, line in enumerate(text.splitlines(), 1)
            if FORBIDDEN.search(line) or COLLOQUIAL.search(line)]
    assert not hits, "用户文档面向使用者：不写 ADR 编号 / 决策号 / 内部机制名 / 口头语：\n" + "\n".join(hits)


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
    assert not leaks, "用户文档不把读者引到建造者 AI 的文档（ADR / CONTEXT / CLAUDE.md / journey / ai-eng）：\n" + "\n".join(leaks)


def test_user_guide_index_matches_directory():
    """owner 表（docs/user-guide/README.md）与目录里的页一一对应：两向差集。"""
    index = (USER_GUIDE / "README.md").read_text(encoding="utf-8")
    listed = set(re.findall(r"\]\(\./([a-z0-9-]+\.md)\)", index))
    present = {p.name for p in USER_GUIDE.glob("*.md")} - {"README.md"}
    assert listed == present, f"owner 表列了但目录没有：{sorted(listed - present)}；目录有但表里没登记：{sorted(present - listed)}"
