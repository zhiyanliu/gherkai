"""`push-worker` 八步 / `deploy` 三步 / 清理 pass / `list-workers` 测试（ADR 0038）。

**证据边界**：AWS 侧全走 moto（SSM/ECS/ECR/DynamoDB），容器引擎走假替身 —— 验的是**编排**（步序、幂等查重、
血缘 tags、退休 tag 的打与摘、清理的各道判定与交错、SSM 记录形状）。交错用钩子壳（`HookedSsm` / `HookedEcs` /
`HookedDdb`）摆到确定的位置上；它们验的是本模块的次序与判据，AWS 侧的可见性与次序（ADR 0038 实测项 10）不在其内。**mock 不出来的两类**另处交代：容器引擎的真实行为在
`test_container.py` 的真 docker 那三条；本文件默认不验证真 ECR 推送或 RunTask 拉起 revision；已完成的真实环境验证及
尚未覆盖的镜像形态见 ADR 0038 实测项 6。协议用例对真实账户执行的结果与适配边界见实测项 9、10。

moto 的两处已知偏差（顺手记下，别当成实现问题）：
- `DescribeTaskDefinition` **不返回 `registeredAt`** → 清理在 moto 下不给孤儿补打 `gherkai:retired-at`（取不到即本趟不打）。
  补打那几支经 `HookedEcs(registered_at=...)` 补上这个字段再验。
- `list_task_definitions` 不分页，故翻页逻辑本身没被 moto 覆盖（实现里带了 `nextToken` 循环）。
"""
from __future__ import annotations

import contextlib
import json
import re
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import boto3
import pytest
from moto import mock_aws

from gherkai_deploy_aws import names, workers
from gherkai_deploy_aws.container import ContainerError, ImageInfo

PREFIX = "gherkai-"
VERSION = "1.4.0"
REGION = "us-east-1"
ACCOUNT = "123456789012"          # moto 的固定账号
REGISTRY = f"{ACCOUNT}.dkr.ecr.{REGION}.amazonaws.com"
NOW = datetime(2026, 9, 8, 12, 0, tzinfo=timezone.utc)


# --------------------------------------------------------------------------- 夹具

@pytest.fixture(autouse=True)
def _aws_env(monkeypatch):
    for var, value in (("AWS_ACCESS_KEY_ID", "t"), ("AWS_SECRET_ACCESS_KEY", "t"),
                       ("AWS_DEFAULT_REGION", REGION), ("AWS_REGION", REGION)):
        monkeypatch.setenv(var, value)
    monkeypatch.delenv("AWS_PROFILE", raising=False)


@pytest.fixture
def aws():
    with mock_aws():
        yield workers.Aws(
            ssm=boto3.client("ssm", region_name=REGION),
            ecs=boto3.client("ecs", region_name=REGION),
            ecr=boto3.client("ecr", region_name=REGION),
            ddb=boto3.client("dynamodb", region_name=REGION),
        )


@pytest.fixture(autouse=True)
def _presentation_is_environment_independent(monkeypatch):
    """人读渲染（ADR 0047）不随运行测试的终端变化：固定关色、表格不按终端取宽——否则 `pytest -s` 在真实终端里会因 ANSI 与折行假红。"""
    from gherkai_runtime import textui
    monkeypatch.setattr(textui, "use_color", lambda: False)
    monkeypatch.setattr(textui, "output_width", lambda: textui.NO_WRAP_WIDTH)


def seed_backend(aws: workers.Aws, *, stamp: str | None = VERSION, cpu: str = "1024") -> dict[str, str]:
    """把「`gherkai deploy` 已经运行过一次」的后端摆出来：ECR repo ×2 + 模板 revision ×2（SSM worker-template）
    + 版本戳 + runs 表（带状态分组索引）。返回 {engine: 模板 revision ARN}。

    `cpu` 供「deploy 改了模板」那组测试造出**第二个**模板 revision。
    """
    templates = {}
    for engine in names.ENGINES:
        repo = names.ecr_repo_name(PREFIX, engine)
        try:
            aws.ecr.create_repository(repositoryName=repo)
        except aws.ecr.exceptions.RepositoryAlreadyExistsException:
            pass
        resp = aws.ecs.register_task_definition(
            family=names.task_def_name(PREFIX, engine),
            containerDefinitions=[{
                "name": names.container_name(engine),
                # CDK 的模板镜像栏是 `<repo-uri>:latest` 占位（ADR 0038「模板 revision」）
                "image": f"{REGISTRY}/{repo}:latest", "cpu": 0, "memory": 2048,
            }],
            requiresCompatibilities=["FARGATE"], networkMode="awsvpc", cpu=cpu, memory="2048",
            # 与 BackendStack 合成出的模板 revision 取值相同（test_stack 的 RuntimePlatform 断言守那一侧）
            runtimePlatform={"cpuArchitecture": "X86_64", "operatingSystemFamily": "LINUX"},
        )
        arn = resp["taskDefinition"]["taskDefinitionArn"]
        templates[engine] = arn
        aws.ssm.put_parameter(Name=names.ssm_path(PREFIX, names.worker_template_key(engine)),
                              Value=arn, Type="String", Overwrite=True)
    if stamp:
        aws.ssm.put_parameter(Name=names.ssm_path(PREFIX, "version"), Value=stamp,
                              Type="String", Overwrite=True)
    table = names.default_name(PREFIX, names.BASE_RUNS_TABLE)
    if table not in aws.ddb.list_tables()["TableNames"]:
        aws.ddb.create_table(
            TableName=table,
            KeySchema=[{"AttributeName": "run_id", "KeyType": "HASH"},
                       {"AttributeName": "item_type", "KeyType": "RANGE"}],
            AttributeDefinitions=[{"AttributeName": "run_id", "AttributeType": "S"},
                                  {"AttributeName": "item_type", "AttributeType": "S"},
                                  {"AttributeName": names.STATE_STATUS_GROUP_ATTR, "AttributeType": "S"}],
            # 键与投影取 BackendStack 状态分组索引的形态（test_stack 逐字比对那一侧）
            GlobalSecondaryIndexes=[{
                "IndexName": names.RUNS_STATUS_GROUP_GSI,
                "KeySchema": [{"AttributeName": names.STATE_STATUS_GROUP_ATTR, "KeyType": "HASH"},
                              {"AttributeName": "run_id", "KeyType": "RANGE"}],
                "Projection": {"ProjectionType": "INCLUDE",
                               "NonKeyAttributes": [names.STATE_WORKER_TASK_DEF_ARNS_ATTR]},
            }],
            BillingMode="PAY_PER_REQUEST",
        )
    return templates


class FakeContainer:
    """容器引擎替身。**只有 push 过的 ref 才有 `repo_digests`**——照抄 overlay2 存储下真 docker 的形态（见 container 模块头：
    本地 build、未推送的镜像 `RepoDigests` 为空）。containerd 镜像存储下 `tag` 之后就有条目，编排只在 `push` 成功返回之后
    才读，两种形态对它等价；在这个替身上提前读会取不到 digest、测试失败。

    `ghcr_noise=True` 时 post-push 的 `repo_digests` **第一条是 GHCR 的**（基础镜像同步路径的真实形态），
    用来让「取第一条」这种实现方式必然测红。
    """

    def __init__(self, *, arch: str | None = "amd64", os_: str | None = "linux", exists: bool = True,
                 digests: list[str] | None = None, ghcr_noise: bool = True, probe_error: str | None = None,
                 multi_platform: bool = False):
        self.arch, self.os_, self.exists = arch, os_, exists
        self.multi_platform = multi_platform  # 本地引用是多平台索引（containerd 镜像存储）
        self.probe_error = probe_error
        self.ghcr_noise = ghcr_noise
        self._queue = list(digests or [])
        self._n = 0
        self.pushed: dict[str, str] = {}
        self.calls: list[tuple] = []

    def _next_digest(self) -> str:
        if self._queue:
            return self._queue.pop(0)
        self._n += 1
        return "sha256:" + f"{self._n:064x}"

    def probe(self):
        self.calls.append(("probe",))
        return self.probe_error

    def inspect(self, ref: str) -> ImageInfo:
        self.calls.append(("inspect", ref))
        if ref in self.pushed:
            repo_uri = ref.rsplit(":", 1)[0]
            entries = []
            if self.ghcr_noise:
                entries.append(f"ghcr.io/zhiyanliu/gherkai-worker-novaact@sha256:{'a' * 64}")
            entries.append(f"{repo_uri}@{self.pushed[ref]}")
            return ImageInfo(exists=True, os=self.os_, architecture=self.arch, repo_digests=tuple(entries),
                             multi_platform=self.multi_platform)
        if not self.exists:
            return ImageInfo(exists=False)
        return ImageInfo(exists=True, os=self.os_, architecture=self.arch, multi_platform=self.multi_platform)

    def tag(self, src, dst):
        self.calls.append(("tag", src, dst))

    def login(self, registry, username, password):
        self.calls.append(("login", registry, username))

    def push(self, ref):
        self.calls.append(("push", ref))
        self.pushed[ref] = self._next_digest()

    def pull(self, ref, *, platform=None):
        self.calls.append(("pull", ref, platform))
        if getattr(self, "pull_fails", False):
            raise ContainerError("模拟 GHCR 拉取失败")


class Spy:
    """boto3 client 的记名壳（验「这一步之前一次 AWS 都没调」）。"""

    def __init__(self, inner):
        self._inner = inner
        self.calls: list[str] = []

    def __getattr__(self, item):
        attr = getattr(self._inner, item)
        if not callable(attr):
            return attr

        def wrapped(*a, **kw):
            self.calls.append(item)
            return attr(*a, **kw)

        return wrapped


class CountingEcs:
    """ECS client 的记参壳（数「同一个 task-def 被 describe 了几次」）——`Spy` 只记方法名，数不出这个。"""

    def __init__(self, inner):
        self._inner = inner
        self.described: list[str] = []

    def describe_task_definition(self, **kw):
        self.described.append(kw["taskDefinition"])
        return self._inner.describe_task_definition(**kw)

    def __getattr__(self, item):
        return getattr(self._inner, item)


class Clock:
    """前进的时钟函数：每读一次前进 `step`，`jump` 模拟两次读之间过了很久；`peek` 读当前值、不前进（测试自己用）。"""

    def __init__(self, start: datetime = NOW, step: timedelta = timedelta(seconds=1)):
        self.t, self.step = start, step

    def __call__(self) -> datetime:
        self.t += self.step
        return self.t

    def peek(self) -> datetime:
        return self.t

    def jump(self, delta: timedelta) -> None:
        self.t += delta


class HookedSsm:
    """SSM client 的钩子壳：每次**新一轮**映射枚举（不带 `NextToken` 的那页）之前 / 之后，写参数之前 / 之后各留一个回调，
    用来把「另一条命令恰在这一刻写映射」「读映射花了很久」这类交错摆到确定的位置上。回调收到第几轮枚举（从 1 计）或
    `put_parameter` 的参数。"""

    def __init__(self, inner, *, before_enumeration=None, after_enumeration=None, before_put=None, after_put=None):
        self._inner = inner
        self.before_enumeration, self.after_enumeration = before_enumeration, after_enumeration
        self.before_put, self.after_put = before_put, after_put
        self.enumerations = 0

    def get_parameters_by_path(self, **kw):
        if "NextToken" not in kw:
            self.enumerations += 1
            if self.before_enumeration:
                self.before_enumeration(self.enumerations)
        resp = self._inner.get_parameters_by_path(**kw)
        if not resp.get("NextToken") and self.after_enumeration:
            self.after_enumeration(self.enumerations)
        return resp

    def put_parameter(self, **kw):
        if self.before_put:
            self.before_put(kw)
        resp = self._inner.put_parameter(**kw)
        if self.after_put:
            self.after_put(kw)
        return resp

    def __getattr__(self, item):
        return getattr(self._inner, item)


class HookedEcs:
    """ECS client 的钩子壳。

    - `registered_at`：给 `DescribeTaskDefinition` 的结果补上 `registeredAt`（moto 不返回这个字段；真实 ECS 返回）。
      取值是一个时刻，或 `{arn: 时刻}`（不在表里的 ARN 不补）。
    - `on_describe(kw, n)`：第 n 次 describe（按 ARN 分别计数，从 1 计）之前调用，可改动 moto 里的状态或抛错。
    - `on_register(arn, n)`：第 n 次注册成功之后调用。
    - `after_tag(arn)`：每次 `TagResource` 成功返回之后调用。
    - `untag_error`：`UntagResource` 一律抛这个异常。
    - `list_error`：`ListTaskDefinitions` 一律抛这个异常。
    - `tagged` 记下每次 `TagResource` 请求的 ARN，`listed` 记下每次 `ListTaskDefinitions` 请求的参数（请求发出即记，
      不论成败）；`untag_failed` 记下底层 `UntagResource` 报错的 ARN（`untag_error` 注入的不算）。
    """

    def __init__(self, inner, *, registered_at=None, on_describe=None, on_register=None, after_tag=None,
                 untag_error=None, list_error=None):
        self._inner = inner
        self.registered_at, self.on_describe, self.on_register = registered_at, on_describe, on_register
        self.after_tag = after_tag
        self.untag_error, self.list_error = untag_error, list_error
        self.describes: dict[str, int] = {}
        self.registered: list[str] = []
        self.tagged: list[str] = []
        self.listed: list[dict] = []
        self.untagged: list[str] = []
        self.untag_failed: list[str] = []
        self.deregistered: list[str] = []

    def describe_task_definition(self, **kw):
        arn = kw["taskDefinition"]
        self.describes[arn] = self.describes.get(arn, 0) + 1
        if self.on_describe:
            self.on_describe(kw, self.describes[arn])
        resp = self._inner.describe_task_definition(**kw)
        when = self.registered_at.get(arn) if isinstance(self.registered_at, dict) else self.registered_at
        if when is not None:
            resp["taskDefinition"]["registeredAt"] = when
        return resp

    def register_task_definition(self, **kw):
        resp = self._inner.register_task_definition(**kw)
        arn = resp["taskDefinition"]["taskDefinitionArn"]
        self.registered.append(arn)
        if self.on_register:
            self.on_register(arn, len(self.registered))
        return resp

    def tag_resource(self, **kw):
        self.tagged.append(kw["resourceArn"])
        resp = self._inner.tag_resource(**kw)
        if self.after_tag:
            self.after_tag(kw["resourceArn"])
        return resp

    def list_task_definitions(self, **kw):
        self.listed.append(kw)
        if self.list_error is not None:
            raise self.list_error
        return self._inner.list_task_definitions(**kw)

    def untag_resource(self, **kw):
        self.untagged.append(kw["resourceArn"])
        if self.untag_error is not None:
            raise self.untag_error
        try:
            return self._inner.untag_resource(**kw)
        except Exception:
            self.untag_failed.append(kw["resourceArn"])
            raise

    def deregister_task_definition(self, **kw):
        self.deregistered.append(kw["taskDefinition"])
        return self._inner.deregister_task_definition(**kw)

    def __getattr__(self, item):
        return getattr(self._inner, item)


INDEX_MISSING = "（索引不存在）"


class HookedDdb:
    """DynamoDB client 的钩子壳：记下每次调用与每次 `Query` 的（索引名、分区键值）；`index_status` 改写 `DescribeTable` 里
    状态分组索引的 `IndexStatus`（`INDEX_MISSING` 即把它从结果里拿掉），`gsis` 把 `DescribeTable` 的索引清单整个换掉，
    `describe_error` / `query_error` 让对应调用抛错，`page_size` 给每次 `Query` 加上 `Limit`、逼出翻页，
    `after_query(resp)` 在每次 `Query` 成功返回之后调用（收到这一页的结果）。"""

    def __init__(self, inner, *, index_status=None, gsis=None, describe_error=None, query_error=None, page_size=None,
                 after_query=None):
        self._inner = inner
        self.index_status, self.gsis = index_status, gsis
        self.describe_error, self.query_error, self.page_size = describe_error, query_error, page_size
        self.after_query = after_query
        self.calls: list[str] = []
        self.queried: list[tuple[str, str]] = []

    def describe_table(self, **kw):
        self.calls.append("describe_table")
        if self.describe_error is not None:
            raise self.describe_error
        resp = self._inner.describe_table(**kw)
        if self.gsis is not None:
            resp["Table"]["GlobalSecondaryIndexes"] = self.gsis
        gsis = resp["Table"].get("GlobalSecondaryIndexes") or []
        if self.index_status == INDEX_MISSING:
            resp["Table"]["GlobalSecondaryIndexes"] = [g for g in gsis if g["IndexName"] != names.RUNS_STATUS_GROUP_GSI]
        elif self.index_status is not None:
            for g in gsis:
                if g["IndexName"] == names.RUNS_STATUS_GROUP_GSI:
                    g["IndexStatus"] = self.index_status
        return resp

    def query(self, **kw):
        self.calls.append("query")
        [value] = kw["ExpressionAttributeValues"].values()
        self.queried.append((kw.get("IndexName"), value["S"]))
        if self.query_error is not None:
            raise self.query_error
        if self.page_size is not None:
            kw = {**kw, "Limit": self.page_size}
        resp = self._inner.query(**kw)
        if self.after_query:
            self.after_query(resp)
        return resp

    def __getattr__(self, item):
        self.calls.append(item)
        return getattr(self._inner, item)


def _client_error(code: str):
    from botocore.exceptions import ClientError

    return ClientError({"Error": {"Code": code, "Message": code}}, "Op")


def _at(t: datetime):
    """固定时刻的时钟函数（被测代码的时间一律经注入的时钟函数取得）。"""
    return lambda: t


def _out():
    """收集打印文本的 out 替身 → (调用函数, 取全文函数)。"""
    lines: list[str] = []
    return (lambda *a: lines.append(" ".join(str(x) for x in a))), (lambda: "\n".join(lines))


def _push(aws, container, *, engine="novaact", variant="login", set_default=False, now=NOW, version=VERSION):
    out, text = _out()
    rc = workers.push_worker("acme:img", engine=engine, variant=variant, set_default=set_default,
                             cli_version=version, prefix=PREFIX, container=container, aws=aws,
                             clock=_at(now), out=out)
    return rc, text()


def _mapping(aws, engine, variant, version=VERSION) -> dict:
    raw = aws.ssm.get_parameter(Name=names.ssm_path(
        PREFIX, names.worker_image_key(engine, names.image_tag(version, variant))))["Parameter"]["Value"]
    return json.loads(raw)


def _revisions(aws, engine) -> list[str]:
    return aws.ecs.list_task_definitions(familyPrefix=names.task_def_name(PREFIX, engine),
                                         status="ACTIVE")["taskDefinitionArns"]


def _tags(aws, arn) -> dict[str, str]:
    resp = aws.ecs.describe_task_definition(taskDefinition=arn, include=["TAGS"])
    return {t["key"]: t["value"] for t in resp.get("tags") or []}


# --------------------------------------------------------------------------- 当前版本映射的筛选

def _image_param(engine, variant, *, version=VERSION, revision="arn:rev", raw=None):
    """`_iter_image_params` 那种 `(engine, tag, value)` 三元组（不过 SSM，直接喂筛选函数）。"""
    tag = names.image_tag(version, variant)
    if raw is None:
        raw = json.dumps({"template_arn": "arn:tpl", "revision_arn": revision,
                          "digest": "sha256:" + "a" * 64, "pushed_at": NOW.isoformat()})
    return engine, tag, raw


def test_current_version_mappings_filters_one_engine_and_version_out_of_a_shared_enumeration():
    """`current_version_mappings` 吃**已枚举好**的参数序列：只留本引擎 + 本版本的、按 variant 名排序，
    读不懂的丢掉、不抛。

    「吃序列而不自己枚举」是接口的一部分——同一份物化结果能连着喂多个引擎，翻页次数才不随引擎数增长
    （逐引擎重走枚举结果一样、只是多打 AWS 调用，只断结果照不出）。
    """
    params = [
        _image_param("novaact", "login"),
        _image_param("novaact", "base"),
        _image_param("novaact", "login", version="1.3.0"),        # 旧版本：留作历史、不参与当前版本解析
        _image_param("midscene", "login"),                        # 另一个引擎
        _image_param("novaact", "broken", raw="{ 这不是 JSON"),    # 坏参数：丢掉、不该让整份列举瘫掉
        _image_param("novaact", "halfwritten", raw='{"template_arn": "arn:tpl"}'),   # 缺键：同上
    ]

    nova = workers.current_version_mappings(params, engine="novaact", version=VERSION)
    assert [m.variant for m in nova] == ["base", "login"], [m.tag for m in nova]
    assert {m.engine for m in nova} == {"novaact"}
    # 同一份序列再喂另一个引擎（多引擎共用一次枚举的实际用法）
    assert [m.variant for m in workers.current_version_mappings(params, engine="midscene", version=VERSION)] \
        == ["login"]
    assert workers.current_version_mappings(params, engine="novaact", version="9.9.9") == []


