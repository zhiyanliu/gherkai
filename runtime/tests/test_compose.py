"""compose（组合根逻辑）单测：不起任何子进程、不烧钱。"""
from __future__ import annotations

from pathlib import Path

import pytest

from gherkai_runtime import compose
from gherkai_core.scope import FeatureSource


def test_build_engines_has_both_legs():
    repo = compose.repo_root()
    engines = compose.build_engines(repo)
    assert set(engines) == {"novaact", "midscene"}
    # cmd 指向各自 worker（不实际起进程，只查接线）
    assert any("run_scope.py" in c for c in engines["novaact"].cmd)
    assert any("run-scope.ts" in c for c in engines["midscene"].cmd)


def test_build_engines_injects_extra_http_headers_env():
    """extra_http_headers（ADR 0035 决策 4）→ 两 worker env 注 GHERKAI_EXTRA_HTTP_HEADERS（JSON）；
    不传则不注入（默认路径零变化）。"""
    import json as _json

    repo = compose.repo_root()
    engines = compose.build_engines(repo, extra_http_headers={"ngrok-skip-browser-warning": "1"})
    for name in ("novaact", "midscene"):
        env = engines[name]._env
        assert env is not None, name
        assert _json.loads(env["GHERKAI_EXTRA_HTTP_HEADERS"]) == {"ngrok-skip-browser-warning": "1"}
    engines2 = compose.build_engines(repo)
    for name in ("novaact", "midscene"):
        env2 = engines2[name]._env
        assert env2 is None or "GHERKAI_EXTRA_HTTP_HEADERS" not in env2, name


def test_resolver_known_and_unknown():
    engines = compose.build_engines(compose.repo_root())
    resolver = compose.make_resolver(engines)
    assert resolver("novaact") is engines["novaact"]
    with pytest.raises(ValueError, match="未知引擎"):
        resolver("nope")


def test_load_feature_uri_is_given_path_normalized(tmp_path: Path, monkeypatch):
    """uri = 用户给出的路径规范化后原样（ADR 0037 决策 3）：相对给相对（`./` 折掉、`..` 保留），不相对任何根。"""
    feat = tmp_path / "features" / "demo.feature"
    feat.parent.mkdir(parents=True)
    feat.write_text("Feature: x\n  Scenario: y\n    When \"做点啥\"\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    fs = compose.load_feature(Path("./features/demo.feature"))
    assert isinstance(fs, FeatureSource)
    assert fs.uri == "features/demo.feature"
    assert "Scenario: y" in fs.text
    monkeypatch.chdir(tmp_path / "features")
    assert compose.load_feature(Path("../features/demo.feature")).uri == "../features/demo.feature"


def test_load_feature_absolute_path_stays_absolute(tmp_path: Path):
    # 绝对路径给绝对路径（不做 relative_to 任何根、不 resolve 符号链接）
    outside = tmp_path / "other.feature"
    outside.write_text("Feature: z\n", encoding="utf-8")
    fs = compose.load_feature(outside)
    assert fs.uri == str(outside)


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


def test_build_engines_never_injects_artifact_s3_env(tmp_path: Path):
    # local 档**恒不注入** S3 上传落点（worker 据「有没有这组 env」决定上传，无 → 报 file://，ADR 0029）：
    # 上传落点只由 cloud 档的 build_fargate_engines 注入，预演由 e2e_harness 自拼 env（ADR 0016 决策 B）。
    nova_dir = tmp_path / "rid" / "nova-trajectories"
    mid_dir = tmp_path / "rid" / "midscene-run"
    engines = compose.build_engines(compose.repo_root(), nova_logs_dir=nova_dir, midscene_run_dir=mid_dir)
    for eng in ("novaact", "midscene"):
        assert "ARTIFACT_S3_BUCKET" not in engines[eng]._env
        assert "ARTIFACT_S3_PREFIX" not in engines[eng]._env


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
        compose.repo_root(), region="ap-southeast-1", profile="cli-prof",  # 无 dirs → 两个引擎走补建
    )
    for eng in ("novaact", "midscene"):
        assert engines[eng]._env["AWS_REGION"] == "ap-southeast-1"  # 补建路径也覆盖生效
        assert engines[eng]._env["AWS_PROFILE"] == "cli-prof"


