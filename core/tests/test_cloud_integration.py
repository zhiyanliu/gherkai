"""云端 adapter 集成测试（@pytest.mark.integration）：连**真** DDB/S3，专测 moto 抓不到的真 AWS 语义。

**默认不跑**（pyproject addopts `-m 'not integration'`）。跑法（见 tests/README.md）：
    export AWS_DDB_TABLE=<你建的真表>  AWS_S3_BUCKET=<你建的真桶>
    uv run pytest -m integration
没设环境变量 → `real_aws` fixture skip（不误连）。用真凭证（default profile），每用例自清理写入的数据。

**为何要连真**：moto 是模拟实现，与真 DDB/S3 在若干边界可能不一致——本文件正是钉这些差异（也是 review
时对抗验证过的疑点）：DDB 空串 SET / 保留字 / 空 Map / `SET jobs.#sid` 单元素刷；S3 中文·斜杠 key 编码 /
`load_all` 全量取回；StepArgument offload 真往返。单测（moto）已覆盖行为契约，这里只补「真后端语义」这一层。
"""
from __future__ import annotations

import itertools

import pytest

from core.model import JobState, RunMeta, RunState, Status
from tests.test_stores import _sample_run

pytestmark = pytest.mark.integration  # 本文件全部用例 = 集成测试（默认 deselect）

_counter = itertools.count(1)  # 单进程内递增，给 run_id 去重


def _uniq(prefix: str) -> str:
    """给真表/真桶造一个本次运行专属的 run_id，避免多次跑撞名（无随机源，用递增计数）。
    跨进程靠 it- 前缀 + fixture 自清理兜底（真资源是你专用的测试表/桶）。"""
    return f"it-{prefix}-{next(_counter)}"


def _ddb_store(real_aws, offloader=None):
    from core.adapters.run_store.ddb import DynamoDBRunStore
    return DynamoDBRunStore(real_aws["ddb"].Table(real_aws["table_name"]), arg_offloader=offloader)


def _s3_result_store(real_aws):
    from core.adapters.result_store.s3 import S3ResultStore
    return S3ResultStore(real_aws["s3"], real_aws["bucket"])


def _offloader(real_aws):
    from core.adapters.run_store.arg_offload import S3StepArgumentOffloader
    return S3StepArgumentOffloader(real_aws["s3"], real_aws["bucket"])


# ---- DynamoDBRunStore：真 DDB 的生命周期 + 真语义边界 ----
def test_ddb_run_store_lifecycle_real(real_aws):
    """真 DDB 上跑完整实时写生命周期：create_run → update_job_state（RUNNING→终态）→ finalize_run → 读回。
    覆盖真语义：空 Map jobs 能存、SET jobs.#sid 单元素刷、finalize 无条件 SET status(保留字)/ended_at、含 /:中文 scope_id。"""
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

    # 各自完成 + finalize（真 DDB 保留字 status/ended_at 的 SET）
    store.update_job_state(rid, JobState(scope_ids[0], Status.PASSED, session_id="sess-real"))
    store.update_job_state(rid, JobState(scope_ids[1], Status.FAILED))
    store.finalize_run(rid, Status.FAILED, "2026-07-01T00:05:00Z")

    final = store.load_run_state(rid)
    assert final.status == Status.FAILED and final.ended_at == "2026-07-01T00:05:00Z"
    assert final.started_at == "2026-07-01T00:00:00Z"  # create 填的起点保留
    assert final.jobs[scope_ids[0]].status == Status.PASSED  # 没被 finalize 覆盖
    # definition 也读回（META item JSON blob 真往返）
    assert store.load_run_meta(rid).jobs[0].scope_id == scope_ids[0]


def test_ddb_update_before_create_raises_real(real_aws):
    """真 DDB：未 create 就 update/finalize → ConditionalCheckFailedException 转 FileNotFoundError（对拍 local 报错语义）。"""
    store = _ddb_store(real_aws)
    rid = _uniq("ddb-nocreate")  # 从不 create，无需登记清理（没写入）
    with pytest.raises(FileNotFoundError):
        store.update_job_state(rid, JobState("s", Status.RUNNING))
    with pytest.raises(FileNotFoundError):
        store.finalize_run(rid, Status.PASSED, "t")


def test_ddb_session_id_none_omitted_real(real_aws):
    """真 DDB：session_id=None omit-when-None，读回仍 None（真 Map entry 缺键的读回语义）。"""
    store = _ddb_store(real_aws)
    rid = _uniq("ddb-nonesess")
    real_aws["cleanup_run_id"](rid)
    meta = _sample_run(rid).run_meta
    store.create_run(meta, RunState(run_id=rid, status=Status.PENDING,
                                    jobs={meta.jobs[0].scope_id: JobState(meta.jobs[0].scope_id, Status.PENDING)}))
    store.update_job_state(rid, JobState(meta.jobs[0].scope_id, Status.ABORTED, session_id=None))
    js = store.load_run_state(rid).jobs[meta.jobs[0].scope_id]
    assert js.status == Status.ABORTED and js.session_id is None


