"""gherkai_core.project 纯投影测试（ADR 0034）：project(records)→RunState 的「两件都要」谓词 + HWM + plan_next，
收尾用的判定明细（project_full），以及从记录组装 run 的结果（assemble_run_result、run_duration_ms）。

纯逻辑、无 I/O、无 mock 外真实行为 → 绿即够（CLAUDE.md「绿≠对·别过度」：mock 内逻辑结论绿即足）。
reconciler 的执行编排（Stream 触发/CAS 真写/进程脱离）不在此测——那是推进编排的真实运行边界。
"""
from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from gherkai_core.model import (
    Cost,
    DeviceFarmRequest,
    Job,
    JobResult,
    JobState,
    RunMeta,
    RunState,
    Scenario,
    ScenarioDone,
    ScopeDone,
    ScopeStarted,
    Status,
    Step,
    StepDone,
    Target,
)
from gherkai_core.project import (DEADLINE_TIMEOUT_MESSAGE, PLATFORM_FAILED_EXIT, Action, EventRecord, TaskExited,
                                  apply_device_metering, assemble_run_result, plan_next, project, project_full,
                                  recover_from_events, run_duration_ms, run_totals)
from gherkai_core.run_status import RUN_ENDINGS, run_status_of, state_without_record
from tests.fake_engine import FAR_DEADLINE


def _job(scope_id: str, engine: str = "novaact") -> Job:
    sc = Scenario(id=f"{scope_id}:1", name="s", steps=(Step(index=0, keyword="Given", text="x"),))
    return Job(scope_id=scope_id, scope_name=scope_id, engine=engine, scenarios=(sc,), timeout_s=300.0)


def _meta(*scope_ids: str) -> RunMeta:
    return RunMeta(run_id="run-1", created_at="2026-07-19T00:00:00Z",
                   jobs=tuple(_job(s) for s in scope_ids), deadline_at=FAR_DEADLINE)


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


# 有记录的 job 的认领时刻（运行态里的值）：收尾时由它与预算、期限重算超时的说明。远早于 FAR_DEADLINE，起作用的是 job 自己的预算。
_CLAIMED = datetime(2030, 1, 1, tzinfo=timezone.utc)


def _full(meta: RunMeta, records, *, claimed_at=None) -> list[JobResult]:
    """project_full，给每个有记录的 job 一个认领时刻（调用方 tick 的快照检查保证它们都在）。"""
    if claimed_at is None:
        claimed_at = {r.scope_id: _CLAIMED for r in records}
    return project_full(meta, records, claimed_at=claimed_at)


# ---------- 「两件都要」谓词（机制二）----------

def test_no_records_job_is_pending():
    """definition 里的 job 没有任何 record → PENDING（还没起）。"""
    state = project(_meta("a"), [])
    assert state.jobs["a"].status == Status.PENDING
    assert state.status == Status.PENDING  # 取法：全部 job 为 pending 时 run 为 pending（ADR 0031 决定三「取法」）


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
    result = _full(_meta("a"), recs)
    assert "退出码未知" in (result[0].message or "")


def test_platform_sentinel_exit_surfaces_reason_in_message():
    """观察者落的平台哨兵（容器没能开始运行）→ ERROR，且 reason（stopCode: stoppedReason）进 job message 给使用方看归因。"""
    exited = TaskExited(scope_id="a", exit_code=PLATFORM_FAILED_EXIT,
                        reason="TaskFailedToStart: CannotPullContainerError: not found")
    recs = [EventRecord(scope_id="a", kind="exit", exited=exited)]  # 零事件：容器根本没起
    result = _full(_meta("a"), recs)
    jr = result[0]
    assert jr.status == Status.ERROR
    assert "CannotPullContainerError" in jr.message and "未能启动" in jr.message
    # 哨兵不带原因（本机 worker 真以 255 退出）→ 指向 worker 日志或部署侧日志，不留空 message
    result2 = _full(_meta("a"), [_exit("a", PLATFORM_FAILED_EXIT)])
    assert "部署侧日志" in result2[0].message


