"""cli --backend cloud 接线层测试（ADR 0016「cli backend 选择」/ 0030 决定七）。

**只验接线，不引 moto、不连真 AWS**：adapter 行为已由 core 包 moto 全覆盖，cli 再测是重复且破窄腰。
做法——patch `compose._make_ddb_table`/`_make_s3_client` 返回**记录调用的 fake 句柄**，验证：
- backend=cloud 构造了正确 adapter：DDB 拿 table 句柄、三个 S3 件套（Result/Report/offloader）**共享同一个** client；
- offloader 已挂（RunMeta 写走 offload 路径）；
- 缺 table/bucket → 退 2；缺 boto3（import 失败）→ 退 2；preflight 失败 → 退 2；运行期 botocore 异常 → 退 1；
- cloud + --no-report → 跳过一切云端（钩子一次不调）；
- artifacts 在 cloud 下是 s3://+ddb:// 形态。
"""
from __future__ import annotations

import json
from pathlib import Path

from core.model import JobResult, RunResult, ScopeStarted, Status

from cli import __main__ as m


def _write_feature(tmp_path: Path) -> Path:
    feat = tmp_path / "demo.feature"
    feat.write_text("Feature: demo\n  Scenario: s\n    When \"做点啥\"\n", encoding="utf-8")
    return feat


def _fake_schedule_factory():
    """不起 worker 的假 schedule：走完 on_event/on_job_complete 实时落库路径（让 adapter 真被调）。"""
    def fake_schedule(run_meta, engines, sink, opts=None, on_job_complete=None, on_event=None):
        results = []
        for j in run_meta.jobs:
            ev = ScopeStarted(scope_id=j.scope_id)
            sink(ev)
            if on_event is not None:
                on_event(ev)
            jr = JobResult(job=j, status=Status.PASSED)
            results.append(jr)
            if on_job_complete is not None:
                on_job_complete(jr)
        return RunResult(run_meta=run_meta, status=Status.PASSED, jobs=results)
    return fake_schedule


# ---- fake boto3 句柄：记录关键调用，不连真 AWS ----
class _FakeTable:
    """假 DDB table 句柄：DynamoDBRunStore 吃它（put_item/update_item/get_item/load/meta.client.exceptions）。"""
    def __init__(self, record):
        self._record = record
        self.meta = type("Meta", (), {"client": type("C", (), {"exceptions": type("E", (), {
            "ConditionalCheckFailedException": type("CCFE", (Exception,), {})})()})()})()

    def load(self): self._record.append(("ddb", "load"))          # preflight 探表
    def put_item(self, **kw): self._record.append(("ddb", "put_item"))
    def update_item(self, **kw): self._record.append(("ddb", "update_item"))
    def get_item(self, **kw):
        self._record.append(("ddb", "get_item"))
        return {}  # 读回空（begin 只写不读；此处防御）


class _FakeS3:
    """假 S3 client：三个件套共享一个；记录 head_bucket（preflight）/put_object。"""
    def __init__(self, record):
        self._record = record
        self.id = id(self)  # 用于断言「三个件套拿的是同一个 client」

    def head_bucket(self, **kw): self._record.append(("s3", "head_bucket"))
    def put_object(self, **kw): self._record.append(("s3", "put_object"))


def _patch_cloud_handles(monkeypatch, record):
    """patch compose 的两个 boto3 钩子，返回记录调用的 fake（不连真 AWS）。返回创建的 s3 fake 供同一性断言。"""
    fake_s3 = _FakeS3(record)
    made = {"ddb_tables": [], "s3_clients": []}

    def fake_make_ddb(table, *, region, profile):
        record.append(("make", "ddb_table", table, region, profile))
        t = _FakeTable(record)
        made["ddb_tables"].append(t)
        return t

    def fake_make_s3(*, region, profile):
        record.append(("make", "s3_client", region, profile))
        made["s3_clients"].append(fake_s3)
        return fake_s3

    monkeypatch.setattr(m.compose, "_make_ddb_table", fake_make_ddb)
    monkeypatch.setattr(m.compose, "_make_s3_client", fake_make_s3)
    return fake_s3, made


