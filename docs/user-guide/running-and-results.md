# 运行测试与查看结果

运行 `.feature`、查看结果与读退出码涉及以下内容：执行方式与执行后端三种组合的选择、`plan` / `run` / `submit` / `status` / `list-runs` / `settle-runs` / `explain` / `list-engines` / `list-deterministic` / `doctor` 的用途与常用选项、停住的 run 怎样结束、报告与证据的位置、费用量级、机读输出与 CI 用法。安装与 AWS 前置见 [`getting-started.md`](./getting-started.md)，`.feature` 的写法见 [`writing-features.md`](./writing-features.md)，`--expose-local` 测本机应用见 [`local-app-testing.md`](./local-app-testing.md)，云端后端的部署与维护见 [`cloud-backend.md`](./cloud-backend.md)，项目配置文件、环境变量与跨命令通用选项见 [`configuration.md`](./configuration.md)。任一命令的完整选项以 `gherkai <命令> --help` 为准。

## 怎么运行、在哪运行：三种组合

执行方式与执行后端合起来有三种组合：本机前台（`run`）、本机后台（`submit --backend local`）、云端后台（`submit --backend cloud`）。云端后端只有后台运行：`run` 只在本机后端执行，`--backend cloud`（无论在命令行上给出还是写在项目配置文件里）会让 `run` 在开始执行之前以退出码 2 结束，并提示云端后端的执行用 `gherkai submit --backend cloud`。

**怎么运行**

| 执行方式 | 命令 | 特点 |
|---|---|---|
| 前台 | `gherkai run <feature...>` | CLI 全程在线，运行结束后直接输出判定与产物位置，退出码就是判定。CLI 进程结束（如终端关闭）这个 run 即停止，记录停在未结束，可用 `settle-runs` 记为已结束（见下「结束停住的 run」）；机器休眠时 CLI 随之暂停、唤醒后继续，休眠的时长计入各 job 的预算与允许运行的时间（见下「允许运行的时间」） |
| 后台 | `gherkai submit <feature...>` 再 `gherkai status <run_id>` | `submit` 等这个 run 建好即打印一个 `run_id` 并退出，后台继续执行；用 `status` 查进度，`status --wait` 等到运行结束并拿判定 |

**在哪运行、落在哪**（`--backend`）

| 后端 | worker 运行在 | 结果落在 | 前置 |
|---|---|---|---|
| `local`（默认） | 本机子进程 | `--report-dir` 指的本地目录 | 本机装好要用的引擎 worker，有 AWS 凭证 |
| `cloud` | Fargate 容器 | 状态与提交记录落 DynamoDB，判定明细与报告落 S3 的产物桶（`<前缀>artifacts`） | 部署方先执行过 `gherkai deploy`，提交时给同一个 `--prefix` |

`submit --backend local` 在本机起一个脱离 CLI 的后台推进进程，由它建立这个 run 并执行到结束，本机要保持开机，这个进程中途退出时 run 不会再往下执行（见下「结束停住的 run」）；`submit --backend cloud` 提交完即可关机，云端自己把这个 run 执行完；只有用 `--expose-local` 时例外——隧道在本机，要保持开机联网到这个 run 结束。

下面各级需要的权限不同、费用记到的账户也不同（`plan` 不需要凭证，单列一行）。

| 命令与后端 | 需要什么 | 费用记到 |
|---|---|---|
| `plan` | 不需要凭证（装了 worker 才有确定性 step 的派发标注） | 不产生费用 |
| `run` / `submit`，`--backend local` | 本机 AWS 凭证与要用的引擎 worker | 自己的 AWS 账户 |
| `submit` + `status`，`--backend cloud` | 运行记录表读写、若干只读检查、调用后端 Lambda、产物桶（`<前缀>artifacts`）`definitions/` 前缀上的写对象权限（每次提交都写这个 run 的 job 列表）；有应用目标（`@app`）的 scope 时另需该桶 `apps/` 前缀的读、写、列举与打标签。不需要任何 ECS 写权限 | 部署方的 AWS 账户 |
| `list-runs` | 本机后端不需要凭证；云端后端只需读权限：运行记录表与它的清单索引、版本戳参数与表结构的只读检查 | 本机后端不产生费用；云端后端只有少量读请求，记到部署方的 AWS 账户 |
| `settle-runs`（只处理本机后端） | 不需要凭证 | 不产生费用 |

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
| `gherkai submit <feature...>` | 提交这个 run，建好即返回，stdout 只有一个 `run_id` | `--backend`、`--max-concurrency`、`--report-dir`、`--prefix`、`--worker-variant` |
| `gherkai status <run_id>` | 查这个 run 的进度与结果；到终态时同时输出三处产物位置 | `--wait`、`--backend`、`--report-dir`、`--prefix`、`--json` |
| `gherkai list-runs` | 列出一个后端里的 run，用来找回 run_id：默认列出全部未结束的 run 与最近创建的 20 条已结束的 run。只读，见下「找回 run_id」 | `--backend`、`--report-dir`、`--prefix`、`--status`、`--limit`、`--json` |
| `gherkai settle-runs [<run_id>]` | 把执行它的 gherkai 进程已不在、或已过允许运行的时间之后再过 5 分钟仍没有结束的本机 run 记为已结束；不给 run_id 时处理报告目录里全部未结束的 run，并清理建立 run 时中断留下的暂存目录。见下「结束停住的 run」 | `--dry-run`、`--report-dir`、`--json` |
| `gherkai explain <run_id> [<scope_id>]` | 看每一步的证据：问了 AI 什么、AI 看见了什么、为什么这么判。用例没过时先运行这个命令 | `--scenario`、`--step`、`--all`、`--full`、`--json` |
| `gherkai list-engines` | 列出本机两个引擎 worker 的拉起命令与来源，没装的那个在同一行给出安装提示 | `--json` |
| `gherkai list-deterministic` | 列出某个引擎支持的确定性 step（含项目 `steps/` 里的），写 feature 时据此复用 | `--engine {midscene,novaact}`（默认 `novaact`）、`--steps-dir`、`--json` |
| `gherkai doctor` | 只读自检：CLI 版本、引擎 worker、实际使用的模型、`steps/` 加载结果；装了部署工具链（Node、cdk、容器引擎）时连带自检它；给了 `--backend cloud` 或 `--prefix` 时再查凭证、后端资源与后端版本 | `--backend cloud`、`--prefix`、`--report-dir`、`--steps-dir`、`--json` |
| `gherkai --version` | 打印 CLI 版本 | — |

`status`、`list-runs`、`settle-runs` 与 `explain` 的 `--backend`、`--report-dir`、`--prefix` 必须与产生这个 run 的 `run` 或 `submit` 一致（前台运行与后台提交都算），云端后端下 `--region` 也要指向同一个 region，否则查不到这个 run：`status`、`explain` 与给了 run_id 的 `settle-runs` 以退出码 2 结束，`list-runs` 列出的是另一处的 run（常见为空清单）。云端后端的 `list-runs` 不读报告，不看 `--report-dir`。`status --wait` 等到这个 run 结束再按判定给退出码。本机后端下它只等待、不推进，前台与后台的 run 相同：执行这个 run 的 gherkai 进程已不在，或已过允许运行的时间之后再过 5 分钟仍没有结束时，它把这个 run 记为已结束、在标准错误说明一句，再照常显示并给退出码（见下「结束停住的 run」）。云端后端下，后台推进停止或卡住时，这条命令会触发云端接着把这个 run 推进到终态。`doctor` 的读法与按症状分表的处置见 [`troubleshooting.md`](./troubleshooting.md)。

