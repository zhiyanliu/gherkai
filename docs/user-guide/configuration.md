# 配置：环境变量与通用选项

本页是 gherkai 全部环境变量与跨命令通用选项的清单：每一项做什么、默认值是多少、在哪里设才生效。命令怎么用、结果与退出码怎么读见 [`running-and-results.md`](./running-and-results.md)；安装与 AWS 前置见 [`getting-started.md`](./getting-started.md)；报错的处置见 [`troubleshooting.md`](./troubleshooting.md)。

## 配置生效的四个位置

同一件事同时有命令行选项和环境变量时，选项优先；两者都没给才用默认值。

| 位置 | 谁读它 | 怎么设 |
|---|---|---|
| 本机 CLI 进程 | `gherkai run` / `plan` / `submit` / `status` / `explain` / `doctor` / `list-engines` / `list-deterministic` 本身 | 在跑命令的 shell 里 export |
| 本机 worker 进程 | 本机后端（`--backend local`）下由 CLI 起的引擎 worker。`plan`、`list-deterministic`、`doctor` 也各起一次本机 worker 读它的确定性 step 信息（`doctor` 还读它自报的模型），与 `--backend` 无关 | 同上 |
| 云端 worker 容器 | 云端后端（`--backend cloud`）下在 Fargate 上跑的 worker | 把变量写进 worker 镜像 variant 的 `ENV`，再用 `gherkai deploy push-worker` 推上去（见 [`cloud-backend.md`](./cloud-backend.md)） |
| 部署机 | `gherkai deploy` / `destroy` / `push-worker` | 在跑部署命令的 shell 里 export |

值怎么从你设的地方到真正读它的进程：

![环境变量从你设的地方流到本机 CLI 进程、它起的子进程与云端 worker 容器，四类边分别是继承、由 gherkai 注入、被选项覆盖、不传](../diagrams/configuration-env-inheritance.svg)

图注：你在 shell 里 export 的值由本机 CLI 进程继承，再传给它起的子进程；图里的「CLI 起的子进程」既指本机 worker 进程，也指部署时起的 cdk 子进程——两者都从 CLI 原样继承环境，也都会被 gherkai 注入的变量和解析后的选项值改写。云端 worker 容器不继承你的 shell，它的环境是 worker 镜像 `ENV` 里的值加上起这个任务的那一方注入的值。**继承** = 原样拿到上一级的值；**被覆盖** = 起子进程时用解析后的选项值改写同名变量；**不传** = 值到不了对面，要生效就设在对面；**由 gherkai 注入** = 由起这个进程的那一方写入，压过继承来的值（含镜像 `ENV` 里的同名项），清单见下文「由 gherkai 注入的环境变量」。部署命令（`deploy` / `destroy` / `push-worker`）本身也是本机 CLI 进程，只是通常在另一台机器上跑，上表把那台机器单列为「部署机」。云端任务在 `run --backend cloud` 下由本机 CLI 起，在 `submit --backend cloud` 下由后端起。哪个变量设在哪里生效，见下面各表的「在哪里设」栏。

## 模型选择

两个引擎各自把默认模型固定在一个具体版本，换默认模型只随 gherkai 发版。判定结果会随模型变化：同一条断言在不同模型上可能翻转，所以升级模型前请先用同一批用例对照一遍。换成别的模型前，先在所用 region 为该模型开通访问权限；没开通时 worker 在建立浏览器会话阶段报权限被拒，处置见 [`troubleshooting.md`](./troubleshooting.md)。

| 引擎 | 默认模型 | 换模型 |
|---|---|---|
| Nova Act | `nova-act-v1.0` | 设 `NOVA_MODEL_ID`。可以设成 `nova-act-preview` 试新模型，但 preview 没有支持承诺、内容随 AWS 变化，也无法固定到某个具体日期的版本 |
| Midscene | `us.openai.gpt-5.6-terra` | 设 `MIDSCENE_MODEL_ID`，取值是 Bedrock 上 Midscene 支持的模型，例如 `qwen.qwen3-vl-235b-a22b`、`us.openai.gpt-6-astra` |

GPT 系的模型要给带地区前缀的推理配置文件 id（inference profile，如 `us.openai.gpt-5.6-terra`、`us.openai.gpt-6-astra`），直接给不带前缀的基础模型 id 会被 Bedrock 端点拒绝。

