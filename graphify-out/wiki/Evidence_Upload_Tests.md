# Evidence Upload Tests

> 58 nodes · cohesion 0.08

## Key Concepts

- **test_evidence.py** (64 connections) — `engines/novaact/tests/test_evidence.py`
- **_synthetic()** (19 connections) — `engines/novaact/tests/test_evidence.py`
- **_Nova** (18 connections) — `engines/novaact/tests/test_evidence.py`
- **_get_uploader()** (12 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **_Sink** (12 connections) — `engines/novaact/tests/test_evidence.py`
- **_done()** (11 connections) — `engines/novaact/tests/test_evidence.py`
- **_picks()** (11 connections) — `engines/novaact/tests/test_evidence.py`
- **_write_traj()** (10 connections) — `engines/novaact/tests/test_evidence.py`
- **test_enqueue_failure_never_changes_verdict()** (9 connections) — `engines/novaact/tests/test_evidence.py`
- **test_evidence_upload_failure_is_swallowed()** (9 connections) — `engines/novaact/tests/test_evidence.py`
- **test_screenshots_enqueued_only_after_step_done_emit()** (9 connections) — `engines/novaact/tests/test_evidence.py`
- **_error_text()** (8 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **Path** (8 connections)
- **test_error_step_also_enqueues_only_after_emit()** (8 connections) — `engines/novaact/tests/test_evidence.py`
- **test_evidence_failure_never_changes_verdict()** (8 connections) — `engines/novaact/tests/test_evidence.py`
- **test_failed_assertion_evidence_has_all_votes_and_message()** (8 connections) — `engines/novaact/tests/test_evidence.py`
- **test_step_done_carries_evidence_ref_appended_after_trajectory()** (8 connections) — `engines/novaact/tests/test_evidence.py`
- **_TracingSink** (8 connections) — `engines/novaact/tests/test_evidence.py`
- **test_no_artifacts_skips_evidence()** (7 connections) — `engines/novaact/tests/test_evidence.py`
- **test_no_enqueue_when_step_wrote_no_screenshot()** (6 connections) — `engines/novaact/tests/test_evidence.py`
- **test_raised_act_evidence_records_error_with_empty_frames()** (6 connections) — `engines/novaact/tests/test_evidence.py`
- **_NovaRaisesAfterFirstVote** (5 connections) — `engines/novaact/tests/test_evidence.py`
- **_Result** (5 connections) — `engines/novaact/tests/test_evidence.py`
- **test_deterministic_and_nav_steps_produce_no_evidence()** (5 connections) — `engines/novaact/tests/test_evidence.py`
- **test_evidence_skipped_when_logs_dir_unset()** (5 connections) — `engines/novaact/tests/test_evidence.py`
- *... and 33 more nodes in this community*

## Relationships

- [Step Evidence Records](Step_Evidence_Records.md) (23 shared connections)
- [Step Execution Dispatch](Step_Execution_Dispatch.md) (14 shared connections)
- [Nova Main Fakes](Nova_Main_Fakes.md) (12 shared connections)
- [Nova Act Worker](Nova_Act_Worker.md) (8 shared connections)
- [Test Fixtures and Conftest](Test_Fixtures_and_Conftest.md) (3 shared connections)
- [Safe Point Upload](Safe_Point_Upload.md) (2 shared connections)
- [Event Sink and Redaction](Event_Sink_and_Redaction.md) (1 shared connections)
- [Transient Error Detection](Transient_Error_Detection.md) (1 shared connections)

## Source Files

- `engines/novaact/gherkai_worker_novaact/run_scope.py`
- `engines/novaact/tests/test_evidence.py`

## Audit Trail

- EXTRACTED: 198 (99%)
- INFERRED: 1 (1%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*