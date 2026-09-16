# Event Reduction & Short-Circuit

> 4 nodes · cohesion 0.50

## Key Concepts

- **status 三级归约（scenario→job→run）** (2 connections) — `docs/adr/0026-schedule-module.md`
- **step_skipped 归约（scope 内短路）** (2 connections) — `docs/adr/0026-schedule-module.md`
- **job 归约的 scope_done 内容完整前置** (1 connections) — `docs/adr/0026-schedule-module.md`
- **scope 内 step 级短路（worker 侧）** (1 connections) — `docs/adr/0028-transient-network-ssl-resilience.md`

## Relationships

- No strong cross-community connections detected

## Source Files

- `docs/adr/0026-schedule-module.md`
- `docs/adr/0028-transient-network-ssl-resilience.md`

## Audit Trail

- EXTRACTED: 3 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*