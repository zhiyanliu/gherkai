"""compose（组合根逻辑）单测：不起任何子进程、不烧钱。"""
from __future__ import annotations

from pathlib import Path

import pytest

from cli import compose
from core.scope import FeatureSource


def test_build_engines_has_both_legs():
    repo = compose.repo_root()
    engines = compose.build_engines(repo)
    assert set(engines) == {"novaact", "midscene"}
    # cmd 指向各自 worker（不实际起进程，只查接线）
    assert any("run_scope.py" in c for c in engines["novaact"].cmd)
    assert any("run-scope.ts" in c for c in engines["midscene"].cmd)


def test_resolver_known_and_unknown():
    engines = compose.build_engines(compose.repo_root())
    resolver = compose.make_resolver(engines)
    assert resolver("novaact") is engines["novaact"]
    with pytest.raises(ValueError, match="未知引擎"):
        resolver("nope")


def test_load_feature_uri_relative_to_repo(tmp_path: Path):
    # 仓库内的 feature → uri 是相对仓库根的路径
    repo = tmp_path
    feat = repo / "features" / "demo.feature"
    feat.parent.mkdir(parents=True)
    feat.write_text("Feature: x\n  Scenario: y\n    When \"做点啥\"\n", encoding="utf-8")
    fs = compose.load_feature(feat, repo)
    assert isinstance(fs, FeatureSource)
    assert fs.uri == "features/demo.feature"
    assert "Scenario: y" in fs.text


def test_load_feature_outside_repo_uses_absolute(tmp_path: Path):
    # 仓库外的 feature → 退用绝对路径（不崩）
    repo = tmp_path / "repo"
    repo.mkdir()
    outside = tmp_path / "other.feature"
    outside.write_text("Feature: z\n", encoding="utf-8")
    fs = compose.load_feature(outside, repo)
    assert fs.uri == str(outside.resolve())


def test_repo_root_contains_core_and_engines():
    repo = compose.repo_root()
    assert (repo / "core").is_dir()
    assert (repo / "engines").is_dir()


def test_build_engines_injects_artifact_dirs_symmetrically(tmp_path: Path):
    # 两引擎对称：产物落点经环境变量注入各自 worker 的 env（ADR 0027 产物归位）。
    repo = compose.repo_root()
    nova_dir = tmp_path / "r1" / "nova-trajectories"
    mid_dir = tmp_path / "r1" / "midscene-run"
    engines = compose.build_engines(repo, nova_logs_dir=nova_dir, midscene_run_dir=mid_dir)
    assert engines["novaact"]._env["NOVA_LOGS_DIR"] == str(nova_dir)
    assert engines["midscene"]._env["MIDSCENE_RUN_DIR"] == str(mid_dir)
    # 完整继承 os.environ（叠加而非替换）——否则 worker 丢 AWS 凭证等
    import os
    assert engines["midscene"]._env.get("PATH") == os.environ.get("PATH")


def test_build_engines_no_dirs_midscene_env_none(tmp_path: Path):
    # 不传落点（如 --no-report）：midscene env 保持 None，SubprocessEngine 回落继承 os.environ（不硬替换）。
    engines = compose.build_engines(compose.repo_root())
    assert engines["midscene"]._env is None


def test_build_engines_nova_always_has_act_timeout(tmp_path: Path):
    # Nova env **恒非 None**：即便无产物落点，组合根也要注入 NOVA_ACT_TIMEOUT_S（双端同源，ADR 0024 grace 硬约束）——
    # worker 读它作 act timeout、组合根用同一常量算 grace 下限，消除两处独立 120 的漂移。
    engines = compose.build_engines(compose.repo_root())
    assert engines["novaact"]._env is not None
    assert engines["novaact"]._env["NOVA_ACT_TIMEOUT_S"] == str(compose.NOVA_ACT_TIMEOUT_S)