使用云端后端时 CLI 不能新于后端：CLI 与后端都是正式发行版本、且 CLI 比后端新时，`submit`、`status`、`list-runs` 与 `explain` 在读写云端之前即以退出码 2 结束。比对规则、后端没有版本戳时的处理与升级顺序见 [`cloud-backend.md`](./cloud-backend.md)「版本与升级」。

提交记录带格式版本。`status`（`--wait` 时在开始等待之前）与 `explain` 读到的提交记录格式与本机 CLI 支持的不一致时以退出码 2 结束并点名写出它的版本：由更新版本写出的请升级本机 CLI，由更早版本写出的用那个版本查看（`uvx --from 'gherkai==<版本>' gherkai status …`）或用当前版本重新提交；`settle-runs` 把这样的 run 记为跳过、不改动它，请用写出它的版本处理。**同一个报告目录不要混用 1.4 与 1.5 的 CLI 读写**：1.4 的 CLI 读 1.5 的记录会静默误判，1.5 的 CLI 读 1.4 的记录直接拒绝。`submit --backend cloud` 提交的 run 在云端读到不能执行的提交记录时，把这个 run 与其中还没结束的 job 都记为 `error`，并在 `status` 的 `message` 行里给出原因（`--json` 下是顶层 `message` 键，各 job 的 `message` 是同一句），这样的 run 没有报告；因超过允许运行的时间、`--fail-fast` 或中断而有 job 没有启动的 run 同样有这一行，说明余下的 job 为什么没有启动（见下「允许运行的时间」与「退出码」）；执行它的进程不在了、由 `settle-runs` 或 `status --wait` 记为已结束的 run 也有，说明它为什么结束（见下「结束停住的 run」）。只有这几类 run 有这一行，job 自身的失败原因看 `explain`。

## 常用选项（`run` / `submit`）

**只运行一部分**（`plan` 认同一组选项）

| 选项 | 说明 |
|---|---|
| `--scope ID` | 只运行这些 scope。值是报告与 JSON 里的 `scope_id`：`@scope` 的名字，或未标 scope 时的 `<文件>:<行号>`。可重复，任一命中。重新运行某个失败的 job 用它最直接 |
| `--tags TAG[,TAG...]` | 只运行带这些 tag 的 scenario。一个值内用逗号分隔表示任一命中，重复给本选项表示都要命中；`@` 可省。feature 行上的 tag 对其下每个 scenario 生效 |
| `--scenario SEL` | 只运行这些 scenario。`SEL` 可以是完整 scenario id、行号（`12` 或 `:12`，纯数字只当行号）、或标题的一段文字（区分大小写）。可重复，任一命中 |

三者同给时都要满足。筛掉一部分时命令会打印一行 `筛选：<已选>/<总数> scenario`，后面附上你给的筛选条件；一条都没选中时以退出码 2 结束并列出这个 run 的全部候选（id、标题、tags），不会静默执行一个空 run。不加任何筛选时，给出的 `.feature` 文件里一个 scenario 都没有（例如只有 Feature 头，或 Scenario Outline 的 Examples 没有数据行），`plan`、`run`、`submit` 同样以退出码 2 结束并提示 `没有可执行的 scenario`，不会启动一个空的 run。一个 run 至多 500 个 job，按筛选之后的数计：超过时 `plan`、`run`、`submit`（本机与云端后端相同）以退出码 2 结束，说明给出这次的 job 数与拆成几个 run 的办法；`@scope` 的值与 scenario 编号的长度上限见[编写 .feature](./writing-features.md)的「有语义的 tag」。

**执行**

| 选项 | 默认 | 说明 |
|---|---|---|
| `--default-engine {midscene,novaact}` | `novaact` | 未标 `@engine` 的 scope 用哪个引擎；标了 tag 的 scope 不受影响 |
| `--assertion-votes N` | `1` | AI 断言执行 N 次取多数票（如 3 或 5），用于降低判定抖动。取 1 到 5，超出时在开始执行前以退出码 2 结束；取值与上限的理由见[编写 .feature](./writing-features.md)的「投票」 |
| `--max-concurrency N` | `4` | 同时运行的 worker 上限，须 ≥ 1。并发只改同时开几个会话（桌面目标是浏览器会话，设备目标是远程访问会话），不改 job 数与总费用；配额紧时调低。`submit --backend cloud` 提交时若超过云端后端对单个 run 的并发上限（当前为 20，见 [`cloud-backend.md`](./cloud-backend.md)），命令会提示并按该上限并行 |
| `--default-job-timeout S` | 按目标 | job 墙钟预算，单位为秒。不给时桌面 scope 为 300 秒，设备 scope 为获取预算（`[devices]` 的 `acquire-timeout-s`）加 900 秒；给 `<=0` 对任何目标都取最长的 7200 秒（2 小时）；给正值时不得超过 7200 秒，设备 scope 还不得低于获取预算加 180 秒；用例上标 `@timeout:<秒>` 可逐 scope 覆盖。超预算的 job 被停掉并判 error |
| `--grace S` | 自动 | 仅 `run`：中止时留给 worker 收尾的秒数，收尾包括释放会话（桌面目标是云端浏览器会话，设备目标是远程访问会话）与保存产物；不给则按这个 run 用到的引擎自报的最短收尾宽限推导。比这个宽限更短时，worker 可能在释放会话或保存产物之前被强制终止，没释放的会话继续计费，所以给出更小的值时命令在开始执行前以退出码 2 结束。云端后端的停止宽限在部署时定，写在 `gherkai.toml` 里的 `grace` 在 `submit --backend cloud` 下只提示一句、不生效 |
| `--fail-fast` | 关 | 仅 `run`：任一 job 出错即中止这个 run 的其余 job：执行中的记 `aborted`，还没有启动的记 `skipped`，run 记 `error` |

单个 job 的网络故障只让那个 job 判 error，其余 job 继续；给了 `--fail-fast` 才会因此中止这个 run。

**允许运行的时间**

每个 run 在提交时得到一个允许运行到的时刻，记在提交记录里（`--json` 下是 `run_meta.deadline_at`），之后不变。它由各 job 的墙钟预算推出：各 job 预算之和，加一次性的 900 秒，再加每个 job 一段收尾余量（本机后端为停止宽限的两倍加 10 秒，云端后端为 210 秒）。它按 job 串行执行累加，并发时更宽，正常的 run 远在它之前结束；运行期间发起的机器休眠过、命令进程被暂停过，或某次云端调用长时间没有返回，才可能到达它。

前台 `run`（`--no-report` 同样）与 `submit` 提交的后台 run 都遵守这个时刻：

- 离这个时刻不到 60 秒时，不再启动新的 job。
- 正在执行的 job 的截止时刻取它自己的预算到点与这个时刻中较早的一个（两者相同时算预算到点）。被这个时刻截断的 job 记 `aborted`、没有归因，说明是「这个 run 已超过允许运行的时间，job 被中止」：run 的时间用完不是这个 job 自己出错，它也不触发 `--fail-fast`。自己的预算不晚于这个时刻到点的，仍判 `error`、归因 `timeout`，说明是「job 超时（预算 …s，已中止）」，运行期间休眠过时多是这种（见下）。截止时刻之后、被停下之前就自己异常退出的 job 同样按到点处理；已经报完全部结果、只是收尾越过截止时刻的 job 保留原有判定。
- 这时仍有 job 没有启动的 run，在正在执行的 job 都结束之后结束：没有启动的 job 记 `skipped`，说明是「这个 run 已超过允许运行的时间，job 没有启动」，它们没有判定明细；run 级写下说明「已超过允许运行的时间」，`run` 的文本汇总与报告首页在总状态下给出这句，并把这些 job 连同各自的说明列在有判定明细的 job 之后。`status` 的 `message` 行、`status --json` 与 `run --json` 顶层的 `message` 都是同一句；`run --json` 的 `jobs` 按提交的次序列出全部 job，这些 job 只带 `scope_id`、`status` 与 `message`。总状态按各 job 的状态得出：有 job 出错为 `error`，否则有用例失败为 `failed`，否则为 `aborted`（这个 run 没有执行完）。重新运行时用 `--scope` 只选 `skipped` 与 `aborted` 的 job，以及归因 `timeout` 的 job。全部 job 都启动了的 run 不带这句说明，总状态同样按各 job 的状态给出。

