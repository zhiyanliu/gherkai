# Deploy CLI Doctor Checks

> 50 nodes · cohesion 0.05

## Key Concepts

- **cli.py** (25 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **gherkai_deploy_aws/names.py** (16 connections) — `deploy_aws/gherkai_deploy_aws/names.py`
- **._guard_vpc_spec()** (9 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **cdk_command()** (7 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **check_node()** (7 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **classify_vpc_state()** (7 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **._stored_vpc_hint()** (7 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **_read_stored_vpc_spec()** (6 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **_stack_exists()** (6 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **_error_code()** (5 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **.doctor()** (5 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **vpc_spec_matches()** (5 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **check_cdk()** (4 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **_make_hint_clients()** (4 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **ssm_vpc_path()** (4 connections) — `deploy_aws/gherkai_deploy_aws/names.py`
- **_make_cfn_client()** (3 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **_make_ssm_client()** (3 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **_make_sts_client()** (3 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **_node_major()** (3 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **_vpc_flag()** (3 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **test_hint_clients_carry_a_bounded_timeout_budget()** (3 connections) — `deploy_aws/tests/test_provider.py`
- **test_stack_not_found_detection_needs_both_code_and_text()** (3 connections) — `deploy_aws/tests/test_provider.py`
- **test_cdk_command_prefers_path_cdk_then_npx()** (2 connections) — `deploy_aws/tests/test_provider.py`
- **test_classify_four_states()** (2 connections) — `deploy_aws/tests/test_provider.py`
- **test_classify_stack_absent_is_first_deploy_even_without_param()** (2 connections) — `deploy_aws/tests/test_provider.py`
- *... and 25 more nodes in this community*

## Relationships

- [Deploy Provider Interface](Deploy_Provider_Interface.md) (16 shared connections)
- [Provider Deploy Subverbs](Provider_Deploy_Subverbs.md) (9 shared connections)
- [CDK App & Backend Stack](CDK_App_%26_Backend_Stack.md) (4 shared connections)
- [SSM Paths & Composition Root](SSM_Paths_%26_Composition_Root.md) (4 shared connections)
- [Container Engine Adapter](Container_Engine_Adapter.md) (3 shared connections)
- [Lambda Asset Build](Lambda_Asset_Build.md) (2 shared connections)
- [AWS Worker Image Management](AWS_Worker_Image_Management.md) (2 shared connections)
- [Resource Naming Source](Resource_Naming_Source.md) (2 shared connections)
- [Skill Deploy Token Checks](Skill_Deploy_Token_Checks.md) (1 shared connections)
- [CDK Context Cache](CDK_Context_Cache.md) (1 shared connections)
- [Provider CLI Flags](Provider_CLI_Flags.md) (1 shared connections)
- [CDK Stack Synth Tests](CDK_Stack_Synth_Tests.md) (1 shared connections)

## Source Files

- `deploy_aws/gherkai_deploy_aws/cli.py`
- `deploy_aws/gherkai_deploy_aws/names.py`
- `deploy_aws/tests/test_provider.py`

## Audit Trail

- EXTRACTED: 108 (99%)
- INFERRED: 1 (1%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*