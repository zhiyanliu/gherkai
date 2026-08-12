# core — 执行核心库（窄腰）

解析 `.feature` → 分组 scope → 调度 → 收集结果。**零引擎依赖**：核心不 import Midscene / Nova Act，引擎跑在 worker 子进程里，靠 worker↔core JSON 协议通信。

设计见 ADR：
- [0016](../docs/adr/0016-execution-architecture-core-lib-run-model.md) 执行架构 / Run 数据模型 / ports
- [0024](../docs/adr/0024-worker-core-protocol.md) worker↔core 协议
- [0025](../docs/adr/0025-plan-module-feature-to-jobs.md) plan 模块（解析 + scope 分组）
- [0026](../docs/adr/0026-schedule-module.md) schedule 模块（并发调度）
- [0027](../docs/adr/0027-runreport-aggregation-index.md) RunReport 归集索引
- [0030](../docs/adr/0030-realtime-persistence-seam.md) 实时写接缝 / [0031](../docs/adr/0031-job-lifecycle-states-and-severity.md) job 生命周期态 + severity
- [0034](../docs/adr/0034-detached-batch-reconciler.md) 无状态跑批 core 侧拆分（project 纯归约投影 + reconcile 推进编排 + event_log 持久事件通道）

## 模块

```
core/
├── model.py      ← 领域模型：Job / Scenario / Step / 7 类事件（含 step_skipped 短路）/ 四层结果 RunResult / Status 七态 / ResourceUri（纯数据）
├── parse.py      ← .feature → 领域模型（借 gherkin-official Compiler；库藏在此 seam 后）
├── scope.py      ← tag 分组 + engine 校验 → Job[]；对外 plan(features, config) -> Job[]
├── serialize.py  ← 领域模型↔dict 的单一序列化真理源（store adapter 复用，ADR 0016/0027）
├── wire.py       ← Job↔JSON 与 0024 事件↔JSON 的线序列化（worker↔core 协议落地）
├── errors.py     ← core 类型化异常：WorkerNetworkError（network_error 重试分类，ADR 0028）/ PlanError（feature 写法与配置违约，parse/scope 共用，ADR 0019/0025）
├── ports.py      ← Engine / WorkerHandle / EngineResolver / Sink / JobSink / RunStore / ResultStore / ReportStore 接口（组合根注入）
├── schedule.py   ← schedule(run_meta, engines, sink, opts, on_job_complete?, on_event?) -> RunResult（同步 run：并发/隔离/超时/优雅停）
├── project.py    ← 无状态跑批纯归约投影（ADR 0034）：project(events)→RunState/JobResult + plan_next(state)→actions + reduce_event（与 schedule 共用一份归约）
├── reconcile.py  ← 无状态跑批推进编排（ADR 0034）：tick(run_id, meta, event_log, run_store, launcher, N)——幂等、多触发源、CAS/HWM 条件写；起 job 经注入 Launcher（core 不 import boto3）+ finalize_artifacts(...)（done 后聚合收尾，cloud Lambda/local per-run 两宿主共用）
├── persist.py    ← RunPersistence：编排 Store ports 随进度实时落库（commit-point 写序，ADR 0030）
└── adapters/
    ├── subprocess_engine.py        ← Engine 实装（local）：spawn worker 子进程 + 读事件流
    ├── fargate_engine.py           ← Engine 实装（cloud）：RunTask 起 Fargate 容器 + job-in 走 S3 / events-out 走 DDB / stop→StopTask + start_scope fire-and-forget（ADR 0024/0032/0034）
    ├── cloud_launcher.py           ← 无状态跑批 cloud Launcher（ADR 0034）：经 resolver 选 FargateEngine 调 start_scope 起 task（fire-and-forget）
    ├── event_log/{sqlite,ddb}.py   ← 无状态跑批持久事件通道（ADR 0034）：local=SQLite / cloud=DDB events 表，reconciler 从此全量重放推演
    ├── _boto.py                    ← 云端 adapter 共享的 boto3 依赖守卫（缺 boto3 友好报错，ADR 0016 窄腰）
    ├── run_store/{local,ddb}.py    ← RunStore：本地文件 + DynamoDB（+ arg_offload.py：StepArgument→S3 指针，解 DDB 400KB 限；+ 无状态跑批条件写 try_claim_job/project_state/try_finalize，ADR 0034）
    ├── result_store/{local,s3}.py  ← ResultStore：本地文件 + S3（每 job 一对象）
    └── report_store/{local,s3}.py  ← ReportStore：本地文件 + S3（manifest+index）
```

云端 adapter（DDB/S3）已建，行为对拍 local、moto 全程 mock 单测（ADR 0030 决定六）；boto3 是可选依赖 `core[aws]`。
组合根按 backend 注入哪套 adapter——cli 已实装 `--backend {local,cloud}`（装配逻辑在 `cli/compose.py` 的 `build_local_stores`/`build_cloud_stores`，未来 WebUI 复用；ADR 0030 决定七）。

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

