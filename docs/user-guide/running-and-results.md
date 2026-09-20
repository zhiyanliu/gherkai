# 运行测试与查看结果

本页讲怎么运行 `.feature`、结果落在哪、退出码怎么读：执行方式与执行后端四种组合的选择、`plan` / `run` / `submit` / `status` / `explain` / `list-engines` / `list-deterministic` / `doctor` 的用途与常用选项、报告与证据的位置、费用量级、机读输出与 CI 用法。安装与 AWS 前置见 [`getting-started.md`](./getting-started.md)，`.feature` 的写法见 [`writing-features.md`](./writing-features.md)，`--expose-local` 测本机应用见 [`local-app-testing.md`](./local-app-testing.md)，云端后端的部署与维护见 [`cloud-backend.md`](./cloud-backend.md)，全部选项与环境变量的总表见 [`configuration.md`](./configuration.md)。任一命令的完整选项以 `gherkai <命令> --help` 为准。

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
| `run` / `submit`，`--backend local` | 本机 AWS 凭证 + 要用的引擎 worker | 自己的 AWS 账户 |
| `submit` + `status`，`--backend cloud` | 运行记录表读写、若干只读检查、调用后端 Lambda；用例带 DataTable / DocString 时另需产物桶（`<前缀>artifacts`）的写权限。不需要任何 ECS 写权限 | 部署方的 AWS 账户 |
| `run`，`--backend cloud` | 运行记录表读写、若干只读检查、起停与查询 Fargate 任务、上传 job 与写产物桶；不需要调用后端 Lambda——这条路径由本机命令进程自己起任务、自己推进 | 部署方的 AWS 账户 |

完整的权限清单见 [`cloud-backend.md`](./cloud-backend.md)「团队成员需要的最小云端权限」。

## 命令

一个 job = 一个 scope 里的全部 scenario，它们共享一个浏览器会话、按书写顺序串行执行。scope 由 `.feature` 里的 `@scope` 标签划分；未标 `@scope` 的 scenario 各自成为一个 job，编号是 `<文件>:<行号>`（见 [`writing-features.md`](./writing-features.md)）。

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
| `gherkai explain <run_id> [<scope_id>]` | 看每一步的证据：问了 AI 什么、AI 看见了什么、为什么这么判。用例没过时先运行这个命令 | `--scenario`、`--step`、`--all`、`--full`、`--json` |
| `gherkai list-engines` | 列出本机两个引擎 worker 的拉起命令与来源，没装的那个原地给安装提示 | `--json` |
| `gherkai list-deterministic` | 列出某个引擎支持的确定性 step（含项目 `steps/` 里的），写 feature 时据此复用 | `--engine {midscene,novaact}`（默认 `novaact`）、`--steps-dir`、`--json` |
| `gherkai doctor` | 只读自检：CLI 版本、引擎 worker、实际使用的模型、`steps/` 加载结果；装了部署工具链（Node、cdk、容器引擎）时连带自检它；给了 `--backend cloud` 或 `--prefix` 时再查凭证、后端资源与后端版本 | `--backend cloud`、`--prefix`、`--report-dir`、`--steps-dir`、`--json` |
| `gherkai --version` | 打印 CLI 版本 | — |

`status` 与 `explain` 的 `--backend`、`--report-dir`、`--prefix` 必须与 `submit` 时一致，否则查不到这个 run。`status --wait` 既是查询也是接力：后台推进停了或卡住时，来查的这条命令会把这个 run 推到终态；本机后端下接力的并发上限按提交时的值走，提交记录里没有值才用 `status --max-concurrency` 给的值。`doctor` 的读法与按症状分表的处置见 [`troubleshooting.md`](./troubleshooting.md)。

使用云端后端时 CLI 不能新于后端（正常保持同版本）：后端记一个版本戳，`submit`、`status`、`explain` 与 `run --backend cloud` 在读写云端之前拿它比对 CLI 版本，CLI 比后端**新**时拒绝执行并退 `2`（新 CLI 写的任务定义旧后端读不懂，没有放行选项）；CLI 比后端旧时只打印一行提示、照常执行。升级顺序见 [`cloud-backend.md`](./cloud-backend.md)「版本与升级」。

