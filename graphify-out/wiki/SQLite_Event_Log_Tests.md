# SQLite Event Log Tests

> 19 nodes · cohesion 0.15

## Key Concepts

- **test_sqlite_event_log.py** (21 connections) — `core/tests/test_sqlite_event_log.py`
- **_log()** (10 connections) — `core/tests/test_sqlite_event_log.py`
- **test_records_feed_project_to_terminal()** (8 connections) — `core/tests/test_sqlite_event_log.py`
- **test_append_idempotent_same_seq()** (3 connections) — `core/tests/test_sqlite_event_log.py`
- **test_exit_code_none_stored()** (3 connections) — `core/tests/test_sqlite_event_log.py`
- **test_exit_record_independent_keyspace()** (3 connections) — `core/tests/test_sqlite_event_log.py`
- **test_has_exit_single_scope()** (3 connections) — `core/tests/test_sqlite_event_log.py`
- **test_opening_a_v140_shaped_db_adds_the_reason_column()** (3 connections) — `core/tests/test_sqlite_event_log.py`
- **test_record_exit_reason_roundtrip()** (3 connections) — `core/tests/test_sqlite_event_log.py`
- **test_append_and_read_back_events()** (2 connections) — `core/tests/test_sqlite_event_log.py`
- **test_max_seq_empty_is_zero()** (2 connections) — `core/tests/test_sqlite_event_log.py`
- **SqliteEventLog 测试（ADR 0034 P3）：持久事件通道往返 + 与 project 联通。 存原始 JSON 行→读回解析成…** (1 connections) — `core/tests/test_sqlite_event_log.py`
- **唯一存活的迁移分支必须有红灯：v1.4.0（已发行）建的 exits 表没有 reason 列，新版接力同一 run 的 events.db 时…** (1 connections) — `core/tests/test_sqlite_event_log.py`
- **退出记录走独立键空间（机制一）：不占 events 的 seq，records() 里 kind='exit'。** (1 connections) — `core/tests/test_sqlite_event_log.py`
- **has_exit 只看本 scope 的退出记录（对位 DdbEventLog.has_exit）：worker 事件不算、别的 scope 不串扰。** (1 connections) — `core/tests/test_sqlite_event_log.py`
- **exit_code=None（退出码未知，仅超时处置直写时出现）可存、读回仍是 None——投影侧判 ERROR、不是宽限态（ADR 0034…** (1 connections) — `core/tests/test_sqlite_event_log.py`
- **同 (scope,seq) 重写幂等（重放/重试无副作用，镜像 DDB PutItem 幂等）。** (1 connections) — `core/tests/test_sqlite_event_log.py`
- **端到端：SQLite records() → project() 推出正确终态（两件都要齐 → passed）。** (1 connections) — `core/tests/test_sqlite_event_log.py`
- **reason（平台侧归因串，port 对称 DDB）随退出记录落库、records() 读回；不传则 None。** (1 connections) — `core/tests/test_sqlite_event_log.py`

## Relationships

- [Job Explain & S3 Offload](Job_Explain_%26_S3_Offload.md) (8 shared connections)
- [SQLite Event Log](SQLite_Event_Log.md) (3 shared connections)
- [Run State Projection](Run_State_Projection.md) (2 shared connections)
- [Cloud Boto3 Guards & EventLog](Cloud_Boto3_Guards_%26_EventLog.md) (2 shared connections)
- [Event Formatting](Event_Formatting.md) (1 shared connections)
- [Cloud Job Launcher](Cloud_Job_Launcher.md) (1 shared connections)

## Source Files

- `core/tests/test_sqlite_event_log.py`

## Audit Trail

- EXTRACTED: 43 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*