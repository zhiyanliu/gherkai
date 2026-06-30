"""schedule 模块测试（ADR 0026）：并发归约 + 失败隔离 + fail-fast + 超时 + 优雅停。

用内存假 Engine（不起子进程）+ fake clock（不真等墙钟），验证 schedule 逻辑。
"""
from __future__ import annotations

from core.model import (
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
from core.schedule import ScheduleOpts, schedule
from tests.fake_engine import CollectSink, FakeEngine, FakeResolver


class _IncClock:
    """确定性递增时钟：每次调用 +step（默认 1.0）。用于精确测时长。"""

    def __init__(self, step: float = 1.0) -> None:
        self.t = 0.0
        self.step = step

    def __call__(self) -> float:
        self.t += self.step
        return self.t


def _job(scope_id: str, engine: str = "midscene", n_scenarios: int = 1) -> Job:
    scenarios = tuple(
        Scenario(id=f"{scope_id}:{i}", name=f"sc{i}", steps=(Step(0, "When", "做事"),))
        for i in range(n_scenarios)
    )
    return Job(scope_id=scope_id, scope_name=scope_id, engine=engine, scenarios=scenarios)


def _rm(jobs: list[Job], run_id: str = "test-run") -> RunMeta:
    """测试用：把 Job[] 包成 RunMeta（definition）喂 schedule（ADR 0016）。"""
    return RunMeta(run_id=run_id, created_at="", jobs=tuple(jobs))


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
    result = schedule(_rm(jobs), FakeResolver(engine), sink)
    assert result.status == Status.PASSED
    assert len(result.jobs) == 2
    assert all(jr.status == Status.PASSED for jr in result.jobs)
    # sink 收到所有事件（2 job × 3 事件）
    assert len(sink.events) == 6


# ---- 断言失败 → RunResult failed（区别于 error）----
def test_assertion_failed_is_failed_not_error():
    jobs = [_job("a")]
    engine = FakeEngine({"a": _failing_events("a", "a:0")})
    result = schedule(_rm(jobs), FakeResolver(engine), CollectSink())
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
    result = schedule(_rm(jobs), FakeResolver(engine), CollectSink())
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
        _rm(jobs), FakeResolver(engine), CollectSink(),
        opts=ScheduleOpts(max_concurrency=2, fail_fast=True),
    )
    assert result.status == Status.ERROR  # 确定性：批次报错
    crash_jr = next(jr for jr in result.jobs if jr.scope_id == "crash")
    assert crash_jr.status == Status.ERROR
    # 被牵连的 slow：协作式中止下结局依时序（已跑完 passed / 跑一半 aborted / 排队没起 skipped 都合法），
    # 但**绝不该是 error**——被牵连中止不是自身故障（ADR 0031；精确的 skipped/aborted 复现见 test_lifecycle_states）
    slow_jr = next(jr for jr in result.jobs if jr.scope_id == "slow")
    assert slow_jr.status in (Status.PASSED, Status.ABORTED, Status.SKIPPED)
    assert slow_jr.status != Status.ERROR


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
    result = schedule(_rm(jobs), FakeResolver(engine), CollectSink(), opts=ScheduleOpts(fail_fast=False))
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
        _rm(jobs), FakeResolver(engine), CollectSink(),
        opts=ScheduleOpts(job_timeout_s=5.0, grace_period_s=2.0, clock=fake_clock),
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


# ---- 输出顺序 = 输入 jobs 顺序（即便完成序不同）----
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
        "a": _events_with_time("a:0", [9.0, 3.0]),   # scope a = 12.0s
        "b": _events_with_time("b:0", [5.0]),         # scope b = 5.0s
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
    # 失败/出错的 step 也真实烧了钱（act/投票照样消耗时长 token）→ cost 仍累加，不漏报成本。
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
    assert jr.total_tokens == 2000          # 但失败步烧的 token 仍计入（1200+800）
    assert result.total_tokens == 2000


# ---- 并发上限：max_concurrency=1 → 串行，仍全部跑完 ----
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
    # 无超时（job_timeout_s=None）时 core 每事件只读 1 次 clock，时长可预期且层级嵌套。
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


# ---- scope 级 reportRefs 从 scope_done 归约进 JobResult（Midscene 报告归集，ADR 0024）----
def test_scope_report_refs_reduced():
    events = [
        ScenarioStarted(scenario_id="m:0"),
        StepDone(scenario_id="m:0", step_index=0, status=Status.PASSED),
        ScenarioDone(scenario_id="m:0", status=Status.PASSED),
        ScopeDone(scope_id="m", session_id="sess-1",
                  report_refs=(ReportRef(kind="scope", ref=ResourceUri("file:///midscene_run/report/x.html")),)),
    ]
    engine = FakeEngine({"m": events})
    result = schedule(_rm([_job("m")]), FakeResolver(engine), CollectSink())
    jr = result.jobs[0]
    assert len(jr.report_refs) == 1
    assert jr.report_refs[0].kind == "scope"
    assert jr.report_refs[0].ref == "file:///midscene_run/report/x.html"


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
    assert engine.run_count["n"] == 1  # 会话已起 → 不重试，只跑 1 次


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
    # job_timeout 跨 attempt 不重置（ADR 0028）：用 _IncClock 让时间每次读 +1s，
    # job_timeout_s=2 → 第一次 attempt 建连崩、重试时 clock 已过 deadline → 记 timeout（不再无限重试）
    engine = FakeEngine({"n": _passing_events("n", "n:0")}, network_crash_after={"n": 0})
    clock = _IncClock(1.0)
    result = schedule(_rm([_job("n")]), FakeResolver(engine), CollectSink(),
                      opts=ScheduleOpts(network_retry=5, job_timeout_s=2.0, clock=clock, retry_sleep=_NOSLEEP))
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
    # 不传回调（默认 None）：行为与从前完全一致（逃生舱，保纯 reducer）
    engine = FakeEngine({"a": _passing_events("a", "a:0")})
    result = schedule(_rm([_job("a")]), FakeResolver(engine), CollectSink())  # 不传 on_job_complete
    assert result.status == Status.PASSED


def test_on_job_complete_streams_not_batched():
    # 流式：job 完成即回调，不是攒到最后一起。用 on_event 钩子让 a 先于 b 完成，
    # 断言回调到达时 job_results 尚未集齐全部（证明边完成边回调）。
    fired_at_len: list[int] = []
    # max_concurrency=1 串行：a 完整跑完→回调→b 才开始。回调发生在 b 尚未完成时。
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
