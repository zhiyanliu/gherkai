"""worker variant 解析（ADR 0038「运行时与 preflight」）：variant 名 → 各引擎的 task-def revision ARN。

**证据边界（CLAUDE.md「绿≠对」）**：本文件用 moto 验的是**解析逻辑与 miss 分支**——SSM 键怎么拼、三环校验的
每一环 miss 各自抛什么、提示语按版本 skew 怎么分叉、以及「任何 miss 都不回落」。moto 之外的真实行为不在此列：
真 `RunTask` 吃显式 revision ARN 起得来、ECR `describe_images` 对真 digest 的行为、push 后 digest 与
`describe-images` 一致——都要真账号（本机无 AWS 凭证），归 ADR 0038「实测项」。
"""
from __future__ import annotations

import json

import pytest

from gherkai_runtime import compose, names

_PREFIX = "t-"
_VERSION = "1.4.0"


@pytest.fixture(autouse=True)
def _fake_aws_creds(monkeypatch):
    """硬隔离：假凭证 + 固定 region，绝不误连真 AWS（同 core/tests/conftest.py 的套装）。"""
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
    monkeypatch.delenv("AWS_ENDPOINT_URL", raising=False)


@pytest.fixture
def aws():
    """moto 下的 ssm / ecs / ecr 三个 client（本 ADR 解析路径要读的全部 AWS 面）。"""
    import boto3
    from moto import mock_aws

    with mock_aws():
        yield {
            "ssm": boto3.client("ssm", region_name="us-east-1"),
            "ecs": boto3.client("ecs", region_name="us-east-1"),
            "ecr": boto3.client("ecr", region_name="us-east-1"),
        }


def _register_revision(ecs, engine: str) -> str:
    """注册一个 task-def revision（模拟 push-worker 第 6 步的产物），返回其 ARN。"""
    resp = ecs.register_task_definition(
        family=names.task_def_name(_PREFIX, engine),
        containerDefinitions=[{"name": names.container_name(engine),
                               "image": "repo@sha256:deadbeef", "memory": 512}],
    )
    return resp["taskDefinition"]["taskDefinitionArn"]


def _push_image(ecr, engine: str, tag: str) -> str:
    """在 moto ECR 里建仓库 + 推一个镜像，返回其 digest（模拟 push-worker 第 4 步取到的 manifest digest）。"""
    repo = names.ecr_repo_name(_PREFIX, engine)
    try:
        ecr.create_repository(repositoryName=repo)
    except ecr.exceptions.RepositoryAlreadyExistsException:
        pass
    manifest = {
        "schemaVersion": 2,
        "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
        "config": {"mediaType": "application/vnd.docker.container.image.v1+json",
                   "size": 7023, "digest": "sha256:" + "a" * 64},
        "layers": [{"mediaType": "application/vnd.docker.image.rootfs.diff.tar.gzip",
                    "size": 32654, "digest": "sha256:" + tag.encode().hex().ljust(64, "b")[:64]}],
    }
    resp = ecr.put_image(repositoryName=repo, imageTag=tag, imageManifest=json.dumps(manifest))
    return resp["image"]["imageId"]["imageDigest"]


def _seed(aws, *, variant: str, engines=("novaact",), version: str = _VERSION,
          set_default: bool = True) -> dict[str, dict]:
    """把一个 variant 完整落到 SSM + ECS + ECR（= push-worker 走完八步后的稳态）。返回各引擎的记录。"""
    tag = names.image_tag(version, variant)
    out: dict[str, dict] = {}
    for engine in engines:
        digest = _push_image(aws["ecr"], engine, tag)
        revision_arn = _register_revision(aws["ecs"], engine)
        rec = {"template_arn": f"arn:aws:ecs:us-east-1:1:task-definition/tpl-{engine}:1",
               "revision_arn": revision_arn, "digest": digest,
               "pushed_at": "2026-09-08T00:00:00Z"}
        aws["ssm"].put_parameter(
            Name=names.ssm_path(_PREFIX, names.worker_image_key(engine, tag)),
            Value=json.dumps(rec), Type="String", Overwrite=True)
        out[engine] = rec
    if set_default:
        aws["ssm"].put_parameter(Name=names.ssm_path(_PREFIX, names.WORKER_DEFAULT_KEY),
                                 Value=variant, Type="String", Overwrite=True)
    return out


