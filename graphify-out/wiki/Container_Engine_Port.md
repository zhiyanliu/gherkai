# Container Engine Port

> 80 nodes · cohesion 0.04

## Key Concepts

- **test_container.py** (28 connections) — `deploy_aws/tests/test_container.py`
- **ContainerError** (22 connections) — `deploy_aws/gherkai_deploy_aws/container.py`
- **ContainerEngine** (16 connections) — `deploy_aws/gherkai_deploy_aws/container.py`
- **ImageInfo** (15 connections) — `deploy_aws/gherkai_deploy_aws/container.py`
- **resolve_container_engine()** (14 connections) — `deploy_aws/gherkai_deploy_aws/container.py`
- **_Fake** (14 connections) — `deploy_aws/tests/test_container.py`
- **CountingEcs** (9 connections) — `deploy_aws/tests/test_workers.py`
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
- *... and 55 more nodes in this community*

## Relationships

- [Worker Image Tests](Worker_Image_Tests.md) (13 shared connections)
- [Deploy Provider & Container Seam](Deploy_Provider_%26_Container_Seam.md) (9 shared connections)
- [Worker Image Mapping & Cleanup](Worker_Image_Mapping_%26_Cleanup.md) (8 shared connections)
- [Task Definition Cleanup](Task_Definition_Cleanup.md) (3 shared connections)
- [CDK App & AWS Provider CLI](CDK_App_%26_AWS_Provider_CLI.md) (2 shared connections)
- [Deploy Provider Commands](Deploy_Provider_Commands.md) (1 shared connections)
- [CDK Command Execution](CDK_Command_Execution.md) (1 shared connections)

## Source Files

- `deploy_aws/gherkai_deploy_aws/container.py`
- `deploy_aws/tests/test_container.py`
- `deploy_aws/tests/test_workers.py`

## Audit Trail

- EXTRACTED: 139 (88%)
- INFERRED: 19 (12%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*