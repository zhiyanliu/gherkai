# Lambda Asset Packaging

> 6 nodes · cohesion 0.33

## Key Concepts

- **._installed_import_source()** (5 connections) — `deploy_aws/gherkai_deploy_aws/stack.py`
- **._build_lambda_asset()** (4 connections) — `deploy_aws/gherkai_deploy_aws/stack.py`
- **test_missing_dependency_fails_loud_naming_it()** (3 connections) — `deploy_aws/tests/test_lambda_asset.py`
- **把 Lambda 代码摊到一个目录，返回其路径（`Code.from_asset` 用）。 内容是本包 `lambdas/` 的 handler…** (1 connections) — `deploy_aws/gherkai_deploy_aws/stack.py`
- **当前 venv 里某个 import 名的源路径（`find_spec`）——Lambda asset 的复制源，见…** (1 connections) — `deploy_aws/gherkai_deploy_aws/stack.py`
- **漏一项 → fail-fast 点名它。静默漏了的后果是 Lambda 运行期 ImportError，要到真起 run 才暴露。** (1 connections) — `deploy_aws/tests/test_lambda_asset.py`

## Relationships

- [Backend CDK Stack](Backend_CDK_Stack.md) (3 shared connections)
- [Lambda Asset Build Tests](Lambda_Asset_Build_Tests.md) (2 shared connections)

## Source Files

- `deploy_aws/gherkai_deploy_aws/stack.py`
- `deploy_aws/tests/test_lambda_asset.py`

## Audit Trail

- EXTRACTED: 10 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*