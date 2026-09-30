# CDK App and Deploy CLI

> 45 nodes · cohesion 0.06

## Key Concepts

- **cli.py** (26 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **gherkai_deploy_aws/names.py** (16 connections) — `deploy_aws/gherkai_deploy_aws/names.py`
- **stack.py** (10 connections) — `deploy_aws/gherkai_deploy_aws/stack.py`
- **._guard_vpc_spec()** (9 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **classify_vpc_state()** (8 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **._stored_vpc_hint()** (7 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **gherkai_deploy_aws/__init__.py** (7 connections) — `deploy_aws/gherkai_deploy_aws/__init__.py`
- **app.py** (6 connections) — `deploy_aws/gherkai_deploy_aws/app.py`
- **_read_stored_vpc_spec()** (6 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **_stack_exists()** (6 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **_error_code()** (5 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **vpc_spec_matches()** (5 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **_make_hint_clients()** (4 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **ssm_vpc_path()** (4 connections) — `deploy_aws/gherkai_deploy_aws/names.py`
- **main()** (3 connections) — `deploy_aws/gherkai_deploy_aws/app.py`
- **_make_cfn_client()** (3 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **_make_ssm_client()** (3 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **stack_name()** (3 connections) — `deploy_aws/gherkai_deploy_aws/names.py`
- **parametrize** (3 connections)
- **test_hint_clients_carry_a_bounded_timeout_budget()** (3 connections) — `deploy_aws/tests/test_provider.py`
- **test_stack_not_found_detection_needs_both_code_and_text()** (3 connections) — `deploy_aws/tests/test_provider.py`
- **test_vpc_accepts_three_dossiers()** (3 connections) — `deploy_aws/tests/test_provider.py`
- **test_vpc_rejects_anything_else()** (3 connections) — `deploy_aws/tests/test_provider.py`
- **test_vpc_spec_matches()** (3 connections) — `deploy_aws/tests/test_provider.py`
- **test_classify_four_states()** (2 connections) — `deploy_aws/tests/test_provider.py`
- *... and 20 more nodes in this community*

## Relationships

- [AWS Deploy Provider](AWS_Deploy_Provider.md) (17 shared connections)
- [CDK Command Wrapper](CDK_Command_Wrapper.md) (6 shared connections)
- [Synth and Lambda Asset Tests](Synth_and_Lambda_Asset_Tests.md) (5 shared connections)
- [SSM Path Naming](SSM_Path_Naming.md) (5 shared connections)
- [Backend CDK Stack](Backend_CDK_Stack.md) (3 shared connections)
- [Worker Image Lifecycle](Worker_Image_Lifecycle.md) (3 shared connections)
- [Worker Deploy CLI](Worker_Deploy_CLI.md) (3 shared connections)
- [Container Engine Wrapper](Container_Engine_Wrapper.md) (2 shared connections)
- [Worker Image Management Tests](Worker_Image_Management_Tests.md) (2 shared connections)
- [CDK Stack Synth Tests](CDK_Stack_Synth_Tests.md) (2 shared connections)
- [Skill Deploy Token Tests](Skill_Deploy_Token_Tests.md) (1 shared connections)
- [Deploy CLI Arguments](Deploy_CLI_Arguments.md) (1 shared connections)

## Source Files

- `deploy_aws/gherkai_deploy_aws/__init__.py`
- `deploy_aws/gherkai_deploy_aws/app.py`
- `deploy_aws/gherkai_deploy_aws/cli.py`
- `deploy_aws/gherkai_deploy_aws/names.py`
- `deploy_aws/gherkai_deploy_aws/stack.py`
- `deploy_aws/tests/test_provider.py`

## Audit Trail

- EXTRACTED: 112 (98%)
- INFERRED: 2 (2%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*