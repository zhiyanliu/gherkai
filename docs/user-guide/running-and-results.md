# 运行测试与查看结果

运行 `.feature`、查看结果与读退出码涉及以下内容：执行方式与执行后端四种组合的选择、`plan` / `run` / `submit` / `status` / `list-runs` / `explain` / `list-engines` / `list-deterministic` / `doctor` 的用途与常用选项、报告与证据的位置、费用量级、机读输出与 CI 用法。安装与 AWS 前置见 [`getting-started.md`](./getting-started.md)，`.feature` 的写法见 [`writing-features.md`](./writing-features.md)，`--expose-local` 测本机应用见 [`local-app-testing.md`](./local-app-testing.md)，云端后端的部署与维护见 [`cloud-backend.md`](./cloud-backend.md)，项目配置文件、环境变量与跨命令通用选项见 [`configuration.md`](./configuration.md)。任一命令的完整选项以 `gherkai <命令> --help` 为准。

## 两个独立的选择：怎么运行、在哪运行

执行方式与执行后端是两个互不影响的选择，四种组合都合法。

**怎么运行**

| 执行方式 | 命令 | 特点 |
|---|---|---|
| 前台 | `gherkai run <feature...>` | CLI 全程在线，运行结束后直接输出判定与产物位置，退出码就是判定。CLI 进程结束（终端关闭、机器休眠）这个 run 即停止 |
| 后台 | `gherkai submit <feature...>` 再 `gherkai status <run_id>` | `submit` 打印一个 `run_id` 后立即退出，后台继续执行；用 `status` 查进度，`status --wait` 等到运行结束并拿判定 |

**在哪运行、落在哪**（`--backend`）

| 后端 | worker 运行在 | 结果落在 | 前置 |
|---|---|---|---|
| `local`（默认） | 本机子进程 | `--report-dir` 指的本地目录 | 本机装好要用的引擎 worker，有 AWS 凭证 |
| `cloud` | Fargate 容器 | 状态与提交记录落 DynamoDB，判定明细与报告落 S3 的产物桶（`<前缀>artifacts`） | 部署方先执行过 `gherkai deploy`，提交时给同一个 `--prefix` |

`submit --backend local` 在本机起一个脱离 CLI 的后台进程推进，本机要保持开机；`submit --backend cloud` 提交完即可关机，云端自己把这个 run 执行完；只有用 `--expose-local` 时例外——隧道在本机，要保持开机联网到这个 run 结束。

下面各级需要的权限不同、费用记到的账户也不同（`plan` 不需要凭证，单列一行）。

| 命令与后端 | 需要什么 | 费用记到 |
|---|---|---|
| `plan` | 不需要凭证（装了 worker 才有确定性 step 的派发标注） | 不产生费用 |
| `run` / `submit`，`--backend local` | 本机 AWS 凭证与要用的引擎 worker | 自己的 AWS 账户 |
| `submit` + `status`，`--backend cloud` | 运行记录表读写、若干只读检查、调用后端 Lambda；用例带 DataTable / DocString 时另需产物桶（`<前缀>artifacts`）的写权限，有应用目标（`@app`）的 scope 时另需该桶 `apps/` 前缀的读、写、列举与打标签。不需要任何 ECS 写权限 | 部署方的 AWS 账户 |
| `list-runs` | 本机后端不需要凭证；云端后端只需读权限：运行记录表与它的清单索引、版本戳参数与表结构的只读检查 | 本机后端不产生费用；云端后端只有少量读请求，记到部署方的 AWS 账户 |
| `run`，`--backend cloud` | 运行记录表读写、若干只读检查、起停与查询 Fargate 任务、把 worker 的任务角色与执行角色传给 ECS（`iam:PassRole`）、上传 job 与写产物桶，有应用目标（`@app`）的 scope 时另需该桶 `apps/` 前缀的读、写、列举与打标签；不需要调用后端 Lambda——这条路径由本机命令进程自己起任务、自己推进 | 部署方的 AWS 账户 |

完整的权限清单见 [`cloud-backend.md`](./cloud-backend.md)「团队成员需要的最小云端权限」。

### 本机后端的凭证需要什么权限

本机后端下命令进程与引擎 worker 都用你本机的 AWS 凭证，而浏览器会话、模型与设备都在云端，所以凭证要能做下面这些事。资源写成 IAM 策略里的形态：`<区域>` 是运行用的 region，`<账号>` 是你自己的 AWS 账号；Device Farm 只在 us-west-2 提供，设备相关的资源区域固定。只测桌面网页的凭证不需要设备与安装包两组。

