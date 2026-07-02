"""Nova Act 引擎的共享常量（单一真理源）。

生产 worker（worker/run_scope.py）与 spike 脚本（spikes/*.py）共享同一 MODEL_ID / WORKFLOW_DEF，
避免各处硬编码同一值漂移。**bdd/ 层不 import 此模块**（该层已由 ADR 0022 决定退役、待删，不为它接线）。

注：WORKFLOW_DEF 值 'spike-wikipedia-benchmark' 沿用自 spike 阶段——它对应云端已建的 workflow
definition（ADR 0004），改名需在 AWS 上重建，故保留此名（非代码可单方改的量）。
"""
from __future__ import annotations

MODEL_ID = "nova-act-latest"
WORKFLOW_DEF = "spike-wikipedia-benchmark"