## 常用选项（`run` / `submit`）

**只运行一部分**（`plan` 认同一组选项）

| 选项 | 说明 |
|---|---|
| `--scope ID` | 只运行这些 scope。值 = 报告与 JSON 里的 `scope_id`：`@scope` 的名字，或未标 scope 时的 `<文件>:<行号>`。可重复，任一命中。重新运行某个失败的 job 用它最直接 |
| `--tags TAG[,TAG...]` | 只运行带这些 tag 的 scenario。一个值内用逗号分隔表示任一命中，重复给本选项表示都要命中；`@` 可省。feature 行上的 tag 对其下每个 scenario 生效 |
| `--scenario SEL` | 只运行这些 scenario。`SEL` = 完整 scenario id、行号（`12` 或 `:12`，纯数字只当行号）、或标题的一段文字（区分大小写）。可重复，任一命中 |

三者同给时都要满足。筛掉一部分时命令会打印一行 `筛选：<已选>/<总数> scenario`，后面附上你给的筛选条件；一条都没选中时退 `2` 并列出这个 run 的全部候选（id、标题、tags），不会静默执行一个空 run。

**执行**

| 选项 | 默认 | 说明 |
|---|---|---|
| `--default-engine {midscene,novaact}` | `novaact` | 未标 `@engine` 的 scope 用哪个引擎；标了 tag 的 scope 不受影响 |
| `--assertion-votes N` | `1` | AI 断言执行 N 次取多数票（如 3 或 5），用于降低判定抖动 |
| `--max-concurrency N` | `1` | 同时运行的 worker 上限，须 ≥ 1。`submit --backend cloud` 提交时若超过部署方为单个 run 设的上限，命令会提示并按该上限并行；`run --backend cloud` 由本机命令进程直接调度，不受该上限约束 |
| `--default-job-timeout S` | `300` | 单个 job 的墙钟预算秒（`<=0` 表示不超时）；用例上标 `@timeout:<秒>` 可逐 scope 覆盖。超预算的 job 被停掉并判 error |
| `--grace S` | 自动 | 仅 `run --backend local`：中止时留给 worker 关闭云端浏览器会话的秒数，不给则按这个 run 用到的引擎自报的最短宽限推导。值过小会漏关会话、继续计费，命令在开始执行前退 `2`。`--backend cloud` 不接受这个选项（给了直接退 `2`），云端的停止宽限在部署时定 |
| `--fail-fast` | 关 | 仅 `run`：任一 job 出错即中止这个 run 的其余 job |

单个 job 的网络故障只让那个 job 判 error，其余 job 继续；给了 `--fail-fast` 才会因此中止这个 run。

**输出与落盘**

| 选项 | 默认 | 说明 |
|---|---|---|
| `--report-dir DIR` | `reports` | 报告落点，每次 run 落 `DIR/<run_id>/`。`status` 与 `explain` 查同一个 run 要给同一个值。云端后端下它是后端的报告前缀，与部署侧不一致时 `submit` 在提交前退 `2` 并点名两侧的值 |
| `--no-report` | 关 | 仅 `run`：报告目录下什么都不落，也不收集引擎自己的报告产物。适合 CI 只看退出码或 JSON |
| `--quiet` | 关 | 仅 `run`：不输出逐事件进度，仍输出文本汇总。在本机运行时 worker 日志改落 `<report-dir>/<run_id>/worker.log`（`--no-report` 时落系统临时目录），只打印一行位置；云端后端下没有本机 worker 日志 |
| `--json` | 关 | 仅 `run`：标准输出只打机器可读 JSON、不打文本汇总；进度与诊断照常走标准错误，逐事件进度可用 `--quiet` 静音 |
| `--steps-dir DIR` | `./steps` | 项目自己的确定性 step 目录，也可用环境变量 `GHERKAI_STEPS_DIR`。目录里任一文件加载失败即整个 run 拒绝运行。云端后端下不生效（云端 worker 的 step 构建在镜像里，只警告不拦），写法见 [`writing-deterministic-steps.md`](./writing-deterministic-steps.md) |
| `--expose-local ORIGIN` | — | 把本机可达的被测应用经隧道暴露给云端浏览器，配套的 `--tunnel`（两条命令都有）与 `--tunnel-ttl`（只有 `submit` 有）见 [`local-app-testing.md`](./local-app-testing.md) |

