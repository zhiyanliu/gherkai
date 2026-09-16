# Scenario Key & Evidence Tests

> 59 nodes · cohesion 0.08

## Key Concepts

- **test_evidence.py** (62 connections) — `engines/novaact/tests/test_evidence.py`
- **_Nova** (18 connections) — `engines/novaact/tests/test_evidence.py`
- **_synthetic()** (18 connections) — `engines/novaact/tests/test_evidence.py`
- **_Sink** (12 connections) — `engines/novaact/tests/test_evidence.py`
- **_done()** (11 connections) — `engines/novaact/tests/test_evidence.py`
- **_picks()** (11 connections) — `engines/novaact/tests/test_evidence.py`
- **_write_traj()** (10 connections) — `engines/novaact/tests/test_evidence.py`
- **test_enqueue_failure_never_changes_verdict()** (9 connections) — `engines/novaact/tests/test_evidence.py`
- **test_evidence_upload_failure_is_swallowed()** (9 connections) — `engines/novaact/tests/test_evidence.py`
- **test_screenshots_enqueued_only_after_step_done_emit()** (9 connections) — `engines/novaact/tests/test_evidence.py`
- **test_error_step_also_enqueues_only_after_emit()** (8 connections) — `engines/novaact/tests/test_evidence.py`
- **test_evidence_failure_never_changes_verdict()** (8 connections) — `engines/novaact/tests/test_evidence.py`
- **test_failed_assertion_evidence_has_all_votes_and_message()** (8 connections) — `engines/novaact/tests/test_evidence.py`
- **test_step_done_carries_evidence_ref_appended_after_trajectory()** (8 connections) — `engines/novaact/tests/test_evidence.py`
- **_TracingSink** (8 connections) — `engines/novaact/tests/test_evidence.py`
- **scenario_key()** (7 connections) — `engines/novaact/gherkai_worker_novaact/evidence.py`
- **Path** (7 connections)
- **test_no_artifacts_skips_evidence()** (7 connections) — `engines/novaact/tests/test_evidence.py`
- **test_no_enqueue_when_step_wrote_no_screenshot()** (6 connections) — `engines/novaact/tests/test_evidence.py`
- **test_raised_act_evidence_records_error_with_empty_frames()** (6 connections) — `engines/novaact/tests/test_evidence.py`
- **test_write_step_evidence_layout_and_screenshots()** (6 connections) — `engines/novaact/tests/test_evidence.py`
- **_NovaRaisesAfterFirstVote** (5 connections) — `engines/novaact/tests/test_evidence.py`
- **_Result** (5 connections) — `engines/novaact/tests/test_evidence.py`
- **test_deterministic_and_nav_steps_produce_no_evidence()** (5 connections) — `engines/novaact/tests/test_evidence.py`
- **test_evidence_skipped_when_logs_dir_unset()** (5 connections) — `engines/novaact/tests/test_evidence.py`
- *... and 34 more nodes in this community*

## Relationships

- [AWS Test Fixtures](AWS_Test_Fixtures.md) (21 shared connections)
- [Step Execution & Error Classification](Step_Execution_%26_Error_Classification.md) (13 shared connections)
- [Worker Main Fakes](Worker_Main_Fakes.md) (12 shared connections)
- [Nova Act Worker Package](Nova_Act_Worker_Package.md) (8 shared connections)
- [Transient Error Detection](Transient_Error_Detection.md) (2 shared connections)

## Source Files

- `engines/novaact/gherkai_worker_novaact/evidence.py`
- `engines/novaact/tests/test_evidence.py`

## Audit Trail

- EXTRACTED: 190 (99%)
- INFERRED: 1 (1%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*