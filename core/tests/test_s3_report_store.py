"""S3ReportStore 对拍测试（ADR 0030 决定六 / 0027 / 0029）：与 LocalReportStore 同一批行为断言，moto mock、不烧真 AWS。

对拍**后端无关的行为契约**（manifest 形态 = 纯派生视图不内嵌 result、report_index 扁平投影、index.html 渲染判定明细+链接、
空态有效页）——即 test_report_store.py 里那批。物理落点断言从「文件系统路径」换成「S3 对象 get」。

**S3 专属差异 = materialize 当 no-op**（[0029] 第一版取舍）：Local 的 materialize=True 会把本地产物拷进 artifacts/、
改写 href；S3 版收到 materialize=True 也忽略、`href` 恒等 `ref`（不拷贝、不报错）。这条**反向**断言正是本文件的重点。

复用 test_report_store 的 _run_with_refs/_rr/_jr 造数据（同一份 fixture 真理源）。
"""
from __future__ import annotations

import json
from urllib.parse import urlparse

from core.model import ScenarioResult, Status, StepResult
from tests.test_report_store import _jr, _rr, _run_with_refs


def _read_s3(aws, uri: str) -> str:
    """把 write() 返回的 s3:// ResourceUri 取回对象正文（测试侧读内容用）。"""
    p = urlparse(uri)
    assert p.scheme == "s3"
    body = aws["s3"].get_object(Bucket=p.netloc, Key=p.path.lstrip("/"))["Body"].read()
    return body.decode("utf-8")


def _read_manifest(aws, run_id: str, prefix: str = "") -> dict:
    body = aws["s3"].get_object(Bucket=aws["bucket"], Key=f"{prefix}{run_id}/manifest.json")["Body"].read()
    return json.loads(body)


# ---- 写 manifest + index，返回 s3:// ResourceUri（对拍 test_writes_manifest_and_index）----
def test_writes_manifest_and_index(s3_report_store, aws, tmp_path):
    run = _run_with_refs(tmp_path)
    index = s3_report_store.write(run.run_id, run, created_at="2026-06-29T00:00:00Z")

    # 返回 s3:// ResourceUri，指向 index.html
    assert index.startswith(f"s3://{aws['bucket']}/") and index.endswith("/20260629-abc123/index.html")
    # 两个对象都真落了 S3
    listed = aws["s3"].list_objects_v2(Bucket=aws["bucket"], Prefix="20260629-abc123/")
    keys = {o["Key"] for o in listed["Contents"]}
    assert keys == {"20260629-abc123/manifest.json", "20260629-abc123/index.html"}
    # index.html 取得回、非空
    assert "<html" in _read_s3(aws, index).lower()


# ---- manifest 形态（对拍 test_manifest_shape）----
def test_manifest_shape(s3_report_store, aws, tmp_path):
    run = _run_with_refs(tmp_path)
    s3_report_store.write(run.run_id, run, created_at="2026-06-29T00:00:00Z")
    m = _read_manifest(aws, "20260629-abc123")

    assert m["schema_version"] == 1
    assert m["run_id"] == "20260629-abc123"
    assert m["created_at"] == "2026-06-29T00:00:00Z"
    assert "tool" not in m
    # 纯派生视图：不内嵌 result 真值副本（靠 run_id 软引用，[0027]/[0016]）
    assert "result" not in m
    # report_index 扁平投影：scope 级 report（scenario_id=None）+ step 级 trajectory 各一条（对拍 local，ADR 0027）
    idx = m["report_index"]
    assert len(idx) == 2
    report_entry = next(e for e in idx if e["kind"] == "report")
    traj_entry = next(e for e in idx if e["kind"] == "trajectory")
    assert report_entry["scenario_id"] is None and report_entry["step_index"] is None
    assert report_entry["engine"] == "midscene"
    assert traj_entry["scenario_id"] == "features/wiki.feature:6" and traj_entry["step_index"] == 0


