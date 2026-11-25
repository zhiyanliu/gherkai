"""发出事件之前对说明与设备描述的截断（ADR 0024「字段语义」节「单条事件的大小」条）。

规则由跨语言夹具 `engines/fixtures/event-truncation-cases.json` 锁住，Midscene 的 `lib/event-bounds.mts` 的测试读同一个文件、逐条相等；
本文件另核对按真实上限的边界、事件出口的两种通道与 `message` 截断时写进 worker 日志的完整文字。
"""
from __future__ import annotations

import io
import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from gherkai_worker_novaact import run_scope as rs
from gherkai_worker_novaact.lib.event_bounds import (
    DEVICE_FIELD_MAX_BYTES, MESSAGE_MAX_BYTES, bound_event, bound_text, utf8_bytes,
)
from gherkai_worker_novaact.lib.event_sink import EventSink
from gherkai_worker_novaact.lib.redact import redact_secrets

_FIXTURE = json.loads((Path(__file__).resolve().parents[2] / "fixtures" / "event-truncation-cases.json")
                      .read_text(encoding="utf-8"))


def _size(text: str) -> int:
    return len(text.encode("utf-8"))


# ---- 跨语言夹具 ----
def test_limits_match_cross_language_fixture():
    assert _FIXTURE["limits"] == {"message_bytes": MESSAGE_MAX_BYTES, "device_field_bytes": DEVICE_FIELD_MAX_BYTES}


def test_bound_text_matches_cross_language_fixture():
    assert _FIXTURE["texts"]
    for c in _FIXTURE["texts"]:
        got = bound_text(c["input"], c["max"])
        assert got == c["expected"], (c["input"], c["max"])
        assert _size(got) <= c["max"], c
        assert redact_secrets(got) == got, c   # 出口对整行再脱敏一次不会把它加长


def test_bound_event_matches_cross_language_fixture():
    assert _FIXTURE["events"]
    for c in _FIXTURE["events"]:
        before = json.dumps(c["input"], sort_keys=True)
        assert bound_event(c["input"], _no_log) == c["expected"], c["input"]
        assert json.dumps(c["input"], sort_keys=True) == before, "传入的事件不被改动"


def _no_log(msg: str) -> None:
    raise AssertionError(f"说明没有超出上限，不该写日志：{msg}")


# ---- 按真实上限的边界 ----
def _logs():
    lines: list[str] = []
    return lines, lines.append


def test_message_exactly_at_limit_is_kept_and_not_logged():
    msg = "x" * MESSAGE_MAX_BYTES
    assert bound_event({"type": "step_done", "message": msg}, _no_log)["message"] == msg


def test_message_one_byte_over_is_cut_and_full_text_logged():
    msg = "x" * (MESSAGE_MAX_BYTES + 1)
    lines, log = _logs()
    out = bound_event({"type": "step_done", "scenarioId": "f:3", "stepIndex": 2, "message": msg}, log)
    assert out["message"] == "x" * MESSAGE_MAX_BYTES
    assert len(lines) == 1 and lines[0].endswith(msg), lines
    assert "scenario f:3 的 step 2 的说明长 8193 字节" in lines[0], lines[0]


@pytest.mark.parametrize(("tail", "kept"), [("汉", MESSAGE_MAX_BYTES - 2), ("😀", MESSAGE_MAX_BYTES - 3), ("é", MESSAGE_MAX_BYTES - 1)])
def test_multibyte_char_across_the_limit_is_dropped_whole(tail, kept):
    """多字节字符压在 8192 字节的边界上：整个字符舍去，不出半个字符。"""
    msg = "x" * kept + tail + "尾"
    out = bound_event({"type": "scope_done", "scopeId": "s", "message": msg}, lambda _m: None)["message"]
    assert out == "x" * kept
    assert _size(out) <= MESSAGE_MAX_BYTES


