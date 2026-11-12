"""worker 镜像交付的云端半边（ADR 0038）：`push-worker` 八步 / `list-workers` / `gherkai deploy` 的四步 + 清理 pass。

**归属**：全部云端写操作（推 ECR、注册 task-def revision、写 SSM 指针）都是**部署变更**，故住
`gherkai-deploy-aws`、不住 CLI 本体（ADR 0038「命令族」）。镜像**构建**不在这里、也不在任何 gherkai 命令里
（定制镜像的 Dockerfile 模板见 `docs/user-guide/cloud-backend.md`）——被拒方案「gherkai 拥有定制镜像的构建」。

## 概念一句话（细节见 ADR 0038「概念模型」）

一个 **variant** 就是一套具名确定性 step 集、也就是一个定制镜像，落 ECR tag `<CLI 版本>-<variant>`，并对应一个
task-def **revision**（从 deploy 登记的**模板** revision 复制、镜像栏换成 `repo@sha256:<digest>`）。run 起
task 时用的是 revision（不可变快照），故重推同名 variant 不会把运行中的 run 换掉镜像。

## 正确性支点（改这个文件前先读）

- **digest 只在推送后取，且要按仓库挑**：见 `container` 模块头两条事实。
- **幂等靠每步先查再做**：`RegisterTaskDefinition` 不幂等，故以（模板 ARN、digest）二元组查重，且只在映射所指的
  revision 仍为 ACTIVE 时跳过注册；SSM 写是覆盖语义；ECR push 同 digest 天然无操作。中断在注册与写映射之间时，
  重新执行会再注册一个，不从 family 里复用未被映射的 revision（ADR 0038 被拒方案「孤儿复用」），上次注册的那个
  由清理 pass 在静默期之后回收。于是一个 revision 进入映射只有一条路：发起注册的那条命令把它写进自己那条映射。
- **`gherkai:retired-at` 表示 revision 从何时起不被任何映射引用，静默期一律从它起算**：替换映射的一步在写映射
  之后现读时钟打，清理 pass 给缺这个 tag 的孤儿补打；仍在映射里的由写映射一方与清理 pass 摘除（ADR 0038「不变量」
  清理 pass 条「候选与静默期起点」「打 tag 与写映射的交错」两段）。时刻一律经注入的时钟函数现读，不用命令开始时的时刻。
- **删 revision 前**：不在任何版本的 `worker-image/*` 映射里、tag 满 `RETIRE_QUIET_PERIOD`、runs 表索引就绪且引用快照里
  没有未到终态的 run 引用它，且注销之前的映射重读与最后核对都通过（`cleanup_pass`）。
  `DeregisterTaskDefinition` 让 revision 再也起不了新 task（且注销后最多 10 分钟才生效），detached run 逐 job
  起 task——删早了剩余 job 全起不来（ADR 0038 被拒方案「重派生/重推后立即删旧 revision」）。

## 退出码

`push-worker` / `list-workers` 的部署方可修的失败 → **2**（对齐 provider 既有前置口径）。
`gherkai deploy` 的四步失败 → **1** 且提示「stack 已生效；重新运行 `gherkai deploy` 幂等收敛」（ADR 0038
「四步的失败语义」）——cdk 已经改了账户，压成 2 会让人以为什么都没发生。
"""
from __future__ import annotations

import base64
from gherkai_runtime.textui import render_table  # 表格渲染单点（ADR 0047）
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from gherkai_deploy_aws import names
from gherkai_deploy_aws.container import ContainerError, digest_for_repo

EXIT_OK = 0
EXIT_FAILED = 1        # cdk 成功、四步失败（账户已被改动，见模块头「退出码」）
EXIT_PRECONDITION = 2  # 部署方可修的前置/校验失败

# 基础镜像同步进 ECR 的那份固定叫 `base`（ADR 0038「概念模型」），也是默认指针的初始值。
BASE_VARIANT = "base"
# 发布方 CI 发布的基础镜像（ADR 0037 决策 5；`<engine>` + `:<版本>`）。**运行时不直接拉它**——task-def 只指
# 使用方自己账号的 ECR（被拒方案「task-def 指向 GHCR 直接拉基础镜像」），这里只在 deploy 的基础镜像同步里 pull 一次。
GHCR_BASE_IMAGE = "ghcr.io/zhiyanliu/gherkai-worker-{engine}"

# 退休静默期（ADR 0038「清理 pass」）：覆盖「提交侧 preflight 刚解析成某 revision、definition 尚未落库」的窗口
# 与「注销后最多 10 分钟该限制才生效」的 AWS 延迟。宁可滞留（ACTIVE 但无人引用，无害）也不早删。
RETIRE_QUIET_PERIOD = timedelta(hours=1)

# `DescribeTaskDefinition` 回来的**只读字段**——`RegisterTaskDefinition` 不收它们（ADR 0038 步 6 逐字列出）。
# 其余字段（含 `runtimePlatform` / `cpu` / `memory` / 两个 role / 日志配置）**原样带走**：模板承载的正是
# 「只有部署后才存在或全局固定」的那些值。`deregisteredAt` 不在列——它只出现在 INACTIVE revision 上，而模板恒 ACTIVE。
_READ_ONLY_TASK_DEF_KEYS = (
    "taskDefinitionArn", "revision", "status", "requiresAttributes",
    "compatibilities", "registeredAt", "registeredBy",
)


class WorkerCommandError(Exception):
    """部署方可修的失败（`str(exc)` 即给人看的整句）。**退出码归调用方**：push-worker 给退出码 2、deploy 四步给退出码 1。"""


# ---------------------------------------------------------------------------
# boto3 句柄（惰性；`--help` 与纯逻辑测试不该为此拉 boto3）
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Aws:
    """本模块用到的四个 client。**组合根注入**（测试直接塞 moto client），同 compose 的 `_make_*` 惯例。"""

    ssm: object
    ecs: object
    ecr: object
    ddb: object


def make_aws(*, region=None, profile=None) -> Aws:
    """建四个 client（同一 session/region/profile 解析链，与 provider 其余命令一致）。"""
    import boto3

    session = boto3.session.Session(profile_name=profile, region_name=region)
    return Aws(ssm=session.client("ssm"), ecs=session.client("ecs"),
               ecr=session.client("ecr"), ddb=session.client("dynamodb"))


def _connect(*, region, profile, out) -> Aws | None:
    """建四个 client；失败（profile 名不存在 / 配不出 region / 缺凭证配置）→ 打一句诊断、返 None（调用点归退出码）。

    必须包住整个 `make_aws`、不是只包 client 调用：不存在的 profile 名在 `boto3.session.Session(...)` **构造期**
    就抛 `ProfileNotFound`，配不出 region 则要到 `session.client(...)` 解析 endpoint 时才抛 `NoRegionError`；
    留在入口 `try` 之外就成裸 traceback（同 `cli._guard_vpc_spec` 的口径：这类对部署方是「先修凭证」）。

    **本钩子不是唯一的一口**：更早一步——把 prefix/region/profile 解析成 target——也能抛同类异常（未给
    region 时解析会回落读 profile config），那一步归 `cli.Provider._resolve_target_or_report`，排在本钩子之前。
    """
    try:
        return make_aws(region=region, profile=profile)
    except Exception as exc:
        out(f"连不上 AWS：{exc}\n需要可用的凭证与 region（--region / AWS_REGION / --profile）。")
        return None


def _error_code(exc: Exception) -> str | None:
    """botocore `ClientError` 的 `Error.Code`（非 ClientError → None）。

    鸭子类型、**不 import botocore**：本模块不该为读一个错误码把 botocore 变成 import 期依赖
    （同 `cli._error_code` / `compose.read_backend_version` 的处理；三行的东西不值得跨模块借私名）。
    """
    resp = getattr(exc, "response", None)
    if not isinstance(resp, dict):
        return None
    return resp.get("Error", {}).get("Code")


# ---------------------------------------------------------------------------
# SSM 读写（三族参数的真源表见 ADR 0038「SSM 参数与命名真源」）
# ---------------------------------------------------------------------------

def _read_ssm(ssm, path: str) -> str | None:
    """读一个参数；`ParameterNotFound` → None（缺失是正常分叉，由调用点给专属提示）。"""
    try:
        resp = ssm.get_parameter(Name=path)
    except Exception as exc:
        if _error_code(exc) == "ParameterNotFound":
            return None
        raise
    return (resp["Parameter"]["Value"] or "").strip() or None


def _put_ssm(ssm, path: str, value: str) -> None:
    """写一个 String 参数（覆盖语义——「最后写者赢」，孤儿由清理 pass 回收，ADR 0038 不变量）。"""
    ssm.put_parameter(Name=path, Value=value, Type="String", Overwrite=True)


@dataclass(frozen=True)
class ImageMapping:
    """SSM `worker-image/<engine>/<tag>` 的一条映射（JSON 四键 + 从键名反推的 engine/tag/variant）。

    `engine` 是记录的身份位（从参数路径反推）；当前调用方都已自带 engine（`current_version_mappings` 用它做
    过滤后才构造），故该字段暂无读点、**有意保留**。
    """

    engine: str
    tag: str
    variant: str
    template_arn: str
    revision_arn: str
    digest: str
    pushed_at: str


def _mapping_path(prefix: str, engine: str, tag: str) -> str:
    return names.ssm_path(prefix, names.worker_image_key(engine, tag))


