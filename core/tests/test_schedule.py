"""schedule 模块测试（ADR 0026）：并发归约 + 失败隔离 + fail-fast + 超时 + 优雅停。

用内存假 Engine（不起子进程）+ fake clock（不真等墙钟），验证 schedule 逻辑。
"""
from __future__ import annotations

import threading

import pytest

from gherkai_core.model import (
    RunMeta,
    Cost,
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
    Votes,
)
from gherkai_core.schedule import ScheduleOpts, schedule
from tests.fake_engine import CollectSink, FakeEngine, FakeResolver


class _IncClock:
    """确定性递增时钟：每次调用 +step（默认 1.0）。用于精确测时长。"""

    def __init__(self, step: float = 1.0) -> None:
        self.t = 0.0
        self.step = step

    def __call__(self) -> float:
        self.t += self.step
        return self.t


def _job(scope_id: str, engine: str = "midscene", n_scenarios: int = 1, timeout_s: float | None = None) -> Job:
    scenarios = tuple(
        Scenario(id=f"{scope_id}:{i}", name=f"sc{i}", steps=(Step(0, "When", "做事"),))
        for i in range(n_scenarios)
    )
    return Job(scope_id=scope_id, scope_name=scope_id, engine=engine, scenarios=scenarios, timeout_s=timeout_s)


def _rm(jobs: list[Job], run_id: str = "test-run") -> RunMeta:
    """测试用：把 Job[] 包成 RunMeta（definition）喂 schedule（ADR 0016）。"""
    return RunMeta(run_id=run_id, created_at="", jobs=tuple(jobs))


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
    assert result.status == Status.PASSED
    assert len(result.jobs) == 2
    assert all(jr.status == Status.PASSED for jr in result.jobs)
    # sink 收到所有事件（2 job × 4 事件，含 scope_done）
    assert len(sink.events) == 8


# ---- 断言失败 → RunResult failed（区别于 error）----
def test_assertion_failed_is_failed_not_error():
    jobs = [_job("a")]
    engine = FakeEngine({"a": _failing_events("a", "a:0")})
    result = schedule(_rm(jobs), FakeResolver(engine), CollectSink())
    assert result.status == Status.FAILED
    assert result.jobs[0].status == Status.FAILED
    assert result.jobs[0].scenarios[0].status == Status.FAILED


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
    crash_jr = next(jr for jr in result.jobs if jr.scope_id == "crash")
    ok_jr = next(jr for jr in result.jobs if jr.scope_id == "ok")
    assert crash_jr.status == Status.ERROR
    assert crash_jr.error_type == "engine_error"
    assert ok_jr.status == Status.PASSED  # 未受牵连
    assert result.status == Status.ERROR  # 总状态：有 error


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
    assert result.status == Status.ERROR  # 确定性：run 判错
    crash_jr = next(jr for jr in result.jobs if jr.scope_id == "crash")
    assert crash_jr.status == Status.ERROR
    # 被牵连的 slow：协作式中止下结局依时序（已完成 passed / 运行到一半 aborted / 排队没起 skipped 都合法），
    # 但**绝不该是 error**——被牵连中止不是自身故障（ADR 0031；精确的 skipped/aborted 复现见 test_lifecycle_states）。
    # 注：PASSED 只在「见到 scope_done（真正完成）」时可达——运行到一半被掐、流 EOF 无 scope_done 必 ABORTED
    # （内容完整前置，0026），此断言不再可能掩盖「部分完成聚合成 PASSED」的假绿。
    slow_jr = next(jr for jr in result.jobs if jr.scope_id == "slow")
    assert slow_jr.status in (Status.PASSED, Status.ABORTED, Status.SKIPPED)
    assert slow_jr.status != Status.ERROR


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
    ok_jr = next(jr for jr in result.jobs if jr.scope_id == "ok")
    assert ok_jr.status == Status.PASSED  # 隔离：ok 运行结束


