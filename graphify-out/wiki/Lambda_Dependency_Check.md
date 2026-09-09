# Lambda Dependency Check

> 4 nodes · cohesion 0.50

## Key Concepts

- **._installed_import_source()** (5 connections) — `deploy_aws/gherkai_deploy_aws/stack.py`
- **test_missing_dependency_fails_loud_naming_it()** (3 connections) — `deploy_aws/tests/test_lambda_asset.py`
- **当前 venv 里某个 import 名的源路径（`find_spec`）——Lambda asset 的复制源，见…** (1 connections) — `deploy_aws/gherkai_deploy_aws/stack.py`
- **漏一项 → fail-fast 点名它。静默漏了的后果是 Lambda 运行期 ImportError，要到真起 run 才暴露。** (1 connections) — `deploy_aws/tests/test_lambda_asset.py`

## Relationships

- [Backend CDK Stack](Backend_CDK_Stack.md) (2 shared connections)
- [Stack Synth Fixtures](Stack_Synth_Fixtures.md) (2 shared connections)

## Source Files

- `deploy_aws/gherkai_deploy_aws/stack.py`
- `deploy_aws/tests/test_lambda_asset.py`

## Audit Trail

- EXTRACTED: 7 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*