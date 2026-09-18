# 排错

本页回答「报错了先看哪」：`gherkai doctor` 每一行的读法，以及安装与版本、凭证与 region、模型、引擎与判定、确定性 step 加载、云端后端、提交后进度停住、隧道这几类症状各自的原因与处置，还有定位参数不一致、筛选筛成空集、`.feature` 语法错误这类其它以退出码 2 结束的情况。每条命令的完整用法与退出码见[运行测试与查看结果](./running-and-results.md)，环境变量与选项的总表见[配置](./configuration.md)，云端后端的部署与维护见[云端后端](./cloud-backend.md)。

## 先运行 gherkai doctor

```bash
gherkai doctor                    # 只查本机
gherkai doctor --backend cloud --prefix gherkai- --report-dir reports/   # 连带查凭证与云端后端
gherkai doctor --json             # 机读 {ok, checks[]}
```

自检只做读操作：不建浏览器会话、不调模型、不产生 AI 费用。输出每行一个检查项，行首三种标记：

| 标记 | 含义 |
|---|---|
| `✓` | 通过。标「未查」的项也算通过 |
| `✗` | **必修项**没通过 |
| `-` | 可选能力缺失，不影响退出码（例如另一个引擎没装、部署工具链不全） |

退出码规则与 `--json` 每项的字段见[开始使用](./getting-started.md)的「用 doctor 预检」。下表说明每一行在查什么、判 `✗` 时怎么办。

### 各行查什么

| 行 | 何时出现 | 内容与判据 |
|---|---|---|
| `cli.version` | 总是 | CLI 版本与 Python 版本。展示项 |
| `engines.novaact`、`engines.midscene` | 总是 | 该引擎 worker 的拉起命令与来源；找不到时这一行就是该引擎的安装指引。单个引擎缺失只标 `-` |
| `engines.any` | 总是 | 至少一个引擎的 worker 可用（本机运行的前提）。必修；`--backend cloud` 下降为可选，因为云端 worker 在容器里运行 |
| `engines.model.<引擎>` | 该引擎 worker 自述成功时 | 这台机器起 job 时**实际会用**的模型 id，由 worker 自报。展示项 |
| `steps.dir` | 总是 | 解析到的确定性 step 目录。没有 `steps/` 目录是多数项目的常态；`--steps-dir` 或 `GHERKAI_STEPS_DIR` 指的路径不是目录时是必修失败 |
| `steps.load.<引擎>` | 每个可用引擎（`steps.dir` 判 `✗` 时不问自述，本行与 `engines.model.<引擎>` 都不出现） | 该引擎加载到多少条确定性 step（含内建）。有 steps 目录时必修，没有时只是可选 |
| `aws.region` | 云端（region 只剩 profile 配置这一处可取时——`--profile` / `AWS_PROFILE` 指的 profile 读不出来，这一行不出现，失败报在 `aws.identity` 那行） | 落实到的 region。四处都没有 region 时必修失败 |
| `aws.identity` | 总是（云端而 `aws.region` 判 `✗` 时不出现） | 调用者身份。凭证不可用或 profile 名不存在时必修失败；未给云端参数时这一行只标「未查（给 --backend cloud 或 --prefix 才查云端）」 |
| `backend.reachability` | 未给云端参数时，或给了云端参数而 `aws.region`、`aws.identity` 先失败时（两者都通过就没有这一行，下面几行即实际探测结果） | 这一行只交代云端为什么没查：三种情形依次标「未查（同上）」/「未查：region 还没解析出来」/「未查：凭证先过不了」，后两种同时标 `-`——真正的失败在它上面那一行，`backend.*` 其余各行都不出现 |
| `backend.version` | 云端 | 后端版本戳与 CLI 版本比对。本机 CLI 新于后端时必修失败（提交也会被拒）；读版本戳本身失败（凭证、权限、网络）时同样必修失败。后端没有版本戳只提示、不拦，按提示让部署方运行一次 `gherkai deploy` 把戳写上。两侧任一不是正式发行版本（含本机从源码直接运行、取不到自身版本）时跳过比对，只提示、标 `✓` |
| `backend.resources` | 云端 | 两张表、产物桶、cluster、两个引擎的 task 定义、三个 Lambda 是否都在，报告前缀与 `--report-dir` 是否一致。必修 |
| `backend.worker.default` | 云端 | 部署级默认 worker 镜像 variant 指针。缺失或读不到时必修失败，云端这一段自检到此为止：下面三行 `backend.worker.*` 都不出现 |
| `backend.worker.<引擎>` | 云端，且 `backend.worker.default` 通过后 | 该引擎在默认 variant 下解析到的 task 定义 revision。单引擎解析不到只标 `-` |
| `backend.worker.any` | 云端，且 `backend.worker.default` 通过后 | 至少一个引擎解析到 worker 镜像。两个都解析不到时必修失败 |
| `backend.worker.grace` | 云端，且 `backend.worker.default` 通过后 | 本机 worker 自报的收尾宽限与云端为它设的停止宽限比对，只比解析到镜像、且本机装了 worker 的引擎：一个引擎都没解析到镜像时整行标「未查」；解析到了、但本机没装对应 worker 的引擎会被跳过并在行内说明。差距只标 `-`、不影响退出码，这一行会说明云端宽限是否还能调高 |
| `provider.deploy-aws` | 未装部署 extra、装了多个部署 provider、或装了却加载失败时 | 前两种只是说明（部署 extra 只有部署方需要）；**装了却加载失败**是必修失败 |
| `provider.node`、`provider.cdk`、`provider.container-engine` | 部署 provider 可自检时 | Node ≥ 22、`cdk` 或 `npx`、容器引擎能否连上。三项都不是必修项：通过标 `✓`，缺失或连不上只标 `-`，不影响退出码；它们只影响 `gherkai deploy` 与 `gherkai deploy push-worker`，不影响提交与本机运行 |

