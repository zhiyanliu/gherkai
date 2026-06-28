"""schedule 模块测试（ADR 0026）：并发归约 + 失败隔离 + fail-fast + 超时 + 优雅停。

用内存假 Engine（不起子进程）+ fake clock（不真等墙钟），验证 schedule 逻辑。
"""
from __future__ import annotations

from core.model import (
    Cost,
    Job,
    Scenario,
    ScenarioDone,
    ScenarioStarted,
    Status,
    Step,
    StepDone,
    Votes,
)
from core.schedule import ScheduleOpts, schedule
from tests.fake_engine import CollectSink, FakeEngine, FakeResolver


def _job(scope_id: str, engine: str = "midscene", n_scenarios: int = 1) -> Job:
    scenarios = tuple(
        Scenario(id=f"{scope_id}:{i}", name=f"sc{i}", steps=(Step(0, "When", "做事"),))
        for i in range(n_scenarios)
    )
    return Job(scope_id=scope_id, scope_name=scope_id, engine=engine, scenarios=scenarios)


def _passing_events(scope_id: str, scenario_id: str) -> list:
    return [
        ScenarioStarted(scenario_id=scenario_id),
        StepDone(scenario_id=scenario_id, step_index=0, status=Status.PASSED, votes=Votes(3, 3)),
        ScenarioDone(scenario_id=scenario_id, status=Status.PASSED),
    ]


def _failing_events(scope_id: str, scenario_id: str) -> list:
    return [
        ScenarioStarted(scenario_id=scenario_id),
        StepDone(scenario_id=scenario_id, step_index=0, status=Status.FAILED, votes=Votes(1, 3),
                 error_type="assertion_failed", message="没过多数票"),
        ScenarioDone(scenario_id=scenario_id, status=Status.FAILED),
    ]


# ---- 正常归约：全 passed → RunResult passed ----
def test_all_pass():
    jobs = [_job("a"), _job("b")]
    engine = FakeEngine({
        "a": _passing_events("a", "a:0"),
        "b": _passing_events("b", "b:0"),
    })
    sink = CollectSink()
    result = schedule(jobs, FakeResolver(engine), sink)
    assert result.status == Status.PASSED
    assert len(result.jobs) == 2
    assert all(jr.status == Status.PASSED for jr in result.jobs)
    # sink 收到所有事件（2 job × 3 事件）
    assert len(sink.events) == 6


# ---- 断言失败 → RunResult failed（区别于 error）----
def test_assertion_failed_is_failed_not_error():
    jobs = [_job("a")]
    engine = FakeEngine({"a": _failing_events("a", "a:0")})
    result = schedule(jobs, FakeResolver(engine), CollectSink())
    assert result.status == Status.FAILED
    assert result.jobs[0].status == Status.FAILED
    assert result.jobs[0].scenarios[0].status == Status.FAILED


# ---- 失败隔离（默认）：一个 job 崩(error)，其余照跑 ----
def test_failure_isolation_default():
    jobs = [_job("crash"), _job("ok")]
    engine = FakeEngine(
        behaviors={
            "crash": _passing_events("crash", "crash:0"),
            "ok": _passing_events("ok", "ok:0"),
        },
        crash_after={"crash": 1},  # crash job 在第 1 个事件后崩
    )
    result = schedule(jobs, FakeResolver(engine), CollectSink())
    # 默认隔离：crash → error，ok 照样 passed
    crash_jr = next(jr for jr in result.jobs if jr.scope_id == "crash")
    ok_jr = next(jr for jr in result.jobs if jr.scope_id == "ok")
    assert crash_jr.status == Status.ERROR
    assert crash_jr.error_type == "engine_error"
    assert ok_jr.status == Status.PASSED  # 未受牵连
    assert result.status == Status.ERROR  # 总状态：有 error


# ---- fail-fast：一个 job 崩 → 批次 ERROR（中止生效）----
# 注：fail-fast 对「在跑的其余 worker」是协作式中止，多 worker 的精确结局依赖线程时序
# （slow 可能已完成/被拦在起跑前/跑到一半被 stop——都合法），故此处只断言确定性保证：
# 批次 ERROR + crash 一定 error。stop() 的调用路径由 test_timeout_with_fake_clock 确定性覆盖。
def test_fail_fast_batch_errors():
    def long_stream(scenario_id):
        evs = [ScenarioStarted(scenario_id=scenario_id)]
        for i in range(50):
            evs.append(StepDone(scenario_id=scenario_id, step_index=i, status=Status.PASSED, votes=Votes(3, 3)))
        evs.append(ScenarioDone(scenario_id=scenario_id, status=Status.PASSED))
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
        jobs, FakeResolver(engine), CollectSink(),
        ScheduleOpts(max_concurrency=2, fail_fast=True),
    )
    assert result.status == Status.ERROR  # 确定性：批次报错
    crash_jr = next(jr for jr in result.jobs if jr.scope_id == "crash")
    assert crash_jr.status == Status.ERROR


