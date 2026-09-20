# Safe-Point Trajectory Upload

> 19 nodes · cohesion 0.18

## Key Concepts

- **_presend_act_siblings()** (10 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **test_safe_point_upload.py** (10 connections) — `engines/novaact/tests/test_safe_point_upload.py`
- **_SpyUploader** (9 connections) — `engines/novaact/tests/test_safe_point_upload.py`
- **_attach_traj_refs()** (5 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **_make_act_pair()** (5 connections) — `engines/novaact/tests/test_safe_point_upload.py`
- **_traj_refs()** (4 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **test_presend_all_act_siblings()** (4 connections) — `engines/novaact/tests/test_safe_point_upload.py`
- **test_presend_swallows_upload_failure()** (4 connections) — `engines/novaact/tests/test_safe_point_upload.py`
- **test_presend_uploads_sibling_json()** (4 connections) — `engines/novaact/tests/test_safe_point_upload.py`
- **test_presend_ignores_non_html()** (3 connections) — `engines/novaact/tests/test_safe_point_upload.py`
- **test_presend_skips_when_no_sibling_json()** (3 connections) — `engines/novaact/tests/test_safe_point_upload.py`
- **本 step 收集的 trajectory 路径 → step 级 reportRefs（kind=trajectory，ADR 0027 下沉）。 一个…** (1 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **把本 step 的 trajectory 挂上 step_done 事件：安全点提前上传配套 json（ADR 0029）+ reportRefs（ADR…** (1 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **act 边界的安全点提前上传（ADR 0029 上传时机第三级，为 Fargate 预演）：在 step_done 安全点，把本 step 各 act 的…** (1 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **act 边界安全点提前上传单测（ADR 0029 上传时机第三级，为 Fargate 预演——subprocess+cloud 先建好并验证）。 验…** (1 connections) — `engines/novaact/tests/test_safe_point_upload.py`
- **记录 to_report_ref 被调的路径（验提前上传）；enabled 可控 no-op。** (1 connections) — `engines/novaact/tests/test_safe_point_upload.py`
- **造一对 act 产物（.html + 配套 _trajectory.json），返回 (html 路径, json 路径)。** (1 connections) — `engines/novaact/tests/test_safe_point_upload.py`
- **.__init__()** (1 connections) — `engines/novaact/tests/test_safe_point_upload.py`
- **.to_report_ref()** (1 connections) — `engines/novaact/tests/test_safe_point_upload.py`

## Relationships

- [Nova Act Worker Entry](Nova_Act_Worker_Entry.md) (6 shared connections)
- [Evidence Artifact Upload](Evidence_Artifact_Upload.md) (2 shared connections)
- [Step Dispatch & Voting](Step_Dispatch_%26_Voting.md) (1 shared connections)

## Source Files

- `engines/novaact/gherkai_worker_novaact/run_scope.py`
- `engines/novaact/tests/test_safe_point_upload.py`

## Audit Trail

- EXTRACTED: 39 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*