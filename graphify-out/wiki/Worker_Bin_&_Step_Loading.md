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

- [TypeScript Deterministic Hooks](TypeScript_Deterministic_Hooks.md) (3 shared connections)
- [TS Event Sink & Upload](TS_Event_Sink_%26_Upload.md) (3 shared connections)
- [Run Scope (TS Worker)](Run_Scope_%28TS_Worker%29.md) (2 shared connections)
- [Run Scope Integration Tests](Run_Scope_Integration_Tests.md) (1 shared connections)

## Source Files

- `engines/midscene/src/bin.mts`
- `engines/midscene/src/worker/user-steps.mts`

## Audit Trail

- EXTRACTED: 18 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*