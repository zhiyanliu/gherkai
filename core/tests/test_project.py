"""gherkai_core.project 纯投影测试（ADR 0034）：project(records)→RunState 的「两件都要」谓词 + HWM + plan_next。

纯逻辑、无 I/O、无 mock 外真实行为 → 绿即够（CLAUDE.md「绿≠对·别过度」：mock 内逻辑结论绿即足）。
reconciler 的执行编排（Stream 触发/CAS 真写/进程脱离）不在此测——那是推进编排的真实运行边界。
"""
from __future__ import annotations

import pytest

from gherkai_core.model import (
    Cost,
    Job,
    JobResult,
    RunMeta,
    Scenario,
    ScenarioDone,
    ScopeDone,
    ScopeStarted,
    Status,
    Step,
    StepDone,
)
from gherkai_core.project import (PLATFORM_FAILED_EXIT, Action, EventRecord, TaskExited, plan_next, project, project_full,
                                  recover_from_events, run_totals)


def _job(scope_id: str, engine: str = "novaact") -> Job:
    sc = Scenario(id=f"{scope_id}:1", name="s", steps=(Step(index=0, keyword="Given", text="x"),))
    return Job(scope_id=scope_id, scope_name=scope_id, engine=engine, scenarios=(sc,))


def _meta(*scope_ids: str) -> RunMeta:
    return RunMeta(run_id="run-1", created_at="2026-07-19T00:00:00Z",
                   jobs=tuple(_job(s) for s in scope_ids))


def _ev(scope_id: str, seq: int, event, ts: float = 0.0) -> EventRecord:
    return EventRecord(scope_id=scope_id, kind="event", seq=seq, event=event, emit_ts=ts)


def _exit(scope_id: str, code: int | None) -> EventRecord:
    return EventRecord(scope_id=scope_id, kind="exit", exited=TaskExited(scope_id=scope_id, exit_code=code))


# 一个「运行完成 passed」的完整 worker 事件序列（scope_started→scenario_done(passed)→scope_done）
def _passed_events(scope_id: str, base_seq: int = 1):
    scen = f"{scope_id}:1"
    return [
        _ev(scope_id, base_seq, ScopeStarted(scope_id=scope_id, session_id="sess-x")),
        _ev(scope_id, base_seq + 1, ScenarioDone(scenario_id=scen, status=Status.PASSED)),
        _ev(scope_id, base_seq + 2, ScopeDone(scope_id=scope_id)),
    ]


def _timeout_exit(scope_id: str, code: int | None) -> EventRecord:
    return EventRecord(scope_id=scope_id, kind="exit",
                       exited=TaskExited(scope_id=scope_id, exit_code=code, timed_out=True))


# ---------- 「两件都要」谓词（机制二）----------

def test_no_records_job_is_pending():
    """definition 里的 job 没有任何 record → PENDING（还没起）。"""
    state = project(_meta("a"), [])
    assert state.jobs["a"].status == Status.PENDING
    assert state.status == Status.PENDING  # 判定集为空时不判 passed（ADR 0031 决定三）：全部 pending 的 run 级值是 pending


def test_scope_started_but_no_exit_is_running():
    """见了 scope_started、有 scope_done，但没 task_exit → RUNNING（进程未确认终止，两件缺一）。"""
    recs = _passed_events("a")  # 含 scope_done，但无 exit 记录
    state = project(_meta("a"), recs)
    assert state.jobs["a"].status == Status.RUNNING
    assert state.jobs["a"].session_id == "sess-x"  # 血缘随 scope_started 落


def test_scope_started_running_without_exit():
    """会话已起（scope_started）、进程还没终止（无 task_exited）→ RUNNING（在运行）。"""
    recs = [_ev("a", 1, ScopeStarted(scope_id="a", session_id="s"))]
    state = project(_meta("a"), recs)
    assert state.jobs["a"].status == Status.RUNNING


def test_clean_exit_without_scope_done_is_error():
    """干净退出（exit=0）却没发完 scope_done（内容不完整）→ ERROR（矛盾态，不死循环；据 worker 崩溃的实际运行复现修正）。"""
    recs = [_ev("a", 1, ScopeStarted(scope_id="a", session_id="s")), _exit("a", 0)]
    state = project(_meta("a"), recs)
    assert state.jobs["a"].status == Status.ERROR


