# Backend CDK Stack

> 35 nodes · cohesion 0.09

## Key Concepts

- **BackendStack** (30 connections) — `deploy_aws/gherkai_deploy_aws/stack.py`
- **.__init__()** (11 connections) — `deploy_aws/gherkai_deploy_aws/stack.py`
- **synth_fixture.py** (9 connections) — `deploy_aws/tests/synth_fixture.py`
- **._reconcile_lambdas()** (7 connections) — `deploy_aws/gherkai_deploy_aws/stack.py`
- **._worker_subnet_ids()** (5 connections) — `deploy_aws/gherkai_deploy_aws/stack.py`
- **IVpc** (5 connections)
- **._cluster()** (4 connections) — `deploy_aws/gherkai_deploy_aws/stack.py`
- **._grant_task_role()** (4 connections) — `deploy_aws/gherkai_deploy_aws/stack.py`
- **._network()** (4 connections) — `deploy_aws/gherkai_deploy_aws/stack.py`
- **._one_task_def()** (4 connections) — `deploy_aws/gherkai_deploy_aws/stack.py`
- **._resolve_stop_timeout()** (4 connections) — `deploy_aws/gherkai_deploy_aws/stack.py`
- **._resolve_version()** (4 connections) — `deploy_aws/gherkai_deploy_aws/stack.py`
- **._ssm_network()** (4 connections) — `deploy_aws/gherkai_deploy_aws/stack.py`
- **._advancer_function()** (3 connections) — `deploy_aws/gherkai_deploy_aws/stack.py`
- **._ssm_deployment_stamp()** (3 connections) — `deploy_aws/gherkai_deploy_aws/stack.py`
- **._task_definitions()** (3 connections) — `deploy_aws/gherkai_deploy_aws/stack.py`
- **BackendStack._build_lambda_asset** (3 connections) — `deploy_aws/DEVELOPMENT.md`
- **._storage()** (2 connections) — `deploy_aws/gherkai_deploy_aws/stack.py`
- **._worker_sg_id()** (2 connections) — `deploy_aws/gherkai_deploy_aws/stack.py`
- **BackendStack._worker_subnet_ids** (2 connections) — `deploy_aws/DEVELOPMENT.md`
- **test_version_context_is_required()** (2 connections) — `deploy_aws/tests/test_stack.py`
- **Role** (2 connections)
- **Cluster** (1 connections)
- **Construct** (1 connections)
- **后端版本戳（PEP 440 字符串）：**`-c version=` 必给、无隐式默认**。 单一真源是发起这次部署的命令（`gherkai deploy`…** (1 connections) — `deploy_aws/gherkai_deploy_aws/stack.py`
- *... and 10 more nodes in this community*

## Relationships

- [Lambda Asset Build Tests](Lambda_Asset_Build_Tests.md) (5 shared connections)
- [CDK App & Backend Stack](CDK_App_%26_Backend_Stack.md) (4 shared connections)
- [CDK Stack Synth Tests](CDK_Stack_Synth_Tests.md) (4 shared connections)
- [Lambda Asset Packaging](Lambda_Asset_Packaging.md) (3 shared connections)
- [Worker Job Source Input](Worker_Job_Source_Input.md) (2 shared connections)
- [Reconcile Lambdas](Reconcile_Lambdas.md) (1 shared connections)
- [Contributor Docs And ADRs](Contributor_Docs_And_ADRs.md) (1 shared connections)
- [SSM Paths And Compose](SSM_Paths_And_Compose.md) (1 shared connections)
- [AWS Deploy CLI Provider](AWS_Deploy_CLI_Provider.md) (1 shared connections)

## Source Files

- `deploy_aws/DEVELOPMENT.md`
- `deploy_aws/gherkai_deploy_aws/stack.py`
- `deploy_aws/tests/synth_fixture.py`
- `deploy_aws/tests/test_stack.py`

## Audit Trail

- EXTRACTED: 72 (95%)
- INFERRED: 4 (5%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*