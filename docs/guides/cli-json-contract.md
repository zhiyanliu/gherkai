# gherkai CLI 的 `--json` 字段契约

> **定位**：给拿 `--json` 写脚本或 agent skill 的人看的参考页（ADR 0041 决策五）。**权威在 code**：`core/gherkai_core/serialize.py`
> 与 `cli/gherkai_cli/render.py`（渲染器）、`cli/gherkai_cli/__main__.py`（`doctor` / `list-engines`）、
> `deploy_aws/gherkai_deploy_aws/workers.py`（`list-workers`）。本页与 code 的一致性由护栏守着：
> `cli/tests/test_cli_json_contract.py` 与 `deploy_aws/tests/test_workers.py` 用真渲染器生成样例、递归收集全部键名、
> 逐个断言出现在本页——漏键即红。本页只讲「有什么字段、什么意思、何时出现」，不讲为什么（那在 ADR）。

通则：`--json` 下 **stdout 只有一个 JSON 文档**，诊断/进度一律走 stderr；`null` 表示「无此值」（如无成本、未落值），
省略键表示「此形态下不存在」（各节注明）。退出码非 0 的前置/读取失败路径 stdout 可为空、诊断在 stderr——**先按退出码分流再解析**。
退出码含义见 `cli/README.md`「退出码」。

## `gherkai run … --json`

顶层 = RunResult（判定）+ `run_meta`（definition）+ `artifacts`（落点）。

| 键 | 类型 | 含义 |
|---|---|---|
| `run_id` | string | 本次 run 的 id（可排序时间戳前缀 + 随机尾） |
| `status` | `passed` / `failed` / `error` / `skipped` / `aborted` | run 级判定：任一 job error → error；任一 failed → failed；全 passed → passed |
| `duration_ms` | number \| null | run 级墙钟（含并发，≠ 各 job 之和） |
| `total_tokens` / `total_time_worked_s` | number \| null | 跨 job 的引擎原生量合计（Midscene 报 tokens、Nova 报 agent 工作秒）；无引擎报即 null，**不折美元** |
| `jobs[]` | array | 每个 job（= 一个 scope，一条浏览器会话）的判定，见下 |
| `run_meta` | object | 本次 run 的 definition（提交时定死），见下 |
| `artifacts` | object | 产物落点，见下；`--no-report` 时**省略**（例外：local 档 `--no-report --quiet` 仍有一键 `worker_log`） |

`jobs[]` 每项：

| 键 | 类型 | 含义 |
|---|---|---|
| `scope_id` | string | scope 键：`@scope:` 的值，或未标 scope 时的 scenario id（`<uri>:<行>`） |
| `status` | 同上五态 | job 判定 |
| `duration_ms` | number \| null | scope 墙钟（会话起止） |
| `total_tokens` / `total_time_worked_s` | number \| null | 本 job 的原生量合计（失败的 act 也计入） |
| `session_id` | string \| null | 引擎会话 id（血缘；可对上 worker 日志/轨迹目录） |
| `error_type` | string \| null | job 级归因（如 `timeout`）；skipped/aborted 恒 null、原因在 `message` |
| `message` | string \| null | job 级说明（超时、未启动原因、fail-fast 被中止等） |
| `report_refs[]` | array | job 级原生产物指针：`kind`（`summary` / `report`）、`ref`（`file://` 或 `s3://` URI）、`label` |
| `scenarios[]` | array | 见下 |

`scenarios[]` 每项：`scenario_id`（`<uri>:<行>`）、`status`、`duration_ms`、`report_refs[]`（同上形状）、`steps[]`：

| 键 | 类型 | 含义 |
|---|---|---|
| `index` | int | scenario 内 0 起的书写序号 |
| `status` | `passed` / `failed` / `error` / `skipped` | step 判定 |
| `duration_ms` | number \| null | step 墙钟（性能指标，与成本正交） |
| `votes` | object \| null | AI 断言才有：`yes`（赞成票）、`total`（总票数）；确定性/动作步为 null |
| `error_type` | string \| null | `assertion_failed` / `engine_error` / `network_error` / `timeout` … |
| `report_refs[]` | array | step 级原生产物（Nova：本 step 的 act 轨迹 `kind=trajectory`） |
| `shortcircuited` | bool | true = 上游 step error 后被跳过、未执行（此时 status=skipped） |

`run_meta`（definition）：`run_id`、`created_at`、`max_concurrency`、`steps_dir`（使用方确定性 step 目录，绝对路径或 null）、
`worker_variant` / `worker_task_defs`（cloud 档：提交时解析的 variant 与各引擎 task-def revision ARN，local 档省略）、
`extra_http_headers`（`--expose-local` 注入的请求头，无则省略）、`jobs[]`：

| 键 | 类型 | 含义 |
|---|---|---|
| `scope_id` / `scope_name` | string | 机器键 / 人写名（`@scope:` 原值或 scenario 标题） |
| `engine` | `novaact` / `midscene` | 该 scope 的引擎 |
| `assertion_votes` | int | AI 断言投票次数 |
| `timeout_s` | number \| null | job 墙钟预算秒；null = 不超时 |
| `scenarios[]` | array | `id`、`name`、`steps[]`：`index`、`keyword`（Given/When/Then）、`text`、`argument`（多行参数：`kind`=`docString` 带 `content`，或 `dataTable` 带 `rows`；无则省略） |

`artifacts`（全 URI；local `file://`，cloud `s3://` + `ddb://`）：