# ---- fail-fast 关闭（默认隔离）对照：crash 崩但 slow 跑完 → ERROR 但 slow passed ----
def test_no_fail_fast_lets_others_finish():
    jobs = [_job("crash"), _job("ok")]
    engine = FakeEngine(
        behaviors={
            "crash": _passing_events("crash", "crash:0"),
            "ok": _passing_events("ok", "ok:0"),
        },
        crash_after={"crash": 0},
    )
    result = schedule(jobs, FakeResolver(engine), CollectSink(), ScheduleOpts(fail_fast=False))
    ok_jr = next(jr for jr in result.jobs if jr.scope_id == "ok")
    assert ok_jr.status == Status.PASSED  # 隔离：ok 跑完


# ---- 超时（fake clock）：job 跑太久 → stop + error:timeout ----
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

    jobs = [_job("slow")]
    engine = FakeEngine({"slow": long_events})
    result = schedule(
        jobs, FakeResolver(engine), CollectSink(),
        ScheduleOpts(job_timeout_s=5.0, grace_period_s=2.0, clock=fake_clock),
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
    result = schedule(jobs, resolver, CollectSink())
    a_jr = next(jr for jr in result.jobs if jr.scope_id == "a")
    b_jr = next(jr for jr in result.jobs if jr.scope_id == "b")
    assert a_jr.status == Status.ERROR
    assert "起 worker 失败" in a_jr.message
    assert b_jr.status == Status.PASSED  # 隔离：b 不受 a 影响


# ---- 输出顺序 = 输入 jobs 顺序（即便完成序不同）----
def test_output_order_stable():
    jobs = [_job("z"), _job("a"), _job("m")]
    engine = FakeEngine({
        "z": _passing_events("z", "z:0"),
        "a": _passing_events("a", "a:0"),
        "m": _passing_events("m", "m:0"),
    })
    result = schedule(jobs, FakeResolver(engine), CollectSink())
    assert [jr.scope_id for jr in result.jobs] == ["z", "a", "m"]


# ---- cost 汇总：step→job→run 累加 cost_usd ----
def _events_with_cost(scenario_id: str, step_costs: list[float]) -> list:
    """构造带 cost 的事件流：每个 step 一个 cost_usd。"""
    evs = [ScenarioStarted(scenario_id=scenario_id)]
    for i, c in enumerate(step_costs):
        evs.append(StepDone(
            scenario_id=scenario_id, step_index=i, status=Status.PASSED,
            cost=Cost(cost_usd=c, precision="estimated", basis="agent_time",
                      evidence={"time_worked_s": c / 4.75 * 3600}),
        ))
    evs.append(ScenarioDone(scenario_id=scenario_id, status=Status.PASSED))
    return evs


def test_cost_aggregation_step_to_job_to_run():
    # 两个 scope：a 的 step 成本 [0.01, 0.02]=0.03；b 的 [0.05]=0.05；run 总 0.08
    engine = FakeEngine({
        "a": _events_with_cost("a:0", [0.01, 0.02]),
        "b": _events_with_cost("b:0", [0.05]),
    })
    result = schedule([_job("a"), _job("b")], FakeResolver(engine), CollectSink())
    a_jr = next(jr for jr in result.jobs if jr.scope_id == "a")
    b_jr = next(jr for jr in result.jobs if jr.scope_id == "b")
    assert abs(a_jr.cost_usd - 0.03) < 1e-9   # scope 级累加
    assert abs(b_jr.cost_usd - 0.05) < 1e-9
    assert abs(result.total_cost_usd - 0.08) < 1e-9  # run 级跨 scope 累加


def test_cost_none_when_no_cost_data():
    # 无 cost 的事件流 → cost_usd / total_cost_usd 保持 None（不假装 0）
    engine = FakeEngine({"a": _passing_events("a", "a:0")})  # 这些 step 无 cost
    result = schedule([_job("a")], FakeResolver(engine), CollectSink())
    assert result.jobs[0].cost_usd is None
    assert result.total_cost_usd is None


def test_cost_partial_some_jobs_have_cost():
    # 混合：a 有 cost、b 无 → run 总 = a 的（只对有 cost 的求和）
    engine = FakeEngine({
        "a": _events_with_cost("a:0", [0.04]),
        "b": _passing_events("b", "b:0"),  # 无 cost
    })
    result = schedule([_job("a"), _job("b")], FakeResolver(engine), CollectSink())
    a_jr = next(jr for jr in result.jobs if jr.scope_id == "a")
    b_jr = next(jr for jr in result.jobs if jr.scope_id == "b")
    assert abs(a_jr.cost_usd - 0.04) < 1e-9
    assert b_jr.cost_usd is None
    assert abs(result.total_cost_usd - 0.04) < 1e-9


# ---- 并发上限：max_concurrency=1 → 串行，仍全部跑完 ----
def test_serial_concurrency_one():
    jobs = [_job(f"j{i}") for i in range(5)]
    engine = FakeEngine({f"j{i}": _passing_events(f"j{i}", f"j{i}:0") for i in range(5)})
    result = schedule(jobs, FakeResolver(engine), CollectSink(), ScheduleOpts(max_concurrency=1))
    assert result.status == Status.PASSED
    assert len(result.jobs) == 5
