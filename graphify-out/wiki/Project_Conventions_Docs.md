# Project Conventions Docs

> 45 nodes · cohesion 0.08

## Key Concepts

- **ADR 0037 分发与打包** (40 connections) — `docs/adr/0037-distribution-and-packaging.md`
- **ADR 0038 worker 镜像交付** (22 connections) — `docs/adr/0038-worker-image-delivery.md`
- **DEVELOPMENT.md — 开发者指南** (14 connections) — `DEVELOPMENT.md`
- **文档健康度复盘任务说明** (11 connections) — `docs/doc-health-review.md`
- **release.yml — 发布全链工作流** (10 connections) — `.github/workflows/release.yml`
- **CLAUDE.md — 项目约定** (9 connections) — `CLAUDE.md`
- **代码健康度复盘任务说明** (9 connections) — `docs/code-health-review.md`
- **README.md — 仓库首页（使用者向）** (8 connections) — `README.md`
- **ci.yml — 常规检查工作流** (7 connections) — `.github/workflows/ci.yml`
- **gherkai deploy push-worker 流程（架构校验、推后取 digest、注册 revision）** (6 connections) — `docs/adr/0038-worker-image-delivery.md`
- **.github/workflows/README.md — CI 与发布链用法** (6 connections) — `.github/workflows/README.md`
- **release job: GHCR 基底镜像（matrix novaact/midscene）** (6 connections) — `.github/workflows/release.yml`
- **worker 镜像：基底 / variant / 默认指针** (4 connections) — `CONTEXT.md`
- **版本 skew 检查三态（SSM 版本戳比对）** (4 connections) — `docs/adr/0037-distribution-and-packaging.md`
- **版本单旋钮 (single version knob)** (3 connections) — `CONTEXT.md`
- **清理 pass：退休 tag + 静默期 + 在跑 run 安全阀** (3 connections) — `docs/adr/0038-worker-image-delivery.md`
- **release job: gate + build** (3 connections) — `.github/workflows/release.yml`
- **release job: publish npm** (3 connections) — `.github/workflows/release.yml`
- **release job: publish PyPI** (3 connections) — `.github/workflows/release.yml`
- **文档纪律（ADR / CONTEXT / journey / guides 分层）** (2 connections) — `CLAUDE.md`
- **graphify 知识图使用约定** (2 connections) — `CLAUDE.md`
- **绿 ≠ 对：识别结论的证据边界** (2 connections) — `CLAUDE.md`
- **agent skill (gherkai skill)** (2 connections) — `CONTEXT.md`
- **通用 step (Generic step)** (2 connections) — `CONTEXT.md`
- **三名分离：发行名 / import 名 / 命令名** (2 connections) — `CONTEXT.md`
- *... and 20 more nodes in this community*

## Relationships

- [Architecture ADR Decisions](Architecture_ADR_Decisions.md) (14 shared connections)
- [Architecture Decision Records](Architecture_Decision_Records.md) (12 shared connections)
- [CLI Docs & Skill References](CLI_Docs_%26_Skill_References.md) (9 shared connections)
- [CLI Usability & Evidence Docs](CLI_Usability_%26_Evidence_Docs.md) (8 shared connections)
- [DynamoDB Events Transport](DynamoDB_Events_Transport.md) (5 shared connections)
- [Execution Model Concepts](Execution_Model_Concepts.md) (4 shared connections)
- [Domain Roles & Concepts Glossary](Domain_Roles_%26_Concepts_Glossary.md) (3 shared connections)
- [Domain Glossary](Domain_Glossary.md) (3 shared connections)
- [Termination & Engine Ports](Termination_%26_Engine_Ports.md) (3 shared connections)
- [Cloud Run State Mechanisms](Cloud_Run_State_Mechanisms.md) (1 shared connections)

## Source Files

- `.claude/commands/code-health-review.md`
- `.claude/commands/doc-health-review.md`
- `.github/workflows/README.md`
- `.github/workflows/ci.yml`
- `.github/workflows/release.yml`
- `CLAUDE.md`
- `CONTEXT.md`
- `DEVELOPMENT.md`
- `README.md`
- `docs/adr/0035-local-app-testing-via-tunnel.md`
- `docs/adr/0037-distribution-and-packaging.md`
- `docs/adr/0038-worker-image-delivery.md`
- `docs/code-health-review.md`
- `docs/doc-health-review.md`
- `docs/guides/cloud-backend-carriers.md`

## Audit Trail

- EXTRACTED: 130 (95%)
- INFERRED: 7 (5%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*