# --------------------------------------------------------------------------- push-worker 八步

def test_push_worker_happy_path(aws):
    """一次干净的推送：tag/push 到 ECR ref → 从模板注册 revision（镜像按 digest、血缘 tags 齐）→ 写 SSM 映射。"""
    templates = seed_backend(aws)
    c = FakeContainer(digests=["sha256:" + "b" * 64])
    rc, text = _push(aws, c)
    assert rc == 0, text

    repo_uri = f"{REGISTRY}/{names.ecr_repo_name(PREFIX, 'novaact')}"
    target = f"{repo_uri}:1.4.0-login"
    assert ("tag", "acme:img", target) in c.calls and ("push", target) in c.calls
    assert ("login", REGISTRY, "AWS") in c.calls, c.calls   # registry 取自 proxyEndpoint、不拼 STS

    record = _mapping(aws, "novaact", "login")
    assert list(record) == ["template_arn", "revision_arn", "digest", "pushed_at"]  # 四键契约（跨组件读侧）
    assert record["template_arn"] == templates["novaact"]
    assert record["digest"] == "sha256:" + "b" * 64
    assert record["pushed_at"] == NOW.isoformat()

    td = aws.ecs.describe_task_definition(taskDefinition=record["revision_arn"])["taskDefinition"]
    assert td["containerDefinitions"][0]["image"] == f"{repo_uri}@sha256:{'b' * 64}"
    assert td["runtimePlatform"] == {"cpuArchitecture": "X86_64", "operatingSystemFamily": "LINUX"}  # 模板原样带走
    assert _tags(aws, record["revision_arn"]) == {
        names.TAG_VARIANT: "login", names.TAG_VERSION: VERSION,
        names.TAG_DIGEST: "sha256:" + "b" * 64, names.TAG_TEMPLATE: templates["novaact"],
    }
    assert "--worker-variant login" in text


def test_digest_comes_from_post_push_inspect_and_is_picked_by_repo(aws):
    """digest 的唯一来源是 **推送后**那次 inspect，且在多条 `RepoDigests` 里**按本 repo 挑**（GHCR 那条在第一位）。"""
    seed_backend(aws)
    c = FakeContainer(digests=["sha256:" + "c" * 64], ghcr_noise=True)
    rc, text = _push(aws, c)
    assert rc == 0, text
    inspects = [ref for kind, ref in ((k, a[0]) for k, *a in c.calls if k == "inspect")]
    assert len(inspects) == 2 and inspects[0] == "acme:img"           # 推送前一次（存在+架构）
    assert inspects[1].endswith(":1.4.0-login")                       # 推送后一次（取 digest）
    assert _mapping(aws, "novaact", "login")["digest"] == "sha256:" + "c" * 64


def test_missing_this_repo_digest_after_push_exits_2_without_registering(aws):
    """推送后的 inspect 里没有本仓库的条目（只剩 GHCR 那条）→ 以退出码 2 结束、不注册 revision、不写映射。

    提示点名本仓库、请人确认 push 后重新运行这条命令（同一段流程也服务 `gherkai deploy` 的基础镜像同步，不点名 push-worker）。
    """
    seed_backend(aws)

    class NoRepoDigest(FakeContainer):
        def inspect(self, ref):
            info = super().inspect(ref)
            kept = tuple(d for d in info.repo_digests if d.startswith("ghcr.io/"))
            return ImageInfo(exists=info.exists, os=info.os, architecture=info.architecture, repo_digests=kept,
                             multi_platform=info.multi_platform)

    before = _revisions(aws, "novaact")
    rc, text = _push(aws, NoRepoDigest())
    assert rc == 2, text
    assert "取不到本仓库" in text and names.ecr_repo_name(PREFIX, "novaact") in text and "重新运行这条命令" in text
    assert _revisions(aws, "novaact") == before
    with pytest.raises(aws.ssm.exceptions.ParameterNotFound):
        _mapping(aws, "novaact", "login")


def test_arch_mismatch_exits_2_before_touching_ecr_or_ecs(aws):
    """架构判据在**任何 ECR/ECS 动作之前**拦下（ADR 0038 步 2：把 Fargate 启动期的 `exec format error` 提前）。

    「之前」的边界：skew 前置本身是一次 SSM 读（ADR 步 1 就在那儿），故这里断言的是 **ECR/ECS 一次没碰**。
    """
    seed_backend(aws)
    aws = workers.Aws(ssm=aws.ssm, ecs=Spy(aws.ecs), ecr=Spy(aws.ecr), ddb=aws.ddb)
    c = FakeContainer(arch="arm64")
    rc, text = _push(aws, c)
    assert rc == 2
    assert "linux/arm64" in text and "--platform linux/amd64" in text
    assert aws.ecr.calls == [] and aws.ecs.calls == []
    assert not any(k in ("tag", "push", "login") for k, *_ in c.calls)


def test_push_rejects_multi_platform_index_without_amd64_content_with_its_own_hint(aws, capsys):
    """containerd 镜像存储下的多平台索引、本机没有 linux/amd64 内容：同样在任何 ECR/ECS 动作之前拦下，提示说清是索引没有内容、
    而不是「平台是 ?/?」（ADR 0038 步 2）。对偶：索引里有 amd64 内容则照常通过架构判据（别的用例走的 amd64 路径不受影响）。"""
    seed_backend(aws)
    aws = workers.Aws(ssm=aws.ssm, ecs=Spy(aws.ecs), ecr=Spy(aws.ecr), ddb=aws.ddb)
    c = FakeContainer(arch=None, os_=None, multi_platform=True)
    rc, text = _push(aws, c)
    assert rc == 2
    assert "多平台索引" in text and "--platform linux/amd64" in text and "?/?" not in text
    assert aws.ecr.calls == [] and aws.ecs.calls == []
    assert not any(k in ("tag", "push", "login") for k, *_ in c.calls)


def test_missing_local_image_exits_2(aws):
    seed_backend(aws)
    rc, text = _push(aws, FakeContainer(exists=False))
    assert rc == 2 and "本地找不到镜像" in text


def test_skew_block_exits_2_before_any_container_call(aws):
    """CLI **新于**后端 → 以退出码 2 结束、无放行口（ADR 0037 决策 7 三态原样沿用），且**一次容器引擎都不碰**：
    被拦下的人该去升后端，不该先被要求装 docker / build 镜像。提示按本命令所在的包给出 extra 形态。"""
    seed_backend(aws, stamp="1.3.0")
    c = FakeContainer()
    rc, text = _push(aws, c, version="1.4.0")
    assert rc == 2
    assert c.calls == []
    assert "gherkai[deploy-aws]==1.3.0" in text


def test_skew_warn_does_not_block(aws):
    """CLI **旧于**后端 → 警告不拦（tag 用 CLI 自己的版本，故推进的是旧版本命名空间；这是决策 7 的口径）。"""
    seed_backend(aws, stamp="1.5.0")
    rc, text = _push(aws, FakeContainer(), version=VERSION)
    assert rc == 0 and "旧于后端" in text


def test_dedupe_skips_register_when_template_and_digest_match(aws):
    """重推同一份镜像（同模板、同 digest）→ **跳过注册**：`RegisterTaskDefinition` 不幂等，二元组查重是那道闸。"""
    seed_backend(aws)
    c = FakeContainer(digests=["sha256:" + "d" * 64, "sha256:" + "d" * 64])
    rc1, _ = _push(aws, c)
    first = _revisions(aws, "novaact")
    rc2, text = _push(aws, c)
    assert (rc1, rc2) == (0, 0)
    assert _revisions(aws, "novaact") == first, "同二元组不该再注册一个 revision"
    assert "跳过注册" in text


def _register_unmapped(aws, templates, *, digest: str, variant: str = "login", version: str = VERSION,
                       engine: str = "novaact") -> str:
    """按血缘 tags 注册一个不写进映射的 revision（中断在注册与写映射之间留下的那种）。"""
    repo_uri = f"{REGISTRY}/{names.ecr_repo_name(PREFIX, engine)}"
    return workers._register_revision(aws.ecs, template_arn=templates[engine], engine=engine,
                                      image_ref=f"{repo_uri}@{digest}", digest=digest, variant=variant, version=version)


def _failing_mapping_put(aws, *, times: int = 1) -> HookedSsm:
    """写 `worker-image/*` 映射的前 `times` 次抛错（模拟中断在注册与写映射之间）。"""
    left = {"n": times}

    def before_put(kw):
        if "/worker-image/" in kw["Name"] and left["n"] > 0:
            left["n"] -= 1
            raise RuntimeError("模拟中断：写映射之前进程被结束")

    return HookedSsm(aws.ssm, before_put=before_put)


def _fail_default_pointer(kw):
    if kw["Name"] == names.ssm_path(PREFIX, names.WORKER_DEFAULT_KEY):
        raise RuntimeError("模拟失败：写默认指针被拒")


def _failing_default_pointer_put(aws) -> HookedSsm:
    """写默认指针一律抛错：`push-worker --set-default` 在写映射之后、末尾的清理之前失败返回。"""
    return HookedSsm(aws.ssm, before_put=_fail_default_pointer)


def test_interrupted_push_registers_a_new_revision_when_executed_again(aws):
    """中断在注册与写映射之间，重新执行时新注册一个写进映射、不沿用上次注册的那个（ADR 0038 步 5，被拒方案「孤儿复用」）：
    上次那个从未进入映射，留给清理在静默期之后回收。"""
    seed_backend(aws)
    digest = "sha256:" + "e" * 64
    broken = workers.Aws(ssm=_failing_mapping_put(aws), ecs=aws.ecs, ecr=aws.ecr, ddb=aws.ddb)
    rc, _ = _push(broken, FakeContainer(digests=[digest]))
    assert rc == 2
    left = [a for a in _revisions(aws, "novaact") if _tags(aws, a).get(names.TAG_VARIANT) == "login"]
    assert len(left) == 1
    rc, text = _push(aws, FakeContainer(digests=[digest]))
    assert rc == 0, text
    mapped = _mapping(aws, "novaact", "login")["revision_arn"]
    assert mapped not in left and left[0] in _revisions(aws, "novaact")
    assert "复用" not in text and "跳过注册" not in text


@pytest.mark.parametrize("history", ["never_tagged", "tag_removed"])
def test_an_unmapped_revision_is_never_written_into_a_mapping(aws, history):
    """不在映射里、与本次（模板，digest，variant，版本）全同的 revision——从没带过 `gherkai:retired-at`，或带过、又被清理摘掉——
    推送都不把它写进映射：一个 revision 进入映射只有发起注册的那条命令一条路（ADR 0038「候选与静默期起点」段）。"""
    templates = seed_backend(aws)
    digest = "sha256:" + "f" * 64
    left = _register_unmapped(aws, templates, digest=digest)
    if history == "tag_removed":
        _retire_now(aws, left, NOW - timedelta(hours=2))
        aws.ecs.untag_resource(resourceArn=left, tagKeys=[names.TAG_RETIRED_AT])
    rc, text = _push(aws, FakeContainer(digests=[digest]))
    assert rc == 0, text
    assert _mapping(aws, "novaact", "login")["revision_arn"] != left


def test_same_digest_under_another_variant_gets_its_own_revision(aws):
    """同 digest 的另一个 variant 注册自己的 revision、不写进 base 的那个（真账户上遇到过跨 variant 共用：base 换 digest
    重推后共用的 revision 被回收，另一 variant 的映射悬空）。每个新注册的 revision 只被发起注册的那条映射引用。"""
    seed_backend(aws)
    digest = "sha256:" + "a" * 64
    rc, _ = _push(aws, FakeContainer(digests=[digest]), variant="base")
    assert rc == 0
    base_rev = _mapping(aws, "novaact", "base")["revision_arn"]
    rc, text = _push(aws, FakeContainer(digests=[digest]), variant="login")
    assert rc == 0, text
    assert _mapping(aws, "novaact", "login")["revision_arn"] != base_rev
    assert "复用" not in text


OLD_VERSION = "1.3.0"   # 比后端戳旧的 CLI 版本：skew 前置只警告、不拦，可在同一后端上摆出旧版本的映射


def _share_with_old_version(aws, digest: str) -> str:
    """摆出早先版本留下的跨版本共用：旧版本推一份镜像，再把它的映射原样抄成当前版本同名 variant 的映射
    （模板 ARN 与 digest 都一致）→ 两个版本的映射指着同一个 revision，返回其 ARN。"""
    rc, text = _push(aws, FakeContainer(digests=[digest]), version=OLD_VERSION)
    assert rc == 0, text
    old = _mapping(aws, "novaact", "login", version=OLD_VERSION)
    aws.ssm.put_parameter(Name=names.ssm_path(PREFIX, names.worker_image_key("novaact", names.image_tag(VERSION, "login"))),
                          Value=json.dumps(old), Type="String", Overwrite=True)
    return old["revision_arn"]


def test_same_digest_under_another_version_gets_its_own_revision(aws):
    """升级后模板没变、新版本推同一份镜像：旧版本同名 variant 的 revision 与本次（模板 ARN、digest、variant）都一致，
    但当前版本没有映射 → 注册本版本自己的 revision，两个版本的映射不共用（ADR 0038「已退休却仍被映射引用」段）。"""
    seed_backend(aws)
    digest = "sha256:" + "5" * 64
    rc, _ = _push(aws, FakeContainer(digests=[digest]), version=OLD_VERSION)
    assert rc == 0
    old_rev = _mapping(aws, "novaact", "login", version=OLD_VERSION)["revision_arn"]
    before = _revisions(aws, "novaact")
    rc, text = _push(aws, FakeContainer(digests=[digest]))
    assert rc == 0, text
    new_rev = _mapping(aws, "novaact", "login")["revision_arn"]
    assert new_rev != old_rev and new_rev not in before, "跨版本同（模板，digest）不该写进旧版本的 revision"
    assert _tags(aws, new_rev)[names.TAG_VERSION] == VERSION
    assert names.TAG_RETIRED_AT not in _tags(aws, old_rev), "旧版本的映射没被替换，它的 revision 不该被退休"
    assert "复用" not in text


def test_existing_cross_version_sharing_still_takes_the_mapping_fast_path(aws):
    """跳过分支沿用本条映射自己记录的 revision，不拆开早先版本留下的共用：当前版本的映射已指向共用 revision、
    （模板，digest）与本次一致且它仍为 ACTIVE → 跳过注册、沿用它，不另注册一个、也不退休它。"""
    seed_backend(aws)
    digest = "sha256:" + "4" * 64
    shared = _share_with_old_version(aws, digest)
    before = _revisions(aws, "novaact")
    rc, text = _push(aws, FakeContainer(digests=[digest]))
    assert rc == 0, text
    assert "跳过注册" in text
    assert _revisions(aws, "novaact") == before
    assert _mapping(aws, "novaact", "login")["revision_arn"] == shared
    assert names.TAG_RETIRED_AT not in _tags(aws, shared)


def test_repush_retires_the_replaced_revision_and_prints_digest_change(aws):
    """重推同名 variant（新 digest）：新 revision 上位、**旧的只打退休 tag、不删**，并打印「原 digest → 新 digest」。"""
    seed_backend(aws)
    old_digest, new_digest = "sha256:" + "1" * 64, "sha256:" + "2" * 64
    c = FakeContainer(digests=[old_digest, new_digest])
    _push(aws, c)
    old_arn = _mapping(aws, "novaact", "login")["revision_arn"]
    # 真 ECR 里 tag 会指向新 digest；moto 侧手工把「tag 原已存在」摆出来（push 前的 describe-images 那一问）
    aws.ecr.put_image(repositoryName=names.ecr_repo_name(PREFIX, "novaact"),
                      imageManifest=json.dumps({
                          "schemaVersion": 2,
                          "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
                          "config": {"mediaType": "application/vnd.docker.container.image.v1+json",
                                     "size": 1, "digest": "sha256:" + "0" * 64},
                          "layers": [],
                      }),
                      imageTag="1.4.0-login")
    rc, text = _push(aws, c, now=NOW + timedelta(minutes=5))
    new_arn = _mapping(aws, "novaact", "login")["revision_arn"]
    assert rc == 0 and new_arn != old_arn
    assert _tags(aws, old_arn)[names.TAG_RETIRED_AT] == (NOW + timedelta(minutes=5)).isoformat()
    assert old_arn in _revisions(aws, "novaact"), "退休不等于立刻删（运行中 run 的后续 job 还要用它起 task）"
    assert "原 digest" in text and "新 digest" in text


def test_skip_branch_requires_the_mapped_revision_to_be_active(aws):
    """二元组一致、映射所指的 revision 已注销：按映射缺失处理——新注册一个替换悬空的映射，已不是 ACTIVE 的旧 revision
    不打 `gherkai:retired-at`（ADR 0038 步 5 与「注册与回收的竞争」段其三）。"""
    seed_backend(aws)
    digest = "sha256:" + "d" * 64
    _push(aws, FakeContainer(digests=[digest]))
    dangling = _mapping(aws, "novaact", "login")["revision_arn"]
    aws.ecs.deregister_task_definition(taskDefinition=dangling)
    rc, text = _push(aws, FakeContainer(digests=[digest]))
    assert rc == 0, text
    fresh = _mapping(aws, "novaact", "login")["revision_arn"]
    assert fresh != dangling and "跳过注册" not in text and "未能确认" in text
    assert names.TAG_RETIRED_AT not in _tags(aws, dangling)


def test_skip_branch_removes_a_stale_retired_at_from_the_mapped_revision(aws):
    """跳过分支确认 ACTIVE 之后无条件摘一次 `gherkai:retired-at`：此前某次交错留下的 tag 不等到命令末尾的清理（ADR 0038 步 5）。"""
    seed_backend(aws)
    digest = "sha256:" + "d" * 64
    _push(aws, FakeContainer(digests=[digest]))
    arn = _mapping(aws, "novaact", "login")["revision_arn"]
    _retire_now(aws, arn, NOW - timedelta(minutes=10))
    # 写默认指针失败、命令在末尾的清理之前返回：摘除只能来自跳过分支本身
    rc, text = _push(workers.Aws(ssm=_failing_default_pointer_put(aws), ecs=aws.ecs, ecr=aws.ecr, ddb=aws.ddb),
                     FakeContainer(digests=[digest]), set_default=True)
    assert rc == 2 and "跳过注册" in text, text
    assert names.TAG_RETIRED_AT not in _tags(aws, arn)


def _deny_describe_of(arn: str, code: str = "ClientException"):
    """`on_describe` 钩子：描述 `arn` 一律抛 `code`（ECS 对权限问题也可能回 `ClientException`）。"""
    def deny(kw, n):
        if kw["taskDefinition"] == arn:
            raise _client_error(code)
    return deny


@pytest.mark.parametrize("code", ["AccessDeniedException", "ThrottlingException"])
def test_skip_branch_read_failure_other_than_client_exception_fails_the_command_without_listing(aws, code):
    """跳过判据按错误码给读失败分流：读映射所指 revision 时报访问被拒或限流，错误含义明确，原样抛出、命令失败，
    不发列举请求、不新注册（与提交侧 preflight 同一判据）。"""
    seed_backend(aws)
    digest = "sha256:" + "d" * 64
    _push(aws, FakeContainer(digests=[digest]))
    arn = _mapping(aws, "novaact", "login")["revision_arn"]
    before = _revisions(aws, "novaact")
    ecs = HookedEcs(aws.ecs, on_describe=_deny_describe_of(arn, code))
    rc, text = _push(workers.Aws(ssm=aws.ssm, ecs=ecs, ecr=aws.ecr, ddb=aws.ddb), FakeContainer(digests=[digest]))
    assert rc == 2 and code in text, text
    assert ecs.listed == [] and ecs.registered == []
    assert _revisions(aws, "novaact") == before


