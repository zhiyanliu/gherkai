"""Nova Act 引擎的共享常量（单一真理源）。

生产 worker（本包 `run_scope.py`）与 spike 脚本（repo 里的 `engines/novaact/spikes/*.py`，不随包发行）
共享同一 MODEL_ID / WORKFLOW_DEF，避免各处硬编码同一值漂移。（v0.x BDD 层已由 ADR 0022 退役删除，不再是共享方。）
`NOVA_GRACE_MARGIN_S` 只被生产 worker 用（自述入口 `--capabilities` 报的 grace 下限的两个组成项之一），
放这里是因为它与 MODEL_ID 同类：有标定/评估来历、缺省锁定值 + env 可 opt-in 覆盖的引擎常量
（WORKFLOW_DEF 不给 env 配置项——它是账户里那个 definition 的名字，改名是一次发版决定）。

WORKFLOW_DEF 取**产品名**：`workflow_setup.py` 的 create-if-not-exists 会在**每个使用方账户**里建出这个
definition（ADR 0004），名字直接出现在使用方自己的 AWS 控制台，故不留试验期代号。
改这个值**无迁移成本**：云端按新名自动建出、无需手动重建，部署侧 IAM 刻意用 `workflow-definition/*` 通配、
不 pin 具体名（ADR 0033）；唯一代价是旧名那个 definition 留在账户里不再被引用（无副作用，其历史 run 仍在旧名下）。
"""
from __future__ import annotations

import os

# 模型版本（ADR 0004「模型版本选择策略」）：**缺省锁定 GA 版本 id，不用 `nova-act-latest` 别名**——别名的
# 语义是「AWS 发新 GA 时自动换模型」、时点由 AWS 定；而本工具的 pass / fail 靠 AI 投票，模型一换判定就变
# （已 A/B 实测：同一批用例里有 scenario 在两个模型间稳定翻转，不是噪声）。这类变化必须随一次有 changelog 的
# 显式发布落地，而不是藏在别名里在使用方账户中静默发生；升级流程（新 GA → 重新运行同一批用例的 A/B → 改本常量
# → 发版点明模型换代）见该 ADR，别在这里改成别名。
# env `NOVA_MODEL_ID` 是 **opt-in 配置项**（与下面的 NOVA_GRACE_MARGIN_S 同形：worker 读、缺省即锁定值）：
# 本机执行时在 shell 里设即生效；云端 Fargate 容器 env 是显式枚举，要用就构建进定制 worker 镜像的 `ENV`（即
# ADR 0038 的 variant 机制）。可设 `nova-act-preview` 试新模型，但 **preview 不作产品默认**：无支持承诺、
# 随 AWS 移动，且**不可锁定**——服务端拒绝直接引用带日期的 preview id（只能用 `nova-act-preview` 别名），
# 正是锁定版本要消掉的那种不受控变化。
# **worker 侧不校验取值**：非法 id 由服务端拒（起会话时报错），worker 再持一份合法值清单就是第二事实源、
# 会随 AWS 上新漂移。本常量经自述入口 `--capabilities` 的 `model_id` 键报出（ADR 0036「5.」），`doctor`
# 据此显示当前模型——覆盖过 env 的机器一眼可见。
MODEL_ID = os.environ.get("NOVA_MODEL_ID", "nova-act-v1.0")
WORKFLOW_DEF = "gherkai-worker"

# grace 余量（ADR 0024 grace 硬约束的 margin）：worker 自报的 grace 下限 = 单 act 上界（`run_scope.ACT_TIMEOUT_S`
# = 组合根注入的 `NOVA_ACT_TIMEOUT_S`）+ 本余量，经自述入口 `--capabilities` 报给组合根（ADR 0024「引擎自报
# 下限」——下限的真值是 worker 自己的收尾预算，住在算它的这一侧才不需要人工同步；曾住组合根）。
# 余量要盖住「SIGTERM 落 act 中途、act 有界返回**之后**」的收尾串行段：会话释放（三层 with 的 `__exit__`）
# + evidence 截图后台队列的退出档有界排空（`run_scope.EVIDENCE_DRAIN_EXIT_S`，排在会话释放之后，ADR 0042 决策一）。
# **已真容器标定**（ADR 0032「真容器校准结论」，4 次实际运行）：SIGTERM→退出最坏 21s，但其中 ~11s 已坐实为 ECS
# 记录 executionStoppedAt 的平台侧滞后（worker 已退），subprocess 档不存在该段——真实预算 = 会话释放 ≤9s
# + 截图排空 6s = 15s，故 60→30（Nova grace 下限 180→150），30 仍留 ~2x 余量。
# （上传本体在队列线程内执行、`use_threads=False`，无 s3transfer 线程池被 atexit join 的尾巴——否则要再加一次
# client 超时 ≈10s，实际运行中量过。）env 可覆盖（再标定/调优）。
NOVA_GRACE_MARGIN_S = int(os.environ.get("NOVA_GRACE_MARGIN_S", "30"))