def _record_json(*, template_arn: str, revision_arn: str, digest: str, pushed_at: str) -> str:
    """映射记录的 JSON——**四个键名是跨组件契约**（提交侧 preflight 的 variant 解析读它，ADR 0038）。"""
    return json.dumps({"template_arn": template_arn, "revision_arn": revision_arn,
                       "digest": digest, "pushed_at": pushed_at}, ensure_ascii=False)


def _parse_mapping(engine: str, tag: str, raw: str, *, version: str) -> ImageMapping | None:
    """JSON → `ImageMapping`；读不懂/缺键 → None（**不抛**：一条坏参数不该让 list-workers 或清理 pass 全瘫）。"""
    try:
        data = json.loads(raw)
    except ValueError:
        return None
    if not isinstance(data, dict):
        return None
    missing = [k for k in ("template_arn", "revision_arn", "digest") if not data.get(k)]
    if missing:
        return None
    return ImageMapping(
        engine=engine, tag=tag, variant=_variant_of(tag, version) or tag,
        template_arn=data["template_arn"], revision_arn=data["revision_arn"],
        digest=data["digest"], pushed_at=str(data.get("pushed_at") or ""),
    )


def read_mapping(ssm, *, prefix: str, engine: str, tag: str, version: str) -> ImageMapping | None:
    """点读一条映射（缺失或读不懂 → None）。"""
    raw = _read_ssm(ssm, _mapping_path(prefix, engine, tag))
    return _parse_mapping(engine, tag, raw, version=version) if raw else None


def _iter_image_params(ssm, prefix: str):
    """枚举 `worker-image/*` 全部参数（**含所有版本、所有引擎**）→ `(engine, tag, value)`。

    `GetParametersByPath(Recursive=True)` 单页最多 10 条、**必须翻页**（ADR 0038「SSM 参数与命名真源」末句）；
    漏翻页的后果是清理 pass 把翻到第二页的 variant 判成孤儿、静默删掉别人在用的 revision。
    """
    root = names.ssm_path(prefix, names.WORKER_IMAGE_ROOT_KEY)
    token = None
    while True:
        kwargs = {"Path": root, "Recursive": True}
        if token:
            kwargs["NextToken"] = token
        resp = ssm.get_parameters_by_path(**kwargs)
        for param in resp.get("Parameters") or []:
            rest = param["Name"][len(root):].strip("/")     # `<engine>/<tag>`
            engine, _, tag = rest.partition("/")
            if engine and tag:
                yield engine, tag, param.get("Value") or ""
        token = resp.get("NextToken")
        if not token:
            return


def _version_tag_prefix(version: str) -> str:
    """当前版本的 tag 前缀 `<归一化版本>-`。

    **由 `names.image_tag` 反推、不复刻它的归一化规则**（拿哨兵 variant 拼出 tag 再去掉尾巴）——tag 命名是
    单一真源、同时是单一校验点（ADR 0038「tag 命名」），第二份归一化实现就是第二个真源。
    """
    sentinel = "x"
    return names.image_tag(version, sentinel)[: -len(sentinel)]


def _variant_of(tag: str, version: str) -> str | None:
    """`<归一化版本>-<variant>` → variant；不属于本版本 → None（variant 名本身可含 `-`，故按前缀切、不按最后一个 `-`）。"""
    head = _version_tag_prefix(version)
    return tag[len(head):] if tag.startswith(head) and len(tag) > len(head) else None


def current_version_mappings(params, *, engine: str, version: str) -> list[ImageMapping]:
    """某引擎**当前版本**的全部 variant 映射（按 variant 名排序）。旧版本的留作历史、不参与当前版本解析。

    **吃一次枚举好的 `(engine, tag, value)` 序列**（`list(_iter_image_params(ssm, prefix))`）、自己不枚举：枚举与
    筛选分开，是为让**一次** `_iter_image_params`（要翻页、且跨全部版本全部引擎）喂多个引擎的筛选——逐引擎各走
    一遍全量枚举会把 `GetParametersByPath` 的翻页次数乘上引擎数。读不懂的映射按 `_parse_mapping` 的口径丢掉、不抛。
    """
    out: list[ImageMapping] = []
    for eng, tag, raw in params:
        if eng != engine or _variant_of(tag, version) is None:
            continue
        mapping = _parse_mapping(eng, tag, raw, version=version)
        if mapping is not None:
            out.append(mapping)
    return sorted(out, key=lambda m: m.variant)


def read_default_variant(ssm, prefix: str) -> str | None:
    """默认指针（部署级一个；缺失 → None）。"""
    return _read_ssm(ssm, names.ssm_path(prefix, names.WORKER_DEFAULT_KEY))


# ---------------------------------------------------------------------------
# task-def family 侧（血缘 tags 是退休/孤儿判定的唯一账本，ADR 0038：不进 SSM）
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RevisionInfo:
    """family 里的一个 ACTIVE revision + 它的 tags。"""

    arn: str
    tags: dict[str, str] = field(default_factory=dict)
    registered_at: datetime | None = None

    @property
    def has_lineage(self) -> bool:
        """带血缘 tags 吗？—— **模板 revision 与任何手工注册的 revision 都没有**，故它们永不进清理候选。"""
        return bool(self.tags.get(names.TAG_VARIANT) and self.tags.get(names.TAG_DIGEST))


def _describe_revision(ecs, arn: str) -> tuple[dict, dict[str, str]]:
    """`DescribeTaskDefinition(include=["TAGS"])` → (taskDefinition, tags dict)。"""
    return _split_described(ecs.describe_task_definition(taskDefinition=arn, include=["TAGS"]))


def _split_described(resp: dict) -> tuple[dict, dict[str, str]]:
    """`DescribeTaskDefinition(include=["TAGS"])` 的响应 → (taskDefinition, tags dict)。"""
    tags = {t["key"]: t["value"] for t in (resp.get("tags") or [])}
    return resp["taskDefinition"], tags


def scan_family(ecs, family: str) -> list[RevisionInfo]:
    """family 的全部 ACTIVE revision（带 tags）。

    两个坑：**`familyPrefix` 是前缀匹配**（`gherkai-novaact-worker` 也会命中 `gherkai-novaact-worker-x`）→ 用
    describe 回来的 `family` 逐条核对；**必须翻页**（`nextToken`）——漏翻页会把翻到第二页的 revision 判成
    「不存在」，于是重复注册 + 漏清理。
    """
    out: list[RevisionInfo] = []
    token = None
    while True:
        kwargs = {"familyPrefix": family, "status": "ACTIVE"}
        if token:
            kwargs["nextToken"] = token
        resp = ecs.list_task_definitions(**kwargs)
        for arn in resp.get("taskDefinitionArns") or []:
            td, tags = _describe_revision(ecs, arn)
            if td.get("family") != family:
                continue
            out.append(RevisionInfo(arn=arn, tags=tags, registered_at=_parse_ts(td.get("registeredAt"))))
        token = resp.get("nextToken")
        if not token:
            return out


def _parse_ts(value) -> datetime | None:
    """tag 里的 ISO 串 / boto3 回来的 datetime → aware UTC datetime；空或读不懂 → None。"""
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    from gherkai_runtime import compose

    try:
        parsed = compose.parse_iso(str(value))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _lineage_tags(*, variant: str, version: str, digest: str, template_arn: str) -> list[dict[str, str]]:
    """注册时打的四个血缘 tag（ADR 0038 步 6）——清理对账、`list-workers`、重派生判定全看它们。"""
    return [
        {"key": names.TAG_VARIANT, "value": variant},
        {"key": names.TAG_VERSION, "value": version},
        {"key": names.TAG_DIGEST, "value": digest},
        {"key": names.TAG_TEMPLATE, "value": template_arn},
    ]


def _register_revision(ecs, *, template_arn: str, engine: str, image_ref: str, digest: str,
                       variant: str, version: str) -> str:
    """从**模板 revision** 复制出一个新 revision（镜像栏是 `image_ref`）+ 打血缘 tags → 新 revision ARN。

    **永远从模板复制、不抄「最近一次」revision**（ADR 0038 被拒方案）：最近一次可能是别人某个 variant 的、
    或模板改过后已过期。只读字段见 `_READ_ONLY_TASK_DEF_KEYS`，其余原样（`runtimePlatform` 因此自动继承 X86_64）。
    """
    td, _ = _describe_revision(ecs, template_arn)
    payload = {k: v for k, v in td.items() if k not in _READ_ONLY_TASK_DEF_KEYS}
    wanted = names.container_name(engine)  # container 名是 RunTask 逐字匹配的硬契约（ADR 0033）
    containers = payload.get("containerDefinitions") or []
    hit = [c for c in containers if c.get("name") == wanted]
    if not hit:
        raise WorkerCommandError(
            f"模板 revision {template_arn} 里没有名为 {wanted!r} 的 container——container 名是 RunTask 逐字匹配的"
            f"硬契约。模板不该被手工改过；重新运行 `gherkai deploy` 让 stack 重建模板。"
        )
    for c in hit:
        c["image"] = image_ref  # `repo@sha256:<digest>`——按 digest 引用（被拒方案「revision 按 tag 引用镜像」）
    resp = ecs.register_task_definition(
        **payload,
        tags=_lineage_tags(variant=variant, version=version, digest=digest, template_arn=template_arn),
    )
    return resp["taskDefinition"]["taskDefinitionArn"]


