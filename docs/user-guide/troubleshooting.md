# 排错

报错后的排查顺序：先按下面的读法看 `gherkai doctor` 的每一行；再按症状分类查原因与处置，分类有安装与版本、凭证与 region、模型、引擎与判定、确定性 step 加载、云端后端、提交后进度停住、隧道、项目配置文件与设备目标；定位参数不一致、筛选筛成空集、`.feature` 语法错误这类其它以退出码 2 结束的情况另列。每条命令的完整用法与退出码见[运行测试与查看结果](./running-and-results.md)，环境变量与选项的总表见[配置](./configuration.md)，云端后端的部署与维护见[云端后端](./cloud-backend.md)。

## 先运行 gherkai doctor

```bash
gherkai doctor                    # 只查本机
gherkai doctor --backend cloud --prefix gherkai- --report-dir reports/   # 连带查凭证与云端后端
gherkai doctor --json             # 机读 {ok, checks[]}
```

自检只做读操作：不建浏览器会话、不调模型，不产生模型费用。输出是一张表，每个检查项一行，「结果」列有三种标记：

| 标记 | 含义 |
|---|---|
| `✓` | 通过。标「未查」的项也算通过 |
| `✗` | **必修项**没通过 |
| `-` | 可选能力缺失，不影响退出码（例如另一个引擎没装、部署工具链不全） |

退出码规则与 `--json` 每项的字段见[开始使用](./getting-started.md)的「用 doctor 自检」。下表说明每一行在查什么、判 `✗` 时怎么办。

### 各行查什么

