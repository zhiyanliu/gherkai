"""schedule 模块测试（ADR 0026）：并发归约 + 失败隔离 + fail-fast + 超时 + 优雅停 + 运行期限与这次 run 的记录（ADR 0054）。

用内存假 Engine（不起子进程）+ 假时间（不真等），验证 schedule 逻辑。job 的截止时刻按墙钟比较、排空与时长按单调时钟计，测超时的用例
用 `_FakeTime` 同时注入两者，在确定的时点推进时间（事件触发、钩子或每读前进），不数时钟被读了几次。

schedule 返回执行事实（`Execution`：判出结果的 job、余下的 job 不再启动的来源、墙钟时长），不给 run 的状态。断言 run 级状态、说明、
合计与没有启动的 job 记成什么的用例经 `_summary`：没有记录的执行按同一套规则在内存里给出的 run 结果（`run --no-report` 同一条路径）。
"""
from __future__ import annotations

import threading
from datetime import datetime, timedelta, timezone

import pytest

from gherkai_core.model import (
    RunMeta,
    Cost,
    DeviceFarmRequest,
    Job,
    ReportRef,
    ResourceUri,
    Scenario,
    ScenarioDone,
    ScenarioStarted,
    ScopeDone,
    ScopeStarted,
    Status,
    Step,
    StepDone,
    StepStarted,
    Target,
    Votes,
)
from gherkai_core.model import RunResult
from gherkai_core.persist import result_without_record
from gherkai_core.run_status import RUN_ENDINGS
from gherkai_core.schedule import Execution, ScheduleOpts, schedule
from tests.fake_engine import FAR_DEADLINE, CollectSink, FakeEngine, FakeResolver


class _IncClock:
    """确定性递增时钟：每次调用 +step（默认 1.0）。用于精确测时长。"""

    def __init__(self, step: float = 1.0) -> None:
        self.t = 0.0
        self.step = step

    def __call__(self) -> float:
        self.t += self.step
        return self.t


_T0 = datetime(2030, 1, 1, tzinfo=timezone.utc)  # 假墙钟的零点（远早于 FAR_DEADLINE）


def _summary(ex: Execution) -> RunResult:
    """没有记录的执行在内存里按同一套规则给出的 run 结果：判出结果的 job 记终态，余下的 job 按 ex.stopped_by 这条来路的结束写结束。"""
    return result_without_record(ex, ended_at=_T0.isoformat())


def _outcome(ex: Execution, scope_id: str):
    """run 结果里某个 job 的那一项（状态取运行态，有判定明细的另带明细）。"""
    return next(o for o in _summary(ex).jobs if o.scope_id == scope_id)


class _FakeTime:
    """一份假时间、两个读法：mono() 注入 ScheduleOpts.clock，每读一次前进 step 秒；wall() 注入 ScheduleOpts.wall_clock，读同一份时间、
    不前进。jump(s) 让时间立即前进 s 秒；n 是单调时钟被读的次数。用 opts(...) 构造同时注入两个时钟的 ScheduleOpts。"""

    def __init__(self, step: float = 0.001) -> None:
        self.t = 0.0
        self.step = step
        self.n = 0

    def mono(self) -> float:
        self.n += 1
        self.t += self.step
        return self.t

    def wall(self) -> datetime:
        return _T0 + timedelta(seconds=self.t)

    def jump(self, seconds: float) -> None:
        self.t += seconds

    def at(self, seconds: float) -> str:
        """假墙钟零点之后 seconds 秒的时刻（记录里的写法），用来给 RunMeta 一个贴近假时间的期限。"""
        return (_T0 + timedelta(seconds=seconds)).isoformat()

    def opts(self, **kw) -> ScheduleOpts:
        return ScheduleOpts(clock=self.mono, wall_clock=self.wall, **kw)


class _JumpSink(CollectSink):
    """sink 见到 trigger 类型的事件时让假时间前进 seconds 秒：sink 在 worker 的事件循环里、这条事件的检查之后被调，所以下一次检查
    （下一条事件或心跳）看到的是越过截止时刻的时间。触发点按事件认，不按时钟被读的次数推算。"""

    def __init__(self, time: _FakeTime, trigger: type, seconds: float = 1000.0):
        super().__init__()
        self.time, self.trigger, self.seconds = time, trigger, seconds
        self.fired = False

    def __call__(self, event) -> None:
        super().__call__(event)
        if isinstance(event, self.trigger) and not self.fired:
            self.fired = True
            self.time.jump(self.seconds)


def _job(scope_id: str, engine: str = "midscene", n_scenarios: int = 1, timeout_s: float = 7200.0,
         device: str = "desktop") -> Job:
    scenarios = tuple(
        Scenario(id=f"{scope_id}:{i}", name=f"sc{i}", steps=(Step(0, "When", "做事"),))
        for i in range(n_scenarios)
    )
    # 设备目标带完整的设备请求（与 definition 的结构校验一致）；缺省是桌面网页
    target = {} if device == "desktop" else dict(target=Target(device=device, ui_kind="web"),
                                                 device_request=DeviceFarmRequest(project_arn="arn:p", os_version="15", billing_method="METERED"))
    return Job(scope_id=scope_id, scope_name=scope_id, engine=engine, scenarios=scenarios, timeout_s=timeout_s, **target)


def _rm(jobs: list[Job], run_id: str = "test-run") -> RunMeta:
    """测试用：把 Job[] 包成 RunMeta（definition）喂 schedule（ADR 0016）。"""
    return RunMeta(run_id=run_id, created_at="", jobs=tuple(jobs), deadline_at=FAR_DEADLINE)


def _passing_events(scope_id: str, scenario_id: str) -> list:
    # 末尾必带 scope_done——真实 worker 契约（ADR 0024）：正常完成必发；EOF 落归约终态以它为前提（0026）。
    return [
        ScenarioStarted(scenario_id=scenario_id),
        StepDone(scenario_id=scenario_id, step_index=0, status=Status.PASSED, votes=Votes(3, 3)),
        ScenarioDone(scenario_id=scenario_id, status=Status.PASSED),
        ScopeDone(scope_id=scope_id),
    ]


def _failing_events(scope_id: str, scenario_id: str) -> list:
    return [
        ScenarioStarted(scenario_id=scenario_id),
        StepDone(scenario_id=scenario_id, step_index=0, status=Status.FAILED, votes=Votes(1, 3),
                 error_type="assertion_failed", message="没过多数票"),
        ScenarioDone(scenario_id=scenario_id, status=Status.FAILED),
        ScopeDone(scope_id=scope_id),
    ]


# ---- 正常归约：全 passed → RunResult passed ----
def test_all_pass():
    jobs = [_job("a"), _job("b")]
    engine = FakeEngine({
        "a": _passing_events("a", "a:0"),
        "b": _passing_events("b", "b:0"),
    })
    sink = CollectSink()
    result = schedule(_rm(jobs), FakeResolver(engine), sink)
    assert _summary(result).status == Status.PASSED
    assert len(result.results) == 2
    assert all(jr.status == Status.PASSED for jr in result.results)
    # sink 收到所有事件（2 job × 4 事件，含 scope_done）
    assert len(sink.events) == 8


# ---- 断言失败 → RunResult failed（区别于 error）----
def test_assertion_failed_is_failed_not_error():
    jobs = [_job("a")]
    engine = FakeEngine({"a": _failing_events("a", "a:0")})
    result = schedule(_rm(jobs), FakeResolver(engine), CollectSink())
    assert _summary(result).status == Status.FAILED
    assert result.results[0].status == Status.FAILED
    assert result.results[0].scenarios[0].status == Status.FAILED


# ---- 失败隔离（默认）：一个 job 崩(error)，其余照常运行 ----
def test_failure_isolation_default():
    jobs = [_job("crash"), _job("ok")]
    engine = FakeEngine(
        behaviors={
            "crash": _passing_events("crash", "crash:0"),
            "ok": _passing_events("ok", "ok:0"),
        },
        crash_after={"crash": 1},  # crash job 在第 1 个事件后崩
    )
    result = schedule(_rm(jobs), FakeResolver(engine), CollectSink())
    # 默认隔离：crash → error，ok 照样 passed
    crash_jr = next(jr for jr in result.results if jr.scope_id == "crash")
    ok_jr = next(jr for jr in result.results if jr.scope_id == "ok")
    assert crash_jr.status == Status.ERROR
    assert crash_jr.error_type == "engine_error"
    assert ok_jr.status == Status.PASSED  # 未受牵连
    assert _summary(result).status == Status.ERROR  # 总状态：有 error


# ---- fail-fast：一个 job 崩 → run 判 ERROR（中止生效）----
# 注：fail-fast 对「在运行的其余 worker」是协作式中止，多 worker 的精确结局依赖线程时序
# （slow 可能已完成/被拦在启动前/运行到一半被 stop——都合法），故此处只断言确定性保证：
# run 判 ERROR + crash 一定 error。stop() 的调用路径由 test_timeout_with_fake_clock 确定性覆盖。
def test_fail_fast_batch_errors():
    def long_stream(scenario_id):
        evs = [ScenarioStarted(scenario_id=scenario_id)]
        for i in range(50):
            evs.append(StepDone(scenario_id=scenario_id, step_index=i, status=Status.PASSED, votes=Votes(3, 3)))
        evs.append(ScenarioDone(scenario_id=scenario_id, status=Status.PASSED))
        evs.append(ScopeDone(scope_id=scenario_id.split(":")[0]))  # 完整运行结束必带（内容完整前置，0026）
        return evs

    jobs = [_job("crash"), _job("slow")]
    engine = FakeEngine(
        behaviors={
            "crash": _passing_events("crash", "crash:0"),
            "slow": long_stream("slow:0"),
        },
        crash_after={"crash": 0},  # crash 立刻崩
    )
    result = schedule(
        _rm(jobs), FakeResolver(engine), CollectSink(),
        opts=ScheduleOpts(max_concurrency=2, fail_fast=True),
    )
    assert _summary(result).status == Status.ERROR  # 确定性：run 判错
    crash_jr = next(jr for jr in result.results if jr.scope_id == "crash")
    assert crash_jr.status == Status.ERROR
    # 被牵连的 slow：协作式中止下结局依时序（已完成 passed / 运行到一半 aborted / 排队没起、由结束写记 skipped 都合法），
    # 但**绝不该是 error**——被牵连中止不是自身故障（ADR 0031；精确的 skipped/aborted 复现见 test_lifecycle_states）。
    # 注：PASSED 只在「见到 scope_done（真正完成）」时可达——运行到一半被掐、流 EOF 无 scope_done 必 ABORTED
    # （内容完整前置，0026），此断言不再可能掩盖「部分完成聚合成 PASSED」的假绿。
    slow = _outcome(result, "slow")
    assert slow.status in (Status.PASSED, Status.ABORTED, Status.SKIPPED)
    if slow.detail is None:  # 没有启动：不在执行事实里，来路是 fail-fast
        assert slow.status == Status.SKIPPED and result.stopped_by == "fail-fast"


# ---- fail-fast 关闭（默认隔离）对照：crash 崩但 slow 运行结束 → ERROR 但 slow passed ----
def test_no_fail_fast_lets_others_finish():
    jobs = [_job("crash"), _job("ok")]
    engine = FakeEngine(
        behaviors={
            "crash": _passing_events("crash", "crash:0"),
            "ok": _passing_events("ok", "ok:0"),
        },
        crash_after={"crash": 0},
    )
    result = schedule(_rm(jobs), FakeResolver(engine), CollectSink(), opts=ScheduleOpts(fail_fast=False))
    ok_jr = next(jr for jr in result.results if jr.scope_id == "ok")
    assert ok_jr.status == Status.PASSED  # 隔离：ok 运行结束


# ---- 超时（fake clock）：job 运行太久 → stop + error:timeout ----
def test_timeout_with_fake_clock():
    # 假时间：单调时钟每被读一次前进 10 秒（每个事件的时长归约读一次），job 预算 5 秒 → 第一个事件处理完之后的那次事件间检查就超时
    ft = _FakeTime(step=10.0)

    # 慢流：多个事件，每个事件推进一次时间
    long_events = [ScenarioStarted(scenario_id="slow:0")]
    for i in range(5):
        long_events.append(StepDone(scenario_id="slow:0", step_index=i, status=Status.PASSED, votes=Votes(3, 3)))
    long_events.append(ScenarioDone(scenario_id="slow:0", status=Status.PASSED))

    jobs = [_job("slow", timeout_s=5.0)]
    engine = FakeEngine({"slow": long_events})
    result = schedule(
        _rm(jobs), FakeResolver(engine), CollectSink(),
        opts=ft.opts(grace_period_s=2.0),
    )
    assert _summary(result).status == Status.ERROR
    assert result.results[0].error_type == "timeout"
    assert result.results[0].message == "job 超时（预算 5s，已中止）"  # 被自己的预算截断：原有的超时说明
    # 超时后 stop 被调，且传了 grace_period
    assert engine.handles["slow"].stopped
    assert engine.handles["slow"].stop_grace == 2.0


# ---- 起 worker 失败（engine resolver/run_scope 抛异常）→ job error，不拖垮 ----
def test_engine_start_failure():
    class BoomEngine:
        def run_scope(self, job):
            raise RuntimeError("spawn 失败")

    jobs = [_job("a"), _job("b")]
    # a 用 boom，b 正常 —— 但 FakeResolver 只给一个 engine，这里换个 resolver
    boom = BoomEngine()
    good = FakeEngine({"b": _passing_events("b", "b:0")})

    def resolver(name):
        return boom if name == "boom_engine" else good

    jobs = [_job("a", engine="boom_engine"), _job("b", engine="good")]
    result = schedule(_rm(jobs), resolver, CollectSink())
    a_jr = next(jr for jr in result.results if jr.scope_id == "a")
    b_jr = next(jr for jr in result.results if jr.scope_id == "b")
    assert a_jr.status == Status.ERROR
    assert "起 worker 失败" in a_jr.message
    assert b_jr.status == Status.PASSED  # 隔离：b 不受 a 影响


# ---- 输出顺序与输入 jobs 顺序一致（即便完成序不同）----
def test_output_order_stable():
    jobs = [_job("z"), _job("a"), _job("m")]
    engine = FakeEngine({
        "z": _passing_events("z", "z:0"),
        "a": _passing_events("a", "a:0"),
        "m": _passing_events("m", "m:0"),
    })
    result = schedule(_rm(jobs), FakeResolver(engine), CollectSink())
    assert [jr.scope_id for jr in result.results] == ["z", "a", "m"]


# ---- cost 归约：core 只各自合计 engine 报的原生量（tokens / time_worked_s），不算美元 ----
def _events_with_time(scenario_id: str, step_times: list[float]) -> list:
    """Nova 形态：每 step 报原生量 time_worked_s。"""
    evs = [ScenarioStarted(scenario_id=scenario_id)]
    for i, t in enumerate(step_times):
        evs.append(StepDone(
            scenario_id=scenario_id, step_index=i, status=Status.PASSED,
            cost=Cost(time_worked_s=t),
        ))
    evs.append(ScenarioDone(scenario_id=scenario_id, status=Status.PASSED))
    return evs


def _events_with_tokens(scenario_id: str, step_tokens: list[int]) -> list:
    """Midscene 形态：每 step 报原生量 tokens。"""
    evs = [ScenarioStarted(scenario_id=scenario_id)]
    for i, t in enumerate(step_tokens):
        evs.append(StepDone(
            scenario_id=scenario_id, step_index=i, status=Status.PASSED,
            cost=Cost(tokens=t),
        ))
    evs.append(ScenarioDone(scenario_id=scenario_id, status=Status.PASSED))
    return evs


def test_time_worked_aggregation_step_to_job_to_run():
    # Nova 形态：time_worked_s 累加 step→scope→run
    engine = FakeEngine({
        "a": _events_with_time("a:0", [9.0, 3.0]),   # scope a 合计 12.0s
        "b": _events_with_time("b:0", [5.0]),         # scope b 合计 5.0s
    })
    result = schedule(_rm([_job("a"), _job("b")]), FakeResolver(engine), CollectSink())
    a_jr = next(jr for jr in result.results if jr.scope_id == "a")
    b_jr = next(jr for jr in result.results if jr.scope_id == "b")
    assert abs(a_jr.total_time_worked_s - 12.0) < 1e-9
    assert abs(b_jr.total_time_worked_s - 5.0) < 1e-9
    assert abs(_summary(result).total_time_worked_s - 17.0) < 1e-9  # run 级跨 scope 合计
    assert _summary(result).total_tokens is None  # Nova 引擎不报 token


def test_token_aggregation():
    # Midscene 形态：tokens 累加
    engine = FakeEngine({"m": _events_with_tokens("m:0", [1000, 500])})
    result = schedule(_rm([_job("m")]), FakeResolver(engine), CollectSink())
    m_jr = result.results[0]
    assert m_jr.total_tokens == 1500
    assert m_jr.total_time_worked_s is None  # Midscene 不报时长
    assert _summary(result).total_tokens == 1500
    assert _summary(result).total_time_worked_s is None


def test_cost_none_when_no_cost_data():
    # 无 cost 的事件流 → 两个原生量合计都保持 None（不假装 0）
    engine = FakeEngine({"a": _passing_events("a", "a:0")})
    result = schedule(_rm([_job("a")]), FakeResolver(engine), CollectSink())
    assert result.results[0].total_tokens is None
    assert result.results[0].total_time_worked_s is None
    assert _summary(result).total_tokens is None
    assert _summary(result).total_time_worked_s is None


def test_mixed_legs_each_native_metric_aggregated_separately():
    # 混引擎：nova 报 time_worked_s、midscene 报 tokens → 各自合计、互不污染、都不丢
    engine = FakeEngine({
        "nova": _events_with_time("nova:0", [9.0]),
        "mid": _events_with_tokens("mid:0", [2000]),
    })
    result = schedule(_rm([_job("nova"), _job("mid")]), FakeResolver(engine), CollectSink())
    nova_jr = next(jr for jr in result.results if jr.scope_id == "nova")
    mid_jr = next(jr for jr in result.results if jr.scope_id == "mid")
    assert abs(nova_jr.total_time_worked_s - 9.0) < 1e-9 and nova_jr.total_tokens is None
    assert mid_jr.total_tokens == 2000 and mid_jr.total_time_worked_s is None
    # run 级：两个原生量各自合计，都不被静默漏掉
    assert abs(_summary(result).total_time_worked_s - 9.0) < 1e-9
    assert _summary(result).total_tokens == 2000


def test_failed_and_error_steps_cost_still_aggregated():
    # 失败/出错的 step 也真实产生了费用（act/投票照样消耗时长 token）→ cost 仍累加，不漏报成本。
    events = [
        ScenarioStarted(scenario_id="x:0"),
        # 失败的 AI 断言步带 cost
        StepDone(scenario_id="x:0", step_index=0, status=Status.FAILED,
                 votes=Votes(1, 3), error_type="assertion_failed", cost=Cost(tokens=1200)),
        # 出错的 step 带 cost
        StepDone(scenario_id="x:0", step_index=1, status=Status.ERROR,
                 error_type="engine_error", cost=Cost(tokens=800)),
        ScenarioDone(scenario_id="x:0", status=Status.ERROR),
    ]
    engine = FakeEngine({"x": events})
    result = schedule(_rm([_job("x")]), FakeResolver(engine), CollectSink())
    jr = result.results[0]
    assert jr.status == Status.ERROR        # 状态如实反映失败
    assert jr.total_tokens == 2000          # 但失败步消耗的 token 仍计入（1200+800）
    assert _summary(result).total_tokens == 2000


# ---- 并发上限：max_concurrency=1 → 串行，仍全部运行完成 ----
def test_serial_concurrency_one():
    jobs = [_job(f"j{i}") for i in range(5)]
    engine = FakeEngine({f"j{i}": _passing_events(f"j{i}", f"j{i}:0") for i in range(5)})
    result = schedule(_rm(jobs), FakeResolver(engine), CollectSink(), opts=ScheduleOpts(max_concurrency=1))
    assert _summary(result).status == Status.PASSED
    assert len(result.results) == 5


