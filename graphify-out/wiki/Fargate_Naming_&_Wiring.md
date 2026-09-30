# Fargate Naming & Wiring

> 10 nodes · cohesion 0.24

## Key Concepts

- **build_fargate_engines 组合根接线** (6 connections) — `docs/adr/0033-iac-aws-backend-and-composition-wiring.md`
- **preflight fail-fast 点名 prefix** (3 connections) — `docs/adr/0033-iac-aws-backend-and-composition-wiring.md`
- **subnet/sg ID 走含 prefix 的 SSM 路径** (3 connections) — `docs/adr/0033-iac-aws-backend-and-composition-wiring.md`
- **两层命名：prefix 批量默认 + 单资源覆盖** (3 connections) — `docs/adr/0033-iac-aws-backend-and-composition-wiring.md`
- **container 名契约 {engine}-worker** (2 connections) — `docs/adr/0033-iac-aws-backend-and-composition-wiring.md`
- **gherkai_runtime.names 命名单一真源** (2 connections) — `docs/adr/0033-iac-aws-backend-and-composition-wiring.md`
- **report ⊥ 执行（--no-report 不改执行环境）** (2 connections) — `docs/adr/0033-iac-aws-backend-and-composition-wiring.md`
- **task-def 不焊 region/凭证** (2 connections) — `docs/adr/0033-iac-aws-backend-and-composition-wiring.md`
- **产物前缀一致性语义探针** (1 connections) — `docs/adr/0033-iac-aws-backend-and-composition-wiring.md`
- **VPC 三种取值 + 公有子网零 NAT** (1 connections) — `docs/adr/0033-iac-aws-backend-and-composition-wiring.md`

## Relationships

- [Package Contributor Docs](Package_Contributor_Docs.md) (3 shared connections)

## Source Files

- `docs/adr/0033-iac-aws-backend-and-composition-wiring.md`

## Audit Trail

- EXTRACTED: 14 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*