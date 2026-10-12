# Midscene Worker Run Scope

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

- [Midscene Worker Entry](Midscene_Worker_Entry.md) (6 shared connections)
- [Run Scope Tests (TS)](Run_Scope_Tests_%28TS%29.md) (5 shared connections)
- [Evidence Collector Tests](Evidence_Collector_Tests.md) (2 shared connections)
- [Midscene Worker IO Edges](Midscene_Worker_IO_Edges.md) (2 shared connections)
- [Engine Spike Probes](Engine_Spike_Probes.md) (2 shared connections)
- [Artifact Upload & Error Text Tests](Artifact_Upload_%26_Error_Text_Tests.md) (2 shared connections)
- [URL Userinfo Redaction](URL_Userinfo_Redaction.md) (1 shared connections)

## Source Files

- `engines/midscene/src/worker/run-scope.mts`
- `engines/midscene/src/worker/run-scope.test.mts`

## Audit Trail

- EXTRACTED: 75 (97%)
- INFERRED: 2 (3%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*