| 用到的场合 | 动作 | 资源 |
|---|---|---|
| 桌面目标，两个引擎 | `bedrock-agentcore:StartBrowserSession`、`bedrock-agentcore:StopBrowserSession` | `arn:aws:bedrock-agentcore:<区域>:aws:browser/aws.browser.v1`（账号段是固定的 `aws`） |
| 桌面目标，两个引擎 | `bedrock-agentcore:ConnectBrowserAutomationStream`、`bedrock-agentcore:ConnectBrowserLiveViewStream` | `*`（这两个动作不支持按资源限定） |
| Midscene 引擎调用模型 | `bedrock:InvokeModel` | `arn:aws:bedrock:*::foundation-model/*`、`arn:aws:bedrock:*:<账号>:inference-profile/*`、`arn:aws:bedrock:*:<账号>:project/default` |
| Nova Act 引擎 | `nova-act:GetWorkflowDefinition`、`nova-act:CreateWorkflowDefinition`、`nova-act:CreateWorkflowRun`、`nova-act:UpdateWorkflowRun`、`nova-act:CreateSession`、`nova-act:CreateAct`、`nova-act:UpdateAct`、`nova-act:InvokeActStep` | `arn:aws:nova-act:<区域>:<账号>:workflow-definition/*` 与 `arn:aws:nova-act:<区域>:<账号>:workflow-definition/*/workflow-run/*` |
| 设备目标：找设备 | `devicefarm:ListDevices` | `*`（不支持按资源限定） |
| 设备目标：建立远程访问会话 | `devicefarm:CreateRemoteAccessSession` | 同一条语句里列两种：你的 Device Farm 项目 ARN，与 `arn:aws:devicefarm:us-west-2::device:*` |
| 设备目标：查询与停止会话 | `devicefarm:GetRemoteAccessSession`、`devicefarm:StopRemoteAccessSession` | 同一条语句里列两种：`arn:aws:devicefarm:us-west-2:<账号>:session:<项目 id>/*` 与项目 ARN |
| 设备目标：连接设备上的 Appium | `devicefarm:GetRemoteAccessSession` | `arn:aws:devicefarm:us-west-2:<账号>:project:session`。这是 Device Farm 为这条连接做授权检查时用的固定资源名，不是某个项目或会话的 ARN；缺它时远程访问会话能建立、Appium 会话却被拒，这个 job 记为执行前失败 |
| 设备目标：核对遗留会话 | `devicefarm:ListRemoteAccessSessions` | 项目 ARN |
| 应用目标：安装包 | `s3:PutObject`、`s3:AbortMultipartUpload`、`s3:GetObject` | `arn:aws:s3:::<应用桶>/apps/*`；另加 `s3:ListBucket` 于 `arn:aws:s3:::<应用桶>`（条件 `s3:prefix` 为 `apps/*`），`<应用桶>` 是放安装包的桶（由 `--app-bucket`、环境变量 `GHERKAI_APP_BUCKET` 或 `[devices] app-bucket` 指定，依次优先） |

云端后端下，除安装包上传外，这些事都由部署建立的 worker 任务角色去做；安装包仍由你的命令进程上传到部署的产物桶（`<前缀>artifacts`）的 `apps/` 前缀并打标签，所以你的凭证需要上表之前那一节的云端权限，其中已含应用目标的这项增量。

## 命令

一个 job 即一个 scope 里的全部 scenario，它们共享一个会话（桌面目标是一个云端浏览器会话，设备目标是一个 Device Farm 远程访问会话）、按书写顺序串行执行。scope 由 `.feature` 里的 `@scope` 标签划分；未标 `@scope` 的 scenario 各自成为一个 job，编号是 `<文件>:<行号>`（见 [`writing-features.md`](./writing-features.md)）。

一次典型的流程：

```bash
gherkai plan features/wikipedia_generic.feature            # 用例预检：分组、校验、派发标注（零费用）
gherkai run  features/wikipedia_generic.feature            # 前台运行（产生模型调用与浏览器会话费用）
RUN_ID=$(gherkai submit features/*.feature --max-concurrency 2)
gherkai status "$RUN_ID" --wait                            # 等到运行结束，按判定给退出码
gherkai explain "$RUN_ID"                                  # 有用例没过时看每一步的证据
```