# ---- backend=cloud 构造正确 adapter + 参数 + offloader 挂 + S3 client 同一性 ----
def test_cloud_wires_stores_with_correct_handles(tmp_path, monkeypatch, capsys):
    record: list = []
    fake_s3, made = _patch_cloud_handles(monkeypatch, record)
    monkeypatch.setattr(m, "schedule", _fake_schedule_factory())

    rc = m.main(["run", str(_write_feature(tmp_path)), "--backend", "cloud",
                 "--ddb-table", "T", "--s3-bucket", "B", "--region", "us-east-1", "--quiet", "--json"])
    assert rc == 0

    # 钩子按参数被调：ddb 用表名 T、s3 只造一次（三件套共享）
    ddb_makes = [r for r in record if r[:2] == ("make", "ddb_table")]
    s3_makes = [r for r in record if r[:2] == ("make", "s3_client")]
    assert ddb_makes == [("make", "ddb_table", "T", "us-east-1", None)]
    assert len(s3_makes) == 1, "S3 client 只该造一次（三个件套共享）"
    assert len(made["s3_clients"]) == 1 and made["s3_clients"][0] is fake_s3
    # preflight 探活：DDB load + S3 head_bucket 都发生了（begin 先探活）
    assert ("ddb", "load") in record
    assert ("s3", "head_bucket") in record
    # 落库真发生（put_item 写 DDB、put_object 写 S3）——证 adapter 真拿到可用句柄
    assert ("ddb", "put_item") in record
    assert ("s3", "put_object") in record


def test_cloud_offloader_attached(tmp_path, monkeypatch, capsys):
    # offloader 挂载验证：含 docString 的 feature，RunMeta 写会触发 offloader put_object 到 args/ 路径。
    record: list = []
    _patch_cloud_handles(monkeypatch, record)
    monkeypatch.setattr(m, "schedule", _fake_schedule_factory())
    feat = tmp_path / "d.feature"
    feat.write_text('Feature: F\n  Scenario: s\n    When "做" \n      """\n      多行正文\n      """\n', encoding="utf-8")

    rc = m.main(["run", str(feat), "--backend", "cloud", "--ddb-table", "T", "--s3-bucket", "B",
                 "--region", "us-east-1", "--quiet"])
    assert rc == 0
    # offloader 挂了 → create_run 写 META 前把 docString 搬 S3（args/ 对象），故有 put_object
    assert ("s3", "put_object") in record


