# Run Scope Integration Tests

> 13 nodes · cohesion 0.15

## Key Concepts

- **run-scope.test.mts** (20 connections) — `engines/midscene/src/worker/run-scope.test.mts`
- **ADR-0014** (2 connections) — `engines/midscene/src/worker/run-scope.mts`
- **ADR-0031** (2 connections) — `engines/midscene/src/worker/run-scope.mts`
- **importMod()** (2 connections) — `engines/midscene/src/worker/run-scope.test.mts`
- **costAgent()** (1 connections) — `engines/midscene/src/worker/run-scope.test.mts`
- **_events** (1 connections) — `engines/midscene/src/worker/run-scope.test.mts`
- **fakeAgent()** (1 connections) — `engines/midscene/src/worker/run-scope.test.mts`
- **fakePage** (1 connections) — `engines/midscene/src/worker/run-scope.test.mts`
- **reportFile()** (1 connections) — `engines/midscene/src/worker/run-scope.test.mts`
- **shortcircuitAgent()** (1 connections) — `engines/midscene/src/worker/run-scope.test.mts`
- **shutdownSpy()** (1 connections) — `engines/midscene/src/worker/run-scope.test.mts`
- **spyUploader()** (1 connections) — `engines/midscene/src/worker/run-scope.test.mts`
- **testSink** (1 connections) — `engines/midscene/src/worker/run-scope.test.mts`

## Relationships

- [Run Scope (TS Worker)](Run_Scope_%28TS_Worker%29.md) (5 shared connections)
- [TS Event Sink & Upload](TS_Event_Sink_%26_Upload.md) (2 shared connections)
- [TypeScript Deterministic Hooks](TypeScript_Deterministic_Hooks.md) (2 shared connections)
- [Artifact Upload & Error Text](Artifact_Upload_%26_Error_Text.md) (1 shared connections)
- [Worker Bin & Step Loading](Worker_Bin_%26_Step_Loading.md) (1 shared connections)

## Source Files

- `engines/midscene/src/worker/run-scope.mts`
- `engines/midscene/src/worker/run-scope.test.mts`

## Audit Trail

- EXTRACTED: 23 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*