| 命令 | 用途 | 常用选项 |
|---|---|---|
| `gherkai plan <feature...>` | 用例预检：打印 scope / job 分组，逐步标注哪些步由确定性 step 执行（行尾给出该 step 的说明），未标注的步交给 AI；同时校验写法与配置。不连云、不产生费用 | `--scope` / `--tags` / `--scenario`、`--default-engine`、`--assertion-votes`、`--default-job-timeout`、`--steps-dir`、`--json` |
| `gherkai run <feature...>` | 前台运行完这个 run，输出文本汇总，并把报告、运行元信息、判定明细三处位置输出到标准错误（stderr） | 见下「常用选项」 |
| `gherkai submit <feature...>` | 提交这个 run 并立即返回，stdout 只有一个 `run_id` | `--backend`、`--max-concurrency`、`--report-dir`、`--prefix`、`--worker-variant`、`--tunnel-ttl` |
| `gherkai status <run_id>` | 查这个 run 的进度与结果；到终态时同时输出三处产物位置 | `--wait`、`--backend`、`--report-dir`、`--prefix`、`--max-concurrency`、`--json` |
| `gherkai list-runs` | 列出一个后端里的 run，用来找回 run_id：默认列出全部未结束的 run 与最近创建的 20 条已结束的 run。只读，见下「找回 run_id」 | `--backend`、`--report-dir`、`--prefix`、`--status`、`--limit`、`--json` |
| `gherkai explain <run_id> [<scope_id>]` | 看每一步的证据：问了 AI 什么、AI 看见了什么、为什么这么判。用例没过时先运行这个命令 | `--scenario`、`--step`、`--all`、`--full`、`--json` |
| `gherkai list-engines` | 列出本机两个引擎 worker 的拉起命令与来源，没装的那个在同一行给出安装提示 | `--json` |
| `gherkai list-deterministic` | 列出某个引擎支持的确定性 step（含项目 `steps/` 里的），写 feature 时据此复用 | `--engine {midscene,novaact}`（默认 `novaact`）、`--steps-dir`、`--json` |
| `gherkai doctor` | 只读自检：CLI 版本、引擎 worker、实际使用的模型、`steps/` 加载结果；装了部署工具链（Node、cdk、容器引擎）时连带自检它；给了 `--backend cloud` 或 `--prefix` 时再查凭证、后端资源与后端版本 | `--backend cloud`、`--prefix`、`--report-dir`、`--steps-dir`、`--json` |
| `gherkai --version` | 打印 CLI 版本 | — |

`status`、`list-runs` 与 `explain` 的 `--backend`、`--report-dir`、`--prefix` 必须与产生这个 run 的 `run` 或 `submit` 一致（前台运行与后台提交都算），云端后端下 `--region` 也要指向同一个 region，否则查不到这个 run：`status` 与 `explain` 以退出码 2 结束，`list-runs` 列出的是另一处的 run（常见为空清单）。云端后端的 `list-runs` 不读报告，不看 `--report-dir`。`status --wait` 既是查询也是接力：后台推进停止或卡住时，这条查询命令会接着把这个 run 推进到终态；本机后端下接力的并发上限按提交时的值走，提交记录里没有值才用 `status --max-concurrency` 给的值。接力只对 `submit` 提交的 run：对正在前台 `run` 的 run 执行 `status --wait`，它只等待那次运行结束再给判定、不接力推进（执行它的进程若已不在，它不会再到终态，按 Ctrl-C 停止等待即可）。`doctor` 的读法与按症状分表的处置见 [`troubleshooting.md`](./troubleshooting.md)。

使用云端后端时 CLI 不能新于后端：CLI 与后端都是正式发行版本、且 CLI 比后端新时，`submit`、`status`、`list-runs`、`explain` 与 `run --backend cloud` 在读写云端之前即以退出码 2 结束。比对规则、后端没有版本戳时的处理与升级顺序见 [`cloud-backend.md`](./cloud-backend.md)「版本与升级」。

提交记录带格式版本。`status`、`explain` 与本机后台接力读到的提交记录格式与本机 CLI 支持的不一致时以退出码 2 结束并点名写出它的版本：由更新版本写出的请升级本机 CLI，由更早版本写出的用那个版本查看（`uvx --from 'gherkai==<版本>' gherkai status …`）或用当前版本重新提交。**同一个报告目录不要混用 1.4 与 1.5 的 CLI 读写**：1.4 的 CLI 读 1.5 的记录会静默误判，1.5 的 CLI 读 1.4 的记录直接拒绝。云端后台读到不能执行的提交记录时把 run 置为 `error` 并在 `status` 的 `message` 行里给出原因（`--json` 下是顶层 `message` 键）；只有这类在派发前就不能执行的 run 才有这一行，job 自身的失败原因看 `explain`。

## 常用选项（`run` / `submit`）

**只运行一部分**（`plan` 认同一组选项）

| 选项 | 说明 |
|---|---|
| `--scope ID` | 只运行这些 scope。值是报告与 JSON 里的 `scope_id`：`@scope` 的名字，或未标 scope 时的 `<文件>:<行号>`。可重复，任一命中。重新运行某个失败的 job 用它最直接 |
| `--tags TAG[,TAG...]` | 只运行带这些 tag 的 scenario。一个值内用逗号分隔表示任一命中，重复给本选项表示都要命中；`@` 可省。feature 行上的 tag 对其下每个 scenario 生效 |
| `--scenario SEL` | 只运行这些 scenario。`SEL` 可以是完整 scenario id、行号（`12` 或 `:12`，纯数字只当行号）、或标题的一段文字（区分大小写）。可重复，任一命中 |

三者同给时都要满足。筛掉一部分时命令会打印一行 `筛选：<已选>/<总数> scenario`，后面附上你给的筛选条件；一条都没选中时以退出码 2 结束并列出这个 run 的全部候选（id、标题、tags），不会静默执行一个空 run。不加任何筛选时，给出的 `.feature` 文件里一个 scenario 都没有（例如只有 Feature 头，或 Scenario Outline 的 Examples 没有数据行），`plan`、`run`、`submit` 同样以退出码 2 结束并提示 `没有可执行的 scenario`，不会启动一个空的 run。

