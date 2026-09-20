# Docs & Terminology ADRs

> 22 nodes · cohesion 0.12

## Key Concepts

- **ADR 0043: 驾驭 gherkai 的 agent skill** (10 connections) — `docs/adr/0043-agent-skill-for-driving-gherkai.md`
- **ADR 0041 面向 agent 的 CLI 能力** (8 connections) — `docs/adr/0041-agent-facing-cli-affordances.md`
- **ADR 0042: step 级机读证据（evidence）与 gherkai explain** (8 connections) — `docs/adr/0042-step-evidence-and-explain.md`
- **ADR 0039: 用户可见面不带内部指代：产品文案与文档分层** (7 connections) — `docs/adr/0039-user-facing-surfaces-no-internal-references.md`
- **ADR 0040: 使用方角色模型与术语** (7 connections) — `docs/adr/0040-consumer-role-model-and-terminology.md`
- **evidence.json：gherkai 自有 schema 的 step 级证据** (5 connections) — `docs/adr/0042-step-evidence-and-explain.md`
- **gherkai explain：判定树 + 证据合成视图** (5 connections) — `docs/adr/0042-step-evidence-and-explain.md`
- **JSON 字段契约文档 + 真值集对照护栏** (3 connections) — `docs/adr/0041-agent-facing-cli-affordances.md`
- **ADR 0027 run 报告归集索引** (2 connections) — `docs/adr/0027-runreport-aggregation-index.md`
- **产品文案零内部指代（禁词表 + AST 扫描护栏）** (2 connections) — `docs/adr/0039-user-facing-surfaces-no-internal-references.md`
- **引擎 SDK 钉精确版本 + 格式漂移四道防线** (2 connections) — `docs/adr/0042-step-evidence-and-explain.md`
- **StepResult.message 落盘与展示** (2 connections) — `docs/adr/0042-step-evidence-and-explain.md`
- **契约页副本 = 确定性转换而非 link 或拷贝** (2 connections) — `docs/adr/0043-agent-skill-for-driving-gherkai.md`
- **skill 源住 cli/gherkai_cli/skills/gherkai/，随 wheel 发行** (2 connections) — `docs/adr/0043-agent-skill-for-driving-gherkai.md`
- **默认模型锁定、随发版评测升级** (2 connections) — `docs/adr/0044-engine-model-selection-and-override.md`
- **README / DEVELOPMENT 按读者分层** (1 connections) — `docs/adr/0039-user-facing-surfaces-no-internal-references.md`
- **执行权限梯级（执行方式 × 执行后端正交轴）** (1 connections) — `docs/adr/0040-consumer-role-model-and-terminology.md`
- **四顶帽子（feature 作者 / 测试开发 / 部署方 / contributor）** (1 connections) — `docs/adr/0040-consumer-role-model-and-terminology.md`
- **--quiet 把 worker 日志落盘 worker.log** (1 connections) — `docs/adr/0041-agent-facing-cli-affordances.md`
- **scenario 筛选：--scope / --tags / --scenario** (1 connections) — `docs/adr/0041-agent-facing-cli-affordances.md`
- **evidence 为 best-effort、对判定零影响（具名例外）** (1 connections) — `docs/adr/0042-step-evidence-and-explain.md`
- **skill 评测循环（两臂对标、去污染硬规则、触发率）** (1 connections) — `docs/adr/0043-agent-skill-for-driving-gherkai.md`

## Relationships

- [Tunnel & Capability ADRs](Tunnel_%26_Capability_ADRs.md) (7 shared connections)
- [AWS Architecture ADRs](AWS_Architecture_ADRs.md) (5 shared connections)
- [Architecture ADRs (Core)](Architecture_ADRs_%28Core%29.md) (4 shared connections)
- [Contributor Guardrail Docs](Contributor_Guardrail_Docs.md) (2 shared connections)

## Source Files

- `docs/adr/0027-runreport-aggregation-index.md`
- `docs/adr/0039-user-facing-surfaces-no-internal-references.md`
- `docs/adr/0040-consumer-role-model-and-terminology.md`
- `docs/adr/0041-agent-facing-cli-affordances.md`
- `docs/adr/0042-step-evidence-and-explain.md`
- `docs/adr/0043-agent-skill-for-driving-gherkai.md`
- `docs/adr/0044-engine-model-selection-and-override.md`

## Audit Trail

- EXTRACTED: 46 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*