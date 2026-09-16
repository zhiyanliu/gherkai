# CLI Usability & Evidence Docs

> 39 nodes · cohesion 0.07

## Key Concepts

- **ADR 0042: step 证据与 explain** (22 connections) — `docs/adr/0042-step-evidence-and-explain.md`
- **ADR 0043 agent skill** (17 connections) — `docs/adr/0043-agent-skill-for-driving-gherkai.md`
- **ADR 0041: 面向 agent 的 CLI 可用性** (16 connections) — `docs/adr/0041-agent-facing-cli-affordances.md`
- **ADR 0039 用户可见面不带内部指代：产品文案与文档分层** (9 connections) — `docs/adr/0039-user-facing-surfaces-no-internal-references.md`
- **SKILL.md 住 cli/gherkai_cli/skills/gherkai/、随 wheel 发行** (8 connections) — `docs/adr/0043-agent-skill-for-driving-gherkai.md`
- **gherkai explain（判定树 + 证据合成，退出码只用 0/2）** (6 connections) — `docs/adr/0042-step-evidence-and-explain.md`
- **materialize.py（物化 / --prepare-cli / --snapshot）** (5 connections) — `docs/adr/0043-agent-skill-for-driving-gherkai.md`
- **gherkai agent skill（SKILL.md + 4 份 references）** (5 connections) — `docs/adr/0043-agent-skill-for-driving-gherkai.md`
- **gherkai skill install（整目录收敛 + 版本标记）** (5 connections) — `docs/adr/0043-agent-skill-for-driving-gherkai.md`
- **决策七：评测与迭代（skill-creator 循环）** (4 connections) — `docs/adr/0043-agent-skill-for-driving-gherkai.md`
- **run_evals.py（行为评测驱动）** (4 connections) — `docs/adr/0043-agent-skill-for-driving-gherkai.md`
- **cli-json-contract.md 字段契约 + 真值集对照护栏** (3 connections) — `docs/adr/0041-agent-facing-cli-affordances.md`
- **fixtures/（物化式被测项目夹具）** (3 connections) — `docs/adr/0043-agent-skill-for-driving-gherkai.md`
- **tools/render_skill_contract.py（契约页确定性转换）** (3 connections) — `docs/adr/0043-agent-skill-for-driving-gherkai.md`
- **cli/tests/test_skill.py（skill 护栏）** (3 connections) — `docs/adr/0043-agent-skill-for-driving-gherkai.md`
- **trigger_eval.py（触发率驱动）** (3 connections) — `docs/adr/0043-agent-skill-for-driving-gherkai.md`
- **worker --list-deterministic dump 模式与 CLI list-deterministic** (2 connections) — `docs/adr/0036-deterministic-capability-discovery.md`
- **禁词表与相对链接护栏（_doc_rules 共享常量）** (2 connections) — `docs/adr/0039-user-facing-surfaces-no-internal-references.md`
- **gherkai doctor 只读自检** (2 connections) — `docs/adr/0041-agent-facing-cli-affordances.md`
- **scenario 筛选 --scope/--tags/--scenario** (2 connections) — `docs/adr/0041-agent-facing-cli-affordances.md`
- **evidence.json（worker 在 step 边界产的 gherkai 自有 schema）** (2 connections) — `docs/adr/0042-step-evidence-and-explain.md`
- **StepResult.message 落进 jobs/*.json** (2 connections) — `docs/adr/0042-step-evidence-and-explain.md`
- **去污染硬规则（CLI 只读记哈希 / 舞台路径随机 / skill 副本不可枚举）** (2 connections) — `docs/adr/0043-agent-skill-for-driving-gherkai.md`
- **验证：四模型两臂评测结果（第三–五轮）** (2 connections) — `docs/adr/0043-agent-skill-for-driving-gherkai.md`
- **evals.json（行为评测集）** (2 connections) — `docs/adr/0043-agent-skill-for-driving-gherkai.md`
- *... and 14 more nodes in this community*

## Relationships

- [Architecture ADR Decisions](Architecture_ADR_Decisions.md) (13 shared connections)
- [Project Conventions Docs](Project_Conventions_Docs.md) (8 shared connections)
- [Execution Model Concepts](Execution_Model_Concepts.md) (8 shared connections)
- [DynamoDB Events Transport](DynamoDB_Events_Transport.md) (6 shared connections)
- [Architecture Decision Records](Architecture_Decision_Records.md) (4 shared connections)
- [Termination & Engine Ports](Termination_%26_Engine_Ports.md) (3 shared connections)
- [CLI Docs & Skill References](CLI_Docs_%26_Skill_References.md) (2 shared connections)

## Source Files

- `docs/adr/0036-deterministic-capability-discovery.md`
- `docs/adr/0039-user-facing-surfaces-no-internal-references.md`
- `docs/adr/0041-agent-facing-cli-affordances.md`
- `docs/adr/0042-step-evidence-and-explain.md`
- `docs/adr/0043-agent-skill-for-driving-gherkai.md`
- `docs/guides/artifacts-and-evidence.md`

## Audit Trail

- EXTRACTED: 97 (98%)
- INFERRED: 2 (2%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*