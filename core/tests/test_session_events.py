"""会话事件与 scope 级 error 的协议红线（ADR 0051 决策 4、7；0024「会话事件」与「scope_done 的可选字段」；0034 机制二「退出信息」）。

本文件守 wire（JSON 行 → dataclass）、类别集差集、落盘往返三件事；归约与终结判定在 test_project / test_terminal 一侧。
"""
from __future__ import annotations

import json
from typing import get_args

import pytest

from gherkai_core.errors import WorkerExitError, WorkerNetworkError
from gherkai_core.model import (
    ErrorType,
    Job,
    JobResult,
    RunMeta,
    RunResult,
    Scenario,
    ScopeDone,
    SessionClosed,
    SessionOpened,
    SessionRecord,
    Status,
    Step,
)
from gherkai_core.serialize import from_dict, job_result_from_dict, job_result_to_dict, to_dict
from gherkai_core.wire import event_from_json, event_from_line, raise_for_worker_exit


# ---- wire：按 ADR 0024 的 camelCase 示例形状解析 ----

def test_session_opened_parses_all_origins_and_opaque_device():
    line = ('{"type":"session_opened","scopeId":"login","sessionId":"arn:aws:devicefarm:…","name":"gherkai:r1:ab12:1:login",'
            '"origin":"created","device":{"platform":"android","model":"Redmi Note 13","osVersion":"15","unit":"u1"}}')
    ev = event_from_line(line)
    assert isinstance(ev, SessionOpened)
    assert (ev.scope_id, ev.session_id, ev.name, ev.origin) == ("login", "arn:aws:devicefarm:…", "gherkai:r1:ab12:1:login", "created")
    assert ev.device == {"platform": "android", "model": "Redmi Note 13", "osVersion": "15", "unit": "u1"}  # 不透明原样搬运
    found = event_from_json({"type": "session_opened", "scopeId": "login", "name": "n", "origin": "discovered"})
    assert isinstance(found, SessionOpened) and found.session_id is None and found.device is None  # 孤儿会话：device 可缺
    tried = event_from_json({"type": "session_opened", "scopeId": "login", "sessionId": None, "name": "n", "origin": "attempted"})
    assert isinstance(tried, SessionOpened) and tried.session_id is None and tried.origin == "attempted"  # 结果未知的尝试只带名


def test_session_closed_keeps_null_observed_distinct_from_zero_and_carries_provider_minutes():
    base = {"type": "session_closed", "scopeId": "login", "sessionId": "arn:x", "name": "n", "release": "confirmed"}
    confirmed = event_from_json({**base, "observedS": 612.4, "providerMinutes": {"total": 11, "metered": 11, "unmetered": 0}})
    assert isinstance(confirmed, SessionClosed)
    assert confirmed.observed_s == 612.4 and confirmed.provider_minutes == {"total": 11, "metered": 11, "unmetered": 0}
    assert event_from_json({**base, "observedS": None}).observed_s is None  # null 保持 None、不改成 0（ADR 0051 决策 7）
    assert event_from_json({**base, "observedS": 0.0}).observed_s == 0.0
    assert event_from_json({**base}).observed_s is None and event_from_json({**base}).provider_minutes is None  # 两键可缺
    unconfirmed = event_from_json({**base, "sessionId": None, "release": "unconfirmed"})
    assert unconfirmed.session_id is None and unconfirmed.release == "unconfirmed"  # attempted 的尝试：只有名、未确认


@pytest.mark.parametrize("bad", [
    {"type": "session_opened", "scopeId": "s", "name": "n", "origin": "pending"},   # origin 不在枚举
    {"type": "session_opened", "scopeId": "s", "origin": "created"},                # 缺 name（sessionId 为 null 时它是配对键）
    {"type": "session_opened", "scopeId": "s", "name": "", "origin": "created"},    # name 空串
    {"type": "session_closed", "scopeId": "s", "name": "n", "release": "stopped"},  # release 不在枚举
    {"type": "session_closed", "scopeId": "s", "release": "confirmed"},             # 缺 name
])
def test_session_events_reject_unknown_enums_and_missing_pairing_key(bad):
    """core 会按 origin / release 分支、按 name 回退配对，故不认的取值与缺键按协议层 fail-loud（与未知事件类型同一口径）。"""
    with pytest.raises(ValueError):
        event_from_json(bad)


