"""`push-worker` 八步 / `deploy` 三步 / 清理 pass / `list-workers` 测试（ADR 0038）。

**证据边界**：AWS 侧全走 moto（SSM/ECS/ECR/DynamoDB），容器引擎走假替身 —— 验的是**编排**（步序、幂等查重、
血缘 tags、退休与清理两道闸、SSM 记录形状）。**mock 不出来的两类**另处交代：容器引擎的真实行为在
`test_container.py` 的真 docker 那三条；真 ECR push / RunTask 拉起注册出来的 revision 需要真账号，本机无凭证、
**未验**（ADR 0038「实测项」6 的后半段仍挂着）。

moto 的两处已知偏差（顺手记下，别当成实现问题）：
- `DescribeTaskDefinition` **不返回 `registeredAt`** → 孤儿 revision 的「退休时刻 := registeredAt」在 moto 下取不到，
  实现回落成「此刻退休」（于是本次必然未满静默期、留到下次 pass）。孤儿**删除**那一支因此用一个小 stub ECS 验。
- `list_task_definitions` 不分页，故翻页逻辑本身没被 moto 覆盖（实现里带了 `nextToken` 循环）。
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

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


def seed_backend(aws: workers.Aws, *, stamp: str | None = VERSION, cpu: str = "1024") -> dict[str, str]:
    """把「`gherkai deploy` 已经跑过一次」的后端摆出来：ECR repo ×2 + 模板 revision ×2（SSM worker-template）
    + 版本戳 + runs 表（带 status GSI）。返回 {engine: 模板 revision ARN}。

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
                # CDK 的模板镜像栏 = `<repo-uri>:latest` 占位（ADR 0038「模板 revision」）
                "image": f"{REGISTRY}/{repo}:latest", "cpu": 0, "memory": 2048,
            }],
            requiresCompatibilities=["FARGATE"], networkMode="awsvpc", cpu=cpu, memory="2048",
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
                                  {"AttributeName": "status", "AttributeType": "S"}],
            GlobalSecondaryIndexes=[{
                "IndexName": names.RUNS_STATUS_GSI,
                "KeySchema": [{"AttributeName": "status", "KeyType": "HASH"}],
                "Projection": {"ProjectionType": "INCLUDE",
                               "NonKeyAttributes": [names.STATE_WORKER_TASK_DEF_ARNS_ATTR]},
            }],
            BillingMode="PAY_PER_REQUEST",
        )
    return templates


class FakeContainer:
    """容器引擎替身。**只有 push 过的 ref 才有 `repo_digests`**——照抄真 docker 的行为（见 container 模块头：
    本地 build 的镜像 `RepoDigests` 为空，这是「推送后才取 digest」的根据）。

    `ghcr_noise=True` 时 post-push 的 `repo_digests` **第一条是 GHCR 的**（基底同步路径的真实形态），
    用来把「取第一条」这种实现方式钉死在红。
    """

    def __init__(self, *, arch: str = "amd64", os_: str = "linux", exists: bool = True,
                 digests: list[str] | None = None, ghcr_noise: bool = True, probe_error: str | None = None):
        self.arch, self.os_, self.exists = arch, os_, exists
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
            return ImageInfo(exists=True, os=self.os_, architecture=self.arch, repo_digests=tuple(entries))
        if not self.exists:
            return ImageInfo(exists=False)
        return ImageInfo(exists=True, os=self.os_, architecture=self.arch)

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


def _out():
    """收集打印文本的 out 替身 → (调用函数, 取全文函数)。"""
    lines: list[str] = []
    return (lambda *a: lines.append(" ".join(str(x) for x in a))), (lambda: "\n".join(lines))


def _push(aws, container, *, engine="novaact", variant="login", set_default=False, now=NOW, version=VERSION):
    out, text = _out()
    rc = workers.push_worker("acme:img", engine=engine, variant=variant, set_default=set_default,
                             cli_version=version, prefix=PREFIX, container=container, aws=aws,
                             now=now, out=out)
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
    """digest 的唯一来源 = **推送后**那次 inspect，且在多条 `RepoDigests` 里**按本 repo 挑**（GHCR 那条在第一位）。"""
    seed_backend(aws)
    c = FakeContainer(digests=["sha256:" + "c" * 64], ghcr_noise=True)
    rc, text = _push(aws, c)
    assert rc == 0, text
    inspects = [ref for kind, ref in ((k, a[0]) for k, *a in c.calls if k == "inspect")]
    assert len(inspects) == 2 and inspects[0] == "acme:img"           # 推送前一次（存在+架构）
    assert inspects[1].endswith(":1.4.0-login")                       # 推送后一次（取 digest）
    assert _mapping(aws, "novaact", "login")["digest"] == "sha256:" + "c" * 64


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