Midscene 还要知道模型属于哪个家族（家族决定它用哪套提示词与请求参数）。worker 按模型 id 自动推断，只要 id 里出现下面的片段就命中对应家族：

| 模型 id 里出现 | 家族 |
|---|---|
| `qwen.qwen3-vl` | `qwen3-vl` |
| `openai.gpt-6` | `gpt-6` |
| `openai.gpt-5` | `gpt-5` |
| `kimi-k2` | `kimi` |
| `kimi-k3` | `kimi3` |
| `deepseek.` | `deepseek` |
| 以 `zai.glm-` 开头且后面还有 `v` | `glm-v` |

匹配看的是片段出现在 id 里的任意位置，所以带 `us.` 或 `global.` 前缀的推理配置文件 id 同样命中。一条都不命中时 worker 启动即报错、不做猜测：家族推错不会报错，只会让模型在页面上找元素和判定的准确度下降，比直接失败更难发现。这时设 `MIDSCENE_MODEL_FAMILY` 指明家族，可取值见 Midscene 文档 <https://midscenejs.com/model-common-config.html>。

查当前实际用的模型：

```bash
gherkai doctor
```

`doctor` 会起一次本机 worker 并打印它自报的模型，每个可用引擎一行。这一行显示这台机器上实际生效的模型，可用来确认环境变量里的覆盖有没有生效。云端 worker 的模型由镜像里的 `ENV` 决定，这一行不反映它。

换模型也会改变每次 run 的费用；量级与计费口径见 [`running-and-results.md`](./running-and-results.md)，最终以你账户的 AWS 账单为准。

## 使用者可设的环境变量

### AWS 访问与云端资源名

| 变量 | 作用 | 默认值 | 在哪里设 |
|---|---|---|---|
| `AWS_REGION` | 用哪个 AWS region，`--region` 没给时用它 | 无 | 本机 CLI 进程、部署机 |
| `AWS_DEFAULT_REGION` | 备用的 region 变量，`AWS_REGION` 没设时用它 | 无 | 同上 |
| `AWS_PROFILE` | 用哪个 AWS profile，`--profile` 没给时用它 | 无（走 AWS 默认凭证链） | 同上 |
| `AWS_RESOURCE_PREFIX` | 云端资源名前缀，`--prefix` 没给时用它 | `gherkai-` | 同上 |
| `AWS_DDB_TABLE` | 运行状态表名，`--ddb-table` 没给时用它 | `<prefix>runs` | 本机 CLI 进程 |
| `AWS_S3_BUCKET` | 产物 S3 桶名，`--s3-bucket` 没给时用它 | `<prefix>artifacts` | 本机 CLI 进程 |

region 的完整解析链是 `--region` > `AWS_REGION` > `AWS_DEFAULT_REGION` > profile 配置里的 region。四处都没有时 gherkai 不补一个默认 region，缺 region 的后果与处置见 [`getting-started.md`](./getting-started.md)。云端 worker 的 region 由起任务的那一方以 `AWS_REGION` 注入，不用写进 variant 镜像。

凭证本身不经 gherkai 的变量传递，走 AWS 默认凭证链：profile、`AWS_ACCESS_KEY_ID` 等标准变量、实例角色都可以，配法见 [`getting-started.md`](./getting-started.md)。

### 引擎行为

| 变量 | 作用 | 默认值 | 在哪里设 |
|---|---|---|---|
| `NOVA_MODEL_ID` | Nova Act 用哪个模型 | `nova-act-v1.0` | 本机 shell、variant 镜像 `ENV` |
| `NOVA_ACT_TIMEOUT_S` | 单个 AI 操作的时间上界（秒） | `120` | 本机 shell（见下方说明） |
| `NOVA_GRACE_MARGIN_S` | Nova worker 收尾预算的余量（秒） | `30` | 本机 shell（见下方说明） |
| `MIDSCENE_MODEL_ID` | Midscene 用哪个模型 | `us.openai.gpt-5.6-terra` | 本机 shell、variant 镜像 `ENV` |
| `MIDSCENE_MODEL_FAMILY` | 显式指定模型家族，优先于自动推断 | 无（按模型 id 推断） | 本机 shell、variant 镜像 `ENV` |
| `GHERKAI_STEPS_DIR` | 你自己的确定性 step 目录，`--steps-dir` 没给时用它 | `./steps` 存在即用 | 本机 shell、variant 镜像 `ENV` |

