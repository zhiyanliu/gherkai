# gherkai CLI 的 `--json` 字段契约

通则：`--json` 下 **stdout 只有一个 JSON 文档**，诊断与进度一律输出到 stderr；`null` 表示「无此值」（如无成本、未落值），
省略键表示「此形态下不存在」（各节注明）。退出码非 0 的前置 / 读取失败路径 stdout 可为空、诊断输出在 stderr，因此**须先按退出码分流，再解析 stdout**。
退出码含义见 `SKILL.md` 的退出码一节，或 https://github.com/zhiyanliu/gherkai/blob/HEAD/docs/user-guide/running-and-results.md 「退出码」。

## `gherkai run … --json`

顶层由三部分组成：这次运行的判定、`run_meta`（提交时固定的本次运行任务本身）、`artifacts`（落点）。

| 键 | 类型 | 含义 |
|---|---|---|
| `run_id` | string | 本次 run 的 id（可排序时间戳前缀 + 随机后缀） |
| `status` | `passed` / `failed` / `error` / `aborted` | run 级判定：任一 job 为 error 则 error；任一为 failed 则 failed；否则 passed。job 级的 `skipped` / `aborted` 不参与 run 级聚合；唯一例外是同步 `run` 被使用方中断（Ctrl-C 或 SIGTERM）且有 job 记 `skipped` 或 `aborted` 时，run 级直接记 `aborted`（判定不完整，不按仅有的判定聚合） |
| `duration_ms` | number \| null | run 级墙钟（含并发，不等于各 job 之和） |
| `total_tokens` / `total_time_worked_s` | number \| null | 跨 job 的引擎原生量合计（Midscene 上报 tokens、Nova 上报 agent 工作秒）；无引擎上报时为 null，**不折算为美元** |
| `device_observed_s` / `device_observed_missing` | number / int \| 省略 | 仅当 run 含设备目标 job 时出现：各设备 job 的 `device_observed_s` 之和，与 `origin` 为 `created` / `discovered` 而 `observed_s` 为 null 的会话总数（不计入合计；`attempted` 的尝试两键都不计） |
| `jobs[]` | array | 每个 job（即一个 scope）的判定，见下 |
| `run_meta` | object | 本次 run 的任务定义（提交时固定），见下 |
| `artifacts` | object | 产物落点，见下；`--no-report` 时**省略**（例外：local 后端 `--no-report --quiet` 仍保留 `worker_log` 一个键） |

`jobs[]` 每项：

| 键 | 类型 | 含义 |
|---|---|---|
| `scope_id` | string | scope 键：`@scope:` 的值，或未标 scope 时的 scenario id（形态见下文 `scenario_id`） |
| `status` | `passed` / `failed` / `error` / `skipped` / `aborted` | job 判定；后两态只在同步 `run` 出现——`--fail-fast` 中止这个 run，或使用方中断（Ctrl-C / SIGTERM）（`skipped` 表示未启动，`aborted` 表示执行中被中止） |
| `duration_ms` | number \| null | scope 墙钟：从 `scope_started` 到 `scope_done`，不含建立会话的时间（设备目标也不含获取设备的时间）；未收到 `scope_started` 或 `scope_done` 时为 null（执行前失败、超时、worker 异常退出、未启动、被中止） |
| `total_tokens` / `total_time_worked_s` | number \| null | 本 job 的原生量合计（失败的 act 也计入） |
| `session_id` | string \| null | 云端浏览器会话 id（血缘；两个引擎都是 AgentCore 浏览器会话 id，可与 worker 日志对应；Nova Act 的轨迹目录按另一种会话 id 命名，worker 日志里有两者的对应行）；设备目标为 Device Farm 远程访问会话的 ARN |
| `sessions[]` | array \| 省略 | 本 job 开过或尝试过的每个会话一项：设备目标是 Device Farm 远程访问会话，桌面目标是 AgentCore 浏览器会话（两个引擎的桌面 worker 都报出会话的建立与停止）；没有会话记录的桌面 job 省略此键。每项含 `session_id`（结果未知的创建尝试为 null）、`name`（会话名；桌面目标与 `session_id` 相同，结果未知的创建尝试为这次请求携带的会话名）、`origin`（`created` / `discovered` / `attempted`；桌面目标没有 `discovered`）、`release`（`confirmed` / `unconfirmed`）、`observed_s`（worker 观察到的占用秒数，缺则 null；桌面目标恒为 null）、`provider_minutes`（服务商回报的 `{total, metered, unmetered}` 快照，缺则 null；桌面目标恒为 null）、`device`（worker 原样报出的设备描述，形如 `{platform, model, osVersion, unit}`、对本工具不透明，缺则 null；桌面目标恒为 null；文本输出的「设备」一行与报告页的设备描述由代表会话的这一项派生） |
| `device_observed_s` / `device_observed_missing` | number / int \| 省略 | 仅设备目标（桌面 job 带会话记录时同样省略）：本 job 各会话 `observed_s` 之和，与 `origin` 为 `created` / `discovered` 而 `observed_s` 为 null 的会话数（不计入合计；`attempted` 的尝试两键都不计，逐条见 `sessions[]`） |
| `error_type` | string \| null | job 级归因（如 `timeout`、`precheck_failed`、`acquire_timeout`、`session_lost`、`release_failed`）；skipped/aborted 恒 null、原因在 `message`。`release_failed` 表示有会话未能确认停止（设备目标与桌面目标都可能出现），`message` 列出会话名，并按目标说明到哪里核对 |
| `message` | string \| null | job 级未达 passed 的原因原文（超时、未启动、fail-fast 或使用方中断导致的中止、worker 异常退出等）；passed 时为 null。**`message` 在本契约里恒表原因**：只出现在非 passed 态上，job 级与 step 级同义 |
| `report_refs[]` | array | job 级原生产物指针：`kind`（`summary` / `report`；设备目标另有 `device_session`，见 `explain` 一节）、`ref`（`file://` 或 `s3://` URI）、`label` |
| `scenarios[]` | array | 见下 |