def test_missing_local_image_exits_2(aws):
    seed_backend(aws)
    rc, text = _push(aws, FakeContainer(exists=False))
    assert rc == 2 and "本地找不到镜像" in text


def test_skew_block_exits_2_before_any_container_call(aws):
    """CLI **新于**后端 → 退 2、无放行口（ADR 0037 决策 7 三态原样沿用），且**一次容器引擎都不碰**：
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


def test_orphan_revision_is_reused_instead_of_registered(aws):
    """「上次中断在注册与写 SSM 之间」留下的孤儿：按血缘 tags 复用，不重复注册（ADR 0038 步 5）。"""
    templates = seed_backend(aws)
    digest = "sha256:" + "e" * 64
    repo_uri = f"{REGISTRY}/{names.ecr_repo_name(PREFIX, 'novaact')}"
    orphan = workers._register_revision(aws.ecs, template_arn=templates["novaact"], engine="novaact",
                                        image_ref=f"{repo_uri}@{digest}", digest=digest,
                                        variant="login", version=VERSION)
    before = _revisions(aws, "novaact")
    rc, text = _push(aws, FakeContainer(digests=[digest]))
    assert rc == 0, text
    assert _revisions(aws, "novaact") == before, "孤儿应被复用，不该再注册"
    assert _mapping(aws, "novaact", "login")["revision_arn"] == orphan
    assert "复用" in text


def test_same_digest_under_another_variant_is_not_reused(aws):
    """同 digest 但**另一个 variant** 的 revision 不复用（真跑抓到：probe 复用了 base 正在用的 revision，之后 base
    换 digest 重推会把它退休、满静默期清掉，probe 的映射悬空）。每个 variant 自己一个 revision。"""
    seed_backend(aws)
    digest = "sha256:" + "a" * 64
    rc, _ = _push(aws, FakeContainer(digests=[digest]), variant="base")
    assert rc == 0
    base_rev = _mapping(aws, "novaact", "base")["revision_arn"]
    rc, text = _push(aws, FakeContainer(digests=[digest]), variant="login")
    assert rc == 0, text
    assert _mapping(aws, "novaact", "login")["revision_arn"] != base_rev
    assert "复用" not in text


def test_retired_orphan_is_not_reused(aws):
    """已打退休 tag 的 revision **不复用**（它已被判下岗，抢回来只会让清理语义混乱）→ 注册一个干净的。"""
    templates = seed_backend(aws)
    digest = "sha256:" + "f" * 64
    repo_uri = f"{REGISTRY}/{names.ecr_repo_name(PREFIX, 'novaact')}"
    retired = workers._register_revision(aws.ecs, template_arn=templates["novaact"], engine="novaact",
                                         image_ref=f"{repo_uri}@{digest}", digest=digest,
                                         variant="login", version=VERSION)
    aws.ecs.tag_resource(resourceArn=retired, tags=[{"key": names.TAG_RETIRED_AT, "value": NOW.isoformat()}])
    rc, _ = _push(aws, FakeContainer(digests=[digest]))
    assert rc == 0
    assert _mapping(aws, "novaact", "login")["revision_arn"] != retired


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
    assert old_arn in _revisions(aws, "novaact"), "退休 ≠ 立刻删（在跑 run 的后续 job 还要用它起 task）"
    assert "原 digest" in text and "新 digest" in text


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


def _cleanup(aws, now):
    out, text = _out()
    return workers.cleanup_pass(prefix=PREFIX, engines=names.ENGINES, ssm=aws.ssm, ecs=aws.ecs,
                                ddb=aws.ddb, now=now, out=out), text()


def test_cleanup_keeps_within_the_quiet_period(aws):
    """退休未满 1 小时 → 不删。静默期覆盖「preflight 刚解析成 R、definition 尚未落库」的窗口 +
    注销后最多 10 分钟才生效的 AWS 延迟。"""
    seed_backend(aws)
    _push(aws, FakeContainer())
    arn = _mapping(aws, "novaact", "login")["revision_arn"]
    aws.ssm.delete_parameter(Name=names.ssm_path(PREFIX, names.worker_image_key("novaact", "1.4.0-login")))
    _retire_now(aws, arn, NOW)
    outcome, _ = _cleanup(aws, NOW + timedelta(minutes=59))
    assert outcome.deleted == ()
    assert any(a == arn and "静默期" in why for a, why in outcome.kept)
    assert arn in _revisions(aws, "novaact")


def test_cleanup_deletes_after_quiet_period_when_unreferenced(aws):
    seed_backend(aws)
    _push(aws, FakeContainer())
    arn = _mapping(aws, "novaact", "login")["revision_arn"]
    aws.ssm.delete_parameter(Name=names.ssm_path(PREFIX, names.worker_image_key("novaact", "1.4.0-login")))
    _retire_now(aws, arn, NOW)
    outcome, _ = _cleanup(aws, NOW + timedelta(hours=2))
    assert outcome.deleted == (arn,), outcome
    assert arn not in _revisions(aws, "novaact")


def test_cleanup_keeps_a_retired_revision_still_referenced_by_a_mapping(aws):
    """退休 tag 只是「某次替换判它下岗」；若任何映射仍指着它（曾被另一 variant 共用的历史状态），删了就悬空——留着。"""
    seed_backend(aws)
    _push(aws, FakeContainer())
    arn = _mapping(aws, "novaact", "login")["revision_arn"]
    _retire_now(aws, arn, NOW - timedelta(hours=3))
    outcome, _ = _cleanup(aws, NOW)
    assert arn not in outcome.deleted
    assert any(a == arn and "映射引用" in why for a, why in outcome.kept)
    assert arn in _revisions(aws, "novaact")


def test_cleanup_keeps_when_a_pending_run_references_it(aws):
    """在跑 run 安全阀：STATE 顶层 `worker_task_def_arns` 里有它 + run 未到终态 → 留着。

    detached run 逐 job 起 task，删早了剩余 job 全起不来。查法 = status GSI 的 Query + `contains` 过滤（不 Scan）。
    """
    seed_backend(aws)
    _push(aws, FakeContainer())
    arn = _mapping(aws, "novaact", "login")["revision_arn"]
    aws.ssm.delete_parameter(Name=names.ssm_path(PREFIX, names.worker_image_key("novaact", "1.4.0-login")))
    _retire_now(aws, arn, NOW)
    aws.ddb.put_item(TableName=names.default_name(PREFIX, names.BASE_RUNS_TABLE), Item={
        "run_id": {"S": "r1"}, "item_type": {"S": "STATE"}, "status": {"S": "pending"},
        names.STATE_WORKER_TASK_DEF_ARNS_ATTR: {"L": [{"S": arn}]},
    })
    outcome, _ = _cleanup(aws, NOW + timedelta(hours=2))
    assert outcome.deleted == ()
    assert any(a == arn and "未到终态" in why for a, why in outcome.kept)


def test_cleanup_deletes_when_the_referencing_run_is_terminal(aws):
    """同一份数据、run 已到终态（passed）→ GSI 上换了分区、安全阀不再拦。"""
    seed_backend(aws)
    _push(aws, FakeContainer())
    arn = _mapping(aws, "novaact", "login")["revision_arn"]
    aws.ssm.delete_parameter(Name=names.ssm_path(PREFIX, names.worker_image_key("novaact", "1.4.0-login")))
    _retire_now(aws, arn, NOW)
    aws.ddb.put_item(TableName=names.default_name(PREFIX, names.BASE_RUNS_TABLE), Item={
        "run_id": {"S": "r1"}, "item_type": {"S": "STATE"}, "status": {"S": "passed"},
        names.STATE_WORKER_TASK_DEF_ARNS_ATTR: {"L": [{"S": arn}]},
    })
    outcome, _ = _cleanup(aws, NOW + timedelta(hours=2))
    assert outcome.deleted == (arn,), outcome


def test_cleanup_detects_orphans_by_lineage_tags(aws):
    """带血缘 tags、ACTIVE、却不在**任何版本**的映射里 → 孤儿（并发 push 的先写者 / 中断残留）。

    moto 不返回 `registeredAt`，实现回落成「此刻退休」→ 本次必然被留下（宁可滞留也不早删）。孤儿**删除**
    那一支见 `test_cleanup_deletes_an_old_orphan`。
    """
    templates = seed_backend(aws)
    repo_uri = f"{REGISTRY}/{names.ecr_repo_name(PREFIX, 'novaact')}"
    orphan = workers._register_revision(aws.ecs, template_arn=templates["novaact"], engine="novaact",
                                        image_ref=f"{repo_uri}@sha256:{'9' * 64}", digest="sha256:" + "9" * 64,
                                        variant="stray", version=VERSION)
    outcome, _ = _cleanup(aws, NOW + timedelta(days=1))
    assert outcome.deleted == ()
    assert any(a == orphan and "孤儿" in why for a, why in outcome.kept), outcome


def test_cleanup_skips_the_whole_pass_when_the_mappings_cannot_be_listed(aws):
    """读不全 `worker-image/*` 映射 → **整趟放弃**，不把所有 revision 判成孤儿。

    「读不全就当没有映射」会让每个在用 revision 都变成孤儿，而真实 ECS 的 `registeredAt` 是过去时刻——
    静默期那道闸拦不住，等于批量误删在跑 run 手里的 revision。
    """
    seed_backend(aws)
    _push(aws, FakeContainer())
    arn = _mapping(aws, "novaact", "login")["revision_arn"]
    _retire_now(aws, arn, NOW - timedelta(hours=5))

    class _BrokenSsm:
        def __getattr__(self, item):
            def boom(**kw):
                raise RuntimeError("AccessDenied: ssm:GetParametersByPath")
            return boom

    out, text = _out()
    outcome = workers.cleanup_pass(prefix=PREFIX, engines=names.ENGINES, ssm=_BrokenSsm(), ecs=aws.ecs,
                                   ddb=aws.ddb, now=NOW, out=out)
    assert outcome == workers.CleanupOutcome() and "跳过清理" in text()
    assert arn in _revisions(aws, "novaact")


def test_cleanup_never_touches_the_template_revision(aws):
    """模板 revision **没有血缘 tags** → 永不进清理候选（它是所有 variant 的母本，删了就没法再注册）。"""
    templates = seed_backend(aws)
    outcome, _ = _cleanup(aws, NOW + timedelta(days=30))
    assert outcome.deleted == () and outcome.kept == ()
    for arn in templates.values():
        assert arn in _revisions(aws, arn.rsplit("/", 1)[-1].split("-")[1])


class _StubEcs:
    """最小 ECS 替身：**返回 `registeredAt`**（moto 不返回）——专供「孤儿满静默期后被回收」那一支。"""

    def __init__(self, arn: str, family: str, registered_at: datetime, tags: dict[str, str]):
        self.arn, self.family, self.registered_at, self._tags = arn, family, registered_at, tags
        self.deregistered: list[str] = []
        self.deleted: list[str] = []

    def list_task_definitions(self, **kw):
        return {"taskDefinitionArns": [self.arn] if kw.get("familyPrefix") == self.family else []}

    def describe_task_definition(self, **kw):
        return {"taskDefinition": {"family": self.family, "taskDefinitionArn": self.arn,
                                   "registeredAt": self.registered_at},
                "tags": [{"key": k, "value": v} for k, v in self._tags.items()]}

    def deregister_task_definition(self, **kw):
        self.deregistered.append(kw["taskDefinition"])

    def delete_task_definitions(self, **kw):
        self.deleted.extend(kw["taskDefinitions"])


def test_cleanup_deletes_an_old_orphan(aws):
    """孤儿的退休时刻 := 它的 `registeredAt`；早于静默期且无 run 引用 → 回收。"""
    seed_backend(aws)
    family = names.task_def_name(PREFIX, "novaact")
    arn = f"arn:aws:ecs:{REGION}:{ACCOUNT}:task-definition/{family}:99"
    stub = _StubEcs(arn, family, NOW - timedelta(hours=5),
                    {names.TAG_VARIANT: "stray", names.TAG_DIGEST: "sha256:" + "8" * 64})
    outcome = workers.cleanup_pass(prefix=PREFIX, engines=("novaact",), ssm=aws.ssm, ecs=stub,
                                   ddb=aws.ddb, now=NOW, out=lambda *a: None)
    assert outcome.deleted == (arn,) and stub.deregistered == [arn] and stub.deleted == [arn]


def test_push_worker_runs_a_cleanup_pass_at_the_end(aws):
    """步 8 末的机会式 pass（无定时任务）：一个早已退休的 revision 在下一次 push 时被回收。"""
    templates = seed_backend(aws)
    repo_uri = f"{REGISTRY}/{names.ecr_repo_name(PREFIX, 'novaact')}"
    stale = workers._register_revision(aws.ecs, template_arn=templates["novaact"], engine="novaact",
                                       image_ref=f"{repo_uri}@sha256:{'7' * 64}", digest="sha256:" + "7" * 64,
                                       variant="old", version=VERSION)
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
    assert "不动" in text2(), "默认指针记的是团队意图，升级不重置（ADR 0038）"


def test_sync_base_pulls_ghcr_and_pushes_as_base(aws):
    seed_backend(aws)
    c = FakeContainer()
    out, text = _out()
    results = workers.sync_base(prefix=PREFIX, engines=names.ENGINES, version=VERSION, container=c,
                               aws=aws, now=NOW, out=out)
    assert [r.variant for r in results] == ["base", "base"]
    pulls = [(ref, platform) for kind, ref, platform in (c_ for c_ in c.calls if c_[0] == "pull")]
    assert pulls == [("ghcr.io/zhiyanliu/gherkai-worker-novaact:1.4.0", "linux/amd64"),
                     ("ghcr.io/zhiyanliu/gherkai-worker-midscene:1.4.0", "linux/amd64")]
    assert _mapping(aws, "novaact", "base")["revision_arn"]


def test_sync_base_skips_non_pure_release_but_deploy_continues(aws):
    """dev 版（`.dev`/`.post`/本地段）**GHCR 上不存在对应基底** → 明确警告 + 跳过基底同步，第 3/4 步照跑。

    判据复用 `compose.is_pure_release`（决策 2b：非纯净版本一定带 `+`/`.dev`）。硬失败会逼 contributor 绕过命令。
    """
    dev = "1.4.0.post3.dev0+28c1684"
    seed_backend(aws, stamp=dev)
    c = FakeContainer()
    out, text = _out()
    rc = workers.run_deploy_steps(prefix=PREFIX, version=dev, container=c, aws=aws, now=NOW, out=out)
    assert rc == 0
    assert not any(k == "pull" for k, *_ in c.calls), "dev 版不该去拉 GHCR"
    assert "GHCR" in text() and "push-worker" in text()
    assert aws.ssm.get_parameter(Name=names.ssm_path(PREFIX, names.WORKER_DEFAULT_KEY)
                                 )["Parameter"]["Value"] == "base", "第 3 步照跑"


def test_sync_base_pull_failure_points_at_the_half_published_state(aws):
    seed_backend(aws)
    c = FakeContainer()
    c.pull_fails = True
    out, text = _out()
    rc = workers.run_deploy_steps(prefix=PREFIX, version=VERSION, container=c, aws=aws, now=NOW, out=out)
    assert rc == 1, "cdk 已成功而后续步骤失败 → 退 1"
    # 断言用户能据以行动的两句：状态（stack 已生效）+ 重跑哪个命令。
    assert "拉不到基底" in text() and "半发布态" in text()  # sync_base 自己那条（不是四步兜底行）
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
                                        aws=aws, now=NOW, out=out)
    after = _mapping(aws, "novaact", "login")
    assert [r.variant for r in results] == ["login"]
    assert after["template_arn"] == new_templates["novaact"]
    assert after["revision_arn"] != before["revision_arn"]
    assert after["digest"] == before["digest"] and after["pushed_at"] == before["pushed_at"]
    td = aws.ecs.describe_task_definition(taskDefinition=after["revision_arn"])["taskDefinition"]
    assert td["cpu"] == "2048", "重派生的意义就在于让既有 variant 跟上模板的新配置"
    assert td["containerDefinitions"][0]["image"].endswith(f"@{before['digest']}")
    assert _tags(aws, before["revision_arn"])[names.TAG_RETIRED_AT] == NOW.isoformat()
    assert "重派生" in text()


def test_rederive_skips_when_template_arn_is_unchanged(aws):
    seed_backend(aws)
    _push(aws, FakeContainer())
    before = _revisions(aws, "novaact")
    out, text = _out()
    results = workers.rederive_variants(prefix=PREFIX, engines=names.ENGINES, version=VERSION,
                                        aws=aws, now=NOW, out=out)
    assert results == [] and _revisions(aws, "novaact") == before
    assert "无需重派生" in text()


def test_rederive_ignores_other_versions(aws):
    """variant 按版本隔离：**只重派生当前版本**的映射（旧版本留作历史，其回收归 `delete-worker`）。"""
    seed_backend(aws)
    _push(aws, FakeContainer(), version="1.3.0")             # 一个旧版本的映射
    new_templates = seed_backend(aws, cpu="2048")
    out, _ = _out()
    results = workers.rederive_variants(prefix=PREFIX, engines=names.ENGINES, version=VERSION,
                                        aws=aws, now=NOW, out=out)
    assert results == []
    assert _mapping(aws, "novaact", "login", version="1.3.0")["template_arn"] != new_templates["novaact"]


def test_run_deploy_steps_reports_a_missing_container_engine_as_exit_1(aws):
    """cdk 已成功、机器上没有容器引擎 → 退 1 + 「stack 已生效、重跑幂等收敛」（不是退 2：账户已被改过）。"""
    seed_backend(aws)
    out, text = _out()
    rc = workers.run_deploy_steps(prefix=PREFIX, version=VERSION,
                                 container=FakeContainer(probe_error="找不到容器引擎 `docker`"),
                                 aws=aws, now=NOW, out=out)
    assert rc == 1
    assert "stack 已生效" in text() and "容器引擎" in text()


def test_deploy_steps_are_idempotent(aws):
    """四步重跑收敛：第二趟不该多出任何 revision（同二元组查重 + 指针不动 + 无需重派生）。"""
    seed_backend(aws)
    c = FakeContainer(digests=["sha256:" + "4" * 64, "sha256:" + "5" * 64,
                               "sha256:" + "4" * 64, "sha256:" + "5" * 64])
    out, _ = _out()
    assert workers.run_deploy_steps(prefix=PREFIX, version=VERSION, container=c, aws=aws, now=NOW, out=out) == 0
    first = {e: _revisions(aws, e) for e in names.ENGINES}
    assert workers.run_deploy_steps(prefix=PREFIX, version=VERSION, container=c, aws=aws,
                                    now=NOW + timedelta(minutes=1), out=out) == 0
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
    assert "== novaact（family gherkai-novaact-worker" in body and "== midscene（" in body
    for expected in ("base", "login", "1.4.0-login", "sha256:666666666666", "gherkai-novaact-worker:"):
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
    assert "版本 skew" in text()


def test_skew_gate_read_failure_exits_2_without_a_traceback(aws):
    """读戳失败（无凭证/无权限）→ 退 2 + 一句人话。

    `compose.read_backend_version` 有意把这类异常抛给入口皮归码，**本模块就是那个皮**——真跑踩过：
    没有凭证时 `gherkai deploy list-workers` 直接吐 botocore 的 `NoCredentialsError` 堆栈。
    """
    class _BrokenSsm:
        def get_parameter(self, **kw):
            raise RuntimeError("Unable to locate credentials")

    broken = workers.Aws(ssm=_BrokenSsm(), ecs=aws.ecs, ecr=aws.ecr, ddb=aws.ddb)
    out, text = _out()
    assert workers.list_workers(prefix=PREFIX, cli_version=VERSION, aws=broken, out=out) == 2
    assert "读不到后端版本戳" in text() and "凭证" in text()
    out2, text2 = _out()
    assert workers.push_worker("acme:img", engine="novaact", variant="v", cli_version=VERSION,
                               prefix=PREFIX, container=FakeContainer(), aws=broken, now=NOW, out=out2) == 2
    assert "读不到后端版本戳" in text2()


def test_list_workers_says_when_the_default_pointer_is_missing(aws):
    seed_backend(aws)
    out, text = _out()
    assert workers.list_workers(prefix=PREFIX, cli_version=VERSION, aws=aws, out=out) == 0
    assert "未初始化" in text()
