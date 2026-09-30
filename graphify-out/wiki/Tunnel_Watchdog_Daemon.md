# Tunnel Watchdog Daemon

> 2 nodes · cohesion 1.00

## Key Concepts

- **_cmd_tunnel_watch()** (3 connections) — `cli/gherkai_cli/__main__.py`
- **隧道守护进程入口（cloud submit setsid fork 它，非使用方直接调，ADR 0035 决策 3）。 守护主体在…** (1 connections) — `cli/gherkai_cli/__main__.py`

## Relationships

- [CLI Entry and Plan](CLI_Entry_and_Plan.md) (1 shared connections)
- [CLI Command Handlers](CLI_Command_Handlers.md) (1 shared connections)

## Source Files

- `cli/gherkai_cli/__main__.py`

## Audit Trail

- EXTRACTED: 3 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*