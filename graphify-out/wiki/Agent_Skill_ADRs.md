# Agent Skill ADRs

> 30 nodes · cohesion 0.10

## Key Concepts

- **ADR 0043 驱动 gherkai 的 agent skill** (20 connections) — `docs/adr/0043-agent-skill-for-driving-gherkai.md`
- **ADR 0045 文档分层与归位** (15 connections) — `docs/adr/0045-documentation-layering-and-placement.md`
- **ADR 0044：引擎模型的选择与覆盖** (9 connections) — `docs/adr/0044-engine-model-selection-and-override.md`
- **权威信息源登记（REFERENCES）** (6 connections) — `docs/ai-eng/REFERENCES.md`
- **ADR 0046：contributor 护栏三层** (5 connections) — `docs/adr/0046-guardrail-layers-tests-hooks-and-lean-claude-md.md`
- **docs/ai-eng 索引** (5 connections) — `docs/ai-eng/README.md`
- **文档健康度复盘任务指令** (4 connections) — `docs/ai-eng/doc-health-review.md`
- **ADR 0004：Nova Act 经 Workflow 的 IAM 鉴权** (3 connections) — `docs/adr/0004-novaact-iam-auth-via-workflow.md`
- **ADR 0037：发行与打包** (3 connections) — `docs/adr/0037-distribution-and-packaging.md`
- **ADR 0039：使用者面零内部指代** (3 connections) — `docs/adr/0039-user-facing-surfaces-no-internal-references.md`
- **skill 评测资产（决策七）** (3 connections) — `docs/adr/0043-agent-skill-for-driving-gherkai.md`
- **按类别定口吻与三种 AI 侧缩写禁用** (3 connections) — `docs/adr/0045-documentation-layering-and-placement.md`
- **代码健康度复盘任务指令** (3 connections) — `docs/ai-eng/code-health-review.md`
- **文档图作者化方法（archify）** (3 connections) — `docs/ai-eng/diagram-authoring.md`
- **文档地图** (3 connections) — `docs/README.md`
- **skills/ 目录说明** (3 connections) — `skills/README.md`
- **SKILL.md（随 CLI wheel 发行的 agent skill）** (2 connections) — `cli/gherkai_cli/skills/gherkai/SKILL.md`
- **图统一用 archify：JSON 图源 + 导出 SVG 入库** (2 connections) — `docs/adr/0045-documentation-layering-and-placement.md`
- **读者三分类（contributor 侧 AI agent / 技术文档 / 用户文档）** (2 connections) — `docs/adr/0045-documentation-layering-and-placement.md`
- **评分子代理提示词模板** (2 connections) — `skills/gherkai-evals/grader-prompt.md`
- **grader-prompt.md（评分子代理提示词）** (2 connections) — `skills/gherkai-evals/grader-prompt.md`
- **gherkai agent skill 包** (1 connections) — `cli/gherkai_cli/skills/gherkai`
- **ADR 0036：确定性能力自述与发现** (1 connections) — `docs/adr/0036-deterministic-capability-discovery.md`
- **默认模型锁定、随发版评估升级** (1 connections) — `docs/adr/0044-engine-model-selection-and-override.md`
- **按引擎 env 覆盖（两引擎对称）** (1 connections) — `docs/adr/0044-engine-model-selection-and-override.md`
- *... and 5 more nodes in this community*

## Relationships

- [Package Contributor Docs](Package_Contributor_Docs.md) (12 shared connections)
- [Architecture Diagrams](Architecture_Diagrams.md) (3 shared connections)
- [Project Conventions Docs](Project_Conventions_Docs.md) (3 shared connections)
- [Reconciler Mechanism Concepts](Reconciler_Mechanism_Concepts.md) (2 shared connections)
- [Agent Skill Reference Docs](Agent_Skill_Reference_Docs.md) (1 shared connections)
- [Core Adapters Documentation](Core_Adapters_Documentation.md) (1 shared connections)

## Source Files

- `cli/gherkai_cli/skills/gherkai`
- `cli/gherkai_cli/skills/gherkai/SKILL.md`
- `docs/README.md`
- `docs/adr/0004-novaact-iam-auth-via-workflow.md`
- `docs/adr/0036-deterministic-capability-discovery.md`
- `docs/adr/0037-distribution-and-packaging.md`
- `docs/adr/0039-user-facing-surfaces-no-internal-references.md`
- `docs/adr/0043-agent-skill-for-driving-gherkai.md`
- `docs/adr/0044-engine-model-selection-and-override.md`
- `docs/adr/0045-documentation-layering-and-placement.md`
- `docs/adr/0046-guardrail-layers-tests-hooks-and-lean-claude-md.md`
- `docs/ai-eng/README.md`
- `docs/ai-eng/REFERENCES.md`
- `docs/ai-eng/code-health-review.md`
- `docs/ai-eng/diagram-authoring.md`
- `docs/ai-eng/doc-health-review.md`
- `docs/internals/cli-json-contract.md`
- `skills/README.md`
- `skills/gherkai-evals/grader-prompt.md`

## Audit Trail

- EXTRACTED: 61 (92%)
- INFERRED: 4 (6%)
- AMBIGUOUS: 1 (2%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*