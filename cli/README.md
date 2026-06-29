# cli — 执行核心库的最薄前端 / 组合根

`core/` 是纯库（零引擎依赖、不碰文件系统）。**cli 是它的第一张皮**：读 `.feature`、
`new` 出具体的引擎子进程 adapter 注入给 core、把 `RunResult` 渲染给人或 CI 看。
WebUI 将来是另一张皮，**直接调 core、复用 `compose`**，不经本 cli（ADR 0016）。

设计见 [ADR 0016](../docs/adr/0016-execution-architecture-core-lib-run-model.md)（执行架构 / 组合根注入）。

## 模块

```
cli/
├── __main__.py   ← argparse 皮：解析参数 → 调 compose/core → 调 render；定义退出码
├── compose.py    ← 组合根：引擎注册表（每腿 cmd/cwd）、读 feature、build resolver（WebUI 也复用）
└── render.py     ← 表层渲染：0024 事件 → 进度行；RunResult → 文本汇总 / JSON
```

`compose`（可复用接线）与 `__main__`（命令行皮）分开：前者是任何前端都要的组合根逻辑，
后者只是 argparse + 标准 IO。

## 跑（会烧真 AWS 钱：模型调用 + AgentCore 会话）

```bash
cd cli
uv sync                                            # 装环境（core 作 path 依赖）

# 跑一个 feature（默认引擎 novaact，默认 max-concurrency=1）
uv run python -m cli run ../features/wikipedia_generic.feature

# 选 Midscene 腿、放开并发、JSON 输出
uv run python -m cli run ../features/wikipedia_generic.feature \
  --engine midscene --max-concurrency 2 --json

# 列可用引擎及其 spawn 命令（不烧钱）
uv run python -m cli list-engines
```

未标 `@engine` 的 scope 用 `--engine` 指定的默认腿；标了 `@engine:` 的按 tag 走（ADR 0019）。

## 退出码

- `0` —— RunResult 总状态 passed
- `1` —— 跑完了但有 failed/error（断言没过 / 引擎异常）
- `2` —— 没跑成：feature 读不到、plan 配置矛盾（PlanError）、或无子命令

## 选项（`run`）

| flag | 默认 | 说明 |
|---|---|---|
| `features...` | — | 一个或多个 `.feature` 路径（位置参数） |
| `--engine` | `novaact` | 未标 `@engine` 的 scope 用的默认引擎 |
| `--max-concurrency` | `1` | 同时在跑的 worker 上限（护真实成本/配额） |
| `--timeout` | `300` | 单 job 墙钟超时秒（`<=0` 不超时） |
| `--grace` | `10` | 停止请求后等优雅退出的宽限秒 |
| `--fail-fast` | off | 任一 job 崩则中止整批 |
| `--json` | off | 只输出机器可读 JSON（CI/WebUI 消费） |
| `--quiet` | off | 不打逐事件进度（仍打文本汇总） |
