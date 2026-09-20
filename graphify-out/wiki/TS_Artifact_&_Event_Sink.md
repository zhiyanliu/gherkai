# TS Artifact & Event Sink

> 30 nodes · cohesion 0.09

## Key Concepts

- **artifact-upload.mts** (12 connections) — `engines/midscene/src/lib/artifact-upload.mts`
- **ADR-0024** (10 connections) — `engines/midscene/src/bin.mts`
- **event-sink.mts** (7 connections) — `engines/midscene/src/lib/event-sink.mts`
- **argument.mts** (6 connections) — `engines/midscene/src/worker/argument.mts`
- **EventSink** (5 connections) — `engines/midscene/src/lib/event-sink.mts`
- **job-source.mts** (5 connections) — `engines/midscene/src/lib/job-source.mts`
- **JobSource** (5 connections) — `engines/midscene/src/lib/job-source.mts`
- **ADR-0016** (4 connections) — `engines/midscene/src/lib/event-sink.mts`
- **ADR-0032** (4 connections) — `engines/midscene/src/lib/event-sink.mts`
- **argumentText()** (3 connections) — `engines/midscene/src/worker/argument.mts`
- **buildInstruction()** (3 connections) — `engines/midscene/src/worker/argument.mts`
- **.client_()** (2 connections) — `engines/midscene/src/lib/event-sink.mts`
- **.emit()** (2 connections) — `engines/midscene/src/lib/event-sink.mts`
- **.fromEnv()** (2 connections) — `engines/midscene/src/lib/event-sink.mts`
- **resolveEventsFd()** (2 connections) — `engines/midscene/src/lib/event-sink.mts`
- **cleanCell()** (2 connections) — `engines/midscene/src/worker/argument.mts`
- **unquote()** (2 connections) — `engines/midscene/src/worker/argument.mts`
- **job-source.test.mts** (2 connections) — `engines/midscene/src/worker/job-source.test.mts`
- **ADR-0034** (1 connections) — `engines/midscene/src/lib/event-sink.mts`
- **CONTENT_TYPES** (1 connections) — `engines/midscene/src/lib/artifact-upload.mts`
- **UPLOAD_TIMEOUT_MS** (1 connections) — `engines/midscene/src/lib/artifact-upload.mts`
- **.constructor()** (1 connections) — `engines/midscene/src/lib/event-sink.mts`
- **Job** (1 connections) — `engines/midscene/src/lib/job-source.mts`
- **.constructor()** (1 connections) — `engines/midscene/src/lib/job-source.mts`
- **.fromEnv()** (1 connections) — `engines/midscene/src/lib/job-source.mts`
- *... and 5 more nodes in this community*

## Relationships

- [Worker Bin & Step Loading](Worker_Bin_%26_Step_Loading.md) (3 shared connections)
- [Engine Spike Scripts](Engine_Spike_Scripts.md) (3 shared connections)
- [TypeScript Worker Run Scope](TypeScript_Worker_Run_Scope.md) (2 shared connections)
- [Run Scope Tests](Run_Scope_Tests.md) (2 shared connections)
- [Artifact Upload Tests (TS)](Artifact_Upload_Tests_%28TS%29.md) (2 shared connections)
- [TS Artifact Uploader](TS_Artifact_Uploader.md) (2 shared connections)

## Source Files

- `engines/midscene/src/bin.mts`
- `engines/midscene/src/lib/artifact-upload.mts`
- `engines/midscene/src/lib/event-sink.mts`
- `engines/midscene/src/lib/job-source.mts`
- `engines/midscene/src/worker/argument.mts`
- `engines/midscene/src/worker/argument.test.mts`
- `engines/midscene/src/worker/job-source.test.mts`

## Audit Trail

- EXTRACTED: 51 (98%)
- INFERRED: 1 (2%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*