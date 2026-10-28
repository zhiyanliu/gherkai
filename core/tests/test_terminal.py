"""终结函数与真值表（ADR 0034 机制二）、代表会话规则、scope 级 error 的合成 SKIPPED、设备计量合计（ADR 0051 决策 4、7）。

纯函数直测：按真值表逐行参数化，并验证按行序取第一个命中的行。两条归约路径的对拍在 test_termination_parity。
"""
from __future__ import annotations

import pytest

from gherkai_core.model import (
    Job,
    JobResult,
    Scenario,
    ScenarioDone,
    ScenarioStarted,
    ScopeDone,
    ScopeStarted,
    SessionClosed,
    SessionOpened,
    SessionRecord,
    Status,
    Step,
    StepDone,
    StepStarted,
)
from gherkai_core.project import (
    RELEASE_FAILED_HINT,
    Timing,
    apply_device_metering,
    device_metering,
    finalize_job,
    reduce_event,
    representative_session,
    unconfirmed_sessions,
)
from gherkai_core.serialize import job_result_from_dict, job_result_to_dict


def _job(n_scenarios: int = 3, timeout_s: float | None = 60.0) -> Job:
    scs = tuple(Scenario(id=f"s:{i}", name=f"sc{i}", steps=(Step(0, "Given", "a"), Step(1, "Then", "b"))) for i in range(n_scenarios))
    return Job(scope_id="s", scope_name="s", engine="midscene", scenarios=scs, timeout_s=timeout_s)


def _confirmed(name: str = "n1") -> SessionRecord:
    return SessionRecord(session_id=f"arn:{name}", name=name, origin="created", release="confirmed", observed_s=1.0)


def _unconfirmed(name: str = "n2") -> SessionRecord:
    return SessionRecord(session_id=f"arn:{name}", name=name, origin="created", release="unconfirmed")


def _attempted(name: str = "n3") -> SessionRecord:
    return SessionRecord(session_id=None, name=name, origin="attempted", release="unconfirmed")


def _fin(**kw):
    base = dict(job=_job(), stop_reason="none", exited=True, exit_code=0, exit_reason=None, saw_scope_started=True,
                saw_session_opened=False, scope_done=ScopeDone(scope_id="s"), scenario_status={"s:0": Status.PASSED},
                sessions=[])
    base.update(kw)
    return finalize_job(**base)


# ---- 真值表逐行 ----

