# Atomic Local Writes

> 29 nodes · cohesion 0.10

## Key Concepts

- **atomic_write_json()** (14 connections) — `core/gherkai_core/adapters/_atomic.py`
- **result_store/local.py** (12 connections) — `core/gherkai_core/adapters/result_store/local.py`
- **test_atomic_write.py** (10 connections) — `core/tests/test_atomic_write.py`
- **atomic_write_text()** (9 connections) — `core/gherkai_core/adapters/_atomic.py`
- **.write()** (8 connections) — `core/gherkai_core/adapters/report_store/local.py`
- **_atomic.py** (7 connections) — `core/gherkai_core/adapters/_atomic.py`
- **.save_job_result()** (5 connections) — `core/gherkai_core/adapters/result_store/local.py`
- **result_store/__init__.py** (3 connections) — `core/gherkai_core/adapters/result_store/__init__.py`
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
- **ResultStore adapters（ADR 0016）：local（本包 `local.py`）+ S3（`s3.py`，ADR 0030 决定六）。…** (1 connections) — `core/gherkai_core/adapters/result_store/__init__.py`
- **LocalResultStore（ADR 0016 数据面）：每 job 的判定结果追加落盘成单独 JSON。 数据面（追加为主）：一次 run 的每个…** (1 connections) — `core/gherkai_core/adapters/result_store/local.py`
- **把单个 JobResult 落盘成 <root>/<run_id>/jobs/<encoded_scope_id>.json（追加，写面）。…** (1 connections) — `core/gherkai_core/adapters/result_store/local.py`
- **共享原子落盘助手（`gherkai_core.adapters._atomic`）的通用性质：并发读者只看到完整内容、权限按声明、失败不留 tmp。 三个…** (1 connections) — `core/tests/test_atomic_write.py`
- **写失败（这里让目标是个目录，os.replace 必炸）时 tmp 要清掉、异常照常冒泡——不留残骸给 glob 到。** (1 connections) — `core/tests/test_atomic_write.py`
- *... and 4 more nodes in this community*

## Relationships

- [DynamoDB RunStore Adapter](DynamoDB_RunStore_Adapter.md) (7 shared connections)
- [Report Index Collection](Report_Index_Collection.md) (5 shared connections)
- [Local Result Store & Persistence](Local_Result_Store_%26_Persistence.md) (4 shared connections)
- [S3 Result Store](S3_Result_Store.md) (3 shared connections)
- [Text Render & Wording Guards](Text_Render_%26_Wording_Guards.md) (1 shared connections)
- [Local Report Store](Local_Report_Store.md) (1 shared connections)
- [Cloud Boto3 Guards & EventLog](Cloud_Boto3_Guards_%26_EventLog.md) (1 shared connections)

## Source Files

- `core/gherkai_core/adapters/_atomic.py`
- `core/gherkai_core/adapters/report_store/local.py`
- `core/gherkai_core/adapters/result_store/__init__.py`
- `core/gherkai_core/adapters/result_store/local.py`
- `core/tests/test_atomic_write.py`

## Audit Trail

- EXTRACTED: 62 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*