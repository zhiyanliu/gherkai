# Report Index Collection

> 24 nodes · cohesion 0.12

## Key Concepts

- **report_store/local.py** (17 connections) — `core/gherkai_core/adapters/report_store/local.py`
- **render_index_html()** (9 connections) — `core/gherkai_core/adapters/report_store/local.py`
- **report_store/s3.py** (9 connections) — `core/gherkai_core/adapters/report_store/s3.py`
- **collect_report_index()** (7 connections) — `core/gherkai_core/adapters/report_store/local.py`
- **._collect()** (7 connections) — `core/gherkai_core/adapters/report_store/local.py`
- **.write()** (6 connections) — `core/gherkai_core/adapters/report_store/s3.py`
- **local_path_from_uri()** (5 connections) — `core/gherkai_core/adapters/report_store/local.py`
- **_relative_href()** (5 connections) — `core/gherkai_core/adapters/report_store/local.py`
- **Path** (4 connections)
- **report_store/__init__.py** (3 connections) — `core/gherkai_core/adapters/report_store/__init__.py`
- **_reason_html()** (3 connections) — `core/gherkai_core/adapters/report_store/local.py`
- **_fmt_ms()** (2 connections) — `core/gherkai_core/adapters/report_store/local.py`
- **.__init__()** (2 connections) — `core/gherkai_core/adapters/report_store/local.py`
- **ReportStore adapters（ADR 0027）：local（本包 `local.py`）+ S3（`s3.py`，ADR 0030 决定六）。…** (1 connections) — `core/gherkai_core/adapters/report_store/__init__.py`
- **LocalReportStore（ADR 0027）：把一次 run 的报告产物归集成本地一份自包含目录。 产出…** (1 connections) — `core/gherkai_core/adapters/report_store/local.py`
- **遍历 result 树投影 report_index（复用共享 collect_report_index）。 make_href：把落在 run…** (1 connections) — `core/gherkai_core/adapters/report_store/local.py`
- **把 run 树内的本地产物 ref 转成相对 run_dir 的 href；否则原样返回 ref（ADR 0027 href 相对化）。…** (1 connections) — `core/gherkai_core/adapters/report_store/local.py`
- **若 ref 指向本地文件（file:// 或裸路径），返回 Path；远端（http/s3 等）返回 None。 **公开小工具**（本模块 href…** (1 connections) — `core/gherkai_core/adapters/report_store/local.py`
- **渲染一行的「原因」片段——job 行与 step 行共用同一份，**别再造第三种样式**。 两分支口径同 render_text（有分类 → err…** (1 connections) — `core/gherkai_core/adapters/report_store/local.py`
- **渲染入口页——**local/s3 共享的渲染真理源**（公开名：同包 `s3.py` 是第二个消费者，两 adapter 出一致的入口页）。…** (1 connections) — `core/gherkai_core/adapters/report_store/local.py`
- **遍历 result 树，把每个 ReportRef 投影成一条扁平 index 项（三级，ADR 0027）——**local/s3 共享的单一真理源**。…** (1 connections) — `core/gherkai_core/adapters/report_store/local.py`
- **ResourceUri** (1 connections)
- **S3ReportStore（ADR 0030 决定六 / 0027 / 0029）：ReportStore port 的 S3 实装。 把一次 run 的…** (1 connections) — `core/gherkai_core/adapters/report_store/s3.py`
- **把 manifest.json + index.html 写到 `s3://bucket/<prefix><run_id>/`，返回 index.html 的…** (1 connections) — `core/gherkai_core/adapters/report_store/s3.py`

## Relationships

- [Local Report Store](Local_Report_Store.md) (7 shared connections)
- [Text Render & Wording Guards](Text_Render_%26_Wording_Guards.md) (7 shared connections)
- [Atomic Local Writes](Atomic_Local_Writes.md) (5 shared connections)
- [Cloud Boto3 Guards & EventLog](Cloud_Boto3_Guards_%26_EventLog.md) (4 shared connections)
- [S3 Report Store & Control Plane](S3_Report_Store_%26_Control_Plane.md) (2 shared connections)
- [Cloud Compose Helpers](Cloud_Compose_Helpers.md) (1 shared connections)

## Source Files

- `core/gherkai_core/adapters/report_store/__init__.py`
- `core/gherkai_core/adapters/report_store/local.py`
- `core/gherkai_core/adapters/report_store/s3.py`

## Audit Trail

- EXTRACTED: 56 (97%)
- INFERRED: 2 (3%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*