# CDK Destroy Confirmation

> 4 nodes · cohesion 0.50

## Key Concepts

- **test_destroy_yes_passes_force_to_cdk_and_is_off_by_default()** (5 connections) — `deploy_aws/tests/test_provider.py`
- **_parse_destroy()** (4 connections) — `deploy_aws/tests/test_provider.py`
- **Namespace** (2 connections)
- **cdk destroy 在非 TTY 下拒绝无确认的销毁（实际运行撞到）；`--yes` 等同于 `--force`，不给则让 cdk 自己问。** (1 connections) — `deploy_aws/tests/test_provider.py`

## Relationships

- [Deploy Provider Tests](Deploy_Provider_Tests.md) (4 shared connections)
- [AWS Deploy Provider](AWS_Deploy_Provider.md) (2 shared connections)

## Source Files

- `deploy_aws/tests/test_provider.py`

## Audit Trail

- EXTRACTED: 9 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*