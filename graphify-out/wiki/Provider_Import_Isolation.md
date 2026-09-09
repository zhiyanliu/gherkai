# Provider Import Isolation

> 2 nodes · cohesion 1.00

## Key Concepts

- **test_provider_module_does_not_import_aws_cdk()** (2 connections) — `deploy_aws/tests/test_provider.py`
- **CLI 经 entry point import 本模块拿 `Provider`；`aws_cdk` 是 jsii 绑定、**import 即起 node…** (1 connections) — `deploy_aws/tests/test_provider.py`

## Relationships

- [AWS Deploy Provider CLI](AWS_Deploy_Provider_CLI.md) (1 shared connections)

## Source Files

- `deploy_aws/tests/test_provider.py`

## Audit Trail

- EXTRACTED: 2 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*