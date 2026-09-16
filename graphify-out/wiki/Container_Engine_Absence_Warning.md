# Container Engine Absence Warning

> 5 nodes · cohesion 0.40

## Key Concepts

- **test_deploy_warns_about_missing_container_engine_only_for_pure_release_versions()** (6 connections) — `deploy_aws/tests/test_provider.py`
- **_AbsentEngine** (5 connections) — `deploy_aws/tests/test_provider.py`
- **.probe()** (1 connections) — `deploy_aws/tests/test_provider.py`
- **容器引擎替身：`probe()` 说「docker 没装」。** (1 connections) — `deploy_aws/tests/test_provider.py`
- **容器引擎缺失的前置警告只对**纯发行版**成立：dev/post/本地段版本的 worker 镜像步骤本就走不到「同步基底」 （ADR 0038…** (1 connections) — `deploy_aws/tests/test_provider.py`

## Relationships

- [Deploy Provider Tests](Deploy_Provider_Tests.md) (4 shared connections)
- [AWS Deploy Provider](AWS_Deploy_Provider.md) (2 shared connections)

## Source Files

- `deploy_aws/tests/test_provider.py`

## Audit Trail

- EXTRACTED: 9 (90%)
- INFERRED: 1 (10%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*