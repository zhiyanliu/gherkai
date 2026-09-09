# Fargate Engine Wiring

> 3 nodes · cohesion 0.67

## Key Concepts

- **build_fargate_engines（组合根接线）** (2 connections) — `docs/adr/0033-iac-aws-backend-and-composition-wiring.md`
- **container 名契约 {engine}-worker** (2 connections) — `docs/adr/0033-iac-aws-backend-and-composition-wiring.md`
- **两个 worker 镜像（Nova / Midscene 各一）** (1 connections) — `docs/adr/0033-iac-aws-backend-and-composition-wiring.md`

## Relationships

- [Architecture Decision Records](Architecture_Decision_Records.md) (1 shared connections)

## Source Files

- `docs/adr/0033-iac-aws-backend-and-composition-wiring.md`

## Audit Trail

- EXTRACTED: 2 (67%)
- INFERRED: 1 (33%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*