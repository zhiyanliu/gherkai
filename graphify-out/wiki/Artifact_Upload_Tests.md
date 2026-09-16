# Artifact Upload Tests

> 34 nodes · cohesion 0.10

## Key Concepts

- **test_artifact_upload.py** (33 connections) — `engines/novaact/tests/test_artifact_upload.py`
- **_uploader_with_mock()** (23 connections) — `engines/novaact/tests/test_artifact_upload.py`
- **_shots()** (7 connections) — `engines/novaact/tests/test_artifact_upload.py`
- **test_concurrent_report_ref_and_queue_share_uploaded_set()** (4 connections) — `engines/novaact/tests/test_artifact_upload.py`
- **test_drain_is_bounded_returns_false_while_item_in_flight()** (4 connections) — `engines/novaact/tests/test_artifact_upload.py`
- **test_enqueue_uploads_in_background_with_same_key_as_ref_for()** (4 connections) — `engines/novaact/tests/test_artifact_upload.py`
- **test_queue_retries_once_then_gives_up_and_keeps_going()** (4 connections) — `engines/novaact/tests/test_artifact_upload.py`
- **test_drain_timeout_abandons_queue_silently()** (3 connections) — `engines/novaact/tests/test_artifact_upload.py`
- **test_flush_skips_files_already_uploaded_by_queue()** (3 connections) — `engines/novaact/tests/test_artifact_upload.py`
- **test_flush_still_uploads_after_drain_timeout()** (3 connections) — `engines/novaact/tests/test_artifact_upload.py`
- **test_queue_retry_succeeds_on_second_attempt()** (3 connections) — `engines/novaact/tests/test_artifact_upload.py`
- **test_ref_for_does_not_need_the_file_to_exist()** (3 connections) — `engines/novaact/tests/test_artifact_upload.py`
- **test_uploads_run_in_calling_thread_not_s3transfer_pool()** (3 connections) — `engines/novaact/tests/test_artifact_upload.py`
- **test_content_type_suffix_match_is_case_insensitive()** (2 connections) — `engines/novaact/tests/test_artifact_upload.py`
- **test_evidence_screenshot_and_json_content_types()** (2 connections) — `engines/novaact/tests/test_artifact_upload.py`
- **test_flush_failure_swallowed_but_dir_kept()** (2 connections) — `engines/novaact/tests/test_artifact_upload.py`
- **test_flush_uploads_rest_skips_uploaded_and_deletes_dir()** (2 connections) — `engines/novaact/tests/test_artifact_upload.py`
- **test_html_gets_text_html_content_type_both_paths()** (2 connections) — `engines/novaact/tests/test_artifact_upload.py`
- **test_ref_for_equals_report_ref_without_uploading()** (2 connections) — `engines/novaact/tests/test_artifact_upload.py`
- **test_report_ref_idempotent_no_reupload()** (2 connections) — `engines/novaact/tests/test_artifact_upload.py`
- **test_report_ref_upload_failure_raises_and_keeps_local()** (2 connections) — `engines/novaact/tests/test_artifact_upload.py`
- **test_report_ref_uploads_realtime_key_mirrors_tree_no_delete()** (2 connections) — `engines/novaact/tests/test_artifact_upload.py`
- **ArtifactUploader 单测（ADR 0029 第一期）：整目录上传 + 删本地 + reportRef 报 s3://，无落点 env 时 no-…** (1 connections) — `engines/novaact/tests/test_artifact_upload.py`
- **key 是确定性纯路径计算 → 截图还没落盘也能先算 URI 写进 evidence.json。** (1 connections) — `engines/novaact/tests/test_artifact_upload.py`
- **队列传出去的 key **必须**等于 evidence.json 里先算好的那个 URI——不等即永久 404。** (1 connections) — `engines/novaact/tests/test_artifact_upload.py`
- *... and 9 more nodes in this community*

## Relationships

- [Artifact Uploader (Python)](Artifact_Uploader_%28Python%29.md) (6 shared connections)
- [Upload Call Recorder](Upload_Call_Recorder.md) (2 shared connections)
- [Worker Artifact Upload](Worker_Artifact_Upload.md) (1 shared connections)
- [Uploader Config Fail-Loud](Uploader_Config_Fail-Loud.md) (1 shared connections)
- [No-op Local Uploader](No-op_Local_Uploader.md) (1 shared connections)

## Source Files

- `engines/novaact/tests/test_artifact_upload.py`

## Audit Trail

- EXTRACTED: 69 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*