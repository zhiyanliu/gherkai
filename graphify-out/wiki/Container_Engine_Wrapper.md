# Container Engine Wrapper

> 69 nodes · cohesion 0.05

## Key Concepts

- **test_container.py** (28 connections) — `deploy_aws/tests/test_container.py`
- **ContainerEngine** (16 connections) — `deploy_aws/gherkai_deploy_aws/container.py`
- **ImageInfo** (15 connections) — `deploy_aws/gherkai_deploy_aws/container.py`
- **resolve_container_engine()** (14 connections) — `deploy_aws/gherkai_deploy_aws/container.py`
- **_Fake** (14 connections) — `deploy_aws/tests/test_container.py`
- **container.py** (12 connections) — `deploy_aws/gherkai_deploy_aws/container.py`
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
- **test_unsupported_engine_is_rejected_not_silently_downgraded()** (3 connections) — `deploy_aws/tests/test_container.py`
- **real_docker** (3 connections)
- *... and 44 more nodes in this community*

## Relationships

- [Container Engine Errors](Container_Engine_Errors.md) (9 shared connections)
- [Worker Image Management Tests](Worker_Image_Management_Tests.md) (4 shared connections)
- [Worker Image Lifecycle](Worker_Image_Lifecycle.md) (3 shared connections)
- [AWS Deploy Provider](AWS_Deploy_Provider.md) (2 shared connections)
- [CDK App and Deploy CLI](CDK_App_and_Deploy_CLI.md) (2 shared connections)
- [Task Definition Cleanup](Task_Definition_Cleanup.md) (1 shared connections)
- [Worker Deploy CLI](Worker_Deploy_CLI.md) (1 shared connections)
- [CDK Command Wrapper](CDK_Command_Wrapper.md) (1 shared connections)

## Source Files

- `deploy_aws/gherkai_deploy_aws/container.py`
- `deploy_aws/tests/test_container.py`
- `deploy_aws/tests/test_workers.py`

## Audit Trail

- EXTRACTED: 123 (93%)
- INFERRED: 9 (7%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*