# Worker Bin & Step Loading

> 9 nodes · cohesion 0.25

## Key Concepts

- **user-steps.mts** (8 connections) — `engines/midscene/src/worker/user-steps.mts`
- **bin.mts** (6 connections) — `engines/midscene/src/bin.mts`
- **ADR-0028** (5 connections) — `engines/midscene/src/bin.mts`
- **collectStepFiles()** (2 connections) — `engines/midscene/src/worker/user-steps.mts`
- **loadUserSteps()** (2 connections) — `engines/midscene/src/worker/user-steps.mts`
- **fromSource** (1 connections) — `engines/midscene/src/bin.mts`
- **hookSpec** (1 connections) — `engines/midscene/src/bin.mts`
- **LoadUserStepsDeps** (1 connections) — `engines/midscene/src/worker/user-steps.mts`
- **STEP_EXTS** (1 connections) — `engines/midscene/src/worker/user-steps.mts`

## Relationships

- [Deterministic Step Resolution (TS)](Deterministic_Step_Resolution_%28TS%29.md) (3 shared connections)
- [TS Artifact & Event Sink](TS_Artifact_%26_Event_Sink.md) (3 shared connections)
- [TypeScript Worker Run Scope](TypeScript_Worker_Run_Scope.md) (2 shared connections)
- [Run Scope Tests](Run_Scope_Tests.md) (1 shared connections)

## Source Files

- `engines/midscene/src/bin.mts`
- `engines/midscene/src/worker/user-steps.mts`

## Audit Trail

- EXTRACTED: 18 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*