**执行**

| 选项 | 默认 | 说明 |
|---|---|---|
| `--default-engine {midscene,novaact}` | `novaact` | 未标 `@engine` 的 scope 用哪个引擎；标了 tag 的 scope 不受影响 |
| `--assertion-votes N` | `1` | AI 断言执行 N 次取多数票（如 3 或 5），用于降低判定抖动 |
| `--max-concurrency N` | `4` | 同时运行的 worker 上限，须 ≥ 1。并发只改同时开几个会话（桌面目标是浏览器会话，设备目标是远程访问会话），不改 job 数与总费用；配额紧时调低。`submit --backend cloud` 提交时若超过云端后端对单个 run 的并发上限（当前为 20，见 [`cloud-backend.md`](./cloud-backend.md)），命令会提示并按该上限并行；`run --backend cloud` 由本机命令进程直接调度，不受该上限约束 |
| `--default-job-timeout S` | 按目标 | job 墙钟预算，单位为秒。不给时桌面 scope 为 300 秒，设备 scope 为获取预算（`[devices]` 的 `acquire-timeout-s`）加 900 秒；给 `<=0` 只让桌面 scope 不超时，设备 scope 仍取缺省；给正值时设备 scope 不得低于获取预算加 180 秒；用例上标 `@timeout:<秒>` 可逐 scope 覆盖。超预算的 job 被停掉并判 error |
| `--grace S` | 自动 | 仅 `run --backend local`：中止时留给 worker 收尾的秒数，收尾包括释放会话（桌面目标是云端浏览器会话，设备目标是远程访问会话）与保存产物；不给则按这个 run 用到的引擎自报的最短收尾宽限推导。比这个宽限更短时，worker 可能在释放会话或保存产物之前被强制终止，没释放的会话继续计费，所以给出更小的值时命令在开始执行前以退出码 2 结束。`--backend cloud` 不接受这个选项（给了直接以退出码 2 结束），云端的停止宽限在部署时定；写在 `gherkai.toml` 里的 `grace` 在云端后端下只提示一句、不生效 |
| `--fail-fast` | 关 | 仅 `run`：任一 job 出错即中止这个 run 的其余 job |

单个 job 的网络故障只让那个 job 判 error，其余 job 继续；给了 `--fail-fast` 才会因此中止这个 run。

**输出与落盘**

| 选项 | 默认 | 说明 |
|---|---|---|
| `--report-dir DIR` | `reports` | 报告落点，每次 run 落 `DIR/<run_id>/`。`status` 与 `explain` 查同一个 run 要给同一个值。云端后端下它是后端的报告前缀，与部署侧不一致时 `submit` 在提交前以退出码 2 结束并点名两侧的值 |
| `--no-report` | 关 | 仅 `run`：报告目录下什么都不落，也不收集引擎自己的报告产物。适合 CI 只看退出码或 JSON |
| `--quiet` | 关 | 仅 `run`：不输出逐事件进度，仍输出文本汇总。在本机运行时 worker 日志改落 `<report-dir>/<run_id>/worker.log`（`--no-report` 时落系统临时目录），只打印一行位置；云端后端下没有本机 worker 日志 |
| `--json` | 关 | 仅 `run`：标准输出只打机器可读 JSON、不打文本汇总；进度与诊断照常走标准错误，逐事件进度可用 `--quiet` 静音 |
| `--steps-dir DIR` | `./steps` | 项目自己的确定性 step 目录，也可用环境变量 `GHERKAI_STEPS_DIR`。目录里任一文件加载失败即整个 run 拒绝运行。云端后端下不生效（云端 worker 的 step 构建在镜像里，只警告不拦），写法见 [`writing-deterministic-steps.md`](./writing-deterministic-steps.md) |
| `--expose-local ORIGIN` | — | 把本机可达的被测应用经隧道暴露给云端浏览器与设备上的浏览器（只用于网页目标，原生应用不适用），配套的 `--tunnel`（两条命令都有）与 `--tunnel-ttl`（只有 `submit` 有）见 [`local-app-testing.md`](./local-app-testing.md) |

**仅 `--backend cloud`**：`--prefix P`（默认 `gherkai-`，兜底环境变量 `AWS_RESOURCE_PREFIX`）须与部署时一致，统一决定表、桶、集群等资源名；`--worker-variant NAME` 选云端 worker 镜像的 variant，不给则用部署时的默认指针，某个引擎缺这个 variant 直接以退出码 2 结束、不回落到默认，见 [`cloud-backend.md`](./cloud-backend.md)。仅 `run`：不给 `--subnet` / `--security-group` 时，Fargate 的子网与安全组按部署时写入的参数自动取用，一般不用给；`submit` 没有这两个选项，它提交的 run 用部署时写进后端的网络配置。单独覆盖某个资源名的选项见 [`configuration.md`](./configuration.md)。

