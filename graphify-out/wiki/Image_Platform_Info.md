# Image Platform Info

> 7 nodes · cohesion 0.29

## Key Concepts

- **ImageInfo** (9 connections) — `deploy_aws/gherkai_deploy_aws/container.py`
- **.matches_target_platform()** (2 connections) — `deploy_aws/gherkai_deploy_aws/container.py`
- **.platform()** (2 connections) — `deploy_aws/gherkai_deploy_aws/container.py`
- **test_target_platform_judgement()** (2 connections) — `deploy_aws/tests/test_container.py`
- **`inspect` 的结果——**只有三件事**：在不在、什么平台、有哪些 registry digest。 `repo_digests` 是…** (1 connections) — `deploy_aws/gherkai_deploy_aws/container.py`
- **`linux/amd64` 形态的人读串（未知段落写 `?`，用于报错文案）。** (1 connections) — `deploy_aws/gherkai_deploy_aws/container.py`
- **是否 linux/amd64（ADR 0038 固定架构）。** (1 connections) — `deploy_aws/gherkai_deploy_aws/container.py`

## Relationships

- [Container Engine Tests](Container_Engine_Tests.md) (4 shared connections)
- [Engine Probe & Inspect](Engine_Probe_%26_Inspect.md) (1 shared connections)
- [Container Engine Errors](Container_Engine_Errors.md) (1 shared connections)

## Source Files

- `deploy_aws/gherkai_deploy_aws/container.py`
- `deploy_aws/tests/test_container.py`

## Audit Trail

- EXTRACTED: 11 (92%)
- INFERRED: 1 (8%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*