def _utc_now() -> datetime:
    """缺省的时钟函数（本机时钟，aware UTC）。打 tag 的时刻一律经可注入的时钟函数现读，测试据此守时刻的先后。"""
    return datetime.now(timezone.utc)


def _tag_retired_at(ecs, arn: str, *, clock) -> None:
    """给 `arn` 打 `gherkai:retired-at`，值在紧邻 `TagResource` 请求之前现读时钟（ADR 0038「不变量」清理 pass 条
    「时钟（实装要求）」段）：读时钟与发出请求之间不插入其它远程调用。异常原样抛给调用方。"""
    value = clock().isoformat()
    ecs.tag_resource(resourceArn=arn, tags=[{"key": names.TAG_RETIRED_AT, "value": value}])


def _untag_retired_at(ecs, arn: str) -> None:
    """无条件摘除 `arn` 上的 `gherkai:retired-at`（不先读它带不带；对不带的 revision 摘除预期成功返回、不改变它，
    ADR 0038 步 7 与实测项 10）。异常原样抛给调用方。"""
    ecs.untag_resource(resourceArn=arn, tagKeys=[names.TAG_RETIRED_AT])


def _clear_retired_at_after_mapping(ecs, arn: str, *, out) -> None:
    """写映射的一方摘除自己写进映射的 revision 上的 `gherkai:retired-at`：步 7 与重派生写映射成功之后、步 5 与重派生的
    跳过分支确认 ACTIVE 之后（ADR 0038「不变量」清理 pass 条「打 tag 与写映射的交错」段）。失败只警告：之后的清理 pass
    见到「仍在映射里却带着这个 tag」会再摘一次。"""
    try:
        _untag_retired_at(ecs, arn)
    except Exception as exc:
        out(f"警告：未能去掉在用 revision {_short_arn(arn)} 上的退休时刻（{exc}）。"
            f"不影响本次结果，之后 push-worker 或 gherkai deploy 末尾的清理会再去掉它。")


def _retire(ecs, arn: str, *, clock, out) -> None:
    """给被替换的旧 revision 打 `gherkai:retired-at`（**本次不删**，回收归清理 pass）。只在写映射成功之后调用，
    时刻在紧邻打 tag 的请求之前现读，于是值不早于它离开这条映射（ADR 0038 步 8）。

    打不上（无权限、限流等）只警告：回收不依赖这一步打上，它已不在映射里，之后的清理 pass 按孤儿给它补打、
    从补打的时刻起算静默期。
    """
    try:
        _tag_retired_at(ecs, arn, clock=clock)
    except Exception as exc:
        out(f"警告：给被替换的旧 revision 记录退休时刻失败（{arn}）：{exc}\n"
            f"     不影响本次结果：它已不在映射里，之后的清理会补记退休时刻，满 {_hours(RETIRE_QUIET_PERIOD)}后回收。")


def _is_active(ecs, arn: str) -> bool:
    """映射所指的 revision 仍为 ACTIVE 吗？（ADR 0038 步 5、重派生的跳过判据，与替换之前判断旧 revision 要不要打 tag。）

    返回 False 的只有两种情形：描述成功且状态不是 ACTIVE；或描述报 `ClientException`、而本次列举该 family 的 ACTIVE
    revision 未发现它（`compose.describe_revision_or_none_if_unlisted`，与提交侧 preflight「缺失的判定口径」同一判据），
    这时按本次未确认可用处理。后者不证明 revision 已被注销或删除：它若只是尚未出现在列举结果里，调用方会多注册一个
    revision，被替换的这个不打 tag，之后由清理 pass 按孤儿补打、满静默期后回收。其余读失败（描述报其余错误，如权限不足、
    限流、网络，这时不列举；描述报 `ClientException` 而它仍被列出；列举本身失败）原样抛出、命令失败——翻成缺失会让缺
    只读权限的部署方每次都新注册一个 revision。
    """
    from gherkai_runtime import compose

    resp = compose.describe_revision_or_none_if_unlisted(ecs, arn)
    return resp is not None and (resp.get("taskDefinition") or {}).get("status") == "ACTIVE"


def _register_unretired(ecs, *, template_arn: str, engine: str, image_ref: str, digest: str,
                        variant: str, version: str) -> str:
    """注册一个 revision，并在写映射之前再读一次：仍为 ACTIVE 且不带 `gherkai:retired-at` 才返回它的 ARN（ADR 0038 步 6）。

    不满足即重新注册一个、同样再读；第二次仍不满足时抛 `WorkerCommandError`（至多重新注册一次）。「不满足」含带着这个
    tag、已不是 ACTIVE，以及未确认可用（判据同 `_is_active`：描述报 `ClientException` 且本次 ACTIVE 列举未发现它，这不
    证明它已被注销或删除）；其余读失败原样抛出。出现的情形包括注册之后长时间停留、恰有一趟清理在注册之后读映射并给它
    补打，以及刚注册的 revision 尚未出现在查询结果里（这时会额外注册一个 revision）；被补打或额外注册的那个从未进入
    映射，满静默期后由清理照常回收。再读只看到那一刻的状态，其余交错由写映射之后的摘除与清理的最后核对处理（ADR 0038
    「不变量」清理 pass 条「注册与回收的竞争」段）。
    """
    from gherkai_runtime import compose

    for _attempt in range(2):
        arn = _register_revision(ecs, template_arn=template_arn, engine=engine, image_ref=image_ref,
                                 digest=digest, variant=variant, version=version)
        resp = compose.describe_revision_or_none_if_unlisted(ecs, arn, include=["TAGS"])
        if resp is None:
            continue
        td, tags = _split_described(resp)
        if td.get("status") == "ACTIVE" and names.TAG_RETIRED_AT not in tags:
            return arn
    raise WorkerCommandError(
        f"连续两次未能确认刚注册的 {engine}/{variant} revision 可用且未被标记为待清理，映射没有改动。"
        f"revision 可能已被标记为待清理、已注销或已删除，也可能尚未在查询结果中可见；请稍后重新执行这条命令。"
    )


# ---------------------------------------------------------------------------
# 清理 pass（ADR 0038「不变量」清理 pass 条）：映射引用 + 静默期 + 运行中 run 引用，机会式、无定时任务
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CleanupOutcome:
    """一次 pass 的结果：删掉的 revision + 留到下次的（ARN、原因）。**生产调用点（push-worker / deploy 末步）
    只看 pass 自己打的输出、丢弃本返回值**；它存在是为让测试直接断言各道判定，不必去解析打印文本。
    `list-workers` 不走这里——它是只读命令，待清理条目由 `_pending_cleanup` 现扫 family 产出机读行、文本渲染在
    `list_workers`（ADR 0038：清理 pass 机会式、由 push-worker/deploy 触发，无定时任务）。
    """

    deleted: tuple[str, ...] = ()
    kept: tuple[tuple[str, str], ...] = ()


def _reference_index_problem(ddb, table: str) -> str | None:
    """就绪检查（ADR 0038「不变量」清理 pass 条「引用检查」段②）：引用快照所读的状态分组索引 `IndexStatus` 为 `ACTIVE` 才放行。

    返回 None 即就绪；否则返回一句产品语言的原因，调用方据此留下全部候选并警告。缺失、`CREATING`、`UPDATING`、
    `DELETING` 与 `DescribeTable` 本身失败一律不放行：清理误判会让 run 后续的 job 起不来，跳过一趟只是让 revision
    多留到下一趟；也不依靠「`Query` 一个建立中的索引会报错」这一没有实测过的行为。
    """
    index = names.RUNS_STATUS_GROUP_GSI
    try:
        resp = ddb.describe_table(TableName=table)
    except Exception as exc:
        return f"读取运行记录表 {table} 的状态失败（{exc}）"
    for gsi in (resp.get("Table") or {}).get("GlobalSecondaryIndexes") or []:
        if gsi.get("IndexName") == index:
            status = gsi.get("IndexStatus")
            return None if status == "ACTIVE" else f"运行记录表的索引 {index} 尚未就绪（当前状态 {status or '未知'}）"
    return f"运行记录表上没有索引 {index}"


def _live_reference_snapshot(ddb, table: str) -> set[str]:
    """引用快照（ADR 0038「不变量」清理 pass 条「引用检查」段③）：未到终态的 run 引用的 revision ARN 全集。

    每趟一次、与候选数无关：对状态分组索引的 `live` 分组做一次 `Query`，只取 `worker_task_def_arns`，按
    `LastEvaluatedKey` 翻页读完、在内存里求并集。非终态 run 共用这一个分组（分组由 core 的 `status_group` 派生，
    ADR 0030 决定六），`pending` 换到 `running` 不改变索引键，所以一次查询就覆盖全部非终态，不按状态分区逐个读。
    不加过滤：过滤在读取之后才应用、不减少读量（被拒方案「对每个候选 revision 逐个 `Query` 并以 `contains` 过滤」）。
    **走 GSI 的 Query、绝不 Scan**：runs 表 `RETAIN`、无 TTL、随历史单调增长（被拒方案「清理靠全表 Scan runs 表」）。
    属性缺失的 item（本机后端 / 旧 definition）不贡献 ARN，语义即「未引用」。任何一页失败即原样抛出，调用方留下全部候选。
    """
    referenced: set[str] = set()
    token = None
    while True:
        kwargs = {
            "TableName": table,
            "IndexName": names.RUNS_STATUS_GROUP_GSI,
            "KeyConditionExpression": "#g = :g",
            # 属性名一律走命名真源、不写字面量
            "ExpressionAttributeNames": {"#g": names.STATE_STATUS_GROUP_ATTR, "#w": names.STATE_WORKER_TASK_DEF_ARNS_ATTR},
            "ExpressionAttributeValues": {":g": {"S": names.STATUS_GROUP_LIVE}},
            "ProjectionExpression": "#w",
        }
        if token:
            kwargs["ExclusiveStartKey"] = token
        resp = ddb.query(**kwargs)
        for item in resp.get("Items") or []:
            for entry in (item.get(names.STATE_WORKER_TASK_DEF_ARNS_ATTR) or {}).get("L") or []:
                if entry.get("S"):
                    referenced.add(entry["S"])
        token = resp.get("LastEvaluatedKey")
        if not token:
            return referenced


