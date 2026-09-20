# gherkai

**gherkai** 是一个 UI 自动化测试工具。测试用 Gherkin（`.feature` 文件）写成自然语言，由 AI 引擎（Midscene 或 Nova Act）读懂后，在 AWS Bedrock AgentCore 承载的云端浏览器里执行，并给出可复核的判定与证据。浏览器、模型与云端组件全部运行在你自己的 AWS 账户内，本机不需要安装浏览器。

一个 step 有三种执行路径：

- **交给 AI（默认）**：引擎读自然语言，自己操作页面、自己判断结果，写用例的人不写代码。AI 的判断可能抖动，断言可以投多票取多数。
- **确定性 step**：必须精确的检查（当前 URL、某个页面元素、精确文本）不交给 AI 猜。测试开发把它写成一个小函数放进项目的 `steps/` 目录，函数直接查页面对象，结果可复现；写用例的人只需在 `.feature` 里照它登记的说法写一句。
- **导航**：step 文本的**双引号**里写的是 `http://` 或 `https://` 开头的地址时，直接打开这个地址，不问 AI（单引号不触发）。

同一份 `.feature` 可以在本机运行，也可以提交到团队共享的云端后端执行；查询类命令都有 `--json` 输出，AI agent（如 Claude Code、Codex）可以直接驾驭。

## 安装

```bash
uv tool install gherkai                     # 命令行工具（只提交云端 run 的人装这一个即可）
uv tool install 'gherkai[local]'            # 加上本机运行的 Nova Act worker
npm i -g @gherkai/worker-midscene           # 本机运行的 Midscene worker（Node ≥ 22）
uv tool install 'gherkai[deploy-aws]'       # 部署方：部署与维护云端后端
```

