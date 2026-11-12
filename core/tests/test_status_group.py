"""DynamoDBRunStore 的状态分组属性（ADR 0030 决定六「runs 表只有一个 GSI」条的写入规则）。

不变量分两半：写 run 级 `status` 的路径在写之后建立 `status_group` 与 `status` 的对应（非终态为 `live`，终态为该终态的
状态值），含 `create_run` 与 `save_run` 传入终态初始状态的情形；不写 run 级 `status` 的路径（全 pending 的投影、只写 job 的
写）保持已有的对应，写之前缺分组属性的记录写之后仍缺。断言直接读 STATE item 的原始属性：分组属性不进 `RunState`，经
`load_run_state` 看不到它。期望值在本文件按上述规则独立写出，不调用被测的派生函数。

本机后端没有索引、不写分组属性，所以这里只有 DynamoDB 一侧。
"""
from __future__ import annotations

import dataclasses
import random

import pytest

from gherkai_core.model import JobState, RunMeta, RunState, Status
from tests.conftest import STATUS_GROUP_INDEX

_TERMINAL = (Status.PASSED, Status.FAILED, Status.ERROR, Status.SKIPPED, Status.ABORTED)
_ARNS = ["arn:aws:ecs:us-east-1:111122223333:task-definition/gherkai-worker-novaact:7"]


def _expected_group(status: str) -> str:
    """规则的独立写法：pending 与 running 归 `live`，其余各自以状态值成组。"""
    return "live" if status in (Status.PENDING.value, Status.RUNNING.value) else status


def _meta(run_id: str = "run-1", *scope_ids: str) -> RunMeta:
    from gherkai_core.model import Job, Scenario, Step
    ids = scope_ids or ("a", "b")
    jobs = tuple(
        Job(scope_id=s, scope_name=s, engine="novaact",
            scenarios=(Scenario(id=f"{s}:1", name="s", steps=(Step(index=0, keyword="Given", text="x"),)),))
        for s in ids
    )
    return RunMeta(run_id=run_id, created_at="2026-11-12T00:00:00Z", jobs=jobs,
                   worker_task_defs={"novaact": _ARNS[0]})


def _initial(meta: RunMeta, status: Status = Status.PENDING) -> RunState:
    return RunState(
        run_id=meta.run_id, status=status,
        jobs={j.scope_id: JobState(scope_id=j.scope_id, status=Status.PENDING) for j in meta.jobs},
        started_at="2026-11-12T00:00:00Z",
    )


def _projection(meta: RunMeta, hwm: int, **job_status: Status) -> RunState:
    """投影：各 job 取给定状态（未给的仍 pending）；run 级值无关紧要，投影写不按它落库。"""
    state = _initial(meta)
    jobs = {sid: dataclasses.replace(js, status=job_status.get(sid, Status.PENDING)) for sid, js in state.jobs.items()}
    return dataclasses.replace(state, jobs=jobs, high_water_mark=hwm)


@pytest.fixture
def table(aws):
    return aws["ddb"].Table(aws["table_name"])


@pytest.fixture
def store(table):
    from gherkai_core.adapters.run_store.ddb import DynamoDBRunStore
    return DynamoDBRunStore(table)


def _raw(table, run_id: str = "run-1") -> dict:
    return table.get_item(Key={"run_id": run_id, "item_type": "STATE"}, ConsistentRead=True)["Item"]


def _assert_corresponds(table, run_id: str = "run-1") -> None:
    item = _raw(table, run_id)
    assert item.get("status_group") == _expected_group(item["status"]), item


def _drop_group(table, run_id: str = "run-1") -> None:
    """造一条缺分组属性的 STATE：早于这一形态写出的记录（ADR 0030 决定六所列的两个来源）只能这样构造。"""
    table.update_item(Key={"run_id": run_id, "item_type": "STATE"}, UpdateExpression="REMOVE status_group")
    assert "status_group" not in _raw(table, run_id)


# ---------- 写 run 级 status 的路径：写之后分组与状态对应 ----------

@pytest.mark.parametrize("status", list(Status))
@pytest.mark.parametrize("method", ["create_run", "save_run"])
def test_create_and_save_derive_group_from_the_initial_status(table, store, method, status):
    """`create_run` 与 `save_run` 按传入初始状态的 `status` 算分组：正常建 run 得 `live`，传入终态得该终态值，不写死 `live`；
    META item 不带分组属性（索引的稀疏由此构造）。"""
    meta = _meta()
    getattr(store, method)(meta, _initial(meta, status))
    assert _raw(table)["status_group"] == _expected_group(status.value)
    meta_item = table.get_item(Key={"run_id": "run-1", "item_type": "META"}, ConsistentRead=True)["Item"]
    assert "status_group" not in meta_item


def _claim(store, meta):
    assert store.try_claim_job(meta.run_id, "a", claimed_at="2026-11-12T00:00:01Z") is True


def _job_write(store, meta):
    store.update_job_state(meta.run_id, JobState(scope_id="a", status=Status.RUNNING, session_id="s-1"))