def test_build_engines_midscene_no_rebuild_when_no_region_profile(tmp_path: Path, monkeypatch):
    # 对称边界：--no-report 且 region/profile 均 None 时 Midscene **不**补建（env=None、继承 os.environ 本就够，
    # 免无谓拷贝）——补建只为 region/profile 覆盖，无值则不建。Nova 仍补建（NOVA_ACT_TIMEOUT_S 恒需）。
    monkeypatch.delenv("AWS_REGION", raising=False)
    monkeypatch.delenv("AWS_DEFAULT_REGION", raising=False)
    engines = compose.build_engines(compose.repo_root(), region=None, profile=None)  # 无 dirs、无 region/profile
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


def test_resolve_region_no_boto3_returns_none_not_crash(monkeypatch):
    # 纯 local 不依赖 boto3：--region/env 全 miss 需回落 profile config，但**缺 boto3（未装 aws extra）时**
    # 不能抛未捕获 ImportError——catch → None fail-loud（等价「无 region」）。绿≠对：dev 装了 boto3 恒绿掩盖此路径，
    # 故拦截 `import boto3` 抛 ImportError 真验。守「纯 local 路径绝不依赖 boto3」不变量（ADR 0016 决策 C；
    # boto3 走库层 `gherkai-core[aws]` extra——CLI 发行包 gherkai 已硬依赖它（ADR 0037 决策 2c），但本不变量
    # 与安装期装没装 boto3 无关）。
    monkeypatch.delenv("AWS_REGION", raising=False)
    monkeypatch.delenv("AWS_DEFAULT_REGION", raising=False)
    import builtins
    _orig_import = builtins.__import__

    def _no_boto3(name, *a, **k):
        if name == "boto3":
            raise ImportError("simulated pure-local: boto3 not installed")
        return _orig_import(name, *a, **k)

    monkeypatch.setattr(builtins, "__import__", _no_boto3)
    assert compose.resolve_region(None, "someprofile") is None  # 缺 boto3 读不到 profile config → None、不崩


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


# ---- resolve_cloud_target：入口皮的 flag/env → 各资源终名 + region/profile（ADR 0033 / 0016 决策 C）----
def _clear_aws_env(monkeypatch):
    for k in ("AWS_REGION", "AWS_DEFAULT_REGION", "AWS_PROFILE", "AWS_RESOURCE_PREFIX",
              "AWS_DDB_TABLE", "AWS_S3_BUCKET"):
        monkeypatch.delenv(k, raising=False)


def test_resolve_cloud_target_derives_all_names_from_prefix(monkeypatch):
    _clear_aws_env(monkeypatch)
    t = compose.resolve_cloud_target(prefix="prod-", region="us-west-2")
    assert (t.prefix, t.region, t.profile) == ("prod-", "us-west-2", None)
    assert (t.runs_table, t.events_table, t.bucket, t.cluster) == (
        "prod-runs", "prod-events", "prod-artifacts", "prod-cluster")
    # 三 Lambda 名同源推导；detached_chain_lambdas 顺序 = 链上顺序（kicker→reconciler→exit-observer）
    assert t.detached_chain_lambdas == ["prod-kicker", "prod-reconciler", "prod-exit-observer"]


def test_resolve_cloud_target_env_fallbacks_are_deliberately_uneven(monkeypatch):
    _clear_aws_env(monkeypatch)
    monkeypatch.setenv("AWS_RESOURCE_PREFIX", "stage-")
    monkeypatch.setenv("AWS_DDB_TABLE", "env-runs")
    monkeypatch.setenv("AWS_S3_BUCKET", "env-bucket")
    monkeypatch.setenv("AWS_PROFILE", "env-prof")
    monkeypatch.setenv("AWS_REGION", "eu-west-1")
    t = compose.resolve_cloud_target()
    assert (t.prefix, t.profile, t.region) == ("stage-", "env-prof", "eu-west-1")
    assert (t.runs_table, t.bucket) == ("env-runs", "env-bucket")  # 这两个有历史 env 面
    # events 表/cluster **无** env 兜底（保既有 CLI 行为，别为对称乱加）——仍走 prefix 默认名
    assert (t.events_table, t.cluster) == ("stage-events", "stage-cluster")


