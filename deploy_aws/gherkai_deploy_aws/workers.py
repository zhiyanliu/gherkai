"""worker 镜像交付的云端半边（ADR 0038）：`push-worker` 八步 / `list-workers` / `gherkai deploy` 的四步 + 清理 pass。

**归属**：全部云端写操作（推 ECR、注册 task-def revision、写 SSM 指针）都是**部署变更**，故住
`gherkai-deploy-aws`、不住 CLI 本体（ADR 0038「命令族」）。镜像**构建**不在这里、也不在任何 gherkai 命令里
（三行定制镜像模板见 `deploy_aws/README.md`）——被拒方案「gherkai 拥有定制镜像的构建」。

## 概念一句话（细节见 ADR 0038「概念模型」）

一个 **variant** = 一套具名确定性 step 集 = 一个定制镜像，落 ECR tag `<CLI 版本>-<variant>`，并对应一个
task-def **revision**（从 deploy 登记的**模板** revision 复制、镜像栏换成 `repo@sha256:<digest>`）。run 起
task 时用的是 revision（不可变快照），故重推同名 variant 不会把在跑的 run 换掉镜像。

## 三条正确性支点（改这个文件前先读）

- **digest 只在推送后取，且要按仓库挑**：见 `container` 模块头两条事实。
- **幂等 = 每步先查再做**：`RegisterTaskDefinition` 不幂等，故以（模板 ARN、digest）二元组查重、孤儿 revision
  按血缘 tags 复用；SSM 写是覆盖语义；ECR push 同 digest 天然无操作。中断后重跑收敛，不堆垃圾 revision。
- **删 revision 前有两道闸**：退休满 `RETIRE_QUIET_PERIOD` + 无未到终态的 run 引用（`cleanup_pass`）。
  `DeregisterTaskDefinition` 让 revision 再也起不了新 task（且注销后最多 10 分钟才生效），detached run 逐 job
  起 task——删早了剩余 job 全起不来（ADR 0038 被拒方案「重派生/重推后立即删旧 revision」）。

## 退出码

`push-worker` / `list-workers` 的用户可修失败 → **2**（对齐 provider 既有前置口径）。
`gherkai deploy` 的四步失败 → **1** 且提示「stack 已生效；重跑 `gherkai deploy` 幂等收敛」（ADR 0038
「四步的失败语义」）——cdk 已经改了账户，压成 2 会让人以为什么都没发生。
"""
from __future__ import annotations

import base64
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from gherkai_deploy_aws import names
from gherkai_deploy_aws.container import ContainerError, digest_for_repo

EXIT_OK = 0
EXIT_FAILED = 1        # cdk 成功、四步失败（账户已被改动，见模块头「退出码」）
EXIT_PRECONDITION = 2  # 用户可修的前置/校验失败

# 基底同步进 ECR 的那份固定叫 `base`（ADR 0038「概念模型」），也是默认指针的初始值。
BASE_VARIANT = "base"
# 维护者 CI 发布的基底镜像（ADR 0037 决策 5；`<engine>` + `:<版本>`）。**运行时不直接拉它**——task-def 只指
# 使用方自己账号的 ECR（被拒方案「task-def 指向 GHCR 直接拉基底」），这里只在 deploy 的基底同步里 pull 一次。
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
    """用户可修的失败（`str(exc)` 即给人看的整句）。**退码归调用方**：push-worker 退 2、deploy 四步退 1。"""


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
    """SSM `worker-image/<engine>/<tag>` 的一条映射（JSON 四键 + 从键名反推的 engine/tag/variant）。"""

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
    """映射记录的 JSON——**四个键名是跨组件契约**（提交侧 preflight 与推进器兼容路径都读它，ADR 0038）。"""
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
    root = names.ssm_path(prefix, "worker-image")
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


def current_version_mappings(ssm, *, prefix: str, engine: str, version: str) -> list[ImageMapping]:
    """某引擎**当前版本**的全部 variant 映射（按 variant 名排序）。旧版本的留作历史、不参与当前版本解析。"""
    out: list[ImageMapping] = []
    for eng, tag, raw in _iter_image_params(ssm, prefix):
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

    @property
    def retired_at(self) -> datetime | None:
        return _parse_ts(self.tags.get(names.TAG_RETIRED_AT))


