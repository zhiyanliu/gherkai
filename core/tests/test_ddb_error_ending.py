"""DynamoDBRunStore 上结束写的 error 变体 `end_run_as_error`（ADR 0030 决定四「error 变体是另一个写入口」条、决定六「两个写入口的
步骤」，ADR 0031 决定三「结束写」小节「运行定义不可用、或 run 由别的格式写出时」条）。

它只在 DDB adapter 上、不在 RunStore 端口上，不参与两端对拍，所以只有 moto 一侧：
- 写下什么：pending 与 running 的条目 status 记 error、message 记原因（条目里已有的说明被原因替换），条目里其余属性（含本版本不认识
  的）与已结束的条目原样复制；run 级 status 与状态分组记 error，结束时刻与 run 级说明取调用方给的值，写入序号加一；STATE 的其余属性
  不变。
- 不按本格式的模型读：本版本的模型读不了的其余属性（形态不对的认领计数与 HWM）不妨碍它写成。
- 返回与读不出：STATE 不存在、run 已结束返回 False、不写；公共部分读不出抛 RunStateUnreadable、不写。
- 先后：读与写之间别的写方落下改变了内容的写，被写入序号的条件挡下、重读再算；重读到 run 已结束即返回 False，记录保持对方的结果。
  先后靠包住被测表对象的 update_item 固定，不靠线程竞争。
与另两个整体替换 jobs 的写入口共有的性质在 test_ddb_write_seq.py 里对三者参数化：重读的次数用尽抛 RunStateWriteContended；条件里
「run 未结束」一项单独挡下的两种先后（读与写之间 run 被不加写入序号的写结束、STATE 被删去）；不是条件不成立的错误原样抛出、不重读。
状态分组随它的变化另见 test_status_group.py。moto 的条件表达式是模拟实现，真实的表上的核对见 test_cloud_integration.py 的集成用例与
ADR 0054 实测项 21、23。
"""
from __future__ import annotations

from decimal import Decimal

import pytest

from gherkai_core.model import Job, JobState, RunMeta, RunState, Scenario, Status, Step
from gherkai_core.run_status import RUN_ENDINGS, CommitOutcome
from tests.conftest import jobs_objects_for

_T0 = "2026-11-25T00:00:00Z"
_CLAIMED = "2026-11-25T00:01:00Z"
_ENDED = "2026-11-25T02:00:00Z"
_REASON = "提交记录不完整或形态不对，后端不能执行它；请用与后端同版本的 gherkai 重新提交"


def _meta(run_id: str, scope_ids: tuple[str, ...]) -> RunMeta:
    jobs = tuple(
        Job(scope_id=s, scope_name=s, engine="novaact", timeout_s=300.0,
            scenarios=(Scenario(id=f"{s}:1", name="s", steps=(Step(index=0, keyword="Given", text="x"),)),))
        for s in scope_ids)
    return RunMeta(run_id=run_id, created_at=_T0, jobs=jobs, deadline_at="2026-11-25T01:00:00+00:00",
                   worker_task_defs={"novaact": "arn:aws:ecs:us-east-1:111122223333:task-definition/w:1"})


def _create(store, scope_ids=("a", "b", "c"), *, run_id="run-1") -> None:
    store.create_run(_meta(run_id, scope_ids), RunState(
        run_id=run_id, status=Status.PENDING, started_at=_T0, high_water_mark=3,
        jobs={s: JobState(s, Status.PENDING) for s in scope_ids}))


@pytest.fixture
def table(aws):
    return aws["ddb"].Table(aws["table_name"])


@pytest.fixture
def store(table, jobs_objects):
    from gherkai_core.adapters.run_store.ddb import DynamoDBRunStore
    return DynamoDBRunStore(table, jobs_objects=jobs_objects)


@pytest.fixture
def other(aws):
    """另一个写入方：持自己的表对象，包住被测表对象的方法不影响它的写。"""
    from gherkai_core.adapters.run_store.ddb import DynamoDBRunStore
    return DynamoDBRunStore(aws["ddb"].Table(aws["table_name"]), jobs_objects=jobs_objects_for(aws))


def _key(run_id="run-1") -> dict:
    return {"run_id": run_id, "item_type": "STATE"}


def _raw(table, run_id="run-1") -> dict:
    return table.get_item(Key=_key(run_id), ConsistentRead=True)["Item"]