def test_crash_no_scope_done_nonzero_exit_is_error():
    """worker 崩溃（吐 scope_started 后非0退出、没 scope_done）→ ERROR（不等 scope_done；据 worker 崩溃致死循环的实际运行复现修正）。"""
    recs = [_ev("a", 1, ScopeStarted(scope_id="a", session_id="s")), _exit("a", 3)]
    state = project(_meta("a"), recs)
    assert state.jobs["a"].status == Status.ERROR


def test_network_exit_before_scope_started_is_error():
    """建连失败（退出码 80、scope_started 都没发）→ ERROR（进程终止即终态，不卡 pending）。"""
    recs = [_exit("a", 80)]
    state = project(_meta("a"), recs)
    assert state.jobs["a"].status == Status.ERROR


def test_two_things_present_clean_exit_terminal_passed():
    """两件都要齐（scope_done 与 exit=0 都齐）→ 终态取 scenario 归约（passed）。"""
    recs = _passed_events("a") + [_exit("a", 0)]
    state = project(_meta("a"), recs)
    assert state.jobs["a"].status == Status.PASSED
    assert state.status == Status.PASSED


def test_nonzero_exit_overrides_content_to_error():
    """关键（机制二）：scope_done 说 passed，但 exit_code!=0 → 判 ERROR（防"发完 scope_done 又非0退出"误报）。"""
    recs = _passed_events("a") + [_exit("a", 1)]  # 内容 passed，进程非干净退出
    state = project(_meta("a"), recs)
    assert state.jobs["a"].status == Status.ERROR
    assert state.status == Status.ERROR


def test_sigkill_137_is_error():
    """SIGKILL 截断 exit=137 → ERROR（实测 payload 带 137，机制二）。"""
    recs = _passed_events("a") + [_exit("a", 137)]
    state = project(_meta("a"), recs)
    assert state.jobs["a"].status == Status.ERROR


def test_exit_code_none_is_error_not_running():
    """有退出记录却无码（exit_code=None）→ ERROR：退出码未知即不可判定为通过（ADR 0034 机制二「退出码缺失」条）。
    曾判 RUNNING「等观察者补」——STOPPED 事件只来一次、永远补不上，那是 run 永久 wedge 的根因。"""
    recs = _passed_events("a") + [_exit("a", None)]
    state = project(_meta("a"), recs)
    assert state.jobs["a"].status == Status.ERROR
    result = project_full(_meta("a"), recs)
    assert "退出码未知" in (result.jobs[0].message or "")


def test_platform_sentinel_exit_surfaces_reason_in_message():
    """观察者落的平台哨兵（容器没能开始运行）→ ERROR，且 reason（stopCode: stoppedReason）进 job message 给使用方看归因。"""
    exited = TaskExited(scope_id="a", exit_code=PLATFORM_FAILED_EXIT,
                        reason="TaskFailedToStart: CannotPullContainerError: not found")
    recs = [EventRecord(scope_id="a", kind="exit", exited=exited)]  # 零事件：容器根本没起
    result = project_full(_meta("a"), recs)
    jr = result.jobs[0]
    assert jr.status == Status.ERROR
    assert "CannotPullContainerError" in jr.message and "未能启动" in jr.message
    # tick 的 launch 失败补偿同一哨兵、无 reason → 指向部署侧日志，不留空 message
    result2 = project_full(_meta("a"), [_exit("a", PLATFORM_FAILED_EXIT)])
    assert "部署侧日志" in result2.jobs[0].message


def test_platform_exit_reason_joins_stop_code_and_reason_with_fallback():
    """ECS 没给退出码时的归因串只有这一份拼法（观察者、云端 tick 的补写与同步路径的 FargateEngine 共用，ADR 0024「exitCode 落值延迟」条）：
    两项齐全用「: 」相连，缺一项只用另一项，两项都缺（或为空串）时取固定兜底句、绝不为空。"""
    from gherkai_core.project import platform_exit_reason

    assert platform_exit_reason("TaskFailedToStart", "CannotPullContainerError: not found") == \
        "TaskFailedToStart: CannotPullContainerError: not found"
    assert platform_exit_reason("TaskFailedToStart", None) == "TaskFailedToStart"
    assert platform_exit_reason(None, "Essential container in task exited") == "Essential container in task exited"
    assert platform_exit_reason(None, None) == platform_exit_reason("", "") == "平台未给出退出码与原因"


