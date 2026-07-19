"""资源命名（ADR 0033 两层命名）——**必须与 cli `compose.py` 的命名规则逐字一致**。

单一事实源风险点（ADR 0033 护栏）：CDK 建的名 = cli 推导的默认名，靠「两侧用同一规则 + 同一 prefix」保证。
CDK 独立工程、不能 import cli，故这里**复刻** cli `compose.default_name`/`task_def_name`/`container_name`/`ssm_path`
的规则。改这里必同步改 cli 侧（反之亦然），否则 cloud 跑批 RunTask 找不到 task-def / 连错表。

基名（prefix 之后固定部分）与 cli `compose._BASE_*` 对齐；引擎规范名 `novaact`/`midscene`（与 core model / cli 一致，
非 `nova`）。prefix 含分隔符、原样拼（默认 `gherkai-`；用户负责分隔符，防粘连——同 cli 侧约定）。
"""
from __future__ import annotations

DEFAULT_PREFIX = "gherkai-"

BASE_RUNS_TABLE = "runs"
BASE_EVENTS_TABLE = "events"
BASE_BUCKET = "artifacts"
BASE_CLUSTER = "cluster"

ENGINES = ("novaact", "midscene")  # 引擎规范名（与 core model / cli compose._ENGINES 一致）

# IAM 资源 ARN 收窄用的稳定段（ADR 0033 IAM 表）：
# QWEN_MODEL_ID 是**模型标识（部署期稳定、非运行期概念）**，故可安全 pin 进 IAM——**须与
# `engines/midscene/lib/agentcore-sigv4.mts` 的 `MODEL` 逐字一致**（Midscene InvokeModel 的 foundation-model
# ARN pin 到它）。裸 id、无跨区前缀（不走 inference profile）。
# （对比：nova-act 的 workflow-definition 名是 worker 运行期概念、不 pin——IAM 用 workflow-definition/* 通配，
#  避免 IaC 跨工程耦合 worker 常量，见 stack.py nova-act 权限注释。）
QWEN_MODEL_ID = "qwen.qwen3-vl-235b-a22b"


def default_name(prefix: str, base: str) -> str:
    """prefix + 基名（原样拼）。对齐 cli `compose.default_name`。"""
    return f"{prefix}{base}"


def task_def_name(prefix: str, engine: str) -> str:
    """task-def family 名 `{prefix}{engine}-worker`（带 prefix）。对齐 cli `compose.task_def_name`。"""
    return f"{prefix}{engine}-worker"


def container_name(engine: str) -> str:
    """task-def 内 container 元素名 `{engine}-worker`（**不带 prefix**，ADR 0033 硬契约）。

    cli `FargateEngine` RunTask 的 containerOverrides[].name 逐字匹配它注 env——不匹配则 env 注入全落空。
    container 是 task-def 内部名、随已带 prefix 的 task-def 走，故不叠 prefix。对齐 cli `compose.container_name`。
    """
    return f"{engine}-worker"


def ssm_subnets_path(prefix: str) -> str:
    """subnet ID 列表的 SSM 路径（含 prefix）。对齐 cli `compose.ssm_path(prefix, "subnets")`。"""
    return f"/{prefix}backend/subnets"


def ssm_security_groups_path(prefix: str) -> str:
    """sg ID 列表的 SSM 路径（含 prefix）。对齐 cli `compose.ssm_path(prefix, "security-groups")`。"""
    return f"/{prefix}backend/security-groups"
