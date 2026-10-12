# Revision Cleanup Pass

> 13 nodes · cohesion 0.15

## Key Concepts

- **cleanup_pass()** (15 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **CleanupOutcome** (6 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **_iter_image_params()** (5 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **_mapped_arn()** (4 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **_referenced_by_live_run()** (4 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **_hours()** (3 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **_non_terminal_statuses()** (3 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **枚举 `worker-image/*` 全部参数（**含所有版本、所有引擎**）→ `(engine, tag, value)`。…** (1 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **一次 pass 的结果：删掉的 revision + 留到下次的（ARN、原因）。**生产调用点（push-worker / deploy 末步） 只看…** (1 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **未到终态的 run 级 status 全集（`Status` - `TERMINAL_STATUSES`，至少含 `pending`）。 **从 core…** (1 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **有未到终态的 run 引用这个 revision 吗？—— **走 status GSI 的 Query + `contains` 过滤，绝不 Scan**。…** (1 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **回收退休/孤儿 revision（**机会式**：`push-worker` 末步与 `gherkai deploy` 第四步末各执行一次）。…** (1 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **映射 JSON → 它引用的 revision ARN（读不懂 → 不产出）。 **读不懂时产出空** 有安全含义：那条映射保护不了它的…** (1 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`

## Relationships

- [AWS Worker Image Registry](AWS_Worker_Image_Registry.md) (13 shared connections)
- [Container Worker Image Tests](Container_Worker_Image_Tests.md) (5 shared connections)
- [List Workers Command](List_Workers_Command.md) (2 shared connections)
- [Container Image Inspection](Container_Image_Inspection.md) (1 shared connections)
- [Cloud Adapter Boundary Modules](Cloud_Adapter_Boundary_Modules.md) (1 shared connections)

## Source Files

- `deploy_aws/gherkai_deploy_aws/workers.py`

## Audit Trail

- EXTRACTED: 32 (94%)
- INFERRED: 2 (6%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*