def test_resolve_cloud_target_flags_win_over_env(monkeypatch):
    _clear_aws_env(monkeypatch)
    monkeypatch.setenv("AWS_RESOURCE_PREFIX", "stage-")
    monkeypatch.setenv("AWS_DDB_TABLE", "env-runs")
    monkeypatch.setenv("AWS_PROFILE", "env-prof")
    monkeypatch.setenv("AWS_REGION", "eu-west-1")
    t = compose.resolve_cloud_target(prefix="prod-", runs_table="flag-runs", bucket="flag-bucket",
                                     events_table="flag-events", cluster="flag-cluster",
                                     profile="flag-prof", region="ap-south-1")
    assert (t.prefix, t.profile, t.region) == ("prod-", "flag-prof", "ap-south-1")
    assert (t.runs_table, t.bucket, t.events_table, t.cluster) == (
        "flag-runs", "flag-bucket", "flag-events", "flag-cluster")
    assert t.kicker_lambda == "prod-kicker"  # 单资源覆盖不影响别的资源仍按 prefix 推导


def test_resolve_cloud_target_default_prefix_when_nothing_given(monkeypatch):
    _clear_aws_env(monkeypatch)
    monkeypatch.setattr(compose, "resolve_region", lambda r, p: None)  # 不摸真 ~/.aws
    t = compose.resolve_cloud_target()
    assert t.prefix == compose.DEFAULT_PREFIX and t.runs_table == f"{compose.DEFAULT_PREFIX}runs"
    assert t.region is None and t.profile is None  # 真无 → fail-loud，不硬编码 east


# ---- prune_empty_dirs（cloud 清本地空壳，ADR 0029）：只删空目录、非空保留 ----
def test_prune_empty_dirs_removes_empty_tree(tmp_path):
    # worker 上传后 rmtree 了子目录，run 根只剩空壳（含空中间目录）→ 整个删掉
    run_dir = tmp_path / "reports" / "rid"
    (run_dir / "nova-trajectories" / "sess").mkdir(parents=True)  # 全空
    (run_dir / "midscene-run" / "report").mkdir(parents=True)     # 全空
    compose.prune_empty_dirs(run_dir)
    assert not run_dir.exists()  # 空壳整个清掉


def test_prune_empty_dirs_keeps_nonempty(tmp_path):
    # 某个引擎 flush 失败保留了产物（目录非空）→ 该目录及其祖先保留（护栏：不误删产物）
    run_dir = tmp_path / "reports" / "rid"
    kept = run_dir / "nova-trajectories" / "sess"
    kept.mkdir(parents=True)
    (kept / "act_0.html").write_text("残留产物")           # 非空
    (run_dir / "midscene-run").mkdir(parents=True)          # 空
    compose.prune_empty_dirs(run_dir)
    assert run_dir.exists()                                  # 因含非空子树而保留
    assert (kept / "act_0.html").exists()                   # 产物没被误删
    assert not (run_dir / "midscene-run").exists()           # 空的那支仍被清


def test_prune_empty_dirs_noop_when_missing(tmp_path):
    compose.prune_empty_dirs(tmp_path / "nonexistent")  # 不存在 → no-op、不抛


def test_is_botocore_error_classifies():
    from botocore.exceptions import ClientError

    assert compose.is_botocore_error(ClientError({"Error": {"Code": "X"}}, "Op"))
    assert not compose.is_botocore_error(ValueError("不是云端故障"))


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


def test_resolve_network_empty_ssm_fails_fast():
    # 空值 fail-fast（低频加固，ADR 0033）：SSM 参数空（值空串 → split 过滤后 []）→ 就地报错点名路径，
    # 不把空列表传到 awsvpcConfiguration、拖到 RunTask 才炸。空串 / 纯逗号 两种空形态都拦。
    import pytest

    class _EmptySsm:
        def __init__(self, val): self._val = val
        def get_parameter(self, Name):
            return {"Parameter": {"Value": self._val}}

    for empty_val in ("", ",", ",,"):  # 空串 / 逗号无值——过滤后都是 []
        with pytest.raises(ValueError, match="为空"):
            compose.resolve_network(prefix="g-", subnets=None, security_groups=None, ssm=_EmptySsm(empty_val))
    # 错误须点名是哪个 SSM 路径（subnets 先读、先炸）
    try:
        compose.resolve_network(prefix="g-", subnets=None, security_groups=None, ssm=_EmptySsm(""))
        assert False, "应 fail-fast"
    except ValueError as e:
        assert "/g-backend/subnets" in str(e)  # 点名路径，便于排障