后台 run 由推进它的一方执行这些规则：

- `submit --backend local`：本机的后台进程在截止时刻停下正在执行的 job，它们结束之后收尾。这个进程已不在时（被结束、机器重启过），没有别的进程接着执行这个 run：用 `settle-runs` 或 `status --wait` 把它记为已结束（执行中的 job 记 `aborted`、没有启动的记 `skipped`），见下「结束停住的 run」。前台 `run` 的进程已不在时同样如此。
- `submit --backend cloud`：每个 job 在云端的到点停止以这个时刻封顶，后端在截止时刻之后停下正在执行的 job（定时服务只承诺分钟精度，停下的时刻会略晚于截止时刻），到期之后的收尾由它们被停下而引出。某个 job 在截止时刻没能被停下、又一直没有任何输出时，后端没有别的东西去推进这个 run，用 `status --wait` 接力即可。

job 的墙钟预算从这个 job 被安排执行时起按系统时钟计，前台 `run` 与后台 run 相同：前台 `run` 与 `submit --backend local` 运行期间你的机器休眠过的，休眠的时长同样计入。

**输出与落盘**

| 选项 | 默认 | 说明 |
|---|---|---|
| `--report-dir DIR` | `reports` | 报告落点，每次 run 落 `DIR/<run_id>/`。本机后端下这个目录要在受支持的本机文件系统上，见下「本机后端的报告目录」。`status` 与 `explain` 查同一个 run 要给同一个值。云端后端下它是后端的报告前缀，与部署侧不一致时 `submit` 在提交前以退出码 2 结束并点名两侧的值 |
| `--no-report` | 关 | 仅 `run`：报告目录下什么都不落，也不收集引擎自己的报告产物。适合 CI 只看退出码或 JSON |
| `--quiet` | 关 | 仅 `run`：不输出逐事件进度，仍输出文本汇总。worker 日志改落 `<report-dir>/<run_id>/worker.log`（`--no-report` 时落系统临时目录），只打印一行位置 |
| `--json` | 关 | 仅 `run`：标准输出只打机器可读 JSON、不打文本汇总；进度与诊断照常走标准错误，逐事件进度可用 `--quiet` 静音 |
| `--steps-dir DIR` | `./steps` | 项目自己的确定性 step 目录，也可用环境变量 `GHERKAI_STEPS_DIR`。目录里任一文件加载失败即整个 run 拒绝运行。云端后端下不生效（云端 worker 的 step 构建在镜像里，只警告不拦），写法见 [`writing-deterministic-steps.md`](./writing-deterministic-steps.md) |
| `--expose-local ORIGIN` | — | 把本机可达的被测应用经隧道暴露给云端浏览器与设备上的浏览器（只用于网页目标，原生应用不适用），需要安装 gherkai 的 tunnel 组件并设置环境变量 `NGROK_AUTHTOKEN`；配套的 `--tunnel`（两条命令都有）与前置见 [`local-app-testing.md`](./local-app-testing.md) |

**本机后端的报告目录**

本机后端下，报告目录（`--report-dir` 选项，或配置文件里的 `report-dir`）要满足下面几条：

- **在这台机器的本机文件系统上**。支持的文件系统类型：macOS 支持 apfs；Linux 支持 ext4、tmpfs、overlay、xfs、btrfs、ext3。别的类型都不支持，例如网络文件系统（NFS、SMB）、FUSE 挂载，以及经虚拟机共享进来的目录（如 macOS 上的 Docker Desktop 从宿主挂载进容器的目录）。
- **可读可写**：gherkai 在它下面为每个 run 建立目录并写入记录；它还不存在时由 gherkai 建出。
- **路径不要太长**：解析之后（换成绝对路径、展开其中的符号链接）不超过 470 字节，按文件系统编码计（ASCII 字符占 1 字节，一个汉字通常占 3 字节）；路径里每一层的名字也要在所在文件系统允许的长度之内，还不存在、要由 gherkai 建出的那几层同样（一层 100 个汉字的名字在 macOS 的 apfs 上可以用，在 Linux 的 ext4 上太长）。每个 run 的记录、事件库与产物都放在它下面，路径再长就建不出或打不开。不满足时，`run`（不带 `--no-report`）、`submit --backend local`、`status`（含 `--wait`）、`explain`、`list-runs` 与 `settle-runs` 在访问报告目录之前以退出码 2 结束、什么都不建，说明分两种：路径太长，或路径里有一层名字太长。
- **不要放在文件同步服务的文件夹里**（如 iCloud Drive、Dropbox、OneDrive 的同步文件夹）。这类文件夹所在的文件系统本身受支持（macOS 上是 apfs），检查会放行，但其中的内容会同步到别的机器；gherkai 只能在同一台机器上确认执行 run 的进程是否还在，两台机器同时读写同一个 run 时，记录可能互相覆盖。
- **多台机器共用运行记录用云端后端**（`submit --backend cloud`），不要让多台机器共用一个本机后端的报告目录。

给出的报告目录在命令开始时解析成绝对路径（展开其中的符号链接），之后都用这一个：输出与说明里的报告目录、run 的目录与各文件的位置，以及提示里给出的整条命令（查进度的 `status`、确认用的 `list-runs`、把 run 记为已结束的 `settle-runs`）带的 `--report-dir`，都是解析之后的绝对路径。换了工作目录、或原来给的符号链接改了指向之后，照抄这些命令仍然找到同一个 run。

报告目录所在的文件系统不受支持、或判断不了时，`run` 与 `submit --backend local` 在开始执行之前以退出码 2 结束，不建立 run；说明写出检测到的文件系统类型（判断不了时写出原因）与上面的清单，判断不了时另说明换了目录仍然判断不了可以改用云端后端。这一项在开始执行之前的检查里就会查出：在那里查出时，不上传安装包、不起隧道，`submit` 也不启动后台推进进程，什么都不建立。建立 run 时还会再检查一次这个位置：检查之后它所在的文件系统变了（例如在那个位置挂载了别的文件系统）而不受支持或判断不了时，同样以退出码 2 结束、不建立 run，说明相同；这时上传安装包、起隧道这些准备可能已经做过（起过的隧道随即关闭）。报告目录还不存在时，按它最近一层已存在的上级判断；经符号链接给出的报告目录，按链接指向的位置判断，run 也建立在那里。打不开报告目录（路径上有一层是文件而不是目录、没有权限）时，同样在开始执行之前以退出码 2 结束，说明与在报告目录里写记录失败时相同。`settle-runs` 与 `status --wait` 把 run 记为已结束之前同样先做这项检查：报告目录（`settle-runs`）不受支持时以退出码 2 结束、不处理其中的 run，某个 run 的目录不受支持时 `settle-runs` 跳过它、`status --wait` 以退出码 2 结束，说明写法相同。`run --no-report` 不落报告目录，不做这项检查；`plan` 也不做。

