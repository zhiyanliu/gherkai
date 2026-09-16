# Backend CDK Stack

> 39 nodes · cohesion 0.08

## Key Concepts

- **BackendStack** (26 connections) — `deploy_aws/gherkai_deploy_aws/stack.py`
- **ValueError** (20 connections)
- **.__init__()** (11 connections) — `deploy_aws/gherkai_deploy_aws/stack.py`
- **._reconcile_lambdas()** (7 connections) — `deploy_aws/gherkai_deploy_aws/stack.py`
- **._installed_import_source()** (5 connections) — `deploy_aws/gherkai_deploy_aws/stack.py`
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
- **.from_env()** (3 connections) — `engines/novaact/gherkai_worker_novaact/lib/event_sink.py`
- **._storage()** (2 connections) — `deploy_aws/gherkai_deploy_aws/stack.py`
- **._worker_sg_id()** (2 connections) — `deploy_aws/gherkai_deploy_aws/stack.py`
- **Role** (2 connections)
- **Cluster** (1 connections)
- **Construct** (1 connections)
- *... and 14 more nodes in this community*

## Relationships

- [CDK App & AWS Provider CLI](CDK_App_%26_AWS_Provider_CLI.md) (4 shared connections)
- [Lambda Asset Build Tests](Lambda_Asset_Build_Tests.md) (4 shared connections)
- [CDK Stack Synth Tests](CDK_Stack_Synth_Tests.md) (2 shared connections)
- [Cloud Target & Worker Resolution](Cloud_Target_%26_Worker_Resolution.md) (2 shared connections)
- [Runtime Composition Root](Runtime_Composition_Root.md) (2 shared connections)
- [Step Execution & Error Classification](Step_Execution_%26_Error_Classification.md) (2 shared connections)
- [Worker IO Edge Components](Worker_IO_Edge_Components.md) (1 shared connections)
- [Scope Parsing & Plan Errors](Scope_Parsing_%26_Plan_Errors.md) (1 shared connections)
- [Cloud Backend CLI Tests](Cloud_Backend_CLI_Tests.md) (1 shared connections)
- [Schedule Core & Fakes](Schedule_Core_%26_Fakes.md) (1 shared connections)
- [Cloud Boto3 Guards & EventLog](Cloud_Boto3_Guards_%26_EventLog.md) (1 shared connections)
- [VPC State & Deploy Flow](VPC_State_%26_Deploy_Flow.md) (1 shared connections)

## Source Files

- `deploy_aws/gherkai_deploy_aws/stack.py`
- `engines/novaact/gherkai_worker_novaact/lib/event_sink.py`
- `runtime/gherkai_runtime/compose.py`

## Audit Trail

- EXTRACTED: 70 (79%)
- INFERRED: 19 (21%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*