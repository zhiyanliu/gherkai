# gherkai CLI 的 `--json` 字段契约

> **定位**：`--json` 字段的参考页，面向用它编写脚本或 agent skill 的读者（ADR 0041 决策五）。**权威在 code**：`core/gherkai_core/serialize.py`
> 与 `cli/gherkai_cli/render.py`（渲染器）、`runtime/gherkai_runtime/compose.py`（`artifacts` 四键的落点拼装：`local_artifact_locations` / `cloud_artifact_locations`）、`cli/gherkai_cli/__main__.py`（`doctor` / `list-engines`，另注入 `artifacts.worker_log`）、
> `deploy_aws/gherkai_deploy_aws/workers.py`（`list-workers`）；worker 侧两组：`engines/novaact/gherkai_worker_novaact/evidence.py`
> 与 `engines/midscene/src/worker/evidence.mts`（`evidence` 的固定键，两引擎同形）、`engines/novaact/gherkai_worker_novaact/deterministic.py`
> 的 `list_registry()` 与 `engines/midscene/src/worker/deterministic.mts` 的 `listRegistry()`（`list-deterministic` 的三键，worker 自述、CLI 只转述）。
> 本页与 code 的一致性由护栏保证：`cli/tests/test_cli_json_contract.py` 与 `deploy_aws/tests/test_workers.py` 用真渲染器生成样例
> （`explain` 的 `evidence` 用一份与两引擎映射测试同形的手写夹具）、递归收集全部键名（`actions[].args` 与 `acts[].result` 两个引擎透传节点不向下递归）、
> 逐个断言出现在本页，漏键即测试失败。本页只说明有哪些字段、各自的含义与出现条件，不说明理由——理由在 ADR。
> **agent skill 里的那份是本页的确定性转换副本**（`cli/gherkai_cli/skills/gherkai/references/cli-json-contract.md`，随 CLI wheel 发行）：
> 由 `tools/render_skill_contract.py` 生成，去掉本引用块与下方的姊妹页导航段，并把仓库内指针与内部用词改写成使用方可访问的形态；
> 本页改动后需重新运行生成器，`cli/tests/test_skill.py` 断言副本与转换结果相等（不用链接、不人工维护第二份的理由见 ADR 0043 决策四）。

姊妹页分工（本页只讲字段）：字段背后的判定语义（四层归约 / 状态 / 退出码）→ [`verdict-model.md`](./verdict-model.md)；`artifacts` 各键指向的落点与证据 → [`artifacts-and-evidence.md`](./artifacts-and-evidence.md)；字段何时具备内容（推进链与落地时机）→ [`execution-and-reconciliation.md`](./execution-and-reconciliation.md)。

通则：`--json` 下 **stdout 只有一个 JSON 文档**，诊断与进度一律输出到 stderr；`null` 表示「无此值」（如无成本、未落值），
省略键表示「此形态下不存在」（各节注明）。退出码非 0 的前置 / 读取失败路径 stdout 可为空、诊断输出在 stderr，因此**须先按退出码分流，再解析 stdout**。
退出码含义见 `docs/user-guide/running-and-results.md`「退出码」。

## `gherkai run … --json`

顶层 = RunResult（判定）+ `run_meta`（definition）+ `artifacts`（落点）。

| 键 | 类型 | 含义 |
|---|---|---|
| `run_id` | string | 本次 run 的 id（可排序时间戳前缀 + 随机后缀） |
| `status` | `passed` / `failed` / `error` | run 级判定：任一 job error → error；任一 failed → failed；否则 passed。job 级的 `skipped` / `aborted` 不参与 run 级聚合，故 run 级不出现这两个值 |
| `duration_ms` | number \| null | run 级墙钟（含并发，≠ 各 job 之和） |
| `total_tokens` / `total_time_worked_s` | number \| null | 跨 job 的引擎原生量合计（Midscene 上报 tokens、Nova 上报 agent 工作秒）；无引擎上报时为 null，**不折算为美元** |
| `jobs[]` | array | 每个 job（= 一个 scope，一条浏览器会话）的判定，见下 |
| `run_meta` | object | 本次 run 的 definition（提交时固定），见下 |
| `artifacts` | object | 产物落点，见下；`--no-report` 时**省略**（例外：local 档 `--no-report --quiet` 仍保留 `worker_log` 一个键） |

