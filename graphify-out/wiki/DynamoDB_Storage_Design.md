# DynamoDB Storage Design

> 6 nodes · cohesion 0.33

## Key Concepts

- **ADR 0033: iac_aws_backend CDK + 组合根接 FargateEngine** (6 connections) — `docs/adr/0033-iac-aws-backend-and-composition-wiring.md`
- **DDB 单表 + META/STATE 两 item** (3 connections) — `docs/adr/0030-realtime-persistence-seam.md`
- **events 表 TTL（expires_at，7 天）** (2 connections) — `docs/adr/0033-iac-aws-backend-and-composition-wiring.md`
- **StepArgument S3 offload（content_ref/rows_ref）** (1 connections) — `docs/adr/0030-realtime-persistence-seam.md`
- **RunState.jobs 改 Map<scope_id>** (1 connections) — `docs/adr/0030-realtime-persistence-seam.md`
- **IAM 最小权限（动作 × 资源两维收窄）** (1 connections) — `docs/adr/0033-iac-aws-backend-and-composition-wiring.md`

## Relationships

- [Artifact Upload & Shutdown](Artifact_Upload_%26_Shutdown.md) (1 shared connections)
- [Report Store & Manifest](Report_Store_%26_Manifest.md) (1 shared connections)
- [Run Persistence & Preflight](Run_Persistence_%26_Preflight.md) (1 shared connections)
- [Detached Run Orchestration](Detached_Run_Orchestration.md) (1 shared connections)

## Source Files

- `docs/adr/0030-realtime-persistence-seam.md`
- `docs/adr/0033-iac-aws-backend-and-composition-wiring.md`

## Audit Trail

- EXTRACTED: 9 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*