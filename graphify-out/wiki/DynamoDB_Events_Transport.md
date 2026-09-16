# DynamoDB Events Transport

> 42 nodes · cohesion 0.06

## Key Concepts

- **ADR 0033 IaC 资源清单与命名契约** (31 connections) — `docs/adr/0033-iac-aws-backend-and-composition-wiring.md`
- **ADR 0030 实时写接缝** (20 connections) — `docs/adr/0030-realtime-persistence-seam.md`
- **ADR 0031 job 生命周期状态与严重度** (16 connections) — `docs/adr/0031-job-lifecycle-states-and-severity.md`
- **ADR 0040 使用方角色模型与术语** (9 connections) — `docs/adr/0040-consumer-role-model-and-terminology.md`
- **DynamoDB 作 events-out 传输（共享表 + Query 轮询）** (6 connections) — `docs/adr/0024-worker-core-protocol.md`
- **EventSink（事件出口可注入接口）** (5 connections) — `docs/adr/0024-worker-core-protocol.md`
- **决定三：commit-point 写序（数据面先、控制面后）** (3 connections) — `docs/adr/0030-realtime-persistence-seam.md`
- **events 表开 TTL（expires_at 7 天）+ 三条护栏** (3 connections) — `docs/adr/0033-iac-aws-backend-and-composition-wiring.md`
- **preflight fail-fast：探资源存在性、错误点名 prefix** (3 connections) — `docs/adr/0033-iac-aws-backend-and-composition-wiring.md`
- **events 表键设计 PK=run_id#scope_id / SK=seq** (2 connections) — `docs/adr/0024-worker-core-protocol.md`
- **被拒方案：DynamoDB Streams（同步 run 语境）** (2 connections) — `docs/adr/0024-worker-core-protocol.md`
- **seq worker 进程内自增（单写者不变量）** (2 connections) — `docs/adr/0024-worker-core-protocol.md`
- **task_exited 事件走独立键空间** (2 connections) — `docs/adr/0024-worker-core-protocol.md`
- **红线：worker 只直写 events 表、绝不碰 RunState** (2 connections) — `docs/adr/0024-worker-core-protocol.md`
- **id 派生（scenarioId/scopeId 稳定可追溯）** (2 connections) — `docs/adr/0025-plan-module-feature-to-jobs.md`
- **决定六：DDB 单表、META/STATE 两 item** (2 connections) — `docs/adr/0030-realtime-persistence-seam.md`
- **决定七：Store port 增 preflight() 探活** (2 connections) — `docs/adr/0030-realtime-persistence-seam.md`
- **决定五：RunState.jobs 改 Map<scope_id>** (2 connections) — `docs/adr/0030-realtime-persistence-seam.md`
- **决定一·补：pending / running 生命周期前置态** (2 connections) — `docs/adr/0031-job-lifecycle-states-and-severity.md`
- **产物前缀一致性探针（detached submit 专属）** (2 connections) — `docs/adr/0033-iac-aws-backend-and-composition-wiring.md`
- **subnet/sg ID 走含 prefix 的 SSM 参数** (2 connections) — `docs/adr/0033-iac-aws-backend-and-composition-wiring.md`
- **两层命名：--prefix 批量默认 + 单资源覆盖** (2 connections) — `docs/adr/0033-iac-aws-backend-and-composition-wiring.md`
- **四顶帽子（feature 作者 / 测试开发 / 部署方 / contributor）与「帽子不是人」** (2 connections) — `docs/adr/0040-consumer-role-model-and-terminology.md`
- **跑法权限梯（执行是正交轴）** (2 connections) — `docs/adr/0040-consumer-role-model-and-terminology.md`
- **events item TTL 自动过期（expires_at 7 天）** (1 connections) — `docs/adr/0024-worker-core-protocol.md`
- *... and 17 more nodes in this community*

## Relationships

- [Architecture ADR Decisions](Architecture_ADR_Decisions.md) (17 shared connections)
- [Execution Model Concepts](Execution_Model_Concepts.md) (6 shared connections)
- [CLI Usability & Evidence Docs](CLI_Usability_%26_Evidence_Docs.md) (6 shared connections)
- [Termination & Engine Ports](Termination_%26_Engine_Ports.md) (5 shared connections)
- [Project Conventions Docs](Project_Conventions_Docs.md) (5 shared connections)
- [CLI Docs & Skill References](CLI_Docs_%26_Skill_References.md) (3 shared connections)
- [Architecture Decision Records](Architecture_Decision_Records.md) (3 shared connections)
- [Act Timeout & Signal Handling](Act_Timeout_%26_Signal_Handling.md) (1 shared connections)

## Source Files

- `docs/adr/0024-worker-core-protocol.md`
- `docs/adr/0025-plan-module-feature-to-jobs.md`
- `docs/adr/0030-realtime-persistence-seam.md`
- `docs/adr/0031-job-lifecycle-states-and-severity.md`
- `docs/adr/0033-iac-aws-backend-and-composition-wiring.md`
- `docs/adr/0040-consumer-role-model-and-terminology.md`

## Audit Trail

- EXTRACTED: 94 (99%)
- INFERRED: 1 (1%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*