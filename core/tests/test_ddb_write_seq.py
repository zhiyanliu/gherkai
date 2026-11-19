"""DynamoDBRunStore 的写入序号与以它为条件的两个写入口（ADR 0030 决定六「STATE item 带写入序号」条、ADR 0034 机制三②）。

两个 adapter 共有的语义在 test_ending_and_commit_writes.py 对拍；这里只有 DynamoDB 一侧才有的性质：
- 写入序号：建 run 写 0；每一次写成的 update_item 恰好加一（认领、执行中的 job 写与它的回退写、投影的标量一步与每一次逐 job 写、
  try_finalize、终态写、结束写），条件不成立的写不改它。用写成的请求数作期望值，不按入口逐个写死次数。
- 读与写之间插入另一方的写：被测的一方读到 STATE 之后、发出写之前，另一个写入方（各持自己的表对象）落下认领、执行中的写、投影、
  终态写或结束写；被测的写被序号的条件挡下，重读之后按新的运行态得出正确结果，对方刚写的内容不被整体替换盖掉。被测方给出的那个
  job 上，对方写下的认领时刻留下；对方写下的会话在被测方没有给出会话时留下，给出了即取被测方的。先后靠包住被测表对象的
  update_item 固定下来，不靠线程竞争。
- 执行中的写（`update_job_state`）被挡下时由这次写带回的条目分辨原因，不另读。
- 写入次数：两个写入口没有并发的写时只发一次 update_item，run 已结束或结束写不成立时不发写；重读再算的次数用尽时抛错、不改记录。
- jobs Map 的条目没有 job 级说明时省键，由结束写结束的条目带说明表的那一句（读原始 STATE，不经 load_run_state）。
- 整体替换只改它该改的属性。状态分组随这两个写入口的变化在 test_status_group.py。
moto 的条件表达式是模拟实现：以序号为条件的整体替换在真实 DynamoDB 上的并发行为与 item 大小上限不在这里的证明范围内（ADR 0034
机制三②「实测项」）。
"""
from __future__ import annotations

import random

import pytest

from gherkai_core.model import Job, JobState, RunMeta, RunState, Scenario, Status, Step
from gherkai_core.run_status import RUN_ENDINGS, CommitOutcome

_T0 = "2026-11-19T00:00:00Z"
_CLAIMED = "2026-11-19T00:01:00Z"
_ENDED = "2026-11-19T02:00:00Z"
_TERMINAL = (Status.PASSED, Status.FAILED, Status.ERROR, Status.SKIPPED, Status.ABORTED)


def _meta(run_id: str, scope_ids: tuple[str, ...]) -> RunMeta:
    jobs = tuple(
        Job(scope_id=s, scope_name=s, engine="novaact", timeout_s=300.0,
            scenarios=(Scenario(id=f"{s}:1", name="s", steps=(Step(index=0, keyword="Given", text="x"),)),))
        for s in scope_ids)
    return RunMeta(run_id=run_id, created_at=_T0, jobs=jobs, deadline_at="2026-11-19T01:00:00+00:00")


def _create(store, scope_ids=("a", "b", "c"), *, run_id="run-1", hwm=0) -> RunMeta:
    meta = _meta(run_id, scope_ids)
    store.create_run(meta, RunState(run_id=run_id, status=Status.PENDING, started_at=_T0, high_water_mark=hwm,
                                    jobs={s: JobState(s, Status.PENDING) for s in scope_ids}))
    return meta


def _done(scope_id, status, *, session=None) -> JobState:
    return JobState(scope_id, status, session_id=session, claimed_at=_CLAIMED)


@pytest.fixture
def table(aws):
    return aws["ddb"].Table(aws["table_name"])


@pytest.fixture
def store(table):
    from gherkai_core.adapters.run_store.ddb import DynamoDBRunStore
    return DynamoDBRunStore(table)


@pytest.fixture
def other(aws):
    """另一个写入方：持自己的表对象，包住被测表对象的方法不影响它的写。"""
    from gherkai_core.adapters.run_store.ddb import DynamoDBRunStore
    return DynamoDBRunStore(aws["ddb"].Table(aws["table_name"]))


def _raw(table, run_id="run-1") -> dict:
    return table.get_item(Key={"run_id": run_id, "item_type": "STATE"}, ConsistentRead=True)["Item"]


