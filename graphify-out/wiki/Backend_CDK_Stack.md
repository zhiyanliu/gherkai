# Backend CDK Stack

> 37 nodes · cohesion 0.09

## Key Concepts

- **BackendStack** (26 connections) — `deploy_aws/gherkai_deploy_aws/stack.py`
- **ValueError** (21 connections)
- **.__init__()** (11 connections) — `deploy_aws/gherkai_deploy_aws/stack.py`
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
- **_read_ssm_list()** (4 connections) — `runtime/gherkai_runtime/compose.py`
- **._advancer_function()** (3 connections) — `deploy_aws/gherkai_deploy_aws/stack.py`
- **._ssm_deployment_stamp()** (3 connections) — `deploy_aws/gherkai_deploy_aws/stack.py`
- **._task_definitions()** (3 connections) — `deploy_aws/gherkai_deploy_aws/stack.py`
- **test_value_error_not_transient()** (3 connections) — `engines/novaact/tests/test_transient_network.py`
- **._storage()** (2 connections) — `deploy_aws/gherkai_deploy_aws/stack.py`
- **._worker_sg_id()** (2 connections) — `deploy_aws/gherkai_deploy_aws/stack.py`
- **test_version_context_is_required()** (2 connections) — `deploy_aws/tests/test_stack.py`
- **Role** (2 connections)
- **Cluster** (1 connections)
- **Construct** (1 connections)
- *... and 12 more nodes in this community*

## Relationships

- [Lambda Asset Build](Lambda_Asset_Build.md) (5 shared connections)
- [CDK App & Backend Stack](CDK_App_%26_Backend_Stack.md) (3 shared connections)
- [SSM Paths & Composition Root](SSM_Paths_%26_Composition_Root.md) (3 shared connections)
- [CDK Stack Synth Tests](CDK_Stack_Synth_Tests.md) (2 shared connections)
- [Transient Network Detection](Transient_Network_Detection.md) (2 shared connections)
- [Worker Locator & AWS Resolution](Worker_Locator_%26_AWS_Resolution.md) (2 shared connections)
- [Provider Deploy Subverbs](Provider_Deploy_Subverbs.md) (2 shared connections)
- [Step Dispatch & Voting](Step_Dispatch_%26_Voting.md) (2 shared connections)
- [Scope Tag Resolution](Scope_Tag_Resolution.md) (1 shared connections)
- [Cloud Backend CLI Tests](Cloud_Backend_CLI_Tests.md) (1 shared connections)
- [Run Scheduling Core](Run_Scheduling_Core.md) (1 shared connections)
- [Wire Protocol Serialization](Wire_Protocol_Serialization.md) (1 shared connections)

## Source Files

- `deploy_aws/gherkai_deploy_aws/stack.py`
- `deploy_aws/tests/test_stack.py`
- `engines/novaact/tests/test_transient_network.py`
- `runtime/gherkai_runtime/compose.py`

## Audit Trail

- EXTRACTED: 68 (77%)
- INFERRED: 20 (23%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*