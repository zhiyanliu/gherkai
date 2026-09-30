# CDK App & Backend Stack

> 8 nodes · cohesion 0.29

## Key Concepts

- **stack.py** (13 connections) — `deploy_aws/gherkai_deploy_aws/stack.py`
- **app.py** (6 connections) — `deploy_aws/gherkai_deploy_aws/app.py`
- **gherkai_deploy_aws/__init__.py** (5 connections) — `deploy_aws/gherkai_deploy_aws/__init__.py`
- **main()** (3 connections) — `deploy_aws/gherkai_deploy_aws/app.py`
- **stack_name()** (3 connections) — `deploy_aws/gherkai_deploy_aws/names.py`
- **CDK app 入口（`gherkai_deploy_aws`，ADR 0033 资源装配 / ADR 0037 决策 6 部署形态）。…** (1 connections) — `deploy_aws/gherkai_deploy_aws/app.py`
- **CloudFormation stack 名（即 `app.py` 给 `BackendStack` 的 construct id，CDK 据此定 stack…** (1 connections) — `deploy_aws/gherkai_deploy_aws/names.py`
- **BackendStack（ADR 0033）：`--backend cloud` 需要的全部 AWS 资源。 一套 stack 建齐（可按 prefix…** (1 connections) — `deploy_aws/gherkai_deploy_aws/stack.py`

## Relationships

- [SSM Path Naming](SSM_Path_Naming.md) (4 shared connections)
- [CDK Backend Stack](CDK_Backend_Stack.md) (3 shared connections)
- [Lambda Asset Synth Tests](Lambda_Asset_Synth_Tests.md) (3 shared connections)
- [Exit Observer Lambda](Exit_Observer_Lambda.md) (2 shared connections)
- [Deploy CLI Backend Helpers](Deploy_CLI_Backend_Helpers.md) (1 shared connections)
- [Deploy Provider Tests](Deploy_Provider_Tests.md) (1 shared connections)
- [CDK Stack Synth Tests](CDK_Stack_Synth_Tests.md) (1 shared connections)
- [Core Adapters Documentation](Core_Adapters_Documentation.md) (1 shared connections)
- [Runtime Architecture Concepts](Runtime_Architecture_Concepts.md) (1 shared connections)

## Source Files

- `deploy_aws/gherkai_deploy_aws/__init__.py`
- `deploy_aws/gherkai_deploy_aws/app.py`
- `deploy_aws/gherkai_deploy_aws/names.py`
- `deploy_aws/gherkai_deploy_aws/stack.py`

## Audit Trail

- EXTRACTED: 25 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*