def _describe_revision(ecs, arn: str) -> tuple[dict, dict[str, str]]:
    """`DescribeTaskDefinition(include=["TAGS"])` → (taskDefinition, tags dict)。"""
    resp = ecs.describe_task_definition(taskDefinition=arn, include=["TAGS"])
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
    """从**模板 revision** 复制出一个新 revision（镜像栏 = `image_ref`）+ 打血缘 tags → 新 revision ARN。

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
            f"硬契约。模板不该被手工改过；重跑 `gherkai deploy` 让 stack 重建模板。"
        )
    for c in hit:
        c["image"] = image_ref  # `repo@sha256:<digest>`——按 digest 引用（被拒方案「revision 按 tag 引用镜像」）
    resp = ecs.register_task_definition(
        **payload,
        tags=_lineage_tags(variant=variant, version=version, digest=digest, template_arn=template_arn),
    )
    return resp["taskDefinition"]["taskDefinitionArn"]


def _retire(ecs, arn: str, *, now: datetime, out) -> bool:
    """给被替换的旧 revision 打 `gherkai:retired-at`（**本次不删**，删归清理 pass 的两道闸）。

    打不上（revision 已被删/无权限）→ 警告不拦：映射已经指向新 revision，旧的下一次 pass 会以**孤儿**
    身份（不在任何映射里 + 带血缘 tags）被同样处置，退休时刻取其 `registeredAt`。
    """
    try:
        ecs.tag_resource(resourceArn=arn, tags=[{"key": names.TAG_RETIRED_AT, "value": now.isoformat()}])
        return True
    except Exception as exc:
        out(f"警告：给旧 revision 打退休 tag 失败（{arn}）：{exc}\n"
            f"     不拦——它已不在映射里，下次清理 pass 会按孤儿处置。")
        return False


# ---------------------------------------------------------------------------
# 清理 pass（ADR 0038「不变量·清理 pass」）：静默期 + 在跑 run 安全阀，机会式、无定时任务
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CleanupOutcome:
    """一次 pass 的结果：删掉的 revision + 留到下次的（ARN、原因）。**生产调用点（push-worker / deploy 末步）
    只看 pass 自己打的输出、丢弃本返回值**；它存在是为让测试直接断言两道闸（静默期 + 在跑 run 引用）的判定，
    不必去解析打印文本。`list-workers` 不走这里——它是只读命令，待清理/孤儿由 `_print_pending_cleanup`
    现扫 family 列出（ADR 0038：清理 pass 机会式、由 push-worker/deploy 触发，无定时任务）。
    """

    deleted: tuple[str, ...] = ()
    kept: tuple[tuple[str, str], ...] = ()


def _non_terminal_statuses() -> list[str]:
    """未到终态的 run 级 status 全集（`Status` - `TERMINAL_STATUSES`，至少含 `pending`）。

    **从 core 的枚举派生、不在此写死名单**：新增前置态时（ADR 0031 的 `_PRE_TERMINAL` 是那处的真源）安全阀
    自动覆盖；写死会让新态的 run 被清理误判成「没人引用」。`gherkai_core` 经 `gherkai-runtime` 的 `==` lockstep
    传递可用（ADR 0037 决策 2b）。
    """
    from gherkai_core.model import TERMINAL_STATUSES, Status

    return sorted(s.value for s in set(Status) - set(TERMINAL_STATUSES))


def _referenced_by_live_run(ddb, table: str, arn: str) -> bool:
    """有未到终态的 run 引用这个 revision 吗？—— **走 status GSI 的 Query + `contains` 过滤，绝不 Scan**。

    访问路径定死（ADR 0038 不变量）：run 用到的 revision ARN 在 `create_run` 时同时写成 STATE item 的顶层属性
    `worker_task_def_arns`（list），runs 表按 `status` 建稀疏 GSI（只有 STATE 带顶层 status）。
    runs 表 `RETAIN`、无 TTL、随历史单调增长——Scan 成本无上界（被拒方案「清理靠全表 Scan runs 表」）。
    属性缺失的 item（local 档 / 旧 definition）`contains` 天然不匹配，语义即「未引用」。
    """
    for status in _non_terminal_statuses():
        token = None
        while True:
            kwargs = {
                "TableName": table,
                "IndexName": names.RUNS_STATUS_GSI,
                "KeyConditionExpression": "#s = :s",
                "FilterExpression": "contains(#w, :arn)",
                # `status` 是 DDB 保留字；`#w` 只为可读（属性名走命名真源、不写字面量）
                "ExpressionAttributeNames": {"#s": "status", "#w": names.STATE_WORKER_TASK_DEF_ARNS_ATTR},
                "ExpressionAttributeValues": {":s": {"S": status}, ":arn": {"S": arn}},
                "ProjectionExpression": "run_id",  # 只要「有没有」，不搬 STATE 正文
            }
            if token:
                kwargs["ExclusiveStartKey"] = token
            resp = ddb.query(**kwargs)
            if resp.get("Items"):
                return True
            token = resp.get("LastEvaluatedKey")
            if not token:
                break
    return False


def cleanup_pass(*, prefix: str, engines, ssm, ecs, ddb, now: datetime, out=print) -> CleanupOutcome:
    """回收退休/孤儿 revision（**机会式**：`push-worker` 末步与 `gherkai deploy` 第四步末各跑一次）。

    候选两类（ADR 0038）：
    - **已退休**：带 `gherkai:retired-at`（被重推/重派生替换掉的那些）。
    - **孤儿**：带血缘 tags、ACTIVE、却不在 SSM **任何版本**的 `worker-image/*` 映射里 —— 覆盖「上次中断在
      注册与写 SSM 之间」与「两人并发推同名 variant，先写者的映射被顶掉」。退休时刻取其 `registeredAt`。
      **旧版本 variant 的 revision 仍在映射里、不是孤儿**（其回收归 `delete-worker`）。
    删的两道闸：退休满 `RETIRE_QUIET_PERIOD` **且** 无未到终态的 run 引用；任一不满足 → 留到下次 pass
    （长期无人 push/deploy 时会滞留，无害：ACTIVE 但无人引用）。

    **不抛**：清理是收尾动作，失败不该把一次成功的 push/deploy 变成失败（打警告、留给下次 pass）。
    """
    # **枚举映射失败就整趟放弃**（不是「当作没有映射继续」）：孤儿判据是「不在任何映射里」，读不全映射会把
    # 别人在用的 revision 全判成孤儿；真实 ECS 的 `registeredAt` 是过去时刻，静默期这道闸拦不住它们。
    # 少跑一次机会式 pass 无害（滞留的 revision ACTIVE 但无人引用），错删在跑 run 的 revision 是事故。
    try:
        referenced_by_ssm = {m for _e, _t, raw in _iter_image_params(ssm, prefix)
                             for m in _mapped_arn(raw)}
    except Exception as exc:
        out(f"警告：清理 pass 读不全 SSM 的 worker-image 映射（{exc}）——本次跳过清理"
            f"（读不全就无从分辨孤儿，宁可不清也不误删）。")
        return CleanupOutcome()
    runs_table = names.default_name(prefix, names.BASE_RUNS_TABLE)
    deleted: list[str] = []
    kept: list[tuple[str, str]] = []
    for engine in engines:
        family = names.task_def_name(prefix, engine)
        try:
            revisions = scan_family(ecs, family)
        except Exception as exc:
            out(f"警告：清理 pass 列不出 {family} 的 revision：{exc}（留到下次 pass）")
            continue
        for rev in revisions:
            retired_at, reason = rev.retired_at, "已退休"
            if retired_at is not None and rev.arn in referenced_by_ssm:
                # 退休 tag 只说明「某次替换判它下岗」；若任何版本的某个映射仍指着它（历史上曾被另一 variant 共用），
                # 删了就让那条映射悬空——留着，直到映射也不再引用。**安全阀之一，与在跑 run 引用并列。**
                kept.append((rev.arn, "已退休，但仍被某个 worker-image 映射引用"))
                continue
            if retired_at is None:
                if not rev.has_lineage or rev.arn in referenced_by_ssm:
                    continue  # 模板/手工 revision，或仍被某版本的映射引用 → 不是候选
                # 孤儿：退休时刻 := registeredAt。取不到（真实 ECS 恒有；moto 不返回）→ 当作「此刻退休」，
                # 于是本次必然未满静默期、留到下次 pass —— 宁可滞留也不早删。
                retired_at, reason = rev.registered_at or now, "孤儿"
            if now - retired_at < RETIRE_QUIET_PERIOD:
                kept.append((rev.arn, f"{reason}，未满 {_hours(RETIRE_QUIET_PERIOD)} 静默期"))
                continue
            try:
                if _referenced_by_live_run(ddb, runs_table, rev.arn):
                    kept.append((rev.arn, f"{reason}，仍有未到终态的 run 引用"))
                    continue
                ecs.deregister_task_definition(taskDefinition=rev.arn)
                ecs.delete_task_definitions(taskDefinitions=[rev.arn])
            except Exception as exc:
                kept.append((rev.arn, f"{reason}，本次回收失败：{exc}"))
                continue
            deleted.append(rev.arn)
    if deleted:
        out(f"清理：回收 {len(deleted)} 个 revision（" + "、".join(_short_arn(a) for a in deleted) + "）")
    return CleanupOutcome(deleted=tuple(deleted), kept=tuple(kept))


def _mapped_arn(raw: str):
    """映射 JSON → 它引用的 revision ARN（读不懂 → 不产出）。

    **读不懂时产出空** 有安全含义：那条映射保护不了它的 revision，于是该 revision 会被判成孤儿。可接受——
    映射由本模块写、格式坏掉说明有人手改过 SSM；而静默期 + 在跑 run 安全阀仍然拦着。
    """
    try:
        data = json.loads(raw)
    except ValueError:
        return
    if isinstance(data, dict) and data.get("revision_arn"):
        yield data["revision_arn"]


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
    """一次「推一个引擎的一个 variant」的结果（deploy 的基底同步复用同一条路径、同一个结果类型）。"""

    engine: str
    variant: str
    tag: str
    digest: str
    revision_arn: str
    template_arn: str


def _ecr_login(aws: Aws, container) -> str:
    """ECR 登录（ADR 0038 步 3）→ **registry host**。

    令牌是 base64 的 `user:password`（ECR 恒 `AWS:<token>`，12 小时有效、重跑重登、幂等）。
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
            f"出路：先跑 `gherkai deploy --prefix {prefix} …`（本 prefix 的后端可能还没部署，"
            f"或上次部署用的 CLI 版本还没有 worker 镜像机制）。"
        )
    return arn


