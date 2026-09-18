# runtime 包 —— contributor 文档

同目录的 [`README.md`](./README.md) 是发行包的入口页（逐字发布到 PyPI，只保留定位 / 安装方式 / 最小用法与外链），使用者的用法见 [`docs/user-guide/`](../docs/user-guide/README.md)；本文件面向修改本包的 contributor，不进发行包。

发行名 `gherkai-runtime` / import 名 `gherkai_runtime`（ADR 0037 决策 2a「三名分离」；发行名 `gherkai` 归 CLI 包）。

`cli` / `lambdas` / 未来 WebUI 的**共同地基**（ADR 0016「演进」节）：本包持有产品级知识——两个引擎的注册与拉起、
云资源命名、run 的装配与推进；各入口只做参数解析与呈现。依赖方向：`入口 → gherkai_runtime → gherkai_core`
（窄腰红线不变：引擎知识不进 core）。

## 模块

包内五个模块（`__init__.py` 只有包说明、无逻辑）：

- `compose.py` —— 组合根/引擎注册表，按职责分四组：
  - **worker 拉起**：`resolve_worker_cmd`（四级定位链，ADR 0037 决策 3——env 覆写 `GHERKAI_WORKER_<ENGINE>_CMD`（+ 可选
    `_CWD`）> 同 venv `-m`（仅 Python 引擎）> PATH 上 `gherkai-worker-<engine>` > `uvx` 按版本临时拉起（**仅 novaact**；
    midscene 无本级，理由见下）；四级均未命中时抛 `WorkerNotFoundError`，交由调用点分叉）/ `build_engines`（local 档）/
    `build_fargate_engines`（cloud 档，接受**显式 task-def revision ARN** 的映射，ADR 0038）。注入 worker 的 env 由本
    模块独占（`GHERKAI_STEPS_DIR` / `GHERKAI_NO_ARTIFACTS` / `GHERKAI_EXTRA_HTTP_HEADERS`：有值显式注入、无值显式清除）。
  - **worker 的两个非 job 入口**（ADR 0036「4.」「5.」）：`query_capabilities`（spawn `worker --capabilities` 读取自述对象——
    steps 加载结果 / 确定性 step 清单 / grace 下限 / 模型 id；契约校验全在此、不合契约不写缓存；进程内按「引擎 + steps
    目录」缓存；`engine_min_grace` 从中取下限，Nova 查询时注入 `NOVA_ACT_TIMEOUT_S` 使两端同源）与 `match_deterministic`
    （spawn `worker --match-steps` 做 plan 标注）。两者共用 `_ask_worker` 中的一份 spawn 与诊断实现。
  - **存储与云端目标装配**：`build_local_stores` / `build_cloud_stores` / `resolve_cloud_target`（云资源终名 +
    region/profile 一处解析）/ `resolve_region` / `resolve_network`（读 SSM 的 subnet/sg）/ `preflight_cloud_resources`
    （提交前的资源存在性检查）/ `probe_aws_identity`（供 doctor 使用）/ `read_resource`（`file://` 与 `s3://` 同一读入口）/
    `local_artifact_locations`·`cloud_artifact_locations`（产物落点清单）。
  - **版本与 variant**：`check_version_skew`·`check_backend_skew`（四个状态常量 `SKEW_OK` / `SKEW_WARN` / `SKEW_BLOCK` /
    `SKEW_SKIP`；六种比对结果如何映射到这四态、逐档措辞见 [`cli/DEVELOPMENT.md`](../cli/DEVELOPMENT.md) 的版本 skew 一节；ADR 0037 决策 7）/ `resolve_worker_variant`
    （提交侧解析 variant → 各引擎 revision）·`resolve_default_worker_task_defs`（旧 definition 的兼容路径）/
    `read_task_def_stop_timeout`（doctor cloud 侧的对照值）/ `new_run_id`·`now_iso`·`run_duration_ms`（run_id 与时钟）/
    `load_feature`·`prune_empty_dirs`（入口共用的工具函数）。