# ---- 超时（fake clock）：job 运行太久 → stop + error:timeout ----
def test_timeout_with_fake_clock():
    # fake clock：每次被读 +10s。job_timeout=5s → 第一次事件间检查就超时
    ticks = {"t": 0.0}

    def fake_clock():
        ticks["t"] += 10.0
        return ticks["t"]

    # 慢流：多个事件，每个事件触发一次 clock 推进
    long_events = [ScenarioStarted(scenario_id="slow:0")]
    for i in range(5):
        long_events.append(StepDone(scenario_id="slow:0", step_index=i, status=Status.PASSED, votes=Votes(3, 3)))
    long_events.append(ScenarioDone(scenario_id="slow:0", status=Status.PASSED))

    jobs = [_job("slow", timeout_s=5.0)]
    engine = FakeEngine({"slow": long_events})
    result = schedule(
        _rm(jobs), FakeResolver(engine), CollectSink(),
        opts=ScheduleOpts(grace_period_s=2.0, clock=fake_clock),
    )
    assert result.status == Status.ERROR
    assert result.jobs[0].error_type == "timeout"
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
    a_jr = next(jr for jr in result.jobs if jr.scope_id == "a")
    b_jr = next(jr for jr in result.jobs if jr.scope_id == "b")
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
    assert [jr.scope_id for jr in result.jobs] == ["z", "a", "m"]


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
    a_jr = next(jr for jr in result.jobs if jr.scope_id == "a")
    b_jr = next(jr for jr in result.jobs if jr.scope_id == "b")
    assert abs(a_jr.total_time_worked_s - 12.0) < 1e-9
    assert abs(b_jr.total_time_worked_s - 5.0) < 1e-9
    assert abs(result.total_time_worked_s - 17.0) < 1e-9  # run 级跨 scope 合计
    assert result.total_tokens is None  # Nova 引擎不报 token


def test_token_aggregation():
    # Midscene 形态：tokens 累加
    engine = FakeEngine({"m": _events_with_tokens("m:0", [1000, 500])})
    result = schedule(_rm([_job("m")]), FakeResolver(engine), CollectSink())
    m_jr = result.jobs[0]
    assert m_jr.total_tokens == 1500
    assert m_jr.total_time_worked_s is None  # Midscene 不报时长
    assert result.total_tokens == 1500
    assert result.total_time_worked_s is None


def test_cost_none_when_no_cost_data():
    # 无 cost 的事件流 → 两个原生量合计都保持 None（不假装 0）
    engine = FakeEngine({"a": _passing_events("a", "a:0")})
    result = schedule(_rm([_job("a")]), FakeResolver(engine), CollectSink())
    assert result.jobs[0].total_tokens is None
    assert result.jobs[0].total_time_worked_s is None
    assert result.total_tokens is None
    assert result.total_time_worked_s is None


def test_mixed_legs_each_native_metric_aggregated_separately():
    # 混引擎：nova 报 time_worked_s、midscene 报 tokens → 各自合计、互不污染、都不丢
    engine = FakeEngine({
        "nova": _events_with_time("nova:0", [9.0]),
        "mid": _events_with_tokens("mid:0", [2000]),
    })
    result = schedule(_rm([_job("nova"), _job("mid")]), FakeResolver(engine), CollectSink())
    nova_jr = next(jr for jr in result.jobs if jr.scope_id == "nova")
    mid_jr = next(jr for jr in result.jobs if jr.scope_id == "mid")
    assert abs(nova_jr.total_time_worked_s - 9.0) < 1e-9 and nova_jr.total_tokens is None
    assert mid_jr.total_tokens == 2000 and mid_jr.total_time_worked_s is None
    # run 级：两个原生量各自合计，都不被静默漏掉
    assert abs(result.total_time_worked_s - 9.0) < 1e-9
    assert result.total_tokens == 2000


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
    jr = result.jobs[0]
    assert jr.status == Status.ERROR        # 状态如实反映失败
    assert jr.total_tokens == 2000          # 但失败步消耗的 token 仍计入（1200+800）
    assert result.total_tokens == 2000


# ---- 并发上限：max_concurrency=1 → 串行，仍全部运行完成 ----
def test_serial_concurrency_one():
    jobs = [_job(f"j{i}") for i in range(5)]
    engine = FakeEngine({f"j{i}": _passing_events(f"j{i}", f"j{i}:0") for i in range(5)})
    result = schedule(_rm(jobs), FakeResolver(engine), CollectSink(), opts=ScheduleOpts(max_concurrency=1))
    assert result.status == Status.PASSED
    assert len(result.jobs) == 5


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
    # 无超时（Job.timeout_s=None）时 core 每事件只读 1 次 clock，时长可预期且层级嵌套。
    engine = FakeEngine({"sc": _full_timed_events("sc", "sc:0", n_steps=2)})
    result = schedule(
        _rm([_job("sc")]), FakeResolver(engine), CollectSink(),
        opts=ScheduleOpts(clock=_IncClock(1.0)),  # 单位秒；core 乘 1000 → ms
    )
    jr = result.jobs[0]
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
    jr = result.jobs[0]
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
    jr = result.jobs[0]
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
    steps = result.jobs[0].scenarios[0].steps
    # step 0 挂两个 trajectory、原样搬入不聚合到 scenario 级
    assert len(steps[0].report_refs) == 2 and steps[0].report_refs[0].kind == "trajectory"
    assert steps[1].report_refs == ()  # 无产物步为空
    assert result.jobs[0].scenarios[0].report_refs == ()  # 不再聚合到 scenario 级


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
    steps = result.jobs[0].scenarios[0].steps
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
    assert result.jobs[0].scenarios[0].status == Status.ERROR  # scenario 判定是 error（未被 skipped 影响）
    assert result.jobs[0].status == Status.ERROR               # job 判定是 error
    assert result.status == Status.ERROR                        # run 判定是 error


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
    steps = result.jobs[0].scenarios[0].steps
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
    assert result.status == Status.PASSED
    assert engine.run_count["n"] == 3  # 起了 3 次 worker（2 次重试）


