# 开始使用

本页回答三个问题：装什么、需要哪些 AWS 前置、第一次怎么完整运行。gherkai 把 `.feature` 里的每个 step 交给 AI 引擎，由引擎操作云端浏览器并做出判定；需要精确判定的 step 由确定性 step 代码接管（引擎自带一条判页面地址的，其余由项目自己写，见[编写确定性 step](./writing-deterministic-steps.md)）。各部件的归属见下面的 [AWS 前置](#aws-前置)。本页不讲 `.feature` 的写法（见[编写 .feature](./writing-features.md)）、执行方式与执行后端四种组合的差别与退出码（见[运行测试与查看结果](./running-and-results.md)）、云端后端的部署（见[云端后端](./cloud-backend.md)）、选项与环境变量总表（见[配置](./configuration.md)）、报错处置（见[排错](./troubleshooting.md)）。

## 按角色选安装形态

| 你要做的事 | 角色 | 装什么 | 需要什么凭证 |
|---|---|---|---|
| 写 `.feature`、提交、看结果 | feature 作者（QA） | `gherkai`；要在本机运行再加下面两个 worker | 写用例不需要凭证；运行用例需要的凭证随执行方式与执行后端而不同，见[运行测试与查看结果](./running-and-results.md) |
| 写 `steps/` 里的确定性 step、在本机验证、构建定制 worker 镜像 | 测试开发 | `gherkai[local]` + `@gherkai/worker-midscene` + 容器引擎 | 本机 AWS 凭证；不需要云端写权限，镜像交部署方推 |
| 建立和维护共享的云端后端、推 worker 镜像 | 部署方 | `gherkai[deploy-aws]` + Node ≥ 22 + 容器引擎 | AWS 账号的部署权限（CloudFormation、IAM 建角色与策略并 `PassRole`、ECR、ECS、Lambda、EventBridge、VPC、SSM 等；完整清单见[云端后端](./cloud-backend.md)）；运行用例的凭证同上 |
| 参与 gherkai 本身的开发 | contributor | 克隆仓库 | 见 [`CONTRIBUTING.md`](../../CONTRIBUTING.md) |

一个人可以同时承担多个角色：本机开发时常常自己写被测应用、自己写确定性 step、自己构建镜像。团队分工时按上表拆开。

## 安装

```bash
uv tool install gherkai                       # 命令行本体
uv tool install 'gherkai[local]'              # 本体 + 在本机运行 Nova Act 引擎的 worker
npm i -g @gherkai/worker-midscene             # 在本机运行 Midscene 引擎的 worker（需 Node ≥ 22）
uv tool install 'gherkai[deploy-aws]'         # 部署方：gherkai deploy / destroy（另需 Node ≥ 22 与容器引擎）
uvx gherkai --version                         # 免安装临时运行一次（uvx --from 'gherkai[local]' gherkai run …）
pipx install --python 3.13 --fetch-python missing gherkai   # 不用 uv 时的回落；本项目要 Python ≥ 3.13
```

pipx 那一行的 `--python 3.13` 是必要的：pipx 只在请求了某个版本、而本机又没有它时才下载解释器，不指定版本就会用默认解释器，默认解释器低于 3.13 时安装失败。

Nova Act 的 worker 随 `[local]` extra 装进同一个 Python 环境，Midscene 的 worker 是 Node 包、走 npm。只用 `--backend cloud` 提交的人两个都不用装，worker 运行在云端。`gherkai list-engines` 打印本机检测到哪个引擎可用，缺的那个原地给出安装命令。用 pipx 或 uvx 装 extra 时，包名写成 `'gherkai[local]'`。

升级：`uv tool upgrade gherkai`（安装时带的 extra 会沿用）；Midscene worker 另外执行 `npm i -g @gherkai/worker-midscene@<CLI 版本>`。CLI 与 worker 要求同版本，CLI 与已部署的云端后端也要求同版本，不一致时的处置见[排错](./troubleshooting.md)。

各发行包的页面：[`gherkai`](https://pypi.org/project/gherkai/)、[`gherkai-worker-novaact`](https://pypi.org/project/gherkai-worker-novaact/)、[`@gherkai/worker-midscene`](https://www.npmjs.com/package/@gherkai/worker-midscene)、[`gherkai-deploy-aws`](https://pypi.org/project/gherkai-deploy-aws/)。

## 运行环境要求

| 组件 | 要求 | 什么时候需要 |
|---|---|---|
| Python | ≥ 3.13，配 [uv](https://docs.astral.sh/uv/) | 命令行本体与 Nova Act worker |
| Node.js | ≥ 22 | 在本机运行 Midscene worker；`gherkai deploy` |
| 容器引擎 | docker | `gherkai deploy`（同步官方 worker 基础镜像）；构建与推送定制 worker 镜像 |
| [ngrok](https://ngrok.com/download) | 可执行文件在 PATH 上 + authtoken（免费账号即可） | 仅用 `--expose-local` 测本机可达的应用时，见[测本机应用](./local-app-testing.md) |

## AWS 前置

![你的机器与 AWS 账户各持有哪些部件：命令行与本机 worker 在你的机器上，云端 worker、浏览器会话与模型服务在 AWS 账户里，被测应用在两者之外](../diagrams/getting-started-component-ownership.svg)

图注：**本机后端** = `--backend local`（默认），**云端后端** = `--backend cloud`。图上两个后端的差别只有一处——worker 在哪运行：云端后端运行的是同样两个引擎，对浏览器会话与模型服务做同样的事。图上的「本机 worker」按引擎分开装，Nova Act 与 Midscene 各一份，见上面的[安装](#安装)。账户归属按后端不同：本机后端用你自己的账户，云端后端用部署方建后端的那个账户（可能是团队共用）；四种组合、结果落点、权限，以及哪种组合记到谁的账户，见[运行测试与查看结果](./running-and-results.md)。要开通哪些服务、模型在哪个 region 处理见下表。确定性 step 代码不在图上：本机后端由 worker 从本机目录加载，云端后端来自 worker 镜像，见[编写确定性 step](./writing-deterministic-steps.md)。被测应用不在公网时的隧道拓扑见[测本机应用](./local-app-testing.md)。

- **凭证**走本机 AWS 默认凭证链：profile、环境变量、实例角色都可以，不需要额外的 API key。用 `--profile` 或 `AWS_PROFILE` 指定 profile。
- **region 必须有出处**，按此顺序解析：`--region` > `AWS_REGION` > `AWS_DEFAULT_REGION` > profile 配置里的 region。四处都没有时不会自动补一个 region：命令照常开始执行，引擎会在启动时因缺 region 报错，该 scope 判为 error。
- 当前验证过的 region 是 `us-east-1`。换其它 region 之前，先确认下表三项服务与你要用的模型在该 region 都可用：`gherkai doctor --backend cloud --prefix <前缀>` 报出凭证与 region 的解析结果，模型与服务的可用性在 AWS 控制台确认。
- 该 region 下的账号需要能用以下服务与模型：

| 你要用的 | 需要开通 | 说明 |
|---|---|---|
| Midscene 引擎 | Amazon Bedrock 上的模型 `us.openai.gpt-5.6-terra` | 默认模型。它经跨区推理在美国境内三个 region（us-east-1 / us-east-2 / us-west-2）处理，浏览器会话与产物仍在你选的 region。环境变量 `MIDSCENE_MODEL_ID` 可换成 Bedrock 上 Midscene 支持的其它模型 |
| Nova Act 引擎 | Amazon Nova Act 服务 + 模型 `nova-act-v1.0` | 默认固定该版本，环境变量 `NOVA_MODEL_ID` 可指定其它模型；所需的 workflow definition 首次运行时自动创建 |
| 两个引擎都要 | AgentCore Browser（`bedrock-agentcore`） | 每个 scope 一个会话 |

- 在本机运行（`--backend local`）同样需要 AWS 凭证：浏览器会话与模型都在云端，本机只运行 worker 进程。纯本地、不需要凭证的命令：`plan`、`list-engines`、`list-deterministic`、`skill install`，不带云端参数的 `doctor`，以及本机后端下只读本地报告目录的 `explain` 与 `status`（`status --wait` 会在本机接着把这个 run 推完，那时需要凭证）。
- 实际运行产生 AWS 费用（模型调用 + 云端浏览器会话），以 AWS 账单为准。费用量级、以及哪种组合记到谁的账户，见[运行测试与查看结果](./running-and-results.md)。
- 用 `--backend cloud` 之前，需要有人先用 `gherkai deploy` 把云端后端建好，见[云端后端](./cloud-backend.md)。

## 用 doctor 自检

`gherkai doctor` 是只读自检：不建浏览器会话、不调模型，不产生模型费用。

```bash
gherkai doctor                                      # 只查本机
gherkai doctor --backend cloud --prefix gherkai-    # 连带查凭证、region 与云端后端（前缀与部署时一致）
```

输出每行一个检查项。全部必修项通过退 `0`，任一必修项未通过退 `2`。加 `--json` 输出 `{ok, checks[]}`，每项含 `section` / `name` / `ok` / `required` / `detail`，脚本按 `required && !ok` 挑出阻塞项。

只查本机的一次实际输出（这台机器没装 Midscene worker，容器引擎的 daemon 也没起）：

```text
✓ cli.version: gherkai <版本>，Python 3.13.14
- engines.midscene: 引擎 midscene 的 worker 运行时未找到。装法：npm i -g @gherkai/worker-midscene（需 Node ≥ 22）……
✓ engines.novaact: /path/to/python3 -m gherkai_worker_novaact（同 venv 模块 gherkai_worker_novaact）
✓ engines.any: 至少一个引擎的 worker 可用
✓ engines.model.novaact: 模型 nova-act-v1.0（本机 worker 自报）
✓ steps.dir: 无 steps/ 目录：只有内建确定性 step（多数项目的常态）
✓ steps.load.novaact: 1 条确定性 step（含内建）；无 steps/ 目录，仅内建
✓ aws.identity: 未查（给 --backend cloud 或 --prefix 才查云端）
✓ backend.reachability: 未查（同上）
✓ provider.node: node /path/to/node
✓ provider.cdk: /path/to/cdk
- provider.container-engine: `docker` 在 PATH 上但连不上 daemon……

部署工具链有缺口（provider 段）：只影响 gherkai deploy / push-worker，不影响提交与本机运行

自检通过
```

`steps.load.*` 的条数含引擎自带的那一条，所以没有 `steps/` 目录时它也不为零。每一行查什么、`✗` 与 `-` 分别怎么处置，见[排错](./troubleshooting.md)。

## 上手路径一：交给 AI agent

装好命令行后，把随包发行的 agent skill 装进项目，让 Claude Code、Codex 这类 AI agent 替你写用例、执行用例、读失败证据、收窄后重新运行并汇报：

```bash
gherkai skill install                   # 装给 Claude Code：<项目>/.claude/skills/gherkai/
gherkai skill install --agent codex     # 装给 Codex：<项目>/.agents/skills/gherkai/；--agent all 两处都装
gherkai skill install --dir <项目根>     # 指定项目根（默认当前目录）
gherkai skill install --global          # 装到用户级目录，对你所有项目生效
gherkai skill install --print           # 只把正文打到标准输出，不安装
```

- 装进去的是与本机 CLI 同版本的那一份。重装是整目录替换，不留上一版残余；目标目录里如果是别的内容（不是本命令装的），命令会停下并退 `2`，不覆盖。
- 安装后会询问一次是否把提示行写进项目的 `CLAUDE.md` / `AGENTS.md`。用 `--pointer yes|no` 免交互；非交互环境默认不写，只打印那一行供你自己粘贴。
- 没装命令行也能取同一份 skill，版本自己指定：

```bash
npx skills add https://github.com/zhiyanliu/gherkai/tree/v<版本>/cli/gherkai_cli/skills/gherkai --agent claude-code
```

这条路不经命令行，版本要自己指定：URL 里的 `v<版本>` 填你要跟随的 CLI 版本（tag 或 commit 均可，带斜杠的分支名不行——安装器在第一个斜杠处切断 ref）；写 `HEAD` 拿的是默认分支最新，可能比你装的命令行新。它装出的目录不带版本标记：之后改用 `gherkai skill install`，命令会因为目标目录不是它装的而停下并退 `2`，先把该目录移走或删掉再装。Codex 的用户级落点两条路也不同，`npx` 写 `~/.codex/skills/`。

装完直接告诉 agent 要测什么，例如：

> 用 gherkai 给结算流程写一条用例：打开 https://shop.example.com ，把一件商品加入购物车，检查购物车里有一件商品。先 plan，再在本机运行一次，没过就把证据给我。

agent 会自己做用例预检、实际运行前把本次运行的规模报给你、失败时先读证据，再收窄重新运行。

## 上手路径二：自己敲命令

分四步完整运行第一条用例。装包上手时手上还没有 `.feature`，先在项目里存一条最小用例，存成 `features/smoke.feature`：

```gherkin
Feature: 冒烟

  Scenario: 打开示例站点
    Given 打开 "https://example.com"
    Then "页面包含 Example Domain 字样"
```

仓库里另有一组示例用例在 [`features/`](../../features/)，克隆仓库、或把其中的文件复制进你的项目就能用。`.feature` 的完整写法见[编写 .feature](./writing-features.md)。

```bash
# ① 用例预检：看分组与每步的派发预期，不连云端、不产生费用
gherkai plan features/smoke.feature

# ② 实际运行：产生模型调用与云端浏览器会话费用
AWS_REGION=us-east-1 gherkai run features/smoke.feature

# ③ 看结果：报告默认落在 reports/<run_id>/，用浏览器打开其中的 index.html
ls reports/<run_id>/

# ④ 有用例没过时读证据
gherkai explain <run_id>
```

`plan` 的输出形如：

```text
===== plan（用例预检，未执行）=====
  1 job(scope)  ·  1 scenario  ·  default_engine=novaact
  job scope='features/smoke.feature:3' (name='打开示例站点') engine=novaact
    scenario 'features/smoke.feature:3'  (2 step)
      [0] Given 打开 "https://example.com"
      [1] Then "页面包含 Example Domain 字样"
```

它给出本次运行会开几个 job（每个 job 对应一个云端浏览器会话）、各自用哪个引擎、每一步走确定性 step 还是走 AI。**先 plan 后执行**：`plan` 零费用，能在实际运行产生费用之前暴露写法与配置问题。

用 `@engine:` tag 指定了引擎的用例，在本机运行要求该引擎的 worker 已安装，否则 `run` 停下并退 `2`。仓库示例里的 `engine_routing.feature` 两个 scenario 分别指定两个引擎，只装了一个引擎时改用未标 `@engine` 的用例，或用 `--scope` 只运行其中一个。

`run` 结束时打印判定汇总与报告位置，退出码即判定结果。`explain` 只读证据、从不改变判定：它按书写顺序列出每一步，把没过的那一步展开成「问了 AI 什么、AI 看见了什么、为什么这么判、截图在哪」。退出码的含义、`submit` + `status` 的后台执行方式、本机与云端两个后端的差别、报告与证据的完整布局，都在[运行测试与查看结果](./running-and-results.md)。

## 下一步

| 想做什么 | 去读 |
|---|---|
| 写 `.feature`，选引擎、scope 与超时 | [编写 .feature](./writing-features.md) |
| 写自己的确定性 step | [编写确定性 step](./writing-deterministic-steps.md) |
| 选执行方式与执行后端、读退出码、找报告与证据 | [运行测试与查看结果](./running-and-results.md) |
| 测只在本机或内网可达的应用 | [测本机应用](./local-app-testing.md) |
| 部署团队共享的云端后端 | [云端后端](./cloud-backend.md) |
| 查某个选项或环境变量 | [配置](./configuration.md) |
| 报错了 | [排错](./troubleshooting.md) |