def test_platform_exit_reason_joins_stop_code_and_reason_with_fallback():
    """ECS 没给退出码时的归因串只有这一份拼法（观察者与云端 tick 的补写共用，ADR 0034 机制二「退出码缺失」条，另见 ADR 0024「控制面不走
    events 表」条）：两项齐全用「: 」相连，缺一项只用另一项，两项都缺（或为空串）时取固定兜底句、绝不为空。"""
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
    recs = _passed_events("a") + [_timeout_exit("a", 137)]
    result = _full(_meta("a"), recs)
    jr = result[0]
    assert jr.status == Status.ERROR
    assert jr.error_type == "timeout"
    assert "超时" in (jr.message or "")


def test_error_without_reduce_message_gets_default_attribution():
    """worker 起来即崩（非 0 退出、零事件）→ message 不再全空——补默认归因指向 worker 日志
    （detached 实际运行教训：error 无任何线索、只能手工复刻排障）。"""
    recs = [_exit("a", 1)]  # 零事件 + exit 1
    jr = _full(_meta("a"), recs)[0]
    assert jr.status == Status.ERROR
    assert jr.message is not None and "退出码 1" in jr.message


def test_error_clean_exit_incomplete_content_gets_attribution():
    """exit 0 但无 scope_done（矛盾形态）→ 同样有归因文本（不留空白 error）。"""
    recs = [_ev("a", 1, ScopeStarted(scope_id="a", session_id="s")), _exit("a", 0)]
    jr = _full(_meta("a"), recs)[0]
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
    """全 job pending → pending（两个 adapter 据此不写 run 级）；任一 job 推进 → running；恒非终态。"""
    from gherkai_core.project import projected_run_status

    def _jobs(*statuses):
        return {f"s{i}": JobState(f"s{i}", st) for i, st in enumerate(statuses)}

    assert projected_run_status(_jobs(Status.PENDING, Status.PENDING)) == Status.PENDING
    assert projected_run_status(_jobs(Status.PENDING, Status.RUNNING)) == Status.RUNNING
    assert projected_run_status(_jobs(Status.PASSED, Status.PENDING)) == Status.RUNNING
    # 全终态也只到 running：run 级终态只随记下最后一个 job 终态的写或结束写写下（ADR 0030 决定四）
    assert projected_run_status(_jobs(Status.PASSED, Status.FAILED)) == Status.RUNNING


def test_projected_run_status_ignores_the_run_status_from_project():
    """判据只看 job 态：全部 job 都结束时 project() 的 run 级 status 按取法已是终态，投影写仍得 running——守「投影写不能原样落传入的
    run 级值」。还有 job 未结束时 project() 的值本来就是前置态。"""
    from gherkai_core.project import projected_run_status

    done = project(_meta("a", "b"), _passed_events("a") + [_exit("a", 0)] + _passed_events("b") + [_exit("b", 0)])
    assert done.status == Status.PASSED  # 前提：全部 job 都结束，取法给出终态
    assert projected_run_status(done.jobs) == Status.RUNNING
    half = project(_meta("a", "b"), _passed_events("a") + [_exit("a", 0)])
    assert (half.jobs["b"].status, half.status) == (Status.PENDING, Status.RUNNING)  # a 已结束、b 仍 pending：取法给出 running
    assert projected_run_status(half.jobs) == Status.RUNNING


