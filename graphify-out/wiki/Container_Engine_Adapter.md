# Container Engine Adapter

> 73 nodes · cohesion 0.05

## Key Concepts

- **test_container.py** (29 connections) — `deploy_aws/tests/test_container.py`
- **ContainerError** (21 connections) — `deploy_aws/gherkai_deploy_aws/container.py`
- **ContainerEngine** (16 connections) — `deploy_aws/gherkai_deploy_aws/container.py`
- **ImageInfo** (14 connections) — `deploy_aws/gherkai_deploy_aws/container.py`
- **_Fake** (14 connections) — `deploy_aws/tests/test_container.py`
- **resolve_container_engine()** (13 connections) — `deploy_aws/gherkai_deploy_aws/container.py`
- **container.py** (12 connections) — `deploy_aws/gherkai_deploy_aws/container.py`
- **digest_for_repo()** (8 connections) — `deploy_aws/gherkai_deploy_aws/container.py`
- **UnsupportedContainerEngine** (8 connections) — `deploy_aws/gherkai_deploy_aws/container.py`
- **._run()** (7 connections) — `deploy_aws/gherkai_deploy_aws/container.py`
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
- *... and 48 more nodes in this community*

## Relationships

- [Worker Image Management](Worker_Image_Management.md) (10 shared connections)
- [Container Worker Push Tests](Container_Worker_Push_Tests.md) (7 shared connections)
- [Architecture Decision Records](Architecture_Decision_Records.md) (2 shared connections)
- [AWS Client Call Spy](AWS_Client_Call_Spy.md) (2 shared connections)
- [Task Definition Cleanup](Task_Definition_Cleanup.md) (2 shared connections)
- [CDK App & Deploy CLI](CDK_App_%26_Deploy_CLI.md) (2 shared connections)
- [Report Refs & Results](Report_Refs_%26_Results.md) (1 shared connections)
- [Provider Deploy Commands](Provider_Deploy_Commands.md) (1 shared connections)
- [AWS Deploy Provider](AWS_Deploy_Provider.md) (1 shared connections)

## Source Files

- `deploy_aws/gherkai_deploy_aws/container.py`
- `deploy_aws/tests/test_container.py`
- `deploy_aws/tests/test_workers.py`

## Audit Trail

- EXTRACTED: 129 (88%)
- INFERRED: 18 (12%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*