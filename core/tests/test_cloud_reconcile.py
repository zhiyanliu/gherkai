"""cloud 无状态批量运行 core 侧测试（ADR 0034 云端后端）：DdbEventLog + CloudLauncher + reconcile.tick(DDB 后端)。

moto mock DDB/ECS——验 DdbEventLog 读全量重放 + task_exited 独立键空间 + CloudLauncher start_scope 调对 +
reconcile.tick 用 DdbEventLog/DynamoDBRunStore/CloudLauncher 走通（与 local SqliteEventLog/LocalRunStore 对拍语义）。
moto 抓不到的真 DDB Stream 触发 / EventBridge / 真 Fargate 是真实运行边界。
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from gherkai_core.adapters.event_log import DdbEventLog
from gherkai_core.adapters.fargate_engine import EXIT_SK, events_pk
from gherkai_core.model import Job, JobState, RunMeta, RunState, Scenario, Status, Step
from gherkai_core.project import project
from gherkai_core.serialize import instant_to_iso
from tests.conftest import jobs_objects_for
from tests.fake_engine import FAR_DEADLINE


def _job(sid: str, timeout_s: float = 7200.0) -> Job:
    return Job(scope_id=sid, scope_name=sid, engine="novaact", timeout_s=timeout_s,
               scenarios=(Scenario(id=f"{sid}:1", name="s", steps=(Step(0, "Given", "x"),)),))


def _meta(*sids: str, deadline_at: str = FAR_DEADLINE) -> RunMeta:
    return RunMeta(run_id="run-1", created_at="t0", jobs=tuple(_job(s) for s in sids), deadline_at=deadline_at)


@pytest.fixture
def events_table(aws):
    """events 表（PK=pk/SK=seq，同 conftest 的 runs 表不同）——云端后端测试单独建，schema 见 ADR 0033/0024。"""
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
    got = events_table.get_item(Key={"pk": events_pk("run-1", "a"), "seq": EXIT_SK})
    assert got["Item"]["item_type"] == "exit"


def test_ddb_has_exit_single_scope(events_table):
    """has_exit 只看本 scope 的退出记录（超时处置的「已在即让路」判据，不重放整 run）：有退出记录才 True，
    只有 worker 事件的 scope / 同 run 别的 scope 都 False。"""
    _passed_worker_events(events_table, "a")
    log = DdbEventLog(events_table, "run-1", ["a", "b"])
    assert log.has_exit("a") is False  # 有 worker 事件但无退出记录
    log.record_exit("a", 0)
    assert log.has_exit("a") is True
    assert log.has_exit("b") is False  # 同 run 别的 scope 不串扰


def test_ddb_record_exit_exited_at_roundtrip_and_omitted_when_absent(events_table):
    """退出时刻随退出记录落库（UTC 的 ISO 串）、读回为同一时刻；没有值时不写这个属性（与 timed_out、reason 同样省略）。"""
    from gherkai_core.adapters.fargate_engine import EXIT_SK

    log = DdbEventLog(events_table, "run-1", ["a", "b"])
    at = datetime(2026, 11, 8, 18, 5, 1, 473000, tzinfo=timezone(timedelta(hours=8)))
    log.record_exit("a", 3, exited_at=at)
    log.record_exit("b", 0)
    exits = {r.scope_id: r.exited for r in log.records() if r.kind == "exit"}
    assert exits["a"].exited_at == at and exits["b"].exited_at is None
    item_a = events_table.get_item(Key={"pk": events_pk("run-1", "a"), "seq": EXIT_SK})["Item"]
    item_b = events_table.get_item(Key={"pk": events_pk("run-1", "b"), "seq": EXIT_SK})["Item"]
    assert item_a["exited_at"] == "2026-11-08T10:05:01.473000+00:00"
    assert "exited_at" not in item_b and "timed_out" not in item_b and "reason" not in item_b


def test_ddb_record_timed_out_if_absent_writes_only_when_there_is_no_exit_record(events_table):
    """补写判为超时的未知退出（对位 SqliteEventLog）：还没有退出记录时写成（退出码未知、带超时标志、不带退出时刻），返回 True；已有
    退出记录时条件写不成立、不报错，返回 False，原记录原样保留。之后到达的真实退出照旧经 record_exit 覆盖补写的那一条。"""
    log = DdbEventLog(events_table, "run-1", ["seen", "lost"])
    at = datetime(2026, 11, 8, 10, 5, 1, tzinfo=timezone.utc)
    log.record_exit("seen", 3, exited_at=at)
    assert log.record_timed_out_if_absent("seen") is False
    assert log.record_timed_out_if_absent("lost") is True
    assert log.record_timed_out_if_absent("lost") is False
    exits = {r.scope_id: r.exited for r in log.records() if r.kind == "exit"}
    assert (exits["seen"].exit_code, exits["seen"].timed_out, exits["seen"].exited_at) == (3, False, at)
    assert (exits["lost"].exit_code, exits["lost"].timed_out, exits["lost"].exited_at) == (None, True, None)
    log.record_exit("lost", 0, exited_at=at)
    exits = {r.scope_id: r.exited for r in log.records() if r.kind == "exit"}
    assert (exits["lost"].exit_code, exits["lost"].timed_out, exits["lost"].exited_at) == (0, False, at)


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


def test_ddb_records_read_only_the_listed_scopes(events_table):
    """按 PK=run_id#scope_id 查询即分流（ADR 0024「消费天然定向 + 天然幂等」条）：同一张表里同 run 别的 scope 的事件不混入，
    每条 record 的 scope_id 与事件自带的 scopeId 一致；重读一遍结果不变（Query 非破坏性）。"""
    _put_worker_event(events_table, "run-1", "browse", 1, '{"type":"scope_started","scopeId":"browse"}')
    _put_worker_event(events_table, "run-1", "browse", 2, '{"type":"scope_done","scopeId":"browse"}')
    _put_worker_event(events_table, "run-1", "search", 1, '{"type":"scope_started","scopeId":"search"}')
    _put_worker_event(events_table, "run-1", "search", 2, '{"type":"scope_done","scopeId":"search"}')
    log = DdbEventLog(events_table, "run-1", ["browse"])
    recs = log.records()
    assert [(r.scope_id, r.event.scope_id) for r in recs] == [("browse", "browse"), ("browse", "browse")]
    assert log.records() == recs


def test_ddb_records_read_midscene_lowlevel_items_in_seq_order(events_table):
    """跨引擎编组同构 + 升序读（ADR 0024）：Midscene worker 用低层 PutItemCommand 写（seq 显式 {N: 字符串}、body {S}），Nova worker
    用 resource 层 put_item（原生 int）。低层写的 item 由 records() 读出、条数与类型都对，且按 seq 升序（跨 9/10 边界）。

    守得住的：两种编组不兼容（如 seq 误写成 {S}）时 moto 拒写或读不出；读端误用降序时顺序断言变红。守不住的：漏写
    ScanIndexForward——moto 默认即按排序键升序返回。moto 对 DDB 数据模型（N 键编组、排序键升序）保真，可用来验证。"""
    import boto3

    low = boto3.client("dynamodb", region_name="us-east-1")  # 低层 client：resource 的 meta.client 会把 {S:..} 再编组成 M
    pk = events_pk("run-1", "browse")
    for i in range(1, 11):
        low.put_item(TableName="gherkai-events", Item={
            "pk": {"S": pk}, "seq": {"N": str(i)},
            "body": {"S": f'{{"type":"step_done","scenarioId":"sc:0","stepIndex":{i - 1},"status":"passed"}}'},
        })
    low.put_item(TableName="gherkai-events", Item={
        "pk": {"S": pk}, "seq": {"N": "11"}, "body": {"S": '{"type":"scope_done","scopeId":"browse"}'}})
    recs = DdbEventLog(events_table, "run-1", ["browse"]).records()
    assert [r.seq for r in recs] == list(range(1, 12))
    assert [r.event.type for r in recs] == ["step_done"] * 10 + ["scope_done"]
    assert [r.event.step_index for r in recs[:10]] == list(range(10))


def test_ddb_records_paginate_across_last_evaluated_key():
    """records() 拉全所有页：DDB Query 单页上限 1MB，超出时返回 LastEvaluatedKey，不续 ExclusiveStartKey 就会静默丢掉后面的事件。
    moto 难造 1MB 分页，这里用按有无 ExclusiveStartKey 返回不同页的假表。"""
    pk = events_pk("run-1", "browse")

    def _item(seq: int) -> dict:
        return {"seq": seq, "body": f'{{"type":"step_done","scenarioId":"sc:0","stepIndex":{seq},"status":"passed"}}'}

    class _PagingTable:
        def __init__(self):
            self.calls = []

        def query(self, **kw):
            self.calls.append(kw)
            if "ExclusiveStartKey" not in kw:
                return {"Items": [_item(1), _item(2)], "LastEvaluatedKey": {"pk": pk, "seq": 2}}
            return {"Items": [_item(3), _item(4)]}

    table = _PagingTable()
    recs = DdbEventLog(table, "run-1", ["browse"]).records()
    assert [r.event.step_index for r in recs] == [1, 2, 3, 4]
    assert len(table.calls) == 2 and table.calls[1]["ExclusiveStartKey"] == {"pk": pk, "seq": 2}


# ---------- CloudLauncher ----------

# tick 认领时算出的截止时刻（认领时刻加预算，以运行期限封顶），随 launch 交出；CloudLauncher 把它原样交给 arm。
_CUTOFF = datetime(2026, 11, 8, 10, 5, 0, 250000, tzinfo=timezone.utc)


def test_cloud_launcher_calls_start_scope():
    """CloudLauncher.launch → resolver 选 engine → start_scope（fire-and-forget，不轮询）。"""
    from gherkai_core.adapters.cloud_launcher import CloudLauncher

    class FakeEngine:
        def __init__(self): self.started = []
        def start_scope(self, job): self.started.append(job.scope_id); return "arn:task/x"

    eng = FakeEngine()
    CloudLauncher(lambda name: eng, run_id="run-1").launch(_job("a"), cutoff_at=_CUTOFF)
    assert eng.started == ["a"]


class _RecorderWatch:
    def __init__(self, raise_on_arm: bool = False):
        self.armed: list[tuple] = []
        self._raise = raise_on_arm

    def arm(self, run_id, scope_id, at):
        if self._raise:
            raise RuntimeError("scheduler down")
        self.armed.append((run_id, scope_id, at))


class _FakeStartEngine:
    def __init__(self): self.started = []
    def start_scope(self, job): self.started.append(job.scope_id)


def test_cloud_launcher_arms_timeout_watch():
    """每个 job 都有截止时刻 → launch 后 arm(run_id, scope_id, at)（ADR 0034「job timeout」节的云端后端一侧）：at 就是 tick 算出的
    截止时刻，原样转交，launcher 不再由预算推算，到点时刻也不按 arm 时刻。"""
    from gherkai_core.adapters.cloud_launcher import CloudLauncher

    eng, watch = _FakeStartEngine(), _RecorderWatch()
    CloudLauncher(lambda name: eng, run_id="run-1", timeout_watch=watch).launch(
        _job("a", timeout_s=60.0), cutoff_at=_CUTOFF)
    assert eng.started == ["a"]
    assert watch.armed == [("run-1", "a", _CUTOFF)]


def test_cloud_launcher_arms_before_start_scope():
    """武装先于起 task（ADR 0034「job timeout」节 best-effort 边界）：launch 与其失败补偿双失败时，
    先建的 schedule 到点仍收敛——顺序倒过来（先 start 后 arm）双失败会失去最后兜底。"""
    from gherkai_core.adapters.cloud_launcher import CloudLauncher

    order = []

    class OrderWatch:
        def arm(self, run_id, scope_id, at): order.append("arm")

    class OrderEngine:
        def start_scope(self, job): order.append("start")

    CloudLauncher(lambda name: OrderEngine(), run_id="run-1", timeout_watch=OrderWatch()).launch(
        _job("a", timeout_s=60.0), cutoff_at=_CUTOFF)
    assert order == ["arm", "start"]


def test_cloud_launcher_launch_failure_still_armed_and_raises():
    """start_scope 抛异常：arm 已先行（schedule 在，双失败兜底生效）、异常照常冒泡（tick 靠它触发
    launch 失败补偿——不许被吞）。"""
    import pytest
    from gherkai_core.adapters.cloud_launcher import CloudLauncher

    watch = _RecorderWatch()

    class BoomEngine:
        def start_scope(self, job): raise RuntimeError("RunTask placement failure")

    with pytest.raises(RuntimeError, match="placement"):
        CloudLauncher(lambda name: BoomEngine(), run_id="run-1", timeout_watch=watch).launch(
            _job("a", timeout_s=60.0), cutoff_at=_CUTOFF)
    assert watch.armed == [("run-1", "a", _CUTOFF)]  # 武装已完成、不随 launch 失败丢失


def test_cloud_launcher_arm_failure_does_not_block_launch():
    """武装失败 best-effort（ADR 0034「job timeout」节边界）：不抛、task 已起——降级 tick 防御扫。"""
    from gherkai_core.adapters.cloud_launcher import CloudLauncher

    eng = _FakeStartEngine()
    CloudLauncher(lambda name: eng, run_id="run-1",
                  timeout_watch=_RecorderWatch(raise_on_arm=True)).launch(_job("a", timeout_s=60.0),
                                                                          cutoff_at=_CUTOFF)
    assert eng.started == ["a"]  # launch 完成、异常被兜（日志降级）


def test_cloud_launcher_requires_run_id_and_warns_only_for_missing_watch(caplog):
    """run_id 是必给参数（漏传在构造时就报 TypeError）；「后端未启用定时能力」的降级日志只对应 timeout_watch 为 None
    （旧部署）这一种情形，task 照常起。"""
    import logging
    import pytest
    from gherkai_core.adapters.cloud_launcher import CloudLauncher

    with pytest.raises(TypeError, match="run_id"):
        CloudLauncher(lambda name: _FakeStartEngine())
    eng = _FakeStartEngine()
    with caplog.at_level(logging.WARNING, logger="gherkai_core.adapters.cloud_launcher"):
        CloudLauncher(lambda name: eng, run_id="run-1").launch(_job("a", timeout_s=60.0), cutoff_at=_CUTOFF)
    assert eng.started == ["a"]
    assert any("后端未启用定时能力" in r.getMessage() for r in caplog.records), caplog.records


# ---------- reconcile.tick 用 DDB 后端（与 local 对拍）----------

_T0 = datetime(2030, 1, 1, tzinfo=timezone.utc)  # 假墙钟（远早于 FAR_DEADLINE）

class _Results:
    """记下每次保存的判定存储替身：ids 是 (scope_id, 标识)，按保存的次序；按标识读回。"""

    def __init__(self) -> None:
        self.ids: list[tuple[str, str]] = []
        self._by_id: dict = {}

    def save_job_result(self, run_id, result_id, jr):
        self.ids.append((jr.scope_id, result_id))
        self._by_id[result_id] = jr

    def load_job_result(self, run_id, result_id):
        return self._by_id.get(result_id)


def test_tick_with_ddb_backend(events_table, ddb_run_store):
    """reconcile.tick 用 DdbEventLog + DynamoDBRunStore + CloudLauncher（fake engine）走通：起 job → 先存明细、再以终态写记下 job 的
    终态并点名那一份，run 随之成为终态 → 再推进读到既有终态即停。"""
    from gherkai_core.adapters.cloud_launcher import CloudLauncher
    from gherkai_core.reconcile import TickOutcome, tick

    meta = _meta("a")
    ddb_run_store.create_run(meta, RunState(
        run_id="run-1", status=Status.PENDING,
        jobs={"a": JobState("a", Status.PENDING)}, started_at="t0", high_water_mark=0))
    log = DdbEventLog(events_table, "run-1", ["a"])

    class FakeEngine:
        def __init__(self): self.started = []
        def start_scope(self, job): self.started.append(job.scope_id)
    eng = FakeEngine()
    launcher = CloudLauncher(lambda name: eng, run_id="run-1")
    results = _Results()

    # tick1：起 a（认领 + launch）
    tick("run-1", meta, log, ddb_run_store, launcher, 1, clock=lambda: _T0, result_store=results)
    assert eng.started == ["a"]
    state = ddb_run_store.load_run_state("run-1")
    assert state.jobs["a"].status == Status.RUNNING
    # 本轮投影在认领之前（全 pending、不写 run 级），run 级由认领同一次写推进（ADR 0034 机制三「run 级状态只进不退」条①）
    assert state.status == Status.RUNNING

    # worker 事件 + 退出落表
    _passed_worker_events(events_table, "a")
    log.record_exit("a", 0)

    # tick2：投影把 a 写成 running（不写终态），终态写记下 a 的 passed 并点名存下的那一份，run 随之成为终态
    done = tick("run-1", meta, log, ddb_run_store, launcher, 1, clock=lambda: _T0 + timedelta(seconds=20),
                result_store=results)
    assert done is TickOutcome.COMMITTED and [sid for sid, _ in results.ids] == ["a"]
    state = ddb_run_store.load_run_state("run-1")
    assert (state.status, state.jobs["a"].status, state.jobs["a"].claimed_at, state.jobs["a"].result_id) == (
        Status.PASSED, Status.PASSED, instant_to_iso(_T0), results.ids[0][1])
    # 再 tick：读到既有终态即停，不再推演，也不再存明细
    assert tick("run-1", meta, log, ddb_run_store, launcher, 1, clock=lambda: _T0 + timedelta(seconds=30),
                result_store=results) is TickOutcome.ENDED
    assert len(results.ids) == 1
    assert ddb_run_store.load_run_state("run-1").ended_at == instant_to_iso(_T0 + timedelta(seconds=20))


def test_ddb_event_log_queries_with_consistent_read():
    """records() 是 reconcile 的投影输入：worker 与退出观察者刚写的尾事件必须**立即**可读
    （ADR 0030 决定六），最终一致读可能漏尾事件、把已完成 job 投成仍在运行——故 Query 必带 ConsistentRead。"""
    class _Rec:
        def __init__(self):
            self.calls = []

        def query(self, **kw):
            self.calls.append(kw)
            return {"Items": []}

    table = _Rec()
    assert DdbEventLog(table, "run-1", ["a", "b"]).records() == []
    assert len(table.calls) == 2
    assert all(kw.get("ConsistentRead") is True for kw in table.calls), table.calls


def test_ddb_record_exit_reason_roundtrip(events_table):
    """DDB 侧 reason 属性 omit-when-empty、records() 读回进 TaskExited.reason（观察者落哨兵时的用户可见归因）。"""
    log = DdbEventLog(events_table, "run-1", ["a", "b"])
    log.record_exit("a", 255, reason="TaskFailedToStart: CannotPullContainerError")
    log.record_exit("b", 0)
    exits = {r.scope_id: r.exited for r in log.records() if r.kind == "exit"}
    assert exits["a"].exit_code == 255 and exits["a"].reason == "TaskFailedToStart: CannotPullContainerError"
    assert exits["b"].reason is None
    item = events_table.get_item(Key={"pk": events_pk("run-1", "b"), "seq": EXIT_SK})["Item"]
    assert "reason" not in item


def _expiry_setup(events_table, ddb_run_store):
    """云端后端上的到期情形：期限在 T0+100（停止启动的时刻是 T0+40），a 在 T0 认领并已结束，b 还没有启动。"""
    from gherkai_core.adapters.cloud_launcher import CloudLauncher
    from gherkai_core.reconcile import tick

    meta = _meta("a", "b", deadline_at=instant_to_iso(_T0 + timedelta(seconds=100)))
    ddb_run_store.create_run(meta, RunState(
        run_id="run-1", status=Status.PENDING,
        jobs={s: JobState(s, Status.PENDING) for s in ("a", "b")}, started_at="t0", high_water_mark=0))
    launcher = CloudLauncher(lambda name: _FakeStartEngine(), run_id="run-1")
    log = DdbEventLog(events_table, "run-1", ["a", "b"])
    tick("run-1", meta, log, ddb_run_store, launcher, 1, clock=lambda: _T0, result_store=_Results())  # 起 a
    _passed_worker_events(events_table, "a")
    log.record_exit("a", 0)
    return meta, launcher


def test_expiry_commits_on_ddb(events_table, ddb_run_store):
    """云端后端上的到期：已过停止启动的时刻，最后一个执行中的 a 在这一轮得出结果，b 还没有启动。同一轮先以终态写记下 a 并点名它的那一份，
    再做到期的结束写：不认领 b，b 记 skipped 并带到期的说明、不点名，run 按取法记 aborted、带「已超过允许运行的时间」；结束写整体替换
    jobs 时带上 a 已有的点名（与本机对拍）。"""
    from gherkai_core.reconcile import TickOutcome, tick
    from gherkai_core.run_status import RUN_ENDINGS

    meta, launcher = _expiry_setup(events_table, ddb_run_store)
    log = DdbEventLog(events_table, "run-1", ["a", "b"])
    results = _Results()
    done = tick("run-1", meta, log, ddb_run_store, launcher, 1, clock=lambda: _T0 + timedelta(seconds=41),
                result_store=results)
    assert done is TickOutcome.COMMITTED and [sid for sid, _ in results.ids] == ["a"]
    ending = RUN_ENDINGS["deadline"]
    state = ddb_run_store.load_run_state("run-1")
    assert (state.status, state.message, state.jobs["a"].status, state.jobs["b"].status, state.jobs["b"].message) == (
        Status.ABORTED, ending.run_message, Status.PASSED, Status.SKIPPED, ending.skipped_message)
    assert (state.jobs["a"].result_id, state.jobs["b"].result_id) == (results.ids[0][1], None)


def test_expiry_loses_to_a_claim_that_landed_after_the_read_on_ddb(events_table, ddb_run_store):
    """到期的结束写与认领并发（云端的条件写）：一个推进器读到「没有执行中的、仍有未启动的」之后，另一个推进器的认领落下——前者的结束写
    按写下时的运行态判断（以写入序号为条件、不成立即重读再算），那时已有 running 的 job，写不成；重读到 run 仍未结束，返回继续推进；
    run 没有结束、新认领的 job 仍是 running，同一轮得出结果的 a 已由终态写记下。"""
    from gherkai_core.reconcile import TickOutcome, tick

    meta, launcher = _expiry_setup(events_table, ddb_run_store)

    class _ClaimLandsAfterRead(DdbEventLog):
        landed = False

        def records(self):
            recs = super().records()
            if not self.landed:
                self.landed = ddb_run_store.try_claim_job("run-1", "b", claimed_at=instant_to_iso(_T0 + timedelta(seconds=39)))
            return recs

    log = _ClaimLandsAfterRead(events_table, "run-1", ["a", "b"])
    outcome = tick("run-1", meta, log, ddb_run_store, launcher, 1, clock=lambda: _T0 + timedelta(seconds=41),
                   result_store=_Results())

    assert log.landed is True
    assert outcome is TickOutcome.CONTINUE
    state = ddb_run_store.load_run_state("run-1")
    assert (state.status, state.claim_count, state.jobs["a"].status, state.jobs["b"].status, state.message) == (
        Status.RUNNING, 2, Status.PASSED, Status.RUNNING, None)


def test_commit_rejected_by_the_write_seq_names_the_same_id_after_rereading(aws, events_table, s3_result_store):
    """云端的终态写被写入序号挡下、重读再算之后写成：运行态里点名的仍是推进步骤这一轮存下的那一份的标识（重读再算用的是同一组
    JobState，不另生成标识、不另存一份；ADR 0030 决定三「被点名的那一份」条），按点名的标识从 S3 读回的正是 a 的那一份。固定先后：终态写
    读到 STATE 之后、发出条件写之前，另一个推进方认领了 b（包住被测表对象的 update_item，只在终态写里插一次）。"""
    from gherkai_core.adapters.cloud_launcher import CloudLauncher
    from gherkai_core.adapters.run_store.ddb import DynamoDBRunStore
    from gherkai_core.named_details import load_named_details
    from gherkai_core.reconcile import TickOutcome, tick

    table = aws["ddb"].Table(aws["table_name"])
    other = DynamoDBRunStore(aws["ddb"].Table(aws["table_name"]), jobs_objects=jobs_objects_for(aws))
    ccf = table.meta.client.exceptions.ConditionalCheckFailedException
    real_update = table.update_item
    log_of_writes: list[str] = []

    class _ArmedOnCommit(DynamoDBRunStore):
        armed = False

        def commit_job_states(self, run_id, job_states, *, ended_at):
            self.armed = True
            return super().commit_job_states(run_id, job_states, ended_at=ended_at)

    store = _ArmedOnCommit(table, jobs_objects=jobs_objects_for(aws))

    def update_item(**kwargs):
        if store.armed:
            store.armed = False
            assert other.try_claim_job("run-1", "b", claimed_at=instant_to_iso(_T0 + timedelta(seconds=5))) is True
            log_of_writes.append("other")
            try:
                resp = real_update(**kwargs)
            except ccf:
                log_of_writes.append("write-rejected")
                raise
            log_of_writes.append("write-ok")
            return resp
        if log_of_writes == ["other", "write-rejected"]:
            log_of_writes.append("reread-write")
        return real_update(**kwargs)

    table.update_item = update_item
    meta = _meta("a", "b")
    store.create_run(meta, RunState(run_id="run-1", status=Status.PENDING, started_at="t0", high_water_mark=0,
                                    jobs={s: JobState(s, Status.PENDING) for s in ("a", "b")}))
    log = DdbEventLog(events_table, "run-1", ["a", "b"])
    launcher = CloudLauncher(lambda name: _FakeStartEngine(), run_id="run-1")
    saved: list[tuple[str, str]] = []

    class _Recording:
        def save_job_result(self, run_id, result_id, jr):
            saved.append((jr.scope_id, result_id))
            s3_result_store.save_job_result(run_id, result_id, jr)

    tick("run-1", meta, log, store, launcher, 1, clock=lambda: _T0, result_store=_Recording())  # 起 a
    _passed_worker_events(events_table, "a")
    log.record_exit("a", 0)

    outcome = tick("run-1", meta, log, store, launcher, 1, clock=lambda: _T0 + timedelta(seconds=20),
                   result_store=_Recording())

    assert outcome is TickOutcome.CONTINUE  # b 已被另一方认领：这一方的认领被挡下
    assert log_of_writes == ["other", "write-rejected", "reread-write"]
    (scope_id, result_id), = saved
    state = store.load_run_state("run-1")
    assert (state.jobs["a"].status, state.jobs["a"].result_id) == (Status.PASSED, result_id)
    assert (state.jobs["b"].status, state.jobs["b"].result_id) == (Status.RUNNING, None)
    details = load_named_details("run-1", state.jobs.values(), s3_result_store)
    assert list(details) == ["a"] and (details["a"].scope_id, details["a"].status) == ("a", Status.PASSED)