`jobs[]` 每项：

| 键 | 类型 | 含义 |
|---|---|---|
| `scope_id` | string | scope 键：`@scope:` 的值，或未标 scope 时的 scenario id（形态见下文 `scenario_id`） |
| `status` | `passed` / `failed` / `error` / `skipped` / `aborted` | job 判定；后两态只在同步 `run` 的 `--fail-fast` 路径出现（`skipped` = 未启动，`aborted` = 执行中被中止） |
| `duration_ms` | number \| null | scope 墙钟（会话起止） |
| `total_tokens` / `total_time_worked_s` | number \| null | 本 job 的原生量合计（失败的 act 也计入） |
| `session_id` | string \| null | 引擎会话 id（血缘；可与 worker 日志 / 轨迹目录对应） |
| `error_type` | string \| null | job 级归因（如 `timeout`）；skipped/aborted 恒 null、原因在 `message` |
| `message` | string \| null | job 级未达 passed 的原因原文（超时、未启动、fail-fast 被中止、worker 异常退出等）；passed 时为 null。**`message` 在本契约里恒表原因**：只出现在非 passed 态上，job 级与 step 级同义 |
| `report_refs[]` | array | job 级原生产物指针：`kind`（`summary` / `report`）、`ref`（`file://` 或 `s3://` URI）、`label` |
| `scenarios[]` | array | 见下 |

`scenarios[]` 每项：`scenario_id`（`<uri>:<行>[:<example 行>]`——Scenario Outline 展开的每行 example 各成一条，以 example 行号消歧）、`status`、`duration_ms`、`report_refs[]`（同上形状）、`steps[]`：

| 键 | 类型 | 含义 |
|---|---|---|
| `index` | int | scenario 内 0 起的书写序号 |
| `status` | `passed` / `failed` / `error` / `skipped` | step 判定 |
| `duration_ms` | number \| null | step 墙钟（性能指标，与成本正交） |
| `votes` | object \| null | 仅 AI 断言步有：`yes`（赞成票）、`total`（总票数）；确定性步与动作步为 null |
| `error_type` | string \| null | `assertion_failed` / `engine_error` / `network_error` / `timeout` … |
| `message` | string \| null | step 级失败原因原文（如「AI 断言未过多数票（0/1）：<断言文>」、act 异常的 `类型: 信息`）；passed 步为 null。旧 run 的落盘记录中无此键 |
| `report_refs[]` | array | step 级产物指针：两引擎都有 `kind=evidence`（gherkai 自有格式的机读证据，由 `gherkai explain` 读取，见下节）；Nova 另有每次 act 的轨迹页 `kind=trajectory` |
| `shortcircuited` | bool | true = 上游 step error 后被跳过、未执行（此时 status=skipped） |

`run_meta`（definition）：`run_id`、`created_at`、`max_concurrency`、`steps_dir`（使用方确定性 step 目录的绝对路径；未解析到目录时**省略**该键——不是 null；cloud 档恒省略，steps 构建在镜像里）、
`worker_variant` / `worker_task_defs`（cloud 档：提交时解析的 variant 与各引擎 task-def revision ARN，local 档省略）、
`extra_http_headers`（`--expose-local` 注入的请求头，无则省略）、`jobs[]`：

| 键 | 类型 | 含义 |
|---|---|---|
| `scope_id` / `scope_name` | string | 机器键 / 人可读名（`@scope:` 原值或 scenario 标题） |
| `engine` | `novaact` / `midscene` | 该 scope 的引擎 |
| `assertion_votes` | int | AI 断言投票次数 |
| `timeout_s` | number \| 省略 | job 墙钟预算秒；**不超时时整个键省略**（不是 null），`--default-job-timeout <=0` 即此形态。判断「不超时」用 `"timeout_s" not in job`，而非 `is None` |
| `scenarios[]` | array | `id`、`name`、`steps[]`：`index`、`keyword`（Given/When/Then）、`text`、`argument`（多行参数：`kind`=`docString` 带 `content`，或 `dataTable` 带 `rows`；无则省略） |

`artifacts`（全 URI；local `file://`，cloud `s3://` + `ddb://`）：