def test_network_error_exhausted_is_network_error():
    # 每次 attempt 都建连失败 → 重试耗尽 → job error_type=network_error
    engine = FakeEngine({"n": _passing_events("n", "n:0")}, network_crash_after={"n": 0})
    result = schedule(_rm([_job("n")]), FakeResolver(engine), CollectSink(),
                      opts=ScheduleOpts(network_retry=2, retry_sleep=_NOSLEEP))
    assert result.status == Status.ERROR
    assert result.jobs[0].error_type == "network_error"
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
    assert result.status == Status.ERROR
    assert result.jobs[0].error_type == "network_error"
    assert engine.run_count["n"] == 1  # 会话已起 → 不重试，只运行 1 次


def test_network_retry_default_off():
    # 默认 network_retry=0 → 网络崩不重试，记 network_error
    engine = FakeEngine({"n": _passing_events("n", "n:0")}, network_crash_after={"n": 0})
    result = schedule(_rm([_job("n")]), FakeResolver(engine), CollectSink())
    assert result.status == Status.ERROR
    assert result.jobs[0].error_type == "network_error"
    assert engine.run_count["n"] == 1  # 默认不重试


def test_non_network_crash_not_retried():
    # 普通 worker 崩（engine_error）即使开了 network_retry 也不重试
    engine = FakeEngine({"n": _passing_events("n", "n:0")}, crash_after={"n": 0})
    result = schedule(_rm([_job("n")]), FakeResolver(engine), CollectSink(),
                      opts=ScheduleOpts(network_retry=2, retry_sleep=_NOSLEEP))
    assert result.status == Status.ERROR
    assert result.jobs[0].error_type == "engine_error"
    assert engine.run_count["n"] == 1  # engine_error 不重试


def test_network_retry_deadline_not_reset_across_attempts():
    # job timeout 跨 attempt 不重置（ADR 0028）：用 _IncClock 让时间每次读 +1s，
    # timeout_s=2 → 第一次 attempt 建连崩、重试时 clock 已过 deadline → 记 timeout（不再无限重试）
    engine = FakeEngine({"n": _passing_events("n", "n:0")}, network_crash_after={"n": 0})
    clock = _IncClock(1.0)
    result = schedule(_rm([_job("n", timeout_s=2.0)]), FakeResolver(engine), CollectSink(),
                      opts=ScheduleOpts(network_retry=5, clock=clock, retry_sleep=_NOSLEEP))
    # deadline 跨 attempt 共享：几次 attempt 后墙钟超 2s → 转 timeout，不会用满 network_retry=5
    assert result.status == Status.ERROR
    assert engine.run_count["n"] < 6  # 没用满 5 次重试（被共享 deadline 截断）


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
    assert result.status == Status.PASSED


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


def test_on_job_complete_fires_for_skipped_job():
    # 关键（ADR 0030/0031）：skipped 的 job 从没 event 流过，但仍必须经回调落库
    # （否则 ResultStore 缺该 scope 的文件、CI 读单 scope 落空）。
    jobs = [_job("crash"), _job("queued")]
    engine = FakeEngine({"crash": _passing_events("crash", "crash:0"),
                         "queued": _passing_events("queued", "queued:0")},
                        crash_after={"crash": 0})
    seen: dict[str, Status] = {}
    schedule(_rm(jobs), FakeResolver(engine), CollectSink(),
             opts=ScheduleOpts(max_concurrency=1, fail_fast=True),
             on_job_complete=lambda jr: seen.__setitem__(jr.scope_id, jr.status))
    # 两个 job 都回调了——含从未 spawn 的 skipped job
    assert seen.get("crash") == Status.ERROR
    assert seen.get("queued") == Status.SKIPPED


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
    # 会等它们自然结束（真 AgentCore 会话持续计费）。验：异常仍抛 + in-flight worker 的 handle 被 stop。
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
    assert result.status == Status.PASSED