def _mapped_arns(ssm, prefix: str) -> set[str]:
    """全部版本、全部引擎的 `worker-image/*` 映射所引用的 revision ARN 集合（枚举失败原样抛出）。"""
    return {a for _e, _t, raw in _iter_image_params(ssm, prefix) for a in _mapped_arn(raw)}


def _skip_reclaim_warning(reason: str) -> str:
    return (f"警告：{reason}，无法确认哪些旧的 worker revision 仍在使用，这次没有回收旧的 revision；"
            f"下次 push-worker 或 gherkai deploy 会再试。")


@dataclass(frozen=True)
class _Mature:
    """成熟候选：判定成熟时读到的 `gherkai:retired-at` 原值随身带着，供注销之前的最后核对逐字比较。"""

    arn: str
    retired_at_raw: str


def cleanup_pass(*, prefix: str, engines, ssm, ecs, ddb, clock=None, out=print) -> CleanupOutcome:
    """回收不被任何映射引用的 revision（**机会式**：`push-worker` 末步与 `gherkai deploy` 第四步末各执行一次）。

    次序按 ADR 0038「不变量」清理 pass 条的「候选与静默期起点」与「引用检查」两段：
    1. 读映射之前记下时刻 t1，读全部版本的映射；读不全即整趟放弃（见下）。
    2. 逐引擎列 family，对每个带血缘 tags 的 ACTIVE revision 分类：在任一映射里的不是候选，带着 `gherkai:retired-at`
       就摘掉；不在映射里、还没有这个 tag 的，`registeredAt` 早于 t1 才补打（值在紧邻请求之前现读）、本趟留下，
       取不到或不早于 t1 的本趟不打；tag 满 `RETIRE_QUIET_PERIOD` 的是成熟候选，未满的留下。
    3. 没有成熟候选就不读 runs 表；有则先做就绪检查，再取一次引用快照。
    4. 本趟补打过或有成熟候选时重读一次映射：补打过的已在映射里即摘掉；成熟候选已在映射里的不注销、摘掉 tag。
    5. 其余成熟候选逐个最后核对：tag 与判定成熟时逐字相同、仍为 ACTIVE，才紧接着注销并删除。

    **不抛**：清理是收尾动作，失败不该把一次成功的 push/deploy 变成失败。就绪检查、快照或重读失败时全部候选留下并
    打一行警告；单个 revision 注销或删除失败只记进 `kept`（不打印），其中注销前就失败的下次 pass 会重试，已注销、
    删除未完成的则不会再被扫到。
    """
    clock = clock or _utc_now
    # t1：开始读映射之前的本机时刻，只用于「registeredAt 早于 t1 才补打」这道附加条件（ADR 0038「打 tag 与写映射的交错」段末）。
    t1 = clock()
    # **枚举映射失败就整趟放弃**（不是「当作没有映射继续」）：候选判据是「不在任何映射里」，读不全映射会把
    # 别人在用的 revision 全判成孤儿并补打，一小时后的下一趟就会批量回收。
    try:
        mapped = _mapped_arns(ssm, prefix)
    except Exception as exc:
        out(f"警告：读不全 worker 镜像映射（{exc}）——本次跳过清理"
            f"（读不全就分不清哪些还在用，宁可不清也不误删）。")
        return CleanupOutcome()
    # 静默期的比较用读完映射之后现读的时刻：不晚于实际时刻，算出的已过时长不会偏大。
    now = clock()
    kept: list[tuple[str, str]] = []
    tagged: list[str] = []          # 本趟补打过的（含 TagResource 报错的：报错不说明服务端没有打上）
    mature: list[_Mature] = []
    for engine in engines:
        family = names.task_def_name(prefix, engine)
        try:
            revisions = scan_family(ecs, family)
        except Exception as exc:
            out(f"警告：清理旧 revision 时列不出 {family} 的 revision：{exc}（留到下次清理）")
            continue
        for rev in revisions:
            if not rev.has_lineage:
                continue  # 模板 / 手工注册的 revision 永不进候选
            raw = rev.tags.get(names.TAG_RETIRED_AT)
            if rev.arn in mapped:
                if raw is not None:
                    # 仍在映射里却带着 tag：交错或早先版本留下的共用，一律摘掉（失败留到下一趟）
                    _try_untag(ecs, rev.arn)
                continue
            retired_at = _parse_ts(raw)
            if retired_at is None:
                # 还没有 tag（读不懂的值同样按没有处理，补打只会把起点推后，偏保守）
                if rev.registered_at is None or rev.registered_at >= t1:
                    kept.append((rev.arn, "未被映射引用，注册时刻取不到或不早于本次读取映射，本次不记录退休时刻"))
                    continue
                tagged.append(rev.arn)
                try:
                    _tag_retired_at(ecs, rev.arn, clock=clock)
                except Exception as exc:
                    kept.append((rev.arn, f"未被映射引用，记录退休时刻失败：{exc}"))
                    continue
                kept.append((rev.arn, "未被映射引用，本次记录退休时刻，满静默期之后回收"))
                continue
            if now - retired_at < RETIRE_QUIET_PERIOD:
                kept.append((rev.arn, f"已退休，未满 {_hours(RETIRE_QUIET_PERIOD)} 静默期"))
                continue
            mature.append(_Mature(arn=rev.arn, retired_at_raw=raw))
    if not mature and not tagged:
        return CleanupOutcome(kept=tuple(kept))

    runs_table = names.default_name(prefix, names.BASE_RUNS_TABLE)
    referenced: set[str] | None = None   # None 即就绪检查或快照没有通过：全部成熟候选留下
    if mature:
        problem = _reference_index_problem(ddb, runs_table)
        if problem is None:
            try:
                referenced = _live_reference_snapshot(ddb, runs_table)
            except Exception as exc:
                problem = f"查询运行记录表失败（{exc}）"
        if problem is not None:
            out(_skip_reclaim_warning(problem))

    # 映射重读：补打与快照都完成之后、注销之前，两件事共用这一次读（ADR 0038「候选与静默期起点」段的「重读」）
    try:
        mapped_again = _mapped_arns(ssm, prefix)
    except Exception as exc:
        # 重读失败：本趟补打的全部摘掉（下一趟重打，回收晚一趟），成熟候选全部留下
        for arn in tagged:
            _try_untag(ecs, arn)
        kept.extend((m.arn, "已退休，重新读取映射失败") for m in mature)
        if mature or tagged:
            out(_skip_reclaim_warning(f"重新读取 worker 镜像映射失败（{exc}）"))
        return CleanupOutcome(kept=tuple(kept))
    for arn in tagged:
        if arn in mapped_again:
            _try_untag(ecs, arn)
    # 成熟候选已在映射里的不注销、摘掉 tag：与就绪检查和快照的结果无关，任何一趟见到「仍在映射里却带着这个 tag」都摘
    unmapped: list[_Mature] = []
    for cand in mature:
        if cand.arn in mapped_again:
            _try_untag(ecs, cand.arn)
            kept.append((cand.arn, "已退休，但已重新被映射引用"))
        else:
            unmapped.append(cand)
    if referenced is None:
        kept.extend((m.arn, "已退休，本次无法确认是否仍有未到终态的 run 引用") for m in unmapped)
        return CleanupOutcome(kept=tuple(kept))

    deleted: list[str] = []
    for cand in unmapped:
        if cand.arn in referenced:
            kept.append((cand.arn, "已退休，仍有未到终态的 run 引用"))
            continue
        changed = _final_check(ecs, cand, out=out)
        if changed is not None:
            kept.append((cand.arn, f"已退休，{changed}"))
            continue
        # 最后核对与注销请求之间不插入其它远程调用（ADR 0038「引用检查」段⑤）。注销之后 revision 即为 INACTIVE，
        # 而 `scan_family` 只列 ACTIVE：删除这一步没完成的，后续 pass 不会再扫到它（起不了新 task、不产生费用，
        # 只是残留）。故原因串要分清「注销前就失败、下次 pass 重试」与「已注销、删除未完成」。
        deregistered = False
        try:
            ecs.deregister_task_definition(taskDefinition=cand.arn)
            deregistered = True
            resp = ecs.delete_task_definitions(taskDefinitions=[cand.arn])
        except Exception as exc:
            why = "已注销、删除未完成" if deregistered else "本次回收失败"
            kept.append((cand.arn, f"已退休，{why}：{exc}"))
            continue
        # 批量 API 的逐项失败放在 `failures` 里、不抛异常——不读它就会把没删掉的也算成回收
        failures = resp.get("failures") or []
        if failures:
            kept.append((cand.arn, f"已退休，已注销、删除未完成：{_failure_text(failures)}"))
            continue
        deleted.append(cand.arn)
    if deleted:
        out(f"清理：回收 {len(deleted)} 个 revision（" + "、".join(_short_arn(a) for a in deleted) + "）")
    return CleanupOutcome(deleted=tuple(deleted), kept=tuple(kept))