def _push_one(image: str, *, engine: str, variant: str, prefix: str, version: str,
              container, aws: Aws, now: datetime, out) -> PushOutcome:
    """ADR 0038「push-worker 流程」步 2–8 的实现（步 1 的版本 skew 前置在 `push_worker` 里；deploy 的基底同步
    与重派生共用本函数 / `_register_revision`，故这里**不做**任何 skew 判断）。"""
    try:
        tag = names.image_tag(version, variant)
    except ValueError as exc:  # variant 名或拼出的 tag 不合 docker/ECR 字符集
        raise WorkerCommandError(str(exc)) from exc
    repo = names.ecr_repo_name(prefix, engine)
    template_arn = _template_arn(aws, prefix=prefix, engine=engine)

    # 步 2：inspect 本地镜像——只取**存在**与**架构**（digest 此时取不到，见 container 模块头）
    info = container.inspect(image)
    if not info.exists:
        raise WorkerCommandError(
            f"本地找不到镜像 {image!r}：push-worker 只推**已 build 好**的镜像，不替你 build。\n"
            f"定制镜像的三行 Dockerfile 模板见 deploy_aws/README.md。"
        )
    if not info.matches_target_platform():
        raise WorkerCommandError(
            f"镜像 {image!r} 的平台是 {info.platform}，worker 固定 linux/amd64（云端 worker 任务是 X86_64）。\n"
            f"重 build 时带上平台：docker build --platform linux/amd64 -t {image} .\n"
            f"（arm Mac 上漏 `--platform` 的后果本来要拖到 Fargate **启动期** `exec format error` 才暴露，"
            f"这里提前拦下。）"
        )

    previous_digest = _tag_digest(aws.ecr, repo, tag)  # 必须在 push 之前问
    registry = _ecr_login(aws, container)              # 步 3
    repo_uri = f"{registry}/{repo}"
    target = f"{repo_uri}:{tag}"

    # 步 4：tag + push；**digest 的唯一来源 = 推送后再 inspect、按本 repo 挑**
    container.tag(image, target)
    container.push(target)
    digest = digest_for_repo(container.inspect(target).repo_digests, repo_uri)
    if not digest:
        raise WorkerCommandError(
            f"推送后在 {target} 上取不到本仓库（{repo_uri}）的 digest。digest 只能推送后取（本地 build 的镜像"
            f"没有 registry digest）——确认 push 真的成功了。"
        )
    if previous_digest and previous_digest != digest:
        out(f"tag {tag} 原已存在：原 digest {names.short_digest(previous_digest)} → 新 digest {names.short_digest(digest)}"
            f"（重推同名 variant 放行；在跑 run 手里的旧 revision 按 digest 指着旧镜像层、不受影响）")

    # 步 5：查重（模板 ARN、digest）二元组
    mapping = read_mapping(aws.ssm, prefix=prefix, engine=engine, tag=tag, version=version)
    if mapping and mapping.template_arn == template_arn and mapping.digest == digest:
        out(f"{engine}/{variant}：映射已是（当前模板，本 digest）→ 跳过注册，沿用 {_short_arn(mapping.revision_arn)}")
        return PushOutcome(engine=engine, variant=variant, tag=tag, digest=digest,
                           revision_arn=mapping.revision_arn, template_arn=template_arn)
    reuse = _find_reusable(aws.ecs, prefix=prefix, engine=engine, variant=variant,
                           template_arn=template_arn, digest=digest)
    if reuse is not None:
        revision_arn = reuse
        out(f"{engine}/{variant}：family 里已有本 variant 同（模板，digest）且未退休的 revision "
            f"{_short_arn(revision_arn)} → 复用（上次中断在注册与写 SSM 之间留下的孤儿）")
    else:
        # 步 6：从模板注册新 revision（镜像栏按 digest 引用）
        revision_arn = _register_revision(aws.ecs, template_arn=template_arn, engine=engine,
                                          image_ref=f"{repo_uri}@{digest}", digest=digest,
                                          variant=variant, version=version)

    # 步 7：写映射（覆盖语义）
    _put_ssm(aws.ssm, _mapping_path(prefix, engine, tag),
             _record_json(template_arn=template_arn, revision_arn=revision_arn,
                          digest=digest, pushed_at=now.isoformat()))

    # 步 8：退休被替换的旧 revision（不删；删归清理 pass）——`_retire` 有副作用（真打 retired-at tag）并自己打印
    old = mapping.revision_arn if mapping else None
    if old and old != revision_arn:
        _retire(aws.ecs, old, now=now, out=out)
    return PushOutcome(engine=engine, variant=variant, tag=tag, digest=digest,
                       revision_arn=revision_arn, template_arn=template_arn)