**云端后端（`submit --backend cloud`）**：`--prefix P`（默认 `gherkai-`，兜底环境变量 `AWS_RESOURCE_PREFIX`）须与部署时一致，统一决定表、桶、集群等资源名；`--worker-variant NAME` 选云端 worker 镜像的 variant，不给则用部署时的默认指针，某个引擎缺这个 variant 直接以退出码 2 结束、不回落到默认，见 [`cloud-backend.md`](./cloud-backend.md)。worker 任务所在的集群、子网与安全组用的是部署时写进后端的配置，提交时不用给。单独覆盖某个资源名的选项见 [`configuration.md`](./configuration.md)。

## 退出码

每条命令的退出码回答的是不同的问题。本页这几条命令里，退出码表示判定结果的只有 `run` 与 `status`，也只有它们的退出码会是 1；部署方命令的退出码见 [`cloud-backend.md`](./cloud-backend.md)。

| 命令 | 退出码回答什么 | `0` | `1` | `2` |
|---|---|---|---|---|
| `run` | 判定 | 这个 run 全部通过 | 有用例失败或出错，或有 job 被中止、没有启动（`--fail-fast`、超过允许运行的时间）；这个 run 在本次执行结束之前已被别处记为已结束（这时不输出汇总，见下） | 开始执行前的配置或可达性问题，含起隧道失败、报告目录的路径太长或其中一层名字太长、报告目录所在的文件系统不受支持，以及在报告目录里建立这个 run 失败（写记录失败、给 run 的目录加锁失败等）；给出了云端后端（`run` 只在本机后端执行，云端后端用 `submit --backend cloud`） |
| `status`（不带 `--wait`） | 查到了吗 | 查到了，含还没结束的 run | 读到的终态不是全部通过 | run 不存在、云端不可达、CLI 与后端版本不匹配、提交记录的格式版本与本机 CLI 不一致或记录不完整、运行状态记录读不出、读取记录失败、本机后端的报告目录路径太长或其中一层名字太长 |
| `status --wait` | 判定 | 运行结束且全部通过 | 运行结束但不是全部通过（有用例失败或出错，或有 job 被中止、没有启动，run 级记 `aborted`）；本命令把它记为已结束的 run 同样如此 | 同上（提交记录的格式版本不一致的，在开始等待之前即结束；提交记录不完整的 run 可以被本命令记为已结束，之后显示它时同样以 2 结束），另加后端没部署或 `--prefix` 配错；本机后端下等待期间 run 被删去、运行状态记录读不出或在 run 的目录上加锁出错而提交记录也读不出（这两种不等待）、run 的目录所在的文件系统不受支持，或读写运行记录失败（这时本命令没有把它记为已结束） |
| `submit` | 提交成功了吗 | 已提交，`run_id` 已打印 | — | 配置或可达性问题、起隧道失败、建立 run 失败；本机后端下报告目录的路径太长或其中一层名字太长，或所在的文件系统不受支持（`submit` 在启动后台推进进程之前的检查里查出，检查之后那个位置所在的文件系统才变了的，由后台推进进程建立 run 时再检查一次查出）；本机后端下后台推进进程在给出提交结果之前退出（这时 run 可能已经建立，见下） |
| `plan` | 这个 run 能运行吗 | 能 | — | 配置错、写法错、`steps/` 里有文件加载失败 |
| `list-runs` | 读到清单了吗 | 读到了；清单为空、或其中有无法读取的行，同样以退出码 0 结束 | — | 参数不合法（`--limit` 不是正整数、`--status` 不是 run 的状态值）、本机后端的报告目录路径太长或其中一层名字太长、本机报告落点目录不可读、云端读不到（region 或凭证、运行记录表不存在或无权限、清单索引缺失或还在建立、读取被限流后重试仍未读全）、CLI 与后端版本不匹配 |
| `settle-runs` | 处理完了吗 | 处理完了，含一个都没有处理、各种跳过（暂存目录的跳过同样） | — | 给出的 run 不存在、报告目录的路径太长或其中一层名字太长、报告目录所在的文件系统不受支持、给出了云端后端（这个版本只处理本机后端）、读写记录失败（就此停止，先输出已处理的部分）；被 Ctrl-C 打断、还有没处理的项时为 130（收到 SIGTERM 时为 143），同样先输出已处理的部分；处理最后一项期间或输出期间才收到的中断不改变退出码 |
| `explain` | 证据读出来了吗 | 渲染出来了，用例判失败也以退出码 0 结束；判定明细尚未写出同样如此 | — | 参数写错（例如 `--step` 没同时给 `--scenario`）、run 或 scope 查不到、本机后端的报告目录路径太长或其中一层名字太长、本机后端下这个 run 的运行状态记录读不出、运行记录指向的那一份判定明细读不到（被删除或移动）、云端读不到、CLI 与后端版本不匹配、提交记录的格式版本与本机 CLI 不一致或记录不完整 |
| `doctor` | 必修项都过了吗 | 全过 | — | 任一必修项失败（可选能力缺失只标 `-`，不影响退出码） |
| `list-deterministic` | 这个引擎有哪些确定性 step | 列出来了 | — | `--steps-dir` 指的不是目录、worker 定位不到、`steps/` 加载失败、该引擎的 worker 自述失败（多为 worker 与 CLI 版本不一致，处置见 [`troubleshooting.md`](./troubleshooting.md)） |
| `list-engines` | 这台机器的引擎环境什么样 | 恒 `0`（某个引擎没装正是要展示的信息，不算命令失败） | — | — |
| `skill install` | agent skill 装上了吗 | 已安装（`--print` 则已打印正文） | — | `--dir` 不是目录、目标目录里已有不是本命令装的内容、包内 agent skill 缺失、写入失败 |

前台 `run` 运行期间处理了中断时退出码不表示判定：按一次 Ctrl-C（或向 CLI 进程发 SIGTERM），CLI 请求全部 worker 停止并等它们释放会话，然后照常输出汇总与产物位置；退出码为 130（Ctrl-C）或 143（SIGTERM），与各 job 的判定无关。执行中被停下的 job 记 `aborted`（说明「收到中断信号：本 job 被中止」），还没有启动的 job 记 `skipped`（说明「收到中断信号，本 job 没有启动」，没有判定明细），run 级写下说明「收到中断信号，余下的 job 不再启动」；总状态按各 job 的状态得出：有 job 出错为 `error`，否则有用例失败为 `failed`，否则为 `aborted`。中断之前已经超过允许运行的时间、或已因 `--fail-fast` 不再启动 job 的，说明取先发生的那一种。全部 job 都已结束之后（收尾、生成报告与输出汇总期间）才收到的中断不改变结果，退出码照常按判定给出。给 worker 的释放宽限由 `--grace` 指定，到期强制结束 worker、再收集结果，再按一次 Ctrl-C 则立即强制结束。强制结束后会话可能来不及释放、继续计费，请到 AWS 控制台核对并手动停止（设备目标看 Device Farm 的远程访问会话，桌面目标看 AgentCore 的浏览器会话）。用 `kill -9` 结束本机 CLI 进程时 worker 收不到任何通知，通常在 CLI 退出后的几秒内检测到并开始释放会话；CLI 已退出但尚未被它的父进程回收、或进程号已被复用时，这项检测可能延后或不触发。释放完成所需的时间取决于当时正在执行的操作与收尾。