@pytest.mark.parametrize("kw, status, error_type, in_message", [
    # 行 1：timeout 优先于一切（含 U 非空与非零退出）
    (dict(stop_reason="timeout", exit_code=137, sessions=[_unconfirmed()]), Status.ERROR, "timeout", "job 超时（预算 60s，已中止）"),
    (dict(stop_reason="timeout", job=_job(timeout_s=None), scope_done=None), Status.ERROR, "timeout", "job 超时（已中止）"),
    (dict(stop_reason="timeout", exit_code=1), Status.ERROR, "timeout", "job 超时"),  # scope_done 已到但非零退出：不算内容完整
    # 行 2：abort → ABORTED、归因为空（优先于非零退出）；U 非空不改判定、只追加提示
    (dict(stop_reason="abort", exit_code=1), Status.ABORTED, None, "fail-fast"),
    (dict(stop_reason="abort", exit_code=1, sessions=[_unconfirmed()]), Status.ABORTED, None, RELEASE_FAILED_HINT),
    # 内容完整（干净退出且有 scope_done）后停止原因不再改写判定：判定按内容给出
    (dict(stop_reason="timeout"), Status.PASSED, None, None),
    (dict(stop_reason="abort", scenario_status={"s:0": Status.FAILED}), Status.FAILED, None, None),
    (dict(stop_reason="timeout", sessions=[_unconfirmed()]), Status.ERROR, "release_failed", RELEASE_FAILED_HINT),
    (dict(stop_reason="timeout", scope_done=ScopeDone(scope_id="s", status=Status.ERROR, error_type="acquire_timeout", message="没拿到设备")),
     Status.ERROR, "acquire_timeout", "没拿到设备"),
    # 行 3：退出码非零 / 未知；U 非空只改归因、退出原因的消息保留
    (dict(exit_code=1, sessions=[_unconfirmed()]), Status.ERROR, "release_failed", RELEASE_FAILED_HINT),
    (dict(exit_code=1, sessions=[_unconfirmed()]), Status.ERROR, "release_failed", "worker 非正常退出（exit 1"),
    (dict(exit_code=-9, sessions=[_unconfirmed(), _attempted()]), Status.ERROR, "release_failed", "exit -9"),
    (dict(exit_code=80), Status.ERROR, "network_error", "建连失败"),
    (dict(exit_code=1), Status.ERROR, "engine_error", "worker 非正常退出（exit 1"),
    (dict(exit_code=1, scope_done=ScopeDone(scope_id="s", status=Status.ERROR, error_type="acquire_timeout", message="没拿到设备")),
     Status.ERROR, "engine_error", "没拿到设备；worker 随后非正常退出（exit 1）"),  # 先报 scope 级 error 再非零退出：原因保留
    (dict(exit_code=-9), Status.ERROR, "engine_error", "exit -9"),
    (dict(exit_code=None), Status.ERROR, "engine_error", "退出码未知"),
    (dict(exit_code=None, exit_reason="worker 异常：解析失败"), Status.ERROR, "engine_error", "worker 异常：解析失败"),  # 消息由调用方带上下文
    (dict(exit_code=255, exit_reason="TaskFailedToStart: 拉不到镜像"), Status.ERROR, "engine_error", "平台侧未取到退出码时也记为 255）：TaskFailedToStart"),
    # 行 4：退出码 0、无 scope_done（U 非空也不改判 release_failed，只追加提示）
    (dict(scope_done=None), Status.ERROR, "engine_error", "没有报完这次运行的结果"),
    (dict(scope_done=None, sessions=[_unconfirmed()]), Status.ERROR, "engine_error", RELEASE_FAILED_HINT),
    # 行 5：scope_done.status = error → 取其归因；U 非空改 release_failed、worker 报的消息保留
    (dict(scope_done=ScopeDone(scope_id="s", status=Status.ERROR, error_type="acquire_timeout", message="没拿到设备")),
     Status.ERROR, "acquire_timeout", "没拿到设备"),
    (dict(scope_done=ScopeDone(scope_id="s", status=Status.ERROR, error_type="session_lost", message="m"), sessions=[_attempted()]),
     Status.ERROR, "release_failed", "结果未知的创建尝试：n3"),
    (dict(scope_done=ScopeDone(scope_id="s", status=Status.ERROR, error_type="session_lost", message="远程访问会话中途丢失"), sessions=[_attempted()]),
     Status.ERROR, "release_failed", "远程访问会话中途丢失"),
    # 行 6：零 scenario → ERROR（曾被 _aggregate([]) 判成 PASSED）；U 非空同样只追加提示
    (dict(scenario_status={}), Status.ERROR, "engine_error", "worker 未报告任何 scenario 判定"),
    (dict(scenario_status={}, sessions=[_unconfirmed()]), Status.ERROR, "engine_error", "worker 未报告任何 scenario 判定"),
    # 行 7：判定集非空 → _aggregate；U 非空改判 release_failed
    (dict(scenario_status={"s:0": Status.PASSED, "s:1": Status.FAILED}), Status.FAILED, None, None),
    (dict(scenario_status={"s:0": Status.PASSED}, sessions=[_confirmed()]), Status.PASSED, None, None),
    (dict(scenario_status={"s:0": Status.PASSED}, sessions=[_confirmed(), _unconfirmed("x")]), Status.ERROR, "release_failed", "未确认停止的会话：x"),
])
def test_truth_table_rows(kw, status, error_type, in_message):
    term = _fin(**kw)
    assert (term.status, term.error_type) == (status, error_type), term
    if in_message is None:
        assert term.message is None
    else:
        assert in_message in (term.message or ""), term.message


def test_not_exited_is_running_or_pending():
    assert _fin(exited=False, exit_code=None, scope_done=None, scenario_status={}).status == Status.RUNNING
    assert _fin(exited=False, exit_code=None, scope_done=None, scenario_status={}, saw_scope_started=False,
                saw_session_opened=True).status == Status.RUNNING  # 只见过 session_opened（取设备期间）也算 RUNNING
    assert _fin(exited=False, exit_code=None, scope_done=None, scenario_status={}, saw_scope_started=False).status == Status.PENDING


def test_network_exit_message_is_not_duplicated_and_reason_only_appends():
    """退出码 80 的消息只有一句（同步路径不再把异常文本当平台归因传入）；平台归因存在时作为后缀追加。"""
    assert _fin(exit_code=80).message == "worker 建连失败（网络/SSL 瞬时故障），退出码 80"
    assert _fin(exit_code=80, exit_reason="Essential container exited").message.endswith("退出码 80：Essential container exited")