def test_build_engines_injects_artifact_s3_env_symmetrically(tmp_path: Path):
    # artifact_s3=(bucket, prefix) → 两个引擎 worker 都拿到 ARTIFACT_S3_BUCKET/PREFIX env（worker from_env 真正读的东西，
    # ADR 0029）。跨越"__main__ 算元组 → compose 翻成 env"这道缝，防键名写错/合并漏掉时静默退回 file://。
    repo = compose.repo_root()
    nova_dir = tmp_path / "rid" / "nova-trajectories"
    mid_dir = tmp_path / "rid" / "midscene-run"
    engines = compose.build_engines(
        repo, nova_logs_dir=nova_dir, midscene_run_dir=mid_dir, artifact_s3=("bkt", "runs/rid/"),
    )
    for eng in ("novaact", "midscene"):
        assert engines[eng]._env["ARTIFACT_S3_BUCKET"] == "bkt"
        assert engines[eng]._env["ARTIFACT_S3_PREFIX"] == "runs/rid/"  # 与 S3ReportStore 同前缀（逐字）


def test_build_engines_artifact_s3_alone_makes_env_nonnull(tmp_path: Path):
    # 只给 artifact_s3、不给 local dir（防御 _env 的 "local_dir is None and not s3_env" 早返回守卫吞掉 s3_env）：
    # env 必须非 None 且含 S3 落点，否则 worker 拿不到、静默退回 file://。
    engines = compose.build_engines(compose.repo_root(), artifact_s3=("bkt", "runs/rid/"))
    for eng in ("novaact", "midscene"):
        assert engines[eng]._env is not None
        assert engines[eng]._env["ARTIFACT_S3_BUCKET"] == "bkt"


def test_build_engines_no_artifact_s3_env_has_no_s3_keys(tmp_path: Path):
    # local（不给 artifact_s3）：env 里不含 S3 落点键（worker no-op 报 file://、零行为变化，ADR 0029）。
    nova_dir = tmp_path / "rid" / "nova-trajectories"
    engines = compose.build_engines(compose.repo_root(), nova_logs_dir=nova_dir)
    assert "ARTIFACT_S3_BUCKET" not in engines["novaact"]._env


def test_build_engines_region_profile_override_env(tmp_path: Path, monkeypatch):
    # ADR 0016 决策 C：--region/--profile 解析值**覆盖**继承的 AWS_REGION/AWS_PROFILE（参数 > env），使二者真贯通到
    # worker（EventSink/JobSource/ArtifactUploader/Nova Workflow 建 client 都读它们），与 core store 同源、消除分叉。
    monkeypatch.setenv("AWS_REGION", "us-east-1")   # shell 里是 east
    monkeypatch.setenv("AWS_PROFILE", "shell-prof")  # shell 里是另一个 profile
    nova_dir = tmp_path / "rid" / "nova-trajectories"
    mid_dir = tmp_path / "rid" / "midscene-run"
    engines = compose.build_engines(
        compose.repo_root(), nova_logs_dir=nova_dir, midscene_run_dir=mid_dir,
        region="us-west-2", profile="cli-prof",  # --region west / --profile cli-prof
    )
    for eng in ("novaact", "midscene"):
        assert engines[eng]._env["AWS_REGION"] == "us-west-2"    # 参数覆盖 env，非继承的 east
        assert engines[eng]._env["AWS_PROFILE"] == "cli-prof"    # profile 同理覆盖


def test_build_engines_region_profile_none_preserve_inherited(tmp_path: Path, monkeypatch):
    # region/profile=None（未给参数、__main__ 解析出 None）：不干预，保留继承的 env（若 shell 有）——
    # 组合根不硬写、留 env/boto 默认链/profile config 兜底（现有宽容）。
    monkeypatch.setenv("AWS_REGION", "eu-central-1")
    monkeypatch.setenv("AWS_PROFILE", "inherited-prof")
    nova_dir = tmp_path / "rid" / "nova-trajectories"
    engines = compose.build_engines(compose.repo_root(), nova_logs_dir=nova_dir, region=None, profile=None)
    assert engines["novaact"]._env["AWS_REGION"] == "eu-central-1"      # 原样继承、未被抹掉
    assert engines["novaact"]._env["AWS_PROFILE"] == "inherited-prof"


