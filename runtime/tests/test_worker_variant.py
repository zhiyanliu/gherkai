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
    """把一个 variant 完整落到 SSM + ECS + ECR（即 push-worker 走完八步后的稳态）。返回各引擎的记录。"""
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
    """默认指针不存在（部署没走过 worker 镜像初始化）→ 提示运行 `gherkai deploy`，不猜 `base`。"""
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
    """CLI **旧于**后端（决策 7「警告不拦」那一种判定）→ 引导升级 CLI，**不**引导去推旧版本 tag 的镜像。

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


def test_deleted_revision_is_a_miss(aws):
    """映射里的 revision 根本不可 Describe（已删除 / 不存在，ECS 回 ClientException）→ miss。"""
    recs = _seed(aws, variant="base")
    rec = dict(recs["novaact"], revision_arn="arn:aws:ecs:us-east-1:123456789012:task-definition/gone:9")
    tag = names.image_tag(_VERSION, "base")
    aws["ssm"].put_parameter(Name=names.ssm_path(_PREFIX, names.worker_image_key("novaact", tag)),
                             Value=json.dumps(rec), Type="String", Overwrite=True)
    with pytest.raises(compose.WorkerVariantError) as e:
        _resolve(aws)
    assert "不可 Describe" in str(e.value)


def test_missing_ecr_repository_is_a_miss(aws):
    """ECR 仓库整个不在（RepositoryNotFoundException）也是「找不到镜像」这一种 miss，重推同名 variant 即恢复。"""
    recs = _seed(aws, variant="base")
    aws["ecr"].delete_repository(repositoryName=names.ecr_repo_name(_PREFIX, "novaact"), force=True)
    with pytest.raises(compose.WorkerVariantError) as e:
        _resolve(aws)
    assert "找不到镜像" in str(e.value) and recs["novaact"]["digest"] in str(e.value)


class _Failing:
    """包一个 moto client，让指定方法抛给定异常（模拟提交者缺只读权限、限流或网络故障），其余方法照常转发。"""

    def __init__(self, inner, method: str, exc: Exception):
        self._inner, self._method, self._exc = inner, method, exc

    def __getattr__(self, name):
        if name == self._method:
            def _raise(**_kw):
                raise self._exc
            return _raise
        return getattr(self._inner, name)


def _client_error(code: str, op: str):
    from botocore.exceptions import ClientError
    return ClientError({"Error": {"Code": code, "Message": "x"}}, op)


@pytest.mark.parametrize("client, method, op", [
    ("ecs", "describe_task_definition", "DescribeTaskDefinition"),
    ("ecr", "describe_images", "DescribeImages"),
])
@pytest.mark.parametrize("code", ["AccessDeniedException", "ThrottlingException"])
def test_access_errors_are_not_misses(aws, client, method, op, code):
    """权限不足 / 限流不是「资源不在」：原样抛 ClientError，由入口按凭证 / region / 权限诊断。

    翻成 WorkerVariantError 会附上「请部署方推送该 variant」的指引，把缺只读权限的提交者引去重推镜像、原地绕圈。
    """
    from botocore.exceptions import ClientError

    _seed(aws, variant="base")
    clients = {**aws, client: _Failing(aws[client], method, _client_error(code, op))}
    with pytest.raises(ClientError) as e:
        compose.resolve_worker_variant(prefix=_PREFIX, variant=None, engines=["novaact"], cli_version=_VERSION,
                                       backend_version=_VERSION, **clients)
    assert not isinstance(e.value, compose.WorkerVariantError)
    assert compose.is_botocore_error(e.value)  # 入口前端靠它归到「凭证 / region / 权限」分支


def test_network_error_on_ecr_is_not_a_miss(aws):
    """连不上端点（BotoCoreError，无错误码）同样原样抛。"""
    from botocore.exceptions import EndpointConnectionError

    _seed(aws, variant="base")
    clients = {**aws, "ecr": _Failing(aws["ecr"], "describe_images",
                                      EndpointConnectionError(endpoint_url="https://api.ecr.us-east-1.amazonaws.com"))}
    with pytest.raises(EndpointConnectionError):
        compose.resolve_worker_variant(prefix=_PREFIX, variant=None, engines=["novaact"], cli_version=_VERSION,
                                       backend_version=_VERSION, **clients)


class _FailingEcs:
    """moto 的 ecs client：描述一律抛 `describe_error`；`list_error` 非 None 时列举也抛它，否则列举照常转发。"""

    def __init__(self, inner, *, describe_error: Exception, list_error: Exception | None = None):
        self._inner, self._describe_error, self._list_error = inner, describe_error, list_error

    def describe_task_definition(self, **_kw):
        raise self._describe_error

    def list_task_definitions(self, **kw):
        if self._list_error is not None:
            raise self._list_error
        return self._inner.list_task_definitions(**kw)

    def __getattr__(self, name):
        return getattr(self._inner, name)


def test_client_exception_on_a_revision_still_listed_as_active_is_not_a_miss(aws):
    """描述报 `ClientException`、而这个 revision 仍在 family 的 ACTIVE revision 里：ECS 对权限问题也可能回这个码，
    描述失败另有原因，原错误原样抛出，不翻成「请推送该 variant」的 miss（ADR 0038「缺失的判定口径」）。"""
    from botocore.exceptions import ClientError

    _seed(aws, variant="base")
    clients = {**aws, "ecs": _FailingEcs(aws["ecs"], describe_error=_client_error("ClientException",
                                                                                  "DescribeTaskDefinition"))}
    with pytest.raises(ClientError) as e:
        compose.resolve_worker_variant(prefix=_PREFIX, variant=None, engines=["novaact"], cli_version=_VERSION,
                                       backend_version=_VERSION, **clients)
    assert not isinstance(e.value, compose.WorkerVariantError)
    assert e.value.response["Error"]["Code"] == "ClientException"


def test_listing_failure_after_a_describe_failure_is_not_a_miss(aws):
    """描述失败、列举 ACTIVE revision 也失败：无法确认 revision 已不在，抛出列举的错误，不翻成 miss。"""
    from botocore.exceptions import ClientError

    _seed(aws, variant="base")
    clients = {**aws, "ecs": _FailingEcs(
        aws["ecs"], describe_error=_client_error("ClientException", "DescribeTaskDefinition"),
        list_error=_client_error("AccessDeniedException", "ListTaskDefinitions"))}
    with pytest.raises(ClientError) as e:
        compose.resolve_worker_variant(prefix=_PREFIX, variant=None, engines=["novaact"], cli_version=_VERSION,
                                       backend_version=_VERSION, **clients)
    assert not isinstance(e.value, compose.WorkerVariantError)
    assert e.value.response["Error"]["Code"] == "AccessDeniedException"


def test_revision_deleted_by_cleanup_is_a_miss(aws):
    """映射所指的 revision 已被注销并删除（清理回收之后的形态）：描述报 `ClientException`，列举确认它不在 ACTIVE revision
    里 → miss，提示推送。"""
    recs = _seed(aws, variant="base")
    arn = recs["novaact"]["revision_arn"]
    aws["ecs"].deregister_task_definition(taskDefinition=arn)
    aws["ecs"].delete_task_definitions(taskDefinitions=[arn])
    with pytest.raises(compose.WorkerVariantError) as e:
        _resolve(aws)
    assert "不可 Describe" in str(e.value) and arn in str(e.value)


class _PagedListing:
    """描述一律报 `ClientException`；列举按 `pages` 分页返回（最后一页不带 `nextToken`），记下每次列举请求的参数。"""

    def __init__(self, pages: list[list[str]]):
        self._pages, self.requests = pages, []

    def describe_task_definition(self, **_kw):
        raise _client_error("ClientException", "DescribeTaskDefinition")

    def list_task_definitions(self, **kw):
        self.requests.append(kw)
        index = int(kw.get("nextToken") or 0)
        resp = {"taskDefinitionArns": self._pages[index]}
        if index + 1 < len(self._pages):
            resp["nextToken"] = str(index + 1)
        return resp


_FAMILY_ARN = "arn:aws:ecs:us-east-1:123456789012:task-definition/gherkai-novaact-worker"


def test_listing_is_read_past_the_first_page_before_a_revision_counts_as_gone():
    """列举分页时读完全部页才下结论：这个 revision 在第二页里即原错误抛出，不当成已删除；各页都没有才返回 None。
    同前缀的另一个 family 的 revision 不算（按完整 ARN 比较）。"""
    from botocore.exceptions import ClientError

    target = f"{_FAMILY_ARN}:7"
    ecs = _PagedListing([[f"{_FAMILY_ARN}-x:7", f"{_FAMILY_ARN}:5"], [target]])
    with pytest.raises(ClientError):
        compose.describe_revision_unless_gone(ecs, target)
    assert [r.get("nextToken") for r in ecs.requests] == [None, "1"]
    assert all(r["familyPrefix"] == "gherkai-novaact-worker" and r["status"] == "ACTIVE" for r in ecs.requests)

    ecs = _PagedListing([[f"{_FAMILY_ARN}-x:7", f"{_FAMILY_ARN}:5"], [f"{_FAMILY_ARN}:6"]])
    assert compose.describe_revision_unless_gone(ecs, target) is None
    assert len(ecs.requests) == 2


def test_one_engine_missing_fails_whole_resolution(aws):
    """一个 run 一个 variant 名、某引擎缺该 variant 即严格失败（ADR 0038）——不给「另一引擎凑合运行」的静默路径。"""
    _seed(aws, variant="base", engines=("novaact",))
    with pytest.raises(compose.WorkerVariantError) as e:
        _resolve(aws, engines=["novaact", "midscene"])
    assert e.value.engine == "midscene"


def test_malformed_ssm_record_is_named(aws):
    """SSM 值不是合法 JSON（人手改坏）→ 点名是哪个参数坏了，不让 JSONDecodeError 原样抛出。"""
    tag = names.image_tag(_VERSION, "base")
    aws["ssm"].put_parameter(Name=names.ssm_path(_PREFIX, names.worker_image_key("novaact", tag)),
                             Value="{不是 JSON", Type="String", Overwrite=True)
    with pytest.raises(compose.WorkerVariantError) as e:
        _resolve(aws, variant="base")
    assert "worker-image/novaact" in str(e.value)


def test_no_cli_version_fails_loud(aws):
    """从源码直接运行取不到自身版本 → 抛（镜像 tag 含版本，无从拼）；fail-loud 好过静默解析成别的版本。"""
    _seed(aws, variant="base")
    with pytest.raises(compose.WorkerVariantError) as e:
        _resolve(aws, cli_version="")
    assert "版本" in str(e.value)


def test_invalid_variant_name_rejected_at_tag_layer(aws):
    """非法 variant 名在 `names.image_tag` 这唯一校验点抛 ValueError（不等到 AWS 那一层才报错）。"""
    _seed(aws, variant="base")
    with pytest.raises(ValueError):
        _resolve(aws, variant="bad/name")


def test_read_worker_default_missing_is_none(aws):
    """默认指针缺失 → None（不抛）：调用方各自决定怎么报（解析函数抛带指引的错、日志只是点名）。"""
    assert compose.read_worker_default(prefix=_PREFIX, ssm=aws["ssm"]) is None
    aws["ssm"].put_parameter(Name=names.ssm_path(_PREFIX, names.WORKER_DEFAULT_KEY),
                             Value="  login  ", Type="String", Overwrite=True)
    assert compose.read_worker_default(prefix=_PREFIX, ssm=aws["ssm"]) == "login"  # strip


# ---- build_fargate_engines：映射外的引擎装空占位项、一用即抛（不 KeyError、不回落 family）----
def test_engine_absent_from_mapping_gets_throwing_placeholder(monkeypatch):
    import gherkai_core.adapters.fargate_engine as fe

    monkeypatch.setattr(fe, "FargateEngine", lambda **kw: ("fake", kw["task_definition"]))
    engines = compose.build_fargate_engines(
        run_id="r1", cluster="c", events_table="ev", bucket="b", report_dir="runs",
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
            run_id="r1", cluster="c", events_table="ev", bucket="b",
            report_dir="runs", network_config={"subnets": ["s"]},
            ecs=object(), s3=object(), ddb_events_table=object(),
        )


def test_never_falls_back_to_healthy_default_when_requested_variant_broken(aws):
    """请求的 variant 坏了而默认 variant 健在 → **仍然抛**（ADR 0038 被拒方案「variant 缺失时静默回落默认」）。

    这是「不回落」这条最容易被实现悄悄破掉的形状：手边正好有一个可运行的默认 variant，回落一下 run 就绿了——
    但那等于替使用方换了 step 集，判定结果不再是他声明的那套。
    """
    _seed(aws, variant="base")  # 默认 base 完整健康
    recs = _seed(aws, variant="login", set_default=False)
    aws["ecs"].deregister_task_definition(taskDefinition=recs["novaact"]["revision_arn"])  # 弄坏 login
    with pytest.raises(compose.WorkerVariantError) as e:
        _resolve(aws, variant="login")
    assert e.value.variant == "login"  # 报的是他要的那个，没偷偷换成 base
