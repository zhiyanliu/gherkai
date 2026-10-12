# Flag-only Interrupt Model

> 37 nodes · cohesion 0.09

## Key Concepts

- **test_interrupt_model.py** (26 connections) — `engines/novaact/tests/test_interrupt_model.py`
- **_RecordNova** (13 connections) — `engines/novaact/tests/test_interrupt_model.py`
- **_step()** (8 connections) — `engines/novaact/tests/test_interrupt_model.py`
- **_emit_scenario_done_unless_stopped()** (7 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **_backoff_interrupted()** (5 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **_on_signal()** (5 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
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
- **test_on_signal_does_no_io_even_if_stderr_is_locked()** (3 connections) — `engines/novaact/tests/test_interrupt_model.py`
- **.__init__()** (2 connections) — `engines/novaact/tests/test_interrupt_model.py`
- **.act()** (2 connections) — `engines/novaact/tests/test_interrupt_model.py`
- **.act_get()** (2 connections) — `engines/novaact/tests/test_interrupt_model.py`
- **test_backoff_interrupted_times_out_without_stop()** (2 connections) — `engines/novaact/tests/test_interrupt_model.py`
- **test_backoff_interrupted_wakes_on_stop()** (2 connections) — `engines/novaact/tests/test_interrupt_model.py`
- **test_scenario_done_emitted_when_not_stopped()** (2 connections) — `engines/novaact/tests/test_interrupt_model.py`
- **test_scenario_done_suppressed_even_with_zero_statuses()** (2 connections) — `engines/novaact/tests/test_interrupt_model.py`
- **test_scenario_done_suppressed_when_stopped()** (2 connections) — `engines/novaact/tests/test_interrupt_model.py`
- *... and 12 more nodes in this community*

## Relationships

- [Step Execution Dispatch](Step_Execution_Dispatch.md) (9 shared connections)
- [Nova Act Worker Package](Nova_Act_Worker_Package.md) (9 shared connections)
- [Fake Event Sink](Fake_Event_Sink.md) (2 shared connections)
- [Stop Flag Test Reset](Stop_Flag_Test_Reset.md) (1 shared connections)

## Source Files

- `engines/novaact/gherkai_worker_novaact/run_scope.py`
- `engines/novaact/tests/test_interrupt_model.py`

## Audit Trail

- EXTRACTED: 77 (99%)
- INFERRED: 1 (1%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*