# Skill and Packaging Features

> 38 nodes · cohesion 0.07

## Key Concepts

- **ADR 0041 面向 agent 的 CLI 可用性** (14 connections) — `docs/adr/0041-agent-facing-cli-affordances.md`
- **SKILL.md（住 CLI 包内、随 wheel 发行的单份内容）** (8 connections) — `docs/adr/0043-agent-skill-for-driving-gherkai.md`
- **gherkai deploy push-worker 流程** (7 connections) — `docs/adr/0038-worker-image-delivery.md`
- **ADR 0039 用户可见面不带内部指代：产品文案与文档分层** (6 connections) — `docs/adr/0039-user-facing-surfaces-no-internal-references.md`
- **gherkai explain（判定树 + 证据合成视图）** (6 connections) — `docs/adr/0042-step-evidence-and-explain.md`
- **worker --capabilities 能力自述入口** (5 connections) — `docs/adr/0036-deterministic-capability-discovery.md`
- **版本 skew 检查（三态）** (5 connections) — `docs/adr/0037-distribution-and-packaging.md`
- **ADR 0040 使用方角色模型与术语** (5 connections) — `docs/adr/0040-consumer-role-model-and-terminology.md`
- **gherkai doctor（按组件分组的只读自检）** (5 connections) — `docs/adr/0041-agent-facing-cli-affordances.md`
- **--expose-local 与 URL 映射** (4 connections) — `docs/adr/0035-local-app-testing-via-tunnel.md`
- **steps/ 定制面（随 definition 走的 GHERKAI_STEPS_DIR）** (4 connections) — `docs/adr/0037-distribution-and-packaging.md`
- **四顶帽子（feature 作者 / 测试开发 / 部署方 / contributor）** (4 connections) — `docs/adr/0040-consumer-role-model-and-terminology.md`
- **evidence（worker 产的 gherkai 自有 schema 机读证据）** (4 connections) — `docs/adr/0042-step-evidence-and-explain.md`
- **SKILL.md（随 CLI wheel 发行的 agent skill）** (3 connections) — `cli/gherkai_cli/skills/gherkai/SKILL.md`
- **git tag 唯一版本真源 + 兄弟包 == 同版本 pin** (3 connections) — `docs/adr/0037-distribution-and-packaging.md`
- **uv workspace 五包 + 三名分离** (3 connections) — `docs/adr/0037-distribution-and-packaging.md`
- **产品文案零内部指代（禁词护栏）** (3 connections) — `docs/adr/0039-user-facing-surfaces-no-internal-references.md`
- **CLI JSON 字段契约文档与真值集护栏** (3 connections) — `docs/adr/0041-agent-facing-cli-affordances.md`
- **scenario 筛选（--scope / --tags / --scenario）** (3 connections) — `docs/adr/0041-agent-facing-cli-affordances.md`
- **隧道凭据脱敏（剥 URL userinfo）** (2 connections) — `docs/adr/0035-local-app-testing-via-tunnel.md`
- **RunMeta.extra_http_headers 注入通道** (2 connections) — `docs/adr/0035-local-app-testing-via-tunnel.md`
- **CLI list-deterministic --engine** (2 connections) — `docs/adr/0036-deterministic-capability-discovery.md`
- **默认 variant 指针（SSM，升级不重置）** (2 connections) — `docs/adr/0038-worker-image-delivery.md`
- **variant（具名确定性 step 集 = 一个定制镜像）** (2 connections) — `docs/adr/0038-worker-image-delivery.md`
- **执行权限梯级（执行是正交轴）** (2 connections) — `docs/adr/0040-consumer-role-model-and-terminology.md`
- *... and 13 more nodes in this community*

## Relationships

- [CLI Docs and ADRs](CLI_Docs_and_ADRs.md) (8 shared connections)
- [Skill and Release ADRs](Skill_and_Release_ADRs.md) (5 shared connections)
- [Core Protocol Documentation](Core_Protocol_Documentation.md) (5 shared connections)
- [Detached Run Mechanisms](Detached_Run_Mechanisms.md) (3 shared connections)
- [Architecture Diagrams](Architecture_Diagrams.md) (3 shared connections)

## Source Files

- `cli/gherkai_cli/skills/gherkai/SKILL.md`
- `docs/adr/0035-local-app-testing-via-tunnel.md`
- `docs/adr/0036-deterministic-capability-discovery.md`
- `docs/adr/0037-distribution-and-packaging.md`
- `docs/adr/0038-worker-image-delivery.md`
- `docs/adr/0039-user-facing-surfaces-no-internal-references.md`
- `docs/adr/0040-consumer-role-model-and-terminology.md`
- `docs/adr/0041-agent-facing-cli-affordances.md`
- `docs/adr/0042-step-evidence-and-explain.md`
- `docs/adr/0043-agent-skill-for-driving-gherkai.md`
- `docs/adr/0047-cli-human-readable-tables-with-rich.md`
- `docs/internals/cli-json-contract.md`

## Audit Trail

- EXTRACTED: 73 (99%)
- INFERRED: 1 (1%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*