def test_skip_branch_client_exception_on_a_revision_still_listed_as_active_fails_the_command(aws):
    """描述映射所指的 revision 报 `ClientException`，但它仍在 family 的 ACTIVE revision 里：描述失败另有原因（如权限），
    列举核对之后原错误原样抛出、命令失败，不当成已删除去新注册、替换映射（ADR 0038「缺失的判定口径」）。"""
    seed_backend(aws)
    digest = "sha256:" + "d" * 64
    _push(aws, FakeContainer(digests=[digest]))
    arn = _mapping(aws, "novaact", "login")["revision_arn"]
    before = _revisions(aws, "novaact")
    ecs = HookedEcs(aws.ecs, on_describe=_deny_describe_of(arn))
    rc, text = _push(workers.Aws(ssm=aws.ssm, ecs=ecs, ecr=aws.ecr, ddb=aws.ddb), FakeContainer(digests=[digest]))
    assert rc == 2 and "ClientException" in text, text
    assert len(ecs.listed) == 1 and ecs.registered == []
    assert _revisions(aws, "novaact") == before and _mapping(aws, "novaact", "login")["revision_arn"] == arn


def test_skip_branch_fails_the_command_when_listing_cannot_confirm_the_revision_is_gone(aws):
    """描述报 `ClientException`、列举 ACTIVE revision 被拒：无从核对它是否仍被列出，列举的错误抛出、命令失败，不新注册。"""
    seed_backend(aws)
    digest = "sha256:" + "d" * 64
    _push(aws, FakeContainer(digests=[digest]))
    arn = _mapping(aws, "novaact", "login")["revision_arn"]
    before = _revisions(aws, "novaact")
    ecs = HookedEcs(aws.ecs, on_describe=_deny_describe_of(arn), list_error=_client_error("AccessDeniedException"))
    rc, text = _push(workers.Aws(ssm=aws.ssm, ecs=ecs, ecr=aws.ecr, ddb=aws.ddb), FakeContainer(digests=[digest]))
    assert rc == 2 and "AccessDeniedException" in text, text
    assert ecs.registered == [] and _revisions(aws, "novaact") == before


class _Deleted:
    """摆出「revision 已被删除」：注销它（于是列举 ACTIVE revision 不再有它），并让经 `hook` 的描述报 `ClientException`
    （moto 对已删除的 revision 的形态；真实账户的一次观察中，发起删除后仍能描述该 revision、返回状态为 `DELETE_IN_PROGRESS`，这里摆出的是列举这一支，见 ADR 0038 实测项 11）。

    不调 moto 的 `DeleteTaskDefinitions`：moto 删掉 family 里编号最大的 revision 之后，下一次注册会重用这个编号、
    得到同一个 ARN，真实 ECS 不重用编号。
    """

    def __init__(self, aws):
        self._aws = aws
        self.arns: set[str] = set()

    def delete(self, arn: str) -> None:
        self._aws.ecs.deregister_task_definition(taskDefinition=arn)
        self.arns.add(arn)

    def hook(self, kw, n):
        if kw["taskDefinition"] in self.arns:
            raise _client_error("ClientException")


def test_skip_branch_treats_a_deleted_revision_as_a_missing_mapping(aws):
    """二元组一致、映射所指的 revision 已被删除（描述报 `ClientException`，本次 ACTIVE 列举未发现它）：按映射缺失
    处理，新注册一个替换映射，不给已删除的那个打 tag。"""
    seed_backend(aws)
    digest = "sha256:" + "d" * 64
    _push(aws, FakeContainer(digests=[digest]))
    gone = _mapping(aws, "novaact", "login")["revision_arn"]
    deleted = _Deleted(aws)
    deleted.delete(gone)
    ecs = HookedEcs(aws.ecs, on_describe=deleted.hook)
    rc, text = _push(workers.Aws(ssm=aws.ssm, ecs=ecs, ecr=aws.ecr, ddb=aws.ddb), FakeContainer(digests=[digest]))
    assert rc == 0, text
    assert _mapping(aws, "novaact", "login")["revision_arn"] == ecs.registered[0] != gone
    assert "未能确认" in text and gone not in ecs.tagged


def test_digest_change_does_not_tag_a_replaced_revision_that_is_no_longer_active(aws):
    """改 digest 重推、映射所指的旧 revision 已注销：替换映射之后不对它发打标请求（已不是 ACTIVE 的不打，ADR 0038
    「注册与回收的竞争」段其三），也不打印打标失败的警告。"""
    seed_backend(aws)
    _push(aws, FakeContainer(digests=["sha256:" + "1" * 64]))
    old = _mapping(aws, "novaact", "login")["revision_arn"]
    aws.ecs.deregister_task_definition(taskDefinition=old)
    ecs = HookedEcs(aws.ecs)
    rc, text = _push(workers.Aws(ssm=aws.ssm, ecs=ecs, ecr=aws.ecr, ddb=aws.ddb),
                     FakeContainer(digests=["sha256:" + "2" * 64]))
    assert rc == 0, text
    assert _mapping(aws, "novaact", "login")["revision_arn"] != old
    assert old not in ecs.tagged, ecs.tagged
    assert "记录退休时刻失败" not in text


def _tag_on_register(aws, *, times: int):
    """新注册的前 `times` 个 revision 在注册之后、再读之前被打上 `gherkai:retired-at`（模拟恰有一趟清理给它补打）。"""
    def on_register(arn, n):
        if n <= times:
            _retire_now(aws, arn, NOW)
    return on_register


def test_reread_before_writing_the_mapping_registers_again_once(aws):
    """注册之后、写映射之前再读一次：带着 `gherkai:retired-at` 的不写进映射，重新注册一个，写进映射的是不带 tag 的那个
    （ADR 0038 步 6）。"""
    seed_backend(aws)
    ecs = HookedEcs(aws.ecs, on_register=_tag_on_register(aws, times=1))
    rc, text = _push(workers.Aws(ssm=aws.ssm, ecs=ecs, ecr=aws.ecr, ddb=aws.ddb), FakeContainer())
    assert rc == 0, text
    first, second = ecs.registered
    assert _mapping(aws, "novaact", "login")["revision_arn"] == second
    assert names.TAG_RETIRED_AT in _tags(aws, first) and names.TAG_RETIRED_AT not in _tags(aws, second)


def test_reread_failing_twice_fails_the_command_without_touching_the_mapping(aws):
    """第二次注册的再读仍不满足：命令失败并提示重新执行，映射不改动。"""
    seed_backend(aws)
    old_digest = "sha256:" + "1" * 64
    _push(aws, FakeContainer(digests=[old_digest]))
    before = _mapping(aws, "novaact", "login")
    ecs = HookedEcs(aws.ecs, on_register=_tag_on_register(aws, times=2))
    rc, text = _push(workers.Aws(ssm=aws.ssm, ecs=ecs, ecr=aws.ecr, ddb=aws.ddb),
                     FakeContainer(digests=["sha256:" + "2" * 64]))
    assert rc == 2 and "请稍后重新执行这条命令" in text and len(ecs.registered) == 2
    assert _mapping(aws, "novaact", "login") == before


def _ecs_deleting_on_register(aws, *, times: int) -> HookedEcs:
    """新注册的前 `times` 个 revision 在注册之后、再读之前被删除（模拟一趟清理已把它回收）。"""
    deleted = _Deleted(aws)

    def on_register(arn, n):
        if n <= times:
            deleted.delete(arn)

    return HookedEcs(aws.ecs, on_register=on_register, on_describe=deleted.hook)


def test_reread_finding_the_new_revision_deleted_registers_again(aws):
    """写映射之前的再读发现刚注册的 revision 已被删除：与带着 tag、已不是 ACTIVE 一样重新注册一个，写进映射的是第二个
    （ADR 0038 步 6），不让命令以读取错误结束。"""
    seed_backend(aws)
    ecs = _ecs_deleting_on_register(aws, times=1)
    rc, text = _push(workers.Aws(ssm=aws.ssm, ecs=ecs, ecr=aws.ecr, ddb=aws.ddb), FakeContainer())
    assert rc == 0, text
    first, second = ecs.registered
    assert _mapping(aws, "novaact", "login")["revision_arn"] == second
    assert first not in _revisions(aws, "novaact")


def test_reread_finding_both_new_revisions_deleted_fails_the_command(aws):
    """连续两次注册的 revision 在再读时都已被删除：命令失败并提示重新执行，映射不改动。"""
    seed_backend(aws)
    _push(aws, FakeContainer(digests=["sha256:" + "1" * 64]))
    before = _mapping(aws, "novaact", "login")
    ecs = _ecs_deleting_on_register(aws, times=2)
    rc, text = _push(workers.Aws(ssm=aws.ssm, ecs=ecs, ecr=aws.ecr, ddb=aws.ddb),
                     FakeContainer(digests=["sha256:" + "2" * 64]))
    assert rc == 2 and "请稍后重新执行这条命令" in text and len(ecs.registered) == 2, text
    assert _mapping(aws, "novaact", "login") == before


class _UnlistedEcs(HookedEcs):
    """摆出「刚注册的 revision 尚未在查询结果中可见」：新注册的前 `times` 个 revision 实际为 ACTIVE，但经本壳的描述报
    `ClientException`，列举 ACTIVE revision 的结果里也没有它。直接经 moto 读取仍看得到它的真实状态。"""

    def __init__(self, inner, *, times: int):
        self.hidden: set[str] = set()

        def hide(arn, n):
            if n <= times:
                self.hidden.add(arn)

        def deny(kw, n):
            if kw["taskDefinition"] in self.hidden:
                raise _client_error("ClientException")

        super().__init__(inner, on_register=hide, on_describe=deny)

    def list_task_definitions(self, **kw):
        resp = super().list_task_definitions(**kw)
        return {**resp, "taskDefinitionArns": [a for a in resp["taskDefinitionArns"] if a not in self.hidden]}


def test_reread_not_yet_listing_the_new_revision_registers_a_second_one(aws):
    """再读时刚注册的 revision 描述报 `ClientException`、ACTIVE 列举暂时还没有它：按本次未确认可用处理，再注册一个并把
    第二个写进映射。第一个实际仍为 ACTIVE（未列出不证明它已被注销或删除），只是多出一条从未被映射引用的 revision。"""
    seed_backend(aws)
    ecs = _UnlistedEcs(aws.ecs, times=1)
    rc, text = _push(workers.Aws(ssm=aws.ssm, ecs=ecs, ecr=aws.ecr, ddb=aws.ddb), FakeContainer())
    assert rc == 0, text
    first, second = ecs.registered
    assert first != second and _mapping(aws, "novaact", "login")["revision_arn"] == second
    assert {first, second} <= set(_revisions(aws, "novaact"))


def test_reread_not_yet_listing_either_new_revision_fails_the_command(aws):
    """连续两次再读都未在 ACTIVE 列举里发现刚注册的 revision：命令失败、映射不改动，提示说明它可能尚未可见、请稍后重新
    执行；两个 revision 实际都仍为 ACTIVE。"""
    seed_backend(aws)
    _push(aws, FakeContainer(digests=["sha256:" + "1" * 64]))
    before = _mapping(aws, "novaact", "login")
    ecs = _UnlistedEcs(aws.ecs, times=2)
    rc, text = _push(workers.Aws(ssm=aws.ssm, ecs=ecs, ecr=aws.ecr, ddb=aws.ddb),
                     FakeContainer(digests=["sha256:" + "2" * 64]))
    assert rc == 2 and len(ecs.registered) == 2, text
    assert ("连续两次未能确认刚注册的 novaact/login revision 可用且未被标记为待清理，映射没有改动。"
            "revision 可能已被标记为待清理、已注销或已删除，也可能尚未在查询结果中可见；请稍后重新执行这条命令。") in text
    assert _mapping(aws, "novaact", "login") == before
    assert set(ecs.registered) <= set(_revisions(aws, "novaact"))


def test_new_revision_reclaimed_by_real_cleanup_passes_before_the_reread_is_registered_again(aws):
    """两趟真实的清理 pass 在注册与再读之间回收刚注册的 revision：第一趟按孤儿补打 `gherkai:retired-at`，时钟推进过静默期
    之后第二趟注销并删除它；推送继续时再读未在 ACTIVE 列举里发现它，重新注册一个并写进映射。

    moto 删掉 family 里编号最大的 revision 之后，下一次注册重用这个编号、得到同一个 ARN（真实 ECS 不重用编号），所以这里
    按注册次数与映射所指 revision 的状态断言，不比较两次注册的 ARN。"""
    seed_backend(aws)
    t = [NOW]
    clock = lambda: t[0]  # noqa: E731
    cleaner = HookedEcs(aws.ecs, registered_at=NOW - timedelta(minutes=10))
    passes: list[workers.CleanupOutcome] = []

    def reclaim(arn, n):
        if n != 1:
            return
        passes.append(_cleanup(aws, clock, ecs=cleaner)[0])
        assert names.TAG_RETIRED_AT in _tags(aws, arn)
        t[0] += workers.RETIRE_QUIET_PERIOD + timedelta(minutes=1)
        passes.append(_cleanup(aws, clock, ecs=cleaner)[0])
        assert arn in passes[-1].deleted

    ecs = HookedEcs(aws.ecs, on_register=reclaim)
    out, text = _out()
    rc = workers.push_worker("acme:img", engine="novaact", variant="login", set_default=False, cli_version=VERSION,
                             prefix=PREFIX, container=FakeContainer(),
                             aws=workers.Aws(ssm=aws.ssm, ecs=ecs, ecr=aws.ecr, ddb=aws.ddb), clock=clock, out=out)
    assert rc == 0, text()
    assert len(passes) == 2 and len(ecs.registered) == 2
    mapped = _mapping(aws, "novaact", "login")["revision_arn"]
    assert mapped == ecs.registered[1] and mapped in _revisions(aws, "novaact")
    assert names.TAG_RETIRED_AT not in _tags(aws, mapped)


def test_writing_the_mapping_is_followed_by_removing_retired_at_from_the_new_revision(aws):
    """写映射成功之后立即对写进映射的 revision 无条件摘除 `gherkai:retired-at`：再读之后、写映射之前被补打的 tag
    不留在在用的 revision 上（ADR 0038 步 7 与「打 tag 与写映射的交错」段）。"""
    seed_backend(aws)

    def tag_just_before_write(kw):
        if "/worker-image/" in kw["Name"]:
            _retire_now(aws, json.loads(kw["Value"])["revision_arn"], NOW)

    def before_put(kw):
        tag_just_before_write(kw)
        _fail_default_pointer(kw)

    # 写默认指针失败、命令在末尾的清理之前返回：摘除只能来自写映射之后的那一步
    ssm = HookedSsm(aws.ssm, before_put=before_put)
    rc, text = _push(workers.Aws(ssm=ssm, ecs=aws.ecs, ecr=aws.ecr, ddb=aws.ddb), FakeContainer(), set_default=True)
    assert rc == 2, text
    assert names.TAG_RETIRED_AT not in _tags(aws, _mapping(aws, "novaact", "login")["revision_arn"])


def test_failing_to_remove_retired_at_after_writing_the_mapping_only_warns(aws):
    seed_backend(aws)
    ecs = HookedEcs(aws.ecs, untag_error=RuntimeError("Throttling"))
    rc, text = _push(workers.Aws(ssm=aws.ssm, ecs=ecs, ecr=aws.ecr, ddb=aws.ddb), FakeContainer())
    assert rc == 0, text
    assert "警告：未能去掉在用 revision" in text and "Throttling" in text


def test_retired_at_of_the_replaced_revision_is_read_after_the_mapping_write(aws):
    """替换的一步打的值不早于写映射成功的时刻（ADR 0038「时钟（实装要求）」段）：时钟在命令开始之后、写映射之前已走了很久，
    值取的是写映射之后的那一刻，不是命令开始时、也不是推送时间。"""
    seed_backend(aws)
    _push(aws, FakeContainer(digests=["sha256:" + "1" * 64]))
    old = _mapping(aws, "novaact", "login")["revision_arn"]
    clock = Clock()
    written: list[datetime] = []

    def before_put(kw):
        if "/worker-image/" in kw["Name"]:
            clock.jump(timedelta(hours=3))      # 写映射这一步之前过了很久

    def after_put(kw):
        if "/worker-image/" in kw["Name"]:
            written.append(clock.peek())

    out, text = _out()
    rc = workers.push_worker("acme:img", engine="novaact", variant="login", cli_version=VERSION, prefix=PREFIX,
                             container=FakeContainer(digests=["sha256:" + "2" * 64]),
                             aws=workers.Aws(ssm=HookedSsm(aws.ssm, before_put=before_put, after_put=after_put),
                                             ecs=aws.ecs, ecr=aws.ecr, ddb=aws.ddb), clock=clock, out=out)
    assert rc == 0, text()
    assert workers._parse_ts(_tags(aws, old)[names.TAG_RETIRED_AT]) >= written[0]


def test_set_default_writes_pointer_and_warns_about_the_other_engine(aws):
    """`--set-default`：写指针；该 variant 在**另一个引擎**尚无镜像 → **警告不拦**（单引擎团队不必凭空推另一引擎）。"""
    seed_backend(aws)
    rc, text = _push(aws, FakeContainer(), set_default=True)
    assert rc == 0
    assert aws.ssm.get_parameter(Name=names.ssm_path(PREFIX, names.WORKER_DEFAULT_KEY)
                                 )["Parameter"]["Value"] == "login"
    assert "警告" in text and "midscene" in text and "1.4.0-login" in text


def test_set_default_no_warning_once_both_engines_have_it(aws):
    seed_backend(aws)
    _push(aws, FakeContainer(), engine="midscene")
    rc, text = _push(aws, FakeContainer(), engine="novaact", set_default=True)
    assert rc == 0 and "尚无镜像" not in text


def test_missing_template_points_at_gherkai_deploy(aws):
    """模板参数由 **stack 资源**写（随 cdk 事务）——缺它就是「这个 prefix 还没部署」，提示指向 `gherkai deploy`。"""
    seed_backend(aws)
    aws.ssm.delete_parameter(Name=names.ssm_path(PREFIX, names.worker_template_key("novaact")))
    rc, text = _push(aws, FakeContainer())
    assert rc == 2 and "gherkai deploy" in text


def test_bad_variant_name_is_rejected_by_the_tag_rule(aws):
    seed_backend(aws)
    rc, text = _push(aws, FakeContainer(), variant="-bad")
    assert rc == 2 and "variant 名不合法" in text


# --------------------------------------------------------------------------- 清理 pass

def _retire_now(aws, arn, when: datetime):
    aws.ecs.tag_resource(resourceArn=arn, tags=[{"key": names.TAG_RETIRED_AT, "value": when.isoformat()}])


def _cleanup(aws, now, *, ecs=None, ssm=None, ddb=None, engines=names.ENGINES):
    out, text = _out()
    return workers.cleanup_pass(prefix=PREFIX, engines=engines, ssm=ssm or aws.ssm, ecs=ecs or aws.ecs,
                                ddb=ddb or aws.ddb, clock=now if callable(now) else _at(now), out=out), text()


def _unmapped_retired(aws, templates, *, retired_at: datetime, variant: str = "login",
                      digest: str = "sha256:" + "b" * 64) -> str:
    """一个已退休（`gherkai:retired-at` = `retired_at`）、不在任何映射里的 revision。"""
    arn = _register_unmapped(aws, templates, digest=digest, variant=variant)
    _retire_now(aws, arn, retired_at)
    return arn


def _put_state(aws, run_id: str, status: str, arns: list[str]):
    """一个 run 的 STATE item：分组属性取 core 写端的同一个派生函数，与 `DynamoDBRunStore` 写出的形态一致。"""
    from gherkai_core.adapters.run_store.ddb import status_group
    from gherkai_core.model import Status

    aws.ddb.put_item(TableName=names.default_name(PREFIX, names.BASE_RUNS_TABLE), Item={
        "run_id": {"S": run_id}, "item_type": {"S": "STATE"}, "status": {"S": status},
        names.STATE_STATUS_GROUP_ATTR: {"S": status_group(Status(status))},
        names.STATE_WORKER_TASK_DEF_ARNS_ATTR: {"L": [{"S": a} for a in arns]},
    })


def _write_mapping_to(aws, arn: str, *, variant: str = "late"):
    """另一条命令把 `arn` 写进一条映射（交错用例里摆在某一刻）。"""
    aws.ssm.put_parameter(
        Name=names.ssm_path(PREFIX, names.worker_image_key("novaact", f"{VERSION}-{variant}")),
        Value=json.dumps({"template_arn": "arn:tpl", "revision_arn": arn, "digest": "sha256:" + "0" * 64,
                          "pushed_at": NOW.isoformat()}),
        Type="String", Overwrite=True)