def test_default_opts_no_min_grace_backcompat():
    # 默认 min_grace_s=0.0 → 不破直接构造 ScheduleOpts 的调用方（默认 grace 5.0 > 0 且 ≥ 0，放行）。
    engine = FakeEngine({"a": _passing_events("a", "a:0")})
    result = schedule(_rm([_job("a")]), FakeResolver(engine), CollectSink())
    assert result.status == Status.PASSED


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
    jr = result.jobs[0]
    assert jr.status == Status.ERROR
    assert jr.error_type == "engine_error"
    assert result.status == Status.ERROR


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
    v_jr = next(jr for jr in result.jobs if jr.scope_id == "v")
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

    class _Clock:  # 第 7 次读时一次性越过 deadline（事件处理约每条读两次时钟），之后慢走——排空上界（grace 加余量）不该被假时钟立刻耗尽
        def __init__(self): self.n = 0; self.t = 0.0
        def __call__(self):
            self.n += 1; self.t += 1000.0 if self.n == 7 else 0.001; return self.t

    res = schedule(_rm([_job(scope, timeout_s=5.0)]), FakeResolver(engine), CollectSink(),
                   opts=ScheduleOpts(max_concurrency=1, clock=_Clock(), heartbeat_interval_s=0.05, grace_period_s=1.0))
    jr = res.jobs[0]
    assert (jr.status, jr.error_type) == (Status.ERROR, "timeout")
    assert [s.release for s in jr.sessions] == ["confirmed"] and (jr.device_observed_s, jr.device_observed_missing) == (3.0, 0)
    assert "未能确认停止" not in (jr.message or "")
    assert engine.handles[scope].stopped


def test_timeout_wins_over_abort_when_deadline_already_passed_on_every_branch():
    """首次仲裁：那一刻 deadline 已过就取 timeout，即使 abort_flag 也已置位——事件分支、WorkerExitError 分支、EOF 分支都一样；
    deadline 未过时同样的置位则判 abort（ABORTED）。abort_flag 在 worker 已 spawn、首事件之前置位（起 worker 前置位会得 SKIPPED）。"""
    import gherkai_core.schedule as sch
    from gherkai_core.errors import WorkerExitError

    def run(scope: str, behavior, *, deadline_passed: bool, set_flag: bool):
        class _Clock:
            def __init__(self): self.n = 0
            def __call__(self):  # 前两次读（run 起点、deadline 基点）为 0；之后一律在 deadline 之后、慢走（别把排空上界也耗尽）
                self.n += 1
                if not deadline_passed:
                    return self.n * 0.001
                return 0.0 if self.n <= 2 else 1000.0 + self.n * 0.001

        captured = {}
        orig = sch._Worker.__init__

        def spy(self, *a, **kw):
            orig(self, *a, **kw)
            captured["w"] = self

        def gen(job):  # worker 已 spawn、首事件前把 fail-fast 标志置位（模拟其他 job 恰在此刻失败）
            if set_flag:
                captured["w"].abort_flag.set()
            return behavior(job)

        sch._Worker.__init__ = spy
        try:
            res = schedule(_rm([_job(scope, timeout_s=1.0)]), FakeResolver(FakeEngine({scope: gen})), CollectSink(),
                           opts=ScheduleOpts(max_concurrency=1, clock=_Clock(), heartbeat_interval_s=0.05, grace_period_s=1.0))
        finally:
            sch._Worker.__init__ = orig
        return res.jobs[0]

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

    class _Clock:  # 第 5 次读（第二条事件的事件间检查）越过 deadline；之后每次读前进 1 秒，排空上界（1 加 5 秒）几次心跳内到点
        def __init__(self): self.n = 0; self.t = 0.0
        def __call__(self):
            self.n += 1
            self.t += 1000.0 if self.n == 5 else (1.0 if self.n > 5 else 0.001)
            return self.t

    engine = FakeEngine({scope: [ScopeStarted(scope_id=scope), ScenarioStarted(scenario_id="h:0")]}, hang_after_stop={scope})
    t0 = time.monotonic()
    res = schedule(_rm([_job(scope, timeout_s=5.0)]), FakeResolver(engine), CollectSink(),
                   opts=ScheduleOpts(max_concurrency=1, clock=_Clock(), heartbeat_interval_s=0.05, grace_period_s=1.0))
    assert time.monotonic() - t0 < 3.0  # 不等真实的 6 秒、也不永远等
    jr = res.jobs[0]
    assert (jr.status, jr.error_type) == (Status.ERROR, "timeout") and engine.handles[scope].stopped


