"""人读呈现件（ADR 0047）的单测：对齐、不折断标识、无 ANSI、颜色开关、标记不解析。排版细节只在这里锁，其它测试只断言内容。"""
import re
import unicodedata

import pytest

from gherkai_runtime import textui
from gherkai_runtime.textui import TreeNode, render_table, render_tree


@pytest.fixture(autouse=True)
def _presentation_is_environment_independent(monkeypatch):
    """人读渲染（ADR 0047）不随运行测试的终端变化：固定关色、表格不按终端取宽——否则 `pytest -s` 在真实终端里会因 ANSI 与折行假红。"""
    from gherkai_runtime import textui
    monkeypatch.setattr(textui, "use_color", lambda: False)
    monkeypatch.setattr(textui, "output_width", lambda: textui.NO_WRAP_WIDTH)


def _shown(line: str) -> int:
    return sum(2 if unicodedata.east_asian_width(ch) in "WF" else 1 for ch in line)


def test_cjk_headers_and_ascii_cells_align_by_display_width():
    text = render_table(["variant", "推送时间（UTC）", "revision"],
                        [["base", "2026-09-29 06:26", "vfy-novaact-worker:27"], ["demo", "2026-09-29 07:09", "vfy-novaact-worker:28"]],
                        width=120)
    lines = text.splitlines()
    assert len({_shown(l) for l in lines}) == 1, lines   # 每行显示宽度相同：中文表头按两格计
    assert "推送时间（UTC）" in text and "vfy-novaact-worker:28" in text


def test_identifier_columns_never_fold_but_wrap_columns_do():
    sid = "features/checkout_flow_long_name.feature:120:45"
    text = render_table(["scope_id", "说明"], [[sid, "很长的说明" * 12]], wrap=[1], width=70)
    assert sid in text                                    # 标识列整条在同一行
    lines = text.splitlines()
    assert sum(1 for l in lines if "说明" in l and "scope_id" not in l) > 1   # 说明列在格内折成多行
    assert all(_shown(l) <= 70 for l in lines), lines     # 折的是说明列，整表仍守住宽度


def test_no_ansi_when_stdout_is_not_a_tty_and_none_shows_dash():
    text = render_table(["a", "b"], [["x", None]], width=80)
    assert "\x1b[" not in text
    assert re.search(r"│\s*-\s*│", text), text


def test_markup_and_emoji_codes_in_user_text_render_literally():
    text = render_table(["step"], [['[red]Then[/] :smile: [link=http://x]y[/link]']], width=200)
    assert "[red]Then[/] :smile: [link=http://x]y[/link]" in text
    tree = TreeNode("[bold]根[/bold]"); tree.add("[0] Given 打开 \"http://a\"")
    out = render_tree(tree)
    assert "[bold]根[/bold]" in out and '[0] Given 打开 "http://a"' in out


def test_color_is_emitted_when_enabled_and_absent_when_disabled(monkeypatch):
    monkeypatch.setattr(textui, "use_color", lambda: True)
    colored = render_table(["状态"], [[textui.status_text("passed")]], width=40)
    assert "\x1b[" in colored and "passed" in re.sub(r"\x1b\[[0-9;]*m", "", colored)   # 去掉颜色后文字完整
    monkeypatch.setattr(textui, "use_color", lambda: False)
    plain = render_table(["状态"], [[textui.status_text("passed")]], width=40)
    assert "\x1b[" not in plain and "passed" in plain


def test_use_color_policy(monkeypatch):
    import sys
    monkeypatch.undo()   # 撤销 autouse 固定的关色，测真实策略
    tty = type("S", (), {"isatty": lambda self: True})()
    monkeypatch.setattr(sys, "stdout", tty)
    monkeypatch.delenv("NO_COLOR", raising=False); monkeypatch.delenv("TERM", raising=False)
    assert textui.use_color() is True
    monkeypatch.setenv("NO_COLOR", "")           # 空值不算设了（no-color.org 与 rich 的口径）
    assert textui.use_color() is True
    monkeypatch.setenv("NO_COLOR", "1")
    assert textui.use_color() is False
    monkeypatch.delenv("NO_COLOR"); monkeypatch.setenv("TERM", "dumb")
    assert textui.use_color() is False
    monkeypatch.delenv("TERM"); monkeypatch.setattr(sys, "stdout", type("S", (), {"isatty": lambda self: False})())
    assert textui.use_color() is False
    monkeypatch.setenv("FORCE_COLOR", "1")
    assert textui.use_color() is True                       # 非终端但 FORCE_COLOR：上色（如 | less -R）
    monkeypatch.delenv("FORCE_COLOR")
    assert textui.output_width() == textui.NO_WRAP_WIDTH   # 非终端：表格不折行


def test_tree_has_guide_lines_and_keeps_long_lines_unwrapped():
    root = TreeNode("运行结果")
    job = root.add("job 'a': passed")
    job.add("原因: " + "很长的原因" * 60)
    text = render_tree(root)
    assert "└── job 'a': passed" in text
    assert "原因: " + "很长的原因" * 60 in text      # 不折行：长行保持一行
    assert "\x1b[" not in text
