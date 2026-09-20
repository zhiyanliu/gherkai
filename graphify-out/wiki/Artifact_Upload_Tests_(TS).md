# Artifact Upload Tests (TS)

> 11 nodes · cohesion 0.24

## Key Concepts

- **ADR-0042** (8 connections) — `engines/midscene/src/worker/evidence.mts`
- **artifact-upload.test.mts** (6 connections) — `engines/midscene/src/worker/artifact-upload.test.mts`
- **ADR-0029** (4 connections) — `engines/midscene/src/worker/run-scope.mts`
- **tmproot()** (3 connections) — `engines/midscene/src/worker/artifact-upload.test.mts`
- **error-text.mts** (3 connections) — `engines/midscene/src/worker/error-text.mts`
- **mkLogDir()** (2 connections) — `engines/midscene/src/worker/artifact-upload.test.mts`
- **mkShots()** (2 connections) — `engines/midscene/src/worker/artifact-upload.test.mts`
- **errorText()** (2 connections) — `engines/midscene/src/worker/error-text.mts`
- **oneLineError()** (2 connections) — `engines/midscene/src/worker/error-text.mts`
- **withMockClient()** (1 connections) — `engines/midscene/src/worker/artifact-upload.test.mts`
- **error-text.test.mts** (1 connections) — `engines/midscene/src/worker/error-text.test.mts`

## Relationships

- [TS Artifact & Event Sink](TS_Artifact_%26_Event_Sink.md) (2 shared connections)
- [TypeScript Worker Run Scope](TypeScript_Worker_Run_Scope.md) (2 shared connections)
- [Run Scope Tests](Run_Scope_Tests.md) (2 shared connections)
- [Evidence Schema (TS)](Evidence_Schema_%28TS%29.md) (1 shared connections)
- [Evidence Collector Tests](Evidence_Collector_Tests.md) (1 shared connections)

## Source Files

- `engines/midscene/src/worker/artifact-upload.test.mts`
- `engines/midscene/src/worker/error-text.mts`
- `engines/midscene/src/worker/error-text.test.mts`
- `engines/midscene/src/worker/evidence.mts`
- `engines/midscene/src/worker/run-scope.mts`

## Audit Trail

- EXTRACTED: 21 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*