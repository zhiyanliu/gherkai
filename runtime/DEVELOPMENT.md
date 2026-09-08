# runtime 包 —— contributor 文档

用户面文档是同目录的 [`README.md`](./README.md)（逐字上 PyPI 页面）；本文件给改这个包的人，不进发行包。

发行名 `gherkai-runtime` / import 名 `gherkai_runtime`（ADR 0037 决策 2a「三名分离」；发行名 `gherkai` 归 CLI 包）。

`cli` / `lambdas` / 未来 WebUI 的**共同地基**（ADR 0016「演进」节）：这里知道产品的一切（有哪两个引擎、
云资源怎么命名、run 怎么装配推进），各入口只是它的皮。依赖方向：`皮 → gherkai_runtime → gherkai_core`
（窄腰红线不变：引擎知识不进 core）。

## 模块

- `compose.py` —— 组合根/引擎注册表：`resolve_worker_cmd`（worker 四级定位链，ADR 0037 决策 3——env 覆写 >
  同 venv `-m` > PATH bin > uvx/npx 兜底；全 miss 抛 `WorkerNotFoundError` 交调用点分叉）/ `build_engines` /
  `build_fargate_engines`（cloud 档，吃**显式 task-def revision ARN** 的映射，ADR 0038）/ `build_local_stores` /
  `build_cloud_stores` / `resolve_cloud_target`（云资源终名 + region/profile 一处解析）/ 版本 skew 比对
  （`check_backend_skew`，五态见 `cli/DEVELOPMENT.md`；ADR 0037 决策 7）/ worker variant 解析（`resolve_worker_variant` 供提交侧 preflight、
  `resolve_default_worker_task_defs` 供宿主兼容路径，ADR 0038）/ 确定性能力自述（`query_deterministic` /
  `match_deterministic`，ADR 0036）/ grace 推导 / run_id·时钟
- `detached.py` —— local 无状态跑批宿主（ADR 0034）：SubprocessLauncher + per-run reconcile loop
- `names.py` —— 资源命名真源（零依赖；`deploy_aws/gherkai_deploy_aws/names.py` 直接 re-export，消复刻）：
  资源名 / SSM 路径 / worker 镜像 tag（`image_tag` 是 PEP 440 → docker tag 字符集的**唯一归一化与校验点**，ADR 0038）
- `tunnel.py` —— 隧道 provider（ADR 0035）：`--expose-local` 起/拆 ngrok（basic-auth 凭据每 run 一换、按
  pid 跨进程收尾）+ job 文本里的 origin 替换（`map_origin_in_jobs`，worker/core 对隧道无知）
- `tunnel_host.py` —— 隧道**宿主**编排（ADR 0035 决策 3）：起隧道 + 映射 definition + 恒注入的额外请求头；
  cloud submit 守护进程的轮询循环与其 TTL 算法（按 definition 算，不是拍常数）

## 从 checkout 跑 / 测试

```bash
uv sync                        # 仓库根：一次装齐五个 workspace 成员 core/runtime/cli/engines/novaact/deploy_aws（editable）
cd runtime && uv run pytest -q # 只跑本包单测（仓库根 `uv run pytest` 跑全部成员）
```

`build_cloud_stores` / `build_fargate_engines` 的 boto3 import 惰性收在 `_make_*` 钩子里——**纯 local 路径绝不
触发 import**（ADR 0016 窄腰 / 0030）。改这些函数时别把 `import boto3` 提到模块顶层。

worker 定位链的第四级（uvx/npx 兜底）与 fd 传递的相互作用是真跑验出来的坑：`uvx` 不吞 fd3、`npx -y` 会把 fd
换掉导致事件全丢（故 midscene 无第四级）——细节与实测证据在 `resolve_worker_cmd` 的 docstring 与 ADR 0037 决策 3。

## 相关 ADR

- [0016](../docs/adr/0016-execution-architecture-core-lib-run-model.md) 执行架构 / 组合根注入 /「演进」节（本包为何从 cli 抽出来）
- [0026](../docs/adr/0026-schedule-module.md) schedule 契约（engines 注入形状）
- [0030](../docs/adr/0030-realtime-persistence-seam.md) 实时写接缝（两套 store 装配复用同一写序）
- [0033](../docs/adr/0033-iac-aws-backend-and-composition-wiring.md) 云端资源清单与命名契约
- [0034](../docs/adr/0034-detached-batch-reconciler.md) 无状态跑批（`detached` 宿主、推进触发源、job timeout）
- [0035](../docs/adr/0035-local-app-testing-via-tunnel.md) 隧道暴露本机应用（`tunnel` / `tunnel_host`）
- [0036](../docs/adr/0036-deterministic-capability-discovery.md) 确定性能力自述
- [0037](../docs/adr/0037-distribution-and-packaging.md) 分发与打包（三名分离、worker 定位链、版本 skew）
- [0038](../docs/adr/0038-worker-image-delivery.md) worker 镜像交付（variant → 显式 revision、镜像 tag 归一化）