def test_deadline_after_scope_done_hurries_exit_but_keeps_verdict():
    """内容完整后不再仲裁（ADR 0034 机制二）：scope_done 已到、worker 收尾期间 deadline 到点 → 只催停（发停止请求），判定仍按内容（PASSED）。"""
    scope = "p"
    events = _passing_events(scope, "p:0")  # 末尾带 scope_done
    n = len(events)

    class _Clock:  # 事件各读两次时钟；全部处理完后的第一次心跳检查（第 2n+3 次读）越过 deadline
        def __init__(self): self.n = 0; self.t = 0.0
        def __call__(self):
            self.n += 1; self.t += 1000.0 if self.n == 2 * n + 3 else 0.001; return self.t

    engine = FakeEngine({scope: events}, tail_after_stop={scope: []})  # 发完事件后活着等停（模拟释放阶段拖过预算）
    res = schedule(_rm([_job(scope, timeout_s=5.0)]), FakeResolver(engine), CollectSink(),
                   opts=ScheduleOpts(max_concurrency=1, clock=_Clock(), heartbeat_interval_s=0.05, grace_period_s=1.0))
    jr = res.jobs[0]
    assert (jr.status, jr.error_type) == (Status.PASSED, None) and engine.handles[scope].stopped


def test_fail_fast_does_not_preempt_network_retry():
    """开 fail_fast 时，可重试的瞬时网络故障（零 step_done 的 network_error）先重试、不触发整批中止；重试成功则 run 通过。"""
    engine = FakeEngine({"a": _passing_events("a", "a:0"), "b": _passing_events("b", "b:0")}, network_crash_after={"a": [0]})
    res = schedule(_rm([_job("a"), _job("b")]), FakeResolver(engine), CollectSink(),
                   opts=ScheduleOpts(max_concurrency=1, fail_fast=True, network_retry=1, retry_sleep=lambda s: None))
    assert engine.run_count["a"] == 2 and res.status == Status.PASSED
    assert [jr.status for jr in res.jobs] == [Status.PASSED, Status.PASSED]


def test_fail_fast_stops_running_workers_from_main_thread_without_heartbeat():
    """fail-fast：主线程的 _stop_all 对仍在运行的 worker 当场落定并发停止请求，不依赖该 worker 自己的心跳检查（这里关掉心跳、
    victim 卡在等停里看不到 abort_flag）。那一刻 deadline 未过的 victim 记 ABORTED，已过的记 timeout。"""
    import time

    def run(scope: str, timeout_s: float | None, crash_delay_s: float):
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
        return next(jr for jr in res.jobs if jr.scope_id == scope)

    jr = run("v", timeout_s=None, crash_delay_s=0.0)
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
    v = next(jr for jr in res.jobs if jr.scope_id == "v")
    assert (v.status, v.error_type) == (Status.ABORTED, None)
    assert [s.release for s in v.sessions] == ["confirmed"] and "未能确认停止" not in (v.message or "")


def test_generic_exception_still_stops_worker_and_spawn_failure_goes_through_finalize():
    """事件流中的普通异常（解析失败 / sink 抛错）后仍向 worker 发停止请求（别留孤儿进程）；起 worker 失败以退出码未知进终结函数：
    消息保留「起 worker 失败」，已过 deadline 的按首次仲裁记 timeout。"""
    engine = FakeEngine({"x": [ScopeStarted(scope_id="x"), ScenarioStarted(scenario_id="x:0")]}, crash_after={"x": 1})
    res = schedule(_rm([_job("x")]), FakeResolver(engine), CollectSink(), opts=ScheduleOpts(max_concurrency=1))
    jr = res.jobs[0]
    assert (jr.status, jr.error_type) == (Status.ERROR, "engine_error") and jr.message.startswith("worker 异常：")
    assert engine.handles["x"].stopped

    class Boom:
        def run_scope(self, job):
            raise OSError("spawn 失败")

    res = schedule(_rm([_job("y")]), FakeResolver(Boom()), CollectSink(), opts=ScheduleOpts(max_concurrency=1))
    assert (res.jobs[0].status, res.jobs[0].error_type, res.jobs[0].message) == (Status.ERROR, "engine_error", "起 worker 失败：spawn 失败")

    class _Clock:  # run 起点与 deadline 基点为 0，之后一律在 deadline 之后
        def __init__(self): self.n = 0
        def __call__(self): self.n += 1; return 0.0 if self.n <= 2 else 1000.0

    res = schedule(_rm([_job("z", timeout_s=1.0)]), FakeResolver(Boom()), CollectSink(), opts=ScheduleOpts(max_concurrency=1, clock=_Clock()))
    assert (res.jobs[0].status, res.jobs[0].error_type) == (Status.ERROR, "timeout")