def _seq(table, run_id="run-1"):
    return _raw(table, run_id).get("write_seq")


def _record(table, monkeypatch, *, before_write=()):
    """包住被测表对象的 get_item 与 update_item，依次记下 `read`、`write-ok`、`write-rejected`；`before_write` 里的动作按序在被测方
    前几次 update_item 发出之前各执行一次（记为 `other`），也就是插在被测方读到 STATE 与它的写之间。返回记录列表。"""
    ccf = table.meta.client.exceptions.ConditionalCheckFailedException
    log: list[str] = []
    pending = list(before_write)
    real_get, real_update = table.get_item, table.update_item

    def get_item(**kwargs):
        log.append("read")
        return real_get(**kwargs)

    def update_item(**kwargs):
        if pending:
            pending.pop(0)()
            log.append("other")
        try:
            resp = real_update(**kwargs)
        except ccf:
            log.append("write-rejected")
            raise
        log.append("write-ok")
        return resp

    monkeypatch.setattr(table, "get_item", get_item)
    monkeypatch.setattr(table, "update_item", update_item)
    return log


# ---------- 写入序号随每一次写成的写加一 ----------

def test_create_run_writes_the_write_seq_zero(table, store):
    _create(store)
    assert _seq(table) == 0


def _claim(store, meta):
    assert store.try_claim_job(meta.run_id, "a", claimed_at=_CLAIMED) is True


def _job_write(store, meta):
    assert store.update_job_state(meta.run_id, JobState("a", Status.RUNNING, session_id="sess-a")) is True


def _job_write_on_an_ended_run(store, meta):
    assert store.try_finalize(meta.run_id, Status.ERROR, "t0") is True
    assert store.update_job_state(meta.run_id, JobState("a", Status.PASSED)) is False  # 第一次写被挡、回退写写成


def _project(store, meta):
    projected = RunState(run_id=meta.run_id, status=Status.RUNNING, high_water_mark=2, jobs={
        "a": JobState("a", Status.RUNNING, session_id="sess-a"), "b": JobState("b", Status.PASSED),
        "c": JobState("c", Status.PENDING)})
    assert store.project_state(meta.run_id, projected) is True  # 标量一步加 a、b 各一次逐 job 写，c 跳过


def _finalize(store, meta):
    assert store.try_finalize(meta.run_id, Status.ERROR, "t1", message="原因") is True


def _commit(store, meta):
    _claim(store, meta)
    assert store.commit_job_states(meta.run_id, [_done("a", Status.PASSED)], ended_at=_ENDED) is CommitOutcome.OPEN


def _end(store, meta):
    _claim(store, meta)
    assert store.end_run(meta.run_id, RUN_ENDINGS["settle-advancer-exited"], ended_at=_ENDED) is True


@pytest.mark.parametrize("write", [_claim, _job_write, _job_write_on_an_ended_run, _project, _finalize, _commit, _end],
                         ids=["try_claim_job", "update_job_state", "update_job_state-ended", "project_state",
                              "try_finalize", "commit_job_states", "end_run"])
def test_each_landed_update_increments_the_write_seq_once(table, store, monkeypatch, write):
    """每个写入口之后，写入序号的增量等于这期间写成的 update_item 请求数：每一次写成的写恰好加一，被条件挡下的写不改它。"""
    meta = _create(store)
    log = _record(table, monkeypatch)
    write(store, meta)
    landed = log.count("write-ok")
    assert landed >= 1, "前提：这个写入口确实写成了"
    assert _seq(table) == landed


def test_rejected_writes_leave_the_write_seq(table, store):
    """条件不成立的写不改写入序号：认领已不是 pending 的 job、过期的投影、对已结束的 run 收尾、终态写与结束写。"""
    meta = _create(store, ("a", "b"), hwm=5)
    _claim(store, meta)
    seq = _seq(table)
    assert store.try_claim_job("run-1", "a") is False
    stale = RunState(run_id="run-1", status=Status.RUNNING, high_water_mark=4,
                     jobs={"a": JobState("a", Status.RUNNING), "b": JobState("b", Status.RUNNING)})
    assert store.project_state("run-1", stale) is False
    assert _seq(table) == seq

    assert store.end_run("run-1", RUN_ENDINGS["settle-past-deadline"], ended_at=_ENDED) is True
    seq = _seq(table)
    assert store.try_finalize("run-1", Status.PASSED, "t2") is False
    assert store.commit_job_states("run-1", [_done("a", Status.PASSED)], ended_at="t2") is CommitOutcome.ALREADY_ENDED
    assert store.end_run("run-1", RUN_ENDINGS["settle-advancer-exited"], ended_at="t2") is False
    assert _seq(table) == seq


