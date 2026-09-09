# Step Dispatch & Error Mapping

> 34 nodes · cohesion 0.16

## Key Concepts

- **test_run_step.py** (32 connections) — `engines/novaact/tests/test_run_step.py`
- **_run_step()** (28 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **_FakeNova** (18 connections) — `engines/novaact/tests/test_run_step.py`
- **_step()** (16 connections) — `engines/novaact/tests/test_run_step.py`
- **_done()** (12 connections) — `engines/novaact/tests/test_run_step.py`
- **_classify_act_error()** (9 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **_run_scenario()** (9 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **test_act_non_network_is_engine_error()** (6 connections) — `engines/novaact/tests/test_run_step.py`
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
- **test_run_scenario_failed_does_not_shortcircuit()** (4 connections) — `engines/novaact/tests/test_run_step.py`
- **test_run_scenario_no_shortcircuit_when_all_pass()** (4 connections) — `engines/novaact/tests/test_run_step.py`
- **test_then_votes2_tie_failed()** (4 connections) — `engines/novaact/tests/test_run_step.py`
- **test_classify_unknown_falls_back_engine_error()** (3 connections) — `engines/novaact/tests/test_run_step.py`
- **EventSink** (3 connections)
- **test_classify_guardrail()** (2 connections) — `engines/novaact/tests/test_run_step.py`
- *... and 9 more nodes in this community*

## Relationships

- [Worker Interrupt Model](Worker_Interrupt_Model.md) (9 shared connections)
- [Nova Act Worker Package](Nova_Act_Worker_Package.md) (8 shared connections)
- [Nova Act Test Doubles](Nova_Act_Test_Doubles.md) (6 shared connections)
- [Trajectory Artifact Test Doubles](Trajectory_Artifact_Test_Doubles.md) (4 shared connections)
- [Transient Error Classification](Transient_Error_Classification.md) (2 shared connections)
- [Fake Sink Test Fixtures](Fake_Sink_Test_Fixtures.md) (2 shared connections)
- [Environment and Version Resolution](Environment_and_Version_Resolution.md) (2 shared connections)
- [Deterministic Step Registry](Deterministic_Step_Registry.md) (1 shared connections)
- [Job Source Input](Job_Source_Input.md) (1 shared connections)
- [Step Argument Assembly](Step_Argument_Assembly.md) (1 shared connections)

## Source Files

- `engines/novaact/gherkai_worker_novaact/run_scope.py`
- `engines/novaact/tests/test_run_step.py`

## Audit Trail

- EXTRACTED: 124 (98%)
- INFERRED: 2 (2%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*