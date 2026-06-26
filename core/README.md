# core — 执行核心库（窄腰）

解析 `.feature` → 分组 scope → 调度 → 收集结果。**零引擎依赖**：核心不 import Midscene / Nova Act，引擎跑在 worker 子进程里，靠 worker↔core JSON 协议通信。

设计见 ADR：
- [0016](../docs/adr/0016-execution-architecture-core-lib-run-model.md) 执行架构 / Run 数据模型 / ports
- [0024](../docs/adr/0024-worker-core-protocol.md) worker↔core 协议
- [0025](../docs/adr/0025-plan-module-feature-to-jobs.md) plan 模块（解析 + scope 分组）
- [0026](../docs/adr/0026-schedule-module.md) schedule 模块（并发调度）

## 模块

```
core/
├── model.py      ← 领域模型：Job / Scenario / Step / 事件 / RunResult（纯数据）
├── parse.py      ← .feature → 领域模型（借 gherkin-official Compiler；库藏在此 seam 后）
├── scope.py      ← tag 分组 + engine 校验 → Job[]；对外 plan(features, config) -> Job[]
├── ports.py      ← Engine / RunStore / ResultStore / ReportStore 接口（组合根注入）
└── schedule.py   ← schedule(jobs, engines, sink, opts) -> RunResult（并发/隔离/超时/优雅停）
```

## 跑测试

```bash
cd core
uv run pytest
```