# ---- build_fargate_engines（ADR 0033/0016 决策 A/C）：按引擎选 task-def、注 region 不注 profile ----
def test_build_fargate_engines_per_engine_taskdef_and_region_no_profile(monkeypatch):
    # 注入 fake FargateEngine 捕获构造参数（不连 AWS、不 require boto3）
    import gherkai_core.adapters.fargate_engine as fe
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
    # Nova act timeout **双端同源**（ADR 0024 grace 硬约束）：cloud 档也须显式注入——容器不继承本地 env，
    # 缺它则 worker 落回自带字面量、调 NOVA_ACT_TIMEOUT_S 只抬高 grace 下限、改不动容器内单 act 上界。
    assert nova["extra_env"]["NOVA_ACT_TIMEOUT_S"] == str(compose.NOVA_ACT_TIMEOUT_S)
    mid = by_engine["prod-midscene-worker"]
    assert mid["sdk_artifact_dir_env"] == {"MIDSCENE_RUN_DIR": "/tmp/gherkai-run/rid-1/midscene-run"}
    assert "NOVA_ACT_TIMEOUT_S" not in mid["extra_env"]  # 引擎特定值只给该引擎（Midscene 无可控 act timeout）


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
    def __init__(self, active, task_defs=()):
        self._active = active
        self._task_defs = set(task_defs)
    def describe_clusters(self, clusters):
        return {"clusters": [{"status": "ACTIVE" if c in self._active else "INACTIVE"} for c in clusters]}
    def describe_task_definition(self, taskDefinition):
        if taskDefinition not in self._task_defs:
            from botocore.exceptions import ClientError
            raise ClientError({"Error": {"Code": "ClientException", "Message": "Unable to describe task definition"}},
                              "DescribeTaskDefinition")
        return {"taskDefinition": {"family": taskDefinition}}


class _FakeLambdaClient:
    def __init__(self, existing, env_by_fn=None):
        self._existing = set(existing)
        self._env_by_fn = env_by_fn or {}  # fn → env dict（缺项 = 该 Lambda 没配 env，同真实返回体省略 Environment）

    def get_function(self, FunctionName):
        if FunctionName not in self._existing:
            from botocore.exceptions import ClientError
            raise ClientError({"Error": {"Code": "ResourceNotFoundException", "Message": "x"}}, "GetFunction")
        cfg = {"FunctionName": FunctionName}
        if FunctionName in self._env_by_fn:
            cfg["Environment"] = {"Variables": dict(self._env_by_fn[FunctionName])}
        return {"Configuration": cfg}


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


def test_preflight_missing_task_def_names_prefix():
    # task-def 维度的 prefix 配错（原漏到 RunTask 才炸、退 1 不点名）→ 现 preflight 点名 fail-fast（ADR 0033）
    err = compose.preflight_cloud_resources(
        prefix="prod-", events_table="prod-events", bucket="prod-artifacts", cluster="prod-cluster",
        task_defs=["prod-novaact-worker"],
        ddb=_FakeDdbClient({"prod-events"}), s3=_FakeS3Client({"prod-artifacts"}),
        ecs=_FakeEcsClient({"prod-cluster"}),  # task-def 集为空 → 缺
    )
    assert err is not None
    assert "prod-novaact-worker" in err and "--prefix='prod-'" in err


def test_preflight_missing_chain_lambda_names_prefix():
    # detached 链三 Lambda 任一缺 = 提交成功但 run 永不推进/收敛 → 挡在提交前（ADR 0033）
    err = compose.preflight_cloud_resources(
        prefix="g-", events_table="g-events", bucket="g-artifacts", cluster="g-cluster",
        lambda_fns=["g-kicker", "g-reconciler", "g-exit-observer"],
        ddb=_FakeDdbClient({"g-events"}), s3=_FakeS3Client({"g-artifacts"}),
        ecs=_FakeEcsClient({"g-cluster"}),
        lam=_FakeLambdaClient({"g-kicker", "g-exit-observer"}),  # reconciler 缺
    )
    assert err is not None and "g-reconciler" in err


