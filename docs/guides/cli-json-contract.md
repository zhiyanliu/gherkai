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
| `message` | string \| null | job 级「为何不是 passed」的原因原文（超时、未启动、fail-fast 被中止、worker 异常退出等）；passed 时为 null。**`message` 在本契约里恒为原因**：只出现在非 passed 态上，job 级与 step 级同义，与 worker 协议里的同名字段一脉相承 |
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
| `message` | string \| null | step 级失败原因原文（如「AI 断言未过多数票（0/1）：<断言文>」、act 异常的 `类型: 信息`）；passed 步为 null。旧 run 的落盘无此键 |
| `report_refs[]` | array | step 级产物指针：两引擎都有 `kind=evidence`（gherkai 自有格式的机读证据，`gherkai explain` 读它，见下节）；Nova 另有每次 act 的轨迹页 `kind=trajectory` |
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

## `gherkai explain <run_id> [<scope_id>] --json`

step 级证据视图：判定树（**骨架 = 提交时的 job 定义**）+ 每个 AI step 的机读证据。**不表判定**——退出码只有 `0`
（渲染成功，哪怕全部 step 没有证据、判定明细尚未落地）与 `2`（参数错 / run 或 scope 不存在 / 云端不可用）；
判定码看 `run` 或 `status --wait`。`--json` 下 stdout 只有这一个文档，「run 仍在跑」这类提示一律不打（机读侧看顶层 `status`）。

| 键 | 类型 | 含义 |
|---|---|---|
| `run_id` | string | |
| `status` | 同 `status` 一节的取值 | run 级运行态；未终态时文档只含已落地的那部分 job |
| `scopes[]` | array | 每个 job 一项，见下 |

`scopes[]` 每项 = `scope_id`、`engine`、`status`、`error_type`、`message`、`session_id`、`report_refs[]`（形状同 `run --json`，
原样搬判定明细里的指针、不解析）、`scenarios[]`，另加：

| 键 | 类型 | 含义 |
|---|---|---|
| `aborted_hint` | string \| null | 非 null = 这个 job 被中止且只落了部分 step 记录：已执行 step 的证据已产出，但指针没进判定记录 |
| `has_step_records` | bool | 这个 job 在判定明细里有没有任何 step 记录（按整个 job 算，不随 `--scenario` / `--step` 筛选变化）；false = 判定只剩 job 级那一层 |

`scenarios[]` 每项 = `scenario_id`、`name`、`status`（**null = 这条 scenario 没有判定记录**——worker 被外部中止时，
没跑完的 scenario 不进判定明细）、`steps[]`：

| 键 | 类型 | 含义 |
|---|---|---|
| `index` / `keyword` / `text` | int / string / string | 来自 job 定义（骨架）：0 起的书写序号、Given/When/Then、step 原文 |
| `status` / `votes` / `error_type` / `message` / `shortcircuited` / `duration_ms` / `report_refs[]` | | 同 `run --json` 的 `steps[]`；`record_missing` 为 true 时 `status` / `votes` / `error_type` / `message` / `duration_ms` 为 null、`report_refs` 为空数组、`shortcircuited` 恒 false（类型始终是 bool；判「有没有记录」一律看 `record_missing`） |
| `record_missing` | bool | true = 骨架里有这一步、判定明细里没有它的记录（未执行或未上报） |
| `evidence` | object \| null | 这一步的机读证据全文（固定键见下）；null 时看 `evidence_missing` |
| `evidence_missing` | `no_ref` / `unreadable` / `unsupported_schema` \| null | null = 证据已读到。`no_ref` = 这一步没有证据指针（确定性步/导航步本就不产，或抽取失败——两者在这里分不出来）；`unreadable` = 指针在但读不到或内容不是 JSON；`unsupported_schema` = 证据的格式版本这个 CLI 认不出 |

### `evidence` 的固定键

一个 AI step 一份，由 worker 在该 step 结束那一刻从引擎产物里抽出，两引擎同形。**字段全部可选容缺**（缺 → `null` /
空数组）：格式只承诺键名与类型，不承诺每个引擎每次都填满。

| 键 | 类型 | 含义 |
|---|---|---|
| `schema_version` | int | 证据格式版本，当前 `1`；认不出的版本 explain 报 `unsupported_schema` |
| `engine` | `novaact` / `midscene` | 产出它的引擎 |
| `scope_id` / `scenario_id` / `step_index` | string / string / int | 这份证据属于哪一步（与判定树冗余，为的是文件自包含） |
| `step` | object | `keyword` + `text`：该 step 的原文 |
| `status` / `message` | 同 `steps[]` 的两个同名键 | 与判定记录里同一步一致 |
| `acts[]` | array | 本 step 里的每次 AI 调用一项（N 票断言 = N 项），见下 |

`acts[]` 每项：

| 键 | 类型 | 含义 |
|---|---|---|
| `index` | int | 本 step 内第几次调用（0 起） |
| `prompt` | string \| null | 交给引擎的指令（step 文本 + 多行参数），不含引擎追加的输出格式样板 |
| `vote` | bool \| null | 这次调用计入判定的那一票；null = 不是投票调用（Given/When 的动作） |
| `url` | string \| null | 调用结束时的页面地址 |
| `frames[]` | array | 引擎内部逐步的「观察—思考—动作」，见下 |
| `result` | object \| null | **引擎原样返回值**：内部键随引擎版本变，**不属本契约**，只供阅读；判票看 `vote` |
| `error` | string \| null | 这次调用抛的错（`类型: 信息`）。Nova 出错的调用没有 frames（引擎不落轨迹文件），这是正常形态、不是抽取失败 |
| `time_worked_s` | number \| null | 这次调用的 agent 工作秒（Nova 报；Midscene 恒 null——它的计时是另一种量、不混用） |

`frames[]` 每项：

| 键 | 类型 | 含义 |
|---|---|---|
| `url` | string \| null | 该 frame 的页面地址（只有 Nova 有；Midscene 恒 null） |
| `thought` | string \| null | 模型这一步的推理原文——「为什么这么判」通常就在最后一段 |
| `screenshot` | string \| null | 该 frame 的截图（`file://` 或 `s3://`）；只有被截图策略选中的 frame 有，其余 null。**只给地址、不内嵌图**；云端档若 worker 中途被杀，地址可能取不到对象（按「读不到」处理） |
| `actions[]` | array | 每项 `name`（动作名）+ `args`（**引擎原样透传的参数对象**：内部键随引擎版本变、**不属本契约**） |

文本形态（不给 `--json`）是给人/agent 一次读进上下文的摘要，不是证据全文转写：默认每次调用只显示最后一段推理与它的截图
（超长截断并指回 `--json` 或那份证据文件），`--full` 关掉这个预算逐 frame 全文，`--all` 连通过的 step 也展开。

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
