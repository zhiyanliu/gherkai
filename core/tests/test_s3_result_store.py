"""S3ResultStore 对拍测试（ADR 0030 决定六 / 0016）：与 LocalResultStore 同一批行为断言，moto mock、不烧真 AWS。

对拍后端无关的行为契约（save/load/load_all round-trip、自包含、scope_id 不透明编码不撞名/不逃逸）——
即 test_stores.py 里 LocalResultStore 那批。物理落点断言（文件系统 glob）是 local 专属、换成 S3 的 list/key 断言。
"""
from __future__ import annotations

from urllib.parse import quote

from core.model import JobResult, Status
from tests.test_stores import _job_def, _sample_run


# ---- save/load/load_all round-trip（对拍 test_result_store_save_load_job）----
def test_save_load_round_trip(s3_result_store, aws):
    r = _sample_run("run-2")
    for jr in r.jobs:
        s3_result_store.save_job_result("run-2", jr)

    # 含 /:中文 的 scope_id 都成一个 S3 对象（每 job 一个）
    listed = aws["s3"].list_objects_v2(Bucket=aws["bucket"], Prefix="run-2/jobs/")
    assert listed["KeyCount"] == 2

    # 读回单 job（判定真值 + definition 完整、自包含）
    j0 = s3_result_store.load_job_result("run-2", "features/wiki.feature:6")
    assert j0 is not None and j0.engine == "midscene" and j0.scope_name == "wiki"
    assert j0.job.scenarios[0].steps[1].text == "搜索 OpenAI"  # 嵌完整 def
    j1 = s3_result_store.load_job_result("run-2", "登录场景")
    assert j1 is not None and j1.error_type == "assertion_failed"

    # 读回全部
    allj = s3_result_store.load_all("run-2")
    assert len(allj) == 2
    assert {jr.scope_id for jr in allj} == {"features/wiki.feature:6", "登录场景"}


def test_load_missing_returns_none(s3_result_store):
    assert s3_result_store.load_job_result("nope", "s") is None
    assert s3_result_store.load_all("nope") == []


def test_scope_id_with_slash_not_subprefix(s3_result_store, aws):
    # scope_id 含 / 被 quote 成 %2F、恒是单段 key，不在 S3 里造假子前缀、load_all 不歧义
    # （对拍 test_result_store_scope_id_not_path_traversal）
    jr = JobResult(job=_job_def("a/b/c:9", "anchor", "midscene"), status=Status.PASSED)
    s3_result_store.save_job_result("run-3", jr)

    listed = aws["s3"].list_objects_v2(Bucket=aws["bucket"], Prefix="run-3/jobs/")
    keys = [o["Key"] for o in listed["Contents"]]
    assert len(keys) == 1
    # key 里 scope_id 段无裸 /（被编码成 %2F），jobs/ 下只有一层、无子目录
    scope_seg = keys[0][len("run-3/jobs/"):-len(".json")]
    assert "/" not in scope_seg and scope_seg == quote("a/b/c:9", safe="")
    # 按原始 scope_id 读得回、且 scope_id 原样还原
    assert s3_result_store.load_job_result("run-3", "a/b/c:9").scope_id == "a/b/c:9"


def test_load_all_stable_order(s3_result_store):
    # load_all 按 key 排序、稳定输出（对拍 local 的 sorted glob）
    for sid in ("c-scope", "a-scope", "b-scope"):
        s3_result_store.save_job_result("run-ord", JobResult(job=_job_def(sid, sid, "midscene"), status=Status.PASSED))
    got = [jr.scope_id for jr in s3_result_store.load_all("run-ord")]
    assert got == sorted(got)  # 稳定（按 quote(scope_id) key 序）


def test_prefix_isolates_runs(aws):
    # 带 key 前缀时不同 run 互不串（load_all 只按本 run 的 prefix 列）
    from core.adapters.result_store.s3 import S3ResultStore
    store = S3ResultStore(aws["s3"], aws["bucket"], prefix="tenantX/")
    store.save_job_result("rA", JobResult(job=_job_def("s", "s", "midscene"), status=Status.PASSED))
    store.save_job_result("rB", JobResult(job=_job_def("s", "s", "novaact"), status=Status.FAILED))
    assert len(store.load_all("rA")) == 1 and len(store.load_all("rB")) == 1
    assert store.load_all("rA")[0].engine == "midscene"
    # 前缀确实进了 key
    listed = aws["s3"].list_objects_v2(Bucket=aws["bucket"], Prefix="tenantX/rA/jobs/")
    assert listed["KeyCount"] == 1