# ---- 三级执行时长：core 基于 started/done 事件到达时间戳算（ADR 0024）----
def _full_timed_events(scope_id: str, scenario_id: str, n_steps: int = 2) -> list:
    """完整 started/done 三级配对事件流（含 scope/step started）。"""
    evs: list = [ScopeStarted(scope_id=scope_id), ScenarioStarted(scenario_id=scenario_id)]
    for i in range(n_steps):
        evs.append(StepStarted(scenario_id=scenario_id, step_index=i))
        evs.append(StepDone(scenario_id=scenario_id, step_index=i, status=Status.PASSED))
    evs.append(ScenarioDone(scenario_id=scenario_id, status=Status.PASSED))
    evs.append(ScopeDone(scope_id=scope_id, session_id="s"))
    return evs


def test_three_level_durations():
    # 递增 clock（每事件到达 +1.0s）+ 完整 started/done 流 → core 算出三级时长。
    # 预算取上限 7200 秒、远不会到点，时长可预期且层级嵌套。
    engine = FakeEngine({"sc": _full_timed_events("sc", "sc:0", n_steps=2)})
    result = schedule(
        _rm([_job("sc")]), FakeResolver(engine), CollectSink(),
        opts=ScheduleOpts(clock=_IncClock(1.0)),  # 单位秒；core 乘 1000 → ms
    )
    jr = result.results[0]
    sr = jr.scenarios[0]
    # 每个 step 有时长，且 > 0
    assert len(sr.steps) == 2
    assert all(s.duration_ms is not None and s.duration_ms > 0 for s in sr.steps)
    # 层级嵌套：step ≤ scenario ≤ scope（scenario 含其所有 step + started/done 间隔）
    assert sr.duration_ms is not None and jr.duration_ms is not None
    assert max(s.duration_ms for s in sr.steps) <= sr.duration_ms
    assert sr.duration_ms <= jr.duration_ms
    # run 级时长由 schedule 整体包住（独立于 worker 事件，故 > 0）
    assert result.duration_ms is not None and result.duration_ms > 0
    # step 索引保序
    assert [s.index for s in sr.steps] == [0, 1]


def test_durations_none_without_started_events():
    # 旧式事件流（无 started 事件）→ 时长字段为 None（不报错、不假装）
    engine = FakeEngine({"a": _passing_events("a", "a:0")})  # 无 ScopeStarted/StepStarted
    result = schedule(_rm([_job("a")]), FakeResolver(engine), CollectSink(), opts=ScheduleOpts(clock=_IncClock()))
    jr = result.results[0]
    assert jr.duration_ms is None                      # 无 scope_started
    assert jr.scenarios[0].steps == [] or all(
        s.duration_ms is None for s in jr.scenarios[0].steps
    )  # 无 step_started → step 时长 None（且本流无 step_started，step 也没被记）


# ---- scope 级 reportRefs 从 scope_done 归约进 JobResult（Midscene report，ADR 0024）----
def test_scope_report_refs_reduced():
    events = [
        ScenarioStarted(scenario_id="m:0"),
        StepDone(scenario_id="m:0", step_index=0, status=Status.PASSED),
        ScenarioDone(scenario_id="m:0", status=Status.PASSED),
        ScopeDone(scope_id="m", session_id="sess-1",
                  report_refs=(ReportRef(kind="report", ref=ResourceUri("file:///midscene_run/report/x.html")),)),
    ]
    engine = FakeEngine({"m": events})
    result = schedule(_rm([_job("m")]), FakeResolver(engine), CollectSink())
    jr = result.results[0]
    assert len(jr.report_refs) == 1
    assert jr.report_refs[0].kind == "report"
    assert jr.report_refs[0].ref == "file:///midscene_run/report/x.html"


# ---- step 级 reportRefs 从 step_done 归约进 StepResult（Nova trajectory 下沉，ADR 0027）----
def test_step_report_refs_reduced():
    events = [
        ScenarioStarted(scenario_id="n:0"),
        StepDone(scenario_id="n:0", step_index=0, status=Status.PASSED, report_refs=(
            ReportRef(kind="trajectory", ref=ResourceUri("file:///t/act_0.html"), label="trajectory 1"),
            ReportRef(kind="trajectory", ref=ResourceUri("file:///t/act_1.html"), label="trajectory 2"),
        )),
        StepDone(scenario_id="n:0", step_index=1, status=Status.PASSED),  # 无 trajectory（如确定性步）
        ScenarioDone(scenario_id="n:0", status=Status.PASSED),
        ScopeDone(scope_id="n", session_id="sess-n"),
    ]
    engine = FakeEngine({"n": events})
    result = schedule(_rm([_job("n")]), FakeResolver(engine), CollectSink())
    steps = result.results[0].scenarios[0].steps
    # step 0 挂两个 trajectory、原样搬入不聚合到 scenario 级
    assert len(steps[0].report_refs) == 2 and steps[0].report_refs[0].kind == "trajectory"
    assert steps[1].report_refs == ()  # 无产物步为空
    assert result.results[0].scenarios[0].report_refs == ()  # 不再聚合到 scenario 级


# ---- scope 内短路：StepSkipped 归约进 StepResult(SKIPPED, shortcircuited=True)（ADR 0031 决定六）----
def test_step_skipped_reduced_to_skipped_shortcircuited():
    # worker 上游 step error 后短路后续 step，发 step_skipped；core 建 StepResult(SKIPPED, shortcircuited=True)。
    from gherkai_core.model import StepSkipped
    events = [
        ScenarioStarted(scenario_id="n:0"),
        StepStarted(scenario_id="n:0", step_index=0),
        StepDone(scenario_id="n:0", step_index=0, status=Status.ERROR, error_type="network_error"),
        StepSkipped(scenario_id="n:0", step_index=1),  # 被短路
        StepSkipped(scenario_id="n:0", step_index=2),  # 被短路
        ScenarioDone(scenario_id="n:0", status=Status.ERROR),  # scenario 判定由那个 error step 决定
        ScopeDone(scope_id="n", session_id="sess-n"),
    ]
    engine = FakeEngine({"n": events})
    result = schedule(_rm([_job("n")]), FakeResolver(engine), CollectSink())
    steps = result.results[0].scenarios[0].steps
    assert len(steps) == 3
    # step 0：实际执行产生的 error
    assert steps[0].status == Status.ERROR and steps[0].shortcircuited is False
    # step 1/2：被短路 → SKIPPED + shortcircuited=True（正交轴），未执行 → 无墙钟
    assert steps[1].status == Status.SKIPPED and steps[1].shortcircuited is True
    assert steps[2].status == Status.SKIPPED and steps[2].shortcircuited is True
    assert steps[1].duration_ms is None  # 被短路步没开始运行（无 step_started）→ 无墙钟


def test_step_skipped_does_not_pollute_scenario_or_run_status():
    # 关键不变量（ADR 0031 决定六）：step 级 SKIPPED 绝不写 scenario_status → 不参与 scenario 归约/severity。
    # 一个 [error, skipped, skipped] 的 scenario，其 scenario/job/run 判定必须是 error（skipped 零污染），
    # 且不会被 SKIPPED 拉低（severity -1）也不会误当 passed。
    from gherkai_core.model import StepSkipped
    events = [
        ScenarioStarted(scenario_id="n:0"),
        StepDone(scenario_id="n:0", step_index=0, status=Status.ERROR, error_type="network_error"),
        StepSkipped(scenario_id="n:0", step_index=1),
        ScenarioDone(scenario_id="n:0", status=Status.ERROR),
        ScopeDone(scope_id="n"),
    ]
    engine = FakeEngine({"n": events})
    result = schedule(_rm([_job("n")]), FakeResolver(engine), CollectSink())
    assert result.results[0].scenarios[0].status == Status.ERROR  # scenario 判定是 error（未被 skipped 影响）
    assert result.results[0].status == Status.ERROR               # job 判定是 error
    assert _summary(result).status == Status.ERROR                        # run 判定是 error


def test_step_skipped_without_scenario_done_still_recorded():
    # 兜底：即便 scenario_done 缺席（worker 中途被停），已归约的 skipped step 也不该丢——
    # 它们暂存在 timing.steps，只在 scenario_done 才挂入 scenarios。此处验证有 scenario_done 时挂入正确。
    # （无 scenario_done 的挂入由 schedule 既有兜底逻辑覆盖，非本 ADR 引入，不重复测。）
    from gherkai_core.model import StepSkipped
    events = [
        ScenarioStarted(scenario_id="n:0"),
        StepDone(scenario_id="n:0", step_index=0, status=Status.ERROR, error_type="engine_error"),
        StepSkipped(scenario_id="n:0", step_index=1),
        ScenarioDone(scenario_id="n:0", status=Status.ERROR),
        ScopeDone(scope_id="n"),
    ]
    engine = FakeEngine({"n": events})
    result = schedule(_rm([_job("n")]), FakeResolver(engine), CollectSink())
    steps = result.results[0].scenarios[0].steps
    assert [s.status for s in steps] == [Status.ERROR, Status.SKIPPED]
    assert steps[1].shortcircuited is True


# ---- 网络瞬时故障的 job 级重试（ADR 0028）----

_NOSLEEP = lambda _s: None  # 注入 no-op sleep，保单测不真等


def test_network_error_retried_then_succeeds():
    # 前两次 attempt 建连失败（零事件），第三次成功 → job 重试后 passed
    sid = "n:0"
    engine = FakeEngine(
        {"n": _passing_events("n", sid)},
        network_crash_after={"n": [0, 0]},  # attempt 0/1 崩（第0个事件前），attempt 2 不在 list→成功
    )
    result = schedule(_rm([_job("n")]), FakeResolver(engine), CollectSink(),
                      opts=ScheduleOpts(network_retry=2, retry_sleep=_NOSLEEP))
    assert _summary(result).status == Status.PASSED
    assert engine.run_count["n"] == 3  # 起了 3 次 worker（2 次重试）


def test_network_error_exhausted_is_network_error():
    # 每次 attempt 都建连失败 → 重试耗尽 → job error_type=network_error
    engine = FakeEngine({"n": _passing_events("n", "n:0")}, network_crash_after={"n": 0})
    result = schedule(_rm([_job("n")]), FakeResolver(engine), CollectSink(),
                      opts=ScheduleOpts(network_retry=2, retry_sleep=_NOSLEEP))
    assert _summary(result).status == Status.ERROR
    assert result.results[0].error_type == "network_error"
    assert engine.run_count["n"] == 3  # network_retry=2 → 总 3 次


def test_network_error_not_retried_when_session_started():
    # 会话已起（已 emit 过 step_done）后才网络崩 → 不 job 级重试（防重复副作用，ADR 0028）
    sid = "n:0"
    events = [
        ScenarioStarted(scenario_id=sid),
        StepDone(scenario_id=sid, step_index=0, status=Status.PASSED, votes=Votes(3, 3)),
    ]
    engine = FakeEngine({"n": events}, network_crash_after={"n": 2})  # 第2个事件后崩（已过 step_done）
    result = schedule(_rm([_job("n")]), FakeResolver(engine), CollectSink(),
                      opts=ScheduleOpts(network_retry=2, retry_sleep=_NOSLEEP))
    assert _summary(result).status == Status.ERROR
    assert result.results[0].error_type == "network_error"
    assert engine.run_count["n"] == 1  # 会话已起 → 不重试，只运行 1 次


def test_network_retry_default_off():
    # 默认 network_retry=0 → 网络崩不重试，记 network_error
    engine = FakeEngine({"n": _passing_events("n", "n:0")}, network_crash_after={"n": 0})
    result = schedule(_rm([_job("n")]), FakeResolver(engine), CollectSink())
    assert _summary(result).status == Status.ERROR
    assert result.results[0].error_type == "network_error"
    assert engine.run_count["n"] == 1  # 默认不重试


def test_non_network_crash_not_retried():
    # 普通 worker 崩（engine_error）即使开了 network_retry 也不重试
    engine = FakeEngine({"n": _passing_events("n", "n:0")}, crash_after={"n": 0})
    result = schedule(_rm([_job("n")]), FakeResolver(engine), CollectSink(),
                      opts=ScheduleOpts(network_retry=2, retry_sleep=_NOSLEEP))
    assert _summary(result).status == Status.ERROR
    assert result.results[0].error_type == "engine_error"
    assert engine.run_count["n"] == 1  # engine_error 不重试


def test_network_retry_deadline_not_reset_across_attempts():
    # job timeout 跨 attempt 不重置（ADR 0028）：截止时刻在认领时算出（认领时刻加预算），重试共享。退避消耗的时间计入墙钟
    # （假 sleep 让假时间前进退避的秒数），timeout_s=2.5 → 第一次退避 2 秒后仍在截止时刻之前、第二次退避 4 秒后已过 → 记 timeout
    # （不再无限重试）
    engine = FakeEngine({"n": _passing_events("n", "n:0")}, network_crash_after={"n": 0})
    ft = _FakeTime()
    result = schedule(_rm([_job("n", timeout_s=2.5)]), FakeResolver(engine), CollectSink(),
                      opts=ft.opts(network_retry=5, retry_sleep=ft.jump))
    # 截止时刻跨 attempt 共享：几次 attempt 后墙钟超 2s → 转 timeout，不会用满 network_retry=5
    assert (_summary(result).status, result.results[0].error_type) == (Status.ERROR, "timeout")
    assert engine.run_count["n"] == 3  # 没用满 5 次重试（被共享的截止时刻截断）


# ---- on_job_complete 回调（ADR 0030 实时写接缝）----
def test_on_job_complete_fires_once_per_job_with_final_jobresult():
    # 每个 job 完成回调一次，传的是已归约好的最终 JobResult（含 status/scope_id）
    jobs = [_job("a"), _job("b")]
    engine = FakeEngine({"a": _passing_events("a", "a:0"), "b": _failing_events("b", "b:0")})
    seen: list[tuple[str, Status]] = []
    schedule(_rm(jobs), FakeResolver(engine), CollectSink(),
             opts=ScheduleOpts(max_concurrency=2),
             on_job_complete=lambda jr: seen.append((jr.scope_id, jr.status)))
    # 两个 job 各回调一次，且拿到的是终态判定（a passed / b failed）
    assert len(seen) == 2
    assert dict(seen) == {"a": Status.PASSED, "b": Status.FAILED}


def test_on_job_complete_default_none_is_noop():
    # 不传回调（默认 None）：行为与从前完全一致（无回调路径，保纯 reducer）
    engine = FakeEngine({"a": _passing_events("a", "a:0")})
    result = schedule(_rm([_job("a")]), FakeResolver(engine), CollectSink())  # 不传 on_job_complete
    assert _summary(result).status == Status.PASSED


def test_on_job_complete_streams_not_batched():
    # 流式：job 完成即回调，不是攒到最后一起。用 on_event 钩子让 a 先于 b 完成，
    # 断言回调到达时 job_results 尚未集齐全部（证明边完成边回调）。
    fired_at_len: list[int] = []
    # max_concurrency=1 串行：a 完整运行结束→回调→b 才开始。回调发生在 b 尚未完成时。
    jobs = [_job("a"), _job("b")]
    engine = FakeEngine({"a": _passing_events("a", "a:0"), "b": _passing_events("b", "b:0")})
    order: list[str] = []
    def cb(jr):
        order.append(jr.scope_id)
        fired_at_len.append(len(order))
    schedule(_rm(jobs), FakeResolver(engine), CollectSink(),
             opts=ScheduleOpts(max_concurrency=1), on_job_complete=cb)
    # 串行下回调按完成序逐个到达：第一次 fire 时只有 1 个、第二次 2 个（增量，非末尾一次性 2 个）
    assert fired_at_len == [1, 2]
    assert len(order) == 2


def test_on_job_complete_is_not_fired_for_a_job_that_never_started():
    # 没有启动的 job 没有执行结果：不回调、不存明细，执行事实里也没有它；余下的 job 不再启动的来源随执行事实交出，由收尾的结束写把它
    # 记 skipped（ADR 0031 决定三「结束写」小节；ADR 0030 决定三）。
    jobs = [_job("crash"), _job("queued")]
    engine = FakeEngine({"crash": _passing_events("crash", "crash:0"),
                         "queued": _passing_events("queued", "queued:0")},
                        crash_after={"crash": 0})
    seen: dict[str, Status] = {}
    ex = schedule(_rm(jobs), FakeResolver(engine), CollectSink(),
                  opts=ScheduleOpts(max_concurrency=1, fail_fast=True),
                  on_job_complete=lambda jr: seen.__setitem__(jr.scope_id, jr.status))
    assert seen == {"crash": Status.ERROR}
    assert [jr.scope_id for jr in ex.results] == ["crash"] and ex.stopped_by == "fail-fast"
    queued = _outcome(ex, "queued")
    assert (queued.status, queued.state.message, queued.detail) == (
        Status.SKIPPED, RUN_ENDINGS["fail-fast"].skipped_message, None)


def test_on_job_complete_exception_propagates_not_swallowed():
    # ADR 0030：回调异常不应被吞——落库失败是真问题，必须冒泡（而非被 ThreadPoolExecutor/as_completed 静默丢）。
    # 若有人给回调加 try/except 兜底（看似稳健、实则掩盖落库失败），此测试变红。
    import pytest
    engine = FakeEngine({"a": _passing_events("a", "a:0")})

    def boom(jr):
        raise RuntimeError("落库炸了")

    with pytest.raises(RuntimeError, match="落库炸了"):
        schedule(_rm([_job("a")]), FakeResolver(engine), CollectSink(), on_job_complete=boom)


def test_on_job_complete_exception_stops_inflight_workers_before_raise():
    # 回调抛异常时，冒泡前必须先 stop 所有运行中的 worker——否则异常跳出 with、shutdown(wait=True)
    # 会等它们自然结束（实际的 AgentCore 会话持续计费）。验：异常仍抛 + in-flight worker 的 handle 被 stop。
    import pytest
    slow_started = threading.Event()  # slow 已 spawn 且在事件循环里
    release_fast = threading.Event()  # 放行 fast 完成（确保 slow 先在运行）

    def slow_stream(scope_id):
        # slow 先吐一个事件（证明已 spawn、在循环里）→ 宣告 started → 阻塞直到被 stop（handle.stopped 后协作退出）
        yield ScenarioStarted(scenario_id=f"{scope_id}:0")
        slow_started.set()
        for i in range(200):
            release_fast.wait(timeout=2)
            yield StepDone(scenario_id=f"{scope_id}:0", step_index=i, status=Status.PASSED, votes=Votes(3, 3))

    def fast_stream(scope_id):
        slow_started.wait(timeout=2)  # 等 slow 真的在运行了，fast 才完成 → 保证 fast 回调抛错时 slow 是 in-flight
        yield from _passing_events(scope_id, f"{scope_id}:0")

    engine = FakeEngine({"fast": fast_stream("fast"), "slow": slow_stream("slow")})

    def boom_on_fast(jr):
        if jr.scope_id == "fast":
            release_fast.set()  # 让 slow 能在被 stop 后从 wait 醒来、看到 handle.stopped 协作退出
            raise RuntimeError("fast 落库炸了")

    with pytest.raises(RuntimeError, match="fast 落库炸了"):
        schedule(_rm([_job("fast"), _job("slow")]), FakeResolver(engine), CollectSink(),
                 opts=ScheduleOpts(max_concurrency=2), on_job_complete=boom_on_fast)
    # 关键断言：slow 的 worker 在异常冒泡前被 stop（止血，不让会话空转计费）
    assert engine.handles["slow"].stopped


