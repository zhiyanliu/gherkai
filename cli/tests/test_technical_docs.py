"""技术文档的措辞护栏（ADR 0045 决策一 / 六：CONTRIBUTING、各包 DEVELOPMENT、internals、工具手册是人读的技术说明）。

技术文档允许术语、允许 ADR 指针（所以不套 `FORBIDDEN`），不允许俏皮与口头语、退役旧名，也不允许决策六列的
ADR 式缩写（把 = 当谓语、「退 N」、自造复合词）。箭头表顺序与因果在这一层合法，不禁。扫描剥掉代码块与行内代码
（`_doc_rules.prose_lines`）——命令示例与配置片段本来就是符号。
"""
from __future__ import annotations

from pathlib import Path

import pytest
from _doc_rules import (COLLOQUIAL, NUMERIC_SHORTHAND, REPO, RETIRED_TERMS, SYMBOL_PREDICATE,
                        prose_lines)


def _technical_docs() -> list[Path]:
    docs = [REPO / "CONTRIBUTING.md", REPO / ".github" / "workflows" / "README.md",
            REPO / "docs" / "README.md", REPO / "core" / "tests" / "README.md", REPO / "skills" / "README.md",
            REPO / "engines" / "midscene" / "spikes" / "SIGV4-FETCH-RECIPE.md"]
    docs += sorted((REPO / "docs" / "internals").glob("*.md"))
    docs += sorted(REPO.glob("*/DEVELOPMENT.md")) + sorted(REPO.glob("engines/*/DEVELOPMENT.md"))
    docs += sorted((REPO / "tools").glob("*.md"))
    return sorted({p for p in docs if p.exists()})


def _rel(p: Path) -> str:
    return str(p.relative_to(REPO))


def test_scan_face_is_not_empty():
    docs = _technical_docs()
    assert REPO / "CONTRIBUTING.md" in docs and len(docs) >= 12, f"技术文档扫描面异常：{[_rel(p) for p in docs]}"


@pytest.mark.parametrize("doc", _technical_docs(), ids=_rel)
def test_technical_doc_uses_written_register(doc: Path):
    """正文无口头语 / 自造复合词、无退役旧名、不把 = 当谓语、不写「退 N」（代码块与行内代码不算）。"""
    hits = []
    for line_no, text in prose_lines(doc.read_text(encoding="utf-8")):
        if COLLOQUIAL.search(text):
            hits.append(f"{_rel(doc)}:{line_no}: 口头语或自造复合词 · {text.strip()[:110]}")
        if RETIRED_TERMS.search(text):
            hits.append(f"{_rel(doc)}:{line_no}: 退役旧名 · {text.strip()[:110]}")
        if SYMBOL_PREDICATE.search(text):
            hits.append(f"{_rel(doc)}:{line_no}: 符号当谓语 · {text.strip()[:110]}")
        if NUMERIC_SHORTHAND.search(text):
            hits.append(f"{_rel(doc)}:{line_no}: 省略中心词的「退 N」 · {text.strip()[:110]}")
    assert not hits, ("技术文档是人读层，按 ADR 0045 决策六写完整词与完整句（规范名见 CONTEXT.md）：\n"
                      + "\n".join(hits))