def _random_write(rng: random.Random, store, meta: RunMeta, hwm: list[int]) -> None:
    sid = rng.choice([j.scope_id for j in meta.jobs])
    op = rng.randrange(6)
    if op == 0:
        store.try_claim_job(meta.run_id, sid, claimed_at=_CLAIMED)
    elif op == 1:
        store.update_job_state(meta.run_id, JobState(sid, rng.choice([Status.PENDING, Status.RUNNING])))
    elif op == 2:
        hwm[0] += rng.choice([-1, 0, 1])  # 含过期的投影（被条件挡下）
        statuses = {j.scope_id: rng.choice([Status.PENDING, Status.RUNNING, *_TERMINAL]) for j in meta.jobs}
        store.project_state(meta.run_id, RunState(run_id=meta.run_id, status=Status.RUNNING, high_water_mark=hwm[0],
                                                  jobs={s: JobState(s, st) for s, st in statuses.items()}))
    elif op == 3:
        store.try_finalize(meta.run_id, rng.choice(_TERMINAL), _ENDED)
    elif op == 4:
        store.commit_job_states(meta.run_id, [_done(sid, rng.choice(_TERMINAL))], ended_at=_ENDED)
    else:
        store.end_run(meta.run_id, RUN_ENDINGS[rng.choice(list(RUN_ENDINGS))], ended_at=_ENDED)


def test_write_seq_counts_every_landed_update_of_a_random_sequence(table, store, monkeypatch):
    """经任意写序列（认领、执行中的 job 写、含过期的投影、收尾写、终态写、各条来路的结束写），每次写之后写入序号都等于至此写成的
    update_item 请求数。种子固定，失败可复现。"""
    rng = random.Random(20261119)
    log = _record(table, monkeypatch)
    for n in range(30):
        meta = _create(store, run_id=f"run-{n:02d}")
        log.clear()
        hwm = [0]
        for _ in range(12):
            _random_write(rng, store, meta, hwm)
            assert _seq(table, meta.run_id) == log.count("write-ok"), log


# ---------- 读与写之间插入另一方的写：终态写 ----------

def test_commit_rewrites_after_a_claim_landing_between_its_read_and_write(table, store, other, monkeypatch):
    """终态写读到 b 仍 pending 之后，另一方认领 b：整体替换被序号的条件挡下，重读之后再写，b 的认领（running、认领时刻、认领计数）
    不被这次替换盖回 pending。"""
    meta = _create(store)
    _claim(store, meta)
    log = _record(table, monkeypatch,
                  before_write=[lambda: other.try_claim_job("run-1", "b", claimed_at="2026-11-19T00:02:00Z")])

    assert store.commit_job_states("run-1", [_done("a", Status.PASSED)], ended_at=_ENDED) is CommitOutcome.OPEN

    assert log == ["read", "other", "write-rejected", "read", "write-ok"]
    got = store.load_run_state("run-1")
    assert got.jobs["a"] == _done("a", Status.PASSED)
    assert got.jobs["b"] == JobState("b", Status.RUNNING, claimed_at="2026-11-19T00:02:00Z")
    assert (got.status, got.claim_count) == (Status.RUNNING, 2)


def test_commit_keeps_a_session_written_by_a_projection_between_its_read_and_write(table, store, other, monkeypatch):
    """终态写读到之后，另一方的投影为执行中的 b 写下代表会话并推进 HWM：重读之后再写，会话与 HWM 都在。"""
    meta = _create(store)
    _claim(store, meta)
    assert store.try_claim_job("run-1", "b", claimed_at=_CLAIMED) is True
    projected = RunState(run_id="run-1", status=Status.RUNNING, high_water_mark=7, jobs={
        "a": JobState("a", Status.RUNNING), "b": JobState("b", Status.RUNNING, session_id="sess-b"),
        "c": JobState("c", Status.PENDING)})
    log = _record(table, monkeypatch, before_write=[lambda: other.project_state("run-1", projected)])

    assert store.commit_job_states("run-1", [_done("a", Status.FAILED)], ended_at=_ENDED) is CommitOutcome.OPEN

    assert log.count("write-rejected") == 1 and log[-1] == "write-ok"
    got = store.load_run_state("run-1")
    assert got.jobs["b"] == JobState("b", Status.RUNNING, session_id="sess-b", claimed_at=_CLAIMED)
    assert (got.jobs["a"].status, got.high_water_mark) == (Status.FAILED, 7)