`scenarios[]` 每项：`scenario_id`（`<uri>:<行>[:<example 行>]`——Scenario Outline 展开的每行 example 各成一条，以 example 行号消歧）、`status`（`passed` / `failed` / `error`，或 `skipped`——worker 报告 scope 级 error（scope 未能就绪，或执行中途无法继续，如会话丢失、设备失去响应）后，该 scenario 从未执行、由本工具补记）、`duration_ms`、`report_refs[]`（形状同上；**当前两引擎都不填 scenario 级产物，恒为空数组**——产物在 step 级与 job 级）、`steps[]`：

| 键 | 类型 | 含义 |
|---|---|---|
| `index` | int | scenario 内 0 起的书写序号 |
| `status` | `passed` / `failed` / `error` / `skipped` | step 判定 |
| `duration_ms` | number \| null | step 墙钟（性能指标，与成本正交） |
| `votes` | object \| null | 仅 AI 断言步有：`yes`（赞成票）、`total`（总票数）；确定性步与动作步为 null |
| `error_type` | string \| null | `assertion_failed` / `engine_error` / `network_error` / `timeout` / `session_lost` / `capability_unavailable`（设备目标：这一步需要的能力在该设备上不提供，重试不会变）… |
| `message` | string \| null | step 级失败原因原文（如「AI 断言未过多数票（0/1）：<断言文>」、act 异常的 `类型: 信息`）；passed 步为 null。旧 run 的落盘记录中无此键 |
| `report_refs[]` | array | step 级产物指针：两引擎都有 `kind=evidence`（gherkai 自有格式的机读证据，由 `gherkai explain` 读取，见下节）；Nova 另有每次 act 的轨迹页 `kind=trajectory` |
| `shortcircuited` | bool | true 表示上游 step error 后被跳过、未执行（此时 status 为 skipped）；status 为 skipped 而此值为 false 表示 worker 报告 scope 级 error 后这一步从未执行，由本工具补记 |

`run_meta`（definition；**键集固定**，不适用的值为 `null` 而不是省键）：`schema_version`（definition 的整数结构版本，当前为 1；`status` / `explain` 读到不等于本机支持的版本以退出码 2 结束并提示升级或改用写出它的版本）、`cli_version`（写出这份记录的 gherkai 版本，只记录；取不到时 null）、`run_id`、`created_at`、`max_concurrency`、`steps_dir`（使用方确定性 step 目录的绝对路径；没有时 null；cloud 后端恒 null，steps 构建在镜像里）、
`worker_variant` / `worker_task_defs`（cloud 后端：提交时解析的 variant 与各引擎 task-def revision ARN；local 后端 null）、
`extra_http_headers`（`--expose-local` 注入的请求头，无则 null）、`session_warmup_url`（`--expose-local` 下本次 run 的会话预热地址，输出时令牌参数的值已替换为 `***`；无则 null）、`jobs[]`：

