# Task Definition Revision Lineage

> 4 nodes · cohesion 0.50

## Key Concepts

- **RevisionInfo** (8 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **.has_lineage()** (2 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **family 里的一个 ACTIVE revision + 它的 tags。** (1 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **带血缘 tags 吗？—— **模板 revision 与任何手工注册的 revision 都没有**，故它们永不进清理候选。** (1 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`

## Relationships

- [Worker Image Management](Worker_Image_Management.md) (3 shared connections)
- [Container Worker Tests](Container_Worker_Tests.md) (1 shared connections)
- [Container Engine Adapter](Container_Engine_Adapter.md) (1 shared connections)
- [Cloud Boto3 Guards & EventLog](Cloud_Boto3_Guards_%26_EventLog.md) (1 shared connections)

## Source Files

- `deploy_aws/gherkai_deploy_aws/workers.py`

## Audit Trail

- EXTRACTED: 7 (78%)
- INFERRED: 2 (22%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*