def _session_by_job_write(other):
    assert other.update_job_state("run-1", JobState("a", Status.RUNNING, session_id="new-session",
                                                    claimed_at=_CLAIMED)) is True


def _session_by_projection(other):
    projected = RunState(run_id="run-1", status=Status.RUNNING, high_water_mark=3, jobs={
        "a": JobState("a", Status.RUNNING, session_id="new-session"), "b": JobState("b", Status.PENDING),
        "c": JobState("c", Status.PENDING)})
    assert other.project_state("run-1", projected) is True


@pytest.mark.parametrize("other_write", [_session_by_job_write, _session_by_projection],
                         ids=["update_job_state", "project_state"])
def test_commit_keeps_a_session_of_its_own_job_written_between_its_read_and_write(table, store, other, monkeypatch,
                                                                                   other_write):
    """终态写读到 a 还没有会话之后，另一方为 a 写下会话（执行中的写，或投影）：被测的写被序号的条件挡下，重读之后按库中的条目合并，
    a 是给出的终态、带着另一方写下的会话；给出的参数没有会话，不以空值覆盖它。"""
    meta = _create(store)
    _claim(store, meta)
    log = _record(table, monkeypatch, before_write=[lambda: other_write(other)])

    assert store.commit_job_states("run-1", [JobState("a", Status.PASSED, claimed_at=_CLAIMED)],
                                   ended_at=_ENDED) is CommitOutcome.OPEN

    assert log == ["read", "other", "write-rejected", "read", "write-ok"]
    assert store.load_run_state("run-1").jobs["a"] == JobState("a", Status.PASSED, session_id="new-session",
                                                               claimed_at=_CLAIMED)


def test_commit_keeps_a_claim_time_of_its_own_job_written_between_its_read_and_write(table, store, other, monkeypatch):
    """终态写读到 a 仍 pending 之后另一方认领 a：被测的写被挡下，重读之后合并，a 是给出的终态，认领时刻是认领写下的（给出的参数
    没有），认领计数为 1。"""
    _create(store)
    log = _record(table, monkeypatch,
                  before_write=[lambda: other.try_claim_job("run-1", "a", claimed_at="2026-11-19T00:02:00Z")])

    assert store.commit_job_states("run-1", [JobState("a", Status.ERROR)], ended_at=_ENDED) is CommitOutcome.OPEN

    assert log == ["read", "other", "write-rejected", "read", "write-ok"]
    got = store.load_run_state("run-1")
    assert got.jobs["a"] == JobState("a", Status.ERROR, claimed_at="2026-11-19T00:02:00Z")
    assert got.claim_count == 1


def test_commit_after_a_rejection_takes_its_own_session_and_the_recorded_claim_time(table, store, other, monkeypatch):
    """终态写读到 a 仍 pending 之后，另一方认领 a 并为它写下会话：被测的写被挡下，重读之后合并。参数带着产出这个结果的那次执行的会话
    与另一个认领时刻：a 的会话取参数的，认领时刻是认领写下的，认领计数为 1。"""
    _create(store)
    claimed = "2026-11-19T00:02:00Z"

    def claim_and_write_a_session():
        assert other.try_claim_job("run-1", "a", claimed_at=claimed) is True
        assert other.update_job_state("run-1", JobState("a", Status.RUNNING, session_id="new-session",
                                                        claimed_at=claimed)) is True

    log = _record(table, monkeypatch, before_write=[claim_and_write_a_session])

    assert store.commit_job_states("run-1", [JobState("a", Status.PASSED, session_id="sess-result",
                                                      claimed_at="2026-11-19T00:09:00Z")],
                                   ended_at=_ENDED) is CommitOutcome.OPEN

    assert log == ["read", "other", "write-rejected", "read", "write-ok"]
    got = store.load_run_state("run-1")
    assert got.jobs["a"] == JobState("a", Status.PASSED, session_id="sess-result", claimed_at=claimed)
    assert got.claim_count == 1


