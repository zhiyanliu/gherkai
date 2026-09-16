# TS Event Sink & Upload

> 26 nodes · cohesion 0.10

## Key Concepts

- **ADR-0024** (10 connections) — `engines/midscene/src/bin.mts`
- **artifact-upload.mts** (10 connections) — `engines/midscene/src/lib/artifact-upload.mts`
- **event-sink.mts** (7 connections) — `engines/midscene/src/lib/event-sink.mts`
- **EventSink** (5 connections) — `engines/midscene/src/lib/event-sink.mts`
- **job-source.mts** (5 connections) — `engines/midscene/src/lib/job-source.mts`
- **JobSource** (5 connections) — `engines/midscene/src/lib/job-source.mts`
- **ADR-0016** (4 connections) — `engines/midscene/src/lib/event-sink.mts`
- **ADR-0032** (4 connections) — `engines/midscene/src/lib/event-sink.mts`
- **ADR-0029** (4 connections) — `engines/midscene/src/worker/run-scope.mts`
- **event-sink.test.mts** (3 connections) — `engines/midscene/src/worker/event-sink.test.mts`
- **.client_()** (2 connections) — `engines/midscene/src/lib/event-sink.mts`
- **.emit()** (2 connections) — `engines/midscene/src/lib/event-sink.mts`
- **.fromEnv()** (2 connections) — `engines/midscene/src/lib/event-sink.mts`
- **resolveEventsFd()** (2 connections) — `engines/midscene/src/lib/event-sink.mts`
- **job-source.test.mts** (2 connections) — `engines/midscene/src/worker/job-source.test.mts`
- **ADR-0034** (1 connections) — `engines/midscene/src/lib/event-sink.mts`
- **CONTENT_TYPES** (1 connections) — `engines/midscene/src/lib/artifact-upload.mts`
- **.constructor()** (1 connections) — `engines/midscene/src/lib/event-sink.mts`
- **Job** (1 connections) — `engines/midscene/src/lib/job-source.mts`
- **.constructor()** (1 connections) — `engines/midscene/src/lib/job-source.mts`
- **.fromEnv()** (1 connections) — `engines/midscene/src/lib/job-source.mts`
- **.read()** (1 connections) — `engines/midscene/src/lib/job-source.mts`
- **.readS3()** (1 connections) — `engines/midscene/src/lib/job-source.mts`
- **argument.test.mts** (1 connections) — `engines/midscene/src/worker/argument.test.mts`
- **fdSink()** (1 connections) — `engines/midscene/src/worker/event-sink.test.mts`
- *... and 1 more nodes in this community*

## Relationships

- [Worker Bin & Step Loading](Worker_Bin_%26_Step_Loading.md) (3 shared connections)
- [Run Scope (TS Worker)](Run_Scope_%28TS_Worker%29.md) (3 shared connections)
- [SigV4 Model Spikes](SigV4_Model_Spikes.md) (3 shared connections)
- [Run Scope Integration Tests](Run_Scope_Integration_Tests.md) (2 shared connections)
- [Artifact Upload & Error Text](Artifact_Upload_%26_Error_Text.md) (2 shared connections)
- [TS Artifact Uploader](TS_Artifact_Uploader.md) (2 shared connections)
- [Step Argument Building](Step_Argument_Building.md) (1 shared connections)

## Source Files

- `engines/midscene/src/bin.mts`
- `engines/midscene/src/lib/artifact-upload.mts`
- `engines/midscene/src/lib/event-sink.mts`
- `engines/midscene/src/lib/job-source.mts`
- `engines/midscene/src/worker/argument.test.mts`
- `engines/midscene/src/worker/event-sink.test.mts`
- `engines/midscene/src/worker/job-source.test.mts`
- `engines/midscene/src/worker/run-scope.mts`

## Audit Trail

- EXTRACTED: 47 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*