# S3 Report Store

> 23 nodes · cohesion 0.11

## Key Concepts

- **test_s3_report_store.py** (19 connections) — `core/tests/test_s3_report_store.py`
- **S3ReportStore** (18 connections) — `core/gherkai_core/adapters/report_store/s3.py`
- **WorkerNotFoundError** (15 connections) — `runtime/gherkai_runtime/compose.py`
- **CloudTarget** (14 connections) — `runtime/gherkai_runtime/compose.py`
- **WorkerCmd** (13 connections) — `runtime/gherkai_runtime/compose.py`
- **_read_s3()** (6 connections) — `core/tests/test_s3_report_store.py`
- **test_empty_report_refs_still_valid_index()** (5 connections) — `core/tests/test_s3_report_store.py`
- **_read_manifest()** (4 connections) — `core/tests/test_s3_report_store.py`
- **test_index_html_links_and_summary()** (3 connections) — `core/tests/test_s3_report_store.py`
- **test_manifest_shape()** (3 connections) — `core/tests/test_s3_report_store.py`
- **test_prefix_lands_under_prefix()** (3 connections) — `core/tests/test_s3_report_store.py`
- **test_s3_href_not_relativized_kept_as_ref()** (3 connections) — `core/tests/test_s3_report_store.py`
- **test_writes_manifest_and_index()** (3 connections) — `core/tests/test_s3_report_store.py`
- **.preflight()** (2 connections) — `core/gherkai_core/adapters/report_store/s3.py`
- **.detached_chain_lambdas()** (2 connections) — `runtime/gherkai_runtime/compose.py`
- **ReportStore 的 S3 实装（组合根注入 boto3 s3 client + bucket + 可选 key 前缀）。行为对拍…** (1 connections) — `core/gherkai_core/adapters/report_store/s3.py`
- **探活（ADR 0030 决定七）：begin 前探桶可达，桶不存在/无权限即抛（cli 接住→以退出码 2 结束）。** (1 connections) — `core/gherkai_core/adapters/report_store/s3.py`
- **S3ReportStore 对拍测试（ADR 0030 决定六 / 0027 / 0029）：与 LocalReportStore 同一批行为断言，moto…** (1 connections) — `core/tests/test_s3_report_store.py`
- **把 write() 返回的 s3:// ResourceUri 取回对象正文（测试侧读内容用）。** (1 connections) — `core/tests/test_s3_report_store.py`
- **一个引擎 worker 的拉起方式即定位链的解析结果（ADR 0037 决策 3）。 cmd/cwd 直接喂 `SubprocessEngine`；**cwd…** (1 connections) — `runtime/gherkai_runtime/compose.py`
- **定位链四级全 miss（ADR 0037 决策 3）：带引擎名 + 该引擎的安装指引，退出码交调用点。 **继承 RuntimeError…** (1 connections) — `runtime/gherkai_runtime/compose.py`
- **一次 cloud 调用打到哪儿：prefix + 各资源终名 + region/profile（ADR 0033 两层命名 / 0016 决策 C）。…** (1 connections) — `runtime/gherkai_runtime/compose.py`
- **无状态批量运行事件驱动链的三 Lambda（ADR 0034）——detached submit 的 preflight 名单，顺序即链上顺序。** (1 connections) — `runtime/gherkai_runtime/compose.py`

## Relationships

- [Local Report Store](Local_Report_Store.md) (14 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (8 shared connections)
- [S3 Result Store Port](S3_Result_Store_Port.md) (6 shared connections)
- [Run Metadata & S3 Offload](Run_Metadata_%26_S3_Offload.md) (5 shared connections)
- [Explain Rendering Tests](Explain_Rendering_Tests.md) (5 shared connections)
- [SSM Paths & Composition Root](SSM_Paths_%26_Composition_Root.md) (5 shared connections)
- [Worker Capability Query](Worker_Capability_Query.md) (3 shared connections)
- [Worker Locator & AWS Resolution](Worker_Locator_%26_AWS_Resolution.md) (3 shared connections)
- [Subprocess Engine Launcher](Subprocess_Engine_Launcher.md) (3 shared connections)
- [Plan Job Generation](Plan_Job_Generation.md) (3 shared connections)
- [Fargate Engine Adapter](Fargate_Engine_Adapter.md) (3 shared connections)
- [Report Store Adapters](Report_Store_Adapters.md) (2 shared connections)

## Source Files

- `core/gherkai_core/adapters/report_store/s3.py`
- `core/tests/test_s3_report_store.py`
- `runtime/gherkai_runtime/compose.py`

## Audit Trail

- EXTRACTED: 56 (61%)
- INFERRED: 36 (39%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*