# gherkai-runtime

gherkai 的运行时装配层：拉起两个 AI 引擎的 worker、解析云端资源名与网络、组装并推进一次 run，执行调度交给核心库 https://pypi.org/project/gherkai-core/ 。它是 gherkai 命令行与 AWS 部署包依赖的库，**一般不直接安装**——要运行测试请装命令行包 `gherkai`。要做另一个前端（Web 界面、自建调度服务、把执行嵌进现有平台）时才直接用它。

## 安装

```bash
uv add gherkai-runtime            # 或 pip install gherkai-runtime；需 Python ≥ 3.13
uv add 'gherkai-runtime[aws]'     # 用到云端后端（DynamoDB / S3 / Fargate）时需要
```

## 最小用法

```python
from pathlib import Path
from gherkai_runtime import compose

features = [compose.load_feature(Path("features/checkout.feature"))]
engines = compose.build_engines(region="us-east-1")     # 本机 worker 子进程
resolver = compose.make_resolver(engines)
# 接着把 features 分组成 job、连同 resolver 交给 gherkai_core.schedule.schedule(...) 执行
```

分组到执行的完整用法见核心库的页面：https://pypi.org/project/gherkai-core/ 。

主要模块：

| 模块 | 提供什么 |
|---|---|
| `gherkai_runtime.compose` | 读 `.feature`、生成 run 身份、拉起本机或 Fargate 引擎 worker、选结果落点、解析云端资源名与网络、查引擎能力 |
| `gherkai_runtime.names` | 云端资源名、SSM 参数路径、worker 镜像 tag 的唯一命名实现 |
| `gherkai_runtime.detached` / `tunnel` | 提交后在本机后台把一个 run 推到完成；把本机可达的被测应用暴露给云端浏览器 |

引擎名是 `novaact` 与 `midscene`。运行时会启动 worker 子进程、读取环境变量、访问 AWS 服务，请在配好 AWS 凭证与 region 的环境里使用。云端资源需先由部署方执行 `gherkai deploy` 建好；调用方的版本不能新于已部署的后端（新于即拒绝执行），旧于时只提示、不拦——建议两侧保持同版本。

## 文档

- 四种跑法、结果与退出码：https://github.com/zhiyanliu/gherkai/blob/HEAD/docs/user-guide/running-and-results.md
- 环境变量与选项总表：https://github.com/zhiyanliu/gherkai/blob/HEAD/docs/user-guide/configuration.md
- 云端后端怎么部署：https://github.com/zhiyanliu/gherkai/blob/HEAD/docs/user-guide/cloud-backend.md
- 每版变更：https://github.com/zhiyanliu/gherkai/blob/HEAD/CHANGELOG.md

项目主页与问题反馈：https://github.com/zhiyanliu/gherkai#readme
