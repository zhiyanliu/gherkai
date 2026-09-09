# Local Report Store

> 25 nodes · cohesion 0.11

## Key Concepts

- **report_store/local.py** (13 connections) — `core/gherkai_core/adapters/report_store/local.py`
- **report_store/s3.py** (9 connections) — `core/gherkai_core/adapters/report_store/s3.py`
- **collect_report_index()** (7 connections) — `core/gherkai_core/adapters/report_store/local.py`
- **._collect()** (7 connections) — `core/gherkai_core/adapters/report_store/local.py`
- **_render_index_html()** (7 connections) — `core/gherkai_core/adapters/report_store/local.py`
- **.write()** (6 connections) — `core/gherkai_core/adapters/report_store/local.py`
- **.write()** (6 connections) — `core/gherkai_core/adapters/report_store/s3.py`
- **_relative_href()** (5 connections) — `core/gherkai_core/adapters/report_store/local.py`
- **_local_path()** (4 connections) — `core/gherkai_core/adapters/report_store/local.py`
- **Path** (4 connections)
- **report_store/__init__.py** (3 connections) — `core/gherkai_core/adapters/report_store/__init__.py`
- **_fmt_ms()** (2 connections) — `core/gherkai_core/adapters/report_store/local.py`
- **.__init__()** (2 connections) — `core/gherkai_core/adapters/report_store/local.py`
- **ReportStore adapters（ADR 0027）。当前只有 local；未来 s3。** (1 connections) — `core/gherkai_core/adapters/report_store/__init__.py`
- **ResourceUri** (1 connections)
- **LocalReportStore（ADR 0027）：把一次 run 的报告产物归集成本地一份自包含目录。 产出…** (1 connections) — `core/gherkai_core/adapters/report_store/local.py`
- **遍历 result 树投影 report_index（复用共享 collect_report_index）。 make_href：把落在 run…** (1 connections) — `core/gherkai_core/adapters/report_store/local.py`
- **把 run 树内的本地产物 ref 转成相对 run_dir 的 href；否则原样返回 ref（ADR 0027 href 相对化）。…** (1 connections) — `core/gherkai_core/adapters/report_store/local.py`
- **若 ref 指向本地文件（file:// 或裸路径），返回 Path；远端（http/s3 等）返回 None。 用 url2pathname 正确还原…** (1 connections) — `core/gherkai_core/adapters/report_store/local.py`
- **渲染入口页。manifest 提供 run_id/created_at/report_index；result（内存 RunResult）提供判定明细 +…** (1 connections) — `core/gherkai_core/adapters/report_store/local.py`
- **遍历 result 树，把每个 ReportRef 投影成一条扁平 index 项（三级，ADR 0027）——**local/s3 共享的单一真理源**。…** (1 connections) — `core/gherkai_core/adapters/report_store/local.py`
- **归集出 <root>/<run_id>/{manifest.json, index.html}，返回 index.html 的 file://…** (1 connections) — `core/gherkai_core/adapters/report_store/local.py`
- **ResourceUri** (1 connections)
- **S3ReportStore（ADR 0030 决定六 / 0027 / 0029）：ReportStore port 的 S3 实装。 把一次 run 的…** (1 connections) — `core/gherkai_core/adapters/report_store/s3.py`
- **把 manifest.json + index.html 写到 `s3://bucket/<prefix><run_id>/`，返回 index.html 的…** (1 connections) — `core/gherkai_core/adapters/report_store/s3.py`

## Relationships

- [Report Refs & Results](Report_Refs_%26_Results.md) (8 shared connections)
- [Run Result Rendering](Run_Result_Rendering.md) (7 shared connections)
- [Engine Ports & Adapters](Engine_Ports_%26_Adapters.md) (2 shared connections)
- [Boto Guard & S3 Offload](Boto_Guard_%26_S3_Offload.md) (2 shared connections)
- [S3 Report Store & Subprocess](S3_Report_Store_%26_Subprocess.md) (2 shared connections)

## Source Files

- `core/gherkai_core/adapters/report_store/__init__.py`
- `core/gherkai_core/adapters/report_store/local.py`
- `core/gherkai_core/adapters/report_store/s3.py`

## Audit Trail

- EXTRACTED: 54 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*