| 键 | 类型 | 含义 |
|---|---|---|
| `scope_id` / `scope_name` | string | 机器键 / 人可读名（`@scope:` 原值或 scenario 标题） |
| `engine` | `novaact` / `midscene` | 该 scope 的引擎 |
| `assertion_votes` | int | AI 断言投票次数 |
| `timeout_s` | number \| null | job 墙钟预算秒；不超时为 `null`，`--default-job-timeout <=0` 即此形态（只对桌面目标；设备目标始终有值） |
| `target` | object | 测试目标（桌面网页也写出 `desktop` / `web`）：`device`（`desktop` / `android` / `ios`）、`ui_kind`（`web` / `app`）；`ui_kind` 为 `app` 时另带 `app`（`alias`、`bucket`、`key`、`sha256`、`app_id`：安装包在 S3 的完整位置与包名或 bundle id；`plan --json` 里只有 `alias` 与 `app_id`，安装包在 `run` / `submit` 时才上传，位置三项恒省略） |
| `device_request` | object \| null | 设备目标的设备请求，桌面目标为 `null`：`provider`（当前只有 `aws-device-farm`）、`device_arn` 或 `os_version`（二选一）、`billing_method`（`METERED` / `UNMETERED`）、`project_arn`、`acquire_timeout_s`；`plan --json` 里恒为 `null`（plan 不解析设备请求） |
| `scenarios[]` | array | `id`、`name`、`steps[]`：`index`、`keyword`（Given/When/Then）、`text`、`argument`（多行参数：`kind` 为 `docString` 时带 `content`，为 `dataTable` 时带 `rows`；无则省略） |

`artifacts`（全 URI；local `file://`，cloud `s3://` + `ddb://`）：

| 键 | 含义 |
|---|---|
| `run_meta` / `run_state` | 任务定义 / 运行态的落点 |
| `jobs_dir` | 判定明细目录（每 job 一份 JSON，文件名是 URL 编码的 scope_id；形状同前述 `jobs[]` 的一项，但**顶层 `scope_id` 换成内嵌的完整 `job` 定义**（同 `run_meta.jobs[]` 每项的形状）——scope 键取自 `job.scope_id`，单文件自包含、无需读 run_meta） |
| `report_index` | 报告首页 `index.html`；报告写失败被隔离时**省略** |
| `worker_log` | worker 日志落点；仅 `--quiet` 且本机执行（`--backend local`）时出现；cloud 后端 worker 在云端执行、日志进 CloudWatch，此键不出现 |

## `gherkai plan … --json`

| 键 | 类型 | 含义 |
|---|---|---|
| `default_engine` | string | 未标 `@engine` 的 scope 使用的引擎 |
| `job_count` / `scenario_count` | int | 筛选后的数量（`--scope` / `--tags` / `--scenario` 生效后；多个筛选 flag 同时给出时需全部满足） |
| `device_session_count` | int | 这次 run 将建立的远程访问会话数：一个设备目标的 scope 一个会话，全部桌面时为 0 |
| `devices` | object | 各平台的设备选择，只列这次 run 里出现的平台（键为 `android` / `ios`）：指定一台时含 `arn`（设备 ARN）与 `source`，按系统版本挑选时含 `os_version`（要求的系统版本）与 `source`，没有任何来源指定时为 `null`（`run` / `submit` 会以退出码 2 结束）；`source` 是来源说明（选项名、环境变量名或配置文件的节与键）。全部桌面时为 `{}` |
| `jobs[]` | array | 与 `run_meta.jobs[]` 结构相同；每个 step **可能**额外带一个 `deterministic` 键（出现条件见下） |

`steps[].deterministic` 四态：至少一个引擎的确定性命中查询成功时，该键在**每个** step 上都出现。`null` 表示该 step 交由 AI 执行；带 `pattern` 与 `description`
表示命中该确定性 step（命中条目在该 scope 目标上的交集条目带前提时另带 `requires`（字符串数组，当前取值只有 `web_context`：设备不提供时这一步会记 error、不转 AI），无前提时省略该键；命中的模式在该 scope 的目标上没有实现时同样为 `null`，stderr 说明走 AI 的原因）；带 `conflict`（命中的模式列表）表示多条模式同时命中，实际执行该 step 会记 error（需先调整模式或 step 措辞）；带 `keyword_mismatch`（命中的模式）与 `keywords`（该 step 接受的关键字）表示这条写法在当前关键字下无意义，实际执行会记 error（如 Then 后只写一个地址）。
**全部引擎的确定性命中查询都取不到结果时该键在每个 step 上一律省略**（不是 null；stderr 有「标注降级」提示；取不到指该引擎的 worker 未能定位、起不来、超时或输出不是合法 JSON）。部分引擎的命中查询取不到结果时，该引擎的 step 同样是
`null`、机读层与「交由 AI」不可区分；降级的引擎名见 stderr 的提示行。命中查询成功而能力自述取不到的引擎，命中的 step 不按 scope 目标核对、一律带 `pattern` 与 `description`（stderr 同样有「标注降级」提示）。
其余失败不降级：worker 起来了但非零退出（如使用方 steps 加载失败）、能力自述与命令行工具不兼容（如两者版本不一致）时，`plan` 以退出码 2 结束、stdout 没有输出。