def _resolve(aws, **kw):
    kw.setdefault("prefix", _PREFIX)
    kw.setdefault("variant", None)
    kw.setdefault("engines", ["novaact"])
    kw.setdefault("cli_version", _VERSION)
    kw.setdefault("backend_version", _VERSION)
    return compose.resolve_worker_variant(ssm=aws["ssm"], ecs=aws["ecs"], ecr=aws["ecr"], **kw)


# ---- 正常路径 ----
def test_variant_none_uses_default_pointer(aws):
    """不给 variant → 取部署级默认指针（ADR 0038「默认指针」）；解析结果带 digest 供打印。"""
    recs = _seed(aws, variant="base")
    got = _resolve(aws)
    assert set(got) == {"novaact"}
    r = got["novaact"]
    assert r.engine == "novaact" and r.variant == "base"
    assert r.revision_arn == recs["novaact"]["revision_arn"]
    assert r.digest == recs["novaact"]["digest"]


def test_explicit_variant_ignores_default_pointer(aws):
    """显式 `--worker-variant` 走该 variant，与默认指针无关（默认指针只是缺省值）。"""
    _seed(aws, variant="base")
    recs = _seed(aws, variant="login", set_default=False)  # 默认仍是 base
    got = _resolve(aws, variant="login")
    assert got["novaact"].variant == "login"
    assert got["novaact"].revision_arn == recs["novaact"]["revision_arn"]


def test_multi_engine_resolves_each(aws):
    """一个 run 一个 variant 名、跨引擎同名（ADR 0038）——按本 run 用到的引擎逐个解析。"""
    recs = _seed(aws, variant="base", engines=("novaact", "midscene"))
    got = _resolve(aws, engines=["novaact", "midscene"])
    assert {e: r.revision_arn for e, r in got.items()} == \
        {e: recs[e]["revision_arn"] for e in ("novaact", "midscene")}


def test_unused_engine_not_probed(aws):
    """只探本 run 用到的引擎（对齐既有 task-def preflight 判据）——另一引擎没镜像也不拦。"""
    _seed(aws, variant="base", engines=("novaact",))  # midscene 完全没推过
    got = _resolve(aws, engines=["novaact"])
    assert set(got) == {"novaact"}


# ---- miss 分支：任一环缺 → 抛，**绝不回落** ----
def test_missing_default_pointer_hints_deploy(aws):
    """默认指针不存在（部署没走过 worker 镜像初始化）→ 提示跑 `gherkai deploy`，不猜 `base`。"""
    _seed(aws, variant="base", set_default=False)
    with pytest.raises(compose.WorkerVariantError) as e:
        _resolve(aws)
    msg = str(e.value)
    assert "gherkai deploy" in msg and names.WORKER_DEFAULT_KEY in msg
    assert e.value.variant is None and e.value.engine is None  # 还没轮到任何引擎


def test_missing_mapping_hints_push_worker_when_same_version(aws):
    """SSM 无该（引擎，variant）映射 + CLI 与后端同版本 → 引导 push-worker，**不回落默认 variant**。"""
    _seed(aws, variant="base")  # 默认 base 存在
    with pytest.raises(compose.WorkerVariantError) as e:
        _resolve(aws, variant="login")  # login 没推过
    msg = str(e.value)
    assert "push-worker" in msg and "--variant login" in msg and "--engine novaact" in msg
    assert "--platform linux/amd64" in msg  # 顺带把 0033 记的架构坑带出来
    assert e.value.engine == "novaact" and e.value.variant == "login"


def test_missing_mapping_hints_cli_upgrade_when_cli_older(aws):
    """CLI **旧于**后端（决策 7「警告不拦」那一档）→ 引导升级 CLI，**不**引导去推旧版本 tag 的镜像。

    理由（ADR 0038 preflight 条）：推一个旧版本命名空间的 tag，推完后端还是解析不到，原地绕圈。
    """
    _seed(aws, variant="base", version="1.5.0")  # 后端已升到 1.5.0
    with pytest.raises(compose.WorkerVariantError) as e:
        _resolve(aws, cli_version="1.4.0", backend_version="1.5.0")
    msg = str(e.value)
    assert "升到后端版本" in msg or "upgrade gherkai" in msg
    assert "push-worker" not in msg


