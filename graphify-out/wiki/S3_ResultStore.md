# S3 ResultStore

> 14 nodes · cohesion 0.19

## Key Concepts

- **S3ResultStore** (18 connections) — `core/gherkai_core/adapters/result_store/s3.py`
- **.load_all()** (5 connections) — `core/gherkai_core/adapters/result_store/s3.py`
- **.load_job_result()** (5 connections) — `core/gherkai_core/adapters/result_store/s3.py`
- **.save_job_result()** (5 connections) — `core/gherkai_core/adapters/result_store/s3.py`
- **._key()** (4 connections) — `core/gherkai_core/adapters/result_store/s3.py`
- **.__init__()** (3 connections) — `core/gherkai_core/adapters/result_store/s3.py`
- **._jobs_prefix()** (3 connections) — `core/gherkai_core/adapters/result_store/s3.py`
- **.preflight()** (2 connections) — `core/gherkai_core/adapters/result_store/s3.py`
- **ResultStore 的 S3 实装（组合根注入 boto3 s3 client + bucket + 可选 key 前缀）。行为对拍…** (1 connections) — `core/gherkai_core/adapters/result_store/s3.py`
- **s3_client：boto3 s3 client（组合根注入；建桶责任在 IaC，adapter 假定桶已存在）。 prefix：可选 key 前缀（如…** (1 connections) — `core/gherkai_core/adapters/result_store/s3.py`
- **把单个 JobResult 存成一个 S3 对象（写面，追加语义=同 key 覆盖，幂等）。** (1 connections) — `core/gherkai_core/adapters/result_store/s3.py`
- **读回单个 JobResult（按键取，无需查询）；不存在返回 None。** (1 connections) — `core/gherkai_core/adapters/result_store/s3.py`
- **读回某 run 的全部 JobResult（CI 遍历用）。无则空 list。 **必须翻页**：list_objects_v2 单页硬上限 1000…** (1 connections) — `core/gherkai_core/adapters/result_store/s3.py`
- **探活（ADR 0030 决定七）：begin 前探桶可达，桶不存在/无权限即抛（cli 接住→退 2）。** (1 connections) — `core/gherkai_core/adapters/result_store/s3.py`

## Relationships

- [Run Result Verdict Model](Run_Result_Verdict_Model.md) (6 shared connections)
- [ResultStore Local/S3](ResultStore_Local-S3.md) (4 shared connections)
- [Cloud Adapter Test Fixtures](Cloud_Adapter_Test_Fixtures.md) (2 shared connections)
- [DynamoDB RunStore Conditional Writes](DynamoDB_RunStore_Conditional_Writes.md) (2 shared connections)
- [Reconciler Lambda & Timeouts](Reconciler_Lambda_%26_Timeouts.md) (1 shared connections)
- [Cloud Store Composition](Cloud_Store_Composition.md) (1 shared connections)
- [Run State Rendering & Boto Guard](Run_State_Rendering_%26_Boto_Guard.md) (1 shared connections)

## Source Files

- `core/gherkai_core/adapters/result_store/s3.py`

## Audit Trail

- EXTRACTED: 31 (91%)
- INFERRED: 3 (9%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*