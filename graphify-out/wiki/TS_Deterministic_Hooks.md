# TS Deterministic Hooks

> 21 nodes · cohesion 0.12

## Key Concepts

- **ADR-0037** (10 connections) — `engines/midscene/src/bin.mts`
- **user-steps.mts** (8 connections) — `engines/midscene/src/worker/user-steps.mts`
- **ADR-0036** (7 connections) — `engines/midscene/src/index.mts`
- **user-steps.test.mts** (6 connections) — `engines/midscene/src/worker/user-steps.test.mts`
- **ADR-0022** (5 connections) — `engines/midscene/src/index.mts`
- **deterministic.steps.mts** (5 connections) — `engines/midscene/src/worker/deterministic.steps.mts`
- **index.mts** (3 connections) — `engines/midscene/src/index.mts`
- **resolve-hook.mts** (3 connections) — `engines/midscene/src/resolve-hook.mts`
- **collectStepFiles()** (2 connections) — `engines/midscene/src/worker/user-steps.mts`
- **loadUserSteps()** (2 connections) — `engines/midscene/src/worker/user-steps.mts`
- **ADR-0015** (1 connections) — `engines/midscene/src/worker/deterministic.steps.mts`
- **initialize()** (1 connections) — `engines/midscene/src/resolve-hook.mts`
- **resolve()** (1 connections) — `engines/midscene/src/resolve-hook.mts`
- **ADR-0020** (1 connections) — `engines/midscene/src/worker/deterministic.steps.mts`
- **deterministic.test.mts** (1 connections) — `engines/midscene/src/worker/deterministic.test.mts`
- **LoadUserStepsDeps** (1 connections) — `engines/midscene/src/worker/user-steps.mts`
- **STEP_EXTS** (1 connections) — `engines/midscene/src/worker/user-steps.mts`
- **BIN** (1 connections) — `engines/midscene/src/worker/user-steps.test.mts`
- **runBin()** (1 connections) — `engines/midscene/src/worker/user-steps.test.mts`
- **tmpSteps()** (1 connections) — `engines/midscene/src/worker/user-steps.test.mts`
- **TSX_LOADER** (1 connections) — `engines/midscene/src/worker/user-steps.test.mts`

## Relationships

- [Midscene Job Source](Midscene_Job_Source.md) (3 shared connections)
- [TS Deterministic Registry](TS_Deterministic_Registry.md) (3 shared connections)
- [Midscene Run Scope](Midscene_Run_Scope.md) (3 shared connections)
- [Midscene Worker Tests](Midscene_Worker_Tests.md) (2 shared connections)
- [Model Spike Scripts](Model_Spike_Scripts.md) (1 shared connections)

## Source Files

- `engines/midscene/src/bin.mts`
- `engines/midscene/src/index.mts`
- `engines/midscene/src/resolve-hook.mts`
- `engines/midscene/src/worker/deterministic.steps.mts`
- `engines/midscene/src/worker/deterministic.test.mts`
- `engines/midscene/src/worker/user-steps.mts`
- `engines/midscene/src/worker/user-steps.test.mts`

## Audit Trail

- EXTRACTED: 37 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*