## `gherkai status <run_id> --json`

顶层由两部分组成：这个 run 的运行态与附加的 `artifacts`：

| 键 | 类型 | 含义 |
|---|---|---|
| `run_id` | string | |
| `status` | `pending` / `running` / `passed` / `failed` / `error` / `skipped` / `aborted` | run 级（job 级的 `skipped` / `aborted` 不上浮到 run 级；`aborted` 只来自被使用方中断的同步 `run`；`skipped` 只在全部 job 都没有执行、又没有被中断时出现，现行的执行方式不产生这样的 run，读取方按可能的取值处理即可）。未到终态时，只要有 job 离开 `pending`（被认领、开始执行或已有判定），run 级即为 `running`、不再回到 `pending`；所以 run 级为 `pending` 表示还没有 job 离开 `pending`。反过来不成立：run 级为 `running` 时 job 仍可能全为 `pending`，要查看各 job 当前记录的状态，读 `jobs[]` |
| `started_at` / `ended_at` | ISO 8601 \| 省略 | `ended_at` 只在终态出现 |
| `high_water_mark` | int \| 省略 | 已处理到的事件水位（诊断用）；仅由后台推进写入的 run 有（`submit` / `status --wait` / 云端推进链），同步 `run` 写出的 run_state 无此键 |
| `message` | string \| 省略 | run 级原因，只在云端推进链**不经任何 job** 就把 run 置为 `error` 时出现（提交记录的结构版本不是后端认的、提交记录不完整、缺 worker 镜像版本）；job 级原因不在这里，看 `run --json` / `explain --json` 里 job 与 step 的 `message` |
| `jobs[]` | array | `scope_id`、`status`（含 `pending` / `running` 前置态）、`session_id`（未建立会话时为 null，键恒在）、`claimed_at`（被后台推进认领的时刻，超时起算点；未认领时**省略**） |
| `artifacts` | object | 与 `run` 同键（`run_meta` / `run_state` / `jobs_dir` / `report_index`）；是**约定落点**，仅在终态后有内容 |

## `gherkai list-runs --json`

一个对象：顶层是所查的落点与执行这次清单的 gherkai 版本，`runs[]` 是找到的 run，按 run_id 降序（即按创建时间从新到旧，创建时间取执行 `run` 或 `submit` 的那台机器的时钟；同一秒内创建的 run 之间先后不定）。默认列出这个后端全部未结束的 run（`pending` / `running`）与最近创建的 `--limit` 条已结束的 run（默认 20 条）；给了 `--status` 时只列这些状态的 run，其中已结束的状态仍受 `--limit` 约束。**不表判定**：退出码只有 `0`（读到了清单；清单为空时 `runs` 是空数组，含 `unreadable` 项的清单同样为 `0`）与 `2`（参数不合法或读不到这个后端，stdout 没有输出）；`--json` 下不输出人读提示，读取方凭顶层的落点分辨「这里没有 run」与「查错了地方」。

| 键 | 类型 | 含义 |
|---|---|---|
| `backend` | `local` / `cloud` | 所查的后端，恒有 |
| `report_dir` | string | 仅本机后端：所查的报告落点目录（各层取值解析后的绝对路径；目录不存在时同样给出） |
| `prefix` / `region` / `ddb_table` | string | 仅云端后端：所查部署的资源名前缀、region 与运行状态表名（都是解析后的值，不区分来自选项、环境变量还是配置文件）。不带 profile（它只决定用哪份凭证），不带云端的报告前缀（清单不读报告） |
| `cli_version` | string \| null | 恒有：执行这次清单的 gherkai 版本，取不到时为 null。与 `runs[]` 各项的 `cli_version` 比较，可知哪些 run 由当前版本写出；为 null 时无从比较，没有哪一项算当前版本写出 |
| `runs[]` | array | 每个 run 一项，见下 |

`runs[]` 每项：