开始执行之前按 Ctrl-C（起隧道期间、在报告目录里建立这个 run 期间），`run` 以退出码 130 结束，标准输出为空，不打印异常栈。还没有建立这个 run 时，说明还没有开始执行。这个 run 的记录已经写下时，`run` 自己把它记为已结束，与执行期间被中断是同一种情形，只是一个 job 都还没有启动：全部 job 记 `skipped`（说明「收到中断信号，本 job 没有启动」），run 级写下「收到中断信号，余下的 job 不再启动」，总状态为 `aborted`；随后生成报告，说明给出它的 `run_id`、说它已因中断记为已结束，并给出查看它的 `status` 命令。这时不打印「开始运行」那一行。把它记为已结束时写不进运行记录的（磁盘已满等），说明写明没有 job 开始执行、这个 run 在记录里停在未结束，并给出把它记为已结束的 `gherkai settle-runs <run_id> --report-dir <目录>` 命令。起好隧道之后、启动第一个 job 之前收到 SIGTERM 时同样如此，退出码为 143。

前台 `run` 还有两种情形不输出汇总（`--json` 时 stdout 为空），说明在标准错误：这个 run 在本次执行结束之前已被别处记为已结束，本次执行不覆盖那条记录、不生成报告，在这之后得出的结果也不写进记录，以退出码 1 结束；运行期间写不进或读不出这个 run 的运行记录（磁盘已满、报告目录没有写权限等），执行中的 job 被停下，说明写明记录在哪里、怎样查看，以非零退出码结束，这时执行中的 job 在记录里仍为 `running`、这个 run 停在未结束，说明最后给出把它记为已结束的 `gherkai settle-runs <run_id> --report-dir <目录>` 命令，排除磁盘或权限问题之后执行它、再重新执行；存一个 job 的判定明细失败时，`run` 先按 1、2、4 秒的间隔重试三次，每次重试之前在标准错误留一句警告，重试期间别的 job 的启动与记录随之等待，仍失败才这样结束；重试期间收到的中断（Ctrl-C 或 SIGTERM）要等重试结束才处理：重试写成时照常处理，仍失败时不再处理、退出码不按信号取。结果已全部写进记录、只是输出汇总之前读回记录失败时（含运行记录指向的那一份判定明细已不在），说明写明记录已是这个 run 的最终状态、不必重新执行，这时也不生成报告。两种情形都用 `gherkai status <run_id>` 查看记录，处理过中断时退出码仍为 130 或 143。

`submit --backend local` 的后台进程遇到同样的失败（存判定明细同样先重试三次），或读不出这个 run 的事件记录时，在 `reconcile.log` 里留一句说明后退出，不打印异常栈：说明写明记录在哪里，执行中的 job 在记录里仍为 `running`；排除磁盘或权限问题之后，用说明里给出的 `gherkai settle-runs <run_id> --report-dir <目录>` 命令把这个 run 记为已结束，再重新提交。它读不出这个 run 的运行状态记录而退出时，`settle-runs` 也不改动这个 run（见下「结束停住的 run」），说明里写的是这一点与怎么办。

`submit` 要等这个 run 建好才退出。本机后端下 run 由 `submit` 在本机起的后台推进进程建立（用了 `--expose-local` 时它先起隧道），`submit` 收到它的结果之后打出查进度的命令、在标准输出给出 `run_id`；后台推进进程在给出结果之前的输出（包括它出错退出时的原因）显示在 `submit` 的终端上，之后的写进 `reconcile.log`。云端后端下 `submit` 自己把 run 写进云端（用了 `--expose-local` 时先由本机的隧道守护进程起隧道，见 [`local-app-testing.md`](./local-app-testing.md)）。没有建成时 `submit` 给出原因、以退出码 2 结束，标准输出为空。本机后端下报告目录所在的文件系统不受支持时，`submit` 在启动后台推进进程之前的检查里查出即以退出码 2 结束，说明与前台 `run` 是同一句；检查之后那个位置所在的文件系统才变了的，由后台推进进程在建立 run 时再检查一次查出，同样不建立 run、以退出码 2 结束，说明也是这一句；后台推进进程在报告目录里建立这个 run 失败时（写记录失败、给 run 的目录加锁失败等），说明同样与前台 `run` 相同；记录已经写下而准备执行用的文件失败时，说明这个 run 在记录里停在 `pending`、还没有开始执行，并给出把它记为已结束的 `gherkai settle-runs <run_id> --report-dir <目录>` 命令，之后重新提交（前台 `run` 在同一处失败时说明相同，只是请你重新执行）。本机后端下后台推进进程在给出结果之前退出时，`submit` 说明它可能已经建立了这个 run，并给出不带 run_id 的 `gherkai settle-runs --report-dir <目录>` 命令：它把这个报告目录里执行它的进程已不在的 run 记为已结束，同时清理建立 run 时中断留下的暂存目录；修好上面打出的原因之后重新提交。

等待期间按 Ctrl-C，`submit` 以退出码 130 结束，标准输出为空，并按进行到哪一步说明：本机后端下，说明这次提交可能仍会建立 run 并执行（后台推进进程在建立 run 之前查到 `submit` 已经退出时不建立、自行退出，查过之后照常建立并执行），请先用说明里给出的 `gherkai list-runs` 命令确认、再决定是否重新提交，`submit` 已经收到建成的结果时直接给出它的 `run_id` 与查进度的命令；云端后端下，还没有开始建立 run 时说明没有建立，中断落在建立 run 的过程中时说明它可能已经写入云端并给出确认用的 `gherkai list-runs` 命令，已经建立时给出它的 `run_id` 与查进度的命令。`submit` 开始在标准输出写出 `run_id` 之后再按 Ctrl-C 不改变结果，照常以退出码 0 结束。

分界线在于是否已经开始执行：开始执行前的一切（feature 读不到、写法或参数不合法、worker 没装、凭证与资源不对、起隧道失败、本机后端的报告目录路径太长或所在的文件系统不受支持、在报告目录里建立这个 run 失败）以退出码 2 结束，正常执行结束的判定退出码为 0 或 1；运行期间处理了中断则为 130 或 143。`status --wait` 的等待被 Ctrl-C 停止时退出码同为 130（本机后端下收到 SIGTERM 时为 143），不表示判定；它不推进 run，停止它不影响 run 的执行。本机后端下，说明写明本命令是否已经把这个 run 记为已结束：还没有时说明没有改动它的记录、可以再执行同一条命令接着等待，已经记下时给出查看它的命令。`settle-runs` 被 Ctrl-C 停止时同样以 130 结束（收到 SIGTERM 时为 143），先输出已处理的部分，其余的没有处理，可以再执行同一条命令。用 `--json` 时先按退出码分流，再解析 stdout。各判定状态的含义与聚合规则见 [`../internals/verdict-model.md`](../internals/verdict-model.md)。

前台 `run`、本机后端的 `status --wait` 与 `settle-runs` 对 Ctrl-C 与 SIGTERM 还有三点相同：

- 只有让命令少做了事的中断才改变结果。`run` 在全部 job 结束之后、`status --wait` 在显示 run 的期间、`settle-runs` 在处理最后一项期间或输出期间才收到的中断，命令照常做完，说明与退出码和没有中断时相同。
- 启动命令时已被设为忽略的信号保持忽略。非交互 shell 里放到后台执行的命令就是这样（例如脚本里的 `gherkai status <run_id> --wait &`）：你对前台的命令按下的 Ctrl-C 不会把它一起停下。
- 命令正在写输出而读的一方一直不读时（例如标准输出接在一个没有人读的管道上），或者要写这个 run 的运行状态、却要等另一个 gherkai 进程写完（它恰在写的中途被暂停）时，Ctrl-C 与 SIGTERM 只被记下，要等这一步做完才起作用；这时只有强制结束（`kill -9`）能停下它。强制结束 `status --wait` 或 `settle-runs` 时，已经记为已结束的 run 不会恢复，还没有生成的报告也不会再补，再执行 `settle-runs` 对它给出 `already_finished`。

## 结果在哪

