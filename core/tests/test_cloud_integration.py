"""云端 adapter 集成测试（@pytest.mark.integration）：连**真** DDB/S3，专测 moto 抓不到的真 AWS 语义。

**默认不运行**（pyproject addopts `-m 'not integration'`）。运行方式（见 tests/README.md）：
    export AWS_DDB_TABLE=<你建的真表>  AWS_S3_BUCKET=<你建的真桶>
    uv run pytest -m integration
没设环境变量 → `real_aws` fixture skip（不误连）。用真凭证（default profile），每用例自清理写入的数据。

**为何要连真**：moto 是模拟实现，与真 DDB/S3 在若干边界可能不一致——本文件正是钉这些差异（也是 review
时对抗验证过的疑点）：DDB 空串 SET / 保留字 / 空 Map / `SET jobs.#sid` 单元素刷；按规模上限取最宽形态的运行态上，结束写整体替换
jobs 在单条记录的大小上限之内写成；S3 按标识存取判定明细（含中文与
斜杠的 scope_id，同一个 job 的两份互不覆盖）；云端提交记录（约 550KB 的定义经头与 jobs 对象往返、同一个 run 标识再建时 jobs 对象的
条件写、缺键得到的错误）。单测（moto）已覆盖行为契约，这里只补「真后端语义」这一层。
"""
from __future__ import annotations

import itertools
import json

import pytest

from gherkai_core.model import JobState, RunMeta, RunState, Status
from gherkai_core.run_status import RUN_ENDINGS, CommitOutcome
from tests.conftest import jobs_objects_for
from tests.test_stores import _sample_run

pytestmark = pytest.mark.integration  # 本文件全部用例都是集成测试（默认 deselect）

_counter = itertools.count(1)  # 单进程内递增，给 run_id 去重


def _uniq(prefix: str) -> str:
    """给真表/真桶造一个本次运行专属的 run_id，避免多次执行撞名（无随机源，用递增计数）。
    跨进程靠 it- 前缀 + fixture 自清理兜底（真资源是你专用的测试表/桶）。"""
    return f"it-{prefix}-{next(_counter)}"


def _ddb_store(real_aws):
    from gherkai_core.adapters.run_store.ddb import DynamoDBRunStore
    return DynamoDBRunStore(real_aws["ddb"].Table(real_aws["table_name"]), jobs_objects=jobs_objects_for(real_aws))


def _s3_result_store(real_aws):
    from gherkai_core.adapters.result_store.s3 import S3ResultStore
    return S3ResultStore(real_aws["s3"], real_aws["bucket"])


# ---- DynamoDBRunStore：真 DDB 的生命周期 + 真语义边界 ----
def test_ddb_run_store_lifecycle_real(real_aws):
    """真 DDB 上执行完整实时写生命周期：create_run → update_job_state（RUNNING）→ commit_job_states（两个 job 的终态，后一次使
    run 成为终态）→ 读回。覆盖真语义：空 Map jobs 能存、SET jobs.#sid 单元素刷、以写入序号为条件整体替换 jobs 并 SET
    status(保留字)/ended_at、含 /:中文 scope_id；对已有的 run 再建被条件挡下。"""
    store = _ddb_store(real_aws)
    rid = _uniq("ddb-life")
    real_aws["cleanup_run_id"](rid)  # 登记清理

    meta = _sample_run(rid).run_meta  # 含 features/wiki.feature:6（/:）+ 登录场景（中文）
    scope_ids = [j.scope_id for j in meta.jobs]

    # create：全 pending（含空/非空 jobs Map 落真表）
    store.create_run(meta, RunState(
        run_id=rid, status=Status.PENDING,
        jobs={sid: JobState(scope_id=sid, status=Status.PENDING) for sid in scope_ids},
        started_at="2026-07-01T00:00:00Z",
    ))
    s0 = store.load_run_state(rid)
    assert s0 is not None and s0.status == Status.PENDING
    assert all(js.status == Status.PENDING for js in s0.jobs.values())

    # update：单元素刷 RUNNING（含血缘）→ 另一个不受影响（真 SET jobs.#sid 的隔离性）
    store.update_job_state(rid, JobState(scope_ids[0], Status.RUNNING, session_id="sess-real"))
    mid = store.load_run_state(rid)
    assert mid.jobs[scope_ids[0]].status == Status.RUNNING
    assert mid.jobs[scope_ids[0]].session_id == "sess-real"
    assert mid.jobs[scope_ids[1]].status == Status.PENDING  # 没被污染
    assert mid.status == Status.RUNNING  # job 离开 pending 的同一次写把 run 级推进为 running（ADR 0034 机制三）

    # 各自完成：终态写，最后一个使 run 成为终态（真 DDB 保留字 status/ended_at 的 SET）
    assert store.commit_job_states(rid, [JobState(scope_ids[0], Status.PASSED, session_id="sess-real")],
                                   ended_at="2026-07-01T00:04:00Z") is CommitOutcome.OPEN
    assert store.commit_job_states(rid, [JobState(scope_ids[1], Status.FAILED)],
                                   ended_at="2026-07-01T00:05:00Z") is CommitOutcome.ENDED_RUN
    with pytest.raises(FileExistsError):
        store.create_run(meta, RunState(run_id=rid, status=Status.PENDING, jobs={}))

    final = store.load_run_state(rid)
    assert final.status == Status.FAILED and final.ended_at == "2026-07-01T00:05:00Z"
    assert final.started_at == "2026-07-01T00:00:00Z"  # create 填的起点保留
    assert final.jobs[scope_ids[0]] == JobState(scope_ids[0], Status.PASSED, session_id="sess-real")
    # definition 也读回（META item JSON blob 真往返）
    assert store.load_run_meta(rid).jobs[0].scope_id == scope_ids[0]