def test_two_commits_each_reading_the_other_job_unfinished_end_the_run_once(table, store, other, monkeypatch):
    """两方各记一个 job 的终态、都读到对方的 job 未结束（ADR 0034 机制三②的理由一段）：另一方先写成、得 OPEN；被测方的写被挡下，重读
    之后两个 job 都已结束，它的写使 run 成为终态、得 ENDED_RUN。不会留下「全部 job 已结束、run 仍为 running」，也不丢另一方的终态。"""
    meta = _create(store, ("a", "b"))
    _claim(store, meta)
    assert store.try_claim_job("run-1", "b", claimed_at=_CLAIMED) is True
    outcomes = []
    log = _record(table, monkeypatch, before_write=[
        lambda: outcomes.append(other.commit_job_states("run-1", [_done("b", Status.PASSED)], ended_at="t-other"))])

    assert store.commit_job_states("run-1", [_done("a", Status.PASSED)], ended_at=_ENDED) is CommitOutcome.ENDED_RUN

    assert outcomes == [CommitOutcome.OPEN]
    assert log == ["read", "other", "write-rejected", "read", "write-ok"]
    got = store.load_run_state("run-1")
    assert {sid: js.status for sid, js in got.jobs.items()} == {"a": Status.PASSED, "b": Status.PASSED}
    assert (got.status, got.ended_at) == (Status.PASSED, _ENDED)


def test_commit_returns_already_ended_when_an_end_run_lands_between_its_read_and_write(table, store, other, monkeypatch):
    """终态写读到之后，处置的结束写结束了 run：被测的写被挡下，重读到 run 已结束，返回 ALREADY_ENDED、不再写；记录是结束写写下的。"""
    meta = _create(store, ("a", "b"))
    _claim(store, meta)
    ended = []

    def settle():
        assert other.end_run("run-1", RUN_ENDINGS["settle-advancer-exited"], ended_at="t-settle") is True
        ended.append(other.load_run_state("run-1"))

    log = _record(table, monkeypatch, before_write=[settle])

    assert store.commit_job_states("run-1", [_done("a", Status.PASSED)], ended_at=_ENDED) is CommitOutcome.ALREADY_ENDED

    assert log == ["read", "other", "write-rejected", "read"]
    assert store.load_run_state("run-1") == ended[0]
    assert ended[0].jobs["a"].status == Status.ABORTED


# ---------- 读与写之间插入另一方的写：结束写 ----------

def test_end_run_by_deadline_yields_to_a_claim_landing_between_its_read_and_write(table, store, other, monkeypatch):
    """到期的结束写读到没有执行中的 job 之后，另一方认领 b：被测的写被挡下，重读之后出现了 running 的 job，这条来路不结束它，返回
    False、不再写；run 仍未结束，b 是 running（ADR 0054 决策二后台推进条「收尾与报告」：有了新的认领按继续推进处理）。"""
    meta = _create(store, ("a", "b"))
    log = _record(table, monkeypatch, before_write=[lambda: other.try_claim_job("run-1", "b", claimed_at=_CLAIMED)])

    assert store.end_run("run-1", RUN_ENDINGS["deadline"], ended_at=_ENDED) is False

    assert log == ["read", "other", "write-rejected", "read"]
    got = store.load_run_state("run-1")
    assert (got.status, got.ended_at, got.message) == (Status.RUNNING, None, None)
    assert (got.jobs["a"].status, got.jobs["b"].status) == (Status.PENDING, Status.RUNNING)


def test_end_run_by_deadline_lands_after_a_claim_and_its_result_both_land_between_its_read_and_write(
        table, store, other, monkeypatch):
    """到期的结束写读到没有执行中的 job 之后，另一方认领 b 并以启动失败的补偿记下 b 的终态：被测的写被序号的条件挡下，重读之后没有
    running 的 job，结束写成立、写成；a 记 skipped，b 保留另一方写下的 error。序号只保证判断按最新的运行态，「没有执行中的 job」这一
    条件是结束写自带的。"""
    meta = _create(store, ("a", "b"))
    ending = RUN_ENDINGS["deadline"]

    def claim_and_fail_to_launch():
        assert other.try_claim_job("run-1", "b", claimed_at=_CLAIMED) is True
        assert other.commit_job_states("run-1", [_done("b", Status.ERROR)], ended_at="t-other") is CommitOutcome.OPEN

    log = _record(table, monkeypatch, before_write=[claim_and_fail_to_launch])

    assert store.end_run("run-1", ending, ended_at=_ENDED) is True

    assert log == ["read", "other", "write-rejected", "read", "write-ok"]
    got = store.load_run_state("run-1")
    assert got.jobs["a"] == JobState("a", Status.SKIPPED, message=ending.skipped_message)
    assert got.jobs["b"] == _done("b", Status.ERROR)
    assert (got.status, got.message, got.ended_at) == (Status.ERROR, ending.run_message, _ENDED)


