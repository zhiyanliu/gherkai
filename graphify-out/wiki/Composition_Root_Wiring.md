# Composition Root Wiring

> 41 nodes · cohesion 0.08

## Key Concepts

- **compose.py** (69 connections) — `runtime/gherkai_runtime/compose.py`
- **WorkerVariantError** (26 connections) — `runtime/gherkai_runtime/compose.py`
- **ssm_path()** (19 connections) — `runtime/gherkai_runtime/names.py`
- **resolve_worker_variant()** (15 connections) — `runtime/gherkai_runtime/compose.py`
- **resolve_default_worker_task_defs()** (14 connections) — `runtime/gherkai_runtime/compose.py`
- **WorkerResolution** (13 connections) — `runtime/gherkai_runtime/compose.py`
- **read_worker_default()** (8 connections) — `runtime/gherkai_runtime/compose.py`
- **_read_worker_image_record()** (8 connections) — `runtime/gherkai_runtime/compose.py`
- **_make_ssm_client()** (7 connections) — `runtime/gherkai_runtime/compose.py`
- **is_botocore_error()** (5 connections) — `runtime/gherkai_runtime/compose.py`
- **_no_default_pointer_error()** (5 connections) — `runtime/gherkai_runtime/compose.py`
- **_release_cmp()** (5 connections) — `runtime/gherkai_runtime/compose.py`
- **_make_ecs_client()** (4 connections) — `runtime/gherkai_runtime/compose.py`
- **_ssm_get()** (4 connections) — `runtime/gherkai_runtime/compose.py`
- **test_read_worker_default_missing_is_none()** (4 connections) — `runtime/tests/test_worker_variant.py`
- **_make_ecr_client()** (3 connections) — `runtime/gherkai_runtime/compose.py`
- **_release_key()** (3 connections) — `runtime/gherkai_runtime/compose.py`
- **_variant_miss_hint()** (3 connections) — `runtime/gherkai_runtime/compose.py`
- **test_is_botocore_error_classifies()** (3 connections) — `runtime/tests/test_compose.py`
- **_make_lambda_client()** (2 connections) — `runtime/gherkai_runtime/compose.py`
- **new_run_id()** (2 connections) — `runtime/gherkai_runtime/compose.py`
- **BaseException** (1 connections)
- **组合根：把抽象的 core 接线到具体的引擎子进程（ADR 0016）。 core 只认 `EngineResolver`（按 engine 名给一个…** (1 connections) — `runtime/gherkai_runtime/compose.py`
- **读 `worker-image/<engine>/<tag>` 的 JSON 记录 → dict；参数不在 → None。 JSON 畸形（人手改坏参数）翻成…** (1 connections) — `runtime/gherkai_runtime/compose.py`
- **variant 某一环 miss 时的整句提示——**按版本 skew 分叉**（ADR 0038「preflight」条）。 CLI **旧于**后端（决策…** (1 connections) — `runtime/gherkai_runtime/compose.py`
- *... and 16 more nodes in this community*

## Relationships

- [Worker Variant Resolution](Worker_Variant_Resolution.md) (12 shared connections)
- [S3 ReportStore & Subprocess Engine](S3_ReportStore_%26_Subprocess_Engine.md) (12 shared connections)
- [Resource Naming Source](Resource_Naming_Source.md) (10 shared connections)
- [Run Result Verdict Model](Run_Result_Verdict_Model.md) (7 shared connections)
- [Cloud Store Composition](Cloud_Store_Composition.md) (7 shared connections)
- [Engine Ports & Adapters](Engine_Ports_%26_Adapters.md) (5 shared connections)
- [Worker Command Resolution](Worker_Command_Resolution.md) (5 shared connections)
- [Local Stores & Deterministic Query](Local_Stores_%26_Deterministic_Query.md) (4 shared connections)
- [Backend Version Stamp Check](Backend_Version_Stamp_Check.md) (4 shared connections)
- [CDK App & Deploy CLI](CDK_App_%26_Deploy_CLI.md) (4 shared connections)
- [Timestamp and Clock Utilities](Timestamp_and_Clock_Utilities.md) (3 shared connections)
- [Engine Resolver Building](Engine_Resolver_Building.md) (3 shared connections)

## Source Files

- `runtime/gherkai_runtime/compose.py`
- `runtime/gherkai_runtime/names.py`
- `runtime/tests/test_compose.py`
- `runtime/tests/test_worker_variant.py`

## Audit Trail

- EXTRACTED: 145 (82%)
- INFERRED: 31 (18%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*