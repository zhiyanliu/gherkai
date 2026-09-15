"""Nova Act 引擎的共享常量（单一真理源）。

生产 worker（本包 `run_scope.py`）与 spike 脚本（repo 里的 `engines/novaact/spikes/*.py`，不随包发行）
共享同一 MODEL_ID / WORKFLOW_DEF，避免各处硬编码同一值漂移。（v0.x BDD 层已由 ADR 0022 退役删除，不再是共享方。）

WORKFLOW_DEF 取**产品名**：`workflow_setup.py` 的 create-if-not-exists 会在**每个使用方账户**里建出这个
definition（ADR 0004），名字直接出现在使用方自己的 AWS 控制台，故不留试验期代号。
改这个值**无迁移成本**：云端按新名自动建出、无需手动重建，部署侧 IAM 刻意用 `workflow-definition/*` 通配、
不 pin 具体名（ADR 0033）；唯一代价是旧名那个 definition 留在账户里不再被引用（无副作用，其历史 run 仍在旧名下）。
"""
from __future__ import annotations

MODEL_ID = "nova-act-latest"
WORKFLOW_DEF = "gherkai-worker"