def test_build_engines_region_profile_injected_on_rebuild_path_both_legs(tmp_path: Path, monkeypatch):
    # 补建路径（无产物落点、如 --no-report → _env 返回 None）：region/profile 须在**两个引擎**补建路径都注入——
    # Nova 恒补建（塞 NOVA_ACT_TIMEOUT_S，_inject_aws 搭便车）；Midscene 在 region/profile 有值时也补建（否则 --no-report
    # 下 midscene worker 继承 os.environ、拿不到 --profile 覆盖，而它经 fromNodeProviderChain 消费 profile 做 AgentCore/
    # Bedrock 鉴权——真消费、非无害，ADR 0016 决策 C）。
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.delenv("AWS_PROFILE", raising=False)
    engines = compose.build_engines(
        compose.repo_root(), region="ap-southeast-1", profile="cli-prof",  # 无 dirs、无 artifact_s3 → 两个引擎走补建
    )
    for eng in ("novaact", "midscene"):
        assert engines[eng]._env["AWS_REGION"] == "ap-southeast-1"  # 补建路径也覆盖生效
        assert engines[eng]._env["AWS_PROFILE"] == "cli-prof"


def test_build_engines_midscene_no_rebuild_when_no_region_profile(tmp_path: Path, monkeypatch):
    # 对称边界：--no-report 且 region/profile 均 None 时 Midscene **不**补建（env=None、继承 os.environ 本就够，
    # 免无谓拷贝）——补建只为 region/profile 覆盖，无值则不建。Nova 仍补建（NOVA_ACT_TIMEOUT_S 恒需）。
    monkeypatch.delenv("AWS_REGION", raising=False)
    monkeypatch.delenv("AWS_DEFAULT_REGION", raising=False)
    engines = compose.build_engines(compose.repo_root(), region=None, profile=None)  # 无 dirs、无 s3、无 region/profile
    assert engines["midscene"]._env is None       # 不补建
    assert engines["novaact"]._env is not None     # Nova 恒补建（timeout）


# ---- resolve_region：region 落实成具体字符串（ADR 0016 决策 C，修 AgentCore profile-only 崩）----
def test_resolve_region_explicit_wins(monkeypatch):
    # --region 显式最高优先，不碰 env/profile
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-2")
    assert compose.resolve_region("us-west-2", "some-prof") == "us-west-2"


def test_resolve_region_env_chain(monkeypatch):
    # 无 --region：AWS_REGION > AWS_DEFAULT_REGION
    monkeypatch.delenv("AWS_REGION", raising=False)
    monkeypatch.setenv("AWS_DEFAULT_REGION", "ap-south-1")
    assert compose.resolve_region(None, None) == "ap-south-1"
    monkeypatch.setenv("AWS_REGION", "eu-west-1")
    assert compose.resolve_region(None, None) == "eu-west-1"  # AWS_REGION 优先于 DEFAULT


def test_resolve_region_falls_back_to_profile_config(monkeypatch):
    # 关键（profile-only region 落实）：--region/env 全 miss → 回落 boto3.Session(profile).region_name 读 profile config 的 region。
    # 不落实则 profile-only 用户下 worker AgentCore validate_region(None) → InvalidRegionError 崩。
    monkeypatch.delenv("AWS_REGION", raising=False)
    monkeypatch.delenv("AWS_DEFAULT_REGION", raising=False)
    captured = {}

    class _FakeSession:
        def __init__(self, profile_name=None):
            captured["profile"] = profile_name
            self.region_name = "eu-west-2"  # 模拟 profile config 里 region=eu-west-2

    import boto3
    monkeypatch.setattr(boto3.session, "Session", _FakeSession)
    assert compose.resolve_region(None, "myprofile") == "eu-west-2"
    assert captured["profile"] == "myprofile"  # 确实按解析出的 profile 读 config


