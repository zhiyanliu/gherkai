# Container Engine Adapter

> 77 nodes · cohesion 0.04

## Key Concepts

- **test_container.py** (28 connections) — `deploy_aws/tests/test_container.py`
- **ContainerError** (22 connections) — `deploy_aws/gherkai_deploy_aws/container.py`
- **ContainerEngine** (16 connections) — `deploy_aws/gherkai_deploy_aws/container.py`
- **ImageInfo** (15 connections) — `deploy_aws/gherkai_deploy_aws/container.py`
- **resolve_container_engine()** (14 connections) — `deploy_aws/gherkai_deploy_aws/container.py`
- **_Fake** (14 connections) — `deploy_aws/tests/test_container.py`
- **container.py** (12 connections) — `deploy_aws/gherkai_deploy_aws/container.py`
- **Spy** (9 connections) — `deploy_aws/tests/test_workers.py`
- **digest_for_repo()** (8 connections) — `deploy_aws/gherkai_deploy_aws/container.py`
- **UnsupportedContainerEngine** (8 connections) — `deploy_aws/gherkai_deploy_aws/container.py`
- **._run()** (6 connections) — `deploy_aws/gherkai_deploy_aws/container.py`
- **test_real_tag_to_ecr_ref_still_has_no_digest()** (6 connections) — `deploy_aws/tests/test_container.py`
- **.inspect()** (5 connections) — `deploy_aws/gherkai_deploy_aws/container.py`
- **._stream()** (5 connections) — `deploy_aws/gherkai_deploy_aws/container.py`
- **_tail()** (5 connections) — `deploy_aws/gherkai_deploy_aws/container.py`
- **test_real_local_image_has_no_repo_digests_and_is_amd64()** (5 connections) — `deploy_aws/tests/test_container.py`
- **test_inspect_missing_image_is_not_an_error()** (4 connections) — `deploy_aws/tests/test_container.py`
- **test_real_arm64_image_is_rejected_by_the_platform_gate()** (4 connections) — `deploy_aws/tests/test_container.py`
- **.login()** (3 connections) — `deploy_aws/gherkai_deploy_aws/container.py`
- **.probe()** (3 connections) — `deploy_aws/gherkai_deploy_aws/container.py`
- **.pull()** (3 connections) — `deploy_aws/gherkai_deploy_aws/container.py`
- **.push()** (3 connections) — `deploy_aws/gherkai_deploy_aws/container.py`
- **test_digest_picked_by_repo_not_first_entry()** (3 connections) — `deploy_aws/tests/test_container.py`
- **test_inspect_parses_os_arch_and_repo_digests()** (3 connections) — `deploy_aws/tests/test_container.py`
- **test_login_password_goes_through_stdin_never_argv()** (3 connections) — `deploy_aws/tests/test_container.py`
- *... and 52 more nodes in this community*

## Relationships

- [Worker Image Tests](Worker_Image_Tests.md) (11 shared connections)
- [AWS Worker Image Management](AWS_Worker_Image_Management.md) (9 shared connections)
- [Task Definition Revisions](Task_Definition_Revisions.md) (3 shared connections)
- [Deploy CLI Doctor Checks](Deploy_CLI_Doctor_Checks.md) (3 shared connections)
- [Deploy Provider Interface](Deploy_Provider_Interface.md) (2 shared connections)
- [Counting ECS Spy](Counting_ECS_Spy.md) (2 shared connections)
- [Provider Deploy Subverbs](Provider_Deploy_Subverbs.md) (1 shared connections)

## Source Files

- `deploy_aws/gherkai_deploy_aws/container.py`
- `deploy_aws/tests/test_container.py`
- `deploy_aws/tests/test_workers.py`

## Audit Trail

- EXTRACTED: 136 (88%)
- INFERRED: 19 (12%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*