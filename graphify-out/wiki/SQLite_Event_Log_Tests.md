# SQLite Event Log Tests

> 13 nodes · cohesion 0.23

## Key Concepts

- **test_sqlite_event_log.py** (19 connections) — `core/tests/test_sqlite_event_log.py`
- **_log()** (9 connections) — `core/tests/test_sqlite_event_log.py`
- **test_append_idempotent_same_seq()** (3 connections) — `core/tests/test_sqlite_event_log.py`
- **test_exit_code_none_stored()** (3 connections) — `core/tests/test_sqlite_event_log.py`
- **test_exit_record_independent_keyspace()** (3 connections) — `core/tests/test_sqlite_event_log.py`
- **test_has_exit_single_scope()** (3 connections) — `core/tests/test_sqlite_event_log.py`
- **test_append_and_read_back_events()** (2 connections) — `core/tests/test_sqlite_event_log.py`
- **test_max_seq_empty_is_zero()** (2 connections) — `core/tests/test_sqlite_event_log.py`
- **SqliteEventLog 测试（ADR 0034 P3）：持久事件通道往返 + 与 project 联通。 存原始 JSON 行→读回解析成…** (1 connections) — `core/tests/test_sqlite_event_log.py`
- **退出记录走独立键空间（机制一）：不占 events 的 seq，records() 里 kind='exit'。** (1 connections) — `core/tests/test_sqlite_event_log.py`
- **has_exit 只看本 scope 的退出记录（对位 DdbEventLog.has_exit）：worker 事件不算、别的 scope 不串扰。** (1 connections) — `core/tests/test_sqlite_event_log.py`
- **exitCode 宽限态（None）可存（机制二兜底）。** (1 connections) — `core/tests/test_sqlite_event_log.py`
- **同 (scope,seq) 重写幂等（重放/重试无副作用，镜像 DDB PutItem 幂等）。** (1 connections) — `core/tests/test_sqlite_event_log.py`

## Relationships

- [Engine Ports & Adapters](Engine_Ports_%26_Adapters.md) (6 shared connections)
- [SQLite Event Log & Projection](SQLite_Event_Log_%26_Projection.md) (2 shared connections)
- [SQLite Event Log Store](SQLite_Event_Log_Store.md) (2 shared connections)
- [Run State Rendering & Boto Guard](Run_State_Rendering_%26_Boto_Guard.md) (1 shared connections)
- [Run Result Verdict Model](Run_Result_Verdict_Model.md) (1 shared connections)
- [Cloud Launcher & DDB EventLog](Cloud_Launcher_%26_DDB_EventLog.md) (1 shared connections)

## Source Files

- `core/tests/test_sqlite_event_log.py`

## Audit Trail

- EXTRACTED: 31 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*