def test_cleanup_keeps_within_the_quiet_period(aws):
    """退休未满 1 小时 → 不删。静默期覆盖「preflight 刚解析成 R、definition 尚未落库」的窗口 +
    注销后最多 10 分钟才生效的 AWS 延迟。"""
    templates = seed_backend(aws)
    arn = _unmapped_retired(aws, templates, retired_at=NOW)
    outcome, _ = _cleanup(aws, NOW + timedelta(minutes=59))
    assert outcome.deleted == ()
    assert any(a == arn and "静默期" in why for a, why in outcome.kept)
    assert arn in _revisions(aws, "novaact")


def test_cleanup_deletes_after_quiet_period_when_unreferenced(aws):
    templates = seed_backend(aws)
    arn = _unmapped_retired(aws, templates, retired_at=NOW)
    outcome, _ = _cleanup(aws, NOW + timedelta(hours=2))
    assert outcome.deleted == (arn,), outcome
    assert arn not in _revisions(aws, "novaact")


def test_cleanup_removes_retired_at_from_a_revision_that_is_still_mapped(aws):
    """仍在任一映射里的 revision 不是候选；它若带着 `gherkai:retired-at`，清理摘掉这个 tag（ADR 0038「候选与静默期起点」段）。"""
    seed_backend(aws)
    _push(aws, FakeContainer())
    arn = _mapping(aws, "novaact", "login")["revision_arn"]
    _retire_now(aws, arn, NOW - timedelta(hours=3))
    outcome, _ = _cleanup(aws, NOW)
    assert outcome.deleted == () and all(a != arn for a, _ in outcome.kept)
    assert names.TAG_RETIRED_AT not in _tags(aws, arn)
    assert arn in _revisions(aws, "novaact")


@pytest.mark.parametrize("status", ["pending", "running"])
def test_cleanup_keeps_when_a_live_run_references_it(aws, status):
    """引用快照里有它（STATE 顶层 `worker_task_def_arns`，run 未到终态）→ 留着。detached run 逐 job 起 task，删早了剩余
    job 全起不来。两个非终态都在 `live` 分组里。"""
    templates = seed_backend(aws)
    arn = _unmapped_retired(aws, templates, retired_at=NOW)
    _put_state(aws, "r1", status, [arn])
    outcome, _ = _cleanup(aws, NOW + timedelta(hours=2))
    assert outcome.deleted == ()
    assert any(a == arn and "未到终态" in why for a, why in outcome.kept)


def test_cleanup_deletes_when_the_referencing_run_is_terminal(aws):
    """同一份数据、run 已到终态（passed）→ 不在 `live` 分组里，引用快照不含它。"""
    templates = seed_backend(aws)
    arn = _unmapped_retired(aws, templates, retired_at=NOW)
    _put_state(aws, "r1", "passed", [arn])
    outcome, _ = _cleanup(aws, NOW + timedelta(hours=2))
    assert outcome.deleted == (arn,), outcome


def test_one_query_reads_both_a_pending_and_a_running_run(aws):
    """`pending` 与 `running` 的 run 在同一次 `Query`（状态分组索引的 `live` 分组）里被读到：两个各被一个 run 引用的成熟
    候选都留下，整趟只查一次，不按状态分区逐个读（ADR 0038「引用检查」段③）。"""
    templates = seed_backend(aws)
    pending_ref = _unmapped_retired(aws, templates, retired_at=NOW - timedelta(hours=3), variant="a", digest="sha256:" + "1" * 64)
    running_ref = _unmapped_retired(aws, templates, retired_at=NOW - timedelta(hours=3), variant="b", digest="sha256:" + "2" * 64)
    _put_state(aws, "r1", "pending", [pending_ref])
    _put_state(aws, "r2", "running", [running_ref])
    ddb = HookedDdb(aws.ddb)
    outcome, _ = _cleanup(aws, NOW, ddb=ddb)
    assert outcome.deleted == ()
    assert {a for a, why in outcome.kept if "未到终态" in why} == {pending_ref, running_ref}, outcome
    assert ddb.queried == [(names.RUNS_STATUS_GROUP_GSI, names.STATUS_GROUP_LIVE)]


def test_snapshot_reads_every_page_of_the_live_group_and_leaves_out_finished_runs(aws):
    """快照按 `LastEvaluatedKey` 翻页读完 `live` 分组、取 `worker_task_def_arns` 的并集；已收尾的 run（各终态）不在快照里，
    不带 revision 列表的 run 不贡献 ARN。"""
    from gherkai_core.model import TERMINAL_STATUSES

    seed_backend(aws)
    table = names.default_name(PREFIX, names.BASE_RUNS_TABLE)
    _put_state(aws, "r-live-1", "pending", ["arn:a", "arn:b"])
    _put_state(aws, "r-live-2", "running", ["arn:b", "arn:c"])
    _put_state(aws, "r-live-3", "running", ["arn:d"])
    _put_state(aws, "r-live-4", "pending", [])
    for i, status in enumerate(sorted(s.value for s in TERMINAL_STATUSES)):
        _put_state(aws, f"r-done-{i}", status, [f"arn:done-{status}"])
    ddb = HookedDdb(aws.ddb, page_size=1)
    assert workers._live_reference_snapshot(ddb, table) == {"arn:a", "arn:b", "arn:c", "arn:d"}
    assert len(ddb.queried) > 1 and set(ddb.queried) == {(names.RUNS_STATUS_GROUP_GSI, names.STATUS_GROUP_LIVE)}


def test_snapshot_sees_what_the_real_run_store_writes_until_the_run_finishes(aws):
    """跨组件：core 的 `DynamoDBRunStore` 真写端写出的 STATE 被真快照读到。建 run 后、换到 `running` 后都在 `live` 分组里，
    收尾之后不在；META item 与不带 revision 的 run 不贡献 ARN（ADR 0038「不变量」清理 pass 条「引用检查」段③）。"""
    from gherkai_core.adapters.run_store.ddb import DynamoDBRunStore
    from gherkai_core.model import JobState, RunMeta, RunState, Status

    seed_backend(aws)
    table = names.default_name(PREFIX, names.BASE_RUNS_TABLE)
    store = DynamoDBRunStore(boto3.resource("dynamodb", region_name=REGION).Table(table))

    def create(run_id: str, worker_task_defs: dict[str, str] | None) -> None:
        meta = RunMeta(run_id=run_id, created_at="2026-09-08T00:00:00Z", jobs=(), worker_task_defs=worker_task_defs)
        state = RunState(run_id=run_id, status=Status.PENDING,
                         jobs={"a.feature:3": JobState(scope_id="a.feature:3", status=Status.PENDING)})
        store.create_run(meta, state)

    create("run-01", {"novaact": "arn:shared", "midscene": "arn:shared"})
    create("run-02", None)
    assert workers._live_reference_snapshot(aws.ddb, table) == {"arn:shared"}
    store.update_job_state("run-01", JobState(scope_id="a.feature:3", status=Status.RUNNING))
    assert workers._live_reference_snapshot(aws.ddb, table) == {"arn:shared"}
    store.finalize_run("run-01", Status.PASSED, "2026-09-08T00:10:00Z")
    assert workers._live_reference_snapshot(aws.ddb, table) == set()


@pytest.mark.parametrize("finalize", ["try_finalize", "finalize_run"])
def test_cleanup_keeps_a_revision_while_its_run_is_pending_or_running_and_reclaims_it_after_the_run_finishes(
        aws, finalize):
    """同一个 run 先拦下、收尾之后再回收（ADR 0038 实测项 9 前半，「引用检查」段③④与「为什么一次快照就够」段其三）。
    run 由 core 的 `DynamoDBRunStore` 真写端建立并推进，清理每一趟都经状态分组索引的 `live` 分组取一次快照。串起的步骤：

    1. 一个不在任何映射里、`gherkai:retired-at` 早已满静默期的 revision R；写端建一个引用 R 的 run，run 级为 `pending`。
    2. 一趟清理：R 是成熟候选，快照里有它，留下，原因是有未到终态的 run 引用；不发注销请求，R 仍为 ACTIVE、tag 不变。
    3. 写端把一个 job 写成 `running`，run 级随同一次写换到 `running`；再一趟清理同样留下 R。
    4. 写端以一条终态写收尾（`try_finalize` 与 `finalize_run` 各走一遍），run 离开 `live` 分组；下一趟清理回收 R。

    守的是：两个非终态都经同一个分组拦下同一个 revision，run 收尾之后的下一趟不再被它拦下。每一趟只查 `live` 分组一次。"""
    from gherkai_core.adapters.run_store.ddb import DynamoDBRunStore
    from gherkai_core.model import JobState, RunMeta, RunState, Status

    templates = seed_backend(aws)
    arn = _unmapped_retired(aws, templates, retired_at=NOW - timedelta(hours=3))
    retired_raw = _tags(aws, arn)[names.TAG_RETIRED_AT]
    table = names.default_name(PREFIX, names.BASE_RUNS_TABLE)
    store = DynamoDBRunStore(boto3.resource("dynamodb", region_name=REGION).Table(table))
    scope = "a.feature:3"
    store.create_run(
        RunMeta(run_id="run-01", created_at="2026-09-08T09:00:00Z", jobs=(), worker_task_defs={"novaact": arn}),
        RunState(run_id="run-01", status=Status.PENDING, jobs={scope: JobState(scope_id=scope, status=Status.PENDING)}))

    def one_pass(at: datetime):
        ecs, ddb = HookedEcs(aws.ecs), HookedDdb(aws.ddb)
        outcome, _ = _cleanup(aws, at, ecs=ecs, ddb=ddb)
        assert ddb.queried == SNAPSHOT_DONE, ddb.queried
        return outcome, ecs

    for i, status in enumerate((Status.PENDING, Status.RUNNING)):
        if status == Status.RUNNING:
            store.update_job_state("run-01", JobState(scope_id=scope, status=Status.RUNNING))
        assert store.load_run_state("run-01").status == status
        outcome, ecs = one_pass(NOW + timedelta(minutes=i))
        assert outcome.deleted == () and ecs.deregistered == [], (status, outcome)
        assert any(a == arn and "仍有未到终态的 run 引用" in why for a, why in outcome.kept), (status, outcome)
        assert arn in _revisions(aws, "novaact") and _tags(aws, arn)[names.TAG_RETIRED_AT] == retired_raw

    if finalize == "try_finalize":
        assert store.try_finalize("run-01", Status.PASSED, "2026-09-08T12:05:00Z") is True
    else:
        store.finalize_run("run-01", Status.PASSED, "2026-09-08T12:05:00Z")
    assert store.load_run_state("run-01").status == Status.PASSED
    outcome, ecs = one_pass(NOW + timedelta(minutes=10))
    assert outcome.deleted == (arn,) and ecs.deregistered == [arn], outcome
    assert arn not in _revisions(aws, "novaact")


def test_cleanup_backfills_retired_at_on_an_orphan_with_a_value_after_reading_the_mappings(aws):
    """不在任何映射里、还没有 `gherkai:retired-at`、`registeredAt` 早于本趟读映射的时刻 → 补打、本趟留下。补打的值不早于
    读完映射的时刻：读映射之前已过了很久（命令开始时刻早得多）时，值仍取补打那一刻（ADR 0038「时钟（实装要求）」段）。"""
    templates = seed_backend(aws)
    orphan = _register_unmapped(aws, templates, digest="sha256:" + "9" * 64, variant="stray")
    clock = Clock()
    read_done: list[datetime] = []
    ssm = HookedSsm(aws.ssm, before_enumeration=lambda n: clock.jump(timedelta(hours=2)) if n == 1 else None,
                    after_enumeration=lambda n: read_done.append(clock.peek()))
    ecs = HookedEcs(aws.ecs, registered_at=NOW - timedelta(days=1))
    outcome, _ = _cleanup(aws, clock, ssm=ssm, ecs=ecs)
    assert outcome.deleted == ()
    assert any(a == orphan and "记录退休时刻" in why for a, why in outcome.kept), outcome
    assert workers._parse_ts(_tags(aws, orphan)[names.TAG_RETIRED_AT]) >= read_done[0]


@pytest.mark.parametrize("registered_at", ["missing", "not_before_t1"])
def test_cleanup_does_not_backfill_when_registered_at_is_missing_or_not_before_reading(aws, registered_at):
    """`registeredAt` 取不到（moto 即如此）或不早于本趟开始读映射的时刻（另一条命令刚注册、尚未写映射）→ 本趟不打、留下。"""
    templates = seed_backend(aws)
    orphan = _register_unmapped(aws, templates, digest="sha256:" + "9" * 64, variant="stray")
    clock = Clock(start=NOW, step=timedelta(0))   # 不前进：t1 恰为 NOW
    ecs = HookedEcs(aws.ecs, registered_at=None if registered_at == "missing" else NOW)
    ddb = HookedDdb(aws.ddb)
    outcome, _ = _cleanup(aws, clock, ecs=ecs, ddb=ddb)
    assert outcome.deleted == ()
    assert any(a == orphan and "本次不记录" in why for a, why in outcome.kept), outcome
    assert names.TAG_RETIRED_AT not in _tags(aws, orphan)
    assert ddb.calls == [], "没有成熟候选、也没有补打，不读 runs 表"


def test_backfilled_orphan_is_reclaimed_an_hour_after_the_backfill_not_after_registration(aws):
    """静默期从补打的时刻起算，不从 `registeredAt` 起算（被拒方案「孤儿的静默期从 `registeredAt` 起算」）。"""
    templates = seed_backend(aws)
    orphan = _register_unmapped(aws, templates, digest="sha256:" + "9" * 64, variant="stray")
    ecs = HookedEcs(aws.ecs, registered_at=NOW - timedelta(days=1))
    _cleanup(aws, NOW, ecs=ecs)
    assert _tags(aws, orphan)[names.TAG_RETIRED_AT] == NOW.isoformat()
    outcome, _ = _cleanup(aws, NOW + timedelta(minutes=59), ecs=ecs)
    assert outcome.deleted == ()
    outcome, _ = _cleanup(aws, NOW + timedelta(minutes=61), ecs=ecs)
    assert outcome.deleted == (orphan,), outcome


def test_reread_removes_a_backfilled_tag_once_the_revision_has_entered_a_mapping(aws):
    """本趟补打之后另一条命令把它写进映射：注销之前的映射重读看到它在映射里，当场摘掉（ADR 0038「打 tag 与写映射的交错」段）。
    只补打过、没有成熟候选时照常重读，但不读 runs 表。"""
    templates = seed_backend(aws)
    orphan = _register_unmapped(aws, templates, digest="sha256:" + "9" * 64, variant="stray")
    ssm = HookedSsm(aws.ssm, before_enumeration=lambda n: _write_mapping_to(aws, orphan) if n == 2 else None)
    ddb = HookedDdb(aws.ddb)
    outcome, _ = _cleanup(aws, NOW, ssm=ssm, ddb=ddb, ecs=HookedEcs(aws.ecs, registered_at=NOW - timedelta(days=1)))
    assert ssm.enumerations == 2 and outcome.deleted == ()
    assert names.TAG_RETIRED_AT not in _tags(aws, orphan)
    assert ddb.calls == [], "没有成熟候选，不读 runs 表"


def test_reread_keeps_a_mature_candidate_that_has_entered_a_mapping_and_removes_its_tag(aws):
    """成熟候选在快照之后、注销之前已被写进映射：不注销、摘掉 tag（ADR 0038「注册与回收的竞争」段其二）。"""
    templates = seed_backend(aws)
    arn = _unmapped_retired(aws, templates, retired_at=NOW - timedelta(hours=3))
    ssm = HookedSsm(aws.ssm, before_enumeration=lambda n: _write_mapping_to(aws, arn) if n == 2 else None)
    outcome, _ = _cleanup(aws, NOW, ssm=ssm)
    assert outcome.deleted == () and arn in _revisions(aws, "novaact")
    assert any(a == arn and "重新被映射引用" in why for a, why in outcome.kept), outcome
    assert names.TAG_RETIRED_AT not in _tags(aws, arn)


def test_reread_removes_the_tag_of_a_remapped_mature_candidate_even_when_the_index_is_not_ready(aws):
    """就绪检查没有通过时，重读照常进行：已被写进映射的成熟候选同样摘掉 tag（任何一趟见到「仍在映射里却带着这个 tag」都摘）。"""
    templates = seed_backend(aws)
    arn = _unmapped_retired(aws, templates, retired_at=NOW - timedelta(hours=3))
    ssm = HookedSsm(aws.ssm, before_enumeration=lambda n: _write_mapping_to(aws, arn) if n == 2 else None)
    outcome, _ = _cleanup(aws, NOW, ssm=ssm, ddb=HookedDdb(aws.ddb, index_status="CREATING"))
    assert ssm.enumerations == 2 and outcome.deleted == ()
    assert names.TAG_RETIRED_AT not in _tags(aws, arn)


def test_reread_failure_removes_this_passes_backfills_and_keeps_every_candidate(aws):
    """重读失败：本趟补打的 tag 全部摘掉（下一趟重打），成熟候选全部留下，打一行警告。"""
    templates = seed_backend(aws)
    mature = _unmapped_retired(aws, templates, retired_at=NOW - timedelta(hours=3))
    orphan = _register_unmapped(aws, templates, digest="sha256:" + "9" * 64, variant="stray")

    def fail_second(n):
        if n == 2:
            raise RuntimeError("Throttling")

    ssm = HookedSsm(aws.ssm, before_enumeration=fail_second)
    outcome, text = _cleanup(aws, NOW, ssm=ssm, ecs=HookedEcs(aws.ecs, registered_at=NOW - timedelta(days=1)))
    assert outcome.deleted == () and mature in _revisions(aws, "novaact")
    assert names.TAG_RETIRED_AT not in _tags(aws, orphan)
    assert "重新读取 worker 镜像映射失败" in text and "下次 push-worker 或 gherkai deploy 会再试" in text


def _change_on_final_check(aws, arn: str, change: str):
    """最后核对那次 describe（同一 ARN 的第二次：第一次在列 family 时）之前改动它。"""
    def on_describe(kw, n):
        if kw["taskDefinition"] != arn or n != 2:
            return
        if change == "rewritten":
            _retire_now(aws, arn, NOW)
        elif change == "removed":
            aws.ecs.untag_resource(resourceArn=arn, tagKeys=[names.TAG_RETIRED_AT])
        elif change == "inactive":
            aws.ecs.deregister_task_definition(taskDefinition=arn)
        else:
            raise RuntimeError("Throttling")
    return on_describe


@pytest.mark.parametrize("change", ["rewritten", "removed", "inactive", "read_fails"])
def test_final_check_skips_a_candidate_that_changed_and_continues_with_the_others(aws, change):
    """注销之前逐个再读：`gherkai:retired-at` 与判定成熟时逐字相同、且仍为 ACTIVE 才注销；被改写、被摘掉、已不是 ACTIVE
    或读取失败的本趟跳过并打一行警告，其余候选照常核对（ADR 0038「引用检查」段⑤）。"""
    templates = seed_backend(aws)
    changed = _unmapped_retired(aws, templates, retired_at=NOW - timedelta(hours=3), variant="login")
    other = _unmapped_retired(aws, templates, retired_at=NOW - timedelta(hours=3), variant="base", digest="sha256:" + "c" * 64)
    ecs = HookedEcs(aws.ecs, on_describe=_change_on_final_check(aws, changed, change))
    outcome, text = _cleanup(aws, NOW, ecs=ecs)
    assert changed not in outcome.deleted and changed not in ecs.deregistered
    assert outcome.deleted == (other,), outcome
    assert workers._short_arn(changed) in text and "这次不回收它" in text


def _after_mapping_reread(ecs: HookedEcs, ddb: HookedDdb, arn: str, act, seen: list):
    """`after_enumeration` 钩子：这一趟的映射重读（第二轮映射枚举）取回最后一页之后、最后核对之前执行 `act()`。

    位置以映射重读为锚、不以最后核对的那次 describe 为锚：去掉最后核对的实现里同一位置照样存在，用例才会在
    「不注销」的断言上失败，而不是因为停不到预定位置。那一刻对 `arn` 已发出的 describe 次数（1 即只有列 family 那一次，
    最后核对还没发生）与快照的 `Query` 记进 `seen`，由用例断言（钩子里抛出的断言会被当成重读失败吞掉）。"""
    def after_enumeration(n):
        if n == 2:
            seen.append((ecs.describes.get(arn, 0), list(ddb.queried)))
            act()
    return after_enumeration


SNAPSHOT_DONE = [(names.RUNS_STATUS_GROUP_GSI, names.STATUS_GROUP_LIVE)]   # 这一趟的引用快照已完成


