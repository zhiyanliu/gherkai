# Repo Digest Selection

> 5 nodes · cohesion 0.40

## Key Concepts

- **digest_for_repo()** (7 connections) — `deploy_aws/gherkai_deploy_aws/container.py`
- **test_digest_picked_by_repo_not_first_entry()** (3 connections) — `deploy_aws/tests/test_container.py`
- **test_digest_none_when_repo_absent_or_empty()** (2 connections) — `deploy_aws/tests/test_container.py`
- **从 `RepoDigests` 里挑出**本仓库**那条的 digest（`sha256:<hex>`）；没有 → None。…** (1 connections) — `deploy_aws/gherkai_deploy_aws/container.py`
- **基础镜像同步先 pull 过 GHCR → `RepoDigests` 多条；**取第一条就会把 GHCR 的 digest 写进 task-def**…** (1 connections) — `deploy_aws/tests/test_container.py`

## Relationships

- [Container Engine Tests](Container_Engine_Tests.md) (3 shared connections)
- [Container Engine Resolution](Container_Engine_Resolution.md) (1 shared connections)
- [Container Engine Errors](Container_Engine_Errors.md) (1 shared connections)
- [Worker Image Management](Worker_Image_Management.md) (1 shared connections)

## Source Files

- `deploy_aws/gherkai_deploy_aws/container.py`
- `deploy_aws/tests/test_container.py`

## Audit Trail

- EXTRACTED: 9 (90%)
- INFERRED: 1 (10%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*