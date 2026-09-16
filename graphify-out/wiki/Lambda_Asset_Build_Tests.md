# Lambda Asset Build Tests

> 25 nodes · cohesion 0.12

## Key Concepts

- **test_lambda_asset.py** (18 connections) — `deploy_aws/tests/test_lambda_asset.py`
- **make_stack()** (8 connections) — `deploy_aws/tests/synth_fixture.py`
- **asset_dir()** (7 connections) — `deploy_aws/tests/test_lambda_asset.py`
- **Path** (7 connections)
- **test_falls_back_to_tempdir_without_env()** (6 connections) — `deploy_aws/tests/test_lambda_asset.py`
- **_fake_installed_sources()** (5 connections) — `deploy_aws/tests/test_lambda_asset.py`
- **_patch_sources()** (4 connections) — `deploy_aws/tests/test_lambda_asset.py`
- **test_asset_imports_with_only_stdlib_beside_it()** (4 connections) — `deploy_aws/tests/test_lambda_asset.py`
- **test_source_lookup_handles_both_packages_and_single_file_modules()** (4 connections) — `deploy_aws/tests/test_lambda_asset.py`
- **test_asset_not_written_into_the_installed_package()** (3 connections) — `deploy_aws/tests/test_lambda_asset.py`
- **test_missing_dependency_fails_loud_naming_it()** (3 connections) — `deploy_aws/tests/test_lambda_asset.py`
- **test_declared_dependencies_land_in_the_right_shape()** (2 connections) — `deploy_aws/tests/test_lambda_asset.py`
- **test_handler_sources_land_at_asset_root()** (2 connections) — `deploy_aws/tests/test_lambda_asset.py`
- ****带上命令真会给的 CDK 特性开关**（`cli.CDK_FEATURE_FLAGS`）——特性开关会改变合成出的资源形态，…** (1 connections) — `deploy_aws/tests/synth_fixture.py`
- **Lambda asset 构建测试（ADR 0037 决策 6「Lambda asset 来源」）：纯本地、不联网、不碰 AWS。…** (1 connections) — `deploy_aws/tests/test_lambda_asset.py`
- **没有命令给的工作目录（裸跑 cdk synth）→ 自建 mkdtemp，仍不写仓库。** (1 connections) — `deploy_aws/tests/test_lambda_asset.py`
- **漏一项 → fail-fast 点名它。静默漏了的后果是 Lambda 运行期 ImportError，要到真起 run 才暴露。** (1 connections) — `deploy_aws/tests/test_lambda_asset.py`
- **`find_spec` 对两种形态都要给出可复制的路径；editable 安装（contributor 的 workspace）也命中源码目录——…** (1 connections) — `deploy_aws/tests/test_lambda_asset.py`
- **把**真** asset 摊出来，在**剥掉 site-packages** 的子进程里 import 一遍。…** (1 connections) — `deploy_aws/tests/test_lambda_asset.py`
- **造假「已安装依赖」：除 `SINGLE_FILE_MODULE` 外都是包目录，各带一个应被排除的 `__pycache__` 与 `tests`。** (1 connections) — `deploy_aws/tests/test_lambda_asset.py`
- **synth 一次 stack，返回摊好的 asset 目录（复制源换成假的，免得断言随真包演进而漂）。** (1 connections) — `deploy_aws/tests/test_lambda_asset.py`
- **两个 handler 摊在 asset **根**、是平级顶层模块——Lambda 的 `handler="reconciler.handler"` 与…** (1 connections) — `deploy_aws/tests/test_lambda_asset.py`
- **内容清单（ADR 0037 决策 6）+ 两种形态各自摆对：包 → 同名目录；单文件模块 → 同名 `.py`。** (1 connections) — `deploy_aws/tests/test_lambda_asset.py`
- **落点在命令给的临时工作目录，**不在包目录内**——旧实现落 `iac_aws_backend/.lambda_build/`， 那要求源码树可写；wheel…** (1 connections) — `deploy_aws/tests/test_lambda_asset.py`
- **test_pycache_and_tests_excluded()** (1 connections) — `deploy_aws/tests/test_lambda_asset.py`

## Relationships

- [CDK App & AWS Provider CLI](CDK_App_%26_AWS_Provider_CLI.md) (5 shared connections)
- [Backend CDK Stack](Backend_CDK_Stack.md) (4 shared connections)
- [CDK Stack Synth Tests](CDK_Stack_Synth_Tests.md) (1 shared connections)
- [AWS Test Fixtures](AWS_Test_Fixtures.md) (1 shared connections)

## Source Files

- `deploy_aws/tests/synth_fixture.py`
- `deploy_aws/tests/test_lambda_asset.py`

## Audit Trail

- EXTRACTED: 48 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*