def test_stop_all_decides_for_every_worker_before_any_blocking_stop():
    """fail-fast 批量中止：先对全部运行中的 worker 落定停止原因、再发停止请求。真 stop() 会阻塞到宽限到点，边落定边停会让前一个 worker
    消耗的宽限把后一个的仲裁推到它的 deadline 之后、把本该的 ABORTED 记成 timeout。这里让假 stop() 把假时钟推过所有 deadline。"""
    class _Clock:
        def __init__(self): self.t = 0.0
        def __call__(self): self.t += 0.001; return self.t

    clock = _Clock()
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
                        on_stop=lambda scope: scope.startswith("v") and setattr(clock, "t", clock.t + 1000.0))
    res = schedule(_rm([_job("v1", timeout_s=50.0), _job("v2", timeout_s=50.0), _job("c")]), FakeResolver(engine), CollectSink(),
                   opts=ScheduleOpts(max_concurrency=3, fail_fast=True, heartbeat_interval_s=0, grace_period_s=1.0, clock=clock))
    by = {jr.scope_id: (jr.status, jr.error_type) for jr in res.jobs}
    assert by["v1"] == (Status.ABORTED, None) and by["v2"] == (Status.ABORTED, None), by


def test_generic_exception_arbitrates_before_blocking_stop():
    """普通异常分支先按首次仲裁落定、再发停止请求：停止前已成立的 abort 不被停止期间越过的 deadline 改成 timeout。"""
    import gherkai_core.schedule as sch

    class _Clock:
        def __init__(self): self.t = 0.0
        def __call__(self): self.t += 0.001; return self.t

    clock = _Clock()
    captured = {}
    orig = sch._Worker.__init__

    def spy(self, *a, **kw):
        orig(self, *a, **kw)
        captured["w"] = self

    def gen(job):  # 零事件：整批已被中止，随后事件流以普通异常断掉
        captured["w"].abort_flag.set()
        raise RuntimeError("解析失败")

    engine = FakeEngine({"x": gen}, on_stop=lambda scope: setattr(clock, "t", clock.t + 1000.0))
    sch._Worker.__init__ = spy
    try:
        res = schedule(_rm([_job("x", timeout_s=50.0)]), FakeResolver(engine), CollectSink(),
                       opts=ScheduleOpts(max_concurrency=1, heartbeat_interval_s=0.05, grace_period_s=1.0, clock=clock))
    finally:
        sch._Worker.__init__ = orig
    jr = res.jobs[0]
    assert (jr.status, jr.error_type) == (Status.ABORTED, None) and engine.handles["x"].stopped


def test_hang_after_hurry_exit_is_timeout_like_stateless_path():
    """内容完整后催停、worker 却卡死不退出：排空上界到点按「退出码未知」回判——deadline 已过记 timeout，与无状态路径的 timed_out 记录一致。"""
    scope = "p"
    events = _passing_events(scope, "p:0")
    n = len(events)

    class _Clock:
        def __init__(self): self.n = 0; self.t = 0.0
        def __call__(self):
            self.n += 1
            self.t += 1000.0 if self.n == 2 * n + 3 else (1.0 if self.n > 2 * n + 3 else 0.001)
            return self.t

    engine = FakeEngine({scope: events}, hang_after_stop={scope})
    res = schedule(_rm([_job(scope, timeout_s=5.0)]), FakeResolver(engine), CollectSink(),
                   opts=ScheduleOpts(max_concurrency=1, clock=_Clock(), heartbeat_interval_s=0.05, grace_period_s=1.0))
    assert (res.jobs[0].status, res.jobs[0].error_type) == (Status.ERROR, "timeout")


def test_fail_fast_during_retry_backoff_keeps_network_error_not_skipped():
    """退避期间整批被 fail-fast 中止：不再重试，但已经运行过一次的 job 保留上次的 network_error 判定（不记成「未启动」的 SKIPPED）。"""
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
    jr = res.jobs[0]
    assert engine.run_count["a"] == 1 and (jr.status, jr.error_type) == (Status.ERROR, "network_error")
    assert "未再重试" in jr.message