def test_on_event_exception_propagates_as_is_without_verdict_and_stops_workers():
    """on_event（实时落库）在运行期抛异常时冒泡出 schedule()，类型与对象都不变（组合根据此以非零退出码报运行期落库失败，ADR 0030
    决定七「非零（run 已开始执行，只有本机 run）」条；冒泡的方式另见 ADR 0030 决定三）；它不进「worker 异常」分支，故不给这个 job
    产生 engine_error 判定；冒泡前本 worker 与其余运行中的 worker 都收到停止请求。"""

    class _StoreDown(Exception):
        pass

    slow_started = threading.Event()

    def slow_gen(_job):
        yield ScenarioStarted(scenario_id="slow:0")
        slow_started.set()
        yield StepDone(scenario_id="slow:0", step_index=0, status=Status.PASSED, votes=Votes(3, 3))

    def obs_gen(_job):
        slow_started.wait(5.0)  # slow 已在运行，obs 的落库失败冒泡时它是运行中的 worker
        yield from _passing_events("obs", "obs:0")

    engine = FakeEngine({"obs": obs_gen, "slow": slow_gen}, tail_after_stop={"obs": [], "slow": []})
    boom = _StoreDown("运行期落库失败")

    def on_event(event):
        if isinstance(event, StepDone) and event.scenario_id == "obs:0":
            raise boom

    seen: list = []
    with pytest.raises(_StoreDown) as exc_info:
        schedule(_rm([_job("obs"), _job("slow")]), FakeResolver(engine), CollectSink(),
                 opts=ScheduleOpts(max_concurrency=2), on_job_complete=seen.append, on_event=on_event)
    assert exc_info.value is boom
    assert seen == []  # 没有任何判定经回调落库，尤其没有归因成「worker 异常」的 engine_error
    assert engine.handles["obs"].stopped  # 本 worker：冒泡前停掉
    assert engine.handles["slow"].stopped  # 其余运行中的 worker：主线程冒泡前停掉


# ---- grace 硬约束 enforce（ADR 0024）：schedule 起 worker 前校验 grace 合法且 ≥ min_grace_s ----
def test_grace_below_min_grace_raises():
    # grace < 声明下限 → 起任何 worker 前就 raise ValueError（引擎无关的关系校验，core 不认下限从何而来）。
    import pytest
    engine = FakeEngine({"a": _passing_events("a", "a:0")})
    with pytest.raises(ValueError, match="grace"):
        schedule(_rm([_job("a")]), FakeResolver(engine), CollectSink(),
                 opts=ScheduleOpts(grace_period_s=5.0, min_grace_s=180.0))
    # 起 worker 前就拒 → 引擎根本没被 run（无副作用、不建会话）
    assert "a" not in engine.handles


def test_grace_nonpositive_raises():
    import pytest
    engine = FakeEngine({"a": _passing_events("a", "a:0")})
    with pytest.raises(ValueError, match="grace"):
        schedule(_rm([_job("a")]), FakeResolver(engine), CollectSink(),
                 opts=ScheduleOpts(grace_period_s=0.0))


def test_grace_at_or_above_min_grace_ok():
    # grace == min_grace（边界）与 grace > min_grace 都放行（正常运行结束）。
    engine = FakeEngine({"a": _passing_events("a", "a:0")})
    result = schedule(_rm([_job("a")]), FakeResolver(engine), CollectSink(),
                      opts=ScheduleOpts(grace_period_s=180.0, min_grace_s=180.0))
    assert _summary(result).status == Status.PASSED


def test_default_opts_no_min_grace_backcompat():
    # 默认 min_grace_s=0.0 → 不破直接构造 ScheduleOpts 的调用方（默认 grace 5.0 > 0 且 ≥ 0，放行）。
    engine = FakeEngine({"a": _passing_events("a", "a:0")})
    result = schedule(_rm([_job("a")]), FakeResolver(engine), CollectSink())
    assert _summary(result).status == Status.PASSED


# ---- 内容完整前置（ADR 0024/0026）：EOF 无 scope_done 不落归约终态,按来源分流 ----


def test_partial_completion_without_scope_done_not_passed():
    """假绿回归（对抗验证探针场景）：worker 干净 EOF 但没发 scope_done → error+engine_error，绝不 PASSED。

    修复前：部分完成的 scenario 聚合出 PASSED（3 个 scenario 只完成 1 个也报 passed）。
    """
    partial = [
        ScenarioStarted(scenario_id="p:0"),
        StepDone(scenario_id="p:0", step_index=0, status=Status.PASSED, votes=Votes(3, 3)),
        ScenarioDone(scenario_id="p:0", status=Status.PASSED),
        # 无 scope_done：流在此 EOF（协作停/异常截断的形状）
    ]
    engine = FakeEngine({"p": partial})
    result = schedule(_rm([_job("p")]), FakeResolver(engine), CollectSink())
    jr = result.results[0]
    assert jr.status == Status.ERROR
    assert jr.error_type == "engine_error"
    assert _summary(result).status == Status.ERROR


def test_abort_then_clean_eof_is_aborted_not_passed():
    """fail-fast 掐停后 worker 干净退出（不吐 scope_done）→ ABORTED（有现场），绝不 PASSED 假绿。

    时序构造：victim 吐完首个 scenario 的事件后，on_event 钩子置 abort_flag（模拟别的 job 崩了触发
    fail-fast）——victim 下一轮事件间检查看到 abort → stop → FakeEngine 配合 return（EOF 无 scope_done）。
    """
    import threading as _th

    crash_now = _th.Event()

    victim_events = [
        ScenarioStarted(scenario_id="v:0"),
        StepDone(scenario_id="v:0", step_index=0, status=Status.PASSED, votes=Votes(3, 3)),
        ScenarioDone(scenario_id="v:0", status=Status.PASSED),
        ScenarioStarted(scenario_id="v:1"),  # 第二个 scenario 运行到一半被掐
        StepDone(scenario_id="v:1", step_index=0, status=Status.PASSED, votes=Votes(3, 3)),
        ScenarioDone(scenario_id="v:1", status=Status.PASSED),
        ScopeDone(scope_id="v"),
    ]
    crash_events = [ScenarioStarted(scenario_id="c:0")]  # 之后崩

    def on_event(scope_id, i):
        if scope_id == "v" and i == 2:
            crash_now.set()  # victim 吐完第一个 scenario → 让 crash job 崩

    def crash_gen(job):
        yield crash_events[0]
        crash_now.wait(timeout=5)
        raise RuntimeError("crash job 崩了")

    engine = FakeEngine({"v": victim_events, "c": crash_gen}, on_event=on_event)
    sink = CollectSink()
    result = schedule(_rm([_job("c"), _job("v")]), FakeResolver(engine), sink,
                      opts=ScheduleOpts(max_concurrency=2, fail_fast=True))
    v_jr = next(jr for jr in result.results if jr.scope_id == "v")
    # victim 结局依时序：真正完成（见 scope_done）→ PASSED 合法；被掐（EOF 无 scope_done）→ ABORTED。
    # 关键断言：绝不 ERROR（被牵连非自身故障）；PASSED 当且仅当 sink 真收到 v 的 scope_done（内容完整）。
    assert v_jr.status in (Status.PASSED, Status.ABORTED)
    v_scope_done_seen = any(isinstance(e, ScopeDone) and e.scope_id == "v" for e in sink.events)
    assert (v_jr.status == Status.PASSED) == v_scope_done_seen  # 假绿不可能：没内容完整就没有 PASSED


# ---- 停止后继续有界消费 + stop_reason 首次仲裁（ADR 0034 机制二；0051 决策 5）----

def test_tail_events_after_stop_are_still_reduced_and_release_confirmed():
    """超时处置后 worker 收 SIGTERM 走收尾、发出 session_closed(confirmed)：core 停止后继续消费到 EOF，U 为空、消息里没有释放失败提示。"""
    from gherkai_core.model import SessionClosed, SessionOpened

    scope = "d"
    events = [SessionOpened(scope_id=scope, name="n", origin="created", session_id="arn:n"),
              ScopeStarted(scope_id=scope, session_id="arn:n"), ScenarioStarted(scenario_id="d:0")]
    tail = [SessionClosed(scope_id=scope, name="n", release="confirmed", session_id="arn:n", observed_s=3.0)]
    engine = FakeEngine({scope: events}, tail_after_stop={scope: tail})
    # 处理完 scenario_started 后时间一次性越过截止时刻，之后慢走——排空上界（grace 加余量）不该被假时间立刻耗尽
    ft = _FakeTime()
    res = schedule(_rm([_job(scope, timeout_s=5.0, device="android")]), FakeResolver(engine), _JumpSink(ft, ScenarioStarted),
                   opts=ft.opts(max_concurrency=1, heartbeat_interval_s=0.05, grace_period_s=1.0))
    jr = res.results[0]
    assert (jr.status, jr.error_type) == (Status.ERROR, "timeout")
    assert [s.release for s in jr.sessions] == ["confirmed"] and (jr.device_observed_s, jr.device_observed_missing) == (3.0, 0)
    assert "未能确认停止" not in (jr.message or "")
    assert engine.handles[scope].stopped


def test_timeout_wins_over_abort_when_deadline_already_passed_on_every_branch():
    """首次仲裁：那一刻 deadline 已过就取 timeout，即使 abort_flag 也已置位——事件分支、WorkerExitError 分支、EOF 分支都一样；
    deadline 未过时同样的置位则判 abort（ABORTED）。abort_flag 在 worker 已 spawn、首事件之前置位（起 worker 前置位则不启动）。"""
    import gherkai_core.schedule as sch
    from gherkai_core.errors import WorkerExitError

    def run(scope: str, behavior, *, deadline_passed: bool, set_flag: bool):
        ft = _FakeTime()  # 认领时刻在零点附近；deadline 情形在 worker 起来之后越过截止时刻，之后慢走（别把排空上界也耗尽）
        captured = {}
        orig = sch._Worker.__init__

        def spy(self, *a, **kw):
            orig(self, *a, **kw)
            captured["w"] = self

        def gen(job):  # worker 已 spawn、首事件前：先越过截止时刻，再把 fail-fast 标志置位（模拟其他 job 恰在此刻失败）
            if deadline_passed:
                ft.jump(1000.0)
            if set_flag:
                captured["w"].abort_flag.set()
            return behavior(job)

        sch._Worker.__init__ = spy
        try:
            res = schedule(_rm([_job(scope, timeout_s=1.0)]), FakeResolver(FakeEngine({scope: gen})), CollectSink(),
                           opts=ft.opts(max_concurrency=1, heartbeat_interval_s=0.05, grace_period_s=1.0))
        finally:
            sch._Worker.__init__ = orig
        return res.results[0]

    def events(job):  # 事件分支：首事件到达时检查（内容不完整——没有 scope_done）
        return iter([ScopeStarted(scope_id="s"), ScenarioStarted(scenario_id="s:0")])

    def network_exit(job):  # WorkerExitError 分支：零事件、worker 以 80 退出
        raise WorkerExitError(80, "fake 建连失败")

    def eof(job):  # EOF 分支：零事件干净退出
        return iter([])

    for behavior in (events, network_exit, eof):
        jr = run("s", behavior, deadline_passed=True, set_flag=True)
        assert (jr.status, jr.error_type) == (Status.ERROR, "timeout"), behavior.__name__  # 不是 ABORTED / network_error / engine_error
    for behavior in (events, network_exit, eof):
        jr = run("s", behavior, deadline_passed=False, set_flag=True)
        assert (jr.status, jr.error_type) == (Status.ABORTED, None), behavior.__name__


def test_drain_bound_ends_consumption_when_worker_hangs_after_stop():
    """排空上界（ADR 0034 机制二）：停止请求后 worker 卡死、再无事件也不退出 → 消费在 grace 加余量处终止、不挂死；判定由 stop_reason 给出。"""
    import time

    scope = "h"
    # 处理完 scope_started 后越过截止时刻（第二条事件的事件间检查即落定超时）；停止请求之后单调时钟每读前进 1 秒，排空上界（1 加 5 秒）
    # 几次心跳内到点
    ft = _FakeTime()
    engine = FakeEngine({scope: [ScopeStarted(scope_id=scope), ScenarioStarted(scenario_id="h:0")]}, hang_after_stop={scope},
                        on_stop=lambda _s: setattr(ft, "step", 1.0))
    t0 = time.monotonic()
    res = schedule(_rm([_job(scope, timeout_s=5.0)]), FakeResolver(engine), _JumpSink(ft, ScopeStarted),
                   opts=ft.opts(max_concurrency=1, heartbeat_interval_s=0.05, grace_period_s=1.0))
    assert time.monotonic() - t0 < 3.0  # 不等真实的 6 秒、也不永远等
    jr = res.results[0]
    assert (jr.status, jr.error_type) == (Status.ERROR, "timeout") and engine.handles[scope].stopped


def test_deadline_after_scope_done_hurries_exit_but_keeps_verdict():
    """内容完整后不再仲裁（ADR 0034 机制二）：scope_done 已到、worker 收尾期间 deadline 到点 → 只催停（发停止请求），判定仍按内容（PASSED）。"""
    scope = "p"
    events = _passing_events(scope, "p:0")  # 末尾带 scope_done
    ft = _FakeTime()  # 处理完 scope_done 后越过截止时刻：之后的第一次心跳检查看到它
    engine = FakeEngine({scope: events}, tail_after_stop={scope: []})  # 发完事件后活着等停（模拟释放阶段拖过预算）
    res = schedule(_rm([_job(scope, timeout_s=5.0)]), FakeResolver(engine), _JumpSink(ft, ScopeDone),
                   opts=ft.opts(max_concurrency=1, heartbeat_interval_s=0.05, grace_period_s=1.0))
    jr = res.results[0]
    assert (jr.status, jr.error_type) == (Status.PASSED, None) and engine.handles[scope].stopped


def test_fail_fast_does_not_preempt_network_retry():
    """开 fail_fast 时，可重试的瞬时网络故障（零 step_done 的 network_error）先重试、不触发 run 中止；重试成功则 run 通过。"""
    engine = FakeEngine({"a": _passing_events("a", "a:0"), "b": _passing_events("b", "b:0")}, network_crash_after={"a": [0]})
    res = schedule(_rm([_job("a"), _job("b")]), FakeResolver(engine), CollectSink(),
                   opts=ScheduleOpts(max_concurrency=1, fail_fast=True, network_retry=1, retry_sleep=lambda s: None))
    assert engine.run_count["a"] == 2 and _summary(res).status == Status.PASSED
    assert [jr.status for jr in res.results] == [Status.PASSED, Status.PASSED]


def test_fail_fast_stops_running_workers_from_main_thread_without_heartbeat():
    """fail-fast：主线程的 _stop_all 对仍在运行的 worker 当场落定并发停止请求，不依赖该 worker 自己的心跳检查（这里关掉心跳、
    victim 卡在等停里看不到 abort_flag）。那一刻 deadline 未过的 victim 记 ABORTED，已过的记 timeout。"""
    import time

    def run(scope: str, timeout_s: float, crash_delay_s: float):
        crash_now = threading.Event()

        def crash_gen(job):
            yield ScenarioStarted(scenario_id="c:0")
            crash_now.wait(timeout=5)
            time.sleep(crash_delay_s)
            raise RuntimeError("crash job 崩了")

        def on_event(scope_id, i):
            if scope_id == scope:
                crash_now.set()  # victim 吐出首事件后让 crash job 崩

        engine = FakeEngine({scope: [ScopeStarted(scope_id=scope)], "c": crash_gen}, on_event=on_event,
                            tail_after_stop={scope: []})  # victim 发完事件后活着等停
        t0 = time.monotonic()
        res = schedule(_rm([_job(scope, timeout_s=timeout_s), _job("c")]), FakeResolver(engine), CollectSink(),
                       opts=ScheduleOpts(max_concurrency=2, fail_fast=True, heartbeat_interval_s=0, grace_period_s=1.0))
        assert time.monotonic() - t0 < crash_delay_s + 3.0  # 没等到 FakeEngine 的 5 秒等停超时：停止请求由主线程当场发出
        return next(jr for jr in res.results if jr.scope_id == scope)

    jr = run("v", timeout_s=7200.0, crash_delay_s=0.0)
    assert (jr.status, jr.error_type) == (Status.ABORTED, None)
    jr = run("w", timeout_s=0.3, crash_delay_s=0.8)  # 实时钟：crash job 崩时 victim 的 deadline 已过 → _stop_all 当场落定 timeout
    assert (jr.status, jr.error_type) == (Status.ERROR, "timeout")


def test_abort_decided_before_deadline_stays_aborted_when_deadline_passes_during_tail():
    """首次仲裁：先判 abort（那一刻 deadline 未过），收尾期间 deadline 才到 → 仍 ABORTED；停止后到达的收尾事件照常归约。"""
    from gherkai_core.model import SessionClosed, SessionOpened

    crash_now = threading.Event()

    def crash_gen(job):
        yield ScenarioStarted(scenario_id="c:0")
        crash_now.wait(timeout=5)
        raise RuntimeError("crash job 崩了")

    def on_event(scope_id, i):
        if scope_id == "v":
            crash_now.set()

    tail = [SessionClosed(scope_id="v", name="n", release="confirmed", session_id="arn:n", observed_s=1.0)]
    engine = FakeEngine({"v": [SessionOpened(scope_id="v", name="n", origin="created", session_id="arn:n"),
                               ScopeStarted(scope_id="v", session_id="arn:n")], "c": crash_gen},
                        on_event=on_event, tail_after_stop={"v": tail}, tail_delay_s=0.6)
    res = schedule(_rm([_job("v", timeout_s=0.3), _job("c")]), FakeResolver(engine), CollectSink(),
                   opts=ScheduleOpts(max_concurrency=2, fail_fast=True, heartbeat_interval_s=0.05, grace_period_s=1.0))
    v = next(jr for jr in res.results if jr.scope_id == "v")
    assert (v.status, v.error_type) == (Status.ABORTED, None)
    assert [s.release for s in v.sessions] == ["confirmed"] and "未能确认停止" not in (v.message or "")


def test_attempted_session_without_arn_plus_abort_stays_aborted_and_lists_the_attempt():
    """0034 对拍矩阵「无 ARN 的未知 Create 加取消」的取消组合：设备 job 只发出 attempted 的 session_opened（结果未知的创建尝试，没有 ARN），
    另一 job 崩溃触发 fail-fast 中止；停止后到达的 attempted session_closed(unconfirmed) 照常归约。判定仍为 ABORTED（中止先于 deadline，
    不是 release_failed），U 非空时 message 追加「未能确认停止」提示并把这次尝试标为结果未知的创建尝试；两个计量键都不计 attempted。"""
    from gherkai_core.model import SessionClosed, SessionOpened

    crash_now = threading.Event()

    def crash_gen(job):
        yield ScenarioStarted(scenario_id="c:0")
        crash_now.wait(timeout=5)
        raise RuntimeError("crash job 崩了")

    def on_event(scope_id, i):
        if scope_id == "v":
            crash_now.set()

    tail = [SessionClosed(scope_id="v", name="n", release="unconfirmed", session_id=None, observed_s=None)]
    engine = FakeEngine({"v": [SessionOpened(scope_id="v", name="n", origin="attempted", session_id=None)], "c": crash_gen},
                        on_event=on_event, tail_after_stop={"v": tail}, tail_delay_s=0.6)
    res = schedule(_rm([_job("v", timeout_s=5.0, device="android"), _job("c")]), FakeResolver(engine), CollectSink(),
                   opts=ScheduleOpts(max_concurrency=2, fail_fast=True, heartbeat_interval_s=0.05, grace_period_s=1.0))
    v = next(jr for jr in res.results if jr.scope_id == "v")
    assert (v.status, v.error_type) == (Status.ABORTED, None)
    assert v.session_id is None
    assert [(x.origin, x.release, x.session_id) for x in v.sessions] == [("attempted", "unconfirmed", None)]
    assert (v.device_observed_s, v.device_observed_missing) == (0.0, 0)  # attempted 不计入两个计量键
    assert "未能确认停止" in (v.message or "") and "结果未知的创建尝试" in (v.message or "")