`--backend local` 下每次 run 落一个目录（下面以默认 `reports/` 为例）：

```
reports/<run_id>/
├─ index.html          可点开的报告入口：判定明细树 + 每条产物一行链接
├─ manifest.json       机读的产物清单
├─ jobs/               判定明细 —— scenario 与 step 的结果和原因在这里，用 `explain` 读；每次保存一份，文件名是一个标识，同一个 job 可能有多份，算数的那一份由 run_state.json 记下（`status --json` 的 `jobs[].result_id`）；没有启动的 job 没有
├─ run_meta.json       这个 run 提交了什么（run_id、并发、每个 job 的用例原文与预算）
├─ run_state.json      运行到哪了：run 与各 job 的状态以这里为准
├─ nova-trajectories/  Nova Act 引擎的轨迹与会话汇总，以及每步的 AI 证据与截图
├─ midscene-run/       Midscene 引擎的报告与截图，以及每步的 AI 证据；log/ai-config.log 记录这次实际用的模型
└─ worker.log          仅 `run --quiet` 且在本机运行时
```

同一目录下的 `events.db` 是这个 run 的事件记录（worker 报出的每条事件一行；`explain` 对被中止的 job 从这里补取已执行 step 的记录与证据），前台 `run` 与 `submit --backend local` 都写它，`--no-report` 不写；`submit --backend local` 还会留后台推进进程的日志 `reconcile.log`（后台运行迟迟不推进时先看它；后台推进进程给出提交结果之前的输出不在这里，在 `submit` 的终端上）。状态以退出码与 `status --json`（读的是 `run_state.json`）为准，scenario 与 step 的明细用 `explain` 看，不要以 `index.html` 为准：它是由这些记录生成的展示视图。也不要按 `jobs/` 下有哪些文件来读明细：执行中断或两个进程同时推进时，那里可能留着没被采用的一份，`explain` 只读 `run_state.json` 记下的那一份。纯确定性的用例不产生引擎产物，但每一步的判定与耗时都在判定明细里。