**仅 `--backend cloud`**：`--prefix P`（默认 `gherkai-`，兜底环境变量 `AWS_RESOURCE_PREFIX`）须与部署时一致，统一决定表、桶、集群等资源名；`--worker-variant NAME` 选云端 worker 镜像的 variant，不给则用部署时的默认指针，某个引擎缺这个 variant 直接退 `2`、不回落到默认，见 [`cloud-backend.md`](./cloud-backend.md)。不给 `--subnet` / `--security-group` 时，Fargate 的子网与安全组按部署时写入的参数自动取用，一般不用给。单独覆盖某个资源名的选项见 [`configuration.md`](./configuration.md)。

## 退出码

每条命令的退出码回答的是不同的问题。本页这几条命令里，表判定的只有 `run` 与 `status`，也只有它们会退 `1`；部署方命令的退出码见 [`cloud-backend.md`](./cloud-backend.md)。

| 命令 | 退出码回答什么 | `0` | `1` | `2` |
|---|---|---|---|---|
| `run` | 判定 | 这个 run 全部通过 | 有用例失败或出错；`--backend cloud` 执行到一半时运行记录存储不可达也退这个码 | 开始执行前的配置或可达性问题 |
| `status`（不带 `--wait`） | 查到了吗 | 查到了，含还没结束的 run | 读到的终态不是全部通过 | run 不存在、云端不可达、CLI 与后端版本不匹配 |
| `status --wait` | 判定 | 运行结束且全部通过 | 运行结束但有用例失败或出错 | 同上，另加后端没部署或 `--prefix` 配错 |
| `submit` | 提交成功了吗 | 已提交，`run_id` 已打印 | — | 配置或可达性问题 |
| `plan` | 这个 run 能运行吗 | 能 | — | 配置错、写法错、`steps/` 里有文件加载失败 |
| `explain` | 证据读出来了吗 | 渲染出来了，用例判失败也退 `0`；判定明细还没落地同样退 `0` | — | 参数写错（例如 `--step` 没同时给 `--scenario`）、run 或 scope 查不到、云端读不到、CLI 与后端版本不匹配 |
| `doctor` | 必修项都过了吗 | 全过 | — | 任一必修项失败（可选能力缺失只标 `-`，不影响退出码） |
| `list-deterministic` | 这个引擎有哪些确定性 step | 列出来了 | — | `--steps-dir` 指的不是目录、worker 定位不到、`steps/` 加载失败、该引擎的 worker 自述失败（多为 worker 与 CLI 版本不一致，处置见 [`troubleshooting.md`](./troubleshooting.md)） |
| `list-engines` | 这台机器的引擎环境什么样 | 恒 `0`（某个引擎没装正是要展示的信息，不算命令失败） | — | — |

分界线在于是否已经开始执行：开始执行前的一切（feature 读不到、写法或参数不合法、worker 没装、凭证与资源不对）退 `2`，开始执行之后的结论退 `0` 或 `1`。用 `--json` 时先按退出码分流，再解析 stdout。各判定状态的含义与聚合规则见 [`../internals/verdict-model.md`](../internals/verdict-model.md)。

## 结果在哪

`--backend local` 下每次 run 落一个目录（下面以默认 `reports/` 为例）：

```
reports/<run_id>/
├─ index.html          可点开的报告入口：判定明细树 + 每条产物一行链接
├─ manifest.json       机读的产物清单
├─ jobs/               每个 job 一份判定明细，文件名由 scope 名派生 —— 判定的权威在这里
├─ run_meta.json       这个 run 提交了什么（run_id、并发、每个 job 的用例原文与预算）
├─ run_state.json      运行到哪了
├─ nova-trajectories/  Nova Act 引擎的轨迹与会话汇总，以及每步的 AI 证据与截图
├─ midscene-run/       Midscene 引擎的报告与截图，以及每步的 AI 证据
└─ worker.log          仅 `run --quiet` 且在本机运行时
```