def test_project_run_status_follows_the_rule():
    """project() 的 run 级 status 按取法给出（ADR 0031 决定三「取法」）：有 job 未结束时是前置态，全部 pending 得 pending，
    否则得 running；全部结束时按 error、failed、aborted 或 skipped、passed 的次序取。与投影写落库的取值一致，但投影写不依赖它。"""
    from gherkai_core.project import projected_run_status

    all_pending = project(_meta("a", "b"), [])
    assert all_pending.status == Status.PENDING
    assert projected_run_status(all_pending.jobs) == Status.PENDING

    mixed = project(_meta("a", "b"), [_ev("a", 1, ScopeStarted(scope_id="a", session_id="s"))])
    assert (mixed.jobs["a"].status, mixed.jobs["b"].status) == (Status.RUNNING, Status.PENDING)
    assert mixed.status == Status.RUNNING
    assert projected_run_status(mixed.jobs) == Status.RUNNING

    failed = project(_meta("a", "b"), _passed_events("a") + [_exit("a", 0), _exit("b", 3)])
    assert (failed.jobs["b"].status, failed.status) == (Status.ERROR, Status.ERROR)


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
    """同一组 job 事件分别经同步 schedule 与无状态 project_full，各 job 的判定相同；run 级 status 两边都按同一个取法从 job 的终态
    算出：前台没有记录时经 state_without_record，后台记下终态的写在 adapter 里按 run_status_of。"""
    from gherkai_core.schedule import ScheduleOpts, schedule
    from tests.fake_engine import CollectSink, FakeEngine, FakeResolver

    scopes = [f"j{i}" for i in range(len(outcomes))]
    streams = {s: _scope_events(s, o) for s, o in zip(scopes, outcomes)}
    meta = _meta(*scopes)
    sync = schedule(meta, FakeResolver(FakeEngine(streams)), CollectSink(), opts=ScheduleOpts(max_concurrency=1))
    recs = [_ev(s, i + 1, ev) for s in scopes for i, ev in enumerate(streams[s])] + [_exit(s, 0) for s in scopes]
    stateless = _full(meta, recs)
    assert [jr.status for jr in sync.results] == [jr.status for jr in stateless] == [Status(o) for o in outcomes]
    assert sync.stopped_by is None
    foreground = state_without_record(meta, sync.results, sync.stopped_by, ended_at="t1").status
    assert foreground == run_status_of(jr.status for jr in stateless) == expected


def test_run_totals_agree_between_schedule_and_project_full():
    """两条路径的明细交给同一处组装（assemble_run_result），run 级四个合计键相同。token 跨 job 求和；只有一个 job 报了工作时长且报的
    是 0，run 级照记 0、不当作没报；桌面 run 没有设备计量两键。"""
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
    stateless = _full(meta, recs)

    def totals(details):
        r = assemble_run_result(meta, state_without_record(meta, details, None, ended_at="t1"), details, duration_ms=None)
        return (r.total_tokens, r.total_time_worked_s, r.device_observed_s, r.device_observed_missing)
    assert totals(sync.results) == totals(stateless) == (1500, 0.0, None, None)


def _device_job(scope_id: str) -> Job:
    return replace(_job(scope_id), target=Target(device="android", ui_kind="web"),
                   device_request=DeviceFarmRequest(project_arn="arn:p", os_version="15", billing_method="METERED"))


def test_run_totals_keeps_separate_missing_rules_for_cost_and_device_metering():
    """run_totals 的两组键各守各的缺失语义：成本原生量只合计报了的 job、全无值才为 None、报了 0 照记 0；设备计量对设备 job
    成对合计，某一键缺失按 0 计入，运行定义里没有设备 job 时两键都是 None。"""
    def jr(job: Job, **kw) -> JobResult:
        return JobResult(job=job, status=Status.PASSED, **kw)

    assert run_totals([], jobs=()) == {"total_tokens": None, "total_time_worked_s": None,
                                       "device_observed_s": None, "device_observed_missing": None}
    a, b, c = _job("a"), _job("b"), _job("c")
    zero = run_totals([jr(a), jr(b, total_tokens=0, total_time_worked_s=0.0)], jobs=(a, b))  # 报了 0 不是没报
    assert zero == {"total_tokens": 0, "total_time_worked_s": 0.0, "device_observed_s": None, "device_observed_missing": None}
    mixed = run_totals([jr(a), jr(b, total_tokens=0), jr(c, total_tokens=7, total_time_worked_s=1.5)], jobs=(a, b, c))
    assert (mixed["total_tokens"], mixed["total_time_worked_s"]) == (7, 1.5)
    d1, d2, web = _device_job("d1"), _device_job("d2"), _job("web")
    one_key = run_totals([jr(d1, device_observed_s=3.0), jr(web)], jobs=(d1, web))  # 设备 job 缺的那一键按 0 计入，不是 None
    assert (one_key["device_observed_s"], one_key["device_observed_missing"]) == (3.0, 0)
    device = run_totals([jr(d1, device_observed_s=3.0), jr(d2, device_observed_missing=2), jr(web)], jobs=(d1, d2, web))
    assert (device["device_observed_s"], device["device_observed_missing"]) == (3.0, 2)
    assert (device["total_tokens"], device["total_time_worked_s"]) == (None, None)