def _set(table, expression: str, values: dict, names: dict | None = None) -> None:
    """直接改 STATE item：别的写方写下、本版本不认识或读不了的属性只能这样造。"""
    table.update_item(Key=_key(), UpdateExpression=expression, ExpressionAttributeValues=values,
                      **({"ExpressionAttributeNames": names} if names else {}))


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


# ---------- 写下什么 ----------

def test_unfinished_entries_become_error_and_everything_else_is_copied(table, store, monkeypatch):
    """a 没有启动（pending）、b 在执行（running，带会话与认领时刻，另带一句别的写方写下的说明）、c 已由终态写结束并点名明细：a 与 b
    记 error、带原因（b 原有的说明被原因替换），b 的会话与认领时刻、两个条目里本版本不认识的属性都原样在；c 的整个条目原样。run 级记
    error（状态分组同为 error），结束时刻与说明取给的值，写入序号加一；开始时刻、HWM、认领计数、顶层附加属性不变。没有并发的写时只读
    一次、写一次。"""
    _create(store)
    for sid in ("b", "c"):
        assert store.try_claim_job("run-1", sid, claimed_at=_CLAIMED) is True
    assert store.update_job_state("run-1", JobState("b", Status.RUNNING, session_id="sess-b", claimed_at=_CLAIMED)) is True
    assert store.commit_job_states("run-1", [JobState("c", Status.PASSED, session_id="sess-c", claimed_at=_CLAIMED,
                                                      result_id="0123456789abcdef")], ended_at="never") is CommitOutcome.OPEN
    # job 级说明属运行态的公共部分，别的格式写出的执行中条目可能带它；本版本经端口写不出，只能直接改库
    _set(table, "SET jobs.a.future_note = :f, jobs.b.future_note = :f, jobs.c.future_note = :f, launcher = :l, jobs.b.#m = :m",
         {":f": {"origin": "future-writer", "n": 3}, ":l": {"pid": 4242}, ":m": "别的写方写下的说明"}, {"#m": "message"})
    assert _raw(table)["jobs"]["b"]["message"] == "别的写方写下的说明", "前提：执行中的 b 带一句说明"
    before = _raw(table)
    log = _record(table, monkeypatch)

    assert store.end_run_as_error("run-1", _REASON, ended_at=_ENDED) is True

    assert log == ["read", "write-ok"]
    after = _raw(table)
    note = {"origin": "future-writer", "n": Decimal(3)}
    assert after["jobs"]["a"] == {"status": "error", "message": _REASON, "future_note": note}
    assert after["jobs"]["b"] == {"status": "error", "message": _REASON, "session_id": "sess-b", "claimed_at": _CLAIMED,
                                  "future_note": note}
    assert after["jobs"]["c"] == before["jobs"]["c"]
    assert (after["status"], after["status_group"], after["ended_at"], after["message"]) == ("error", "error", _ENDED, _REASON)
    assert after["write_seq"] == before["write_seq"] + 1
    changed = {k for k in before.keys() | after.keys() if before.get(k) != after.get(k)}
    assert changed == {"jobs", "status", "status_group", "ended_at", "message", "write_seq"}


def test_attributes_the_model_cannot_read_do_not_stop_it(table, store):
    """本版本的模型读不了的记录（认领计数与 HWM 不是数，按模型读运行态即失败）：error 变体只读公共部分，照样写成，那两个属性原样留下。
    这正是它能结束别的格式写出的 run 的前提。"""
    _create(store, ("a",))
    _set(table, "SET claim_count = :c, high_water_mark = :h", {":c": "many", ":h": "x"})
    with pytest.raises(ValueError):
        store.load_run_state("run-1")  # 前提：按本格式的模型读不了

    assert store.end_run_as_error("run-1", _REASON, ended_at=_ENDED) is True

    after = _raw(table)
    assert (after["status"], after["jobs"]["a"]["status"]) == ("error", "error")
    assert (after["claim_count"], after["high_water_mark"]) == ("many", "x")


def test_a_record_without_status_group_or_write_seq_is_still_ended(table, store):
    """缺状态分组与写入序号的记录（早于这两项写出的记录只能这样构造）：缺状态分组不算读不出，写入序号按「仍没有这个属性」为条件；写成
    之后两项都补上（分组为 error，序号从 0 起算得 1）。"""
    _create(store, ("a",))
    table.update_item(Key=_key(), UpdateExpression="REMOVE status_group, write_seq")
    assert "status_group" not in _raw(table) and "write_seq" not in _raw(table)

    assert store.end_run_as_error("run-1", _REASON, ended_at=_ENDED) is True

    after = _raw(table)
    assert (after["status"], after["status_group"], after["write_seq"]) == ("error", "error", 1)


