# AWS Unreachable Error Handling

> 2 nodes · cohesion 1.00

## Key Concepts

- **test_list_workers_reports_unreachable_aws_without_a_traceback()** (4 connections) — `deploy_aws/tests/test_workers.py`
- **建不出 client（这里用不存在的 profile 名）→ 退出码 2 + 一句人话，不吐 botocore 堆栈。…** (1 connections) — `deploy_aws/tests/test_workers.py`

## Relationships

- [Worker Image Tests](Worker_Image_Tests.md) (2 shared connections)
- [Worker Image Mapping & Cleanup](Worker_Image_Mapping_%26_Cleanup.md) (1 shared connections)

## Source Files

- `deploy_aws/tests/test_workers.py`

## Audit Trail

- EXTRACTED: 4 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*