def _final_check_pass(aws, arn: str, change: str, *, at: datetime, value: datetime | None = None):
    """一趟在快照与映射重读之后、最后核对之前被改动了候选 tag 的清理 → (outcome, text, ecs)：`rewritten` 改写为
    `value`，`removed` 摘掉。断言改动确实落在这个位置。"""
    def act():
        if change == "rewritten":
            _retire_now(aws, arn, value)
        else:
            aws.ecs.untag_resource(resourceArn=arn, tagKeys=[names.TAG_RETIRED_AT])

    ecs, ddb, seen = HookedEcs(aws.ecs), HookedDdb(aws.ddb), []
    ssm = HookedSsm(aws.ssm, after_enumeration=_after_mapping_reread(ecs, ddb, arn, act, seen))
    outcome, text = _cleanup(aws, at, ssm=ssm, ecs=ecs, ddb=ddb)
    assert seen == [(1, SNAPSHOT_DONE)], seen
    return outcome, text, ecs


def test_candidate_whose_retired_at_is_rewritten_before_the_final_check_is_judged_again_by_the_new_value(aws):
    """成熟候选的 `gherkai:retired-at` 在快照与映射重读之后、最后核对之前被改写为新值：这一趟不注销；之后各趟按新值重新
    判定，新值未满静默期即留下，满了才回收（ADR 0038「引用检查」段⑤与实测项 10「注销之前的最后核对」）。串起的步骤：

    1. 一个不在任何映射里、tag 早已满静默期的 revision R，被一趟清理收为成熟候选；这一趟做完就绪检查、快照与映射重读之后，
       最后核对之前 R 的 tag 被改写为这一趟的时刻。
    2. 这一趟：最后核对读到的值与判定成熟时不同，不发注销请求，R 仍为 ACTIVE、带着新值。
    3. 新值之后未满静默期的一趟：按新值判为未满，留下，不发注销请求。
    4. 新值满静默期之后的一趟：回收 R。

    守的是：最后核对比较的是 tag 的值，不只是 tag 在不在；被跳过的候选之后按届时的值重新判定，不沿用这一趟的旧值。"""
    templates = seed_backend(aws)
    arn = _unmapped_retired(aws, templates, retired_at=NOW - timedelta(hours=3))
    outcome, text, ecs = _final_check_pass(aws, arn, "rewritten", at=NOW, value=NOW)
    assert arn not in ecs.deregistered and arn not in outcome.deleted
    assert any(a == arn and "退休时刻已改变" in why for a, why in outcome.kept), outcome
    assert workers._short_arn(arn) in text and "这次不回收它" in text
    assert arn in _revisions(aws, "novaact") and _tags(aws, arn)[names.TAG_RETIRED_AT] == NOW.isoformat()

    ecs = HookedEcs(aws.ecs)
    outcome, _ = _cleanup(aws, NOW + workers.RETIRE_QUIET_PERIOD - timedelta(minutes=1), ecs=ecs)
    assert outcome.deleted == () and ecs.deregistered == []
    assert any(a == arn and "静默期" in why for a, why in outcome.kept), outcome
    assert arn in _revisions(aws, "novaact")

    outcome, _ = _cleanup(aws, NOW + workers.RETIRE_QUIET_PERIOD + timedelta(minutes=1))
    assert outcome.deleted == (arn,), outcome
    assert arn not in _revisions(aws, "novaact")


def test_candidate_whose_retired_at_is_removed_before_the_final_check_is_backfilled_and_reclaimed_later(aws):
    """成熟候选的 `gherkai:retired-at` 在快照与映射重读之后、最后核对之前被摘掉：这一趟不注销；下一趟按「不在映射、无 tag」
    处理，补打、留下，再满静默期才回收（ADR 0038「引用检查」段⑤与「候选与静默期起点」段）。串起的步骤：

    1. 一个不在任何映射里、tag 早已满静默期的 revision R，被一趟清理收为成熟候选；这一趟做完就绪检查、快照与映射重读之后，
       最后核对之前 R 的 tag 被摘掉。
    2. 这一趟：最后核对读到 tag 已不在，不发注销请求，R 仍为 ACTIVE、不带 tag。
    3. 下一趟：R 不在任何映射里、没有 tag、注册时刻早于本趟读映射的时刻，补打（值为本趟的时刻）、本趟留下。
    4. 补打之后未满静默期的一趟：留下，不发注销请求。
    5. 补打满静默期之后的一趟：回收 R。

    守的是：被摘掉 tag 的候选只会从更晚的补打时刻重新起算，回收推迟、不提前。真实 ECS 返回的 `registeredAt` 是真实时刻、
    晚于注入的时钟，补打那一趟起的描述按注入的时钟覆盖这个字段（moto 不返回它）。"""
    templates = seed_backend(aws)
    arn = _unmapped_retired(aws, templates, retired_at=NOW - timedelta(hours=3))
    outcome, text, ecs = _final_check_pass(aws, arn, "removed", at=NOW)
    assert arn not in ecs.deregistered and arn not in outcome.deleted
    assert any(a == arn and "退休时刻已被去掉" in why for a, why in outcome.kept), outcome
    assert workers._short_arn(arn) in text and "这次不回收它" in text
    assert arn in _revisions(aws, "novaact") and names.TAG_RETIRED_AT not in _tags(aws, arn)

    cleaner = HookedEcs(aws.ecs, registered_at=NOW - timedelta(days=1))
    backfilled_at = NOW + timedelta(minutes=10)
    outcome, _ = _cleanup(aws, backfilled_at, ecs=cleaner)
    assert outcome.deleted == () and cleaner.tagged == [arn], cleaner.tagged
    assert _tags(aws, arn)[names.TAG_RETIRED_AT] == backfilled_at.isoformat()
    assert any(a == arn and "本次记录退休时刻" in why for a, why in outcome.kept), outcome

    outcome, _ = _cleanup(aws, backfilled_at + workers.RETIRE_QUIET_PERIOD - timedelta(minutes=1), ecs=cleaner)
    assert outcome.deleted == () and cleaner.deregistered == []
    assert any(a == arn and "静默期" in why for a, why in outcome.kept), outcome

    outcome, _ = _cleanup(aws, backfilled_at + workers.RETIRE_QUIET_PERIOD + timedelta(minutes=1), ecs=cleaner)
    assert outcome.deleted == (arn,), outcome
    assert arn not in _revisions(aws, "novaact")


class _PartyStopped(BaseException):
    """停在预定位置的一方被中止，或停留超时：从 `hold()` 抛出，让那一方从停点直接退出、不再执行其余步骤。

    继承 `BaseException` 而不是 `Exception`：被测代码对 AWS 调用失败有宽泛的 `except Exception`，继承 `Exception` 的
    异常会被它接住，那一方随后照常执行其余步骤、继续发出调用。被测的 `gherkai_deploy_aws.workers` 里没有接住
    `BaseException` 的处理，也没有 `finally` 块。"""


_PARTY_THREADS: list[threading.Thread] = []   # 启动过的参与方线程，供 `lingering_party_threads()` 查询


def lingering_party_threads() -> list[threading.Thread]:
    """仍然存活的参与方线程。正常收尾时为空；对真实账户执行这些用例的装置（`tools/workers_real_aws/`）在每条用例对账户
    的清理之前查询它，不为空即说明有一方中止之后仍可能发出调用：装置记下这一点，跳过这条用例的清理（那一方可能在清理
    期间恢复执行、重新写入资源），并终止整个会话，不再执行后续用例，资源留给进程退出之后的清扫。"""
    _PARTY_THREADS[:] = [t for t in _PARTY_THREADS if t.is_alive()]
    return list(_PARTY_THREADS)


class _Party:
    """在独立线程里执行交错中的一方（一条推送或一趟清理），并把它停在钩子回调里的预定位置：钩子在那一方的线程里调用
    `hold()`，主线程 `release_until_done()` 放行并等它结束、取回返回值（它抛出的异常在主线程原样抛出）。一方可以依次停在
    几个位置：`release_until_held()` 放行它，并等它停在下一个位置；`release_until_done()` 之后它不再停留，余下的 `hold()`
    直接返回（中止之后除外，见下）。

    次序为何确定（适用于没有超时、没有中止的执行）：主线程启动或放行一方之后，等到它停在预定位置（`start_until_held()` /
    `release_until_held()`）或结束（`release_until_done()`）才往下走，停住的一方在被放行之前不发出任何调用。于是任一时刻
    至多一方在执行，各方 AWS 调用的先后完全由主线程启动与放行的先后决定，与线程调度无关。没有停在预定位置就结束的，
    主线程立即报错，不等超时。

    超时与中止：停留超过 `timeout` 仍未被放行的一方，从停点抛出 `_PartyStopped` 退出；用例结束时（含断言失败）
    `_parties` 中止各方，停着的一方同样从停点抛出 `_PartyStopped` 退出，不再发出后续调用。中止那一刻仍在执行、没有停着的
    一方（只在主线程等它超时之后才会出现）在下一个停点退出，没有下一个停点的执行到结束。`_parties` 等待之后仍有存活的
    线程，用例以错误失败，错误信息写明是哪一方，`lingering_party_threads()` 也能查到它。

    超时取得宽，是因为真实账户上第一次 DynamoDB 调用要等建表，这期间其余各方一直停着；测试本辅助的用例传入小的
    `timeout`。"""

    TIMEOUT = 1800.0   # 秒

    def __init__(self, name: str, target, *, timeout: float = TIMEOUT):
        self.name, self._target, self.timeout = name, target, timeout
        self.result = None
        self.error: BaseException | None = None
        self._cond = threading.Condition()
        self._holds = 0          # 已停留的次数
        self._releases = 0       # 已放行的次数
        self._free = False       # `release_until_done()` 之后不再停留
        self._finished = False
        self._aborted = False
        self._thread = threading.Thread(target=self._run, name=name, daemon=True)

    def _run(self):
        try:
            self.result = self._target()
        except BaseException as exc:  # noqa: BLE001  交给主线程原样抛出
            self.error = exc
        finally:
            with self._cond:
                self._finished = True
                self._cond.notify_all()

    def hold(self) -> None:
        with self._cond:
            if self._aborted:
                raise _PartyStopped(f"{self.name}：用例已中止")
            if self._free:
                return
            self._holds += 1
            n = self._holds
            self._cond.notify_all()
            if not self._cond.wait_for(lambda: self._releases >= n or self._free or self._aborted, self.timeout):
                raise _PartyStopped(f"{self.name}：停留超时，没有被放行")
            if self._aborted:
                raise _PartyStopped(f"{self.name}：用例已中止")

    def _until_held(self, n: int) -> None:
        with self._cond:
            settled = self._cond.wait_for(lambda: self._holds >= n or self._finished, self.timeout)
            held = self._holds >= n
        assert settled, f"{self.name} 超时仍未停在预定位置"
        if not held:
            raise AssertionError(f"{self.name} 没有停在预定位置就结束了：error={self.error!r} result={self.result!r}")

    def start_until_held(self) -> None:
        _PARTY_THREADS.append(self._thread)
        self._thread.start()
        self._until_held(1)

    def release_until_held(self) -> None:
        with self._cond:
            self._releases += 1
            n = self._releases + 1
            self._cond.notify_all()
        self._until_held(n)

    def release_until_done(self):
        with self._cond:
            self._releases += 1
            self._free = True
            self._cond.notify_all()
        self._thread.join(self.timeout)
        assert not self._thread.is_alive(), f"{self.name} 放行之后没有结束"
        if self.error is not None:
            raise self.error
        return self.result

    def signal_abort(self) -> None:
        with self._cond:
            self._aborted = True
            self._cond.notify_all()


@contextlib.contextmanager
def _parties(*parties: _Party):
    """用例结束时（含断言失败）中止各方：先通知全部参与方，再在共同的期限内统一等待，之后仍有存活的线程即让用例失败。"""
    try:
        yield parties
    finally:
        for party in parties:
            party.signal_abort()
        deadline = time.monotonic() + max(party.timeout for party in parties)
        for party in parties:
            if party._thread.is_alive():   # 尚未启动的一方不必等待
                party._thread.join(max(0.0, deadline - time.monotonic()))
        alive = [party.name for party in parties if party._thread.is_alive()]
        if alive:
            raise AssertionError(f"中止之后仍未结束的参与方：{'、'.join(alive)}；它们之后仍可能发出调用")


def _party_under_broad_except(calls: list, *, timeout: float) -> _Party:
    """一方：停点处的调用被生产代码那样的 `try/except Exception` 包着，停点之后与 `except` 之后各记一次后续调用。"""
    def target():
        try:
            calls.append("停点之前")
            party.hold()
            calls.append("停点之后")
        except Exception:
            calls.append("接住异常之后")
        calls.append("其余步骤")
    party = _Party("一方", target, timeout=timeout)
    return party


def test_aborted_party_held_under_a_broad_except_issues_no_further_call_and_has_ended():
    calls: list[str] = []
    party = _party_under_broad_except(calls, timeout=5.0)
    with pytest.raises(AssertionError, match="用例中的断言失败"):
        with _parties(party):
            party.start_until_held()
            raise AssertionError("用例中的断言失败")
    assert calls == ["停点之前"], calls
    assert not party._thread.is_alive()
    assert isinstance(party.error, _PartyStopped) and "用例已中止" in str(party.error)
    assert party._thread not in lingering_party_threads()


def test_hold_timeout_does_not_let_a_party_under_a_broad_except_go_on():
    calls: list[str] = []
    party = _party_under_broad_except(calls, timeout=0.2)
    with _parties(party):
        party.start_until_held()
        party._thread.join(5.0)
        assert not party._thread.is_alive(), "停留超时之后应已结束"
        assert calls == ["停点之前"], calls
        assert isinstance(party.error, _PartyStopped) and "停留超时" in str(party.error)


def test_party_still_running_when_aborted_exits_at_its_next_hold_even_after_release():
    """`release_until_done()` 之后 `hold()` 本应直接返回；中止之后仍在执行的一方到下一个停点就退出，不再执行其余步骤。"""
    calls: list[str] = []
    gate = threading.Event()

    def target():
        try:
            party.hold()
            gate.wait(5.0)          # 放行之后的一段慢步骤，主线程等它超时
            calls.append("下一个停点之前")
            party.hold()
            calls.append("下一个停点之后")
        except Exception:
            calls.append("接住异常之后")
        calls.append("其余步骤")
    party = _Party("一方", target, timeout=0.2)
    with _parties(party):
        party.start_until_held()
        with pytest.raises(AssertionError, match="放行之后没有结束"):
            party.release_until_done()
        party.signal_abort()
        gate.set()
        party._thread.join(5.0)
        assert not party._thread.is_alive()
        assert calls == ["下一个停点之前"], calls
        assert isinstance(party.error, _PartyStopped) and "用例已中止" in str(party.error)


def test_parties_fails_the_test_when_a_party_is_still_alive_after_the_wait():
    gate = threading.Event()
    stuck = _Party("不响应的一方", lambda: gate.wait(10.0), timeout=0.2)   # 不经停点，中止对它不起作用
    try:
        with pytest.raises(AssertionError, match="中止之后仍未结束的参与方：不响应的一方"):
            with _parties(stuck):
                stuck.start_until_held()
        assert stuck._thread in lingering_party_threads()
    finally:
        gate.set()
        stuck._thread.join(5.0)
    assert stuck._thread not in lingering_party_threads()


def test_final_check_keeps_a_revision_a_push_wrote_after_the_backfilling_pass_removed_its_tag(aws):
    """「摘掉自己补打的 tag 放行推送」的交错（ADR 0038「注册与回收的竞争」段其二、残余风险⑥(b)，实测项 10 同名一条）。
    三方各在一个线程里，按协议位置依次启动与放行（次序为何确定见 `_Party`）：

    1. 推送 Q 注册 R（步 6），停在写映射之前的再读之前（注册请求返回之后、对 R 的第一次 describe 之前）。
    2. 清理 P0 读映射（R 不在其中），补打 R（值 v0），停在映射重读之前（第二轮映射枚举之前）。
    3. 时钟越过 v0 之后的静默期，清理 P1 把 R 收为成熟候选，做完就绪检查、快照与映射重读（R 仍不在映射里），停在最后核对
       之前（映射重读取回最后一页之后，位置的取法见 `_after_mapping_reread`）。
    4. 放行 P0：映射重读失败，按协议摘掉本趟补打的 tag，R 不再带 tag。
    5. 放行 Q：再读看到 R 为 ACTIVE、不带 tag，不重新注册，把 R 写进映射。
    6. 放行 P1：最后核对读到 tag 已不在，不发注销请求。

    守的是：P1 凭 v0 收下的候选已被写进映射，注销之前的最后核对拦下它，R 仍在映射里、仍为 ACTIVE。真实 ECS 返回的
    `registeredAt` 是真实时刻、晚于注入的时钟，P0 的描述按注入的时钟覆盖这个字段（moto 不返回它）。"""
    seed_backend(aws)
    backfilled_at = NOW + timedelta(minutes=1)
    matured_at = backfilled_at + workers.RETIRE_QUIET_PERIOD + timedelta(minutes=1)

    q_ecs = HookedEcs(aws.ecs, on_register=lambda arn, n: q.hold() if n == 1 else None)
    q = _Party("推送 Q", lambda: _push(workers.Aws(ssm=aws.ssm, ecs=q_ecs, ecr=aws.ecr, ddb=aws.ddb), FakeContainer()))

    def p0_reread(n):
        if n == 2:
            p0.hold()
            raise RuntimeError("Throttling")

    p0_ssm, p0_ecs = HookedSsm(aws.ssm, before_enumeration=p0_reread), HookedEcs(aws.ecs, registered_at=NOW)
    p0 = _Party("清理 P0", lambda: _cleanup(aws, backfilled_at, ssm=p0_ssm, ecs=p0_ecs))

    p1_ecs, p1_ddb, p1_seen = HookedEcs(aws.ecs), HookedDdb(aws.ddb), []
    p1_ssm = HookedSsm(aws.ssm, after_enumeration=lambda n: _after_mapping_reread(
        p1_ecs, p1_ddb, q_ecs.registered[0], p1.hold, p1_seen)(n))
    p1 = _Party("清理 P1", lambda: _cleanup(aws, matured_at, ssm=p1_ssm, ecs=p1_ecs, ddb=p1_ddb))

    with _parties(q, p0, p1):
        q.start_until_held()
        [r] = q_ecs.registered
        assert q_ecs.describes.get(r, 0) == 0, "推送应停在对 R 的再读之前"

        p0.start_until_held()
        assert p0_ssm.enumerations == 2 and p0_ecs.tagged == [r]
        assert _tags(aws, r)[names.TAG_RETIRED_AT] == backfilled_at.isoformat()

        p1.start_until_held()
        assert p1_seen == [(1, SNAPSHOT_DONE)], "P1 应已完成快照与映射重读、尚未做最后核对"
        assert p1_ecs.deregistered == []
        with pytest.raises(aws.ssm.exceptions.ParameterNotFound):
            _mapping(aws, "novaact", "login")

        p0_outcome, p0_text = p0.release_until_done()
        assert p0_outcome.deleted == () and p0_ecs.untagged == [r]
        assert "重新读取 worker 镜像映射失败" in p0_text
        assert names.TAG_RETIRED_AT not in _tags(aws, r)

        rc, q_text = q.release_until_done()
        assert rc == 0, q_text
        assert q_ecs.registered == [r], "再读看到 ACTIVE、不带 tag，不应重新注册"
        assert _mapping(aws, "novaact", "login")["revision_arn"] == r

        p1_outcome, p1_text = p1.release_until_done()
    assert r not in p1_ecs.deregistered and p1_outcome.deleted == ()
    assert any(a == r and "退休时刻已被去掉" in why for a, why in p1_outcome.kept), p1_outcome
    assert workers._short_arn(r) in p1_text and "这次不回收它" in p1_text
    assert _mapping(aws, "novaact", "login")["revision_arn"] == r and r in _revisions(aws, "novaact")