给 `--backend cloud` 或 `--prefix` 才会查 `aws.*` 与 `backend.*` 两段；`--prefix` 与 `--report-dir` 都要与提交时用的值一致，否则查的是另一套资源。云端两段中途早退不影响 `provider.*` 段，它照常查。自检不查隧道前置。

## 安装与版本

| 症状 | 原因 | 处置 |
|---|---|---|
| 以退出码 2 结束，`引擎 novaact 的 worker 运行时未找到`（或 midscene），后面跟一句装法 | 该引擎的 worker 没装，或不在 PATH 上 | 按报错中给出的安装命令安装：Nova Act 用 `uv tool install 'gherkai[local]'`，Midscene 用 `npm i -g @gherkai/worker-midscene`。用自建 worker 时用 `GHERKAI_WORKER_NOVAACT_CMD` / `GHERKAI_WORKER_MIDSCENE_CMD` 指向它 |
| 以退出码 2 结束，`worker 自述失败，拒绝运行`，末尾提到「worker 与命令行工具版本不一致——两者须同版本安装」 | worker 与 CLI 不是同一个版本 | 把两侧装成同版本：`uv tool upgrade gherkai`；Midscene 侧运行 `npm i -g @gherkai/worker-midscene@<gherkai --version 显示的版本>` |
| `能力自述格式版本是 … 命令行工具认的是 …`、`自述的最短停止宽限不是非负有限数` | 同上，版本不一致的另一种形态 | 同上 |
| `要问的是引擎 X 的 worker，回答的却自称 Y` | `GHERKAI_WORKER_*_CMD` 指到了另一个引擎的 worker | 改正该环境变量，或取消设置改用已安装的 worker |
| Midscene worker 起不来，且 `node --version` 低于 22 | `@gherkai/worker-midscene` 要求 Node ≥ 22 | 把 Node 升到 22 或更高，再重装该包 |
| `plan` 打出「标注降级」 | 某个引擎的 worker 不可用，只影响命中标注 | 不阻塞 `plan`；需要标注时把那个 worker 装上 |

只提交云端 run 的人不必装任何 worker：`--backend cloud` 的 `run` / `submit` 不查本机 worker。

## 凭证与 region

| 症状 | 原因 | 处置 |
|---|---|---|
| `没解析出 region`（自检的 `aws.region` 行），或 worker 启动即报 `AWS_REGION 未设` | `--region`、`AWS_REGION`、`AWS_DEFAULT_REGION`、`--profile` / `AWS_PROFILE` 指的 profile 配置，四处都没有 region | 任选一处设上。缺失时不会替你选一个 region |
| `凭证/region 不可用（--region / AWS_REGION / AWS_DEFAULT_REGION / --profile / AWS_PROFILE）` | 本机凭证链取不到可用凭证，或 `--profile` / `AWS_PROFILE` 给的 profile 名不存在 | 配好 AWS 凭证（profile、环境变量、实例角色皆可），或改正 profile 名。两个引擎都用 IAM 鉴权，不需要 API key |
| 本机运行也报凭证错 | 浏览器与模型都在云端，本机 `run` / `submit` 同样要凭证 | 不需要 AWS 凭证的命令只有 `plan`、`list-engines`、`list-deterministic`、`gherkai skill install`、不带云端参数的 `doctor`，以及本机后端下只读报告目录的 `status` 与 `explain`（`status --wait` 会接着推进这个 run，那时需要凭证） |

## 模型