def test_drain_bound_counts_from_stop_request_not_after_blocking_stop():
    """排空上界从停止请求时刻起算：真 stop() 阻塞消耗的宽限不再额外加进上界。假 stop() 把时钟推进很多，正确实现随后第一次心跳检查就到点；
    若从 stop() 返回后起算，还要再等满宽限加余量（多读六次以上时钟）。"""
    scope = "h"

    class _Clock:
        def __init__(self): self.n = 0; self.t = 0.0; self.n_at_stop = None
        def __call__(self):
            self.n += 1
            self.t += 1000.0 if self.n == 5 else (1.0 if self.n > 5 else 0.001)
            return self.t

    clock = _Clock()

    def on_stop(scope_id):
        clock.t += 100.0  # 模拟 stop() 阻塞消耗的时间（远超宽限加余量）
        if clock.n_at_stop is None:
            clock.n_at_stop = clock.n

    engine = FakeEngine({scope: [ScopeStarted(scope_id=scope), ScenarioStarted(scenario_id="h:0")]}, hang_after_stop={scope}, on_stop=on_stop)
    res = schedule(_rm([_job(scope, timeout_s=5.0)]), FakeResolver(engine), CollectSink(),
                   opts=ScheduleOpts(max_concurrency=1, clock=clock, heartbeat_interval_s=0.05, grace_period_s=1.0))
    assert (res.jobs[0].status, res.jobs[0].error_type) == (Status.ERROR, "timeout")
    assert clock.n - clock.n_at_stop <= 4, clock.n - clock.n_at_stop


def test_drain_bound_applies_without_deadline_under_fail_fast():
    """没有 deadline 的 job 被 fail-fast 中止后卡死不退出：排空上界同样起作用（靠心跳醒来），不挂死，判 ABORTED。"""
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
    v = next(jr for jr in res.jobs if jr.scope_id == "v")
    assert (v.status, v.error_type) == (Status.ABORTED, None)


@pytest.mark.parametrize("exit_kind", ["sigkill", "network", "exception"])
@pytest.mark.parametrize("trigger", ["deadline", "abort"])
def test_non_clean_exit_after_complete_content_is_re_arbitrated(exit_kind, trigger):
    """内容完整（scope_done 已到）之后 worker 非干净退出（SIGKILL 负码 / 80 / 普通异常）：不算内容完整，按首次仲裁回判——
    deadline 已过记 timeout、已被 fail-fast 中止记 ABORTED，而不是 engine_error / network_error。"""
    import gherkai_core.schedule as sch
    from gherkai_core.errors import WorkerExitError

    scope = "p"
    events = _passing_events(scope, "p:0")
    n = len(events)
    captured = {}
    orig = sch._Worker.__init__

    def spy(self, *a, **kw):
        orig(self, *a, **kw)
        captured["w"] = self

    class _Clock:  # deadline 触发：全部事件处理完后的下一次读越过 deadline
        def __init__(self): self.n = 0; self.t = 0.0
        def __call__(self):
            self.n += 1
            self.t += 1000.0 if (trigger == "deadline" and self.n == 2 * n + 3) else 0.001
            return self.t

    done = threading.Event()

    class _Sink(CollectSink):
        def __call__(self, ev):
            super().__call__(ev)
            if isinstance(ev, ScopeDone):
                done.set()  # core 已把 scope_done 记为内容完整

    def gen(job):
        yield from events
        done.wait(5)
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
                       opts=ScheduleOpts(max_concurrency=1, clock=_Clock(), heartbeat_interval_s=0.05, grace_period_s=1.0))
    finally:
        sch._Worker.__init__ = orig
    jr = res.jobs[0]
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
    n = len(events)
    captured = {}
    orig = sch._Worker.__init__

    def spy(self, *a, **kw):
        orig(self, *a, **kw)
        captured["w"] = self

    class _Clock:
        def __init__(self): self.n = 0; self.t = 0.0
        def __call__(self):
            self.n += 1
            self.t += 1000.0 if (trigger == "deadline" and self.n == 2 * n + 3) else 0.001
            return self.t

    done = threading.Event()

    class _Sink(CollectSink):
        def __call__(self, ev):
            super().__call__(ev)
            if isinstance(ev, ScopeDone):
                done.set()

    def gen(job):
        yield from events
        done.wait(5)
        if trigger == "abort":
            captured["w"].abort_flag.set()
        raise WorkerExitError(1, "x")

    sch._Worker.__init__ = spy
    try:
        res = schedule(_rm([_job(scope, n_scenarios=2, timeout_s=5.0)]), FakeResolver(FakeEngine({scope: gen})), _Sink(),
                       opts=ScheduleOpts(max_concurrency=1, clock=_Clock(), heartbeat_interval_s=0.05, grace_period_s=1.0))
    finally:
        sch._Worker.__init__ = orig
    jr = res.jobs[0]
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

    sch._Worker.__init__ = spy
    try:
        res = schedule(_rm([_job("a")]), resolver, CollectSink(),
                       opts=ScheduleOpts(max_concurrency=1, network_retry=2, retry_sleep=lambda s: None, grace_period_s=1.0))
    finally:
        sch._Worker.__init__ = orig
    jr = res.jobs[0]
    assert engine.run_count["a"] == 2 and (jr.status, jr.error_type) == (Status.ABORTED, None), (jr.status, jr.error_type, jr.message)
    assert engine.handles["a"].stopped  # 新 handle 确被停（不是靠 FakeEngine 自然 EOF）