def test_generic_exception_still_stops_worker_and_spawn_failure_goes_through_finalize():
    """事件流中的普通异常（解析失败 / sink 抛错）后仍向 worker 发停止请求（别留孤儿进程）；起 worker 失败以退出码未知进终结函数：
    消息保留「起 worker 失败」，已过 deadline 的按首次仲裁记 timeout。"""
    engine = FakeEngine({"x": [ScopeStarted(scope_id="x"), ScenarioStarted(scenario_id="x:0")]}, crash_after={"x": 1})
    res = schedule(_rm([_job("x")]), FakeResolver(engine), CollectSink(), opts=ScheduleOpts(max_concurrency=1))
    jr = res.results[0]
    assert (jr.status, jr.error_type) == (Status.ERROR, "engine_error") and jr.message.startswith("worker 异常：")
    assert engine.handles["x"].stopped

    class Boom:
        def run_scope(self, job):
            raise OSError("spawn 失败")

    res = schedule(_rm([_job("y")]), FakeResolver(Boom()), CollectSink(), opts=ScheduleOpts(max_concurrency=1))
    assert (res.results[0].status, res.results[0].error_type, res.results[0].message) == (Status.ERROR, "engine_error", "起 worker 失败：spawn 失败")

    ft = _FakeTime()

    class SlowBoom:  # 起 worker 的调用拖过了截止时刻才失败（认领在调用之前，截止时刻已定）
        def run_scope(self, job):
            ft.jump(1000.0)
            raise OSError("spawn 失败")

    res = schedule(_rm([_job("z", timeout_s=1.0)]), FakeResolver(SlowBoom()), CollectSink(), opts=ft.opts(max_concurrency=1))
    assert (res.results[0].status, res.results[0].error_type) == (Status.ERROR, "timeout")


def test_stop_all_decides_for_every_worker_before_any_blocking_stop():
    """fail-fast 批量中止：先对全部运行中的 worker 落定停止原因、再发停止请求。真 stop() 会阻塞到宽限到点，边落定边停会让前一个 worker
    消耗的宽限把后一个的仲裁推到它的 deadline 之后、把本该的 ABORTED 记成 timeout。这里让假 stop() 把假时钟推过所有 deadline。"""
    clock = _FakeTime()
    seen = {"v1": threading.Event(), "v2": threading.Event()}

    def crash_gen(job):
        yield ScenarioStarted(scenario_id="c:0")
        seen["v1"].wait(5)
        seen["v2"].wait(5)
        raise RuntimeError("crash job 崩了")

    def on_event(scope_id, i):
        if scope_id in seen:
            seen[scope_id].set()

    engine = FakeEngine({"v1": [ScopeStarted(scope_id="v1")], "v2": [ScopeStarted(scope_id="v2")], "c": crash_gen},
                        on_event=on_event, tail_after_stop={"v1": [], "v2": []},
                        # 模拟 victim 的 stop() 阻塞消耗的宽限：越过所有 deadline（crash job 自己收尾的 stop 不算，它发生在批量中止之前）
                        on_stop=lambda scope: scope.startswith("v") and clock.jump(1000.0))
    res = schedule(_rm([_job("v1", timeout_s=50.0), _job("v2", timeout_s=50.0), _job("c")]), FakeResolver(engine), CollectSink(),
                   opts=clock.opts(max_concurrency=3, fail_fast=True, heartbeat_interval_s=0, grace_period_s=1.0))
    by = {jr.scope_id: (jr.status, jr.error_type) for jr in res.results}
    assert by["v1"] == (Status.ABORTED, None) and by["v2"] == (Status.ABORTED, None), by


def test_generic_exception_arbitrates_before_blocking_stop():
    """普通异常分支先按首次仲裁落定、再发停止请求：停止前已成立的 abort 不被停止期间越过的 deadline 改成 timeout。"""
    import gherkai_core.schedule as sch

    clock = _FakeTime()
    captured = {}
    orig = sch._Worker.__init__

    def spy(self, *a, **kw):
        orig(self, *a, **kw)
        captured["w"] = self

    def gen(job):  # 零事件：这个 run 已被中止，随后事件流以普通异常断掉
        captured["w"].abort_flag.set()
        raise RuntimeError("解析失败")

    engine = FakeEngine({"x": gen}, on_stop=lambda scope: clock.jump(1000.0))
    sch._Worker.__init__ = spy
    try:
        res = schedule(_rm([_job("x", timeout_s=50.0)]), FakeResolver(engine), CollectSink(),
                       opts=clock.opts(max_concurrency=1, heartbeat_interval_s=0.05, grace_period_s=1.0))
    finally:
        sch._Worker.__init__ = orig
    jr = res.results[0]
    assert (jr.status, jr.error_type) == (Status.ABORTED, None) and engine.handles["x"].stopped


def test_hang_after_hurry_exit_is_timeout_like_stateless_path():
    """内容完整后催停、worker 却卡死不退出：排空上界到点按「退出码未知」回判——deadline 已过记 timeout，与无状态路径的 timed_out 记录一致。"""
    scope = "p"
    events = _passing_events(scope, "p:0")
    # 处理完 scope_done 后越过截止时刻（下一次心跳检查即催收尾）；停止请求之后单调时钟每读前进 1 秒，排空上界几次心跳内到点
    ft = _FakeTime()
    engine = FakeEngine({scope: events}, hang_after_stop={scope}, on_stop=lambda _s: setattr(ft, "step", 1.0))
    res = schedule(_rm([_job(scope, timeout_s=5.0)]), FakeResolver(engine), _JumpSink(ft, ScopeDone),
                   opts=ft.opts(max_concurrency=1, heartbeat_interval_s=0.05, grace_period_s=1.0))
    assert (res.results[0].status, res.results[0].error_type) == (Status.ERROR, "timeout")


def test_fail_fast_during_retry_backoff_keeps_the_network_error_of_the_attempt_that_ran():
    """退避期间 run 被 fail-fast 中止：不再重试，但已经运行过一次的 job 保留上次的 network_error 判定（不当作没有启动）。"""
    import gherkai_core.schedule as sch

    captured = {}
    orig = sch._Worker.__init__

    def spy(self, *a, **kw):
        orig(self, *a, **kw)
        captured["w"] = self

    engine = FakeEngine({"a": _passing_events("a", "a:0")}, network_crash_after={"a": [0]})
    sch._Worker.__init__ = spy
    try:
        res = schedule(_rm([_job("a")]), FakeResolver(engine), CollectSink(),
                       opts=ScheduleOpts(max_concurrency=1, network_retry=1, retry_sleep=lambda s: captured["w"].abort_flag.set()))
    finally:
        sch._Worker.__init__ = orig
    jr = res.results[0]
    assert engine.run_count["a"] == 1 and (jr.status, jr.error_type) == (Status.ERROR, "network_error")
    assert "未再重试" in jr.message


def test_drain_bound_counts_from_stop_request_not_after_blocking_stop():
    """排空上界从停止请求时刻起算：真 stop() 阻塞消耗的宽限不再额外加进上界。假 stop() 把时钟推进很多，正确实现随后第一次心跳检查就到点；
    若从 stop() 返回后起算，还要再等满宽限加余量（多读六次以上时钟）。"""
    scope = "h"
    ft = _FakeTime()  # 处理完 scope_started 后越过截止时刻；停止请求之后单调时钟每读前进 1 秒
    n_at_stop: list[int] = []

    def on_stop(scope_id):
        ft.jump(100.0)  # 模拟 stop() 阻塞消耗的时间（远超宽限加余量）
        ft.step = 1.0
        if not n_at_stop:
            n_at_stop.append(ft.n)

    engine = FakeEngine({scope: [ScopeStarted(scope_id=scope), ScenarioStarted(scenario_id="h:0")]}, hang_after_stop={scope}, on_stop=on_stop)
    res = schedule(_rm([_job(scope, timeout_s=5.0)]), FakeResolver(engine), _JumpSink(ft, ScopeStarted),
                   opts=ft.opts(max_concurrency=1, heartbeat_interval_s=0.05, grace_period_s=1.0))
    assert (res.results[0].status, res.results[0].error_type) == (Status.ERROR, "timeout")
    assert ft.n - n_at_stop[0] <= 4, ft.n - n_at_stop[0]


def test_drain_bound_applies_before_deadline_under_fail_fast():
    """deadline 远未到的 job 被 fail-fast 中止后卡死不退出：排空上界同样起作用（靠心跳醒来），不挂死，判 ABORTED。"""
    import time

    class _Clock:
        def __init__(self): self.t = 0.0; self.stopped = False
        def __call__(self): self.t += 1.0 if self.stopped else 0.001; return self.t

    clock = _Clock()
    crash_now = threading.Event()

    def crash_gen(job):
        yield ScenarioStarted(scenario_id="c:0")
        crash_now.wait(5)
        raise RuntimeError("崩")

    def on_event(scope_id, i):
        if scope_id == "v":
            crash_now.set()

    def on_stop(scope_id):
        if scope_id == "v":
            clock.stopped = True  # 停止请求之后每次读时钟前进一秒，排空上界几次心跳内到点

    engine = FakeEngine({"v": [ScopeStarted(scope_id="v")], "c": crash_gen}, on_event=on_event, hang_after_stop={"v"}, on_stop=on_stop)
    t0 = time.monotonic()
    res = schedule(_rm([_job("v"), _job("c")]), FakeResolver(engine), CollectSink(),
                   opts=ScheduleOpts(max_concurrency=2, fail_fast=True, heartbeat_interval_s=0.05, grace_period_s=1.0, clock=clock))
    assert time.monotonic() - t0 < 3.0
    v = next(jr for jr in res.results if jr.scope_id == "v")
    assert (v.status, v.error_type) == (Status.ABORTED, None)


# ---- 停止后的等待预算就是 grace：排空上界取首次停止请求时刻加 grace、再加余量（ADR 0034 机制二「停止后继续有界消费完整事件流」条）----

class _StopWindowTime(_FakeTime):
    """停止前每次读单调时钟前进 1 ms；发出停止请求后时间停在请求时刻加 window 秒（两个读法都停在那里）。越过截止时刻由 `_JumpSink` 触发。

    停在一个固定时刻，把「停止后的收尾在请求后 window 秒到达」写成确定的时序：之后每次排空检查读到的都是这个时刻，
    收尾落在排空上界之内还是之外只由取法决定，与心跳次数无关。"""

    def __init__(self, window: float):
        super().__init__()
        self.window = window
        self.frozen: float | None = None

    def mono(self) -> float:
        return self.frozen if self.frozen is not None else super().mono()

    def wall(self) -> datetime:
        return _T0 + timedelta(seconds=self.frozen) if self.frozen is not None else super().wall()

    def on_stop(self, scope_id: str) -> None:  # FakeEngine 的 on_stop 钩子：handle.stop() 被调时，停止请求时刻已经记下
        if self.frozen is None:
            self.frozen = self.t + self.window


@pytest.mark.parametrize("grace, eof_in_bound", [
    (1.0, False),  # 排空上界为请求后 1 + 5 = 6 秒，20 秒处到达的 EOF 在它之外
    (30.0, True),  # 排空上界为请求后 35 秒，20 秒处的 EOF 在它之内
])
def test_grace_sets_drain_window_for_eof_after_hurry_exit(grace, eof_in_bound):
    """内容完整后 deadline 才到（催收尾）、EOF 在停止请求后 20 秒到达：在排空上界之内即干净退出、判 PASSED；在上界之外则退出信息
    未知、内容完整被回落，按首次仲裁判 ERROR timeout。"""
    scope = "p"
    clock = _StopWindowTime(window=20.0)
    engine = FakeEngine({scope: _passing_events(scope, "p:0")}, tail_after_stop={scope: []}, tail_delay_s=0.2,
                        on_stop=clock.on_stop)  # 发完事件后活着等停，收到停止请求后过一会儿才 EOF
    res = schedule(_rm([_job(scope, timeout_s=5.0)]), FakeResolver(engine), _JumpSink(clock, ScopeDone),
                   opts=clock.opts(max_concurrency=1, heartbeat_interval_s=0.02, grace_period_s=grace))
    jr = res.results[0]
    assert engine.handles[scope].stopped and clock.frozen is not None  # 确实走了催收尾、时钟停在请求后 20 秒
    expected = (Status.PASSED, None) if eof_in_bound else (Status.ERROR, "timeout")
    assert (jr.status, jr.error_type) == expected
    # 终结处只在排空上界到点退出时补发一次停止请求；事件流在上界内正常结束的不补发
    assert len(engine.handles[scope].stop_graces) == (1 if eof_in_bound else 2)


@pytest.mark.parametrize("grace, closed_in_bound", [(1.0, False), (30.0, True)])
def test_grace_lets_late_session_closed_be_reduced(grace, closed_in_bound):
    """停止决定落在 scope 中途（超时）、confirmed 的 session_closed 在停止请求后 20 秒到达：在排空上界之内（grace 30 秒，上界为请求后
    35 秒）即被归约，未确认集为空、job message 不带释放提示；grace 1 秒（排空上界为请求后 6 秒）时它被丢弃，message 多出「未能确认停止」
    的提示。两种情形的判定都是 ERROR timeout：停止原因在作出停止决定那一刻已落定，收尾到没到只影响会话记录与提示。"""
    from gherkai_core.model import SessionClosed, SessionOpened

    scope = "n"
    clock = _StopWindowTime(window=20.0)
    events = [SessionOpened(scope_id=scope, name="s-1", origin="created", session_id="s-1"),
              ScopeStarted(scope_id=scope, session_id="s-1"), ScenarioStarted(scenario_id="n:0")]
    tail = [SessionClosed(scope_id=scope, name="s-1", release="confirmed", session_id="s-1")]
    engine = FakeEngine({scope: events}, tail_after_stop={scope: tail}, tail_delay_s=0.2, on_stop=clock.on_stop)
    res = schedule(_rm([_job(scope, timeout_s=5.0)]), FakeResolver(engine), _JumpSink(clock, ScenarioStarted),
                   opts=clock.opts(max_concurrency=1, heartbeat_interval_s=0.02, grace_period_s=grace))
    jr = res.results[0]
    assert (jr.status, jr.error_type) == (Status.ERROR, "timeout") and clock.frozen is not None
    if closed_in_bound:
        assert [s.release for s in jr.sessions] == ["confirmed"]
        assert "未能确认停止" not in (jr.message or "")
    else:
        assert "未能确认停止" in (jr.message or "") and "s-1" in jr.message
    assert len(engine.handles[scope].stop_graces) == (1 if closed_in_bound else 2)  # 到点退出才补发


# ---- 终结处的补发停止请求（ADR 0034 机制二「停止调用自身也有界」条）：只在事件流没有正常结束时补发 ----
# 排空上界到点退出与普通异常两种情形各有覆盖：上面两组排空上界测试的上界之外分支、test_generic_exception_still_stops_worker_*。

@pytest.mark.parametrize("exit_kind", ["eof", "exit_code"])
@pytest.mark.parametrize("trigger", ["deadline", "abort"])
def test_re_arbitration_after_worker_exit_sends_no_stop(monkeypatch, trigger, exit_kind):
    """worker 在事件间检查有机会执行之前就已退出（零事件 EOF，或以非零退出码退出）：终结前的回判按首次仲裁落定停止原因，但不跟停止请求。
    事件流已正常结束说明 worker 已经退出，再发一次不改变任何事实，只会在控制面迟缓时把 job 的结束推迟一段客户端超时。"""
    import gherkai_core.schedule as sch
    from gherkai_core.errors import WorkerExitError

    captured = {}
    orig = sch._Worker.__init__

    def spy(self, *a, **kw):
        orig(self, *a, **kw)
        captured["w"] = self

    monkeypatch.setattr(sch._Worker, "__init__", spy)

    ft = _FakeTime()  # abort 情形慢走、不越过截止时刻

    def gen(job):  # worker 已 spawn、首事件之前：deadline 情形越过截止时刻，abort 情形置中止标志（模拟其他 job 恰在此刻失败），随后零事件即退出
        if trigger == "deadline":
            ft.jump(1000.0)
        if trigger == "abort":
            captured["w"].abort_flag.set()
        if exit_kind == "exit_code":
            raise WorkerExitError(80, "fake 建连失败")
        return iter([])

    engine = FakeEngine({"s": gen})
    # 关掉心跳：零事件的事件流直接结束，循环里的事件间检查一次也不执行，停止原因只能由终结前的回判落定
    res = schedule(_rm([_job("s", timeout_s=1.0)]), FakeResolver(engine), CollectSink(),
                   opts=ft.opts(max_concurrency=1, heartbeat_interval_s=0, grace_period_s=1.0))
    jr = res.results[0]
    expected = (Status.ERROR, "timeout") if trigger == "deadline" else (Status.ABORTED, None)
    assert (jr.status, jr.error_type) == expected
    assert not engine.handles["s"].stopped


def test_exit_code_after_stop_request_is_not_followed_by_another_stop():
    """事件循环里作出停止决定后，worker 收尾并以非零退出码退出（已拿到退出码）：终结处不补发，停止请求只有作出决定时的那一次。"""
    scope = "e"
    clock = _StopWindowTime(window=0.5)  # 收尾在请求后 0.5 秒结束，落在排空上界（1 加 5 秒）之内
    engine = FakeEngine({scope: [ScopeStarted(scope_id=scope), ScenarioStarted(scenario_id="e:0")]},
                        tail_after_stop={scope: []}, exit_code={scope: 1}, on_stop=clock.on_stop)
    res = schedule(_rm([_job(scope, timeout_s=5.0)]), FakeResolver(engine), _JumpSink(clock, ScenarioStarted),
                   opts=clock.opts(max_concurrency=1, heartbeat_interval_s=0.02, grace_period_s=1.0))
    jr = res.results[0]
    assert (jr.status, jr.error_type) == (Status.ERROR, "timeout") and clock.frozen is not None
    assert len(engine.handles[scope].stop_graces) == 1


@pytest.mark.parametrize("exit_kind", ["sigkill", "network", "exception"])
@pytest.mark.parametrize("trigger", ["deadline", "abort"])
def test_non_clean_exit_after_complete_content_is_re_arbitrated(exit_kind, trigger):
    """内容完整（scope_done 已到）之后 worker 非干净退出（SIGKILL 负码 / 80 / 普通异常）：不算内容完整，按首次仲裁回判——
    deadline 已过记 timeout、已被 fail-fast 中止记 ABORTED，而不是 engine_error / network_error。"""
    import gherkai_core.schedule as sch
    from gherkai_core.errors import WorkerExitError

    scope = "p"
    events = _passing_events(scope, "p:0")
    captured = {}
    orig = sch._Worker.__init__

    def spy(self, *a, **kw):
        orig(self, *a, **kw)
        captured["w"] = self

    ft = _FakeTime()
    done = threading.Event()

    class _Sink(CollectSink):
        def __call__(self, ev):
            super().__call__(ev)
            if isinstance(ev, ScopeDone):
                done.set()  # core 已把 scope_done 记为内容完整

    def gen(job):
        yield from events
        done.wait(5)
        if trigger == "deadline":
            ft.jump(1000.0)  # 全部事件处理完之后越过截止时刻
        if trigger == "abort":
            captured["w"].abort_flag.set()
        if exit_kind == "sigkill":
            raise WorkerExitError(-9, "x")
        if exit_kind == "network":
            raise WorkerExitError(80, "x")
        raise RuntimeError("崩")

    sch._Worker.__init__ = spy
    try:
        res = schedule(_rm([_job(scope, timeout_s=5.0)]), FakeResolver(FakeEngine({scope: gen})), _Sink(),
                       opts=ft.opts(max_concurrency=1, heartbeat_interval_s=0.05, grace_period_s=1.0))
    finally:
        sch._Worker.__init__ = orig
    jr = res.results[0]
    expected = (Status.ERROR, "timeout") if trigger == "deadline" else (Status.ABORTED, None)
    assert (jr.status, jr.error_type) == expected, jr.message