- `detached.py` —— local 无状态跑批宿主（ADR 0034）：`SubprocessLauncher` + `run_reconcile_loop`（per-run 推进循环）+
  `build_local_reconcile`·`drive_local_reconcile`（装配与驱动）+ 超时 claim 回收 + 隧道事实文件的读写
- `names.py` —— 资源命名真源（零依赖；`deploy_aws/gherkai_deploy_aws/names.py` 直接 re-export 后再加 provider 特有常量，
  避免复刻）：资源名 / SSM 路径 / ECR repo 名 / 血缘 tag 键 / worker 镜像 tag（`image_tag` 是 PEP 440 → docker tag 字符集的
  **唯一归一化与校验点**，ADR 0038）
- `tunnel.py` —— 隧道 provider（ADR 0035）：`--expose-local` 启动 / 拆除 ngrok（basic-auth 凭据每个 run 轮换一次、
  按 pid 跨进程收尾）+ job 文本里的 origin 替换（`map_origin_in_jobs`，worker/core 对隧道无知）
- `tunnel_host.py` —— 隧道**宿主**编排（ADR 0035 决策 3）：启动隧道 + 映射 definition + 恒注入的额外请求头
  （`TUNNEL_EXTRA_HTTP_HEADERS`）；cloud submit 守护进程的轮询循环与其 TTL 算法（`compute_watch_ttl_s` 按 definition 计算：
  Σ 各 job 预算 + 启动/级联余量 `CLOUD_STARTUP_MARGIN_S`，执行侧不超时的 job 按 `UNBOUNDED_JOB_BUDGET_S` 记账）

## 从 checkout 跑 / 测试

```bash
uv sync                          # 仓库根：一次安装五个 workspace 成员 core/runtime/cli/engines/novaact/deploy_aws（editable）
uv run pytest -q runtime/tests   # 仓库根：只跑本包单测（`uv run pytest` 不带路径 = 跑全部成员）
```

`build_cloud_stores` / `build_fargate_engines` 的 boto3 import 惰性收敛在 `_make_*` 钩子内：**纯 local 路径绝不
触发该 import**（ADR 0016 窄腰 / 0030）。修改这些函数时须保持 `import boto3` 不上移到模块顶层。

worker 定位链第四级（`uvx`）与 fd 传递的相互作用是真跑得出的约束：`uvx` 穿透 fd3，`npx -y` 会替换 fd
并导致事件全部丢失（因此 midscene 无第四级）。细节与实测证据见 `resolve_worker_cmd` 的 docstring 与 ADR 0037 决策 3。

## 相关 ADR

- [0016](../docs/adr/0016-execution-architecture-core-lib-run-model.md) 执行架构 / 组合根注入 /「演进」节（本包为何从 cli 拆出）
- [0026](../docs/adr/0026-schedule-module.md) schedule 契约（engines 注入形状）
- [0030](../docs/adr/0030-realtime-persistence-seam.md) 实时写接缝（两套 store 装配复用同一写序）
- [0033](../docs/adr/0033-iac-aws-backend-and-composition-wiring.md) 云端资源清单与命名契约
- [0034](../docs/adr/0034-detached-batch-reconciler.md) 无状态跑批（`detached` 宿主、推进触发源、job timeout）
- [0035](../docs/adr/0035-local-app-testing-via-tunnel.md) 隧道暴露本机应用（`tunnel` / `tunnel_host`）
- [0036](../docs/adr/0036-deterministic-capability-discovery.md) 确定性能力自述
- [0037](../docs/adr/0037-distribution-and-packaging.md) 分发与打包（三名分离、worker 定位链、版本 skew）
- [0038](../docs/adr/0038-worker-image-delivery.md) worker 镜像交付（variant → 显式 revision、镜像 tag 归一化）

参与开发的总入口（环境、测试、发布链、文档地图）见根 [`CONTRIBUTING.md`](../CONTRIBUTING.md)；执行与推进的机理解读见
[`docs/internals/`](../docs/internals/README.md)。
