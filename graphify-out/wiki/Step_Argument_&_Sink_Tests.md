# Step Argument & Sink Tests

> 12 nodes · cohesion 0.21

## Key Concepts

- **ADR-0024** (10 connections) — `engines/midscene/src/bin.mts`
- **argument.mts** (6 connections) — `engines/midscene/src/worker/argument.mts`
- **argumentText()** (3 connections) — `engines/midscene/src/worker/argument.mts`
- **buildInstruction()** (3 connections) — `engines/midscene/src/worker/argument.mts`
- **event-sink.test.mts** (3 connections) — `engines/midscene/src/worker/event-sink.test.mts`
- **cleanCell()** (2 connections) — `engines/midscene/src/worker/argument.mts`
- **unquote()** (2 connections) — `engines/midscene/src/worker/argument.mts`
- **job-source.test.mts** (2 connections) — `engines/midscene/src/worker/job-source.test.mts`
- **StepArgument** (1 connections) — `engines/midscene/src/worker/argument.mts`
- **argument.test.mts** (1 connections) — `engines/midscene/src/worker/argument.test.mts`
- **fdSink()** (1 connections) — `engines/midscene/src/worker/event-sink.test.mts`
- **withStdin()** (1 connections) — `engines/midscene/src/worker/job-source.test.mts`

## Relationships

- [Event Sink & Job Source](Event_Sink_%26_Job_Source.md) (2 shared connections)
- [Midscene Resolve Hooks](Midscene_Resolve_Hooks.md) (1 shared connections)
- [Artifact Upload & Error Text](Artifact_Upload_%26_Error_Text.md) (1 shared connections)
- [Midscene Run Scope](Midscene_Run_Scope.md) (1 shared connections)
- [Run Scope Tests](Run_Scope_Tests.md) (1 shared connections)
- [Model Spike Scripts](Model_Spike_Scripts.md) (1 shared connections)

## Source Files

- `engines/midscene/src/bin.mts`
- `engines/midscene/src/worker/argument.mts`
- `engines/midscene/src/worker/argument.test.mts`
- `engines/midscene/src/worker/event-sink.test.mts`
- `engines/midscene/src/worker/job-source.test.mts`

## Audit Trail

- EXTRACTED: 20 (95%)
- INFERRED: 1 (5%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*