def _project_running(store, meta):
    assert store.project_state(meta.run_id, _projection(meta, 3, a=Status.RUNNING)) is True


@pytest.mark.parametrize("write", [_claim, _job_write, _project_running], ids=["claim", "job-write", "projection"])
@pytest.mark.parametrize("drop", [False, True], ids=["group-present", "group-missing"])
def test_writes_landing_running_set_live(table, store, write, drop):
    """认领、前台 job 写与把 run 级写成 running 的投影写 `live`。库中已是 `live` 时是同值写；写之前缺分组属性的记录由这次写
    补上（这一情形才能区分「写了分组」与「没碰分组」）。两者落在同一条更新请求里由下面的请求断言守。"""
    meta = _meta()
    store.create_run(meta, _initial(meta))
    if drop:
        _drop_group(table)
    write(store, meta)
    item = _raw(table)
    assert item["status"] == "running" and item["status_group"] == "live"


@pytest.mark.parametrize("status", _TERMINAL)
@pytest.mark.parametrize("drop", [False, True], ids=["group-present", "group-missing"])
def test_terminal_writes_set_the_terminal_group(table, store, status, drop):
    """`try_finalize` 与 `finalize_run` 把分组改为该终态的值（缺分组属性的记录同样补上；与终态落在同一条更新请求里由下面的
    请求断言守）。"""
    for run_id, finalize in (("run-1", store.try_finalize), ("run-2", store.finalize_run)):
        meta = _meta(run_id)
        store.create_run(meta, _initial(meta))
        if drop:
            _drop_group(table, run_id)
        result = finalize(run_id, status, "2026-11-12T01:00:00Z")
        assert result in (True, None)
        assert _raw(table, run_id)["status_group"] == status.value


def _record_updates(table, monkeypatch) -> list[dict]:
    """记下发往表的每条 `update_item` 请求的参数（同 test_conditional_writes 的记录手法），请求照常执行。"""
    calls: list[dict] = []
    real = table.update_item

    def recording(**kwargs):
        calls.append(kwargs)
        return real(**kwargs)

    monkeypatch.setattr(table, "update_item", recording)
    return calls


def _top_level_sets(request: dict) -> dict[str, str]:
    """一条 `update_item` 请求在 item 顶层 SET 的属性 → 写入值（占位名与占位值都已解析；`jobs.<id>.status` 这类嵌套路径
    不算顶层）。本模块的更新表达式只用 SET、各赋值的右侧都是单个占位值，按逗号切分即可。"""
    expr = request["UpdateExpression"].strip()
    assert expr.startswith("SET "), expr
    names = request.get("ExpressionAttributeNames") or {}
    values = request.get("ExpressionAttributeValues") or {}
    out: dict[str, str] = {}
    for part in expr[len("SET "):].split(","):
        target, _, value = (p.strip() for p in part.partition("="))
        if "." not in target:
            out[names.get(target, target)] = values.get(value, value)
    return out


def _try_finalize_failed(store, meta):
    assert store.try_finalize(meta.run_id, Status.FAILED, "2026-11-12T01:00:00Z") is True


def _finalize_run_failed(store, meta):
    store.finalize_run(meta.run_id, Status.FAILED, "2026-11-12T01:00:00Z")


@pytest.mark.parametrize("write, status", [
    (_claim, "running"), (_job_write, "running"), (_project_running, "running"),
    (_try_finalize_failed, "failed"), (_finalize_run_failed, "failed"),
], ids=["claim", "job-write", "projection", "try-finalize", "finalize-run"])
def test_run_status_and_group_are_set_in_the_same_update_request(table, store, monkeypatch, write, status):
    """写 run 级 `status` 的更新路径把分组写在同一条更新请求里：这次写发出的请求中，在顶层写 `status` 或 `status_group` 的
    恰有一条，两者都在其中、取值对应。只看写之后的属性照不出这一点：把一次写拆成先写 `status`、再另发一条写 `status_group`，
    最终属性相同，中间却有一刻两者不对应。"""
    meta = _meta()
    store.create_run(meta, _initial(meta))
    calls = _record_updates(table, monkeypatch)
    write(store, meta)
    touching = [sets for sets in map(_top_level_sets, calls) if {"status", "status_group"} & sets.keys()]
    assert len(touching) == 1, calls
    assert touching[0]["status"] == status and touching[0]["status_group"] == _expected_group(status), touching[0]


def test_finalize_run_overwriting_a_terminal_status_moves_the_group(table, store):
    """`finalize_run` 的条件只要求 STATE 存在，会覆盖已有终态：分组随之换成新终态的值，不留在旧终态的分组里。"""
    meta = _meta()
    store.create_run(meta, _initial(meta))
    store.finalize_run("run-1", Status.PASSED, "2026-11-12T01:00:00Z")
    store.finalize_run("run-1", Status.FAILED, "2026-11-12T01:00:01Z")
    item = _raw(table)
    assert item["status"] == "failed" and item["status_group"] == "failed"


# ---------- 不写 run 级 status 的路径：保持已有的对应 ----------

def _project_all_pending(store, meta):
    assert store.project_state(meta.run_id, _projection(meta, 2)) is True


