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

- [Midscene Run Scope](Midscene_Run_Scope.md) (5 shared connections)
- [Artifact Upload & Error Text](Artifact_Upload_%26_Error_Text.md) (3 shared connections)
- [Midscene Resolve Hooks](Midscene_Resolve_Hooks.md) (3 shared connections)
- [Model Spike Scripts](Model_Spike_Scripts.md) (2 shared connections)
- [Step Argument & Sink Tests](Step_Argument_%26_Sink_Tests.md) (1 shared connections)

## Source Files

- `engines/midscene/src/worker/run-scope.mts`
- `engines/midscene/src/worker/run-scope.test.mts`

## Audit Trail

- EXTRACTED: 28 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*