@pytest.mark.parametrize("trigger", ["deadline", "abort"])
def test_synthesized_details_survive_sync_path_timeout_and_abort(trigger):
    """合成明细与判定分开（ADR 0034 机制二）：scope 级 error 合成 SKIPPED 之后 worker 非零退出且已过 deadline / 已被 fail-fast 中止，
    同步路径判 timeout / ABORTED，合成的明细原样保留在 JobResult 里。"""
    import gherkai_core.schedule as sch
    from gherkai_core.errors import WorkerExitError
    from gherkai_core.model import SessionOpened

    scope = "d"
    events = [SessionOpened(scope_id=scope, name="n", origin="created", session_id="arn:n"),
              ScopeDone(scope_id=scope, status=Status.ERROR, error_type="acquire_timeout", message="没拿到设备")]
    captured = {}
    orig = sch._Worker.__init__

    def spy(self, *a, **kw):
        orig(self, *a, **kw)
        captured["w"] = self

    ft = _FakeTime()
    done = threading.Event()

    class _Sink(CollectSink):
        def __call__(self, ev):
            super().__call__(ev)
            if isinstance(ev, ScopeDone):
                done.set()

    def gen(job):
        yield from events
        done.wait(5)
        if trigger == "deadline":
            ft.jump(1000.0)  # 全部事件处理完之后越过截止时刻
        if trigger == "abort":
            captured["w"].abort_flag.set()
        raise WorkerExitError(1, "x")

    sch._Worker.__init__ = spy
    try:
        res = schedule(_rm([_job(scope, n_scenarios=2, timeout_s=5.0)]), FakeResolver(FakeEngine({scope: gen})), _Sink(),
                       opts=ft.opts(max_concurrency=1, heartbeat_interval_s=0.05, grace_period_s=1.0))
    finally:
        sch._Worker.__init__ = orig
    jr = res.results[0]
    expected = (Status.ERROR, "timeout") if trigger == "deadline" else (Status.ABORTED, None)
    assert (jr.status, jr.error_type) == expected, jr.message
    assert [sr.status for sr in jr.scenarios] == [Status.SKIPPED, Status.SKIPPED]
    assert all(st.status == Status.SKIPPED and not st.shortcircuited for sr in jr.scenarios for st in sr.steps)


def test_fail_fast_between_check_and_spawn_on_retry_aborts_the_attempt():
    """起 worker 前的检查到 spawn 之间的窗口（无法原子化）：重试时 fail-fast 恰在其中置位，worker 已起——立即落定 abort 并停它，
    判 ABORTED（不是 SKIPPED，也不是重试执行完之后的 PASSED），且不再有第三次 spawn。"""
    import gherkai_core.schedule as sch

    captured = {}
    orig = sch._Worker.__init__

    def spy(self, *a, **kw):
        orig(self, *a, **kw)
        captured["w"] = self

    # 第二次 attempt 的假 worker 不发事件、活着等停止请求（tail_after_stop 的键存在即等停）：这样它只能被停止请求结束，
    # 判定不可能靠「自己执行完」变成 PASSED，ABORTED 与「新 handle 确被停」才是确定性的断言
    engine = FakeEngine({"a": []}, network_crash_after={"a": [0]}, tail_after_stop={"a": []})
    calls = {"n": 0}

    def resolver(name):  # 第二次解析（重试那次）时置位：恰落在起 worker 前的检查之后、spawn 之前
        calls["n"] += 1
        if calls["n"] == 2:
            captured["w"].abort_flag.set()
        return engine

    import time

    sch._Worker.__init__ = spy
    t0 = time.monotonic()
    try:
        res = schedule(_rm([_job("a")]), resolver, CollectSink(),
                       opts=ScheduleOpts(max_concurrency=1, network_retry=2, retry_sleep=lambda s: None, grace_period_s=1.0))
    finally:
        sch._Worker.__init__ = orig
    elapsed = time.monotonic() - t0
    jr = res.results[0]
    assert engine.run_count["a"] == 2 and (jr.status, jr.error_type) == (Status.ABORTED, None), (jr.status, jr.error_type, jr.message)
    assert engine.handles["a"].stopped
    # 新 handle 是被 spawn 之后的停止请求停下的：假 worker 没收到停止请求会等满 5 秒才自然 EOF（之后收尾的幂等停也会把 stopped 置位），
    # 故耗时上界才是真正的护栏
    assert elapsed < 3.0, elapsed


def test_device_job_network_error_is_not_retried():
    """设备 job 的建连失败不做 job 级重试（ADR 0051 决策 2）：同样的零 step_done network_error，桌面 job 重试、设备 job 不重试。"""
    def run(device: str):
        engine = FakeEngine({"a": _passing_events("a", "a:0")}, network_crash_after={"a": [0]})
        res = schedule(_rm([_job("a", device=device)]), FakeResolver(engine), CollectSink(),
                       opts=ScheduleOpts(max_concurrency=1, network_retry=1, retry_sleep=lambda s: None))
        return engine.run_count["a"], res.results[0]

    n, jr = run("desktop")
    assert n == 2 and jr.status == Status.PASSED
    n, jr = run("android")
    assert n == 1 and (jr.status, jr.error_type) == (Status.ERROR, "network_error")


def test_desktop_network_error_retry_follows_session_release():
    """桌面 worker 也成对发会话事件（ADR 0051 决策 4）：建连重试耗尽前被丢弃的 attempt 建起的会话都确认停止时，退出码 80 仍判
    network_error、job 级重试照旧（ADR 0028）；有会话没能确认停止即按释放优先改判 release_failed，不再重试。"""
    from gherkai_core.model import SessionClosed, SessionOpened

    def discarded(sid: str, release: str) -> list:
        return [SessionOpened(scope_id="a", name=sid, origin="created", session_id=sid),
                SessionClosed(scope_id="a", name=sid, release=release, session_id=sid)]

    def run(release: str):
        attempts = iter([discarded("s-1", release), [SessionOpened(scope_id="a", name="s-2", origin="created", session_id="s-2"),
                                                       ScopeStarted(scope_id="a", session_id="s-2"),
                                                       *_passing_events("a", "a:0")[:-1],
                                                       SessionClosed(scope_id="a", name="s-2", release="confirmed", session_id="s-2"),
                                                       ScopeDone(scope_id="a")]])
        engine = FakeEngine({"a": lambda job: iter(next(attempts))}, network_crash_after={"a": [2]})
        res = schedule(_rm([_job("a")]), FakeResolver(engine), CollectSink(),
                       opts=ScheduleOpts(max_concurrency=1, network_retry=1, retry_sleep=lambda s: None))
        return engine.run_count["a"], res.results[0]

    n, jr = run("confirmed")
    assert n == 2 and (jr.status, jr.error_type) == (Status.PASSED, None) and jr.session_id == "s-2"
    assert (jr.device_observed_s, jr.device_observed_missing) == (None, None)
    n, jr = run("unconfirmed")
    assert n == 1 and (jr.status, jr.error_type) == (Status.ERROR, "release_failed")
    assert "退出码 80" in jr.message and "未确认停止的会话：s-1" in jr.message and "设备控制台" not in jr.message


def test_sigkill_negative_exit_code_is_error_not_clean():
    """被信号强杀（负退出码）不再按干净退出处理（ADR 0034 机制二）：零事件、exit -9 → ERROR engine_error，消息带退出码。"""
    engine = FakeEngine({"k": []}, exit_code={"k": -9})
    res = schedule(_rm([_job("k")]), FakeResolver(engine), CollectSink(), opts=ScheduleOpts(max_concurrency=1))
    jr = res.results[0]
    assert (jr.status, jr.error_type) == (Status.ERROR, "engine_error") and "退出码 -9" in jr.message


def test_worker_exit_error_text_does_not_reach_job_message():
    """终结函数只看 WorkerExitError 上有类型的退出码：异常消息文本不当归因、不进 job message，消息由终结函数按码给出。"""
    from gherkai_core.errors import WorkerExitError

    def exits(code):
        def gen(job):
            raise WorkerExitError(code, "异常消息文本")
        return gen

    res = schedule(_rm([_job("s"), _job("n")]), FakeResolver(FakeEngine({"s": exits(255), "n": exits(3)})), CollectSink(),
                   opts=ScheduleOpts(max_concurrency=2))
    by = {jr.scope_id: jr for jr in res.results}
    for sid, code in (("s", 255), ("n", 3)):
        assert (by[sid].status, by[sid].error_type) == (Status.ERROR, "engine_error")
        assert f"退出码 {code}" in by[sid].message and "异常消息文本" not in by[sid].message


def test_scope_done_after_nonzero_exit_is_error_and_zero_scenario_scope_done_is_error():
    """发完 scope_done 又非零退出 → ERROR（不是 PASSED）；零 scenario 的 scope_done 以 0 退出 → ERROR「未报告任何 scenario 判定」。"""
    engine = FakeEngine({"a": _passing_events("a", "a:0"), "z": [ScopeStarted(scope_id="z"), ScopeDone(scope_id="z")]},
                        exit_code={"a": 1})
    res = schedule(_rm([_job("a"), _job("z")]), FakeResolver(engine), CollectSink(), opts=ScheduleOpts(max_concurrency=2))
    by = {jr.scope_id: jr for jr in res.results}
    assert (by["a"].status, by["a"].error_type) == (Status.ERROR, "engine_error") and "退出码 1" in by["a"].message
    assert (by["z"].status, by["z"].error_type) == (Status.ERROR, "engine_error") and "未报告任何 scenario 判定" in by["z"].message


def test_run_level_device_metering_sums_device_jobs_and_omits_for_desktop_runs():
    from gherkai_core.model import SessionClosed, SessionOpened

    def dev(scope: str, observed: float | None):
        return [SessionOpened(scope_id=scope, name=scope, origin="created", session_id=f"arn:{scope}"),
                ScopeStarted(scope_id=scope, session_id=f"arn:{scope}"), *_passing_events(scope, f"{scope}:0")[:-1],
                SessionClosed(scope_id=scope, name=scope, release="confirmed", session_id=f"arn:{scope}", observed_s=observed),
                ScopeDone(scope_id=scope)]
    # 桌面 job 也带一对已确认的 AgentCore 会话事件（ADR 0051 决策 4）：计量两键只按目标给，它不进合计、自身也是 None
    engine = FakeEngine({"d1": dev("d1", 10.0), "d2": dev("d2", None), "desk": dev("desk", None)})
    res = schedule(_rm([_job("d1", device="android"), _job("d2", device="ios"), _job("desk")]), FakeResolver(engine), CollectSink(),
                   opts=ScheduleOpts(max_concurrency=3))
    assert (_summary(res).device_observed_s, _summary(res).device_observed_missing) == (10.0, 1)
    desk = next(jr for jr in res.results if jr.scope_id == "desk")
    assert (desk.device_observed_s, desk.device_observed_missing) == (None, None)
    assert desk.status == Status.PASSED and [s.release for s in desk.sessions] == ["confirmed"]
    only_desk = schedule(_rm([_job("desk")]), FakeResolver(FakeEngine({"desk": _passing_events("desk", "desk:0")})), CollectSink(),
                         opts=ScheduleOpts(max_concurrency=1))
    assert (_summary(only_desk).device_observed_s, _summary(only_desk).device_observed_missing) == (None, None)


def test_device_job_that_never_started_has_no_detail_and_the_run_level_metering_keys_stay():
    """没有启动的设备 job 没有判定明细，也就没有 job 级的计量两键；run 级两键按运行定义里有设备 job 照常给出（合计 0.0、缺计量 0），
    不按有明细的 job 判断（ADR 0051 决策 7；ADR 0031 决定三「结束写」小节）。"""
    engine = FakeEngine({"crash": _passing_events("crash", "crash:0")}, crash_after={"crash": 0})
    res = schedule(_rm([_job("crash"), _job("dev", device="android"), _job("desk")]), FakeResolver(engine), CollectSink(),
                   opts=ScheduleOpts(max_concurrency=1, fail_fast=True))
    assert [jr.scope_id for jr in res.results] == ["crash"] and res.stopped_by == "fail-fast"
    summary = _summary(res)
    assert {o.scope_id: (o.status, o.detail) for o in summary.jobs if o.scope_id != "crash"} == {
        "dev": (Status.SKIPPED, None), "desk": (Status.SKIPPED, None)}
    assert (summary.device_observed_s, summary.device_observed_missing) == (0.0, 0)


def test_device_job_spawn_failure_still_carries_metering_keys():
    """起 worker 失败的设备 job 也成对带计量两键（合计 0.0、缺计量 0、会话记录为空），run 级两键随之出现；桌面 job 两键保持 None。"""

    class Boom:
        def run_scope(self, job):
            raise OSError("spawn 失败")

    res = schedule(_rm([_job("dev", device="ios"), _job("desk")]), FakeResolver(Boom()), CollectSink(),
                   opts=ScheduleOpts(max_concurrency=1))
    dev = next(jr for jr in res.results if jr.scope_id == "dev")
    desk = next(jr for jr in res.results if jr.scope_id == "desk")
    assert (dev.status, dev.message) == (Status.ERROR, "起 worker 失败：spawn 失败") and dev.sessions == []
    assert (dev.device_observed_s, dev.device_observed_missing) == (0.0, 0)
    assert desk.status == Status.ERROR and (desk.device_observed_s, desk.device_observed_missing) == (None, None)
    assert (_summary(res).device_observed_s, _summary(res).device_observed_missing) == (0.0, 0)


# ---- 使用方中断（ADR 0024 终止契约「使用方中断」条）----

def _interrupt_sequence(levels):
    """按轮询次数给出中断级别：第 i 次轮询返回 levels[min(i, len(levels) - 1)]。返回 (回调, 轮询计数列表)。"""
    polls: list[None] = []

    def interrupt() -> int:
        polls.append(None)
        return levels[min(len(polls) - 1, len(levels) - 1)]

    return interrupt, polls


_RUNNING_HALF = [  # 执行到一半、仍在等待停止请求的 worker（配 tail_after_stop 键）
    ScenarioStarted(scenario_id="a:0"),
    StepDone(scenario_id="a:0", step_index=0, status=Status.PASSED, votes=Votes(3, 3)),
]
_WHOLE_PASS = [
    ScenarioStarted(scenario_id="b:0"),
    StepDone(scenario_id="b:0", step_index=0, status=Status.PASSED, votes=Votes(3, 3)),
    ScenarioDone(scenario_id="b:0", status=Status.PASSED),
    ScopeDone(scope_id="b"),
]


def test_user_interrupt_level1_stops_running_skips_queued_marks_run_aborted():
    """首次中断（级别 1）走与 fail-fast 同一条路：运行中 worker 被协作停止、按 abort 判 ABORTED；排队中的 job 不启动、不在执行事实里，
    余下的 job 不再启动的来源是 interrupt，由结束写记 skipped 并带中断的说明；run 按取法记 aborted；on_interrupt(1) 恰被调一次。"""
    engine = FakeEngine({"a": _RUNNING_HALF, "b": _WHOLE_PASS}, tail_after_stop={"a": []})
    interrupt, polls = _interrupt_sequence([0, 1])  # 第一次轮询还没中断，之后一直是 1
    levels: list[int] = []
    result = schedule(_rm([_job("a"), _job("b")]), FakeResolver(engine), CollectSink(),
                      opts=ScheduleOpts(max_concurrency=1, interrupt=interrupt, on_interrupt=levels.append,
                                        interrupt_poll_s=0.05))
    (a,) = result.results
    assert a.scope_id == "a" and a.status == Status.ABORTED  # 有现场、被掐断
    assert result.stopped_by == "interrupt" and "b" not in engine.run_count  # worker 从未起
    # 说明按来源区分（真机演练实测：此前两处都写成 fail-fast 的文案）
    assert a.message == "收到中断信号：本 job 被中止" and a.error_type is None
    b = _outcome(result, "b")
    assert (b.status, b.state.message) == (Status.SKIPPED, "收到中断信号，本 job 没有启动")
    assert (_summary(result).status, _summary(result).message) == (Status.ABORTED, "收到中断信号，余下的 job 不再启动")
    assert levels == [1]
    assert len(polls) >= 2
    h = engine.handles["a"]
    # 协作停止：每次停止请求都带宽限，没有零宽限的强制
    assert h.stopped and h.stop_graces and all(g > 0 for g in h.stop_graces)


def test_user_interrupt_with_passed_and_aborted_marks_run_aborted():
    """中断时已有 job 出了判定（b 已 passed、a 被中止）：两个 job 都有结果、不需要结束写，run 按取法记 aborted（没有 error 与 failed、
    有 aborted），不是 passed；余下的 job 不再启动的来源照样记下 interrupt。"""
    a_started, b_done = threading.Event(), threading.Event()

    def a_gen(_job):
        a_started.set()  # 事件开始读出时 a 的句柄已返回：中断到达时 a 必是运行中的 worker、不会被记成 skipped
        yield from _RUNNING_HALF

    def b_gen(_job):
        a_started.wait(5.0)
        yield from _WHOLE_PASS

    engine = FakeEngine({"a": a_gen, "b": b_gen}, tail_after_stop={"a": []})
    levels: list[int] = []
    result = schedule(_rm([_job("a"), _job("b")]), FakeResolver(engine), CollectSink(),
                      opts=ScheduleOpts(max_concurrency=2, interrupt=lambda: 1 if b_done.is_set() else 0,
                                        on_interrupt=levels.append, interrupt_poll_s=0.05),
                      on_job_complete=lambda jr: b_done.set() if jr.scope_id == "b" else None)
    statuses = {jr.scope_id: jr.status for jr in result.results}
    assert statuses == {"a": Status.ABORTED, "b": Status.PASSED}
    assert result.stopped_by == "interrupt"
    assert _summary(result).status == Status.ABORTED
    assert levels == [1]


def test_zero_job_run_has_no_results_and_no_stop_source():
    """零个 job 的 run：执行事实里没有结果，也没有余下的 job 不再启动的来源。"""
    result = schedule(_rm([]), FakeResolver(FakeEngine({})), CollectSink())
    assert (result.results, result.stopped_by) == ((), None)


def test_user_interrupt_level2_forces_running_worker_with_zero_grace():
    """再次中断（级别 2）：在协作停止之外对运行中 worker 再发一次零宽限的 stop（子进程 adapter 即 SIGKILL）；
    on_interrupt 依次收到 1、2；判定仍按首次仲裁的 abort 落 ABORTED。"""
    import time as _t
    # on_stop 拖住每次 stop 0.2 秒：worker 在第一次 stop 返回前不会结束，保证 _force_all 看到的是仍在运行的 worker
    engine = FakeEngine({"a": _RUNNING_HALF}, tail_after_stop={"a": []}, on_stop=lambda _sid: _t.sleep(0.2))
    interrupt, _ = _interrupt_sequence([2])
    levels: list[int] = []
    result = schedule(_rm([_job("a")]), FakeResolver(engine), CollectSink(),
                      opts=ScheduleOpts(max_concurrency=1, interrupt=interrupt, on_interrupt=levels.append,
                                        interrupt_poll_s=0.05))
    assert levels == [1, 2]
    h = engine.handles["a"]
    assert 0.0 in h.stop_graces and any(g > 0 for g in h.stop_graces)  # 协作停止的宽限之外多了一次零宽限的强制
    assert result.results[0].status == Status.ABORTED
    assert _summary(result).status == Status.ABORTED


def test_user_interrupt_level_only_rises_once_per_level():
    """级别回调只在首次升高时触发：轮询多次仍为 1 不重复 on_interrupt，也不会升到强制。"""
    engine = FakeEngine({"a": _RUNNING_HALF}, tail_after_stop={"a": []}, tail_delay_s=0.3)  # 收尾拖 0.3 秒，期间会多轮询几次
    interrupt, polls = _interrupt_sequence([1])
    levels: list[int] = []
    schedule(_rm([_job("a")]), FakeResolver(engine), CollectSink(),
             opts=ScheduleOpts(max_concurrency=1, interrupt=interrupt, on_interrupt=levels.append, interrupt_poll_s=0.05))
    assert len(polls) >= 3
    assert levels == [1]
    assert 0.0 not in engine.handles["a"].stop_graces  # 级别没升到 2，没有零宽限的强制


