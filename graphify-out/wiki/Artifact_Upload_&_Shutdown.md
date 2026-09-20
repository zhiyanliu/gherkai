# Artifact Upload & Shutdown

> 13 nodes · cohesion 0.17

## Key Concepts

- **uploader 组件（from_env/to_report_ref/flush_and_cleanup）** (5 connections) — `docs/adr/0029-engine-artifacts-to-s3.md`
- **ADR 0032: Fargate 执行环境特有问题** (5 connections) — `docs/adr/0032-fargate-execution-environment.md`
- **ReportRef {kind, ref, label}** (3 connections) — `docs/adr/0027-runreport-aggregation-index.md`
- **ADR 0029: engine artifact → S3（注入驱动）** (3 connections) — `docs/adr/0029-engine-artifacts-to-s3.md`
- **grace/stopTimeout 真容器校准（stopTimeout=120）** (3 connections) — `docs/adr/0032-fargate-execution-environment.md`
- **优雅终止（schedule 只下 handle.stop 逻辑指令）** (2 connections) — `docs/adr/0026-schedule-module.md`
- **删本地（以上传成功确认为前提、整目录删）** (2 connections) — `docs/adr/0029-engine-artifacts-to-s3.md`
- **上传时机四级（实时 ref / scope 末 flush / act 边界 / scenario 边界）** (2 connections) — `docs/adr/0029-engine-artifacts-to-s3.md`
- **compose.build_fargate_engines** (2 connections) — `docs/adr/0033-iac-aws-backend-and-composition-wiring.md`
- **上传必须套超时（退出时间有界）** (1 connections) — `docs/adr/0029-engine-artifacts-to-s3.md`
- **ACT_TIMEOUT_S 不压（拒候选解法 B）** (1 connections) — `docs/adr/0032-fargate-execution-environment.md`
- **孤儿产物扫盘 reaper 否决** (1 connections) — `docs/adr/0032-fargate-execution-environment.md`
- **container 名契约 {engine}-worker** (1 connections) — `docs/adr/0033-iac-aws-backend-and-composition-wiring.md`

## Relationships

- [Schedule & Retry ADRs](Schedule_%26_Retry_ADRs.md) (2 shared connections)
- [Report Aggregation & Status](Report_Aggregation_%26_Status.md) (1 shared connections)
- [Report Store & Manifest](Report_Store_%26_Manifest.md) (1 shared connections)
- [DynamoDB Storage Design](DynamoDB_Storage_Design.md) (1 shared connections)

## Source Files

- `docs/adr/0026-schedule-module.md`
- `docs/adr/0027-runreport-aggregation-index.md`
- `docs/adr/0029-engine-artifacts-to-s3.md`
- `docs/adr/0032-fargate-execution-environment.md`
- `docs/adr/0033-iac-aws-backend-and-composition-wiring.md`

## Audit Trail

- EXTRACTED: 17 (94%)
- INFERRED: 1 (6%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*