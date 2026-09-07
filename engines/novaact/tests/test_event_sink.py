"""EventSink 单测（Nova，ADR 0024「I/O 边缘可注入接口」）：subprocess 态写 EVENTS_FD fd + 回落 + 保序 + 中文。

这三条 fd 逻辑此前内联在 run_scope、无测试覆盖（绿≠对：EVENTS_FD 回落/ensure_ascii/每条 flush 保序都没被测）。
不连真 AWS、不起子进程。
"""
import io
import json
import os
import time

from gherkai_worker_novaact.lib.event_sink import EventSink


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


def test_ddb_state_putitem(monkeypatch):
    # DDB 态（Fargate 化，ADR 0024）：注入 EVENTS_DDB_TABLE+RUN_ID+SCOPE_ID → emit = PutItem(PK=run_id#scope_id,
    # SK=自增 seq, body=json line)。mock DDB Table（MagicMock，不加 moto 依赖——对称 test_artifact_upload.py 惯例）。
    from unittest.mock import MagicMock

    monkeypatch.setenv("EVENTS_DDB_TABLE", "ev")
    monkeypatch.setenv("RUN_ID", "run-1")
    monkeypatch.setenv("SCOPE_ID", "browse")
    sink = EventSink.from_env()
    fake_table = MagicMock()
    sink._client = fake_table  # 绕惰性 _ddb() 建真 client
    sink.emit({"type": "scope_started", "scopeId": "browse"})
    sink.emit({"type": "scope_done", "scopeId": "browse"})
    items = [c.kwargs["Item"] for c in fake_table.put_item.call_args_list]
    # 两条、PK=run_id#scope_id、SK 自增 1/2、body 是原样 json line
    assert [it["pk"] for it in items] == ["run-1#browse", "run-1#browse"]
    assert [it["seq"] for it in items] == [1, 2]
    assert json.loads(items[0]["body"])["type"] == "scope_started"
    assert json.loads(items[1]["body"])["type"] == "scope_done"
    # expires_at = now+7d（epoch 秒，DDB TTL，ADR 0033）：范围断言避时钟脆——落在 [now+7d-60, now+7d+60]
    now = int(time.time())
    ttl_7d = 7 * 24 * 60 * 60
    for it in items:
        assert now + ttl_7d - 60 <= it["expires_at"] <= now + ttl_7d + 60


def test_ddb_state_binds_target_table_name(monkeypatch):
    # env→目标表接线（对称 Midscene event-sink.test.ts 断言 TableName=='ev'）：EVENTS_DDB_TABLE 必须真被用作
    # .Table(name) 的目标。上一条测试绕过了 _ddb()（直塞 _client），故表名接线无覆盖——若 _ddb() 绑错表名/读错
    # env 仍会绿、只有真跑才炸。这里 mock boto3.resource 让真 _ddb() 跑一遍、断言 .Table 以 "ev" 调用。
    import boto3
    from unittest.mock import MagicMock

    monkeypatch.setenv("EVENTS_DDB_TABLE", "ev")
    monkeypatch.setenv("RUN_ID", "run-1")
    monkeypatch.setenv("SCOPE_ID", "browse")
    fake_resource = MagicMock()
    monkeypatch.setattr(boto3, "resource", lambda *a, **kw: fake_resource)
    sink = EventSink.from_env()
    sink.emit({"type": "scope_started", "scopeId": "browse"})  # 走真 _ddb()：boto3.resource(...).Table("ev")
    fake_resource.Table.assert_called_once_with("ev")          # env 名确实绑成目标表
    fake_resource.Table.return_value.put_item.assert_called_once()


def test_empty_ddb_table_treated_as_unset(monkeypatch, capsys):
    # 空串 EVENTS_DDB_TABLE 当「未注入」（or None）→ 走 fd/stdout、不误进 DDB 态。
    monkeypatch.setenv("EVENTS_DDB_TABLE", "")
    monkeypatch.delenv("EVENTS_FD", raising=False)
    EventSink.from_env().emit({"type": "scope_started"})  # 不抛、走 stdout
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


def test_ddb_mode_missing_run_or_scope_id_fails_loud(monkeypatch):
    """DDB 态缺 RUN_ID/SCOPE_ID → 装配错误 fail-loud(否则事件静默写进 "None#None" 假 PK,run 永不收敛)。"""
    import pytest

    monkeypatch.setenv("EVENTS_DDB_TABLE", "t")
    monkeypatch.delenv("RUN_ID", raising=False)
    monkeypatch.setenv("SCOPE_ID", "s1")
    with pytest.raises(ValueError, match="RUN_ID/SCOPE_ID"):
        EventSink.from_env()
    monkeypatch.setenv("RUN_ID", "r1")
    monkeypatch.delenv("SCOPE_ID", raising=False)
    with pytest.raises(ValueError, match="RUN_ID/SCOPE_ID"):
        EventSink.from_env()
