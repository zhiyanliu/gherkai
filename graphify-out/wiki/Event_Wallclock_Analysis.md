# Event Wallclock Analysis

> 16 nodes · cohesion 0.20

## Key Concepts

- **events_wallclock.py** (10 connections) — `tools/events_wallclock.py`
- **analyze()** (7 connections) — `tools/events_wallclock.py`
- **_acts_from_scope()** (4 connections) — `tools/events_wallclock.py`
- **_emit_epoch()** (3 connections) — `tools/events_wallclock.py`
- **main()** (3 connections) — `tools/events_wallclock.py`
- **_percentile()** (3 connections) — `tools/events_wallclock.py`
- **_query_by_pk()** (3 connections) — `tools/events_wallclock.py`
- **_scan_by_run_id()** (3 connections) — `tools/events_wallclock.py`
- **_summary()** (3 connections) — `tools/events_wallclock.py`
- **_print_human()** (2 connections) — `tools/events_wallclock.py`
- **_table()** (2 connections) — `tools/events_wallclock.py`
- **线性插值分位数（q∈[0,1]）。sorted_vals 非空、已升序。** (1 connections) — `tools/events_wallclock.py`
- **Scan + FilterExpression begins_with(pk, "<run_id>#") 圈本 run 全 scope 的…** (1 connections) — `tools/events_wallclock.py`
- **Query 单 scope（PK=pk），强一致读全事件（免最终一致漏读；分析是事后一次性、成本忽略）。** (1 connections) — `tools/events_wallclock.py`
- **从 item 的 expires_at 还原 worker emit epoch 秒（= expires_at - 7d）。缺…** (1 connections) — `tools/events_wallclock.py`
- **一个 scope（pk）的 items → 单 act 墙钟列表。 按 seq 升序，配对同 (scenario_id, step_index) 的…** (1 connections) — `tools/events_wallclock.py`

## Relationships

- No strong cross-community connections detected

## Source Files

- `tools/events_wallclock.py`

## Audit Trail

- EXTRACTED: 24 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*