# Task Definition Lineage Cleanup

> 19 nodes · cohesion 0.12

## Key Concepts

- **_register_revision()** (12 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **RevisionInfo** (8 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **scan_family()** (8 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **_pending_cleanup()** (6 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **_describe_revision()** (5 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **_parse_ts()** (5 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **test_pending_cleanup_is_json_serializable_with_real_registered_at()** (5 connections) — `deploy_aws/tests/test_workers.py`
- **_lineage_tags()** (3 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **.retired_at()** (3 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **.has_lineage()** (2 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **family 里的一个 ACTIVE revision + 它的 tags。** (1 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **带血缘 tags 吗？—— **模板 revision 与任何手工注册的 revision 都没有**，故它们永不进清理候选。** (1 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **`DescribeTaskDefinition(include=["TAGS"])` → (taskDefinition, tags dict)。** (1 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **family 的全部 ACTIVE revision（带 tags）。 两个坑：**`familyPrefix` 是前缀匹配**（`gherkai-…** (1 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **tag 里的 ISO 串 / boto3 回来的 datetime → aware UTC datetime；空或读不懂 → None。** (1 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **注册时打的四个血缘 tag（ADR 0038 步 6）——清理对账、`list-workers`、重派生判定全看它们。** (1 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **从**模板 revision** 复制出一个新 revision（镜像栏是 `image_ref`）+ 打血缘 tags → 新 revision ARN。…** (1 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **已退休（带 retired-at）与孤儿（带血缘 tags、不在任何版本的映射里）——清理 pass 的候选，列出来才可解释 「为什么 family 里…** (1 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **真 AWS 的 DescribeTaskDefinition 带 registeredAt（datetime），moto 不带——`--json` 曾因此…** (1 connections) — `deploy_aws/tests/test_workers.py`

## Relationships

- [Worker Image Lifecycle](Worker_Image_Lifecycle.md) (16 shared connections)
- [Worker Image Management Tests](Worker_Image_Management_Tests.md) (7 shared connections)
- [List Workers Command](List_Workers_Command.md) (1 shared connections)
- [Container Engine Errors](Container_Engine_Errors.md) (1 shared connections)
- [Run Result Aggregation Tree](Run_Result_Aggregation_Tree.md) (1 shared connections)

## Source Files

- `deploy_aws/gherkai_deploy_aws/workers.py`
- `deploy_aws/tests/test_workers.py`

## Audit Trail

- EXTRACTED: 44 (96%)
- INFERRED: 2 (4%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*