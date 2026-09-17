# gherkai

用 Gherkin `.feature` 写 UI 端到端测试，交给 AI 浏览器引擎（Nova Act 或 Midscene）在云端浏览器里操作页面、判定断言。本包是 gherkai 的命令行入口：解析 `.feature`、按 tag 分组成可并发的 job、派给引擎执行、汇总每条用例的判定与报告。测试跑在你自己的 AWS 账户里，会产生真实 AWS 费用，金额以你的 AWS 账单为准。

## 安装

```bash
uv tool install gherkai                # 命令行本体，需 Python ≥ 3.13
uv tool install 'gherkai[local]'       # 附带在本机跑 Nova Act 引擎所需的 worker
npm i -g @gherkai/worker-midscene      # 在本机跑 Midscene 引擎所需的 worker，需 Node ≥ 22
```

Midscene worker 与命令行须是同一个版本：用 `gherkai --version` 查版本号，再装 `npm i -g @gherkai/worker-midscene@<版本号>`。

## 最小用法

```bash
export AWS_REGION=us-east-1               # region 必须有出处：--region、环境变量或 profile 配置
gherkai doctor                            # 自检环境；加 --backend cloud 连带查凭证与云端后端
gherkai plan features/checkout.feature    # 预检分组与派发预期，不连云端、不产生费用
gherkai run features/checkout.feature     # 在本机起 worker 跑一批（浏览器与模型仍在云端）；退出码给出判定
gherkai explain <run_id>                  # 读这个 run 的每步证据，看断言为什么这么判
```

全部命令与选项以 `gherkai --help`、`gherkai <命令> --help` 为准。`plan`、`run`、`status`、`explain`、`doctor` 等命令都支持 `--json`，便于脚本与 CI 解析。

用 AI coding agent 操作 gherkai 的话，先跑 `gherkai skill install` 把使用说明装进你的项目，之后直接告诉 agent 要测什么。

## 文档

- 装什么、要哪些 AWS 前置、第一次怎么跑通：https://github.com/zhiyanliu/gherkai/blob/HEAD/docs/user-guide/getting-started.md
- 四种跑法、结果在哪、退出码什么意思：https://github.com/zhiyanliu/gherkai/blob/HEAD/docs/user-guide/running-and-results.md
- `.feature` 怎么写才跑得稳：https://github.com/zhiyanliu/gherkai/blob/HEAD/docs/user-guide/writing-features.md
- 环境变量与选项总表：https://github.com/zhiyanliu/gherkai/blob/HEAD/docs/user-guide/configuration.md
- 报错了先看哪：https://github.com/zhiyanliu/gherkai/blob/HEAD/docs/user-guide/troubleshooting.md
- 每版变更：https://github.com/zhiyanliu/gherkai/blob/HEAD/CHANGELOG.md

项目主页与问题反馈：https://github.com/zhiyanliu/gherkai#readme