# ---- 配置缺失 / boto3 缺 → 退 2 ----
def test_cloud_missing_table_or_bucket_exits_2(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(m, "schedule", _fake_schedule_factory())
    monkeypatch.delenv("AWS_DDB_TABLE", raising=False)
    monkeypatch.delenv("AWS_S3_BUCKET", raising=False)
    # 缺 bucket
    rc = m.main(["run", str(_write_feature(tmp_path)), "--backend", "cloud", "--ddb-table", "T", "--quiet"])
    assert rc == 2
    assert "缺必需配置" in capsys.readouterr().err
    # 缺 table
    rc = m.main(["run", str(_write_feature(tmp_path)), "--backend", "cloud", "--s3-bucket", "B", "--quiet"])
    assert rc == 2


def test_cloud_table_bucket_from_env(tmp_path, monkeypatch, capsys):
    # 环境变量兜底：AWS_DDB_TABLE/AWS_S3_BUCKET 供值时无需 flag
    record: list = []
    _patch_cloud_handles(monkeypatch, record)
    monkeypatch.setattr(m, "schedule", _fake_schedule_factory())
    monkeypatch.setenv("AWS_DDB_TABLE", "ET")
    monkeypatch.setenv("AWS_S3_BUCKET", "EB")
    rc = m.main(["run", str(_write_feature(tmp_path)), "--backend", "cloud", "--region", "us-east-1", "--quiet"])
    assert rc == 0
    assert ("make", "ddb_table", "ET", "us-east-1", None) in record


def test_cloud_missing_boto3_exits_2(tmp_path, monkeypatch, capsys):
    # 缺 boto3：build_cloud_stores 的钩子 import boto3 抛 ImportError → 退 2 + 提示装 core[aws]
    monkeypatch.setattr(m, "schedule", _fake_schedule_factory())
    def boom_import(*a, **k):
        raise ImportError("No module named 'boto3'")
    monkeypatch.setattr(m.compose, "_make_ddb_table", boom_import)
    rc = m.main(["run", str(_write_feature(tmp_path)), "--backend", "cloud",
                 "--ddb-table", "T", "--s3-bucket", "B", "--quiet"])
    assert rc == 2
    assert "boto3" in capsys.readouterr().err


# ---- preflight 失败（begin 前云端不可达）→ 退 2 ----
def test_cloud_preflight_failure_exits_2(tmp_path, monkeypatch, capsys):
    # 桶不存在/无权限：head_bucket 抛 botocore ClientError → begin 的 preflight 暴露 → 退 2
    from botocore.exceptions import ClientError
    record: list = []
    fake_s3, _ = _patch_cloud_handles(monkeypatch, record)
    def boom_head(**kw):
        raise ClientError({"Error": {"Code": "404", "Message": "Not Found"}}, "HeadBucket")
    monkeypatch.setattr(fake_s3, "head_bucket", boom_head)
    monkeypatch.setattr(m, "schedule", _fake_schedule_factory())
    rc = m.main(["run", str(_write_feature(tmp_path)), "--backend", "cloud",
                 "--ddb-table", "T", "--s3-bucket", "B", "--region", "us-east-1", "--quiet"])
    assert rc == 2
    assert "云端不可达" in capsys.readouterr().err


# ---- 运行期 botocore 异常（run 已开跑）→ 退 1 ----
def test_cloud_runtime_botocore_error_exits_1(tmp_path, monkeypatch, capsys):
    # schedule 运行期落库回调抛 botocore 异常（如桶被删）→ 退 1（error 级，run 已开跑）
    from botocore.exceptions import ClientError
    record: list = []
    _patch_cloud_handles(monkeypatch, record)

    def boom_schedule(run_meta, resolver, sink, opts=None, on_job_complete=None, on_event=None):
        # 模拟 schedule 内部落库回调抛 botocore 异常后冒泡（决定三：stop worker 后重抛）
        raise ClientError({"Error": {"Code": "NoSuchBucket", "Message": "gone"}}, "PutObject")
    monkeypatch.setattr(m, "schedule", boom_schedule)
    rc = m.main(["run", str(_write_feature(tmp_path)), "--backend", "cloud",
                 "--ddb-table", "T", "--s3-bucket", "B", "--region", "us-east-1", "--quiet"])
    assert rc == 1
    assert "运行期落库失败" in capsys.readouterr().err


# ---- cloud + --no-report：跳过一切云端（钩子一次不调）----
def test_cloud_no_report_skips_all_cloud(tmp_path, monkeypatch, capsys):
    record: list = []
    _patch_cloud_handles(monkeypatch, record)
    monkeypatch.setattr(m, "schedule", _fake_schedule_factory())
    rc = m.main(["run", str(_write_feature(tmp_path)), "--backend", "cloud", "--no-report", "--quiet"])
    assert rc == 0
    # 没有任何云端钩子被调（need_cloud=False）——即便没给 table/bucket 也不报错（逃生舱）
    assert not any(r[0] == "make" for r in record)


# ---- artifacts cloud 下是 s3://+ddb:// 形态 ----
def test_cloud_artifacts_are_s3_and_ddb_uris(tmp_path, monkeypatch, capsys):
    record: list = []
    _patch_cloud_handles(monkeypatch, record)
    monkeypatch.setattr(m, "schedule", _fake_schedule_factory())
    rc = m.main(["run", str(_write_feature(tmp_path)), "--backend", "cloud",
                 "--ddb-table", "T", "--s3-bucket", "B", "--report-dir", "runs",
                 "--region", "us-east-1", "--json"])
    assert rc == 0
    doc = json.loads(capsys.readouterr().out)
    art = doc["artifacts"]
    # jobs_dir/report_index = s3://；run_meta/run_state = ddb:// 诊断指针
    assert art["jobs_dir"].startswith("s3://B/runs/") and art["jobs_dir"].endswith("/jobs/")
    assert art["run_meta"].startswith("ddb://T/") and art["run_meta"].endswith("#META")
    assert art["run_state"].endswith("#STATE")
    assert art["report_index"].startswith("s3://B/")  # S3ReportStore.write 返回的 s3:// index