# ---------- job timeout 归因链（ADR 0034「job timeout」节）----------

def test_timed_out_exit_is_error_regardless_of_exit_code_shape():
    """超时处置的 stop → ERROR，不论 exit_code 形态（SIGKILL 137 / 协作以退出码 0 退出 / 未落值 None——
    timed_out 归因优先：处置本身即终态信号，error_type 记 timeout 而非按码归因）。"""
    for code in (137, 0, None):
        recs = [_ev("a", 1, ScopeStarted(scope_id="a", session_id="s")), _timeout_exit("a", code)]
        state = project(_meta("a"), recs)
        assert state.jobs["a"].status == Status.ERROR, f"exit_code={code} 应判 ERROR"


def test_timed_out_attribution_error_type_timeout():
    """归因 error_type="timeout"（对齐同步路径，[0031] 决定一）——即使内容完整（scope_done 都到了）
    也以超时为根因、覆盖 reduce 期归因。"""
    from gherkai_core.project import project_full

    recs = _passed_events("a") + [_timeout_exit("a", 137)]
    result = project_full(_meta("a"), recs)
    jr = result.jobs[0]
    assert jr.status == Status.ERROR
    assert jr.error_type == "timeout"
    assert "超时" in (jr.message or "")


def test_error_without_reduce_message_gets_default_attribution():
    """worker 起来即崩（非 0 退出、零事件）→ message 不再全空——补默认归因指向 worker 日志
    （detached 实际运行教训：error 无任何线索、只能手工复刻排障）。"""
    from gherkai_core.project import project_full

    recs = [_exit("a", 1)]  # 零事件 + exit 1
    jr = project_full(_meta("a"), recs).jobs[0]
    assert jr.status == Status.ERROR
    assert jr.message is not None and "退出码 1" in jr.message


def test_error_clean_exit_incomplete_content_gets_attribution():
    """exit 0 但无 scope_done（矛盾形态）→ 同样有归因文本（不留空白 error）。"""
    from gherkai_core.project import project_full

    recs = [_ev("a", 1, ScopeStarted(scope_id="a", session_id="s")), _exit("a", 0)]
    jr = project_full(_meta("a"), recs).jobs[0]
    assert jr.status == Status.ERROR
    assert jr.message is not None and "没有报完" in jr.message


# ---------- HWM（机制三）----------

def test_hwm_is_max_worker_seq():
    """high_water_mark 是所有 scope 的 worker 段 max seq（exit 记录无 seq、不参与）。"""
    recs = _passed_events("a", base_seq=1) + [_exit("a", 0)]  # worker seq 1,2,3
    state = project(_meta("a"), recs)
    assert state.high_water_mark == 3


def test_hwm_across_scopes():
    """多 scope：HWM 取跨 scope 的全局 max。"""
    recs = _passed_events("a", base_seq=1) + _passed_events("b", base_seq=1)
    recs += [_exit("a", 0), _exit("b", 0)]
    meta = _meta("a", "b")
    state = project(meta, recs)
    assert state.high_water_mark == 3  # 各 scope 独立 seq，max=3


def test_out_of_order_records_reduced_by_seq():
    """乱序 records（全量重放抗乱序，机制三前提）：project 内按 seq 升序归约，结果与顺序无关。"""
    recs = list(reversed(_passed_events("a"))) + [_exit("a", 0)]  # 倒序喂
    state = project(_meta("a"), recs)
    assert state.jobs["a"].status == Status.PASSED  # 仍正确归约


# ---------- 投影写的 run 级 status（机制三，两 RunStore adapter 共用同一规则）----------

