# 排错

报错后的排查顺序：先按下面的读法看 `gherkai doctor` 的每一行；再按症状分类查原因与处置，分类有安装与版本、凭证与 region、模型、引擎与判定、确定性 step 加载、云端后端、run 一直停在 pending 或 running、隧道、项目配置文件与设备目标；定位参数不一致、本机后端的报告目录不受支持或路径太长、筛选筛成空集、给定的 `.feature` 里没有任何 scenario、`.feature` 语法错误这类其它以退出码 2 结束的情况另列。每条命令的完整用法与退出码见[运行测试与查看结果](./running-and-results.md)，环境变量与选项的总表见[配置](./configuration.md)，云端后端的部署与维护见[云端后端](./cloud-backend.md)。

## 先运行 gherkai doctor

```bash
gherkai doctor                    # 只查本机
gherkai doctor --backend cloud --prefix gherkai- --report-dir reports/   # 连带查凭证与云端后端
gherkai doctor --json             # 机读 {ok, checks[]}
```

自检只做读操作：不建浏览器会话、不调模型，不产生模型费用。输出是一张表，每个检查项一行，「结果」列有四种标记：

| 标记 | 含义 |
|---|---|
| `✓` | 查过且通过 |
| `✗` | **必修项**没通过 |
| `-` | 查过、可选项没通过，不影响退出码（例如另一个引擎没装、部署工具链不全、项目里还有未结束的远程访问会话） |
| `·` | 未查：这一行这次没有检查，说明列写着原因（例如没给云端参数、前面的凭证检查已失败、没装部署 extra）。不影响退出码，也不表示那一部分没有问题 |

有未查的行时，表格下方的结论行会点明 `·` 的含义。退出码规则与 `--json` 每项的字段见[开始使用](./getting-started.md)的「用 doctor 自检」。下表说明每一行在查什么、判 `✗` 时怎么办。

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
| `steps.load.<引擎>` | 每个可用引擎（`steps.dir` 判 `✗` 时不查询 worker 的能力自述，本行与 `engines.model.<引擎>`、`engines.targets.<引擎>` 都不出现） | 该引擎加载到多少条确定性 step（含内建）。有 steps 目录时必修，没有时只是可选 |
| `aws.region` | 云端（region 只剩 profile 配置这一处可取时——`--profile` / `AWS_PROFILE` / 配置文件 `[common]` 的 `profile` 指的 profile 读不出来，这一行不出现，失败报在 `aws.identity` 那行） | 落实到的 region。五处都没有 region 时必修失败 |
| `aws.identity` | 总是（云端而 `aws.region` 判 `✗` 时不出现） | 调用者身份。凭证不可用或 profile 名不存在时必修失败；未给云端参数时这一行标 `·`，说明为「未查（给 --backend cloud 或 --prefix 才查云端）」 |
| `backend.reachability` | 未给云端参数时，或给了云端参数而 `aws.region`、`aws.identity` 先失败时（两者都通过就没有这一行，下面几行即实际探测结果） | 这一行只交代云端为什么没查，总是标 `·`：三种情形的说明依次为「未查（同上）」/「未查：region 未能解析」/「未查：AWS 身份检查未通过」。后两种情形下真正的失败在它上面那一行（标 `✗`），`backend.*` 其余各行都不出现 |
| `backend.version` | 云端 | 后端版本戳与 CLI 版本比对。本机 CLI 新于后端时必修失败（提交也会被拒）；读版本戳本身失败（凭证、权限、网络）时同样必修失败。后端没有版本戳只提示、不拦，按提示请部署方运行一次 `gherkai deploy` 写入版本戳。两侧任一不是正式发行版本（含本机从源码直接运行、取不到自身版本）时跳过比对，只提示、标 `✓` |
| `backend.resources` | 云端 | 两张表、产物桶、cluster、两个引擎的 task 定义、三个 Lambda 是否都在，报告前缀与 `--report-dir` 是否一致。必修 |
| `backend.worker.default` | 云端 | 部署级默认 worker 镜像 variant 指针。缺失或读不到时必修失败，下面三行 `backend.worker.*` 都不出现；设备支持的两行照常检查 |
| `backend.worker.<引擎>` | 云端，且 `backend.worker.default` 通过后 | 该引擎在默认 variant 下解析到的 task 定义 revision。单引擎解析不到只标 `-` |
| `backend.worker.any` | 云端，且 `backend.worker.default` 通过后 | 至少一个引擎解析到 worker 镜像。两个都解析不到时必修失败 |
| `backend.worker.grace` | 云端，且 `backend.worker.default` 通过后 | 本机 worker 自报的收尾宽限与云端为它设的停止宽限比对，只比解析到镜像、且本机装了 worker 的引擎：一个引擎都没解析到镜像，或解析到的引擎本机都没装对应 worker 时，整行标 `·`（未查）；只比了一部分时按比了的引擎给结果，本机没装 worker 的引擎被跳过并在行内说明。差距只标 `-`、不影响退出码；行内给出两种情形的处置：云端宽限还没到平台上限时，可以请部署方用 `gherkai deploy --stop-timeout` 调高；已到上限时，这条差距来自平台限制，不必处理（按默认值部署的后端上停止宽限已是平台上限，Nova Act 这一项通常就是这种情形） |
| `backend.devices.project` | 云端 | 这套后端是否启用了设备支持，即部署时建立的 Device Farm 项目 ARN 是否记在 SSM 里。没有时标 `-` 并提示「部署未启用设备支持」：不测设备的团队可以忽略；要测设备时，请部署方用有 Device Farm 权限的凭证重新运行 `gherkai deploy`。读这个参数本身失败时同样只标 `-`，行内给出原因。不影响退出码 |
| `backend.devices.sessions` | 云端，且 `backend.devices.project` 读到项目后 | 项目里还没结束的远程访问会话（含排队中的），每条带控制台链接与停止命令 `aws devicefarm stop-remote-access-session --region us-west-2 --arn <会话 ARN>`；doctor 使用了 profile（来自 `--profile`、`AWS_PROFILE` 或配置文件 `[common]` 的 `profile`）时，命令末尾还带同一个 `--profile <名称>`。没有时标 `✓`；有时标 `-`：正在执行的 run 也有会话，停止前先确认没有 run 在使用它，没有 run 使用的会话会继续计费并占用设备，最长到 Device Farm 的 150 分钟上限。列举需要 us-west-2 上对这个项目的 `devicefarm:ListRemoteAccessSessions` 权限，缺这项权限时这一行说明缺什么，遇到限流、网络等其他错误时同样只标 `-`、行内给出原因与下一步；停止需要 `devicefarm:StopRemoteAccessSession`，只提交 run 的成员的最小权限里没有这一项，请有该权限的人停止。表格在窄终端里会把长链接与命令折成多行，`doctor --json` 的 `detail` 里是完整的一行。不影响退出码 |
| `provider.deploy-aws` | 未装部署 extra、装了多个部署 provider、或装了却加载失败时 | 前两种标 `·`（部署工具链没有检查；部署 extra 只有部署方需要）；**装了却加载失败**是必修失败 |
| `provider.node`、`provider.cdk`、`provider.container-engine` | 部署 provider 可自检时 | Node ≥ 22、`cdk` 或 `npx`、容器引擎能否连上。三项都不是必修项：通过标 `✓`，缺失或连不上只标 `-`，不影响退出码；它们只影响 `gherkai deploy` 与 `gherkai deploy push-worker`，不影响提交与本机运行 |
| `provider.aws` | 部署 provider 的自检本身出错时，或装上的部署 provider 不提供自检时（这时都不出现上一行的三项） | 自检出错时行内给出错误原因、只标 `-`；不提供自检时标 `·`。都不影响退出码 |

