"""双路径对拍（ADR 0034 机制二「双路径对拍是实施护栏」）：同一组事件矩阵分别输入同步 schedule（FakeEngine）与无状态
project_full（EventRecord 加 TaskExited，认领时刻取同步路径认领时的假墙钟），逐项比较判定、归因、消息、明细、sessions[] 与计量键，
以及两条路径交给终结函数的见过 scope_started / session_opened 两个布尔。超时行另在运行期限截断时对拍一遍（预算到点记 error 加
timeout、期限到点记 aborted，两种判定都由共用的终结函数给出）；起 worker 失败与到期的结束写两种情形另以无状态路径的推进步骤 tick 对拍，
run 级的状态与说明对拍没有记录时在内存里算出的运行态与后台写下的记录（ADR 0054 决策二后台推进条）；worker 在截止时刻
前后自己退出的几种情形，无状态路径的退出记录只带退出时刻、不带超时标志（同一条的「截止时刻与说明」）。含 abort 的行只经同步路径。矩阵以设备 job 为主，另有几行桌面 job：桌面 worker 也成对
发会话事件，配对与释放判定与设备同一条，计量两键与释放提示按目标给（ADR 0051 决策 4、7）。
未退出时的 job 态另有一组对拍：同步路径的实时落库（RunPersistence）与无状态路径的 project() 投影逐项比较 status 与 session_id。
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import pytest

from gherkai_core.model import (
    DeviceFarmRequest,
    Job,
    RunMeta,
    Scenario,
    ScenarioDone,
    ScenarioStarted,
    ScopeDone,
    ScopeStarted,
    SessionClosed,
    SessionOpened,
    Status,
    Step,
    StepDone,
    Target,
)
from gherkai_core.project import (DEADLINE_TIMEOUT_MESSAGE, DESKTOP_RELEASE_FAILED_HINT, DEVICE_RELEASE_FAILED_HINT, EventRecord,
                                  TaskExited, assemble_run_result, project, project_full)
from gherkai_core.run_status import RUN_ENDINGS, state_without_record
from gherkai_core.schedule import ScheduleOpts, schedule
from gherkai_core.serialize import job_result_to_dict
from tests.fake_engine import FAR_DEADLINE, CollectSink, FakeEngine, FakeResolver

SCOPE = "dev"


_DEVICE = dict(target=Target(device="android", ui_kind="web"), device_request=DeviceFarmRequest(project_arn="arn:p", os_version="15", billing_method="METERED"))


def _job(timeout_s: float = 7200.0, device: str = "android") -> Job:
    scs = tuple(Scenario(id=f"{SCOPE}:{i}", name=f"sc{i}", steps=(Step(0, "Given", "a"),)) for i in range(2))
    target = {} if device == "desktop" else _DEVICE
    return Job(scope_id=SCOPE, scope_name=SCOPE, engine="midscene", scenarios=scs, timeout_s=timeout_s, **target)


def _opened(name: str, origin: str = "created", sid: str | None = "auto") -> SessionOpened:
    return SessionOpened(scope_id=SCOPE, name=name, origin=origin, session_id=(f"arn:{name}" if sid == "auto" else sid))


def _closed(name: str, release: str = "confirmed", observed_s: float | None = 5.0, sid: str | None = "auto") -> SessionClosed:
    return SessionClosed(scope_id=SCOPE, name=name, release=release, session_id=(f"arn:{name}" if sid == "auto" else sid),
                         observed_s=observed_s)


def _passed_scenario(i: int) -> list:
    sc = f"{SCOPE}:{i}"
    return [ScenarioStarted(scenario_id=sc), StepDone(scenario_id=sc, step_index=0, status=Status.PASSED),
            ScenarioDone(scenario_id=sc, status=Status.PASSED)]


@dataclass
class Row:
    name: str
    events: list            # 停止前 worker 发出的事件（同步路径的主流；无状态路径的 events 段）
    tail: list              # 停止后 worker 仍发出的收尾事件（同步路径经 tail_after_stop；无状态路径追加进 events 段）
    exit_code: int | None   # worker 退出码（同步路径由 FakeEngine 抛 WorkerExitError；无状态路径写进 TaskExited）
    timed_out: bool = False  # 推进器超时处置（同步路径靠 fake clock 过 deadline；无状态路径 TaskExited.timed_out）
    timeout_s: float = 7200.0
    crash: bool = False     # 事件发完后 worker 以非退出码异常终止（同步路径 FakeEngine 抛 RuntimeError；无状态路径退出码 None）
    device: str = "android"  # job 的目标：desktop 的行是 AgentCore 浏览器会话（name 与 sessionId 都是会话 id，不带计量）


MATRIX = [
    Row("前置 scope 级 error 加退出 0", [_opened("a"), _closed("a"),
                                      ScopeDone(scope_id=SCOPE, status=Status.ERROR, error_type="acquire_timeout", message="没拿到设备")], [], 0),
    Row("scope 级 error 后非零退出", [_opened("a"), ScopeDone(scope_id=SCOPE, status=Status.ERROR, error_type="precheck_failed", message="m")], [], 1),
    Row("未确认的 session_closed", [_opened("a"), ScopeStarted(scope_id=SCOPE, session_id="arn:a"), *_passed_scenario(0), *_passed_scenario(1),
                                   _closed("a", release="unconfirmed", observed_s=None), ScopeDone(scope_id=SCOPE)], [], 1),
    Row("零 scenario 的 scope_done", [_opened("a"), ScopeStarted(scope_id=SCOPE, session_id="arn:a"), _closed("a"), ScopeDone(scope_id=SCOPE)], [], 0),
    Row("已记真实 ARN 后到达的 attempted", [_opened("a"), ScopeStarted(scope_id=SCOPE, session_id="arn:a"), *_passed_scenario(0), *_passed_scenario(1),
                                           _opened("t", origin="attempted", sid=None), _closed("a"),
                                           _closed("t", release="unconfirmed", observed_s=None, sid=None), ScopeDone(scope_id=SCOPE)], [], 1),
    Row("完整成功的设备 job", [_opened("a"), ScopeStarted(scope_id=SCOPE, session_id="arn:a"), *_passed_scenario(0), *_passed_scenario(1),
                             _closed("a", observed_s=12.5), ScopeDone(scope_id=SCOPE)], [], 0),
    Row("scenario 中途超时加停止后 session_closed", [_opened("a"), ScopeStarted(scope_id=SCOPE, session_id="arn:a"), *_passed_scenario(0)],
        [_closed("a")], 0, timed_out=True, timeout_s=5.0),
    Row("停止后到达的 session_closed 未确认", [_opened("a"), ScopeStarted(scope_id=SCOPE, session_id="arn:a"), *_passed_scenario(0)],
        [_closed("a", release="unconfirmed", observed_s=None)], 1, timed_out=True, timeout_s=5.0),
    # 先收到 scope 级 error、收尾期间才过 deadline：内容完整（干净退出）→ 判定按内容、已合成的 SKIPPED 不撤销
    Row("scope 级 error 后超时", [_opened("a"), ScopeDone(scope_id=SCOPE, status=Status.ERROR, error_type="acquire_timeout", message="没拿到设备")],
        [_closed("a")], 0, timed_out=True, timeout_s=5.0),
    # scope 级 error 后非零退出且超时：非零退出不算内容完整 → 停止原因生效记 timeout，合成明细保留
    Row("scope 级 error 后非零退出且超时", [_opened("a"), ScopeDone(scope_id=SCOPE, status=Status.ERROR, error_type="acquire_timeout", message="没拿到设备")],
        [], 1, timed_out=True, timeout_s=5.0),
    Row("停止后到达的 session_opened", [_opened("a"), ScopeStarted(scope_id=SCOPE, session_id="arn:a"), *_passed_scenario(0)],
        [_opened("t", origin="attempted", sid=None), _closed("t", release="unconfirmed", observed_s=None, sid=None), _closed("a")],
        1, timed_out=True, timeout_s=5.0),
    Row("云端超时处置补写 timed_out（退出码未知）", [_opened("a"), ScopeStarted(scope_id=SCOPE, session_id="arn:a")], [], None,
        timed_out=True, timeout_s=5.0, crash=True),
    Row("无 ARN 的未知 Create 加取消", [_opened("t", origin="attempted", sid=None), _closed("t", release="unconfirmed", observed_s=None, sid=None),
                                     ScopeDone(scope_id=SCOPE, status=Status.ERROR, error_type="acquire_timeout", message="没拿到设备")], [], 1),
    # 桌面 job（ADR 0051 决策 4）：会话事件成对、确认即 StopBrowserSession 成功；session_closed 不带 observedS
    Row("桌面会话成对且确认停止", [_opened("s-1", sid="s-1"), ScopeStarted(scope_id=SCOPE, session_id="s-1"), *_passed_scenario(0),
                                *_passed_scenario(1), _closed("s-1", observed_s=None, sid="s-1"), ScopeDone(scope_id=SCOPE)], [], 0,
        device="desktop"),
    Row("桌面会话未能确认停止", [_opened("s-1", sid="s-1"), ScopeStarted(scope_id=SCOPE, session_id="s-1"), *_passed_scenario(0),
                              *_passed_scenario(1), _closed("s-1", release="unconfirmed", observed_s=None, sid="s-1"), ScopeDone(scope_id=SCOPE)],
        [], 1, device="desktop"),
    Row("桌面建连重试耗尽且丢弃的会话均已确认", [_opened("s-1", sid="s-1"), _closed("s-1", observed_s=None, sid="s-1"),
                                           _opened("s-2", sid="s-2"), _closed("s-2", observed_s=None, sid="s-2")], [], 80, device="desktop"),
    Row("桌面建连重试耗尽且有会话未确认", [_opened("s-1", sid="s-1"), _closed("s-1", observed_s=None, sid="s-1"), _opened("s-2", sid="s-2")],
        [], 80, device="desktop"),
]


class _Clock:
    """假时间：单调时钟每读前进 1 ms，墙钟读同一份时间、不前进；sink 收到第 jump_after 条事件后一次性越过截止时刻（模拟超时处置），
    之后慢走（排空上界不该被假时钟立刻耗尽）。触发点按事件数认，不按时钟被读的次数推算。"""

    T0 = datetime(2030, 1, 1, tzinfo=timezone.utc)

    def __init__(self, jump_after: int | None):
        self.t = 0.0
        self.jump_after = jump_after
        self.seen = 0

    def __call__(self) -> float:
        self.t += 0.001
        return self.t

    def wall(self) -> datetime:
        return self.T0 + timedelta(seconds=self.t)

    def sink(self) -> CollectSink:
        clock = self

        class _Sink(CollectSink):
            def __call__(self, event) -> None:
                super().__call__(event)
                clock.seen += 1
                if clock.jump_after is not None and clock.seen == clock.jump_after:
                    clock.t += 1000.0

        return _Sink()


def _sync(row: Row, deadline_at: str = FAR_DEADLINE):
    job = _job(row.timeout_s, row.device)
    engine = FakeEngine({SCOPE: list(row.events)}, tail_after_stop={SCOPE: list(row.tail)} if row.tail else {},
                        exit_code={SCOPE: row.exit_code} if row.exit_code else {})
    # 超时：处理完全部主流事件后越过截止时刻（下一次事件间检查即判超时，之后排空 tail）
    clock = _Clock(jump_after=len(row.events) if row.timed_out else None)
    if row.timed_out:
        # 主流事件走完后再追加一条心跳可见的事件，使超时检查有机会发生：用 tail 之前的一条无害事件
        engine.behaviors[SCOPE] = list(row.events) + [ScenarioStarted(scenario_id=f"{SCOPE}:1")]
    if row.crash:
        engine.crash_after = {SCOPE: len(engine.behaviors[SCOPE])}  # 全部事件发完后抛 RuntimeError（退出码未知）
    res = schedule(RunMeta(run_id="r", created_at="", jobs=(job,), deadline_at=deadline_at), FakeResolver(engine), clock.sink(),
                   opts=ScheduleOpts(max_concurrency=1, clock=clock, wall_clock=clock.wall, heartbeat_interval_s=0.05,
                                     grace_period_s=1.0))
    return res.results[0]


def _stateless(row: Row, deadline_at: str = FAR_DEADLINE):
    job = _job(row.timeout_s, row.device)
    events = list(row.events) + ([ScenarioStarted(scenario_id=f"{SCOPE}:1")] if row.timed_out else []) + list(row.tail)
    records = [EventRecord(scope_id=SCOPE, kind="event", seq=i + 1, event=ev, emit_ts=float(i)) for i, ev in enumerate(events)]
    records.append(EventRecord(scope_id=SCOPE, kind="exit",
                               exited=TaskExited(scope_id=SCOPE, exit_code=row.exit_code, timed_out=row.timed_out)))
    # 认领时刻取同步路径认领时的假墙钟（零点起、只差几毫秒），超时时起作用的截止时刻两边由同一组值算出
    res = project_full(RunMeta(run_id="r", created_at="", jobs=(job,), deadline_at=deadline_at), records,
                       claimed_at={SCOPE: _Clock.T0})
    return res[0]


def _comparable(jr) -> dict:
    d = job_result_to_dict(jr)
    for k in ("duration_ms",):
        d.pop(k, None)
    for sr in d["scenarios"]:
        sr.pop("duration_ms", None)
        for st in sr["steps"]:
            st.pop("duration_ms", None)
    return d


@pytest.mark.parametrize("row", MATRIX, ids=[r.name for r in MATRIX])
def test_sync_and_stateless_paths_agree(row: Row):
    a, b = _comparable(_sync(row)), _comparable(_stateless(row))
    assert a == b, f"\n同步：{a}\n无状态：{b}"


@pytest.mark.parametrize("row", MATRIX, ids=[r.name for r in MATRIX])
def test_sync_and_stateless_paths_feed_finalize_the_same_flags(monkeypatch, row: Row):
    """两条路径只准备输入、判定只由终结函数给出：同一事件流交给终结函数的 saw_scope_started / saw_session_opened 也一致。
    只有 attempted 的 session_opened 两条路径都不计（ADR 0051 决策 4）；同步路径到终结时恒已退出、这两个布尔不改变判定，
    判定对拍照不出它们的分歧，故单独比较输入。"""
    import gherkai_core.project as project_mod
    import gherkai_core.schedule as schedule_mod

    seen: dict[str, list[tuple[bool, bool]]] = {"sync": [], "stateless": []}

    def spy(path: str, real):
        def wrapped(**kw):
            seen[path].append((kw["saw_scope_started"], kw["saw_session_opened"]))
            return real(**kw)
        return wrapped

    monkeypatch.setattr(schedule_mod, "finalize_job", spy("sync", schedule_mod.finalize_job))
    monkeypatch.setattr(project_mod, "finalize_job", spy("stateless", project_mod.finalize_job))
    _sync(row)
    _stateless(row)
    assert seen["sync"] and seen["stateless"]
    assert seen["sync"][-1] == seen["stateless"][-1], f"\n同步：{seen['sync']}\n无状态：{seen['stateless']}"


# 停止后的收尾在停止请求之后 20 秒才到（worker 释放会话耗时较长，但仍在 grace 之内）：排空上界取停止请求时刻加 grace 再加余量
# （ADR 0034 机制二「停止后继续有界消费完整事件流」条），同步路径照常等到收尾与 EOF，同一组事实与无状态路径的结论一致。
# grace 只取 1 秒时排空上界早于收尾到达，同步路径丢掉晚到的收尾、与无状态路径分歧：这组对照证明上面的时序确实让收尾晚到。

class _LateStopClock:
    """与 _Clock 相同地越过 deadline；发出停止请求后停在请求时刻加 20 秒：停止后的收尾事件与 EOF 都在这个时刻到达，
    落在 grace 30 秒加余量之内。"""

    WINDOW_S = 20.0
    GRACE_S = 30.0

    def __init__(self, jump_after: int):
        self.inner = _Clock(jump_after)
        self.frozen: float | None = None

    def __call__(self) -> float:
        return self.frozen if self.frozen is not None else self.inner()

    def wall(self) -> datetime:
        return _Clock.T0 + timedelta(seconds=self.frozen) if self.frozen is not None else self.inner.wall()

    def on_stop(self, scope_id: str) -> None:  # FakeEngine 的 on_stop 钩子：停止请求时刻已经记下
        if self.frozen is None:
            self.frozen = self.inner.t + self.WINDOW_S


def _sync_late_stop(row: Row, grace_s: float = _LateStopClock.GRACE_S):
    """超时行的同步路径，收尾改为停止请求后 20 秒才到（事件序列与 _sync 相同，与 _stateless 同源）。"""
    job = _job(row.timeout_s, row.device)
    clock = _LateStopClock(jump_after=len(row.events))
    main = list(row.events) + [ScenarioStarted(scenario_id=f"{SCOPE}:1")]
    engine = FakeEngine({SCOPE: main}, tail_after_stop={SCOPE: list(row.tail)},  # 发完事件后活着等停，收尾隔一会儿才到
                        exit_code={SCOPE: row.exit_code} if row.exit_code else {}, tail_delay_s=0.2, on_stop=clock.on_stop)
    if row.crash:
        engine.crash_after = {SCOPE: len(main)}
    res = schedule(RunMeta(run_id="r", created_at="", jobs=(job,), deadline_at=FAR_DEADLINE), FakeResolver(engine), clock.inner.sink(),
                   opts=ScheduleOpts(max_concurrency=1, clock=clock, wall_clock=clock.wall, heartbeat_interval_s=0.02,
                                     grace_period_s=grace_s))
    return res.results[0]


_TIMED_OUT = [r for r in MATRIX if r.timed_out]
# 内容完整（scope_done 已到、干净退出）后 deadline 才到：无状态路径按「内容完整后不再仲裁」判 PASSED
_COMPLETE_THEN_DEADLINE = Row("内容完整后 deadline 才到", [_opened("a"), ScopeStarted(scope_id=SCOPE, session_id="arn:a"),
                                                       *_passed_scenario(0), *_passed_scenario(1), _closed("a"), ScopeDone(scope_id=SCOPE)],
                              [], 0, timed_out=True, timeout_s=5.0)


@pytest.mark.parametrize("row", [*_TIMED_OUT, _COMPLETE_THEN_DEADLINE], ids=[r.name for r in [*_TIMED_OUT, _COMPLETE_THEN_DEADLINE]])
def test_paths_agree_when_stop_tail_arrives_late_within_grace(row: Row):
    a, b = _comparable(_sync_late_stop(row)), _comparable(_stateless(row))
    assert a == b, f"\n同步：{a}\n无状态：{b}"


def test_grace_shorter_than_the_late_stop_tail_makes_the_paths_diverge():
    """上一组对拍的时序确实让收尾晚到（不是即时到达、碰巧一致）：grace 取 1 秒时排空上界是停止请求后 6 秒，早于 20 秒才到的收尾，
    同步路径复现两个后果——①停止后晚到的 confirmed session_closed 被丢弃，message 多出释放提示；②内容已完整的 job 等不到 EOF，
    退出码记为未知，判成 ERROR timeout，而无状态路径判 PASSED。"""
    row = next(r for r in MATRIX if r.name == "scenario 中途超时加停止后 session_closed")
    late = _sync_late_stop(row, grace_s=1.0)
    assert DEVICE_RELEASE_FAILED_HINT in late.message and DEVICE_RELEASE_FAILED_HINT not in (_stateless(row).message or "")
    late = _sync_late_stop(_COMPLETE_THEN_DEADLINE, grace_s=1.0)
    assert (late.status, late.error_type) == (Status.ERROR, "timeout")
    assert _stateless(_COMPLETE_THEN_DEADLINE).status == Status.PASSED


# 未退出时的 job 态（ADR 0034 机制二真值表「未退出」行、ADR 0051 决策 4）：同步路径由实时落库（schedule 把每条事件原样转给
# RunPersistence.on_event）写进 RunStore，无状态路径由 project() 从同一事件段投影（无退出记录、无基线）。只有 attempted 的
# session_opened 两条路径都为 PENDING；见过非 attempted 的 session_opened 或 scope_started 才是 RUNNING。
IN_FLIGHT = [
    ("只有 attempted 的 session_opened", [_opened("t", origin="attempted", sid=None)], (Status.PENDING, None)),
    ("attempted 的尝试加未确认的 session_closed", [_opened("t", origin="attempted", sid=None),
                                               _closed("t", release="unconfirmed", observed_s=None, sid=None)], (Status.PENDING, None)),
    ("attempted 之后换台建成", [_opened("t", origin="attempted", sid=None), _opened("a")], (Status.RUNNING, "arn:a")),
    ("已记真实 ARN 后到达的 attempted", [_opened("a"), _opened("t", origin="attempted", sid=None)], (Status.RUNNING, "arn:a")),
    ("attempted 之后 scope_started", [_opened("t", origin="attempted", sid=None), ScopeStarted(scope_id=SCOPE)], (Status.RUNNING, None)),
]


@pytest.mark.parametrize("events,expected", [r[1:] for r in IN_FLIGHT], ids=[r[0] for r in IN_FLIGHT])
def test_in_flight_job_state_agrees(tmp_path, events, expected, lock_holder):
    from gherkai_core.adapters.result_store.local import LocalResultStore
    from gherkai_core.adapters.run_store.local import LocalRunStore
    from gherkai_core.persist import RunPersistence

    meta = RunMeta(run_id="r", created_at="", jobs=(_job(),), deadline_at=FAR_DEADLINE)
    run_store = LocalRunStore(tmp_path, lock_holder=lock_holder)
    persistence = RunPersistence("r", run_store, LocalResultStore(tmp_path))
    persistence.begin(meta, started_at="t0")
    for ev in events:
        persistence.on_event(ev)
    synced_state = run_store.load_run_state("r")
    synced = synced_state.jobs[SCOPE]
    records = [EventRecord(scope_id=SCOPE, kind="event", seq=i + 1, event=ev, emit_ts=float(i)) for i, ev in enumerate(events)]
    projected = project(meta, records).jobs[SCOPE]
    assert (synced.status, synced.session_id) == (projected.status, projected.session_id) == expected
    # 单 job 的 run：job 离开 pending 时实时落库的 run 级随之为 running，仍为 pending 时 run 级也是 pending
    # （ADR 0034 机制三「run 级状态只进不退」条③）
    assert synced_state.status == expected[0]


def test_crash_row_sync_side_really_exits_with_unknown_code():
    """「云端超时处置补写 timed_out」一行的同步侧输入确实是退出码未知：去掉超时处置后同一事件流按退出码未知归因（会话 a 未确认，
    归因改为 release_failed）且消息是 worker 异常（若 FakeEngine 没在事件发完后崩溃，同步侧会以退出码 0 结束、消息变成
    「没有报完这次运行的结果」，对拍只是碰巧相等）。"""
    row = next(r for r in MATRIX if r.name == "云端超时处置补写 timed_out（退出码未知）")
    plain = Row(row.name, row.events, row.tail, row.exit_code, timed_out=False, timeout_s=7200.0, crash=True, device=row.device)
    jr = _sync(plain)
    assert (jr.status, jr.error_type) == (Status.ERROR, "release_failed") and "worker 异常：" in jr.message  # a 未确认 → 归因改 release_failed，原因保留


def test_stateless_run_level_device_metering():
    """无状态路径的明细组装出的 run 级设备计量合计（ADR 0051 决策 7）：多 job 求和、缺计量数相加，与各 job 级一致；桌面 job 不计入，
    带成对会话事件的桌面 job 也不计入、自身不出现两键。"""
    row = next(r for r in MATRIX if r.name == "完整成功的设备 job")
    job = _job(row.timeout_s)
    other = Job(scope_id="dev2", scope_name="dev2", engine="midscene",
                scenarios=(Scenario(id="dev2:0", name="sc0", steps=(Step(0, "Given", "a"),)),), timeout_s=row.timeout_s, **_DEVICE)
    desktop = Job(scope_id="web", scope_name="web", engine="novaact",
                  scenarios=(Scenario(id="web:0", name="sc0", steps=(Step(0, "Given", "a"),)),), timeout_s=300.0)
    other_events = [SessionOpened(scope_id="dev2", name="b", origin="created", session_id="arn:b"),
                    SessionOpened(scope_id="dev2", name="c", origin="discovered", session_id="arn:c"),
                    ScopeStarted(scope_id="dev2", session_id="arn:b"),
                    ScenarioStarted(scenario_id="dev2:0"), StepDone(scenario_id="dev2:0", step_index=0, status=Status.PASSED),
                    ScenarioDone(scenario_id="dev2:0", status=Status.PASSED),
                    SessionClosed(scope_id="dev2", name="b", release="confirmed", session_id="arn:b", observed_s=2.5),
                    SessionClosed(scope_id="dev2", name="c", release="confirmed", session_id="arn:c", observed_s=None),
                    ScopeDone(scope_id="dev2")]
    web_events = [SessionOpened(scope_id="web", name="s-w", origin="created", session_id="s-w"),
                  ScopeStarted(scope_id="web", session_id="s-w"), ScenarioStarted(scenario_id="web:0"),
                  StepDone(scenario_id="web:0", step_index=0, status=Status.PASSED), ScenarioDone(scenario_id="web:0", status=Status.PASSED),
                  SessionClosed(scope_id="web", name="s-w", release="confirmed", session_id="s-w"), ScopeDone(scope_id="web")]
    records = []
    for scope, evs in ((SCOPE, row.events), ("dev2", other_events), ("web", web_events)):
        records += [EventRecord(scope_id=scope, kind="event", seq=i + 1, event=ev, emit_ts=float(i)) for i, ev in enumerate(evs)]
        records.append(EventRecord(scope_id=scope, kind="exit", exited=TaskExited(scope_id=scope, exit_code=0)))
    meta = RunMeta(run_id="r", created_at="", jobs=(job, other, desktop), deadline_at=FAR_DEADLINE)
    details = project_full(meta, records, claimed_at={sid: _Clock.T0 for sid in (SCOPE, "dev2", "web")})
    res = assemble_run_result(meta, state_without_record(meta, details, None, ended_at="t1"), details, duration_ms=None)
    by = {jr.scope_id: jr for jr in details}
    assert (by[SCOPE].device_observed_s, by[SCOPE].device_observed_missing) == (12.5, 0)
    assert (by["dev2"].device_observed_s, by["dev2"].device_observed_missing) == (2.5, 1)
    assert (by["web"].device_observed_s, by["web"].device_observed_missing) == (None, None)
    assert by["web"].status == Status.PASSED and [s.release for s in by["web"].sessions] == ["confirmed"]
    assert (res.device_observed_s, res.device_observed_missing) == (15.0, 1)


def test_matrix_covers_expected_verdicts():
    """矩阵各行的判定本身（不只两路一致，还要对）：按 ADR 0034 真值表。"""
    by = {r.name: _stateless(r) for r in MATRIX}
    assert (by["前置 scope 级 error 加退出 0"].status, by["前置 scope 级 error 加退出 0"].error_type) == (Status.ERROR, "acquire_timeout")
    assert [sr.status for sr in by["前置 scope 级 error 加退出 0"].scenarios] == [Status.SKIPPED, Status.SKIPPED]  # 合成明细
    assert by["scope 级 error 后非零退出"].error_type == "release_failed"  # a 没有 session_closed → U 非空
    assert by["未确认的 session_closed"].error_type == "release_failed"
    assert by["零 scenario 的 scope_done"].error_type == "engine_error" and "未报告任何 scenario" in by["零 scenario 的 scope_done"].message
    att = by["已记真实 ARN 后到达的 attempted"]
    assert att.session_id == "arn:a" and [s.origin for s in att.sessions] == ["created", "attempted"]
    assert (att.device_observed_s, att.device_observed_missing) == (5.0, 0) and att.error_type == "release_failed"
    ok = by["完整成功的设备 job"]
    assert ok.status == Status.PASSED and (ok.device_observed_s, ok.device_observed_missing) == (12.5, 0)
    mid = by["scenario 中途超时加停止后 session_closed"]
    assert mid.error_type == "timeout" and mid.sessions[0].release == "confirmed"
    late = by["停止后到达的 session_closed 未确认"]
    assert late.error_type == "timeout" and "未确认停止的会话：a" in late.message  # 超时优先，但 U 非空照样提示
    pre = by["scope 级 error 后超时"]  # 内容完整后不再仲裁：判定按 worker 报的 scope 级 error，合成明细保留
    assert (pre.status, pre.error_type, pre.message) == (Status.ERROR, "acquire_timeout", "没拿到设备")
    assert [sr.status for sr in pre.scenarios] == [Status.SKIPPED, Status.SKIPPED] and pre.sessions[0].release == "confirmed"
    nz = by["scope 级 error 后非零退出且超时"]
    assert nz.error_type == "timeout" and [sr.status for sr in nz.scenarios] == [Status.SKIPPED, Status.SKIPPED]
    assert "未确认停止的会话：a" in nz.message
    opened_late = by["停止后到达的 session_opened"]
    assert opened_late.error_type == "timeout" and [s.origin for s in opened_late.sessions] == ["created", "attempted"]
    assert "结果未知的创建尝试：t" in opened_late.message and "未确认停止的会话" not in opened_late.message
    supplemented = by["云端超时处置补写 timed_out（退出码未知）"]
    assert supplemented.error_type == "timeout" and "未确认停止的会话：a" in supplemented.message
    unknown = by["无 ARN 的未知 Create 加取消"]
    assert unknown.error_type == "release_failed" and "没拿到设备" in unknown.message and "结果未知的创建尝试：t" in unknown.message
    assert (unknown.device_observed_s, unknown.device_observed_missing) == (0.0, 0) and unknown.session_id is None
    assert DEVICE_RELEASE_FAILED_HINT in unknown.message
    # 桌面行：判定与设备同一条，计量两键只按目标给、释放提示不提设备控制台（ADR 0051 决策 4、7）
    desk = by["桌面会话成对且确认停止"]
    assert (desk.status, desk.error_type, desk.message, desk.session_id) == (Status.PASSED, None, None, "s-1")
    assert [(s.name, s.origin, s.release) for s in desk.sessions] == [("s-1", "created", "confirmed")]
    assert (desk.device_observed_s, desk.device_observed_missing) == (None, None)
    lost = by["桌面会话未能确认停止"]
    assert (lost.status, lost.error_type) == (Status.ERROR, "release_failed") and (lost.device_observed_s, lost.device_observed_missing) == (None, None)
    assert DESKTOP_RELEASE_FAILED_HINT in lost.message and "设备控制台" not in lost.message and "未确认停止的会话：s-1" in lost.message
    net = by["桌面建连重试耗尽且丢弃的会话均已确认"]
    assert (net.status, net.error_type) == (Status.ERROR, "network_error") and "未能确认停止" not in net.message
    assert [s.release for s in net.sessions] == ["confirmed", "confirmed"] and net.device_observed_s is None
    net_lost = by["桌面建连重试耗尽且有会话未确认"]
    assert (net_lost.status, net_lost.error_type) == (Status.ERROR, "release_failed") and "退出码 80" in net_lost.message
    assert DESKTOP_RELEASE_FAILED_HINT in net_lost.message and "未确认停止的会话：s-2" in net_lost.message


# 前台路径的两种中止（ADR 0054 决策二）：被期限截断的 job、发现 run 已被别处结束而被中止的 job，都记 aborted，判定由前台与后台共用的
# 终结函数给出。同步路径交给终结函数的是哪个截止时刻起作用（timeout_cause）、哪个中止来源（abort_cause），判定原样取它的返回。

class _EndedRecord:
    """ScheduleOpts.record 的替身：认领都成立、run 级未结束；停手信号在收到第一条事件之后成立（模拟写 job 状态时得知 run 级已结束）。"""

    def __init__(self):
        import threading
        self.ended = threading.Event()

    def claim(self, scope_id, claimed_at):
        return True

    def still_open(self):
        return True

    def ended_elsewhere(self):
        return self.ended.is_set()


@pytest.mark.parametrize("cause", ["deadline", "ended-elsewhere"])
def test_sync_path_new_verdicts_come_from_the_shared_finalize(monkeypatch, cause):
    import gherkai_core.project as project_mod
    import gherkai_core.schedule as schedule_mod
    from gherkai_core.project import DEADLINE_TIMEOUT_MESSAGE, ENDED_ELSEWHERE_ABORT_MESSAGE

    row = next(r for r in MATRIX if r.name == "scenario 中途超时加停止后 session_closed")
    calls: list[tuple[dict, object]] = []

    def spy(**kw):
        term = project_mod.finalize_job(**kw)
        calls.append((kw, term))
        return term

    monkeypatch.setattr(schedule_mod, "finalize_job", spy)
    job = _job(7200.0, row.device)  # 预算远长于期限：deadline 情形起作用的是期限
    clock = _Clock(jump_after=len(row.events) if cause == "deadline" else None)
    record = _EndedRecord()
    sink = clock.sink()
    if cause == "ended-elsewhere":
        inner = sink

        class _Sink(CollectSink):
            def __call__(self, event) -> None:
                inner(event)
                record.ended.set()

        sink = _Sink()
    engine = FakeEngine({SCOPE: list(row.events) + [ScenarioStarted(scenario_id=f"{SCOPE}:1")]},
                        tail_after_stop={SCOPE: list(row.tail)})
    meta = RunMeta(run_id="r", created_at="", jobs=(job,), deadline_at=(_Clock.T0 + timedelta(seconds=100)).isoformat())
    res = schedule(meta, FakeResolver(engine), sink,
                   opts=ScheduleOpts(max_concurrency=1, clock=clock, wall_clock=clock.wall, heartbeat_interval_s=0.02,
                                     grace_period_s=1.0, record=record, interrupt_poll_s=0.02))
    jr = res.results[0]
    kw, term = calls[-1]
    assert (jr.status, jr.error_type, jr.message) == (term.status, term.error_type, term.message)
    again = project_mod.finalize_job(**kw)  # 同一组输入直接调用共用的终结函数：同一结论
    assert (again.status, again.error_type, again.message) == (jr.status, jr.error_type, jr.message)
    if cause == "deadline":
        assert (kw["stop_reason"], kw["timeout_cause"]) == ("timeout", "deadline")
        assert (jr.status, jr.error_type, jr.message) == (Status.ABORTED, None, DEADLINE_TIMEOUT_MESSAGE)
    else:
        assert (kw["stop_reason"], kw["abort_cause"]) == ("abort", "ended-elsewhere")
        assert (jr.status, jr.error_type, jr.message) == (Status.ABORTED, None, ENDED_ELSEWHERE_ABORT_MESSAGE)
    assert [s.release for s in jr.sessions] == ["confirmed"]  # 停止后到达的收尾照常归约


# ---------- 后台路径与前台同一结论（ADR 0054 决策二后台推进条、实测项 4）----------

_NEAR = (_Clock.T0 + timedelta(seconds=100)).isoformat()  # 运行期限：同步路径的假墙钟越过截止时刻时它已过


@pytest.mark.parametrize("row", _TIMED_OUT, ids=[r.name for r in _TIMED_OUT])
def test_paths_agree_when_the_run_deadline_cuts_the_job(row: Row):
    """被运行期限截断的 job（预算远长于期限）：同步路径在认领时算出起作用的是期限，无状态路径由认领时刻、预算与期限重算出同一个结论，
    两边的判定、归因与说明逐项相同；被截断而内容不完整的 job 记 aborted、没有归因，说明是期限那一句；内容完整的不改判。"""
    long = Row(row.name, row.events, row.tail, row.exit_code, timed_out=True, timeout_s=7200.0, crash=row.crash, device=row.device)
    a, b = _comparable(_sync(long, _NEAR)), _comparable(_stateless(long, _NEAR))
    assert a == b, f"\n同步：{a}\n无状态：{b}"
    assert b["error_type"] != "timeout"  # 期限到点不是超时
    if row.name == "scope 级 error 后超时":
        assert (b["status"], b["error_type"]) == ("error", "acquire_timeout")  # 内容完整：判定按 worker 报的 scope 级 error
    else:
        assert (b["status"], b["error_type"]) == ("aborted", None) and b["message"].startswith(DEADLINE_TIMEOUT_MESSAGE)


# worker 在截止时刻前后自己退出（ADR 0054 决策二后台推进条「截止时刻与说明」、实测项 11）：同步路径在终结之前对内容不完整的 job
# 再查一次截止时刻；无状态路径的退出记录与本机启动器、云端观察者写的同一形态——不带超时标志、只带退出时刻，由投影按它是否晚于
# 截止时刻判断。预算 5 秒；同步路径的假墙钟在最后一条事件之后越过截止时刻（after_cutoff）或一直停在它之前。同步路径不包心跳：最后
# 一条事件之后紧接着就是 worker 的退出，中间没有事件间检查，也就不会先发出停止请求。

@dataclass
class SelfExit:
    name: str
    events: list
    exit_code: int
    after_cutoff: bool
    expected: tuple  # (status, error_type)


_DESKTOP_RUN = [_opened("s-1", sid="s-1"), ScopeStarted(scope_id=SCOPE, session_id="s-1"), *_passed_scenario(0)]
SELF_EXITS = [
    SelfExit("截止时刻之后以非零退出码自行退出", [*_DESKTOP_RUN, _closed("s-1", observed_s=None, sid="s-1")], 3, True,
             (Status.ERROR, "timeout")),
    SelfExit("截止时刻之前以非零退出码自行退出", [*_DESKTOP_RUN, _closed("s-1", observed_s=None, sid="s-1")], 3, False,
             (Status.ERROR, "engine_error")),
    SelfExit("截止时刻之后以非零退出码自行退出且会话未确认", list(_DESKTOP_RUN), 3, True, (Status.ERROR, "timeout")),
    SelfExit("内容完整而退出时刻晚于截止时刻", [*_DESKTOP_RUN, *_passed_scenario(1), _closed("s-1", observed_s=None, sid="s-1"),
                                            ScopeDone(scope_id=SCOPE)], 0, True, (Status.PASSED, None)),
]


def _sync_self_exit(row: SelfExit):
    job = _job(5.0, "desktop")
    engine = FakeEngine({SCOPE: list(row.events)}, exit_code={SCOPE: row.exit_code} if row.exit_code else {})
    clock = _Clock(jump_after=len(row.events) if row.after_cutoff else None)
    res = schedule(RunMeta(run_id="r", created_at="", jobs=(job,), deadline_at=FAR_DEADLINE), FakeResolver(engine), clock.sink(),
                   opts=ScheduleOpts(max_concurrency=1, clock=clock, wall_clock=clock.wall, heartbeat_interval_s=0,
                                     grace_period_s=1.0))
    assert not engine.handles[SCOPE].stopped  # worker 是自己退出的：同步路径没有发出过停止请求
    return res.results[0]


def _stateless_self_exit(row: SelfExit):
    job = _job(5.0, "desktop")
    records = [EventRecord(scope_id=SCOPE, kind="event", seq=i + 1, event=ev, emit_ts=float(i)) for i, ev in enumerate(row.events)]
    exited_at = _Clock.T0 + timedelta(seconds=1000.0 if row.after_cutoff else 1.0)
    records.append(EventRecord(scope_id=SCOPE, kind="exit",
                               exited=TaskExited(scope_id=SCOPE, exit_code=row.exit_code, exited_at=exited_at)))
    res = project_full(RunMeta(run_id="r", created_at="", jobs=(job,), deadline_at=FAR_DEADLINE), records,
                       claimed_at={SCOPE: _Clock.T0})
    return res[0]


@pytest.mark.parametrize("row", SELF_EXITS, ids=[r.name for r in SELF_EXITS])
def test_paths_agree_when_the_worker_exits_on_its_own_around_its_cutoff(row: SelfExit):
    """worker 在截止时刻之后、停止请求发出之前自己以非零退出码退出：两条路径都记超时（说明是预算那一句）；在截止时刻之前这样退出时
    都按退出码归因；内容完整的不因退出时刻晚于截止时刻而改判。判定、归因、说明与明细逐项相同。"""
    a, b = _comparable(_sync_self_exit(row)), _comparable(_stateless_self_exit(row))
    assert a == b, f"\n同步：{a}\n无状态：{b}"
    assert (Status(b["status"]), b["error_type"]) == row.expected
    if row.expected[1] == "timeout":
        assert b["message"].startswith("job 超时（预算 5s，已中止）")


def _boom_sync(deadline_at: str, timeout_s: float, *, slow: bool):
    """同步路径起 worker 失败；slow 时起 worker 的调用拖过截止时刻才失败。"""
    job = _job(timeout_s, "desktop")
    clock = _Clock(jump_after=None)

    class Boom:
        def run_scope(self, job):
            if slow:
                clock.t += 1000.0
            raise OSError("spawn 失败")

    meta = RunMeta(run_id="r", created_at="", jobs=(job,), deadline_at=deadline_at)
    return schedule(meta, FakeResolver(Boom()), CollectSink(),
                    opts=ScheduleOpts(max_concurrency=1, clock=clock, wall_clock=clock.wall, grace_period_s=1.0))


def _boom_stateless(tmp_path, deadline_at: str, timeout_s: float, *, slow: bool, lock_holder):
    """无状态路径的推进步骤 tick 起 job 失败（launch 抛出），下一轮以终态写记下这个 job，run 随之成为终态；slow 时启动调用拖过截止时刻
    才失败。返回按运行态点名读回的判定明细（与报告同一种读法）、补写的退出记录与 run 成为终态之后的运行态。"""
    from gherkai_core.adapters.event_log import SqliteEventLog
    from gherkai_core.adapters.result_store.local import LocalResultStore
    from gherkai_core.adapters.run_store.local import LocalRunStore
    from gherkai_core.model import JobState, RunState
    from gherkai_core.named_details import load_named_details
    from gherkai_core.reconcile import TickOutcome, tick

    job = _job(timeout_s, "desktop")
    meta = RunMeta(run_id="r", created_at="", jobs=(job,), deadline_at=deadline_at)
    store, log = LocalRunStore(tmp_path, lock_holder=lock_holder), SqliteEventLog(tmp_path / "e.db")
    store.create_run(meta, RunState(run_id="r", status=Status.PENDING, jobs={SCOPE: JobState(SCOPE, Status.PENDING)},
                                    started_at="t0", high_water_mark=0))
    now = {"t": 0.0}

    class Boom:
        def launch(self, job, *, cutoff_at):
            if slow:
                now["t"] += 1000.0
            raise OSError("spawn 失败")

    def clock():
        return _Clock.T0 + timedelta(seconds=now["t"])

    results = LocalResultStore(tmp_path)
    assert tick("r", meta, log, store, Boom(), 1, clock=clock, result_store=results) is TickOutcome.CONTINUE
    assert tick("r", meta, log, store, Boom(), 1, clock=clock, result_store=results) is TickOutcome.COMMITTED
    [exit_rec] = [r.exited for r in log.records() if r.kind == "exit"]
    recorded = store.load_run_state("r")
    return list(load_named_details("r", recorded.jobs.values(), results).values()), exit_rec, recorded


@pytest.mark.parametrize("deadline_at, timeout_s, slow, status, message", [
    (FAR_DEADLINE, 5.0, False, Status.ERROR, "起 worker 失败：spawn 失败"),
    (FAR_DEADLINE, 5.0, True, Status.ERROR, "job 超时（预算 5s，已中止）"),
    (_NEAR, 5.0, True, Status.ERROR, "job 超时（预算 5s，已中止）"),
    (_NEAR, 7200.0, True, Status.ABORTED, DEADLINE_TIMEOUT_MESSAGE),
], ids=["起不来", "拖过预算才失败", "拖过预算才失败且期限更晚", "拖过期限才失败"])
def test_launch_failure_agrees_between_the_foreground_and_the_advancer(tmp_path, deadline_at, timeout_s, slow, status, message, lock_holder):
    """起 worker 失败的 job（ADR 0054 决策二后台推进条「时刻」）：推进步骤补写的退出记录与前台交给终结函数的输入相同——退出码未知、带
    启动失败的原因。补写只记失败的那一刻作退出时刻、不带超时标志，投影按它是否晚于截止时刻判断，与前台起 worker 失败的分支是
    同一个判断——两条路径的判定、归因与说明逐项相同；拖过期限才失败的记 aborted。run 级两边都按取法由这个 job 的终态算出：前台没有
    记录时在内存里算出，后台是记下终态的写写下的记录，都没有 run 级说明。"""
    sync = _boom_sync(deadline_at, timeout_s, slow=slow)
    stateless, exit_rec, recorded = _boom_stateless(tmp_path, deadline_at, timeout_s, slow=slow, lock_holder=lock_holder)
    assert (exit_rec.exit_code, exit_rec.timed_out) == (None, False)
    assert exit_rec.exited_at == _Clock.T0 + timedelta(seconds=1000.0 if slow else 0.0)
    a, b = _comparable(sync.results[0]), _comparable(stateless[0])
    assert a == b, f"\n同步：{a}\n无状态：{b}"
    assert (b["status"], b["message"]) == (status.value, message)
    foreground = state_without_record(sync.run_meta, sync.results, sync.stopped_by, ended_at="t1")
    assert (foreground.status, foreground.message) == (recorded.status, recorded.message) == (status, None)


def test_expiry_agrees_between_the_foreground_and_the_advancer(tmp_path, lock_holder):
    """到期：a 结束之后已过停止启动的时刻，b 还没有启动。前台没有记录时组装出的结果（`persist.result_without_record`）与后台推进
    步骤写下的记录一致：a passed、b 由执行方自己到期这条来路的结束写记 skipped 并带说明，run 为 aborted、带 run 级说明；判定明细只有
    a 的，b 没有：后台记录里只有 a 被点名，按点名读回的也只有 a（ADR 0054 决策二第 3 条、实测项 4）。"""
    from gherkai_core.adapters.event_log import SqliteEventLog
    from gherkai_core.adapters.result_store.local import LocalResultStore
    from gherkai_core.adapters.run_store.local import LocalRunStore
    from gherkai_core.model import JobState, RunState
    from gherkai_core.named_details import load_named_details
    from gherkai_core.persist import result_without_record
    from gherkai_core.reconcile import TickOutcome, tick

    def job(sid):
        return Job(scope_id=sid, scope_name=sid, engine="novaact", timeout_s=7200.0,
                   scenarios=(Scenario(id=f"{sid}:0", name="sc0", steps=(Step(0, "Given", "a"),)),))

    meta = RunMeta(run_id="r", created_at="", jobs=(job("a"), job("b")), deadline_at=_NEAR)
    a_events = [ScopeStarted(scope_id="a", session_id="s"), ScenarioDone(scenario_id="a:0", status=Status.PASSED),
                ScopeDone(scope_id="a")]
    clock = _Clock(jump_after=len(a_events))  # a 的最后一条事件之后越过停止启动的时刻
    sync = schedule(meta, FakeResolver(FakeEngine({"a": a_events})), clock.sink(),
                    opts=ScheduleOpts(max_concurrency=1, clock=clock, wall_clock=clock.wall, heartbeat_interval_s=0.02,
                                      grace_period_s=1.0))

    store, log = LocalRunStore(tmp_path, lock_holder=lock_holder), SqliteEventLog(tmp_path / "e.db")
    store.create_run(meta, RunState(run_id="r", status=Status.PENDING, high_water_mark=0, started_at="t0",
                                    jobs={s: JobState(s, Status.PENDING) for s in ("a", "b")}))
    now = {"t": 0.0}

    class Launcher:
        def launch(self, job, *, cutoff_at):
            pass

    def wall():
        return _Clock.T0 + timedelta(seconds=now["t"])

    results = LocalResultStore(tmp_path)
    tick("r", meta, log, store, Launcher(), 1, clock=wall, result_store=results)  # 认领并启动 a
    log.append_event("a", 1, '{"type":"scope_started","scopeId":"a","sessionId":"s"}', 1.0)
    log.append_event("a", 2, '{"type":"scenario_done","scenarioId":"a:0","status":"passed"}', 2.0)
    log.append_event("a", 3, '{"type":"scope_done","scopeId":"a"}', 3.0)
    log.record_exit("a", 0)
    now["t"] = 1000.0
    done = tick("r", meta, log, store, Launcher(), 1, clock=wall, result_store=results)

    assert done is TickOutcome.COMMITTED
    assert sync.stopped_by == "deadline"
    foreground = result_without_record(sync, ended_at="t1")
    recorded = store.load_run_state("r")
    ending = RUN_ENDINGS["deadline"]
    assert (foreground.status, foreground.message) == (recorded.status, recorded.message) == (Status.ABORTED, ending.run_message)
    assert [(o.scope_id, o.status, o.state.message) for o in foreground.jobs] \
        == [(sid, js.status, js.message) for sid, js in recorded.jobs.items()] \
        == [("a", Status.PASSED, None), ("b", Status.SKIPPED, ending.skipped_message)]
    named = load_named_details("r", recorded.jobs.values(), results)
    assert [jr.scope_id for jr in foreground.details] == list(named) == ["a"]
