"""双路径对拍（ADR 0034 机制二「双路径对拍是实施护栏」）：同一组事件矩阵分别输入同步 schedule（FakeEngine）与无状态
project_full（EventRecord 加 TaskExited），逐项比较判定、归因、消息、明细、sessions[] 与计量键。含 abort 的行只经同步路径。
"""
from __future__ import annotations

from dataclasses import dataclass

import pytest

from gherkai_core.model import (
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
)
from gherkai_core.project import EventRecord, TaskExited, project_full
from gherkai_core.schedule import ScheduleOpts, schedule
from gherkai_core.serialize import job_result_to_dict
from tests.fake_engine import CollectSink, FakeEngine, FakeResolver

SCOPE = "dev"


def _job(timeout_s: float | None = None) -> Job:
    scs = tuple(Scenario(id=f"{SCOPE}:{i}", name=f"sc{i}", steps=(Step(0, "Given", "a"),)) for i in range(2))
    return Job(scope_id=SCOPE, scope_name=SCOPE, engine="midscene", scenarios=scs, timeout_s=timeout_s)


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
    timeout_s: float | None = None
    crash: bool = False     # 事件发完后 worker 以非退出码异常终止（同步路径 FakeEngine 抛 RuntimeError；无状态路径退出码 None）


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
    Row("停止后到达的 session_opened", [_opened("a"), ScopeStarted(scope_id=SCOPE, session_id="arn:a"), *_passed_scenario(0)],
        [_opened("t", origin="attempted", sid=None), _closed("t", release="unconfirmed", observed_s=None, sid=None), _closed("a")],
        1, timed_out=True, timeout_s=5.0),
    Row("接力者直接落 timed_out（退出码未知）", [_opened("a"), ScopeStarted(scope_id=SCOPE, session_id="arn:a")], [], None,
        timed_out=True, timeout_s=5.0, crash=True),
    Row("无 ARN 的未知 Create 加取消", [_opened("t", origin="attempted", sid=None), _closed("t", release="unconfirmed", observed_s=None, sid=None),
                                     ScopeDone(scope_id=SCOPE, status=Status.ERROR, error_type="acquire_timeout", message="没拿到设备")], [], 1),
]


class _Clock:
    """fake clock：事件处理到第 k 次读时钟后跳过 deadline（模拟超时处置）。"""

    def __init__(self, jump_after: int | None):
        self.t = 0.0
        self.n = 0
        self.jump_after = jump_after

    def __call__(self) -> float:
        self.n += 1
        if self.jump_after is not None and self.n == self.jump_after + 1:
            self.t += 1000.0  # 一次性越过 deadline，之后慢走（排空上界不该被假时钟立刻耗尽）
        else:
            self.t += 0.001
        return self.t


def _sync(row: Row):
    job = _job(row.timeout_s)
    engine = FakeEngine({SCOPE: list(row.events)}, tail_after_stop={SCOPE: list(row.tail)} if row.tail else {},
                        exit_code={SCOPE: row.exit_code} if row.exit_code else {})
    # 超时：让时钟在处理完全部主流事件后越过 deadline（下一次事件间检查即判超时，之后排空 tail）
    clock = _Clock(jump_after=(len(row.events) * 2 + 2) if row.timed_out else None)
    if row.timed_out:
        # 主流事件走完后再追加一条心跳可见的事件，使超时检查有机会发生：用 tail 之前的一条无害事件
        engine.behaviors[SCOPE] = list(row.events) + [ScenarioStarted(scenario_id=f"{SCOPE}:1")]
    if row.crash:
        engine.crash_after = {SCOPE: len(engine.behaviors[SCOPE])}  # 全部事件发完后抛 RuntimeError（退出码未知）
    res = schedule(RunMeta(run_id="r", created_at="", jobs=(job,)), FakeResolver(engine), CollectSink(),
                   opts=ScheduleOpts(max_concurrency=1, clock=clock, heartbeat_interval_s=0.05, grace_period_s=1.0))
    return res.jobs[0]


