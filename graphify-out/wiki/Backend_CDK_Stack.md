# Backend CDK Stack

> 34 nodes · cohesion 0.10

## Key Concepts

- **BackendStack** (26 connections) — `deploy_aws/gherkai_deploy_aws/stack.py`
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
- **._advancer_function()** (3 connections) — `deploy_aws/gherkai_deploy_aws/stack.py`
- **._ssm_deployment_stamp()** (3 connections) — `deploy_aws/gherkai_deploy_aws/stack.py`
- **._task_definitions()** (3 connections) — `deploy_aws/gherkai_deploy_aws/stack.py`
- **._storage()** (2 connections) — `deploy_aws/gherkai_deploy_aws/stack.py`
- **._worker_sg_id()** (2 connections) — `deploy_aws/gherkai_deploy_aws/stack.py`
- **Role** (2 connections)
- **Cluster** (1 connections)
- **Construct** (1 connections)
- **后端版本戳（PEP 440 字符串）：**`-c version=` 必给、无隐式默认**。 单一真源是发起这次部署的命令（`gherkai deploy`…** (1 connections) — `deploy_aws/gherkai_deploy_aws/stack.py`
- **建/取 VPC，**并把生效的取值记进 `self._vpc_spec`**（写 SSM 供下次 deploy 三态比对，ADR 0037 决策 6）。…** (1 connections) — `deploy_aws/gherkai_deploy_aws/stack.py`
- **worker task 落哪些 subnet——「优先公有子网、无则回落私有」这条契约的**唯一落点**（ADR 0033）。 三个消费者必须恒等（都喂同一个…** (1 connections) — `deploy_aws/gherkai_deploy_aws/stack.py`
- *... and 9 more nodes in this community*

## Relationships

- [Synth and Lambda Asset Tests](Synth_and_Lambda_Asset_Tests.md) (5 shared connections)
- [CDK App and Deploy CLI](CDK_App_and_Deploy_CLI.md) (3 shared connections)
- [CDK Stack Synth Tests](CDK_Stack_Synth_Tests.md) (2 shared connections)
- [Release Notes Tooling](Release_Notes_Tooling.md) (2 shared connections)

## Source Files

- `deploy_aws/gherkai_deploy_aws/stack.py`

## Audit Trail

- EXTRACTED: 64 (97%)
- INFERRED: 2 (3%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*