def test_ddb_update_before_create_raises_real(real_aws):
    """真 DDB：未 create 就写 → 执行中的写与终态写抛 FileNotFoundError（对拍 local 报错语义；执行中的写的原因取自条件不成立时
    带回的条目）；结束写写不成；都不臆造 STATE。"""
    store = _ddb_store(real_aws)
    rid = _uniq("ddb-nocreate")  # 从不 create，无需登记清理（没写入）
    with pytest.raises(FileNotFoundError):
        store.update_job_state(rid, JobState("s", Status.RUNNING))
    with pytest.raises(FileNotFoundError):
        store.commit_job_states(rid, [JobState("s", Status.PASSED)], ended_at="t")
    assert store.end_run(rid, RUN_ENDINGS["deadline"], ended_at="t") is False
    assert store.load_run_state(rid) is None


def _real_run(store, real_aws, tag: str):
    """在真表上建一个全 pending 的 run，返回 (run_id, meta, scope_ids, 初始运行态)。"""
    rid = _uniq(tag)
    real_aws["cleanup_run_id"](rid)
    meta = _sample_run(rid).run_meta
    scope_ids = [j.scope_id for j in meta.jobs]
    initial = RunState(run_id=rid, status=Status.PENDING,
                       jobs={sid: JobState(scope_id=sid, status=Status.PENDING) for sid in scope_ids},
                       started_at="2026-07-01T00:00:00Z", high_water_mark=0)
    store.create_run(meta, initial)
    return rid, meta, scope_ids, initial


def test_ddb_claim_advances_run_and_is_rejected_after_the_run_ends_real(real_aws):
    """真 DDB 上的认领（ADR 0034 机制三「run 级状态只进不退」条①）：认领成功的同一次写把 run 级置为 running；结束写的 error 变体
    把 run 与未结束的 job 都记为 error 之后，认领返回 False，run 级、结束时刻、原因、job 态与认领时刻都不变。同一条更新表达式
    同时写顶层属性与 Map 内路径、条件同时判两处，是真 DDB 的表达式语义，moto 上通过不能替代。"""
    store = _ddb_store(real_aws)
    rid, _meta, scope_ids, _initial = _real_run(store, real_aws, "ddb-claim")
    assert store.try_claim_job(rid, scope_ids[0], claimed_at="2026-07-01T00:00:01Z") is True
    mid = store.load_run_state(rid)
    assert mid.status == Status.RUNNING and mid.high_water_mark == 0
    assert mid.jobs[scope_ids[0]] == JobState(scope_ids[0], Status.RUNNING, claimed_at="2026-07-01T00:00:01Z")
    assert mid.jobs[scope_ids[1]].status == Status.PENDING

    assert store.end_run_as_error(rid, "原因", ended_at="2026-07-01T00:01:00Z") is True
    before = store.load_run_state(rid)
    assert (before.status, before.message, before.jobs[scope_ids[1]]) == (
        Status.ERROR, "原因", JobState(scope_ids[1], Status.ERROR, message="原因"))
    assert store.try_claim_job(rid, scope_ids[1], claimed_at="2026-07-01T00:02:00Z") is False
    assert store.load_run_state(rid) == before


@pytest.mark.parametrize("hwm", [0, 3], ids=["same_hwm", "higher_hwm"])
def test_ddb_stale_all_pending_projection_keeps_run_running_real(real_aws, hwm):
    """真 DDB 上认领之后写入全 pending 的旧投影（同 HWM 与更高 HWM）：run 级保持 running，HWM 按条件前进，已认领的 job
    仍为 running（条②：全 pending 的投影只写事件进度、不写 run 级）。"""
    store = _ddb_store(real_aws)
    rid, _meta, scope_ids, initial = _real_run(store, real_aws, f"ddb-stale-{hwm}")
    assert store.try_claim_job(rid, scope_ids[0]) is True
    stale = RunState(run_id=rid, status=Status.PENDING, jobs=dict(initial.jobs),
                     started_at=initial.started_at, high_water_mark=hwm)
    assert store.project_state(rid, stale) is True
    got = store.load_run_state(rid)
    assert got.status == Status.RUNNING
    assert got.high_water_mark == hwm
    assert got.jobs[scope_ids[0]].status == Status.RUNNING


