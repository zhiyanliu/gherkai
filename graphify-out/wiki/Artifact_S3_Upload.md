# Artifact S3 Upload

> 41 nodes · cohesion 0.08

## Key Concepts

- **test_artifact_upload.py** (18 connections) — `engines/novaact/tests/test_artifact_upload.py`
- **ArtifactUploader** (17 connections) — `engines/novaact/gherkai_worker_novaact/lib/artifact_upload.py`
- **_uploader_with_mock()** (11 connections) — `engines/novaact/tests/test_artifact_upload.py`
- **.flush_and_cleanup()** (6 connections) — `engines/novaact/gherkai_worker_novaact/lib/artifact_upload.py`
- **.to_report_ref()** (6 connections) — `engines/novaact/gherkai_worker_novaact/lib/artifact_upload.py`
- **Path** (6 connections)
- **_Calls** (6 connections) — `engines/novaact/tests/test_artifact_upload.py`
- **artifact_upload.py** (5 connections) — `engines/novaact/gherkai_worker_novaact/lib/artifact_upload.py`
- **._key_for()** (5 connections) — `engines/novaact/gherkai_worker_novaact/lib/artifact_upload.py`
- **_extra_args()** (5 connections) — `engines/novaact/gherkai_worker_novaact/lib/artifact_upload.py`
- **.from_env()** (4 connections) — `engines/novaact/gherkai_worker_novaact/lib/artifact_upload.py`
- **._s3()** (3 connections) — `engines/novaact/gherkai_worker_novaact/lib/artifact_upload.py`
- **.enabled()** (2 connections) — `engines/novaact/gherkai_worker_novaact/lib/artifact_upload.py`
- **.__init__()** (2 connections) — `engines/novaact/gherkai_worker_novaact/lib/artifact_upload.py`
- **test_bucket_without_logs_dir_fails_loud()** (2 connections) — `engines/novaact/tests/test_artifact_upload.py`
- **test_content_type_suffix_match_is_case_insensitive()** (2 connections) — `engines/novaact/tests/test_artifact_upload.py`
- **test_flush_failure_swallowed_but_dir_kept()** (2 connections) — `engines/novaact/tests/test_artifact_upload.py`
- **test_flush_uploads_rest_skips_uploaded_and_deletes_dir()** (2 connections) — `engines/novaact/tests/test_artifact_upload.py`
- **test_html_gets_text_html_content_type_both_paths()** (2 connections) — `engines/novaact/tests/test_artifact_upload.py`
- **test_noop_preserves_bare_path_no_symlink_resolve()** (2 connections) — `engines/novaact/tests/test_artifact_upload.py`
- **test_noop_reports_file_uri_and_no_delete()** (2 connections) — `engines/novaact/tests/test_artifact_upload.py`
- **test_report_ref_idempotent_no_reupload()** (2 connections) — `engines/novaact/tests/test_artifact_upload.py`
- **test_report_ref_upload_failure_raises_and_keeps_local()** (2 connections) — `engines/novaact/tests/test_artifact_upload.py`
- **test_report_ref_uploads_realtime_key_mirrors_tree_no_delete()** (2 connections) — `engines/novaact/tests/test_artifact_upload.py`
- **test_s3_client_has_bounded_timeouts_and_no_retry()** (2 connections) — `engines/novaact/tests/test_artifact_upload.py`
- *... and 16 more nodes in this community*

## Relationships

- [Nova Act Worker](Nova_Act_Worker.md) (2 shared connections)
- [Worker Job Source](Worker_Job_Source.md) (1 shared connections)
- [Env Config & Error Classification](Env_Config_%26_Error_Classification.md) (1 shared connections)

## Source Files

- `engines/novaact/gherkai_worker_novaact/lib/artifact_upload.py`
- `engines/novaact/tests/test_artifact_upload.py`

## Audit Trail

- EXTRACTED: 66 (96%)
- INFERRED: 3 (4%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*