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

- [Midscene Run Scope Worker](Midscene_Run_Scope_Worker.md) (5 shared connections)
- [Midscene Hook & Entry](Midscene_Hook_%26_Entry.md) (3 shared connections)
- [Midscene Artifact & Event Sink](Midscene_Artifact_%26_Event_Sink.md) (2 shared connections)
- [Upload And Error Text Tests](Upload_And_Error_Text_Tests.md) (2 shared connections)
- [Midscene Spike Probes](Midscene_Spike_Probes.md) (2 shared connections)

## Source Files

- `engines/midscene/src/worker/run-scope.mts`
- `engines/midscene/src/worker/run-scope.test.mts`

## Audit Trail

- EXTRACTED: 28 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*