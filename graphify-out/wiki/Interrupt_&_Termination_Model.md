# Interrupt & Termination Model

> 48 nodes · cohesion 0.06

## Key Concepts

- **test_interrupt_model.py** (26 connections) — `engines/novaact/tests/test_interrupt_model.py`
- **_RecordNova** (13 connections) — `engines/novaact/tests/test_interrupt_model.py`
- **_FakeSink** (8 connections) — `engines/novaact/tests/test_interrupt_model.py`
- **_step()** (8 connections) — `engines/novaact/tests/test_interrupt_model.py`
- **_emit_scenario_done_unless_stopped()** (7 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **_backoff_interrupted()** (5 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **_on_signal()** (5 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **captured()** (4 connections) — `engines/novaact/tests/test_interrupt_model.py`
- **_FakeResult** (4 connections) — `engines/novaact/tests/test_interrupt_model.py`
- **test_act_called_with_timeout()** (4 connections) — `engines/novaact/tests/test_interrupt_model.py`
- **test_act_get_called_with_timeout()** (4 connections) — `engines/novaact/tests/test_interrupt_model.py`
- **test_run_scenario_stops_midway()** (4 connections) — `engines/novaact/tests/test_interrupt_model.py`
- **test_run_scenario_stops_on_flag_no_step_skipped()** (4 connections) — `engines/novaact/tests/test_interrupt_model.py`
- **test_vote_loop_full_votes_then_stop_still_emits()** (4 connections) — `engines/novaact/tests/test_interrupt_model.py`
- **test_vote_loop_stops_before_any_vote()** (4 connections) — `engines/novaact/tests/test_interrupt_model.py`
- **test_vote_loop_stops_midway_no_bogus_verdict()** (4 connections) — `engines/novaact/tests/test_interrupt_model.py`
- **_aggregate()** (3 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **_Meta** (3 connections) — `engines/novaact/tests/test_interrupt_model.py`
- **_reset_stop()** (3 connections) — `engines/novaact/tests/test_interrupt_model.py`
- **test_on_signal_does_no_io_even_if_stderr_is_locked()** (3 connections) — `engines/novaact/tests/test_interrupt_model.py`
- **.__init__()** (2 connections) — `engines/novaact/tests/test_interrupt_model.py`
- **.act()** (2 connections) — `engines/novaact/tests/test_interrupt_model.py`
- **.act_get()** (2 connections) — `engines/novaact/tests/test_interrupt_model.py`
- **test_backoff_interrupted_times_out_without_stop()** (2 connections) — `engines/novaact/tests/test_interrupt_model.py`
- **test_backoff_interrupted_wakes_on_stop()** (2 connections) — `engines/novaact/tests/test_interrupt_model.py`
- *... and 23 more nodes in this community*

## Relationships

- [Step Execution & Error Classification](Step_Execution_%26_Error_Classification.md) (9 shared connections)
- [Nova Act Worker Package](Nova_Act_Worker_Package.md) (9 shared connections)
- [AWS Test Fixtures](AWS_Test_Fixtures.md) (2 shared connections)

## Source Files

- `engines/novaact/gherkai_worker_novaact/run_scope.py`
- `engines/novaact/tests/test_interrupt_model.py`

## Audit Trail

- EXTRACTED: 88 (99%)
- INFERRED: 1 (1%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*