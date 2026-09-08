# gherkai-core

gherkai 的执行核心库：把 `.feature` 解析成领域模型 → 按 tag 分组成可并发的 job → 并发调度 → 收集成结构化结果。
核心逻辑**不带任何 AI 引擎依赖、不碰文件系统、也不 import boto3**——AI 引擎跑在被 spawn 的 worker 子进程里、讲一套
JSON 协议，落盘/云服务/起进程都在你注入的接口实现里（本包顺带提供了几个现成实现，见下）。想直接跑测试的人要的是命令行工具
[`gherkai`](https://github.com/zhiyanliu/gherkai#readme)；本包是给要把这套执行模型**嵌进自己程序**
（WebUI、调度服务、CI 插件）的人。

## 安装

```bash
uv add gherkai-core            # 或 pip install gherkai-core
uv add 'gherkai-core[aws]'     # 顺带 DynamoDB / S3 那组实现（拉 boto3）
```

需要 Python ≥ 3.13。装了 `gherkai` 命令行的人不用单独装它。

## 最小用法

```python
from gherkai_core.model import RunMeta
from gherkai_core.schedule import ScheduleOpts, schedule
from gherkai_core.scope import FeatureSource, PlanConfig, plan

jobs = plan(
    [FeatureSource(uri="checkout.feature", text=feature_text)],   # 内容，不是路径
    PlanConfig(default_engine="novaact", default_job_timeout_s=300),
)
meta = RunMeta(run_id="r-1", created_at="2026-01-01T00:00:00Z", jobs=tuple(jobs), max_concurrency=2)
result = schedule(meta, engine_resolver, progress_sink, ScheduleOpts(max_concurrency=2))
print(result.status)          # passed / failed / error / …
```

- `plan(features, config)` 按 `@scope` / `@engine` / `@timeout:` tag 分组、校验冲突，产出 `Job[]`。
- `schedule(...)` 同步跑完一批：并发上限、失败隔离、墙钟超时、优雅停都在里面。`RunResult` 是四层结构
  （run → job → scenario → step），每层带判定与时长。
- 想要「提交完就走、谁来查谁接力」那种跑法，用 `reconcile.tick(...)`：它从一条持久事件流重放推演出下一步动作，
  可以由任何宿主（后台进程、云函数、下一次查询）反复调用而不重复起 job。

## 你要注入什么（`gherkai_core.ports`）

| 接口 | 你提供 |
|---|---|
| `Engine` / `WorkerHandle` / `EngineResolver` | 怎么起一个引擎 worker、怎么读它的事件流、怎么停它 |
| `Sink` / `JobSink` | 进度事件、每个 job 完成时的判定结果回调（进度显示、实时落库） |
| `RunStore` / `ResultStore` / `ReportStore` | 运行状态、判定真值、报告分别落在哪 |

`gherkai_core.adapters` 里已有一组现成实现：本机子进程引擎 / Fargate 引擎、本地文件 store / DynamoDB + S3 store、
SQLite / DynamoDB 事件流。**不想自己接线**就用 [`gherkai-runtime`](https://pypi.org/project/gherkai-runtime/)，
它把这些组装好了（命令行工具用的就是它）。

## 异常

| 异常 | 什么时候 |
|---|---|
| `errors.PlanError` | feature 写法或配置违约（同一个 scope 标了多个引擎、uri 冲突…）——在起任何 job 之前抛 |
| `errors.WorkerNetworkError` | 引擎 worker 报的网络类故障，已归好类，由你决定要不要重试 |
| `parse.FeatureParseError` | Gherkin 语法错 |

判定态是 `model.Status`：worker 只报 `passed` / `failed` / `error`，`skipped` / `aborted` 是快速失败下的派生终态，
`pending` / `running` 只出现在运行中的状态视图里、不会成为终态判定。

## 相关

主页与问题反馈：https://github.com/zhiyanliu/gherkai#readme ｜ https://github.com/zhiyanliu/gherkai/issues

设计文档（架构决策记录）见 https://github.com/zhiyanliu/gherkai/tree/HEAD/docs/adr