| 键 | 类型 | 含义 |
|---|---|---|
| `run_id` | string | 恒有 |
| `status` | 同 `status` 一节 | run 级状态，取值与 `status --json` 的 `status` 相同；是读回时的当前状态 |
| `started_at` / `ended_at` | ISO 8601 \| 省略 | 无值时省略 |
| `message` | string \| 省略 | 含义同 `status --json` 的 `message`，无值时省略 |
| `job_counts` | object | 按 job 状态计数，形如 `{"passed": 2, "failed": 1}`：键取 job 级状态值 `pending` / `running` / `passed` / `failed` / `error` / `skipped` / `aborted`，只含出现的状态，缺的状态按 0 读。逐个 job 的状态用 `status --json` 的 `jobs[]` 取（形状不同，所以键名不复用） |
| `detached` | bool | 运行态读得出的项恒有：true 表示由 `submit` 提交到后台执行的 run。未结束且为 false 的 run 由前台 `run` 执行：执行它的进程若已不在，它不会再到终态，`status --wait` 对它只等待、不接力 |
| `cli_version` | string \| null | 恒有：写出这个 run 的 gherkai 版本，读不到（提交记录不存在、其中没有版本或内容无法解析）时为 null。不为 null 且与顶层 `cli_version` 相同，即由当前版本写出 |
| `unreadable` | `true` \| 省略 | 只在这个 run 的运行态无法解析时出现（可能由其它版本写出）。这样的项只含 `run_id`、`unreadable` 与 `cli_version`，其余键省略；它没有可用的状态，不参与 `--status` 过滤与 `--limit` 截取，找到即列出。用 `gherkai status <run_id>` 查看 |

清单不带产物落点、任务定义的内容与事件水位：对选中的 run 用 `status --json` 与 `explain --json` 取。云端后端按状态找 run 的那一步是最终一致的，刚换状态或刚建的 run 偶尔会在一次清单里缺席，稍后再查即可见；各项的状态、时刻与 job 计数以读回的运行态为准。由更新版本写出、状态值当前所用的 gherkai 版本不认识的 run，本机后端列为 `unreadable`，云端后端看不到。

## `gherkai explain <run_id> [<scope_id>] --json`

step 级证据视图：判定树（**骨架是提交时的 job 定义**）与每个 AI step 的机读证据（设备目标上另含判为 failed / error 的确定性与导航 step，其 `acts` 为空数组）。**不表判定**：退出码只有 `0`
（渲染成功，即使全部 step 没有证据、判定明细尚未落地）与 `2`（参数错 / run 或 scope 不存在 / 云端不可用）；
表判定的退出码由 `run` 或 `status --wait` 给出。`--json` 下 stdout 只有这一个文档，「run 仍在运行」这类提示一律不输出（机读侧从顶层 `status` 读运行态）。

| 键 | 类型 | 含义 |
|---|---|---|
| `run_id` | string | |
| `status` | 同 `status` 一节：`pending` / `running` / `passed` / `failed` / `error` / `skipped` / `aborted` | run 级运行态；未到终态时文档只含已落地的 job |
| `scopes[]` | array | 每个 job 一项，见下；指定 `--scenario` / `--step` 时**无一命中的 scope 整条不出现**（不产生空条目），此时条数可少于该 run 的 job 数 |

`scopes[]` 每项包含 `scope_id`、`engine`、`status`、`error_type`、`message`、`session_id`、`sessions[]`（出现条件与形状同 `run --json`）与 `device_observed_s` / `device_observed_missing`（仅设备目标，形状同 `run --json`）、`console_url`（仅当 `session_id` 是 Device Farm 远程访问会话的 ARN 时出现：控制台里该会话页面的链接，录像与日志在那里看）、`report_refs[]`（形状同 `run --json`，
原样取自判定明细中的指针，不做解析；设备目标另有 `kind=device_session`，指向这个 scope 的设备诊断文件 `device-session.json`（能力探测结论、所用会话与设备、换台记录与各阶段时刻），只给链接、不解析）、`scenarios[]`，另加：

| 键 | 类型 | 含义 |
|---|---|---|
| `aborted_hint` | string \| null | 非 null 表示该 job 终态是 `aborted` 或 `error`、骨架里有无记录的 step，而本工具**没能**从事件流补取它们的记录（后半句写明原因：这个 run 没有事件流记录、事件流里没有这个 job 的记录（云端 events 表只保留 7 天，或 worker 在发出任何事件前就被中止）、本机事件库读取失败、云端 events 表读不到或缺权限、记录解析失败）。补取成功时为 null，补到的 step 见 `steps[].record_source`。不应据此判断终态，终态见同层 `status` |
| `recovered_steps` | int | 这个 job 从事件流补取到的 step 数（按整个 job 统计，不随 `--scenario` / `--step` 筛选变化；筛后文档里 `record_source` 为 `events` 的 step 可能少于它）；为 0 且 `has_step_records` 为 false 时文本形态才指去看 worker 日志 |
| `has_step_records` | bool | 该 job 在判定明细里是否有任何 step 记录（按整个 job 统计，不随 `--scenario` / `--step` 筛选变化；含本工具在 scope 级 error 后补记的 skipped 记录）；false 表示判定只有 job 级一层 |