def _find_reusable(ecs, *, prefix: str, engine: str, variant: str, template_arn: str, digest: str) -> str | None:
    """family 里有没有**本 variant** 同（模板 ARN、digest）、ACTIVE、**未退休**的 revision（ADR 0038 步 5 的孤儿复用）。

    **限定同 variant**：复用的语义是「捡回上次中断留下的自己的孤儿」，不是「凡 digest 相同就共用」。真跑踩过：
    variant B 推的镜像 digest 恰与 A 相同，复用了 A 正在用的 revision → 之后 A 换 digest 重推会把它退休、
    满静默期被清理，B 的映射悬空。每个 variant 自己一个 revision（ECR 层共享、多一条 task-def 而已），
    退休与清理才能按 variant 独立判。
    为何不复用已退休的：退休 tag 说的是「有人决定它下岗」，复用它等于把它从清理 pass 手里抢回来、语义混乱；
    重新注册一个干净的 revision 更便宜（ECR 镜像层一个字节不动）。
    """
    for rev in scan_family(ecs, names.task_def_name(prefix, engine)):
        if (rev.tags.get(names.TAG_TEMPLATE) == template_arn
                and rev.tags.get(names.TAG_DIGEST) == digest
                and rev.tags.get(names.TAG_VARIANT) == variant
                and not rev.tags.get(names.TAG_RETIRED_AT)):
            return rev.arn
    return None