def test_interrupt_arriving_after_all_jobs_done_is_not_acted_on():
    """全部 job 完成后才到的中断不处置：on_interrupt 不被调、判定照常 PASSED（组合根据此按判定给退出码）。
    轮询间隔放长，使 job 在第一次轮询前就完成。"""
    engine = FakeEngine({"b": _WHOLE_PASS})
    interrupt, polls = _interrupt_sequence([1])
    levels: list[int] = []
    result = schedule(_rm([_job("b")]), FakeResolver(engine), CollectSink(),
                      opts=ScheduleOpts(max_concurrency=1, interrupt=interrupt, on_interrupt=levels.append,
                                        interrupt_poll_s=5.0))
    assert _summary(result).status == Status.PASSED
    assert levels == []
    assert polls == []  # pending 已空，不再轮询


def test_no_interrupt_callback_keeps_passed_run_passed():
    """不注入 interrupt：等待循环与此前相同，正常 run 仍 PASSED（回归护栏）。"""
    engine = FakeEngine({"b": _WHOLE_PASS})
    result = schedule(_rm([_job("b")]), FakeResolver(engine), CollectSink(), opts=ScheduleOpts(max_concurrency=1))
    assert _summary(result).status == Status.PASSED


_WHOLE_PASS_A = [
    ScenarioStarted(scenario_id="a:0"),
    StepDone(scenario_id="a:0", step_index=0, status=Status.PASSED, votes=Votes(3, 3)),
    ScenarioDone(scenario_id="a:0", status=Status.PASSED),
    ScopeDone(scope_id="a"),
]


def test_on_job_complete_timeout_error_propagates_and_stops_running_workers():
    """落库回调抛 TimeoutError 必须冒泡（Python 3.11 起 concurrent.futures.TimeoutError 就是内建 TimeoutError 的别名，等待循环
    不得为了醒来轮询而把它吞掉），且冒泡前停掉仍在运行的 worker；注入了 interrupt 也一样。"""
    engine = FakeEngine({"b": _WHOLE_PASS, "a": _RUNNING_HALF}, tail_after_stop={"a": []})

    def on_job_complete(_jr):
        raise TimeoutError("persistence timed out")

    with pytest.raises(TimeoutError):
        schedule(_rm([_job("a"), _job("b")]), FakeResolver(engine), CollectSink(),
                 opts=ScheduleOpts(max_concurrency=2, interrupt=lambda: 0, interrupt_poll_s=0.05),
                 on_job_complete=on_job_complete)
    assert engine.handles["a"].stopped  # 止血：冒泡前停掉仍在运行的 worker


def test_force_requested_before_handle_returns_is_honored():
    """起 worker 期间（句柄尚未返回）到达的第二次中断不丢：句柄返回后的首次停止即用零宽限。"""
    import threading as _th

    class SlowStart(FakeEngine):
        def __init__(self, *a, **k):
            super().__init__(*a, **k)
            self.started = _th.Event()
            self.release = _th.Event()

        def run_scope(self, job):
            self.started.set()
            self.release.wait(5.0)
            return super().run_scope(job)

    engine = SlowStart({"a": _RUNNING_HALF}, tail_after_stop={"a": []})
    levels: list[int] = []

    def on_interrupt(level: int) -> None:
        levels.append(level)
        if level == 2:
            engine.release.set()  # 两级都处置完才让句柄返回

    result = schedule(_rm([_job("a")]), FakeResolver(engine), CollectSink(),
                      opts=ScheduleOpts(max_concurrency=1, interrupt=lambda: 2 if engine.started.is_set() else 0,
                                        on_interrupt=on_interrupt, interrupt_poll_s=0.05))
    assert levels == [1, 2]
    h = engine.handles["a"]
    assert h.stop_graces and all(g == 0.0 for g in h.stop_graces)  # 句柄返回后的停止全部零宽限
    assert result.results[0].status == Status.ABORTED
    assert _summary(result).status == Status.ABORTED


def test_interrupt_after_all_jobs_done_but_unconsumed_is_not_acted_on():
    """慢落库回调期间其他 job 已全部完成（future 已完成、尚未消费），随后才到的中断不处置：没有可停的 worker、判定已完整。"""
    import threading as _th
    import time as _t

    a_persist_started = _th.Event()

    def b_gen(_job):
        a_persist_started.wait(5.0)  # 等 a 的落库回调开始后再完成：此时 a 正被消费、b 完成后留在 pending
        yield from _WHOLE_PASS

    engine = FakeEngine({"a": _WHOLE_PASS_A, "b": b_gen})

    def on_job_complete(jr):
        if jr.scope_id == "a":
            a_persist_started.set()
            _t.sleep(0.4)

    levels: list[int] = []
    result = schedule(_rm([_job("a"), _job("b")]), FakeResolver(engine), CollectSink(),
                      opts=ScheduleOpts(max_concurrency=2, interrupt=lambda: 1, on_interrupt=levels.append,
                                        interrupt_poll_s=0.05),
                      on_job_complete=on_job_complete)
    assert _summary(result).status == Status.PASSED
    assert levels == []


# ---- 运行期限与这次 run 的记录（ADR 0054 决策二、五）：墙钟截止时刻、起 worker 与重试之前的检查次序、第三种中止来源、run 级裁决 ----

from gherkai_core.project import DEADLINE_TIMEOUT_MESSAGE, ENDED_ELSEWHERE_ABORT_MESSAGE  # noqa: E402

_DEADLINE_ENDING = RUN_ENDINGS["deadline"]  # 到期的结束写：run 级说明与没有启动的 job 的说明


class _FakeRecord:
    """注入 ScheduleOpts.record 的假记录（落库服务的替身）：claim 对 reject 里的 scope 拒绝并发出停手信号，记下每次认领与认领时刻；
    still_open 返回 open_ 并计数，读到「已结束」同样发出停手信号；ended 是停手信号本身，测试也可以直接置位它（模拟写 job 状态时得知
    run 级已结束）。claim_error / read_error 给出时对应调用抛出它（模拟存储不可达）。signals=False 时认领被拒与读到「已结束」不汇进
    停手信号，用来确认调度循环自己记下这两处发现、不依赖记录一侧。"""

    def __init__(self, *, reject=(), open_: bool = True, claim_error: BaseException | None = None,
                 read_error: BaseException | None = None, signals: bool = True):
        self.claims: list[tuple[str, datetime]] = []
        self.reads = 0
        self.reject = set(reject)
        self.open_ = open_
        self.claim_error = claim_error
        self.read_error = read_error
        self.signals = signals
        self.ended = threading.Event()

    def claim(self, scope_id: str, claimed_at: datetime) -> bool:
        if self.claim_error is not None and scope_id in self.reject:
            raise self.claim_error
        self.claims.append((scope_id, claimed_at))
        if scope_id in self.reject:
            if self.signals:
                self.ended.set()
            return False
        return True

    def still_open(self) -> bool:
        self.reads += 1
        if self.read_error is not None:
            raise self.read_error
        if not self.open_ and self.signals:
            self.ended.set()
        return self.open_

    def ended_elsewhere(self) -> bool:
        return self.ended.is_set()


def _rm_at(jobs: list[Job], deadline_at: str) -> RunMeta:
    return RunMeta(run_id="test-run", created_at="", jobs=tuple(jobs), deadline_at=deadline_at)


def test_job_budget_is_judged_on_the_wall_clock_not_the_monotonic_one():
    """job 的截止时刻按墙钟比较（ADR 0054 决策二第 2 条）：单调时钟一动不动（发起机器休眠时单调时钟不走），墙钟越过认领时刻加预算，
    job 照样按自己的预算超时、说明是原有的预算那一句。"""
    ft = _FakeTime(step=0.0)
    engine = FakeEngine({"a": [ScopeStarted(scope_id="a"), ScenarioStarted(scenario_id="a:0")]}, tail_after_stop={"a": []})
    res = schedule(_rm([_job("a", timeout_s=5.0)]), FakeResolver(engine), _JumpSink(ft, ScenarioStarted, seconds=6.0),
                   opts=ScheduleOpts(clock=lambda: 0.0, wall_clock=ft.wall, max_concurrency=1, heartbeat_interval_s=0.02,
                                     grace_period_s=1.0))
    jr = res.results[0]
    assert (jr.status, jr.error_type, jr.message) == (Status.ERROR, "timeout", "job 超时（预算 5s，已中止）")


_BUDGET_100 = (Status.ERROR, "timeout", "job 超时（预算 100s，已中止）")


@pytest.mark.parametrize("deadline_s, budget_s, expected", [
    (99.5, 100.0, (Status.ABORTED, None, DEADLINE_TIMEOUT_MESSAGE)),  # 期限早于认领时刻加预算：被期限截断
    (100.0, 100.0, _BUDGET_100),  # 两者相等：算 job 自己的预算到点
    (100.5, 100.0, _BUDGET_100),
])
def test_cutoff_is_the_earlier_of_budget_and_run_deadline(deadline_s, budget_s, expected):
    """截止时刻取认领时刻加预算与运行期限中较早的一个，相等时算预算（ADR 0054 决策二第 2 条）；被期限截断的 job 记 aborted、没有归因，
    说明是期限那一句，被自己的预算截断的记 error 加 timeout（ADR 0031 决定一）。全部 job 都有结果时不做结束写，run 的状态按取法、
    不带到期说明（第 4 条）。"""
    ft = _FakeTime(step=0.0)  # 认领时刻恰为假墙钟零点
    record = _FakeRecord()
    engine = FakeEngine({"a": [ScopeStarted(scope_id="a"), ScenarioStarted(scenario_id="a:0")]}, tail_after_stop={"a": []})
    res = schedule(_rm_at([_job("a", timeout_s=budget_s)], ft.at(deadline_s)), FakeResolver(engine), _JumpSink(ft, ScenarioStarted),
                   opts=ft.opts(max_concurrency=1, heartbeat_interval_s=0.02, grace_period_s=1.0, record=record))
    jr = res.results[0]
    assert (jr.status, jr.error_type, jr.message) == expected
    assert record.claims == [("a", _T0)]  # 认领时刻就是起 worker 之前读到的墙钟
    assert res.stopped_by is None
    assert (_summary(res).status, _summary(res).message) == (expected[0], None)


@pytest.mark.parametrize("deadline_s, starts", [(60.0, True), (59.999, False)])
def test_stop_start_boundary_is_strictly_after_deadline_minus_lead(deadline_s, starts):
    """停止启动的时刻是期限减 60 秒，「已过」取严格晚于：恰在那一刻仍启动，晚一点即不启动。"""
    ft = _FakeTime(step=0.0)
    engine = FakeEngine({"a": _passing_events("a", "a:0")})
    res = schedule(_rm_at([_job("a")], ft.at(deadline_s)), FakeResolver(engine), CollectSink(), opts=ft.opts(max_concurrency=1))
    assert ("a" in engine.run_count) is starts
    assert [jr.status for jr in res.results] == ([Status.PASSED] if starts else [])


def test_past_stop_start_starts_nothing_and_the_run_ends_with_the_deadline_ending():
    """一开始就已过停止启动的时刻（ADR 0054 决策二第 1 条）：不认领、不起 worker、不产出判定（不回调 on_job_complete），执行事实里
    没有结果，来路是 deadline；到期的结束写把每个 job 记 skipped 并带到期的说明，run 按取法记 aborted、run 级说明是「已超过允许运行的
    时间」（第 3 条）。设备 job 全部没有启动时设备计量两项为 0、不省键。"""
    ft = _FakeTime()
    record = _FakeRecord()
    engine = FakeEngine({"a": _passing_events("a", "a:0"), "d": _passing_events("d", "d:0")})
    seen: list = []
    res = schedule(_rm_at([_job("a"), _job("d", device="android")], ft.at(30.0)), FakeResolver(engine), CollectSink(),
                   opts=ft.opts(max_concurrency=2, record=record), on_job_complete=seen.append)
    assert engine.run_count == {} and record.claims == [] and seen == [] and res.results == ()
    assert res.stopped_by == "deadline"
    summary = _summary(res)
    assert (summary.status, summary.message) == (Status.ABORTED, _DEADLINE_ENDING.run_message)
    assert [(o.status, o.state.message) for o in summary.jobs] == [(Status.SKIPPED, _DEADLINE_ENDING.skipped_message)] * 2
    assert (summary.device_observed_s, summary.device_observed_missing) == (0.0, 0)


def test_queued_job_after_stop_start_has_no_verdict_and_the_finished_one_keeps_its_own():
    """执行中途越过停止启动的时刻：已在执行、内容完整的 job 保留它的判定；排队中的 job 不启动、不产出判定，由到期的结束写记 skipped，
    run 按取法记 aborted 并带到期的说明。"""
    ft = _FakeTime()
    engine = FakeEngine({"a": _passing_events("a", "a:0"), "b": _passing_events("b", "b:0")})
    seen: list = []
    res = schedule(_rm_at([_job("a"), _job("b")], ft.at(1000.0)), FakeResolver(engine), _JumpSink(ft, ScopeDone, seconds=950.0),
                   opts=ft.opts(max_concurrency=1), on_job_complete=seen.append)
    assert [(jr.scope_id, jr.status) for jr in res.results] == [("a", Status.PASSED)]
    assert [jr.scope_id for jr in seen] == ["a"] and "b" not in engine.run_count
    assert res.stopped_by == "deadline"
    assert (_outcome(res, "b").status, _outcome(res, "b").state.message) == (Status.SKIPPED, _DEADLINE_ENDING.skipped_message)
    assert (_summary(res).status, _summary(res).message) == (Status.ABORTED, _DEADLINE_ENDING.run_message)


def test_running_job_is_stopped_at_the_run_deadline_and_queued_job_stays_without_verdict():
    """到了运行期限，执行中的 job 的截止时刻已到（以期限封顶），走到点停止：内容不完整，记 aborted、没有归因、说明是期限那一句；之后
    排队中的 job 已过停止启动的时刻，不启动。开着 fail-fast 也一样：被期限截断不是这个 job 自己出错，不触发 fail-fast，来路是
    deadline，到期的结束写把排队的 job 记 skipped。"""
    ft = _FakeTime()
    engine = FakeEngine({"a": [ScopeStarted(scope_id="a"), ScenarioStarted(scenario_id="a:0")], "b": _passing_events("b", "b:0")},
                        tail_after_stop={"a": []})
    seen: list = []
    res = schedule(_rm_at([_job("a"), _job("b")], ft.at(1000.0)), FakeResolver(engine), _JumpSink(ft, ScenarioStarted, seconds=1001.0),
                   opts=ft.opts(max_concurrency=1, fail_fast=True, heartbeat_interval_s=0.02, grace_period_s=1.0),
                   on_job_complete=seen.append)
    a = res.results[0]
    assert [jr.scope_id for jr in res.results] == ["a"] and [jr.scope_id for jr in seen] == ["a"]
    assert (a.status, a.error_type, a.message) == (Status.ABORTED, None, DEADLINE_TIMEOUT_MESSAGE)
    assert engine.handles["a"].stopped and "b" not in engine.run_count
    assert res.stopped_by == "deadline"
    assert (_outcome(res, "b").status, _outcome(res, "b").state.message) == (Status.SKIPPED, _DEADLINE_ENDING.skipped_message)
    assert (_summary(res).status, _summary(res).message) == (Status.ABORTED, _DEADLINE_ENDING.run_message)


def test_stop_start_once_observed_is_kept_after_a_clock_rollback():
    """停止启动一经成立不撤销：墙钟先返回已过停止启动的时刻，之后回拨到更早的时刻。看到已过的那次检查拦下 b；回拨之后排队的 c 也不
    启动；来路取记下的事实、不重读墙钟：deadline，到期的结束写给 run 带上「已超过允许运行的时间」，没有启动的 job 不在执行事实里。"""
    t = {"s": 0.0}

    def wall() -> datetime:
        now = _T0 + timedelta(seconds=t["s"])
        if t["s"] >= 950.0:
            t["s"] = 0.0  # 返回已过停止启动的时刻的只有这一次读，之后墙钟回拨到期限之前很远
        return now

    class _Sink(CollectSink):  # a 的内容一完整，墙钟就越过停止启动的时刻（期限减 60 秒）
        def __call__(self, event) -> None:
            super().__call__(event)
            if isinstance(event, ScopeDone):
                t["s"] = 950.0

    engine = FakeEngine({sid: _passing_events(sid, f"{sid}:0") for sid in ("a", "b", "c")})
    res = schedule(_rm_at([_job("a"), _job("b"), _job("c")], (_T0 + timedelta(seconds=1000)).isoformat()), FakeResolver(engine),
                   _Sink(), opts=ScheduleOpts(max_concurrency=1, heartbeat_interval_s=0, wall_clock=wall))
    assert t["s"] == 0.0  # 已过的时刻确实被读到过、墙钟随后回拨
    assert [jr.scope_id for jr in res.results] == ["a"] and set(engine.run_count) == {"a"}
    assert res.stopped_by == "deadline"
    assert (_summary(res).status, _summary(res).message) == (Status.ABORTED, _DEADLINE_ENDING.run_message)


def test_job_cutoff_once_observed_is_kept_after_a_clock_rollback():
    """job 的截止时刻一经观察到已过就不撤销：事件间检查读到已过本 job 的截止时刻（认领时刻加预算 10 秒），随后的首次仲裁读到回拨
    之后的墙钟。job 仍记超时、说明是预算那一句，不落成中止：没有开 fail-fast，也没有任何中止来源。"""
    state = {"armed": False, "fired": False}

    def wall() -> datetime:
        if state["armed"] and not state["fired"]:
            state["fired"] = True
            return _T0 + timedelta(seconds=20)  # 只有这一次读越过截止时刻，之后墙钟回拨到认领时刻
        return _T0

    class _Sink(CollectSink):  # 第一个事件处理完之后，下一次事件间检查读墙钟时越过截止时刻
        def __call__(self, event) -> None:
            super().__call__(event)
            if isinstance(event, ScopeStarted):
                state["armed"] = True

    engine = FakeEngine({"a": [ScopeStarted(scope_id="a"), ScenarioStarted(scenario_id="a:0"),
                               ScenarioDone(scenario_id="a:0", status=Status.PASSED), ScopeDone(scope_id="a")]},
                        tail_after_stop={"a": []})
    res = schedule(_rm([_job("a", timeout_s=10.0)]), FakeResolver(engine), _Sink(),
                   opts=ScheduleOpts(max_concurrency=1, heartbeat_interval_s=0, wall_clock=wall, grace_period_s=1.0))
    assert state["fired"]  # 已过的时刻确实被读到过、墙钟随后回拨
    jr = res.results[0]
    assert (jr.status, jr.error_type, jr.message) == (Status.ERROR, "timeout", "job 超时（预算 10s，已中止）")
    assert _summary(res).status == Status.ERROR


def test_claim_rejected_means_ended_elsewhere_and_later_jobs_are_not_claimed():
    """认领被拒即发现 run 已被别处记为已结束：这个 job 不启动，之后的 job 在认领之前就被「已发现」那一项拦下，不再认领；都不产出判定，
    余下的 job 不再启动的来源是 ended-elsewhere（记录已是终态，落库服务不做结束写）。"""
    record = _FakeRecord(reject={"a"})
    engine = FakeEngine({"a": _passing_events("a", "a:0"), "b": _passing_events("b", "b:0")})
    seen: list = []
    res = schedule(_rm([_job("a"), _job("b")]), FakeResolver(engine), CollectSink(),
                   opts=ScheduleOpts(max_concurrency=1, record=record), on_job_complete=seen.append)
    assert [sid for sid, _ in record.claims] == ["a"] and engine.run_count == {} and seen == [] and res.results == ()
    assert res.stopped_by == "ended-elsewhere"