def test_preflight_task_defs_and_lambdas_all_present():
    err = compose.preflight_cloud_resources(
        prefix="g-", runs_table="g-runs", events_table="g-events", bucket="g-artifacts", cluster="g-cluster",
        task_defs=["g-novaact-worker", "g-midscene-worker"],
        lambda_fns=["g-kicker", "g-reconciler", "g-exit-observer"],
        ddb=_FakeDdbClient({"g-runs", "g-events"}), s3=_FakeS3Client({"g-artifacts"}),
        ecs=_FakeEcsClient({"g-cluster"}, task_defs={"g-novaact-worker", "g-midscene-worker"}),
        lam=_FakeLambdaClient({"g-kicker", "g-reconciler", "g-exit-observer"}),
    )
    assert err is None


# ---- preflight 的产物前缀一致性（ADR 0033）：--report-dir vs 推进器 REPORT_DIR ----
_CHAIN = ["g-kicker", "g-reconciler", "g-exit-observer"]


def _preflight_report_dir(report_dir, env_by_fn=None):
    return compose.preflight_cloud_resources(
        prefix="g-", runs_table="g-runs", events_table="g-events", bucket="g-artifacts",
        cluster="g-cluster", lambda_fns=_CHAIN, report_dir=report_dir,
        ddb=_FakeDdbClient({"g-runs", "g-events"}), s3=_FakeS3Client({"g-artifacts"}),
        ecs=_FakeEcsClient({"g-cluster"}),
        lam=_FakeLambdaClient(_CHAIN, env_by_fn=env_by_fn),
    )


def test_preflight_report_dir_mismatch_fails_fast_naming_both_sides():
    # --report-dir 与推进器 REPORT_DIR 分裂 = 跑完但结果落在用户没指定的前缀下（静默分裂）→ 挡在提交前、点名两侧值。
    # kicker 对上、reconciler 没对上 → 两个推进器都比（不是只看第一个）
    err = _preflight_report_dir("mine", env_by_fn={"g-kicker": {"REPORT_DIR": "mine"},
                                                  "g-reconciler": {"REPORT_DIR": "reports"}})
    assert err is not None
    assert "'mine'" in err and "'reports'" in err and "g-reconciler" in err


def test_preflight_report_dir_mismatch_detected_when_lambda_env_absent():
    # 推进器没配 REPORT_DIR（IaC 有意不注入、Lambda 内缺省 reports）→ 缺键视作 reports，非默认 --report-dir 仍要拦
    err = _preflight_report_dir("mine")
    assert err is not None and "'reports'" in err


def test_preflight_report_dir_match_returns_none():
    # 对偶（防「恒报错」）：两侧一致 → 放行；尾斜杠差异不算冲突（同 S3 前缀规范化）
    assert _preflight_report_dir("reports") is None
    assert _preflight_report_dir("reports/") is None
    assert _preflight_report_dir("mine", env_by_fn={fn: {"REPORT_DIR": "mine"} for fn in _CHAIN}) is None


def test_preflight_report_dir_ignores_exit_observer_env():
    # exit-observer 不读 REPORT_DIR（只写 task_exited）→ 它的 env 不参与比对，别拿它造假冲突
    assert _preflight_report_dir(
        "mine", env_by_fn={"g-kicker": {"REPORT_DIR": "mine"}, "g-reconciler": {"REPORT_DIR": "mine"},
                           "g-exit-observer": {"REPORT_DIR": "reports"}}) is None


def test_preflight_report_dir_not_checked_when_not_passed():
    # 同步 run 不传 report_dir（也不传 lambda_fns）→ 一致性探针整体不生效，只探存在性
    assert _preflight_report_dir(None, env_by_fn={"g-reconciler": {"REPORT_DIR": "whatever"}}) is None


# ---- preflight 的「声明超部署侧 cap」提示（ADR 0034 机制四）：警但不失败 ----

