# Execution Model Concepts

> 21 nodes · cohesion 0.18

## Key Concepts

- **执行与推进模型导览** (18 connections) — `docs/guides/execution-and-reconciliation.md`
- **判定模型导览** (12 connections) — `docs/guides/verdict-model.md`
- **产物与证据地理** (11 connections) — `docs/guides/artifacts-and-evidence.md`
- **CLI --json 字段契约** (11 connections) — `docs/guides/cli-json-contract.md`
- **确定性 step 的一生** (10 connections) — `docs/guides/deterministic-step-lifecycle.md`
- **云端后端的五个载体** (9 connections) — `docs/guides/cloud-backend-carriers.md`
- **docs/guides 索引** (8 connections) — `docs/guides/README.md`
- **三 Lambda 事件驱动链（kicker / reconciler / exit-observer）** (4 connections) — `docs/guides/execution-and-reconciliation.md`
- **四层归约：一票 → step → scenario → job → run** (4 connections) — `docs/guides/verdict-model.md`
- **worker 进程内的确定性注册表（唯一匹配面）** (3 connections) — `docs/guides/deterministic-step-lifecycle.md`
- **各命令退出码的分工** (3 connections) — `docs/guides/verdict-model.md`
- **七个状态与 severity 序** (3 connections) — `docs/guides/verdict-model.md`
- **推进器 (advancer)** (2 connections) — `CONTEXT.md`
- **五类产物（definition / 运行态 / 判定真值 / 派生导航 / 现场证据）** (2 connections) — `docs/guides/artifacts-and-evidence.md`
- **submit 定义期解析、运行期照抄（钉死 revision）** (2 connections) — `docs/guides/cloud-backend-carriers.md`
- **三级短路派发链（注册表 → 内建 URL 导航 → AI）** (2 connections) — `docs/guides/deterministic-step-lifecycle.md`
- **detached 两道闸门（云端 Lambda 不抢前台 run）** (2 connections) — `docs/guides/execution-and-reconciliation.md`
- **job 墙钟预算的三路同形兜底** (2 connections) — `docs/guides/execution-and-reconciliation.md`
- **无状态驱动 reconcile.tick（四个宿主）** (2 connections) — `docs/guides/execution-and-reconciliation.md`
- **job 墙钟预算 (job timeout)** (1 connections) — `CONTEXT.md`
- **同步驱动 schedule()（前台 run）** (1 connections) — `docs/guides/execution-and-reconciliation.md`

## Relationships

- [Architecture ADR Decisions](Architecture_ADR_Decisions.md) (14 shared connections)
- [CLI Usability & Evidence Docs](CLI_Usability_%26_Evidence_Docs.md) (8 shared connections)
- [DynamoDB Events Transport](DynamoDB_Events_Transport.md) (6 shared connections)
- [Project Conventions Docs](Project_Conventions_Docs.md) (4 shared connections)
- [Termination & Engine Ports](Termination_%26_Engine_Ports.md) (3 shared connections)
- [CLI Docs & Skill References](CLI_Docs_%26_Skill_References.md) (1 shared connections)
- [Architecture Decision Records](Architecture_Decision_Records.md) (1 shared connections)
- [Domain Glossary](Domain_Glossary.md) (1 shared connections)

## Source Files

- `CONTEXT.md`
- `docs/guides/README.md`
- `docs/guides/artifacts-and-evidence.md`
- `docs/guides/cli-json-contract.md`
- `docs/guides/cloud-backend-carriers.md`
- `docs/guides/deterministic-step-lifecycle.md`
- `docs/guides/execution-and-reconciliation.md`
- `docs/guides/verdict-model.md`

## Audit Trail

- EXTRACTED: 74 (99%)
- INFERRED: 1 (1%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*