"""人读输出的呈现件（ADR 0047）：表格、树、语义颜色，cli 与 deploy provider 两个前端包共用。

- 表格给「多行同结构」的清单，树给 job → scenario → step 这类层级；两者都不解析标记语法，用户文本原样呈现。
- 折行只发生在**终端里**且只折**说明类列**：标识列（scope_id、示例、模式、tag、地址）永不折断，说明列在终端宽度不够时
  在格内折行；标准输出不是终端（管道、日志、CI）时整张表不折行，每行保持一行。树在任何情况下都不折行。
- 颜色只作语义标记，映射沿用 ADR 0031 的视觉映射并翻译到终端基础 16 色：通过绿、失败红、出错紫红、中止亮红、跳过淡显、
  运行中青、待执行蓝；符号与文字仍是信息的主载体。标准输出不是终端、或 `NO_COLOR` 为非空值、或 `TERM=dumb` 时不发任何
  ANSI 序列；`FORCE_COLOR` 为非空值时反之。机读形态（`--json`）不经过这里。
- 已知限制：框线与引导线是东亚宽度歧义字符，把歧义字符设为双宽的终端会错位；老式 Windows 控制台未开 VT 时会显示原始转义码。
"""
from __future__ import annotations

import io
import os
import shutil
import sys

from gherkai_core.termcolor import color_env_override
from typing import Iterable, Sequence

from rich import box
from rich.console import Console
from rich.table import Table
from rich.text import Text
from rich.tree import Tree

__all__ = ["Text", "TreeNode", "render_table", "render_tree", "status_text", "styled", "plain", "use_color", "output_width"]

# 判定 / 状态词 → 颜色（ADR 0031 决定二「视觉映射」在终端基础色上的翻译）。未列出的按默认色。
STATUS_STYLE = {
    "passed": "green", "failed": "red", "error": "magenta", "aborted": "bright_red", "skipped": "dim",
    "running": "cyan", "pending": "blue",
}
DIM = "dim"
NO_WRAP_WIDTH = 100_000  # 不折行时给控制台的名义宽度（树恒用它；表格在非终端时用它）


def use_color() -> bool:
    """标准输出上的人读输出要不要带颜色：`NO_COLOR` 为非空值或 `TERM=dumb` → 不上色；`FORCE_COLOR` 为非空值 → 上色
    （如 `| less -R`）；否则看标准输出是否为终端。策略与 worker 日志前缀共用一份（`gherkai_core.termcolor`）。"""
    override = color_env_override()
    if override is not None:
        return override
    return _stdout_is_tty()


def _stdout_is_tty() -> bool:
    out = sys.stdout
    try:
        return out is not None and out.isatty()
    except (AttributeError, ValueError):
        return False


def output_width() -> int:
    """表格用的宽度：标准输出是终端时取其实际列数（取不到时 80；窄终端也按实际列数，让 rich 自行收窄），否则不折行。"""
    if _stdout_is_tty():
        return max(20, shutil.get_terminal_size((80, 24)).columns)
    return NO_WRAP_WIDTH


def plain(text: object) -> Text:
    """用户文本原样呈现（不解析标记语法）；None 显示为 `-`。"""
    return Text("-" if text is None else str(text))


def styled(text: object, style: str) -> Text:
    return Text(str(text), style=style)


def status_text(status: object) -> Text:
    """判定 / 状态词按语义上色；颜色关掉时就是原文。"""
    s = "-" if status is None else str(status)
    return Text(s, style=STATUS_STYLE.get(s, ""))


def _as_text(label: object) -> Text:
    return label if isinstance(label, Text) else plain(label)


def _console(buf: io.StringIO, width: int) -> Console:
    color = use_color()
    return Console(file=buf, width=width, force_terminal=color, color_system="standard" if color else None,
                   no_color=not color, highlight=False, markup=False, emoji=False)


def render_table(headers: Sequence[object], rows: Iterable[Sequence[object]], *,
                 wrap: Sequence[int] = (), width: int | None = None) -> str:
    """表头与各行 → 一段多行文本（末尾不带换行）。

    `wrap` 列出允许在格内折行的列下标（说明类长文本）；其余列是标识列，永不折断。单元格可给字符串或已上色的
    Text；None 显示为 `-`。`width` 不给时按 `output_width()`（终端取列数，非终端不折行）。
    """
    table = Table(box=box.ROUNDED, show_header=True, header_style="", pad_edge=True)
    for i, h in enumerate(headers):
        if i in wrap:
            table.add_column(_as_text(h), overflow="fold")
        else:
            table.add_column(_as_text(h), no_wrap=True, overflow="ignore")
    for row in rows:
        table.add_row(*[_as_text(cell) for cell in row])
    buf = io.StringIO()
    _console(buf, width or output_width()).print(table)
    return buf.getvalue().rstrip("\n")


class TreeNode:
    """树的一个节点：`label` 是字符串或 Text，`add()` 返回子节点以便继续挂。"""

    def __init__(self, label: object) -> None:
        self.label = label
        self.children: list[TreeNode] = []

    def add(self, label: object) -> "TreeNode":
        node = TreeNode(label)
        self.children.append(node)
        return node

    def find(self, needle: str) -> "TreeNode | None":
        """深度优先找第一个 label 含 needle 的节点（测试与诊断用）。"""
        if needle in str(self.label):
            return self
        for c in self.children:
            hit = c.find(needle)
            if hit is not None:
                return hit
        return None


def render_tree(root: TreeNode) -> str:
    """层级结构 → 带引导线的多行文本（末尾不带换行）。不折行：长的地址、原因、推理文本保持一行、由终端自行软换行，
    与此前纯文本一致，产物地址复制不会被截断（Tree 的 label 按控制台宽度硬折，故给一个远超任何终端的名义宽度）。
    多行 label 的续行对齐到 label 起点、带引导线。"""
    tree = Tree(_as_text(root.label), guide_style=DIM)

    def walk(node: TreeNode, branch: Tree) -> None:
        for child in node.children:
            walk(child, branch.add(_as_text(child.label)))

    walk(root, tree)
    buf = io.StringIO()
    _console(buf, NO_WRAP_WIDTH).print(tree)
    return buf.getvalue().rstrip("\n")