def test_settling_end_run_records_a_job_claimed_between_its_read_and_write_as_aborted(table, store, other, monkeypatch):
    """处置的结束写读到之后另一方认领 b：重读之后再写，b 按运行态里的 running 记 aborted、带认领时刻，a 记 skipped。"""
    meta = _create(store, ("a", "b"))
    ending = RUN_ENDINGS["settle-past-deadline"]
    _record(table, monkeypatch, before_write=[lambda: other.try_claim_job("run-1", "b", claimed_at=_CLAIMED)])

    assert store.end_run("run-1", ending, ended_at=_ENDED) is True

    got = store.load_run_state("run-1")
    assert got.jobs["a"] == JobState("a", Status.SKIPPED, message=ending.skipped_message)
    assert got.jobs["b"] == JobState("b", Status.ABORTED, claimed_at=_CLAIMED, message=ending.aborted_message)
    assert (got.status, got.claim_count) == (Status.ABORTED, 1)


def test_end_run_returns_false_when_the_last_commit_lands_between_its_read_and_write(table, store, other, monkeypatch):
    """处置的结束写读到之后，最后一个 job 的终态写使 run 成为终态：被测的写被挡下，重读到 run 已结束，返回 False；记录是终态写写下的，
    没有 run 级说明。"""
    meta = _create(store, ("a",))
    _claim(store, meta)
    log = _record(table, monkeypatch, before_write=[
        lambda: other.commit_job_states("run-1", [_done("a", Status.PASSED)], ended_at="t-commit")])

    assert store.end_run("run-1", RUN_ENDINGS["settle-advancer-exited"], ended_at=_ENDED) is False

    assert log == ["read", "other", "write-rejected", "read"]
    got = store.load_run_state("run-1")
    assert (got.status, got.ended_at, got.message, got.jobs["a"]) == (
        Status.PASSED, "t-commit", None, _done("a", Status.PASSED))


def test_end_run_keeps_a_projection_landing_between_its_read_and_write(table, store, other, monkeypatch):
    """结束写读到之后另一方的投影推进 HWM 并给执行中的 a 写下会话：重读之后再写，a 记 aborted 时带着这个会话，HWM 保留投影写下的值。"""
    meta = _create(store, ("a", "b"))
    _claim(store, meta)
    projected = RunState(run_id="run-1", status=Status.RUNNING, high_water_mark=9,
                         jobs={"a": JobState("a", Status.RUNNING, session_id="sess-a"), "b": JobState("b", Status.PENDING)})
    _record(table, monkeypatch, before_write=[lambda: other.project_state("run-1", projected)])

    assert store.end_run("run-1", RUN_ENDINGS["settle-advancer-exited"], ended_at=_ENDED) is True

    got = store.load_run_state("run-1")
    assert (got.jobs["a"].status, got.jobs["a"].session_id, got.high_water_mark) == (Status.ABORTED, "sess-a", 9)


def test_replacement_on_a_record_without_write_seq_is_still_conditional(table, store, other, monkeypatch):
    """STATE 上没有写入序号属性（早于这个属性写出的记录只能这样构造）：终态写以「仍没有这个属性」为条件。读之后落下的认领从 0 起算把
    它补成 1，被测的写因此被挡下、重读再写，认领不丢；写成之后序号为 2。"""
    meta = _create(store)
    _claim(store, meta)
    table.update_item(Key={"run_id": "run-1", "item_type": "STATE"}, UpdateExpression="REMOVE write_seq")
    assert _seq(table) is None
    log = _record(table, monkeypatch, before_write=[lambda: other.try_claim_job("run-1", "b", claimed_at=_CLAIMED)])

    assert store.commit_job_states("run-1", [_done("a", Status.PASSED)], ended_at=_ENDED) is CommitOutcome.OPEN

    assert log.count("write-rejected") == 1
    got = store.load_run_state("run-1")
    assert (got.jobs["a"].status, got.jobs["b"].status) == (Status.PASSED, Status.RUNNING)
    assert _seq(table) == 2


