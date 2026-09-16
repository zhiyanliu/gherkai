# Tunnel Watch Daemon

> 2 nodes · cohesion 1.00

## Key Concepts

- **_cmd_tunnel_watch()** (3 connections) — `cli/gherkai_cli/__main__.py`
- **隧道守护进程入口（cloud submit setsid fork 它，非用户直接调，ADR 0035 决策 3）。 守护主体在…** (1 connections) — `cli/gherkai_cli/__main__.py`

## Relationships

- [CLI Main Flow Tests](CLI_Main_Flow_Tests.md) (1 shared connections)
- [CLI Command Entry Points](CLI_Command_Entry_Points.md) (1 shared connections)

## Source Files

- `cli/gherkai_cli/__main__.py`

## Audit Trail

- EXTRACTED: 3 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*