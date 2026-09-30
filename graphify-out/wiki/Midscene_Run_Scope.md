# Midscene Run Scope

> 37 nodes · cohesion 0.09

## Key Concepts

- **run-scope.mts** (53 connections) — `engines/midscene/src/worker/run-scope.mts`
- **main()** (12 connections) — `engines/midscene/src/worker/run-scope.mts`
- **runStep()** (6 connections) — `engines/midscene/src/worker/run-scope.mts`
- **runScenario()** (5 connections) — `engines/midscene/src/worker/run-scope.mts`
- **agentOpts()** (4 connections) — `engines/midscene/src/worker/run-scope.mts`
- **shutdownSequence()** (4 connections) — `engines/midscene/src/worker/run-scope.mts`
- **cumulativeTokens()** (3 connections) — `engines/midscene/src/worker/run-scope.mts`
- **drainArtifactQueue()** (3 connections) — `engines/midscene/src/worker/run-scope.mts`
- **isTransientNetwork()** (3 connections) — `engines/midscene/src/worker/run-scope.mts`
- **log()** (3 connections) — `engines/midscene/src/worker/run-scope.mts`
- **stepCost()** (3 connections) — `engines/midscene/src/worker/run-scope.mts`
- **aggregate()** (2 connections) — `engines/midscene/src/worker/run-scope.mts`
- **appendReportRef()** (2 connections) — `engines/midscene/src/worker/run-scope.mts`
- **artifactFlushRoot()** (2 connections) — `engines/midscene/src/worker/run-scope.mts`
- **interruptSnapshot()** (2 connections) — `engines/midscene/src/worker/run-scope.mts`
- **makeGuardedCleanup()** (2 connections) — `engines/midscene/src/worker/run-scope.mts`
- **minGraceSeconds()** (2 connections) — `engines/midscene/src/worker/run-scope.mts`
- **modelConfig()** (2 connections) — `engines/midscene/src/worker/run-scope.mts`
- **step()** (2 connections) — `engines/midscene/src/worker/run-scope.test.mts`
- **writeStdoutFlushed()** (2 connections) — `engines/midscene/src/worker/run-scope.mts`
- **ADR-0019** (1 connections) — `engines/midscene/src/worker/run-scope.mts`
- **ADR-0026** (1 connections) — `engines/midscene/src/worker/run-scope.mts`
- **ADR-0027** (1 connections) — `engines/midscene/src/worker/run-scope.mts`
- **ADR-0039** (1 connections) — `engines/midscene/src/worker/run-scope.mts`
- **AWS_TRANSIENT_NAMES** (1 connections) — `engines/midscene/src/worker/run-scope.mts`
- *... and 12 more nodes in this community*

## Relationships

- [Midscene Resolve Hooks](Midscene_Resolve_Hooks.md) (6 shared connections)
- [Run Scope Tests](Run_Scope_Tests.md) (5 shared connections)
- [Evidence Collector Tests](Evidence_Collector_Tests.md) (2 shared connections)
- [Model Spike Scripts](Model_Spike_Scripts.md) (2 shared connections)
- [Artifact Upload & Error Text](Artifact_Upload_%26_Error_Text.md) (2 shared connections)
- [Step Argument & Sink Tests](Step_Argument_%26_Sink_Tests.md) (1 shared connections)
- [URL Redaction](URL_Redaction.md) (1 shared connections)
- [Event Sink & Job Source](Event_Sink_%26_Job_Source.md) (1 shared connections)

## Source Files

- `engines/midscene/src/worker/run-scope.mts`
- `engines/midscene/src/worker/run-scope.test.mts`

## Audit Trail

- EXTRACTED: 75 (97%)
- INFERRED: 2 (3%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*