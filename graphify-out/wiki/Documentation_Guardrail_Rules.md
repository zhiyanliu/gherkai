# Documentation Guardrail Rules

> 49 nodes · cohesion 0.08

## Key Concepts

- **ADR 0043：驱动 gherkai 的 agent skill** (21 connections) — `docs/adr/0043-agent-skill-for-driving-gherkai.md`
- **ADR 0045: 文档分层与归位** (17 connections) — `docs/adr/0045-documentation-layering-and-placement.md`
- **文档健康度复盘任务说明** (9 connections) — `docs/ai-eng/doc-health-review.md`
- **render_skill_contract.py** (7 connections) — `tools/render_skill_contract.py`
- **render()** (7 connections) — `tools/render_skill_contract.py`
- **_doc_rules.py（逐行可判规则与扫描面的唯一源）** (6 connections) — `docs/adr/0046-guardrail-layers-tests-hooks-and-lean-claude-md.md`
- **ADR 0046：contributor 护栏三层** (6 connections) — `docs/adr/0046-guardrail-layers-tests-hooks-and-lean-claude-md.md`
- **代码健康度复盘任务说明** (6 connections) — `docs/ai-eng/code-health-review.md`
- **权威信息源登记（REFERENCES）** (6 connections) — `docs/ai-eng/REFERENCES.md`
- **build_diagrams.mjs（deliver 渲染 + headless 导出）** (6 connections) — `docs/adr/0045-documentation-layering-and-placement.md`
- **transform()** (6 connections) — `tools/render_skill_contract.py`
- **test_user_docs.py（用户文档与图源护栏）** (5 connections) — `docs/adr/0045-documentation-layering-and-placement.md`
- **docs/ai-eng 索引** (5 connections) — `docs/ai-eng/README.md`
- **run_evals.py（行为评测驱动）** (5 connections) — `docs/adr/0043-agent-skill-for-driving-gherkai.md`
- **TransformError** (5 connections) — `tools/render_skill_contract.py`
- **test_skill.py（skill 产品面与真值护栏）** (4 connections) — `docs/adr/0043-agent-skill-for-driving-gherkai.md`
- **ADR 0037：发行与打包** (4 connections) — `docs/adr/0037-distribution-and-packaging.md`
- **ADR 0039：使用者面零内部指代** (4 connections) — `docs/adr/0039-user-facing-surfaces-no-internal-references.md`
- **archify 图流程（JSON 图源 + 导出 SVG 入库）** (4 connections) — `docs/adr/0045-documentation-layering-and-placement.md`
- **文档图作者化方法（archify）** (4 connections) — `docs/ai-eng/diagram-authoring.md`
- **materialize.py（物化 / --prepare-cli / --snapshot）** (4 connections) — `docs/adr/0043-agent-skill-for-driving-gherkai.md`
- **_assert_clean()** (4 connections) — `tools/render_skill_contract.py`
- **ADR 0041：面向 agent 的 CLI 可操作面** (3 connections) — `docs/adr/0041-agent-facing-cli-affordances.md`
- **评测去污染硬规则（CLI 来自仓库外 wheel、skill 副本随机目录、舞台路径随机）** (3 connections) — `docs/adr/0043-agent-skill-for-driving-gherkai.md`
- **两臂评测法（with-skill 对 baseline）** (3 connections) — `docs/adr/0043-agent-skill-for-driving-gherkai.md`
- *... and 24 more nodes in this community*

## Relationships

- [Model Selection ADRs](Model_Selection_ADRs.md) (6 shared connections)
- [Cloud Backend Docs & Diagrams](Cloud_Backend_Docs_%26_Diagrams.md) (1 shared connections)
- [Project Docs & Glossary](Project_Docs_%26_Glossary.md) (1 shared connections)
- [Doc Rules Source](Doc_Rules_Source.md) (1 shared connections)
- [Worker Job Source Input](Worker_Job_Source_Input.md) (1 shared connections)

## Source Files

- `docs/adr/0001-scope-limited-to-english-ui.md`
- `docs/adr/0037-distribution-and-packaging.md`
- `docs/adr/0039-user-facing-surfaces-no-internal-references.md`
- `docs/adr/0041-agent-facing-cli-affordances.md`
- `docs/adr/0043-agent-skill-for-driving-gherkai.md`
- `docs/adr/0045-documentation-layering-and-placement.md`
- `docs/adr/0046-guardrail-layers-tests-hooks-and-lean-claude-md.md`
- `docs/adr/0047-cli-human-readable-tables-with-rich.md`
- `docs/ai-eng/README.md`
- `docs/ai-eng/REFERENCES.md`
- `docs/ai-eng/code-health-review.md`
- `docs/ai-eng/diagram-authoring.md`
- `docs/ai-eng/doc-health-review.md`
- `docs/diagrams/architecture-overview-layers.svg`
- `docs/diagrams/architecture-overview-run-lifecycle.svg`
- `tools/render_skill_contract.py`

## Audit Trail

- EXTRACTED: 97 (94%)
- INFERRED: 6 (6%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*