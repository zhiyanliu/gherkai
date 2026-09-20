# Cloud Status Command

> 8 nodes · cohesion 0.25

## Key Concepts

- **_patch_skew()** (6 connections) — `cli/tests/test_backend_cloud.py`
- **test_status_cloud_json_includes_artifact_locations()** (4 connections) — `cli/tests/test_backend_cloud.py`
- **test_status_cloud_terminal_prints_s3_and_ddb_locations()** (4 connections) — `cli/tests/test_backend_cloud.py`
- **test_status_wait_cloud_kicker_missing_fails_fast()** (4 connections) — `cli/tests/test_backend_cloud.py`
- **cloud status 到终态打出与 `run --backend cloud` 相同的位置行（s3:// 报告与判定明细、ddb:// 元信息）， 落点按…** (1 connections) — `cli/tests/test_backend_cloud.py`
- **status --json 附加 artifacts（ADR 0041 决策三）：RunState 部分形状不变，多一个键给报告/判定明细/元信息位置。** (1 connections) — `cli/tests/test_backend_cloud.py`
- **--wait 接力 invoke 的 kicker 不存在（ResourceNotFound）→ 点名 prefix 并以退出码 2 结束，不再吞掉死等…** (1 connections) — `cli/tests/test_backend_cloud.py`
- **把版本 skew 闸（ADR 0037 决策 7）patch 成默认放行且静默：读戳不建 ssm client、判定直接给 `skew`。 两处都得…** (1 connections) — `cli/tests/test_backend_cloud.py`

## Relationships

- [Cloud Backend CLI Tests](Cloud_Backend_CLI_Tests.md) (5 shared connections)
- [CLI Plan Command Behavior](CLI_Plan_Command_Behavior.md) (3 shared connections)

## Source Files

- `cli/tests/test_backend_cloud.py`

## Audit Trail

- EXTRACTED: 15 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*