| 键 | 含义 |
|---|---|
| `run_meta` / `run_state` | definition / 运行态的落点 |
| `jobs_dir` | 判定明细目录（每 job 一份 JSON，文件名 = URL 编码的 scope_id；形状 = 前述 `jobs[]` 的一项，但**顶层 `scope_id` 换成内嵌的完整 `job` definition**（同 `run_meta.jobs[]` 每项的形状）——scope 键取自 `job.scope_id`，单文件自包含、无需读 run_meta） |
| `report_index` | RunReport `index.html`；报告写失败被隔离时**省略** |
| `worker_log` | worker 日志落点；仅 `--quiet` 且本机执行（`--backend local`）时出现；cloud 档 worker 在云端执行、日志进 CloudWatch，此键不出现 |

## `gherkai plan … --json`

| 键 | 类型 | 含义 |
|---|---|---|
| `default_engine` | string | 未标 `@engine` 的 scope 使用的引擎 |
| `job_count` / `scenario_count` | int | 筛选后的数量（`--scope` / `--tags` / `--scenario` 生效后；多个筛选 flag 同时给出时需全部满足） |
| `jobs[]` | array | 与 `run_meta.jobs[]` 同形；每个 step **可能**额外带一个 `deterministic` 键（出现条件见下） |

`steps[].deterministic` 三态：至少一个引擎自述成功时，该键在**每个** step 上都出现。`null` = 该 step 交由 AI 执行；带 `pattern` + `description`
= 命中该确定性 step；带 `conflict`（命中的模式列表）= 多条模式同时命中，实际执行该 step 会记 error（需先调整模式或 step 措辞）。
**全部引擎都取不到 worker 自述时该键整批省略**（不是 null；stderr 有「标注降级」提示）。部分引擎降级时，该引擎的 step 同样是
`null`、机读层与「交由 AI」不可区分；降级的引擎名见 stderr 的提示行。

## `gherkai status <run_id> --json`

RunState（控制面运行态）+ 附加 `artifacts`：

| 键 | 类型 | 含义 |
|---|---|---|
| `run_id` | string | |
| `status` | `pending` / `running` / `passed` / `failed` / `error` | run 级（job 级的 `skipped` / `aborted` 不上浮到 run 级）；job 已被认领时 run 级仍可能为 `pending`（投影滞后于 job 级状态） |
| `started_at` / `ended_at` | ISO 8601 \| 省略 | `ended_at` 只在终态出现 |
| `high_water_mark` | int \| 省略 | 已投影的事件水位（诊断用）；仅经推进器投影写入的 run 有（`submit` / `status --wait` / 云端推进链），同步 `run` 写出的 run_state 无此键 |
| `jobs[]` | array | `scope_id`、`status`（含 `pending` / `running` 前置态）、`session_id`（未建立会话时为 null，键恒在）、`claimed_at`（被推进器认领的时刻，超时起算点；未认领时**省略**） |
| `artifacts` | object | 与 `run` 同键（`run_meta` / `run_state` / `jobs_dir` / `report_index`）；是**约定落点**，仅在终态后有内容 |

## `gherkai explain <run_id> [<scope_id>] --json`

step 级证据视图：判定树（**骨架 = 提交时的 job 定义**）+ 每个 AI step 的机读证据。**不表判定**：退出码只有 `0`
（渲染成功，即使全部 step 没有证据、判定明细尚未落地）与 `2`（参数错 / run 或 scope 不存在 / 云端不可用）；
判定码由 `run` 或 `status --wait` 给出。`--json` 下 stdout 只有这一个文档，「run 仍在运行」这类提示一律不输出（机读侧从顶层 `status` 读运行态）。

| 键 | 类型 | 含义 |
|---|---|---|
| `run_id` | string | |
| `status` | 同 `status` 一节：`pending` / `running` / `passed` / `failed` / `error` | run 级运行态；未到终态时文档只含已落地的 job |
| `scopes[]` | array | 每个 job 一项，见下；指定 `--scenario` / `--step` 时**无一命中的 scope 整条不出现**（不产生空条目），此时条数可少于该 run 的 job 数 |

`scopes[]` 每项 = `scope_id`、`engine`、`status`、`error_type`、`message`、`session_id`、`report_refs[]`（形状同 `run --json`，
原样取自判定明细中的指针，不做解析）、`scenarios[]`，另加：

