# cli — 执行核心库的最薄前端 / 组合根

`core/` 是纯库（零引擎依赖、不碰文件系统）。**cli 是它的第一张皮**：读 `.feature`、
`new` 出具体的引擎子进程 adapter 注入给 core、把 `RunResult` 渲染给人或 CI 看。
WebUI 将来是另一张皮，**直接调 core、复用 `compose`**，不经本 cli（ADR 0016）。

设计见 [ADR 0016](../docs/adr/0016-execution-architecture-core-lib-run-model.md)（执行架构 / 组合根注入）。

## 模块

```
cli/
├── __main__.py   ← argparse 皮：解析参数 → 调 compose/core → 注入 RunPersistence 实时落库 → 调 render；定义退出码
├── compose.py    ← 组合根：引擎注册表（每个引擎 cmd/cwd）、读 feature、build resolver（WebUI 也复用）
└── render.py     ← 表层渲染：0024 事件 → 进度行；RunResult → 文本汇总 / JSON
```

`compose`（可复用接线）与 `__main__`（命令行皮）分开：前者是任何前端都要的组合根逻辑，
后者只是 argparse + 标准 IO。

**实时落库（ADR 0030）**：`run` 不是「跑完才一次性落盘」——`__main__` 注入 core 的 `RunPersistence`
（组合根注入三个本地 Store adapter），run 开始即写 definition + 初始全 pending 态，每个 scope 起跑刷
RUNNING、完成即落该 scope 判定真值，最后 `finalize` 写总状态（commit point）。`--no-report` 时跳过整条落库
（裸跑、零落盘逃生舱）。WebUI 换注入 DDB/S3 adapter、复用同一条 `RunPersistence`，cli 这张皮的接线不变。

## 跑（会烧真 AWS 钱：模型调用 + AgentCore 会话）

```bash
cd cli
uv sync                                            # 装环境（core 作 path 依赖）

# 跑一个 feature（默认引擎 novaact，默认 max-concurrency=1）
uv run python -m cli run ../features/wikipedia_generic.feature

# 未标 @engine 的 scope 默认走 Midscene 引擎、放开并发、JSON 输出
uv run python -m cli run ../features/wikipedia_generic.feature \
  --default-engine midscene --max-concurrency 2 --json

# 预检 .feature（不烧钱）：看 scope/job 分组、校验配置（@scope/@engine 冲突等），不真跑
uv run python -m cli plan ../features/wikipedia_generic.feature
uv run python -m cli plan ../features/*.feature --json     # 机器可读分组

# 列可用引擎及其 spawn 命令（不烧钱）
uv run python -m cli list-engines
```

**先 `plan` 后 `run`**：`run` 每次真烧 AWS 钱，`plan` 是纯本地预检——验证 feature 写法、确认
scope/job 分组与 engine 路由符合预期、提前暴露 `PlanError`（uri 冲突 / 同 scope 多 engine 等），
都不连云、不花钱。退出码 0=可跑 / 2=配置错。

> 文本模式对 DataTable/DocString 多行参数只标注尺寸（`+dataTable(行×列)` / `+docString(N 行)`）保持紧凑；
> 要核对参数**完整内容**用 `--json`（携带 content/rows 全文）。

未标 `@engine` 的 scope 用 `--default-engine` 指定的默认引擎；标了 `@engine:` 的按 tag 走、不受此 flag 影响（ADR 0019）。

## 退出码

- `0` —— RunResult 总状态 passed
- `1` —— 跑完了但有 failed/error（断言没过 / 引擎异常）
- `2` —— 没跑成：feature 读不到、plan 配置矛盾（PlanError）、参数非法（如 `--assertion-votes < 1`）、或无子命令

## 输出：stdout = 数据 / stderr = 进度

遵循 Unix 惯例：**stdout 只放该命令的核心产出**（`--json` 的 JSON 文档 / 人看的文本汇总 / `list-engines` 列表），**stderr 放所有进度诊断**（plan、逐事件、run_id、RunReport 落点、worker 透传日志）。故：

- `cli run … --json > r.json` —— `r.json` 是纯净 JSON（进度仍在终端可见、不污染文件）
- `cli run … > summary.txt` —— `summary.txt` 是纯净文本汇总

## 选项（`run`）

| flag | 默认 | 说明 |
|---|---|---|
| `features...` | — | 一个或多个 `.feature` 路径（位置参数） |
| `--default-engine` | `novaact` | 未标 `@engine` 的 scope 用的默认引擎（标了 `@engine:` 的按 tag 走） |
| `--assertion-votes` | `1` | AI 断言（`Then`）投票次数（默认 1=单次判定）；调高（如 3/5）启用抖动检测：跑 N 次取多数票（ADR 0014）。须 ≥1 |
| `--max-concurrency` | `1` | 同时在跑的 worker 上限（护真实成本/配额） |
| `--timeout` | `300` | 单 job 墙钟超时秒（`<=0` 不超时） |
| `--grace` | `10` | 停止请求后等优雅退出的宽限秒 |
| `--fail-fast` | off | 任一 job 崩则中止整批 |
| `--json` | off | 只输出机器可读 JSON（CI/WebUI 消费） |
| `--quiet` | off | 不打逐事件进度（仍打文本汇总） |
| `--report-dir` | `reports` | RunReport 归集落点；每次 run 落 `DIR/<run_id>/`（ADR 0027） |
| `--no-report` | off | 跳过 RunReport 归集（逃生舱：CI 只看退出码/JSON、或调试不想落盘） |
| `--materialize` | off | 归集时把本地原生产物按字节拷进 `<run_id>/artifacts/`（自包含、可搬运/上 S3；默认只链接不拷） |

### RunReport（每次 run 的应得产物，默认生成）

每次 `run` **默认**把这次执行归集成一份 RunReport（ADR 0027）到 `reports/<run_id>/`：
- `manifest.json` —— 机器可读（CI/WebUI 消费）：判定/时长/成本 + 各引擎原生报告产物的扁平清单。
- `index.html` —— 人可导航入口：每个原生产物（Midscene html / Nova trajectory）一行链接，
  点开看**原样**产物。RunReport 只索引/链接、**不解析融合**产物内容；新引擎报任意 `kind` 零改 core。

默认 index 链接指向产物**原位**；要自包含目录（搬走/上 S3/发同事）见选项表的 `--materialize`、跳过归集见 `--no-report`。