def test_resolve_region_none_when_all_miss(monkeypatch):
    # 全 miss（无 --region/env、profile config 也无 region）→ None＝fail-loud（worker 报错、不硬编码 east）。
    monkeypatch.delenv("AWS_REGION", raising=False)
    monkeypatch.delenv("AWS_DEFAULT_REGION", raising=False)

    class _NoRegionSession:
        def __init__(self, profile_name=None):
            self.region_name = None  # profile 无 region 字段

    import boto3
    monkeypatch.setattr(boto3.session, "Session", _NoRegionSession)
    assert compose.resolve_region(None, None) is None


# ---- engine_min_grace：按引擎给 grace 下限（ADR 0024 grace 硬约束）----
def test_engine_min_grace_nova_covers_act_timeout_plus_margin():
    # 断言语义关系而非重述公式（否则同义反复、测不出常量漂移）：Nova 下限须**严格大于**单 act 上界——
    # 才留得出会话释放余量（SIGTERM 落长 act 中途须等 act 有界返回才协作退释放会话，ADR 0024）。
    # 若 margin 误设为 0（违 ADR「grace 须留会话释放余量」红线），下限=act_timeout，此断言会红。
    g = compose.engine_min_grace("novaact")
    assert g > compose.NOVA_ACT_TIMEOUT_S, "Nova grace 下限须 > 单 act 上界（留会话释放余量）"
    assert compose.NOVA_GRACE_MARGIN_S > 0, "margin 须 > 0（ADR 0024 会话释放余量红线）"


def test_engine_min_grace_midscene_nonzero_covers_onsignal_budget():
    # Midscene 下限 = MIDSCENE_GRACE_MIN_S（非零）：onSignal 收尾路径超时预算之和须 < grace，否则 worker 被
    # SIGKILL、中断兜底 report 抢传截断（ADR 0024 grace 硬约束；曾为 0.0 致 midscene-only run grace 回落 5s < 上传 10s）。
    assert compose.engine_min_grace("midscene") == float(compose.MIDSCENE_GRACE_MIN_S)
    assert compose.engine_min_grace("midscene") > 0.0
    # 必须够 onSignal 最坏串行路径（会话 Stop + browser.close + 中断兜底上传超时），且 > Midscene 上传超时 10s。
    assert compose.MIDSCENE_GRACE_MIN_S >= 10


def test_engine_min_grace_unknown_engine_zero():
    # 未知引擎无下限（0.0）——保守：core enforce grace > 0 仍兜底。
    assert compose.engine_min_grace("unknown") == 0.0


def test_engine_min_grace_mixed_run_takes_max():
    # 混引擎 run 的 min_grace = 各引擎下限的 max（grace 是 run 级单值，__main__ 取 max）——Nova 下限最大、支配。
    legs = ["novaact", "midscene"]
    assert max(compose.engine_min_grace(e) for e in legs) == compose.engine_min_grace("novaact")


# ---- 两层命名（ADR 0033）：prefix + 基名推导 / task-def / container / SSM 路径 ----
def test_default_name_prefix_original_concat():
    # prefix 原样拼基名（含分隔符由用户负责，防粘连——同 S3 prefix 先例）
    assert compose.default_name("gherkai-", "runs") == "gherkai-runs"
    assert compose.default_name("prod-", "events") == "prod-events"
    assert compose.default_name("nodash", "runs") == "nodashruns"  # 无分隔符 → 粘连（用户负责）


def test_task_def_and_container_name():
    # task-def family 带 prefix、按引擎；container 名不带 prefix（随 task-def 走，避冗余）
    assert compose.task_def_name("prod-", "novaact") == "prod-novaact-worker"
    assert compose.task_def_name("gherkai-", "midscene") == "gherkai-midscene-worker"
    assert compose.container_name("novaact") == "novaact-worker"
    assert compose.container_name("midscene") == "midscene-worker"