| 键 | 类型 | 含义 |
|---|---|---|
| `aborted_hint` | string \| null | 非 null = 该 job 终态是 `aborted` 或 `error`、且判定明细里只有**部分** step 的记录（一条记录都没有时不给出此提示）：已执行 step 的证据已产出，但指针未写入判定记录。不应据此判断终态，终态见同层 `status` |
| `has_step_records` | bool | 该 job 在判定明细里是否有任何 step 记录（按整个 job 统计，不随 `--scenario` / `--step` 筛选变化）；false = 判定只有 job 级一层 |

`scenarios[]` 每项 = `scenario_id`、`name`、`status`（**null = 这条 scenario 没有判定记录**：worker 被外部中止时，
未执行完的 scenario 不进入判定明细）、`steps[]`：

| 键 | 类型 | 含义 |
|---|---|---|
| `index` / `keyword` / `text` | int / string / string | 来自 job 定义（骨架）：0 起的书写序号、Given/When/Then、step 原文 |
| `status` / `votes` / `error_type` / `message` / `shortcircuited` / `duration_ms` / `report_refs[]` | | 同 `run --json` 的 `steps[]`；`record_missing` 为 true 时 `status` / `votes` / `error_type` / `message` / `duration_ms` 为 null、`report_refs` 为空数组、`shortcircuited` 恒 false（类型始终是 bool；判断有无记录一律以 `record_missing` 为准） |
| `record_missing` | bool | true = 骨架里有这一步，判定明细里没有对应记录（未执行或未上报） |
| `evidence` | object \| null | 这一步的机读证据全文（固定键见下）；为 null 时原因见 `evidence_missing`；`record_missing` 为 true 时恒为 null |
| `evidence_missing` | `no_ref` / `unreadable` / `unsupported_schema` \| null | null = 证据已读取。`no_ref` = 这一步没有证据指针，三种情形在此字段上无法区分：确定性步 / 导航步本不产出证据、AI 已执行但抽取失败、或这一步没有判定记录（`record_missing` 为 true）；区分「未执行」与「已执行但未产出证据」一律以 `record_missing` 为准；`unreadable` = 指针存在但读不到，或内容不是 JSON；`unsupported_schema` = 证据的格式版本当前 CLI 不识别 |

### `evidence` 的固定键

一个 AI step 一份，由 worker 在该 step 结束时从引擎产物中抽取，两引擎同形。**字段全部可选容缺**（缺 → `null` /
空数组）：格式只承诺键名与类型，不承诺每个引擎每次都填写完整。

| 键 | 类型 | 含义 |
|---|---|---|
| `schema_version` | int | 证据格式版本，当前 `1`；无法识别的版本由 explain 报 `unsupported_schema` |
| `engine` | `novaact` / `midscene` | 产出该证据的引擎 |
| `scope_id` / `scenario_id` / `step_index` | string / string / int | 这份证据所属的 step（与判定树冗余，用于使文件自包含） |
| `step` | object | `keyword` + `text`：该 step 的原文 |
| `status` / `message` | 同 `steps[]` 的两个同名键 | 与判定记录中同一步一致 |
| `acts[]` | array | 本 step 中的每次 AI 调用一项（N 票断言 = N 项），见下 |

`acts[]` 每项：

| 键 | 类型 | 含义 |
|---|---|---|
| `index` | int | 本 step 内的调用序号（0 起） |
| `prompt` | string \| null | 提交给引擎的指令（step 文本 + 多行参数），不含引擎追加的输出格式样板 |
| `vote` | bool \| null | 本次调用计入判定的票值；null = 非投票调用（Given/When 的动作步） |
| `url` | string \| null | 页面地址：Nova = 该次调用末 frame 的地址；Midscene = 本 **step** 结束时读取的一次 `page.url()`，同 step 各 act 共用同一值 |
| `frames[]` | array | 引擎内部逐步的「观察—思考—动作」，见下 |
| `result` | object \| null | **引擎原样返回值**：内部键随引擎版本变化，**不属本契约**，只供阅读；票值见 `vote` |
| `error` | string \| null | 本次调用抛出的错误（`类型: 信息`）。Nova 出错的调用没有 frames（引擎不写轨迹文件），这是正常形态、不是抽取失败 |
| `time_worked_s` | number \| null | 本次调用的 agent 工作秒（Nova 上报；Midscene 恒 null——其计时属另一种量、不混用） |

