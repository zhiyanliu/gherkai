# Run Scope Tests

> 15 nodes · cohesion 0.13

## Key Concepts

- **run-scope.test.mts** (25 connections) — `engines/midscene/src/worker/run-scope.test.mts`
- **ADR-0014** (2 connections) — `engines/midscene/src/worker/run-scope.mts`
- **ADR-0031** (2 connections) — `engines/midscene/src/worker/run-scope.mts`
- **importMod()** (2 connections) — `engines/midscene/src/worker/run-scope.test.mts`
- **costAgent()** (1 connections) — `engines/midscene/src/worker/run-scope.test.mts`
- **_events** (1 connections) — `engines/midscene/src/worker/run-scope.test.mts`
- **fakeAgent()** (1 connections) — `engines/midscene/src/worker/run-scope.test.mts`
- **fakePage** (1 connections) — `engines/midscene/src/worker/run-scope.test.mts`
- **metrics()** (1 connections) — `engines/midscene/src/worker/run-scope.test.mts`
- **reportFile()** (1 connections) — `engines/midscene/src/worker/run-scope.test.mts`
- **shortcircuitAgent()** (1 connections) — `engines/midscene/src/worker/run-scope.test.mts`
- **shutdownSpy()** (1 connections) — `engines/midscene/src/worker/run-scope.test.mts`
- **spawnWorker()** (1 connections) — `engines/midscene/src/worker/run-scope.test.mts`
- **spyUploader()** (1 connections) — `engines/midscene/src/worker/run-scope.test.mts`
- **testSink** (1 connections) — `engines/midscene/src/worker/run-scope.test.mts`

## Relationships

- [TypeScript Worker Run Scope](TypeScript_Worker_Run_Scope.md) (5 shared connections)
- [TS Artifact & Event Sink](TS_Artifact_%26_Event_Sink.md) (2 shared connections)
- [Artifact Upload Tests (TS)](Artifact_Upload_Tests_%28TS%29.md) (2 shared connections)
- [Deterministic Step Resolution (TS)](Deterministic_Step_Resolution_%28TS%29.md) (2 shared connections)
- [Engine Spike Scripts](Engine_Spike_Scripts.md) (2 shared connections)
- [Worker Bin & Step Loading](Worker_Bin_%26_Step_Loading.md) (1 shared connections)

## Source Files

- `engines/midscene/src/worker/run-scope.mts`
- `engines/midscene/src/worker/run-scope.test.mts`

## Audit Trail

- EXTRACTED: 28 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*