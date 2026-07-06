"""EventSink 单测（Nova，ADR 0024 I/O 边缘可注入接口第一期）：subprocess 态写 EVENTS_FD fd + 回落 + 保序 + 中文。

这三条 fd 逻辑此前内联在 run_scope、无测试覆盖（绿≠对：EVENTS_FD 回落/ensure_ascii/每条 flush 保序都没被测）。
不连真 AWS、不起子进程。
"""
import io
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib.event_sink import EventSink


def test_emit_writes_jsonline_to_injected_fd(tmp_path, monkeypatch):
    # subprocess 态：EVENTS_FD 指向一个真 fd，emit 写 JSON Lines 到它。
    f = tmp_path / "events.jsonl"
    fd = os.open(str(f), os.O_WRONLY | os.O_CREAT | os.O_TRUNC)
    monkeypatch.setenv("EVENTS_FD", str(fd))
    sink = EventSink.from_env()
    sink.emit({"type": "scope_started", "scopeId": "s:0"})
    sink.emit({"type": "scope_done", "scopeId": "s:0"})
    # 读回：两行、各是一个事件、顺序保持（每条 flush）
    lines = f.read_text(encoding="utf-8").strip().split("\n")
    assert [json.loads(x)["type"] for x in lines] == ["scope_started", "scope_done"]


def test_emit_preserves_chinese_ensure_ascii_false(tmp_path, monkeypatch):
    # ensure_ascii=False 保中文（与旧内联 emit 逐字节一致）——若漏设会写成 \uXXXX。
    f = tmp_path / "ev.jsonl"
    fd = os.open(str(f), os.O_WRONLY | os.O_CREAT | os.O_TRUNC)
    monkeypatch.setenv("EVENTS_FD", str(fd))
    EventSink.from_env().emit({"message": "断言未过"})
    raw = f.read_text(encoding="utf-8")
    assert "断言未过" in raw            # 原样中文
    assert "\\u" not in raw             # 没被转义


def test_from_env_falls_back_to_stdout_when_no_events_fd(monkeypatch, capsys):
    # 无 EVENTS_FD（手动直跑）→ 回落 stdout，便于调试。
    monkeypatch.delenv("EVENTS_FD", raising=False)
    EventSink.from_env().emit({"type": "scope_started"})
    assert '"scope_started"' in capsys.readouterr().out


def test_from_env_falls_back_to_stdout_on_invalid_events_fd(monkeypatch, capsys):
    # EVENTS_FD 非法（int() 失败，ValueError 分支）→ 回落 stdout（既有 try/except 兜底，别崩）。
    monkeypatch.setenv("EVENTS_FD", "not-a-number")
    EventSink.from_env().emit({"type": "scope_done"})
    assert '"scope_done"' in capsys.readouterr().out


def test_from_env_falls_back_to_stdout_on_bad_fd_number(monkeypatch, capsys):
    # EVENTS_FD 是合法整数但非法 fd（fdopen 抛 OSError 分支——区别于上面的 int() ValueError）→ 同样回落 stdout。
    monkeypatch.setenv("EVENTS_FD", "999999")  # 数字合法、但该 fd 未打开 → os.fdopen 抛 OSError
    EventSink.from_env().emit({"type": "scope_done"})
    assert '"scope_done"' in capsys.readouterr().out


def test_sqs_url_injected_raises_not_silently_fd(monkeypatch):
    # SQS 态守卫（Fargate 化未实现，对称 JobSource）：注入 EVENTS_SQS_URL → from_env fail-loud 抛，不静默走
    # fd/stdout（否则 Fargate 事件写进无人读的 fd、静默丢）。锁死守卫不被误删。
    import pytest
    monkeypatch.setenv("EVENTS_SQS_URL", "https://sqs.us-east-1.amazonaws.com/x/q.fifo")
    with pytest.raises(NotImplementedError, match="SQS 态未实现"):
        EventSink.from_env()


def test_empty_sqs_url_treated_as_unset(monkeypatch, capsys):
    # 空串 EVENTS_SQS_URL 当「未注入」（or None）→ 正常走 fd/stdout、不误抛。
    monkeypatch.setenv("EVENTS_SQS_URL", "")
    monkeypatch.delenv("EVENTS_FD", raising=False)
    EventSink.from_env().emit({"type": "scope_started"})  # 不抛
    assert '"scope_started"' in capsys.readouterr().out


def test_emit_flushes_each_event():
    # 每条 flush（ADR 0024 顺序不变量）：用可观察 flush 的假流验证 emit 后立即 flush。
    flushed = []
    fake = io.StringIO()
    fake.flush = lambda: flushed.append(fake.getvalue())  # type: ignore[method-assign]
    sink = EventSink(out=fake)
    sink.emit({"type": "step_started"})
    sink.emit({"type": "step_done"})
    assert len(flushed) == 2  # 两次 emit 各 flush 一次（不攒 buffer）