| 症状 | 原因 | 处置 |
|---|---|---|
| worker 日志或 `explain` 里出现 AWS 的权限被拒、模型不可用一类报错 | 该 region 未开通所用模型，或凭证缺 Bedrock、AgentCore Browser、Nova Act 的权限 | 在该 region 开通模型或补权限。`gherkai doctor` 的 `engines.model.<引擎>` 行显示这台机器实际会用哪个模型 |
| Midscene worker 启动即退，`模型 … 不在已知家族里——无法确定该按哪种模型去驱动浏览器` | `MIDSCENE_MODEL_ID` 换成了识别不出家族的模型 | 设 `MIDSCENE_MODEL_FAMILY` 指明家族（取值见 https://midscenejs.com/model-common-config.html ），或把 `MIDSCENE_MODEL_ID` 换回受支持的模型；默认值是 `us.openai.gpt-5.6-terra` |
| Nova Act 侧报模型不存在或不可用 | `NOVA_MODEL_ID` 覆盖成了该 region 没有的模型 | 取消该环境变量，回到默认的 `nova-act-v1.0` |

## 引擎与判定

| 症状 | 原因 | 处置 |
|---|---|---|
| job 判 `error`，归因是 `timeout`，说明是 `job 超时（>…s）` | 这个 job 的墙钟预算到点（未标 `@timeout` 的 scope 用 `--default-job-timeout`，默认 300 秒） | 给慢的 scope 标 `@timeout:600`，或调高 `--default-job-timeout`；也可以把长流程拆成多个 scope |
| 某一步记 `error` 并标 `(timeout)`，job 级归因为空 | Nova Act 的单次 AI 操作到点（默认 120 秒），不是 job 墙钟到点 | 把这一步的动作写得更细，或调高 `NOVA_ACT_TIMEOUT_S`，见[配置](./configuration.md)。调高 `--default-job-timeout` 对这种超时无效 |
| Nova Act 引擎下，非英文页面上「正文里出现某个中文词」这类文本包含断言系统性判否（同一页面上的英文词仍可靠） | Nova Act 在非英文页面上不适合做这类文本断言，提高投票次数无效 | 按[编写 .feature](./writing-features.md)的「按引擎选写法」选一种改法：改用 Midscene 引擎、把断言改写成页面级语义陈述，或改成确定性 step |
| 同一条 AI 断言两次运行的结论不同 | AI 判定本身会抖动 | 用 `--assertion-votes 3` 运行多次取多数票，或把这条判定改成确定性 step；取值与取舍见[编写 .feature](./writing-features.md)的「投票」 |

判 `error` 的 job 与 step 带一个归因标记：`gherkai status` 与 `run` 的文本输出把它显示成 `(<归因>: <说明>)`，`--json` 输出里它是 `error_type` 字段（机读字段全表见 [`../internals/cli-json-contract.md`](../internals/cli-json-contract.md)）。常见的四种：

| 归因 | 含义与处置 |
|---|---|
| `timeout` | 墙钟预算到点，或 Nova Act 的单次 AI 操作到点。见上表前两行 |
| `network_error` | 网络瞬时故障（建连失败，或中途断网）。原样重新运行通常就能过 |
| `engine_error` | worker 起不来、运行中途崩溃，或干净退出却没交完结果。先看 worker 日志，再用 `gherkai explain <run_id>` 看已有的证据 |
| `guardrail` | Nova Act 的安全护栏拦下了这一步的操作。改写这一步的措辞，或把这条 scenario 标 `@engine:midscene` |

本机运行时的 worker 日志：前台 `run` 直接打在终端里，加 `--quiet` 时落 `<report-dir>/<run_id>/worker.log`；`submit --backend local` 的后台进程把它写进同一目录的 `reconcile.log`。云端运行时的日志位置见下面「云端后端」。

## 确定性 step 加载

任一 step 文件加载失败即拒绝运行。各种加载失败的表现与逐条处置见[编写确定性 step](./writing-deterministic-steps.md)的「加载失败的表现」；下面两种情形不容易归因，单独列出。

| 症状 | 原因 | 处置 |
|---|---|---|
| `引擎 X 的 worker 自述失败，拒绝运行：…`，后面附「常见成因是 steps/ 目录里的文件加载失败，或 worker 与命令行工具版本不一致」 | 这一句同时覆盖两种成因，真因在 worker 自己的报错里 | 先读 worker 那句报错：报错点名了具体文件就修该文件；只有一句解析错误、没有具体原因时，按上面「安装与版本」的版本不一致处理 |
| 写了 `steps/` 却全部走 AI | 目录没被读到，或正则匹配不上 step 文本 | 用 `gherkai list-deterministic --engine <引擎> --steps-dir <目录>` 核对清单，再对照每条的 `example` 改 step 文本 |

## 云端后端