def test_run_totals_device_keys_follow_the_definition_when_the_verdict_list_is_incomplete():
    """判定清单不全时（有 job 没有启动），设备计量两键是否出现按运行定义里有没有设备 job 判断（ADR 0054 决策二）：设备 job 全部
    没有启动时两键都是 0、不省键；运行定义里没有设备 job 时仍是 None。成本两键不受影响。"""
    d1, web = _device_job("d1"), _job("web")
    only_web = run_totals([JobResult(job=web, status=Status.PASSED, total_tokens=5)], jobs=(d1, web))
    assert only_web == {"total_tokens": 5, "total_time_worked_s": None, "device_observed_s": 0.0, "device_observed_missing": 0}
    assert isinstance(only_web["device_observed_s"], float)
    nothing_started = run_totals([], jobs=(d1,))
    assert (nothing_started["device_observed_s"], nothing_started["device_observed_missing"]) == (0.0, 0)
    desktop_only = run_totals([], jobs=(web,))
    assert (desktop_only["device_observed_s"], desktop_only["device_observed_missing"]) == (None, None)


def test_run_totals_with_a_complete_verdict_list_matches_the_metered_job_results():
    """判定清单完整时，按运行定义判出现与否和按判定里设备计量两键是否有值判，结果相同：设备 job 的判定由终结流程填上两键，
    桌面 job 的保持 None。两条归约路径产出的 JobResult 都经同一个填法（apply_device_metering）。"""
    d1, web = _device_job("d1"), _job("web")
    results = [JobResult(job=d1, status=Status.PASSED, sessions=[]), JobResult(job=web, status=Status.PASSED)]
    for r in results:
        apply_device_metering(r)
    assert (results[0].device_observed_s, results[0].device_observed_missing) == (0.0, 0)
    assert (results[1].device_observed_s, results[1].device_observed_missing) == (None, None)
    got = run_totals(results, jobs=(d1, web))
    assert (got["device_observed_s"], got["device_observed_missing"]) == (0.0, 0)
    assert run_totals(results[1:], jobs=(web,))["device_observed_s"] is None


# ---------- 被期限截断的 job（ADR 0054 决策二第 2 条、ADR 0031 决定一）----------

def test_stateless_path_yields_aborted_only_for_a_job_cut_by_the_run_deadline():
    """无状态路径不作中止决定：推进器停掉的 job 只带超时标志。被自己的预算截断时判 error 加 timeout；被 run 的期限截断（预算之内
    期限先到）时判 aborted、没有归因，说明是期限那一句——run 的时间用完不是这个 job 自己出错。内容完整的 job 不受影响。"""
    recs = [_ev("a", 1, ScopeStarted(scope_id="a", session_id="s")), _timeout_exit("a", 143)] \
        + _passed_events("b") + [_exit("b", 0)]
    by_budget = {jr.scope_id: jr for jr in _full(_meta("a", "b"), recs)}
    assert (by_budget["a"].status, by_budget["a"].error_type) == (Status.ERROR, "timeout")
    near = replace(_meta("a", "b"), deadline_at=(_CLAIMED + timedelta(seconds=100)).isoformat())  # 预算 300 秒，期限先到
    by_deadline = {jr.scope_id: jr for jr in _full(near, recs)}
    a = by_deadline["a"]
    assert (a.status, a.error_type, a.message) == (Status.ABORTED, None, DEADLINE_TIMEOUT_MESSAGE)
    assert by_deadline["b"].status == Status.PASSED