# ---------- 执行中的写：被挡下的原因取自这次写带回的条目 ----------

def test_job_write_tells_why_it_was_rejected_from_the_rejected_write_itself(table, store, monkeypatch):
    """`update_job_state` 被挡下时不另读：run 未结束而 a 已是终态时只有被挡下的那一次写，a 不变、返回 True；run 经 try_finalize 结束、
    b 仍执行中时，被挡下之后再写一次只写 b、返回 False；a 已是终态时在已结束的 run 上同样只有被挡下的那一次写、返回 False。"""
    meta = _create(store, ("a", "b"))
    _claim(store, meta)
    assert store.try_claim_job("run-1", "b", claimed_at=_CLAIMED) is True
    assert store.commit_job_states("run-1", [_done("a", Status.PASSED)], ended_at="never") is CommitOutcome.OPEN
    log = _record(table, monkeypatch)

    assert store.update_job_state("run-1", JobState("a", Status.RUNNING, session_id="late")) is True
    assert log == ["write-rejected"]
    assert store.load_run_state("run-1").jobs["a"] == _done("a", Status.PASSED)

    assert store.try_finalize("run-1", Status.ERROR, "t1") is True
    log.clear()
    assert store.update_job_state("run-1", JobState("b", Status.PASSED, session_id="sess-b")) is False
    assert log == ["write-rejected", "write-ok"]
    log.clear()
    assert store.update_job_state("run-1", JobState("a", Status.RUNNING)) is False
    assert log == ["write-rejected"]
    got = store.load_run_state("run-1")
    assert (got.jobs["a"], got.jobs["b"], got.status) == (
        _done("a", Status.PASSED), JobState("b", Status.PASSED, session_id="sess-b"), Status.ERROR)


# ---------- 写入次数 ----------

def test_both_entries_write_once_without_contention_and_not_at_all_when_they_do_not_land(table, store, monkeypatch):
    """没有并发的写时，终态写与结束写各只发一次 update_item，不等待；run 已结束、给出的 job 都已是终态、参数不合要求、到期的结束写
    遇到 running 的 job 时都不发写。"""
    from gherkai_core.adapters.run_store import ddb
    sleeps: list[float] = []
    monkeypatch.setattr(ddb.time, "sleep", sleeps.append)
    meta = _create(store)
    _claim(store, meta)
    log = _record(table, monkeypatch)

    assert store.commit_job_states("run-1", [_done("a", Status.PASSED)], ended_at=_ENDED) is CommitOutcome.OPEN
    assert log == ["read", "write-ok"]
    log.clear()
    assert store.commit_job_states("run-1", [_done("a", Status.ERROR)], ended_at=_ENDED) is CommitOutcome.OPEN
    with pytest.raises(ValueError):
        store.commit_job_states("run-1", [_done("ghost", Status.PASSED)], ended_at=_ENDED)
    assert "write-ok" not in log and "write-rejected" not in log

    store.update_job_state("run-1", JobState("b", Status.RUNNING))  # 不经被测入口的前提写，下面清掉它的记录
    log.clear()
    assert store.end_run("run-1", RUN_ENDINGS["interrupt"], ended_at=_ENDED) is False
    assert log == ["read"]
    log.clear()
    assert store.end_run("run-1", RUN_ENDINGS["settle-advancer-exited"], ended_at=_ENDED) is True
    assert log == ["read", "write-ok"]
    log.clear()
    assert store.end_run("run-1", RUN_ENDINGS["settle-past-deadline"], ended_at=_ENDED) is False
    assert store.commit_job_states("run-1", [_done("c", Status.PASSED)], ended_at=_ENDED) is CommitOutcome.ALREADY_ENDED
    assert log == ["read", "read"]
    assert sleeps == []