def test_release_failed_hint_lists_sessions_and_attempts_separately_even_on_timeout():
    """U 非空时无论判定为何都追加提示：会话名与「结果未知的创建尝试」分开列。"""
    term = _fin(stop_reason="timeout", scope_done=None, sessions=[_unconfirmed("a"), _attempted("b"), _confirmed("c")])
    assert term.error_type == "timeout"
    assert "未确认停止的会话：a" in term.message and "结果未知的创建尝试：b" in term.message and "c" not in term.message.split("会话：")[1].split("；")[0]
    assert unconfirmed_sessions([_unconfirmed("a"), _attempted("b"), _confirmed("c")]) == [_unconfirmed("a"), _attempted("b")]


# ---- 代表会话（ADR 0051 决策 4 / 0024 sessionId 取值优先级）----

def test_representative_session_rules():
    sid, locked = representative_session(None, False, SessionOpened(scope_id="s", name="A", origin="created", session_id="A"))
    assert (sid, locked) == ("A", False)
    sid, locked = representative_session(sid, locked, SessionOpened(scope_id="s", name="B", origin="created", session_id="B"))  # 换台：后到覆盖
    assert sid == "B"
    sid, locked = representative_session(sid, locked, SessionOpened(scope_id="s", name="T", origin="attempted"))  # attempted 不写入
    assert sid == "B"
    sid, locked = representative_session(sid, locked, ScopeStarted(scope_id="s", session_id="B"))  # 锁定
    assert (sid, locked) == ("B", True)
    sid, locked = representative_session(sid, locked, SessionOpened(scope_id="s", name="C", origin="discovered", session_id="C"))
    assert sid == "B"  # 锁定后不改写
    sid, locked = representative_session(sid, locked, ScopeDone(scope_id="s", session_id="D"))
    assert sid == "B"  # scope_done 不覆盖已取到的值
    assert representative_session(None, False, ScopeDone(scope_id="s", session_id="D"))[0] == "D"  # 没值时 scope_done 补
    assert representative_session(None, False, SessionOpened(scope_id="s", name="T", origin="attempted"))[0] is None  # 只有 attempted → None


def test_reduce_event_tracks_sessions_and_representative_session():
    result = JobResult(job=_job(), status=Status.PENDING)
    ss: dict = {}
    t = Timing()
    reduce_event(SessionOpened(scope_id="s", name="A", origin="created", session_id="arn:A", device={"platform": "android"}), result, ss, t, 1.0)
    reduce_event(SessionOpened(scope_id="s", name="B", origin="created", session_id="arn:B"), result, ss, t, 2.0)
    reduce_event(ScopeStarted(scope_id="s", session_id="arn:B"), result, ss, t, 3.0)
    reduce_event(SessionOpened(scope_id="s", name="T", origin="attempted"), result, ss, t, 4.0)
    reduce_event(SessionClosed(scope_id="s", name="A", release="confirmed", session_id="arn:A", observed_s=10.0,
                               provider_minutes={"total": 1, "metered": 1, "unmetered": 0}), result, ss, t, 5.0)
    reduce_event(SessionClosed(scope_id="s", name="T", release="unconfirmed"), result, ss, t, 6.0)  # attempted 按名配对
    reduce_event(ScopeDone(scope_id="s", session_id="arn:C"), result, ss, t, 7.0)
    assert result.session_id == "arn:B"
    assert [(s.session_id, s.name, s.origin, s.release, s.observed_s) for s in result.sessions] == [
        ("arn:A", "A", "created", "confirmed", 10.0), ("arn:B", "B", "created", None, None), (None, "T", "attempted", "unconfirmed", None)]
    assert result.sessions[0].provider_minutes == {"total": 1, "metered": 1, "unmetered": 0}
    assert result.sessions[0].device == {"platform": "android"} and result.sessions[1].device is None  # device 原样留在记录上
    # 同一 ARN 重发 session_opened 不重复登记；补发的 device 填进已有记录
    reduce_event(SessionOpened(scope_id="s", name="A", origin="created", session_id="arn:A"), result, ss, t, 8.0)
    reduce_event(SessionOpened(scope_id="s", name="B", origin="created", session_id="arn:B", device={"model": "m"}), result, ss, t, 8.5)
    assert len(result.sessions) == 3 and result.sessions[1].device == {"model": "m"}
    back = job_result_from_dict(job_result_to_dict(result))  # 序列化往返保留 device
    assert [s.device for s in back.sessions] == [{"platform": "android"}, {"model": "m"}, None]


