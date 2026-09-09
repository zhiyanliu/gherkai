# S3 Argument Offloader

> 13 nodes · cohesion 0.19

## Key Concepts

- **S3StepArgumentOffloader** (24 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **.offload()** (5 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **.restore()** (4 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **._fetch()** (3 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **.__init__()** (3 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **._put()** (3 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **._key()** (2 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **按 s3:// URI 取回 JSON 值（解析出 bucket/key，不重算——URI 自描述）。** (1 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **把 RunMeta 里 docString/dataTable 的正文搬 S3（DdbRunStore 注入）。offload/restore 一对，互逆。** (1 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **s3_client：boto3 s3 client（组合根注入；建桶责任在 IaC）。prefix：可选 key 前缀。** (1 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **把值 JSON 化上传，返回 s3:// URI（自描述指针，restore 直接按它取回、不重算 key）。** (1 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **就地把每个 docString 的 content / dataTable 的 rows 搬 S3、原键换成 content_ref / rows_ref。…** (1 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **就地把 content_ref / rows_ref 取回、消解回内联 content / rows（offload 的逆）。 按「哪个 _ref…** (1 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`

## Relationships

- [S3 Report Store & Subprocess](S3_Report_Store_%26_Subprocess.md) (5 shared connections)
- [Boto Guard & S3 Offload](Boto_Guard_%26_S3_Offload.md) (4 shared connections)
- [Engine Ports & Adapters](Engine_Ports_%26_Adapters.md) (3 shared connections)
- [Cloud Test Fixtures](Cloud_Test_Fixtures.md) (2 shared connections)
- [Reconciler Lambda](Reconciler_Lambda.md) (2 shared connections)
- [SSM Path & Client Composition](SSM_Path_%26_Client_Composition.md) (2 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (1 shared connections)
- [Cloud Store Composition](Cloud_Store_Composition.md) (1 shared connections)

## Source Files

- `core/gherkai_core/adapters/run_store/arg_offload.py`

## Audit Trail

- EXTRACTED: 25 (71%)
- INFERRED: 10 (29%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*