@pytest.mark.parametrize("entry", ["commit_job_states", "end_run"])
def test_exhausted_retries_raise_without_changing_the_record(table, store, other, monkeypatch, entry):
    """每一次写之前都有另一方的写落下时，重读再算到次数用尽即抛 RunStateWriteContended：写的次数是一次加上全部重试，每次重试之前
    都等待，记录只有另一方的写。"""
    from gherkai_core.adapters.run_store import ddb
    sleeps: list[float] = []
    monkeypatch.setattr(ddb.time, "sleep", sleeps.append)
    meta = _create(store)
    _claim(store, meta)
    attempts = ddb._REPLACE_MAX_RETRIES + 1
    sessions = iter(range(attempts))
    log = _record(table, monkeypatch, before_write=[
        lambda: other.update_job_state("run-1", JobState("c", Status.RUNNING, session_id=f"s{next(sessions)}"))
    ] * attempts)

    with pytest.raises(ddb.RunStateWriteContended) as raised:
        if entry == "commit_job_states":
            store.commit_job_states("run-1", [_done("a", Status.PASSED)], ended_at=_ENDED)
        else:
            store.end_run("run-1", RUN_ENDINGS["settle-advancer-exited"], ended_at=_ENDED)

    assert raised.value.attempts == attempts and raised.value.run_id == "run-1"
    assert log.count("write-rejected") == attempts and "write-ok" not in log
    assert len(sleeps) == attempts - 1
    got = store.load_run_state("run-1")
    assert (got.status, got.jobs["a"].status) == (Status.RUNNING, Status.RUNNING)
    assert got.jobs["c"] == JobState("c", Status.RUNNING, session_id=f"s{attempts - 1}")


# ---------- jobs Map 条目的 job 级说明 ----------

def test_job_entries_omit_the_message_key_unless_an_ending_wrote_one(table, store):
    """jobs Map 里没有 job 级说明的条目不带 message 键（省键，不写成 NULL）：建 run、终态写的 OPEN 与 ENDED_RUN、结束写之后读原始
    STATE，由执行结果结束与还没有结束的 job 都没有这个键；由结束写结束的 job 的条目里是说明表的那一句。只经 load_run_state 读回
    比较时，写成 NULL 与省键读回都是 None，分不出来。"""
    def entries(run_id):
        return _raw(table, run_id)["jobs"]

    _create(store, ("a", "b"))
    assert all("message" not in e for e in entries("run-1").values())
    for sid in ("a", "b"):
        assert store.try_claim_job("run-1", sid, claimed_at=_CLAIMED) is True
    assert store.commit_job_states("run-1", [_done("a", Status.PASSED)], ended_at="t-a") is CommitOutcome.OPEN
    assert all("message" not in e for e in entries("run-1").values())
    assert store.commit_job_states("run-1", [_done("b", Status.FAILED)], ended_at=_ENDED) is CommitOutcome.ENDED_RUN
    assert all("message" not in e for e in entries("run-1").values())

    _create(store, ("a", "b", "c"), run_id="run-2")
    for sid in ("b", "c"):
        assert store.try_claim_job("run-2", sid, claimed_at=_CLAIMED) is True
    assert store.commit_job_states("run-2", [_done("c", Status.PASSED)], ended_at="t-c") is CommitOutcome.OPEN
    ending = RUN_ENDINGS["settle-advancer-exited"]
    assert store.end_run("run-2", ending, ended_at=_ENDED) is True
    got = entries("run-2")
    assert (got["a"]["message"], got["b"]["message"]) == (ending.skipped_message, ending.aborted_message)
    assert "message" not in got["c"]


# ---------- 整体替换写的属性 ----------

def test_replacement_leaves_start_hwm_claim_count_and_extras(table, store):
    """整体替换只改 jobs、run 状态与分组、结束时刻、run 级说明与写入序号：开始时刻、HWM、认领计数与顶层附加属性原样保留。"""
    meta = _create(store, ("a", "b"), hwm=4)
    _claim(store, meta)
    table.update_item(Key={"run_id": "run-1", "item_type": "STATE"}, UpdateExpression="SET detached = :d",
                      ExpressionAttributeValues={":d": True})
    before = _raw(table)
    assert store.end_run("run-1", RUN_ENDINGS["settle-past-deadline"], ended_at=_ENDED) is True
    after = _raw(table)
    changed = {k for k in before.keys() | after.keys() if before.get(k) != after.get(k)}
    assert changed == {"jobs", "status", "status_group", "ended_at", "message", "write_seq"}
    assert (after["started_at"], after["high_water_mark"], after["claim_count"], after["detached"]) == (_T0, 4, 1, True)
