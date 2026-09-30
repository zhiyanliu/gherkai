"""人读表格渲染（ADR 0047）的单测：对齐、无 ANSI、宽度、None 显示。排版细节只在这里锁，其它测试只断言内容。"""
import re
import unicodedata

from gherkai_runtime.textui import render_table


def _shown(line: str) -> int:
    return sum(2 if unicodedata.east_asian_width(ch) in "WF" else 1 for ch in line)


def test_cjk_headers_and_ascii_cells_align_by_display_width():
    text = render_table(["variant", "推送时间（UTC）", "revision"],
                        [["base", "2026-09-29 06:26", "vfy-novaact-worker:27"], ["demo", "2026-09-29 07:09", "vfy-novaact-worker:28"]],
                        width=120)
    lines = text.splitlines()
    assert len({_shown(l) for l in lines}) == 1, lines   # 每行显示宽度相同：中文表头按两格计
    assert "推送时间（UTC）" in text and "vfy-novaact-worker:28" in text


def test_no_ansi_sequences_and_none_shows_dash():
    text = render_table(["a", "b"], [["x", None]], width=80)
    assert "\x1b[" not in text
    assert re.search(r"│\s*-\s*│", text), text


def test_width_parameter_bounds_the_table():
    text = render_table(["列"], [["很长的一段中文内容" * 6]], width=40)
    assert all(_shown(l) <= 40 for l in text.splitlines())