需要 Python ≥ 3.13 与 [uv](https://docs.astral.sh/uv/)，以及一个开通了 AgentCore Browser 与所用引擎对应服务（Nova Act 服务 / Bedrock 上的默认模型）的 AWS 账户；在本机运行 Midscene worker 或部署云端后端另需 Node ≥ 22。前置要求与逐步说明见 [用户指南：开始使用](./docs/user-guide/getting-started.md)。

## 30 秒上手

### 让 AI agent 替你做

```bash
gherkai skill install          # 装给 Claude Code；--agent codex 装给 Codex，--agent all 两处都装
```

然后告诉 agent 你要测什么，例如：「用 gherkai 给 `https://www.wikipedia.org` 的搜索功能写一条用例，完整运行一次后把结果汇报给我。」agent 会写 `.feature`、先做用例预检再运行、读失败证据、收窄范围后重试并汇报。

### 自己敲命令

```bash
gherkai plan features/wikipedia_generic.feature       # 用例预检：分组、引擎路由、每一步走 AI 还是确定性；零费用
gherkai run  features/wikipedia_generic.feature       # 运行；结果落在 reports/<run_id>/（index.html 是入口）
gherkai explain <run_id>                              # 有用例没过：逐步看问了 AI 什么、AI 看见了什么、截图在哪
```

后台运行用 `submit` 提交、`status --wait` 收结果；加 `--backend cloud --prefix <前缀>` 切到团队的云端后端。执行方式与执行后端的四种组合、常用选项与退出码见 [运行测试与查看结果](./docs/user-guide/running-and-results.md)。

## 它是如何工作的

![本机与云端两个后端：命令行读入 .feature，起本机 worker 或提交到云端后端；worker 用你账户里的模型做 AI step 的操作与判定、经 CDP 驱动云端浏览器，浏览器直达公网被测应用或经隧道回本机应用；结果与证据由 explain / status 读回](./docs/diagrams/readme-runtime-topology.svg)

本机后端与云端后端各自把结果落在哪、要什么凭证与权限，见下面三条；判定由哪个模型做出，见下一节的披露表。浏览器会话按用例分组算：同一个分组（`.feature` 里的 `@scope` 标签）的用例串行共享一个云端浏览器会话，写法见 [编写 .feature](./docs/user-guide/writing-features.md)。

- **本机后端**（默认）：worker 是本机子进程，结果落当前目录的 `reports/`。需要本机 AWS 凭证。
- **云端后端**：worker 在部署方建好的 Fargate 上运行，状态落 DynamoDB、结果落 S3；提交完关机也会继续运行到结束。团队成员只需最小的云端权限，见 [部署与维护云端后端](./docs/user-guide/cloud-backend.md)。
- **费用**来自模型调用与云端浏览器会话，按你账户的 AWS 账单计。`plan` 是纯本地的用例预检，不产生费用。

更完整的架构与执行模型见 [`docs/internals/architecture-overview.md`](./docs/internals/architecture-overview.md)。

## 判定由谁做出：底层模型披露

gherkai 自己不含模型，也不接收任何数据。每个 AI step 的操作与判定由下面两个模型完成，全部在**你的 AWS 账户**里的托管服务上运行：Nova Act 在你选的 region；Midscene 默认的 GPT-5.6 经 Bedrock 跨区推理在**美国境内三个 region**（us-east-1 / us-east-2 / us-west-2）处理，浏览器会话与产物仍在你选的 region。发给模型的是 step 文本与被测页面的截图。唯一的第三方是可选的 ngrok：只有用 `--expose-local` 测本机应用时，云端浏览器到你本机应用的流量才经过 ngrok 的隧道。各部件与数据边界见 [开始使用 › AWS 前置](./docs/user-guide/getting-started.md#aws-前置)。

| 引擎           | 模型                                            | 服务            | 版本策略                                                | 怎么看 / 怎么换                                                                                                                                                |
|----------------|-------------------------------------------------|-----------------|---------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Nova Act（默认） | `nova-act-v1.0`                                 | Amazon Nova Act | 固定 GA 版本；换模型只随 gherkai 发版，并在版本说明里点明 | `gherkai doctor` 显示实际模型；环境变量 `NOVA_MODEL_ID` 可换（如 `nova-act-preview`，无支持承诺）                                                                  |
| Midscene       | `us.openai.gpt-5.6-terra`（OpenAI GPT-5.6 Terra） | Amazon Bedrock  | 固定；换模型只随 gherkai 发版，并在版本说明里点明         | `gherkai doctor` 显示实际模型；环境变量 `MIDSCENE_MODEL_ID` 可换成 Bedrock 上 Midscene 支持的其它模型，模型家族一般自动识别，识别不了再设 `MIDSCENE_MODEL_FAMILY` |

判定会随模型变：同一条断言在不同模型版本上可能翻转，所以默认不使用「自动跟随最新」的别名。量级上，一条 5 步左右的 scenario 在 Midscene 默认模型上约 5 美分、换成 `qwen.qwen3-vl-235b-a22b` 约 2 美分（按 2026-09 Bedrock 标价与实测 token 估算，以账单为准）；Nova Act 引擎按 Nova Act 服务计费。**被测 UI 的语言**：Midscene 引擎不限；Nova Act 引擎支持英文 UI，非英文应用请用 `@engine:midscene` 路由。配置方法见 [配置](./docs/user-guide/configuration.md)。

## 文档

| 任务                                                  | 对应文档                                                                                                                     |
|-------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------|
| 安装、前置要求、第一次完整运行                          | [开始使用](./docs/user-guide/getting-started.md)                                                                             |
| 写 `.feature`、写确定性 step                           | [编写 .feature](./docs/user-guide/writing-features.md) · [编写确定性 step](./docs/user-guide/writing-deterministic-steps.md) |
| 四种组合、选项、退出码、结果在哪                         | [运行测试与查看结果](./docs/user-guide/running-and-results.md)                                                               |
| 测只在本机 / 内网可达的应用                           | [测本机或内网里的被测应用](./docs/user-guide/local-app-testing.md)                                                           |
| 部署与维护团队的云端后端                              | [部署与维护云端后端](./docs/user-guide/cloud-backend.md)                                                                     |
| 环境变量与选项总表                                    | [配置](./docs/user-guide/configuration.md)                                                                                   |
| 报错了先看哪                                          | [排错](./docs/user-guide/troubleshooting.md)                                                                                 |
| 上手前的疑问：要不要先部署云端后端、AI 判定能不能当门禁 | [常见问题](./docs/user-guide/faq.md)                                                                                         |
| 每个版本改了什么、升级要做什么                         | [CHANGELOG](./CHANGELOG.md)                                                                                                  |
| 系统内部如何运转                                      | [`docs/internals/`](./docs/internals/README.md)                                                                              |
| 参与开发                                              | [`CONTRIBUTING.md`](./CONTRIBUTING.md)                                                                                       |

全部文档的地图在 [`docs/README.md`](./docs/README.md)。发行包页面：[`gherkai`](https://pypi.org/project/gherkai/) · [`gherkai-worker-novaact`](https://pypi.org/project/gherkai-worker-novaact/) · [`@gherkai/worker-midscene`](https://www.npmjs.com/package/@gherkai/worker-midscene) · [`gherkai-deploy-aws`](https://pypi.org/project/gherkai-deploy-aws/) · 库 [`gherkai-core`](https://pypi.org/project/gherkai-core/) / [`gherkai-runtime`](https://pypi.org/project/gherkai-runtime/)。示例用例在 [`features/`](./features/)。

## 注意

- 运行会产生真实的 AWS 费用（模型调用与云端浏览器会话）。先用 `plan` 做用例预检，再运行。
- 用于生产之前，先用示例用例（`features/` 里的 wikipedia 用例）确认环境与凭证正常。

## 许可证

MIT [LICENSE](./LICENSE)。
