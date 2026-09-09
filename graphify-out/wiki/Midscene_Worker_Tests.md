# Midscene Worker Tests

> 18 nodes · cohesion 0.12

## Key Concepts

- **run-scope.test.mts** (19 connections) — `engines/midscene/src/worker/run-scope.test.mts`
- **artifact-upload.test.mts** (4 connections) — `engines/midscene/src/worker/artifact-upload.test.mts`
- **ADR-0029** (4 connections) — `engines/midscene/src/worker/run-scope.mts`
- **mkLogDir()** (2 connections) — `engines/midscene/src/worker/artifact-upload.test.mts`
- **tmproot()** (2 connections) — `engines/midscene/src/worker/artifact-upload.test.mts`
- **ADR-0014** (2 connections) — `engines/midscene/src/worker/run-scope.mts`
- **ADR-0031** (2 connections) — `engines/midscene/src/worker/run-scope.mts`
- **importMod()** (2 connections) — `engines/midscene/src/worker/run-scope.test.mts`
- **withMockClient()** (1 connections) — `engines/midscene/src/worker/artifact-upload.test.mts`
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

- [Midscene Run Scope](Midscene_Run_Scope.md) (6 shared connections)
- [Midscene Job Source](Midscene_Job_Source.md) (3 shared connections)
- [TS Deterministic Hooks](TS_Deterministic_Hooks.md) (2 shared connections)

## Source Files

- `engines/midscene/src/worker/artifact-upload.test.mts`
- `engines/midscene/src/worker/run-scope.mts`
- `engines/midscene/src/worker/run-scope.test.mts`

## Audit Trail

- EXTRACTED: 29 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*