def test_ddb_job_write_on_finalized_run_changes_nothing_real(real_aws):
    """真 DDB 上由结束写结束的 run 再收到前台的执行中写：那一次带 run 级条件的写被挡下、返回 False，记录整份不变（ADR 0034 机制三
    「run 级状态只进不退」条③）。两种起点：没有启动过 job（都记 skipped），以及有执行中的 job（记 aborted）。被挡下的原因取自条件不
    成立时带回的条目（`ReturnValuesOnConditionCheckFailure`），这一参数的真实行为只能在真 DDB 上核对。"""
    store = _ddb_store(real_aws)
    rid, _meta, scope_ids, _initial = _real_run(store, real_aws, "ddb-latejob")
    assert store.end_run(rid, RUN_ENDINGS["settle-advancer-exited"], ended_at="2026-07-01T00:01:00Z") is True
    before = store.load_run_state(rid)
    assert store.update_job_state(rid, JobState(scope_ids[0], Status.RUNNING, session_id="late")) is False
    assert store.load_run_state(rid) == before

    rid2, _meta2, scope_ids2, _initial2 = _real_run(store, real_aws, "ddb-latejob-ended")
    assert store.try_claim_job(rid2, scope_ids2[0], claimed_at="2026-07-01T00:00:01Z") is True
    assert store.end_run(rid2, RUN_ENDINGS["settle-advancer-exited"], ended_at="2026-07-01T00:01:00Z") is True
    before2 = store.load_run_state(rid2)
    assert store.update_job_state(rid2, JobState(scope_ids2[0], Status.RUNNING, session_id="late")) is False
    assert store.load_run_state(rid2) == before2


def test_ddb_session_id_none_omitted_real(real_aws):
    """真 DDB：session_id=None omit-when-None，读回仍 None（真 Map entry 缺键的读回语义）。"""
    store = _ddb_store(real_aws)
    rid = _uniq("ddb-nonesess")
    real_aws["cleanup_run_id"](rid)
    meta = _sample_run(rid).run_meta
    store.create_run(meta, RunState(run_id=rid, status=Status.PENDING,
                                    jobs={meta.jobs[0].scope_id: JobState(meta.jobs[0].scope_id, Status.PENDING)}))
    assert store.update_job_state(rid, JobState(meta.jobs[0].scope_id, Status.RUNNING, session_id=None)) is True
    js = store.load_run_state(rid).jobs[meta.jobs[0].scope_id]
    assert js.status == Status.RUNNING and js.session_id is None


def _raw_state(real_aws, rid: str) -> dict:
    return real_aws["ddb"].Table(real_aws["table_name"]).get_item(
        Key={"run_id": rid, "item_type": "STATE"}, ConsistentRead=True)["Item"]


def _set_entry_attr(real_aws, rid: str, scope_id: str, attr: str, value) -> None:
    """直接在真表的 jobs Map 条目里写一个属性：别的写方写下、本版本不认识的属性只能这样造。"""
    real_aws["ddb"].Table(real_aws["table_name"]).update_item(
        Key={"run_id": rid, "item_type": "STATE"}, UpdateExpression="SET jobs.#sid.#a = :v",
        ExpressionAttributeNames={"#sid": scope_id, "#a": attr}, ExpressionAttributeValues={":v": value})


def test_ddb_job_write_sets_and_removes_model_keys_and_leaves_unknown_attributes_real(real_aws):
    """真 DDB 上执行中的写逐属性写条目里的模型键（ADR 0030 决定四「改写运行态时原样保留不认识的部分」条）：同一条更新表达式里 SET
    这次有值的键、REMOVE 这次没有值的键（含条目里本来不存在的键），不认识的属性原样留下；条件里的 job 路径与 run 级状态同一次判断。
    嵌套路径上 SET 与 REMOVE 并用、REMOVE 一个不存在的嵌套属性不报错，是真 DDB 的表达式语义。"""
    store = _ddb_store(real_aws)
    rid, _meta, scope_ids, _initial = _real_run(store, real_aws, "ddb-jobattrs")
    sid = scope_ids[0]
    assert store.try_claim_job(rid, sid, claimed_at="2026-07-01T00:00:01Z") is True
    _set_entry_attr(real_aws, rid, sid, "future_note", {"origin": "future-writer"})
    assert store.update_job_state(rid, JobState(sid, Status.RUNNING, session_id="sess-1")) is True
    assert _raw_state(real_aws, rid)["jobs"][sid] == {"status": "running", "session_id": "sess-1",
                                                      "future_note": {"origin": "future-writer"}}
    assert store.update_job_state(rid, JobState(sid, Status.RUNNING)) is True
    assert _raw_state(real_aws, rid)["jobs"][sid] == {"status": "running", "future_note": {"origin": "future-writer"}}
    # 不在 Map 里的 job：父路径不存在的 SET 与 REMOVE 先被条件挡成条件不成立（不是表达式错误），返回 True、记录不变
    before = _raw_state(real_aws, rid)
    assert store.update_job_state(rid, JobState("ghost", Status.RUNNING, session_id="s")) is True
    assert _raw_state(real_aws, rid) == before