def test_redacts_before_cutting_at_the_limit():
    """凭据跨过 8192 字节的边界：先截断会留下没有 @ 的「https://admin:hunt」，脱敏规则认不出，口令片段就出了 worker。"""
    secret = "https://admin:hunter2hunter2@h.example/login"
    msg = "x" * (MESSAGE_MAX_BYTES - 20) + secret
    lines, log = _logs()
    out = bound_event({"type": "step_done", "message": msg}, log)["message"]
    assert "admin" not in out and "hunter2" not in out, out[-40:]
    assert out == ("x" * (MESSAGE_MAX_BYTES - 20) + redact_secrets(secret))[:MESSAGE_MAX_BYTES]
    assert "hunter2" not in lines[0] and redact_secrets(secret) in lines[0], "日志里的完整文字同样已脱敏"


def test_redaction_shrinking_to_the_limit_means_no_cut_and_no_log():
    """原文超出上限、脱敏之后恰好等于上限：要不要截断与写日志按脱敏之后的长度判断，所以原样（已脱敏）发出、不写日志。"""
    secret = "https://admin:hunter2hunter2@h/"   # 脱敏之后短 17 字节
    msg = "x" * (MESSAGE_MAX_BYTES - _size(redact_secrets(secret))) + secret
    assert _size(msg) == MESSAGE_MAX_BYTES + 17
    out = bound_event({"type": "step_done", "scenarioId": "f:1", "stepIndex": 0, "message": msg}, _no_log)["message"]
    assert out == redact_secrets(msg) and _size(out) == MESSAGE_MAX_BYTES


def test_redaction_growing_over_the_limit_means_cut_and_log():
    """原文恰好等于上限、脱敏之后超出：截断，日志写一行，行尾是脱敏之后的全文。"""
    tail = "?X-Amz-Signature=a"   # 脱敏之后长 2 字节
    msg = "x" * (MESSAGE_MAX_BYTES - len(tail)) + tail
    assert _size(msg) == MESSAGE_MAX_BYTES
    lines, log = _logs()
    out = bound_event({"type": "scope_done", "scopeId": "s", "message": msg}, log)["message"]
    assert out == msg[:-len("=a")], out[-30:]   # 退到 `=` 之前，出口补回 `***` 时不超限
    assert len(lines) == 1 and lines[0].endswith(redact_secrets(msg)), lines
    assert f"scope s 的说明长 {MESSAGE_MAX_BYTES + 2} 字节" in lines[0], lines[0][:80]


def test_cut_inside_masked_value_backs_off_so_the_exit_redaction_stays_within_limit():
    """截断点正好落在 `X-Amz-Signature=` 之后：整行再脱敏会补回 `***`、超出上限 3 字节；截断改为退到 `=` 之前，补回之后不再超限。"""
    head = "x" * (MESSAGE_MAX_BYTES - len("?X-Amz-Signature="))
    out = bound_text(head + "?X-Amz-Signature=sig&a=1", MESSAGE_MAX_BYTES)
    assert out == head + "?X-Amz-Signature"
    assert _size(redact_secrets(out)) <= MESSAGE_MAX_BYTES


def test_non_string_message_is_converted_first():
    class Long:
        def __str__(self) -> str:
            return "原因" * 2000   # 12000 字节

    lines, log = _logs()
    out = bound_event({"type": "step_done", "message": Long()}, log)["message"]
    assert isinstance(out, str) and out == "原因" * 1365   # 再多一个字就是 8193 字节
    assert _size(out) == 8190 and len(lines) == 1


