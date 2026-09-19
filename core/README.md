# gherkai-core

gherkai 的执行核心库：把 `.feature` 解析成领域模型、按 tag 分组成可并发的 job、并发调度、汇总成四层（run / job / scenario / step）结构化结果。它是 gherkai 命令行与 `gherkai-runtime` 依赖的库，**一般不直接安装**——要运行测试请装命令行包 `gherkai`。把这套执行模型嵌进自己的程序（Web 界面、调度服务、CI 插件）时才直接用它。

## 安装

```bash
uv add gherkai-core            # 或 pip install gherkai-core；需 Python ≥ 3.13
uv add 'gherkai-core[aws]'     # 用 DynamoDB / S3 存储实现时加装（补 boto3 依赖）；只用本地文件存储时不必装
```

## 最小用法

```python
from gherkai_core.model import RunMeta
from gherkai_core.schedule import schedule
from gherkai_core.scope import FeatureSource, PlanConfig, plan

# ① 分组：一组 .feature 文本 → 可并发的 job 列表（core 不读文件，路径与内容由你给）
jobs = plan([FeatureSource(uri="features/checkout.feature", text=feature_text)],
            PlanConfig(default_engine="novaact"))

# ② 执行：run 身份由你生成，引擎与事件回调由你注入
run_meta = RunMeta(run_id=run_id, created_at=created_at, jobs=tuple(jobs))
result = schedule(run_meta, engine_resolver, event_sink)
```

最常用的模块（完整清单见包内各模块的 docstring）：

| 模块 | 提供什么 |
|---|---|
| `gherkai_core.scope` | `plan(features, config)`：按 tag 分组成 job、校验冲突 |
| `gherkai_core.schedule` | `schedule(...)`：并发执行完一个 run 的全部 job，带并发上限、失败隔离、超时、优雅停 |
| `gherkai_core.model` | `RunMeta` / `RunResult` / `Status` 等判定与结果类型 |
| `gherkai_core.ports` | 引擎、存储、进度回调的接口，由你注入实现 |
| `gherkai_core.adapters` | 本机子进程引擎、Fargate 引擎、文件与 DynamoDB + S3 存储等现成实现 |
| `gherkai_core.persist` / `gherkai_core.project` / `gherkai_core.reconcile` | 随进度实时落库、从事件归约出 run 状态，以及幂等推进一次 run（自建后台或无状态批量运行要用） |
| `gherkai_core.errors` | 计划期与执行期的异常类型 |

引擎与存储按 `gherkai_core.ports` 里的接口注入。不想自己接线就用 https://pypi.org/project/gherkai-runtime/ ，它把引擎与存储组装好了。

## 文档

- 判定、退出码、报告与证据：https://github.com/zhiyanliu/gherkai/blob/HEAD/docs/user-guide/running-and-results.md
- 装什么、要哪些 AWS 前置：https://github.com/zhiyanliu/gherkai/blob/HEAD/docs/user-guide/getting-started.md
- 每版变更：https://github.com/zhiyanliu/gherkai/blob/HEAD/CHANGELOG.md

项目主页与问题反馈：https://github.com/zhiyanliu/gherkai#readme
