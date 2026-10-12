# Atomic Local File Writes

> 26 nodes · cohesion 0.11

## Key Concepts

- **atomic_write_json()** (14 connections) — `core/gherkai_core/adapters/_atomic.py`
- **_atomic.py** (10 connections) — `core/gherkai_core/adapters/_atomic.py`
- **test_atomic_write.py** (10 connections) — `core/tests/test_atomic_write.py`
- **atomic_write_text()** (9 connections) — `core/gherkai_core/adapters/_atomic.py`
- **.write()** (8 connections) — `core/gherkai_core/adapters/report_store/local.py`
- **.save_job_result()** (5 connections) — `core/gherkai_core/adapters/result_store/local.py`
- **ResultStore adapters (local / s3)** (4 connections) — `core/DEVELOPMENT.md`
- **_page()** (3 connections) — `core/tests/test_atomic_write.py`
- **test_concurrent_reader_never_sees_empty_or_truncated_text()** (3 connections) — `core/tests/test_atomic_write.py`
- **test_failed_replace_leaves_no_tmp_behind()** (3 connections) — `core/tests/test_atomic_write.py`
- **test_json_round_trip_and_default_mode_readable_by_others()** (3 connections) — `core/tests/test_atomic_write.py`
- **test_mode_can_be_narrowed()** (3 connections) — `core/tests/test_atomic_write.py`
- **test_target_name_at_name_max_still_writable()** (3 connections) — `core/tests/test_atomic_write.py`
- **Path** (2 connections)
- **本地 adapter 共享的原子落盘（同目录 tmp + `os.replace`）：读者要么看到旧文件、要么看到新文件，绝不看到半截/空内容。…** (1 connections) — `core/gherkai_core/adapters/_atomic.py`
- **把 text 原子落到 path（UTF-8）：写同目录 tmp → chmod 成 mode → `os.replace` 顶上。失败清理 tmp、异常冒泡。** (1 connections) — `core/gherkai_core/adapters/_atomic.py`
- **同 `atomic_write_text`，内容是 obj 的 JSON（`ensure_ascii=False, indent=2`——全仓落盘口径一致）。** (1 connections) — `core/gherkai_core/adapters/_atomic.py`
- **ResourceUri** (1 connections)
- **归集出 <root>/<run_id>/{manifest.json, index.html}，返回 index.html 的 file://…** (1 connections) — `core/gherkai_core/adapters/report_store/local.py`
- **把单个 JobResult 落盘成 <root>/<run_id>/jobs/<encoded_scope_id>.json（追加，写面）。…** (1 connections) — `core/gherkai_core/adapters/result_store/local.py`
- **共享原子落盘助手（`gherkai_core.adapters._atomic`）的通用性质：并发读者只看到完整内容、权限按声明、失败不留 tmp。 三个…** (1 connections) — `core/tests/test_atomic_write.py`
- **写失败（这里让目标是个目录，os.replace 必炸）时 tmp 要清掉、异常照常冒泡——不留残骸给 glob 到。** (1 connections) — `core/tests/test_atomic_write.py`
- **报告 index.html 量级（几十 KB）的页面：内容长度随 tick 变，防「两次写恰好等长」掩盖撕裂。** (1 connections) — `core/tests/test_atomic_write.py`
- **默认权限给 group/other 读：判定真值与报告产物的消费者是 CI/人/静态 server（ADR 0034 / 0027）， 而 tmp 文件本身是…** (1 connections) — `core/tests/test_atomic_write.py`
- **控制面（run_meta/run_state）要 0600：调用方声明的 mode 必须被照落，别被默认值顶掉。** (1 connections) — `core/tests/test_atomic_write.py`
- *... and 1 more nodes in this community*

## Relationships

- [Report Store Collection](Report_Store_Collection.md) (5 shared connections)
- [Local Result Store](Local_Result_Store.md) (2 shared connections)
- [SQLite Event Log Adapter](SQLite_Event_Log_Adapter.md) (2 shared connections)
- [Cloud Launcher & Fargate Adapters](Cloud_Launcher_%26_Fargate_Adapters.md) (2 shared connections)
- [S3 Result Store](S3_Result_Store.md) (2 shared connections)
- [Reconcile Tick & Report Finalize](Reconcile_Tick_%26_Report_Finalize.md) (1 shared connections)
- [Run State Rendering & DDB Store](Run_State_Rendering_%26_DDB_Store.md) (1 shared connections)
- [Result Rendering & Explain](Result_Rendering_%26_Explain.md) (1 shared connections)
- [Local Report Store](Local_Report_Store.md) (1 shared connections)
- [Cloud Store Composition Root](Cloud_Store_Composition_Root.md) (1 shared connections)
- [Job State Serialization](Job_State_Serialization.md) (1 shared connections)
- [Local Result Store & Persistence](Local_Result_Store_%26_Persistence.md) (1 shared connections)

## Source Files

- `core/DEVELOPMENT.md`
- `core/gherkai_core/adapters/_atomic.py`
- `core/gherkai_core/adapters/report_store/local.py`
- `core/gherkai_core/adapters/result_store/local.py`
- `core/tests/test_atomic_write.py`

## Audit Trail

- EXTRACTED: 55 (98%)
- INFERRED: 1 (2%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*