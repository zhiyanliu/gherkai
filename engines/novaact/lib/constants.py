"""Nova Act 引擎的共享常量（单一真理源）。

生产 worker（worker/run_scope.py）与 spike 脚本（spikes/*.py）共享同一 MODEL_ID / WORKFLOW_DEF，
避免各处硬编码同一值漂移。（v0.x BDD 层已由 ADR 0022 退役删除，不再是共享方。）

注：WORKFLOW_DEF 值 'spike-wikipedia-benchmark' 沿用自 spike 阶段。技术上改名已可行——lib/workflow_setup.py
的 create-if-not-exists 会自动在云端建出新 definition（ADR 0004），无需手动重建；保留此名只为不把既有
definition 名下的历史 run 孤立掉。
"""
from __future__ import annotations

MODEL_ID = "nova-act-latest"
WORKFLOW_DEF = "spike-wikipedia-benchmark"
