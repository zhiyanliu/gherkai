# Foundational ADRs

> 20 nodes · cohesion 0.13

## Key Concepts

- **代码健康度复盘任务说明** (10 connections) — `docs/code-health-review.md`
- **ADR 0003 Qwen3-VL 定位** (8 connections) — `docs/adr/0003-midscene-grounding-qwen3vl-bedrock.md`
- **ADR 0001 框架范围限定为英文 UI** (6 connections) — `docs/adr/0001-scope-limited-to-english-ui.md`
- **ADR 0010 spike 作对标基准** (6 connections) — `docs/adr/0010-spike-as-apples-to-apples-benchmark.md`
- **ADR 0009 最大化使用 AWS 是硬前提** (5 connections) — `docs/adr/0009-maximize-aws-hard-constraint.md`
- **@gherkai/worker-midscene README** (5 connections) — `engines/midscene/README.md`
- **SIGV4-FETCH-RECIPE.md** (5 connections) — `engines/midscene/spikes/SIGV4-FETCH-RECIPE.md`
- **ADR 0002 不用 gpt-5.5** (4 connections) — `docs/adr/0002-midscene-not-driven-by-gpt55.md`
- **sigv4Fetch custom fetch** (3 connections) — `engines/midscene/spikes/SIGV4-FETCH-RECIPE.md`
- **Lambda handler 入口（lambdas/）** (2 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/`
- **ADR 0024 engine 只报原生量、core 不折美元** (2 connections) — `docs/code-health-review.md`
- **ADR 0027 core 不透明搬运产物** (2 connections) — `docs/code-health-review.md`
- **图扫的盲区与 grep 强制基线** (2 connections) — `docs/code-health-review.md`
- **Qwen3-VL 235B on Bedrock (grounding model)** (2 connections) — `engines/midscene/README.md`
- **ADR 0026 纯 reducer 不臆断因果** (1 connections) — `docs/code-health-review.md`
- **ADR 0034 reconcile 为 core 纯函数、副作用在 adapter** (1 connections) — `docs/code-health-review.md`
- **GHERKAI_STEPS_DIR env contract** (1 connections) — `engines/midscene/DEVELOPMENT.md`
- **AgentCore cloud browser (CDP)** (1 connections) — `engines/midscene/README.md`
- **Deterministic step (user-authored)** (1 connections) — `engines/midscene/README.md`
- **createOpenAIClient injection** (1 connections) — `engines/midscene/spikes/SIGV4-FETCH-RECIPE.md`

## Relationships

- [Architecture Decision Records](Architecture_Decision_Records.md) (15 shared connections)
- [Deploy Docs](Deploy_Docs.md) (3 shared connections)

## Source Files

- `deploy_aws/gherkai_deploy_aws/lambdas/`
- `docs/adr/0001-scope-limited-to-english-ui.md`
- `docs/adr/0002-midscene-not-driven-by-gpt55.md`
- `docs/adr/0003-midscene-grounding-qwen3vl-bedrock.md`
- `docs/adr/0009-maximize-aws-hard-constraint.md`
- `docs/adr/0010-spike-as-apples-to-apples-benchmark.md`
- `docs/code-health-review.md`
- `engines/midscene/DEVELOPMENT.md`
- `engines/midscene/README.md`
- `engines/midscene/spikes/SIGV4-FETCH-RECIPE.md`

## Audit Trail

- EXTRACTED: 43 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*