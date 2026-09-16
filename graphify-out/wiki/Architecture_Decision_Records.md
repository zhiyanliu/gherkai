# Architecture Decision Records

> 15 nodes · cohesion 0.27

## Key Concepts

- **ADR 0001 范围限定英文 UI** (15 connections) — `docs/adr/0001-scope-limited-to-english-ui.md`
- **ADR 0035 经隧道测本机应用** (15 connections) — `docs/adr/0035-local-app-testing-via-tunnel.md`
- **权威信息源（自查用）REFERENCES** (15 connections) — `docs/REFERENCES.md`
- **ADR 0010: spike 作同题基准** (12 connections) — `docs/adr/0010-spike-as-apples-to-apples-benchmark.md`
- **ADR 0003 Midscene grounding 用 Bedrock Qwen3-VL** (9 connections) — `docs/adr/0003-midscene-grounding-qwen3vl-bedrock.md`
- **ADR 0009 最大化使用 AWS 是硬前提** (9 connections) — `docs/adr/0009-maximize-aws-hard-constraint.md`
- **SIGV4-FETCH-RECIPE 配方笔记** (8 connections) — `engines/midscene/spikes/SIGV4-FETCH-RECIPE.md`
- **ADR 0008: Midscene→Bedrock SigV4 自签鉴权** (6 connections) — `docs/adr/0008-midscene-bedrock-auth-sigv4-selfsign.md`
- **ADR 0004: Nova Act IAM 鉴权经 Workflow** (5 connections) — `docs/adr/0004-novaact-iam-auth-via-workflow.md`
- **ADR 0002 Midscene 不用 Bedrock GPT-5.5** (3 connections) — `docs/adr/0002-midscene-not-driven-by-gpt55.md`
- **ADR 0007 程序化登录，HITL 仅作调试逃生舱** (3 connections) — `docs/adr/0007-programmatic-login-hitl-as-escape-hatch.md`
- **ADR 0011 AgentCore 浏览器：默认 vs 自建** (3 connections) — `docs/adr/0011-agentcore-browser-system-default-vs-custom.md`
- **ADR 0012 planning 复用 Qwen3-VL、不引独立文本规划器** (3 connections) — `docs/adr/0012-planning-shares-qwen3vl-no-text-planner.md`
- **URL 映射：feature 写原始地址、组装 job 时替换** (2 connections) — `docs/adr/0035-local-app-testing-via-tunnel.md`
- **TunnelProvider 可插拔口子（首个实现 ngrok）** (1 connections) — `docs/adr/0035-local-app-testing-via-tunnel.md`

## Relationships

- [Architecture ADR Decisions](Architecture_ADR_Decisions.md) (21 shared connections)
- [Project Conventions Docs](Project_Conventions_Docs.md) (12 shared connections)
- [CLI Usability & Evidence Docs](CLI_Usability_%26_Evidence_Docs.md) (4 shared connections)
- [CLI Docs & Skill References](CLI_Docs_%26_Skill_References.md) (3 shared connections)
- [Domain Glossary](Domain_Glossary.md) (3 shared connections)
- [DynamoDB Events Transport](DynamoDB_Events_Transport.md) (3 shared connections)
- [Engine & Protocol ADRs](Engine_%26_Protocol_ADRs.md) (3 shared connections)
- [Termination & Engine Ports](Termination_%26_Engine_Ports.md) (1 shared connections)
- [Execution Model Concepts](Execution_Model_Concepts.md) (1 shared connections)
- [Cloud Run State Mechanisms](Cloud_Run_State_Mechanisms.md) (1 shared connections)
- [Midscene Worker Entry & SigV4](Midscene_Worker_Entry_%26_SigV4.md) (1 shared connections)

## Source Files

- `docs/REFERENCES.md`
- `docs/adr/0001-scope-limited-to-english-ui.md`
- `docs/adr/0002-midscene-not-driven-by-gpt55.md`
- `docs/adr/0003-midscene-grounding-qwen3vl-bedrock.md`
- `docs/adr/0004-novaact-iam-auth-via-workflow.md`
- `docs/adr/0007-programmatic-login-hitl-as-escape-hatch.md`
- `docs/adr/0008-midscene-bedrock-auth-sigv4-selfsign.md`
- `docs/adr/0009-maximize-aws-hard-constraint.md`
- `docs/adr/0010-spike-as-apples-to-apples-benchmark.md`
- `docs/adr/0011-agentcore-browser-system-default-vs-custom.md`
- `docs/adr/0012-planning-shares-qwen3vl-no-text-planner.md`
- `docs/adr/0035-local-app-testing-via-tunnel.md`
- `engines/midscene/spikes/SIGV4-FETCH-RECIPE.md`

## Audit Trail

- EXTRACTED: 79 (98%)
- INFERRED: 1 (1%)
- AMBIGUOUS: 1 (1%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*