- `NOVA_ACT_TIMEOUT_S` 由起 worker 的那一侧读取后注给 worker：`run`（两档后端都算）与 `submit --backend local` 用发起命令的 shell 里的值；`submit --backend local` 提交的 run 之后由 `gherkai status --wait` 接着推完时，用运行 `status` 的那个 shell 里的值；`submit --backend cloud` 的任务由云端起，固定用 120 秒。
- `NOVA_ACT_TIMEOUT_S` 与 `NOVA_GRACE_MARGIN_S` 相加就是 Nova 引擎自报的最小停止宽限（默认 150 秒；Midscene 自报的是固定的 31 秒），调大前者会同时抬高本机跑允许的最小 `--grace`。
- `NOVA_GRACE_MARGIN_S` 只影响本机跑允许的最小 `--grace`。云端 worker 的停止宽限由部署时的 `gherkai deploy --stop-timeout` 决定。
- 云端 worker 读自己镜像里 `ENV GHERKAI_STEPS_DIR` 指的目录，确定性 step 随镜像一起构建进去（见 [`cloud-backend.md`](./cloud-backend.md)）；本机 shell 里的 `GHERKAI_STEPS_DIR` 与 `--steps-dir` 给了只提示一句、不拦截。step 的写法与目录约定见 [`writing-deterministic-steps.md`](./writing-deterministic-steps.md)。

### 隧道与 worker 拉起

| 变量 | 作用 | 默认值 | 在哪里设 |
|---|---|---|---|
| `NGROK_AUTHTOKEN` | `--expose-local` 起 ngrok 隧道用的 authtoken；也可以改用 `ngrok config add-authtoken <token>` 写进 ngrok 自己的配置文件 | 无 | 本机 shell |
| `GHERKAI_WORKER_NOVAACT_CMD`、`GHERKAI_WORKER_MIDSCENE_CMD` | 显式指定该引擎 worker 的拉起命令（自建 worker、或从源码目录跑）；值按 shell 词法拆分，引号不配对即报错，不会静默改用别的 worker | 无（按已安装的 worker 自动查找） | 本机 shell |
| `GHERKAI_WORKER_NOVAACT_CWD`、`GHERKAI_WORKER_MIDSCENE_CWD` | 上一项命令的工作目录 | 无（继承当前目录） | 本机 shell |

隧道的前置、限制与存活时间见 [`local-app-testing.md`](./local-app-testing.md)。

### 部署机

| 变量 | 作用 | 默认值 |
|---|---|---|
| `GHERKAI_CONTAINER_ENGINE` | 用哪个容器引擎，`--container-engine` 没给时用它 | `docker` |
| `XDG_CACHE_HOME` | CDK 环境查询缓存的根目录，缓存落 `<该目录>/gherkai/cdk-context/` | `~/.cache` |

## 由 gherkai 注入的环境变量

下面这些变量由 gherkai 自己写入，**使用者不要设**。设了不报错：一部分在起 worker 时被清掉或覆盖，另一部分会被 worker 原样读到，把 job 的来源、事件表、产物落点指到别处，本机跑与云端跑就此不一致。要调整对应行为，用括号里的选项。

- worker 侧：`RUN_ID`、`SCOPE_ID`、`JOB_S3_URI`、`EVENTS_DDB_TABLE`、`EVENTS_FD`、`ARTIFACT_S3_BUCKET`、`ARTIFACT_S3_PREFIX`、`NOVA_LOGS_DIR` 与 `MIDSCENE_RUN_DIR`（产物落点用 `--report-dir` 定）、`GHERKAI_NO_ARTIFACTS`（用 `--no-report`）、`GHERKAI_EXTRA_HTTP_HEADERS`（由 `--expose-local` 决定）。
- 云端后端侧：`REGION`、`CLUSTER`、`SUBNETS`、`SECURITY_GROUPS`、`RUNS_TABLE`、`EVENTS_TABLE`、`ARTIFACTS_BUCKET`、`PREFIX`、`MAX_CONCURRENCY`、`KICKER_ARN`、`SCHEDULER_ROLE_ARN`。`REPORT_DIR` 与 `ASSIGN_PUBLIC_IP` 云端不注入，走内置缺省（`reports` / 公网 IP 启用）；要改报告前缀或让 worker 走私有子网，由部署方在部署时调整。
- 部署工具链侧：`GHERKAI_LAMBDA_ASSET_DIR`（部署命令给合成过程用的临时目录）。部署命令还会把解析出的 region 以 `AWS_REGION` / `AWS_DEFAULT_REGION` 写进它启动的 cdk 子进程，覆盖你 shell 里的同名值；`CDK_DEFAULT_ACCOUNT` / `CDK_DEFAULT_REGION` 由 CDK 自己注入，不用你设。

