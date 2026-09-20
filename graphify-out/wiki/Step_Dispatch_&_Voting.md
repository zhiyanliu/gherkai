# Step Dispatch & Voting

> 47 nodes · cohesion 0.11

## Key Concepts

- **_run_step()** (47 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **test_run_step.py** (38 connections) — `engines/novaact/tests/test_run_step.py`
- **_FakeNova** (21 connections) — `engines/novaact/tests/test_run_step.py`
- **_step()** (20 connections) — `engines/novaact/tests/test_run_step.py`
- **_done()** (16 connections) — `engines/novaact/tests/test_run_step.py`
- **_classify_act_error()** (9 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **test_async_deterministic_handler_is_error_not_silent_pass()** (8 connections) — `engines/novaact/tests/test_run_step.py`
- **test_failed_act_reports_time_worked_from_exception_metadata()** (7 connections) — `engines/novaact/tests/test_run_step.py`
- **test_act_non_network_is_engine_error()** (6 connections) — `engines/novaact/tests/test_run_step.py`
- **test_failed_act_without_metadata_has_no_cost()** (6 connections) — `engines/novaact/tests/test_run_step.py`
- **test_failed_vote_keeps_already_billed_votes_in_cost()** (6 connections) — `engines/novaact/tests/test_run_step.py`
- **_TrajNova** (6 connections) — `engines/novaact/tests/test_run_step.py`
- **test_act_transient_network_is_network_error()** (5 connections) — `engines/novaact/tests/test_run_step.py`
- **test_deterministic_and_url_steps_have_no_traj_refs()** (5 connections) — `engines/novaact/tests/test_run_step.py`
- **test_given_url_goes_to_nav_no_ai()** (5 connections) — `engines/novaact/tests/test_run_step.py`
- **test_run_scenario_shortcircuits_after_error()** (5 connections) — `engines/novaact/tests/test_run_step.py`
- **test_step_done_carries_step_level_trajectory_refs()** (5 connections) — `engines/novaact/tests/test_run_step.py`
- **test_then_votes1_single_yes_passed()** (5 connections) — `engines/novaact/tests/test_run_step.py`
- **test_then_votes3_cost_sums_all_votes()** (5 connections) — `engines/novaact/tests/test_run_step.py`
- **test_then_votes3_majority_2of3_passed()** (5 connections) — `engines/novaact/tests/test_run_step.py`
- **test_then_votes3_only_1of3_failed()** (5 connections) — `engines/novaact/tests/test_run_step.py`
- **test_then_votes_multiple_trajectories_on_one_step()** (5 connections) — `engines/novaact/tests/test_run_step.py`
- **test_when_natural_language_goes_to_act()** (5 connections) — `engines/novaact/tests/test_run_step.py`
- **_TrajResult** (5 connections) — `engines/novaact/tests/test_run_step.py`
- **test_run_scenario_failed_does_not_shortcircuit()** (4 connections) — `engines/novaact/tests/test_run_step.py`
- *... and 22 more nodes in this community*

## Relationships

- [Evidence Artifact Upload](Evidence_Artifact_Upload.md) (13 shared connections)
- [Interrupt & Termination Model](Interrupt_%26_Termination_Model.md) (11 shared connections)
- [Nova Act Worker Entry](Nova_Act_Worker_Entry.md) (10 shared connections)
- [Nova SDK Test Doubles](Nova_SDK_Test_Doubles.md) (8 shared connections)
- [Deterministic Step Registry](Deterministic_Step_Registry.md) (3 shared connections)
- [Fake Event Sink](Fake_Event_Sink.md) (2 shared connections)
- [Backend CDK Stack](Backend_CDK_Stack.md) (2 shared connections)
- [Transient Network Detection](Transient_Network_Detection.md) (1 shared connections)
- [Step Argument Assembly](Step_Argument_Assembly.md) (1 shared connections)
- [AWS Test Fixtures (moto)](AWS_Test_Fixtures_%28moto%29.md) (1 shared connections)
- [Safe-Point Trajectory Upload](Safe-Point_Trajectory_Upload.md) (1 shared connections)

## Source Files

- `engines/novaact/gherkai_worker_novaact/run_scope.py`
- `engines/novaact/tests/test_run_step.py`

## Audit Trail

- EXTRACTED: 168 (98%)
- INFERRED: 3 (2%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*