def test_project_full_timeout_message_is_recomputed_from_the_claim_time():
    """后台被截断的 job 由认领时刻、预算与期限重算是哪一个截止时刻起作用，与前台同一个算法（ADR 0054 决策二第 2 条；判定见
    ADR 0034 机制二「终结函数与真值表」）：认领时刻加预算早于期限是预算到点，记 error 加 timeout；晚于期限是期限到点，记 aborted、
    没有归因，说明是期限那一句；两者相等算预算到点。"""
    deadline = _CLAIMED + timedelta(seconds=300)  # _job 的预算是 300 秒
    recs = [_ev("a", 1, ScopeStarted(scope_id="a", session_id="s")), _timeout_exit("a", None)]

    def jr(claimed: datetime, deadline_at: datetime):
        meta = replace(_meta("a"), deadline_at=deadline_at.isoformat())
        return _full(meta, recs, claimed_at={"a": claimed})[0]

    by_budget = jr(_CLAIMED, deadline + timedelta(seconds=1))
    by_deadline = jr(_CLAIMED + timedelta(seconds=1), deadline)
    tie = jr(_CLAIMED, deadline)
    assert (by_budget.status, by_budget.error_type, by_budget.message) == (Status.ERROR, "timeout", "job 超时（预算 300s，已中止）")
    assert (by_deadline.status, by_deadline.error_type, by_deadline.message) == (Status.ABORTED, None, DEADLINE_TIMEOUT_MESSAGE)
    assert (tie.status, tie.error_type, tie.message) == (by_budget.status, by_budget.error_type, by_budget.message)


def _exited_at(scope_id: str, code: int | None, at: datetime, *, reason: str | None = None) -> EventRecord:
    """只带事实的退出记录：退出码与退出时刻，不带超时标志（本机启动器、云端观察者与启动失败补偿写的形态）。"""
    return EventRecord(scope_id=scope_id, kind="exit",
                       exited=TaskExited(scope_id=scope_id, exit_code=code, reason=reason, exited_at=at))


def test_project_full_judges_an_exit_after_the_cutoff_as_timeout():
    """收尾投影按退出时刻判断是否已过截止时刻（ADR 0054 决策二后台推进条「截止时刻与说明」）：退出时刻严格晚于截止时刻（认领时刻加预算
    300 秒）的退出与带超时标志的同样按超时交给终结函数；恰在截止时刻或之前退出的按退出码归因；内容完整的不改判。"""
    cutoff = _CLAIMED + timedelta(seconds=300)
    started = [_ev("a", 1, ScopeStarted(scope_id="a", session_id="s"))]

    def jr(recs):
        return _full(_meta("a"), recs)[0]

    late = jr(started + [_exited_at("a", 3, cutoff + timedelta(microseconds=1))])
    on_time = jr(started + [_exited_at("a", 3, cutoff)])
    complete = jr(_passed_events("a") + [_exited_at("a", 0, cutoff + timedelta(hours=1))])
    failed_late = jr([_exited_at("a", None, cutoff + timedelta(seconds=1), reason="起 worker 失败：boom")])
    assert (late.status, late.error_type, late.message) == (Status.ERROR, "timeout", "job 超时（预算 300s，已中止）")
    assert (on_time.status, on_time.error_type) == (Status.ERROR, "engine_error")
    assert (complete.status, complete.error_type) == (Status.PASSED, None)
    assert (failed_late.status, failed_late.error_type) == (Status.ERROR, "timeout")


def test_per_round_projection_applies_the_exit_time_rule_when_the_claim_time_is_readable(monkeypatch):
    """每轮的无状态投影交给终结函数的输入与收尾投影一致：基线里这个 job 的认领时刻读得出时，退出时刻晚于截止时刻的退出按超时交给
    终结函数；没有基线、认领时刻缺失或读不出时只看超时标志。运行态只记状态，内容不完整的退出不论哪种都是 error。"""
    import gherkai_core.project as project_mod
    from gherkai_core.model import JobState, RunState

    seen: list[str] = []
    real = project_mod.finalize_job

    def spy(**kw):
        seen.append(kw["stop_reason"])
        return real(**kw)

    monkeypatch.setattr(project_mod, "finalize_job", spy)
    recs = [_ev("a", 1, ScopeStarted(scope_id="a", session_id="s")),
            _exited_at("a", 3, _CLAIMED + timedelta(seconds=301))]

    def stop_reason(claimed_at) -> tuple[str, Status]:
        seen.clear()
        baseline = None if claimed_at is ... else RunState(
            run_id="run-1", status=Status.RUNNING, jobs={"a": JobState("a", Status.RUNNING, claimed_at=claimed_at)})
        state = project(_meta("a"), recs, baseline)
        return seen[-1], state.jobs["a"].status

    assert stop_reason(_CLAIMED.isoformat()) == ("timeout", Status.ERROR)
    assert stop_reason((_CLAIMED + timedelta(seconds=2)).isoformat()) == ("none", Status.ERROR)  # 截止时刻随认领时刻推后
    assert stop_reason(None) == ("none", Status.ERROR)
    assert stop_reason("不是时刻") == ("none", Status.ERROR)
    assert stop_reason(...) == ("none", Status.ERROR)  # 没有基线