def push_worker(image: str, *, engine: str, variant: str, set_default: bool = False,
                cli_version: str | None, prefix: str, region=None, profile=None, container,
                aws: Aws | None = None, now: datetime | None = None, out=print) -> int:
    """`gherkai deploy push-worker <本地镜像> --engine <e> --variant <v> [--set-default]` → 退出码。

    八步见 ADR 0038「push-worker 流程」。**一次一个引擎**（两引擎镜像本就分别 build，被拒方案「一次收两个引擎」）。
    """
    from gherkai_runtime import compose

    aws = aws or make_aws(region=region, profile=profile)
    now = now or datetime.now(timezone.utc)

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
                           container=container, aws=aws, now=now, out=out)
        if set_default:
            _set_default(aws, prefix=prefix, variant=variant, version=str(cli_version),
                         engine=engine, out=out)
    except (WorkerCommandError, ContainerError) as exc:
        out(str(exc))
        return EXIT_PRECONDITION
    except Exception as exc:  # 凭证/权限/region/网络：对用户是「先修凭证」，与前置同一档、不该抛 traceback
        out(f"AWS 调用失败：{exc}\n需要部署方权限（ECR 推送域 + ecr:GetAuthorizationToken/DescribeImages、"
            f"ecs:RegisterTaskDefinition/ListTaskDefinitions/DescribeTaskDefinition/TagResource、iam:PassRole、"
            f"SSM 读写 /{prefix}backend/*、runs 表 Query），以及可用的凭证/region。")
        return EXIT_PRECONDITION
    cleanup_pass(prefix=prefix, engines=names.ENGINES, ssm=aws.ssm, ecs=aws.ecs, ddb=aws.ddb,
                 now=now, out=out)
    out(f"\n✓ {engine} / variant {result.variant}\n"
        f"  tag       {result.tag}\n"
        f"  digest    {result.digest}\n"
        f"  revision  {result.revision_arn}\n"
        f"提交时用 --worker-variant {result.variant}")
    return EXIT_OK


