# Tunnel CLI Wiring Tests

> 42 nodes · cohesion 0.09

## Key Concepts

- **test_tunnel_cli.py** (25 connections) — `cli/tests/test_tunnel_cli.py`
- **_write_feature()** (16 connections) — `cli/tests/test_tunnel_cli.py`
- **_patch_tunnel()** (13 connections) — `cli/tests/test_tunnel_cli.py`
- **test_submit_cloud_keeps_tunnel_after_daemon_fork()** (9 connections) — `cli/tests/test_tunnel_cli.py`
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
- **run --json 的输出脱敏、落盘的 run 定义保留明文（ADR 0035 决策 5）。 stdout 里 step 文本与判定消息的隧道地址都是…** (1 connections) — `cli/tests/test_tunnel_cli.py`
- *... and 17 more nodes in this community*

## Relationships

- [Plan Command CLI Tests](Plan_Command_CLI_Tests.md) (16 shared connections)
- [CLI Run Wiring Tests](CLI_Run_Wiring_Tests.md) (2 shared connections)
- [Run Definition Domain Model](Run_Definition_Domain_Model.md) (2 shared connections)
- [CLI Command Entrypoints](CLI_Command_Entrypoints.md) (1 shared connections)
- [Core Adapters Documentation](Core_Adapters_Documentation.md) (1 shared connections)
- [Tunnel Host Orchestration](Tunnel_Host_Orchestration.md) (1 shared connections)
- [Cloud Composition Helpers](Cloud_Composition_Helpers.md) (1 shared connections)

## Source Files

- `cli/tests/test_tunnel_cli.py`

## Audit Trail

- EXTRACTED: 95 (95%)
- INFERRED: 5 (5%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*