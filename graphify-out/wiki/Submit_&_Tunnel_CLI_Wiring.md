# Submit & Tunnel CLI Wiring

> 50 nodes · cohesion 0.07

## Key Concepts

- **test_tunnel_cli.py** (24 connections) — `cli/tests/test_tunnel_cli.py`
- **_write_feature()** (15 connections) — `cli/tests/test_tunnel_cli.py`
- **_FakeProc** (15 connections) — `runtime/tests/test_tunnel.py`
- **_patch_tunnel()** (12 connections) — `cli/tests/test_tunnel_cli.py`
- **test_submit_cloud_keeps_tunnel_after_daemon_fork()** (9 connections) — `cli/tests/test_tunnel_cli.py`
- **.cmd()** (9 connections) — `core/gherkai_core/adapters/subprocess_engine.py`
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

- [CLI Plan Command Behavior](CLI_Plan_Command_Behavior.md) (18 shared connections)
- [CLI Entry Wiring Tests](CLI_Entry_Wiring_Tests.md) (7 shared connections)
- [Run Metadata & S3 Offload](Run_Metadata_%26_S3_Offload.md) (4 shared connections)
- [Tunnel Provider](Tunnel_Provider.md) (3 shared connections)
- [CLI Command Dispatch](CLI_Command_Dispatch.md) (1 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (1 shared connections)
- [CLI Test Fixtures](CLI_Test_Fixtures.md) (1 shared connections)
- [SSM Paths & Composition Root](SSM_Paths_%26_Composition_Root.md) (1 shared connections)
- [Subprocess Engine Launcher](Subprocess_Engine_Launcher.md) (1 shared connections)
- [Worker Capability Query](Worker_Capability_Query.md) (1 shared connections)
- [Ngrok Tunnel Provider](Ngrok_Tunnel_Provider.md) (1 shared connections)
- [Cloud Backend CLI Tests](Cloud_Backend_CLI_Tests.md) (1 shared connections)

## Source Files

- `cli/tests/test_main.py`
- `cli/tests/test_tunnel_cli.py`
- `core/gherkai_core/adapters/subprocess_engine.py`
- `runtime/tests/test_tunnel.py`

## Audit Trail

- EXTRACTED: 106 (84%)
- INFERRED: 20 (16%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*