`frames[]` 每项：

| 键 | 类型 | 含义 |
|---|---|---|
| `url` | string \| null | 该 frame 的页面地址（只有 Nova 有；Midscene 恒 null） |
| `thought` | string \| null | 模型这一步的推理原文；判定理由通常在最后一段 |
| `screenshot` | string \| null | 该 frame 的截图（`file://` 或 `s3://`）；只有被截图策略选中的 frame 有，其余 null。**只记录地址、不内嵌图像**；云端档若 worker 中途被强制终止，该地址可能取不到对象（按「读不到」处理，同 `unreadable`） |
| `actions[]` | array | 每项 `name`（动作名）+ `args`（**引擎原样透传的参数对象**：内部键随引擎版本变化、**不属本契约**） |

文本形态（未给 `--json`）是摘要，不是证据全文转写：超长推理会截断，并提示改用 `--json` 或直接读那份证据文件；需要完整证据时使用 `--json`。`--all` / `--full` 的语义见 `docs/user-guide/running-and-results.md` 的 `explain` 一节。

## `gherkai list-engines --json`

数组，每引擎一项：

| 键 | 含义 |
|---|---|
| `engine` | `novaact` / `midscene` |
| `available` | 本机能否启动该引擎的 worker |
| `cmd` / `cwd` | 启动命令（数组）与工作目录（多为 null）；不可用时为 null |
| `source` | 命中定位链的哪一级（`env …` / `同 venv 模块 …` / `PATH 可执行 …` / `uvx 兜底拉起 …`） |
| `hint` | 不可用时的安装指引；可用时 null |

## `gherkai list-deterministic --engine <名> --json`

顶层 `engine` + `deterministic_steps[]`，每项 `pattern`（正则，命中即按确定性 step 执行）、`description` / `example`（step 作者登记的说明与示例；
写 `.feature` 时以 `example` 的表述为准）。

## `gherkai doctor --json`

顶层 `ok`（全部 `required` 项通过，也是退出码 0/2 的依据）+ `checks[]`，每项：

| 键 | 含义 |
|---|---|
| `section` | `cli` / `engines` / `steps` / `aws` / `backend` / `provider` |
| `name` | 项名：`cli`：`version`；`engines`：`novaact` / `midscene` / `any` / `model.<engine>`（本机该引擎 worker 自报的模型 id（云端 job 使用镜像内的模型），仅自述成功时出现）；`steps`：`dir` / `load.<engine>`；`aws`：`region` / `identity`；`backend`：`version` / `resources` / `worker.default` / `worker.<engine>` / `worker.any` / `worker.grace`（本机 worker 自报的收尾宽限 vs 云端 `stopTimeout`，缺口 ok=false/required=false）/ `reachability`（云端未查时的占位）；`provider`：`deploy-aws`（provider 不可用时的占位：未安装时 ok=true/required=false，已安装但加载失败时 ok=false）、provider 自报的 `node` / `cdk` / `container-engine`，或 provider 自身的 `name`（provider 未提供自检、或自检抛错时以它作项名） |
| `ok` | 该项通过 |
| `required` | false = 可选能力缺失（另一个引擎未安装、未安装 deploy-aws extra、部署工具链缺项），不影响退出码；退出码 = 全部 required 项是否 ok |
| `detail` | 一句说明：通过时给事实（命令、版本、ARN），失败时给处置办法 |

未给 `--backend cloud` / `--prefix` 时，`aws` / `backend` 段标「未查」、`required=false`。

## `gherkai deploy list-workers --json`

| 键 | 含义 |
|---|---|
| `prefix` / `version` | 后端前缀；「当前版本」= 本 CLI 版本（镜像 tag 命名空间） |
| `default_variant` | 默认 variant 名；未初始化为 null |
| `engines.<engine>.family` / `ecr_repo` | task-def family 与 ECR 仓库名 |
| `engines.<engine>.variants[]` | `variant`、`tag`（`<版本>-<variant>`）、`digest`、`pushed_at`、`revision_arn`、`template_arn` |
| `engines.<engine>.pending_cleanup[]` | 待清理 revision：`revision_arn`、`reason`（`retired` / `orphan`）、`variant`、`retired_at`、`registered_at` |