# ---- S3ResultStore：真 S3 的 key 编码 + 全量取回 ----
def test_s3_result_store_round_trip_real(real_aws):
    """真 S3：save/load/load_all round-trip，含 /:中文 scope_id 的 quote 编码在真 S3 不撞名/不造子前缀。"""
    store = _s3_result_store(real_aws)
    rid = _uniq("s3-rt")
    real_aws["cleanup_prefix"](f"{rid}/")  # 登记清理该 run 的所有对象

    run = _sample_run(rid)
    for jr in run.jobs:
        store.save_job_result(rid, jr)

    # 单个读回（含 /:）
    j0 = store.load_job_result(rid, "features/wiki.feature:6")
    assert j0 is not None and j0.engine == "midscene"
    # 中文 scope_id 读回
    j1 = store.load_job_result(rid, "登录场景")
    assert j1 is not None and j1.error_type == "assertion_failed"
    # 全量
    allj = store.load_all(rid)
    assert {jr.scope_id for jr in allj} == {"features/wiki.feature:6", "登录场景"}
    # miss → None
    assert store.load_job_result(rid, "不存在") is None


# ---- StepArgument offload：真 S3 指针往返 ----
def test_offload_round_trip_real(real_aws):
    """真 S3：DdbRunStore 挂 offloader，docString/dataTable 搬真 S3、META 只留指针、读回逐字节还原。"""
    from core.model import Job, Scenario, Step, StepArgument

    store = _ddb_store(real_aws, offloader=_offloader(real_aws))
    rid = _uniq("offload")
    real_aws["cleanup_run_id"](rid)
    real_aws["cleanup_prefix"](f"{rid}/args/")  # offload 对象在 <rid>/args/ 下

    job = Job(scope_id="s", scope_name="s", engine="midscene", scenarios=(
        Scenario(id="s:1", name="sc", steps=(
            Step(0, "When", "填表", StepArgument(kind="dataTable", rows=(("k", "v"), ("", "空cell")))),
            Step(1, "Then", "看", StepArgument(kind="docString", content="多行\n正文\ns3://像指针的正文")),
        )),
    ))
    meta = RunMeta(run_id=rid, created_at="t", jobs=(job,))
    store.create_run(meta, RunState(run_id=rid, status=Status.PENDING, jobs={}))  # 空 Map jobs 真表可存

    got = store.load_run_meta(rid)
    arg0 = got.jobs[0].scenarios[0].steps[0].argument
    arg1 = got.jobs[0].scenarios[0].steps[1].argument
    assert arg0.rows == (("k", "v"), ("", "空cell"))          # 空 cell 保留
    assert arg1.content == "多行\n正文\ns3://像指针的正文"    # 正文以 s3:// 开头也逐字节还原（非值探测）


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

    钉「STATE 控制面 jobs Map 无上限保护」这个真实天花板——**STATE 路径从不 offload**（offloader 只挂 META），
    jobs 规模撞 400KB 无兜底。moto **只在 put_item 校验 400KB、update_item 增量路径零校验**（实测连刷近 1MB 全 ACCEPT），
    故只有真 DDB 能证。session_id 是 `_job_state_to_item` 里唯一可控放大点（每 entry 塞 ~30KB）。
    """
    from botocore.exceptions import ClientError

    store = _ddb_store(real_aws)
    rid = _uniq("ddb-400k-state")
    real_aws["cleanup_run_id"](rid)  # 撞限那次 update 失败、item 停在 <400KB，仍登记兜底清理

    store.create_run(rid_meta := _sample_run(rid).run_meta,
                     RunState(run_id=rid, status=Status.PENDING, jobs={}))  # 空 Map STATE 起步
    del rid_meta

    big = "x" * 30000  # 每个 job entry ~30KB（session_id 放大点）；~14 个即越 400KB
    with pytest.raises(ClientError) as exc:
        for i in range(100):  # 硬上限防死循环（远早于此就该撞限）
            store.update_job_state(rid, JobState(f"scope-{i:03d}", Status.PASSED, session_id=big))
    assert _is_ddb_too_large(exc), f"应因 STATE item 超 400KB 抛 ValidationException，实际 {exc.value}"


def test_offload_unblocks_oversized_docstring_real(real_aws):
    """真 DDB+S3 因果闭环：含 >400KB docString 的 RunMeta——不挂 offloader 时 create_run 撞 400KB 抛错；
    挂 offloader 时同一 meta 成功、META 只留 s3:// 指针、load_run_meta 逐字节还原。

    这是 offloader 存在的根本理由（解 DDB 400KB 限）的端到端证成——补 test_offload_round_trip_real 缺的下半句
    （它只证小 docString 能还原字节，从没证「无 offload 撞限 / 有 offload 解限」）。moto 双 mock 证不了真尺寸边界
    与「解限」这对因果（真 DDB 逐字节精确计量 + 中文 UTF-8 多字节，moto 近似阈值不对齐）。
    """
    from botocore.exceptions import ClientError
    from core.model import Job, Scenario, Step, StepArgument

    huge = "x" * (500 * 1024)  # 远超 400KB（规避 moto 近似阈值歧义，非贴边）
    job = Job(scope_id="s", scope_name="s", engine="midscene", scenarios=(
        Scenario(id="s:1", name="sc", steps=(
            Step(0, "Given", "巨型正文", StepArgument(kind="docString", content=huge)),
        )),
    ))

    # 分支 A：不挂 offloader → put_item META（500KB）先于 STATE，撞 400KB 抛 ValidationException（无 STATE 残留）
    rid_a = _uniq("offload-A-nooffload")
    real_aws["cleanup_run_id"](rid_a)
    store_a = _ddb_store(real_aws)  # offloader=None
    meta_a = RunMeta(run_id=rid_a, created_at="t", jobs=(job,))
    with pytest.raises(ClientError) as exc:
        store_a.create_run(meta_a, RunState(run_id=rid_a, status=Status.PENDING, jobs={}))
    assert _is_ddb_too_large(exc), f"无 offload 时 500KB META 应撞 400KB，实际 {exc.value}"

    # 分支 B：挂真 S3 offloader → 同一 meta create_run 成功、META 只留指针、load 逐字节还原
    rid_b = _uniq("offload-B-offloaded")
    real_aws["cleanup_run_id"](rid_b)
    real_aws["cleanup_prefix"](f"{rid_b}/args/")
    store_b = _ddb_store(real_aws, offloader=_offloader(real_aws))
    meta_b = RunMeta(run_id=rid_b, created_at="t", jobs=(job,))
    store_b.create_run(meta_b, RunState(run_id=rid_b, status=Status.PENDING, jobs={}))  # 不再撞限

    # 强断言：读原始 META item，证正文确实搬走（含 content_ref / s3://）且 META 远 <400KB（非仅"写成功"）
    raw = real_aws["ddb"].Table(real_aws["table_name"]).get_item(
        Key={"run_id": rid_b, "sk": "META"}, ConsistentRead=True)["Item"]
    meta_json = raw["meta_json"]
    assert "content_ref" in meta_json and "s3://" in meta_json
    assert len(meta_json.encode("utf-8")) < 400 * 1024, "META 应因 offload 远小于 400KB"
    # 逐字节还原
    restored = store_b.load_run_meta(rid_b)
    assert restored.jobs[0].scenarios[0].steps[0].argument.content == huge


def test_ddb_empty_string_scalar_and_map_entry_real(real_aws):
    """真 DDB（2026）空串行为的回归基线：finalize 写 ended_at=""（顶层标量 SET）、update 写 session_id=""
    （原生 Map entry 内空串）被接受、读回仍 ""。区分 ""-存（空串）与 None-omit（键消失）两条真代码路径。

    空串是 DDB 史上最著名的 moto/真分叉源。现代真 DDB（2020 后）已放行非 key String 空串，故此测在真 AWS 上
    会通过——它是「把当前真语义固化成回归基线」的 pin 测试（moto 对空串一律 ACCEPT、不能作权威）。
    与 test_ddb_session_id_none_omitted_real（None-omit）互补：`if session_id is not None` vs finalize 无条件 SET ended_at。
    """
    store = _ddb_store(real_aws)
    rid = _uniq("ddb-emptystr")
    real_aws["cleanup_run_id"](rid)

    meta = _sample_run(rid).run_meta
    sid = meta.jobs[0].scope_id
    store.create_run(meta, RunState(run_id=rid, status=Status.PENDING,
                                    jobs={sid: JobState(sid, Status.PENDING)}))
    store.update_job_state(rid, JobState(sid, Status.PASSED, session_id=""))  # 空串 Map entry
    store.finalize_run(rid, Status.PASSED, ended_at="")                        # 空串顶层标量
    # 注：若未来真 DDB 意外改回拒空串，此断言会红——届时改断 pytest.raises 并更新 README 分叉说明。
    final = store.load_run_state(rid)
    assert final.ended_at == ""                       # 空串顶层标量存/读回
    assert final.jobs[sid].session_id == ""            # 空串 Map entry 存/读回
