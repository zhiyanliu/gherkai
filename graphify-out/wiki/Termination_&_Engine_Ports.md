# Termination & Engine Ports

> 28 nodes · cohesion 0.09

## Key Concepts

- **ADR 0029 引擎产物上传 S3** (18 connections) — `docs/adr/0029-engine-artifacts-to-s3.md`
- **ADR 0032 Fargate 执行环境** (17 connections) — `docs/adr/0032-fargate-execution-environment.md`
- **ADR 0017: 云执行选 Fargate** (8 connections) — `docs/adr/0017-cloud-execution-fargate-over-runtime.md`
- **远程传输演进：port 抽象活、pipe 传输死** (5 connections) — `docs/adr/0024-worker-core-protocol.md`
- **逻辑层：schedule 经 worker 句柄请求停** (5 connections) — `docs/adr/0024-worker-core-protocol.md`
- **终止契约（core 请求 worker 优雅停止）** (5 connections) — `docs/adr/0024-worker-core-protocol.md`
- **ArtifactUploader 组件（from_env / to_report_ref / flush）** (5 connections) — `docs/adr/0029-engine-artifacts-to-s3.md`
- **事件流结束信号 / 存活判定迁移** (3 connections) — `docs/adr/0024-worker-core-protocol.md`
- **Midscene worker 有序显式 cleanup handler** (3 connections) — `docs/adr/0024-worker-core-protocol.md`
- **Engine port（run_scope，不挂 stop）** (2 connections) — `docs/adr/0024-worker-core-protocol.md`
- **FargateWorkerHandle.stop → StopTask** (2 connections) — `docs/adr/0024-worker-core-protocol.md`
- **JobSource（job 入口可注入接口）** (2 connections) — `docs/adr/0024-worker-core-protocol.md`
- **固有残余（不救）：抢传覆盖不到的产物** (2 connections) — `docs/adr/0029-engine-artifacts-to-s3.md`
- **snapshotLogs（scenario 边界 log 抢传）** (2 connections) — `docs/adr/0029-engine-artifacts-to-s3.md`
- **snapshotReport（Midscene 单引擎增补）** (2 connections) — `docs/adr/0029-engine-artifacts-to-s3.md`
- **上传必须套超时（退出时间有界）** (2 connections) — `docs/adr/0029-engine-artifacts-to-s3.md`
- **上传时机四级（实时 + flush + act 抢传 + scenario 抢传）** (2 connections) — `docs/adr/0029-engine-artifacts-to-s3.md`
- **grace 下限 vs stopTimeout 冲突：解法 D（接受 120 硬顶 + TTL 兜底）** (2 connections) — `docs/adr/0032-fargate-execution-environment.md`
- **真容器 grace / stopTimeout 校准结论** (2 connections) — `docs/adr/0032-fargate-execution-environment.md`
- **孤儿产物扫盘 reaper（经分析否决）** (2 connections) — `docs/adr/0032-fargate-execution-environment.md`
- **上传失败处理两层（分类 + scope 级降级）** (2 connections) — `docs/adr/0032-fargate-execution-environment.md`
- **组合根接线：build_fargate_engines 切 cloud 执行** (2 connections) — `docs/adr/0033-iac-aws-backend-and-composition-wiring.md`
- **exitCode 落值延迟的有界宽限轮询** (1 connections) — `docs/adr/0024-worker-core-protocol.md`
- **未来演进：显式 core→worker 控制通道** (1 connections) — `docs/adr/0024-worker-core-protocol.md`
- **子进程 adapter stop：SIGTERM→grace→SIGKILL** (1 connections) — `docs/adr/0024-worker-core-protocol.md`
- *... and 3 more nodes in this community*

## Relationships

- [Architecture ADR Decisions](Architecture_ADR_Decisions.md) (14 shared connections)
- [DynamoDB Events Transport](DynamoDB_Events_Transport.md) (5 shared connections)
- [Execution Model Concepts](Execution_Model_Concepts.md) (3 shared connections)
- [Project Conventions Docs](Project_Conventions_Docs.md) (3 shared connections)
- [CLI Usability & Evidence Docs](CLI_Usability_%26_Evidence_Docs.md) (3 shared connections)
- [Architecture Decision Records](Architecture_Decision_Records.md) (1 shared connections)
- [Act Timeout & Signal Handling](Act_Timeout_%26_Signal_Handling.md) (1 shared connections)
- [Schedule Semantics Concepts](Schedule_Semantics_Concepts.md) (1 shared connections)

## Source Files

- `docs/adr/0017-cloud-execution-fargate-over-runtime.md`
- `docs/adr/0024-worker-core-protocol.md`
- `docs/adr/0029-engine-artifacts-to-s3.md`
- `docs/adr/0032-fargate-execution-environment.md`
- `docs/adr/0033-iac-aws-backend-and-composition-wiring.md`

## Audit Trail

- EXTRACTED: 66 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*