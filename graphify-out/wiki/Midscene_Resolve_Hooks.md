# Midscene Resolve Hooks

> 26 nodes · cohesion 0.10

## Key Concepts

- **ADR-0037** (11 connections) — `engines/midscene/src/bin.mts`
- **user-steps.mts** (8 connections) — `engines/midscene/src/worker/user-steps.mts`
- **ADR-0036** (7 connections) — `engines/midscene/src/index.mts`
- **bin.mts** (6 connections) — `engines/midscene/src/bin.mts`
- **user-steps.test.mts** (6 connections) — `engines/midscene/src/worker/user-steps.test.mts`
- **ADR-0028** (5 connections) — `engines/midscene/src/bin.mts`
- **ADR-0022** (5 connections) — `engines/midscene/src/index.mts`
- **deterministic.steps.mts** (5 connections) — `engines/midscene/src/worker/deterministic.steps.mts`
- **index.mts** (3 connections) — `engines/midscene/src/index.mts`
- **resolve-hook.mts** (3 connections) — `engines/midscene/src/resolve-hook.mts`
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
- **tmpSteps()** (1 connections) — `engines/midscene/src/worker/user-steps.test.mts`
- *... and 1 more nodes in this community*

## Relationships

- [Midscene Run Scope](Midscene_Run_Scope.md) (6 shared connections)
- [Run Scope Tests](Run_Scope_Tests.md) (3 shared connections)
- [Deterministic Step Registry](Deterministic_Step_Registry.md) (3 shared connections)
- [Step Argument & Sink Tests](Step_Argument_%26_Sink_Tests.md) (1 shared connections)
- [Artifact Upload & Error Text](Artifact_Upload_%26_Error_Text.md) (1 shared connections)
- [Model Spike Scripts](Model_Spike_Scripts.md) (1 shared connections)
- [Event Sink & Job Source](Event_Sink_%26_Job_Source.md) (1 shared connections)

## Source Files

- `engines/midscene/src/bin.mts`
- `engines/midscene/src/index.mts`
- `engines/midscene/src/resolve-hook.mts`
- `engines/midscene/src/worker/deterministic.steps.mts`
- `engines/midscene/src/worker/deterministic.test.mts`
- `engines/midscene/src/worker/no-artifacts.test.mts`
- `engines/midscene/src/worker/user-steps.mts`
- `engines/midscene/src/worker/user-steps.test.mts`

## Audit Trail

- EXTRACTED: 47 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*