def _skew_gate(compose, *, prefix: str, cli_version: str | None, ssm, out) -> int | None:
    """版本 skew 前置：block → 退 2（无放行口）；warn/skip → 打一行继续；ok → 静默；**读不到戳（凭证/权限）
    也退 2**（对用户是「先修凭证」，与前置同一档）。

    判据与措辞的单一真源是 `compose.check_backend_skew`（ADR 0037 决策 7）。**block 时补一句本命令专属的出路**：
    push-worker 住 `gherkai-deploy-aws`，临时用同版本 CLI 要带 extra（`gherkai[deploy-aws]==X.Y.Z`），
    compose 那句给的是不带 extra 的形态；戳由 `check_backend_skew` 一并返回、不二次读。
    """
    try:
        verdict, message, stamp = compose.check_backend_skew(prefix=prefix, cli_version=cli_version, ssm=ssm)
    except Exception as exc:
        # 读戳失败（凭证/权限/region/网络）——`read_backend_version` 有意把这类异常抛给入口皮归码，
        # 本模块就是那个皮：归到「前置失败」这一档、不抛 traceback（同 `cli._guard_vpc_spec` 的口径）。
        out(f"读不到后端版本戳（SSM {names.ssm_path(prefix, 'version')}）：{exc}\n"
            f"需要可用的凭证与 region（--region / AWS_REGION / --profile），以及 ssm:GetParameter 权限。")
        return EXIT_PRECONDITION
    if verdict != compose.SKEW_BLOCK:
        if message:
            out(message)
        return None
    out(message)
    out(f"（本命令住 gherkai-deploy-aws，故临时跑同版本时要带 extra："
        f"uvx --from 'gherkai[deploy-aws]=={stamp}' gherkai deploy …）\n"
        f"不放行的理由：CLI 跑在后端前面会把镜像推进一个没人解析的版本命名空间"
        f"（tag 含 CLI 版本），而提交者的 preflight 提示又把他推回这一步、形成死循环。")
    return EXIT_PRECONDITION


def _set_default(aws: Aws, *, prefix: str, variant: str, version: str, engine: str, out) -> None:
    """`--set-default`：写默认指针 + **该 variant 在其它引擎尚无镜像时警告不拦**（ADR 0038 步 7）。

    不硬要求每个引擎都有（被拒方案「`--set-default` 硬要求 variant 在每个引擎都存在」）：与 preflight
    「按本 run 用到的引擎判」同一判据，单引擎团队不该被逼着凭空推另一个引擎的镜像。
    """
    _put_ssm(aws.ssm, names.ssm_path(prefix, names.WORKER_DEFAULT_KEY), variant)
    out(f"默认指针 → {variant}（提交时不给 --worker-variant 即用它）")
    tag = names.image_tag(version, variant)
    for other in names.ENGINES:
        if other == engine:
            continue
        if read_mapping(aws.ssm, prefix=prefix, engine=other, tag=tag, version=version) is None:
            out(f"警告：variant `{variant}` 在 {other} 尚无镜像（tag {tag}），用到该引擎的 run 会在 preflight 被拦。"
                f"\n     需要就为 {other} 也推一份：gherkai deploy push-worker <镜像> --engine {other} "
                f"--variant {variant}")


# ---------------------------------------------------------------------------
# `gherkai deploy` 的 worker 镜像四步（第 1 步是 stack 资源；后三步 + 清理在这里）
# ---------------------------------------------------------------------------

def sync_base(*, prefix: str, engines, version: str, container, aws: Aws, now: datetime, out) -> list[PushOutcome]:
    """第 2 步：从 GHCR 拉当前版本基底、走 push-worker 同一条内部路径推成 `<版本>-base`。

    **非纯发行版（`.dev`/`.post`/本地段）没有 GHCR 基底**——那些版本由 tag 之后的 commit 派生、不可能发布
    （ADR 0037 决策 2b），拉必然失败。此时打一条明确警告、**跳过本步继续第 3/4 步**：contributor 在自己的 dev
    树上部署是正常用法，把 deploy 变成硬失败会逼他们绕过命令手工推。
    """
    from gherkai_runtime import compose

    if not compose.is_pure_release(version):
        out(f"警告：CLI 版本 {version} 不是纯发行版（含 .dev/.post/本地段）——GHCR 上不存在对应基底镜像，"
            f"跳过基底同步。\n"
            f"     dev 版要能跑：本地 build 一份镜像后 `gherkai deploy push-worker <镜像> --engine <e> "
            f"--variant base`（默认指针已初始化为 base）。")
        return []
    results = []
    for engine in engines:
        ref = f"{GHCR_BASE_IMAGE.format(engine=engine)}:{version}"
        out(f"\n== 基底同步 {engine}：{ref} ==")
        try:
            container.pull(ref, platform="linux/amd64")
        except ContainerError as exc:
            raise WorkerCommandError(
                f"{exc}\n拉不到基底 {ref}：PyPI 已发、镜像还没发完的半发布态是已知情形——"
                f"等镜像发布完成后再 `gherkai deploy`（幂等收敛）。"
            ) from exc
        results.append(_push_one(ref, engine=engine, variant=BASE_VARIANT, prefix=prefix, version=version,
                                 container=container, aws=aws, now=now, out=out))
    return results


