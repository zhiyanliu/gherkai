# Nova Worker Process Entry

> 36 nodes · cohesion 0.07

## Key Concepts

- **main()** (18 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **_RecUploader** (12 connections) — `engines/novaact/tests/test_evidence.py`
- **_FakeNovaAct** (8 connections) — `engines/novaact/tests/test_evidence.py`
- **test_exception_path_drains_and_still_raises()** (6 connections) — `engines/novaact/tests/test_evidence.py`
- **test_stop_signal_path_drains_after_session_release()** (6 connections) — `engines/novaact/tests/test_evidence.py`
- **_FakeCdp** (5 connections) — `engines/novaact/tests/test_evidence.py`
- **_install_provider()** (5 connections) — `engines/novaact/tests/test_evidence.py`
- **main_fakes()** (5 connections) — `engines/novaact/tests/test_evidence.py`
- **test_scope_end_drains_before_flush()** (5 connections) — `engines/novaact/tests/test_evidence.py`
- **_capabilities()** (4 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **test_drain_logs_one_line_when_not_fully_drained()** (4 connections) — `engines/novaact/tests/test_evidence.py`
- **test_drain_timeout_before_flush_promises_flush_not_broken_links()** (4 connections) — `engines/novaact/tests/test_evidence.py`
- **test_network_exhausted_path_drains()** (4 connections) — `engines/novaact/tests/test_evidence.py`
- **gherkai_worker_novaact/__main__.py** (3 connections) — `engines/novaact/gherkai_worker_novaact/__main__.py`
- **.__init__()** (2 connections) — `engines/novaact/tests/test_evidence.py`
- **.__init__()** (2 connections) — `engines/novaact/tests/test_evidence.py`
- **test_sigterm_and_sigint_both_installed_as_flag_only()** (2 connections) — `engines/novaact/tests/test_interrupt_model.py`
- **worker 进程入口（`python -m gherkai_worker_novaact`，ADR 0037 决策 3 定位链第二级）。 argv…** (1 connections) — `engines/novaact/gherkai_worker_novaact/__main__.py`
- **本 worker 的能力声明（`--capabilities` 的 stdout，ADR 0036「5.」）。 `min_grace_s` 是 grace…** (1 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **.__enter__()** (1 connections) — `engines/novaact/tests/test_evidence.py`
- **.__exit__()** (1 connections) — `engines/novaact/tests/test_evidence.py`
- **.__init__()** (1 connections) — `engines/novaact/tests/test_evidence.py`
- **.__enter__()** (1 connections) — `engines/novaact/tests/test_evidence.py`
- **.__exit__()** (1 connections) — `engines/novaact/tests/test_evidence.py`
- **.get_session_id()** (1 connections) — `engines/novaact/tests/test_evidence.py`
- *... and 11 more nodes in this community*

## Relationships

- [Scenario Evidence Keys](Scenario_Evidence_Keys.md) (12 shared connections)
- [Nova Act Worker Runtime](Nova_Act_Worker_Runtime.md) (9 shared connections)
- [Interrupt and Signal Handling](Interrupt_and_Signal_Handling.md) (3 shared connections)
- [Registry Self-Description](Registry_Self-Description.md) (1 shared connections)
- [User Steps Directory Loading](User_Steps_Directory_Loading.md) (1 shared connections)
- [Deterministic Registry (Python)](Deterministic_Registry_%28Python%29.md) (1 shared connections)
- [Nova Worker Library Setup](Nova_Worker_Library_Setup.md) (1 shared connections)
- [Transient Error Detection](Transient_Error_Detection.md) (1 shared connections)
- [CLI Test Fixtures](CLI_Test_Fixtures.md) (1 shared connections)

## Source Files

- `engines/novaact/gherkai_worker_novaact/__main__.py`
- `engines/novaact/gherkai_worker_novaact/run_scope.py`
- `engines/novaact/tests/test_evidence.py`
- `engines/novaact/tests/test_interrupt_model.py`

## Audit Trail

- EXTRACTED: 71 (99%)
- INFERRED: 1 (1%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*