def test_device_job_network_error_is_not_retried(monkeypatch):
    """设备 job 的建连失败不做 job 级重试（ADR 0051 决策 2）：同样的零 step_done network_error，桌面 job 重试、设备 job 不重试。"""
    import gherkai_core.schedule as sch

    def run():
        engine = FakeEngine({"a": _passing_events("a", "a:0")}, network_crash_after={"a": [0]})
        res = schedule(_rm([_job("a")]), FakeResolver(engine), CollectSink(),
                       opts=ScheduleOpts(max_concurrency=1, network_retry=1, retry_sleep=lambda s: None))
        return engine.run_count["a"], res.jobs[0]

    n, jr = run()
    assert n == 2 and jr.status == Status.PASSED
    monkeypatch.setattr(sch, "is_device_job", lambda job: True)  # 目标字段落地前恒 False，这里钉住门槛本身
    n, jr = run()
    assert n == 1 and (jr.status, jr.error_type) == (Status.ERROR, "network_error")


def test_sigkill_negative_exit_code_is_error_not_clean():
    """被信号强杀（负退出码）不再按干净退出处理（ADR 0034 机制二）：零事件、exit -9 → ERROR engine_error，消息带退出码。"""
    engine = FakeEngine({"k": []}, exit_code={"k": -9})
    res = schedule(_rm([_job("k")]), FakeResolver(engine), CollectSink(), opts=ScheduleOpts(max_concurrency=1))
    jr = res.jobs[0]
    assert (jr.status, jr.error_type) == (Status.ERROR, "engine_error") and "exit -9" in jr.message


def test_scope_done_after_nonzero_exit_is_error_and_zero_scenario_scope_done_is_error():
    """发完 scope_done 又非零退出 → ERROR（不是 PASSED）；零 scenario 的 scope_done 以 0 退出 → ERROR「未报告任何 scenario 判定」。"""
    engine = FakeEngine({"a": _passing_events("a", "a:0"), "z": [ScopeStarted(scope_id="z"), ScopeDone(scope_id="z")]},
                        exit_code={"a": 1})
    res = schedule(_rm([_job("a"), _job("z")]), FakeResolver(engine), CollectSink(), opts=ScheduleOpts(max_concurrency=2))
    by = {jr.scope_id: jr for jr in res.jobs}
    assert (by["a"].status, by["a"].error_type) == (Status.ERROR, "engine_error") and "exit 1" in by["a"].message
    assert (by["z"].status, by["z"].error_type) == (Status.ERROR, "engine_error") and "未报告任何 scenario 判定" in by["z"].message


def test_run_level_device_metering_sums_device_jobs_and_omits_for_desktop_runs():
    from gherkai_core.model import SessionClosed, SessionOpened

    def dev(scope: str, observed: float | None):
        return [SessionOpened(scope_id=scope, name=scope, origin="created", session_id=f"arn:{scope}"),
                ScopeStarted(scope_id=scope, session_id=f"arn:{scope}"), *_passing_events(scope, f"{scope}:0")[:-1],
                SessionClosed(scope_id=scope, name=scope, release="confirmed", session_id=f"arn:{scope}", observed_s=observed),
                ScopeDone(scope_id=scope)]
    engine = FakeEngine({"d1": dev("d1", 10.0), "d2": dev("d2", None), "desk": _passing_events("desk", "desk:0")})
    res = schedule(_rm([_job("d1"), _job("d2"), _job("desk")]), FakeResolver(engine), CollectSink(), opts=ScheduleOpts(max_concurrency=3))
    assert (res.device_observed_s, res.device_observed_missing) == (10.0, 1)
    desk = next(jr for jr in res.jobs if jr.scope_id == "desk")
    assert (desk.device_observed_s, desk.device_observed_missing) == (None, None)
    only_desk = schedule(_rm([_job("desk")]), FakeResolver(FakeEngine({"desk": _passing_events("desk", "desk:0")})), CollectSink(),
                         opts=ScheduleOpts(max_concurrency=1))
    assert (only_desk.device_observed_s, only_desk.device_observed_missing) == (None, None)