def test_final_check_keeps_a_shared_revision_whose_last_mapping_is_replaced_while_the_pass_holds_the_old_value(aws):
    """早先版本留下的共用 revision、最后一条映射被替换的交错（ADR 0038「引用检查」段⑤其一、残余风险①(d)，实测项 10
    同名一条）。替换的一方与清理各在一个线程里，按协议位置依次启动与放行（次序为何确定见 `_Party`）：

    1. 摆出共用：旧版本推送注册 R，当前版本同名 variant 的映射也指向 R。当前版本换 digest 重推，替换的一步给 R 打上
       t0（远早于静默期）；这条推送在末尾的清理之前失败返回（写默认指针失败），之后也没有一趟清理摘掉这个 tag。此时只剩
       旧版本那条映射引用 R。
    2. 旧版本换 digest 重推 Q：注册 R3，把旧版本的映射替换为 R3（写映射成功），停在给 R 打 tag 之前（这次 `put_parameter`
       返回之后）。
    3. 清理 P 读映射（R 已不在其中），按 t0 把 R 收为成熟候选，做完就绪检查、快照与映射重读，停在最后核对之前（映射重读
       取回最后一页之后，位置的取法见 `_after_mapping_reread`）。
    4. 放行 Q：替换的一步给 R 写入新时刻，Q 正常结束。
    5. 放行 P：最后核对读到的值已不是 t0，不发注销请求。

    守的是：清理凭旧值收下的候选，替换的一步在最后核对之前写入新时刻时不被注销，R 之后从新时刻起算静默期。"""
    seed_backend(aws)
    shared = _share_with_old_version(aws, "sha256:" + "4" * 64)
    t0 = NOW - timedelta(hours=3)
    rc, text = _push(workers.Aws(ssm=_failing_default_pointer_put(aws), ecs=aws.ecs, ecr=aws.ecr, ddb=aws.ddb),
                     FakeContainer(digests=["sha256:" + "9" * 64]), set_default=True, now=t0)
    assert rc == 2, text
    assert _mapping(aws, "novaact", "login")["revision_arn"] != shared
    assert _mapping(aws, "novaact", "login", version=OLD_VERSION)["revision_arn"] == shared
    assert _tags(aws, shared)[names.TAG_RETIRED_AT] == t0.isoformat()

    replaced_at = NOW + timedelta(minutes=1)
    old_mapping = names.ssm_path(PREFIX, names.worker_image_key("novaact", names.image_tag(OLD_VERSION, "login")))
    q_ssm = HookedSsm(aws.ssm, after_put=lambda kw: q.hold() if kw["Name"] == old_mapping else None)
    q_ecs = HookedEcs(aws.ecs)
    q = _Party("替换 Q", lambda: _push(workers.Aws(ssm=q_ssm, ecs=q_ecs, ecr=aws.ecr, ddb=aws.ddb),
                                     FakeContainer(digests=["sha256:" + "8" * 64]), version=OLD_VERSION,
                                     now=replaced_at))

    p_ecs, p_ddb, p_seen = HookedEcs(aws.ecs), HookedDdb(aws.ddb), []
    p_ssm = HookedSsm(aws.ssm, after_enumeration=_after_mapping_reread(p_ecs, p_ddb, shared, lambda: p.hold(), p_seen))
    p = _Party("清理 P", lambda: _cleanup(aws, NOW, ssm=p_ssm, ecs=p_ecs, ddb=p_ddb))

    with _parties(q, p):
        q.start_until_held()
        [r3] = q_ecs.registered
        assert _mapping(aws, "novaact", "login", version=OLD_VERSION)["revision_arn"] == r3
        assert q_ecs.tagged == [], "Q 应停在给 R 打 tag 之前"

        p.start_until_held()
        assert p_seen == [(1, SNAPSHOT_DONE)], "P 应已完成快照与映射重读、尚未做最后核对"
        assert p_ecs.deregistered == []
        assert _tags(aws, shared)[names.TAG_RETIRED_AT] == t0.isoformat()

        rc, q_text = q.release_until_done()
        assert rc == 0, q_text
        assert q_ecs.tagged == [shared]
        assert _tags(aws, shared)[names.TAG_RETIRED_AT] == replaced_at.isoformat()

        p_outcome, p_text = p.release_until_done()
    assert shared not in p_ecs.deregistered and p_outcome.deleted == ()
    assert any(a == shared and "退休时刻已改变" in why for a, why in p_outcome.kept), p_outcome
    assert workers._short_arn(shared) in p_text and "这次不回收它" in p_text
    assert shared in _revisions(aws, "novaact")
    assert _tags(aws, shared)[names.TAG_RETIRED_AT] == replaced_at.isoformat()


def _held_push(aws):
    """一条在三个位置停留的推送 Q（novaact/login，映射原本缺失）→ (Q, Q 的 ECS 钩子壳, Q 的 SSM 钩子壳)：
    ① 写映射之前的再读之后、写映射（这条映射的 `put_parameter`）之前；② 写映射返回之后、写映射一方的立即摘除之前；
    ③ 立即摘除之后、命令末尾的清理开始读映射之前。三处都以 Q 自己的调用为锚：①② 是这条映射的写请求前后，③ 是
    Q 第一次枚举映射（步 1 到步 8 只点读 SSM，不枚举）。"""
    path = names.ssm_path(PREFIX, names.worker_image_key("novaact", names.image_tag(VERSION, "login")))
    q_ecs = HookedEcs(aws.ecs)
    q_ssm = HookedSsm(aws.ssm, before_put=lambda kw: q.hold() if kw["Name"] == path else None,
                      after_put=lambda kw: q.hold() if kw["Name"] == path else None,
                      before_enumeration=lambda n: q.hold() if n == 1 else None)
    q = _Party("推送 Q", lambda: _push(workers.Aws(ssm=q_ssm, ecs=q_ecs, ecr=aws.ecr, ddb=aws.ddb), FakeContainer()))
    return q, q_ecs, q_ssm


def _start_held_push(aws, q, q_ecs) -> str:
    """启动 Q 到位置①，断言它确已注册 R、做完写映射之前的再读（对 R 的 describe 恰一次，那时 R 不带 tag）、尚未写映射。"""
    q.start_until_held()
    [r] = q_ecs.registered
    assert q_ecs.describes.get(r) == 1, "推送应停在对 R 的再读之后"
    assert names.TAG_RETIRED_AT not in _tags(aws, r)
    with pytest.raises(aws.ssm.exceptions.ParameterNotFound):
        _mapping(aws, "novaact", "login")
    return r


@pytest.mark.parametrize("order", ["pass_removes_first", "push_removes_first"])
def test_reread_removes_the_backfilled_tag_of_a_revision_a_held_push_writes_into_its_mapping(aws, order):
    """「打 tag 与写映射的交错」里 tw 落在 r1 与 r3 之间的那种次序，由真实的推送写映射（ADR 0038「打 tag 与写映射的交错」段、
    「候选与静默期起点」段的「重读」，实测项 10「交错」一条）。推送与清理各在一个线程里，按协议位置依次启动与放行（次序为何
    确定见 `_Party`，推送的三个停留位置见 `_held_push`）：

    1. 推送 Q 注册 R（步 6），做完写映射之前的再读（R 为 ACTIVE、不带 tag），停在写映射之前。
    2. 清理 P 读映射（R 不在其中），按注册时刻早于本趟读映射的时刻给 R 补打（值为本趟的时刻），停在补打返回之后、
       映射重读之前。
    3. 放行 Q 写映射（步 7），停在写映射返回之后、它自己的立即摘除之前：R 已在映射里，仍带着 P 补打的 tag。
    4. 两种次序：
       - `pass_removes_first`：先放行 P，P 的重读看到 R 已在映射里，当场摘掉；这时 Q 还没有摘，R 已不带 tag，摘除出自 P。
         再放行 Q 做完立即摘除（对已不带 tag 的 R 再摘一次）。
       - `push_removes_first`：先放行 Q 做完立即摘除、停在它末尾的清理之前，R 已不带 tag；再放行 P，P 的重读同样看到
         R 在映射里，对已不带 tag 的 R 再摘一次，照常成功。
    5. 放行 Q 做完末尾的清理。

    两种次序里 P 都不发注销请求，Q 末尾的清理也不发。守的是：补打之后、重读之前被写进映射的 revision，由补打的那一趟在重读
    之后当场摘掉，不依赖写映射一方的摘除；写映射一方的立即摘除在命令末尾的清理之前完成。最终 R 在映射里、为 ACTIVE、
    不带 tag。真实 ECS 返回的 `registeredAt` 是真实时刻、晚于注入的时钟，P 的描述按注入的时钟覆盖这个字段（moto 不返回它）。"""
    seed_backend(aws)
    backfilled_at = NOW + timedelta(minutes=1)
    q, q_ecs, q_ssm = _held_push(aws)
    p_ecs = HookedEcs(aws.ecs, registered_at=NOW, after_tag=lambda arn: p.hold() if arn in q_ecs.registered else None)
    p_ssm = HookedSsm(aws.ssm)
    p = _Party("清理 P", lambda: _cleanup(aws, backfilled_at, ssm=p_ssm, ecs=p_ecs))

    with _parties(q, p):
        r = _start_held_push(aws, q, q_ecs)

        p.start_until_held()
        assert p_ecs.tagged == [r] and p_ssm.enumerations == 1, "P 应停在补打之后、映射重读之前"
        assert _tags(aws, r)[names.TAG_RETIRED_AT] == backfilled_at.isoformat()

        q.release_until_held()
        assert _mapping(aws, "novaact", "login")["revision_arn"] == r
        assert q_ecs.untagged == [], "Q 应停在它自己的摘除之前"
        assert _tags(aws, r)[names.TAG_RETIRED_AT] == backfilled_at.isoformat()

        if order == "pass_removes_first":
            p_outcome, _ = p.release_until_done()
            assert p_ecs.untagged == [r] and p_ecs.untag_failed == [] and p_ssm.enumerations == 2
            assert q_ecs.untagged == [], "这时 Q 还没有摘，摘除出自 P 的重读"
            assert names.TAG_RETIRED_AT not in _tags(aws, r)
            q.release_until_held()
            assert q_ecs.untagged == [r] and q_ecs.untag_failed == [] and q_ssm.enumerations == 1
        else:
            q.release_until_held()
            assert q_ecs.untagged == [r] and q_ecs.untag_failed == [] and q_ssm.enumerations == 1
            assert names.TAG_RETIRED_AT not in _tags(aws, r), "Q 写映射之后、末尾的清理之前已摘掉"
            assert p_ecs.untagged == []
            p_outcome, _ = p.release_until_done()
            assert p_ecs.untagged == [r] and p_ecs.untag_failed == [] and p_ssm.enumerations == 2

        rc, q_text = q.release_until_done()
    assert rc == 0, q_text
    assert q_ecs.registered == [r]
    assert p_outcome.deleted == () and p_ecs.deregistered == [] and q_ecs.deregistered == [], p_outcome
    assert _mapping(aws, "novaact", "login")["revision_arn"] == r and r in _revisions(aws, "novaact")
    assert names.TAG_RETIRED_AT not in _tags(aws, r)


@pytest.mark.parametrize("matured_by", ["manual_tag", "earlier_backfill"])
def test_reread_keeps_a_mature_candidate_that_a_held_push_writes_into_its_mapping_after_the_snapshot(aws, matured_by):
    """注销之前的映射重读拦下成熟候选，由真实的推送写映射（ADR 0038「注册与回收的竞争」段其二的映射重读、「候选与静默期
    起点」段的「重读」，实测项 10「注销之前的重读」一条）。推送与清理各在一个线程里，按协议位置依次启动与放行（次序为何
    确定见 `_Party`，推送的三个停留位置见 `_held_push`）：

    1. 推送 Q 注册 R（步 6），做完写映射之前的再读（R 为 ACTIVE、不带 tag），停在写映射之前。
    2. R 在再读之后带上一个已满静默期的 `gherkai:retired-at`：`manual_tag` 手工打一个早于此刻 3 小时的值；
       `earlier_backfill` 由一趟完整的清理 P0 按注册时刻补打（值为 P0 的时刻），清理 P 的时刻取补打之后满静默期。
    3. 清理 P 读映射（R 不在其中），把 R 收为成熟候选，做完就绪检查与快照（快照里没有 R），停在快照最后一页返回之后、
       映射重读之前。
    4. 放行 Q 写映射（步 7），停在写映射返回之后、它自己的立即摘除之前：R 已在映射里，仍带着那个 tag。
    5. 放行 P：重读看到 R 已在映射里，不注销、摘掉 tag，也不对 R 做最后核对；这时 Q 还没有摘，摘除出自 P。
    6. 放行 Q 做完立即摘除与末尾的清理。

    守的是：快照之后、重读之前被写进映射的成熟候选，注销之前的映射重读把它留下并摘掉 tag，不依赖最后核对，也不依赖写映射
    一方的摘除。最终 R 在映射里、为 ACTIVE、不带 tag。`earlier_backfill` 里 P0 的描述按注入的时钟覆盖 `registeredAt`
    （真实 ECS 返回的是真实时刻、晚于注入的时钟；moto 不返回它）。"""
    seed_backend(aws)
    if matured_by == "manual_tag":
        retired_raw, matured_at = (NOW - timedelta(hours=3)).isoformat(), NOW
    else:
        retired_raw, matured_at = NOW.isoformat(), NOW + workers.RETIRE_QUIET_PERIOD + timedelta(minutes=1)
    q, q_ecs, q_ssm = _held_push(aws)
    p_ecs, p_ssm = HookedEcs(aws.ecs), HookedSsm(aws.ssm)
    p_ddb = HookedDdb(aws.ddb, after_query=lambda resp: p.hold() if not resp.get("LastEvaluatedKey") else None)
    p = _Party("清理 P", lambda: _cleanup(aws, matured_at, ssm=p_ssm, ecs=p_ecs, ddb=p_ddb))

    with _parties(q, p):
        r = _start_held_push(aws, q, q_ecs)

        if matured_by == "manual_tag":
            _retire_now(aws, r, NOW - timedelta(hours=3))
        else:
            p0_ecs = HookedEcs(aws.ecs, registered_at=NOW - timedelta(days=1))
            p0_outcome, _ = _cleanup(aws, NOW, ecs=p0_ecs)
            assert p0_ecs.tagged == [r] and p0_ecs.untagged == [] and p0_outcome.deleted == (), p0_outcome
        assert _tags(aws, r)[names.TAG_RETIRED_AT] == retired_raw

        p.start_until_held()
        assert p_ddb.queried == SNAPSHOT_DONE and p_ssm.enumerations == 1, "P 应停在快照之后、映射重读之前"
        assert p_ddb.calls == ["describe_table", "query"], "P 应先做就绪检查、再取快照"
        assert p_ecs.describes.get(r) == 1 and p_ecs.untagged == [] and p_ecs.deregistered == []

        q.release_until_held()
        assert _mapping(aws, "novaact", "login")["revision_arn"] == r
        assert q_ecs.untagged == [], "Q 应停在它自己的摘除之前"
        assert _tags(aws, r)[names.TAG_RETIRED_AT] == retired_raw

        p_outcome, _ = p.release_until_done()
        assert r not in p_ecs.deregistered and p_outcome.deleted == (), p_outcome
        assert p_ecs.untagged == [r] and p_ecs.untag_failed == []
        assert p_ssm.enumerations == 2
        assert p_ecs.describes.get(r) == 1, "已在映射里的候选不再做最后核对"
        assert any(a == r and "重新被映射引用" in why for a, why in p_outcome.kept), p_outcome
        assert q_ecs.untagged == [], "这时 Q 还没有摘，摘除出自 P 的重读"
        assert names.TAG_RETIRED_AT not in _tags(aws, r) and r in _revisions(aws, "novaact")

        q.release_until_held()
        assert q_ecs.untagged == [r] and q_ecs.untag_failed == []
        rc, q_text = q.release_until_done()
    assert rc == 0, q_text
    assert q_ecs.registered == [r] and q_ecs.deregistered == []
    assert _mapping(aws, "novaact", "login")["revision_arn"] == r and r in _revisions(aws, "novaact")
    assert names.TAG_RETIRED_AT not in _tags(aws, r)


@pytest.mark.parametrize("index_status", [INDEX_MISSING, "CREATING", "UPDATING", "DELETING", "describe_fails"])
def test_readiness_check_only_lets_an_active_index_through(aws, index_status):
    """就绪检查：状态分组索引的 `IndexStatus` 为 `ACTIVE` 才继续；缺失、`CREATING`、`UPDATING`、`DELETING` 或
    `DescribeTable` 本身失败，全部候选留下、打一行警告、不 `Query`（ADR 0038「引用检查」段②）。"""
    templates = seed_backend(aws)
    arn = _unmapped_retired(aws, templates, retired_at=NOW - timedelta(hours=3))
    ddb = (HookedDdb(aws.ddb, describe_error=RuntimeError("AccessDenied")) if index_status == "describe_fails"
           else HookedDdb(aws.ddb, index_status=index_status))
    outcome, text = _cleanup(aws, NOW, ddb=ddb)
    assert outcome.deleted == () and arn in _revisions(aws, "novaact")
    assert "query" not in ddb.calls
    assert "这次没有回收旧的 revision" in text


def test_readiness_check_with_an_active_index_proceeds_to_one_snapshot(aws):
    templates = seed_backend(aws)
    arn = _unmapped_retired(aws, templates, retired_at=NOW - timedelta(hours=3))
    ddb = HookedDdb(aws.ddb)
    outcome, _ = _cleanup(aws, NOW, ddb=ddb)
    assert outcome.deleted == (arn,)
    assert ddb.calls == ["describe_table", "query"]
    assert ddb.queried == [(names.RUNS_STATUS_GROUP_GSI, names.STATUS_GROUP_LIVE)]


def test_readiness_check_looks_at_the_status_group_index_only(aws):
    """就绪检查看的是状态分组索引：表上别的索引都为 `ACTIVE`、唯独它不在时，全部候选留下、不 `Query`，警告点名它。"""
    templates = seed_backend(aws)
    arn = _unmapped_retired(aws, templates, retired_at=NOW - timedelta(hours=3))
    ddb = HookedDdb(aws.ddb, gsis=[{"IndexName": "other-index", "IndexStatus": "ACTIVE"}])
    outcome, text = _cleanup(aws, NOW, ddb=ddb)
    assert outcome.deleted == () and arn in _revisions(aws, "novaact")
    assert "query" not in ddb.calls
    assert names.RUNS_STATUS_GROUP_GSI in text and "这次没有回收旧的 revision" in text


def test_snapshot_query_failure_keeps_every_candidate_but_still_rereads_for_backfills(aws):
    """快照的 `Query` 失败：全部候选留下并警告；本趟补打过 tag 的仍照常做映射重读。"""
    templates = seed_backend(aws)
    mature = _unmapped_retired(aws, templates, retired_at=NOW - timedelta(hours=3))
    orphan = _register_unmapped(aws, templates, digest="sha256:" + "9" * 64, variant="stray")
    ssm = HookedSsm(aws.ssm, before_enumeration=lambda n: _write_mapping_to(aws, orphan) if n == 2 else None)
    ddb = HookedDdb(aws.ddb, query_error=RuntimeError("ProvisionedThroughputExceeded"))
    outcome, text = _cleanup(aws, NOW, ssm=ssm, ddb=ddb, ecs=HookedEcs(aws.ecs, registered_at=NOW - timedelta(days=1)))
    assert outcome.deleted == () and mature in _revisions(aws, "novaact")
    assert "查询运行记录表失败" in text
    assert ssm.enumerations == 2 and names.TAG_RETIRED_AT not in _tags(aws, orphan)


def test_cleanup_does_not_read_the_runs_table_without_a_mature_candidate(aws):
    """没有成熟候选就不读 runs 表（多数 pass 如此）：只有未满静默期的候选时，一次 DynamoDB 调用都没有，也不重读映射。"""
    templates = seed_backend(aws)
    _unmapped_retired(aws, templates, retired_at=NOW)
    ddb = HookedDdb(aws.ddb)
    ssm = HookedSsm(aws.ssm)
    outcome, _ = _cleanup(aws, NOW + timedelta(minutes=30), ddb=ddb, ssm=ssm)
    assert outcome.deleted == () and ddb.calls == [] and ssm.enumerations == 1


def test_snapshot_read_volume_does_not_grow_with_the_number_of_candidates(aws):
    """每趟一次快照：成熟候选从 1 个到 3 个，`Query` 次数不变（被拒方案「对每个候选 revision 逐个 `Query`」）。"""
    templates = seed_backend(aws)
    _unmapped_retired(aws, templates, retired_at=NOW - timedelta(hours=3), variant="a", digest="sha256:" + "1" * 64)
    one = HookedDdb(aws.ddb)
    _cleanup(aws, NOW, ddb=one)
    for variant, d in (("b", "2"), ("c", "3"), ("d", "4")):
        _unmapped_retired(aws, templates, retired_at=NOW - timedelta(hours=3), variant=variant, digest="sha256:" + d * 64)
    three = HookedDdb(aws.ddb)
    outcome, _ = _cleanup(aws, NOW, ddb=three)
    assert len(outcome.deleted) == 3
    assert three.calls.count("query") == one.calls.count("query") == 1


