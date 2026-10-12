# Backend CDK Stack Constructs

> 37 nodes · cohesion 0.09

## Key Concepts

- **BackendStack** (30 connections) — `deploy_aws/gherkai_deploy_aws/stack.py`
- **.__init__()** (11 connections) — `deploy_aws/gherkai_deploy_aws/stack.py`
- **synth_fixture.py** (9 connections) — `deploy_aws/tests/synth_fixture.py`
- **._reconcile_lambdas()** (7 connections) — `deploy_aws/gherkai_deploy_aws/stack.py`
- **._worker_subnet_ids()** (5 connections) — `deploy_aws/gherkai_deploy_aws/stack.py`
- **IVpc** (5 connections)
- **._build_lambda_asset()** (4 connections) — `deploy_aws/gherkai_deploy_aws/stack.py`
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
- *... and 12 more nodes in this community*

## Relationships

- [Lambda Asset Build Tests](Lambda_Asset_Build_Tests.md) (7 shared connections)
- [CDK App & AWS Provider CLI](CDK_App_%26_AWS_Provider_CLI.md) (5 shared connections)
- [CDK Stack Synthesis Tests](CDK_Stack_Synthesis_Tests.md) (4 shared connections)
- [Worker Job Source Input](Worker_Job_Source_Input.md) (2 shared connections)
- [Exit Observer Lambda](Exit_Observer_Lambda.md) (1 shared connections)
- [Cloud Backend Docs & Diagrams](Cloud_Backend_Docs_%26_Diagrams.md) (1 shared connections)
- [Cloud Store Composition Root](Cloud_Store_Composition_Root.md) (1 shared connections)

## Source Files

- `deploy_aws/DEVELOPMENT.md`
- `deploy_aws/gherkai_deploy_aws/stack.py`
- `deploy_aws/tests/synth_fixture.py`
- `deploy_aws/tests/test_stack.py`

## Audit Trail

- EXTRACTED: 74 (95%)
- INFERRED: 4 (5%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*