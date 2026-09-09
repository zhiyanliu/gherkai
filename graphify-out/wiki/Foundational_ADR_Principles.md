# Foundational ADR Principles

> 14 nodes · cohesion 0.22

## Key Concepts

- **ADR 0035 隧道暴露本机应用** (11 connections) — `docs/adr/0035-local-app-testing-via-tunnel.md`
- **代码健康度复盘任务说明** (10 connections) — `docs/code-health-review.md`
- **ADR 0003 Qwen3-VL 定位** (8 connections) — `docs/adr/0003-midscene-grounding-qwen3vl-bedrock.md`
- **ADR 0001 框架范围限定为英文 UI** (6 connections) — `docs/adr/0001-scope-limited-to-english-ui.md`
- **ADR 0010 spike 作对标基准** (6 connections) — `docs/adr/0010-spike-as-apples-to-apples-benchmark.md`
- **ADR 0009 最大化使用 AWS 是硬前提** (5 connections) — `docs/adr/0009-maximize-aws-hard-constraint.md`
- **ADR 0002 不用 gpt-5.5** (4 connections) — `docs/adr/0002-midscene-not-driven-by-gpt55.md`
- **Lambda handler 入口（lambdas/）** (2 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/`
- **ADR 0024 engine 只报原生量、core 不折美元** (2 connections) — `docs/code-health-review.md`
- **ADR 0027 core 不透明搬运产物** (2 connections) — `docs/code-health-review.md`
- **图扫的盲区与 grep 强制基线** (2 connections) — `docs/code-health-review.md`
- **ADR 0011 AgentCore 浏览器：默认 vs 自建** (1 connections) — `docs/adr/0011-agentcore-browser-system-default-vs-custom.md`
- **ADR 0026 纯 reducer 不臆断因果** (1 connections) — `docs/code-health-review.md`
- **ADR 0034 reconcile 为 core 纯函数、副作用在 adapter** (1 connections) — `docs/code-health-review.md`

## Relationships

- [ADR Index & Dev Docs](ADR_Index_%26_Dev_Docs.md) (16 shared connections)
- [Deploy AWS README](Deploy_AWS_README.md) (3 shared connections)
- [Midscene Worker Integration Docs](Midscene_Worker_Integration_Docs.md) (1 shared connections)
- [Local App Tunneling (ADR 0035)](Local_App_Tunneling_%28ADR_0035%29.md) (1 shared connections)

## Source Files

- `deploy_aws/gherkai_deploy_aws/lambdas/`
- `docs/adr/0001-scope-limited-to-english-ui.md`
- `docs/adr/0002-midscene-not-driven-by-gpt55.md`
- `docs/adr/0003-midscene-grounding-qwen3vl-bedrock.md`
- `docs/adr/0009-maximize-aws-hard-constraint.md`
- `docs/adr/0010-spike-as-apples-to-apples-benchmark.md`
- `docs/adr/0011-agentcore-browser-system-default-vs-custom.md`
- `docs/adr/0035-local-app-testing-via-tunnel.md`
- `docs/code-health-review.md`

## Audit Trail

- EXTRACTED: 41 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*