def init_default_pointer(*, prefix: str, aws: Aws, out) -> str:
    """第 3 步：默认指针缺失 → `base`；**已存在则不动**（ADR 0038「默认指针不自动重置」——它记的是团队意图，
    升级时重置回 base 会抹掉它，被拒方案有专条）。"""
    current = read_default_variant(aws.ssm, prefix)
    if current:
        out(f"默认 variant 已是 `{current}`——不动（升级不重置团队意图）")
        return current
    _put_ssm(aws.ssm, names.ssm_path(prefix, names.WORKER_DEFAULT_KEY), BASE_VARIANT)
    out(f"默认 variant 初始化为 `{BASE_VARIANT}`")
    return BASE_VARIANT


def rederive_variants(*, prefix: str, engines, version: str, aws: Aws, now: datetime, out) -> list[PushOutcome]:
    """第 4 步：模板换了就用**新模板 + 已记录的 digest** 重注册各 variant 的 revision（镜像一个字节不动）。

    为何必须（ADR 0038 被拒方案「deploy 改模板后不重派生既有 variant」）：revision 是不可变快照、无继承——
    deploy 调了 cpu / stopTimeout 后，旧 variant 会一直跑旧配置直到有人想起来重推。按模板 ARN 判定、幂等。
    `pushed_at` **保留原值**：它记的是镜像推上去的时刻，重派生没碰镜像。
    """
    results: list[PushOutcome] = []
    for engine in engines:
        template_arn = _template_arn(aws, prefix=prefix, engine=engine)
        for mapping in current_version_mappings(aws.ssm, prefix=prefix, engine=engine, version=version):
            if mapping.template_arn == template_arn:
                continue
            repo_uri = _repo_uri_from_template(aws.ecs, template_arn=template_arn, engine=engine)
            new_arn = _register_revision(aws.ecs, template_arn=template_arn, engine=engine,
                                         image_ref=f"{repo_uri}@{mapping.digest}", digest=mapping.digest,
                                         variant=mapping.variant, version=version)
            _put_ssm(aws.ssm, _mapping_path(prefix, engine, mapping.tag),
                     _record_json(template_arn=template_arn, revision_arn=new_arn,
                                  digest=mapping.digest, pushed_at=mapping.pushed_at))
            _retire(aws.ecs, mapping.revision_arn, now=now, out=out)
            out(f"重派生 {engine}/{mapping.variant}：模板已更新 → {_short_arn(new_arn)}"
                f"（旧 {_short_arn(mapping.revision_arn)} 已打退休 tag）")
            results.append(PushOutcome(engine=engine, variant=mapping.variant, tag=mapping.tag,
                                       digest=mapping.digest, revision_arn=new_arn,
                                       template_arn=template_arn))
    if not results:
        out("重派生：所有 variant 的 revision 都已基于当前模板——无需重派生")
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
        f"模板 revision {template_arn} 里没有名为 {wanted!r} 的 container，取不到 ECR repo——重跑 `gherkai deploy`。")


def run_deploy_steps(*, prefix: str, version: str, container, engines=None, region=None, profile=None,
                     aws: Aws | None = None, now: datetime | None = None, out=print) -> int:
    """`gherkai deploy` 的 worker 镜像第 2/3/4 步 + 清理 pass（第 1 步是 stack 资源、随 cdk 事务）。

    **不做版本 skew 前置**（ADR 0038）：deploy 本身就是改戳的动作——前置在 cdk 前会把自己拦死、在 cdk 后恒真。
    失败 → 退 1 且点明「stack 已生效」：cdk 已经改了账户，退 2（= 什么都没发生）会误导。
    """
    from gherkai_runtime import compose

    aws = aws or make_aws(region=region, profile=profile)
    now = now or datetime.now(timezone.utc)
    engines = tuple(engines or names.ENGINES)

    # 容器引擎只有第 2 步（同步基底 pull/push）用；非纯发行版本步会整步跳过（见 `sync_base`），此时不探活——
    # contributor 在没装 docker 的机器上 deploy dev 版，第 3/4 步照样收敛，不为用不到的东西退 1。
    # （纯发行版则 deploy 的机器必须有容器引擎；「免容器引擎的 registry 直拷」是 ADR 0038 重议闸门里的加法。）
    if compose.is_pure_release(version):
        probe = container.probe()
        if probe:
            out(f"{probe}\nstack 已生效，但同步基底镜像要 pull/push——deploy 的机器需要容器引擎。\n"
                f"装好后重跑 `gherkai deploy`（幂等收敛，不会重复注册）。")
            return EXIT_FAILED
    try:
        sync_base(prefix=prefix, engines=engines, version=version, container=container,
                  aws=aws, now=now, out=out)
        init_default_pointer(prefix=prefix, aws=aws, out=out)
        rederive_variants(prefix=prefix, engines=engines, version=version, aws=aws, now=now, out=out)
    except Exception as exc:  # 含 AWS 侧异常：cdk 已改过账户，一律归「四步失败」这一档、不抛 traceback
        out(f"{exc}\nstack 已生效；worker 镜像步骤未完成——重跑 `gherkai deploy` 幂等收敛。")
        return EXIT_FAILED
    cleanup_pass(prefix=prefix, engines=engines, ssm=aws.ssm, ecs=aws.ecs, ddb=aws.ddb, now=now, out=out)
    return EXIT_OK