def test_projected_run_status_pending_only_while_all_jobs_pending():
    """全 job pending → pending（两个 adapter 据此不写 run 级）；任一 job 推进 → running；恒非终态（终态归 finalize）。"""
    from gherkai_core.model import JobState
    from gherkai_core.project import projected_run_status

    def _jobs(*statuses):
        return {f"s{i}": JobState(f"s{i}", st) for i, st in enumerate(statuses)}

    assert projected_run_status(_jobs(Status.PENDING, Status.PENDING)) == Status.PENDING
    assert projected_run_status(_jobs(Status.PENDING, Status.RUNNING)) == Status.RUNNING
    assert projected_run_status(_jobs(Status.PASSED, Status.PENDING)) == Status.RUNNING
    # 全终态也只到 running：run 级终态是 try_finalize 这个 commit point 专属（ADR 0030）
    assert projected_run_status(_jobs(Status.PASSED, Status.FAILED)) == Status.RUNNING


def test_projected_run_status_ignores_aggregate_value_from_project():
    """判据只看 job 态：运行中的 run 只要有一个 job 出了判定，project() 的 run 级 status 就是终态（a 已 passed、b 仍 pending
    时为 passed），投影写仍得 running——守「投影写不能原样落传入的 run 级值」。"""
    from gherkai_core.project import projected_run_status

    state = project(_meta("a", "b"), _passed_events("a") + [_exit("a", 0)])
    assert state.jobs["b"].status == Status.PENDING
    assert state.status == Status.PASSED  # 前提：运行中的 run 的聚合值已是终态
    assert projected_run_status(state.jobs) == Status.RUNNING


def test_project_run_status_before_any_verdict_is_pre_terminal():
    """还没有 job 出判定时，project() 的 run 级 status 是前置态（ADR 0031 决定三的空判定集规则）：
    全部 pending 得 pending；pending 与 running 并存得 running。与投影写落库的取值一致，但投影写不依赖它。"""
    from gherkai_core.project import projected_run_status

    all_pending = project(_meta("a", "b"), [])
    assert all_pending.status == Status.PENDING
    assert projected_run_status(all_pending.jobs) == Status.PENDING

    mixed = project(_meta("a", "b"), [_ev("a", 1, ScopeStarted(scope_id="a", session_id="s"))])
    assert (mixed.jobs["a"].status, mixed.jobs["b"].status) == (Status.RUNNING, Status.PENDING)
    assert mixed.status == Status.RUNNING
    assert projected_run_status(mixed.jobs) == Status.RUNNING


def _scope_events(scope_id: str, outcome: str) -> list:
    """一个 job 干净结束时的 worker 事件：outcome 为 passed / failed（scenario 判定）或 error（scope 级 error）。"""
    started = ScopeStarted(scope_id=scope_id, session_id=f"sess-{scope_id}")
    if outcome == "error":
        return [started, ScopeDone(scope_id=scope_id, status=Status.ERROR, error_type="engine_error", message="未就绪")]
    return [started, ScenarioDone(scenario_id=f"{scope_id}:1", status=Status(outcome)), ScopeDone(scope_id=scope_id)]


@pytest.mark.parametrize("outcomes, expected", [
    (("passed", "passed"), Status.PASSED),
    (("passed", "failed"), Status.FAILED),
    (("failed", "error"), Status.ERROR),
])
def test_run_status_agrees_between_schedule_and_project_full(outcomes, expected):
    """两条路径共用同一个 _aggregate：同一组 job 事件分别经同步 schedule 与无状态 project_full，run 级 status 相同。"""
    from gherkai_core.schedule import ScheduleOpts, schedule
    from tests.fake_engine import CollectSink, FakeEngine, FakeResolver

    scopes = [f"j{i}" for i in range(len(outcomes))]
    streams = {s: _scope_events(s, o) for s, o in zip(scopes, outcomes)}
    meta = _meta(*scopes)
    sync = schedule(meta, FakeResolver(FakeEngine(streams)), CollectSink(), opts=ScheduleOpts(max_concurrency=1))
    recs = [_ev(s, i + 1, ev) for s in scopes for i, ev in enumerate(streams[s])] + [_exit(s, 0) for s in scopes]
    stateless = project_full(meta, recs)
    assert [jr.status for jr in sync.jobs] == [jr.status for jr in stateless.jobs] == [Status(o) for o in outcomes]
    assert sync.status == stateless.status == expected


