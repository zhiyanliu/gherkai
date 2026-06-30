# core — 执行核心库（窄腰）

解析 `.feature` → 分组 scope → 调度 → 收集结果。**零引擎依赖**：核心不 import Midscene / Nova Act，引擎跑在 worker 子进程里，靠 worker↔core JSON 协议通信。

设计见 ADR：
- [0016](../docs/adr/0016-execution-architecture-core-lib-run-model.md) 执行架构 / Run 数据模型 / ports
- [0024](../docs/adr/0024-worker-core-protocol.md) worker↔core 协议
- [0025](../docs/adr/0025-plan-module-feature-to-jobs.md) plan 模块（解析 + scope 分组）
- [0026](../docs/adr/0026-schedule-module.md) schedule 模块（并发调度）
- [0027](../docs/adr/0027-runreport-aggregation-index.md) RunReport 归集索引
- [0030](../docs/adr/0030-realtime-persistence-seam.md) 实时写接缝 / [0031](../docs/adr/0031-job-lifecycle-states-and-severity.md) job 生命周期态 + severity

## 模块

```
core/
├── model.py      ← 领域模型：Job / Scenario / Step / 6 类事件 / 四层结果 RunResult / Status 七态 / ResourceUri（纯数据）
├── parse.py      ← .feature → 领域模型（借 gherkin-official Compiler；库藏在此 seam 后）
├── scope.py      ← tag 分组 + engine 校验 → Job[]；对外 plan(features, config) -> Job[]
├── serialize.py  ← 领域模型↔dict 的单一序列化真理源（store adapter 复用，ADR 0016/0027）
├── wire.py       ← Job↔JSON 与 0024 事件↔JSON 的线序列化（worker↔core 协议落地）
├── ports.py      ← Engine / WorkerHandle / EngineResolver / Sink / JobSink / RunStore / ResultStore / ReportStore 接口（组合根注入）
├── schedule.py   ← schedule(run_meta, engines, sink, opts, on_job_complete?, on_event?) -> RunResult（并发/隔离/超时/优雅停）
├── persist.py    ← RunPersistence：编排 Store ports 随进度实时落库（commit-point 写序，ADR 0030）
└── adapters/
    ├── subprocess_engine.py        ← Engine 实装：spawn worker 子进程 + 读事件流
    └── {run,result,report}_store/local.py  ← 三个 Store 的本地文件 adapter（云端 DDB/S3 adapter 待建）
```

## 跑测试

```bash
cd core
uv run pytest
```

## 实际执行（跑 .feature）

core 是库，不自带可执行入口。用 [`cli/`](../cli/README.md) 这张皮来跑（它是组合根：读
feature、注入引擎 adapter、渲染结果）：

```bash
cd cli && uv run python -m cli run ../features/wikipedia_generic.feature
```