def test_device_model_and_os_version_cut_to_255_bytes():
    ev = {"type": "session_opened", "scopeId": "s", "sessionId": "arn", "name": "n", "origin": "created",
          "device": {"platform": "android", "model": "机" * 100, "osVersion": "1" * 256, "unit": "u" * 300}}
    out = bound_event(ev, _no_log)
    assert out["device"]["model"] == "机" * 85 and _size(out["device"]["model"]) == DEVICE_FIELD_MAX_BYTES
    assert out["device"]["osVersion"] == "1" * DEVICE_FIELD_MAX_BYTES
    assert out["device"]["unit"] == "u" * 300, "只截型号与系统版本"
    assert ev["device"]["model"] == "机" * 100, "传入的事件不被改动"
    exact = {**ev, "device": {**ev["device"], "model": "m" * DEVICE_FIELD_MAX_BYTES}}
    assert bound_event(exact, _no_log)["device"]["model"] == "m" * DEVICE_FIELD_MAX_BYTES


def test_lone_surrogate_counts_as_replacement_char():
    assert utf8_bytes("a\ud800") == "a\ufffd".encode("utf-8")


# ---- 事件出口：两种通道同一规则 ----
def _long_step_done() -> dict:
    return {"type": "step_done", "scenarioId": "f:1", "stepIndex": 0, "status": "failed", "errorType": "assertion_failed",
            "votes": {"yes": 0, "total": 1}, "message": "断言未过：" + "长" * 4000}


def test_fd_sink_bounds_message_and_logs_full_text():
    out = io.StringIO()
    lines, log = _logs()
    ev = _long_step_done()
    EventSink(out=out, log=log).emit(ev)
    sent = json.loads(out.getvalue())
    assert _size(sent["message"]) <= MESSAGE_MAX_BYTES and sent["message"].startswith("断言未过：长长")
    assert {k: v for k, v in sent.items() if k != "message"} == {k: v for k, v in ev.items() if k != "message"}
    assert ev["message"].endswith("长" * 10) and _size(ev["message"]) > MESSAGE_MAX_BYTES, "传入的事件不被改动"
    assert len(lines) == 1 and lines[0].endswith(ev["message"])


def test_ddb_sink_bounds_message_and_logs_full_text():
    lines, log = _logs()
    sink = EventSink(log=log, table_name="ev", run_id="r", scope_id="s")
    sink._client = MagicMock()
    sink.emit(_long_step_done())
    sink.emit({"type": "scope_done", "scopeId": "s", "status": "error", "errorType": "engine_error", "message": "y" * 9000})
    bodies = [json.loads(c.kwargs["Item"]["body"]) for c in sink._client.put_item.call_args_list]
    assert [_size(b["message"]) <= MESSAGE_MAX_BYTES for b in bodies] == [True, True]
    assert bodies[1]["message"] == "y" * MESSAGE_MAX_BYTES
    assert len(lines) == 2 and "scope s 的说明长 9000 字节" in lines[1]


def test_sink_exit_redaction_does_not_push_message_over_the_limit():
    """出口对整行的脱敏在截断之后执行：截在 `=` 之后时它会补回 `***`，sink 写出的说明仍在上限之内。"""
    out = io.StringIO()
    head = "x" * (MESSAGE_MAX_BYTES - len("?X-Amz-Signature="))
    EventSink(out=out, log=lambda _m: None).emit({"type": "step_done", "message": head + "?X-Amz-Signature=sig"})
    assert _size(json.loads(out.getvalue())["message"]) <= MESSAGE_MAX_BYTES


def test_deterministic_step_done_is_bounded_by_the_sink():
    """不经 evidence 的 step_done（确定性 step 带多行参数）直接 sink.emit：sink 这一处兜住，不漏。"""
    out = io.StringIO()
    lines, log = _logs()
    step = {"index": 0, "keyword": "Given", "text": '"https://example.com/' + "a" * 9000 + '"',
            "argument": {"type": "docString", "content": "x"}}
    assert rs._run_step(object(), "f:1", step, 1, EventSink(out=out, log=log)) == "error"
    done = [json.loads(x) for x in out.getvalue().splitlines()][-1]
    assert done["type"] == "step_done" and done["errorType"] == "engine_error"
    assert _size(done["message"]) <= MESSAGE_MAX_BYTES
    assert len(lines) == 1 and lines[0].endswith("a" * 100 + '"')