def test_run_totals_agree_between_schedule_and_project_full():
    """两条路径共用同一个 run_totals：同一组带成本的 job 事件分别经同步 schedule 与无状态 project_full，run 级四个合计键相同。
    token 跨 job 求和；只有一个 job 报了工作时长且报的是 0，run 级照记 0、不当作没报；桌面 run 没有设备计量两键。"""
    from gherkai_core.schedule import ScheduleOpts, schedule
    from tests.fake_engine import CollectSink, FakeEngine, FakeResolver

    costs = {"j0": Cost(tokens=1000), "j1": Cost(tokens=500, time_worked_s=0.0), "j2": None}
    streams = {s: [ScopeStarted(scope_id=s, session_id=f"sess-{s}"),
                   StepDone(scenario_id=f"{s}:1", step_index=0, status=Status.PASSED, cost=c),
                   ScenarioDone(scenario_id=f"{s}:1", status=Status.PASSED), ScopeDone(scope_id=s)]
               for s, c in costs.items()}
    meta = _meta(*costs)
    sync = schedule(meta, FakeResolver(FakeEngine(streams)), CollectSink(), opts=ScheduleOpts(max_concurrency=1))
    recs = [_ev(s, i + 1, ev) for s in costs for i, ev in enumerate(streams[s])] + [_exit(s, 0) for s in costs]
    stateless = project_full(meta, recs)

    def totals(r):
        return (r.total_tokens, r.total_time_worked_s, r.device_observed_s, r.device_observed_missing)
    assert totals(sync) == totals(stateless) == (1500, 0.0, None, None)


def test_run_totals_keeps_separate_missing_rules_for_cost_and_device_metering():
    """run_totals 的两组键各守各的缺失语义：成本原生量只合计报了的 job、全无值才为 None、报了 0 照记 0；设备计量按设备 job
    成对合计，任一键有值即为设备 job、其另一键缺失按 0 计入，没有设备 job 时两键都是 None。"""
    def jr(scope: str, **kw) -> JobResult:
        return JobResult(job=_job(scope), status=Status.PASSED, **kw)

    assert run_totals([]) == {"total_tokens": None, "total_time_worked_s": None,
                              "device_observed_s": None, "device_observed_missing": None}
    zero = run_totals([jr("a"), jr("b", total_tokens=0, total_time_worked_s=0.0)])  # 报了 0 不是没报
    assert zero == {"total_tokens": 0, "total_time_worked_s": 0.0, "device_observed_s": None, "device_observed_missing": None}
    mixed = run_totals([jr("a"), jr("b", total_tokens=0), jr("c", total_tokens=7, total_time_worked_s=1.5)])
    assert (mixed["total_tokens"], mixed["total_time_worked_s"]) == (7, 1.5)
    one_key = run_totals([jr("d1", device_observed_s=3.0), jr("web")])  # 设备 job 缺的那一键按 0 计入，不是 None
    assert (one_key["device_observed_s"], one_key["device_observed_missing"]) == (3.0, 0)
    device = run_totals([jr("d1", device_observed_s=3.0), jr("d2", device_observed_missing=2), jr("web")])
    assert (device["device_observed_s"], device["device_observed_missing"]) == (3.0, 2)
    assert (device["total_tokens"], device["total_time_worked_s"]) == (None, None)


def test_stateless_path_cannot_yield_aborted_job():
    """无状态路径不作中止决定：推进器停掉的 job 只带 timed_out，判 error 与 timeout，不判 aborted。故使用方中断的 run 级 aborted
    例外只在同步路径上有，project_full 的 run 级 status 只由 _aggregate 给出。"""
    recs = [_ev("a", 1, ScopeStarted(scope_id="a", session_id="s")), _timeout_exit("a", 143)] \
        + _passed_events("b") + [_exit("b", 0)]
    full = project_full(_meta("a", "b"), recs)
    a = next(jr for jr in full.jobs if jr.scope_id == "a")
    assert (a.status, a.error_type) == (Status.ERROR, "timeout")
    assert all(jr.status not in (Status.ABORTED, Status.SKIPPED) for jr in full.jobs)
    assert full.status == Status.ERROR