def test_ddb_projection_writes_a_job_only_when_its_content_differs_real(real_aws):
    """真 DDB 上投影的逐 job 写以「这次写提及的字段至少一项与库中不同」为条件（ADR 0034 机制三「② 的 job 级半边落地形态」段）：库中
    缺会话与认领时刻、投影带了时写成、写入序号加一；同一份投影再发一遍不写、序号不变；标量一步不改序号。这次核的是产品代码发出的
    请求，此前同一写法只在写入层核过。"""
    store = _ddb_store(real_aws)
    rid, _meta, scope_ids, _initial = _real_run(store, real_aws, "ddb-projdiff")
    sid = scope_ids[0]
    assert store.try_claim_job(rid, sid) is True  # 不带认领时刻：库中这个 job 缺会话与认领时刻
    seq = _raw_state(real_aws, rid)["write_seq"]
    projected = RunState(run_id=rid, status=Status.RUNNING, high_water_mark=1, jobs={
        sid: JobState(sid, Status.RUNNING, session_id="sess-1", claimed_at="2026-07-01T00:00:01Z")})
    assert store.project_state(rid, projected) is True
    assert _raw_state(real_aws, rid)["write_seq"] == seq + 1
    assert store.project_state(rid, projected) is True
    raw = _raw_state(real_aws, rid)
    assert (raw["write_seq"], raw["high_water_mark"]) == (seq + 1, 1)
    assert store.load_run_state(rid).jobs[sid] == JobState(sid, Status.RUNNING, session_id="sess-1",
                                                           claimed_at="2026-07-01T00:00:01Z")


def test_ddb_whole_jobs_writes_merge_unknown_attributes_real(real_aws):
    """真 DDB 上整体替换 jobs 的两个按模型的写入口经产品代码各写一次（ADR 0034 机制三②「实测项」）：读到的条目带一个不认识的属性，
    写下之后它原样在，各已知键取这次算出的值，这次算出的条目省去的已知键（终态写没有给出的点名标识）不按读到的旧值写回。"""
    store = _ddb_store(real_aws)
    rid, _meta, scope_ids, _initial = _real_run(store, real_aws, "ddb-merge")
    first, second = scope_ids[0], scope_ids[1]
    assert store.try_claim_job(rid, first, claimed_at="2026-07-01T00:00:01Z") is True
    for sid in (first, second):
        _set_entry_attr(real_aws, rid, sid, "future_note", "kept")
    _set_entry_attr(real_aws, rid, first, "result_id", "stale-id")
    assert store.commit_job_states(rid, [JobState(first, Status.PASSED)], ended_at="t1") is CommitOutcome.OPEN
    entry = _raw_state(real_aws, rid)["jobs"][first]
    assert entry == {"status": "passed", "claimed_at": "2026-07-01T00:00:01Z", "future_note": "kept"}
    ending = RUN_ENDINGS["settle-advancer-exited"]
    assert store.end_run(rid, ending, ended_at="t2") is True
    jobs = _raw_state(real_aws, rid)["jobs"]
    assert jobs[second] == {"status": "skipped", "message": ending.skipped_message, "future_note": "kept"}
    assert jobs[first] == entry


def _meta_of(rid: str, scope_ids) -> RunMeta:
    """只为建 run 用的运行定义：每个 job 一个只有一步的 scenario，scope 名与 scenario 标识都取短值，提交记录不随 scope 标识变长。"""
    from gherkai_core.model import Job, Scenario, Step
    jobs = tuple(
        Job(scope_id=sid, scope_name=f"job-{i}", engine="novaact", timeout_s=300.0,
            scenarios=(Scenario(id=f"{i}:1", name="s", steps=(Step(index=0, keyword="Given", text="x"),)),))
        for i, sid in enumerate(scope_ids))
    return RunMeta(run_id=rid, created_at="2026-07-01T00:00:00Z", jobs=jobs, deadline_at="2026-07-01T02:00:00+00:00")


