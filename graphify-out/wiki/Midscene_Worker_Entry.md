# Midscene Worker Entry

> 27 nodes · cohesion 0.10

## Key Concepts

- **user-steps.mts** (12 connections) — `engines/midscene/src/worker/user-steps.mts`
- **ADR-0037** (11 connections) — `engines/midscene/src/bin.mts`
- **bin.mts** (8 connections) — `engines/midscene/src/bin.mts`
- **ADR-0036** (7 connections) — `engines/midscene/src/index.mts`
- **resolve-hook.mts** (6 connections) — `engines/midscene/src/resolve-hook.mts`
- **user-steps.test.mts** (6 connections) — `engines/midscene/src/worker/user-steps.test.mts`
- **ADR-0028** (5 connections) — `engines/midscene/src/bin.mts`
- **ADR-0022** (5 connections) — `engines/midscene/src/index.mts`
- **deterministic.steps.mts** (5 connections) — `engines/midscene/src/worker/deterministic.steps.mts`
- **index.mts** (3 connections) — `engines/midscene/src/index.mts`
- **确定性 step 加载失败即拒绝运行** (2 connections) — `docs/user-guide/writing-deterministic-steps.md`
- **no-artifacts.test.mts** (2 connections) — `engines/midscene/src/worker/no-artifacts.test.mts`
- **collectStepFiles()** (2 connections) — `engines/midscene/src/worker/user-steps.mts`
- **loadUserSteps()** (2 connections) — `engines/midscene/src/worker/user-steps.mts`
- **ADR-0015** (1 connections) — `engines/midscene/src/worker/deterministic.steps.mts`
- **fromSource** (1 connections) — `engines/midscene/src/bin.mts`
- **hookSpec** (1 connections) — `engines/midscene/src/bin.mts`
- **initialize()** (1 connections) — `engines/midscene/src/resolve-hook.mts`
- **resolve()** (1 connections) — `engines/midscene/src/resolve-hook.mts`
- **ADR-0020** (1 connections) — `engines/midscene/src/worker/deterministic.steps.mts`
- **deterministic.test.mts** (1 connections) — `engines/midscene/src/worker/deterministic.test.mts`
- **LoadUserStepsDeps** (1 connections) — `engines/midscene/src/worker/user-steps.mts`
- **STEP_EXTS** (1 connections) — `engines/midscene/src/worker/user-steps.mts`
- **BIN** (1 connections) — `engines/midscene/src/worker/user-steps.test.mts`
- **runBin()** (1 connections) — `engines/midscene/src/worker/user-steps.test.mts`
- *... and 2 more nodes in this community*

## Relationships

- [Midscene Worker Run Scope](Midscene_Worker_Run_Scope.md) (6 shared connections)
- [Midscene Worker IO Edges](Midscene_Worker_IO_Edges.md) (3 shared connections)
- [Contributor Docs And ADRs](Contributor_Docs_And_ADRs.md) (3 shared connections)
- [Run Scope Tests (TS)](Run_Scope_Tests_%28TS%29.md) (3 shared connections)
- [Deterministic Registry (TS)](Deterministic_Registry_%28TS%29.md) (3 shared connections)
- [Cloud Backend Concepts](Cloud_Backend_Concepts.md) (1 shared connections)
- [Engine Spike Probes](Engine_Spike_Probes.md) (1 shared connections)
- [Architecture Diagram Catalog](Architecture_Diagram_Catalog.md) (1 shared connections)

## Source Files

- `docs/user-guide/writing-deterministic-steps.md`
- `engines/midscene/src/bin.mts`
- `engines/midscene/src/index.mts`
- `engines/midscene/src/resolve-hook.mts`
- `engines/midscene/src/worker/deterministic.steps.mts`
- `engines/midscene/src/worker/deterministic.test.mts`
- `engines/midscene/src/worker/no-artifacts.test.mts`
- `engines/midscene/src/worker/user-steps.mts`
- `engines/midscene/src/worker/user-steps.test.mts`

## Audit Trail

- EXTRACTED: 54 (98%)
- INFERRED: 1 (2%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*