def test_project_full_without_any_record_is_passed():
    """所有 job 都没有记录时 project_full 不臆造明细，_aggregate 收到空输入、run 级 passed（防御分支，记下空输入的这个来源）。"""
    full = project_full(_meta("a", "b"), [])
    assert full.jobs == []
    assert full.status == Status.PASSED


# ---------- plan_next（机制四）----------

def test_plan_next_starts_up_to_concurrency():
    """全 pending、max_concurrency=2 → 提议 start 前 2 个。"""
    state = project(_meta("a", "b", "c"), [])
    actions = plan_next(state, max_concurrency=2)
    starts = [a.scope_id for a in actions if a.kind == "start"]
    assert len(starts) == 2


def test_plan_next_respects_running_slots():
    """已有 1 个 running、max_concurrency=2 → 只补 1 个 pending。"""
    recs = [_ev("a", 1, ScopeStarted(scope_id="a"))]  # a 在 running（scope_started 无 scope_done/exit）
    state = project(_meta("a", "b", "c"), recs)
    assert state.jobs["a"].status == Status.RUNNING
    actions = plan_next(state, max_concurrency=2)
    starts = [a.scope_id for a in actions if a.kind == "start"]
    assert len(starts) == 1  # 2-1=1 slot
    assert "a" not in starts  # 不重启 running 的


def test_plan_next_finalize_when_all_terminal():
    """所有 job 达终态（无 pending/running）→ 提议 finalize。"""
    recs = _passed_events("a") + [_exit("a", 0)]
    state = project(_meta("a"), recs)
    actions = plan_next(state, max_concurrency=2)
    assert actions == [Action(kind="finalize")]


def test_plan_next_not_finalize_while_running():
    """有 running 时不 finalize（即使有别的 pending 也优先补并发、不收尾）。"""
    recs = [_ev("a", 1, ScopeStarted(scope_id="a"))]
    state = project(_meta("a", "b"), recs)
    actions = plan_next(state, max_concurrency=2)
    assert not any(a.kind == "finalize" for a in actions)


# ---- exit-without-events 真值表（ADR 0034 机制二：task_exited 判定不设 saw_scope_started 前置）----


def test_clean_exit_without_any_event_is_error():
    """零事件 + exit==0（构造期 SIGTERM 干净退出，0024 设计内）→ ERROR，不得判 PENDING。

    若判 PENDING：与已 claim 的 RUNNING 基线单调合并 → 永停 RUNNING → plan_next 空 → run 永不收敛
    （对抗验证探针复现的死循环）。ERROR（内容不完整但进程说成功，两者矛盾）比死循环安全。
    """
    meta = _meta("a")
    state = project(meta, [_exit("a", 0)])
    assert state.jobs["a"].status == Status.ERROR


def test_projection_keeps_baseline_session_id_when_events_only_carry_attempted():
    """代表会话（ADR 0051 决策 4）：events 只带 attempted 的 session_opened（没有 ARN）时，project() 带 baseline 合并不会用 None
    覆盖库里已记的 session_id。"""
    from gherkai_core.model import JobState, RunState, SessionOpened

    meta = _meta("a")
    baseline = RunState(run_id="run-1", status=Status.RUNNING,
                        jobs={"a": JobState("a", Status.RUNNING, session_id="arn:a")}, high_water_mark=0)
    recs = [EventRecord(scope_id="a", kind="event", seq=1, event=SessionOpened(scope_id="a", name="t", origin="attempted"), emit_ts=1.0)]
    state = project(meta, recs, baseline=baseline)
    assert (state.jobs["a"].session_id, state.jobs["a"].status) == ("arn:a", Status.RUNNING)


def test_clean_exit_without_events_converges_with_claimed_baseline():
    """同上,带「已 claim RUNNING」基线也必须收敛到 ERROR(终态 rank > running,单调合并不回退)。"""
    from gherkai_core.model import JobState, RunState

    meta = _meta("a")
    baseline = RunState(run_id="run-1", status=Status.RUNNING,
                        jobs={"a": JobState("a", Status.RUNNING)}, high_water_mark=0)
    state = project(meta, [_exit("a", 0)], baseline)
    assert state.jobs["a"].status == Status.ERROR