def test_ddb_error_ending_copies_entries_and_ends_the_run_real(real_aws):
    """真 DDB 上结束写的 error 变体（ADR 0030 决定四「error 变体是另一个写入口」条，结果的完整核对是 ADR 0054 实测项 21、23）：执行中与
    没有启动的条目记 error 带原因、其余属性（含不认识的）原样复制；已由终态写结束、带点名标识与不认识属性的条目逐字段原样；run 级与
    状态分组记 error，写入序号加一；以读到的写入序号为条件的整体替换在真表上写成，第二次调用读到已结束、返回 False。"""
    store = _ddb_store(real_aws)
    rid = _uniq("ddb-errend")
    real_aws["cleanup_run_id"](rid)
    running, pending, ended = "features/wiki.feature:6", "登录场景", "第三个/job:9"
    store.create_run(_meta_of(rid, (running, pending, ended)), RunState(
        run_id=rid, status=Status.PENDING, started_at="2026-07-01T00:00:00Z", high_water_mark=0,
        jobs={sid: JobState(sid, Status.PENDING) for sid in (running, pending, ended)}))
    for sid in (running, ended):
        assert store.try_claim_job(rid, sid, claimed_at="2026-07-01T00:00:01Z") is True
    assert store.commit_job_states(rid, [JobState(ended, Status.PASSED, session_id="sess-e",
                                                  result_id="0123456789abcdef")], ended_at="t-never") is CommitOutcome.OPEN
    for sid in (running, ended):
        _set_entry_attr(real_aws, rid, sid, "future_note", "kept")
    before = _raw_state(real_aws, rid)
    assert before["jobs"][ended] == {"status": "passed", "session_id": "sess-e", "claimed_at": "2026-07-01T00:00:01Z",
                                     "result_id": "0123456789abcdef", "future_note": "kept"}, "前提：已结束的条目带满各项"
    assert store.end_run_as_error(rid, "原因", ended_at="2026-07-01T00:01:00Z") is True
    after = _raw_state(real_aws, rid)
    assert after["jobs"][running] == {"status": "error", "message": "原因", "claimed_at": "2026-07-01T00:00:01Z",
                                      "future_note": "kept"}
    assert after["jobs"][pending] == {"status": "error", "message": "原因"}
    assert after["jobs"][ended] == before["jobs"][ended]
    assert (after["status"], after["status_group"], after["ended_at"], after["message"]) == (
        "error", "error", "2026-07-01T00:01:00Z", "原因")
    assert after["write_seq"] == before["write_seq"] + 1
    assert store.end_run_as_error(rid, "第二句", ended_at="2026-07-01T00:02:00Z") is False
    assert _raw_state(real_aws, rid) == after


# 部署侧的并发上限（deploy_aws 的 stack.py 里 DEPLOY_SIDE_MAX_CONCURRENCY）：一个 run 里同时执行中的 job 至多这么多个。core 的测试不
# import 部署包，数值照 ADR 0034 机制三②「实测项」写在这里。
_RUNNING_AT_MOST = 20


def _widest_run(store, real_aws, tag: str) -> tuple[str, int]:
    """在真表上建一个按规模上限取最宽形态的 run（ADR 0034 机制三②「实测项」）：`MAX_JOBS_PER_RUN` 个 job，scope 标识与会话标识都取
    上限字节数；`_RUNNING_AT_MOST` 个执行中，带会话与认领时刻；其余都由执行结果结束，带会话、认领时刻与点名明细的标识。建 run 原样写下
    给出的初始运行态，记录由这一次写建出，不经逐个 job 的认领与终态写。返回 (run_id, 执行中的 job 数)。"""
    from gherkai_core.model import MAX_ID_BYTES, MAX_JOBS_PER_RUN
    from gherkai_core.wire import MAX_SESSION_ID_BYTES

    rid = _uniq(tag)
    real_aws["cleanup_run_id"](rid)
    scope_ids = [f"{i:03d}/".ljust(MAX_ID_BYTES, "s") for i in range(MAX_JOBS_PER_RUN)]
    claimed = "2026-07-01T00:00:01.123456+00:00"
    jobs = {}
    for i, sid in enumerate(scope_ids):
        session = f"sess-{i:03d}-".ljust(MAX_SESSION_ID_BYTES, "v")
        if i < _RUNNING_AT_MOST:
            jobs[sid] = JobState(sid, Status.RUNNING, session_id=session, claimed_at=claimed)
        else:
            jobs[sid] = JobState(sid, Status.FAILED, session_id=session, claimed_at=claimed, result_id=f"{i:016x}")
    assert all(len(s.encode()) == MAX_ID_BYTES for s in scope_ids), "前提：scope 标识取满上限"
    store.create_run(_meta_of(rid, scope_ids), RunState(
        run_id=rid, status=Status.RUNNING, started_at="2026-07-01T00:00:00Z", high_water_mark=10**9,
        claim_count=MAX_JOBS_PER_RUN, jobs=jobs))
    return rid, _RUNNING_AT_MOST