def test_cleanup_skips_the_whole_pass_when_the_mappings_cannot_be_listed(aws):
    """读不全 `worker-image/*` 映射 → **整趟放弃**，不把所有 revision 判成孤儿。

    「读不全就当没有映射」会让每个在用 revision 都变成孤儿并被补打，一小时后的下一趟就会批量回收。
    """
    seed_backend(aws)
    _push(aws, FakeContainer())
    arn = _mapping(aws, "novaact", "login")["revision_arn"]

    class _BrokenSsm:
        def __getattr__(self, item):
            def boom(**kw):
                raise RuntimeError("AccessDenied: ssm:GetParametersByPath")
            return boom

    ecs = HookedEcs(aws.ecs, registered_at=NOW - timedelta(days=1))
    outcome, text = _cleanup(aws, NOW, ssm=_BrokenSsm(), ecs=ecs)
    assert outcome == workers.CleanupOutcome() and "跳过清理" in text
    assert arn in _revisions(aws, "novaact") and names.TAG_RETIRED_AT not in _tags(aws, arn)


def test_cleanup_never_touches_the_template_revision(aws):
    """模板 revision **没有血缘 tags** → 永不进清理候选（它是所有 variant 的母本，删了就没法再注册）。"""
    templates = seed_backend(aws)
    outcome, _ = _cleanup(aws, NOW + timedelta(days=30), ecs=HookedEcs(aws.ecs, registered_at=NOW - timedelta(days=60)))
    assert outcome.deleted == () and outcome.kept == ()
    for arn in templates.values():
        assert arn in _revisions(aws, arn.rsplit("/", 1)[-1].split("-")[1])
        assert names.TAG_RETIRED_AT not in _tags(aws, arn)


class _StubEcs:
    """最小 ECS 替身：一个已退休满静默期、不在映射里的 revision，专供删除没完成的几种形态。

    `delete_failures` / `delete_error` 造出删除没完成的两种形态：批量 API 的逐项失败（放在响应的 `failures` 里、
    不抛异常）与调用本身抛错；`deregister_error` 造出注销这一步就失败的形态。
    """

    def __init__(self, arn: str, family: str, tags: dict[str, str], *,
                 delete_failures: list[dict] | None = None, delete_error: Exception | None = None,
                 deregister_error: Exception | None = None):
        self.arn, self.family, self._tags = arn, family, dict(tags)
        self.delete_failures, self.delete_error = delete_failures or [], delete_error
        self.deregister_error = deregister_error
        self.deregistered: list[str] = []
        self.deleted: list[str] = []

    def list_task_definitions(self, **kw):
        return {"taskDefinitionArns": [self.arn] if kw.get("familyPrefix") == self.family else []}

    def describe_task_definition(self, **kw):
        return {"taskDefinition": {"family": self.family, "taskDefinitionArn": self.arn, "status": "ACTIVE",
                                   "registeredAt": NOW - timedelta(days=1)},
                "tags": [{"key": k, "value": v} for k, v in self._tags.items()]}

    def deregister_task_definition(self, **kw):
        if self.deregister_error is not None:
            raise self.deregister_error
        self.deregistered.append(kw["taskDefinition"])

    def delete_task_definitions(self, **kw):
        if self.delete_error is not None:
            raise self.delete_error
        if self.delete_failures:
            return {"taskDefinitions": [], "failures": self.delete_failures}
        self.deleted.extend(kw["taskDefinitions"])
        return {"taskDefinitions": [{"taskDefinitionArn": a} for a in kw["taskDefinitions"]], "failures": []}


def _mature_stub(**kw) -> tuple[str, _StubEcs]:
    family = names.task_def_name(PREFIX, "novaact")
    arn = f"arn:aws:ecs:{REGION}:{ACCOUNT}:task-definition/{family}:99"
    return arn, _StubEcs(arn, family, {names.TAG_VARIANT: "stray", names.TAG_DIGEST: "sha256:" + "8" * 64,
                                       names.TAG_RETIRED_AT: (NOW - timedelta(hours=5)).isoformat()}, **kw)


def test_cleanup_deletes_a_mature_candidate_on_the_stub(aws):
    seed_backend(aws)
    arn, stub = _mature_stub()
    outcome, _ = _cleanup(aws, NOW, ecs=stub, engines=("novaact",))
    assert outcome.deleted == (arn,) and stub.deregistered == [arn] and stub.deleted == [arn]


def test_cleanup_does_not_count_a_per_item_delete_failure_as_reclaimed(aws):
    """`DeleteTaskDefinitions` 是批量 API：逐项失败放在响应的 `failures` 里、不抛异常——不读它就会把没删掉的也算成回收。"""
    seed_backend(aws)
    arn, stub = _mature_stub(delete_failures=[{"arn": "arn:x", "reason": "INVALID", "detail": "busy"}])
    outcome, _ = _cleanup(aws, NOW, ecs=stub, engines=("novaact",))
    assert outcome.deleted == ()
    assert outcome.kept == ((arn, "已退休，已注销、删除未完成：INVALID（busy）"),), outcome


def test_cleanup_reports_a_delete_error_after_deregister_as_not_retryable(aws):
    """注销成功、删除抛错：revision 已是 INACTIVE，`scan_family` 只列 ACTIVE、以后再也扫不到——原因串不能写成会重试的样子。"""
    seed_backend(aws)
    arn, stub = _mature_stub(delete_error=RuntimeError("Throttling"))
    outcome, _ = _cleanup(aws, NOW, ecs=stub, engines=("novaact",))
    assert outcome.deleted == () and stub.deregistered == [arn]
    assert outcome.kept == ((arn, "已退休，已注销、删除未完成：Throttling"),), outcome
    assert "本次回收失败" not in outcome.kept[0][1]


def test_cleanup_reports_a_deregister_error_as_retryable(aws):
    """注销这一步就抛错：revision 仍是 ACTIVE，下次 pass 还会扫到它——原因串保留「本次回收失败」。"""
    seed_backend(aws)
    arn, stub = _mature_stub(deregister_error=RuntimeError("Throttling"))
    outcome, _ = _cleanup(aws, NOW, ecs=stub, engines=("novaact",))
    assert outcome.deleted == () and stub.deregistered == [] and stub.deleted == []
    assert outcome.kept == ((arn, "已退休，本次回收失败：Throttling"),), outcome


def test_push_worker_runs_a_cleanup_pass_at_the_end(aws):
    """步 8 末的机会式 pass（无定时任务）：一个早已退休的 revision 在下一次 push 时被回收。"""
    templates = seed_backend(aws)
    stale = _register_unmapped(aws, templates, digest="sha256:" + "7" * 64, variant="old")
    _retire_now(aws, stale, NOW - timedelta(hours=3))
    rc, text = _push(aws, FakeContainer())
    assert rc == 0
    assert stale not in _revisions(aws, "novaact"), "退休满静默期且无引用 → 该被这次 pass 回收"
    assert "清理：回收 1 个 revision" in text


# --------------------------------------------------------------------------- deploy 三步

def test_init_default_pointer_only_when_missing(aws):
    seed_backend(aws)
    out, text = _out()
    assert workers.init_default_pointer(prefix=PREFIX, aws=aws, out=out) == "base"
    aws.ssm.put_parameter(Name=names.ssm_path(PREFIX, names.WORKER_DEFAULT_KEY), Value="common",
                          Type="String", Overwrite=True)
    out2, text2 = _out()
    assert workers.init_default_pointer(prefix=PREFIX, aws=aws, out=out2) == "common"
    assert "已保留默认 worker 镜像 variant `common`" in text2(), "默认指针记的是团队意图，升级不重置（ADR 0038）"


def test_sync_base_pulls_ghcr_and_pushes_as_base(aws):
    seed_backend(aws)
    c = FakeContainer()
    out, text = _out()
    results = workers.sync_base(prefix=PREFIX, engines=names.ENGINES, version=VERSION, container=c,
                               aws=aws, clock=_at(NOW), out=out)
    assert [r.variant for r in results] == ["base", "base"]
    pulls = [(ref, platform) for kind, ref, platform in (c_ for c_ in c.calls if c_[0] == "pull")]
    assert pulls == [("ghcr.io/zhiyanliu/gherkai-worker-novaact:1.4.0", "linux/amd64"),
                     ("ghcr.io/zhiyanliu/gherkai-worker-midscene:1.4.0", "linux/amd64")]
    assert _mapping(aws, "novaact", "base")["revision_arn"]


def test_sync_base_skips_non_pure_release_but_deploy_continues(aws):
    """dev 版（`.dev`/`.post`/本地段）**GHCR 上不存在对应基础镜像** → 明确警告 + 跳过基础镜像同步，第 3/4 步照常执行。

    判据复用 `compose.is_pure_release`（决策 2b：非纯净版本一定带 `+`/`.dev`）。硬失败会逼 contributor 绕过命令。
    """
    dev = "1.4.0.post3.dev0+28c1684"
    seed_backend(aws, stamp=dev)
    c = FakeContainer()
    out, text = _out()
    rc = workers.run_deploy_steps(prefix=PREFIX, version=dev, container=c, aws=aws, clock=_at(NOW), out=out)
    assert rc == 0
    assert not any(k == "pull" for k, *_ in c.calls), "dev 版不该去拉 GHCR"
    assert "GHCR" in text() and "push-worker" in text()
    assert aws.ssm.get_parameter(Name=names.ssm_path(PREFIX, names.WORKER_DEFAULT_KEY)
                                 )["Parameter"]["Value"] == "base", "第 3 步照常执行"


def test_sync_base_pull_failure_points_at_the_half_published_state(aws):
    seed_backend(aws)
    c = FakeContainer()
    c.pull_fails = True
    out, text = _out()
    rc = workers.run_deploy_steps(prefix=PREFIX, version=VERSION, container=c, aws=aws, clock=_at(NOW), out=out)
    assert rc == 1, "cdk 已成功而后续步骤失败 → 退出码 1"
    # 断言用户能据以行动的两句：状态（stack 已生效）+ 重新运行哪个命令。
    assert "拉不到基础镜像" in text() and "半发布态" in text()  # sync_base 自己那条（不是四步兜底行）
    assert "stack 已生效" in text() and "gherkai deploy" in text()


def test_rederive_registers_from_the_new_template_and_retires_the_old(aws):
    """deploy 改了模板（如 cpu）→ 用**新模板 + 已记录的 digest** 重注册；镜像一个字节不动、`pushed_at` 保留。"""
    seed_backend(aws)
    _push(aws, FakeContainer(digests=["sha256:" + "3" * 64]))
    before = _mapping(aws, "novaact", "login")
    new_templates = seed_backend(aws, cpu="2048")            # 模拟 cdk 换出新模板 revision
    assert new_templates["novaact"] != before["template_arn"]

    out, text = _out()
    results = workers.rederive_variants(prefix=PREFIX, engines=("novaact",), version=VERSION,
                                        aws=aws, clock=_at(NOW), out=out)
    after = _mapping(aws, "novaact", "login")
    assert [r.variant for r in results] == ["login"]
    assert after["template_arn"] == new_templates["novaact"]
    assert after["revision_arn"] != before["revision_arn"]
    assert after["digest"] == before["digest"] and after["pushed_at"] == before["pushed_at"]
    td = aws.ecs.describe_task_definition(taskDefinition=after["revision_arn"])["taskDefinition"]
    assert td["cpu"] == "2048", "重派生的意义就在于让既有 variant 跟上模板的新配置"
    assert td["containerDefinitions"][0]["image"].endswith(f"@{before['digest']}")
    assert _tags(aws, before["revision_arn"])[names.TAG_RETIRED_AT] == NOW.isoformat()
    assert "运行配置已按本次部署更新" in text()


def test_rederive_skips_when_template_arn_is_unchanged(aws):
    seed_backend(aws)
    _push(aws, FakeContainer())
    before = _revisions(aws, "novaact")
    out, text = _out()
    results = workers.rederive_variants(prefix=PREFIX, engines=names.ENGINES, version=VERSION,
                                        aws=aws, clock=_at(NOW), out=out)
    assert results == [] and _revisions(aws, "novaact") == before
    assert "运行配置已是最新，无需更新" in text()


def test_rederive_ignores_other_versions(aws):
    """variant 按版本隔离：**只重派生当前版本**的映射（旧版本留作历史，其回收归 `delete-worker`）。"""
    seed_backend(aws)
    _push(aws, FakeContainer(), version="1.3.0")             # 一个旧版本的映射
    new_templates = seed_backend(aws, cpu="2048")
    out, _ = _out()
    results = workers.rederive_variants(prefix=PREFIX, engines=names.ENGINES, version=VERSION,
                                        aws=aws, clock=_at(NOW), out=out)
    assert results == []
    assert _mapping(aws, "novaact", "login", version="1.3.0")["template_arn"] != new_templates["novaact"]


def test_rederive_enumerates_ssm_once_and_reads_the_template_once_per_engine(aws):
    """重派生是「枚举一次、逐引擎筛」+「repo URI 每引擎算一次」：SSM 全量枚举次数不随引擎数增长、
    模板 describe 次数不随 variant 数翻倍。

    **只断输出照不出这两条**——逐引擎重走枚举 / 逐 variant 重读模板，结果一模一样，只是多打 AWS 调用
    （枚举要翻页，每页 10 条）。
    """
    seed_backend(aws)
    _push(aws, FakeContainer(digests=["sha256:" + "1" * 64]))
    _push(aws, FakeContainer(digests=["sha256:" + "2" * 64]), variant="base")
    _push(aws, FakeContainer(digests=["sha256:" + "3" * 64]), engine="midscene")
    new_templates = seed_backend(aws, cpu="2048")             # cdk 换出新模板 → 三个 variant 全部待重派生

    ssm_spy, ecs_counter = Spy(aws.ssm), CountingEcs(aws.ecs)
    counted = workers.Aws(ssm=ssm_spy, ecs=ecs_counter, ecr=aws.ecr, ddb=aws.ddb)
    out, _ = _out()
    results = workers.rederive_variants(prefix=PREFIX, engines=names.ENGINES, version=VERSION,
                                        aws=counted, clock=_at(NOW), out=out)
    assert {(r.engine, r.variant) for r in results} == {("novaact", "base"), ("novaact", "login"),
                                                        ("midscene", "login")}
    assert ssm_spy.calls.count("get_parameters_by_path") == 1, \
        f"全量枚举应只执行一次（两个引擎共用），实际 {ssm_spy.calls.count('get_parameters_by_path')} 次"
    # 每引擎：取 repo URI 读模板一次 + 每个新 revision 从模板复制一次（不扫 family：重派生不复用已有的 revision）
    assert ecs_counter.described.count(new_templates["novaact"]) == 3, ecs_counter.described
    assert ecs_counter.described.count(new_templates["midscene"]) == 2, ecs_counter.described


def test_interrupted_rederive_registers_again_when_executed_again(aws):
    """重派生中断在注册与写映射之间，重新执行时再注册一个、不沿用上次注册的那个（ADR 0038 deploy 第 4 步，被拒方案「孤儿复用」）。"""
    seed_backend(aws)
    _push(aws, FakeContainer(digests=["sha256:" + "3" * 64]))
    before = _mapping(aws, "novaact", "login")
    seed_backend(aws, cpu="2048")
    broken = workers.Aws(ssm=_failing_mapping_put(aws), ecs=aws.ecs, ecr=aws.ecr, ddb=aws.ddb)
    with pytest.raises(RuntimeError, match="模拟中断"):
        workers.rederive_variants(prefix=PREFIX, engines=("novaact",), version=VERSION, aws=broken,
                                  clock=_at(NOW), out=lambda *a: None)
    left = set(_revisions(aws, "novaact")) - {before["revision_arn"]}
    assert _mapping(aws, "novaact", "login") == before

    out, text = _out()
    [result] = workers.rederive_variants(prefix=PREFIX, engines=("novaact",), version=VERSION,
                                         aws=aws, clock=_at(NOW), out=out)
    assert result.revision_arn not in left and _mapping(aws, "novaact", "login")["revision_arn"] == result.revision_arn
    assert "复用" not in text()


def test_revision_left_by_an_interrupted_rederive_is_backfilled_and_reclaimed_after_the_quiet_period(aws):
    """重派生中断在注册与写映射之间、重新执行之后，上次注册的那一批从未进入映射，由之后的清理补打、满静默期后回收
    （ADR 0038 deploy 第 4 步与「候选与静默期起点」段）。串起的步骤：

    1. deploy 改了模板，重派生为 login 注册 R1，写映射时中断：映射仍指向原 revision R0，R1 不带 `gherkai:retired-at`。
    2. 重新执行重派生：新注册 R2 写进映射，给 R0 打 tag；R1 不被沿用，重派生也不给它打 tag。
    3. 之后的一趟清理：R1 不在任何映射里、没有 tag、注册时刻早于本趟读映射的时刻，补打（值为本趟的时刻）、本趟留下。
    4. 补打之后未满静默期的一趟：R1 留下，不发注销请求；R0 按替换时打的值先到期、被回收。
    5. 补打满静默期之后的一趟：R1 被回收，R2 仍在映射里、仍为 ACTIVE。

    守的是：中断留下的那一批经清理的补打进入回收，静默期从补打的时刻起算。真实 ECS 返回的 `registeredAt` 是真实时刻、
    晚于注入的时钟，清理一侧的描述按注入的时钟覆盖这个字段（moto 不返回它）。"""
    seed_backend(aws)
    _push(aws, FakeContainer(digests=["sha256:" + "3" * 64]))
    before = _mapping(aws, "novaact", "login")
    seed_backend(aws, cpu="2048")
    interrupted = HookedEcs(aws.ecs)
    broken = workers.Aws(ssm=_failing_mapping_put(aws), ecs=interrupted, ecr=aws.ecr, ddb=aws.ddb)
    with pytest.raises(RuntimeError, match="模拟中断"):
        workers.rederive_variants(prefix=PREFIX, engines=("novaact",), version=VERSION, aws=broken,
                                  clock=_at(NOW), out=lambda *a: None)
    [left] = interrupted.registered
    assert _mapping(aws, "novaact", "login") == before
    assert names.TAG_RETIRED_AT not in _tags(aws, left)

    rederived_at = NOW + timedelta(minutes=5)
    again = HookedEcs(aws.ecs)
    out, text = _out()
    [result] = workers.rederive_variants(prefix=PREFIX, engines=("novaact",), version=VERSION,
                                         aws=workers.Aws(ssm=aws.ssm, ecs=again, ecr=aws.ecr, ddb=aws.ddb),
                                         clock=_at(rederived_at), out=out)
    assert again.registered == [result.revision_arn] and result.revision_arn != left
    assert _mapping(aws, "novaact", "login")["revision_arn"] == result.revision_arn
    assert again.tagged == [before["revision_arn"]], again.tagged
    assert _tags(aws, before["revision_arn"])[names.TAG_RETIRED_AT] == rederived_at.isoformat()
    assert names.TAG_RETIRED_AT not in _tags(aws, left) and left in _revisions(aws, "novaact")

    cleaner = HookedEcs(aws.ecs, registered_at=NOW)
    backfilled_at = NOW + timedelta(minutes=10)
    outcome, _ = _cleanup(aws, backfilled_at, ecs=cleaner)
    assert outcome.deleted == () and cleaner.tagged == [left], cleaner.tagged
    assert _tags(aws, left)[names.TAG_RETIRED_AT] == backfilled_at.isoformat()
    assert any(a == left and "本次记录退休时刻" in why for a, why in outcome.kept), outcome

    outcome, _ = _cleanup(aws, backfilled_at + workers.RETIRE_QUIET_PERIOD - timedelta(minutes=1), ecs=cleaner)
    assert left not in cleaner.deregistered and left in _revisions(aws, "novaact")
    assert any(a == left and "静默期" in why for a, why in outcome.kept), outcome
    assert outcome.deleted == (before["revision_arn"],), outcome

    outcome, _ = _cleanup(aws, backfilled_at + workers.RETIRE_QUIET_PERIOD + timedelta(minutes=1), ecs=cleaner)
    assert outcome.deleted == (left,), outcome
    assert left not in _revisions(aws, "novaact")
    assert _mapping(aws, "novaact", "login")["revision_arn"] == result.revision_arn
    assert result.revision_arn in _revisions(aws, "novaact")