def test_exit_none_without_events_is_error_not_pending_nor_running():
    """零事件 + 有退出记录却无码 → ERROR（终态），既非 PENDING 也非 RUNNING（ADR 0034 机制二「退出码缺失」条）。

    判 PENDING 会让 plan_next 重复提议 start（与已 claim 基线合并后则永停）；判 RUNNING「等观察者补」同样永停——
    STOPPED 事件只来一次。观察者本应落哨兵，此分支是防 wedge 的防御。
    """
    meta = _meta("a")
    state = project(meta, [_exit("a", None)])
    assert state.jobs["a"].status == Status.ERROR


def test_project_full_refuses_non_terminal_snapshot():
    """ADR 0031 决定一·补的强制点：收尾快照里 job 仍 running（只见 scope_started）→ 抛、一份判定都不落，
    绝不把前置态写进 jobs/*.json。"""
    import pytest
    from gherkai_core.project import NonTerminalSnapshot
    recs = [_ev("a", 1, ScopeStarted(scope_id="a", session_id="s"))]
    with pytest.raises(NonTerminalSnapshot):
        project_full(_meta("a"), recs)


def test_project_full_carries_run_duration_from_host():
    """run 级墙钟由宿主按 RunState started_at→ended_at 算好传入（ADR 0024「三级执行时长」detached 条；core 不取时钟）；
    不传则 None（报告显「?」）。曾从不给，detached 的 RunReport 首屏墙钟恒「?」。"""
    recs = _passed_events("a") + [_exit("a", 0)]
    assert project_full(_meta("a"), recs).duration_ms is None
    assert project_full(_meta("a"), recs, run_duration_ms=135000.0).duration_ms == 135000.0


def test_step_done_message_is_kept_in_step_result():
    """step 级失败原因原文从 StepDone 搬进 StepResult（ADR 0042 决策三）——曾长期在归约时被丢。"""
    from gherkai_core.model import StepDone, StepStarted
    recs = [
        _ev("a", 1, ScopeStarted(scope_id="a", session_id="sess-x")),
        _ev("a", 2, StepStarted(scenario_id="a:1", step_index=0)),
        _ev("a", 3, StepDone(scenario_id="a:1", step_index=0, status=Status.FAILED,
                             error_type="assertion_failed", message="AI 断言未过多数票（0/1）：x")),
        _ev("a", 4, ScenarioDone(scenario_id="a:1", status=Status.FAILED)),
        _ev("a", 5, ScopeDone(scope_id="a")),
        _exit("a", 0),
    ]
    result = project_full(_meta("a"), recs)
    st = result.jobs[0].scenarios[0].steps[0]
    assert st.status == Status.FAILED and st.message == "AI 断言未过多数票（0/1）：x"


# ---------- 未完成 scenario 的事件流投影（ADR 0042 决策七）----------

