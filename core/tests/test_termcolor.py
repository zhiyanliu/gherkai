"""终端颜色开关的统一策略（gherkai_core.termcolor，ADR 0047）：环境变量优先于目标流是否终端，非空语义同 no-color.org。"""
from __future__ import annotations

from gherkai_core import termcolor


class _Tty:
    def isatty(self):
        return True


class _Pipe:
    def isatty(self):
        return False


def _clean_env(monkeypatch):
    for k in ("NO_COLOR", "FORCE_COLOR", "TERM"):
        monkeypatch.delenv(k, raising=False)


def test_stream_decides_when_no_env(monkeypatch):
    _clean_env(monkeypatch)
    assert termcolor.use_color(_Tty()) is True
    assert termcolor.use_color(_Pipe()) is False
    assert termcolor.use_color(None) is False


def test_no_color_non_empty_wins_over_tty(monkeypatch):
    _clean_env(monkeypatch)
    monkeypatch.setenv("NO_COLOR", "")           # 空值不算设了
    assert termcolor.use_color(_Tty()) is True
    monkeypatch.setenv("NO_COLOR", "1")
    assert termcolor.use_color(_Tty()) is False
    monkeypatch.setenv("FORCE_COLOR", "1")      # 同时设时 NO_COLOR 优先
    assert termcolor.use_color(_Tty()) is False


def test_term_dumb_disables(monkeypatch):
    _clean_env(monkeypatch)
    monkeypatch.setenv("TERM", "dumb")
    assert termcolor.use_color(_Tty()) is False


def test_force_color_enables_on_pipe(monkeypatch):
    _clean_env(monkeypatch)
    monkeypatch.setenv("FORCE_COLOR", "1")
    assert termcolor.use_color(_Pipe()) is True
    monkeypatch.setenv("FORCE_COLOR", "")
    assert termcolor.use_color(_Pipe()) is False


def test_broken_stream_counts_as_not_tty(monkeypatch):
    _clean_env(monkeypatch)

    class _Closed:
        def isatty(self):
            raise ValueError("I/O operation on closed file")

    assert termcolor.use_color(_Closed()) is False