def _pending_job_write(store, meta):
    store.update_job_state(meta.run_id, JobState(scope_id="b", status=Status.PENDING, session_id="s-2"))


@pytest.mark.parametrize("write", [_project_all_pending, _pending_job_write], ids=["all-pending-projection",
                                                                                   "pending-job-write"])
@pytest.mark.parametrize("drop", [False, True], ids=["group-present", "group-missing"])
def test_writes_not_touching_run_status_leave_the_group(table, store, write, drop):
    """全 pending 的投影只写事件进度、写入 pending 的 job 写只写该 job：两者都不碰分组属性，库中的 `live` 保持，缺的仍缺。"""
    meta = _meta()
    store.create_run(meta, _initial(meta))
    if drop:
        _drop_group(table)
    before = _raw(table)
    write(store, meta)
    after = _raw(table)
    assert after["status"] == before["status"] == "pending"
    assert after.get("status_group") == before.get("status_group")
    assert ("status_group" in after) is (not drop)


@pytest.mark.parametrize("drop", [False, True], ids=["group-present", "group-missing"])
def test_job_write_on_a_finalized_run_leaves_the_group(table, store, drop):
    """已收尾的 run 上前台 job 写的回退写只写 job：run 级与分组都不变，缺的仍缺。"""
    meta = _meta()
    store.create_run(meta, _initial(meta))
    store.finalize_run("run-1", Status.PASSED, "2026-11-12T01:00:00Z")
    if drop:
        _drop_group(table)
    store.update_job_state("run-1", JobState(scope_id="a", status=Status.FAILED, session_id="s-1"))
    item = _raw(table)
    assert item["jobs"]["a"]["status"] == "failed" and item["status"] == "passed"
    assert item.get("status_group") == (None if drop else "passed")


# ---------- 随机写序列的性质 ----------

def _random_write(rng: random.Random, store, meta: RunMeta, hwm: list[int]) -> None:
    sid = rng.choice([j.scope_id for j in meta.jobs])
    op = rng.randrange(6)
    if op == 0:
        store.try_claim_job(meta.run_id, sid, claimed_at="2026-11-12T00:00:01Z")
    elif op == 1:
        store.update_job_state(meta.run_id, JobState(scope_id=sid, status=rng.choice(list(Status))))
    elif op == 2:
        hwm[0] += rng.choice([-1, 0, 1, 2])  # 含过期的投影（被条件挡下）
        statuses = {j.scope_id: rng.choice([Status.PENDING, Status.RUNNING, *_TERMINAL]) for j in meta.jobs}
        if rng.random() < 0.4:
            statuses = {s: Status.PENDING for s in statuses}  # 全 pending 的投影
        store.project_state(meta.run_id, _projection(meta, hwm[0], **statuses))
    elif op == 3:
        store.try_finalize(meta.run_id, rng.choice(_TERMINAL), "2026-11-12T01:00:00Z",
                           message=rng.choice([None, "m"]))
    elif op == 4:
        store.finalize_run(meta.run_id, rng.choice(_TERMINAL), "2026-11-12T01:00:00Z")
    else:
        state = dataclasses.replace(_initial(meta), status=rng.choice(list(Status)))
        rng.choice([store.save_run, store.create_run])(meta, state)


def test_group_corresponds_to_status_after_every_write_of_a_random_sequence(table, store):
    """由写 run 级 `status` 的路径建立的记录，经任意写序列（认领、各状态的 job 写、含全 pending 与过期的投影、两条终态写、
    整体重写），每次写之后都满足「分组为 `live` 当且仅当状态非终态」，终态时分组等于状态值。种子固定，失败可复现。"""
    rng = random.Random(20261112)
    for seq in range(40):
        meta = _meta(f"run-{seq:02d}", "a", "b", "c")
        store.create_run(meta, dataclasses.replace(_initial(meta), status=rng.choice(list(Status))))
        _assert_corresponds(table, meta.run_id)
        hwm = [0]
        for _ in range(15):
            _random_write(rng, store, meta, hwm)
            _assert_corresponds(table, meta.run_id)


# ---------- 索引成员资格 ----------

def test_state_items_enter_the_status_group_index_and_move_on_finalize(table, store):
    """STATE item 按分组进入状态分组索引、带投影的 revision 列表，META item 不进；收尾之后离开 `live` 分组、进入终态分组。"""
    def members(group: str) -> list[dict]:
        return table.query(IndexName=STATUS_GROUP_INDEX, KeyConditionExpression="status_group = :g",
                           ExpressionAttributeValues={":g": group})["Items"]

    meta = _meta()
    store.create_run(meta, _initial(meta))
    [live] = members("live")
    assert live["run_id"] == "run-1" and live["item_type"] == "STATE" and live["worker_task_def_arns"] == _ARNS
    assert "status" not in live and "jobs" not in live  # 投影只有键与 revision 列表

    store.try_finalize("run-1", Status.ERROR, "2026-11-12T01:00:00Z")
    assert members("live") == []
    assert [i["run_id"] for i in members("error")] == ["run-1"]
