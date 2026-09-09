# CDK SSM Parameter Guardrails

> 13 nodes · cohesion 0.15

## Key Concepts

- **_ssm_params()** (10 connections) — `deploy_aws/tests/test_stack.py`
- **test_ssm_parameter_set_is_exactly_six()** (4 connections) — `deploy_aws/tests/test_stack.py`
- **test_ssm_vpc_spec_new_carries_created_vpc_id()** (4 connections) — `deploy_aws/tests/test_stack.py`
- **test_ssm_worker_template_arn_per_engine_refs_task_def()** (4 connections) — `deploy_aws/tests/test_stack.py`
- **test_prefix_switches_whole_set()** (3 connections) — `deploy_aws/tests/test_stack.py`
- **test_ssm_version_parameter_from_context()** (3 connections) — `deploy_aws/tests/test_stack.py`
- **test_ssm_vpc_spec_default_dossier()** (3 connections) — `deploy_aws/tests/test_stack.py`
- **test_ssm_vpc_spec_reuse_existing_records_the_id()** (3 connections) — `deploy_aws/tests/test_stack.py`
- **Template** (1 connections)
- **SSM 参数**全集**钉死（枚举型护栏）：网络 2（subnets/security-groups，cli resolve_network 读） + 部署戳…** (1 connections) — `deploy_aws/tests/test_stack.py`
- **模板里全部 SSM 参数：Name → Properties。Name 恒是字面量（路径由 prefix 纯推导、无 token）。** (1 connections) — `deploy_aws/tests/test_stack.py`
- **建新档记 `new:<所建 vpc-id>`——**带出 id 才可回溯核对**（ADR 0037 决策 6）。 id 是部署期才有值的 CDK…** (1 connections) — `deploy_aws/tests/test_stack.py`
- **每引擎一个 `worker-template/<engine>` 参数，值 = task-def 的 `Ref`（**带 revision** 的 ARN）。…** (1 connections) — `deploy_aws/tests/test_stack.py`

## Relationships

- [Backend Stack Synth Assertions](Backend_Stack_Synth_Assertions.md) (15 shared connections)

## Source Files

- `deploy_aws/tests/test_stack.py`

## Audit Trail

- EXTRACTED: 27 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*