给 `--backend cloud` 或 `--prefix` 才会查 `aws.*` 与 `backend.*` 两段；`--prefix` 与 `--report-dir` 都要与提交时用的值一致，否则查的是另一套资源。云端两段中途早退不影响 `provider.*` 段，它照常查。自检不查隧道前置。

## 安装与版本

| 症状 | 原因 | 处置 |
|---|---|---|
| 以退出码 2 结束，`引擎 novaact 的 worker 运行时未找到`（或 midscene），后面跟一句装法 | 该引擎的 worker 没装，或不在 PATH 上 | 按报错中给出的安装命令安装：Nova Act 用 `uv tool install 'gherkai[local]'`，Midscene 用 `npm i -g @gherkai/worker-midscene`。用自建 worker 时用 `GHERKAI_WORKER_NOVAACT_CMD` / `GHERKAI_WORKER_MIDSCENE_CMD` 指向它 |
| 以退出码 2 结束，`worker 自述失败，拒绝运行`，末尾提到「worker 与命令行工具版本不一致——两者须同版本安装」 | worker 与 CLI 不是同一个版本 | 把两侧装成同版本：`uv tool upgrade gherkai`；Midscene 侧运行 `npm i -g @gherkai/worker-midscene@<gherkai --version 显示的版本>` |
| `能力自述格式版本是 …，这个命令行工具认的是 …：命令行工具与 worker 的版本不一致，请把两者装成同一版本`（本机后端的 `run`、`submit`，以及 `list-deterministic` 与 `plan` 都以退出码 2 结束并给出这一句）；`自述的最短停止宽限不是非负有限数` 等以同一句结尾的提示 | 同上，版本不一致的另一种形态 | 同上 |
| `plan` 以退出码 2 结束，worker 的报错是「收到的确定性 step 查询不是这个 worker 认的格式：命令行工具与 worker 的版本不一致」 | 同上：查询确定性 step 时暴露的版本不一致（1.4 的命令行工具把它冠以「使用方 steps 加载失败」） | 同上 |
| `要问的是引擎 X 的 worker，回答的却自称 Y` | `GHERKAI_WORKER_*_CMD` 指到了另一个引擎的 worker | 改正该环境变量，或取消设置改用已安装的 worker |
| Midscene worker 无法启动，且 `node --version` 低于 22 | `@gherkai/worker-midscene` 要求 Node ≥ 22 | 把 Node 升到 22 或更高，再重装该包 |
| `plan` 输出以「（标注降级）」开头的提示 | 某个引擎的 worker 不可用（没装、起不来或没有及时回应），只影响命中标注；worker 与命令行工具版本不一致不在此列，`plan` 以退出码 2 结束（见上） | 不阻塞 `plan`；需要标注时把那个 worker 装上 |

只提交云端 run 的人不必装任何 worker：`submit --backend cloud` 不查本机 worker。

## 凭证与 region

