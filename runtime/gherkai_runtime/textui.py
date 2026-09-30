"""人读输出的表格渲染（ADR 0047）：多行同结构的清单统一由这里出表，cli 与 deploy provider 两个前端包共用。

样式固定：圆角框线、无颜色、无高亮、不解析标记语法；宽度取终端列数（至少 80），非终端时取 160（日志与 CI
里避免无谓折行）。机读形态（`--json`）不经过这里。测试只断言单元格内容，不断言排版（同 ADR）。
"""
from __future__ import annotations

import io
import shutil
import sys
from typing import Iterable, Sequence

from rich import box
from rich.console import Console
from rich.table import Table


def render_table(headers: Sequence[str], rows: Iterable[Sequence[object]], *, width: int | None = None) -> str:
    """把表头与各行渲染成一段多行文本（末尾不带换行）。单元格按 `str()` 取值，None 显示为 `-`。"""
    table = Table(box=box.ROUNDED, show_header=True, header_style="", pad_edge=True)
    for h in headers:
        table.add_column(str(h), overflow="fold")
    for row in rows:
        table.add_row(*["-" if cell is None else str(cell) for cell in row])
    buf = io.StringIO()
    console = Console(file=buf, width=width or terminal_width(), no_color=True, highlight=False,
                      markup=False, emoji=False, force_terminal=False, color_system=None)
    console.print(table)
    return buf.getvalue().rstrip("\n")


def terminal_width() -> int:
    """标准输出是终端时取其列数（至少 80）；否则 160。"""
    if sys.stdout is not None and sys.stdout.isatty():
        return max(80, shutil.get_terminal_size((80, 24)).columns)
    return 160
