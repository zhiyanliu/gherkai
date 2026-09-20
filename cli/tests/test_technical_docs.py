"""技术文档的措辞与悬空指针护栏（ADR 0045 决策一 / 六：CONTRIBUTING、各包 DEVELOPMENT、internals、工具手册是人读的技术说明）。

技术文档允许术语、允许 ADR 指针（所以不套内部指代表），不允许俏皮与口头语、退役旧名，也不允许决策六列的 ADR 式缩写
（把 = 当谓语、「退 N」、自造复合词），不指 journey 文件与 WP 编号。箭头表顺序与因果在这一层合法，不禁。扫描剥掉代码块
与行内代码（`_doc_rules.prose_lines`）——命令示例与配置片段本来就是符号。规则束与扫描面在 `_doc_rules`（`scan("technical-doc", …)`），
hook 与提交闸门用同一束（ADR 0046）。
"""
from __future__ import annotations

from pathlib import Path

import pytest
from _doc_rules import REPO, scan, technical_docs


def _rel(p: Path) -> str:
    return str(p.relative_to(REPO))


def test_scan_face_is_not_empty():
    docs = technical_docs()
    assert REPO / "CONTRIBUTING.md" in docs and len(docs) >= 12, f"技术文档扫描面异常：{[_rel(p) for p in docs]}"


@pytest.mark.parametrize("doc", technical_docs(), ids=_rel)
def test_technical_doc_uses_written_register(doc: Path):
    """正文无口头语 / 自造复合词、无退役旧名、不把 = 当谓语、不写「退 N」、不指 journey 文件与 WP 编号（代码块与行内代码不算）。"""
    hits = [f"{_rel(doc)}:{line_no}: {label} · {text}" for line_no, label, text in scan("technical-doc", doc)]
    assert not hits, ("技术文档是人读层，按 ADR 0045 决策六写完整词与完整句（规范名见 CONTEXT.md）：\n"
                      + "\n".join(hits))