def _stateless(row: Row):
    job = _job(row.timeout_s)
    events = list(row.events) + ([ScenarioStarted(scenario_id=f"{SCOPE}:1")] if row.timed_out else []) + list(row.tail)
    records = [EventRecord(scope_id=SCOPE, kind="event", seq=i + 1, event=ev, emit_ts=float(i)) for i, ev in enumerate(events)]
    records.append(EventRecord(scope_id=SCOPE, kind="exit",
                               exited=TaskExited(scope_id=SCOPE, exit_code=row.exit_code, timed_out=row.timed_out)))
    res = project_full(RunMeta(run_id="r", created_at="", jobs=(job,)), records)
    return res.jobs[0]


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


def test_stateless_run_level_device_metering():
    """无状态路径的 run 级设备计量合计（ADR 0051 决策 7）：多 job 求和、缺计量数相加，与各 job 级一致；桌面 job 不计入。"""
    row = next(r for r in MATRIX if r.name == "完整成功的设备 job")
    job = _job(row.timeout_s)
    other = Job(scope_id="dev2", scope_name="dev2", engine="midscene",
                scenarios=(Scenario(id="dev2:0", name="sc0", steps=(Step(0, "Given", "a"),)),))
    desktop = Job(scope_id="web", scope_name="web", engine="novaact",
                  scenarios=(Scenario(id="web:0", name="sc0", steps=(Step(0, "Given", "a"),)),))
    other_events = [SessionOpened(scope_id="dev2", name="b", origin="created", session_id="arn:b"),
                    SessionOpened(scope_id="dev2", name="c", origin="discovered", session_id="arn:c"),
                    ScopeStarted(scope_id="dev2", session_id="arn:b"),
                    ScenarioStarted(scenario_id="dev2:0"), StepDone(scenario_id="dev2:0", step_index=0, status=Status.PASSED),
                    ScenarioDone(scenario_id="dev2:0", status=Status.PASSED),
                    SessionClosed(scope_id="dev2", name="b", release="confirmed", session_id="arn:b", observed_s=2.5),
                    SessionClosed(scope_id="dev2", name="c", release="confirmed", session_id="arn:c", observed_s=None),
                    ScopeDone(scope_id="dev2")]
    web_events = [ScopeStarted(scope_id="web"), ScenarioStarted(scenario_id="web:0"),
                  StepDone(scenario_id="web:0", step_index=0, status=Status.PASSED), ScenarioDone(scenario_id="web:0", status=Status.PASSED),
                  ScopeDone(scope_id="web")]
    records = []
    for scope, evs in ((SCOPE, row.events), ("dev2", other_events), ("web", web_events)):
        records += [EventRecord(scope_id=scope, kind="event", seq=i + 1, event=ev, emit_ts=float(i)) for i, ev in enumerate(evs)]
        records.append(EventRecord(scope_id=scope, kind="exit", exited=TaskExited(scope_id=scope, exit_code=0)))
    res = project_full(RunMeta(run_id="r", created_at="", jobs=(job, other, desktop)), records)
    by = {jr.scope_id: jr for jr in res.jobs}
    assert (by[SCOPE].device_observed_s, by[SCOPE].device_observed_missing) == (12.5, 0)
    assert (by["dev2"].device_observed_s, by["dev2"].device_observed_missing) == (2.5, 1)
    assert (by["web"].device_observed_s, by["web"].device_observed_missing) == (None, None)
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
    opened_late = by["停止后到达的 session_opened"]
    assert opened_late.error_type == "timeout" and [s.origin for s in opened_late.sessions] == ["created", "attempted"]
    assert "结果未知的创建尝试：t" in opened_late.message and "未确认停止的会话" not in opened_late.message
    relay = by["接力者直接落 timed_out（退出码未知）"]
    assert relay.error_type == "timeout" and "未确认停止的会话：a" in relay.message
    unknown = by["无 ARN 的未知 Create 加取消"]
    assert unknown.error_type == "release_failed" and "没拿到设备" in unknown.message and "结果未知的创建尝试：t" in unknown.message
    assert (unknown.device_observed_s, unknown.device_observed_missing) == (0.0, 0) and unknown.session_id is None
