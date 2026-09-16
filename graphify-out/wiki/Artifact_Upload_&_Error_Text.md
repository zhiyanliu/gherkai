# Artifact Upload & Error Text

> 10 nodes · cohesion 0.27

## Key Concepts

- **ADR-0042** (8 connections) — `engines/midscene/src/worker/evidence.mts`
- **artifact-upload.test.mts** (6 connections) — `engines/midscene/src/worker/artifact-upload.test.mts`
- **tmproot()** (3 connections) — `engines/midscene/src/worker/artifact-upload.test.mts`
- **error-text.mts** (3 connections) — `engines/midscene/src/worker/error-text.mts`
- **mkLogDir()** (2 connections) — `engines/midscene/src/worker/artifact-upload.test.mts`
- **mkShots()** (2 connections) — `engines/midscene/src/worker/artifact-upload.test.mts`
- **errorText()** (2 connections) — `engines/midscene/src/worker/error-text.mts`
- **oneLineError()** (2 connections) — `engines/midscene/src/worker/error-text.mts`
- **withMockClient()** (1 connections) — `engines/midscene/src/worker/artifact-upload.test.mts`
- **error-text.test.mts** (1 connections) — `engines/midscene/src/worker/error-text.test.mts`

## Relationships

- [TS Event Sink & Upload](TS_Event_Sink_%26_Upload.md) (2 shared connections)
- [Evidence Schema (TS)](Evidence_Schema_%28TS%29.md) (1 shared connections)
- [Evidence Collector Tests](Evidence_Collector_Tests.md) (1 shared connections)
- [Run Scope (TS Worker)](Run_Scope_%28TS_Worker%29.md) (1 shared connections)
- [Run Scope Integration Tests](Run_Scope_Integration_Tests.md) (1 shared connections)

## Source Files

- `engines/midscene/src/worker/artifact-upload.test.mts`
- `engines/midscene/src/worker/error-text.mts`
- `engines/midscene/src/worker/error-text.test.mts`
- `engines/midscene/src/worker/evidence.mts`

## Audit Trail

- EXTRACTED: 18 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*