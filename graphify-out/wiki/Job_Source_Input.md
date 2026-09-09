# Job Source Input

> 24 nodes · cohesion 0.09

## Key Concepts

- **JobSource** (9 connections) — `engines/novaact/gherkai_worker_novaact/lib/job_source.py`
- **_DeterministicCtx** (9 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **test_job_source.py** (9 connections) — `engines/novaact/tests/test_job_source.py`
- **job_source.py** (4 connections) — `engines/novaact/gherkai_worker_novaact/lib/job_source.py`
- **._read_s3()** (4 connections) — `engines/novaact/gherkai_worker_novaact/lib/job_source.py`
- **.read()** (3 connections) — `engines/novaact/gherkai_worker_novaact/lib/job_source.py`
- **.from_env()** (2 connections) — `engines/novaact/gherkai_worker_novaact/lib/job_source.py`
- **test_s3_uri_without_key_fails_loud()** (2 connections) — `engines/novaact/tests/test_job_source.py`
- **.__init__()** (1 connections) — `engines/novaact/gherkai_worker_novaact/lib/job_source.py`
- **job 入口（Nova worker，ADR 0024「I/O 边缘可注入接口」）：worker 主流程唯一的 job 读入口。 对称 Midscene 的…** (1 connections) — `engines/novaact/gherkai_worker_novaact/lib/job_source.py`
- **按注入的 env 读一个 scope 的 job。subprocess 态：json.loads(sys.stdin.readline())；S3…** (1 connections) — `engines/novaact/gherkai_worker_novaact/lib/job_source.py`
- **从注入的 env 造（唯一读 env 处）。JOB_S3_URI 非空 → S3 态；无/空串 → stdin 态。 `or…** (1 connections) — `engines/novaact/gherkai_worker_novaact/lib/job_source.py`
- **读并解析一个 job（返回 dict，非流）。subprocess 态：stdin 首行 JSON（同步 readline、不等 EOF）。 S3…** (1 connections) — `engines/novaact/gherkai_worker_novaact/lib/job_source.py`
- **s3://bucket/key → GetObject → json.loads。惰性建 client + 超时（对称…** (1 connections) — `engines/novaact/gherkai_worker_novaact/lib/job_source.py`
- **.__init__()** (1 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **.page()** (1 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **传给确定性 handler 的上下文：暴露 Playwright `page`（精确 DOM/URL 查，不走 AI）。 Nova 把底层…** (1 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **JobSource 单测（Nova，ADR 0024「I/O 边缘可注入接口」）：subprocess 态读 stdin 首行 JSON。 此前内联在…** (1 connections) — `engines/novaact/tests/test_job_source.py`
- **s3://bucket(无 key 段)→ fail-loud(对称 midscene;放行会晚一步在 GetObject 报模糊参数错)。** (1 connections) — `engines/novaact/tests/test_job_source.py`
- **test_empty_s3_uri_treated_as_unset()** (1 connections) — `engines/novaact/tests/test_job_source.py`
- **test_read_parses_first_line_json_from_stdin()** (1 connections) — `engines/novaact/tests/test_job_source.py`
- **test_read_takes_only_first_line_not_eof()** (1 connections) — `engines/novaact/tests/test_job_source.py`
- **test_s3_state_getobject()** (1 connections) — `engines/novaact/tests/test_job_source.py`
- **test_s3_uri_must_be_s3_scheme()** (1 connections) — `engines/novaact/tests/test_job_source.py`

## Relationships

- [Nova Act Worker Package](Nova_Act_Worker_Package.md) (3 shared connections)
- [Environment and Version Resolution](Environment_and_Version_Resolution.md) (1 shared connections)
- [Step Dispatch & Error Mapping](Step_Dispatch_%26_Error_Mapping.md) (1 shared connections)
- [Worker Event Sink](Worker_Event_Sink.md) (1 shared connections)
- [Artifact S3 Upload](Artifact_S3_Upload.md) (1 shared connections)
- [User Steps Directory Loader](User_Steps_Directory_Loader.md) (1 shared connections)

## Source Files

- `engines/novaact/gherkai_worker_novaact/lib/job_source.py`
- `engines/novaact/gherkai_worker_novaact/run_scope.py`
- `engines/novaact/tests/test_job_source.py`

## Audit Trail

- EXTRACTED: 28 (85%)
- INFERRED: 5 (15%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*