# ---------------------------------------------------------------------------
# list-workers
# ---------------------------------------------------------------------------

def list_workers(*, prefix: str, cli_version: str | None, engines=None, region=None, profile=None,
                 aws: Aws | None = None, out=print) -> int:
    """按引擎列**当前版本**的 variant（tag / digest / 推送时间 / revision）+ 默认指针 + 待清理与孤儿。

    「当前版本」= 跑这条命令的 CLI 自身版本（与 push-worker 打 tag 用的同一个）——故本命令同样过 skew 前置：
    版本对不上时列出来的是另一个命名空间的东西，比不列更误导。
    """
    from gherkai_runtime import compose

    aws = aws or make_aws(region=region, profile=profile)
    engines = tuple(engines or names.ENGINES)
    blocked = _skew_gate(compose, prefix=prefix, cli_version=cli_version, ssm=aws.ssm, out=out)
    if blocked is not None:
        return blocked
    version = str(cli_version)
    try:
        default = read_default_variant(aws.ssm, prefix)
        out(f"prefix {prefix}    版本 {version}    默认 variant {default or '（未初始化——跑一次 gherkai deploy）'}")
        # 全部版本的映射只枚举一次（GetParametersByPath 每页 10 条要翻页），两个引擎共用——同 cleanup_pass 的做法
        mapped = {a for _e, _t, raw in _iter_image_params(aws.ssm, prefix) for a in _mapped_arn(raw)}
        for engine in engines:
            family = names.task_def_name(prefix, engine)
            out(f"\n== {engine}（family {family}，ECR repo {names.ecr_repo_name(prefix, engine)}）==")
            mappings = current_version_mappings(aws.ssm, prefix=prefix, engine=engine, version=version)
            if not mappings:
                out("  （本版本还没有任何 variant——`gherkai deploy` 会同步基底，或 push-worker 推一个）")
            else:
                tag_w = max(28, max(len(m.tag) for m in mappings) + 2)  # dev 版 tag 很长，列宽随内容
                out("  " + _cell("variant", 16) + _cell("tag", tag_w) + _cell("digest", 20)
                    + _cell("推送时间", 28) + "revision")
                for m in mappings:
                    out("  " + _cell(m.variant, 16) + _cell(m.tag, tag_w)
                        + _cell(names.short_digest(m.digest), 20) + _cell(m.pushed_at or "-", 28)
                        + _short_arn(m.revision_arn))
            _print_pending_cleanup(aws, family=family, mapped=mapped, out=out)
    except Exception as exc:  # 读侧命令：连不上/没权限也别抛 traceback（同 provider 其余读侧的口径）
        out(f"读不到 worker 镜像状态（SSM/ECS）：{exc}")
        return EXIT_PRECONDITION
    return EXIT_OK


def _print_pending_cleanup(aws: Aws, *, family: str, mapped: set, out) -> None:
    """已退休（带 retired-at）与孤儿（带血缘 tags、不在任何版本的映射里）——清理 pass 的候选，列出来才可解释
    「为什么 family 里 revision 比 variant 多」。`mapped` = 全部版本映射引用的 revision ARN 集合（调用方算一次）。"""
    lines = []
    for rev in scan_family(aws.ecs, family):
        if rev.tags.get(names.TAG_RETIRED_AT):
            lines.append(f"  待清理 {_cell(_short_arn(rev.arn), 28)}已退休 {rev.tags[names.TAG_RETIRED_AT]}"
                         f"（variant {rev.tags.get(names.TAG_VARIANT, '?')}）")
        elif rev.has_lineage and rev.arn not in mapped:
            lines.append(f"  待清理 {_cell(_short_arn(rev.arn), 28)}孤儿：无任何版本的映射引用"
                         f"（variant {rev.tags.get(names.TAG_VARIANT, '?')}，注册于 {rev.registered_at or '?'}）")
    for line in lines:
        out(line)


def _cell(text: str, width: int) -> str:
    """定宽列（**按显示宽度补，不按字符数**）：中文表头字符占两列，用 `f"{s:<28}"` 会让整张表歪掉。

    只认「东亚宽/全角」这一档（`unicodedata.east_asian_width` 的 W/F）——够表头用；数据列受 tag 字符集约束、恒 ASCII。
    """
    import unicodedata

    shown = sum(2 if unicodedata.east_asian_width(ch) in "WF" else 1 for ch in text)
    return text + " " * max(1, width - shown)