def test_the_status_values_of_the_common_part_are_the_seven_fixed_ones():
    """error 变体按运行态公共部分里状态的七个取值读 STATE（ADR 0037 决策 7「运行态的公共部分」：取值集合固定，pending 与 running 表示
    未结束），不随模型变化。"""
    from gherkai_core.adapters.run_store import ddb

    assert ddb._STATUS_VALUES == {"pending", "running", "passed", "failed", "error", "aborted", "skipped"}
    assert ddb._OPEN_STATUS_VALUES == {"pending", "running"}


# ---------- 返回与读不出 ----------

def test_a_missing_state_returns_false_and_writes_nothing(table, store, monkeypatch):
    """STATE 不存在：返回 False，只读一次、不发写，什么都没有建出。"""
    log = _record(table, monkeypatch)
    assert store.end_run_as_error("nope", _REASON, ended_at=_ENDED) is False
    assert log == ["read"]
    assert "Item" not in table.get_item(Key=_key("nope"), ConsistentRead=True)


@pytest.mark.parametrize("ended_by", ["commit", "end_run", "end_run_as_error"])
def test_an_ended_run_returns_false_and_keeps_its_record(table, store, monkeypatch, ended_by):
    """run 已结束（由终态写、按模型算出的结束写或另一次 error 变体）：返回 False，只读一次、不发写，记录不变。"""
    _create(store, ("a",))
    assert store.try_claim_job("run-1", "a", claimed_at=_CLAIMED) is True
    if ended_by == "commit":
        assert store.commit_job_states("run-1", [JobState("a", Status.PASSED)], ended_at="t1") is CommitOutcome.ENDED_RUN
    elif ended_by == "end_run":
        assert store.end_run("run-1", RUN_ENDINGS["settle-advancer-exited"], ended_at="t1") is True
    else:
        assert store.end_run_as_error("run-1", "第一句", ended_at="t1") is True
    before = _raw(table)
    log = _record(table, monkeypatch)

    assert store.end_run_as_error("run-1", _REASON, ended_at=_ENDED) is False

    assert log == ["read"]
    assert _raw(table) == before


@pytest.mark.parametrize("expression, values, names", [
    ("REMOVE #st", {}, {"#st": "status"}),
    ("SET #st = :v", {":v": "PENDING"}, {"#st": "status"}),
    ("SET #st = :v", {":v": 1}, {"#st": "status"}),
    ("SET jobs = :v", {":v": ["a"]}, None),
    ("REMOVE jobs", {}, None),
    ("SET jobs.a.#st = :v", {":v": "queued"}, {"#st": "status"}),
    ("REMOVE jobs.a.#st", {}, {"#st": "status"}),
    ("SET jobs.b = :v", {":v": "not-a-map"}, None),
    ("SET write_seq = :v", {":v": "seven"}, None),
    ("SET write_seq = :v", {":v": Decimal("1.5")}, None),
    ("SET write_seq = :v", {":v": None}, None),
], ids=["run-status-missing", "run-status-unknown", "run-status-not-a-string", "jobs-not-a-map", "jobs-missing",
        "job-status-unknown", "job-status-missing", "entry-not-a-map", "write-seq-not-a-number", "write-seq-fraction",
        "write-seq-null"])
def test_an_unreadable_common_part_raises_without_writing(table, store, monkeypatch, expression, values, names):
    """公共部分读不出（run 级状态缺失或不是七个取值之一、jobs 不是 Map、条目不是 Map 或它的状态读不出、写入序号不是整数，含属性在而
    值为 null：它不按缺属性处理，否则「仍没有这个属性」的条件永不成立、重读到次数用尽）：抛 RunStateUnreadable（ValueError 的子类，
    调用方按闸里的读不出处理），只读一次、不发写，记录不变。"""
    from gherkai_core.adapters.run_store.ddb import RunStateUnreadable
    from gherkai_core.serialize import UNREADABLE_RECORD_ERRORS

    _create(store, ("a", "b"))
    table.update_item(Key=_key(), UpdateExpression=expression,
                      **({"ExpressionAttributeValues": values} if values else {}),
                      **({"ExpressionAttributeNames": names} if names else {}))
    before = _raw(table)
    log = _record(table, monkeypatch)

    with pytest.raises(RunStateUnreadable) as raised:
        store.end_run_as_error("run-1", _REASON, ended_at=_ENDED)

    assert isinstance(raised.value, UNREADABLE_RECORD_ERRORS)
    assert raised.value.run_id == "run-1"
    assert log == ["read"]
    assert _raw(table) == before


