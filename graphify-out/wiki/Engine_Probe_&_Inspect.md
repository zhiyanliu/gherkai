# Engine Probe & Inspect

> 6 nodes · cohesion 0.33

## Key Concepts

- **.inspect()** (5 connections) — `deploy_aws/gherkai_deploy_aws/container.py`
- **_tail()** (5 connections) — `deploy_aws/gherkai_deploy_aws/container.py`
- **.probe()** (3 connections) — `deploy_aws/gherkai_deploy_aws/container.py`
- **引擎可用吗？可用 → None；不可用 → 给人看的一句（**不抛**，同 `cli.check_node` 的口径）。 两级：PATH…** (1 connections) — `deploy_aws/gherkai_deploy_aws/container.py`
- **本地镜像的存在 + 平台 + registry digest 列表。镜像不存在 → `ImageInfo(exists=False)`（**不抛**：…** (1 connections) — `deploy_aws/gherkai_deploy_aws/container.py`
- **报错里带的引擎输出：去空白 + 只留尾部（docker 的失败原因在最后几行，前面全是层进度）。** (1 connections) — `deploy_aws/gherkai_deploy_aws/container.py`

## Relationships

- [Container Engine Wrapper](Container_Engine_Wrapper.md) (3 shared connections)
- [Container Engine Errors](Container_Engine_Errors.md) (2 shared connections)
- [Image Platform Info](Image_Platform_Info.md) (1 shared connections)

## Source Files

- `deploy_aws/gherkai_deploy_aws/container.py`

## Audit Trail

- EXTRACTED: 11 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*