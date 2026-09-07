"""资源命名（ADR 0033 两层命名）——共享部分**直接 import 产品本体 `gherkai_runtime.names`（真同源）**。

曾因「CDK 独立工程、不能 import 当时的 `cli` 包（今 `gherkai_cli`）」在此复刻命名函数（双写、靠对拍测试防漂移）；组合根共享层
抽为平级包（今 `runtime/gherkai_runtime`）后（ADR 0016「演进」节），命名纯函数移入零依赖的
`gherkai_runtime.names`，本文件退成「re-export + IaC 特有常量」的薄壳——复刻消除，护栏测试转为结构性保证。
"""
from __future__ import annotations

# 共享命名真源（re-export 保 stack.py/tests 既有引用不动）
from gherkai_runtime.names import (  # noqa: F401
    BASE_CLUSTER,
    BASE_BUCKET,
    BASE_EVENTS_TABLE,
    BASE_EXIT_OBSERVER_LAMBDA,
    BASE_KICKER_LAMBDA,
    BASE_RECONCILER_LAMBDA,
    BASE_RUNS_TABLE,
    DEFAULT_PREFIX,
    ENGINES,
    container_name,
    default_name,
    job_timeout_schedule_prefix,
    ssm_path,
    task_def_name,
)

# ---- IaC 特有（不进 gherkai_runtime.names：只有 IAM 收窄用，cli/Lambda 不消费）----

# IAM 资源 ARN 收窄用的稳定段（ADR 0033 IAM 表）：
# QWEN_MODEL_ID 是**模型标识（部署期稳定、非运行期概念）**，故可安全 pin 进 IAM——**须与
# `engines/midscene/src/lib/agentcore-sigv4.mts` 的 `MODEL` 逐字一致**（Midscene InvokeModel 的 foundation-model
# ARN pin 到它）。裸 id、无跨区前缀（不走 inference profile）。
# （对比：nova-act 的 workflow-definition 名是 worker 运行期概念、不 pin——IAM 用 workflow-definition/* 通配，
#  避免 IaC 跨工程耦合 worker 常量，见 stack.py nova-act 权限注释。）
QWEN_MODEL_ID = "qwen.qwen3-vl-235b-a22b"


def ssm_subnets_path(prefix: str) -> str:
    """subnet ID 列表的 SSM 路径（= gherkai_runtime.names.ssm_path(prefix, "subnets") 的便捷形式）。"""
    return ssm_path(prefix, "subnets")


def ssm_security_groups_path(prefix: str) -> str:
    """sg ID 列表的 SSM 路径（= gherkai_runtime.names.ssm_path(prefix, "security-groups") 的便捷形式）。"""
    return ssm_path(prefix, "security-groups")
