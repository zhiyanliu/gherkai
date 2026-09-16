# Tunnel PID File

> 2 nodes · cohesion 1.00

## Key Concepts

- **write_tunnel_file()** (3 connections) — `runtime/gherkai_runtime/detached.py`
- **local submit 落隧道收尾凭据：进程对象句柄跨进程传不过去，pid 落盘是唯一通道（ADR 0035）。** (1 connections) — `runtime/gherkai_runtime/detached.py`

## Relationships

- [SQLite Event Log](SQLite_Event_Log.md) (1 shared connections)
- [CLI Command Entry Points](CLI_Command_Entry_Points.md) (1 shared connections)

## Source Files

- `runtime/gherkai_runtime/detached.py`

## Audit Trail

- EXTRACTED: 2 (67%)
- INFERRED: 1 (33%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*