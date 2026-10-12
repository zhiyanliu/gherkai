# Midscene Worker IO Edges

> 25 nodes · cohesion 0.10

## Key Concepts

- **artifact-upload.mts** (12 connections) — `engines/midscene/src/lib/artifact-upload.mts`
- **ADR-0024** (10 connections) — `engines/midscene/src/bin.mts`
- **event-sink.mts** (7 connections) — `engines/midscene/src/lib/event-sink.mts`
- **EventSink** (5 connections) — `engines/midscene/src/lib/event-sink.mts`
- **job-source.mts** (5 connections) — `engines/midscene/src/lib/job-source.mts`
- **JobSource** (5 connections) — `engines/midscene/src/lib/job-source.mts`
- **ADR-0016** (4 connections) — `engines/midscene/src/lib/event-sink.mts`
- **ADR-0032** (4 connections) — `engines/midscene/src/lib/event-sink.mts`
- **contentTypeFor()** (2 connections) — `engines/midscene/src/lib/artifact-upload.mts`
- **.client_()** (2 connections) — `engines/midscene/src/lib/event-sink.mts`
- **.emit()** (2 connections) — `engines/midscene/src/lib/event-sink.mts`
- **.fromEnv()** (2 connections) — `engines/midscene/src/lib/event-sink.mts`
- **resolveEventsFd()** (2 connections) — `engines/midscene/src/lib/event-sink.mts`
- **job-source.test.mts** (2 connections) — `engines/midscene/src/worker/job-source.test.mts`
- **ADR-0034** (1 connections) — `engines/midscene/src/lib/event-sink.mts`
- **CONTENT_TYPES** (1 connections) — `engines/midscene/src/lib/artifact-upload.mts`
- **UPLOAD_TIMEOUT_MS** (1 connections) — `engines/midscene/src/lib/artifact-upload.mts`
- **.constructor()** (1 connections) — `engines/midscene/src/lib/event-sink.mts`
- **Job** (1 connections) — `engines/midscene/src/lib/job-source.mts`
- **.constructor()** (1 connections) — `engines/midscene/src/lib/job-source.mts`
- **.fromEnv()** (1 connections) — `engines/midscene/src/lib/job-source.mts`
- **.read()** (1 connections) — `engines/midscene/src/lib/job-source.mts`
- **.readS3()** (1 connections) — `engines/midscene/src/lib/job-source.mts`
- **argument.test.mts** (1 connections) — `engines/midscene/src/worker/argument.test.mts`
- **withStdin()** (1 connections) — `engines/midscene/src/worker/job-source.test.mts`

## Relationships

- [Midscene Worker Entry](Midscene_Worker_Entry.md) (3 shared connections)
- [Engine Spike Probes](Engine_Spike_Probes.md) (3 shared connections)
- [Midscene Worker Run Scope](Midscene_Worker_Run_Scope.md) (2 shared connections)
- [Run Scope Tests (TS)](Run_Scope_Tests_%28TS%29.md) (2 shared connections)
- [Artifact Upload & Error Text Tests](Artifact_Upload_%26_Error_Text_Tests.md) (2 shared connections)
- [Artifact Uploader (TS)](Artifact_Uploader_%28TS%29.md) (2 shared connections)
- [Step Argument Utils (TS)](Step_Argument_Utils_%28TS%29.md) (1 shared connections)

## Source Files

- `engines/midscene/src/bin.mts`
- `engines/midscene/src/lib/artifact-upload.mts`
- `engines/midscene/src/lib/event-sink.mts`
- `engines/midscene/src/lib/job-source.mts`
- `engines/midscene/src/worker/argument.test.mts`
- `engines/midscene/src/worker/job-source.test.mts`

## Audit Trail

- EXTRACTED: 45 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*