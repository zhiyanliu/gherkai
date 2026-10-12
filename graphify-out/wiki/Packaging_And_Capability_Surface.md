# Packaging And Capability Surface

> 39 nodes · cohesion 0.06

## Key Concepts

- **ADR 0043: 随 CLI 发行的 agent skill** (14 connections) — `docs/adr/0043-agent-skill-for-driving-gherkai.md`
- **ADR 0041: 面向 agent 的 CLI 能力** (10 connections) — `docs/adr/0041-agent-facing-cli-affordances.md`
- **ADR 0039: 用户可见面不带内部指代与文档分层** (8 connections) — `docs/adr/0039-user-facing-surfaces-no-internal-references.md`
- **ADR 0040: 使用方角色模型与术语** (7 connections) — `docs/adr/0040-consumer-role-model-and-terminology.md`
- **gherkai deploy push-worker（推送并注册 revision）** (6 connections) — `docs/adr/0038-worker-image-delivery.md`
- **worker --capabilities 自述入口** (5 connections) — `docs/adr/0036-deterministic-capability-discovery.md`
- **steps/ 定制面（随 definition 走 + env 注入）** (5 connections) — `docs/adr/0037-distribution-and-packaging.md`
- **evidence（worker 产的 gherkai 自有 schema 机读证据）** (5 connections) — `docs/adr/0042-step-evidence-and-explain.md`
- **gherkai explain（判定树 + 证据合成视图）** (5 connections) — `docs/adr/0042-step-evidence-and-explain.md`
- **版本 skew 检查（三态）** (4 connections) — `docs/adr/0037-distribution-and-packaging.md`
- **git tag 唯一版本真源 + 兄弟包 == 同版本 pin** (4 connections) — `docs/adr/0037-distribution-and-packaging.md`
- **gherkai doctor（按组件分组的只读自检）** (4 connections) — `docs/adr/0041-agent-facing-cli-affordances.md`
- **variant（一套具名确定性 step 集 = 一个定制镜像）** (3 connections) — `docs/adr/0038-worker-image-delivery.md`
- **四顶帽子（feature 作者 / 测试开发 / 部署方 / contributor）** (3 connections) — `docs/adr/0040-consumer-role-model-and-terminology.md`
- **JSON 字段契约文档 + 真值集对照护栏** (3 connections) — `docs/adr/0041-agent-facing-cli-affordances.md`
- **RunMeta.extra_http_headers（额外请求头注入）** (2 connections) — `docs/adr/0035-local-app-testing-via-tunnel.md`
- **URL 映射（job 组装时替换 origin 前缀）** (2 connections) — `docs/adr/0035-local-app-testing-via-tunnel.md`
- **CLI list-deterministic --engine** (2 connections) — `docs/adr/0036-deterministic-capability-discovery.md`
- **CI 发布链与占名（tag 触发全链）** (2 connections) — `docs/adr/0037-distribution-and-packaging.md`
- **uv workspace 五包 + 三名分离** (2 connections) — `docs/adr/0037-distribution-and-packaging.md`
- **清理 pass（退休 tag + 静默期 + 运行中 run 引用检查）** (2 connections) — `docs/adr/0038-worker-image-delivery.md`
- **默认指针（部署级 variant 指针）** (2 connections) — `docs/adr/0038-worker-image-delivery.md`
- **运行时显式 revision（RunMeta.worker_task_defs）** (2 connections) — `docs/adr/0038-worker-image-delivery.md`
- **产品文案护栏（AST 扫禁词表）** (2 connections) — `docs/adr/0039-user-facing-surfaces-no-internal-references.md`
- **两侧 AI agent 是执行者、不立新帽子** (2 connections) — `docs/adr/0040-consumer-role-model-and-terminology.md`
- *... and 14 more nodes in this community*

## Relationships

- [Contributor Docs And ADRs](Contributor_Docs_And_ADRs.md) (9 shared connections)
- [Shared Feature Boundary ADRs](Shared_Feature_Boundary_ADRs.md) (6 shared connections)
- [Execution Architecture ADRs](Execution_Architecture_ADRs.md) (6 shared connections)
- [Engine And Model ADRs](Engine_And_Model_ADRs.md) (2 shared connections)
- [Architecture Diagram Catalog](Architecture_Diagram_Catalog.md) (2 shared connections)
- [Agent Skill Eval Harness](Agent_Skill_Eval_Harness.md) (2 shared connections)
- [Reconcile Mechanisms Overview](Reconcile_Mechanisms_Overview.md) (1 shared connections)
- [Fargate Deployment Wiring](Fargate_Deployment_Wiring.md) (1 shared connections)

## Source Files

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

- EXTRACTED: 74 (97%)
- INFERRED: 2 (3%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*