def test_ssm_path_contains_prefix():
    # SSM 路径含 prefix（cli 已知 prefix 拼路径读 subnet/sg，无循环——ADR 0033）
    assert compose.ssm_path("prod-", "subnets") == "/prod-backend/subnets"
    assert compose.ssm_path("gherkai-", "security-groups") == "/gherkai-backend/security-groups"


# ---- resolve_network（ADR 0033）：subnet/sg 覆盖 or 读 SSM ----
def test_resolve_network_explicit_overrides_skip_ssm():
    # 显式给 subnet/sg → 不读 SSM（ssm 注入个会炸的哨兵，验它没被调）
    class _BoomSsm:
        def get_parameter(self, **kw):
            raise AssertionError("显式给 subnet/sg 时不该读 SSM")
    net = compose.resolve_network(
        prefix="prod-", subnets=["subnet-a", "subnet-b"], security_groups=["sg-1"],
        assign_public_ip="DISABLED", ssm=_BoomSsm(),
    )
    assert net == {"subnets": ["subnet-a", "subnet-b"], "securityGroups": ["sg-1"], "assignPublicIp": "DISABLED"}


def test_resolve_network_reads_ssm_when_missing():
    # 未给 subnet/sg → 读含 prefix 的 SSM 路径（CDK 写的生成 ID，逗号分隔 StringList）
    reads = []

    class _FakeSsm:
        def get_parameter(self, Name):
            reads.append(Name)
            val = "subnet-x,subnet-y" if Name.endswith("subnets") else "sg-z"
            return {"Parameter": {"Value": val}}

    net = compose.resolve_network(prefix="prod-", subnets=None, security_groups=None, ssm=_FakeSsm())
    assert net["subnets"] == ["subnet-x", "subnet-y"]
    assert net["securityGroups"] == ["sg-z"]
    assert reads == ["/prod-backend/subnets", "/prod-backend/security-groups"]  # 路径含 prefix


def test_resolve_network_partial_override_reads_only_missing():
    # 只给 subnet、不给 sg → 只读 sg 的 SSM（subnet 用显式）
    reads = []

    class _FakeSsm:
        def get_parameter(self, Name):
            reads.append(Name)
            return {"Parameter": {"Value": "sg-only"}}

    net = compose.resolve_network(prefix="g-", subnets=["subnet-explicit"], security_groups=None, ssm=_FakeSsm())
    assert net["subnets"] == ["subnet-explicit"]
    assert net["securityGroups"] == ["sg-only"]
    assert reads == ["/g-backend/security-groups"]  # 只读缺的那个