def test_project_full_requires_the_claim_time_of_every_recorded_job():
    """有记录的 job 不带认领时刻时 project_full 报错，不回落到预算那一句说明（ADR 0054 决策二后台推进条「快照」）；没有记录的 job
    不需要认领时刻。"""
    recs = _passed_events("a") + [_exit("a", 0)]
    with pytest.raises(ValueError, match="认领时刻"):
        _full(_meta("a", "b"), recs, claimed_at={"b": _CLAIMED})
    assert [jr.scope_id for jr in _full(_meta("a", "b"), recs, claimed_at={"a": _CLAIMED})] == ["a"]


def test_assembled_device_keys_follow_the_definition_when_the_device_job_has_no_detail():
    """后台到期收尾：设备 job 没有记录、project_full 不给它明细，由结束写记 skipped；组装出的 run 结果的设备计量两键按运行定义判
    出现与否，两键为 0、不省键。"""
    meta = RunMeta(run_id="run-1", created_at="2026-07-19T00:00:00Z", jobs=(_device_job("d"), _job("w")),
                   deadline_at=FAR_DEADLINE)
    full = _full(meta, _passed_events("w") + [_exit("w", 0)])
    assert [jr.scope_id for jr in full] == ["w"]
    result = assemble_run_result(meta, state_without_record(meta, full, "deadline", ended_at="t1"), full, duration_ms=None)
    assert result.jobs[0].status == Status.SKIPPED and result.jobs[0].detail is None
    assert (result.device_observed_s, result.device_observed_missing) == (0.0, 0)


# ---------- plan_next（机制四）----------

def _plan(meta: RunMeta, recs, *, max_concurrency: int = 2, past_stop_start: bool = False, baseline=None):
    """plan_next 的输入取法与 tick 相同：投影出的运行态，加事件流里有记录的 scope。"""
    return plan_next(project(meta, recs, baseline), max_concurrency, past_stop_start=past_stop_start,
                     recorded={r.scope_id for r in recs})


def test_plan_next_starts_up_to_concurrency():
    """全 pending、max_concurrency=2 → 提议 start 前 2 个。"""
    actions = _plan(_meta("a", "b", "c"), [])
    starts = [a.scope_id for a in actions if a.kind == "start"]
    assert len(starts) == 2


def test_plan_next_respects_running_slots():
    """已有 1 个 running、max_concurrency=2 → 只补 1 个 pending。"""
    recs = [_ev("a", 1, ScopeStarted(scope_id="a"))]  # a 在 running（scope_started 无 scope_done/exit）
    assert project(_meta("a", "b", "c"), recs).jobs["a"].status == Status.RUNNING
    actions = _plan(_meta("a", "b", "c"), recs)
    starts = [a.scope_id for a in actions if a.kind == "start"]
    assert len(starts) == 1  # 2-1=1 slot
    assert "a" not in starts  # 不重启 running 的


def test_plan_next_finalize_when_all_terminal():
    """所有 job 达终态（无 pending/running）→ 提议 finalize，不论是否已过停止启动的时刻。"""
    recs = _passed_events("a") + [_exit("a", 0)]
    assert _plan(_meta("a"), recs) == [Action(kind="finalize")]
    assert _plan(_meta("a"), recs, past_stop_start=True) == [Action(kind="finalize")]


def test_plan_next_not_finalize_while_running():
    """有 running 时不 finalize（即使有别的 pending 也优先补并发、不收尾）。"""
    recs = [_ev("a", 1, ScopeStarted(scope_id="a"))]
    actions = _plan(_meta("a", "b"), recs)
    assert not any(a.kind == "finalize" for a in actions)