def test_session_pairing_falls_back_to_name_when_one_side_lacks_session_id():
    """配对键（ADR 0024）：一侧带 sessionId、另一侧缺省的同名事件配成一条记录（不多登记、不误判未确认）；缺省侧后来带上的 ARN 补进记录；
    同名而 ARN 不同的两条真实会话不混为一条。"""
    result, ss = _run_events([
        SessionOpened(scope_id="s", name="A", origin="created", session_id="arn:A"),
        SessionClosed(scope_id="s", name="A", release="confirmed", observed_s=4.0),  # 没带 sessionId
        SessionOpened(scope_id="s", name="T", origin="attempted"),
        SessionClosed(scope_id="s", name="T", release="confirmed", session_id="arn:T", observed_s=1.0),  # 事后才知道 ARN
        SessionOpened(scope_id="s", name="B", origin="created", session_id="arn:B1"),
        SessionOpened(scope_id="s", name="B", origin="created", session_id="arn:B2"),
    ])
    by = {(s.name, s.session_id): s for s in result.sessions}
    assert set(by) == {("A", "arn:A"), ("T", "arn:T"), ("B", "arn:B1"), ("B", "arn:B2")}
    assert by[("A", "arn:A")].release == "confirmed" and by[("A", "arn:A")].observed_s == 4.0
    assert by[("T", "arn:T")].origin == "attempted" and not by[("T", "arn:T")].confirmed  # 补了 ARN，origin 不改、仍在 U 里
    assert unconfirmed_sessions(result.sessions) == [by[("T", "arn:T")], by[("B", "arn:B1")], by[("B", "arn:B2")]]


# ---- 合成 SKIPPED（ADR 0051 决策 4；0031 决定一、六）----

def _run_events(events, job=None):
    result = JobResult(job=job or _job(), status=Status.PENDING)
    ss: dict = {}
    t = Timing()
    for i, ev in enumerate(events):
        reduce_event(ev, result, ss, t, float(i))
    return result, ss


def test_scope_error_synthesizes_skipped_only_for_zero_event_scenarios():
    result, ss = _run_events([
        ScopeStarted(scope_id="s", session_id="x"),
        ScenarioStarted(scenario_id="s:0"), StepDone(scenario_id="s:0", step_index=0, status=Status.PASSED),
        StepDone(scenario_id="s:0", step_index=1, status=Status.PASSED), ScenarioDone(scenario_id="s:0", status=Status.PASSED),
        ScenarioStarted(scenario_id="s:1"), StepStarted(scenario_id="s:1", step_index=0),  # 在途：有 started 无 done
        ScopeDone(scope_id="s", status=Status.ERROR, error_type="session_lost", message="设备没了"),
    ])
    by = {sr.scenario_id: sr for sr in result.scenarios}
    assert set(by) == {"s:0", "s:2"}  # 在途的 s:1 整条不合成
    assert by["s:2"].status == Status.SKIPPED
    assert [(st.index, st.status, st.shortcircuited, st.duration_ms) for st in by["s:2"].steps] == [
        (0, Status.SKIPPED, False, None), (1, Status.SKIPPED, False, None)]
    assert "s:2" not in ss  # 合成的 SKIPPED 不写 scenario_status（不进 _aggregate）
    back = job_result_from_dict(job_result_to_dict(result))  # 序列化往返保留 shortcircuited=False
    assert [st.shortcircuited for st in back.scenarios[1].steps] == [False, False]


def test_session_opened_by_name_fills_arn_and_later_arn_is_a_new_session():
    """按名命中的记录补 ARN：discovered（无 ARN）→ opened(A) 配成一条并补上 A；再来 opened(B) 是另一条真实会话，不并进去。"""
    result, _ = _run_events([
        SessionOpened(scope_id="s", name="n", origin="discovered"),
        SessionOpened(scope_id="s", name="n", origin="created", session_id="arn:A"),
        SessionOpened(scope_id="s", name="n", origin="created", session_id="arn:B"),
    ])
    assert [(s.session_id, s.origin) for s in result.sessions] == [("arn:A", "discovered"), ("arn:B", "created")]


