"""资源命名真源（`gherkai-runtime` 产品本体，ADR 0033「两层命名」）：cli / IaC / Lambda 共用的纯字符串推导。

**零依赖**（不 import core/boto3）——`gherkai-deploy-aws`（`gherkai_deploy_aws.names`）直接 import 本模块拿命名，依赖面最小
（曾因「CDK 独立工程、不能 import 当时的 `cli` 包（今 `gherkai_cli`）」在 iac 侧复刻一份、靠对拍测试防漂移，抽入本模块后复刻消除、真同源）。
"""
from __future__ import annotations

import re

DEFAULT_PREFIX = "gherkai-"

# 各资源的「基名」（prefix 之后的固定部分）——CDK 与 cli 共享的约定（CDK 侧须用同名，否则 preflight 报 prefix 不一致）。
BASE_RUNS_TABLE = "runs"
BASE_EVENTS_TABLE = "events"
BASE_BUCKET = "artifacts"
BASE_CLUSTER = "cluster"
# 无状态跑批 kicker（踢启器）Lambda 基名（ADR 0034）：CDK 建 `{prefix}kicker`（stack.py 用同名），cli status
# --wait 据 --prefix 推理出它 invoke 接力 kickoff（Lambda 名单一真源、cli↔IaC 同源）。
BASE_KICKER_LAMBDA = "kicker"
BASE_RECONCILER_LAMBDA = "reconciler"
BASE_EXIT_OBSERVER_LAMBDA = "exit-observer"
# job timeout 到点触发器的 one-time schedule 基名（ADR 0034「job timeout」节）：推进器运行期建
# `{prefix}job-timeout-{摘要}`、IaC 只给这一族名的 IAM 资源域——名字空间前缀见 job_timeout_schedule_prefix。
BASE_JOB_TIMEOUT_SCHEDULE = "job-timeout"
# task-def / container：按 job.engine 拼 `{prefix}{engine}-worker`（对称 EngineResolver 按 engine 选）。
ENGINES = ("novaact", "midscene")

# 后端 SSM 参数的相对键（全路径 = `ssm_path(prefix, 键)`；参数族真值表见 ADR 0038「SSM 参数与命名真源」、0037 决策 6）。
# 调用点一律引常量、不写裸字面量——推送方/解析方/IaC/Lambda 拼的必须是同一个键。
BACKEND_VERSION_KEY = "version"        # 后端版本戳（stack 资源随部署事务写；提交侧 skew 比对读）
SUBNETS_KEY = "subnets"                # worker 子网 ID 列表
SECURITY_GROUPS_KEY = "security-groups"  # worker 安全组 ID
VPC_KEY = "vpc"                       # 生效的 VPC 档（部署方三态比对读，ADR 0037 决策 6）
WORKER_IMAGE_ROOT_KEY = "worker-image"  # `worker-image/<engine>/<tag>` 映射族的根（按路径列举时用；单条键走 worker_image_key）

# 引擎原生产物在 run 树下的子目录名（ADR 0029「S3 key 镜像本地 run 树」的前提）：同步 run / local per-run / cloud 容器内
# 三宿主拼的必须是同一个名字，故单点；键 = 引擎名（ENGINES）。改名 = 改 S3 key 布局，须同时考虑已落产物的可读性。
ARTIFACT_SUBDIR = {"novaact": "nova-trajectories", "midscene": "midscene-run"}


def default_name(prefix: str, base: str) -> str:
    """prefix + 基名（原样拼，prefix 含分隔符由用户负责）。CDK 与 cli 共用此推导 → 单一事实源。"""
    return f"{prefix}{base}"


def task_def_name(prefix: str, engine: str) -> str:
    """引擎的 task-def family 名：`{prefix}{engine}-worker`（按 job.engine 选，对称 EngineResolver）。"""
    return f"{prefix}{engine}-worker"


def container_name(engine: str) -> str:
    """task-def 里的 container 名（RunTask overrides 指定往哪个 container 注 env）。不带 prefix——container 是
    task-def 内部名、随 task-def 走（task-def 已带 prefix），再叠 prefix 冗余。固定 `{engine}-worker`。"""
    return f"{engine}-worker"


def job_timeout_schedule_prefix(prefix: str) -> str:
    """job timeout schedule 的名字空间前缀 `{prefix}job-timeout-`（其后接 run+scope 摘要段）。

    **含尾部 `-`**：通配/摘要就从这里起——推进器据它建 schedule 名、IaC 据它拼 IAM 资源域
    `schedule/default/{此前缀}*`，两侧同源。任一侧单独改名 → CreateSchedule 被 IAM 拒（best-effort
    只打日志），job timeout 静默降级为防御扫、纯静默 job 彻底失去超时保护（ADR 0034「job timeout」节）。
    """
    return f"{default_name(prefix, BASE_JOB_TIMEOUT_SCHEDULE)}-"


def ssm_path(prefix: str, key: str) -> str:
    """`/{prefix}backend/<key>`：本部署**全部** SSM 参数的路径构造单点（网络 subnets/security-groups、
    version/vpc、worker-template/worker-image/worker-default 皆经此；IAM 资源域按同一形态拼 `*`）。
    cli 已知 prefix 直接拼路径读、无循环依赖（ADR 0033）；参数族清单见 ADR 0038「SSM 参数与命名真源」。"""
    return f"/{prefix}backend/{key}"


