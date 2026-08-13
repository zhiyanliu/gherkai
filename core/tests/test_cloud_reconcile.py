"""cloud 无状态跑批 core 侧测试（ADR 0034 P4a）：DdbEventLog + CloudLauncher + reconcile.tick(DDB 后端)。

moto mock DDB/ECS——验 DdbEventLog 读全量重放 + task_exited 独立键空间 + CloudLauncher start_scope 调对 +
reconcile.tick 用 DdbEventLog/DynamoDBRunStore/CloudLauncher 跑通（与 local SqliteEventLog/LocalRunStore 对拍语义）。
moto 抓不到的真 DDB Stream 触发/EventBridge/真 Fargate 是 P4d 真跑边界。
"""
from __future__ import annotations

import pytest

from core.adapters.event_log import DdbEventLog
from core.adapters.event_log.ddb import _EXIT_SK
from core.adapters.fargate_engine import events_pk
from core.model import Job, JobState, RunMeta, RunState, Scenario, Status, Step
from core.project import project


def _job(sid: str, timeout_s: float | None = None) -> Job:
    return Job(scope_id=sid, scope_name=sid, engine="novaact", timeout_s=timeout_s,
               scenarios=(Scenario(id=f"{sid}:1", name="s", steps=(Step(0, "Given", "x"),)),))


def _meta(*sids: str) -> RunMeta:
    return RunMeta(run_id="run-1", created_at="t0", jobs=tuple(_job(s) for s in sids))


@pytest.fixture
def events_table(aws):
    """events 表（PK=pk/SK=seq，同 conftest 的 runs 表不同）——P4 单独建，schema 见 ADR 0033/0024。"""
    import boto3
    ddb = boto3.resource("dynamodb", region_name="us-east-1")
    ddb.create_table(
        TableName="gherkai-events",
        KeySchema=[{"AttributeName": "pk", "KeyType": "HASH"},
                   {"AttributeName": "seq", "KeyType": "RANGE"}],
        AttributeDefinitions=[{"AttributeName": "pk", "AttributeType": "S"},
                              {"AttributeName": "seq", "AttributeType": "N"}],
        BillingMode="PAY_PER_REQUEST",
    )
    return ddb.Table("gherkai-events")


def _put_worker_event(table, run_id, scope_id, seq, body, emit_ts=100.0):
    """模拟 worker PutItem 一条执行事件（含 expires_at=emit_ts+7d，DdbEventLog 据此还原 emit_ts）。"""
    table.put_item(Item={"pk": events_pk(run_id, scope_id), "seq": seq, "body": body,
                         "expires_at": int(emit_ts + 7 * 24 * 3600)})


def _passed_worker_events(table, scope_id):
    _put_worker_event(table, "run-1", scope_id, 1, f'{{"type":"scope_started","scopeId":"{scope_id}","sessionId":"s"}}')
    _put_worker_event(table, "run-1", scope_id, 2, f'{{"type":"scenario_done","scenarioId":"{scope_id}:1","status":"passed"}}')
    _put_worker_event(table, "run-1", scope_id, 3, f'{{"type":"scope_done","scopeId":"{scope_id}"}}')


# ---------- DdbEventLog ----------

def test_ddb_event_log_reads_worker_events(events_table):
    _passed_worker_events(events_table, "a")
    log = DdbEventLog(events_table, "run-1", ["a"])
    recs = log.records()
    evs = [r for r in recs if r.kind == "event"]
    assert len(evs) == 3
    assert evs[0].seq == 1 and evs[0].event.type == "scope_started"
    assert evs[0].emit_ts == 100.0  # expires_at - 7d 还原


def test_ddb_record_exit_independent_keyspace(events_table):
    """task_exited 写保留高位 SK（机制一独立键空间），records() 里 kind='exit'、不占 worker seq 段。"""
    _passed_worker_events(events_table, "a")
    log = DdbEventLog(events_table, "run-1", ["a"])
    log.record_exit("a", 0)
    recs = log.records()
    exits = [r for r in recs if r.kind == "exit"]
    assert len(exits) == 1 and exits[0].exited.exit_code == 0
    # worker events 仍是 3 条（exit 在高位 SK、不混入）
    assert len([r for r in recs if r.kind == "event"]) == 3
    # 底层：exit item 的 SK 是保留高位
    got = events_table.get_item(Key={"pk": events_pk("run-1", "a"), "seq": _EXIT_SK})
    assert got["Item"]["item_type"] == "exit"


def test_ddb_records_feed_project(events_table):
    """DdbEventLog.records() → project() 推正确终态（两件都要齐 → passed）。"""
    _passed_worker_events(events_table, "a")
    log = DdbEventLog(events_table, "run-1", ["a"])
    log.record_exit("a", 0)
    state = project(_meta("a"), log.records())
    assert state.jobs["a"].status == Status.PASSED
    assert state.high_water_mark == 3


def test_ddb_multi_scope_records(events_table):
    """多 scope：逐 scope Query 拼全量（不需 GSI）。"""
    _passed_worker_events(events_table, "a")
    _passed_worker_events(events_table, "b")
    log = DdbEventLog(events_table, "run-1", ["a", "b"])
    log.record_exit("a", 0)
    log.record_exit("b", 0)
    state = project(_meta("a", "b"), log.records())
    assert state.jobs["a"].status == Status.PASSED
    assert state.jobs["b"].status == Status.PASSED


# ---------- CloudLauncher ----------

