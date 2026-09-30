# Artifact Upload & Error Text

> 14 nodes · cohesion 0.19

## Key Concepts

- **artifact-upload.mts** (12 connections) — `engines/midscene/src/lib/artifact-upload.mts`
- **ADR-0042** (8 connections) — `engines/midscene/src/worker/evidence.mts`
- **artifact-upload.test.mts** (6 connections) — `engines/midscene/src/worker/artifact-upload.test.mts`
- **ADR-0029** (4 connections) — `engines/midscene/src/worker/run-scope.mts`
- **tmproot()** (3 connections) — `engines/midscene/src/worker/artifact-upload.test.mts`
- **error-text.mts** (3 connections) — `engines/midscene/src/worker/error-text.mts`
- **mkLogDir()** (2 connections) — `engines/midscene/src/worker/artifact-upload.test.mts`
- **mkShots()** (2 connections) — `engines/midscene/src/worker/artifact-upload.test.mts`
- **errorText()** (2 connections) — `engines/midscene/src/worker/error-text.mts`
- **oneLineError()** (2 connections) — `engines/midscene/src/worker/error-text.mts`
- **CONTENT_TYPES** (1 connections) — `engines/midscene/src/lib/artifact-upload.mts`
- **UPLOAD_TIMEOUT_MS** (1 connections) — `engines/midscene/src/lib/artifact-upload.mts`
- **withMockClient()** (1 connections) — `engines/midscene/src/worker/artifact-upload.test.mts`
- **error-text.test.mts** (1 connections) — `engines/midscene/src/worker/error-text.test.mts`

## Relationships

- [Run Scope Tests](Run_Scope_Tests.md) (3 shared connections)
- [TypeScript Worker IO Edges](TypeScript_Worker_IO_Edges.md) (2 shared connections)
- [Artifact Uploader (TypeScript)](Artifact_Uploader_%28TypeScript%29.md) (2 shared connections)
- [Midscene Run Scope Worker](Midscene_Run_Scope_Worker.md) (2 shared connections)
- [TypeScript Entry and Hooks](TypeScript_Entry_and_Hooks.md) (1 shared connections)
- [Worker Step Arguments](Worker_Step_Arguments.md) (1 shared connections)
- [Model Spike Scripts](Model_Spike_Scripts.md) (1 shared connections)
- [Evidence Schema Builder](Evidence_Schema_Builder.md) (1 shared connections)
- [Evidence Collector Tests](Evidence_Collector_Tests.md) (1 shared connections)

## Source Files

- `engines/midscene/src/lib/artifact-upload.mts`
- `engines/midscene/src/worker/artifact-upload.test.mts`
- `engines/midscene/src/worker/error-text.mts`
- `engines/midscene/src/worker/error-text.test.mts`
- `engines/midscene/src/worker/evidence.mts`
- `engines/midscene/src/worker/run-scope.mts`

## Audit Trail

- EXTRACTED: 31 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*