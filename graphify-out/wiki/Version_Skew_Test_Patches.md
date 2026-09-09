# Version Skew Test Patches

> 4 nodes · cohesion 0.50

## Key Concepts

- **_patch_skew()** (4 connections) — `cli/tests/test_backend_cloud.py`
- **test_status_wait_cloud_kicker_missing_fails_fast()** (4 connections) — `cli/tests/test_backend_cloud.py`
- **--wait 接力 invoke 的 kicker 不存在（ResourceNotFound）→ 点名 prefix 退 2，不再吞掉死等…** (1 connections) — `cli/tests/test_backend_cloud.py`
- **把版本 skew 闸（ADR 0037 决策 7）patch 成默认放行且静默：读戳不建 ssm client、判定直接给 `skew`。 两处都得…** (1 connections) — `cli/tests/test_backend_cloud.py`

## Relationships

- [Cloud Backend CLI Tests](Cloud_Backend_CLI_Tests.md) (3 shared connections)
- [CLI Run Entry Tests](CLI_Run_Entry_Tests.md) (1 shared connections)

## Source Files

- `cli/tests/test_backend_cloud.py`

## Audit Trail

- EXTRACTED: 7 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*