"""Nova Act workflow definition 的 create-if-not-exists（端到端闭环，无需手动 CLI）。

@workflow 的 IAM 路径要求 workflow definition 已存在（否则 CreateWorkflowRun 报 404，见 ADR 0004）。
本 helper 用 boto3 探测、不存在才创建，把那一步手动 CLI 吸收进代码——首次跑自动建、之后探测到就跳过。
boto3 操作与 `aws nova-act create-workflow-definition` CLI 完全等价。
"""
from __future__ import annotations

import boto3


def ensure_workflow_definition(name: str, *, region: str = "us-east-1", description: str | None = None) -> str:
    """确保名为 `name` 的 workflow definition 存在；返回 'exists' 或 'created'。"""
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