def _preflight_cap(declared, cap_env, warns):
    """跑一次带 cap 提示的 preflight：推进器 env 给 MAX_CONCURRENCY=cap_env；警告收进 warns。"""
    return compose.preflight_cloud_resources(
        prefix="g-", runs_table="g-runs", events_table="g-events", bucket="g-artifacts",
        cluster="g-cluster", lambda_fns=_CHAIN,
        declared_max_concurrency=declared, on_warn=warns.append,
        ddb=_FakeDdbClient({"g-runs", "g-events"}), s3=_FakeS3Client({"g-artifacts"}),
        ecs=_FakeEcsClient({"g-cluster"}),
        lam=_FakeLambdaClient(_CHAIN, env_by_fn={fn: {"MAX_CONCURRENCY": cap_env} for fn in _CHAIN}),
    )


def test_preflight_warns_once_when_declared_max_concurrency_exceeds_cap():
    # 声明 8 > cap 4 → 提交时就告知「本 run 只会按 4 并行」（否则用户以为按 8 跑、只看到莫名慢）。
    # 但**不构成 preflight 失败**：钳制不改产物落点、run 照跑（对照 REPORT_DIR 分岔的退 2——判据 = 分岔后果）。
    warns = []
    err = _preflight_cap(8, "4", warns)
    assert err is None                       # 只警不拦
    assert len(warns) == 1                   # 两推进器同值 → 只警一条，不重复噪声
    assert "8" in warns[0] and "4" in warns[0] and "MAX_CONCURRENCY" in warns[0]


def test_preflight_no_cap_warn_when_declared_within_cap():
    # 对偶（防「恒警」）：声明 2 ≤ cap 4 → 一句不警（提交侧在 cap 以内说了算，没有钳制发生）。
    warns = []
    assert _preflight_cap(2, "4", warns) is None
    assert warns == []


def test_preflight_missing_cluster_detected():
    err = compose.preflight_cloud_resources(
        prefix="g-", runs_table="g-runs", events_table="g-events", bucket="g-artifacts", cluster="g-cluster",
        ddb=_FakeDdbClient({"g-runs", "g-events"}),
        s3=_FakeS3Client({"g-artifacts"}),
        ecs=_FakeEcsClient(set()),  # cluster 非 ACTIVE
    )
    assert err is not None and "g-cluster" in err


# ---- query_deterministic（ADR 0036）：spawn worker 自述、fake subprocess ----

def test_query_deterministic_parses_worker_json(monkeypatch):
    import subprocess

    class _P:
        returncode = 0
        stdout = b'[{"pattern": "p", "description": "d", "example": "e"}]'
        stderr = b""

    captured = {}

    def fake_run(cmd, **kw):
        captured["cmd"] = cmd
        captured["cwd"] = kw.get("cwd")
        return _P()

    monkeypatch.setattr(subprocess, "run", fake_run)
    got = compose.query_deterministic(compose.repo_root(), "novaact")
    assert got == [{"pattern": "p", "description": "d", "example": "e"}]
    assert captured["cmd"][-1] == "--list-deterministic"  # 既有 worker cmd + 自述 flag
    assert "novaact" in " ".join(captured["cmd"])
    assert captured["cwd"] is not None  # 在 worker cwd 下 spawn（相对依赖如 .venv 才可达）


def test_query_deterministic_unknown_engine():
    with pytest.raises(ValueError, match="未知引擎"):
        compose.query_deterministic(compose.repo_root(), "nope")


def test_query_deterministic_worker_failure_raises(monkeypatch):
    import subprocess

    class _P:
        returncode = 1
        stdout = b""
        stderr = "worker exploded".encode()

    monkeypatch.setattr(subprocess, "run", lambda cmd, **kw: _P())
    with pytest.raises(RuntimeError, match="自述失败"):
        compose.query_deterministic(compose.repo_root(), "midscene")


def test_match_deterministic_feeds_stdin_and_parses(monkeypatch):
    import subprocess

    class _P:
        returncode = 0
        stdout = b'[{"pattern": "p", "description": "d"}, null]'
        stderr = b""

    captured = {}

    def fake_run(cmd, **kw):
        captured["cmd"], captured["input"] = cmd, kw.get("input")
        return _P()

    monkeypatch.setattr(subprocess, "run", fake_run)
    got = compose.match_deterministic(compose.repo_root(), "midscene", ["a", "b"])
    assert got == [{"pattern": "p", "description": "d"}, None]
    assert captured["cmd"][-1] == "--match-steps"
    import json as _json
    assert _json.loads(captured["input"].decode()) == ["a", "b"]
