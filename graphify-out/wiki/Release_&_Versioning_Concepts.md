# Release & Versioning Concepts

> 32 nodes · cohesion 0.08

## Key Concepts

- **ADR 0043: 随 CLI 发行的 agent skill** (14 connections) — `docs/adr/0043-agent-skill-for-driving-gherkai.md`
- **ADR 0041: 面向 agent 的 CLI 能力** (10 connections) — `docs/adr/0041-agent-facing-cli-affordances.md`
- **ADR 0039: 用户可见面不带内部指代与文档分层** (8 connections) — `docs/adr/0039-user-facing-surfaces-no-internal-references.md`
- **ADR 0040: 使用方角色模型与术语** (7 connections) — `docs/adr/0040-consumer-role-model-and-terminology.md`
- **gherkai deploy push-worker（推送并注册 revision）** (6 connections) — `docs/adr/0038-worker-image-delivery.md`
- **evidence（worker 产的 gherkai 自有 schema 机读证据）** (5 connections) — `docs/adr/0042-step-evidence-and-explain.md`
- **gherkai explain（判定树 + 证据合成视图）** (5 connections) — `docs/adr/0042-step-evidence-and-explain.md`
- **版本 skew 检查（三态）** (4 connections) — `docs/adr/0037-distribution-and-packaging.md`
- **git tag 唯一版本真源 + 兄弟包 == 同版本 pin** (4 connections) — `docs/adr/0037-distribution-and-packaging.md`
- **gherkai doctor（按组件分组的只读自检）** (4 connections) — `docs/adr/0041-agent-facing-cli-affordances.md`
- **四顶帽子（feature 作者 / 测试开发 / 部署方 / contributor）** (3 connections) — `docs/adr/0040-consumer-role-model-and-terminology.md`
- **JSON 字段契约文档 + 真值集对照护栏** (3 connections) — `docs/adr/0041-agent-facing-cli-affordances.md`
- **URL 映射（job 组装时替换 origin 前缀）** (2 connections) — `docs/adr/0035-local-app-testing-via-tunnel.md`
- **CLI list-deterministic --engine** (2 connections) — `docs/adr/0036-deterministic-capability-discovery.md`
- **CI 发布链与占名（tag 触发全链）** (2 connections) — `docs/adr/0037-distribution-and-packaging.md`
- **uv workspace 五包 + 三名分离** (2 connections) — `docs/adr/0037-distribution-and-packaging.md`
- **默认指针（部署级 variant 指针）** (2 connections) — `docs/adr/0038-worker-image-delivery.md`
- **产品文案护栏（AST 扫禁词表）** (2 connections) — `docs/adr/0039-user-facing-surfaces-no-internal-references.md`
- **两侧 AI agent 是执行者、不立新帽子** (2 connections) — `docs/adr/0040-consumer-role-model-and-terminology.md`
- **执行权限梯级（正交轴）** (2 connections) — `docs/adr/0040-consumer-role-model-and-terminology.md`
- **scenario 筛选（--scope / --tags / --scenario）** (2 connections) — `docs/adr/0041-agent-facing-cli-affordances.md`
- **gherkai skill install（整目录收敛 + 版本标记）** (2 connections) — `docs/adr/0043-agent-skill-for-driving-gherkai.md`
- **隧道凭据脱敏（剥 URL userinfo）** (1 connections) — `docs/adr/0035-local-app-testing-via-tunnel.md`
- **基础镜像（GHCR，零使用方内容）** (1 connections) — `docs/adr/0038-worker-image-delivery.md`
- **README / DEVELOPMENT 按读者分层** (1 connections) — `docs/adr/0039-user-facing-surfaces-no-internal-references.md`
- *... and 7 more nodes in this community*

## Relationships

- [Shared Feature Scope ADRs](Shared_Feature_Scope_ADRs.md) (9 shared connections)
- [Model Selection ADRs](Model_Selection_ADRs.md) (6 shared connections)
- [Core Library Concepts & ADRs](Core_Library_Concepts_%26_ADRs.md) (5 shared connections)
- [Cloud Backend Docs & Diagrams](Cloud_Backend_Docs_%26_Diagrams.md) (3 shared connections)
- [Agent Skill Evaluation Harness](Agent_Skill_Evaluation_Harness.md) (2 shared connections)
- [Browser And Tunnel Decisions](Browser_And_Tunnel_Decisions.md) (1 shared connections)
- [Stateless Run Advancement](Stateless_Run_Advancement.md) (1 shared connections)

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

- EXTRACTED: 63 (97%)
- INFERRED: 2 (3%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*