# ---- index.html 链接 + 判定明细（对拍 test_index_html_links_and_summary）----
def test_index_html_links_and_summary(s3_report_store, aws, tmp_path):
    run = _run_with_refs(tmp_path)
    idx = s3_report_store.write(run.run_id, run, created_at="x")
    txt = _read_s3(aws, idx)
    assert "20260629-abc123" in txt
    assert "passed" in txt.lower()
    assert "midscene" in txt
    assert "Midscene report" in txt          # label 作锚文本
    assert "[report]" in txt and "[trajectory]" in txt
    assert "判定明细" in txt
    assert "features/wiki.feature:6" in txt   # scenario_id
    assert "step[0]" in txt                   # step 级判定


# ---- 连锁失败旁注在 S3 index.html 对称（复用 local 渲染，ADR 0031 决定六）----
def test_index_html_taints_shortcircuited_step(s3_report_store, aws):
    # S3 版复用 local 的 _render_index_html，taint 行为应自动对称——显式锚住，防未来 S3 分叉出独立渲染。
    run = _rr(
        "chain",
        [_jr("s", "novaact", status=Status.ERROR, scenarios=[
            ScenarioResult(scenario_id="s:0", status=Status.ERROR, steps=[
                StepResult(index=0, status=Status.ERROR, error_type="network_error"),
                StepResult(index=1, status=Status.SKIPPED, shortcircuited=True),  # 被短路 → 旁注
            ]),
        ])],
        status=Status.ERROR,
    )
    txt = _read_s3(aws, s3_report_store.write(run.run_id, run))
    assert "被跳过" in txt and "skipped" in txt


# ---- S3 专属：materialize 当 no-op，href 恒等 ref（对拍/反向 test_default_no_materialize_keeps_ref）----
def test_materialize_is_noop_href_equals_ref(s3_report_store, aws, tmp_path):
    run = _run_with_refs(tmp_path)
    # 即便传 materialize=True，也不拷贝、不报错，href 仍等于 ref（第一版取舍，[0029]）
    s3_report_store.write(run.run_id, run, materialize=True)
    m = _read_manifest(aws, "20260629-abc123")
    for entry in m["report_index"]:
        assert entry["href"] == entry["ref"], f"materialize 应为 no-op，href 不应改写：{entry}"
    # 没有产生 artifacts/ 前缀的对象（没拷贝任何产物）
    listed = aws["s3"].list_objects_v2(Bucket=aws["bucket"], Prefix="20260629-abc123/artifacts/")
    assert listed.get("KeyCount", 0) == 0


# ---- 空 report_refs 仍出有效页（对拍 test_empty_report_refs_still_valid_index）----
def test_empty_report_refs_still_valid_index(s3_report_store, aws):
    run = _rr("empty-run", [_jr("s", "novaact", status=Status.PASSED)], status=Status.PASSED)
    idx = s3_report_store.write(run.run_id, run)
    txt = _read_s3(aws, idx)
    assert "empty-run" in txt
    assert "无引擎报告产物" in txt          # 空态有效页
    m = _read_manifest(aws, "empty-run")
    assert m["report_index"] == []


# ---- key 前缀隔离（S3 专属：多租户/多环境前缀不串）----
def test_prefix_lands_under_prefix(aws, tmp_path):
    from core.adapters.report_store.s3 import S3ReportStore
    store = S3ReportStore(aws["s3"], aws["bucket"], prefix="tenantX/")
    run = _run_with_refs(tmp_path)
    idx = store.write(run.run_id, run, created_at="x")
    # 返回 URI 与实际对象都带前缀
    assert idx == f"s3://{aws['bucket']}/tenantX/20260629-abc123/index.html"
    listed = aws["s3"].list_objects_v2(Bucket=aws["bucket"], Prefix="tenantX/20260629-abc123/")
    keys = {o["Key"] for o in listed["Contents"]}
    assert keys == {"tenantX/20260629-abc123/manifest.json", "tenantX/20260629-abc123/index.html"}
    # 前缀外无泄漏
    assert aws["s3"].list_objects_v2(Bucket=aws["bucket"], Prefix="20260629-abc123/").get("KeyCount", 0) == 0