def test_plan_next_past_stop_start_never_proposes_a_start():
    """已过停止启动的时刻（ADR 0054 决策二第 1 条）：不再提议 start；没有执行中的 job、余下的 job 都没有任何记录 → 到期收尾。
    一个 job 都没有启动时同样到期收尾。"""
    done = _passed_events("a") + [_exit("a", 0)]
    assert _plan(_meta("a", "b", "c"), done, past_stop_start=True) == [Action(kind="finalize_expired")]
    assert _plan(_meta("a", "b"), [], past_stop_start=True) == [Action(kind="finalize_expired")]


def test_plan_next_past_stop_start_waits_for_running_jobs():
    """已过停止启动的时刻而还有执行中的 job（事件里见到它在执行，或已被认领、事件还没到）：不收尾、不启动，这一轮继续推进；
    执行中的 job 由它的截止时刻停下，之后再收尾。"""
    from gherkai_core.model import JobState, RunState

    running = [_ev("a", 1, ScopeStarted(scope_id="a"))]
    assert _plan(_meta("a", "b"), running, past_stop_start=True) == []
    claimed = RunState(run_id="run-1", status=Status.RUNNING, high_water_mark=0,
                       jobs={"a": JobState("a", Status.RUNNING), "b": JobState("b", Status.PENDING)})
    assert _plan(_meta("a", "b"), [], past_stop_start=True, baseline=claimed) == []


def test_plan_next_past_stop_start_does_not_expire_while_a_recorded_job_is_still_pending():
    """有记录而投影仍为 pending 的 job（别的推进方刚认领、worker 只发出了结果未知的建会话尝试）说明已经有人启动了它：已过停止启动的
    时刻时这一轮不到期收尾、继续推进。「未启动」只指事件流里没有任何记录的 job。"""
    from gherkai_core.model import SessionOpened

    attempted = [EventRecord(scope_id="b", kind="event", seq=1, event=SessionOpened(scope_id="b", name="t", origin="attempted"),
                             emit_ts=1.0)]
    recs = _passed_events("a") + [_exit("a", 0)] + attempted
    assert project(_meta("a", "b", "c"), recs).jobs["b"].status == Status.PENDING
    assert _plan(_meta("a", "b", "c"), recs, past_stop_start=True) == []
    # 同一快照在没过停止启动的时刻时照常提议 start：pending 的 job 都可提议，认领的条件写挡住已被别人认领的那个
    assert {a.scope_id for a in _plan(_meta("a", "b", "c"), recs)} == {"b", "c"}


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
    """收尾快照里 job 仍 running（只见 scope_started）→ 抛、一份判定都不落，
    绝不把前置态写进 jobs/*.json。"""
    import pytest
    from gherkai_core.project import NonTerminalSnapshot
    recs = [_ev("a", 1, ScopeStarted(scope_id="a", session_id="s"))]
    with pytest.raises(NonTerminalSnapshot):
        _full(_meta("a"), recs)


def test_run_duration_ms_from_run_state_timestamps():
    """后台的 run 级墙钟由运行态的起止算出（ADR 0024「三级执行时长」）：两端都在时为差值；还没结束、没有运行态、时刻读不出或不带
    时区时为 None（报告显示「?」，不让生成报告因它失败）。"""
    def st(started_at, ended_at=None):
        return RunState(run_id="r", status=Status.PASSED, jobs={}, high_water_mark=0, started_at=started_at, ended_at=ended_at)

    assert run_duration_ms(st("2026-09-09T09:40:38.625792+00:00", "2026-09-09T09:42:53.215060+00:00")) == pytest.approx(134589.268)
    assert run_duration_ms(st("2026-09-09T09:40:38+00:00")) is None  # 还没结束
    assert run_duration_ms(None) is None
    assert run_duration_ms(st("t0", "t9")) is None  # 读不出
    assert run_duration_ms(st("2026-09-09T09:40:38", "2026-09-09T09:42:53")) is None  # 不带时区


# ---------- 从记录组装 run 的结果（唯一一处）----------

def _detail(job: Job, status: Status, **kw) -> JobResult:
    return JobResult(job=job, status=status, **kw)