| 行 | 何时出现 | 内容与判据 |
|---|---|---|
| `cli.version` | 总是 | CLI 版本与 Python 版本。展示项 |
| `config.file` | 总是 | 本次加载的项目配置文件路径；没有加载时注明按 `--config`、环境变量 `GHERKAI_CONFIG`、当前目录的 `gherkai.toml` 依次查找。展示项 |
| `engines.novaact`、`engines.midscene` | 总是 | 该引擎 worker 的拉起命令与来源；找不到时这一行就是该引擎的安装指引。单个引擎缺失只标 `-` |
| `engines.any` | 总是 | 至少一个引擎的 worker 可用（本机运行的前提）。必修；`--backend cloud` 下降为可选，因为云端 worker 在容器里运行 |
| `engines.model.<引擎>` | 该引擎 worker 自述成功时 | 这台机器起 job 时**实际会用**的模型 id，由 worker 自报。展示项 |
| `engines.targets.<引擎>` | 该引擎 worker 自述成功时 | 该引擎 worker 支持的测试目标（桌面网页、Android 网页这类名称），带会话上限的目标附分钟数；由 worker 自报，不支持设备不算失败。展示项；两引擎的能力矩阵见 [`engines.md`](./engines.md) |
| `steps.dir` | 总是 | 解析到的确定性 step 目录。没有 `steps/` 目录是多数项目的常态；`--steps-dir`、`GHERKAI_STEPS_DIR` 或配置文件的 `steps-dir` 指的路径不是目录时是必修失败 |
| `steps.load.<引擎>` | 每个可用引擎（`steps.dir` 判 `✗` 时不问自述，本行与 `engines.model.<引擎>`、`engines.targets.<引擎>` 都不出现） | 该引擎加载到多少条确定性 step（含内建）。有 steps 目录时必修，没有时只是可选 |
| `aws.region` | 云端（region 只剩 profile 配置这一处可取时——`--profile` / `AWS_PROFILE` / 配置文件 `[common]` 的 `profile` 指的 profile 读不出来，这一行不出现，失败报在 `aws.identity` 那行） | 落实到的 region。五处都没有 region 时必修失败 |
| `aws.identity` | 总是（云端而 `aws.region` 判 `✗` 时不出现） | 调用者身份。凭证不可用或 profile 名不存在时必修失败；未给云端参数时这一行只标「未查（给 --backend cloud 或 --prefix 才查云端）」 |
| `backend.reachability` | 未给云端参数时，或给了云端参数而 `aws.region`、`aws.identity` 先失败时（两者都通过就没有这一行，下面几行即实际探测结果） | 这一行只交代云端为什么没查：三种情形依次标「未查（同上）」/「未查：region 还没解析出来」/「未查：凭证先过不了」，后两种同时标 `-`——真正的失败在它上面那一行，`backend.*` 其余各行都不出现 |
| `backend.version` | 云端 | 后端版本戳与 CLI 版本比对。本机 CLI 新于后端时必修失败（提交也会被拒）；读版本戳本身失败（凭证、权限、网络）时同样必修失败。后端没有版本戳只提示、不拦，按提示让部署方运行一次 `gherkai deploy` 把戳写上。两侧任一不是正式发行版本（含本机从源码直接运行、取不到自身版本）时跳过比对，只提示、标 `✓` |
| `backend.resources` | 云端 | 两张表、产物桶、cluster、两个引擎的 task 定义、三个 Lambda 是否都在，报告前缀与 `--report-dir` 是否一致。必修 |
| `backend.worker.default` | 云端 | 部署级默认 worker 镜像 variant 指针。缺失或读不到时必修失败，下面三行 `backend.worker.*` 都不出现；设备支持的两行照常检查 |
| `backend.worker.<引擎>` | 云端，且 `backend.worker.default` 通过后 | 该引擎在默认 variant 下解析到的 task 定义 revision。单引擎解析不到只标 `-` |
| `backend.worker.any` | 云端，且 `backend.worker.default` 通过后 | 至少一个引擎解析到 worker 镜像。两个都解析不到时必修失败 |
| `backend.worker.grace` | 云端，且 `backend.worker.default` 通过后 | 本机 worker 自报的收尾宽限与云端为它设的停止宽限比对，只比解析到镜像、且本机装了 worker 的引擎：一个引擎都没解析到镜像时整行标「未查」；解析到了、但本机没装对应 worker 的引擎会被跳过并在行内说明。差距只标 `-`、不影响退出码，这一行会说明云端宽限是否还能调高 |
| `backend.devices.project` | 云端 | 这套后端是否启用了设备支持，即部署时建立的 Device Farm 项目 ARN 是否记在 SSM 里。没有时标 `-` 并提示「部署未启用设备支持」：不测设备的团队可以忽略；要测设备时，请部署方用有 Device Farm 权限的凭证重新运行 `gherkai deploy`。读这个参数本身失败时同样只标 `-`，行内给出原因。不影响退出码 |
| `backend.devices.sessions` | 云端，且 `backend.devices.project` 读到项目后 | 项目里还没结束的远程访问会话（含排队中的），每条带控制台链接与停止命令 `aws devicefarm stop-remote-access-session --region us-west-2 --arn <会话 ARN>`；doctor 使用了 profile（来自 `--profile`、`AWS_PROFILE` 或配置文件 `[common]` 的 `profile`）时，命令末尾还带同一个 `--profile <名称>`。没有时标 `✓`；有时标 `-`：正在执行的 run 也有会话，停止前先确认没有 run 在使用它，没有 run 使用的会话会继续计费并占用设备，最长到 Device Farm 的 150 分钟上限。列举需要 us-west-2 上对这个项目的 `devicefarm:ListRemoteAccessSessions` 权限，缺这项权限时这一行说明缺什么，遇到限流、网络等其他错误时同样只标 `-`、行内给出原因与下一步；停止需要 `devicefarm:StopRemoteAccessSession`，只提交 run 的成员的最小权限里没有这一项，请有该权限的人停止。表格在窄终端里会把长链接与命令折成多行，`doctor --json` 的 `detail` 里是完整的一行。不影响退出码 |
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
| Midscene worker 无法启动，且 `node --version` 低于 22 | `@gherkai/worker-midscene` 要求 Node ≥ 22 | 把 Node 升到 22 或更高，再重装该包 |
| `plan` 打出「标注降级」 | 某个引擎的 worker 不可用，只影响命中标注 | 不阻塞 `plan`；需要标注时把那个 worker 装上 |

只提交云端 run 的人不必装任何 worker：`--backend cloud` 的 `run` / `submit` 不查本机 worker。

## 凭证与 region