# ---------- 读与写之间插入另一方的写 ----------

def test_a_claim_between_its_read_and_write_is_reread_and_the_claimed_job_ends_as_error(table, store, other, monkeypatch):
    """error 变体读到 b 仍 pending 之后另一方认领 b：被写入序号的条件挡下，重读之后再写，b 按重读到的 running 记 error，认领时刻与认领
    计数留下。"""
    _create(store, ("a", "b"))
    log = _record(table, monkeypatch, before_write=[lambda: other.try_claim_job("run-1", "b", claimed_at=_CLAIMED)])

    assert store.end_run_as_error("run-1", _REASON, ended_at=_ENDED) is True

    assert log == ["read", "other", "write-rejected", "read", "write-ok"]
    got = store.load_run_state("run-1")
    assert got.jobs["b"] == JobState("b", Status.ERROR, claimed_at=_CLAIMED, message=_REASON)
    assert (got.status, got.claim_count) == (Status.ERROR, 1)


def test_a_commit_between_its_read_and_write_keeps_its_terminal_job(table, store, other, monkeypatch):
    """error 变体读到之后，另一方（按这个 run 的格式写它的一方）记下 a 的终态而 run 仍未结束：重读之后再写，a 保持另一方写下的终态与
    点名，只有仍未结束的 b 记 error（ADR 0037 决策 7「与别的写方的先后」）。"""
    _create(store, ("a", "b"))
    assert store.try_claim_job("run-1", "a", claimed_at=_CLAIMED) is True
    committed = JobState("a", Status.PASSED, session_id="sess-a", claimed_at=_CLAIMED, result_id="0123456789abcdef")
    log = _record(table, monkeypatch, before_write=[
        lambda: other.commit_job_states("run-1", [committed], ended_at="t-other")])

    assert store.end_run_as_error("run-1", _REASON, ended_at=_ENDED) is True

    assert log == ["read", "other", "write-rejected", "read", "write-ok"]
    got = store.load_run_state("run-1")
    assert got.jobs["a"] == committed
    assert got.jobs["b"] == JobState("b", Status.ERROR, message=_REASON)
    assert (got.status, got.ended_at, got.message) == (Status.ERROR, _ENDED, _REASON)


def test_a_run_ended_between_its_read_and_write_is_left_as_the_other_side_wrote_it(table, store, other, monkeypatch):
    """error 变体读到之后，另一方以处置的结束写使 run 成为终态：被挡下、重读到已结束，返回 False、不再写，记录是对方写下的。"""
    _create(store, ("a", "b"))
    ended = []

    def settle():
        assert other.end_run("run-1", RUN_ENDINGS["settle-past-deadline"], ended_at="t-settle") is True
        ended.append(other.load_run_state("run-1"))  # 经另一方的表对象读，不进被测方的记录

    log = _record(table, monkeypatch, before_write=[settle])

    assert store.end_run_as_error("run-1", _REASON, ended_at=_ENDED) is False

    assert log == ["read", "other", "write-rejected", "read"]
    assert other.load_run_state("run-1") == ended[0]
    assert (ended[0].status, ended[0].message) == (Status.ABORTED, RUN_ENDINGS["settle-past-deadline"].run_message)


def test_an_unchanged_projection_between_its_read_and_write_does_not_make_it_reread(table, store, other, monkeypatch):
    """读与写之间落下的、内容与库中相同的投影只推进 HWM、不改写入序号：error 变体第一次就写成。"""
    _create(store, ("a",))
    assert store.try_claim_job("run-1", "a", claimed_at=_CLAIMED) is True
    unchanged = RunState(run_id="run-1", status=Status.RUNNING, high_water_mark=3,
                         jobs={"a": JobState("a", Status.RUNNING, claimed_at=_CLAIMED)})
    log = _record(table, monkeypatch, before_write=[lambda: other.project_state("run-1", unchanged)])

    assert store.end_run_as_error("run-1", _REASON, ended_at=_ENDED) is True

    assert log == ["read", "other", "write-ok"]
