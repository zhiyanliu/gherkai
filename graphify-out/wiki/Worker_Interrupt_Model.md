# Worker Interrupt Model

> 29 nodes · cohesion 0.12

## Key Concepts

- **test_interrupt_model.py** (26 connections) — `engines/novaact/tests/test_interrupt_model.py`
- **_RecordNova** (13 connections) — `engines/novaact/tests/test_interrupt_model.py`
- **_step()** (8 connections) — `engines/novaact/tests/test_interrupt_model.py`
- **_emit_scenario_done_unless_stopped()** (7 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
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
- **test_scenario_done_emitted_when_not_stopped()** (2 connections) — `engines/novaact/tests/test_interrupt_model.py`
- **test_scenario_done_suppressed_even_with_zero_statuses()** (2 connections) — `engines/novaact/tests/test_interrupt_model.py`
- **test_scenario_done_suppressed_when_stopped()** (2 connections) — `engines/novaact/tests/test_interrupt_model.py`
- **scenario 跑完后的 scenario_done 出口 + 中止护栏（模块级、供单测直驱）。 返回 True＝中止（调用方应停止本…** (1 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **.__init__()** (1 connections) — `engines/novaact/tests/test_interrupt_model.py`
- **flag-only 中断模型单测（ADR 0024 终止契约）。 锁两条曾致命的中断反模式的修复（见 ADR 0024 被拒方案）：建连早期 SIGTERM…** (1 connections) — `engines/novaact/tests/test_interrupt_model.py`
- **handler 里绝不做 I/O：信号落在主线程正写 stderr 的瞬间，handler 再写 stderr 会撞 BufferedWriter 的非重入锁…** (1 connections) — `engines/novaact/tests/test_interrupt_model.py`
- *... and 4 more nodes in this community*

## Relationships

- [Step Dispatch & Error Mapping](Step_Dispatch_%26_Error_Mapping.md) (9 shared connections)
- [Nova Act Worker Package](Nova_Act_Worker_Package.md) (9 shared connections)
- [Fake Event Sink Fixtures](Fake_Event_Sink_Fixtures.md) (3 shared connections)

## Source Files

- `engines/novaact/gherkai_worker_novaact/run_scope.py`
- `engines/novaact/tests/test_interrupt_model.py`

## Audit Trail

- EXTRACTED: 68 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*