def test_inactive_revision_is_a_miss(aws):
    """映射在、但 revision 已被清理注销（INACTIVE）→ miss（INACTIVE 不能再起新 task），不回落 family。"""
    recs = _seed(aws, variant="base")
    aws["ecs"].deregister_task_definition(taskDefinition=recs["novaact"]["revision_arn"])
    with pytest.raises(compose.WorkerVariantError) as e:
        _resolve(aws)
    assert "不是 ACTIVE" in str(e.value)  # 走的是状态判支（Describe 仍成功、只是 status=INACTIVE）


def test_digest_not_in_ecr_is_a_miss(aws):
    """映射与 revision 都在、但 ECR 里按 digest 找不到镜像 → miss。

    不拦的后果：RunTask 会拖到 Fargate 启动期才 `manifest unknown`（正是 preflight 存在的理由）。
    """
    tag = names.image_tag(_VERSION, "base")
    revision_arn = _register_revision(aws["ecs"], "novaact")
    aws["ecr"].create_repository(repositoryName=names.ecr_repo_name(_PREFIX, "novaact"))
    rec = {"template_arn": "arn:tpl", "revision_arn": revision_arn,
           "digest": "sha256:" + "0" * 64, "pushed_at": "2026-09-08T00:00:00Z"}
    aws["ssm"].put_parameter(Name=names.ssm_path(_PREFIX, names.worker_image_key("novaact", tag)),
                             Value=json.dumps(rec), Type="String", Overwrite=True)
    aws["ssm"].put_parameter(Name=names.ssm_path(_PREFIX, names.WORKER_DEFAULT_KEY),
                             Value="base", Type="String", Overwrite=True)
    with pytest.raises(compose.WorkerVariantError) as e:
        _resolve(aws)
    assert "digest" in str(e.value) and "ECR" in str(e.value)


def test_one_engine_missing_fails_whole_resolution(aws):
    """一个 run 一个 variant 名、某引擎缺该 variant 即严格失败（ADR 0038）——不给「另一引擎凑合跑」的静默档。"""
    _seed(aws, variant="base", engines=("novaact",))
    with pytest.raises(compose.WorkerVariantError) as e:
        _resolve(aws, engines=["novaact", "midscene"])
    assert e.value.engine == "midscene"


def test_malformed_ssm_record_is_named(aws):
    """SSM 值不是合法 JSON（人手改坏）→ 点名是哪个参数坏了，不让 JSONDecodeError 裸奔。"""
    tag = names.image_tag(_VERSION, "base")
    aws["ssm"].put_parameter(Name=names.ssm_path(_PREFIX, names.worker_image_key("novaact", tag)),
                             Value="{不是 JSON", Type="String", Overwrite=True)
    with pytest.raises(compose.WorkerVariantError) as e:
        _resolve(aws, variant="base")
    assert "worker-image/novaact" in str(e.value)


def test_no_cli_version_fails_loud(aws):
    """源码直跑取不到自身版本 → 抛（镜像 tag 含版本，无从拼）；fail-loud 好过静默解析成别的版本。"""
    _seed(aws, variant="base")
    with pytest.raises(compose.WorkerVariantError) as e:
        _resolve(aws, cli_version="")
    assert "版本" in str(e.value)


def test_invalid_variant_name_rejected_at_tag_layer(aws):
    """非法 variant 名在 `names.image_tag` 这唯一校验点抛 ValueError（不到 AWS 那一层才炸）。"""
    _seed(aws, variant="base")
    with pytest.raises(ValueError):
        _resolve(aws, variant="bad/name")


# ---- 宿主的兼容路径：definition 缺 worker_task_defs → 按后端默认指针解析 ----
def test_default_task_defs_for_legacy_definition(aws):
    """旧 definition 的兼容路径（ADR 0038「读侧兼容口径」）：**后端**版本 + 默认指针 → revision ARN。"""
    recs = _seed(aws, variant="base", engines=("novaact", "midscene"), version="1.5.0")
    got = compose.resolve_default_worker_task_defs(
        prefix=_PREFIX, engines=["novaact", "midscene"], backend_version="1.5.0", ssm=aws["ssm"])
    assert got == {e: recs[e]["revision_arn"] for e in ("novaact", "midscene")}


def test_default_task_defs_missing_pointer_raises(aws):
    """默认指针缺失 → 抛（**不回落 family 最新 ACTIVE、不回落模板 revision**，ADR 0038 被拒方案两条）。"""
    _seed(aws, variant="base", set_default=False)
    with pytest.raises(compose.WorkerVariantError):
        compose.resolve_default_worker_task_defs(
            prefix=_PREFIX, engines=["novaact"], backend_version=_VERSION, ssm=aws["ssm"])