def test_scope_done_optional_fields_come_and_go_together():
    plain = event_from_json({"type": "scope_done", "scopeId": "s", "sessionId": "x"})
    assert isinstance(plain, ScopeDone) and (plain.status, plain.error_type, plain.message) == (None, None, None)  # 正常路径形态不变
    failed = event_from_json({"type": "scope_done", "scopeId": "s", "status": "error", "errorType": "acquire_timeout",
                              "message": "在等待时间内没有拿到可用设备 https://u:p@h.example/x"})
    assert failed.status == Status.ERROR and failed.error_type == "acquire_timeout"
    assert failed.message == "在等待时间内没有拿到可用设备 https://***@h.example/x"  # 与 step_done 同样脱敏（ADR 0035 决策 5）
    for partial in ({"status": "error"}, {"errorType": "precheck_failed"}, {"message": "m"},
                    {"status": "error", "errorType": "precheck_failed"}, {"status": "error", "message": "m"},
                    {"errorType": "precheck_failed", "message": "m"}):
        with pytest.raises(ValueError, match="同时出现或同时缺省"):
            event_from_json({"type": "scope_done", "scopeId": "s", **partial})
    with pytest.raises(ValueError, match="只允许"):
        event_from_json({"type": "scope_done", "scopeId": "s", "status": "passed", "errorType": "x", "message": "m"})
    for bad in (None, "", 7):  # 键在而值为 null / 空串 / 非字符串：scope 级 error 没有归因，与缺键同罪
        with pytest.raises(ValueError, match="errorType 须为非空字符串"):
            event_from_json({"type": "scope_done", "scopeId": "s", "status": "error", "errorType": bad, "message": "m"})
    nullmsg = event_from_json({"type": "scope_done", "scopeId": "s", "status": "error", "errorType": "precheck_failed", "message": None})
    assert (nullmsg.status, nullmsg.error_type, nullmsg.message) == (Status.ERROR, "precheck_failed", None)  # message 可为 null


def test_session_closed_observed_s_must_be_numeric_or_null():
    base = {"type": "session_closed", "scopeId": "s", "name": "n", "release": "confirmed"}
    assert event_from_json({**base, "observedS": None}).observed_s is None
    assert event_from_json({**base, "observedS": 12}).observed_s == 12
    assert event_from_json({**base, "observedS": 0.5}).observed_s == 0.5
    for bad in ("12", True, [1], {"s": 1}):
        with pytest.raises(ValueError, match="observedS 须为数值或 null"):
            event_from_json({**base, "observedS": bad})


def test_error_type_category_set_is_exactly_the_eleven_of_adr_0024():
    """差集护栏：类别集是原六项加设备目标五项（ADR 0024「errorType」条、0051 决策 4 类别表），用显式集合做相等断言。"""
    assert set(get_args(ErrorType)) == {
        "assertion_failed", "timeout", "guardrail", "engine_error", "navigation_error", "network_error",
        "precheck_failed", "acquire_timeout", "session_lost", "capability_unavailable", "release_failed",
    }


def test_worker_exit_error_carries_exit_code_and_network_is_a_subclass():
    with pytest.raises(WorkerExitError) as ei:
        raise_for_worker_exit(137, code_label="exitCode")
    assert ei.value.exit_code == 137 and "exitCode=137" in str(ei.value)
    with pytest.raises(WorkerExitError) as neg:
        raise_for_worker_exit(-9, code_label="returncode")
    assert neg.value.exit_code == -9
    assert issubclass(WorkerNetworkError, WorkerExitError)
    assert WorkerNetworkError("x").exit_code == 80