def _final_check(ecs, cand: _Mature, *, out) -> str | None:
    """注销之前的最后核对（ADR 0038「不变量」清理 pass 条「引用检查」段⑤）：再读一次，`gherkai:retired-at` 与判定成熟时
    逐字相同、且仍为 ACTIVE 才返回 None（放行注销）；否则打印一行警告、返回写进 `kept` 的原因。

    它只看得到核对时刻已可见的改动：替换的一步给共用 revision 写入新时刻、或补打的一趟摘掉自己的 tag，在核对之前可见时
    这一趟不注销；核对之后的改动不在它能识别的范围内（残余风险的总括）。
    """
    short = _short_arn(cand.arn)
    try:
        td, tags = _describe_revision(ecs, cand.arn)
    except Exception as exc:
        out(f"警告：读取 {short} 的当前状态失败（{exc}），这次不回收它；之后的清理会重新判断。")
        return f"注销之前读取失败：{exc}"
    current = tags.get(names.TAG_RETIRED_AT)
    if current is None:
        detail = "退休时刻已被去掉"
    elif current != cand.retired_at_raw:
        detail = "退休时刻已改变"
    elif td.get("status") != "ACTIVE":
        detail = "已不是 ACTIVE"
    else:
        return None
    out(f"警告：{short} 在这次清理期间有变化（{detail}），这次不回收它；之后的清理会按届时的状态重新判断。")
    return f"注销之前核对时{detail}"


def _try_untag(ecs, arn: str) -> None:
    """清理 pass 内的摘除：失败不打印、留到下一趟（ADR 0038「候选与静默期起点」段：「失败留到下一趟」）。"""
    try:
        _untag_retired_at(ecs, arn)
    except Exception:
        pass


def _mapped_arn(raw: str):
    """映射 JSON → 它引用的 revision ARN（读不懂 → 不产出）。

    **读不懂时产出空** 有安全含义：那条映射保护不了它的 revision，于是该 revision 会被判成孤儿。可接受——
    映射由本模块写、格式坏掉说明有人手改过 SSM；而静默期 + 运行中 run 引用检查仍然拦着。
    """
    try:
        data = json.loads(raw)
    except ValueError:
        return
    if isinstance(data, dict) and data.get("revision_arn"):
        yield data["revision_arn"]


def _failure_text(failures) -> str:
    """`DeleteTaskDefinitions` 的 `failures`（每项 `arn` / `reason` / `detail`）→ 一句原因（多项以「；」连接）。"""
    parts = []
    for f in failures:
        text = str(f.get("reason") or "未给出原因")
        if f.get("detail"):
            text += f"（{f['detail']}）"
        parts.append(text)
    return "；".join(parts)


def _hours(delta: timedelta) -> str:
    return f"{int(delta.total_seconds() // 3600)} 小时"


def _short_arn(arn: str) -> str:
    """`…:task-definition/gherkai-novaact-worker:7` → `gherkai-novaact-worker:7`（表格/日志用）。"""
    return arn.rsplit("/", 1)[-1] if "/" in arn else arn


# ---------------------------------------------------------------------------
# push-worker 八步
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PushOutcome:
    """一次「推一个引擎的一个 variant」的结果（deploy 的基础镜像同步复用同一条路径、同一个结果类型）。

    **不带 `template_arn`**（同 `gherkai_runtime.compose.WorkerResolution` 的取舍）：消费侧无人读，
    「从哪个模板派生」由 `gherkai deploy list-workers` 从 SSM/血缘 tags 直读展示。
    `engine` 是本条结果的引擎身份位（`sync_base` / `rederive_variants` 返回的是跨引擎平铺 list，靠它区分归属）；
    当前 `push_worker` 的成功输出用的是自己的局部 engine，故该字段暂无读点、**有意保留**。
    """

    engine: str
    variant: str
    tag: str
    digest: str
    revision_arn: str


def _ecr_login(aws: Aws, container) -> str:
    """ECR 登录（ADR 0038 步 3）→ **registry host**。

    令牌是 base64 的 `user:password`（ECR 恒 `AWS:<token>`，12 小时有效、重新运行即重登、幂等）。
    registry host 取 `proxyEndpoint`——**不用 STS 拼 `<account>.dkr.ecr.<region>`**：授权响应里已经带着权威值，
    少一个 API、少一个「account/region 从哪来」的分叉。
    """
    resp = aws.ecr.get_authorization_token()
    data = (resp.get("authorizationData") or [None])[0]
    if not data or not data.get("authorizationToken") or not data.get("proxyEndpoint"):
        raise WorkerCommandError("ECR 授权响应里没有令牌/registry（ecr:GetAuthorizationToken）——检查凭证与 region。")
    try:
        decoded = base64.b64decode(data["authorizationToken"]).decode("utf-8")
    except Exception as exc:
        raise WorkerCommandError(f"ECR 授权令牌解不开（base64）：{exc}") from exc
    user, _, password = decoded.partition(":")
    registry = data["proxyEndpoint"].removeprefix("https://").removeprefix("http://").rstrip("/")
    container.login(registry, user, password)
    return registry


def _tag_digest(ecr, repo: str, tag: str) -> str | None:
    """ECR 里某 tag 当前指向的 digest（不存在 → None）。**必须在 push 之前问**——push 之后 tag 已指向新 digest，
    「原 digest → 新 digest」就再也打印不出来了（ADR 0038 步 4「tag 可变，replace 与否交给使用方」）。"""
    try:
        resp = ecr.describe_images(repositoryName=repo, imageIds=[{"imageTag": tag}])
    except Exception as exc:
        # 只吞这两个码（tag 从未推过 / repo 还没建）——**不吞 None 码**：那会把任何编程错误也变成「没有旧 digest」。
        if _error_code(exc) in ("ImageNotFoundException", "RepositoryNotFoundException"):
            return None
        raise
    details = resp.get("imageDetails") or []
    return details[0].get("imageDigest") if details else None


def _template_arn(aws: Aws, *, prefix: str, engine: str) -> str:
    """读该引擎的模板 revision ARN（缺 → 让人先 `gherkai deploy`：它由 **stack 资源**写、随 cdk 事务）。"""
    path = names.ssm_worker_template_path(prefix, engine)  # 与 stack 的写侧同一个 helper，不重拼
    arn = _read_ssm(aws.ssm, path)
    if not arn:
        raise WorkerCommandError(
            f"读不到 {engine} 的 worker task-def 模板（SSM {path}）："
            f"这个参数由 stack 随 `gherkai deploy` 的 cdk 事务写入。\n"
            f"出路：先运行 `gherkai deploy --prefix {prefix} …`（本 prefix 的后端可能还没部署，"
            f"或上次部署用的 CLI 版本还没有 worker 镜像机制）。"
        )
    return arn


