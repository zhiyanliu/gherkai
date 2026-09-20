"""repo 内 code 注释与 docstring 的措辞与悬空指针护栏（ADR 0045 决策六：注释与 docstring 是人读层；ADR 0046 三层护栏的测试层）。

注释随 code 长期存在、读者是 contributor，此前却不在任何护栏的扫描面内——用户可见字符串归 `test_user_facing_messages.py`、
文档归 `test_user_docs.py` / `test_skill.py` / `test_package_readmes.py`，注释层的退役旧名、口头语与 ADR 式缩写只能靠
定期复盘用人眼找（code-health 第 5 轮一次抓出约 50 处退役名、约 600 处缩写）。规则束、扫描面与抽取器都在
`_doc_rules`（`scan("code", …)`）：口吻表（含决策六形态②的自造复合词）、退役名（去掉与 Stream 事件批同形的「批」义三词）、
决策六形态①③的启发式、指向 journey 文件的链接与裸 WP 编号。同一束规则由 hook 在写完即查（`.claude/hooks/wording-guard.sh`）
与提交前再查（`commit-gate.sh`），本文件是 CI 兜底。箭头不在此禁：注释里表顺序与因果合法。
"""
from __future__ import annotations

from pathlib import Path

import pytest
from _doc_rules import REPO, code_comment_files, scan


def _rel(p: Path) -> str:
    return str(p.relative_to(REPO))


def test_scan_face_is_not_empty():
    files = code_comment_files()
    assert len(files) > 100, f"扫描面只剩 {len(files)} 个文件——目录搬家了？先修 _doc_rules.PY_ROOTS_FOR_COMMENTS，别让护栏空转"


@pytest.mark.parametrize("path", code_comment_files(), ids=_rel)
def test_comments_follow_the_written_register(path: Path):
    """注释与 docstring：无口头语 / 自造复合词、无退役旧名、不把 = 当谓语、不写「退 N」、不指 journey 文件与 WP 编号。"""
    hits = [f"{_rel(path)}:{line_no}: {label} · {text}" for line_no, label, text in scan("code", path)]
    assert not hits, ("注释与 docstring 是人读层，按 ADR 0045 决策六写完整词与完整句（规范名见 CONTEXT.md）：\n"
                      + "\n".join(hits))
