# gherkai-runtime

gherkai 的运行时层：**「这个产品有哪两个 AI 引擎、怎么把它们拉起来、云资源叫什么名字、一次 run 怎么组装与推进」
这些知识全收在这里**，让任何前端（命令行、Web 界面、云函数）只需写自己的界面与交互。命令行工具
[`gherkai`](https://github.com/zhiyanliu/gherkai#readme) 就是建在它上面的第一个前端；本包是给要**做另一个前端**
（Web 界面、自建调度服务、把执行嵌进现有平台）的人。执行模型本身在
[`gherkai-core`](https://pypi.org/project/gherkai-core/)，本包负责把引擎、存储、云资源这些对象组装好交给它。

## 安装

```bash
uv add gherkai-runtime            # 或 pip install gherkai-runtime
uv add 'gherkai-runtime[aws]'     # 用到云端（DynamoDB / S3 / Fargate）时需要（拉 boto3）
```

需要 Python ≥ 3.13。装了 `gherkai` 命令行的人不用单独装它。

## 最小用法：在本机跑完一批

```python
from pathlib import Path

from gherkai_core.model import RunMeta
from gherkai_core.schedule import ScheduleOpts, schedule
from gherkai_core.scope import PlanConfig, plan
from gherkai_runtime import compose

features = [compose.load_feature(Path("features/checkout.feature"))]
jobs = plan(features, PlanConfig(default_engine="novaact", default_job_timeout_s=300))

engines = compose.build_engines(region="us-east-1")          # 本机 worker 子进程
meta = RunMeta(run_id=compose.new_run_id(), created_at=compose.now_iso(),
               jobs=tuple(jobs), max_concurrency=2)
result = schedule(meta, compose.make_resolver(engines), print, ScheduleOpts(max_concurrency=2))
```

要落库就把 store 一起装上：`compose.build_local_stores(report_dir=...)`（文件）或
`compose.build_cloud_stores(...)`（DynamoDB + S3），交给核心库的实时写编排即可，两条路复用同一套写序。

## 主要入口

| 你要做的事 | 用哪个 |
|---|---|
| 读 `.feature`、生成 run 身份 | `compose.load_feature` / `new_run_id` / `now_iso` |
| 拉起本机引擎 worker | `compose.build_engines` + `compose.make_resolver` |
| 拉起云端（Fargate）引擎 worker | `compose.build_fargate_engines` |
| 决定结果落哪 | `compose.build_local_stores` / `build_cloud_stores` |
| 解析云资源终名与 region/profile | `compose.resolve_cloud_target` / `resolve_network` |
| 提交前的体检（资源在不在、版本对不对、镜像选哪套） | `compose.preflight_cloud_resources` / `check_backend_skew` / `resolve_worker_variant` |
| 查引擎支持哪些确定性步骤、某段文本会不会命中 | `compose.query_deterministic` / `match_deterministic` |
| 「提交完就走」的本机后台推进 | `detached` |
| 云资源、SSM 路径、worker 镜像 tag 怎么命名 | `names`（命名规则只有这一份实现，别自己拼字符串） |
| 把本机可达的被测应用暴露给云端浏览器 | `tunnel` / `tunnel_host` |

引擎名是 `novaact` / `midscene`（`names.ENGINES`）。worker 是独立安装的程序，`compose.resolve_worker_cmd`
负责按顺序找它（环境变量覆写 > 同环境模块 > PATH 上的可执行 > 临时拉起兜底——最后一级仅 novaact 有，且要求 CLI 是正式发行版本、机器上有 `uvx`；midscene 必须真装），全都找不到时抛
`WorkerNotFoundError`，报错里自带该引擎的安装命令——你的前端把它原样转述给用户即可。

## 注意

- **本包会 spawn 子进程、读环境变量、连 AWS**（这些正是它替你担的脏活）。纯本机路径不会 import boto3。
- 云端那套资源要先有人用 `gherkai deploy` 建好；调用方与已部署后端**必须同版本**，`check_backend_skew`
  就是给你的前端做这个体检的，请在动任何资源之前调它。
- `names` 里的命名规则与部署侧共用一份实现：别在自己的前端里另拼一套表名/桶名，换 prefix 就会错开。

## 相关

主页与问题反馈：https://github.com/zhiyanliu/gherkai#readme ｜ https://github.com/zhiyanliu/gherkai/issues

设计文档（架构决策记录）见 https://github.com/zhiyanliu/gherkai/tree/HEAD/docs/adr