## 退出码

每条命令的退出码回答的是不同的问题。本页这几条命令里，退出码表示判定结果的只有 `run` 与 `status`，也只有它们的退出码会是 1；部署方命令的退出码见 [`cloud-backend.md`](./cloud-backend.md)。

| 命令 | 退出码回答什么 | `0` | `1` | `2` |
|---|---|---|---|---|
| `run` | 判定 | 这个 run 全部通过 | 有用例失败或出错；`--backend cloud` 执行到一半时运行记录存储不可达也以这个退出码结束 | 开始执行前的配置或可达性问题 |
| `status`（不带 `--wait`） | 查到了吗 | 查到了，含还没结束的 run | 读到的终态不是全部通过 | run 不存在、云端不可达、CLI 与后端版本不匹配、提交记录的格式版本与本机 CLI 不一致或记录不完整 |
| `status --wait` | 判定 | 运行结束且全部通过 | 运行结束但不是全部通过（有用例失败或出错，或前台 `run` 被中断、run 级判定记 `aborted`） | 同上，另加后端没部署或 `--prefix` 配错 |
| `submit` | 提交成功了吗 | 已提交，`run_id` 已打印 | — | 配置或可达性问题 |
| `plan` | 这个 run 能运行吗 | 能 | — | 配置错、写法错、`steps/` 里有文件加载失败 |
| `list-runs` | 读到清单了吗 | 读到了；清单为空、或其中有无法读取的行，同样以退出码 0 结束 | — | 参数不合法（`--limit` 不是正整数、`--status` 不是 run 的状态值）、本机报告落点目录不可读、云端读不到（region 或凭证、运行记录表不存在或无权限、清单索引缺失或还在建立、读取被限流后重试仍未读全）、CLI 与后端版本不匹配 |
| `explain` | 证据读出来了吗 | 渲染出来了，用例判失败也以退出码 0 结束；判定明细尚未写出同样如此 | — | 参数写错（例如 `--step` 没同时给 `--scenario`）、run 或 scope 查不到、云端读不到、CLI 与后端版本不匹配、提交记录的格式版本与本机 CLI 不一致或记录不完整 |
| `doctor` | 必修项都过了吗 | 全过 | — | 任一必修项失败（可选能力缺失只标 `-`，不影响退出码） |
| `list-deterministic` | 这个引擎有哪些确定性 step | 列出来了 | — | `--steps-dir` 指的不是目录、worker 定位不到、`steps/` 加载失败、该引擎的 worker 自述失败（多为 worker 与 CLI 版本不一致，处置见 [`troubleshooting.md`](./troubleshooting.md)） |
| `list-engines` | 这台机器的引擎环境什么样 | 恒 `0`（某个引擎没装正是要展示的信息，不算命令失败） | — | — |
| `skill install` | agent skill 装上了吗 | 已安装（`--print` 则已打印正文） | — | `--dir` 不是目录、目标目录里已有不是本命令装的内容、包内 agent skill 缺失、写入失败 |

前台 `run` 运行期间处理了中断时退出码不表示判定：按一次 Ctrl-C（或向 CLI 进程发 SIGTERM），CLI 请求全部 worker 停止并等它们释放会话，然后照常输出汇总与产物位置；退出码为 130（Ctrl-C）或 143（SIGTERM），与各 job 的判定无关；有 job 记为 aborted 或 skipped 时，run 级判定记 `aborted`。本机后端给 worker 的释放宽限由 `--grace` 指定，到期强制结束 worker、再收集结果，再按一次 Ctrl-C 则立即强制结束；云端后端的停止宽限由部署配置决定，再按一次只会重发停止请求、不能缩短等待。强制结束后会话可能来不及释放、继续计费，请到 AWS 控制台核对并手动停止（设备目标看 Device Farm 的远程访问会话，桌面目标看 AgentCore 的浏览器会话）。用 `kill -9` 结束本机 CLI 进程时 worker 收不到任何通知，通常在 CLI 退出后的几秒内检测到并开始释放会话；CLI 已退出但尚未被它的父进程回收、或进程号已被复用时，这项检测可能延后或不触发。释放完成所需的时间取决于当时正在执行的操作与收尾；云端 worker 不做这项检测。

分界线在于是否已经开始执行：开始执行前的一切（feature 读不到、写法或参数不合法、worker 没装、凭证与资源不对）以退出码 2 结束，正常执行结束的判定退出码为 0 或 1；运行期间处理了中断则为 130 或 143。`status --wait` 的等待或接力被 Ctrl-C 停止时退出码同为 130，不表示判定。这条命令若只是在等待（所等的 run 由前台 `run` 推进），或这个 run 在云端后端，停止它不影响 run 的推进；本机后端下由这条命令接力的 run 若没有别的进程在推进，会停在当前状态，它起的 worker 自行收尾并释放会话，再执行同一条命令可继续。用 `--json` 时先按退出码分流，再解析 stdout。各判定状态的含义与聚合规则见 [`../internals/verdict-model.md`](../internals/verdict-model.md)。