`submit --backend local` 还会在同一目录留后台进程日志 `reconcile.log`（后台运行迟迟不推进时先看它）与事件库 `events.db`；用了 `--expose-local` 时另有隧道记录 `tunnel.json`。判定要读 `jobs/` 下的明细或退出码，别读 `index.html`——那是可以重建的展示视图。纯确定性的用例不产生引擎产物，但每一步的判定与耗时都在判定明细里。

`--backend cloud` 下没有这棵本地树：提交记录与运行状态在 DynamoDB 的运行记录表里，判定明细与报告在产物桶（`<前缀>artifacts`）的 `<报告前缀>/<run_id>/` 下，相对位置与上面这棵树一一对应；worker 日志在 CloudWatch 日志组 `/<前缀>worker/<引擎>`。

`run` 结束时与 `status` 到终态时都会把三处位置输出到标准错误（stderr），云端后端下给的是 `s3://` 与运行记录表的诊断指针：

```
报告: file:///…/reports/<run_id>/index.html
运行元信息: file:///…/run_meta.json、file:///…/run_state.json
判定明细: file:///…/reports/<run_id>/jobs
```

`--json` 下同一组位置在 `artifacts` 键里。产物分类与每一份该拿来回答什么问题见 [`../internals/artifacts-and-evidence.md`](../internals/artifacts-and-evidence.md)。

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
- `explain` 从不表判定，用例失败它照样退 `0`。run 还没到终态时判定明细还没落地，它会提示先用 `status --wait`。
- 哪一步没有 AI 证据（确定性 step 本就不产，或抽取当时失败了），它会明说，并给出该步其它产物的链接。

## 费用量级

`plan`、`list-engines`、`list-deterministic`、`doctor` 都是本地或只读操作，不产生模型费用。`run` 与 `submit` 每次都会真实消耗 AWS 费用（模型调用 + 云端浏览器会话）。量级上，一条 5 步左右的 scenario 在 Midscene 默认模型（`us.openai.gpt-5.6-terra`）上约 5 美分，换成 `qwen.qwen3-vl-235b-a22b` 约 2 美分（按 2026-09 Bedrock 标价与实测 token 估算，以账单为准），Nova Act 引擎按 Nova Act 服务计费。换模型的办法见 [`configuration.md`](./configuration.md)「模型选择」。每个 job 有墙钟预算（默认 300 秒），超预算即被停掉，防止任务卡住时持续计费。

## 机读输出

运行与查询的命令都有 `--json`：`plan`、`run`、`status`、`explain`、`list-engines`、`list-deterministic`、`doctor`（部署方的 `gherkai deploy list-workers` 也有，见 [`cloud-backend.md`](./cloud-backend.md)）；`submit` 没有这个选项，它的 stdout 本来就只有一个 `run_id`。通则：stdout 只有一个 JSON 文档，进度与诊断一律走 stderr，所以 `gherkai run … --json > result.json` 拿到的是纯净 JSON、进度仍在终端可见。字段名、类型与出现条件见 [`../internals/cli-json-contract.md`](../internals/cli-json-contract.md)。

## 在 CI 里运行

前台一条命令即拿判定码：

```bash
gherkai run features/*.feature --quiet --max-concurrency 2
```

后台运行把提交与收结果拆开，判定码来自 `status --wait`：

```bash
RUN_ID=$(gherkai submit features/*.feature --backend cloud --prefix gherkai-)
gherkai status "$RUN_ID" --backend cloud --prefix gherkai- --wait --json > result.json
rc=$?
if [ "$rc" -eq 1 ]; then
  gherkai explain "$RUN_ID" --backend cloud --prefix gherkai-   # 有用例没过：把证据输出到构建日志
fi
exit "$rc"
```

三条注意：不带 `--wait` 的 `status` 在 run 还没结束时退 `0`，不能当判定门；`explain` 只渲染证据、也不能当判定门；`submit` 的退出码只说提交成功了。示例 `.feature` 在 [`features/`](../../features/) 目录，可直接用来验证流水线是否接对。
