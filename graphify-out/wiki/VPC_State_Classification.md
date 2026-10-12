# VPC State Classification

> 10 nodes · cohesion 0.20

## Key Concepts

- **classify_vpc_state()** (7 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **vpc_spec_matches()** (5 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **parametrize** (3 connections)
- **test_vpc_accepts_three_dossiers()** (3 connections) — `deploy_aws/tests/test_provider.py`
- **test_vpc_rejects_anything_else()** (3 connections) — `deploy_aws/tests/test_provider.py`
- **test_vpc_spec_matches()** (3 connections) — `deploy_aws/tests/test_provider.py`
- **test_classify_four_states()** (2 connections) — `deploy_aws/tests/test_provider.py`
- **test_classify_stack_absent_is_first_deploy_even_without_param()** (2 connections) — `deploy_aws/tests/test_provider.py`
- **SSM 里记的生效取值 `stored` 是否与本次 `--vpc requested` 一致。 三种取值形态见…** (1 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **三态判定（ADR 0037 决策 6）。返回上面四个 `VPC_*` 之一。 判序里 **stack…** (1 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`

## Relationships

- [Deploy Provider & Container Seam](Deploy_Provider_%26_Container_Seam.md) (9 shared connections)
- [CDK App & AWS Provider CLI](CDK_App_%26_AWS_Provider_CLI.md) (3 shared connections)

## Source Files

- `deploy_aws/gherkai_deploy_aws/cli.py`
- `deploy_aws/tests/test_provider.py`

## Audit Trail

- EXTRACTED: 21 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*