## 结果在哪

`--backend local` 下每次 run 落一个目录（下面以默认 `reports/` 为例）：

```
reports/<run_id>/
├─ index.html          可点开的报告入口：判定明细树 + 每条产物一行链接
├─ manifest.json       机读的产物清单
├─ jobs/               每个 job 一份判定明细，文件名由 `scope_id` 编码而来（未标 `@scope` 的用例，`scope_id` 就是 `<文件>:<行号>`） —— 判定的权威在这里
├─ run_meta.json       这个 run 提交了什么（run_id、并发、每个 job 的用例原文与预算）
├─ run_state.json      运行到哪了
├─ nova-trajectories/  Nova Act 引擎的轨迹与会话汇总，以及每步的 AI 证据与截图
├─ midscene-run/       Midscene 引擎的报告与截图，以及每步的 AI 证据；log/ai-config.log 记录这次实际用的模型
└─ worker.log          仅 `run --quiet` 且在本机运行时
```

同一目录下的 `events.db` 是这个 run 的事件记录（worker 报出的每条事件一行；`explain` 对被中止的 job 从这里补取已执行 step 的记录与证据），前台 `run` 与 `submit --backend local` 都写它，`--no-report` 不写；`submit --backend local` 还会留后台进程日志 `reconcile.log`（后台运行迟迟不推进时先看它）；用了 `--expose-local` 时另有隧道记录 `tunnel.json`。判定以 `jobs/` 下的明细或退出码为准，不要以 `index.html` 为准：它是可以重建的展示视图。纯确定性的用例不产生引擎产物，但每一步的判定与耗时都在判定明细里。

