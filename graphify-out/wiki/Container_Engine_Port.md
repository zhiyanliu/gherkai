# Container Engine Port

> 59 nodes · cohesion 0.05

## Key Concepts

- **test_container.py** (28 connections) — `deploy_aws/tests/test_container.py`
- **ContainerEngine** (16 connections) — `deploy_aws/gherkai_deploy_aws/container.py`
- **container.py** (14 connections) — `deploy_aws/gherkai_deploy_aws/container.py`
- **resolve_container_engine()** (14 connections) — `deploy_aws/gherkai_deploy_aws/container.py`
- **_Fake** (14 connections) — `deploy_aws/tests/test_container.py`
- **digest_for_repo()** (8 connections) — `deploy_aws/gherkai_deploy_aws/container.py`
- **UnsupportedContainerEngine** (8 connections) — `deploy_aws/gherkai_deploy_aws/container.py`
- **._run()** (6 connections) — `deploy_aws/gherkai_deploy_aws/container.py`
- **test_real_tag_to_ecr_ref_still_has_no_digest()** (6 connections) — `deploy_aws/tests/test_container.py`
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
- **.tag()** (2 connections) — `deploy_aws/gherkai_deploy_aws/container.py`
- **.__init__()** (2 connections) — `deploy_aws/tests/test_container.py`
- *... and 34 more nodes in this community*

## Relationships

- [Container Image Inspection](Container_Image_Inspection.md) (13 shared connections)
- [AWS Worker Image Registry](AWS_Worker_Image_Registry.md) (3 shared connections)
- [AWS Deploy Provider Tests](AWS_Deploy_Provider_Tests.md) (3 shared connections)
- [CDK Command Wrapper](CDK_Command_Wrapper.md) (2 shared connections)
- [AWS Deploy CLI Provider](AWS_Deploy_CLI_Provider.md) (2 shared connections)
- [Container Worker Image Tests](Container_Worker_Image_Tests.md) (1 shared connections)
- [Contributor Docs And ADRs](Contributor_Docs_And_ADRs.md) (1 shared connections)

## Source Files

- `deploy_aws/gherkai_deploy_aws/container.py`
- `deploy_aws/tests/test_container.py`

## Audit Trail

- EXTRACTED: 113 (96%)
- INFERRED: 5 (4%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*