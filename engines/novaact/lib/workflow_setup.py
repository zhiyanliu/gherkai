"""Nova Act workflow definition 的 create-if-not-exists（端到端闭环，无需手动 CLI）。

@workflow 的 IAM 路径要求 workflow definition 已存在（否则 CreateWorkflowRun 报 404，见 ADR 0004）。
本 helper 用 boto3 探测、不存在才创建，把那一步手动 CLI 吸收进代码——首次跑自动建、之后探测到就跳过。
boto3 操作与 `aws nova-act create-workflow-definition` CLI 完全等价。
"""
from __future__ import annotations

import boto3


def ensure_workflow_definition(name: str, *, region: str | None = None, description: str | None = None) -> str:
    """确保名为 `name` 的 workflow definition 存在；返回 'exists' 或 'created'。

    region=None（不再硬编码 us-east-1，ADR 0016 决策 C）→ boto3 nova-act client 走默认链/profile config 解析 region；
    真无 region（全 miss）→ NoRegionError（fail-loud、别静默跑错区）。注：本函数的 nova-act client **会**查 profile config，
    但同 worker 的 AgentCore 那条路径（AgentCoreBrowserSessionProvider.validate_region）**不查**、要显式字符串——故正常路径靠
    组合根 `resolve_region` 把 region 落实成具体字符串再注入（见 run_scope.py REGION 注释 / ADR 0016 决策 C）。
    """
    client = boto3.client("nova-act", region_name=region)
    try:
        client.get_workflow_definition(workflowDefinitionName=name)
        return "exists"
    except client.exceptions.ResourceNotFoundException:
        kwargs = {"name": name}
        if description:
            kwargs["description"] = description
        client.create_workflow_definition(**kwargs)
        return "created"
