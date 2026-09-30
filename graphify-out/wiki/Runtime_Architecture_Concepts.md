# Runtime Architecture Concepts

> 23 nodes · cohesion 0.10

## Key Concepts

- **云端后端由哪些载体组成** (13 connections) — `docs/internals/cloud-backend-carriers.md`
- **提交时刻固定 task-def revision** (6 connections) — `docs/internals/cloud-backend-carriers.md`
- **gherkai UI 自动化测试工具** (6 connections) — `README.md`
- **载体：使用方的 variant 镜像** (4 connections) — `docs/internals/cloud-backend-carriers.md`
- **确定性 step** (4 connections) — `README.md`
- **基础镜像 / variant / 默认指针** (3 connections) — `CONTEXT.md`
- **revision 机会式清理 pass** (3 connections) — `docs/internals/cloud-backend-carriers.md`
- **载体：SSM 参数（版本戳/模板/镜像映射/默认指针）** (3 connections) — `docs/internals/cloud-backend-carriers.md`
- **GHERKAI_STEPS_DIR / --steps-dir** (3 connections) — `docs/user-guide/configuration.md`
- **执行核心库窄腰** (2 connections) — `CONTEXT.md`
- **核心注入接口 (core ports)** (2 connections) — `CONTEXT.md`
- **确定性 step 注册表** (2 connections) — `CONTEXT.md`
- **执行引擎 port (engine port)** (2 connections) — `CONTEXT.md`
- **版本真源 (single version source)** (2 connections) — `CONTEXT.md`
- **steps 目录 / 定制面** (2 connections) — `CONTEXT.md`
- **每 scope 一个 worker 进程 + 薄 worker** (2 connections) — `CONTEXT.md`
- **载体：官方 worker 基础镜像** (2 connections) — `docs/internals/cloud-backend-carriers.md`
- **载体：CloudFormation stack** (2 connections) — `docs/internals/cloud-backend-carriers.md`
- **两个真值源：local 的 steps 目录 vs cloud 的 variant 镜像** (2 connections) — `docs/internals/deterministic-step-lifecycle.md`
- **云端后端（--backend cloud）** (2 connections) — `README.md`
- **部署 provider** (1 connections) — `CONTEXT.md`
- **本机后端（--backend local）** (1 connections) — `README.md`
- **导航 step（双引号里的 URL）** (1 connections) — `README.md`

## Relationships

- [Agent Skill Reference Docs](Agent_Skill_Reference_Docs.md) (5 shared connections)
- [Architecture Diagrams](Architecture_Diagrams.md) (3 shared connections)
- [Package Contributor Docs](Package_Contributor_Docs.md) (2 shared connections)
- [Project Conventions Docs](Project_Conventions_Docs.md) (2 shared connections)
- [Core Adapters Documentation](Core_Adapters_Documentation.md) (2 shared connections)
- [SSM Path Naming](SSM_Path_Naming.md) (1 shared connections)
- [Worker Image Management](Worker_Image_Management.md) (1 shared connections)
- [CDK App & Backend Stack](CDK_App_%26_Backend_Stack.md) (1 shared connections)
- [Cloud Composition Helpers](Cloud_Composition_Helpers.md) (1 shared connections)

## Source Files

- `CONTEXT.md`
- `README.md`
- `docs/internals/cloud-backend-carriers.md`
- `docs/internals/deterministic-step-lifecycle.md`
- `docs/user-guide/configuration.md`

## Audit Trail

- EXTRACTED: 40 (91%)
- INFERRED: 4 (9%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*