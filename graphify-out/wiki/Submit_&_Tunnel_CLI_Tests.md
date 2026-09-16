# Submit & Tunnel CLI Tests

> 50 nodes · cohesion 0.07

## Key Concepts

- **test_tunnel_cli.py** (24 connections) — `cli/tests/test_tunnel_cli.py`
- **_write_feature()** (15 connections) — `cli/tests/test_tunnel_cli.py`
- **_FakeProc** (15 connections) — `runtime/tests/test_tunnel.py`
- **_patch_tunnel()** (12 connections) — `cli/tests/test_tunnel_cli.py`
- **test_submit_cloud_keeps_tunnel_after_daemon_fork()** (9 connections) — `cli/tests/test_tunnel_cli.py`
- **.cmd()** (8 connections) — `core/gherkai_core/adapters/subprocess_engine.py`
- **_stops()** (7 connections) — `cli/tests/test_tunnel_cli.py`
- **test_submit_cloud_preflight_failure_tears_down_tunnel()** (7 connections) — `cli/tests/test_tunnel_cli.py`
- **test_submit_local_failure_after_handoff_keeps_tunnel()** (7 connections) — `cli/tests/test_tunnel_cli.py`
- **test_submit_local_writes_tunnel_file_for_per_run_cleanup()** (7 connections) — `cli/tests/test_tunnel_cli.py`
- **test_submit_local_persists_steps_dir_into_definition()** (6 connections) — `cli/tests/test_main.py`
- **test_submit_local_writes_max_concurrency_into_definition()** (6 connections) — `cli/tests/test_main.py`
- **test_submit_cloud_target_resolution_failure_tears_down_tunnel()** (6 connections) — `cli/tests/test_tunnel_cli.py`
- **test_submit_local_fork_failure_tears_down_tunnel()** (6 connections) — `cli/tests/test_tunnel_cli.py`
- **test_submit_local_store_failure_tears_down_tunnel()** (6 connections) — `cli/tests/test_tunnel_cli.py`
- **test_run_expose_local_maps_jobs_and_injects_headers()** (5 connections) — `cli/tests/test_tunnel_cli.py`
- **test_run_without_expose_local_zero_change()** (5 connections) — `cli/tests/test_tunnel_cli.py`
- **test_submit_rejects_nonfinite_tunnel_ttl()** (5 connections) — `cli/tests/test_tunnel_cli.py`
- **test_submit_rejects_nonpositive_tunnel_ttl_before_starting_tunnel()** (5 connections) — `cli/tests/test_tunnel_cli.py`
- **test_submit_rejects_max_concurrency_below_one()** (4 connections) — `cli/tests/test_main.py`
- **_patch_cloud_commit()** (4 connections) — `cli/tests/test_tunnel_cli.py`
- **_patch_cloud_gates()** (4 connections) — `cli/tests/test_tunnel_cli.py`
- **test_plan_expose_local_annotates_not_replaces()** (4 connections) — `cli/tests/test_tunnel_cli.py`
- **test_run_tunnel_failure_exits_2()** (4 connections) — `cli/tests/test_tunnel_cli.py`
- **test_tunnel_watch_entry_wires_argparse_to_host_and_prints()** (3 connections) — `cli/tests/test_tunnel_cli.py`
- *... and 25 more nodes in this community*

## Relationships

- [CLI Main Flow Tests](CLI_Main_Flow_Tests.md) (18 shared connections)
- [CLI Run Command Tests](CLI_Run_Command_Tests.md) (7 shared connections)
- [Job Explain & S3 Offload](Job_Explain_%26_S3_Offload.md) (4 shared connections)
- [CLI Command Entry Points](CLI_Command_Entry_Points.md) (1 shared connections)
- [Cloud Boto3 Guards & EventLog](Cloud_Boto3_Guards_%26_EventLog.md) (1 shared connections)
- [Runtime Composition & Tunnel Host](Runtime_Composition_%26_Tunnel_Host.md) (1 shared connections)
- [S3 Report Store & Control Plane](S3_Report_Store_%26_Control_Plane.md) (1 shared connections)
- [SQLite Event Log](SQLite_Event_Log.md) (1 shared connections)
- [Tunnel Origin Mapping](Tunnel_Origin_Mapping.md) (1 shared connections)
- [Ngrok Tunnel Implementation](Ngrok_Tunnel_Implementation.md) (1 shared connections)
- [Tunnel Provider Factory](Tunnel_Provider_Factory.md) (1 shared connections)
- [Tunnel Info Credentials](Tunnel_Info_Credentials.md) (1 shared connections)

## Source Files

- `cli/tests/test_main.py`
- `cli/tests/test_tunnel_cli.py`
- `core/gherkai_core/adapters/subprocess_engine.py`
- `runtime/tests/test_tunnel.py`

## Audit Trail

- EXTRACTED: 106 (85%)
- INFERRED: 19 (15%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*