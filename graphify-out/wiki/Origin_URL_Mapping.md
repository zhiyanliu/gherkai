# Origin URL Mapping

> 9 nodes · cohesion 0.31

## Key Concepts

- **map_origin_in_jobs()** (8 connections) — `runtime/gherkai_runtime/tunnel.py`
- **_job_with()** (8 connections) — `runtime/tests/test_tunnel.py`
- **test_map_replaces_docstring_and_datatable()** (4 connections) — `runtime/tests/test_tunnel.py`
- **test_map_leaves_non_matching_urls_untouched()** (3 connections) — `runtime/tests/test_tunnel.py`
- **test_map_replaces_step_text_prefix()** (3 connections) — `runtime/tests/test_tunnel.py`
- **StepArgument** (2 connections)
- **Job** (1 connections)
- **把 job 文本中的 origin 前缀替换成隧道 base（ADR 0035 决策 2：job-in 前、worker/AI 无感）。 替换面为…** (1 connections) — `runtime/gherkai_runtime/tunnel.py`
- **Job** (1 connections)

## Relationships

- [Tunnel Provider](Tunnel_Provider.md) (6 shared connections)
- [Run Metadata & S3 Offload](Run_Metadata_%26_S3_Offload.md) (2 shared connections)
- [Tunnel Host Orchestration](Tunnel_Host_Orchestration.md) (1 shared connections)

## Source Files

- `runtime/gherkai_runtime/tunnel.py`
- `runtime/tests/test_tunnel.py`

## Audit Trail

- EXTRACTED: 20 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*