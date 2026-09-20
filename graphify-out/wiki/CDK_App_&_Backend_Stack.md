# CDK App & Backend Stack

> 8 nodes · cohesion 0.29

## Key Concepts

- **stack.py** (8 connections) — `deploy_aws/gherkai_deploy_aws/stack.py`
- **gherkai_deploy_aws/__init__.py** (7 connections) — `deploy_aws/gherkai_deploy_aws/__init__.py`
- **app.py** (6 connections) — `deploy_aws/gherkai_deploy_aws/app.py`
- **main()** (3 connections) — `deploy_aws/gherkai_deploy_aws/app.py`
- **stack_name()** (3 connections) — `deploy_aws/gherkai_deploy_aws/names.py`
- **CDK app 入口（`gherkai_deploy_aws`，ADR 0033 资源装配 / ADR 0037 决策 6 部署形态）。…** (1 connections) — `deploy_aws/gherkai_deploy_aws/app.py`
- **CloudFormation stack 名（即 `app.py` 给 `BackendStack` 的 construct id，CDK 据此定 stack…** (1 connections) — `deploy_aws/gherkai_deploy_aws/names.py`
- **BackendStack（ADR 0033）：`--backend cloud` 需要的全部 AWS 资源。 一套 stack 建齐（可按 prefix…** (1 connections) — `deploy_aws/gherkai_deploy_aws/stack.py`

## Relationships

- [Deploy CLI Doctor Checks](Deploy_CLI_Doctor_Checks.md) (4 shared connections)
- [Backend CDK Stack](Backend_CDK_Stack.md) (3 shared connections)
- [Lambda Asset Build](Lambda_Asset_Build.md) (3 shared connections)
- [AWS Worker Image Management](AWS_Worker_Image_Management.md) (1 shared connections)
- [Deploy Provider Interface](Deploy_Provider_Interface.md) (1 shared connections)
- [Worker Image Tests](Worker_Image_Tests.md) (1 shared connections)
- [CDK Stack Synth Tests](CDK_Stack_Synth_Tests.md) (1 shared connections)

## Source Files

- `deploy_aws/gherkai_deploy_aws/__init__.py`
- `deploy_aws/gherkai_deploy_aws/app.py`
- `deploy_aws/gherkai_deploy_aws/names.py`
- `deploy_aws/gherkai_deploy_aws/stack.py`

## Audit Trail

- EXTRACTED: 22 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*