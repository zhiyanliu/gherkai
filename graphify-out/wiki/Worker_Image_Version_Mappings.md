# Worker Image Version Mappings

> 4 nodes · cohesion 0.50

## Key Concepts

- **test_current_version_mappings_filters_one_engine_and_version_out_of_a_shared_enumeration()** (4 connections) — `deploy_aws/tests/test_workers.py`
- **_image_param()** (3 connections) — `deploy_aws/tests/test_workers.py`
- **`_iter_image_params` 那种 `(engine, tag, value)` 三元组（不过 SSM，直接喂筛选函数）。** (1 connections) — `deploy_aws/tests/test_workers.py`
- **`current_version_mappings` 吃**已枚举好**的参数序列：只留本引擎 + 本版本的、按 variant 名排序，…** (1 connections) — `deploy_aws/tests/test_workers.py`

## Relationships

- [Container Worker Tests](Container_Worker_Tests.md) (2 shared connections)
- [Worker Image Management](Worker_Image_Management.md) (1 shared connections)

## Source Files

- `deploy_aws/tests/test_workers.py`

## Audit Trail

- EXTRACTED: 6 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*