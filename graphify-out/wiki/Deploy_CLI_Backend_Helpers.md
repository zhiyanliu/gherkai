# Deploy CLI Backend Helpers

> 50 nodes · cohesion 0.05

## Key Concepts

- **cli.py** (26 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **._guard_vpc_spec()** (9 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **classify_vpc_state()** (8 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **.bootstrap()** (8 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **cdk_command()** (7 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **check_node()** (7 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **._stored_vpc_hint()** (7 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **._toolchain_gate()** (7 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **_read_stored_vpc_spec()** (6 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **_stack_exists()** (6 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **_error_code()** (5 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **.doctor()** (5 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **vpc_spec_matches()** (5 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **check_cdk()** (4 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **_make_hint_clients()** (4 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
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

- [Deploy Provider Tests](Deploy_Provider_Tests.md) (11 shared connections)
- [Provider Deploy Commands](Provider_Deploy_Commands.md) (9 shared connections)
- [AWS Deploy Provider](AWS_Deploy_Provider.md) (7 shared connections)
- [Container Engine Resolution](Container_Engine_Resolution.md) (2 shared connections)
- [SSM Path Naming](SSM_Path_Naming.md) (2 shared connections)
- [Deploy Provider Discovery](Deploy_Provider_Discovery.md) (2 shared connections)
- [Worker Image Management](Worker_Image_Management.md) (1 shared connections)
- [Container Engine Errors](Container_Engine_Errors.md) (1 shared connections)
- [CDK App & Backend Stack](CDK_App_%26_Backend_Stack.md) (1 shared connections)
- [Lambda Asset Synth Tests](Lambda_Asset_Synth_Tests.md) (1 shared connections)
- [Skill Deploy Token Guardrail](Skill_Deploy_Token_Guardrail.md) (1 shared connections)
- [CDK Context Cache](CDK_Context_Cache.md) (1 shared connections)

## Source Files

- `deploy_aws/gherkai_deploy_aws/cli.py`
- `deploy_aws/tests/test_provider.py`

## Audit Trail

- EXTRACTED: 100 (96%)
- INFERRED: 4 (4%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*