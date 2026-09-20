# Python Artifact Uploader

> 30 nodes · cohesion 0.13

## Key Concepts

- **ArtifactUploader** (29 connections) — `engines/novaact/gherkai_worker_novaact/lib/artifact_upload.py`
- **Path** (11 connections)
- **._upload_once_with_retry()** (10 connections) — `engines/novaact/gherkai_worker_novaact/lib/artifact_upload.py`
- **.to_report_ref()** (9 connections) — `engines/novaact/gherkai_worker_novaact/lib/artifact_upload.py`
- **._key_for()** (6 connections) — `engines/novaact/gherkai_worker_novaact/lib/artifact_upload.py`
- **._upload_queued()** (6 connections) — `engines/novaact/gherkai_worker_novaact/lib/artifact_upload.py`
- **.flush_and_cleanup()** (5 connections) — `engines/novaact/gherkai_worker_novaact/lib/artifact_upload.py`
- **._is_uploaded()** (5 connections) — `engines/novaact/gherkai_worker_novaact/lib/artifact_upload.py`
- **.ref_for()** (5 connections) — `engines/novaact/gherkai_worker_novaact/lib/artifact_upload.py`
- **_extra_args()** (5 connections) — `engines/novaact/gherkai_worker_novaact/lib/artifact_upload.py`
- **.from_env()** (4 connections) — `engines/novaact/gherkai_worker_novaact/lib/artifact_upload.py`
- **._mark_uploaded()** (4 connections) — `engines/novaact/gherkai_worker_novaact/lib/artifact_upload.py`
- **._transfer_config()** (4 connections) — `engines/novaact/gherkai_worker_novaact/lib/artifact_upload.py`
- **._queue_loop()** (3 connections) — `engines/novaact/gherkai_worker_novaact/lib/artifact_upload.py`
- **._s3()** (3 connections) — `engines/novaact/gherkai_worker_novaact/lib/artifact_upload.py`
- **.__init__()** (2 connections) — `engines/novaact/gherkai_worker_novaact/lib/artifact_upload.py`
- **test_noop_preserves_bare_path_no_symlink_resolve()** (2 connections) — `engines/novaact/tests/test_artifact_upload.py`
- **test_noop_reports_file_uri_and_no_delete()** (2 connections) — `engines/novaact/tests/test_artifact_upload.py`
- **test_ref_for_noop_reports_same_file_uri_as_report_ref()** (2 connections) — `engines/novaact/tests/test_artifact_upload.py`
- **test_s3_client_has_bounded_timeouts_and_no_retry()** (2 connections) — `engines/novaact/tests/test_artifact_upload.py`
- **产物本地绝对路径 → S3 key（镜像 run 树：prefix + 相对 run_dir 的 POSIX 路径）。** (1 connections) — `engines/novaact/gherkai_worker_novaact/lib/artifact_upload.py`
- **reportRef 指向的文件 → 实时上传（不删、记 _uploaded）、报 s3://；no-op 时报 file://。 失败原样抛（worker 记…** (1 connections) — `engines/novaact/gherkai_worker_novaact/lib/artifact_upload.py`
- ****只算 ref、不上传**：返回该文件将来（scope 末 flush 后）会有的那个 ref，与 `to_report_ref` 逐字一致。 给…** (1 connections) — `engines/novaact/gherkai_worker_novaact/lib/artifact_upload.py`
- **传一个文件、失败**重试一次**；成功 True（并记进已传集合）、两次都失败 False（不抛）。 队列与 flush 共用（key 规则与…** (1 connections) — `engines/novaact/gherkai_worker_novaact/lib/artifact_upload.py`
- **boto3 传输配置：`use_threads=False` → 传输在调用线程内执行（NonThreadedExecutor）。 默认的线程池是非…** (1 connections) — `engines/novaact/gherkai_worker_novaact/lib/artifact_upload.py`
- *... and 5 more nodes in this community*

## Relationships

- [Artifact Upload Tests](Artifact_Upload_Tests.md) (6 shared connections)
- [Worker Artifact Upload](Worker_Artifact_Upload.md) (3 shared connections)
- [Nova Act Worker Entry](Nova_Act_Worker_Entry.md) (2 shared connections)
- [Background Upload Queue](Background_Upload_Queue.md) (2 shared connections)
- [Local No-Op Uploader](Local_No-Op_Uploader.md) (1 shared connections)
- [Log Upload Enablement](Log_Upload_Enablement.md) (1 shared connections)
- [Bounded Queue Drain](Bounded_Queue_Drain.md) (1 shared connections)
- [Upload Call Recorder](Upload_Call_Recorder.md) (1 shared connections)
- [Backend CDK Stack](Backend_CDK_Stack.md) (1 shared connections)
- [AWS Test Fixtures (moto)](AWS_Test_Fixtures_%28moto%29.md) (1 shared connections)

## Source Files

- `engines/novaact/gherkai_worker_novaact/lib/artifact_upload.py`
- `engines/novaact/tests/test_artifact_upload.py`

## Audit Trail

- EXTRACTED: 70 (95%)
- INFERRED: 4 (5%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*