def test_ddb_endings_of_the_widest_run_land_real(real_aws):
    """真 DDB 上一条记录装得下按规模上限取最宽形态的 run 的结束写（ADR 0034 机制三②「条目大小」与「实测项」：结束写给由它结束的 job
    各添一句说明，落在结束这类 run 必须写成的那一次写上）。处置的结束写与 error 变体的结束写各对一个这样的 run 写一次，都整条写成：
    执行中的 job 各记 aborted 或 error、带那一句，其余条目不变。error 变体的原因取记录格式版本不合的那一句，拼进的写出版本取满截断的
    上界、用四字节字符。超出单条记录的大小上限时这两次写以 ValidationException 失败（不是条件不成立），这条用例随之失败。"""
    from gherkai_core.run_status import schema_mismatch_reason

    store = _ddb_store(real_aws)
    ending = RUN_ENDINGS["settle-past-deadline"]
    rid, running = _widest_run(store, real_aws, "ddb-widest-settle")
    assert store.end_run(rid, ending, ended_at="2026-07-01T03:00:00.000000+00:00") is True
    entries = _raw_state(real_aws, rid)["jobs"].values()
    assert sum(e["status"] == "aborted" and e["message"] == ending.aborted_message for e in entries) == running
    assert sum(e["status"] == "failed" and "message" not in e for e in entries) == len(entries) - running

    reason = schema_mismatch_reason(10**38 - 1, 1, "\U0001d7d7" * 100)
    rid, running = _widest_run(store, real_aws, "ddb-widest-error")
    assert store.end_run_as_error(rid, reason, ended_at="2026-07-01T03:00:00.000000+00:00") is True
    raw = _raw_state(real_aws, rid)
    assert (raw["status"], raw["status_group"], raw["message"]) == ("error", "error", reason)
    assert sum(e["status"] == "error" and e["message"] == reason for e in raw["jobs"].values()) == running


# ---- S3ResultStore：真 S3 上按标识存取 ----
def test_s3_result_store_round_trip_real(real_aws):
    """真 S3：每份明细以一个标识存下、按标识取回（含 /:中文 scope_id 的明细，键里只有标识）；同一个 job 以两个标识各存一份互不覆盖；
    不存在的标识取回 None（测试凭证带列举权限时 S3 回 NoSuchKey）。"""
    store = _s3_result_store(real_aws)
    rid = _uniq("s3-rt")
    real_aws["cleanup_prefix"](f"{rid}/")  # 登记清理该 run 的所有对象

    run = _sample_run(rid)
    ids = {jr.scope_id: f"{n:016x}" for n, jr in enumerate(run.details)}
    for jr in run.details:
        store.save_job_result(rid, ids[jr.scope_id], jr)
    for jr in run.details:
        assert store.load_job_result(rid, ids[jr.scope_id]) == jr

    again = run.details[0]
    store.save_job_result(rid, "00000000000000ff", again)
    assert store.load_job_result(rid, "00000000000000ff") == again
    assert store.load_job_result(rid, ids[again.scope_id]) == again  # 前一份仍在

    listed = real_aws["s3"].list_objects_v2(Bucket=real_aws["bucket"], Prefix=f"{rid}/jobs/")
    assert sorted(o["Key"] for o in listed["Contents"]) == sorted(
        f"{rid}/jobs/{i}.json" for i in [*ids.values(), "00000000000000ff"])
    assert store.load_job_result(rid, "ffffffffffffffff") is None  # 这个 run 下从没存过的标识


# ---- 云端提交记录：头加 jobs 对象（ADR 0030 决定六「云端提交记录」条的实测项 1、2、4）----
def _wide_meta(rid: str, n_jobs: int, n_steps: int) -> RunMeta:
    """n_jobs 个 job、每个一个 scenario、n_steps 个约 55 个字符的 step 的运行定义（实测项 1 那一格是 500 × 8）。"""
    from gherkai_core.model import Job, Scenario, Step

    def job(i: int) -> Job:
        sid = f"features/checkout-{i:03d}.feature:{10 + i}"
        return Job(scope_id=sid, scope_name=f"下单流程 {i}", engine="midscene", timeout_s=300.0, scenarios=(
            Scenario(id=sid, name=f"下单流程 {i}", steps=tuple(
                Step(k, "When", f"在结算页填写第 {k} 项收货信息并确认页面显示正确的合计金额与优惠-{i:03d}")
                for k in range(n_steps))),))
    return RunMeta(run_id=rid, created_at="t", jobs=tuple(job(i) for i in range(n_jobs)),
                   deadline_at="2026-01-01T01:00:00+00:00")


def _jobs_keys_real(real_aws, rid: str) -> list[str]:
    listed = real_aws["s3"].list_objects_v2(Bucket=real_aws["bucket"], Prefix=f"definitions/{rid}/")
    return sorted(o["Key"] for o in listed.get("Contents", []))