设备目标的 scope 另在 `midscene-run/device/` 下按 scope 分目录，放这个 scope 的诊断文件 `device-session.json`（能力探测结论、所用的会话与设备、换台记录、从获取设备到释放各阶段的时刻，以及执行前失败的原因与释放时是否有会话未能确认停止）与判为 failed / error 的 step 的原始控件树 `page-source/step-NNNN.xml`（按采集次序编号）；两者写盘前都经过脱敏。会话在 Device Farm 控制台里的录像与日志由 AWS 保留 400 天，存放在 us-west-2（与运行用的 region 无关），到期自动删除（见 [Device Farm 的数据保留](https://docs.aws.amazon.com/devicefarm/latest/developerguide/data-protection.html)）；gherkai 不删除任何会话。要留得更久，自己从控制台或 API 归档；要提前删除，在 Device Farm 控制台删除对应的会话，或执行 `aws devicefarm delete-remote-access-session --region us-west-2 --arn <会话 ARN>`（只能删除已结束的会话），删除后报告与 `explain` 里指向这个会话的控制台链接随之失效。录像会录下设备屏幕上显示的全部内容，在被测应用里登录请使用专用的测试账号。安装包不经 Device Farm 上传，保留期由放它的 S3 桶决定（见[配置](./configuration.md)）。

`--backend cloud` 下没有这棵本地树：提交记录与运行状态在 DynamoDB 的运行记录表里，判定明细与报告在产物桶（`<前缀>artifacts`）的 `<报告前缀>/<run_id>/` 下，相对位置与上面这棵树一一对应；worker 日志在 CloudWatch 日志组 `/<前缀>worker/<引擎>`。

`run` 结束时与 `status` 到终态时都会把三处位置输出到标准错误（stderr），云端后端下给的是 `s3://` 与运行记录表的诊断指针：

```
报告: file:///…/reports/<run_id>/index.html
运行元信息: file:///…/run_meta.json、file:///…/run_state.json
判定明细: file:///…/reports/<run_id>/jobs
```

`--json` 下同一组位置在 `artifacts` 键里。产物分类与每一份该拿来回答什么问题见 [`../internals/artifacts-and-evidence.md`](../internals/artifacts-and-evidence.md)。

## 找回 run_id：`list-runs`

`status` 与 `explain` 都要先有 run_id。换了终端、提交时没有记下、或要查看别人提交的 run 时，用 `list-runs` 列出一个后端里的 run：

```bash
gherkai list-runs                                           # 本机后端，报告落点 reports
gherkai list-runs --backend cloud --prefix gherkai-         # 云端后端
gherkai list-runs --status running --status pending         # 只看还没结束的
gherkai list-runs --limit 50 --json > runs.json
```

- **查哪里**：`--backend`、`--report-dir`、`--prefix`、`--region`、`--profile`、`--ddb-table` 与 `status` 同名同义，同样读项目配置文件（见 [`configuration.md`](./configuration.md)）。一次只列一个后端、一处报告落点，不跨后端查找；要列另一处就换一组定位参数再执行一次。云端后端下 `--report-dir` 与清单无关，给了也忽略。
- **列哪些**：默认列出全部还没结束的 run（`pending`、`running`），加上最近创建的 20 条已结束的 run；`--limit N` 改已结束部分的条数（正整数），还没结束的 run 不受它限制、全部列出。`--status S` 只列这些状态的 run，可重复给出，取值是 `passed`、`failed`、`error`、`skipped`、`aborted`、`pending`、`running`；其中已结束的状态同样受 `--limit` 约束。
- **先后**：新创建的在前。「最近」按创建时间算、不按结束时间：早创建而刚结束的 run 不会因为刚结束就排到前面。创建时间取执行 `run` 或 `submit` 的那台机器的时钟，同一秒内创建的 run 之间先后不定；多台机器向同一个后端提交时，机器之间的时钟偏差会直接体现为清单里的先后。
- **表格**：每行一个 run，列出 run_id、状态、开始与结束时刻（UTC）、各状态的 job 数、版本与说明。
  - 「版本」列只在这个 run 由另一个版本的 gherkai 写出时显示那个版本，读不到时显示「未知」；当前版本写出的 run 这一列留空。对这样的 run 执行 `status` 或 `explain` 时，仍按上面「命令」一节末尾的提交记录格式版本规则处理。
  - 「说明」列放这个 run 的 `message`（云端后台在派发前不能执行它时的原因）。还没结束、由前台 `run` 执行的 run，说明列另有一句「由前台 run 执行：执行它的进程若已不在，它不会再到终态；status --wait 对它只等待、不接力」：前台 `run` 被强制结束或所在的机器失联时，它会一直停在这个状态，不会自行消失。
  - 运行状态读不出的行（多半由其它版本写出）只有 run_id 与版本两列有值，状态列显示「无法读取（可能由其它版本写出），用 status 查看」。这样的行不参与 `--status` 与 `--limit` 的筛选，找到即列出。由更新版本写出、状态值本版本不认识的 run，本机后端列为无法读取，云端后端不会列出。
- **清单为空**：只打一行以「没有找到 run：」开头的提示，点名所查的落点，并提示核对定位参数是否与产生 run 的 `run` 或 `submit` 一致。本机后端分两种说法，都给出解析后的目录：目录不存在时说「报告落点目录 … 不存在（这里还没有落过盘的 run，或路径给错了）」，目录存在而其中没有 run 时说「报告落点目录 … 下没有任何 run」（给了 `--status` 时说没有这些状态的 run）；云端后端给出前缀、region 与运行记录表名。
- **`--json`**：一个 JSON 文档，顶层是所查的落点（`backend`；本机另有 `report_dir`，云端另有 `prefix`、`region`、`ddb_table`），加上 `runs` 数组；清单为空时 `runs` 是空数组，不打人读提示。字段见 [`../internals/cli-json-contract.md`](../internals/cli-json-contract.md)。
- **只读**：不推进任何 run、不启动任务。判定仍对具体的 run 用 `status --wait` 取；退出码见上「退出码」一节。
- **不在清单里的**：`run --no-report` 的执行不留运行记录，两个后端的清单里都没有它。
- **云端后端下刚变化的 run**：状态、时刻与 job 数总是读取那一刻的值；刚提交或刚改变状态的 run 偶尔会在一次清单里缺席，稍后再列即可看到。后端刚升级时清单所用的索引可能还在建立，这段时间 `list-runs --backend cloud` 以退出码 2 结束，见 [`cloud-backend.md`](./cloud-backend.md)「版本与升级」。

## 看失败原因：`explain`

```bash
gherkai explain "$RUN_ID"                                   # 全部 job，默认只展开没过的步
gherkai explain "$RUN_ID" login                             # 只看这一个 scope
gherkai explain "$RUN_ID" --scenario "搜索词条" --step 2      # 点名某条用例的第 2 步（0 起）
gherkai explain "$RUN_ID" --all --full --json > evidence.json
```

- 默认展开状态为失败、出错、被跳过的步；通过的步只列一行。
- `--step N` 点名的那一步连通过也展开，须与 `--scenario` 同给；`--all` 让通过的步也展开。
- 文本形态是摘要：每次 AI 调用只显示最后一段推理与它的截图地址，`--full` 逐帧全文，`--json` 内嵌完整证据。
- job 被中止或出错时（按了 Ctrl-C、超时、fail-fast、worker 被外部停止），没执行完的用例没有判定，但其中已执行完的步 `explain` 仍能显示并带出证据：这些步从这个 run 的事件记录补取，行尾标「记录取自事件流」，所属用例标「未完成」；被中止时还没上报完成记录的那一步没有记录。补不到（例如这个 run 由不写事件记录的旧版本执行）时在该 job 下写明原因。
- `explain` 的退出码从不表示判定结果，用例失败它照样以退出码 0 结束。`submit` 提交的 run 还没到终态时判定明细尚未写出，它会提示先用 `status --wait`；`run` 还在执行时，它显示已完成的 job，并提示这只是已完成的部分。
- 哪一步没有 AI 证据（确定性 step 本就不产，设备目标上只有判为 passed 的确定性与导航 step 不产；或抽取当时失败了），它会明说，并给出该步其它产物的链接。
- 设备目标上，判为 failed / error 的确定性与导航 step 也有证据（没有 AI 调用，`acts` 为空）。设备的证据多几项：这一步的执行方式 `step_kind`（`ai` / `deterministic` / `navigation`）；step 结束时的页面地址 `url`，取不到时 `url_missing` 说明原因（设备不提供网页上下文、应用目标没有地址、读取超时或出错）；判为 failed / error 的 step 另有控件摘要 `controls`（每个控件的类型、id、文本与无障碍标识，条数有上限、超出时注明截断）与原始控件树文件 `page_source`（只给地址，超过大小上限时截断并以 `page_source_truncated` 注明）。设备 job 另有一条 `device_session` 链接，指向上面的 `device-session.json`，`explain` 只给链接、不解析它。地址读取与控件采集按 step 累加计入 job 墙钟预算。

## 费用量级

`plan`、`list-runs`、`list-engines`、`list-deterministic`、`doctor` 都是本地或只读操作，不产生模型费用。`run` 与 `submit` 每次都会真实消耗 AWS 费用：桌面目标是模型调用与云端浏览器会话的费用；设备目标是模型调用与 Device Farm 远程访问会话的费用。远程访问会话按设备分钟计费，一个设备 scope 通常只建一个会话；获取设备期间设备拒绝安装驱动辅助程序而换一台时（至多一次），被替换的那个会话同样计费。设备分钟从服务商开始准备设备起算，并发槽位满时的排队等待不计费；准备设备到可用的时间约 1 到 2.5 分钟，通常计费；停止会话后的收尾可能继续计费。设备分钟按量约 0.17 美元每分钟，一条 5 步左右的设备 scenario 一次大约 3 到 5 设备分钟；每平台每月用量很大时（约 1470 设备分钟以上），不计量槽位（约 250 美元每月）更省：须先在 AWS 为对应平台购买不计量设备槽位，再把 `gherkai.toml` 的 `billing-method` 设为 `UNMETERED`；没有槽位时服务商在准备阶段就结束会话，见 [`configuration.md`](./configuration.md)「项目配置文件」。设备 job 结果里的「设备占用时长」（`--json` 的 `device_observed_s`）是 worker 观察到的时长，与账单上的设备分钟口径不同，以账单为准。量级上，一条 5 步左右的 scenario 在 Midscene 默认模型（`us.openai.gpt-5.6-terra`）上约 5 美分，换成 `qwen.qwen3-vl-235b-a22b` 约 2 美分（按 2026-09 Bedrock 标价与一条 5 步示例用例的 token 用量估算，以账单为准），Nova Act 引擎按 Nova Act 服务计费。换模型的办法见 [`configuration.md`](./configuration.md)「模型选择」。每个 job 都有 job 墙钟预算（桌面 scope 默认 300 秒，设备 scope 默认为获取预算加 900 秒），超出即被停掉，防止任务卡住时持续计费。

## 机读输出

运行与查询的命令都有 `--json`：`plan`、`run`、`status`、`list-runs`、`explain`、`list-engines`、`list-deterministic`、`doctor`（部署方的 `gherkai deploy list-workers` 也有，见 [`cloud-backend.md`](./cloud-backend.md)）；`submit` 没有这个选项，它的 stdout 本来就只有一个 `run_id`。通则：stdout 只有一个 JSON 文档，进度与诊断一律走 stderr，所以 `gherkai run … --json > result.json` 拿到的是纯净 JSON、进度仍在终端可见。字段名、类型与出现条件见 [`../internals/cli-json-contract.md`](../internals/cli-json-contract.md)。

## 在 CI 里运行

前台运行时，一条命令的退出码就表示判定结果：

```bash
gherkai run features/*.feature --quiet --max-concurrency 2
```

后台运行把提交与收结果拆开，表示判定结果的退出码来自 `status --wait`：

```bash
RUN_ID=$(gherkai submit features/*.feature --backend cloud --prefix gherkai-)
gherkai status "$RUN_ID" --backend cloud --prefix gherkai- --wait --json > result.json
rc=$?
if [ "$rc" -eq 1 ]; then
  gherkai explain "$RUN_ID" --backend cloud --prefix gherkai-   # 有用例没过：把证据输出到构建日志
fi
exit "$rc"
```

三条注意：不带 `--wait` 的 `status` 在 run 还没结束时退出码为 0，不能当判定门；`explain` 只渲染证据、也不能当判定门；`submit` 的退出码只说提交成功了。示例 `.feature` 在 [`features/`](../../features/) 目录，可直接用来验证流水线是否接对。
