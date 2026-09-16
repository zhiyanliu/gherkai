# Midscene Worker Entry & SigV4

> 12 nodes · cohesion 0.18

## Key Concepts

- **03-midscene-grounding.ts** (7 connections) — `engines/midscene/spikes/03-midscene-grounding.ts`
- **src/worker/run-scope.mts — main / run-scope** (5 connections) — `engines/midscene/DEVELOPMENT.md`
- **src/bin.mts — worker 唯一入口** (4 connections) — `engines/midscene/DEVELOPMENT.md`
- **sigv4Fetch 自定义 fetch** (4 connections) — `engines/midscene/spikes/SIGV4-FETCH-RECIPE.md`
- **createOpenAIClient 注入点** (3 connections) — `engines/midscene/spikes/SIGV4-FETCH-RECIPE.md`
- **src/lib/agentcore-sigv4.mts — SigV4 与 region 解析** (2 connections) — `engines/midscene/DEVELOPMENT.md`
- **main()** (2 connections) — `engines/midscene/spikes/03-midscene-grounding.ts`
- **ADR-0010** (1 connections) — `engines/midscene/spikes/03-midscene-grounding.ts`
- **src/resolve-hook.mts — 裸 specifier 解析钩子** (1 connections) — `engines/midscene/DEVELOPMENT.md`
- **BASE_URL** (1 connections) — `engines/midscene/spikes/03-midscene-grounding.ts`
- **MODEL_CONFIG** (1 connections) — `engines/midscene/spikes/03-midscene-grounding.ts`
- **REGION** (1 connections) — `engines/midscene/spikes/03-midscene-grounding.ts`

## Relationships

- [SigV4 Model Spikes](SigV4_Model_Spikes.md) (3 shared connections)
- [Engine & Protocol ADRs](Engine_%26_Protocol_ADRs.md) (2 shared connections)
- [Compose Root & ADR Links](Compose_Root_%26_ADR_Links.md) (1 shared connections)
- [Architecture Decision Records](Architecture_Decision_Records.md) (1 shared connections)
- [User Steps Loading](User_Steps_Loading.md) (1 shared connections)

## Source Files

- `engines/midscene/DEVELOPMENT.md`
- `engines/midscene/spikes/03-midscene-grounding.ts`
- `engines/midscene/spikes/SIGV4-FETCH-RECIPE.md`

## Audit Trail

- EXTRACTED: 16 (80%)
- INFERRED: 4 (20%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*