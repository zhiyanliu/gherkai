# Act Boundary Presend Upload

> 15 nodes · cohesion 0.25

## Key Concepts

- **_presend_act_siblings()** (10 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **test_antetheft.py** (10 connections) — `engines/novaact/tests/test_antetheft.py`
- **_SpyUploader** (9 connections) — `engines/novaact/tests/test_antetheft.py`
- **_make_act_pair()** (5 connections) — `engines/novaact/tests/test_antetheft.py`
- **test_presend_all_act_siblings()** (4 connections) — `engines/novaact/tests/test_antetheft.py`
- **test_presend_swallows_upload_failure()** (4 connections) — `engines/novaact/tests/test_antetheft.py`
- **test_presend_uploads_sibling_json()** (4 connections) — `engines/novaact/tests/test_antetheft.py`
- **test_presend_ignores_non_html()** (3 connections) — `engines/novaact/tests/test_antetheft.py`
- **test_presend_skips_when_no_sibling_json()** (3 connections) — `engines/novaact/tests/test_antetheft.py`
- **act 边界抢传（ADR 0029「act 边界抢传」，为 Fargate 预演）：在 step_done 安全点，把本 step 各 act 的 配套…** (1 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **act 边界抢传单测（ADR 0029「act 边界抢传」，为 Fargate 预演——subprocess+cloud 先建好并验证）。 验…** (1 connections) — `engines/novaact/tests/test_antetheft.py`
- **记录 to_report_ref 被调的路径（验抢传）；enabled 可控 no-op。** (1 connections) — `engines/novaact/tests/test_antetheft.py`
- **造一对 act 产物（.html + 配套 _trajectory.json），返回 (html 路径, json 路径)。** (1 connections) — `engines/novaact/tests/test_antetheft.py`
- **.__init__()** (1 connections) — `engines/novaact/tests/test_antetheft.py`
- **.to_report_ref()** (1 connections) — `engines/novaact/tests/test_antetheft.py`

## Relationships

- [Nova Act Worker Package](Nova_Act_Worker_Package.md) (6 shared connections)

## Source Files

- `engines/novaact/gherkai_worker_novaact/run_scope.py`
- `engines/novaact/tests/test_antetheft.py`

## Audit Trail

- EXTRACTED: 32 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*