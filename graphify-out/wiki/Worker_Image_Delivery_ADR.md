# Worker Image Delivery ADR

> 19 nodes · cohesion 0.11

## Key Concepts

- **0038. worker 镜像交付：基底、variant 与推送注册** (19 connections) — `docs/adr/0038-worker-image-delivery.md`
- **`gherkai deploy` 的 worker 镜像四步（第 1 步随 cdk 事务，后三步在 cdk 之后；全部幂等）** (1 connections) — `docs/adr/0038-worker-image-delivery.md`
- **`push-worker` 流程** (1 connections) — `docs/adr/0038-worker-image-delivery.md`
- **SSM 参数与命名真源** (1 connections) — `docs/adr/0038-worker-image-delivery.md`
- **不变量** (1 connections) — `docs/adr/0038-worker-image-delivery.md`
- **与版本升级的交互** (1 connections) — `docs/adr/0038-worker-image-delivery.md`
- **命令族（全在 `gherkai-deploy-aws`，云端写操作归部署方）** (1 connections) — `docs/adr/0038-worker-image-delivery.md`
- **多版本与多环境** (1 connections) — `docs/adr/0038-worker-image-delivery.md`
- **实测项（Draft → Accepted 前必清；「绿≠对」）** (1 connections) — `docs/adr/0038-worker-image-delivery.md`
- **容器引擎口子** (1 connections) — `docs/adr/0038-worker-image-delivery.md`
- **对既有 ADR 的影响** (1 connections) — `docs/adr/0038-worker-image-delivery.md`
- **对既有文档与 code 的影响（校准清单，Draft→Accepted 门槛的一部分）** (1 connections) — `docs/adr/0038-worker-image-delivery.md`
- **权限面增量** (1 connections) — `docs/adr/0038-worker-image-delivery.md`
- **概念模型** (1 connections) — `docs/adr/0038-worker-image-delivery.md`
- **背景与问题** (1 connections) — `docs/adr/0038-worker-image-delivery.md`
- **落地次序与依赖（依赖关系，非进度追踪）** (1 connections) — `docs/adr/0038-worker-image-delivery.md`
- **被拒方案（护栏，防未来重踩）** (1 connections) — `docs/adr/0038-worker-image-delivery.md`
- **运行时与 preflight** (1 connections) — `docs/adr/0038-worker-image-delivery.md`
- **重议闸门** (1 connections) — `docs/adr/0038-worker-image-delivery.md`

## Relationships

- [ADR Index & Dev Docs](ADR_Index_%26_Dev_Docs.md) (1 shared connections)

## Source Files

- `docs/adr/0038-worker-image-delivery.md`

## Audit Trail

- EXTRACTED: 19 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*