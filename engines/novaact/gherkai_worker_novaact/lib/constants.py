"""Nova Act 引擎的共享常量（单一真理源）。

生产 worker（本包 `run_scope.py`）与 spike 脚本（repo 里的 `engines/novaact/spikes/*.py`，不随包发行）
共享同一 MODEL_ID / WORKFLOW_DEF，避免各处硬编码同一值漂移。（v0.x BDD 层已由 ADR 0022 退役删除，不再是共享方。）
`NOVA_GRACE_MARGIN_S` 只被生产 worker 用（自述入口 `--capabilities` 报的 grace 下限的两个组成项之一），
放这里是因为它与上面两个同类：可 env 覆盖、有标定来历的引擎常量。

WORKFLOW_DEF 取**产品名**：`workflow_setup.py` 的 create-if-not-exists 会在**每个使用方账户**里建出这个
definition（ADR 0004），名字直接出现在使用方自己的 AWS 控制台，故不留试验期代号。
改这个值**无迁移成本**：云端按新名自动建出、无需手动重建，部署侧 IAM 刻意用 `workflow-definition/*` 通配、
不 pin 具体名（ADR 0033）；唯一代价是旧名那个 definition 留在账户里不再被引用（无副作用，其历史 run 仍在旧名下）。
"""
from __future__ import annotations

import os

MODEL_ID = "nova-act-latest"
WORKFLOW_DEF = "gherkai-worker"

# grace 余量（ADR 0024 grace 硬约束的 margin）：worker 自报的 grace 下限 = 单 act 上界（`run_scope.ACT_TIMEOUT_S`
# = 组合根注入的 `NOVA_ACT_TIMEOUT_S`）+ 本余量，经自述入口 `--capabilities` 报给组合根（ADR 0024「引擎自报
# 下限」——下限的真值是 worker 自己的收尾预算，住在算它的这一侧才不需要人工同步；曾住组合根）。
# 余量要盖住「SIGTERM 落 act 中途、act 有界返回**之后**」的收尾串行段：会话释放（三层 with 的 `__exit__`）
# + evidence 截图后台队列的退出档有界排空（`run_scope.EVIDENCE_DRAIN_EXIT_S`，排在会话释放之后，ADR 0042 决策一）。
# **已真容器标定**（ADR 0032「真容器校准结论」，4 次真跑）：SIGTERM→退出最坏 21s，但其中 ~11s 已坐实为 ECS
# 记录 executionStoppedAt 的平台侧滞后（worker 已退），subprocess 档不存在该段——真实预算 = 会话释放 ≤9s
# + 截图排空 6s = 15s，故 60→30（Nova grace 下限 180→150），30 仍留 ~2x 余量。
# （上传本体在队列线程内跑、`use_threads=False`，无 s3transfer 线程池被 atexit join 的尾巴——否则要再加一次
# client 超时 ≈10s，真跑量过。）env 可覆盖（再标定/调优）。
NOVA_GRACE_MARGIN_S = int(os.environ.get("NOVA_GRACE_MARGIN_S", "30"))