## 跨命令通用选项

下面这些选项在多个命令上同名同义。这一节只回答「哪些命令上有它、跨命令有什么差异」，语义、默认值与取舍见 [`running-and-results.md`](./running-and-results.md)；每个命令的完整选项表看 `gherkai <命令> --help`。

| 选项 | 出现在 | 跨命令差异 |
|---|---|---|
| `--backend {local,cloud}` | `run`、`submit`、`status`、`explain`、`doctor` | 默认 `local`。查一个 run 的 `status` / `explain` 要给与 `submit` 相同的值 |
| `--prefix P` | `run`、`submit`、`status`、`explain`、`doctor`、`deploy`、`destroy`、`deploy push-worker`、`deploy list-workers` | 在 `run` / `submit` / `status` / `explain` / `doctor` 上只对云端档起作用，部署命令用它给资源命名；两侧的值须一致。多环境切换（`prod-` / `stage-`）用它 |
| `--report-dir DIR` | `run`、`submit`、`status`、`explain`、`doctor` | `status` / `explain` 要给与 `submit` 相同的值才查得到这个 run。`submit --backend cloud` 下这个值还须与后端部署时设的报告前缀一致，不一致在提交前即被拒；`run --backend cloud` 不做这项比对 |
| `--steps-dir DIR` | `run`、`plan`、`submit`、`doctor`、`list-deterministic` | 五个命令上同义；云端档不生效（云端 worker 的 step 构建在镜像里） |
| `--default-engine {midscene,novaact}` | `run`、`plan`、`submit` | 三个命令上同义 |
| `--grace S` | `run` | 只有本机后端用它。云端的停止宽限在部署时由 `gherkai deploy --stop-timeout` 定，`--backend cloud` 给这个选项会退 `2` |
| `--json` | `run`、`plan`、`status`、`explain`、`doctor`、`list-engines`、`list-deterministic`、`deploy list-workers` | 每个命令输出各自的 JSON 文档；`submit` 没有这个选项，它的输出本来就只有一个 `run_id` |
| `--quiet` | `run` | 只影响进度输出与本机 worker 日志的落点 |
| `--region R`、`--profile P` | `run`、`submit`、`status`、`explain`、`doctor`、`deploy`、`destroy`、`deploy push-worker`、`deploy list-workers` | 优先于同义的环境变量（解析链见上）。云端 worker 只收 region，凭证用它自己的任务角色 |

`--json` 输出里有哪些字段、字段怎么用，入口在 [`running-and-results.md`](./running-and-results.md)。

## 云端资源名与网络的单项覆盖

下面这些选项只在 `--backend cloud` 下起作用，用来单独覆盖某一个资源名或网络设置。一般只用 `--prefix`；这些单项覆盖用于资源名不按前缀约定的部署。

| 选项 | 出现在 | 不给时用什么 | 环境变量 |
|---|---|---|---|
| `--ddb-table NAME` | `run`、`submit`、`status`、`explain` | `<prefix>runs` | `AWS_DDB_TABLE` |
| `--s3-bucket NAME` | `run`、`submit` | `<prefix>artifacts` | `AWS_S3_BUCKET` |
| `--events-table NAME` | `run` | `<prefix>events` | 无 |
| `--cluster NAME` | `run` | `<prefix>cluster` | 无 |
| `--subnet ID` | `run` | 部署时写入的参数 `/<prefix>backend/subnets` | 无 |
| `--security-group ID` | `run` | 部署时写入的参数 `/<prefix>backend/security-groups` | 无 |

`--subnet` 与 `--security-group` 可以重复给，表示多个子网或安全组。`submit` 只收 `--ddb-table` 与 `--s3-bucket`：它提交的 run 由云端后端拉起 worker，集群、events 表与网络用的是部署时写进后端的值。选云端 worker 镜像 variant 的 `--worker-variant` 见 [`cloud-backend.md`](./cloud-backend.md)。
