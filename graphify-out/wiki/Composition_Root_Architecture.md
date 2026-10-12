# Composition Root Architecture

> 23 nodes · cohesion 0.11

## Key Concepts

- **build_cloud_stores（云端三 store 装配）** (5 connections) — `docs/adr/0016-execution-architecture-core-lib-run-model.md`
- **compose.py（可复用组合根 / 引擎注册表）** (5 connections) — `docs/adr/0016-execution-architecture-core-lib-run-model.md`
- **FargateEngine（云端执行 adapter）** (4 connections) — `docs/adr/0016-execution-architecture-core-lib-run-model.md`
- **RunPersistence（实时写编排）** (4 connections) — `docs/adr/0016-execution-architecture-core-lib-run-model.md`
- **执行核心库 core/（窄腰，零引擎依赖）** (3 connections) — `docs/adr/0016-execution-architecture-core-lib-run-model.md`
- **决策 C：Fargate 执行配置走 CLI 参数注入（region/profile 非对称）** (3 connections) — `docs/adr/0016-execution-architecture-core-lib-run-model.md`
- **Engine port（run_scope(job) → 事件流）** (3 connections) — `docs/adr/0016-execution-architecture-core-lib-run-model.md`
- **ReportStore port（RunReport 归集）** (3 connections) — `docs/adr/0016-execution-architecture-core-lib-run-model.md`
- **RunStore port（控制面：definition + 运行态）** (3 connections) — `docs/adr/0016-execution-architecture-core-lib-run-model.md`
- **runtime/gherkai_runtime（产品本体包 = 组合根共享层）** (3 connections) — `docs/adr/0016-execution-architecture-core-lib-run-model.md`
- **build_engines（SubprocessEngine 注册表）** (2 connections) — `docs/adr/0016-execution-architecture-core-lib-run-model.md`
- **build_local_stores（本地三 store 装配）** (2 connections) — `docs/adr/0016-execution-architecture-core-lib-run-model.md`
- **cli/gherkai_cli（纯皮：argparse + 渲染 + 分派）** (2 connections) — `docs/adr/0016-execution-architecture-core-lib-run-model.md`
- **决策 A：--backend cloud = 存储上云 + Fargate 执行（单一选项）** (2 connections) — `docs/adr/0016-execution-architecture-core-lib-run-model.md`
- **决策 B：subprocess + 云存储降为内部预演手段** (2 connections) — `docs/adr/0016-execution-architecture-core-lib-run-model.md`
- **注入红线：禁止 ports 内 env-sniff 全局单例** (2 connections) — `docs/adr/0016-execution-architecture-core-lib-run-model.md`
- **resolve_cloud_target（云目标解析）** (2 connections) — `docs/adr/0016-execution-architecture-core-lib-run-model.md`
- **ResultStore port（数据面：判定真值唯一权威）** (2 connections) — `docs/adr/0016-execution-architecture-core-lib-run-model.md`
- **SubprocessEngine（参数化单 adapter）** (2 connections) — `docs/adr/0016-execution-architecture-core-lib-run-model.md`
- **build_fargate_engines（云端执行引擎接线点）** (1 connections) — `docs/adr/0016-execution-architecture-core-lib-run-model.md`
- **deploy_aws/gherkai_deploy_aws（AWS deploy provider）** (1 connections) — `docs/adr/0016-execution-architecture-core-lib-run-model.md`
- **names.py（资源命名真源，零依赖纯函数）** (1 connections) — `docs/adr/0016-execution-architecture-core-lib-run-model.md`
- **RunReport（跨引擎归集索引）** (1 connections) — `docs/adr/0016-execution-architecture-core-lib-run-model.md`

## Relationships

- [Core Library Concepts & ADRs](Core_Library_Concepts_%26_ADRs.md) (3 shared connections)
- [Model Selection ADRs](Model_Selection_ADRs.md) (1 shared connections)

## Source Files

- `docs/adr/0016-execution-architecture-core-lib-run-model.md`

## Audit Trail

- EXTRACTED: 30 (97%)
- INFERRED: 1 (3%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*