`scenarios[]` 每项包含 `scenario_id`、`name`、`status`（**null 表示这条 scenario 没有判定记录**：worker 被外部中止时，未执行完的 scenario 不进入判定明细）、`unfinished`（bool：true 表示这条 scenario 没有判定记录也没有 `scenario_done`，但事件流里有它已执行 step 的记录、已补进 `steps[]`（给了 `--step` 筛选时只出现被筛到的那一步）；判定明细缺这条 scenario 而事件流里有 `scenario_done` 时，`status` 取事件流里的判定、`unfinished` 为 false，其 step 的 `record_source` 仍为 `events`）、`steps[]`：

| 键 | 类型 | 含义 |
|---|---|---|
| `index` / `keyword` / `text` | int / string / string | 来自 job 定义（骨架）：0 起的书写序号、Given/When/Then、step 原文 |
| `status` / `votes` / `error_type` / `message` / `shortcircuited` / `duration_ms` / `report_refs[]` | | 同 `run --json` 的 `steps[]`；`record_missing` 为 true 时 `status` / `votes` / `error_type` / `message` / `duration_ms` 为 null、`report_refs` 为空数组、`shortcircuited` 恒 false（类型始终是 bool；判断有无记录一律以 `record_missing` 为准） |
| `record_missing` | bool | true 表示骨架里有这一步，判定明细里没有它、从事件流也没补到（未执行、被中止时还没上报完成记录，或事件流读不到——这种情形所属 scope 的 `aborted_hint` 带原因） |
| `record_source` | `verdict` / `events` \| null | 这一步记录的来源：`verdict` 来自判定明细；`events` 是 job 被中止后从事件流补取的（这条 scenario 不在判定明细里，这一步已执行完并上报），字段与判定明细里的相同；`record_missing` 为 true 时为 null |
| `evidence` | object \| null | 这一步的机读证据全文（固定键见下）；为 null 时原因见 `evidence_missing`；`record_missing` 为 true 时恒为 null |
| `evidence_missing` | `no_ref` / `unreadable` / `unsupported_schema` \| null | null 表示证据已读取。`no_ref` 表示这一步没有证据指针，三种情形在此字段上无法区分：确定性步 / 导航步本不产出证据（设备目标上只有 passed 的确定性步 / 导航步如此）、AI 已执行但抽取失败、或这一步没有判定记录（`record_missing` 为 true）；区分「未执行」与「已执行但未产出证据」一律以 `record_missing` 为准；`unreadable` 表示指针存在但读不到，或内容不是 JSON；`unsupported_schema` 表示证据的格式版本当前 CLI 不识别 |

### `evidence` 的固定键

一个 AI step 一份（设备目标上判为 failed / error 的确定性与导航 step 也有一份），由 worker 在该 step 结束时从引擎产物中抽取，两引擎结构相同。**字段全部可选容缺**（缺则给 `null` /
空数组）：格式只承诺键名与类型，不承诺每个引擎每次都填写完整。

| 键 | 类型 | 含义 |
|---|---|---|
| `schema_version` | int | 证据格式版本，当前 `1`；无法识别的版本由 explain 报 `unsupported_schema` |
| `engine` | `novaact` / `midscene` | 产出该证据的引擎 |
| `scope_id` / `scenario_id` / `step_index` | string / string / int | 这份证据所属的 step（与判定树冗余，用于使文件自包含） |
| `step` | object | `keyword` + `text`：该 step 的原文 |
| `status` / `message` | 同 `steps[]` 的两个同名键 | 与判定记录中同一步一致 |
| `acts[]` | array | 本 step 中的每次 AI 调用一项（N 票断言对应 N 项），见下；设备目标上判为 failed / error 的确定性与导航 step 也有一份证据，此时为空数组 |
| `step_kind` | `ai` / `deterministic` / `navigation` \| 省略 | 仅设备目标：这一步的执行方式；据它区分「没有 act 是正常的」与「证据抽取失败」 |
| `url` / `url_missing` | string \| null / string \| null | 仅设备目标：step 结束时的页面地址；取不到时 `url` 为 null 并由 `url_missing` 说明原因（`no_web_context` 设备不提供网页上下文、`not_applicable` 应用目标、`timeout`、`error`） |
| `controls` / `controls_missing` | object \| null / string \| null | 仅设备目标且仅 failed / error 步：`controls` 是一个对象，含 `items[]`（每项 `type` / `id` / `text` / `a11y_id`，空数组表示采集成功但这一屏没有可识别控件）、`total`（采到的控件总数）与 `truncated`（`items[]` 是否因上限被截断）；采集失败时 `controls` 为 null、`controls_missing` 为 `timeout` 或 `error`；passed 步与桌面目标省略 |
| `page_source` / `page_source_truncated` | string \| null / bool | 仅设备目标且仅 failed / error 步：原始控件树文件的地址（`file://` 或 `s3://`，只给地址不内嵌；采集或写盘失败时为 null）与它是否因超过大小上限被截断；云端后端若 worker 中途被强制终止，该地址可能取不到对象（同 `frames[].screenshot`，按「读不到」处理） |

