# CDK App & Deploy CLI

> 45 nodes · cohesion 0.06

## Key Concepts

- **cli.py** (25 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **gherkai_deploy_aws/names.py** (16 connections) — `deploy_aws/gherkai_deploy_aws/names.py`
- **._guard_vpc_spec()** (9 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **app.py** (8 connections) — `deploy_aws/gherkai_deploy_aws/app.py`
- **check_node()** (8 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **classify_vpc_state()** (7 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **gherkai_deploy_aws/__init__.py** (7 connections) — `deploy_aws/gherkai_deploy_aws/__init__.py`
- **_error_code()** (5 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **_read_stored_vpc_spec()** (5 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **_stack_exists()** (5 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **vpc_spec_matches()** (5 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **ssm_vpc_path()** (4 connections) — `deploy_aws/gherkai_deploy_aws/names.py`
- **main()** (3 connections) — `deploy_aws/gherkai_deploy_aws/app.py`
- **_make_cfn_client()** (3 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **_make_ssm_client()** (3 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **_node_major()** (3 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **ssm_security_groups_path()** (3 connections) — `deploy_aws/gherkai_deploy_aws/names.py`
- **ssm_subnets_path()** (3 connections) — `deploy_aws/gherkai_deploy_aws/names.py`
- **ssm_version_path()** (3 connections) — `deploy_aws/gherkai_deploy_aws/names.py`
- **stack_name()** (3 connections) — `deploy_aws/gherkai_deploy_aws/names.py`
- **test_stack_not_found_detection_needs_both_code_and_text()** (3 connections) — `deploy_aws/tests/test_provider.py`
- **test_classify_four_states()** (2 connections) — `deploy_aws/tests/test_provider.py`
- **test_classify_stack_absent_is_first_deploy_even_without_param()** (2 connections) — `deploy_aws/tests/test_provider.py`
- **test_node_too_old_is_rejected()** (2 connections) — `deploy_aws/tests/test_provider.py`
- **test_unparseable_node_version_does_not_block()** (2 connections) — `deploy_aws/tests/test_provider.py`
- *... and 20 more nodes in this community*

## Relationships

- [AWS Deploy Provider CLI](AWS_Deploy_Provider_CLI.md) (13 shared connections)
- [CDK Command Orchestration](CDK_Command_Orchestration.md) (7 shared connections)
- [Stack Synth Fixtures](Stack_Synth_Fixtures.md) (6 shared connections)
- [Composition Root Wiring](Composition_Root_Wiring.md) (4 shared connections)
- [Worker Image Push Workflow](Worker_Image_Push_Workflow.md) (3 shared connections)
- [Backend Stack Constructs](Backend_Stack_Constructs.md) (2 shared connections)
- [ADR Index & Dev Docs](ADR_Index_%26_Dev_Docs.md) (2 shared connections)
- [Container Engine Adapter](Container_Engine_Adapter.md) (2 shared connections)
- [Container Push Tests](Container_Push_Tests.md) (2 shared connections)
- [Resource Naming Source](Resource_Naming_Source.md) (2 shared connections)
- [Provider Flag Wiring](Provider_Flag_Wiring.md) (1 shared connections)
- [CDK Context Cache](CDK_Context_Cache.md) (1 shared connections)

## Source Files

- `deploy_aws/gherkai_deploy_aws/__init__.py`
- `deploy_aws/gherkai_deploy_aws/app.py`
- `deploy_aws/gherkai_deploy_aws/cli.py`
- `deploy_aws/gherkai_deploy_aws/names.py`
- `deploy_aws/tests/test_provider.py`

## Audit Trail

- EXTRACTED: 103 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*