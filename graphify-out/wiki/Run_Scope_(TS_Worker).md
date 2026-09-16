# Run Scope (TS Worker)

> 29 nodes · cohesion 0.11

## Key Concepts

- **run-scope.mts** (43 connections) — `engines/midscene/src/worker/run-scope.mts`
- **main()** (11 connections) — `engines/midscene/src/worker/run-scope.mts`
- **runStep()** (6 connections) — `engines/midscene/src/worker/run-scope.mts`
- **runScenario()** (5 connections) — `engines/midscene/src/worker/run-scope.mts`
- **shutdownSequence()** (4 connections) — `engines/midscene/src/worker/run-scope.mts`
- **cumulativeTokens()** (3 connections) — `engines/midscene/src/worker/run-scope.mts`
- **drainArtifactQueue()** (3 connections) — `engines/midscene/src/worker/run-scope.mts`
- **isTransientNetwork()** (3 connections) — `engines/midscene/src/worker/run-scope.mts`
- **log()** (3 connections) — `engines/midscene/src/worker/run-scope.mts`
- **stepCost()** (3 connections) — `engines/midscene/src/worker/run-scope.mts`
- **aggregate()** (2 connections) — `engines/midscene/src/worker/run-scope.mts`
- **appendReportRef()** (2 connections) — `engines/midscene/src/worker/run-scope.mts`
- **artifactFlushRoot()** (2 connections) — `engines/midscene/src/worker/run-scope.mts`
- **interruptSnapshot()** (2 connections) — `engines/midscene/src/worker/run-scope.mts`
- **modelConfig()** (2 connections) — `engines/midscene/src/worker/run-scope.mts`
- **step()** (2 connections) — `engines/midscene/src/worker/run-scope.test.mts`
- **writeStdoutFlushed()** (2 connections) — `engines/midscene/src/worker/run-scope.mts`
- **ADR-0019** (1 connections) — `engines/midscene/src/worker/run-scope.mts`
- **ADR-0026** (1 connections) — `engines/midscene/src/worker/run-scope.mts`
- **ADR-0027** (1 connections) — `engines/midscene/src/worker/run-scope.mts`
- **ADR-0035** (1 connections) — `engines/midscene/src/worker/run-scope.mts`
- **AWS_TRANSIENT_NAMES** (1 connections) — `engines/midscene/src/worker/run-scope.mts`
- **AWS_TRANSIENT_STATUS** (1 connections) — `engines/midscene/src/worker/run-scope.mts`
- **CONNECT_BACKOFF_MS** (1 connections) — `engines/midscene/src/worker/run-scope.mts`
- **Job** (1 connections) — `engines/midscene/src/worker/run-scope.mts`
- *... and 4 more nodes in this community*

## Relationships

- [Run Scope Integration Tests](Run_Scope_Integration_Tests.md) (5 shared connections)
- [TypeScript Deterministic Hooks](TypeScript_Deterministic_Hooks.md) (4 shared connections)
- [TS Event Sink & Upload](TS_Event_Sink_%26_Upload.md) (3 shared connections)
- [Evidence Collector Tests](Evidence_Collector_Tests.md) (2 shared connections)
- [Worker Bin & Step Loading](Worker_Bin_%26_Step_Loading.md) (2 shared connections)
- [Artifact Upload & Error Text](Artifact_Upload_%26_Error_Text.md) (1 shared connections)
- [SigV4 Model Spikes](SigV4_Model_Spikes.md) (1 shared connections)

## Source Files

- `engines/midscene/src/worker/run-scope.mts`
- `engines/midscene/src/worker/run-scope.test.mts`

## Audit Trail

- EXTRACTED: 62 (97%)
- INFERRED: 2 (3%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*