def test_assemble_run_result_lists_every_job_with_its_record_state_and_optional_detail():
    """按运行定义逐个列出 job：状态与 job 级说明取运行态（明细里的状态不作数），由执行结果结束的 job 附上它的明细，由结束写结束的
    job 没有明细；run 级状态与说明取运行态；原生量只由明细合计；墙钟由调用方给出。"""
    meta = _meta("a", "b", "c")
    a, b, c = meta.jobs
    details = [_detail(b, Status.PASSED, total_tokens=7), _detail(a, Status.PASSED, total_tokens=5)]  # 次序与运行定义不同
    state = RunState(run_id="run-1", status=Status.ERROR, message="有 job 出错，余下的 job 不再启动（fail-fast）", jobs={
        "a": JobState("a", Status.PASSED, session_id="s-a"),
        "b": JobState("b", Status.ERROR),  # 运行态与明细不一致时以运行态为准
        "c": JobState("c", Status.SKIPPED, message="fail-fast：其他 job 出错，本 job 没有启动"),
    })
    result = assemble_run_result(meta, state, details, duration_ms=12.5)
    assert [o.scope_id for o in result.jobs] == ["a", "b", "c"]
    assert [o.status for o in result.jobs] == [Status.PASSED, Status.ERROR, Status.SKIPPED]
    assert [o.detail for o in result.jobs] == [details[1], details[0], None]
    assert result.jobs[2].state.message == "fail-fast：其他 job 出错，本 job 没有启动"
    assert result.details == [details[1], details[0]]  # 按运行定义的次序
    assert (result.status, result.message, result.state) == (Status.ERROR, state.message, state)
    assert (result.duration_ms, result.total_tokens, result.total_time_worked_s) == (12.5, 12, None)
    assert (result.device_observed_s, result.device_observed_missing) == (None, None)


def test_assemble_run_result_ignores_details_outside_the_definition_and_requires_every_job_in_the_state():
    """不在运行定义里的明细不出现；运行定义里的 job 不在运行态里时抛 ValueError（运行态与运行定义不对应）。"""
    meta = _meta("a")
    ghost = _detail(_job("ghost"), Status.PASSED, total_tokens=99)
    state = RunState(run_id="run-1", status=Status.ABORTED, jobs={"a": JobState("a", Status.SKIPPED)})
    result = assemble_run_result(meta, state, [ghost], duration_ms=None)
    assert [(o.scope_id, o.detail) for o in result.jobs] == [("a", None)] and result.total_tokens is None
    with pytest.raises(ValueError, match="运行态里没有"):
        assemble_run_result(_meta("a", "b"), state, [], duration_ms=None)


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
    result = _full(_meta("a"), recs)
    st = result[0].scenarios[0].steps[0]
    assert st.status == Status.FAILED and st.message == "AI 断言未过多数票（0/1）：x"


# ---------- 未完成 scenario 的事件流投影（ADR 0042 决策七）----------

def test_recover_from_events_returns_scenarios_absent_from_the_verdict_with_their_step_records():
    """三条 scenario：A 完整（有 scenario_done 且已在判定真值里，不补）；B 被中止在第三步（两条 step_done、一条只有 step_started）；
    C 零事件。补取只给 B（status None 即未完成），且 B 只含两条有 step_done 的 step，字段（含 report_refs）与归约路径一致；不写判定、
    不看退出记录。判定真值里**没有** A 时（同步 run 在归约前退出），A 也补取、带事件流里的 scenario 判定。"""
    from gherkai_core.model import ReportRef, StepDone, StepStarted, ScenarioStarted, Votes
    steps = tuple(Step(index=i, keyword="When", text=f"s{i}") for i in range(3))
    job = Job(scope_id="a", scope_name="a", engine="novaact", scenarios=(
        Scenario(id="a:A", name="A", steps=steps), Scenario(id="a:B", name="B", steps=steps), Scenario(id="a:C", name="C", steps=steps)), timeout_s=300.0)
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
        Scenario(id="a:B", name="B", steps=steps), Scenario(id="a:C", name="C", steps=steps)), timeout_s=300.0)
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
