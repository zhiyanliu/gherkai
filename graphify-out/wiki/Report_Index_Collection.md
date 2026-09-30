# Report Index Collection

> 13 nodes · cohesion 0.18

## Key Concepts

- **collect_report_index()** (7 connections) — `core/gherkai_core/adapters/report_store/local.py`
- **._collect()** (7 connections) — `core/gherkai_core/adapters/report_store/local.py`
- **.write()** (6 connections) — `core/gherkai_core/adapters/report_store/s3.py`
- **local_path_from_uri()** (5 connections) — `core/gherkai_core/adapters/report_store/local.py`
- **_relative_href()** (5 connections) — `core/gherkai_core/adapters/report_store/local.py`
- **Path** (4 connections)
- **.__init__()** (2 connections) — `core/gherkai_core/adapters/report_store/local.py`
- **遍历 result 树投影 report_index（复用共享 collect_report_index）。 make_href：把落在 run…** (1 connections) — `core/gherkai_core/adapters/report_store/local.py`
- **把 run 树内的本地产物 ref 转成相对 run_dir 的 href；否则原样返回 ref（ADR 0027 href 相对化）。…** (1 connections) — `core/gherkai_core/adapters/report_store/local.py`
- **若 ref 指向本地文件（file:// 或裸路径），返回 Path；远端（http/s3 等）返回 None。 **公开小工具**（本模块 href…** (1 connections) — `core/gherkai_core/adapters/report_store/local.py`
- **遍历 result 树，把每个 ReportRef 投影成一条扁平 index 项（三级，ADR 0027）——**local/s3 共享的单一真理源**。…** (1 connections) — `core/gherkai_core/adapters/report_store/local.py`
- **ResourceUri** (1 connections)
- **把 manifest.json + index.html 写到 `s3://bucket/<prefix><run_id>/`，返回 index.html 的…** (1 connections) — `core/gherkai_core/adapters/report_store/s3.py`

## Relationships

- [Atomic Write and Report Stores](Atomic_Write_and_Report_Stores.md) (6 shared connections)
- [Run Result Aggregation Tree](Run_Result_Aggregation_Tree.md) (3 shared connections)
- [Local Report Store](Local_Report_Store.md) (2 shared connections)
- [Result Store & Report Refs](Result_Store_%26_Report_Refs.md) (1 shared connections)
- [SSM Path Naming](SSM_Path_Naming.md) (1 shared connections)
- [S3 Store Adapters](S3_Store_Adapters.md) (1 shared connections)

## Source Files

- `core/gherkai_core/adapters/report_store/local.py`
- `core/gherkai_core/adapters/report_store/s3.py`

## Audit Trail

- EXTRACTED: 27 (96%)
- INFERRED: 1 (4%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*