| 键 | 含义 |
|---|---|
| `run_meta` / `run_state` | definition / 运行态的落点 |
| `jobs_dir` | 判定明细目录（每 job 一份 JSON，形状 = 上面 `jobs[]` 的一项 + 内嵌 `job` definition） |
| `report_index` | RunReport `index.html`；报告写失败被隔离时**省略** |
| `worker_log` | worker 日志落点；仅 `--quiet` 且本机执行（`--backend local`）时出现——cloud 档 worker 在云端跑、日志在 CloudWatch，此键不出现 |

## `gherkai plan … --json`

| 键 | 类型 | 含义 |
|---|---|---|
| `default_engine` | string | 未标 `@engine` 的 scope 用的引擎 |
| `job_count` / `scenario_count` | int | 筛选后的数量（`--tags` / `--scenario` 生效后） |
| `jobs[]` | array | 与 `run_meta.jobs[]` 同形，另每个 step **可能**多一个 `deterministic` 键（出现条件见下） |

`steps[].deterministic` 三态：至少一个引擎自述成功时该键在**每个** step 上都出现——`null` = 走 AI；带 `pattern` + `description` = 命中
该确定性 step；带 `conflict`（命中的模式列表）= 多条模式同时命中，真跑该 step 会记 error（先改模式或措辞）。**全部引擎都问不到
worker 自述时该键整批省略**（不是 null；stderr 有「标注降级」提示）。部分引擎降级时，该引擎的 step 同样是 `null`、机读层与「走 AI」
不可区分——看 stderr 那行点出的引擎名。

## `gherkai status <run_id> --json`

RunState（控制面运行态）+ 附加 `artifacts`：

| 键 | 类型 | 含义 |
|---|---|---|
| `run_id` | string | |
| `status` | `pending` / `running` / 五终态 | run 级；**注意** job 已被认领时 run 级仍可能 `pending`（投影滞后一拍） |
| `started_at` / `ended_at` | ISO 8601 \| 省略 | `ended_at` 只在终态出现 |
| `high_water_mark` | int \| 省略 | 已投影的事件水位（诊断用）；仅经推进器投影写过的 run 有（`submit` / `status --wait` / 云端推进链），同步 `run` 落的 run_state 无此键 |
| `jobs[]` | array | `scope_id`、`status`（含 `pending` / `running` 前置态）、`session_id`（未起会话时 null，键恒在）、`claimed_at`（被推进器认领的时刻，超时起算点；未认领时**省略**） |
| `artifacts` | object | 与 `run` 同键（`run_meta` / `run_state` / `jobs_dir` / `report_index`）；是**约定落点**，终态后才真有内容 |

## `gherkai list-engines --json`

数组，每引擎一项：

| 键 | 含义 |
|---|---|
| `engine` | `novaact` / `midscene` |
| `available` | 本机能否拉起该引擎的 worker |
| `cmd` / `cwd` | 拉起命令（数组）与工作目录（多为 null）；不可用时为 null |
| `source` | 命中定位链的哪一级（`env …` / `同 venv 模块 …` / `PATH 可执行 …` / `uvx 兜底拉起 …`） |
| `hint` | 不可用时的安装指引；可用时 null |

## `gherkai list-deterministic --engine <名> --json`

顶层 `engine` + `deterministic_steps[]`，每项 `pattern`（正则，命中即走确定性）、`description` / `example`（step 作者登记的说明与示例——
写 `.feature` 时照 `example` 的说法写）。

## `gherkai doctor --json`

顶层 `ok`（全部 `required` 项通过，也是退出码 0/2 的依据）+ `checks[]`，每项：

| 键 | 含义 |
|---|---|
| `section` | `cli` / `engines` / `steps` / `aws` / `backend` / `provider` |
| `name` | 项名：`cli`：`version`；`engines`：`novaact` / `midscene` / `any`；`steps`：`dir` / `load.<engine>`；`aws`：`region` / `identity`；`backend`：`version` / `resources` / `worker.default` / `worker.<engine>` / `worker.any` / `reachability`（云端未查时的占位）；`provider`：`deploy-aws`（provider 不可用时的占位——没装 ok=true/required=false，装了但加载失败 ok=false）、provider 自报的 `node` / `cdk` / `container-engine`，或它的 name |
| `ok` | 该项通过 |
| `required` | false = 可选能力缺失（另一个引擎没装、没装 deploy-aws extra、部署工具链缺项），不影响退出码；退出码 = 全部 required 项是否 ok |
| `detail` | 一句人话：通过时是事实（命令、版本、ARN），失败时是怎么办 |

不给 `--backend cloud` / `--prefix` 时 `aws` / `backend` 段标「未查」、`required=false`。

## `gherkai deploy list-workers --json`

| 键 | 含义 |
|---|---|
| `prefix` / `version` | 后端前缀；「当前版本」= 本 CLI 版本（镜像 tag 命名空间） |
| `default_variant` | 默认 variant 名；未初始化为 null |
| `engines.<engine>.family` / `ecr_repo` | task-def family 与 ECR 仓库名 |
| `engines.<engine>.variants[]` | `variant`、`tag`（`<版本>-<variant>`）、`digest`、`pushed_at`、`revision_arn`、`template_arn` |
| `engines.<engine>.pending_cleanup[]` | 待清理 revision：`revision_arn`、`reason`（`retired` / `orphan`）、`variant`、`retired_at`、`registered_at` |
