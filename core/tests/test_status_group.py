"""DynamoDBRunStore 的状态分组属性（写入规则见 ADR 0030 决定六「runs 表只有一个 GSI」条）。

不变量分两半：写 run 级 `status` 的路径在写之后建立 `status_group` 与 `status` 的对应（非终态为 `live`，终态为该终态的
状态值），含 `create_run` 传入终态初始状态的情形，以及带结果的 job 终态写 `commit_job_states`、结束写 `end_run` 与它的 error 变体
`end_run_as_error`；不写 run 级
`status` 的路径（投影的标量一步、全 pending 的投影、写不成的执行中写）保持已有的对应，写之前缺分组属性的记录写之后仍缺。投影只在
把 job 写成 running 的那次逐 job 写里写 run 级 `status` 与分组。断言直接读 STATE item 的原始属性：分组属性不进 `RunState`，经
`load_run_state` 看不到它。期望值在本文件按上述规则独立写出，不调用被测的派生函数。

本机后端没有索引、不写分组属性，所以这里只有 DynamoDB 一侧。
"""
from __future__ import annotations

import dataclasses
import random
import re

import pytest

from gherkai_core.model import JobState, RunMeta, RunState, Status
from gherkai_core.run_status import RUN_ENDINGS, CommitOutcome
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
            scenarios=(Scenario(id=f"{s}:1", name="s", steps=(Step(index=0, keyword="Given", text="x"),)),), timeout_s=300.0)
        for s in ids
    )
    return RunMeta(run_id=run_id, created_at="2026-11-12T00:00:00Z", jobs=jobs,
                   worker_task_defs={"novaact": _ARNS[0]}, deadline_at="2026-01-01T01:00:00+00:00")


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
def test_create_derives_group_from_the_initial_status(table, store, status):
    """`create_run` 按传入初始状态的 `status` 算分组：正常建 run 得 `live`，传入终态得该终态值，不写死 `live`；
    META item 不带分组属性（索引的稀疏由此构造）。"""
    meta = _meta()
    store.create_run(meta, _initial(meta, status))
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


@pytest.mark.parametrize("drop", [False, True], ids=["group-present", "group-missing"])
def test_commit_leaving_the_run_open_sets_live(table, store, drop):
    """没有使 run 成为终态的终态写把 run 级写成 running，分组为 `live`：库中已是 `live` 时是同值写，缺分组属性的记录由这次写补上。"""
    meta = _meta()
    store.create_run(meta, _initial(meta))
    _claim(store, meta)
    if drop:
        _drop_group(table)
    assert store.commit_job_states("run-1", [JobState("a", Status.PASSED)], ended_at="never") is CommitOutcome.OPEN
    item = _raw(table)
    assert item["status"] == "running" and item["status_group"] == "live"


# 只有一个 job 的 run：这个 job 的终态 → run 的状态（ADR 0031 决定三的取法，skipped 与 aborted 都使 run 没有执行完）
_RUN_STATUS_OF_ONE_JOB = {Status.PASSED: "passed", Status.FAILED: "failed", Status.ERROR: "error",
                          Status.SKIPPED: "aborted", Status.ABORTED: "aborted"}


@pytest.mark.parametrize("job_status", _TERMINAL)
@pytest.mark.parametrize("drop", [False, True], ids=["group-present", "group-missing"])
def test_commit_ending_the_run_sets_the_terminal_group(table, store, job_status, drop):
    """使 run 成为终态的终态写把分组改为 run 的终态值（缺分组属性的记录同样补上）。"""
    meta = _meta("run-1", "a")
    store.create_run(meta, _initial(meta))
    _claim(store, meta)
    if drop:
        _drop_group(table)
    assert store.commit_job_states("run-1", [JobState("a", job_status)], ended_at="2026-11-12T01:00:00Z") \
        is CommitOutcome.ENDED_RUN
    item = _raw(table)
    assert item["status"] == item["status_group"] == _RUN_STATUS_OF_ONE_JOB[job_status]


def _end_with(ending):
    def end(store):
        return store.end_run("run-1", ending, ended_at="2026-11-12T01:00:00Z")
    return end


def _end_as_error(store):
    return store.end_run_as_error("run-1", "提交记录不完整或形态不对", ended_at="2026-11-12T01:00:00Z")


