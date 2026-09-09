# Tunnel CLI Wiring Tests

> 23 nodes · cohesion 0.13

## Key Concepts

- **test_tunnel_cli.py** (15 connections) — `cli/tests/test_tunnel_cli.py`
- **_write_feature()** (9 connections) — `cli/tests/test_tunnel_cli.py`
- **test_submit_local_writes_tunnel_file_for_per_run_cleanup()** (7 connections) — `cli/tests/test_tunnel_cli.py`
- **_patch_tunnel()** (6 connections) — `cli/tests/test_tunnel_cli.py`
- **test_run_expose_local_maps_jobs_and_injects_headers()** (5 connections) — `cli/tests/test_tunnel_cli.py`
- **test_run_without_expose_local_zero_change()** (5 connections) — `cli/tests/test_tunnel_cli.py`
- **test_submit_rejects_nonfinite_tunnel_ttl()** (5 connections) — `cli/tests/test_tunnel_cli.py`
- **test_submit_rejects_nonpositive_tunnel_ttl_before_starting_tunnel()** (5 connections) — `cli/tests/test_tunnel_cli.py`
- **test_plan_expose_local_annotates_not_replaces()** (4 connections) — `cli/tests/test_tunnel_cli.py`
- **test_run_tunnel_failure_exits_2()** (4 connections) — `cli/tests/test_tunnel_cli.py`
- **test_tunnel_watch_entry_wires_argparse_to_host_and_prints()** (3 connections) — `cli/tests/test_tunnel_cli.py`
- **test_tunnel_watch_requires_explicit_ttl()** (3 connections) — `cli/tests/test_tunnel_cli.py`
- **Path** (1 connections)
- **--expose-local 的 CLI 接线测试（ADR 0035）：fake tunnel provider——不真起 ngrok、不连 AWS。…** (1 connections) — `cli/tests/test_tunnel_cli.py`
- **_tunnel_watch 入口：argparse → tunnel_host.watch_run_and_stop_tunnel + 打印拆除原因。…** (1 connections) — `cli/tests/test_tunnel_cli.py`
- **--ttl 无默认值（必给）：曾恒 1h 且无任何生产写入者、与 run 预算脱钩（ADR 0035 决策 3），不留幻影默认。** (1 connections) — `cli/tests/test_tunnel_cli.py`
- **plan：显示替换前原始地址 + 标注将映射（零副作用不起隧道，ADR 0035 决策 2）。** (1 connections) — `cli/tests/test_tunnel_cli.py`
- **--tunnel-ttl <=0 → 退 2 且**没起隧道**（早拒才真零副作用，对齐 --grace 的入口校验惯例）。** (1 connections) — `cli/tests/test_tunnel_cli.py`
- **--tunnel-ttl nan/inf → 退 2（float() 会收下它们；nan 使守护的 monotonic()<deadline 首轮 即…** (1 connections) — `cli/tests/test_tunnel_cli.py`
- **run --expose-local：job 文本中 origin 前缀 → 凭据内嵌隧道 URL；skip 头进 RunMeta（ADR 0035 决策…** (1 connections) — `cli/tests/test_tunnel_cli.py`
- **不给 --expose-local：不碰 tunnel 模块、meta 无 headers（默认路径零变化，ADR 0035 边界）。** (1 connections) — `cli/tests/test_tunnel_cli.py`
- **隧道起不来（如 authtoken 缺失）→ 退 2「没开跑就被拒」，不产生引擎费用。** (1 connections) — `cli/tests/test_tunnel_cli.py`
- **local submit：tunnel.json 落 run 目录（pid 交棒给 per-run/接力收尾者，ADR 0035 决策 3）。** (1 connections) — `cli/tests/test_tunnel_cli.py`

## Relationships

- [CLI Run Entry Tests](CLI_Run_Entry_Tests.md) (10 shared connections)
- [Engine Ports & Adapters](Engine_Ports_%26_Adapters.md) (2 shared connections)
- [CLI Main Entry](CLI_Main_Entry.md) (1 shared connections)
- [Resource Naming Source](Resource_Naming_Source.md) (1 shared connections)

## Source Files

- `cli/tests/test_tunnel_cli.py`

## Audit Trail

- EXTRACTED: 46 (96%)
- INFERRED: 2 (4%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*