# ---- serialize：设备 job 带 sessions[] 与两个计量键、桌面 job 省键、往返一致、旧落盘可读 ----

def _job(scope_id: str = "s") -> Job:
    return Job(scope_id=scope_id, scope_name=scope_id, engine="midscene",
               scenarios=(Scenario(id=f"{scope_id}:1", name="n", steps=(Step(0, "Given", "x"),)),))


def test_device_job_round_trips_sessions_and_metering_and_desktop_job_omits_them():
    sessions = [
        SessionRecord(session_id="arn:a", name="n-a", origin="created", release="confirmed", observed_s=10.0,
                      provider_minutes={"total": 1, "metered": 1, "unmetered": 0}),
        SessionRecord(session_id="arn:b", name="n-b", origin="discovered", release="unconfirmed", observed_s=None),
        SessionRecord(session_id=None, name="n-c", origin="attempted", release="unconfirmed"),
        SessionRecord(session_id="arn:d", name="n-d", origin="created", release=None),  # 没收到 session_closed
    ]
    device = JobResult(job=_job("dev"), status=Status.ERROR, sessions=sessions, device_observed_s=10.0, device_observed_missing=2)
    d = job_result_to_dict(device)
    assert [s["release"] for s in d["sessions"]] == ["confirmed", "unconfirmed", "unconfirmed", "unconfirmed"]  # None 写端归 unconfirmed
    assert d["sessions"][2]["session_id"] is None and d["device_observed_s"] == 10.0 and d["device_observed_missing"] == 2
    back = job_result_from_dict(d)
    assert back.device_observed_s == 10.0 and back.device_observed_missing == 2
    assert [(s.session_id, s.name, s.origin, s.release, s.observed_s, s.provider_minutes) for s in back.sessions] == [
        ("arn:a", "n-a", "created", "confirmed", 10.0, {"total": 1, "metered": 1, "unmetered": 0}),
        ("arn:b", "n-b", "discovered", "unconfirmed", None, None),
        (None, "n-c", "attempted", "unconfirmed", None, None),
        ("arn:d", "n-d", "created", "unconfirmed", None, None),  # 读回即 unconfirmed（写端已规范化）
    ]
    desktop = job_result_to_dict(JobResult(job=_job("desk"), status=Status.PASSED))
    assert not {"sessions", "device_observed_s", "device_observed_missing"} & set(desktop)  # 桌面 job 三键都不出现
    old = job_result_from_dict(desktop)  # 旧落盘 / 桌面：读出空列表与 None，不报错
    assert old.sessions == [] and old.device_observed_s is None and old.device_observed_missing is None


def test_run_result_run_level_metering_keys_follow_the_same_omit_rule():
    meta = RunMeta(run_id="r", created_at="t", jobs=(_job("a"), _job("b")))
    desktop_run = RunResult(run_meta=meta, status=Status.PASSED, jobs=[JobResult(job=_job("a"), status=Status.PASSED)])
    assert not {"device_observed_s", "device_observed_missing"} & set(to_dict(desktop_run))
    device_run = RunResult(run_meta=meta, status=Status.ERROR, device_observed_s=25.5, device_observed_missing=1,
                           jobs=[JobResult(job=_job("b"), status=Status.ERROR, sessions=[
                               SessionRecord(session_id="arn:x", name="n", origin="created", release="confirmed", observed_s=25.5)],
                               device_observed_s=25.5, device_observed_missing=1)])
    d = to_dict(device_run)
    assert d["device_observed_s"] == 25.5 and d["device_observed_missing"] == 1
    back = from_dict(json.loads(json.dumps(d)))
    assert back.device_observed_s == 25.5 and back.device_observed_missing == 1 and back.jobs[0].sessions[0].name == "n"