def test_wide_definition_round_trips_through_head_and_jobs_object_real(real_aws):
    """实测项 1：约 550KB 的定义（500 个 job、每个 8 个 step）建 run 之后读回，读回的运行定义与写入的相同；jobs 对象超过单条记录的
    上限，头仍只有几百字节。"""
    from gherkai_core.serialize import run_meta_to_dict

    store = _ddb_store(real_aws)
    rid = _uniq("wide-def")
    real_aws["cleanup_run_id"](rid)
    meta = _wide_meta(rid, 500, 8)
    store.create_run(meta, RunState(run_id=rid, status=Status.PENDING,
                                    jobs={j.scope_id: JobState(j.scope_id, Status.PENDING) for j in meta.jobs}))

    assert store.load_run_meta(rid) == meta
    [key] = _jobs_keys_real(real_aws, rid)
    size = real_aws["s3"].head_object(Bucket=real_aws["bucket"], Key=key)["ContentLength"]
    assert size > 409_600, f"前提：jobs 对象应超过单条记录的上限，实际 {size} 字节"
    head = real_aws["ddb"].Table(real_aws["table_name"]).get_item(
        Key={"run_id": rid, "item_type": "META"}, ConsistentRead=True)["Item"]
    assert len(head["meta_json"].encode("utf-8")) < 1024
    assert json.loads(real_aws["s3"].get_object(Bucket=real_aws["bucket"], Key=key)["Body"].read()) == \
        run_meta_to_dict(meta)["jobs"]


def _snapshot_real(real_aws, rid: str):
    table = real_aws["ddb"].Table(real_aws["table_name"])
    items = tuple(table.get_item(Key={"run_id": rid, "item_type": t}, ConsistentRead=True).get("Item") for t in ("META", "STATE"))
    objects = {k: real_aws["s3"].get_object(Bucket=real_aws["bucket"], Key=k)["Body"].read() for k in _jobs_keys_real(real_aws, rid)}
    return items[0], items[1], objects


def test_recreating_a_run_changes_no_record_real(real_aws, monkeypatch):
    """实测项 2：同一个 run 标识再建一次。键不同时以 run 已存在失败，头、运行态与先前的 jobs 对象都不改，只多出一个没有记录指向的
    jobs 对象；让再建取到相同的键（替换随机段的来源）时，jobs 对象的条件写得到 412（PreconditionFailed），以 run 已存在失败，什么都
    不改、也不多出对象。受限角色下的 412 要部署之后另核。"""
    from botocore.exceptions import ClientError

    from gherkai_core.adapters.run_store import jobs_object
    from gherkai_core.errors import RunAlreadyExists

    store = _ddb_store(real_aws)
    for same_key in (False, True):
        rid = _uniq(f"recreate-{'same' if same_key else 'new'}-key")
        real_aws["cleanup_run_id"](rid)
        if same_key:
            monkeypatch.setattr(jobs_object, "_new_segment", lambda: "0" * 32)
        meta = _sample_run(rid).run_meta
        store.create_run(meta, RunState(run_id=rid, status=Status.PENDING,
                                        jobs={j.scope_id: JobState(j.scope_id, Status.PENDING) for j in meta.jobs}))
        before = _snapshot_real(real_aws, rid)
        with pytest.raises(RunAlreadyExists) as exc:
            store.create_run(_wide_meta(rid, 2, 1), RunState(run_id=rid, status=Status.PENDING, jobs={}))
        after = _snapshot_real(real_aws, rid)
        assert after[:2] == before[:2]
        if same_key:
            assert isinstance(exc.value.__cause__, ClientError)
            assert exc.value.__cause__.response["Error"]["Code"] == "PreconditionFailed"
            assert after[2] == before[2]
        else:
            assert {k: after[2][k] for k in before[2]} == before[2] and len(after[2]) == len(before[2]) + 1
        assert store.load_run_meta(rid) == meta
        monkeypatch.undo()


def test_missing_jobs_object_reads_as_missing_key_with_list_permission_real(real_aws):
    """删去 jobs 对象之后读整份定义：有桶的列举权限时（执行本测试的凭证）得到「键不存在」。没有列举权限时得到拒绝访问，要以按最小
    权限授予的角色另核。"""
    from gherkai_core.adapters.run_store.jobs_object import JobsObjectFailure, JobsObjectUnreadable

    store = _ddb_store(real_aws)
    rid = _uniq("jobs-gone")
    real_aws["cleanup_run_id"](rid)
    meta = _sample_run(rid).run_meta
    store.create_run(meta, RunState(run_id=rid, status=Status.PENDING, jobs={}))
    [key] = _jobs_keys_real(real_aws, rid)
    real_aws["s3"].delete_object(Bucket=real_aws["bucket"], Key=key)
    with pytest.raises(JobsObjectUnreadable) as exc:
        store.load_run_meta(rid)
    assert (exc.value.failure, exc.value.error_code) == (JobsObjectFailure.MISSING, "NoSuchKey")


def test_store_without_jobs_objects_reports_missing_wiring_real(real_aws):
    """实测项 4：没给 jobs 对象存取的 DynamoDBRunStore，建 run 与读整份定义都报装配缺失（不带多行参数的 run 同样报，什么都不写）；
    只读头的读照常。"""
    from gherkai_core.adapters.run_store.ddb import DynamoDBRunStore

    rid = _uniq("no-wiring")
    real_aws["cleanup_run_id"](rid)
    meta = _sample_run(rid).run_meta
    _ddb_store(real_aws).create_run(meta, RunState(run_id=rid, status=Status.PENDING, jobs={}))
    bare = DynamoDBRunStore(real_aws["ddb"].Table(real_aws["table_name"]))
    other = _uniq("no-wiring-create")
    real_aws["cleanup_run_id"](other)
    with pytest.raises(RuntimeError, match="jobs_objects"):
        bare.create_run(_sample_run(other).run_meta, RunState(run_id=other, status=Status.PENDING, jobs={}))
    with pytest.raises(RuntimeError, match="jobs_objects"):
        bare.load_run_meta(rid)
    assert bare.peek_definition_header(rid) == (2, None)
    assert bare.load_run_state(rid) is not None
    assert _snapshot_real(real_aws, other) == (None, None, {})


