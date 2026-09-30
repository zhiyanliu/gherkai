# Reconciler Mechanism Concepts

> 48 nodes · cohesion 0.05

## Key Concepts

- **SKILL.md（住 CLI 包内、随 wheel 发行的单份内容）** (8 connections) — `docs/adr/0043-agent-skill-for-driving-gherkai.md`
- **gherkai deploy push-worker 流程** (7 connections) — `docs/adr/0038-worker-image-delivery.md`
- **reconcile.tick（四宿主一份的推进入口）** (6 connections) — `docs/adr/0034-detached-batch-reconciler.md`
- **gherkai explain（判定树 + 证据合成视图）** (6 connections) — `docs/adr/0042-step-evidence-and-explain.md`
- **worker --capabilities 能力自述入口** (5 connections) — `docs/adr/0036-deterministic-capability-discovery.md`
- **版本 skew 检查（三态）** (5 connections) — `docs/adr/0037-distribution-and-packaging.md`
- **ADR 0040 使用方角色模型与术语** (5 connections) — `docs/adr/0040-consumer-role-model-and-terminology.md`
- **gherkai doctor（按组件分组的只读自检）** (5 connections) — `docs/adr/0041-agent-facing-cli-affordances.md`
- **CQRS + 无状态 reconciler 机制** (4 connections) — `docs/adr/0034-detached-batch-reconciler.md`
- **退出观察者（平台侧读 exitCode 写 task_exited）** (4 connections) — `docs/adr/0034-detached-batch-reconciler.md`
- **project()：纯归约全量重放投影** (4 connections) — `docs/adr/0034-detached-batch-reconciler.md`
- **--expose-local 与 URL 映射** (4 connections) — `docs/adr/0035-local-app-testing-via-tunnel.md`
- **steps/ 定制面（随 definition 走的 GHERKAI_STEPS_DIR）** (4 connections) — `docs/adr/0037-distribution-and-packaging.md`
- **四顶帽子（feature 作者 / 测试开发 / 部署方 / contributor）** (4 connections) — `docs/adr/0040-consumer-role-model-and-terminology.md`
- **evidence（worker 产的 gherkai 自有 schema 机读证据）** (4 connections) — `docs/adr/0042-step-evidence-and-explain.md`
- **detached 顶层标记（推进链只碰 detached run）** (3 connections) — `docs/adr/0034-detached-batch-reconciler.md`
- **events 表（append-only 真值日志）** (3 connections) — `docs/adr/0034-detached-batch-reconciler.md`
- **job timeout（definition 载体 + 三路推进器各自 enforce）** (3 connections) — `docs/adr/0034-detached-batch-reconciler.md`
- **RunState 物化读视图（单一读接口不变量）** (3 connections) — `docs/adr/0034-detached-batch-reconciler.md`
- **git tag 唯一版本真源 + 兄弟包 == 同版本 pin** (3 connections) — `docs/adr/0037-distribution-and-packaging.md`
- **uv workspace 五包 + 三名分离** (3 connections) — `docs/adr/0037-distribution-and-packaging.md`
- **产品文案零内部指代（禁词护栏）** (3 connections) — `docs/adr/0039-user-facing-surfaces-no-internal-references.md`
- **CLI JSON 字段契约文档与真值集护栏** (3 connections) — `docs/adr/0041-agent-facing-cli-affordances.md`
- **scenario 筛选（--scope / --tags / --scenario）** (3 connections) — `docs/adr/0041-agent-facing-cli-affordances.md`
- **kicker Lambda（冷启动推进器）** (2 connections) — `docs/adr/0034-detached-batch-reconciler.md`
- *... and 23 more nodes in this community*

## Relationships

- [Package Contributor Docs](Package_Contributor_Docs.md) (15 shared connections)
- [Agent Skill ADRs](Agent_Skill_ADRs.md) (2 shared connections)

## Source Files

- `docs/adr/0034-detached-batch-reconciler.md`
- `docs/adr/0035-local-app-testing-via-tunnel.md`
- `docs/adr/0036-deterministic-capability-discovery.md`
- `docs/adr/0037-distribution-and-packaging.md`
- `docs/adr/0038-worker-image-delivery.md`
- `docs/adr/0039-user-facing-surfaces-no-internal-references.md`
- `docs/adr/0040-consumer-role-model-and-terminology.md`
- `docs/adr/0041-agent-facing-cli-affordances.md`
- `docs/adr/0042-step-evidence-and-explain.md`
- `docs/adr/0043-agent-skill-for-driving-gherkai.md`

## Audit Trail

- EXTRACTED: 77 (97%)
- INFERRED: 2 (3%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*