| 症状 | 原因 | 处置 |
|---|---|---|
| cloud 命令以退出码 2 结束，提示「本机 CLI X 新于后端 Y」 | CLI 与后端不是同一版本，新 CLI 写的任务定义不能交给旧后端读 | 请部署方运行 `gherkai deploy` 把后端升级到同版本；也可以临时用 `uvx --from 'gherkai==<后端版本>' gherkai …` 提交，不改动本机安装。没有强行放行的开关。反过来，本机 CLI 旧于后端只提示、不拦截，用 `uv tool upgrade gherkai` 升级本机 CLI |
| 提交以退出码 2 结束，`引擎 X 的 worker variant '…' 解析失败` | 当前 CLI 版本下，该引擎没有这个 variant 的镜像 | 临时改用 `--worker-variant base` 提交（部署方运行过本版本的 `gherkai deploy` 即有）；请部署方补推该 variant 的步骤见[云端后端](./cloud-backend.md)的「worker 镜像 variant」。报错说的是本机 CLI 旧于后端时，先升级 CLI，不要照旧版本推镜像 |
| 提交以退出码 2 结束，提示后端没有默认 worker 镜像 variant 指针 | 这个 prefix 下的后端还没完成过本版本的初始化，或默认指针被清掉 | 请部署方运行一次 `gherkai deploy` 完成初始化；急用时提交方用 `--worker-variant base` 显式指定 |
| `run` / `submit --backend cloud` 以退出码 2 结束，`--backend cloud 资源缺失：<资源>（用 --prefix=… 拼出）不存在`；或自检的 `backend.resources` 标 `✗` | `--prefix` 与部署用的不一致，或该 prefix 下还没部署过 | 用部署方给的 prefix，并确认 region 与账户也是部署时那一套；`--report-dir` 同样要与提交时一致 |
| 自检的 `backend.version` 标 `✗`，`读不到后端版本戳（prefix 配错或后端未部署？）` | 读这个参数本身失败：凭证、权限或网络不通 | 先按上一行核对 prefix 与 region，再确认当前凭证有读 SSM 参数的权限 |
| 云端 job 判 `error`，报告里看不出原因 | 失败发生在容器里 | 先用 `gherkai status <run_id> --backend cloud` 看 job 的 `message`，再用 `gherkai explain <run_id> --backend cloud` 看证据；worker 容器日志在 CloudWatch 日志组 `/<prefix>worker/<引擎>`，默认前缀下即 `/gherkai-worker/novaact` 与 `/gherkai-worker/midscene` |
| 以退出码 2 结束，`--grace 在云端不生效` | 云端的停止宽限由部署方在部署时用 `gherkai deploy --stop-timeout` 设定，运行时给这个选项不生效 | 去掉 `--grace`。`doctor --backend cloud` 的 `backend.worker.grace` 行会比对部署侧设的宽限够不够 |

## 提交后进度停住

`submit` 之后 `status` 长时间停在同一进度、也没有报错，说明后台推进停了：本机后端下是那个后台进程已退出，云端后端下是事件链没有继续。用与 `submit` 相同的定位参数运行 `gherkai status <run_id> --wait`，这条命令既查询也接力，会把这个 run 推到终态。

## 隧道（`--expose-local`）

| 症状 | 原因 | 处置 |
|---|---|---|
| `--expose-local 隧道未就绪：找不到 ngrok 可执行文件` | ngrok 没装，或不在 PATH 上 | 装好 ngrok（https://ngrok.com/download ）并确认 `ngrok version` 能正常执行 |
| `ngrok 隧道未就绪（…s 内拿不到公网 URL）`，提示 authtoken 未配置或无外网 | authtoken 没配，或本机连不上外网 | 运行 `ngrok config add-authtoken <token>`，或设 `NGROK_AUTHTOKEN`；两处任一即可。前置与限制见[测本机应用](./local-app-testing.md) |

`gherkai doctor` 不查隧道前置，隧道问题只会在 `run` / `submit` 起隧道时暴露。隧道特有的其它症状见[测本机应用](./local-app-testing.md)的「常见故障」。

## 其它以退出码 2 结束的错误

| 症状 | 原因 | 处置 |
|---|---|---|
| `未找到 run：<run_id>（--report-dir 是否与 submit 一致？）` | 定位参数与产生这个 run 的那条命令不一致 | 照那条命令逐字对齐 `--backend`、`--report-dir`、`--prefix` |
| `没有 scenario 匹配 …`，随后列出本批全部候选 | `--scope` / `--tags` / `--scenario` 把范围筛成了空集 | 从列出的候选里挑正确的值 |
| `feature 语法错误（gherkin 解析失败，含行:列）` | `.feature` 文件语法有误 | 按报出的行列改；写法见[编写 .feature](./writing-features.md) |

## 仍未定位到原因时

反馈问题时请附上三项信息：`gherkai doctor --json`（带上出问题那一档的参数）、`gherkai --version`、失败 run 的 `gherkai explain <run_id> --json`。问题反馈见 https://github.com/zhiyanliu/gherkai/issues 。
