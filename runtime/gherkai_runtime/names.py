"""资源命名真源（`gherkai-runtime` 产品本体，ADR 0033「两层命名」）：cli / IaC / Lambda 共用的纯字符串推导。

**零依赖**（不 import core/boto3）——`gherkai-deploy-aws`（`gherkai_deploy_aws.names`）直接 import 本模块拿命名，依赖面最小
（曾因「CDK 独立工程、不能 import 当时的 `cli` 包（今 `gherkai_cli`）」在 iac 侧复刻一份、靠对拍测试防漂移，抽入本模块后复刻消除、真同源）。
"""
from __future__ import annotations

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
    """subnet/sg 的 SSM 参数路径（含 prefix，cli 已知 prefix 拼路径读，无循环——ADR 0033）。"""
    return f"/{prefix}backend/{key}"
