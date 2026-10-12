# Local Tunnel Exposure Tests

> 44 nodes · cohesion 0.08

## Key Concepts

- **test_tunnel_cli.py** (25 connections) — `cli/tests/test_tunnel_cli.py`
- **_write_feature()** (16 connections) — `cli/tests/test_tunnel_cli.py`
- **_patch_tunnel()** (13 connections) — `cli/tests/test_tunnel_cli.py`
- **test_submit_cloud_keeps_tunnel_after_daemon_fork()** (9 connections) — `cli/tests/test_tunnel_cli.py`
- **.cmd()** (9 connections) — `core/gherkai_core/adapters/subprocess_engine.py`
- **_stops()** (7 connections) — `cli/tests/test_tunnel_cli.py`
- **test_submit_cloud_preflight_failure_tears_down_tunnel()** (7 connections) — `cli/tests/test_tunnel_cli.py`
- **test_submit_local_failure_after_handoff_keeps_tunnel()** (7 connections) — `cli/tests/test_tunnel_cli.py`
- **test_submit_local_writes_tunnel_file_for_per_run_cleanup()** (7 connections) — `cli/tests/test_tunnel_cli.py`
- **test_submit_cloud_target_resolution_failure_tears_down_tunnel()** (6 connections) — `cli/tests/test_tunnel_cli.py`
- **test_submit_local_fork_failure_tears_down_tunnel()** (6 connections) — `cli/tests/test_tunnel_cli.py`
- **test_submit_local_store_failure_tears_down_tunnel()** (6 connections) — `cli/tests/test_tunnel_cli.py`
- **test_run_expose_local_maps_jobs_and_injects_headers()** (5 connections) — `cli/tests/test_tunnel_cli.py`
- **test_run_json_masks_tunnel_credentials_but_run_meta_keeps_them()** (5 connections) — `cli/tests/test_tunnel_cli.py`
- **test_run_without_expose_local_zero_change()** (5 connections) — `cli/tests/test_tunnel_cli.py`
- **test_submit_rejects_nonfinite_tunnel_ttl()** (5 connections) — `cli/tests/test_tunnel_cli.py`
- **test_submit_rejects_nonpositive_tunnel_ttl_before_starting_tunnel()** (5 connections) — `cli/tests/test_tunnel_cli.py`
- **_patch_cloud_commit()** (4 connections) — `cli/tests/test_tunnel_cli.py`
- **_patch_cloud_gates()** (4 connections) — `cli/tests/test_tunnel_cli.py`
- **test_plan_expose_local_annotates_not_replaces()** (4 connections) — `cli/tests/test_tunnel_cli.py`
- **test_run_tunnel_failure_exits_2()** (4 connections) — `cli/tests/test_tunnel_cli.py`
- **test_tunnel_watch_entry_wires_argparse_to_host_and_prints()** (3 connections) — `cli/tests/test_tunnel_cli.py`
- **test_tunnel_watch_requires_explicit_ttl()** (3 connections) — `cli/tests/test_tunnel_cli.py`
- **Path** (1 connections)
- **--expose-local 的 CLI 接线测试（ADR 0035）：fake tunnel provider——不真起 ngrok、不连 AWS。…** (1 connections) — `cli/tests/test_tunnel_cli.py`
- *... and 19 more nodes in this community*

## Relationships

- [CLI Plan Command Behavior](CLI_Plan_Command_Behavior.md) (16 shared connections)
- [CLI Run Entry Tests](CLI_Run_Entry_Tests.md) (4 shared connections)
- [Cloud Launcher & Fargate Adapters](Cloud_Launcher_%26_Fargate_Adapters.md) (2 shared connections)
- [Job/Scenario Explain Model](Job-Scenario_Explain_Model.md) (2 shared connections)
- [CLI Command Dispatch Entry](CLI_Command_Dispatch_Entry.md) (1 shared connections)
- [Cloud Store Composition Root](Cloud_Store_Composition_Root.md) (1 shared connections)
- [SQLite Event Log Adapter](SQLite_Event_Log_Adapter.md) (1 shared connections)
- [Worker Capability Queries](Worker_Capability_Queries.md) (1 shared connections)

## Source Files

- `cli/tests/test_tunnel_cli.py`
- `core/gherkai_core/adapters/subprocess_engine.py`

## Audit Trail

- EXTRACTED: 97 (91%)
- INFERRED: 10 (9%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*