`acts[]` 每项：

| 键 | 类型 | 含义 |
|---|---|---|
| `index` | int | 本 step 内的调用序号（0 起） |
| `prompt` | string \| null | 提交给引擎的指令（step 文本 + 多行参数），不含引擎追加的输出格式样板 |
| `vote` | bool \| null | 本次调用计入判定的票值；null 表示非投票调用（Given/When 的动作步） |
| `url` | string \| null | 页面地址：Nova 引擎给的是该次调用末 frame 的地址；Midscene 引擎给的是本 **step** 结束时读取的一次地址（桌面为 `page.url()`；设备目标为网页上下文里读到的地址，与证据顶层 `url` 同值，取不到时为 null、原因见顶层 `url_missing`），同 step 各 act 共用同一值 |
| `frames[]` | array | 引擎内部逐步的「观察—思考—动作」，见下 |
| `result` | object \| null | **引擎原样返回值**：内部键随引擎版本变化，**不属本契约**，只供阅读；票值见 `vote` |
| `error` | string \| null | 本次调用抛出的错误（`类型: 信息`）。Nova 出错的调用没有 frames（引擎不写轨迹文件），这是正常形态、不是抽取失败 |
| `time_worked_s` | number \| null | 本次调用的 agent 工作秒（Nova 上报；Midscene 恒 null——其计时属另一种量、不混用） |

`frames[]` 每项：

| 键 | 类型 | 含义 |
|---|---|---|
| `url` | string \| null | 该 frame 的页面地址（只有 Nova 有；Midscene 恒 null） |
| `thought` | string \| null | 模型这一步的推理原文；判定理由通常在最后一段 |
| `screenshot` | string \| null | 该 frame 的截图（`file://` 或 `s3://`）；只有被截图策略选中的 frame 有，其余 null。**只记录地址、不内嵌图像**；云端后端若 worker 中途被强制终止，该地址可能取不到对象（按「读不到」处理，同 `unreadable`） |
| `actions[]` | array | 每项 `name`（动作名）+ `args`（**引擎原样透传的参数对象**：内部键随引擎版本变化、**不属本契约**） |

文本形态（未给 `--json`）是摘要，不是证据全文转写：超长推理会截断，并提示改用 `--json` 或直接读那份证据文件；需要完整证据时使用 `--json`。`--all` / `--full` 的语义见 `gherkai explain --help`。

## `gherkai list-engines --json`

数组，每引擎一项：

| 键 | 含义 |
|---|---|
| `engine` | `novaact` / `midscene` |
| `available` | 本机能否启动该引擎的 worker |
| `cmd` / `cwd` | 启动命令（数组）与工作目录（多为 null）；不可用时为 null |
| `source` | 命中 worker 查找顺序的哪一级（`env …` / `同 venv 模块 …` / `PATH 可执行 …` / `uvx 兜底拉起 …`）；不可用时为 null |
| `hint` | 不可用时的安装指引；可用时 null |

## `gherkai list-deterministic --engine <名> --json`

顶层 `engine` + `deterministic_steps[]`，每项 `pattern`（正则，命中即按确定性 step 执行）、`description` / `example`（测试开发登记的说明与示例；
写 `.feature` 时以 `example` 的表述为准）、`keywords[]`（这条 step 接受的 Gherkin 关键字，缺省为 Given、When、Then 全部）、`targets[]`（worker 原样报出的该 step 有实现的目标：每项 `device`、`ui_kinds[]`，可带 `requires[]`）与 `available_targets[]`（由本工具与该引擎支持的目标求交后的结果，形状相同；声明了但该引擎不支持的目标不在其中）。

## `gherkai doctor --json`

顶层 `ok`（全部 `required` 项通过，也是退出码 0/2 的依据）+ `checks[]`，每项：

