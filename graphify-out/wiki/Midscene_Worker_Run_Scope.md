# Midscene Worker Run Scope

> 27 nodes · cohesion 0.11

## Key Concepts

- **run-scope.mts** (36 connections) — `engines/midscene/src/worker/run-scope.mts`
- **main()** (9 connections) — `engines/midscene/src/worker/run-scope.mts`
- **runScenario()** (5 connections) — `engines/midscene/src/worker/run-scope.mts`
- **runStep()** (5 connections) — `engines/midscene/src/worker/run-scope.mts`
- **cumulativeTokens()** (3 connections) — `engines/midscene/src/worker/run-scope.mts`
- **isTransientNetwork()** (3 connections) — `engines/midscene/src/worker/run-scope.mts`
- **log()** (3 connections) — `engines/midscene/src/worker/run-scope.mts`
- **shutdownSequence()** (3 connections) — `engines/midscene/src/worker/run-scope.mts`
- **stepCost()** (3 connections) — `engines/midscene/src/worker/run-scope.mts`
- **aggregate()** (2 connections) — `engines/midscene/src/worker/run-scope.mts`
- **interruptSnapshot()** (2 connections) — `engines/midscene/src/worker/run-scope.mts`
- **modelConfig()** (2 connections) — `engines/midscene/src/worker/run-scope.mts`
- **step()** (2 connections) — `engines/midscene/src/worker/run-scope.test.mts`
- **writeStdoutFlushed()** (2 connections) — `engines/midscene/src/worker/run-scope.mts`
- **ADR-0019** (1 connections) — `engines/midscene/src/worker/run-scope.mts`
- **ADR-0026** (1 connections) — `engines/midscene/src/worker/run-scope.mts`
- **ADR-0027** (1 connections) — `engines/midscene/src/worker/run-scope.mts`
- **ADR-0032** (1 connections) — `engines/midscene/src/worker/run-scope.mts`
- **ADR-0035** (1 connections) — `engines/midscene/src/worker/run-scope.mts`
- **AWS_TRANSIENT_NAMES** (1 connections) — `engines/midscene/src/worker/run-scope.mts`
- **AWS_TRANSIENT_STATUS** (1 connections) — `engines/midscene/src/worker/run-scope.mts`
- **CONNECT_BACKOFF_MS** (1 connections) — `engines/midscene/src/worker/run-scope.mts`
- **Job** (1 connections) — `engines/midscene/src/worker/run-scope.mts`
- **ADR-0020** (1 connections) — `engines/midscene/src/worker/run-scope.mts`
- **Scenario** (1 connections) — `engines/midscene/src/worker/run-scope.mts`
- *... and 2 more nodes in this community*

## Relationships

- [Midscene TS Tests](Midscene_TS_Tests.md) (6 shared connections)
- [Midscene Job Source TS](Midscene_Job_Source_TS.md) (3 shared connections)
- [Midscene TS Hooks & ADRs](Midscene_TS_Hooks_%26_ADRs.md) (3 shared connections)
- [TypeScript Spike Probes](TypeScript_Spike_Probes.md) (1 shared connections)

## Source Files

- `engines/midscene/src/worker/run-scope.mts`
- `engines/midscene/src/worker/run-scope.test.mts`

## Audit Trail

- EXTRACTED: 51 (96%)
- INFERRED: 2 (4%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*