def test_default_task_defs_missing_mapping_raises(aws):
    """默认 variant 在该引擎/该后端版本下无映射（如升级后没重推同名 variant）→ 抛，点名修复动作。"""
    _seed(aws, variant="common", engines=("novaact",), version="1.4.0")
    with pytest.raises(compose.WorkerVariantError) as e:
        compose.resolve_default_worker_task_defs(  # 后端已是 1.5.0、common 只有 1.4.0 的
            prefix=_PREFIX, engines=["novaact"], backend_version="1.5.0", ssm=aws["ssm"])
    assert "common" in str(e.value) and "push-worker" in str(e.value)


def test_default_task_defs_no_backend_stamp_raises(aws):
    """后端无版本戳 → 抛（tag 含版本、无从拼）；不猜一个版本、不回落 family。"""
    _seed(aws, variant="base")
    with pytest.raises(compose.WorkerVariantError) as e:
        compose.resolve_default_worker_task_defs(
            prefix=_PREFIX, engines=["novaact"], backend_version=None, ssm=aws["ssm"])
    assert "版本戳" in str(e.value)


def test_read_worker_default_missing_is_none(aws):
    """默认指针缺失 → None（不抛）：调用方各自决定怎么报（解析函数抛带指引的错、日志只是点名）。"""
    assert compose.read_worker_default(prefix=_PREFIX, ssm=aws["ssm"]) is None
    aws["ssm"].put_parameter(Name=names.ssm_path(_PREFIX, names.WORKER_DEFAULT_KEY),
                             Value="  login  ", Type="String", Overwrite=True)
    assert compose.read_worker_default(prefix=_PREFIX, ssm=aws["ssm"]) == "login"  # strip


# ---- build_fargate_engines：映射外的引擎装空腿、一用即抛（不 KeyError、不回落 family）----
def test_engine_absent_from_mapping_gets_throwing_placeholder(monkeypatch):
    import gherkai_core.adapters.fargate_engine as fe

    monkeypatch.setattr(fe, "FargateEngine", lambda **kw: ("fake", kw["task_definition"]))
    engines = compose.build_fargate_engines(
        run_id="r1", prefix=_PREFIX, cluster="c", events_table="ev", bucket="b", report_dir="runs",
        network_config={"subnets": ["s"]},
        worker_task_defs={"novaact": "arn:aws:ecs:us-east-1:1:task-definition/t-novaact-worker:7"},
        ecs=object(), s3=object(), ddb_events_table=object(),
    )
    assert engines["novaact"] == ("fake", "arn:aws:ecs:us-east-1:1:task-definition/t-novaact-worker:7")
    # 没解析的引擎恒在册（resolver 语义不变），但真去起它才抛——且抛的是带指引的结构化异常
    for call in (lambda: engines["midscene"].start_scope(object()),
                 lambda: engines["midscene"].run_scope(object())):
        with pytest.raises(compose.WorkerVariantError) as e:
            call()
        assert "midscene" in str(e.value)


def test_worker_task_defs_is_required():
    """漏传 worker_task_defs → TypeError（不静默缺省成 family 名，ADR 0038 不变量做成硬约束）。"""
    with pytest.raises(TypeError):
        compose.build_fargate_engines(
            run_id="r1", prefix=_PREFIX, cluster="c", events_table="ev", bucket="b",
            report_dir="runs", network_config={"subnets": ["s"]},
            ecs=object(), s3=object(), ddb_events_table=object(),
        )


def test_never_falls_back_to_healthy_default_when_requested_variant_broken(aws):
    """请求的 variant 坏了而默认 variant 健在 → **仍然抛**（ADR 0038 被拒方案「variant 缺失时静默回落默认」）。

    这是「不回落」这条最容易被实现悄悄破掉的形状：手边正好有一个能跑的默认 variant，回落一下 run 就绿了——
    但那等于替使用方换了 step 集，判定结果不再是他声明的那套。
    """
    _seed(aws, variant="base")  # 默认 base 完整健康
    recs = _seed(aws, variant="login", set_default=False)
    aws["ecs"].deregister_task_definition(taskDefinition=recs["novaact"]["revision_arn"])  # 弄坏 login
    with pytest.raises(compose.WorkerVariantError) as e:
        _resolve(aws, variant="login")
    assert e.value.variant == "login"  # 报的是他要的那个，没偷偷换成 base