# ============================================================================
# DDB 400KB item 上限：moto 抓不到的真语义（真连独有价值，见 tests/README + ADR 0030 决定六）
# moto 5.x 只在 put_item 校验 400KB、update_item 增量路径**零校验**；真 DDB 对两条路径都计入 400KB。
# ============================================================================


def _is_ddb_too_large(exc) -> bool:
    """真 DDB item 超 400KB 的 ValidationException 判定（不硬编字节数/次数，躲阈值/版本漂移的 flaky）。"""
    err = exc.value.response.get("Error", {})
    return err.get("Code") == "ValidationException" and "size" in err.get("Message", "").lower()


def test_ddb_state_item_grows_past_400kb_on_incremental_update_real(real_aws):
    """真 DDB：STATE item 经反复 `SET jobs.#sid` 增量长大、整个 item 越过 400KB 时 update_item 抛 ValidationException。

    钉「STATE 控制面 jobs Map 无上限保护」这个真实天花板——**运行态只在 runs 表里**（产物桶里只放提交记录的 jobs 对象），
    jobs 规模撞 400KB 无兜底。moto **只在 put_item 校验 400KB、update_item 增量路径零校验**（实测连刷近 1MB 全 ACCEPT），
    故只有真 DDB 能证。session_id 是 `_job_state_to_item` 里唯一可控放大点（每 entry 塞 ~30KB）。
    """
    from botocore.exceptions import ClientError

    store = _ddb_store(real_aws)
    rid = _uniq("ddb-400k-state")
    real_aws["cleanup_run_id"](rid)  # 撞限那次 update 失败、item 停在 <400KB，仍登记兜底清理

    scope_ids = [f"scope-{i:03d}" for i in range(100)]  # 执行中的写只写运行态里已有的 job：建 run 时先放好（每个条目很小）
    store.create_run(rid_meta := _sample_run(rid).run_meta,
                     RunState(run_id=rid, status=Status.PENDING, jobs={sid: JobState(sid, Status.PENDING) for sid in scope_ids}))
    del rid_meta

    big = "x" * 30000  # 每个 job entry ~30KB（session_id 放大点）；~14 个即越 400KB
    with pytest.raises(ClientError) as exc:
        for sid in scope_ids:  # 硬上限防死循环（远早于此就该撞限）
            store.update_job_state(rid, JobState(sid, Status.RUNNING, session_id=big))
    assert _is_ddb_too_large(exc), f"应因 STATE item 超 400KB 抛 ValidationException，实际 {exc.value}"


def test_ddb_empty_string_scalar_and_map_entry_real(real_aws):
    """真 DDB（2026）空串行为的回归基线：使 run 成为终态的终态写写 ended_at=""（顶层标量 SET）、执行中的写写 session_id=""
    （原生 Map entry 内空串）被接受、读回仍 ""。区分 ""-存（空串）与 None-omit（键消失）两条真代码路径。

    空串是 DDB 史上最著名的 moto/真分叉源。现代真 DDB（2020 后）已放行非 key String 空串，故此测在真 AWS 上
    会通过——它是「把当前真语义固化成回归基线」的 pin 测试（moto 对空串一律 ACCEPT、不能作权威）。
    与 test_ddb_session_id_none_omitted_real（None-omit）互补：`if session_id is not None` vs 收尾时恒 SET ended_at。
    """
    store = _ddb_store(real_aws)
    rid = _uniq("ddb-emptystr")
    real_aws["cleanup_run_id"](rid)

    meta = _sample_run(rid).run_meta
    sid = meta.jobs[0].scope_id
    store.create_run(meta, RunState(run_id=rid, status=Status.PENDING,
                                    jobs={sid: JobState(sid, Status.PENDING)}))
    assert store.update_job_state(rid, JobState(sid, Status.RUNNING, session_id="")) is True  # 空串 Map entry
    # 空串顶层标量；给出的终态不带会话，库中的空串会话保留
    assert store.commit_job_states(rid, [JobState(sid, Status.PASSED)], ended_at="") is CommitOutcome.ENDED_RUN
    # 注：若未来真 DDB 意外改回拒空串，此断言会红——届时改断 pytest.raises 并更新 README 分叉说明。
    final = store.load_run_state(rid)
    assert final.ended_at == ""                       # 空串顶层标量存/读回
    assert final.jobs[sid].session_id == ""            # 空串 Map entry 存/读回