def test_rederive_reregisters_when_the_mapped_revision_is_no_longer_active(aws):
    """模板没变、映射所指的 revision 已注销：按映射缺失处理，按映射里记录的 digest 新注册、替换映射，已不是 ACTIVE 的
    旧 revision 不打 `gherkai:retired-at`；`pushed_at` 保留（ADR 0038 deploy 第 4 步）。"""
    seed_backend(aws)
    _push(aws, FakeContainer(digests=["sha256:" + "3" * 64]))
    before = _mapping(aws, "novaact", "login")
    aws.ecs.deregister_task_definition(taskDefinition=before["revision_arn"])
    out, text = _out()
    [result] = workers.rederive_variants(prefix=PREFIX, engines=("novaact",), version=VERSION,
                                         aws=aws, clock=_at(NOW), out=out)
    after = _mapping(aws, "novaact", "login")
    assert after["revision_arn"] == result.revision_arn != before["revision_arn"]
    assert (after["digest"], after["pushed_at"], after["template_arn"]) == \
        (before["digest"], before["pushed_at"], before["template_arn"])
    assert names.TAG_RETIRED_AT not in _tags(aws, before["revision_arn"])
    assert "未能确认" in text()


def test_rederive_with_a_changed_template_does_not_tag_a_replaced_revision_that_is_no_longer_active(aws):
    """deploy 改了模板、映射所指的旧 revision 已注销：重派生替换映射之后不对它发打标请求，输出也不说它已标记待清理。"""
    seed_backend(aws)
    _push(aws, FakeContainer(digests=["sha256:" + "3" * 64]))
    before = _mapping(aws, "novaact", "login")
    aws.ecs.deregister_task_definition(taskDefinition=before["revision_arn"])
    new_templates = seed_backend(aws, cpu="2048")
    ecs = HookedEcs(aws.ecs)
    out, text = _out()
    [result] = workers.rederive_variants(prefix=PREFIX, engines=("novaact",), version=VERSION,
                                         aws=workers.Aws(ssm=aws.ssm, ecs=ecs, ecr=aws.ecr, ddb=aws.ddb),
                                         clock=_at(NOW), out=out)
    assert _mapping(aws, "novaact", "login")["template_arn"] == new_templates["novaact"]
    assert result.revision_arn != before["revision_arn"]
    assert before["revision_arn"] not in ecs.tagged, ecs.tagged
    assert "运行配置已按本次部署更新" in text() and "已标记待清理" not in text()


def test_rederive_skip_removes_a_stale_retired_at_and_does_not_read_the_template(aws):
    """模板没变、所指 revision 为 ACTIVE（deploy 重新运行的常态）→ 跳过，确认 ACTIVE 之后摘一次 `gherkai:retired-at`；
    模板一次都不读：判定只用映射里记的模板 ARN 与所指 revision 的状态。"""
    templates = seed_backend(aws)
    _push(aws, FakeContainer())
    arn = _mapping(aws, "novaact", "login")["revision_arn"]
    _retire_now(aws, arn, NOW)
    counter = CountingEcs(aws.ecs)
    out, _ = _out()
    assert workers.rederive_variants(prefix=PREFIX, engines=names.ENGINES, version=VERSION,
                                     aws=workers.Aws(ssm=aws.ssm, ecs=counter, ecr=aws.ecr, ddb=aws.ddb),
                                     clock=_at(NOW), out=out) == []
    assert counter.described == [arn], f"只该读映射所指的 revision：{counter.described}"
    assert templates["novaact"] not in counter.described
    assert names.TAG_RETIRED_AT not in _tags(aws, arn)


def test_run_deploy_steps_reports_a_missing_container_engine_as_exit_1(aws):
    """cdk 已成功、机器上没有容器引擎 → 退出码 1 + 「stack 已生效、重新运行幂等收敛」（不是退出码 2：账户已被改过）。"""
    seed_backend(aws)
    out, text = _out()
    rc = workers.run_deploy_steps(prefix=PREFIX, version=VERSION,
                                 container=FakeContainer(probe_error="找不到容器引擎 `docker`"),
                                 aws=aws, clock=_at(NOW), out=out)
    assert rc == 1
    assert "stack 已生效" in text() and "容器引擎" in text()


def test_deploy_steps_are_idempotent(aws):
    """四步重新运行收敛：第二趟不该多出任何 revision（同二元组查重 + 指针不动 + 无需重派生）。"""
    seed_backend(aws)
    c = FakeContainer(digests=["sha256:" + "4" * 64, "sha256:" + "5" * 64,
                               "sha256:" + "4" * 64, "sha256:" + "5" * 64])
    out, _ = _out()
    assert workers.run_deploy_steps(prefix=PREFIX, version=VERSION, container=c, aws=aws, clock=_at(NOW), out=out) == 0
    first = {e: _revisions(aws, e) for e in names.ENGINES}
    assert workers.run_deploy_steps(prefix=PREFIX, version=VERSION, container=c, aws=aws,
                                    clock=_at(NOW + timedelta(minutes=1)), out=out) == 0
    assert {e: _revisions(aws, e) for e in names.ENGINES} == first


# --------------------------------------------------------------------------- list-workers

def test_list_workers_output_shape(aws):
    seed_backend(aws)
    _push(aws, FakeContainer(digests=["sha256:" + "6" * 64]), set_default=True)
    _push(aws, FakeContainer(digests=["sha256:" + "7" * 64]), variant="base")
    out, text = _out()
    rc = workers.list_workers(prefix=PREFIX, cli_version=VERSION, aws=aws, out=out)
    body = text()
    assert rc == 0, body
    assert f"prefix {PREFIX}" in body and f"版本 {VERSION}" in body and "默认 variant login" in body
    family = names.task_def_name(PREFIX, "novaact")
    assert f"== novaact（family {family}" in body and "== midscene（" in body
    for expected in ("base", "login", "1.4.0-login", "sha256:666666666666", f"{family}:"):
        assert expected in body, expected
    assert "（本版本还没有任何 variant" in body, "midscene 没推过 → 明说，别留空白"


def test_list_workers_marks_retired_and_orphan_revisions(aws):
    templates = seed_backend(aws)
    _push(aws, FakeContainer(digests=["sha256:" + "a" * 64, "sha256:" + "b" * 64]))
    old = _mapping(aws, "novaact", "login")["revision_arn"]
    _push(aws, FakeContainer(digests=["sha256:" + "b" * 64]))          # 重推 → old 退休
    repo_uri = f"{REGISTRY}/{names.ecr_repo_name(PREFIX, 'novaact')}"
    orphan = workers._register_revision(aws.ecs, template_arn=templates["novaact"], engine="novaact",
                                        image_ref=f"{repo_uri}@sha256:{'c' * 64}", digest="sha256:" + "c" * 64,
                                        variant="stray", version=VERSION)
    out, text = _out()
    assert workers.list_workers(prefix=PREFIX, cli_version=VERSION, aws=aws, out=out) == 0
    body = text()
    assert f"待清理 {workers._short_arn(old)}" in body and "已退休" in body
    assert f"待清理 {workers._short_arn(orphan)}" in body and "孤儿" in body


def test_list_workers_is_blocked_by_skew(aws):
    seed_backend(aws, stamp="1.3.0")
    out, text = _out()
    assert workers.list_workers(prefix=PREFIX, cli_version=VERSION, aws=aws, out=out) == 2
    assert "版本不一致" in text()


def test_skew_gate_read_failure_exits_2_without_a_traceback(aws):
    """读戳失败（无凭证/无权限）→ 退出码 2 + 一句可读的说明。

    `compose.read_backend_version` 有意把这类异常抛给入口前端决定退出码，**本模块就是那个前端**——实际运行中遇到过：
    没有凭证时 `gherkai deploy list-workers` 直接吐 botocore 的 `NoCredentialsError` 堆栈。
    """
    class _BrokenSsm:
        def get_parameter(self, **kw):
            raise RuntimeError("Unable to locate credentials")

    broken = workers.Aws(ssm=_BrokenSsm(), ecs=aws.ecs, ecr=aws.ecr, ddb=aws.ddb)
    out, text = _out()
    assert workers.list_workers(prefix=PREFIX, cli_version=VERSION, aws=broken, out=out) == 2
    assert "读取后端版本戳失败" in text() and "凭证" in text()
    out2, text2 = _out()
    assert workers.push_worker("acme:img", engine="novaact", variant="v", cli_version=VERSION,
                               prefix=PREFIX, container=FakeContainer(), aws=broken, clock=_at(NOW), out=out2) == 2
    assert "读取后端版本戳失败" in text2()


def test_list_workers_reports_unreachable_aws_without_a_traceback():
    """建不出 client（这里用不存在的 profile 名）→ 退出码 2 + 一句可读的说明，不吐 botocore 堆栈。

    `boto3.session.Session(profile_name=...)` 对不存在的 profile 在**构造期**就抛 `ProfileNotFound`，配不出
    region 则要等到 `session.client(...)` 解析 endpoint 才抛——两者都发生在本模块自身的 `try` 之前，故建句柄
    本身必须被包住（不接 `aws=` 的真实调用路径才走到这里，所以这条不用 moto 夹具）。

    断言范围是**本层**：命令入口那一层还有更早的一口（解析 prefix/region/profile 时读 profile config 也会抛
    同类异常），归 `cli.Provider._resolve_target_or_report`，其用例在 provider 测试里。
    """
    out, text = _out()
    rc = workers.list_workers(prefix=PREFIX, cli_version=VERSION, profile="definitely-not-a-profile", out=out)
    assert rc == 2
    assert "连不上 AWS" in text()


def test_list_workers_says_when_the_default_pointer_is_missing(aws):
    seed_backend(aws)
    out, text = _out()
    assert workers.list_workers(prefix=PREFIX, cli_version=VERSION, aws=aws, out=out) == 0
    assert "未初始化" in text()


def test_list_workers_enumerates_ssm_once_for_all_engines(aws):
    """`list-workers` 的全量枚举（待清理对账用的映射集 + 各引擎当前版本的 variant）只执行一次、两个引擎共用。

    **只断输出照不出这条**——逐引擎重走一遍枚举，列出来的东西一模一样，只是多花几趟分页
    （`GetParametersByPath` 每页 10 条）。
    """
    seed_backend(aws)
    _push(aws, FakeContainer(digests=["sha256:" + "6" * 64]), set_default=True)
    _push(aws, FakeContainer(digests=["sha256:" + "7" * 64]), engine="midscene")
    spy = Spy(aws.ssm)
    out, text = _out()
    assert workers.list_workers(prefix=PREFIX, cli_version=VERSION,
                                aws=workers.Aws(ssm=spy, ecs=aws.ecs, ecr=aws.ecr, ddb=aws.ddb),
                                out=out) == 0
    n = spy.calls.count("get_parameters_by_path")
    assert n == 1, f"全量枚举应只执行一次（两个引擎共用），实际 {n} 次"
    body = text()
    assert body.count("1.4.0-login") == 2, f"枚举一次不等于少列东西：两个引擎的 variant 都该在\n{body}"


def test_list_workers_json_shape(aws):
    """list-workers --json（ADR 0041 决策三）：与文本同一份 doc——prefix/version/default_variant/engines{family, ecr_repo,
    variants[], pending_cleanup[]}；退休 revision 进 pending_cleanup 且 reason=retired。"""
    seed_backend(aws)
    _push(aws, FakeContainer(digests=["sha256:" + "6" * 64]), set_default=True)
    _push(aws, FakeContainer(digests=["sha256:" + "7" * 64]))  # 重推 login → 旧 revision 退休
    out, text = _out()
    assert workers.list_workers(prefix=PREFIX, cli_version=VERSION, aws=aws, out=out, as_json=True) == 0
    import json as _json
    doc = _json.loads(text())
    assert doc["prefix"] == PREFIX and doc["version"] == VERSION and doc["default_variant"] == "login"
    nova = doc["engines"]["novaact"]
    assert nova["family"] == names.task_def_name(PREFIX, "novaact") and nova["ecr_repo"] == names.ecr_repo_name(PREFIX, "novaact")
    assert [v["variant"] for v in nova["variants"]] == ["login"]
    v = nova["variants"][0]
    assert v["tag"] == f"{VERSION}-login" and v["digest"].startswith("sha256:7") and v["revision_arn"] and v["template_arn"]
    assert nova["pending_cleanup"] and nova["pending_cleanup"][0]["reason"] == "retired" and nova["pending_cleanup"][0]["retired_at"]
    assert doc["engines"]["midscene"]["variants"] == []


def test_list_workers_lists_only_revisions_outside_every_mapping(aws):
    """待清理条目只列不在任何版本映射里、带血缘 tags 的 revision（ADR 0038「命令族」节 list-workers 条）：仍在某个映射里的
    不列，即使它带着 `gherkai:retired-at`（下一趟清理会摘掉那个 tag）；带这个 tag 的为 `retired`、`retired_at` 即 tag 值，
    还没有的为 `orphan`、`retired_at` 为 null。各条键集相同，不带 `still_mapped`。"""
    templates = seed_backend(aws)
    shared = _share_with_old_version(aws, "sha256:" + "4" * 64)
    _push(aws, FakeContainer(digests=["sha256:" + "9" * 64]))           # 当前版本换 digest 重推：shared 只剩旧版本的映射引用
    _retire_now(aws, shared, NOW - timedelta(hours=3))                   # 摆出「仍在映射里却带着 tag」，还没有清理摘掉它
    retired = _unmapped_retired(aws, templates, retired_at=NOW - timedelta(minutes=10), variant="base",
                                digest="sha256:" + "a" * 64)
    orphan = _register_unmapped(aws, templates, digest="sha256:" + "c" * 64, variant="stray")

    out, text = _out()
    assert workers.list_workers(prefix=PREFIX, cli_version=VERSION, aws=aws, out=out, as_json=True) == 0
    items = {i["revision_arn"]: i for i in json.loads(text())["engines"]["novaact"]["pending_cleanup"]}
    assert set(items) == {retired, orphan}, items
    assert (items[retired]["reason"], items[retired]["retired_at"]) == ("retired", (NOW - timedelta(minutes=10)).isoformat())
    assert (items[orphan]["reason"], items[orphan]["retired_at"]) == ("orphan", None)
    assert {frozenset(i) for i in items.values()} == {
        frozenset({"revision_arn", "reason", "variant", "retired_at", "registered_at"})}

    out, text = _out()
    assert workers.list_workers(prefix=PREFIX, cli_version=VERSION, aws=aws, out=out) == 0
    body = text()
    assert f"待清理 {workers._short_arn(shared)} " not in body
    assert f"待清理 {workers._short_arn(retired)}  已退休 " in body
    assert f"待清理 {workers._short_arn(orphan)}  孤儿：无任何版本的映射引用" in body
    assert "仍被某个版本的映射引用" not in body


# 契约页的切节与键名提取规则同 cli/tests/test_cli_json_contract.py 的 `_sections` 与 `_documented_keys`（同源复制，改一处须同步另一处）。
# 不从那里导入：两个测试目录都不是 Python 包，且那个模块导入 gherkai_cli，而本包是 CLI 的可选依赖，不反过来依赖 CLI。
CONTRACT_DOC = Path(__file__).resolve().parents[2] / "docs" / "internals" / "cli-json-contract.md"


def _sections() -> dict[str, str]:
    """契约页按 `## ` 标题切节：键是标题里 `gherkai` 之后的命令名（`run`、`list-deterministic`、`deploy list-workers`…，
    到第一个占位、省略号或选项为止），值是该节全文（含其下的 `###` 子节）。第一个 `## ` 之前的头部与通则不属于任何命令。"""
    sections: dict[str, str] = {}
    for chunk in re.split(r"^## ", CONTRACT_DOC.read_text(encoding="utf-8"), flags=re.M)[1:]:
        heading = chunk.partition("\n")[0]
        hit = re.match(r"`gherkai ([a-z][a-z-]*(?: [a-z][a-z-]*)*)", heading)
        assert hit, f"契约页的节标题应形如「`gherkai <命令> … --json`」，现为 {heading!r}：改标题，或改这里的切法"
        assert hit.group(1) not in sections, f"契约页有两节的命令名都是 {hit.group(1)!r}"
        sections[hit.group(1)] = chunk
    return sections


def _documented_keys(text: str) -> set[str]:
    """一段文档里以反引号写出的键名。合法书写形态：`key`、`a` / `b`（一格两个键）、`engines.<engine>.family`（取路径末段）、
    `jobs[]`（数组键，比对时去掉 `[]`）。"""
    keys = set()
    for token in re.findall(r"`([A-Za-z_][A-Za-z0-9_.<>/ \[\]]*?)`", text):
        for part in re.split(r"\s*/\s*", token):
            keys.add(part.split(".")[-1].rstrip("[]"))
    return keys


def test_list_workers_json_keys_match_contract_doc(aws):
    """`--json` 字段契约护栏（ADR 0041 决策五，与 cli/tests/test_cli_json_contract.py 读同一份文档）：从真实输出递归收集全部键名，
    逐个断言出现在契约页「`gherkai deploy list-workers --json`」一节里（以反引号写出）；别节写过的同名键不计入本节。
    样例含 variant 与退休 revision，键才收得全。"""
    seed_backend(aws)
    _push(aws, FakeContainer(digests=["sha256:" + "6" * 64]), set_default=True)
    _push(aws, FakeContainer(digests=["sha256:" + "7" * 64]))
    out, text = _out()
    assert workers.list_workers(prefix=PREFIX, cli_version=VERSION, aws=aws, out=out, as_json=True) == 0
    doc = json.loads(text())

    def leaf_keys(o, acc=None):
        acc = set() if acc is None else acc
        if isinstance(o, dict):
            for k, v in o.items():
                acc.add(k)
                leaf_keys(v, acc)
        elif isinstance(o, list):
            for v in o:
                leaf_keys(v, acc)
        return acc

    documented = _documented_keys(_sections()["deploy list-workers"])
    missing = sorted(k for k in leaf_keys(doc) if k not in documented and k not in {"novaact", "midscene"})  # 引擎名是键、非契约字段
    assert not missing, (f"[deploy list-workers] 这些键出现在真实输出里、契约页「deploy list-workers」一节没写：{missing}——改 "
                         "docs/internals/cli-json-contract.md 的对应节")


def test_pending_cleanup_is_json_serializable_with_real_registered_at(monkeypatch):
    """真 AWS 的 DescribeTaskDefinition 带 registeredAt（datetime），moto 不带——`--json` 曾因此 TypeError 而单测照不出。
    _pending_cleanup 把它转成 ISO 串，doc 可直接 json.dumps；在映射里的不列，无血缘 tags 的不列。"""
    from types import SimpleNamespace

    revs = [workers.RevisionInfo(arn="arn:r/1", tags={names.TAG_VARIANT: "login", names.TAG_DIGEST: "sha256:a",
                                                        names.TAG_RETIRED_AT: "2026-09-08T07:00:00+00:00"},
                                 registered_at=datetime(2026, 9, 8, 6, 0, tzinfo=timezone.utc)),
            workers.RevisionInfo(arn="arn:r/2", tags={names.TAG_VARIANT: "stray", names.TAG_DIGEST: "sha256:b"},
                                 registered_at=datetime(2026, 9, 8, 6, 30, tzinfo=timezone.utc)),
            workers.RevisionInfo(arn="arn:r/3", tags={names.TAG_RETIRED_AT: "2026-09-08T07:00:00+00:00"})]
    monkeypatch.setattr(workers, "scan_family", lambda ecs, family: revs)
    items = workers._pending_cleanup(aws=SimpleNamespace(ecs=None), family="f", mapped=set())  # scan_family 已替换，ecs 不被真用
    assert [i["reason"] for i in items] == ["retired", "orphan"]
    assert items[0]["registered_at"] == "2026-09-08T06:00:00+00:00"
    json.dumps(items)  # 不抛
    mapped_items = workers._pending_cleanup(aws=SimpleNamespace(ecs=None), family="f", mapped={"arn:r/1"})
    assert [i["revision_arn"] for i in mapped_items] == ["arn:r/2"]


def test_list_workers_json_sends_diagnostics_to_err_sink(aws):
    """--json 下 stdout 只留一个 JSON 文档：skew 提示 / 读失败诊断走 err（stderr），文本输出行为不变。"""
    seed_backend(aws, stamp="9.9.9")  # 后端戳与 CLI 版本不一致 → skew 提示
    out, text = _out()
    errs: list[str] = []
    rc = workers.list_workers(prefix=PREFIX, cli_version=VERSION, aws=aws, out=out,
                              err=lambda *a: errs.append(" ".join(str(x) for x in a)), as_json=True)
    body = text()
    if rc == 0:
        import json as _json
        _json.loads(body)  # stdout 可解析
        assert errs, "skew 提示应走 err"
    else:
        assert body == "" and errs  # block 判定：stdout 为空、诊断在 err
