# Fargate Deployment Wiring

> 13 nodes · cohesion 0.17

## Key Concepts

- **stopTimeout=120 / grace 预算校准** (5 connections) — `docs/adr/0032-fargate-execution-environment.md`
- **组合根 build_fargate_engines 接线（report ⊥ 执行）** (5 connections) — `docs/adr/0033-iac-aws-backend-and-composition-wiring.md`
- **资源清单（DDB 2 表 / S3 桶 / ECS / Lambda 链 / SSM）** (5 connections) — `docs/adr/0033-iac-aws-backend-and-composition-wiring.md`
- **IAM 最小权限（task role 动作×资源两维收窄）** (4 connections) — `docs/adr/0033-iac-aws-backend-and-composition-wiring.md`
- **preflight fail-fast（探资源存在性、错误点名 prefix）** (3 connections) — `docs/adr/0033-iac-aws-backend-and-composition-wiring.md`
- **subnet/sg 走 SSM 参数** (3 connections) — `docs/adr/0033-iac-aws-backend-and-composition-wiring.md`
- **两层命名：--prefix 批量默认 + 单资源覆盖** (3 connections) — `docs/adr/0033-iac-aws-backend-and-composition-wiring.md`
- **job-in S3 对象按 tag 的 7 天 lifecycle** (2 connections) — `docs/adr/0033-iac-aws-backend-and-composition-wiring.md`
- **产物前缀一致性探针（--report-dir vs Lambda REPORT_DIR）** (2 connections) — `docs/adr/0033-iac-aws-backend-and-composition-wiring.md`
- **ACT_TIMEOUT_S=120 不压（否决解法 B）** (1 connections) — `docs/adr/0032-fargate-execution-environment.md`
- **关 SDK 重试 + 单次墙钟封顶（不拖爆 grace）** (1 connections) — `docs/adr/0032-fargate-execution-environment.md`
- **container 名约定 {engine}-worker（CDK↔cli 硬契约）** (1 connections) — `docs/adr/0033-iac-aws-backend-and-composition-wiring.md`
- **VPC 来源三种取值（公有子网出网、零 NAT）** (1 connections) — `docs/adr/0033-iac-aws-backend-and-composition-wiring.md`

## Relationships

- [Contributor Docs And ADRs](Contributor_Docs_And_ADRs.md) (4 shared connections)
- [Execution Architecture ADRs](Execution_Architecture_ADRs.md) (3 shared connections)
- [Engine And Model ADRs](Engine_And_Model_ADRs.md) (2 shared connections)
- [Packaging And Capability Surface](Packaging_And_Capability_Surface.md) (1 shared connections)

## Source Files

- `docs/adr/0032-fargate-execution-environment.md`
- `docs/adr/0033-iac-aws-backend-and-composition-wiring.md`

## Audit Trail

- EXTRACTED: 22 (96%)
- INFERRED: 1 (4%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*