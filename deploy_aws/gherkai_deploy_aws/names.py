"""资源命名（ADR 0033 两层命名）——共享部分**直接 import 产品本体 `gherkai_runtime.names`（真同源）**。

曾因「CDK 独立工程、不能 import 当时的 `cli` 包（今 `gherkai_cli`）」在此复刻命名函数（双写、靠对拍测试防漂移）；组合根共享层
抽为平级包（今 `runtime/gherkai_runtime`）后（ADR 0016「演进」节），命名纯函数移入零依赖的
`gherkai_runtime.names`，本文件退成「re-export + provider 特有常量」的薄壳——复刻消除，护栏测试转为结构性保证。

**本模块零 `aws_cdk` 依赖**：`cli.py`（provider 命令面，绝不 import aws_cdk——jsii import 即起 node 子进程，
ADR 0037 决策 6）与 `stack.py`（CDK 侧）共用它，故此处只放纯字符串推导。
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

# ---- provider 特有（不进 gherkai_runtime.names：只有 IAM 收窄 / CloudFormation 层用，cli/Lambda 不消费）----

# IAM 资源 ARN 收窄用的稳定段（ADR 0033 IAM 表）：
# QWEN_MODEL_ID 是**模型标识（部署期稳定、非运行期概念）**，故可安全 pin 进 IAM——**须与
# `engines/midscene/src/lib/agentcore-sigv4.mts` 的 `MODEL` 逐字一致**（Midscene InvokeModel 的 foundation-model
# ARN pin 到它）。裸 id、无跨区前缀（不走 inference profile）。
# （对比：nova-act 的 workflow-definition 名是 worker 运行期概念、不 pin——IAM 用 workflow-definition/* 通配，
#  避免 IaC 跨工程耦合 worker 常量，见 stack.py nova-act 权限注释。）
QWEN_MODEL_ID = "qwen.qwen3-vl-235b-a22b"

# Lambda asset 构建目录的落点 env——**命令进程 → cdk 起的 app 进程之间的管道**（`cli.Provider._run_cdk` 写、
# `stack.BackendStack._build_lambda_asset` 读）。放在本模块是因为两侧唯一的共同 import 就是它（`cli.py` 不能
# import `stack.py`：那会拉起 aws_cdk/jsii 的 node 子进程）。
# **不做成 CDK context**：它是管道、不是设计旋钮，混进 context 会破坏「flag 面 == context 旋钮全集」这条对齐
# （ADR 0037 决策 6）。缺它（裸跑 cdk synth）→ app 侧自建 mkdtemp。
LAMBDA_ASSET_DIR_ENV = "GHERKAI_LAMBDA_ASSET_DIR"


def stack_name(prefix: str) -> str:
    """CloudFormation stack 名（= `app.py` 给 `BackendStack` 的 construct id，CDK 据此定 stack 名）。

    **两个消费者必须恒等**：`app.py` 建 stack 用它；`cli.py` 的 VPC 档三态比对用它 `DescribeStacks`
    探「stack 是否已存在」（ADR 0037 决策 6 三态①）。任一侧单独改推导 → 要么部署出第二套 stack、要么
    三态误判成「真首次部署」而放行错档 —— 故收在此一处。
    **公式不得变更**：现网已部署的 stack 就叫这个名，改推导等于换 stack（旧 stack 遗留、新 stack 与旧资源撞名）。
    """
    return f"BackendStack-{prefix.rstrip('-') or 'default'}"


def ssm_subnets_path(prefix: str) -> str:
    """subnet ID 列表的 SSM 路径（= gherkai_runtime.names.ssm_path(prefix, "subnets") 的便捷形式）。"""
    return ssm_path(prefix, "subnets")


def ssm_security_groups_path(prefix: str) -> str:
    """sg ID 列表的 SSM 路径（= gherkai_runtime.names.ssm_path(prefix, "security-groups") 的便捷形式）。"""
    return ssm_path(prefix, "security-groups")


def ssm_version_path(prefix: str) -> str:
    """后端版本戳的 SSM 路径（ADR 0037 决策 6「版本戳」/ 决策 7 skew 比对读侧）。"""
    return ssm_path(prefix, "version")


def ssm_vpc_path(prefix: str) -> str:
    """生效 VPC 档的 SSM 路径（ADR 0037 决策 6「VPC 档持久化比对，三态齐全」）。

    值形态三档：`default` / `new:<所建 vpc-id>` / `<复用的 vpc-id>`——`new` 档也存出所建 vpc-id 使其可回溯核对。
    比对逻辑（含 `new:` 前缀匹配）在 `cli.vpc_spec_matches`，与本路径同一批语义、别在别处重写。
    """
    return ssm_path(prefix, "vpc")


def ssm_worker_template_path(prefix: str, engine: str) -> str:
    """引擎 worker task-def **模板 revision ARN** 的 SSM 路径（ADR 0038「SSM 参数与命名真源」第 1 行）。

    写者 = stack 资源（随 `gherkai deploy` 的 cdk 事务同生死、回滚不留错值），值取 CDK 内
    `taskDefinition.taskDefinitionArn`（`AWS::ECS::TaskDefinition` 的 `Ref` 返回带 revision 的 ARN）。
    `push-worker` 永远从它复制模板，不抄「最近一次」revision。
    """
    return ssm_path(prefix, f"worker-template/{engine}")
