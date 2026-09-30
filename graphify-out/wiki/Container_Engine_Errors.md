# Container Engine Errors

> 8 nodes · cohesion 0.29

## Key Concepts

- **container.py** (12 connections) — `deploy_aws/gherkai_deploy_aws/container.py`
- **ContainerError** (10 connections) — `deploy_aws/gherkai_deploy_aws/container.py`
- **UnsupportedContainerEngine** (8 connections) — `deploy_aws/gherkai_deploy_aws/container.py`
- **.pull()** (2 connections) — `deploy_aws/tests/test_workers.py`
- **Exception** (1 connections)
- **容器引擎口子（ADR 0038「容器引擎口子」）：worker 镜像交付碰容器引擎的**唯一落点**。 **只五个动词**：`inspect`（存在 +…** (1 connections) — `deploy_aws/gherkai_deploy_aws/container.py`
- **容器引擎侧的失败（**用户可修**：引擎没装、daemon 没起、镜像不存在、push 被拒……）。 `str(exc)`…** (1 connections) — `deploy_aws/gherkai_deploy_aws/container.py`
- **要求了本期未实装的容器引擎（ADR 0038：只 docker）。** (1 connections) — `deploy_aws/gherkai_deploy_aws/container.py`

## Relationships

- [Container Engine Tests](Container_Engine_Tests.md) (5 shared connections)
- [Container Engine Wrapper](Container_Engine_Wrapper.md) (3 shared connections)
- [Worker Push Deploy Tests](Worker_Push_Deploy_Tests.md) (2 shared connections)
- [Container Engine Resolution](Container_Engine_Resolution.md) (2 shared connections)
- [Engine Probe & Inspect](Engine_Probe_%26_Inspect.md) (2 shared connections)
- [Worker Image Management](Worker_Image_Management.md) (1 shared connections)
- [Deploy Provider Tests](Deploy_Provider_Tests.md) (1 shared connections)
- [Image Platform Info](Image_Platform_Info.md) (1 shared connections)
- [Repo Digest Selection](Repo_Digest_Selection.md) (1 shared connections)
- [Deploy CLI Backend Helpers](Deploy_CLI_Backend_Helpers.md) (1 shared connections)
- [AWS Deploy Provider](AWS_Deploy_Provider.md) (1 shared connections)

## Source Files

- `deploy_aws/gherkai_deploy_aws/container.py`
- `deploy_aws/tests/test_workers.py`

## Audit Trail

- EXTRACTED: 24 (86%)
- INFERRED: 4 (14%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*