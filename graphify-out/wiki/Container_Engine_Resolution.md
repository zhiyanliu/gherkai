# Container Engine Resolution

> 14 nodes · cohesion 0.18

## Key Concepts

- **resolve_container_engine()** (14 connections) — `deploy_aws/gherkai_deploy_aws/container.py`
- **test_real_tag_to_ecr_ref_still_has_no_digest()** (6 connections) — `deploy_aws/tests/test_container.py`
- **test_real_local_image_has_no_repo_digests_and_is_amd64()** (5 connections) — `deploy_aws/tests/test_container.py`
- **test_real_arm64_image_is_rejected_by_the_platform_gate()** (4 connections) — `deploy_aws/tests/test_container.py`
- **test_unsupported_engine_is_rejected_not_silently_downgraded()** (3 connections) — `deploy_aws/tests/test_container.py`
- **real_docker** (3 connections)
- **test_default_is_docker()** (2 connections) — `deploy_aws/tests/test_container.py`
- **test_env_selects_engine_and_flag_wins()** (2 connections) — `deploy_aws/tests/test_container.py`
- **skipif** (2 connections)
- **选容器引擎：`--container-engine` > env `GHERKAI_CONTAINER_ENGINE` > `docker`。 未实装的名字…** (1 connections) — `deploy_aws/gherkai_deploy_aws/container.py`
- **ADR 0038 步 2 那条事实：**本地 build、从未推过的镜像 `RepoDigests` 为空** → 推送前拿不到 digest。…** (1 connections) — `deploy_aws/tests/test_container.py`
- **arm 变体真镜像 → 架构判据拒（即 push-worker 以退出码 2 结束那一支）。 用 alpine（小）代替真 worker 镜像：判据只看…** (1 connections) — `deploy_aws/tests/test_container.py`
- **`docker tag` 到 ECR ref **不会**产生 registry digest（只有 push 才会）——第二次确认「推送后才取…** (1 connections) — `deploy_aws/tests/test_container.py`
- **`--container-engine podman` **不静默回落 docker**：回落会让人以为自己验过 podman 路径（ADR 0038）。** (1 connections) — `deploy_aws/tests/test_container.py`

## Relationships

- [Container Engine Tests](Container_Engine_Tests.md) (7 shared connections)
- [Deploy CLI Backend Helpers](Deploy_CLI_Backend_Helpers.md) (2 shared connections)
- [Container Engine Errors](Container_Engine_Errors.md) (2 shared connections)
- [Provider Deploy Commands](Provider_Deploy_Commands.md) (1 shared connections)
- [Container Engine Wrapper](Container_Engine_Wrapper.md) (1 shared connections)
- [Repo Digest Selection](Repo_Digest_Selection.md) (1 shared connections)

## Source Files

- `deploy_aws/gherkai_deploy_aws/container.py`
- `deploy_aws/tests/test_container.py`

## Audit Trail

- EXTRACTED: 30 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*