@pytest.mark.parametrize("end, run_status", [
    (_end_with(RUN_ENDINGS["deadline"]), "aborted"),
    (_end_with(RUN_ENDINGS["settle-advancer-exited"]), "aborted"),
    (_end_as_error, "error"),
], ids=["deadline", "settle", "error-ending"])
@pytest.mark.parametrize("drop", [False, True], ids=["group-present", "group-missing"])
def test_end_run_sets_the_terminal_group(table, store, end, run_status, drop):
    """结束写（按模型算出的与 error 变体）把分组改为 run 的终态值（缺分组属性的记录同样补上）。"""
    meta = _meta()
    store.create_run(meta, _initial(meta))
    if drop:
        _drop_group(table)
    assert end(store) is True
    item = _raw(table)
    assert item["status"] == item["status_group"] == run_status


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
    不算顶层）。本模块的更新表达式以 SET 开头，执行中的写另在其后带 REMOVE 子句（删去的是条目里的嵌套路径，不涉及顶层），只看 SET
    子句；各赋值按括号外的逗号切分，右侧是单个占位值时取出它的值，是函数表达式（认领计数的 `if_not_exists(...) + :one`）时原样保留
    表达式文本。"""
    expr = request["UpdateExpression"].strip().split(" REMOVE ")[0]
    assert expr.startswith("SET "), expr
    names = request.get("ExpressionAttributeNames") or {}
    values = request.get("ExpressionAttributeValues") or {}
    out: dict[str, str] = {}
    for part in re.split(r",(?![^(]*\))", expr[len("SET "):]):
        target, _, value = (p.strip() for p in part.partition("="))
        if "." not in target:
            out[names.get(target, target)] = values.get(value, value)
    return out


def _commit_open(store, meta):
    assert store.commit_job_states(meta.run_id, [JobState("a", Status.PASSED)], ended_at="never") is CommitOutcome.OPEN


def _commit_ending_failed(store, meta):
    assert store.commit_job_states(meta.run_id, [JobState("a", Status.PASSED), JobState("b", Status.FAILED)],
                                   ended_at="2026-11-12T01:00:00Z") is CommitOutcome.ENDED_RUN


def _end_run_deadline(store, meta):
    assert store.end_run(meta.run_id, RUN_ENDINGS["deadline"], ended_at="2026-11-12T01:00:00Z") is True


def _end_run_as_error(store, meta):
    assert store.end_run_as_error(meta.run_id, "提交记录不完整或形态不对", ended_at="2026-11-12T01:00:00Z") is True


@pytest.mark.parametrize("write, status", [
    (_claim, "running"), (_job_write, "running"), (_project_running, "running"),
    (_commit_open, "running"), (_commit_ending_failed, "failed"), (_end_run_deadline, "aborted"),
    (_end_run_as_error, "error"),
], ids=["claim", "job-write", "projection", "commit-open", "commit-ending", "end-run", "error-ending"])
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


def test_second_end_run_leaves_the_terminal_status_and_group(table, store):
    """run 级终态不可变（ADR 0054 决策五）：终态之后的另一次结束写被挡，状态与分组都留在第一次结束写的终态上，不发生终态之间的
    分组移动（第二次若写成，分组会从 aborted 换到 error）。"""
    meta = _meta()
    store.create_run(meta, _initial(meta))
    assert store.end_run("run-1", RUN_ENDINGS["deadline"], ended_at="2026-11-12T01:00:00Z") is True
    assert store.end_run_as_error("run-1", "提交记录不完整或形态不对", ended_at="2026-11-12T01:00:01Z") is False
    item = _raw(table)
    assert item["status"] == "aborted" and item["status_group"] == "aborted"


def test_group_changes_only_in_the_write_that_ends_the_run(table, store, monkeypatch):
    """一个 run 从建立到结束的一串写里，分组的值只在使 run 成为终态的那次写里改变：认领、执行中的 job 写、投影与没有使 run 成为
    终态的终态写之后都是 `live`，记下最后一个 job 的终态写改成终态值，之后的结束写与终态写被挡下、不再改它。逐条请求核对：顶层写
    `status_group` 且值不是 `live` 的请求只有那一条。"""
    meta = _meta()
    store.create_run(meta, _initial(meta))
    calls = _record_updates(table, monkeypatch)
    writes = [
        lambda: store.try_claim_job("run-1", "a", claimed_at="2026-11-12T00:00:01Z"),
        lambda: store.update_job_state("run-1", JobState("a", Status.RUNNING, session_id="s-1")),
        lambda: store.project_state("run-1", _projection(meta, 2, a=Status.RUNNING)),
        lambda: store.try_claim_job("run-1", "b", claimed_at="2026-11-12T00:00:02Z"),
        lambda: store.commit_job_states("run-1", [JobState("a", Status.PASSED, session_id="s-1")], ended_at="never"),
        lambda: store.commit_job_states("run-1", [JobState("b", Status.ERROR)], ended_at="2026-11-12T01:00:00Z"),
        lambda: store.end_run("run-1", RUN_ENDINGS["settle-advancer-exited"], ended_at="2026-11-12T01:00:01Z"),
        lambda: store.commit_job_states("run-1", [JobState("b", Status.PASSED)], ended_at="2026-11-12T01:00:02Z"),
    ]
    groups, first_call_of = [], []
    for write in writes:
        first_call_of.append(len(calls))
        write()
        groups.append(_raw(table)["status_group"])
    assert groups == ["live"] * 5 + ["error"] * 3
    terminal_group_writes = [i for i, sets in enumerate(map(_top_level_sets, calls))
                             if sets.get("status_group", "live") != "live"]
    assert terminal_group_writes == [first_call_of[5]]


# ---------- 不写 run 级 status 的路径：保持已有的对应 ----------

def _project_all_pending(store, meta):
    assert store.project_state(meta.run_id, _projection(meta, 2)) is True


def _job_write_outside_the_run(store, meta):
    assert store.update_job_state(meta.run_id, JobState(scope_id="ghost", status=Status.RUNNING, session_id="s-2")) is True


@pytest.mark.parametrize("write", [_project_all_pending, _job_write_outside_the_run],
                         ids=["all-pending-projection", "rejected-job-write"])
@pytest.mark.parametrize("drop", [False, True], ids=["group-present", "group-missing"])
def test_writes_not_touching_run_status_leave_the_group(table, store, write, drop):
    """全 pending 的投影只写事件进度、写不成的执行中写（运行态里没有这个 job）什么都不写：两者都不碰分组属性，库中的 `live` 保持，
    缺的仍缺。"""
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


@pytest.mark.parametrize("projection", [
    {"a": Status.RUNNING}, {"a": Status.PASSED, "b": Status.FAILED}, {},
], ids=["one-running", "results", "all-pending"])
def test_projection_scalar_step_writes_neither_status_nor_group(table, store, monkeypatch, projection):
    """投影的标量一步（请求里没有 `#sid`）只推进 HWM，不写 run 级 `status`、`status_group` 与写入序号；它的条件仍要求 run 未结束。
    在顶层写 `status` 的只有把 job 写成 running 的那几次逐 job 写，投影里已有结果的 job 同样按 running 写、带上 run 级与 `live`；
    全 pending 的投影没有这样的写。"""
    meta = _meta()
    store.create_run(meta, _initial(meta))
    calls = _record_updates(table, monkeypatch)
    assert store.project_state("run-1", _projection(meta, 3, **projection)) is True
    scalar = [c for c in calls if "#sid" not in (c.get("ExpressionAttributeNames") or {})]
    assert len(scalar) == 1
    assert {"status", "status_group", "write_seq"}.isdisjoint(_top_level_sets(scalar[0]))
    assert "#stIN(:pending,:running)" in scalar[0]["ConditionExpression"].replace(" ", "")
    setting_status = sorted(c["ExpressionAttributeNames"]["#sid"] for c in calls
                            if {"status", "status_group"} & _top_level_sets(c).keys())
    assert setting_status == sorted(projection)
    for c in calls:
        sets = _top_level_sets(c)
        if "status" in sets:
            assert (sets["status"], sets["status_group"]) == ("running", "live")


@pytest.mark.parametrize("drop", [False, True], ids=["group-present", "group-missing"])
def test_job_write_on_a_finalized_run_leaves_the_group(table, store, drop):
    """已由结束写结束的 run 上前台的执行中写写不成：job、run 级与分组都不变，缺的仍缺。"""
    meta = _meta()
    store.create_run(meta, _initial(meta))
    assert store.end_run("run-1", RUN_ENDINGS["deadline"], ended_at="2026-11-12T01:00:00Z") is True
    if drop:
        _drop_group(table)
    assert store.update_job_state("run-1", JobState(scope_id="a", status=Status.RUNNING, session_id="s-1")) is False
    item = _raw(table)
    assert item["jobs"]["a"]["status"] == "skipped" and item["status"] == "aborted"
    assert item.get("status_group") == (None if drop else "aborted")


# ---------- 随机写序列的性质 ----------

def _random_write(rng: random.Random, store, meta: RunMeta, hwm: list[int]) -> None:
    sid = rng.choice([j.scope_id for j in meta.jobs])
    op = rng.randrange(6)
    if op == 0:
        store.try_claim_job(meta.run_id, sid, claimed_at="2026-11-12T00:00:01Z")
    elif op == 1:
        store.update_job_state(meta.run_id, JobState(scope_id=sid, status=Status.RUNNING, session_id=rng.choice([None, "s-1"])))
    elif op == 2:
        hwm[0] += rng.choice([-1, 0, 1, 2])  # 含过期的投影（被条件挡下）
        statuses = {j.scope_id: rng.choice([Status.PENDING, Status.RUNNING, *_TERMINAL]) for j in meta.jobs}
        if rng.random() < 0.4:
            statuses = {s: Status.PENDING for s in statuses}  # 全 pending 的投影
        store.project_state(meta.run_id, _projection(meta, hwm[0], **statuses))
    elif op == 3:
        store.commit_job_states(meta.run_id, [JobState(scope_id=sid, status=rng.choice(_TERMINAL))],
                                ended_at="2026-11-12T01:00:00Z")
    elif op == 4:
        if rng.random() < 0.8:
            store.end_run(meta.run_id, RUN_ENDINGS[rng.choice(list(RUN_ENDINGS))], ended_at="2026-11-12T01:00:00Z")
        else:
            store.end_run_as_error(meta.run_id, "提交记录不完整或形态不对", ended_at="2026-11-12T01:00:00Z")
    else:
        state = dataclasses.replace(_initial(meta), status=rng.choice(list(Status)))
        with pytest.raises(FileExistsError):  # 对已有的 run 再建被拒、不改任何东西
            store.create_run(meta, state)


def test_group_corresponds_to_status_after_every_write_of_a_random_sequence(table, store):
    """由写 run 级 `status` 的路径建立的记录，经任意写序列（认领、执行中的写、含全 pending 与过期的投影、终态写、各条来路的结束写与
    error 变体、对已有 run 的重建），每次写之后都满足「分组为 `live` 当且仅当状态非终态」，终态时分组等于状态值。种子固定，失败可复现。"""
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

def test_state_items_enter_the_status_group_index_and_move_when_the_run_ends(table, store):
    """STATE item 按分组进入状态分组索引、带投影的 revision 列表，META item 不进；结束写之后离开 `live` 分组、进入终态分组（结束写的
    error 变体进 error，到期的结束写进 aborted）。"""
    def members(group: str) -> list[dict]:
        return table.query(IndexName=STATUS_GROUP_INDEX, KeyConditionExpression="status_group = :g",
                           ExpressionAttributeValues={":g": group})["Items"]

    meta = _meta()
    store.create_run(meta, _initial(meta))
    [live] = members("live")
    assert live["run_id"] == "run-1" and live["item_type"] == "STATE" and live["worker_task_def_arns"] == _ARNS
    assert "status" not in live and "jobs" not in live  # 投影只有键与 revision 列表

    assert store.end_run_as_error("run-1", "提交记录不完整或形态不对", ended_at="2026-11-12T01:00:00Z") is True
    assert members("live") == []
    assert [i["run_id"] for i in members("error")] == ["run-1"]

    meta2 = _meta("run-2")
    store.create_run(meta2, _initial(meta2))
    assert [i["run_id"] for i in members("live")] == ["run-2"]
    assert store.end_run("run-2", RUN_ENDINGS["deadline"], ended_at="2026-11-12T01:00:00Z") is True
    assert members("live") == []
    assert [i["run_id"] for i in members("aborted")] == ["run-2"]