def test_scheduler_keeps_its_own_discoveries_without_the_record_signal():
    """认领被拒、重试之前读到 run 级终态是调度循环自己看到的发现，当场记下、不等记录一侧把它们汇进停手信号：认领被拒之后的 job 不再
    认领、不启动；读到终态的重试不再进行，这一次的结果不被采用；两种情形来源都是 ended-elsewhere。"""
    record = _FakeRecord(reject={"a"}, signals=False)
    engine = FakeEngine({"a": _passing_events("a", "a:0"), "b": _passing_events("b", "b:0")})
    res = schedule(_rm([_job("a"), _job("b")]), FakeResolver(engine), CollectSink(),
                   opts=ScheduleOpts(max_concurrency=1, record=record))
    assert [sid for sid, _ in record.claims] == ["a"] and res.results == () and res.stopped_by == "ended-elsewhere"
    assert not record.ended.is_set()  # 记录一侧确实没有给信号

    record = _FakeRecord(open_=False, signals=False)
    engine = FakeEngine({"n": _passing_events("n", "n:0")}, network_crash_after={"n": [0]})
    res = schedule(_rm([_job("n")]), FakeResolver(engine), CollectSink(),
                   opts=ScheduleOpts(max_concurrency=1, network_retry=1, retry_sleep=_NOSLEEP, record=record))
    assert record.reads == 1 and engine.run_count["n"] == 1
    assert (res.results, res.stopped_by) == ((), "ended-elsewhere")


def test_no_claim_when_the_run_is_already_aborted():
    """认领排在各项检查之后、紧贴起 worker：run 已因 fail-fast 中止时排队的 job 不认领、不启动，来源是 fail-fast（已过停止启动的时刻
    也不认领，见上面「一开始就已过停止启动的时刻」那一条）。"""
    record = _FakeRecord()
    engine = FakeEngine({"crash": _passing_events("crash", "crash:0"), "q": _passing_events("q", "q:0")}, crash_after={"crash": 0})
    res = schedule(_rm([_job("crash"), _job("q")]), FakeResolver(engine), CollectSink(),
                   opts=ScheduleOpts(max_concurrency=1, fail_fast=True, record=record))
    assert [sid for sid, _ in record.claims] == ["crash"]
    assert [(jr.scope_id, jr.status) for jr in res.results] == [("crash", Status.ERROR)] and res.stopped_by == "fail-fast"


def test_ended_elsewhere_check_precedes_abort_for_queued_jobs():
    """排队中的 job 起 worker 之前，「已发现 run 被别处结束」排在「run 已中止」之前、也在认领之前：两者都成立时它不认领、不启动。
    这里 crash job 崩溃之前（同一个 worker 线程里）停手信号已成立，随后它的 error 在判定得出时登记 fail-fast；调度循环这时还没有读停手
    信号，余下的 job 不再启动的来源取最先登记的 fail-fast。记录已被别处结束时落库服务按停手信号收尾、不做结束写。"""
    record = _FakeRecord()

    def crash_gen(job):
        record.ended.set()  # 写 job 状态时得知 run 级已结束
        raise RuntimeError("崩")
        yield  # 使它成为生成器函数：第一次取事件时才执行上面两行

    engine = FakeEngine({"crash": crash_gen, "q": _passing_events("q", "q:0")})
    res = schedule(_rm([_job("crash"), _job("q")]), FakeResolver(engine), CollectSink(),
                   opts=ScheduleOpts(max_concurrency=1, fail_fast=True, record=record, interrupt_poll_s=5.0))
    assert [(jr.scope_id, jr.status) for jr in res.results] == [("crash", Status.ERROR)]
    assert "q" not in engine.run_count and [sid for sid, _ in record.claims] == ["crash"]
    assert res.stopped_by == "fail-fast"


def test_queued_job_is_not_claimed_when_the_abort_source_is_ended_elsewhere(monkeypatch):
    """读停手信号得到「未发现」之后、看中止标志之前，另一个线程以 ended-elsewhere 登记了中止标志：排队中的 job 不认领、不启动、不产出
    判定，来源是 ended-elsewhere。这里直接构造这个状态：中止标志已以 ended-elsewhere 置位，停手信号的读取返回 False。"""
    import gherkai_core.schedule as sch

    monkeypatch.setattr(sch._EndedElsewhere, "seen", lambda self: False)
    orig = sch._Worker.__init__

    def spy(self, *a, **kw):
        orig(self, *a, **kw)
        self.abort_flag.set("ended-elsewhere")

    monkeypatch.setattr(sch._Worker, "__init__", spy)
    record = _FakeRecord()
    engine = FakeEngine({"q": _passing_events("q", "q:0")})
    seen: list = []
    res = schedule(_rm([_job("q")]), FakeResolver(engine), CollectSink(),
                   opts=ScheduleOpts(max_concurrency=1, record=record), on_job_complete=seen.append)
    assert res.results == () and seen == [] and engine.run_count == {} and record.claims == []
    assert res.stopped_by == "ended-elsewhere"


def test_claim_rejected_concurrently_keeps_the_other_queued_job_unclaimed(monkeypatch):
    """两个 job 并发起步，a 的认领被拒：b 恰在读完停手信号（未发现）之后、看中止标志之前碰上 a 登记 ended-elsewhere。b 同样不认领、
    不启动、不产出判定，来源是 ended-elsewhere。钩子把这个交错固定下来：a 的认领等 b 读完停手信号才被拒，b 读完之后等 a 登记完再往下走。"""
    import gherkai_core.schedule as sch

    who = threading.local()
    b_read, a_noted = threading.Event(), threading.Event()
    orig_run, orig_seen, orig_note = sch._Worker.run, sch._EndedElsewhere.seen, sch._EndedElsewhere.note

    def run(self):
        who.scope = self.job.scope_id
        return orig_run(self)

    def seen(self):
        found = orig_seen(self)
        if getattr(who, "scope", None) == "b" and not found and not b_read.is_set():
            b_read.set()
            a_noted.wait(5.0)
        return found

    def note(self):
        orig_note(self)
        if getattr(who, "scope", None) == "a":
            a_noted.set()

    monkeypatch.setattr(sch._Worker, "run", run)
    monkeypatch.setattr(sch._EndedElsewhere, "seen", seen)
    monkeypatch.setattr(sch._EndedElsewhere, "note", note)
    record = _FakeRecord(reject={"a"})
    orig_claim = record.claim

    def claim(scope_id, claimed_at):
        if scope_id == "a":
            b_read.wait(5.0)
        return orig_claim(scope_id, claimed_at)

    record.claim = claim
    engine = FakeEngine({"a": _passing_events("a", "a:0"), "b": _passing_events("b", "b:0")})
    done: list = []
    res = schedule(_rm([_job("a"), _job("b")]), FakeResolver(engine), CollectSink(),
                   opts=ScheduleOpts(max_concurrency=2, record=record), on_job_complete=done.append)
    assert b_read.is_set() and a_noted.is_set()  # 交错确实发生
    assert res.results == () and done == [] and engine.run_count == {} and [sid for sid, _ in record.claims] == ["a"]
    assert res.stopped_by == "ended-elsewhere"


def test_stop_signal_is_polled_with_the_interrupt_cadence_and_stops_running_jobs():
    """停手信号（写 job 状态时得知 run 级已结束）由等待循环按使用方中断的节拍读取：这里没有注入 interrupt、worker 也没有心跳（卡在等停
    里看不到中止标志），仍由主线程当场落定并发停止请求；运行中的 job 记 aborted、说明是「这个 run 已被记为已结束」，排队的不启动。"""
    import time

    record = _FakeRecord()

    class _Sink(CollectSink):
        def __call__(self, event) -> None:
            super().__call__(event)
            if isinstance(event, ScopeStarted):
                record.ended.set()

    engine = FakeEngine({"a": [ScopeStarted(scope_id="a")], "b": _passing_events("b", "b:0")}, tail_after_stop={"a": []})
    t0 = time.monotonic()
    res = schedule(_rm([_job("a"), _job("b")]), FakeResolver(engine), _Sink(),
                   opts=ScheduleOpts(max_concurrency=1, heartbeat_interval_s=0, grace_period_s=1.0, record=record,
                                     interrupt_poll_s=0.02))
    assert time.monotonic() - t0 < 3.0  # 没等到假 worker 的 5 秒等停超时
    a = res.results[0]
    assert [jr.scope_id for jr in res.results] == ["a"] and "b" not in engine.run_count
    assert (a.status, a.error_type, a.message) == (Status.ABORTED, None, ENDED_ELSEWHERE_ABORT_MESSAGE)
    assert res.stopped_by == "ended-elsewhere"


def test_claim_rejected_for_one_job_stops_the_other_running_job():
    """认领被拒（另一个 job 起 worker 之前）同样停下运行中的 job：worker 线程当场记下，运行中的 job 在下一次事件间检查按首次仲裁记 aborted。"""
    record = _FakeRecord(reject={"b"})
    a_running = threading.Event()

    def a_gen(job):
        yield ScopeStarted(scope_id="a")
        a_running.set()

    engine = FakeEngine({"a": a_gen, "b": _passing_events("b", "b:0")}, tail_after_stop={"a": []})
    orig_claim = record.claim  # b 的认领在 a 已经运行之后才发生

    def claim(scope_id, claimed_at):
        if scope_id == "b":
            a_running.wait(5.0)
        return orig_claim(scope_id, claimed_at)

    record.claim = claim
    res = schedule(_rm([_job("a"), _job("b")]), FakeResolver(engine), CollectSink(),
                   opts=ScheduleOpts(max_concurrency=2, heartbeat_interval_s=0.02, grace_period_s=1.0, record=record))
    assert [jr.scope_id for jr in res.results] == ["a"] and "b" not in engine.run_count
    assert (res.results[0].status, res.results[0].message) == (Status.ABORTED, ENDED_ELSEWHERE_ABORT_MESSAGE)


def test_fail_fast_first_then_ended_elsewhere_keeps_the_fail_fast_message():
    """运行中的 job 的停止原因按首次仲裁落定一次、中止的说明取最先成立的来源：fail-fast 先成立、随后才发现 run 已被别处结束（在 victim
    已被落定、发出停止请求之后），说明仍是 fail-fast 那一句，余下的 job 不再启动的来源也是 fail-fast。"""
    record = _FakeRecord()
    crash_now = threading.Event()

    def crash_gen(job):
        yield ScenarioStarted(scenario_id="c:0")
        crash_now.wait(5)
        raise RuntimeError("崩")

    def on_event(scope_id, i):
        if scope_id == "v":
            crash_now.set()  # v 已运行：让 crash job 崩，fail-fast 先成立

    def on_stop(scope_id):
        if scope_id == "v":
            record.ended.set()

    engine = FakeEngine({"v": [ScopeStarted(scope_id="v")], "c": crash_gen}, on_event=on_event, on_stop=on_stop,
                        tail_after_stop={"v": []})
    res = schedule(_rm([_job("v"), _job("c")]), FakeResolver(engine), CollectSink(),
                   opts=ScheduleOpts(max_concurrency=2, fail_fast=True, heartbeat_interval_s=0.02, grace_period_s=1.0,
                                     record=record, interrupt_poll_s=0.02))
    v = next(jr for jr in res.results if jr.scope_id == "v")
    assert (v.status, v.message) == (Status.ABORTED, "fail-fast：其他 job 失败，本 job 被中止")
    assert res.stopped_by == "fail-fast"


def test_ended_elsewhere_first_then_interrupt_keeps_the_ended_message():
    """反过来：先发现 run 已被别处结束、运行中的 job 已被落定之后使用方才中断（收尾期间），说明仍是「这个 run 已被记为已结束」那一句。"""
    record = _FakeRecord()

    class _Sink(CollectSink):
        def __call__(self, event) -> None:
            super().__call__(event)
            record.ended.set()  # 写 job 状态时得知 run 级已结束

    engine = FakeEngine({"a": _RUNNING_HALF}, tail_after_stop={"a": []}, tail_delay_s=0.3)  # 收尾拖 0.3 秒，期间中断到达

    def interrupt() -> int:
        h = engine.handles.get("a")
        return 1 if h is not None and h.stopped else 0

    levels: list[int] = []
    res = schedule(_rm([_job("a")]), FakeResolver(engine), _Sink(),
                   opts=ScheduleOpts(max_concurrency=1, interrupt=interrupt, on_interrupt=levels.append, interrupt_poll_s=0.02,
                                     record=record))
    assert levels == [1]
    assert (res.results[0].status, res.results[0].message) == (Status.ABORTED, ENDED_ELSEWHERE_ABORT_MESSAGE)
    assert res.stopped_by == "ended-elsewhere"


def test_interrupt_then_ended_elsewhere_keeps_the_interrupt_message():
    """使用方中断先成立、随后才发现 run 已被别处结束：运行中的 job 的说明仍是中断那一句，来源也是 interrupt。"""
    record = _FakeRecord()
    engine = FakeEngine({"a": _RUNNING_HALF}, tail_after_stop={"a": []}, on_stop=lambda _s: record.ended.set())
    levels: list[int] = []
    res = schedule(_rm([_job("a")]), FakeResolver(engine), CollectSink(),
                   opts=ScheduleOpts(max_concurrency=1, interrupt=lambda: 1 if "a" in engine.handles else 0,
                                     on_interrupt=levels.append, interrupt_poll_s=0.02, record=record))
    assert levels == [1]
    assert (res.results[0].status, res.results[0].message) == (Status.ABORTED, "收到中断信号：本 job 被中止")
    assert res.stopped_by == "interrupt"


def test_ended_found_in_a_persistence_callback_before_an_interrupt_keeps_the_ended_message():
    """落库服务在一次落库回调里发现 run 已结束，使用方中断在这之后才到，两者都早于等待循环的下一次轮询：中止的说明取最先登记的来源，
    被停的 job 记「这个 run 已被记为已结束」。那次回调一直等到中断被处置之后才返回，所以这里看的是等待循环的次序：同一次轮询里先读
    停手信号、再处理中断。"""
    record = _FakeRecord()
    handled = threading.Event()

    def on_event(event):
        if isinstance(event, ScopeStarted):
            record.ended.set()  # 写 job 状态时得知 run 级已结束
            handled.wait(5.0)

    levels: list[int] = []

    def on_interrupt(level: int) -> None:
        levels.append(level)
        handled.set()

    engine = FakeEngine({"a": [ScopeStarted(scope_id="a"), ScenarioStarted(scenario_id="a:0")]}, tail_after_stop={"a": []})
    res = schedule(_rm([_job("a")]), FakeResolver(engine), CollectSink(),
                   opts=ScheduleOpts(max_concurrency=1, interrupt=lambda: 1 if record.ended.is_set() else 0,
                                     on_interrupt=on_interrupt, interrupt_poll_s=0.02, grace_period_s=1.0, record=record),
                   on_event=on_event)
    assert levels == [1]
    assert (res.results[0].status, res.results[0].message) == (Status.ABORTED, ENDED_ELSEWHERE_ABORT_MESSAGE)
    assert res.stopped_by == "ended-elsewhere"


def test_interrupt_registered_before_ended_is_found_in_a_persistence_callback_keeps_the_interrupt_message():
    """反过来：中断先被轮询登记，之后才在一次落库回调里发现 run 已结束：说明是中断那一句，后登记的来源不改写先登记的。"""
    record = _FakeRecord()
    interrupted = threading.Event()  # 中断已登记、停止请求已发出

    def on_event(event):
        if interrupted.is_set():
            record.ended.set()  # 收尾事件的那次写 job 状态时得知 run 级已结束

    engine = FakeEngine({"a": [ScopeStarted(scope_id="a"), ScenarioStarted(scenario_id="a:0")]},
                        tail_after_stop={"a": [ScenarioDone(scenario_id="a:0", status=Status.PASSED)]},
                        on_stop=lambda _s: interrupted.set())
    levels: list[int] = []
    res = schedule(_rm([_job("a")]), FakeResolver(engine), CollectSink(),
                   opts=ScheduleOpts(max_concurrency=1, interrupt=lambda: 1 if "a" in engine.handles else 0,
                                     on_interrupt=levels.append, interrupt_poll_s=0.02, grace_period_s=1.0, record=record),
                   on_event=on_event)
    assert levels == [1] and record.ended.is_set()
    assert (res.results[0].status, res.results[0].message) == (Status.ABORTED, "收到中断信号：本 job 被中止")
    assert res.stopped_by == "interrupt"


def test_ended_found_in_on_event_is_registered_before_a_later_fail_fast():
    """落库服务在 v 的一次落库回调里发现 run 已结束，随后 c 才得出 error 判定（fail-fast 在判定得出时登记），两者都早于等待循环的下一次
    轮询：发现在那次回调返回之后当场登记、先于 fail-fast，v 的说明是「这个 run 已被记为已结束」。c 在发现之前已报出 scope 级 error，
    判定不受后来的中止影响；关掉心跳，事件逐个取出：c 的事件流等 v 的那次回调返回、v 取下一个事件时才结束。"""
    record = _FakeRecord()
    c_reported, v_moved_on = threading.Event(), threading.Event()

    def on_event(event):
        if isinstance(event, ScopeStarted) and event.scope_id == "v":
            c_reported.wait(5.0)
            record.ended.set()  # 写 v 的 job 状态时得知 run 级已结束

    def engine_on_event(scope_id, i):
        if scope_id == "v" and i == 1:  # v 的第二个事件产出时，第一个事件的落库回调已经返回
            v_moved_on.set()

    def c_gen(job):
        yield ScopeDone(scope_id="c", status=Status.ERROR, error_type="engine_error", message="未就绪")
        c_reported.set()  # c 的事件循环已处理完 scope 级 error、来取下一个事件
        v_moved_on.wait(5.0)

    engine = FakeEngine({"v": [ScopeStarted(scope_id="v"), ScenarioStarted(scenario_id="v:0")], "c": c_gen},
                        on_event=engine_on_event, tail_after_stop={"v": []})
    res = schedule(_rm([_job("v"), _job("c")]), FakeResolver(engine), CollectSink(),
                   opts=ScheduleOpts(max_concurrency=2, fail_fast=True, heartbeat_interval_s=0, grace_period_s=1.0,
                                     record=record, interrupt_poll_s=5.0),
                   on_event=on_event)
    statuses = {jr.scope_id: (jr.status, jr.message) for jr in res.results}
    assert statuses["v"] == (Status.ABORTED, ENDED_ELSEWHERE_ABORT_MESSAGE)
    assert statuses["c"][0] == Status.ERROR
    assert res.stopped_by == "ended-elsewhere"