| 症状 | 原因 | 处置 |
|---|---|---|
| `没解析出 region`（自检的 `aws.region` 行），或 worker 启动即报 `AWS_REGION 未设` | `--region`、`AWS_REGION`、`AWS_DEFAULT_REGION`、配置文件 `[common]` 的 `region`、`--profile` / `AWS_PROFILE`（或配置文件的 `profile`）指的 profile 配置，五处都没有 region | 任选一处设上。缺失时不会替你选一个 region |
| `凭证/region 不可用（--region / AWS_REGION / AWS_DEFAULT_REGION / 配置文件 [common] region、--profile / AWS_PROFILE / 配置文件 [common] profile）` | 本机凭证链取不到可用凭证，或 `--profile` / `AWS_PROFILE` / 配置文件 `[common]` 的 `profile` 给的 profile 名不存在 | 配好 AWS 凭证（profile、环境变量、实例角色皆可），或改正 profile 名。两个引擎都用 IAM 鉴权，不需要 API key |
| 本机运行也报凭证错 | 浏览器与模型都在云端，本机 `run` / `submit` 同样要凭证 | 配好凭证。不需要 AWS 凭证的命令只有几条，清单见[开始使用](./getting-started.md#aws-前置)；其中 `status --wait` 会接着推进这个 run，那时需要凭证 |

## 模型

| 症状 | 原因 | 处置 |
|---|---|---|
| worker 日志或 `explain` 里出现 AWS 的权限被拒、模型不可用一类报错 | 该 region 未开通所用模型，或凭证缺 Bedrock、AgentCore Browser、Nova Act 的权限 | 在该 region 开通模型或补权限。`gherkai doctor` 的 `engines.model.<引擎>` 行显示这台机器实际会用哪个模型 |
| Midscene worker 启动即退，`模型 … 不在已知家族里——无法确定该按哪种模型去驱动浏览器` | `MIDSCENE_MODEL_ID` 换成了识别不出家族的模型 | 设 `MIDSCENE_MODEL_FAMILY` 指明家族（取值见 https://midscenejs.com/model-common-config.html ），或把 `MIDSCENE_MODEL_ID` 换回受支持的模型；默认值是 `us.openai.gpt-5.6-terra` |
| Nova Act 侧报模型不存在或不可用 | `NOVA_MODEL_ID` 覆盖成了该 region 没有的模型 | 取消该环境变量，回到默认的 `nova-act-v1.0` |

## 引擎与判定

| 症状 | 原因 | 处置 |
|---|---|---|
| job 判 `error`，归因是 `timeout`，说明是 `job 超时（预算 …s，已中止）` | 这个 job 的墙钟预算到点（未标 `@timeout` 的 scope 用 `--default-job-timeout`，桌面 scope 默认 300 秒，设备 scope 默认为获取设备的预算加 900 秒） | 给慢的 scope 标 `@timeout:600`，或调高 `--default-job-timeout`；也可以把长流程拆成多个 scope |
| 某一步记 `error` 并标 `(timeout)`，job 级归因为空 | Nova Act 的单次 AI 操作到点（默认 120 秒），不是 job 墙钟到点 | 把这一步的动作写得更细，或调高 `NOVA_ACT_TIMEOUT_S`，见[配置](./configuration.md)。调高 `--default-job-timeout` 对这种超时无效 |
| Nova Act 引擎下，非英文页面上「正文里出现某个中文词」这类文本包含断言系统性判否（同一页面上的英文词仍可靠） | Nova Act 在非英文页面上不适合做这类文本断言，提高投票次数无效 | 按[编写 .feature](./writing-features.md)的「按引擎选写法」选一种改法：改用 Midscene 引擎、把断言改写成页面级语义陈述，或改成确定性 step |
| 同一条 AI 断言两次运行的结论不同 | AI 判定本身会抖动 | 用 `--assertion-votes 3` 运行多次取多数票，或把这条判定改成确定性 step；取值与取舍见[编写 .feature](./writing-features.md)的「投票」 |

判 `error` 的 job 与 step 带一个归因标记：`gherkai status` 与 `run` 的文本输出把它显示成 `(<归因>: <说明>)`，`--json` 输出里它是 `error_type` 字段（机读字段全表见 [`../internals/cli-json-contract.md`](../internals/cli-json-contract.md)）。常见的四种：

| 归因 | 含义与处置 |
|---|---|
| `timeout` | job 墙钟预算到点，或 Nova Act 的单次 AI 操作到点。见上表前两行 |
| `network_error` | 网络瞬时故障（建连失败，或中途断网）。原样重新运行通常就能过 |
| `engine_error` | worker 无法启动、运行中途崩溃，或干净退出却没交完结果。先看 worker 日志，再用 `gherkai explain <run_id>` 看已有的证据 |
| `guardrail` | Nova Act 的安全护栏拦下了这一步的操作。改写这一步的措辞，或把这条 scenario 标 `@engine:midscene` |

本机运行时的 worker 日志：前台 `run` 直接打在终端里，每行带 `[worker <scope_id>:out]` 或 `[worker <scope_id>:err]` 前缀，前缀的颜色只用来区分来源 scope（按 job 启动顺序分配，不用红绿），不表示严重程度；加 `--quiet` 时落 `<report-dir>/<run_id>/worker.log`；`submit --backend local` 的后台进程把它写进同一目录的 `reconcile.log`。云端运行时的日志位置见下面「云端后端」。

## 确定性 step 加载

任一 step 文件加载失败即拒绝运行。各种加载失败的表现与逐条处置见[编写确定性 step](./writing-deterministic-steps.md)的「加载失败的表现」；下面两种情形不容易归因，单独列出。

| 症状 | 原因 | 处置 |
|---|---|---|
| `引擎 X 的 worker 自述失败，拒绝运行：…`，后面附「常见成因是 steps/ 目录里的文件加载失败，或 worker 与命令行工具版本不一致」 | 这一句同时覆盖两种成因，真因在 worker 自己的报错里 | 先读 worker 那句报错：报错点名了具体文件就修该文件；只有一句解析错误、没有具体原因时，按上面「安装与版本」的版本不一致处理 |
| 写了 `steps/` 却全部走 AI | 目录没被读到；Midscene 侧文件用了 `.mts` / `.mjs` 以外的扩展名（被跳过，不报错）；或正则匹配不上 step 文本 | 确认 `--steps-dir` 指对、扩展名改成 `.mts` 或 `.mjs`，再用 `gherkai list-deterministic --engine <引擎> --steps-dir <目录>` 核对清单，再对照每条的 `example` 改 step 文本 |

## 云端后端

| 症状 | 原因 | 处置 |
|---|---|---|
| cloud 命令以退出码 2 结束，提示「本机 CLI X 新于后端 Y」 | CLI 与后端不是同一版本，新 CLI 写的任务定义不能交给旧后端读 | 请部署方运行 `gherkai deploy` 把后端升级到同版本；也可以临时用 `uvx --from 'gherkai==<后端版本>' gherkai …` 提交，不改动本机安装。没有强行放行的开关。反过来，本机 CLI 旧于后端只提示、不拦截，用 `uv tool upgrade gherkai` 升级本机 CLI |
| 提交以退出码 2 结束，`引擎 X 的 worker variant '…' 解析失败` | 当前 CLI 版本下，该引擎没有这个 variant 的镜像 | 临时改用 `--worker-variant base` 提交（部署方运行过本版本的 `gherkai deploy` 即有）；请部署方补推该 variant 的步骤见[云端后端](./cloud-backend.md)的「worker 镜像 variant」。报错说的是本机 CLI 旧于后端时，先升级 CLI，不要照旧版本推镜像 |
| 提交以退出码 2 结束，提示后端没有默认 worker 镜像 variant 指针 | 这个 prefix 下的后端还没完成过本版本的初始化，或默认指针被清掉 | 请部署方运行一次 `gherkai deploy` 完成初始化；急用时提交者用 `--worker-variant base` 显式指定 |
| `run` / `submit --backend cloud` 以退出码 2 结束，`--backend cloud 资源缺失：<资源>（用 --prefix=… 拼出）不存在`；或自检的 `backend.resources` 标 `✗` | `--prefix` 与部署用的不一致，或该 prefix 下还没部署过 | 用部署方给的 prefix，并确认 region 与账户也是部署时那一套；`--report-dir` 同样要与提交时一致 |
| 自检的 `backend.version` 标 `✗`，`读不到后端版本戳（prefix 配错或后端未部署？）` | 读这个参数本身失败：凭证、权限或网络不通 | 先按上一行核对 prefix 与 region，再确认当前凭证有读 SSM 参数的权限 |
| 云端 job 判 `error`，报告里看不出原因 | 失败发生在容器里 | 先用 `gherkai status <run_id> --backend cloud` 看 job 的 `message`，再用 `gherkai explain <run_id> --backend cloud` 看证据；worker 容器日志在 CloudWatch 日志组 `/<prefix>worker/<引擎>`，默认前缀下即 `/gherkai-worker/novaact` 与 `/gherkai-worker/midscene` |
| `run` / `submit --backend cloud` 以退出码 2 结束，`后端没有版本戳 … 带设备目标或使用 --expose-local 的 run 不能提交到它` | 这个后端部署早于本版本、从未升级，它丢得掉这类 run 的关键信息 | 请部署方运行 `gherkai deploy` 升级后端；没有使用 `--expose-local` 的桌面 run 不受影响 |
| 提交以退出码 2 结束，`部署未启用设备支持` | 部署时没有建立 Device Farm 项目：部署版本早于本功能，或部署方没有 Device Farm 权限 | 请部署方用有 Device Farm 权限的凭证重新运行 `gherkai deploy`；之后 `doctor --backend cloud` 的 `backend.devices.project` 行应显示项目 ARN |
| 以退出码 2 结束，`--grace 在云端不生效` | 云端的停止宽限由部署方在部署时用 `gherkai deploy --stop-timeout` 设定，运行时给这个选项不生效 | 去掉 `--grace`。`doctor --backend cloud` 的 `backend.worker.grace` 行会比对部署侧设的宽限够不够 |

## 提交后进度停住

`submit` 之后 `status` 长时间停在同一进度、也没有报错，说明后台推进停了：本机后端下是那个后台进程已退出，云端后端下是事件链没有继续。用与 `submit` 相同的定位参数运行 `gherkai status <run_id> --wait`：后台推进停止或卡住时，这条查询命令会接着把这个 run 推进到终态。

## 隧道（`--expose-local`）

| 症状 | 原因 | 处置 |
|---|---|---|
| `--expose-local 隧道未就绪：找不到 ngrok 可执行文件` | ngrok 没装，或不在 PATH 上 | 装好 ngrok（https://ngrok.com/download ）并确认 `ngrok version` 能正常执行 |
| `ngrok 隧道未就绪（…s 内拿不到公网 URL）`，提示 authtoken 未配置或无外网 | authtoken 没配，或本机连不上外网 | 运行 `ngrok config add-authtoken <token>`，或设 `NGROK_AUTHTOKEN`；两处任一即可。前置与限制见[测本机应用](./local-app-testing.md) |
| 本机后端 `--expose-local` 以退出码 2 结束，提示「worker 不支持本机应用测试需要的会话预热」 | 引擎 worker 比命令行工具旧，不会在隧道上做会话预热 | 把 worker 与命令行工具装成同一个版本（`uv tool upgrade gherkai`；Midscene 侧 `npm i -g @gherkai/worker-midscene@<同版本>`） |
| run 里每个 scope 都没执行任何 step，job 的消息以「隧道会话预热」或「后端未传递会话预热地址」开头 | 隧道的会话预热失败：令牌不被接受、会话 cookie 未通过校验、隧道已拆或浏览器到隧道入口的网络不通、云端后端旧于命令行工具 | 按消息处置，见[测本机应用](./local-app-testing.md)的「常见故障」 |

`gherkai doctor` 不查隧道前置，隧道问题只会在 `run` / `submit` 起隧道时暴露。隧道特有的其它症状见[测本机应用](./local-app-testing.md)的「常见故障」。

## 项目配置文件与设备目标

| 症状 | 原因 | 处置 |
|---|---|---|
| `配置文件 … 里有不认识的键 …`，随后列出可用的键 | 键名拼错，或把只影响本次调用的选项写进了文件 | 键名是选项长名去掉 `--`，可用键见[配置](./configuration.md)「项目配置文件」；只影响本次调用的选项在命令行上给 |
| `配置文件 … 不是合法的 TOML：…` | 文件语法错 | 按报出的行列改 |
| `… os-version = 18.6 要写成字符串、加引号` | 版本号写成了数字，会被当成浮点数读、末尾的 0 丢失 | 写成 `os-version = "18.6"` |
| `这个 run 里有在 Android 设备上执行的 scope，但没有指定用哪台设备` | 该平台没有任何来源给出设备 | 在 `gherkai.toml` 的 `[devices.android]` 给 `arn` 或 `os-version`，或用 `--android-device-arn`（iOS 同理）；`plan` 对此只警告 |
| `… 给的设备 ARN 形态不对：这看起来是项目 ARN、不是设备 ARN` | 把别的 ARN 贴进了设备 ARN 的位置 | 设备 ARN 形如 `arn:aws:devicefarm:<区域>::device:<设备 id>`，账号段为空；项目 ARN 形如 `arn:aws:devicefarm:<区域>:<账号>:project:<项目 id>` |
| `本机运行设备 scope 需要一个 Device Farm 项目，但没有指定` / `需要一个放安装包的 S3 桶，但没有指定` | 本机后端驱动真机要自己给项目与应用桶 | 在 `[devices]` 给 `project-arn` / `app-bucket`，或用 `--device-farm-project-arn` / `--app-bucket`、环境变量 `GHERKAI_DEVICE_FARM_PROJECT_ARN` / `GHERKAI_APP_BUCKET` |
| `注意：Device Farm 项目 … 属于账号 X，当前凭证属于账号 Y` | 项目 ARN 与当前凭证不在同一账号，多半是复制了别的环境的 ARN | 换对的项目或凭证；这条只警告不拦 |
| `安装包不存在：…（配置文件 [apps.<别名>.<平台>] 的 file）` | `file` 指向的文件不在 | 路径相对配置文件所在目录，核对路径与构建产物 |
| 云端 run 的 `status` 为 `error`、状态行下有一行 `message=…` 说提交记录由更新或更早版本写出、不完整、或没有记 worker 镜像版本，没有任何 job 开始过 | 后端读到了它不能执行的提交记录：提交记录的格式版本与后端不一致、记录不完整，或没有记 worker 镜像版本 | 按 `message` 里的原因处置：提交记录由更新版本写出的，请部署方把后端升级到提交侧的版本，或用后端版本的 CLI 重新提交；由更早版本写出的，把提交侧的 CLI 升级到后端的版本后重新提交；其它情况重新提交 |
| `status` / `explain` 以退出码 2 结束，`这个 run 的提交记录由更新版本的 gherkai … 写出` 或 `由更早版本的 … 写出` | 提交记录的格式与本机 CLI 不一致 | 更新的：`uv tool upgrade gherkai`；更早的：用写出它的那个版本查看（`uvx --from 'gherkai==<版本>' gherkai status …`）或重新提交。同一个报告目录不要混用 1.4 与 1.5 的 CLI |
| job 判 `error`、归因为 `precheck_failed`，消息「这个 job 的格式版本是 …：命令行工具与 worker 的版本不一致」或「这个 job 没有带测试目标」 | 起 job 的命令行工具与 worker 不是同一版本 | 把两者装成同一版本；云端用与命令行工具同版本的 worker 镜像（部署方运行 `gherkai deploy`） |

## 其它以退出码 2 结束的错误

| 症状 | 原因 | 处置 |
|---|---|---|
| `未找到 run：<run_id>（--report-dir 是否与 submit 一致？）` | 定位参数与产生这个 run 的那条命令不一致 | 照那条命令逐字对齐 `--backend`、`--report-dir`、`--prefix` |
| `没有 scenario 匹配 …`，随后列出这个 run 的全部候选 | `--scope` / `--tags` / `--scenario` 把范围筛成了空集 | 从列出的候选里挑正确的值 |
| `feature 语法错误（gherkin 解析失败，含行:列）` | `.feature` 文件语法有误 | 按报出的行列改；写法见[编写 .feature](./writing-features.md) |

## 仍未定位到原因时

反馈问题时请附上三项信息：`gherkai doctor --json`（带上出问题那个后端的参数）、`gherkai --version`、失败 run 的 `gherkai explain <run_id> --json`。问题反馈见 https://github.com/zhiyanliu/gherkai/issues 。