设备目标的 scope 另在 `midscene-run/device/` 下按 scope 分目录，放这个 scope 的诊断文件 `device-session.json`（能力探测结论、所用的会话与设备、换台记录、从获取设备到释放各阶段的时刻，以及执行前失败的原因与释放时是否有会话未能确认停止）与判为 failed / error 的 step 的原始控件树 `page-source/step-NNNN.xml`（按采集次序编号）；两者写盘前都经过脱敏。会话在 Device Farm 控制台里的录像与日志由 AWS 保留 400 天，存放在 us-west-2（与运行用的 region 无关），到期自动删除（见 [Device Farm 的数据保留](https://docs.aws.amazon.com/devicefarm/latest/developerguide/data-protection.html)）；gherkai 不删除任何会话。要留得更久，自己从控制台或 API 归档；要提前删除，在 Device Farm 控制台删除对应的会话，或执行 `aws devicefarm delete-remote-access-session --region us-west-2 --arn <会话 ARN>`（只能删除已结束的会话），删除后报告与 `explain` 里指向这个会话的控制台链接随之失效。录像会录下设备屏幕上显示的全部内容，在被测应用里登录请使用专用的测试账号。安装包不经 Device Farm 上传，保留期由放它的 S3 桶决定（见[配置](./configuration.md)）。

`--backend cloud` 下没有这棵本地树：运行状态与提交记录在 DynamoDB 的运行记录表里，其中提交记录里的 job 列表放在产物桶（`<前缀>artifacts`）根下的 `definitions/<run_id>/` 里、不随报告前缀变化；判定明细与报告在产物桶的 `<报告前缀>/<run_id>/` 下，相对位置与上面这棵树一一对应；worker 日志在 CloudWatch 日志组 `/<前缀>worker/<引擎>`。

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
- **列哪些**：默认列出全部还没结束的 run（`pending`、`running`），加上最近创建的 20 条已结束的 run。还没结束的 run 里，`pending` 表示全部 job 都还是 `pending`；只要有一个 job 不再是 `pending`（已被安排执行、正在执行或已有结果，包括被跳过），run 就显示为 `running`，到结束之前不会再回到 `pending`，`status` 显示的状态也是如此。`--limit N` 改已结束部分的条数（正整数），还没结束的 run 不受它限制、全部列出。`--status S` 只列这些状态的 run，可重复给出，取值是 `passed`、`failed`、`error`、`skipped`、`aborted`、`pending`、`running`；其中已结束的状态同样受 `--limit` 约束。
- **先后**：新创建的在前。「最近」按创建时间算、不按结束时间：早创建而刚结束的 run 不会因为刚结束就排到前面。创建时间取执行 `run` 或 `submit` 的那台机器的时钟，同一秒内创建的 run 之间先后不定；多台机器向同一个后端提交时，机器之间的时钟偏差会直接体现为清单里的先后。
- **表格**：每行一个 run，列出 run_id、状态、开始与结束时刻（本机时区；run_id 开头的时间戳是 UTC）、job 数与版本，有提示时另有一列「提示」。
  - 「job」列是这个 run 的 job 总数；各 job 的状态与 run 的状态不全相同时，括注各状态的个数，如 `3（passed 2 · failed 1）`。
  - 「版本」列给出写出这个 run 的 gherkai 版本，读不到时显示「未知」；由当前版本写出的 run 在版本后带 `*`，表格上方一行「当前 gherkai 版本 …（版本列以 * 标出）」点明当前版本（当前版本取不到时没有这一行，也没有带 `*` 的行）。对版本与当前版本不同的 run 执行 `status` 或 `explain` 时，按上面「命令」一节末尾的提交记录格式版本规则处理。
  - 「提示」列放这个 run 的 `message`（这个 run 在还有 job 没有结果时为什么结束，哪几类 run 有它见上「命令」一节末尾），清单里没有任何提示时这一列不出现。某个 job 为什么没通过不在清单里，用 `explain` 查看。执行它的进程已不在的未结束 run 会一直停在这个状态、不会自行消失，用 `settle-runs` 把它记为已结束（见下「结束停住的 run」）。
  - 运行状态读不出的行（多半由其它版本写出）只有 run_id 与版本两列有值，状态列显示「无法读取（可能由其它版本写出），用 status 查看」。这样的行不参与 `--status` 与 `--limit` 的筛选，找到即列出。由更新版本写出、状态值本版本不认识的 run，本机后端列为无法读取，云端后端不会列出。
- **清单为空**：只打一行提示，点名所查的落点，并提示核对定位参数是否与执行 `run` 或 `submit` 时所用的一致。本机后端分两种说法，都给出解析后的目录：目录不存在时说「本机后端的报告目录 … 不存在，这里还没有 run」，目录存在而其中没有 run 时说「本机后端的报告目录 … 下没有任何 run」；云端后端说「云端后端里没有任何 run」并给出前缀、region 与运行记录表名。给了 `--status` 而没有这些状态的 run 时，两个后端都把「任何 run」换成「状态为 … 的 run」。
- **`--json`**：一个 JSON 文档，顶层是所查的落点（`backend`；本机另有 `report_dir`，云端另有 `prefix`、`region`、`ddb_table`）与执行这次清单的 gherkai 版本 `cli_version`，加上 `runs` 数组；每项的 `cli_version` 是写出这个 run 的版本（读不到为 `null`），不为 `null` 且与顶层的相同，即由当前版本写出。清单为空时 `runs` 是空数组，不打人读提示。字段见 [`../internals/cli-json-contract.md`](../internals/cli-json-contract.md)。
- **只读**：不推进任何 run、不启动任务、不改动记录。判定仍对具体的 run 用 `status --wait` 取；退出码见上「退出码」一节。
- **不在清单里的**：`run --no-report` 的执行不留运行记录，清单里没有它。
- **云端后端下刚变化的 run**：状态、时刻与 job 数总是读取那一刻的值；刚提交或刚结束的 run 偶尔会在一次清单里缺席，稍后再列即可看到。

## 结束停住的 run：`settle-runs`

本机后端的一个 run 由执行它的那个 gherkai 进程从头执行到结束：前台是执行 `run` 的进程，后台是 `submit --backend local` 起的后台推进进程。这个进程在执行期间一直在这个 run 的目录上加着锁，进程退出时锁由系统放开。它没有写下结束记录就退出了（被 `kill -9` 结束、终端关闭、机器重启、运行期间读写记录失败）时，run 停在 `pending` 或 `running`，不会再往下执行，也没有别的进程接着执行它；`list-runs` 照常把它列在未结束的 run 里。下面两条命令可以把这样的 run 记为已结束：

```bash
gherkai settle-runs --dry-run                     # 只判断、不改动：列出会被记为已结束的 run
gherkai settle-runs                               # 处理报告目录 reports 里全部未结束的 run，并清理暂存目录
gherkai settle-runs <run_id> --report-dir DIR     # 只处理这一个 run
gherkai status <run_id> --wait                    # 等它结束；条件成立时同样把它记为已结束
```

- **什么时候记为已结束**：两条之一成立即可，前台与后台的 run 相同。一是执行它的 gherkai 进程已经退出（gherkai 能在这个 run 的目录上加上锁）；二是现在已过了它允许运行的时间之后再过 5 分钟（见上「允许运行的时间」），这时即使执行它的进程还在（例如被暂停）也记为已结束。两条都不成立时不动它，所以对正在正常执行的 run 执行这两条命令是安全的。
- **记成什么**：执行中的 job 记 `aborted`，说明「执行这个 run 的 gherkai 进程已退出，job 没有结果（已记为已结束）」；没有启动的 job 记 `skipped`，说明「执行这个 run 的 gherkai 进程已退出，job 没有启动（已记为已结束）」；run 级写下「执行这个 run 的 gherkai 进程已退出（已记为已结束）」。按第二条记为已结束的，三句的前半句换成「这个 run 已超过允许运行的时间」，run 级是「已超过允许运行的时间（已记为已结束）」。已经得出结果的 job 保留原来的判定；总状态按各 job 的状态得出，不会是 `passed`。随后生成报告；提交记录读不出的 run 被记为已结束之后没有报告（报告按提交记录逐个列出 job），说明里写明报告没有生成及原因。要重新运行没有结果的 job，用 `--scope` 选出它们。
- **只改记录、不停执行**：执行它的进程已退出时，它起的 worker 通常在几秒内察觉、开始收尾并释放会话；进程被暂停的，恢复之后，前台 `run` 在下一次写记录时（通常是某个执行中的 job 结束时）发现 run 已被记为已结束，停下其余的 worker，不输出汇总、以退出码 1 结束（见上「退出码」一节）；后台推进进程随即退出，它起的 worker 与执行它的进程已退出时一样自行收尾。
- **不处理的 run**：由别的版本的 gherkai 写出的 run（请用写出它的版本处理）；运行状态记录读不出的 run（`settle-runs` 与 `status --wait` 都不改动它，确认不再需要之后可以手工移走这个 run 的目录）；run 的目录不在受支持的本机文件系统上的 run（见上「本机后端的报告目录」）。它们留在 `list-runs` 里。
- **没有常驻的进程替你做这件事**：没有人执行这两条命令时，停住的 run 一直留在 `list-runs` 里。

**`settle-runs`**。定位参数（`--backend`、`--report-dir`）与 `status` 相同，同样读项目配置文件。这个版本只处理本机后端的 run：给出 `--backend cloud`（命令行上或配置文件里）时以退出码 2 结束，不访问云端。不给 run_id 时，它处理报告目录里全部未结束的 run 与运行状态读不出的 run，处理期间被删去的 run 略过；给了 run_id 只处理那一个，这个 run 不存在（含报告目录不存在）时以退出码 2 结束，说明与 `status` 的「未找到 run」相同。没有给 run_id 而报告目录不存在时，说明这里还没有 run，以退出码 0 结束。`--dry-run` 只判断、不改动，给出的是判断那一刻的结果：这之后才结束的 run，紧接着不带 `--dry-run` 执行时会得到「已结束」。

人读输出是一张表，每个 run 一行，写明处置（已记为已结束、会记为已结束、跳过）与原因，记为已结束而报告没有生成的另写明原因；清理暂存目录时另有一张表。`--json` 输出一个对象（记为已结束的每一项带 `report_written`，报告没有生成时为 `false`），字段见 [`../internals/cli-json-contract.md`](../internals/cli-json-contract.md)；每个 run 的 `reason` 取下表第一条成立的：

| `reason` | 含义 | `outcome` |
|---|---|---|
| `other_version` | 由别的版本的 gherkai 写出 | `skipped` |
| `unreadable` | 运行状态记录读不出 | `skipped` |
| `already_finished` | 已经结束，含处理期间被执行它的进程或另一条命令先记为已结束 | `skipped` |
| `unsupported_filesystem` | run 的目录不在受支持的本机文件系统上，无法确认执行它的进程是否还在 | `skipped` |
| `advancer_exited` | 执行它的 gherkai 进程已退出 | `settled`；`--dry-run` 下为 `would_settle` |
| `past_deadline` | 已过允许运行的时间之后再过 5 分钟 | 同上 |
| `lock_held` | 执行它的 gherkai 进程还在，或另一条 gherkai 命令正在处理它；还没有到可以按时间记为已结束的时刻，或提交记录读不出、不知道它允许运行到什么时候 | `skipped` |
| `undetermined` | 在 run 的目录上加锁出错，无法确认执行它的进程是否还在；也还没有到可以按时间记为已结束的时刻，或提交记录读不出 | `skipped` |

**暂存目录**。建立 run 时，gherkai 先在报告目录里建一个名字以 `.gherkai-creating-` 开头的暂存目录，写好记录再改名成这个 run 的目录。建立 run 的进程在改名之前被强制结束时，暂存目录留在报告目录里；它不是 run，`list-runs` 不列出它。不给 run_id 的 `settle-runs` 处理完 run 之后，删去没有进程在使用的暂存目录（`--dry-run` 下只列出会删除的），另一个进程正在使用的（正在建立 run，或另一个 `settle-runs` 正在处理）跳过。它只认 gherkai 自己生成的名字（前缀之后是 16 个小写十六进制字符），文件、符号链接与别的名字一概不碰。删除中途出错的记为跳过并给出原因，已删去的部分不恢复，再执行一次会接着删。

**退出码**：0 表示执行完成，含一个都没有处理、各种跳过与暂存目录的各种跳过。2 表示给出的 run 不存在、报告目录的路径太长或其中一层名字太长、报告目录不在受支持的本机文件系统上、给出了云端后端，或读写记录失败；读写记录失败时就此停止，先输出已处理的部分，出错的那个与其余的没有改动，修好原因之后再执行同一条命令即可（已处理的给出 `already_finished`）。130 表示被 Ctrl-C 打断（收到 SIGTERM 时为 143），先输出已处理的部分，其余的没有处理，可以再执行同一条命令；处理最后一项期间或输出期间才收到的中断没有让它少处理什么，不改变退出码（见上「退出码」一节末尾的三点）。读写记录失败与被打断时，`--json` 同样先输出那一个对象。

**等待中的 `status --wait`**（本机后端）。run 还没有结束时，它每轮做一次与 `settle-runs` 相同的判断；条件成立即把这个 run 记为已结束，在标准错误说明一句本命令已把它记为已结束及原因（报告没有生成时一并说明原因，不给报告的位置），然后照不带 `--wait` 的 `status` 显示它、按总状态给退出码（不是 `passed` 即为 1）。它不推进 run、不启动任何 job，也不需要 AWS 凭证。它只在等得到头的时候等待：执行它的进程还在（这时等它退出），或读得到它允许运行到什么时候（这时至多等到那之后再过 5 分钟）。条件不成立时接着等待：执行它的进程还在而提交记录读得出时不提示；执行它的进程还在而提交记录读不出（只能等执行它的进程退出）、在 run 的目录上加锁出错而提交记录读得出（说明到什么时刻会按时间把它记为已结束）时，各说明一次，可以按 Ctrl-C 停止等待。以退出码 2 结束的情形：run 不存在（含等待期间被删去）；run 由别的版本写出（在开始等待之前即结束，说明与 `status` 相同）；运行状态记录读不出（不等待，说明与不带 `--wait` 的 `status` 相同，等下去也不会有结果）；在 run 的目录上加锁出错而提交记录也读不出（不等待：既无法确认执行它的进程是否还在，也不知道该等到什么时候；说明写出加锁失败的原因与怎么办）；run 的目录不在受支持的本机文件系统上；读写记录失败（本命令没有把它记为已结束）。提交记录不完整或形态不对的 run 可以被本命令记为已结束，之后显示它时与不带 `--wait` 的 `status` 一样以退出码 2 结束。用 `--json` 时，等待中的说明与「已记为已结束」那一句不输出，JSON 文档里 run 的 `status` 与 `message` 给出它怎样结束；以退出码 2 结束的原因、被 Ctrl-C 打断时的说明、记为已结束而报告没有生成及其原因照常写到标准错误（JSON 文档里的 `artifacts` 照常给出报告的约定位置，不表示那里已有报告）；本命令记为已结束之后显示不了、以退出码 2 结束而没有 JSON 文档时，已记为已结束这件事写在那一句说明里。被 Ctrl-C 打断时怎样说明见上「退出码」一节；显示期间才收到的中断不改变显示与退出码。

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
- 没有启动的 job（`--fail-fast`、中断、超过允许运行的时间或 run 被记为已结束之后余下的，状态是 `skipped`）没有判定明细：点名它时（`gherkai explain "$RUN_ID" <scope_id>`）给出运行状态里的状态与说明，退出码为 0；不点名时 `explain` 不列出它，它的状态与说明在 `status` 里也看得到。
- job 被中止或出错时（按了 Ctrl-C、超时、fail-fast、超过允许运行的时间、worker 被外部停止），没执行完的用例没有判定，但其中已执行完的步 `explain` 仍能显示并带出证据：这些步从这个 run 的事件记录补取，行尾标「记录取自事件流」，所属用例标「未完成」；被中止时还没上报完成记录的那一步没有记录。补不到（例如这个 run 由不写事件记录的旧版本执行）时在该 job 下写明原因。
- 每一步与每个 job 的失败说明最长 8192 字节（按 UTF-8 计，约 2700 个汉字），更长的只保留开头部分，`explain`、`run` 的汇总、报告与判定明细里都是截断之后的这一份；截断之前的完整说明写在 worker 日志里（位置见[排障](./troubleshooting.md)）。设备的型号与系统版本同样各保留前 255 字节。
- `explain` 的退出码从不表示判定结果，用例失败它照样以退出码 0 结束。每个 job 得出结果时即写下它的判定明细，`run` 与 `submit` 提交的 run 都是如此：run 还在执行时，`explain` 显示已完成的 job，并提示这只是已完成的部分；还没有任何 job 完成时，它提示先用 `status --wait` 等到结束。
- 哪一步没有 AI 证据（确定性 step 本就不产，设备目标上只有判为 passed 的确定性与导航 step 不产；或抽取当时失败了），它会明说，并给出该步其它产物的链接。
- 设备目标上，判为 failed / error 的确定性与导航 step 也有证据（没有 AI 调用，`acts` 为空）。设备的证据多几项：这一步的执行方式 `step_kind`（`ai` / `deterministic` / `navigation`）；step 结束时的页面地址 `url`，取不到时 `url_missing` 说明原因（设备不提供网页上下文、应用目标没有地址、读取超时或出错）；判为 failed / error 的 step 另有控件摘要 `controls`（每个控件的类型、id、文本与无障碍标识，条数有上限、超出时注明截断）与原始控件树文件 `page_source`（只给地址，超过大小上限时截断并以 `page_source_truncated` 注明）。设备 job 另有一条 `device_session` 链接，指向上面的 `device-session.json`，`explain` 只给链接、不解析它。地址读取与控件采集按 step 累加计入 job 墙钟预算。

## 费用量级

`plan`、`list-runs`、`list-engines`、`list-deterministic`、`doctor` 都是本地或只读操作，不产生模型费用。`run` 与 `submit` 每次都会真实消耗 AWS 费用：桌面目标是模型调用与云端浏览器会话的费用；设备目标是模型调用与 Device Farm 远程访问会话的费用。远程访问会话按设备分钟计费，一个设备 scope 通常只建一个会话；获取设备期间设备拒绝安装驱动辅助程序而换一台时（至多一次），被替换的那个会话同样计费。设备分钟从服务商开始准备设备起算，并发槽位满时的排队等待不计费；准备设备到可用的时间约 1 到 2.5 分钟，通常计费；停止会话后的收尾可能继续计费。设备分钟按量约 0.17 美元每分钟，一条 5 步左右的设备 scenario 一次大约 3 到 5 设备分钟；每平台每月用量很大时（约 1470 设备分钟以上），不计量槽位（约 250 美元每月）更省：须先在 AWS 为对应平台购买不计量设备槽位，再把 `gherkai.toml` 的 `billing-method` 设为 `UNMETERED`；没有槽位时服务商在准备阶段就结束会话，见 [`configuration.md`](./configuration.md)「项目配置文件」。设备 job 结果里的「设备占用时长」（`--json` 的 `device_observed_s`）是 worker 观察到的时长，与账单上的设备分钟口径不同，以账单为准。量级上，一条 5 步左右的 scenario 在 Midscene 默认模型（`us.openai.gpt-5.6-terra`）上约 5 美分，换成 `qwen.qwen3-vl-235b-a22b` 约 2 美分（按 2026-09 Bedrock 标价与一条 5 步示例用例的 token 用量估算，以账单为准），Nova Act 引擎按 Nova Act 服务计费。换模型的办法见 [`configuration.md`](./configuration.md)「模型选择」。每个 job 都有 job 墙钟预算（桌面 scope 默认 300 秒，设备 scope 默认为获取预算加 900 秒），超出即被停掉，防止任务卡住时持续计费。

## 机读输出

运行与查询的命令都有 `--json`：`plan`、`run`、`status`、`list-runs`、`explain`、`list-engines`、`list-deterministic`、`doctor`（部署方的 `gherkai deploy list-workers` 也有，见 [`cloud-backend.md`](./cloud-backend.md)）；改动记录的命令里只有 `settle-runs` 有它，输出逐个 run 的处置结果；`submit` 没有这个选项，它的 stdout 本来就只有一个 `run_id`。通则：stdout 只有一个 JSON 文档，进度与诊断一律走 stderr，所以 `gherkai run … --json > result.json` 拿到的是纯净 JSON、进度仍在终端可见。字段名、类型与出现条件见 [`../internals/cli-json-contract.md`](../internals/cli-json-contract.md)。

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