| 键 | 含义 |
|---|---|
| `section` | `cli` / `config` / `engines` / `steps` / `aws` / `backend` / `provider` |
| `name` | 项名：`cli`：`version`；`config`：`file`（本次加载的项目配置文件 gherkai.toml 的绝对路径，或「未使用配置文件」；纯展示，required=false）；`engines`：`novaact` / `midscene` / `any` / `model.<engine>`（本机该引擎 worker 自报的模型 id（云端 job 使用镜像内的模型），仅自述成功时出现）/ `targets.<engine>`（该引擎 worker 支持的测试目标清单，带会话上限的目标附分钟数；纯展示，required=false）；`steps`：`dir` / `load.<engine>`；`aws`：`region` / `identity`；`backend`：`version` / `resources` / `worker.default` / `worker.<engine>` / `worker.any` / `worker.grace`（本机 worker 自报的收尾宽限与云端 `stopTimeout` 的对比，缺口 ok=false/required=false）/ `reachability`（云端未查时的占位，恒为未查）/ `devices.project`（设备支持是否已部署：部署时建立的 Device Farm 项目 ARN 是否记在 SSM 中，记着时 detail 给出项目 ARN；未部署、读 SSM 失败均为 ok=false/required=false）/ `devices.sessions`（读到项目 ARN 才出现：该项目里未到 COMPLETED 的远程访问会话，含排队中的；detail 给出会话数，以及每个会话的 ARN、状态（服务返回名称与创建时间时一并给出）、控制台链接与停止命令；没有会话 ok=true，有残留或列举失败（含无权限）ok=false/required=false）；`provider`：`deploy-aws`（provider 不可用时的占位：未安装，或装了多个部署 provider 而未指名时为未查；已安装但加载失败时 ok=false、required=true）、provider 自报的 `node` / `cdk` / `container-engine`，或 provider 自身的 `name`（provider 未提供自检时以它作项名、为未查；自检抛错时同样以它作项名、ok=false） |
| `ok` | 这一行没有报告问题；查过且通过要同时看 `skipped` 为 false。false 专指这一行自己报告了问题 |
| `required` | true 表示必修项，没通过时退出码为 2；false 表示可选项，没通过只表示可选能力缺失（另一个引擎未安装、部署工具链缺项），不影响退出码。未查的行恒为 false |
| `skipped` | bool，恒有：true 表示这一行没有执行检查，原因在 `detail`，这时 `ok` 恒为 true、`required` 恒为 false；其余行为 false |
| `detail` | 一句说明：通过时给事实（命令、版本、ARN），失败时给处置办法，未查时给没有检查的原因 |

未查的行：未给 `--backend cloud` / `--prefix` 时的 `aws.identity` 与 `backend.reachability`；给了云端参数而 region 或凭证先失败时的 `backend.reachability`（失败本身由其上的 `aws` 段必修项报出）；没有可比对的引擎时的 `backend.worker.grace`（没有解析到镜像的引擎，或解析到的引擎本机都没有 worker；比了一部分时按已比的部分给结果、`skipped` 为 false，跳过的引擎写在 `detail`）；`provider` 段的占位行在未安装部署 provider、装了多个而未指名、或装上的 provider 不提供自检时。整体能否运行看顶层 `ok` 与退出码，只取决于必修项；某一行查过且通过是 `skipped` 为 false 且 `ok` 为 true；按 `required` 为 true 且 `ok` 为 false 挑阻塞项，不必另看 `skipped`。

## `gherkai deploy list-workers --json`

| 键 | 含义 |
|---|---|
| `prefix` / `version` | 后端前缀；「当前版本」指本 CLI 版本（镜像 tag 命名空间） |
| `default_variant` | 默认 variant 名；未初始化为 null |
| `engines` | 按引擎名分组的对象，每个引擎一项（下面各行是它的子键） |
| `engines.<engine>.family` / `ecr_repo` | task-def family 与 ECR 仓库名 |
| `engines.<engine>.variants[]` | `variant`、`tag`（`<版本>-<variant>`）、`digest`、`pushed_at`、`revision_arn`、`template_arn` |
| `engines.<engine>.pending_cleanup[]` | 待清理 revision：`revision_arn`、`reason`（`retired` / `orphan`）、`variant`、`retired_at`、`registered_at`、`still_mapped`（布尔，每条都带：该 revision 是否仍被某个版本的映射引用；为 `true` 时清理不会删它，为 `false` 不表示下次清理就删，退休满静默期、没有未到终态的 run 引用两个条件照样要满足；孤儿恒为 `false`） |
