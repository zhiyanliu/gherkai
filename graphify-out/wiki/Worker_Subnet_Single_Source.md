# Worker Subnet Single Source

> 4 nodes · cohesion 0.50

## Key Concepts

- **test_worker_subnets_single_source_across_ssm_and_lambda_env()** (4 connections) — `deploy_aws/tests/test_stack.py`
- **_joined_refs()** (3 connections) — `deploy_aws/tests/test_stack.py`
- **从模板值（Fn::Join）取出被拼接的资源 Ref 序列。SSM StringList 与 Lambda env 的 Join 形态不同 （分隔符一个在…** (1 connections) — `deploy_aws/tests/test_stack.py`
- **subnet 选取（公有优先、无则回落私有）只有一处落点 `_worker_subnet_ids`：写给 cli 读的 SSM 与…** (1 connections) — `deploy_aws/tests/test_stack.py`

## Relationships

- [CDK Stack Synth Tests](CDK_Stack_Synth_Tests.md) (3 shared connections)

## Source Files

- `deploy_aws/tests/test_stack.py`

## Audit Trail

- EXTRACTED: 6 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*