def test_finalize_after_synthesis_keeps_synthesized_details():
    """合成明细与判定分开（ADR 0034 机制二）：scope 级 error 合成 SKIPPED 后，终结函数判 timeout / abort 不撤销明细。"""
    sd = ScopeDone(scope_id="s", status=Status.ERROR, error_type="acquire_timeout", message="没拿到设备")
    result, ss = _run_events([sd])
    for stop_reason, status in (("timeout", Status.ERROR), ("abort", Status.ABORTED)):
        term = _fin(stop_reason=stop_reason, exit_code=1, scope_done=sd, scenario_status=ss)  # 非零退出：内容不完整，停止原因生效
        assert term.status == status and [sr.status for sr in result.scenarios] == [Status.SKIPPED] * 3


def test_scenario_done_after_synthesis_replaces_the_synthesized_record():
    """worker 违约（scope_done 之后仍发 scenario_done）时同一 scenario 只留一条记录：真实判定取代合成的 SKIPPED。"""
    result, ss = _run_events([
        ScopeDone(scope_id="s", status=Status.ERROR, error_type="session_lost", message="m"),
        ScenarioStarted(scenario_id="s:1"), ScenarioDone(scenario_id="s:1", status=Status.FAILED),
    ])
    assert [sr.scenario_id for sr in result.scenarios] == ["s:0", "s:1", "s:2"]
    assert [sr.status for sr in result.scenarios] == [Status.SKIPPED, Status.FAILED, Status.SKIPPED] and ss == {"s:1": Status.FAILED}


@pytest.mark.parametrize("inflight", [
    [StepStarted(scenario_id="s:1", step_index=0)],
    [StepDone(scenario_id="s:1", step_index=0, status=Status.PASSED)],
    ["step_skipped"],
    [ScenarioStarted(scenario_id="s:1")],
], ids=["step_started", "step_done", "step_skipped", "scenario_started"])
def test_any_single_event_marks_scenario_in_flight(inflight):
    """零事件判据：见过任何一种事件（不只 scenario_started）的 scenario 都算在途、整条不合成。"""
    from gherkai_core.model import StepSkipped

    events = [StepSkipped(scenario_id="s:1", step_index=1) if e == "step_skipped" else e for e in inflight]
    result, _ = _run_events([*events, ScopeDone(scope_id="s", status=Status.ERROR, error_type="session_lost", message="m")])
    assert [sr.scenario_id for sr in result.scenarios] == ["s:0", "s:2"]


def test_no_synthesis_without_scope_error():
    result, _ = _run_events([ScopeStarted(scope_id="s"), ScopeDone(scope_id="s")])  # 正常 scope_done 不带 status
    assert result.scenarios == []
    result, _ = _run_events([ScopeStarted(scope_id="s")])  # 没有 scope_done
    assert result.scenarios == []


def test_synthesis_happens_at_scope_done_and_later_events_do_not_undo_it():
    result, ss = _run_events([ScopeDone(scope_id="s", status=Status.ERROR, error_type="precheck_failed", message="m")])
    assert [sr.status for sr in result.scenarios] == [Status.SKIPPED] * 3 and ss == {}
    # 之后到达的事件（如停止后的 session_closed）不撤销明细
    reduce_event(SessionClosed(scope_id="s", name="n", release="confirmed"), result, ss, Timing(), 9.0)
    assert len(result.scenarios) == 3


# ---- 设备计量（ADR 0051 决策 7）----

def test_device_metering_counts_created_and_discovered_only():
    sessions = [
        SessionRecord(session_id="a", name="a", origin="created", release="confirmed", observed_s=10.0),
        SessionRecord(session_id="b", name="b", origin="discovered", release="confirmed", observed_s=None),
        SessionRecord(session_id="c", name="c", origin="created", release=None),  # 没收到 session_closed
        SessionRecord(session_id=None, name="d", origin="attempted", release="unconfirmed"),
        SessionRecord(session_id="e", name="e", origin="created", release="confirmed", observed_s=0.0),  # 0 计入合计、不算缺失
    ]
    assert device_metering(sessions) == (10.0, 2)
    jr = JobResult(job=_job(), status=Status.ERROR, sessions=sessions)
    apply_device_metering(jr)
    assert (jr.device_observed_s, jr.device_observed_missing) == (10.0, 2)
    desktop = JobResult(job=_job(), status=Status.PASSED)
    apply_device_metering(desktop)
    assert (desktop.device_observed_s, desktop.device_observed_missing) == (None, None)  # 桌面 job 两键都 None（序列化省键）