def _push_one(image: str, *, engine: str, variant: str, prefix: str, version: str,
              container, aws: Aws, clock, out) -> PushOutcome:
    """ADR 0038「push-worker 流程」步 2-8 的实现（步 1 的版本 skew 前置在 `push_worker` 里；deploy 的基础镜像同步
    与重派生共用本函数 / `_register_revision`，故这里**不做**任何 skew 判断）。"""
    try:
        tag = names.image_tag(version, variant)
    except ValueError as exc:  # variant 名或拼出的 tag 不合 docker/ECR 字符集
        raise WorkerCommandError(str(exc)) from exc
    repo = names.ecr_repo_name(prefix, engine)
    template_arn = _template_arn(aws, prefix=prefix, engine=engine)

    # 步 2：inspect 本地镜像——只取**存在**与**架构**（此时读到的 repo digest 不证明仓库里有这份内容，不取，见 container 模块头）
    info = container.inspect(image)
    if not info.exists:
        raise WorkerCommandError(
            f"本地找不到镜像 {image!r}：push-worker 只推已经构建好的镜像，不替你 build。\n"
            f"定制镜像的 Dockerfile 模板见 https://github.com/zhiyanliu/gherkai/blob/HEAD/docs/user-guide/cloud-backend.md 。"
        )
    if not info.matches_target_platform():
        if info.multi_platform:
            raise WorkerCommandError(
                f"镜像 {image!r} 在本机是多平台索引，但没有 linux/amd64 的内容可推（worker 固定 linux/amd64，云端 worker 任务是 X86_64）。\n"
                f"重 build 时只构建这一个平台：docker build --platform linux/amd64 -t {image} .\n"
                f"（容器引擎用的是 containerd 镜像存储：多平台镜像只有拉取或构建到本机的平台才有内容。）"
            )
        raise WorkerCommandError(
            f"镜像 {image!r} 的平台是 {info.platform}，worker 固定 linux/amd64（云端 worker 任务是 X86_64）。\n"
            f"重 build 时带上平台：docker build --platform linux/amd64 -t {image} .\n"
            f"（arm Mac 上漏 `--platform` 的后果本来要拖到 Fargate 启动期 `exec format error` 才暴露，"
            f"这里提前拦下。）"
        )

    previous_digest = _tag_digest(aws.ecr, repo, tag)  # 必须在 push 之前问
    registry = _ecr_login(aws, container)              # 步 3
    repo_uri = f"{registry}/{repo}"
    target = f"{repo_uri}:{tag}"

    # 步 4：tag + push；**digest 的唯一来源是推送成功之后再 inspect、按本 repo 挑**（push 失败由非零退出码抛错，走不到这里）
    container.tag(image, target)
    container.push(target)
    digest = digest_for_repo(container.inspect(target).repo_digests, repo_uri)
    if not digest:
        raise WorkerCommandError(
            f"推送后在 {target} 上取不到本仓库（{repo_uri}）的 digest，无法注册 revision："
            f"revision 按推送成功之后本仓库的 digest 引用镜像。\n"
            f"请确认这次 push 确实成功，再重新运行这条命令（推送与注册都是幂等的）。"
        )
    if previous_digest and previous_digest != digest:
        out(f"tag {tag} 原已存在：原 digest {names.short_digest(previous_digest)} → 新 digest {names.short_digest(digest)}"
            f"（重推同名 variant 放行；运行中 run 手里的旧 revision 按 digest 指着旧镜像层、不受影响）")

    # 步 5：查重。只在（模板 ARN、digest）二元组一致**且**映射所指的 revision 仍为 ACTIVE 时跳过注册；其余一律新注册，
    # 不从 family 里复用未被映射的 revision（ADR 0038 步 5 与被拒方案「孤儿复用」）
    mapping = read_mapping(aws.ssm, prefix=prefix, engine=engine, tag=tag, version=version)
    # 映射所指的 revision 是否仍为 ACTIVE：既是跳过的条件之一，也决定新注册之后要不要给它打 tag——未确认仍为 ACTIVE
    # 的不打（ADR 0038「不变量」清理 pass 条「注册与回收的竞争」段其三），二元组不一致的分支同样如此
    old_active = mapping is not None and _is_active(aws.ecs, mapping.revision_arn)
    if mapping and mapping.template_arn == template_arn and mapping.digest == digest:
        if old_active:
            # 跳过分支不经过步 7：此前某次交错留下的 tag 在这里就摘，不等到命令末尾的清理
            _clear_retired_at_after_mapping(aws.ecs, mapping.revision_arn, out=out)
            out(f"{engine}/{variant}：映射已指向用当前模板与本 digest 注册的 {_short_arn(mapping.revision_arn)}，跳过注册")
            return PushOutcome(engine=engine, variant=variant, tag=tag, digest=digest,
                               revision_arn=mapping.revision_arn)
        out(f"{engine}/{variant}：未能确认映射所指的 {_short_arn(mapping.revision_arn)} 仍可用"
            f"（可能已注销或已删除），重新注册一个")

    # 步 6：从模板注册新 revision（镜像栏按 digest 引用），写映射之前再读一次
    revision_arn = _register_unretired(aws.ecs, template_arn=template_arn, engine=engine,
                                       image_ref=f"{repo_uri}@{digest}", digest=digest,
                                       variant=variant, version=version)
    _write_mapping_and_retire(aws, prefix=prefix, engine=engine, tag=tag, template_arn=template_arn,
                              revision_arn=revision_arn, digest=digest, pushed_at=clock().isoformat(),
                              replaced=mapping.revision_arn if old_active else None,
                              clock=clock, out=out)
    return PushOutcome(engine=engine, variant=variant, tag=tag, digest=digest,
                       revision_arn=revision_arn)


def _write_mapping_and_retire(aws: Aws, *, prefix: str, engine: str, tag: str, template_arn: str, revision_arn: str,
                              digest: str, pushed_at: str, replaced: str | None, clock, out) -> None:
    """步 7 与步 8（push-worker 与重派生共用）：写映射 → 立即摘除写进映射的 revision 上的 `gherkai:retired-at` →
    给被替换的旧 revision 打 tag。

    `replaced` 为 None 即没有要退休的旧 revision（映射原本缺失，或未确认所指的 revision 仍为 ACTIVE：这样的不打，
    ADR 0038「不变量」清理 pass 条「注册与回收的竞争」段其三）。打 tag 的时刻在写映射成功之后、紧邻请求之前现读，
    于是不早于旧 revision 离开这条映射（同条「时钟（实装要求）」段）。
    """
    _put_ssm(aws.ssm, _mapping_path(prefix, engine, tag),
             _record_json(template_arn=template_arn, revision_arn=revision_arn, digest=digest, pushed_at=pushed_at))
    _clear_retired_at_after_mapping(aws.ecs, revision_arn, out=out)
    if replaced and replaced != revision_arn:
        _retire(aws.ecs, replaced, clock=clock, out=out)


def push_worker(image: str, *, engine: str, variant: str, set_default: bool = False,
                cli_version: str | None, prefix: str, region=None, profile=None, container,
                aws: Aws | None = None, clock=None, out=print) -> int:
    """`gherkai deploy push-worker <本地镜像> --engine <e> --variant <v> [--set-default]` → 退出码。

    八步见 ADR 0038「push-worker 流程」。**一次一个引擎**（两引擎镜像本就分别 build，被拒方案「一次收两个引擎」）。
    `clock` 是时钟函数（缺省本机时钟）：推送时间与退休时刻在用到的那一刻现读，不用命令开始时的时刻。
    """
    from gherkai_runtime import compose

    if aws is None:
        aws = _connect(region=region, profile=profile, out=out)
        if aws is None:
            return EXIT_PRECONDITION
    clock = clock or _utc_now

    # 步 1 的版本 skew 前置（ADR 0038「push-worker 与 list-workers 的前置」，沿用 0037 决策 7 三态、无放行口）
    blocked = _skew_gate(compose, prefix=prefix, cli_version=cli_version, ssm=aws.ssm, out=out)
    if blocked is not None:
        return blocked
    # 容器引擎探活**在 skew 之后**：被 skew 拦下的人（CLI 超前于后端）该去升后端，不该先被要求装 docker。
    probe = container.probe()
    if probe:
        out(probe)
        return EXIT_PRECONDITION

    try:
        result = _push_one(image, engine=engine, variant=variant, prefix=prefix, version=str(cli_version),
                           container=container, aws=aws, clock=clock, out=out)
        if set_default:
            _set_default(aws, prefix=prefix, variant=variant, version=str(cli_version),
                         engine=engine, out=out)
    except (WorkerCommandError, ContainerError) as exc:
        out(str(exc))
        return EXIT_PRECONDITION
    except Exception as exc:  # 凭证/权限/region/网络：对部署方是「先修凭证」，与前置同一类、不该抛 traceback
        out(f"AWS 调用失败：{exc}\n需要部署方权限（向 worker 镜像 ECR 仓库推送所需的 ecr:BatchCheckLayerAvailability/"
            f"InitiateLayerUpload/UploadLayerPart/CompleteLayerUpload/PutImage，另需 ecr:GetAuthorizationToken/DescribeImages、"
            f"ecs:RegisterTaskDefinition/ListTaskDefinitions/DescribeTaskDefinition/TagResource/UntagResource、"
            f"iam:PassRole、SSM 读写 /{prefix}backend/*、运行记录表的 DescribeTable 与索引 Query），以及可用的凭证/region。")
        return EXIT_PRECONDITION
    cleanup_pass(prefix=prefix, engines=names.ENGINES, ssm=aws.ssm, ecs=aws.ecs, ddb=aws.ddb,
                 clock=clock, out=out)
    out(f"\n✓ {engine} / variant {result.variant}\n"
        f"  tag       {result.tag}\n"
        f"  digest    {result.digest}\n"
        f"  revision  {result.revision_arn}\n"
        f"提交时用 --worker-variant {result.variant}")
    return EXIT_OK


def _skew_gate(compose, *, prefix: str, cli_version: str | None, ssm, out) -> int | None:
    """版本 skew 前置：block → 以退出码 2 结束（无放行口）；warn/skip → 打一行继续；ok → 静默；**读不到戳（凭证/权限）
    也以退出码 2 结束**（对部署方是「先修凭证」，与前置同一类）。

    判据与措辞的单一真源是 `compose.check_backend_skew`（ADR 0037 决策 7）。**block 时补一句本命令专属的出路**：
    push-worker 住 `gherkai-deploy-aws`，临时用同版本 CLI 要带 extra（`gherkai[deploy-aws]==X.Y.Z`），
    compose 那句给的是不带 extra 的形态；戳由 `check_backend_skew` 一并返回、不二次读。
    """
    try:
        verdict, message, stamp = compose.check_backend_skew(prefix=prefix, cli_version=cli_version, ssm=ssm)
    except Exception as exc:
        # 读戳失败（凭证/权限/region/网络）——`read_backend_version` 有意把这类异常抛给入口前端决定退出码，
        # 本模块就是那个前端：归到「前置失败」这一类、不抛 traceback（同 `cli._guard_vpc_spec` 的口径）。
        out(f"读取后端版本戳失败（SSM 参数 {names.ssm_path(prefix, names.BACKEND_VERSION_KEY)}）：{exc}\n"
            f"需要可用的凭证与 region（--region / AWS_REGION / --profile），以及 ssm:GetParameter 权限。")
        return EXIT_PRECONDITION
    if verdict != compose.SKEW_BLOCK:
        if message:
            out(message)
        return None
    out(message)
    out(f"本命令随 gherkai[deploy-aws] 扩展安装，临时使用同版本 CLI 时写作：uvx --from 'gherkai[deploy-aws]=={stamp}' gherkai deploy …\n"
        f"不提供放行选项的原因：worker 镜像标签含 CLI 版本，CLI 领先于后端时推送的镜像不会被后端使用，"
        f"提交者仍会被要求先升级后端。")
    return EXIT_PRECONDITION