def test_cloud_launcher_calls_start_scope():
    """CloudLauncher.launch → resolver 选 engine → start_scope（fire-and-forget，不轮询）。"""
    from core.adapters.cloud_launcher import CloudLauncher

    class FakeEngine:
        def __init__(self): self.started = []
        def start_scope(self, job): self.started.append(job.scope_id); return "arn:task/x"

    eng = FakeEngine()
    CloudLauncher(lambda name: eng).launch(_job("a"))
    assert eng.started == ["a"]


class _RecorderWatch:
    def __init__(self, raise_on_arm: bool = False):
        self.armed: list[tuple] = []
        self._raise = raise_on_arm

    def arm(self, run_id, scope_id, timeout_s):
        if self._raise:
            raise RuntimeError("scheduler down")
        self.armed.append((run_id, scope_id, timeout_s))


class _FakeStartEngine:
    def __init__(self): self.started = []
    def start_scope(self, job): self.started.append(job.scope_id)


def test_cloud_launcher_arms_timeout_watch():
    """job.timeout_s 非 None → launch 后 arm(run_id, scope_id, timeout_s)（ADR 0034「job timeout」节 cloud 档）。"""
    from core.adapters.cloud_launcher import CloudLauncher

    eng, watch = _FakeStartEngine(), _RecorderWatch()
    CloudLauncher(lambda name: eng, run_id="run-1", timeout_watch=watch).launch(_job("a", timeout_s=60.0))
    assert eng.started == ["a"]
    assert watch.armed == [("run-1", "a", 60.0)]


def test_cloud_launcher_no_arm_without_timeout():
    """无预算（timeout_s=None）→ 不建 schedule（idle 零成本：不为不超时的 job 造任何云资源）。"""
    from core.adapters.cloud_launcher import CloudLauncher

    eng, watch = _FakeStartEngine(), _RecorderWatch()
    CloudLauncher(lambda name: eng, run_id="run-1", timeout_watch=watch).launch(_job("a"))
    assert eng.started == ["a"] and watch.armed == []


def test_cloud_launcher_arms_before_start_scope():
    """武装先于起 task（ADR 0034「job timeout」节 best-effort 边界）：launch 与其失败补偿双失败时，
    先建的 schedule 到点仍收敛——顺序倒过来（先 start 后 arm）双失败会失去最后兜底。"""
    from core.adapters.cloud_launcher import CloudLauncher

    order = []

    class OrderWatch:
        def arm(self, run_id, scope_id, timeout_s): order.append("arm")

    class OrderEngine:
        def start_scope(self, job): order.append("start")

    CloudLauncher(lambda name: OrderEngine(), run_id="run-1", timeout_watch=OrderWatch()).launch(
        _job("a", timeout_s=60.0))
    assert order == ["arm", "start"]


def test_cloud_launcher_launch_failure_still_armed_and_raises():
    """start_scope 抛异常：arm 已先行（schedule 在，双失败兜底生效）、异常照常冒泡（tick 靠它触发
    launch 失败补偿 record_exit(255)——不许被吞）。"""
    import pytest
    from core.adapters.cloud_launcher import CloudLauncher

    watch = _RecorderWatch()

    class BoomEngine:
        def start_scope(self, job): raise RuntimeError("RunTask placement failure")

    with pytest.raises(RuntimeError, match="placement"):
        CloudLauncher(lambda name: BoomEngine(), run_id="run-1", timeout_watch=watch).launch(
            _job("a", timeout_s=60.0))
    assert watch.armed == [("run-1", "a", 60.0)]  # 武装已完成、不随 launch 失败丢失


def test_cloud_launcher_arm_failure_does_not_block_launch():
    """武装失败 best-effort（ADR 0034「job timeout」节边界）：不抛、task 已起——降级 tick 防御扫。"""
    from core.adapters.cloud_launcher import CloudLauncher

    eng = _FakeStartEngine()
    CloudLauncher(lambda name: eng, run_id="run-1",
                  timeout_watch=_RecorderWatch(raise_on_arm=True)).launch(_job("a", timeout_s=60.0))
    assert eng.started == ["a"]  # launch 完成、异常被兜（日志降级）


# ---------- reconcile.tick 用 DDB 后端（与 local 对拍）----------

def test_tick_with_ddb_backend(events_table, ddb_run_store):
    """reconcile.tick 用 DdbEventLog + DynamoDBRunStore + CloudLauncher（fake engine）跑通：起 job → 推进 → finalize。"""
    from core.adapters.cloud_launcher import CloudLauncher
    from core.reconcile import tick

    meta = _meta("a")
    ddb_run_store.create_run(meta, RunState(
        run_id="run-1", status=Status.PENDING,
        jobs={"a": JobState("a", Status.PENDING)}, started_at="t0", high_water_mark=0))
    log = DdbEventLog(events_table, "run-1", ["a"])

    class FakeEngine:
        def __init__(self): self.started = []
        def start_scope(self, job): self.started.append(job.scope_id)
    eng = FakeEngine()
    launcher = CloudLauncher(lambda name: eng)

    # tick1：起 a（CAS claim + launch）
    tick("run-1", meta, log, ddb_run_store, launcher, 1, now_iso="t1")
    assert eng.started == ["a"]
    assert ddb_run_store.load_run_state("run-1").jobs["a"].status == Status.RUNNING

    # worker 事件 + 退出落表
    _passed_worker_events(events_table, "a")
    log.record_exit("a", 0)

    # tick2：推进到终态 + finalize
    done = tick("run-1", meta, log, ddb_run_store, launcher, 1, now_iso="t2")
    assert done is True
    assert ddb_run_store.load_run_state("run-1").status == Status.PASSED