def test_recover_from_events_returns_scenarios_absent_from_the_verdict_with_their_step_records():
    """三条 scenario：A 完整（有 scenario_done 且已在判定真值里，不补）；B 被中止在第三步（两条 step_done、一条只有 step_started）；
    C 零事件。补取只给 B（status None 即未完成），且 B 只含两条有 step_done 的 step，字段（含 report_refs）与归约路径一致；不写判定、
    不看退出记录。判定真值里**没有** A 时（同步 run 在归约前退出），A 也补取、带事件流里的 scenario 判定。"""
    from gherkai_core.model import ReportRef, StepDone, StepStarted, ScenarioStarted, Votes
    steps = tuple(Step(index=i, keyword="When", text=f"s{i}") for i in range(3))
    job = Job(scope_id="a", scope_name="a", engine="novaact", scenarios=(
        Scenario(id="a:A", name="A", steps=steps), Scenario(id="a:B", name="B", steps=steps), Scenario(id="a:C", name="C", steps=steps)))
    ref = ReportRef(kind="evidence", ref="file:///tmp/ev-b1.json", label="evidence")
    recs = [
        _ev("a", 1, ScopeStarted(scope_id="a", session_id="s")),
        _ev("a", 2, ScenarioStarted(scenario_id="a:A"), 10.0),
        _ev("a", 3, StepDone(scenario_id="a:A", step_index=0, status=Status.PASSED), 11.0),
        _ev("a", 4, ScenarioDone(scenario_id="a:A", status=Status.PASSED), 12.0),
        _ev("a", 5, ScenarioStarted(scenario_id="a:B"), 20.0),
        _ev("a", 6, StepStarted(scenario_id="a:B", step_index=0), 20.0),
        _ev("a", 7, StepDone(scenario_id="a:B", step_index=0, status=Status.PASSED), 23.5),
        _ev("a", 8, StepStarted(scenario_id="a:B", step_index=1), 24.0),
        _ev("a", 9, StepDone(scenario_id="a:B", step_index=1, status=Status.FAILED, votes=Votes(yes=0, total=1),
                              error_type="assertion_failed", message="没过", report_refs=(ref,)), 30.0),
        _ev("a", 10, StepStarted(scenario_id="a:B", step_index=2), 31.0),  # 被中止时正在执行：没有 step_done
        _exit("a", -15),
    ]
    out = recover_from_events(job, recs, recorded={"a:A"})
    assert [(u.scenario_id, u.status) for u in out] == [("a:B", None)]
    b = out[0].steps
    assert [(st.index, st.status) for st in b] == [(0, Status.PASSED), (1, Status.FAILED)]
    assert b[0].duration_ms == 3500.0 and b[1].report_refs == (ref,) and b[1].votes == Votes(yes=0, total=1)
    assert b[1].error_type == "assertion_failed" and b[1].message == "没过"
    # 乱序到达的记录按 seq 归约（与 _reduce_scope 同一排序）
    assert [u.scenario_id for u in recover_from_events(job, list(reversed(recs)), recorded={"a:A"})] == ["a:B"]
    # 判定真值里连 A 都没有：A 带事件流里的判定补取（status 来自 scenario_done），B 仍是未完成
    out2 = recover_from_events(job, recs, recorded=set())
    assert [(u.scenario_id, u.status, [st.index for st in u.steps]) for u in out2] == [("a:A", Status.PASSED, [0]), ("a:B", None, [0, 1])]
    # 没有任何事件：空；判定真值已有的 scenario 不补
    assert recover_from_events(job, [], recorded=set()) == [] and recover_from_events(job, recs[:4], recorded={"a:A"}) == []


def test_recover_from_events_ignores_scenarios_synthesized_after_scope_error():
    """scope 级 error 后 core 合成的 SKIPPED scenario（零事件）不是「未完成」；有 step 记录的在途 scenario 仍补取。"""
    from gherkai_core.model import StepDone, StepStarted, ScenarioStarted
    steps = (Step(index=0, keyword="When", text="x"), Step(index=1, keyword="Then", text="y"))
    job = Job(scope_id="a", scope_name="a", engine="midscene", scenarios=(
        Scenario(id="a:B", name="B", steps=steps), Scenario(id="a:C", name="C", steps=steps)))
    recs = [
        _ev("a", 1, ScopeStarted(scope_id="a")),
        _ev("a", 2, ScenarioStarted(scenario_id="a:B")),
        _ev("a", 3, StepStarted(scenario_id="a:B", step_index=0)),
        _ev("a", 4, StepDone(scenario_id="a:B", step_index=0, status=Status.PASSED)),
        _ev("a", 5, ScopeDone(scope_id="a", status=Status.ERROR, error_type="session_lost", message="丢了")),
    ]
    # 合成的 SKIPPED（C）会进判定真值，故在 recorded 里；B 在途、不在判定真值里 → 补取
    out = recover_from_events(job, recs, recorded={"a:C"})
    assert [(u.scenario_id, u.status, [st.index for st in u.steps]) for u in out] == [("a:B", None, [0])]
    # scope_done(error) 已在事件流、判定真值却一条 scenario 都没有：零事件的 C 仍不能被当成「从事件流补取」（它只是合成的 SKIPPED），
    # 只补事件流里真出现过的 B
    out2 = recover_from_events(job, recs, recorded=set())
    assert [(u.scenario_id, u.status) for u in out2] == [("a:B", None)]