def _set_default(aws: Aws, *, prefix: str, variant: str, version: str, engine: str, out) -> None:
    """`--set-default`：写默认指针 + **该 variant 在其它引擎尚无镜像时警告不拦**（ADR 0038 步 7）。

    不硬要求每个引擎都有（被拒方案「`--set-default` 硬要求 variant 在每个引擎都存在」）：与 preflight
    「按本 run 用到的引擎判」同一判据，单引擎团队不该被逼着凭空推另一个引擎的镜像。
    """
    _put_ssm(aws.ssm, names.ssm_path(prefix, names.WORKER_DEFAULT_KEY), variant)
    out(f"默认指针已设为 {variant}（提交时不给 --worker-variant 即用它）")
    tag = names.image_tag(version, variant)
    for other in names.ENGINES:
        if other == engine:
            continue
        if read_mapping(aws.ssm, prefix=prefix, engine=other, tag=tag, version=version) is None:
            out(f"警告：variant `{variant}` 在 {other} 尚无镜像（tag {tag}），用到该引擎的 run 会在提交前检查被拦。"
                f"\n     需要就为 {other} 也推一份：gherkai deploy push-worker <镜像> --engine {other} "
                f"--variant {variant}")


# ---------------------------------------------------------------------------
# `gherkai deploy` 的 worker 镜像四步（第 1 步是 stack 资源；后三步 + 清理在这里）
# ---------------------------------------------------------------------------

def sync_base(*, prefix: str, engines, version: str, container, aws: Aws, clock, out) -> list[PushOutcome]:
    """第 2 步：从 GHCR 拉当前版本基础镜像、走 push-worker 同一条内部路径推成 `<版本>-base`。

    **非纯发行版（`.dev`/`.post`/本地段）没有 GHCR 基础镜像**——那些版本由 tag 之后的 commit 派生、不可能发布
    （ADR 0037 决策 2b），拉必然失败。此时打一条明确警告、**跳过本步继续第 3/4 步**：contributor 在自己的 dev
    树上部署是正常用法，把 deploy 变成硬失败会逼他们绕过命令手工推。
    """
    from gherkai_runtime import compose

    if not compose.is_pure_release(version):
        out(f"警告：CLI 版本 {version} 不是纯发行版（含 .dev/.post/本地段）——GHCR 上不存在对应基础镜像，"
            f"跳过基础镜像同步。\n"
            f"     dev 版要能运行：本地 build 一份镜像后 `gherkai deploy push-worker <镜像> --engine <e> "
            f"--variant base`（默认指针缺失时会初始化为 base；已设为别的 variant 时，提交时用 "
            f"`--worker-variant base`，或推那个同名 variant）。")
        return []
    results = []
    for engine in engines:
        ref = f"{GHCR_BASE_IMAGE.format(engine=engine)}:{version}"
        out(f"\n== 基础镜像同步 {engine}：{ref} ==")
        try:
            container.pull(ref, platform="linux/amd64")
        except ContainerError as exc:
            raise WorkerCommandError(
                f"{exc}\n拉不到基础镜像 {ref}：PyPI 已发、镜像还没发完的半发布态是已知情形——"
                f"等镜像发布完成后再 `gherkai deploy`（幂等收敛）。"
            ) from exc
        results.append(_push_one(ref, engine=engine, variant=BASE_VARIANT, prefix=prefix, version=version,
                                 container=container, aws=aws, clock=clock, out=out))
    return results


def init_default_pointer(*, prefix: str, aws: Aws, out) -> str:
    """第 3 步：默认指针缺失 → `base`；**已存在则不动**（ADR 0038「默认指针不自动重置」——它记的是团队意图，
    升级时重置回 base 会抹掉它，被拒方案有专条）。"""
    current = read_default_variant(aws.ssm, prefix)
    if current:
        out(f"已保留默认 worker 镜像 variant `{current}`（部署不改动已有的默认设置）")
        return current
    _put_ssm(aws.ssm, names.ssm_path(prefix, names.WORKER_DEFAULT_KEY), BASE_VARIANT)
    out(f"默认 worker 镜像 variant 初始化为 `{BASE_VARIANT}`（官方基础镜像，未定制）")
    return BASE_VARIANT


def rederive_variants(*, prefix: str, engines, version: str, aws: Aws, clock, out) -> list[PushOutcome]:
    """第 4 步：用**当前模板 + 映射里记录的 digest** 重注册需要更新的 variant 的 revision（镜像一个字节不动）。

    为何必须（ADR 0038 被拒方案「deploy 改模板后不重派生既有 variant」）：revision 是不可变快照、无继承——
    deploy 调了 cpu / stopTimeout 后，旧 variant 会一直以旧配置运行直到有人想起来重推。幂等。
    跳过的判据同 push-worker 步 5：映射记录的模板 ARN 与当前模板一致、且所指 revision 仍为 ACTIVE 才跳过，并在确认之后
    摘一次 `gherkai:retired-at`；未能确认所指 revision 仍为 ACTIVE 时按映射缺失处理、新注册，且不给它打 tag。**不在 family 里
    匹配已有的 revision**（被拒方案「孤儿复用」）：中断在注册与写映射之间时，重新执行再注册一批，前一批由清理回收。
    `pushed_at` **保留原值**：它记的是镜像推上去的时刻，重派生没碰镜像。
    """
    results: list[PushOutcome] = []
    # 全部版本的映射只枚举一次（要翻页），各引擎的筛选共用：每个引擎只改自己那些映射参数，故这份快照与
    # 逐引擎重读等价。
    params = list(_iter_image_params(aws.ssm, prefix))
    for engine in engines:
        template_arn = _template_arn(aws, prefix=prefix, engine=engine)
        # repo URI 只依赖（模板，引擎），故**每引擎至多算一次**、到第一个需要注册的 variant 才算：放进循环会让
        # 待重派生的每个 variant 多打一次模板 describe，整个引擎无事可做时连这一次也不打。
        repo_uri: str | None = None
        for mapping in current_version_mappings(params, engine=engine, version=version):
            # 同 push-worker 步 5：既是跳过的条件之一，也决定替换之后要不要给旧 revision 打 tag（未确认仍为 ACTIVE 的不打）
            old_active = _is_active(aws.ecs, mapping.revision_arn)
            if mapping.template_arn == template_arn and old_active:
                _clear_retired_at_after_mapping(aws.ecs, mapping.revision_arn, out=out)
                continue
            if repo_uri is None:
                repo_uri = _repo_uri_from_template(aws.ecs, template_arn=template_arn, engine=engine)
            new_arn = _register_unretired(aws.ecs, template_arn=template_arn, engine=engine,
                                          image_ref=f"{repo_uri}@{mapping.digest}", digest=mapping.digest,
                                          variant=mapping.variant, version=version)
            _write_mapping_and_retire(aws, prefix=prefix, engine=engine, tag=mapping.tag, template_arn=template_arn,
                                      revision_arn=new_arn, digest=mapping.digest, pushed_at=mapping.pushed_at,
                                      replaced=mapping.revision_arn if old_active else None, clock=clock, out=out)
            if old_active:
                out(f"{engine}/{mapping.variant} 的 worker 运行配置已按本次部署更新为 {_short_arn(new_arn)}"
                    f"（旧配置 {_short_arn(mapping.revision_arn)} 已标记待清理）")
            elif mapping.template_arn == template_arn:
                out(f"{engine}/{mapping.variant} 原用的 worker 运行配置 {_short_arn(mapping.revision_arn)} 未能确认仍可用"
                    f"（可能已注销或已删除），已按记录的镜像重新注册为 {_short_arn(new_arn)}")
            else:
                out(f"{engine}/{mapping.variant} 的 worker 运行配置已按本次部署更新为 {_short_arn(new_arn)}")
            results.append(PushOutcome(engine=engine, variant=mapping.variant, tag=mapping.tag,
                                       digest=mapping.digest, revision_arn=new_arn))
    if not results:
        out("各 variant 的 worker 运行配置已是最新，无需更新")
    return results


def _repo_uri_from_template(ecs, *, template_arn: str, engine: str) -> str:
    """模板 container 的镜像栏 → 本引擎的 ECR repo URI（`<registry>/<repo>`）。

    重派生**不推镜像、不登录**，故 registry host 只能从这里学：模板的镜像栏是 CDK 建的 `<repo-uri>:latest`
    占位（ADR 0038「模板 revision」）。`:` 只在最后一段（ECR host 无端口）才是 tag 分隔符，故按最后一个 `/` 之后找。
    """
    td, _ = _describe_revision(ecs, template_arn)
    wanted = names.container_name(engine)
    for c in td.get("containerDefinitions") or []:
        if c.get("name") != wanted:
            continue
        ref = str(c.get("image") or "")
        ref = ref.split("@", 1)[0]                       # 万一模板已是 digest 形态
        head, _, last = ref.rpartition("/")
        return f"{head}/{last.split(':', 1)[0]}" if head else last.split(":", 1)[0]
    raise WorkerCommandError(
        f"模板 revision {template_arn} 里没有名为 {wanted!r} 的 container，取不到 ECR repo——重新运行 `gherkai deploy`。")


