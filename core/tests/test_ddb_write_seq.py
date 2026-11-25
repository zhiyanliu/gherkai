"""DynamoDBRunStore 的写入序号与以它为条件的两个写入口（ADR 0030 决定六「STATE item 带写入序号」条、ADR 0034 机制三②）。

两个 adapter 共有的语义在 test_ending_and_commit_writes.py 对拍；这里只有 DynamoDB 一侧才有的性质：
- 写入序号：建 run 写 0；改变了整体替换所写内容（jobs 与 run 状态）的写在同一次写里恰好加一（认领、执行中的 job 写、投影的逐 job
  写、终态写、结束写），投影的标量一步只写 HWM、不加，条件不成立的写不改它。用写成的请求数作期望值，不按入口逐个写死次数；另核每一次
  改变了 jobs 或 run 状态的写都加了一。
- 投影的逐 job 写只在这次写提及的字段与库中此刻的值至少一项不同时写成：内容不变的投影不改写入序号，所以读与写之间落下的这类投影
  不再把终态写挤去重读（ADR 0034 机制三「逐 job 写：内容不变不写，注定不成立的不发」段的两线程反例）。
- 读与写之间插入另一方的写：被测的一方读到 STATE 之后、发出写之前，另一个写入方（各持自己的表对象）落下认领、执行中的写、投影、
  终态写或结束写；被测的写被序号的条件挡下，重读之后按新的运行态得出正确结果，对方刚写的内容不被整体替换盖掉。被测方给出的那个
  job 上，对方写下的认领时刻留下；对方写下的会话在被测方没有给出会话时留下，给出了即取被测方的。先后靠包住被测表对象的
  update_item 固定下来，不靠线程竞争。
- 执行中的写（`update_job_state`）只发一次写，被挡下时由这次写带回的条目分辨原因，不另读；它逐属性写条目里的模型键，这次没有值的
  删去，不提及不认识的属性。
- 写入次数：两个写入口没有并发的写时只发一次 update_item，run 已结束或结束写不成立时不发写；重读再算的次数用尽时抛错、不改记录。
- 整体替换的条件里「run 未结束」一项（ADR 0030 决定六「两个写入口的步骤」）：读与写之间 run 被一次不加写入序号的写结束、或 STATE
  在没有写入序号的记录上被删去，序号的条件仍成立，只有这一项挡下；三个整体替换入口都不写成、不建出 STATE。
- 不是条件不成立的错误（如超出单条记录的大小上限）原样抛出，不重读、不等待；读到的写入序号不是整数（含 null）按读不出抛错、不写。
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


def _record(table, monkeypatch, *, before_write=(), snapshots=None):
    """包住被测表对象的 get_item 与 update_item，依次记下 `read`、`write-ok`、`write-hwm`、`write-rejected`：写成的投影标量一步（更新
    表达式不涉及 jobs，只写 HWM）记为 `write-hwm`，其余写成的写记为 `write-ok`。`before_write` 里的动作按序在被测方前几次
    update_item 发出之前各执行一次（记为 `other`），也就是插在被测方读到 STATE 与它的写之间。给出 snapshots 列表时，每一次写另记下
    （请求参数, 写之前的 STATE, 写之后的 STATE），被条件挡下的写的「写之后」为 None；前后两次读不经包装、不进记录。返回记录列表。"""
    ccf = table.meta.client.exceptions.ConditionalCheckFailedException
    log: list[str] = []
    pending = list(before_write)
    real_get, real_update = table.get_item, table.update_item

    def get_item(**kwargs):
        log.append("read")
        return real_get(**kwargs)

    def raw_state(key):
        return real_get(Key=key, ConsistentRead=True).get("Item")

    def update_item(**kwargs):
        if pending:
            pending.pop(0)()
            log.append("other")
        before = raw_state(kwargs["Key"]) if snapshots is not None else None
        try:
            resp = real_update(**kwargs)
        except ccf:
            log.append("write-rejected")
            if snapshots is not None:
                snapshots.append((kwargs, before, None))
            raise
        log.append("write-ok" if "jobs" in kwargs["UpdateExpression"] else "write-hwm")
        if snapshots is not None:
            snapshots.append((kwargs, before, raw_state(kwargs["Key"])))
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


def _project(store, meta):
    projected = RunState(run_id=meta.run_id, status=Status.RUNNING, high_water_mark=2, jobs={
        "a": JobState("a", Status.RUNNING, session_id="sess-a"), "b": JobState("b", Status.PASSED),
        "c": JobState("c", Status.PENDING)})
    assert store.project_state(meta.run_id, projected) is True  # 标量一步加 a、b 各一次逐 job 写，c 跳过


def _commit(store, meta):
    _claim(store, meta)
    assert store.commit_job_states(meta.run_id, [_done("a", Status.PASSED)], ended_at=_ENDED) is CommitOutcome.OPEN


def _end(store, meta):
    _claim(store, meta)
    assert store.end_run(meta.run_id, RUN_ENDINGS["settle-advancer-exited"], ended_at=_ENDED) is True


def _end_as_error(store, meta):
    _claim(store, meta)
    assert store.end_run_as_error(meta.run_id, "提交记录不完整或形态不对", ended_at=_ENDED) is True


@pytest.mark.parametrize("write", [_claim, _job_write, _project, _commit, _end, _end_as_error],
                         ids=["try_claim_job", "update_job_state", "project_state", "commit_job_states", "end_run",
                              "end_run_as_error"])
def test_each_landed_update_increments_the_write_seq_once(table, store, monkeypatch, write):
    """每个写入口之后，写入序号的增量等于这期间写成的、涉及 jobs 的 update_item 请求数：这样的写恰好加一，投影的标量一步写成也不加，
    被条件挡下的写不改它。"""
    meta = _create(store)
    log = _record(table, monkeypatch)
    write(store, meta)
    landed = log.count("write-ok")
    assert landed >= 1, "前提：这个写入口确实写成了"
    assert _seq(table) == landed
    if write is _project:
        assert log.count("write-hwm") == 1, "前提：标量一步写成"


def test_rejected_writes_leave_the_write_seq(table, store):
    """条件不成立的写不改写入序号：认领已不是 pending 的 job、过期的投影，以及 run 已结束之后的执行中的写、终态写与结束写。"""
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
    assert store.update_job_state("run-1", JobState("a", Status.RUNNING, session_id="late")) is False
    assert store.commit_job_states("run-1", [_done("a", Status.PASSED)], ended_at="t2") is CommitOutcome.ALREADY_ENDED
    assert store.end_run("run-1", RUN_ENDINGS["settle-advancer-exited"], ended_at="t2") is False
    assert _seq(table) == seq


def _random_write(rng: random.Random, store, meta: RunMeta, hwm: list[int]) -> None:
    sid = rng.choice([j.scope_id for j in meta.jobs])
    op = rng.randrange(6)
    # 会话与认领时刻取自很小的集合，可缺：库中与投影只差其中一项的情形经常出现
    if op == 0:
        store.try_claim_job(meta.run_id, sid, claimed_at=rng.choice([None, _CLAIMED]))
    elif op == 1:
        store.update_job_state(meta.run_id, JobState(sid, Status.RUNNING, session_id=rng.choice([None, "s1", "s2"]),
                                                     claimed_at=rng.choice([None, _CLAIMED])))
    elif op == 2:
        hwm[0] += rng.choice([-1, 0, 1])  # 含过期的投影（被条件挡下）
        statuses = {j.scope_id: rng.choice([Status.PENDING, Status.RUNNING, *_TERMINAL]) for j in meta.jobs}
        # 内容与库中相同、因而不写的投影逐 job 写同样经常出现
        store.project_state(meta.run_id, RunState(run_id=meta.run_id, status=Status.RUNNING, high_water_mark=hwm[0], jobs={
            s: JobState(s, st, session_id=rng.choice([None, "s1", "s2"]), claimed_at=rng.choice([None, _CLAIMED]))
            for s, st in statuses.items()}))
    elif op == 3:
        store.commit_job_states(meta.run_id, [_done(sid, rng.choice(_TERMINAL))], ended_at=_ENDED)
    elif op == 4:
        store.end_run(meta.run_id, RUN_ENDINGS[rng.choice(list(RUN_ENDINGS))], ended_at=_ENDED)
    elif rng.random() < 0.3:  # error 变体使 run 立即结束，少用一些，让序列更长地停在未结束
        store.end_run_as_error(meta.run_id, "提交记录不完整或形态不对", ended_at=_ENDED)


def _projection_job_write_blocked(request: dict, before: dict) -> bool:
    """按写那一刻库中的 STATE，投影的一次逐 job 写的条件是否不成立（ADR 0034 机制三「② 的 job 级半边落地形态」段的四项，与 adapter
    的条件表达式各自独立写出）：库中 HWM 大于这次投影的、run 已结束、这个 job 不在 Map 里或比投影更推进，或这次写提及的字段都与库中
    相同。"""
    values = request["ExpressionAttributeValues"]
    entry = before["jobs"].get(request["ExpressionAttributeNames"]["#sid"])
    stored_hwm = before.get("high_water_mark")
    if stored_hwm is not None and stored_hwm > values[":h"]:
        return True
    if before["status"] not in ("pending", "running") or entry is None:
        return True
    if entry["status"] not in (("pending", "running") if values[":st"] == "running" else ("pending",)):
        return True
    mentioned = [("status", ":st"), ("session_id", ":sess"), ("claimed_at", ":cat")]
    return all(entry.get(attr) == values[value] for attr, value in mentioned if value in values)


def test_write_seq_counts_every_landed_update_of_a_random_sequence(table, store, monkeypatch):
    """经任意写序列（认领、执行中的 job 写、含过期与内容不变的投影、终态写、各条来路的结束写与 error 变体），每次写之后写入序号都等于
    至此写成的、涉及 jobs 的 update_item 请求数；逐条看写成的写：改变了 jobs 或 run 状态的写都恰好加一，投影的标量一步不加、也不改变
    它们，写成的投影逐 job 写都改变了 jobs（内容与库中相同的不写）。投影的每一次逐 job 写，写成与否都与按写那一刻库中的值独立判断的
    条件相符：被挡下的必有一项条件不成立（库中更推进、HWM 更高、run 已结束、job 不在，或提及的字段都与库中相同），写成的四项都成立。
    种子固定，失败可复现。"""
    rng = random.Random(20261119)
    snapshots: list = []
    log = _record(table, monkeypatch, snapshots=snapshots)
    for n in range(30):
        meta = _create(store, run_id=f"run-{n:02d}")
        log.clear()
        hwm = [0]
        for _ in range(12):
            snapshots.clear()
            _random_write(rng, store, meta, hwm)
            assert _seq(table, meta.run_id) == log.count("write-ok"), log
            for request, before, after in snapshots:
                projection_job_write = ":st" in request["ExpressionAttributeValues"]
                if after is None:  # 被条件挡下的写
                    if projection_job_write:
                        assert _projection_job_write_blocked(request, before), (request, before)
                    continue
                changed = before["jobs"] != after["jobs"] or before["status"] != after["status"]
                delta = after.get("write_seq", 0) - before.get("write_seq", 0)
                if "jobs" not in request["UpdateExpression"]:  # 投影的标量一步
                    assert (delta, changed) == (0, False), request
                    continue
                assert delta == 1, request
                if projection_job_write:
                    assert changed and not _projection_job_write_blocked(request, before), (request, before)


# ---------- 投影的逐 job 写：内容与库中相同不写（ADR 0034 机制三「逐 job 写：内容不变不写，注定不成立的不发」段）----------

def test_projection_matching_the_stored_jobs_writes_no_job_and_leaves_the_write_seq(table, store, monkeypatch):
    """投影里执行中的 a 与库中逐字段相同（状态、会话、认领时刻），已有结果的 b 在库中是同一会话的 running（投影按 running 写）：只有
    标量一步写成、推进 HWM，两次逐 job 写都被「至少一项不同」的条件挡下，写入序号不变。c 是无效果的 pending 项，不发写。"""
    meta = _create(store)
    for sid in ("a", "b"):
        assert store.try_claim_job("run-1", sid, claimed_at=_CLAIMED) is True
        assert store.update_job_state("run-1", JobState(sid, Status.RUNNING, session_id=f"sess-{sid}",
                                                        claimed_at=_CLAIMED)) is True
    seq, before = _seq(table), _raw(table)["jobs"]
    log = _record(table, monkeypatch)
    projected = RunState(run_id=meta.run_id, status=Status.RUNNING, high_water_mark=2, jobs={
        "a": JobState("a", Status.RUNNING, session_id="sess-a", claimed_at=_CLAIMED),
        "b": JobState("b", Status.PASSED, session_id="sess-b"), "c": JobState("c", Status.PENDING)})

    assert store.project_state("run-1", projected) is True

    assert log == ["write-hwm", "write-rejected", "write-rejected"]
    assert _seq(table) == seq
    assert (_raw(table)["jobs"], _raw(table)["high_water_mark"]) == (before, 2)


@pytest.mark.parametrize("stored, missing", [
    ({}, "both"), ({"session_id": "sess-a"}, "claim time"), ({"claimed_at": _CLAIMED}, "session"),
], ids=["both-missing", "claim-time-missing", "session-missing"])
def test_projection_bringing_a_missing_session_or_claim_time_lands_once_then_not_again(table, store, monkeypatch, stored,
                                                                                       missing):
    """库中执行中的 a 缺会话、缺认领时刻或两者都缺，投影带上两者（缺失的那一项与库中不同，用显式的「属性不存在」判断）：逐 job 写写成、
    写入序号加一；同一份投影再发一遍，内容已与库中相同，逐 job 写被挡下、序号不变。"""
    _create(store, ("a",))
    assert store.try_claim_job("run-1", "a", claimed_at=stored.get("claimed_at")) is True
    if "session_id" in stored:
        table.update_item(Key={"run_id": "run-1", "item_type": "STATE"}, UpdateExpression="SET jobs.a.session_id = :s",
                          ExpressionAttributeValues={":s": stored["session_id"]})
    assert {k for k in ("session_id", "claimed_at") if k in _raw(table)["jobs"]["a"]} == set(stored), f"前提：缺 {missing}"
    seq = _seq(table)
    log = _record(table, monkeypatch)
    projected = RunState(run_id="run-1", status=Status.RUNNING, high_water_mark=1,
                         jobs={"a": JobState("a", Status.RUNNING, session_id="sess-a", claimed_at=_CLAIMED)})

    assert store.project_state("run-1", projected) is True
    assert log == ["write-hwm", "write-ok"] and _seq(table) == seq + 1
    assert store.load_run_state("run-1").jobs["a"] == JobState("a", Status.RUNNING, session_id="sess-a", claimed_at=_CLAIMED)

    log.clear()
    assert store.project_state("run-1", projected) is True
    assert log == ["write-hwm", "write-rejected"] and _seq(table) == seq + 1


def test_commit_lands_although_an_unchanged_projection_lands_before_each_of_its_writes(table, store, other, monkeypatch):
    """两线程反例的固定交错（ADR 0034 机制三「逐 job 写：内容不变不写」段「费用与竞争」条）：12 个 job 的 run 上全部 job 都在执行、
    带着各自的会话与认领时刻；终态写每次读到运行态之后、发出整体替换之前，另一方都落下一次内容不变的投影。投影只推进 HWM、逐 job 写都
    不写，写入序号不变，终态写第一次就写成，不再被挤去重读、不抛 RunStateWriteContended。"""
    from gherkai_core.adapters.run_store import ddb
    monkeypatch.setattr(ddb.time, "sleep", lambda _s: None)
    scope_ids = tuple(f"j{i:02d}" for i in range(12))
    _create(store, scope_ids)
    for sid in scope_ids:
        assert store.try_claim_job("run-1", sid, claimed_at=_CLAIMED) is True
        assert store.update_job_state("run-1", JobState(sid, Status.RUNNING, session_id=f"s-{sid}",
                                                        claimed_at=_CLAIMED)) is True
    unchanged = RunState(run_id="run-1", status=Status.RUNNING, high_water_mark=0, jobs={
        sid: JobState(sid, Status.RUNNING, session_id=f"s-{sid}", claimed_at=_CLAIMED) for sid in scope_ids})
    log = _record(table, monkeypatch, before_write=[
        lambda: other.project_state("run-1", unchanged)] * (ddb._REPLACE_MAX_RETRIES + 1))

    assert store.commit_job_states("run-1", [_done("j00", Status.PASSED, session="s-j00")],
                                   ended_at=_ENDED) is CommitOutcome.OPEN

    assert log == ["read", "other", "write-ok"]
    assert store.load_run_state("run-1").jobs["j00"].status == Status.PASSED


def test_projection_scalar_step_request_carries_no_write_seq(table, store, monkeypatch):
    """投影的标量一步只写 HWM：请求里没有写入序号的占位名与占位值；逐 job 写的请求带上它。"""
    meta = _create(store, ("a",))
    calls: list[dict] = []
    real = table.update_item
    monkeypatch.setattr(table, "update_item", lambda **kw: (calls.append(kw), real(**kw))[1])
    projected = RunState(run_id=meta.run_id, status=Status.RUNNING, high_water_mark=1,
                         jobs={"a": JobState("a", Status.RUNNING, session_id="sess-a")})
    assert store.project_state("run-1", projected) is True
    scalar, job = calls
    assert "write_seq" not in (scalar.get("ExpressionAttributeNames") or {}).values()
    assert not {":ws0", ":ws1"} & set(scalar["ExpressionAttributeValues"])
    assert scalar["UpdateExpression"].replace(" ", "") == "SEThigh_water_mark=:h"
    assert "write_seq" in job["ExpressionAttributeNames"].values()


# ---------- 执行中的写：逐属性写模型里的键（ADR 0030 决定四「改写运行态时原样保留不认识的部分」条）----------

def test_job_write_sets_model_keys_one_by_one_and_leaves_unknown_attributes(table, store):
    """执行中的写在 DynamoDB 上逐属性写条目里的模型键：这次有值的写下，这次没有值的删去（认领写下的认领时刻、条目里一句本不该在执行中
    的 job 上出现的说明都不在了，与本机整项替换模型键的结果相同），别的写方写下、本版本不认识的属性原样保留。"""
    _create(store, ("a",))
    assert store.try_claim_job("run-1", "a", claimed_at=_CLAIMED) is True
    table.update_item(Key={"run_id": "run-1", "item_type": "STATE"},
                      UpdateExpression="SET jobs.a.future_note = :f, jobs.a.#m = :m",
                      ExpressionAttributeNames={"#m": "message"},
                      ExpressionAttributeValues={":f": {"origin": "future-writer"}, ":m": "stale"})

    assert store.update_job_state("run-1", JobState("a", Status.RUNNING, session_id="sess-a")) is True

    assert _raw(table)["jobs"]["a"] == {"status": "running", "session_id": "sess-a", "future_note": {"origin": "future-writer"}}


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
    """`update_job_state` 被挡下时不另读、不再写：run 未结束而 a 已是终态、或 job 不在 Map 里时只有被挡下的那一次写，记录不变、返回
    True；run 已结束时（执行中的 b 由结束写记 aborted，a 由终态写结束）同样只有被挡下的那一次写，记录不变、返回 False：这两个 job
    都已是终态，返回值取的是带回条目里的 run 级状态。"""
    meta = _create(store, ("a", "b"))
    _claim(store, meta)
    assert store.try_claim_job("run-1", "b", claimed_at=_CLAIMED) is True
    assert store.commit_job_states("run-1", [_done("a", Status.PASSED)], ended_at="never") is CommitOutcome.OPEN
    log = _record(table, monkeypatch)

    assert store.update_job_state("run-1", JobState("a", Status.RUNNING, session_id="late")) is True
    assert log == ["write-rejected"]
    assert store.load_run_state("run-1").jobs["a"] == _done("a", Status.PASSED)
    log.clear()
    assert store.update_job_state("run-1", JobState("ghost", Status.RUNNING)) is True
    assert log == ["write-rejected"]
    assert set(store.load_run_state("run-1").jobs) == {"a", "b"}

    assert store.end_run("run-1", RUN_ENDINGS["settle-advancer-exited"], ended_at=_ENDED) is True
    before = store.load_run_state("run-1")
    for js in (JobState("b", Status.RUNNING, session_id="sess-b"), JobState("a", Status.RUNNING)):
        log.clear()
        assert store.update_job_state("run-1", js) is False
        assert log == ["write-rejected"]
    assert store.load_run_state("run-1") == before
    assert (before.status, before.jobs["a"], before.jobs["b"].status) == (
        Status.ABORTED, _done("a", Status.PASSED), Status.ABORTED)


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


_REPLACING_ENTRIES = ["commit_job_states", "end_run", "end_run_as_error"]  # 整体替换 jobs 的三个写入口


def _replace_via(store, entry: str):
    """以一组没有并发的写时会写成的参数调用一个整体替换入口（前提：a 已被认领），返回它的返回值。"""
    if entry == "commit_job_states":
        return store.commit_job_states("run-1", [_done("a", Status.PASSED)], ended_at=_ENDED)
    if entry == "end_run":
        return store.end_run("run-1", RUN_ENDINGS["settle-advancer-exited"], ended_at=_ENDED)
    return store.end_run_as_error("run-1", "提交记录不完整或形态不对", ended_at=_ENDED)


@pytest.fixture
def raw_table(aws):
    """直接改库用的表对象：不是被测方的那一个，包住被测表对象的方法不影响它。"""
    return aws["ddb"].Table(aws["table_name"])


_STATE_KEY = {"run_id": "run-1", "item_type": "STATE"}


@pytest.mark.parametrize("entry", _REPLACING_ENTRIES)
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
        _replace_via(store, entry)

    assert raised.value.attempts == attempts and raised.value.run_id == "run-1"
    assert log.count("write-rejected") == attempts and "write-ok" not in log
    assert len(sleeps) == attempts - 1
    got = store.load_run_state("run-1")
    assert (got.status, got.jobs["a"].status) == (Status.RUNNING, Status.RUNNING)
    assert got.jobs["c"] == JobState("c", Status.RUNNING, session_id=f"s{attempts - 1}")


# ---------- 整体替换的条件里「run 未结束」一项（ADR 0030 决定六「两个写入口的步骤」）----------

_NOT_WRITTEN = {"commit_job_states": CommitOutcome.ALREADY_ENDED, "end_run": False, "end_run_as_error": False}


@pytest.mark.parametrize("entry", _REPLACING_ENTRIES)
@pytest.mark.parametrize("has_write_seq", [True, False], ids=["write-seq", "no-write-seq"])
def test_a_run_ended_without_a_write_seq_increment_between_read_and_write_is_not_rewritten(
        table, store, raw_table, monkeypatch, entry, has_write_seq):
    """被测方读到 run 未结束之后，另一个写方使 run 成为终态而没有把写入序号加一（不守序号约定的写方，例如早于写入序号的版本；记录也
    可以本来就没有这个属性）：序号的条件此时仍成立，挡下被测写的只有「run 未结束」一项，它让终态不可变不只靠每一次写都加了序号。三个
    整体替换入口都被挡下、重读到 run 已结束即不再写，记录逐项是对方写下的终态。"""
    meta = _create(store)
    _claim(store, meta)
    if not has_write_seq:
        raw_table.update_item(Key=_STATE_KEY, UpdateExpression="REMOVE write_seq")
    written: list[dict] = []

    def end_without_increment():
        raw_table.update_item(
            Key=_STATE_KEY,
            UpdateExpression=("SET #st = :x, status_group = :x, ended_at = :e, #m = :m, "
                              "jobs.a.#st = :x, jobs.b.#st = :x, jobs.c.#st = :x"),
            ExpressionAttributeNames={"#st": "status", "#m": "message"},
            ExpressionAttributeValues={":x": "aborted", ":e": "t-other", ":m": "别的写方的结束"})
        written.append(raw_table.get_item(Key=_STATE_KEY, ConsistentRead=True)["Item"])

    log = _record(table, monkeypatch, before_write=[end_without_increment])

    assert _replace_via(store, entry) == _NOT_WRITTEN[entry]

    assert log == ["read", "other", "write-rejected", "read"]
    assert written[0].get("write_seq") == (1 if has_write_seq else None), "前提：对方的写没有改写入序号"
    assert _raw(table) == written[0]


@pytest.mark.parametrize("entry", _REPLACING_ENTRIES)
def test_a_state_deleted_between_read_and_write_is_not_recreated(table, store, raw_table, monkeypatch, entry):
    """没有写入序号的记录（早于这个属性写出的记录只能这样构造），STATE 在被测方的读与写之间被删去：「仍没有这个属性」在不存在的条目上
    也成立，挡下这次写的只有「run 未结束」一项（STATE 已不在时它同样不成立）。三个入口都不建出 STATE：重读不到，终态写抛
    FileNotFoundError，两个结束写返回 False。"""
    meta = _create(store)
    _claim(store, meta)
    raw_table.update_item(Key=_STATE_KEY, UpdateExpression="REMOVE write_seq")
    log = _record(table, monkeypatch, before_write=[lambda: raw_table.delete_item(Key=_STATE_KEY)])

    if entry == "commit_job_states":
        with pytest.raises(FileNotFoundError):
            _replace_via(store, entry)
    else:
        assert _replace_via(store, entry) is False

    assert log == ["read", "other", "write-rejected", "read"]
    assert "Item" not in raw_table.get_item(Key=_STATE_KEY, ConsistentRead=True)


# ---------- 别的错误与读不出的写入序号 ----------

@pytest.mark.parametrize("entry", _REPLACING_ENTRIES)
def test_an_error_other_than_a_failed_condition_is_raised_without_rereading(table, store, monkeypatch, entry):
    """整体替换遇到不是条件不成立的错误（这里是真实的表在条目超出单条记录的大小上限时给出的 ValidationException；moto 对
    update_item 的大小核法与真实的表不同，见 core/tests/README.md，这里用替身造出这个错误）：原样抛出，只写一次、不重读、不等待，不当作写入竞争，记录不变（ADR 0034 机制三②「条目
    大小」）。当作竞争会重读到次数用尽、报成写入竞争，而这次写永远写不成。"""
    from botocore.exceptions import ClientError

    from gherkai_core.adapters.run_store import ddb
    sleeps: list[float] = []
    monkeypatch.setattr(ddb.time, "sleep", sleeps.append)
    meta = _create(store)
    _claim(store, meta)
    before = _raw(table)
    too_large = ClientError({"Error": {"Code": "ValidationException",
                                       "Message": "Item size has exceeded the maximum allowed size"}}, "UpdateItem")
    calls: list[dict] = []

    def update_item(**kwargs):
        calls.append(kwargs)
        raise too_large

    monkeypatch.setattr(table, "update_item", update_item)

    with pytest.raises(ClientError) as raised:
        _replace_via(store, entry)

    assert raised.value is too_large
    assert len(calls) == 1 and sleeps == []
    assert _raw(table) == before


@pytest.mark.parametrize("entry", _REPLACING_ENTRIES)
@pytest.mark.parametrize("value", [None, "seven"], ids=["null", "not-a-number"])
def test_a_write_seq_that_is_not_an_integer_raises_unreadable_without_writing(table, store, monkeypatch, entry, value):
    """读到的写入序号在而不是整数（含值为 null：它不按缺属性处理）：三个整体替换入口都抛 RunStateUnreadable（ValueError 的子类，落在
    读不出的口径之内），只读一次、不发写，记录不变。按缺属性处理时，「仍没有这个属性」的条件对它永不成立，会重读到次数用尽、把读不出的
    记录报成写入竞争。"""
    from gherkai_core.adapters.run_store.ddb import RunStateUnreadable
    from gherkai_core.serialize import UNREADABLE_RECORD_ERRORS

    meta = _create(store)
    _claim(store, meta)
    table.update_item(Key=_STATE_KEY, UpdateExpression="SET write_seq = :v", ExpressionAttributeValues={":v": value})
    before = _raw(table)
    log = _record(table, monkeypatch)

    with pytest.raises(RunStateUnreadable) as raised:
        _replace_via(store, entry)

    assert isinstance(raised.value, UNREADABLE_RECORD_ERRORS)
    assert log == ["read"]
    assert _raw(table) == before


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