def test_ended_found_in_on_job_complete_is_registered_before_a_later_fail_fast(monkeypatch):
    """p、q 同批交给等待循环：落库服务在写其中第一个的终态时发现 run 已结束；第二个的落库回调一直等到 c 得出 error、以 fail-fast 登记
    之后才返回，这都早于等待循环的下一次轮询。发现在第一次回调返回之后当场登记、先于 fail-fast，被停下的 v 的说明是「这个 run 已被记为
    已结束」。c 在发现之前已报出 scope 级 error，判定不受后来的中止影响；关掉心跳、不接 on_event，回调之间没有别处读停手信号。"""
    import time

    import gherkai_core.schedule as sch

    record = _FakeRecord()
    v_started, c_reported, c_go, c_registered = (threading.Event() for _ in range(4))
    calls: list[str] = []
    orig_run, orig_wait = sch._Worker.run, sch._wait_futures

    def run(self):
        try:
            return orig_run(self)
        finally:
            if self.job.scope_id == "c":
                c_registered.set()  # c 的判定已得出，fail-fast 在返回之前已登记

    def wait(fs, timeout=None, return_when=sch.FIRST_COMPLETED):
        done, rest = orig_wait(fs, timeout=timeout, return_when=return_when)
        if done and not calls:  # 第一次有 job 完成时等到 p、q 都完成，两者同批交出（c 与 v 此刻都仍在运行）
            end = time.monotonic() + 5.0
            while sum(f.done() for f in fs) < 2 and time.monotonic() < end:
                time.sleep(0.005)
            done = {f for f in fs if f.done()}
            rest = set(fs) - done
        return done, rest

    def on_job_complete(jr):
        calls.append(jr.scope_id)
        if len(calls) == 1:
            v_started.wait(5.0)
            c_reported.wait(5.0)
            record.ended.set()  # 写这个 job 的终态时得知 run 级已结束
        elif len(calls) == 2:
            c_go.set()
            c_registered.wait(5.0)

    def c_gen(job):
        yield ScopeDone(scope_id="c", status=Status.ERROR, error_type="engine_error", message="未就绪")
        c_reported.set()  # c 的事件循环已处理完 scope 级 error、来取下一个事件
        c_go.wait(5.0)

    def engine_on_event(scope_id, i):
        if scope_id == "v" and i == 0:  # v 已通过起 worker 之前的检查、认领并起了 worker
            v_started.set()

    monkeypatch.setattr(sch._Worker, "run", run)
    monkeypatch.setattr(sch, "_wait_futures", wait)
    engine = FakeEngine({"p": _passing_events("p", "p:0"), "q": _passing_events("q", "q:0"), "c": c_gen,
                         "v": [ScopeStarted(scope_id="v"), ScenarioStarted(scenario_id="v:0")]},
                        on_event=engine_on_event, tail_after_stop={"v": []})
    res = schedule(_rm([_job("p"), _job("q"), _job("c"), _job("v")]), FakeResolver(engine), CollectSink(),
                   opts=ScheduleOpts(max_concurrency=4, fail_fast=True, heartbeat_interval_s=0, grace_period_s=1.0,
                                     record=record, interrupt_poll_s=5.0),
                   on_job_complete=on_job_complete)
    assert sorted(calls[:2]) == ["p", "q"] and c_registered.is_set()  # 交错确实发生
    statuses = {jr.scope_id: (jr.status, jr.message) for jr in res.results}
    assert statuses["v"] == (Status.ABORTED, ENDED_ELSEWHERE_ABORT_MESSAGE)
    assert statuses["c"][0] == Status.ERROR and statuses["p"][0] == statuses["q"][0] == Status.PASSED
    assert res.stopped_by == "ended-elsewhere"


def test_abort_flag_records_only_the_first_cause_under_concurrent_set():
    """并发的两次登记只有第一次记下来源：判空与赋值之间插不进另一次登记。这里让第一次登记读到「尚无来源」之后停一下，给第二个线程插进来
    的机会；它只能等第一次登记完成，读到已有的来源，不再赋值。"""
    import time

    import gherkai_core.schedule as sch

    first_read = threading.Event()
    assigned: list[str] = []

    class _Probe(sch._AbortFlag):
        @property
        def cause(self):
            value = self.__dict__.get("_probe_cause")
            if value is None and threading.current_thread().name == "first":
                first_read.set()
                time.sleep(0.2)  # 第二个线程此刻若能进来，会同样读到「尚无来源」
            return value

        @cause.setter
        def cause(self, value):
            self.__dict__["_probe_cause"] = value
            if value is not None:
                assigned.append(value)

    ledger = sch._StartsStopped()
    flag = _Probe(ledger)
    first = threading.Thread(target=flag.set, args=("fail-fast",), name="first")
    second = threading.Thread(target=lambda: (first_read.wait(5.0), flag.set("interrupt")), name="second")
    first.start()
    second.start()
    first.join(5.0)
    second.join(5.0)
    assert assigned == ["fail-fast"] and flag.cause == "fail-fast" and flag.is_set()
    assert ledger.first == "fail-fast"  # 余下的 job 不再启动的来源同样只记第一次


def test_deadline_passed_at_the_moment_of_decision_wins_over_ended_elsewhere():
    """做出停止决定的那一刻截止时刻已过即为到点：墙钟越过期限的同时发现 run 已被别处结束，运行中的 job 按期限截断记（aborted、期限
    那一句），不记「这个 run 已被记为已结束」那一句。"""
    ft = _FakeTime()
    record = _FakeRecord()

    class _Sink(CollectSink):
        def __call__(self, event) -> None:
            super().__call__(event)
            if isinstance(event, ScenarioStarted):
                ft.jump(1001.0)
                record.ended.set()

    engine = FakeEngine({"a": [ScopeStarted(scope_id="a"), ScenarioStarted(scenario_id="a:0")]}, tail_after_stop={"a": []})
    res = schedule(_rm_at([_job("a")], ft.at(1000.0)), FakeResolver(engine), _Sink(),
                   opts=ft.opts(max_concurrency=1, heartbeat_interval_s=0.02, grace_period_s=1.0, record=record,
                                interrupt_poll_s=0.02))
    a = res.results[0]
    assert (a.status, a.error_type, a.message) == (Status.ABORTED, None, DEADLINE_TIMEOUT_MESSAGE)


def test_interrupt_then_past_stop_start_ends_the_run_by_the_interrupt():
    """使用方中断之后、排队中的 job 起 worker 之前已过停止启动的时刻：它不启动、不产出判定；余下的 job 不再启动的来源取最先登记的
    interrupt，结束写把它记 skipped、带中断的说明，run 级说明也是中断那一句（退出码按信号取，由组合根给）。"""
    ft = _FakeTime()
    engine = FakeEngine({"a": _RUNNING_HALF, "b": _WHOLE_PASS}, tail_after_stop={"a": []},
                        on_stop=lambda scope: scope == "a" and ft.jump(950.0))  # 中断停下 a 期间墙钟越过停止启动的时刻
    levels: list[int] = []
    res = schedule(_rm_at([_job("a"), _job("b")], ft.at(1000.0)), FakeResolver(engine), CollectSink(),
                   opts=ft.opts(max_concurrency=1, interrupt=lambda: 1 if "a" in engine.handles else 0,
                                on_interrupt=levels.append, interrupt_poll_s=0.02))
    assert levels == [1] and "b" not in engine.run_count
    assert [(jr.scope_id, jr.status, jr.message) for jr in res.results] == [("a", Status.ABORTED, "收到中断信号：本 job 被中止")]
    assert res.stopped_by == "interrupt"
    assert (_outcome(res, "b").status, _outcome(res, "b").state.message) == (Status.SKIPPED, RUN_ENDINGS["interrupt"].skipped_message)
    assert (_summary(res).status, _summary(res).message) == (Status.ABORTED, RUN_ENDINGS["interrupt"].run_message)


def test_fail_fast_registered_before_stop_start_is_the_stop_source(monkeypatch):
    """余下的 job 不再启动的来源取最先登记的一条：fail-fast 在判定得出时登记之后，排队的 q 起 worker 之前的检查才观察到已过停止启动的
    时刻。q 因停止启动而不启动，来源仍是 fail-fast：结束写把 q 记 skipped、带 fail-fast 的说明，run 有 error 即记 error。"""
    import gherkai_core.schedule as sch

    ft = _FakeTime()
    orig_set = sch._AbortFlag.set

    def set_then_pass_stop_start(self, cause="fail-fast"):  # fail-fast 一登记，墙钟就越过停止启动的时刻（期限减 60 秒）
        orig_set(self, cause)
        ft.jump(950.0)

    monkeypatch.setattr(sch._AbortFlag, "set", set_then_pass_stop_start)
    engine = FakeEngine({"crash": _passing_events("crash", "crash:0"), "q": _passing_events("q", "q:0")}, crash_after={"crash": 0})
    res = schedule(_rm_at([_job("crash"), _job("q")], ft.at(1000.0)), FakeResolver(engine), CollectSink(),
                   opts=ft.opts(max_concurrency=1, fail_fast=True))
    assert [(jr.scope_id, jr.status) for jr in res.results] == [("crash", Status.ERROR)] and "q" not in engine.run_count
    assert res.stopped_by == "fail-fast"
    q = _outcome(res, "q")
    assert (q.status, q.state.message) == (Status.SKIPPED, RUN_ENDINGS["fail-fast"].skipped_message)
    assert (_summary(res).status, _summary(res).message) == (Status.ERROR, RUN_ENDINGS["fail-fast"].run_message)


def test_stop_start_observed_before_fail_fast_is_the_stop_source(monkeypatch):
    """反过来：排队的 c 起 worker 之前的检查先观察到已过停止启动的时刻、登记 deadline，此后执行中的 a 才出错、登记 fail-fast。来源是
    deadline：结束写把 c 记 skipped、带到期的说明，run 有 error 即记 error、带到期的 run 级说明。"""
    import gherkai_core.schedule as sch

    ft = _FakeTime()
    observed = threading.Event()
    orig_check = sch._StopStart.check

    def check(self):
        hit = orig_check(self)
        if hit:
            observed.set()
        return hit

    monkeypatch.setattr(sch._StopStart, "check", check)

    def a_gen(job):  # 等 c 的检查观察到停止启动之后才出错
        yield ScopeStarted(scope_id="a")
        observed.wait(5.0)
        raise RuntimeError("崩")

    engine = FakeEngine({"a": a_gen, "b": _passing_events("b", "b:0"), "c": _passing_events("c", "c:0")})
    res = schedule(_rm_at([_job("a"), _job("b"), _job("c")], ft.at(1000.0)), FakeResolver(engine),
                   _JumpSink(ft, ScopeDone, seconds=950.0),  # b 的内容一完整，墙钟就越过停止启动的时刻
                   opts=ft.opts(max_concurrency=2, fail_fast=True))
    assert observed.is_set() and "c" not in engine.run_count
    assert {jr.scope_id: jr.status for jr in res.results} == {"a": Status.ERROR, "b": Status.PASSED}
    assert res.stopped_by == "deadline"
    c = _outcome(res, "c")
    assert (c.status, c.state.message) == (Status.SKIPPED, _DEADLINE_ENDING.skipped_message)
    assert (_summary(res).status, _summary(res).message) == (Status.ERROR, _DEADLINE_ENDING.run_message)


def test_claim_failure_is_a_persistence_failure():
    """认领本身失败（存储不可达）按运行期落库失败处理：异常原样冒泡出 schedule()，冒泡前停掉运行中的 worker，失败的 job 不产出判定。"""
    boom = OSError("存储不可达")
    record = _FakeRecord(reject={"b"}, claim_error=boom)
    a_running = threading.Event()

    def a_gen(job):
        yield ScopeStarted(scope_id="a")
        a_running.set()

    engine = FakeEngine({"a": a_gen, "b": _passing_events("b", "b:0")}, tail_after_stop={"a": []})
    orig_claim = record.claim

    def claim(scope_id, claimed_at):
        if scope_id == "b":
            a_running.wait(5.0)
        return orig_claim(scope_id, claimed_at)

    record.claim = claim
    seen: list = []
    with pytest.raises(OSError) as exc:
        schedule(_rm([_job("a"), _job("b")]), FakeResolver(engine), CollectSink(),
                 opts=ScheduleOpts(max_concurrency=2, heartbeat_interval_s=0, grace_period_s=1.0, record=record),
                 on_job_complete=seen.append)
    assert exc.value is boom
    assert engine.handles["a"].stopped and "b" not in engine.run_count and all(jr.scope_id != "b" for jr in seen)


# ---- 重试之前的检查（ADR 0054 决策二「上一次尝试已经结束、正在等待重试的 job」一条）：产品的 run 不开 job 级重试，规则在调度层核 ----

_NOT_RETRIED_DEADLINE = "这个 run 已接近或超过允许运行的时间：未再重试"
_NOT_RETRIED_FAIL_FAST = "fail-fast：其他 job 失败，未再重试"
_NOT_RETRIED_INTERRUPT = "收到中断信号：未再重试"


@pytest.mark.parametrize("hold, expected, reads", [
    ({"deadline", "ended", "abort", "closed"}, _NOT_RETRIED_DEADLINE, 0),
    ({"ended", "abort", "closed"}, None, 0),
    ({"abort", "closed"}, _NOT_RETRIED_FAIL_FAST, 0),
    ({"interrupt", "closed"}, _NOT_RETRIED_INTERRUPT, 0),
    ({"closed"}, None, 1),
])
def test_retry_checks_run_in_order_and_note_the_first_hit(monkeypatch, hold, expected, reads):
    """退避期间成立的停止原因按次序检查、取最先命中的一条：已过停止启动的时刻；已发现 run 被别处结束；run 已中止（说明按中止来源区分
    fail-fast 与使用方中断）；读到 run 级已是终态。命中即不再重试。命中已过停止启动或 run 已中止时保留上一次的 network_error 判定并
    注明原因，经 on_job_complete 作为终态写下；命中「已发现 run 被别处结束」（含读到终态）时这一次的结果不被采用：不进执行事实、
    不回调（expected 为 None，ADR 0054 决策五）。前三项命中时不读存储。重试不再认领：认领只在第一次起 worker 之前做一次。"""
    import gherkai_core.schedule as sch

    ft = _FakeTime()
    record = _FakeRecord()
    captured = {}
    orig = sch._Worker.__init__

    def spy(self, *a, **kw):
        orig(self, *a, **kw)
        captured["w"] = self

    monkeypatch.setattr(sch._Worker, "__init__", spy)

    def backoff(_s):  # 上一次尝试已经结束、正在等待重试时，这些原因同时成立
        if "deadline" in hold:
            ft.jump(950.0)
        if "ended" in hold:
            record.ended.set()
        if "abort" in hold:
            captured["w"].abort_flag.set("fail-fast")
        if "interrupt" in hold:
            captured["w"].abort_flag.set("interrupt")
        if "closed" in hold:
            record.open_ = False

    engine = FakeEngine({"n": _passing_events("n", "n:0")}, network_crash_after={"n": [0]})
    seen: list = []
    res = schedule(_rm_at([_job("n")], ft.at(1000.0)), FakeResolver(engine), CollectSink(),
                   opts=ft.opts(max_concurrency=1, network_retry=1, retry_sleep=backoff, record=record),
                   on_job_complete=seen.append)
    assert engine.run_count["n"] == 1
    assert record.reads == reads and [sid for sid, _ in record.claims] == ["n"]
    if expected is None:
        assert res.results == () and seen == []
        return
    (jr,) = res.results
    assert (jr.status, jr.error_type) == (Status.ERROR, "network_error")
    assert jr.message.endswith("；" + expected), jr.message
    assert [x.message for x in seen] == [jr.message]


def test_retry_proceeds_after_one_read_without_claiming_again():
    """检查都不命中时照常重试：重新起 worker 之前读一次 run 级状态、不再认领，截止时刻沿用第一次认领时算出的那个。"""
    record = _FakeRecord()
    engine = FakeEngine({"n": _passing_events("n", "n:0")}, network_crash_after={"n": [0, 0]})
    res = schedule(_rm([_job("n")]), FakeResolver(engine), CollectSink(),
                   opts=ScheduleOpts(max_concurrency=1, network_retry=2, retry_sleep=_NOSLEEP, record=record))
    assert engine.run_count["n"] == 3 and res.results[0].status == Status.PASSED
    assert record.reads == 2 and [sid for sid, _ in record.claims] == ["n"]


def test_retry_found_ended_before_backoff_drops_the_result_without_waiting():
    """上一次尝试结束时 run 已被别处结束（这次尝试期间写 job 状态时得知）：不必等退避、不读存储，这一次的结果不被采用，不进执行事实。"""
    record = _FakeRecord()
    sleeps: list[float] = []

    def gen(job):
        record.ended.set()
        return iter([])

    engine = FakeEngine({"n": gen}, network_crash_after={"n": [0]})
    res = schedule(_rm([_job("n")]), FakeResolver(engine), CollectSink(),
                   opts=ScheduleOpts(max_concurrency=1, network_retry=1, retry_sleep=sleeps.append, record=record,
                                     interrupt_poll_s=5.0))  # 主线程这期间不轮询：这次尝试的判定只由 worker 自己给出
    assert sleeps == [] and record.reads == 0 and engine.run_count["n"] == 1
    assert (res.results, res.stopped_by) == ((), "ended-elsewhere")


def test_retry_drops_the_result_when_the_abort_source_is_ended_elsewhere(monkeypatch):
    """等待重试的 job 碰上同一个交错：退避期间另一个线程以 ended-elsewhere 登记了中止标志，而停手信号的读取返回 False。重新启动之前的
    检查按「已发现 run 被别处结束」处理，不按 fail-fast：这一次的结果不被采用；中止标志那一项已命中，不再读存储。"""
    import gherkai_core.schedule as sch

    monkeypatch.setattr(sch._EndedElsewhere, "seen", lambda self: False)
    captured = {}
    orig = sch._Worker.__init__

    def spy(self, *a, **kw):
        orig(self, *a, **kw)
        captured["w"] = self

    monkeypatch.setattr(sch._Worker, "__init__", spy)
    record = _FakeRecord()
    engine = FakeEngine({"n": _passing_events("n", "n:0")}, network_crash_after={"n": [0]})
    res = schedule(_rm([_job("n")]), FakeResolver(engine), CollectSink(),
                   opts=ScheduleOpts(max_concurrency=1, network_retry=1, record=record,
                                     retry_sleep=lambda _s: captured["w"].abort_flag.set("ended-elsewhere")))
    assert engine.run_count["n"] == 1 and record.reads == 0
    assert (res.results, res.stopped_by) == ((), "ended-elsewhere")


def test_retry_is_not_restarted_after_a_clock_rollback_once_stop_start_was_observed(monkeypatch):
    """停止启动一经成立不撤销，对等待重试的 job 同样成立：n 退避期间，排队的 b 的检查读到已过停止启动的时刻、没有启动；随后墙钟回拨到
    更早的时刻，n 重新启动之前的检查仍按已过处理，不再重试、注明原因。来路是 deadline：到期的结束写记下 b，run 有 error 即记 error，
    带「已超过允许运行的时间」。"""
    import gherkai_core.schedule as sch

    t = {"s": 0.0}
    in_backoff, b_done = threading.Event(), threading.Event()
    orig_run = sch._Worker.run

    def run(self):
        if self.job.scope_id != "b":
            return orig_run(self)
        in_backoff.wait(5.0)  # b 在 n 等待重试期间才起步
        try:
            return orig_run(self)
        finally:
            b_done.set()

    def backoff(_s):
        t["s"] = 950.0  # 越过停止启动的时刻（期限减 60 秒）
        in_backoff.set()
        b_done.wait(5.0)
        t["s"] = 10.0  # b 的检查已经看到已过，墙钟随后回拨

    monkeypatch.setattr(sch._Worker, "run", run)
    engine = FakeEngine({"n": _passing_events("n", "n:0"), "b": _passing_events("b", "b:0")}, network_crash_after={"n": [0]})
    res = schedule(_rm_at([_job("n"), _job("b")], (_T0 + timedelta(seconds=1000)).isoformat()), FakeResolver(engine), CollectSink(),
                   opts=ScheduleOpts(max_concurrency=2, network_retry=1, retry_sleep=backoff,
                                     wall_clock=lambda: _T0 + timedelta(seconds=t["s"])))
    assert b_done.is_set() and engine.run_count == {"n": 1}
    n = res.results[0]
    assert [jr.scope_id for jr in res.results] == ["n"] and n.error_type == "network_error"
    assert n.message.endswith("；" + _NOT_RETRIED_DEADLINE), n.message
    assert res.stopped_by == "deadline" and _outcome(res, "b").status == Status.SKIPPED
    assert (_summary(res).status, _summary(res).message) == (Status.ERROR, _DEADLINE_ENDING.run_message)


def test_retry_read_failure_is_a_persistence_failure():
    """重试之前那次读本身失败（存储不可达）按运行期落库失败处理：异常原样冒泡出 schedule()，不再重试、不产出判定。"""
    boom = OSError("存储不可达")
    record = _FakeRecord(read_error=boom)
    engine = FakeEngine({"n": _passing_events("n", "n:0")}, network_crash_after={"n": [0]})
    seen: list = []
    with pytest.raises(OSError) as exc:
        schedule(_rm([_job("n")]), FakeResolver(engine), CollectSink(),
                 opts=ScheduleOpts(max_concurrency=1, network_retry=1, retry_sleep=_NOSLEEP, record=record),
                 on_job_complete=seen.append)
    assert exc.value is boom and engine.run_count["n"] == 1 and seen == []