def run_deploy_steps(*, prefix: str, version: str, container, engines=None, region=None, profile=None,
                     aws: Aws | None = None, clock=None, out=print) -> int:
    """`gherkai deploy` 的 worker 镜像第 2/3/4 步 + 清理 pass（第 1 步是 stack 资源、随 cdk 事务）。

    **不做版本 skew 前置**（ADR 0038）：deploy 本身就是改戳的动作——前置在 cdk 前会把自己拦死、在 cdk 后恒真。
    失败 → 以退出码 1 结束且点明「stack 已生效」：cdk 已经改了账户，退出码 2（即什么都没发生）会误导。
    """
    from gherkai_runtime import compose

    if aws is None:
        aws = _connect(region=region, profile=profile, out=out)
        if aws is None:
            # 本函数只在 cdk 成功之后执行，故按本函数契约（见 docstring）给退出码 1 并点明 stack 已生效：
            # 账户已被改动，退出码 2（即什么都没发生）会误导。
            out("stack 已生效；worker 镜像步骤未完成——重新运行 `gherkai deploy` 幂等收敛。")
            return EXIT_FAILED
    clock = clock or _utc_now
    engines = tuple(engines or names.ENGINES)

    # 容器引擎只有第 2 步（同步基础镜像 pull/push）用；非纯发行版本步会整步跳过（见 `sync_base`），此时不探活——
    # contributor 在没装 docker 的机器上 deploy dev 版，第 3/4 步照样收敛，不为用不到的东西给退出码 1。
    # （纯发行版则 deploy 的机器必须有容器引擎；「免容器引擎的 registry 直拷」是 ADR 0038 重议闸门里的加法。）
    if compose.is_pure_release(version):
        probe = container.probe()
        if probe:
            out(f"{probe}\nstack 已生效，但同步基础镜像要 pull/push——deploy 的机器需要容器引擎。\n"
                f"装好后重新运行 `gherkai deploy`（幂等收敛，不会重复注册）。")
            return EXIT_FAILED
    try:
        sync_base(prefix=prefix, engines=engines, version=version, container=container,
                  aws=aws, clock=clock, out=out)
        init_default_pointer(prefix=prefix, aws=aws, out=out)
        rederive_variants(prefix=prefix, engines=engines, version=version, aws=aws, clock=clock, out=out)
    except Exception as exc:  # 含 AWS 侧异常：cdk 已改过账户，一律归「四步失败」这一类、不抛 traceback
        out(f"{exc}\nstack 已生效；worker 镜像步骤未完成——重新运行 `gherkai deploy` 幂等收敛。")
        return EXIT_FAILED
    cleanup_pass(prefix=prefix, engines=engines, ssm=aws.ssm, ecs=aws.ecs, ddb=aws.ddb, clock=clock, out=out)
    return EXIT_OK


# ---------------------------------------------------------------------------
# list-workers
# ---------------------------------------------------------------------------

def list_workers(*, prefix: str, cli_version: str | None, engines=None, region=None, profile=None,
                 aws: Aws | None = None, out=print, err=None, as_json: bool = False) -> int:
    """按引擎列**当前版本**的 variant（tag / digest / 推送时间 / revision）+ 默认指针 + 待清理与孤儿。

    「当前版本」指运行这条命令的 CLI 自身版本（与 push-worker 打 tag 用的同一个）——故本命令同样过 skew 前置：
    版本对不上时列出来的是另一个命名空间的东西，比不列更误导。
    """
    from gherkai_runtime import compose

    engines = tuple(engines or names.ENGINES)
    err = err or (lambda *a: print(*a, file=sys.stderr))
    # diag 在建句柄**之前**定好：连不上 AWS 的诊断与 skew 提示同属诊断面，--json 下同样不能污染那个 JSON 文档
    diag = err if as_json else out  # --json 下 stdout 只留一个 JSON 文档：skew 提示 / 读失败诊断走 stderr（ADR 0041 决策三）
    if aws is None:
        aws = _connect(region=region, profile=profile, out=diag)
        if aws is None:
            return EXIT_PRECONDITION
    blocked = _skew_gate(compose, prefix=prefix, cli_version=cli_version, ssm=aws.ssm, out=diag)
    if blocked is not None:
        return blocked
    version = str(cli_version)
    try:
        default = read_default_variant(aws.ssm, prefix)
        # 全部版本的映射只枚举一次（GetParametersByPath 每页 10 条要翻页）：孤儿对账用的 `mapped` 与
        # 各引擎的当前版本筛选共用这一份物化结果——同 cleanup_pass 的做法（枚举一次、逐引擎对账）
        params = list(_iter_image_params(aws.ssm, prefix))
        mapped = {a for _e, _t, raw in params for a in _mapped_arn(raw)}
        doc: dict = {"prefix": prefix, "version": version, "default_variant": default, "engines": {}}
        for engine in engines:
            family = names.task_def_name(prefix, engine)
            mappings = current_version_mappings(params, engine=engine, version=version)
            doc["engines"][engine] = {
                "family": family, "ecr_repo": names.ecr_repo_name(prefix, engine),
                "variants": [{"variant": m.variant, "tag": m.tag, "digest": m.digest, "pushed_at": m.pushed_at,
                              "revision_arn": m.revision_arn, "template_arn": m.template_arn} for m in mappings],
                "pending_cleanup": _pending_cleanup(aws, family=family, mapped=mapped),
            }
    except Exception as exc:  # 读侧命令：连不上/没权限也别抛 traceback（同 provider 其余读侧的口径）
        diag(f"读不到 worker 镜像状态（SSM/ECS）：{exc}")
        return EXIT_PRECONDITION
    if as_json:  # 机读形态（ADR 0041 决策三）：同一份 doc、不另拼
        out(json.dumps(doc, ensure_ascii=False, indent=2))
        return EXIT_OK
    out(f"prefix {prefix}    版本 {version}    默认 variant {default or '（未初始化——运行一次 gherkai deploy）'}"
        + ("（表中以 * 标出）" if default else ""))
    for engine, info in doc["engines"].items():
        out(f"\n== {engine}（family {info['family']}，ECR repo {info['ecr_repo']}）==")
        variants = info["variants"]
        if not variants:
            out("  （本版本还没有任何 variant——`gherkai deploy` 会同步基础镜像，或 push-worker 推一个）")
        else:
            rows = [[v["variant"] + (" *" if v["variant"] == default else ""), v["tag"],
                     names.short_digest(v["digest"]), _pushed_at_human(v["pushed_at"]), _short_arn(v["revision_arn"])]
                    for v in variants]
            out(render_table(["variant", "tag", "digest", "推送时间（UTC）", "revision"], rows))
        # 待清理条目分已退休与孤儿两类、字段不同，不构成同结构的清单，按 ADR 0047 保持逐行输出、不手工对齐列。
        for item in info["pending_cleanup"]:
            if item["reason"] == "retired":
                out(f"  待清理 {_short_arn(item['revision_arn'])}  已退休 {item['retired_at']}"
                    f"（variant {item['variant']}）")
            else:
                out(f"  待清理 {_short_arn(item['revision_arn'])}  孤儿：无任何版本的映射引用"
                    f"（variant {item['variant']}，注册于 {item['registered_at'] or '?'}）")
    return EXIT_OK


def _pending_cleanup(aws: Aws, *, family: str, mapped: set) -> list[dict]:
    """待清理条目：带血缘 tags、不在任何版本的映射里的 ACTIVE revision，判据与清理 pass 的候选判据是同一份
    （`mapped` 是全部版本映射引用的 revision ARN 集合，调用方算一次）。列出来才可解释「为什么 family 里 revision
    比 variant 多」。机读行 {revision_arn, reason: retired|orphan, variant, retired_at, registered_at}；文本渲染在 list_workers。

    `reason` 是 retired / orphan 闭集（ADR 0038「命令族」节 list-workers 条）：带 `gherkai:retired-at` 的为 retired，
    `retired_at` 即静默期的起点，替换映射时打上的与清理 pass 补打的不区分；还没有这个 tag 的为 orphan（`retired_at`
    为 null），之后的清理在它的注册时刻早于那一趟读映射的时刻时给它补打。仍在某个映射里的 revision 不列，即使它带着
    `retired-at`：那是之后的清理会摘掉的 tag，它是在用的 revision。"""
    items: list[dict] = []
    for rev in scan_family(aws.ecs, family):
        if not rev.has_lineage or rev.arn in mapped:
            continue
        # registered_at 是 datetime → 转 ISO 串：doc 要能 json.dumps（真 AWS 返 registeredAt，moto 不返——单测照不出）
        reg = rev.registered_at.isoformat() if rev.registered_at else None
        retired_at = rev.tags.get(names.TAG_RETIRED_AT) or None
        items.append({"revision_arn": rev.arn, "reason": "retired" if retired_at else "orphan",
                      "variant": rev.tags.get(names.TAG_VARIANT, "?"), "retired_at": retired_at,
                      "registered_at": reg})
    return items


def _pushed_at_human(iso: str | None) -> str:
    """推送时间的人读形态：`2026-09-29T07:09:14.961520+00:00` → `2026-09-29 07:09`（换算到 UTC、到分钟）。
    机读形态（`--json`）仍是完整的 ISO 串；缺值给 `-`；解析不了的原样返回、不抛。"""
    if not iso:
        return "-"
    dt = _parse_ts(iso)  # 与 tag 时刻同一个解析入口；不带时区的按 UTC 读
    return iso if dt is None else dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M")


