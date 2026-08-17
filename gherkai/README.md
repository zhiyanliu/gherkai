# gherkai —— 产品本体（组合根共享层）

`cli` / `lambdas` / 未来 WebUI 的**共同地基**（ADR 0016「演进」节）：这里知道产品的一切（有哪两个引擎、
云资源怎么命名、run 怎么装配推进），各入口只是它的皮。依赖方向：`皮 → gherkai → core`（窄腰红线不变）。

- `compose.py` —— 组合根/引擎注册表：`build_engines` / `build_fargate_engines` / `build_local_stores` /
  `build_cloud_stores` / grace 推导 / run_id·时钟
- `detached.py` —— local 无状态跑批宿主（ADR 0034）：SubprocessLauncher + per-run reconcile loop
- `names.py` —— 资源命名真源（零依赖；`iac_aws_backend` 直接 import，消复刻）
- `tunnel.py` —— 隧道 provider（ADR 0035）：`--expose-local` 起/拆 ngrok（basic-auth 凭据每 run 一换、按
  pid 跨进程收尾）+ job 文本里的 origin 替换（`map_origin_in_jobs`，worker/core 对隧道无知）

```bash
cd gherkai && uv sync && uv run pytest tests/ -q
```
