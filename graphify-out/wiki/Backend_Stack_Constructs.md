# Backend Stack Constructs

> 29 nodes · cohesion 0.11

## Key Concepts

- **BackendStack** (25 connections) — `deploy_aws/gherkai_deploy_aws/stack.py`
- **.__init__()** (11 connections) — `deploy_aws/gherkai_deploy_aws/stack.py`
- **._reconcile_lambdas()** (6 connections) — `deploy_aws/gherkai_deploy_aws/stack.py`
- **._worker_subnet_ids()** (5 connections) — `deploy_aws/gherkai_deploy_aws/stack.py`
- **IVpc** (5 connections)
- **._build_lambda_asset()** (4 connections) — `deploy_aws/gherkai_deploy_aws/stack.py`
- **._cluster()** (4 connections) — `deploy_aws/gherkai_deploy_aws/stack.py`
- **._grant_task_role()** (4 connections) — `deploy_aws/gherkai_deploy_aws/stack.py`
- **._network()** (4 connections) — `deploy_aws/gherkai_deploy_aws/stack.py`
- **._one_task_def()** (4 connections) — `deploy_aws/gherkai_deploy_aws/stack.py`
- **._resolve_stop_timeout()** (4 connections) — `deploy_aws/gherkai_deploy_aws/stack.py`
- **._ssm_network()** (4 connections) — `deploy_aws/gherkai_deploy_aws/stack.py`
- **._ssm_deployment_stamp()** (3 connections) — `deploy_aws/gherkai_deploy_aws/stack.py`
- **._task_definitions()** (3 connections) — `deploy_aws/gherkai_deploy_aws/stack.py`
- **._storage()** (2 connections) — `deploy_aws/gherkai_deploy_aws/stack.py`
- **._worker_sg_id()** (2 connections) — `deploy_aws/gherkai_deploy_aws/stack.py`
- **test_version_context_is_required()** (2 connections) — `deploy_aws/tests/test_stack.py`
- **Role** (2 connections)
- **Cluster** (1 connections)
- **Construct** (1 connections)
- **建/取 VPC，**并把生效的档记进 `self._vpc_spec`**（写 SSM 供下次 deploy 三态比对，ADR 0037 决策 6）。…** (1 connections) — `deploy_aws/gherkai_deploy_aws/stack.py`
- **worker task 落哪些 subnet——「优先公有子网、无则回落私有」这条契约的**唯一落点**（ADR 0033）。 三个消费者必须恒等（都喂同一个…** (1 connections) — `deploy_aws/gherkai_deploy_aws/stack.py`
- **task role 最小权限（ADR 0033 IAM 表，按动作×资源收窄）。两个引擎共享的 + 各引擎特有的。** (1 connections) — `deploy_aws/gherkai_deploy_aws/stack.py`
- **把「这次部署是什么版本、落在哪个 VPC」写成 **stack 资源**（不是命令事后 `put_parameter`）。 **为何是 stack…** (1 connections) — `deploy_aws/gherkai_deploy_aws/stack.py`
- **事件驱动推进链（ADR 0034 端到端 cloud 流程）： - **退出观察者 Lambda**：EventBridge ECS Task STOPPED…** (1 connections) — `deploy_aws/gherkai_deploy_aws/stack.py`
- *... and 4 more nodes in this community*

## Relationships

- [Stack Synth Fixtures](Stack_Synth_Fixtures.md) (4 shared connections)
- [Environment and Version Resolution](Environment_and_Version_Resolution.md) (3 shared connections)
- [CDK App & Deploy CLI](CDK_App_%26_Deploy_CLI.md) (2 shared connections)
- [Backend Stack Synth Assertions](Backend_Stack_Synth_Assertions.md) (2 shared connections)
- [Lambda Dependency Bundling](Lambda_Dependency_Bundling.md) (2 shared connections)

## Source Files

- `deploy_aws/gherkai_deploy_aws/stack.py`
- `deploy_aws/tests/test_stack.py`

## Audit Trail

- EXTRACTED: 58 (98%)
- INFERRED: 1 (2%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*