# ---- build_fargate_engines（ADR 0033/0016 决策 A/C）：按引擎选 task-def、注 region 不注 profile ----
def test_build_fargate_engines_per_engine_taskdef_and_region_no_profile(monkeypatch):
    # 注入 fake FargateEngine 捕获构造参数（不连 AWS、不 require boto3）
    import core.adapters.fargate_engine as fe
    captured = []

    class _FakeFargate:
        def __init__(self, **kwargs):
            captured.append(kwargs)

    monkeypatch.setattr(fe, "FargateEngine", _FakeFargate)
    engines = compose.build_fargate_engines(
        run_id="rid-1", prefix="prod-", cluster="prod-cluster", events_table="prod-events",
        bucket="prod-artifacts", report_dir="runs", network_config={"subnets": ["subnet-x"]},
        region="us-west-2", profile="myprof",
        ecs=object(), s3=object(), ddb_events_table=object(),  # 注入句柄免惰性建
    )
    assert set(engines) == {"novaact", "midscene"}
    by_engine = {k["task_definition"]: k for k in captured}
    # 按引擎选 task-def（{prefix}{engine}-worker）
    assert "prod-novaact-worker" in by_engine and "prod-midscene-worker" in by_engine
    nova = by_engine["prod-novaact-worker"]
    assert nova["container_name"] == "novaact-worker"
    assert nova["run_id"] == "rid-1" and nova["cluster"] == "prod-cluster"
    assert nova["events_table_name"] == "prod-events"
    assert nova["region"] == "us-west-2"          # region 注入（决策 C）
    assert "profile" not in nova                    # **profile 不传 FargateEngine**（正确非对称，决策 C）
    # job_s3 = (bucket, "{report_dir}/{run_id}/jobs-in/")——**jobs-in/ 非 jobs/**（避与 ResultStore 判定 key 撞，真跑暴露）
    assert nova["job_s3"] == ("prod-artifacts", "runs/rid-1/jobs-in/")
    # artifact_s3 = (bucket, "{report_dir}/{run_id}/")——**cloud 必注入**（否则容器盘销毁产物必丢，ADR 0029）
    assert nova["artifact_s3"] == ("prod-artifacts", "runs/rid-1/")
    # SDK 产物落点 env（按引擎、容器内路径）——**uploader 靠它算 run_dir，缺它 no-op 报 file://、产物丢**（真跑暴露）。
    assert nova["sdk_artifact_dir_env"] == {"NOVA_LOGS_DIR": "/tmp/gherkai-run/rid-1/nova-trajectories"}
    mid = by_engine["prod-midscene-worker"]
    assert mid["sdk_artifact_dir_env"] == {"MIDSCENE_RUN_DIR": "/tmp/gherkai-run/rid-1/midscene-run"}


# ---- preflight_cloud_resources（ADR 0033）：探资源存在性、缺则点名 prefix ----
class _FakeDdbClient:
    def __init__(self, existing):
        self._existing = existing
    def describe_table(self, TableName):
        if TableName not in self._existing:
            from botocore.exceptions import ClientError
            raise ClientError({"Error": {"Code": "ResourceNotFoundException", "Message": "x"}}, "DescribeTable")
        return {"Table": {"TableName": TableName}}


class _FakeS3Client:
    def __init__(self, existing):
        self._existing = existing
    def head_bucket(self, Bucket):
        if Bucket not in self._existing:
            from botocore.exceptions import ClientError
            raise ClientError({"Error": {"Code": "404", "Message": "x"}}, "HeadBucket")


class _FakeEcsClient:
    def __init__(self, active):
        self._active = active
    def describe_clusters(self, clusters):
        return {"clusters": [{"status": "ACTIVE" if c in self._active else "INACTIVE"} for c in clusters]}


def test_preflight_all_present_returns_none():
    err = compose.preflight_cloud_resources(
        prefix="gherkai-", runs_table="gherkai-runs", events_table="gherkai-events",
        bucket="gherkai-artifacts", cluster="gherkai-cluster",
        ddb=_FakeDdbClient({"gherkai-runs", "gherkai-events"}),
        s3=_FakeS3Client({"gherkai-artifacts"}),
        ecs=_FakeEcsClient({"gherkai-cluster"}),
    )
    assert err is None


def test_preflight_missing_events_table_names_prefix():
    err = compose.preflight_cloud_resources(
        prefix="prod-", runs_table="prod-runs", events_table="prod-events",
        bucket="prod-artifacts", cluster="prod-cluster",
        ddb=_FakeDdbClient({"prod-runs"}),  # events 表缺
        s3=_FakeS3Client({"prod-artifacts"}),
        ecs=_FakeEcsClient({"prod-cluster"}),
    )
    assert err is not None
    assert "prod-events" in err and "--prefix='prod-'" in err and "CDK" in err  # 点名 prefix + 引导


def test_preflight_missing_cluster_detected():
    err = compose.preflight_cloud_resources(
        prefix="g-", runs_table="g-runs", events_table="g-events", bucket="g-artifacts", cluster="g-cluster",
        ddb=_FakeDdbClient({"g-runs", "g-events"}),
        s3=_FakeS3Client({"g-artifacts"}),
        ecs=_FakeEcsClient(set()),  # cluster 非 ACTIVE
    )
    assert err is not None and "g-cluster" in err