def ecr_repo_name(prefix: str, engine: str) -> str:
    """引擎 worker 镜像的 ECR 仓库名 —— **恒等于 `task_def_name(prefix, engine)`**（ADR 0038「tag 命名」节）。

    「ECR repo 名复用 task-def family 名」是一条约定（同 prefix 心智、一个引擎一套资源同名），曾以注释 +
    内联副本散在 IaC 侧与推送脚本里；收在此处后**改名只改一处**，两侧不会漂。
    单独立函数而非让调用方直接用 `task_def_name`：调用点意图是「取 ECR 仓库」，语义名让「将来若要拆开」有落点。
    """
    return task_def_name(prefix, engine)


# worker 镜像 tag / SSM 键（ADR 0038）。
# ---- tag 字符集（docker/OCI 与 ECR 共同约束）：首字符 `[A-Za-z0-9_]`，其后 `[A-Za-z0-9_.-]`，总长 ≤128 ----
_TAG_RE = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}$")
# variant 名（tag 的后半段）：同字符集但不设长度上限（总长由 _TAG_RE 兜）。单独校验是为了把
# 「variant 名本身不合法」与「拼出来的 tag 超长/首字符非法」两类错误分开报。
_VARIANT_RE = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.-]*$")

# 默认 variant 指针（部署级一个；deploy 初始化为 `base`，`push-worker --set-default` 改写）。
WORKER_DEFAULT_KEY = "worker-default"

# task-def revision 上记血缘与退休时刻的 tag 键（ADR 0038：退休时刻与血缘**不进 SSM**、随 revision 同生死）。
TAG_VARIANT = "gherkai:variant"
TAG_VERSION = "gherkai:version"
TAG_DIGEST = "gherkai:digest"
TAG_TEMPLATE = "gherkai:template"
TAG_RETIRED_AT = "gherkai:retired-at"

# runs 表 STATE item 的顶层属性名：本 run 用到的 worker task-def revision ARN 列表（清理 pass 的在跑 run
# 安全阀按它判引用，沿用 ADR 0034 `detached` 顶层标记先例）。
STATE_WORKER_TASK_DEF_ARNS_ATTR = "worker_task_def_arns"
# runs 表按 `status` 的稀疏 GSI 名（只索引 STATE item）：清理 pass Query 非终态 run，不扫全表。
RUNS_STATUS_GSI = "status-index"


def image_tag(version: str, variant: str) -> str:
    """worker 镜像 tag `<归一化版本>-<variant>` —— **命名单一真源，同时是单一校验点**（ADR 0038）。

    PEP 440 的 `+`（本地段）与 `!`（epoch）不在 docker/ECR 的 tag 字符集内（`1.4.0.post3.dev0+28c1684` 直接
    `docker tag` 即 `invalid reference format`，实测），故两者归一化为 `.`；返回前按字符集正则校验，不匹配即
    `ValueError`——推送方与解析方（preflight / 推进器兼容路径）拼的是同一个函数，键不会两边算法不同而对不上。
    """
    if not _VARIANT_RE.match(variant):
        raise ValueError(
            f"variant 名不合法：{variant!r}——须匹配 {_VARIANT_RE.pattern}"
            "（字母数字下划线开头，其后可含 `.` `-`）"
        )
    tag = f"{version.replace('+', '.').replace('!', '.')}-{variant}"
    if not _TAG_RE.match(tag):
        raise ValueError(
            f"镜像 tag 不合法：{tag!r}（由版本 {version!r} + variant {variant!r} 拼出）"
            f"——须匹配 {_TAG_RE.pattern}"
        )
    return tag


def worker_template_key(engine: str) -> str:
    """模板 revision ARN 的 SSM 键（相对键，全路径 = `ssm_path(prefix, 本键)`）。写者 = stack 资源。"""
    return f"worker-template/{engine}"


def short_digest(digest: str | None, keep: int = 12) -> str:
    """镜像 digest 的人读缩写：`sha256:<前 keep 位>`（缺 → `-`）。**单点**：list-workers 表格与 preflight 打印都用它，
    同一个 digest 在两处长相一致，人对照「是不是刚推上去那个」不用换算。机器要全串看 definition / SSM。"""
    if not digest:
        return "-"
    algo, _, hexpart = digest.partition(":")
    return f"{algo}:{hexpart[:keep]}" if hexpart else digest[:keep]


def worker_image_key(engine: str, tag: str) -> str:
    """（引擎，镜像 tag）→ revision 映射的 SSM 键（相对键，全路径 = `ssm_path(prefix, 本键)`）。

    值 = JSON：`template_arn` / `revision_arn` / `digest` / `pushed_at`（ISO 8601 UTC）。键含版本 ⇒ variant
    **按版本隔离**：旧版本的 variant 留作历史、不参与当前版本解析。
    """
    return f"{WORKER_IMAGE_ROOT_KEY}/{engine}/{tag}"