| 症状 | 原因 | 处置 |
|---|---|---|
| `没解析出 region`（自检的 `aws.region` 行），或 worker 启动即报 `AWS_REGION 未设` | `--region`、`AWS_REGION`、`AWS_DEFAULT_REGION`、配置文件 `[common]` 的 `region`、`--profile` / `AWS_PROFILE`（或配置文件的 `profile`）指的 profile 配置，五处都没有 region | 任选一处设上。缺失时不会替你选一个 region |
| `凭证/region 不可用（--region / AWS_REGION / AWS_DEFAULT_REGION / 配置文件 [common] region、--profile / AWS_PROFILE / 配置文件 [common] profile）` | 本机凭证链取不到可用凭证，或 `--profile` / `AWS_PROFILE` / 配置文件 `[common]` 的 `profile` 给的 profile 名不存在 | 配好 AWS 凭证（profile、环境变量、实例角色皆可），或改正 profile 名。两个引擎都用 IAM 鉴权，不需要 API key |
| 以退出码 2 结束，`AWS 身份不可用：--profile / AWS_PROFILE / 配置文件 [common] profile 指定的 profile 读不出来，或凭证链不可用：…` | `--profile`、`AWS_PROFILE` 或配置文件 `[common]` 的 `profile` 给的 profile 名不存在（拼错，或指向已删除的 profile），而 region 没有从 `--region`、`AWS_REGION`、`AWS_DEFAULT_REGION` 或配置文件 `[common]` 的 `region` 给出、只能从这个 profile 的配置里读；也可能是 AWS 的配置文件（默认 `~/.aws/config`）本身无法解析 | 改成本机已配置的 profile 名，或去掉它改用默认凭证链；AWS 配置文件无法解析时按报错里的路径修正。提示末尾附有 AWS SDK 的原始报错，写明是哪个 profile 读不出来，或哪个文件无法解析 |
| 本机运行也报凭证错 | 浏览器与模型都在云端，本机 `run` / `submit` 同样要凭证 | 配好凭证。不需要 AWS 凭证的命令只有几条，清单见[开始使用](./getting-started.md#aws-前置) |

## 模型

| 症状 | 原因 | 处置 |
|---|---|---|
| worker 日志或 `explain` 里出现 AWS 的权限被拒、模型不可用一类报错 | 该 region 未开通所用模型，或凭证缺 Bedrock、AgentCore Browser、Nova Act 的权限；本机后端的设备 run 还要 Device Farm 与应用桶的权限 | 在该 region 开通模型或补权限，本机后端所需的动作与资源见[运行测试与查看结果](./running-and-results.md#本机后端的凭证需要什么权限)。`gherkai doctor` 的 `engines.model.<引擎>` 行显示这台机器实际会用哪个模型 |
| Midscene worker 启动即退，`模型 … 不在已知家族里——无法确定该按哪种模型去驱动浏览器` | `MIDSCENE_MODEL_ID` 换成了识别不出家族的模型 | 设 `MIDSCENE_MODEL_FAMILY` 指明家族（取值见 https://midscenejs.com/model-api-setup ），或把 `MIDSCENE_MODEL_ID` 换回受支持的模型；默认值是 `us.openai.gpt-5.6-terra` |
| Nova Act 侧报模型不存在或不可用 | `NOVA_MODEL_ID` 覆盖成了该 region 没有的模型 | 取消该环境变量，回到默认的 `nova-act-v1.0` |

## 引擎与判定

| 症状 | 原因 | 处置 |
|---|---|---|
| job 判 `error`，归因是 `timeout`，说明是 `job 超时（预算 …s，已中止）` | 这个 job 的墙钟预算到点（未标 `@timeout` 的 scope 用 `--default-job-timeout`，桌面 scope 默认 300 秒，设备 scope 默认为获取预算（`[devices]` 的 `acquire-timeout-s`）加 900 秒）。前台 `run` 或 `submit --backend local` 运行期间机器休眠过，或执行它的进程被暂停过时，这段时长同样计入预算 | 因休眠或暂停到点的，原样重新运行即可，调大预算没有用。其余情形给慢的 scope 标一个大于当前预算的 `@timeout:<秒>`，或把 `--default-job-timeout` 调到大于当前预算：桌面 scope 如 `@timeout:600`；设备 scope 的缺省已是获取预算加 900 秒（获取预算为默认的 600 秒时是 1500 秒），给的值要比它大才算调高，且不得低于获取预算加 180 秒，否则在开始执行前就以退出码 2 被拒；预算最长 7200 秒（`--default-job-timeout 0` 即取这个值），超过同样被拒；也可以把长流程拆成多个 scope |
| `run` 或 `status` 的说明是「已超过允许运行的时间」，有 job 记 `skipped`、说明「这个 run 已超过允许运行的时间，job 没有启动」；或 job 记 `aborted`，说明是 `这个 run 已超过允许运行的时间，job 被中止` | 这个 run 到了允许运行到的时刻（`run_meta.deadline_at`），见[运行测试与查看结果](./running-and-results.md)「允许运行的时间」。这个时刻按全部 job 的预算串行累加，正常的 run 远在它之前结束；到达它多半是运行期间发起的机器休眠过、执行它的进程被暂停过、某次云端调用长时间没有返回，或云端后端的后台推进中断过、过了这个时刻才接着推进。说明末尾带「（已记为已结束）」的，是 `settle-runs` 或 `status --wait` 在允许运行的时间之后再过 5 分钟把它记为已结束的，执行中的 job 记 `aborted`、说明「这个 run 已超过允许运行的时间，job 没有结果（已记为已结束）」（见下「run 一直停在 pending 或 running」）。总状态按各 job 的状态得出：有 job 出错为 `error`，否则有用例失败为 `failed`，否则为 `aborted` | 用 `--scope` 只重新运行 `skipped` 与 `aborted` 的 job，以及归因 `timeout` 的 job（休眠过的 run 里先到点的往往是 job 自己的预算，这样的 job 判 `error`、归因 `timeout`）。机读输出里找它们：`run --json` 的 `jobs` 与 `status --json` 的 `jobs[]` 都列出全部 job，按 `status` 挑出 `skipped` 与 `aborted`；归因 `timeout` 的看 `run --json` 里各 job 的 `error_type`，`status --json` 不带归因，用 `gherkai explain <run_id> --json` 里各 scope 的 `error_type` 看。运行期间让机器保持唤醒，云端后端的后台推进停住时尽早用 `status --wait` 触发它接着推进（见下「run 一直停在 pending 或 running」）。调大预算只在 job 本身确实需要更长时间时才有用 |
| 某一步记 `error` 并标 `(timeout)`，job 级归因为空 | Nova Act 的单次 AI 操作到点（默认 120 秒），不是 job 墙钟到点 | 把这一步的动作写得更细，或调高 `NOVA_ACT_TIMEOUT_S`，见[配置](./configuration.md)。调高 `--default-job-timeout` 对这种超时无效 |
| Nova Act 引擎下，非英文页面上「正文里出现某个中文词」这类文本包含断言系统性判否（同一页面上的英文词仍可靠） | Nova Act 在非英文页面上不适合做这类文本断言，提高投票次数无效 | 按[编写 .feature](./writing-features.md)的「按引擎选写法」选一种改法：改用 Midscene 引擎、把断言改写成页面级语义陈述，或改成确定性 step |
| 同一条 AI 断言两次运行的结论不同 | AI 判定本身会抖动 | 用 `--assertion-votes 3` 让每条 AI 断言判三次、取多数，或把这条判定改成确定性 step；取值与取舍见[编写 .feature](./writing-features.md)的「投票」 |
| 设备上要求收起键盘的那一步判 `error`，说明以 `键盘仍然显示：` 开头 | 说明的后半句写明原因：iOS 上「收起键盘」只点纯粹用来收起的控件（键盘上的 Done / 完成键、键盘上方工具栏里的 Done），这个输入框没有这样的控件；或点了控件键盘仍在；Android 上是系统的收起命令没有收起 | 输入框靠 Return 键或点空白处收起的，在用例里写明「按下 Return」或「点击输入框外的空白处」；下一步的目标没有被键盘遮住就删掉「收起键盘」；两者都不是则是被测应用自身的可用性问题，按失败处理；写法见[编写 .feature](./writing-features.md)的「设备上的软键盘」 |

判 `error` 的 job 与 step 带一个归因标记：`gherkai status` 与 `run` 的文本输出把它显示成 `(<归因>: <说明>)`，`--json` 输出里它是 `error_type` 字段（机读字段全表见 [`../internals/cli-json-contract.md`](../internals/cli-json-contract.md)）。常见的几种：

| 归因 | 含义与处置 |
|---|---|
| `timeout` | job 墙钟预算到点、这个 run 已超过允许运行的时间，或 Nova Act 的单次 AI 操作到点。见上表前三行 |
| `network_error` | 网络瞬时故障（建连失败，或中途断网）。原样重新运行通常就能过 |
| `engine_error` | worker 无法启动、运行中途崩溃，或干净退出却没交完结果。先看 worker 日志，再用 `gherkai explain <run_id>` 看已有的证据 |
| `guardrail` | Nova Act 的安全护栏拦下了这一步的操作。改写这一步的措辞，或把这条 scenario 标 `@engine:midscene` |
| `release_failed` | 有会话没能确认停止，可能仍在计费：worker 停止会话时失败或超时，或者某次建立会话的请求结果未知、收尾前也没能核实（说明里记为「结果未知的创建尝试」）。结果未知的情形是收到停止信号时建立请求还没有返回；设备目标上还包括建立请求超时、连接中断、服务返回服务端错误（HTTP 5xx），以及回应里没有会话 ARN，之后按会话名也没有找到这个会话。说明里追加一句按目标给出的提示（接在原有的失败原因之后），桌面目标为「AgentCore 浏览器会话未能确认停止，可能仍在计费，请在 Amazon Bedrock AgentCore 控制台核对并手动停止」，设备目标为「远程访问会话未能确认停止，可能仍在计费，请在设备控制台核对并手动停止」，提示之后列出未确认停止的会话名与结果未知的创建尝试。桌面目标到 Amazon Bedrock AgentCore 控制台按会话名核对这些浏览器会话、手动停止仍在运行的；设备目标到 Device Farm 控制台核对远程访问会话，云端后端也可以用 `gherkai doctor --backend cloud` 的 `backend.devices.sessions` 行列出未结束的会话与停止命令。已报出的 scenario 结果照常保留 |
| `precheck_failed` | 测试还没有开始，重新运行结果也不会变，scope 里一条 step 都没有执行。设备目标上常见的形态：没有符合条件的设备（消息带最接近的可用系统版本）、指定的设备 ARN 被拒、安装包已不在存储桶里或没有读取权限、应用启动后立即自行退出（多半带运行环境检测，要提供关闭检测的测试包）、设备拒绝安装驱动辅助程序、服务商没有安排设备就结束了会话（消息带服务商的说明，常见于不计量方式而账号没有不计量设备槽位：改回按量或先购买槽位）。按消息改设备选择、换测试包或换设备；会话预热被拒、命令行工具与 worker 版本不一致也归这一类，见下文对应各节 |
| `acquire_timeout` | 在获取设备的等待时间内没有拿到可用设备（排队、设备繁忙或准备时间过长）。稍后重试，或在 `gherkai.toml` 的 `[devices]` 调大 `acquire-timeout-s`。应用目标在准备安装包（检查存储桶里的安装包、生成安装包的下载地址）时到期也归这一类，消息以「准备安装包时超过了获取设备的等待时间」开头：这几步正常很快就完成，到期多半是网络或 AWS 凭证来源没有响应，先确认网络连接与 AWS 凭证正常再重新运行 |
| `session_lost` | 设备的远程访问会话在执行中途结束（被人手动停止，或到达会话上限），当前 step 记 `error`、本 scope 余下的 scenario 未执行，判定不完整。缩短 scope，或核对是否有人在控制台停止了会话。会话也可能在准备设备时就已结束（获取设备、启动应用或会话预热期间），这时本 scope 的 step 都没有执行；核对是否有人在控制台停止了会话，然后重新运行 |
| `capability_unavailable` | step 级：这台设备不提供这一步需要的能力，重新运行不会变，例如需要网页上下文的确定性 step 落在不提供它的设备上、设备不支持经系统打开地址、Android 上地址含 `;`、`'`、`(`、`)` 或中文等地址中不允许的字符而没有百分号编码。按消息改写为 AI 步、改地址或换一台设备 |

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
| `run` 以退出码 2 结束，`gherkai run 只在本机执行，不支持云端后端（… 给出的是 cloud）：要在云端后端执行，请用 gherkai submit --backend cloud 提交 …` | `run` 只在本机后端执行：命令行给了 `--backend cloud`，或项目配置文件 `[common]` 的 `backend` 设为 `cloud` | 云端后端用 `gherkai submit --backend cloud --prefix <前缀>` 提交、`gherkai status <run_id> --backend cloud --prefix <前缀> --wait` 等结果；要在本机前台运行，去掉 `--backend cloud`，配置文件里设了 `cloud` 时在命令行上给 `--backend local` |
| `settle-runs` 以退出码 2 结束，`这个版本的 gherkai settle-runs 只处理本机后端（--backend local）的 run，还不能处理云端后端的 run。` | 命令行给了 `--backend cloud`，或项目配置文件 `[common]` 的 `backend` 设为 `cloud`；这时没有访问云端 | 云端后端的 run 由后端推进与结束，停住时见下「run 一直停在 pending 或 running」；要处理本机报告目录里的 run，配置文件里设了 `cloud` 时在命令行上给 `--backend local` |
| `run` 以退出码 2 结束，`unrecognized arguments: --prefix …`（或 `--ddb-table`、`--s3-bucket`、`--worker-variant`） | 这几个选项只用于云端后端，`run` 只在本机后端执行、不收它们 | 要在云端后端执行，改用 `gherkai submit --backend cloud`，这几个选项照原样写在 `submit` 上；要在本机前台运行，去掉它们 |
| cloud 命令以退出码 2 结束，提示「本机 CLI X 新于后端 Y」 | CLI 与后端不是同一版本，新 CLI 写的任务定义不能交给旧后端读 | 请部署方运行 `gherkai deploy` 把后端升级到同版本；也可以临时用 `uvx --from 'gherkai==<后端版本>' gherkai …` 提交，不改动本机安装。没有强行放行的开关。反过来，本机 CLI 旧于后端只提示、不拦截，用 `uv tool upgrade gherkai` 升级本机 CLI |
| 提交以退出码 2 结束，`引擎 X 的 worker variant '…' 解析失败` | 当前 CLI 版本下，该引擎没有这个 variant 的镜像 | 临时改用 `--worker-variant base` 提交（部署方运行过本版本的 `gherkai deploy` 即有）；请部署方补推该 variant 的步骤见[云端后端](./cloud-backend.md)的「worker 镜像 variant」。报错说的是本机 CLI 旧于后端时，先升级 CLI，不要照旧版本推镜像 |
| 提交以退出码 2 结束，提示后端没有默认 worker 镜像 variant 指针 | 这个 prefix 下的后端还没完成过本版本的初始化，或默认指针被清掉 | 请部署方运行一次 `gherkai deploy` 完成初始化；急用时提交者用 `--worker-variant base` 显式指定 |
| `submit --backend cloud` 以退出码 2 结束，`--backend cloud 资源缺失：<资源>（用 --prefix=… 拼出）不存在`；或自检的 `backend.resources` 标 `✗` | `--prefix` 与部署用的不一致，或该 prefix 下还没部署过 | 用部署方给的 prefix，并确认 region 与账户也是部署时那一套；`--report-dir` 同样要与提交时一致 |
| 自检的 `backend.version` 标 `✗`，`读不到后端版本戳（prefix 配错或后端未部署？）` | 读这个参数本身失败：凭证、权限或网络不通 | 先按上一行核对 prefix 与 region，再确认当前凭证有读 SSM 参数的权限 |
| 云端 job 判 `error`，报告里看不出原因 | 失败发生在容器里 | 用 `gherkai explain <run_id> --backend cloud` 看 job 的 `message` 与证据；worker 容器日志在 CloudWatch 日志组 `/<prefix>worker/<引擎>`，默认前缀下即 `/gherkai-worker/novaact` 与 `/gherkai-worker/midscene` |
| `submit --backend cloud` 以退出码 2 结束，`后端没有版本戳 … 带设备目标或使用 --expose-local 的 run 不能提交到它` | 这个后端在 1.4.0 之前部署（那时的部署不写版本戳），之后没有升级过；它会丢掉这类 run 的设备目标或会话预热设置，结果可能被误判为通过 | 请部署方运行 `gherkai deploy` 升级后端；没有使用 `--expose-local` 的桌面 run 不受影响 |
| 提交以退出码 2 结束，`部署未启用设备支持` | 部署时没有建立 Device Farm 项目：部署版本早于本功能，或部署方没有 Device Farm 权限 | 请部署方用有 Device Farm 权限的凭证重新运行 `gherkai deploy`；之后 `doctor --backend cloud` 的 `backend.devices.project` 行应显示项目 ARN |
| `list-runs --backend cloud` 以退出码 2 结束，`云端后端的 run 清单索引还在建立，暂时不能列出 run。…` | AWS 还在为运行记录表建立清单所用的索引 | 稍后重试；`submit` 与 `status` 不因清单索引尚未就绪而被拦截。长时间仍是这样时，请部署方检查索引的建立进度。 |
| `list-runs --backend cloud` 以退出码 2 结束，`云端后端还没有 run 清单索引，不能列出 run。…`，或说索引 `正在被删除` | 这个后端还没有用当前版本部署，或索引被删除了 | 请部署方用当前版本的 `gherkai deploy` 重新部署后端 |
| `list-runs --backend cloud` 以退出码 2 结束，`读取运行状态表 … 时重试 … 次后仍有 … 个 run 没有读回（通常是读取被限流）` | 读回运行状态时被限流，为免给出缺行的清单，这次没有列出 | 稍后重试 |
| `list-runs --backend cloud 读不到运行状态表 …（表、索引、凭证、region 或权限）：…` | 表不存在（`--prefix`、`--ddb-table` 或 region 不对），或凭证缺列出 run 所需的权限 | 先按上面「资源缺失」一行核对前缀与 region；权限缺的是索引上的 `dynamodb:Query` 与表上的 `dynamodb:BatchGetItem`，见[云端后端](./cloud-backend.md)「团队成员需要的最小云端权限」 |
| 以退出码 2 结束，`--grace 在云端不生效` | 云端的停止宽限由部署方在部署时用 `gherkai deploy --stop-timeout` 设定，运行时给这个选项不生效 | 去掉 `--grace`。`doctor --backend cloud` 的 `backend.worker.grace` 行会比对部署侧设的宽限够不够 |

## run 一直停在 pending 或 running

`status` 或 `list-runs` 里一个 run 长时间停在 `pending` 或 `running`、进度不变也没有报错，说明执行它的那一方已经停下。

**本机后端**（前台 `run` 与 `submit --backend local` 都是）：执行这个 run 的 gherkai 进程已经退出（被结束、终端关闭、机器重启或出错退出）或被暂停，没有别的进程会接着执行它。后台推进进程出错退出时，原因在这个 run 目录里的 `reconcile.log`。用与产生这个 run 的命令相同的 `--report-dir` 执行下面任一条：

- `gherkai settle-runs <run_id>`：执行它的进程已经退出，或已过了允许运行的时间之后再过 5 分钟时，把这个 run 记为已结束（执行中的 job 记 `aborted`、没有启动的记 `skipped`），然后照常可以 `status`、`explain`。不给 run_id 时处理这个报告目录里全部未结束的 run；先加 `--dry-run` 可以只看判断、不改动。
- `gherkai status <run_id> --wait`：等待这个 run 结束，条件成立时同样把它记为已结束，再按判定给退出码。等不出结果时它不等待、以退出码 2 结束并说明原因：运行状态记录读不出，或在 run 的目录上加锁出错而提交记录也读不出（说明的写法与处理见下「其它以退出码 2 结束的错误」）。

之后用 `--scope` 重新运行没有结果的 job。`settle-runs` 的结果是「跳过」、原因说执行它的进程还在时，这个 run 仍在执行或执行它的进程被暂停了：等它结束，或等到允许运行的时间之后再过 5 分钟。原因说运行状态记录读不出的，`settle-runs` 与 `status --wait` 都不改动它，确认不再需要之后可以手工移走这个 run 的目录；原因说由别的版本写出的，用写出它的那个版本处理。各原因的含义见[运行测试与查看结果](./running-and-results.md)「结束停住的 run」。

**云端后端**：负责推进的云端后台任务没有继续触发。云端的 run 只由后端推进与结束：`gherkai status <run_id> --wait`（定位参数与 `submit` 相同：`--backend cloud`、`--prefix`、`--report-dir`）只等待这个 run 结束，不会让云端接着推进它。后端在过了允许运行的时间之后才接着推进的 run 不再启动任何 job：此前已经启动、没有留下结束记录的 job 按到点处理（被允许运行的时间截断的记 `aborted`，自己的预算先到点的判超时）；还有 job 没有启动时，它们记 `skipped`，run 带说明「已超过允许运行的时间」结束，这些 job 要重新提交。总状态都按各 job 的状态给出（见[运行测试与查看结果](./running-and-results.md)「允许运行的时间」）。后端一直没有接着推进的 run，到了允许运行的时间后端会停下它仍在执行的 job；过了允许运行的时间再过 5 分钟仍没有结束时，后端把它记为已结束：执行中的 job 记 `aborted`、没有启动的记 `skipped`，run 带说明「已超过允许运行的时间（已记为已结束）」，随后生成报告、停掉仍在执行的 worker 任务，所以等待中的 `status --wait` 至多等到那时；没有结果的 job 要重新提交。到了那个时刻仍停在 `pending` 或 `running` 的云端 run，多半是它的运行状态记录读不出（后端不改动这样的记录，只停掉它仍在执行的 worker 任务），或后端的定时触发没有建成，部署方可以在推进 Lambda（`<前缀>kicker`）的日志里按 run_id 查看原因。这个版本的 `settle-runs` 还不能处理云端后端的 run。

**报告目录里有名字以 `.gherkai-creating-` 开头的目录**：这是建立 run 时用的暂存目录，建立 run 的进程在完成之前被强制结束时会留下它。它不是 run，不影响别的命令；不给 run_id 的 `gherkai settle-runs --report-dir <目录>` 会删去没有进程在使用的暂存目录，正在使用的跳过。

## 隧道（`--expose-local`）

| 症状 | 原因 | 处置 |
|---|---|---|
| `--expose-local 的取值 '…' 不是 origin：…`，随后提示只写到端口为止 | 取值要是 origin，即 `scheme://主机[:端口]`；这里含路径、查询串、片段、用户信息或空白字符，scheme 不是 `http` 或 `https`，缺少主机名，冒号之后缺少端口号或端口为 0，或主机、端口无法解析。提示里写明了是哪一种 | 只写到端口为止，例如 `http://localhost:3000`（末尾带一个斜杠也可以）；路径写在 feature 的 step 里 |
| `--expose-local 要用的隧道组件没有安装。…` | 安装 gherkai 时没有带上 tunnel 组件 | 重新安装并带上它，已经装的其它组件要一并列出：如 `uv tool install 'gherkai[local,tunnel]'`，只往云端提交时 `uv tool install 'gherkai[tunnel]'`。不需要安装 ngrok 可执行文件。前置见[测本机应用](./local-app-testing.md) |
| `--expose-local 要用的隧道组件已经安装，但无法加载：…` | tunnel 组件的安装不完整或已损坏，冒号之后是加载时的错误 | 重新安装带 tunnel 组件的 gherkai，如 `uv tool install --reinstall 'gherkai[local,tunnel]'`（组件照上一行一并列出） |
| `--expose-local 需要 ngrok 的令牌，但环境变量 NGROK_AUTHTOKEN 没有设置。…` | 执行这条命令的 shell 里没有设置 `NGROK_AUTHTOKEN`；gherkai 只从这个环境变量取令牌，`ngrok config add-authtoken` 写进 ngrok 配置文件的令牌不会被用到 | 在 ngrok dashboard 的 **Your Authtoken** 页取得令牌，`export NGROK_AUTHTOKEN=<token>` 后重新执行 |
| `隧道没有建成：这个 ngrok 账号上另一条在线的隧道占用了同一个地址（ERR_NGROK_334）。…` | 新注册的 ngrok 账号同一时间只有一条隧道能在线，这个账号上已有一条在线：另一个带 `--expose-local` 的运行，或在别处起的 ngrok | 等那条隧道下线之后再试；它属于另一个带 `--expose-local` 的 gherkai 运行时，持有它的进程退出之后它就会下线（还没结束的 run 用 `gherkai list-runs` 查看） |
| `隧道没有建成：…（ERR_NGROK_<数字>）。` | 隧道服务拒绝了这次连接，括号里是错误码、冒号之后是隧道服务给出的原因；常见的有令牌无效（`ERR_NGROK_105`，多半是填成了 **API Keys** 页上的值）、这个账号同时在线的会话数超出上限（`ERR_NGROK_108`） | 按原因处置：令牌无效时换成 **Your Authtoken** 页上的值；会话数超限时结束同一账号上别处的 ngrok 会话，或稍后再试 |
| `隧道没有建成：…。`，不带错误码 | 连不上隧道服务等原因，冒号之后是隧道服务给出的说明 | 确认本机能访问外网（代理与防火墙放行 ngrok）后重新执行 |
| `隧道没有建成：20 秒内没有连上隧道服务。请确认本机能访问外网后重新执行。` | 本机在时限内没有连上隧道服务：没有外网，或被代理、防火墙拦下 | 确认本机能访问外网后重新执行 |
| 本机后端 `--expose-local` 以退出码 2 结束，提示「worker 不支持本机应用测试需要的会话预热」 | 引擎 worker 比命令行工具旧，不会在隧道上做会话预热 | 把 worker 与命令行工具装成同一个版本（`uv tool upgrade gherkai`；Midscene 侧 `npm i -g @gherkai/worker-midscene@<同版本>`） |
| run 里每个 scope 都没执行任何 step，job 的消息以「隧道会话预热」或「后端未传递会话预热地址」开头 | 隧道的会话预热失败：令牌不被接受、会话 cookie 未通过校验、隧道已关闭或浏览器到隧道入口的网络不通、云端后端旧于命令行工具 | 按消息处置，见[测本机应用](./local-app-testing.md)的「常见故障」 |

以上起隧道的失败都以退出码 2 结束、不建立 run；gherkai 不另写隧道的日志文件，原因都在那一句说明里。`gherkai doctor` 不查隧道前置。取值不是 origin 的错误 `plan` 就能报出；没有安装 tunnel 组件与没有设置 `NGROK_AUTHTOKEN` 由 `run` / `submit` 在开始执行之前查出；其余隧道问题在起隧道时暴露。隧道特有的其它症状（含云端提交时隧道守护进程的几种报错）见[测本机应用](./local-app-testing.md)的「常见故障」。

## 项目配置文件与设备目标

| 症状 | 原因 | 处置 |
|---|---|---|
| `配置文件 … 里有不认识的键 …`，随后列出可用的键 | 键名拼错，或把只影响本次调用的选项写进了文件 | `[common]` 与 `[cloud]` 的键名是选项长名去掉 `--`，`[devices]` 与 `[apps]` 的键见[配置](./configuration.md)「项目配置文件」，报错里也列出了该节可用的键；只影响本次调用的选项在命令行上给 |
| `配置文件 … 不是合法的 TOML：…` | 文件语法错 | 按报出的行列改 |
| `… os-version = 18.6 要写成字符串、加引号` | 版本号写成了数字，会被当成浮点数读、末尾的 0 丢失 | 写成 `os-version = "18.6"` |
| `这个 run 里有在 Android 设备上执行的 scope，但没有指定用哪台设备` | 该平台没有任何来源给出设备 | 在 `gherkai.toml` 的 `[devices.android]` 给 `arn` 或 `os-version`，或用 `--android-device-arn`（iOS 同理）；`plan` 对此只警告 |
| `… 给的设备 ARN 形态不对：这看起来是项目 ARN、不是设备 ARN` | 把别的 ARN 贴进了设备 ARN 的位置 | 设备 ARN 形如 `arn:aws:devicefarm:<区域>::device:<设备 id>`，账号段为空；项目 ARN 形如 `arn:aws:devicefarm:<区域>:<账号>:project:<项目 id>` |
| `本机运行设备 scope 需要一个 Device Farm 项目，但没有指定` / `需要一个放安装包的 S3 桶，但没有指定` | 本机后端驱动真机要自己给项目与应用桶 | 在 `[devices]` 给 `project-arn` / `app-bucket`，或用 `--device-farm-project-arn` / `--app-bucket`、环境变量 `GHERKAI_DEVICE_FARM_PROJECT_ARN` / `GHERKAI_APP_BUCKET` |
| `注意：Device Farm 项目 … 属于账号 X，当前凭证属于账号 Y` | 项目 ARN 与当前凭证不在同一账号，多半是复制了别的环境的 ARN | 换对的项目或凭证；这条只警告不拦 |
| `注意：应用桶 … 在 <区域>，当前区域配置为 <区域>` | 应用桶不在当前区域配置（`--region`、`AWS_REGION` 或配置文件里的 `region`）所指的区域 | 不需要处理：安装包按桶所在区域处理；不想看到提示就让桶与区域配置一致 |
| 应用目标的 scope 记 `precheck_failed`，消息含 `does not exist or is not accessible` | 设备侧从存储桶下载安装包失败；这条消息本身不能确定具体原因 | 重新运行；仍失败时核对应用桶与加密密钥的访问权限，确认签发下载地址的 worker 所用 AWS 身份能读取该对象并有所需的解密权限 |
| `安装包不存在：…（配置文件 [apps.<别名>.<平台>] 的 file）` | `file` 指向的文件不在 | 路径相对配置文件所在目录，核对路径与构建产物 |
| 云端 run 的 `status` 为 `error`、状态行下有一行 `message=…` 说提交记录由更新或更早版本写出、不完整、或没有记 worker 镜像版本，没有任何 job 开始过，各 job 同样是 `error`、说明是同一句，没有报告 | 后端读到了它不能执行的提交记录：提交记录的格式版本与后端不一致、记录不完整，或没有记 worker 镜像版本 | 按 `message` 里的原因处置：提交记录由更新版本写出的，请部署方把后端升级到提交侧的版本，或用后端版本的 CLI 重新提交；由更早版本写出的，把提交侧的 CLI 升级到后端的版本后重新提交；其它情况重新提交 |
| `status` / `explain` 以退出码 2 结束，`这个 run 的提交记录由更新版本的 gherkai … 写出` 或 `由更早版本的 … 写出` | 提交记录的格式与本机 CLI 不一致 | 更新的：`uv tool upgrade gherkai`；更早的：用写出它的那个版本查看（`uvx --from 'gherkai==<版本>' gherkai status …`）或重新提交。同一个报告目录不要混用 1.4 与 1.5 的 CLI |
| job 判 `error`、归因为 `precheck_failed`，消息「这个 job 的格式版本是 …：命令行工具与 worker 的版本不一致」或「这个 job 没有带测试目标」 | 起 job 的命令行工具与 worker 不是同一版本 | 把两者装成同一版本；云端用与命令行工具同版本的 worker 镜像（部署方运行 `gherkai deploy`） |

## 其它以退出码 2 结束的错误

| 症状 | 原因 | 处置 |
|---|---|---|
| `未找到 run：<run_id>（--report-dir 是否与产生这个 run 的 run 或 submit 一致？）`，云端后端为 `（--prefix/--ddb-table 是否与产生这个 run 的 run 或 submit 一致？）` | 定位参数与产生这个 run 的那条命令不一致 | 照那条命令逐字对齐 `--backend`、`--report-dir`、`--prefix`，给过 `--ddb-table` 的也要一致；不知道 run_id 或想确认它在不在这个后端里，用同一组定位参数执行 `gherkai list-runs` |
| `无法读取本机后端的报告目录 …（请检查目录权限，或 --report-dir 是否正确）：…` | 本机后端的 `list-runs` 无法读取报告目录或其中的运行状态文件 | 核对 `--report-dir` 与目录权限 |
| `没有 scenario 匹配 …`，随后列出这个 run 的全部候选 | `--scope` / `--tags` / `--scenario` 把范围筛成了空集 | 从列出的候选里挑正确的值 |
| `没有可执行的 scenario：<文件> 里一个 scenario 都没有（常见原因：只有 Feature 头，或 Scenario Outline 的 Examples 没有数据行）` | 没有加筛选，给定的 `.feature` 里也没有任何可执行的 scenario：文件为空、只有 Feature 头、只有 Background 或不含 scenario 的 Rule，或 Scenario Outline 的 Examples 没有数据行 | 补写 scenario，或给 Examples 补上数据行；同时核对传入的路径是否是要测的那批文件 |
| `feature 语法错误（gherkin 解析失败，含行:列）` | `.feature` 文件语法有误 | 按报出的行列改；写法见[编写 .feature](./writing-features.md) |
| `报告目录 … 所在的文件系统是 …，本机后端不支持：在这样的目录上无法确认执行 run 的 gherkai 进程是否还在，没有建立 run。…`（报告目录还不存在时前半句是 `报告目录 … 还不存在，按最近一层已存在的上级 … 判断，它所在的文件系统是 …，本机后端不支持`），或 `无法判断报告目录 … 所在的文件系统（…）：…`；前台 `run` 与 `submit --backend local` 同一句，`settle-runs`（对报告目录）与 `status --wait`（对 run 的目录）给出同类说明 | 本机后端的报告目录不在受支持的本机文件系统上：网络文件系统（NFS、SMB）、FUSE 挂载、经虚拟机共享进来的目录（如 macOS 上的 Docker Desktop 从宿主挂载进容器的目录）等。判断不了时括号里写明原因，例如这台机器不是 macOS 或 Linux、读不到挂载信息 | 按说明把报告目录（`--report-dir` 选项，或配置文件里的 `report-dir`）换到清单里的本机文件系统上，在容器里执行时用容器自己的文件系统里的目录；之后的 `status`、`explain`、`list-runs` 与 `settle-runs` 给同一个值。多台机器要共用运行记录时用云端后端；判断不了、换了目录仍然判断不了时（原因在这台机器本身，如它不是 macOS 或 Linux、读不到挂载信息），同样改用云端后端。报告目录的全部要求见[运行测试与查看结果](./running-and-results.md)「本机后端的报告目录」 |
| `在报告目录 … 里给这个 run 的目录加锁失败（…），没有建立 run：不能加锁的目录上无法确认执行 run 的 gherkai 进程是否还在。…` | 报告目录所在的文件系统或访问权限不允许给 run 的目录加锁，括号里是系统给出的原因 | 按说明检查这个目录所在的文件系统与访问权限后重新执行 |
| `在报告目录 … 里准备这个 run 的目录时，连续 3 次遇到另一个进程同时在处理同一个暂存目录，没有建立 run。请稍后重新执行。` | 建立 run 时，gherkai 在报告目录里准备的目录连续几次都正被另一个进程处理，极少出现 | 稍后重新执行同一条命令 |
| `在报告目录 … 里写这个 run 的记录失败：…。还没有开始执行；…`（前台 `run` 与 `submit --backend local` 同一句） | 报告目录没有写权限，或所在磁盘已满；在开始执行之前打不开报告目录（路径上有一层是文件而不是目录、没有权限）时也是这一句 | 检查这个目录的读写权限与剩余空间后重新执行 |
| `run … 的记录已经写下，但在报告目录 … 里准备执行用的文件失败：…` | 记录写下之后，建事件记录或打开日志文件时失败（多为权限或磁盘空间）；这个 run 在记录里停在 `pending`，没有开始执行 | 检查这个目录的读写权限与剩余空间，用说明里给出的 `gherkai settle-runs <run_id> --report-dir …` 把停在 `pending` 的那个 run 记为已结束，再重新执行（经 `submit` 报出的重新提交） |
| `run … 已经存在，没有重新建立。请重新执行这条命令。` | 新建的 run 与报告目录或云端里已有的 run 撞了标识，极少出现 | 重新执行同一条命令 |
| `submit --backend local` 打出 `后台推进进程在给出提交结果之前退出了，提交没有完成；它退出之前如果有输出，原因在上面。…` | `submit` 在本机起的后台推进进程在建好 run、给出结果之前退出了；它出错退出时原因打在这句之前，被系统或别的进程结束时（如 `kill -9`、内存不足）没有输出 | 有输出时按它处理好原因，没有输出时查看是什么结束了这个进程，然后重新提交；它退出之前可能已经建立了这个 run，这样的 run 没有后台进程在执行，不必等它的结果：执行说明里给出的 `gherkai settle-runs --report-dir …`，把这个报告目录里执行它的进程已不在的 run 记为已结束，同时清理建立 run 时中断留下的暂存目录 |
| `无法启动后台推进进程：…。没有提交。` | 本机起不了新进程（进程数或内存耗尽等，原因在冒号之后） | 处理报出的原因后重新提交 |
| `报告目录 … 的路径太长…` | 本机后端的报告目录解析之后（换成绝对路径、展开其中的符号链接）超过 470 字节，按文件系统编码计（一个汉字通常占 3 字节）；每个 run 的记录、事件库与产物都放在它下面，路径再长就建不出或打不开。`run`、`submit --backend local`、`status`、`explain`、`list-runs`、`settle-runs` 在访问报告目录之前先查这一项，什么都不建 | 换一个路径较短的报告目录（`--report-dir` 选项，或配置文件里的 `report-dir`），之后的查询命令给同一个值 |
| `报告目录 … 的路径里有一层名字太长…` | 报告目录路径里某一层的名字超过了所在文件系统允许的长度（还不存在、要由 gherkai 建出的那几层同样检查）；查法与上一行相同，什么都不建 | 换一个每层名字较短的报告目录 |
| `run … 的运行状态记录读不出（…），本命令不能显示它：…`（`status`，带不带 `--wait` 同一句，带 `--wait` 时不等待；后台推进进程因此停下时，`reconcile.log` 里是 `run … 的运行状态记录读不出，后台推进已停止：…`） | 这个 run 的运行状态记录已损坏，或由别的版本写出 | 由别的版本写出的，用写出它的那个版本查看；确认不再需要之后可以手工移走这个 run 的目录。`settle-runs` 与 `status --wait` 都不改动这样的 run |
| `无法确认执行 run … 的 gherkai 进程是否还在（在 run 目录上加锁失败：…），它的提交记录也…，不知道它允许运行到什么时候。…`（`status --wait`，以退出码 2 结束、不等待） | 在这个 run 的目录上加锁出错（括号里是系统给出的原因，多为所在的文件系统或访问权限不允许加锁），它的提交记录（`run_meta.json`）又不存在或不完整：既无法确认执行它的进程是否还在，也不知道该等到什么时候，等下去没有结果 | 按说明检查这个 run 的目录所在的文件系统与访问权限后重新执行；只想看它现在的状态，用说明里给出的不带 `--wait` 的 `status` 命令 |
| `读写报告目录 … 里的记录失败：…`（`settle-runs`），或 `读写 run … 的记录失败：…`（`status --wait`） | 读写 run 的记录时出错，多为权限或磁盘问题。`settle-runs` 就此停止，已处理的列在前面，出错的那个与其余的没有改动；`status --wait` 没有把这个 run 记为已结束 | 检查报告目录的读写权限与所在磁盘，再执行同一条命令 |

## 仍未定位到原因时

反馈问题时请附上三项信息：`gherkai doctor --json`（带上出问题那个后端的参数）、`gherkai --version`、失败 run 的 `gherkai explain <run_id> --json`。问题反馈见 https://github.com/zhiyanliu/gherkai/issues 。
