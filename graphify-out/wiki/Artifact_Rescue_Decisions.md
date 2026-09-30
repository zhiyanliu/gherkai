# Artifact Rescue Decisions

> 6 nodes · cohesion 0.33

## Key Concepts

- **task role IAM 最小权限** (4 connections) — `docs/adr/0033-iac-aws-backend-and-composition-wiring.md`
- **act/step 安全点提前上传** (3 connections) — `docs/adr/0032-fargate-execution-environment.md`
- **容器盘停即销毁导致的中断产物丢失** (2 connections) — `docs/adr/0032-fargate-execution-environment.md`
- **孤儿产物扫盘 reaper（经分析否决）** (2 connections) — `docs/adr/0032-fargate-execution-environment.md`
- **job-in 对象按 tag 的 7 天 lifecycle** (2 connections) — `docs/adr/0033-iac-aws-backend-and-composition-wiring.md`
- **job-in 独立前缀 jobs-in/** (1 connections) — `docs/adr/0033-iac-aws-backend-and-composition-wiring.md`

## Relationships

- [Package Contributor Docs](Package_Contributor_Docs.md) (4 shared connections)

## Source Files

- `docs/adr/0032-fargate-execution-environment.md`
- `docs/adr/0033-iac-aws-backend-and-composition-wiring.md`

## Audit Trail

- EXTRACTED: 9 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*