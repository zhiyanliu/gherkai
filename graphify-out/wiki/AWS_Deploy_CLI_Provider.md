# AWS Deploy CLI Provider

> 43 nodes · cohesion 0.06

## Key Concepts

- **cli.py** (25 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **gherkai_deploy_aws/names.py** (18 connections) — `deploy_aws/gherkai_deploy_aws/names.py`
- **._guard_vpc_spec()** (9 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **check_node()** (7 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **classify_vpc_state()** (7 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **._stored_vpc_hint()** (7 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **_read_stored_vpc_spec()** (6 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **_stack_exists()** (6 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **_error_code()** (5 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **vpc_spec_matches()** (5 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **_make_hint_clients()** (4 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **ssm_vpc_path()** (4 connections) — `deploy_aws/gherkai_deploy_aws/names.py`
- **_make_cfn_client()** (3 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **_make_ssm_client()** (3 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **_node_major()** (3 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **parametrize** (3 connections)
- **test_hint_clients_carry_a_bounded_timeout_budget()** (3 connections) — `deploy_aws/tests/test_provider.py`
- **test_stack_not_found_detection_needs_both_code_and_text()** (3 connections) — `deploy_aws/tests/test_provider.py`
- **test_vpc_accepts_three_dossiers()** (3 connections) — `deploy_aws/tests/test_provider.py`
- **test_vpc_rejects_anything_else()** (3 connections) — `deploy_aws/tests/test_provider.py`
- **test_vpc_spec_matches()** (3 connections) — `deploy_aws/tests/test_provider.py`
- **test_classify_four_states()** (2 connections) — `deploy_aws/tests/test_provider.py`
- **test_classify_stack_absent_is_first_deploy_even_without_param()** (2 connections) — `deploy_aws/tests/test_provider.py`
- **test_node_too_old_is_rejected()** (2 connections) — `deploy_aws/tests/test_provider.py`
- **test_unparseable_node_version_does_not_block()** (2 connections) — `deploy_aws/tests/test_provider.py`
- *... and 18 more nodes in this community*

## Relationships

- [AWS Deploy Provider Tests](AWS_Deploy_Provider_Tests.md) (19 shared connections)
- [CDK Command Wrapper](CDK_Command_Wrapper.md) (9 shared connections)
- [CDK App & Backend Stack](CDK_App_%26_Backend_Stack.md) (4 shared connections)
- [SSM Paths And Compose](SSM_Paths_And_Compose.md) (4 shared connections)
- [Container Engine Port](Container_Engine_Port.md) (2 shared connections)
- [AWS Worker Image Registry](AWS_Worker_Image_Registry.md) (2 shared connections)
- [Runtime Naming Source](Runtime_Naming_Source.md) (2 shared connections)
- [Backend CDK Stack](Backend_CDK_Stack.md) (1 shared connections)
- [Skill Deploy Token Guards](Skill_Deploy_Token_Guards.md) (1 shared connections)
- [Deploy CLI Flag Parsers](Deploy_CLI_Flag_Parsers.md) (1 shared connections)
- [CDK Context Cache](CDK_Context_Cache.md) (1 shared connections)
- [Lambda Asset Build Tests](Lambda_Asset_Build_Tests.md) (1 shared connections)

## Source Files

- `deploy_aws/gherkai_deploy_aws/cli.py`
- `deploy_aws/gherkai_deploy_aws/names.py`
- `deploy_aws/tests/test_provider.py`

## Audit Trail

- EXTRACTED: 103 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*