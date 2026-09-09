# Midscene Job Source

> 19 nodes · cohesion 0.12

## Key Concepts

- **ADR-0024** (10 connections) — `engines/midscene/src/bin.mts`
- **bin.mts** (6 connections) — `engines/midscene/src/bin.mts`
- **artifact-upload.mts** (6 connections) — `engines/midscene/src/lib/artifact-upload.mts`
- **ADR-0028** (5 connections) — `engines/midscene/src/bin.mts`
- **JobSource** (5 connections) — `engines/midscene/src/lib/job-source.mts`
- **ADR-0016** (4 connections) — `engines/midscene/src/lib/event-sink.mts`
- **job-source.mts** (4 connections) — `engines/midscene/src/lib/job-source.mts`
- **event-sink.test.mts** (3 connections) — `engines/midscene/src/worker/event-sink.test.mts`
- **job-source.test.mts** (2 connections) — `engines/midscene/src/worker/job-source.test.mts`
- **fromSource** (1 connections) — `engines/midscene/src/bin.mts`
- **hookSpec** (1 connections) — `engines/midscene/src/bin.mts`
- **Job** (1 connections) — `engines/midscene/src/lib/job-source.mts`
- **.constructor()** (1 connections) — `engines/midscene/src/lib/job-source.mts`
- **.fromEnv()** (1 connections) — `engines/midscene/src/lib/job-source.mts`
- **.read()** (1 connections) — `engines/midscene/src/lib/job-source.mts`
- **.readS3()** (1 connections) — `engines/midscene/src/lib/job-source.mts`
- **argument.test.mts** (1 connections) — `engines/midscene/src/worker/argument.test.mts`
- **fdSink()** (1 connections) — `engines/midscene/src/worker/event-sink.test.mts`
- **withStdin()** (1 connections) — `engines/midscene/src/worker/job-source.test.mts`

## Relationships

- [TS Deterministic Hooks](TS_Deterministic_Hooks.md) (3 shared connections)
- [Midscene Run Scope](Midscene_Run_Scope.md) (3 shared connections)
- [Midscene Worker Tests](Midscene_Worker_Tests.md) (3 shared connections)
- [TypeScript Event Sink](TypeScript_Event_Sink.md) (2 shared connections)
- [Model Spike Scripts](Model_Spike_Scripts.md) (2 shared connections)
- [Step Argument Parsing (TS)](Step_Argument_Parsing_%28TS%29.md) (1 shared connections)
- [Artifact Uploader](Artifact_Uploader.md) (1 shared connections)

## Source Files

- `engines/midscene/src/bin.mts`
- `engines/midscene/src/lib/artifact-upload.mts`
- `engines/midscene/src/lib/event-sink.mts`
- `engines/midscene/src/lib/job-source.mts`
- `engines/midscene/src/worker/argument.test.mts`
- `engines/midscene/src/worker/event-sink.test.mts`
- `engines/midscene/src/worker/job-source.test.mts`

## Audit Trail

- EXTRACTED: 35 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*