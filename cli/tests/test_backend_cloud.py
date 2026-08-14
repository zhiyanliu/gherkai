"""cli --backend cloud 接线层测试（ADR 0016「cli backend 选择」/ 0030 决定七 / 0033 IaC+接线）。

**只验接线，不引 moto、不连真 AWS**：adapter 行为已由 core 包 moto 全覆盖，cli 再测是重复且破窄腰。
做法——patch `compose._make_ddb_table`/`_make_s3_client`（store 句柄）+ `preflight_cloud_resources`（探活）
+ `build_fargate_engines`（cloud 执行）返回**记录调用的 fake**，验证：
- backend=cloud 构造了正确 store adapter：DDB 拿 table 句柄、三个 S3 件套共享同一个 client、offloader 挂；
- **prefix 两层命名（ADR 0033）**：--prefix 批量推导默认名（{prefix}runs/artifacts/events/cluster）、单资源 --xxx 覆盖；
- **preflight fail-fast**：资源不存在退 2 + 错误点名 prefix；
- **cloud ⇒ FargateEngine（决策 A）**：cloud 走 build_fargate_engines（非 build_engines）；
- 缺 boto3 → 退 2；运行期 botocore 异常 → 退 1；cloud + --no-report → 跳过一切云端 + 走 subprocess（逃生舱）；
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

    def load(self): self._record.append(("ddb", "load"))          # begin 探活
    def put_item(self, **kw): self._record.append(("ddb", "put_item"))
    def update_item(self, **kw): self._record.append(("ddb", "update_item"))
    def get_item(self, **kw):
        self._record.append(("ddb", "get_item"))
        return {}  # 读回空（begin 只写不读；此处防御）


class _FakeS3:
    """假 S3 client：三个件套共享一个；记录 head_bucket（begin 探活）/put_object。"""
    def __init__(self, record):
        self._record = record
        self.id = id(self)  # 用于断言「三个件套拿的是同一个 client」

    def head_bucket(self, **kw): self._record.append(("s3", "head_bucket"))
    def put_object(self, **kw): self._record.append(("s3", "put_object"))


def _patch_cloud_handles(monkeypatch, record, *, preflight_err=None):
    """patch store 钩子 + preflight（默认放行）返回记录调用的 fake（不连真 AWS）。

    preflight_cloud_resources 默认 patch 成返回 preflight_err（None=资源都在、放行）——它自己建 boto client 探活，
    测试里不真探，只验「接线调它 + 它的返回决定退 2」。返回 (fake_s3, made, preflight_calls)。
    """
    fake_s3 = _FakeS3(record)
    made = {"ddb_tables": [], "s3_clients": [], "fargate": []}
    preflight_calls = []

    def fake_make_ddb(table, *, region, profile):
        record.append(("make", "ddb_table", table, region, profile))
        t = _FakeTable(record)
        made["ddb_tables"].append(t)
        return t

    def fake_make_s3(*, region, profile):
        record.append(("make", "s3_client", region, profile))
        made["s3_clients"].append(fake_s3)
        return fake_s3

    def fake_preflight(**kwargs):
        preflight_calls.append(kwargs)
        return preflight_err

    def fake_resolve_network(**kwargs):
        return {"subnets": ["subnet-x"], "securityGroups": ["sg-x"], "assignPublicIp": "ENABLED"}

    def fake_build_fargate(**kwargs):
        made["fargate"].append(kwargs)
        return {"novaact": object(), "midscene": object()}  # 假 engine dict（fake_schedule 不真用）

    monkeypatch.setattr(m.compose, "_make_ddb_table", fake_make_ddb)
    monkeypatch.setattr(m.compose, "_make_s3_client", fake_make_s3)
    monkeypatch.setattr(m.compose, "preflight_cloud_resources", fake_preflight)
    monkeypatch.setattr(m.compose, "resolve_network", fake_resolve_network)
    monkeypatch.setattr(m.compose, "build_fargate_engines", fake_build_fargate)
    return fake_s3, made, preflight_calls


# ---- backend=cloud 构造正确 store adapter + 参数 + offloader 挂 + S3 client 同一性 ----
def test_cloud_wires_stores_with_correct_handles(tmp_path, monkeypatch, capsys):
    record: list = []
    fake_s3, made, _ = _patch_cloud_handles(monkeypatch, record)
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
    # begin 探活：DDB load + S3 head_bucket 都发生了
    assert ("ddb", "load") in record
    assert ("s3", "head_bucket") in record
    # 落库真发生（put_item 写 DDB、put_object 写 S3）——证 store adapter 真拿到可用句柄
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
    assert ("s3", "put_object") in record


# ---- 两层命名（ADR 0033）：prefix 批量推导默认名 + 单资源覆盖 ----
def test_cloud_prefix_derives_default_names(tmp_path, monkeypatch, capsys):
    # 不给 --ddb-table/--s3-bucket/--events-table/--cluster：全走 prefix 推导（默认 gherkai-）。
    record: list = []
    _, made, preflight_calls = _patch_cloud_handles(monkeypatch, record)
    monkeypatch.setattr(m, "schedule", _fake_schedule_factory())
    monkeypatch.delenv("AWS_DDB_TABLE", raising=False)
    monkeypatch.delenv("AWS_S3_BUCKET", raising=False)
    monkeypatch.delenv("AWS_RESOURCE_PREFIX", raising=False)

    rc = m.main(["run", str(_write_feature(tmp_path)), "--backend", "cloud",
                 "--region", "us-east-1", "--quiet", "--json"])
    assert rc == 0
    # RunStore 表 = gherkai-runs（prefix 默认推导）
    assert ("make", "ddb_table", "gherkai-runs", "us-east-1", None) in record
    # preflight 拿到全套 prefix 推导名
    pf = preflight_calls[0]
    assert pf["prefix"] == "gherkai-"
    assert pf["runs_table"] == "gherkai-runs"
    assert pf["events_table"] == "gherkai-events"
    assert pf["bucket"] == "gherkai-artifacts"
    assert pf["cluster"] == "gherkai-cluster"
    # task-def 按本 run 实际用到的引擎探（feature 未标 @engine → default novaact，ADR 0033 preflight 条）
    assert pf["task_defs"] == ["gherkai-novaact-worker"]
    assert pf.get("lambda_fns") is None  # 同步 run 进程内推进、不依赖事件驱动链 → 不探 Lambda


def test_cloud_prefix_custom_switches_whole_set(tmp_path, monkeypatch, capsys):
    # --prefix prod- 一键切整套默认名（多环境）。
    record: list = []
    _, _, preflight_calls = _patch_cloud_handles(monkeypatch, record)
    monkeypatch.setattr(m, "schedule", _fake_schedule_factory())
    monkeypatch.delenv("AWS_DDB_TABLE", raising=False)
    monkeypatch.delenv("AWS_S3_BUCKET", raising=False)

    rc = m.main(["run", str(_write_feature(tmp_path)), "--backend", "cloud", "--prefix", "prod-",
                 "--region", "us-east-1", "--quiet"])
    assert rc == 0
    pf = preflight_calls[0]
    assert pf["prefix"] == "prod-"
    assert pf["runs_table"] == "prod-runs" and pf["events_table"] == "prod-events"
    assert pf["bucket"] == "prod-artifacts" and pf["cluster"] == "prod-cluster"


def test_cloud_single_resource_override_beats_prefix(tmp_path, monkeypatch, capsys):
    # 单资源 --xxx 覆盖：给完整终值，prefix 自然不参与（覆盖不走「拼默认名」路径，无特判）。
    record: list = []
    _, _, preflight_calls = _patch_cloud_handles(monkeypatch, record)
    monkeypatch.setattr(m, "schedule", _fake_schedule_factory())
    monkeypatch.delenv("AWS_DDB_TABLE", raising=False)
    monkeypatch.delenv("AWS_S3_BUCKET", raising=False)

    rc = m.main(["run", str(_write_feature(tmp_path)), "--backend", "cloud", "--prefix", "prod-",
                 "--ddb-table", "custom-runs", "--events-table", "custom-events",
                 "--region", "us-east-1", "--quiet"])
    assert rc == 0
    pf = preflight_calls[0]
    assert pf["runs_table"] == "custom-runs"      # 覆盖，非 prod-runs
    assert pf["events_table"] == "custom-events"  # 覆盖
    assert pf["bucket"] == "prod-artifacts"       # 未覆盖 → 仍走 prefix
    assert pf["cluster"] == "prod-cluster"


def test_cloud_table_bucket_from_env(tmp_path, monkeypatch, capsys):
    # 环境变量兜底：AWS_DDB_TABLE/AWS_S3_BUCKET 供值时无需 flag（优先级：flag > env > prefix 推导）
    record: list = []
    _patch_cloud_handles(monkeypatch, record)
    monkeypatch.setattr(m, "schedule", _fake_schedule_factory())
    monkeypatch.setenv("AWS_DDB_TABLE", "ET")
    monkeypatch.setenv("AWS_S3_BUCKET", "EB")
    rc = m.main(["run", str(_write_feature(tmp_path)), "--backend", "cloud", "--region", "us-east-1", "--quiet"])
    assert rc == 0
    assert ("make", "ddb_table", "ET", "us-east-1", None) in record


def test_cloud_missing_boto3_exits_2(tmp_path, monkeypatch, capsys):
    # 缺 boto3：preflight 的 import boto3 抛 ImportError → 退 2 + 提示装 core[aws]
    monkeypatch.setattr(m, "schedule", _fake_schedule_factory())
    def boom_import(**k):
        raise ImportError("No module named 'boto3'")
    monkeypatch.setattr(m.compose, "preflight_cloud_resources", boom_import)
    rc = m.main(["run", str(_write_feature(tmp_path)), "--backend", "cloud",
                 "--ddb-table", "T", "--s3-bucket", "B", "--region", "us-east-1", "--quiet"])
    assert rc == 2
    assert "boto3" in capsys.readouterr().err


# ---- preflight fail-fast：资源不存在 → 退 2 + 错误点名 prefix ----
def test_cloud_preflight_missing_resource_exits_2_names_prefix(tmp_path, monkeypatch, capsys):
    # preflight 返回非 None（某资源不存在）→ 退 2，错误串含 prefix（引导「prefix 配错/CDK 没部署」）。
    record: list = []
    _patch_cloud_handles(monkeypatch, record,
                         preflight_err="--backend cloud 资源缺失：DynamoDB 表 gherkai-events（用 --prefix='gherkai-' 拼出）不存在——是 --prefix 配错、还是 iac_aws_backend（CDK）未部署？")
    monkeypatch.setattr(m, "schedule", _fake_schedule_factory())
    rc = m.main(["run", str(_write_feature(tmp_path)), "--backend", "cloud",
                 "--region", "us-east-1", "--quiet"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "资源缺失" in err and "--prefix" in err and "CDK" in err


# ---- begin 探活失败（store 不可达）→ 退 2 ----
def test_cloud_begin_probe_failure_exits_2(tmp_path, monkeypatch, capsys):
    # preflight 放行但 begin 的 head_bucket 抛 botocore（如权限）→ 退 2。
    from botocore.exceptions import ClientError
    record: list = []
    fake_s3, _, _ = _patch_cloud_handles(monkeypatch, record)
    def boom_head(**kw):
        raise ClientError({"Error": {"Code": "403", "Message": "Forbidden"}}, "HeadBucket")
    monkeypatch.setattr(fake_s3, "head_bucket", boom_head)
    monkeypatch.setattr(m, "schedule", _fake_schedule_factory())
    rc = m.main(["run", str(_write_feature(tmp_path)), "--backend", "cloud",
                 "--ddb-table", "T", "--s3-bucket", "B", "--region", "us-east-1", "--quiet"])
    assert rc == 2
    assert "云端不可达" in capsys.readouterr().err


# ---- 运行期 botocore 异常（run 已开跑）→ 退 1 ----
def test_cloud_runtime_botocore_error_exits_1(tmp_path, monkeypatch, capsys):
    from botocore.exceptions import ClientError
    record: list = []
    _patch_cloud_handles(monkeypatch, record)

    def boom_schedule(run_meta, resolver, sink, opts=None, on_job_complete=None, on_event=None):
        raise ClientError({"Error": {"Code": "NoSuchBucket", "Message": "gone"}}, "PutObject")
    monkeypatch.setattr(m, "schedule", boom_schedule)
    rc = m.main(["run", str(_write_feature(tmp_path)), "--backend", "cloud",
                 "--ddb-table", "T", "--s3-bucket", "B", "--region", "us-east-1", "--quiet"])
    assert rc == 1
    assert "运行期落库失败" in capsys.readouterr().err


# ---- cloud ⇒ FargateEngine（决策 A，ADR 0016/0033）----
def test_cloud_wires_fargate_engines(tmp_path, monkeypatch, capsys):
    # cloud 走 build_fargate_engines（非 build_engines）——决策 A 落到 CLI。验注入的参数正确。
    record: list = []
    _, made, _ = _patch_cloud_handles(monkeypatch, record)
    monkeypatch.setattr(m, "schedule", _fake_schedule_factory())
    monkeypatch.delenv("AWS_DDB_TABLE", raising=False)
    monkeypatch.delenv("AWS_S3_BUCKET", raising=False)
    rc = m.main(["run", str(_write_feature(tmp_path)), "--backend", "cloud", "--prefix", "prod-",
                 "--report-dir", "runs", "--region", "us-west-2", "--quiet"])
    assert rc == 0
    assert len(made["fargate"]) == 1, "cloud 应走 build_fargate_engines"
    fk = made["fargate"][0]
    assert fk["prefix"] == "prod-"
    assert fk["cluster"] == "prod-cluster"
    assert fk["events_table"] == "prod-events"
    assert fk["bucket"] == "prod-artifacts"
    assert fk["region"] == "us-west-2"
    assert fk["network_config"]["subnets"] == ["subnet-x"]  # 来自 resolve_network（fake）


def test_local_uses_subprocess_not_fargate(tmp_path, monkeypatch, capsys):
    # local 不走 build_fargate_engines（走 build_engines/SubprocessEngine）。
    box = {"fargate": 0}
    monkeypatch.setattr(m.compose, "build_fargate_engines", lambda **k: box.__setitem__("fargate", box["fargate"] + 1) or {})
    monkeypatch.setattr(m, "schedule", _fake_schedule_factory())
    rc = m.main(["run", str(_write_feature(tmp_path)), "--report-dir", str(tmp_path / "r"), "--quiet"])
    assert rc == 0
    assert box["fargate"] == 0  # local 从不造 FargateEngine


# ---- cloud + --no-report：不落库（跳过 store）但**仍 Fargate 执行**（report 与执行正交，ADR 0016 决策 A）----
def test_cloud_no_report_still_fargate_but_no_store(tmp_path, monkeypatch, capsys):
    # --no-report 只关不落库、**不碰在哪执行**：--backend cloud --no-report 仍在 Fargate 跑，只是不生成 report。
    record: list = []
    _, made, preflight_calls = _patch_cloud_handles(monkeypatch, record)
    monkeypatch.setattr(m, "schedule", _fake_schedule_factory())
    rc = m.main(["run", str(_write_feature(tmp_path)), "--backend", "cloud", "--no-report",
                 "--region", "us-east-1", "--quiet"])
    assert rc == 0
    # 落库轴：不构造任何 store 钩子（need_cloud=False，逃生舱）
    assert not any(r[0] == "make" for r in record)
    # 执行轴：仍走 Fargate（决策 A：cloud ⇒ Fargate，与 report 正交）
    assert len(made["fargate"]) == 1, "--no-report --backend cloud 仍应 Fargate 执行"
    # preflight 探执行资源（events/cluster/桶）但 runs_table=None（不落库、不探 runs 表）
    assert preflight_calls[0]["runs_table"] is None
    assert preflight_calls[0]["events_table"] == "gherkai-events"


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
    assert art["jobs_dir"].startswith("s3://B/runs/") and art["jobs_dir"].endswith("/jobs/")
    assert art["run_meta"].startswith("ddb://T/") and art["run_meta"].endswith("#META")
    assert art["run_state"].endswith("#STATE")
    assert art["report_index"].startswith("s3://B/")


# ---- cloud 把产物 S3 上传落点（artifact_s3）注入 worker（ADR 0029 第一期接线）----
def test_cloud_injects_artifact_s3_to_fargate(tmp_path, monkeypatch):
    # cloud 下 artifact_s3 经 build_fargate_engines 的 job_s3（bucket+prefix）到 worker——ADR 0029/0033。
    # （build_fargate_engines 内部据 bucket+report_dir+run_id 拼 job_s3；此处验 bucket 传对、report_dir 传对。）
    record: list = []
    _, made, _ = _patch_cloud_handles(monkeypatch, record)
    monkeypatch.setattr(m, "schedule", _fake_schedule_factory())
    rc = m.main(["run", str(_write_feature(tmp_path)), "--backend", "cloud",
                 "--s3-bucket", "mybkt", "--report-dir", "runs",
                 "--region", "us-east-1", "--quiet", "--json"])
    assert rc == 0
    fk = made["fargate"][0]
    assert fk["bucket"] == "mybkt"
    assert fk["report_dir"] == "runs"


def test_local_does_not_inject_artifact_s3(tmp_path, monkeypatch):
    # local 模式不注入 artifact_s3（worker 报 file://、不上传）——ADR 0029 零行为变化
    box = {}
    real_build = m.compose.build_engines

    def spy_build(repo, **kwargs):
        box.update(kwargs)
        return real_build(repo)

    monkeypatch.setattr(m.compose, "build_engines", spy_build)
    monkeypatch.setattr(m, "schedule", _fake_schedule_factory())
    rc = m.main(["run", str(_write_feature(tmp_path)), "--report-dir", str(tmp_path / "r"), "--quiet"])
    assert rc == 0
    assert box.get("artifact_s3") is None  # local 不注入


# ---- submit/status cloud 的 preflight/fail-fast 接线（ADR 0033 preflight 条）----

def test_submit_cloud_preflight_probes_taskdefs_and_lambda_chain(tmp_path, monkeypatch, capsys):
    """submit cloud 的 preflight 除表/桶/cluster 外还探：本 run 用到引擎的 task-def + 事件驱动链三 Lambda
    （任一缺 = 提交成功但 run 永不推进/收敛，须挡在提交前）。"""
    record: list = []
    _, _, preflight_calls = _patch_cloud_handles(monkeypatch, record)
    monkeypatch.delenv("AWS_DDB_TABLE", raising=False)
    monkeypatch.delenv("AWS_S3_BUCKET", raising=False)
    monkeypatch.delenv("AWS_RESOURCE_PREFIX", raising=False)

    rc = m.main(["submit", str(_write_feature(tmp_path)), "--backend", "cloud", "--region", "us-east-1"])
    assert rc == 0
    pf = preflight_calls[0]
    assert pf["task_defs"] == ["gherkai-novaact-worker"]
    assert pf["lambda_fns"] == ["gherkai-kicker", "gherkai-reconciler", "gherkai-exit-observer"]


def test_submit_cloud_preflight_failure_exits_2(tmp_path, monkeypatch, capsys):
    """preflight 报资源缺（如链上 Lambda 不存在）→ 提交前退 2、不写任何东西。"""
    record: list = []
    _patch_cloud_handles(monkeypatch, record, preflight_err="Lambda 函数 gherkai-kicker 不存在——…")
    rc = m.main(["submit", str(_write_feature(tmp_path)), "--backend", "cloud", "--region", "us-east-1"])
    assert rc == 2
    assert not [r for r in record if r[0] == "table"]  # 没碰 runs 表（挡在 create_run 前）


def test_status_wait_cloud_kicker_missing_fails_fast(monkeypatch, capsys):
    """--wait 接力 invoke 的 kicker 不存在（ResourceNotFound）→ 点名 prefix 退 2，不再吞掉死等
    （接力对象缺失时轮询永不终止；其他 AWS 瞬时错仍吞、下轮再踢——ADR 0033 preflight 条）。"""
    from botocore.exceptions import ClientError

    class _PendingTable:
        def get_item(self, **kw):
            return {"Item": {"run_id": "r1", "item_type": "STATE", "status": "pending", "jobs": {}}}

    class _NoKickerLambda:
        def invoke(self, **kw):
            raise ClientError({"Error": {"Code": "ResourceNotFoundException", "Message": "Function not found"}},
                              "Invoke")

    monkeypatch.setattr(m.compose, "_make_ddb_table", lambda table, *, region, profile: _PendingTable())
    monkeypatch.setattr(m.compose, "_make_lambda_client", lambda *, region, profile: _NoKickerLambda())
    import time as _t
    monkeypatch.setattr(_t, "sleep", lambda s: None)  # 卡住判定要连续 3 轮，免真等
    rc = m.main(["status", "r1", "--backend", "cloud", "--region", "us-east-1", "--wait"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "gherkai-kicker" in err and "--prefix" in err


def test_submit_cloud_forks_tunnel_watch_daemon(tmp_path, monkeypatch, capsys):
    """cloud submit --expose-local：fork 隧道守护进程（_tunnel_watch，携带隧道 pid）并明示「本机保持开机」
    （ADR 0035 决策 3——cloud submit 的 CLI 即退，守护是隧道唯一宿主）。"""
    import subprocess

    from gherkai import tunnel as gtunnel

    record: list = []
    _patch_cloud_handles(monkeypatch, record)
    info = gtunnel.TunnelInfo(url="https://t.ngrok-free.app", auth="u1:p1", pid=777,
                              local_origin="http://localhost:3000")

    class _Provider:
        def start(self, origin, **kw):
            return info

    monkeypatch.setattr(gtunnel, "make_tunnel", lambda name: _Provider())
    forked = []

    class _FakeProc:
        pid = 9

    monkeypatch.setattr(subprocess, "Popen", lambda cmd, **kw: forked.append(cmd) or _FakeProc())
    rc = m.main(["submit", str(_write_feature(tmp_path)), "--backend", "cloud",
                 "--region", "us-east-1", "--expose-local", "http://localhost:3000"])
    assert rc == 0
    watch = [c for c in forked if "_tunnel_watch" in c]
    assert len(watch) == 1
    cmd = watch[0]
    assert cmd[cmd.index("--tunnel-pid") + 1] == "777"
    assert "--ddb-table" in cmd
    assert "保持开机" in capsys.readouterr().err  # 明示边界（关机=隧道断）
