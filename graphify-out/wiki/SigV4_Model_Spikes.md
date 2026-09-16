# SigV4 Model Spikes

> 24 nodes · cohesion 0.11

## Key Concepts

- **ADR-0033** (9 connections) — `engines/midscene/src/lib/event-sink.mts`
- **agentcore-sigv4.mts** (8 connections) — `engines/midscene/src/lib/agentcore-sigv4.mts`
- **sigv4Fetch()** (7 connections) — `engines/midscene/src/lib/agentcore-sigv4.mts`
- **01-model-sigv4.ts** (6 connections) — `engines/midscene/spikes/01-model-sigv4.ts`
- **05-negative-assertions.ts** (6 connections) — `engines/midscene/spikes/05-negative-assertions.ts`
- **getRegion()** (4 connections) — `engines/midscene/src/lib/agentcore-sigv4.mts`
- **main()** (3 connections) — `engines/midscene/spikes/01-model-sigv4.ts`
- **04-planning-probe.ts** (3 connections) — `engines/midscene/spikes/04-planning-probe.ts`
- **modelSigner_()** (3 connections) — `engines/midscene/src/lib/agentcore-sigv4.mts`
- **makePng()** (2 connections) — `engines/midscene/spikes/01-model-sigv4.ts`
- **main()** (2 connections) — `engines/midscene/spikes/04-planning-probe.ts`
- **main()** (2 connections) — `engines/midscene/spikes/05-negative-assertions.ts`
- **getBaseUrl()** (2 connections) — `engines/midscene/src/lib/agentcore-sigv4.mts`
- **signCdpUpgrade()** (2 connections) — `engines/midscene/src/lib/agentcore-sigv4.mts`
- **agentcore-sigv4.test.mts** (2 connections) — `engines/midscene/src/worker/agentcore-sigv4.test.mts`
- **BASE_URL** (1 connections) — `engines/midscene/spikes/01-model-sigv4.ts`
- **REGION** (1 connections) — `engines/midscene/spikes/01-model-sigv4.ts`
- **BASE_URL** (1 connections) — `engines/midscene/spikes/04-planning-probe.ts`
- **BASE_URL** (1 connections) — `engines/midscene/spikes/05-negative-assertions.ts`
- **Check** (1 connections) — `engines/midscene/spikes/05-negative-assertions.ts`
- **MODEL_CONFIG** (1 connections) — `engines/midscene/spikes/05-negative-assertions.ts`
- **REGION** (1 connections) — `engines/midscene/spikes/05-negative-assertions.ts`
- **MODEL** (1 connections) — `engines/midscene/src/lib/agentcore-sigv4.mts`
- **withRegion()** (1 connections) — `engines/midscene/src/worker/agentcore-sigv4.test.mts`

## Relationships

- [Midscene Worker Entry & SigV4](Midscene_Worker_Entry_%26_SigV4.md) (3 shared connections)
- [TS Event Sink & Upload](TS_Event_Sink_%26_Upload.md) (3 shared connections)
- [TypeScript Deterministic Hooks](TypeScript_Deterministic_Hooks.md) (1 shared connections)
- [Run Scope (TS Worker)](Run_Scope_%28TS_Worker%29.md) (1 shared connections)

## Source Files

- `engines/midscene/spikes/01-model-sigv4.ts`
- `engines/midscene/spikes/04-planning-probe.ts`
- `engines/midscene/spikes/05-negative-assertions.ts`
- `engines/midscene/src/lib/agentcore-sigv4.mts`
- `engines/midscene/src/lib/event-sink.mts`
- `engines/midscene/src/worker/agentcore-sigv4.test.mts`

## Audit Trail

- EXTRACTED: 34 (87%)
- INFERRED: 5 (13%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*