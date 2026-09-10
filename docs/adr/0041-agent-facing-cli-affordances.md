# 0041. 面向 AI agent 驾驭的 CLI 能力：scenario 筛选、静默落盘、JSON 覆盖补齐、doctor 自检、JSON 契约

> **Status:** Accepted（2026-09-10）—— 五项均已实装并有护栏；agent skill（另立）以本 ADR 的命令面为教学对象。

## 背景与问题

gherkai 的直接操作者越来越多是 AI coding agent（Claude Code / Codex 这类），替人写 `.feature`、跑、读结果、改确定性 step。agent 的工作循环与人不同：每一轮都要把命令输出读进上下文，每一次真跑都花几分钟与真金白银的 AI 费用，且它只能靠机读输出与退出码分流、不会「看一眼」HTML。对照 [0039](./0039-user-facing-surfaces-no-internal-references.md)（产品面文案）、[0036](./0036-deterministic-capability-discovery.md)（worker 自述）与 [0037](./0037-distribution-and-packaging.md) 决策 3（定位链）已经给出的底子（退出码 0/1/2 边界清楚、错误带「怎么办」、`plan` 零费用预检、`run/plan/status/list-deterministic` 有 `--json`、stdout 只放数据），复盘一轮真实 agent 使用后仍有五个洞，全部落在「迭代循环成本」与「机读完备性」两条线上：

1. 只能整文件跑：改一句断言想验证，`.feature` 里全部 scenario 重跑一遍——最贵的一格。
2. `--quiet` 只静音 core 的逐事件进度，worker 的 stdout/stderr（SDK 的 think/act 噪声，每步数百字符）无条件透传，agent 的上下文被灌满。
3. JSON 覆盖有洞：`list-engines` / `deploy list-workers` 只有文本；`status --json` 没有产物位置。
4. 没有一条自检：「凭证/region、两个引擎、`steps/` 能否加载、后端可达、版本 skew」散在四处，agent 要试错才知道环境缺什么。
5. `--json` 的字段没有契约文档，agent 靠猜字段名，写进 skill 又必漂移。

## 决策

### 一、scenario 筛选：`--scope` / `--tags` / `--scenario`，run / plan / submit 三命令同形

- 三个可重复 flag，都在 **scope 分组与 engine/timeout 解析之后、Job 组装之前**筛（core `plan(features, config, select=…)` 收一个 `(ParsedScenario, scope_id) → bool` 谓词（scope_id 一并传入，业务概念按分组键判、不从 tags 反推））。**不变量：筛选只减少「跑哪几条」**——scope 的引擎、墙钟预算、会话身份一律按全量成员解析，与不筛时逐字一致；否则筛后跑的与全量跑的不是同一件事，迭代结论不可迁移（曾在分组前筛：把带 `@engine:midscene @timeout:900` 的成员筛掉，剩下的成员静默跑在 novaact / 300s，对抗审查真跑复现）。整组被筛空的 scope 不进任何 job，且在解析 engine/timeout **之前**跳过——被筛掉的 scope 里的 tag 冲突不拦本次迭代；`_scope_key`（一个 scenario 多个 `@scope`）仍对全量成员 fail-fast。跨文件合并 warning 按**要跑的**成员算。三个命令同一套解析（`_load_and_plan`），definition 即筛后的 job 集——`submit` 落库的就是它，`plan` 标注的也是它。空值（`--tags ""`）退 2，不静默降级成跑全批。
- **`--scope ID`**：可重复、彼此为**或**；值 = 报告与 `--json` 里的 `scope_id`（`@scope:` 的名字，未标 scope 时是 `<uri>:<行>`），按分组键**精确**匹配。这是「重跑某个失败 job」的直接回路：agent 从 `jobs/*.json` 读到 `scope_id` 原样填回来。scope 是业务概念，在 Gherkin 里靠 tag 承载（[0019](./0019-feature-tags-scope-and-engine.md) 的取舍——Gherkin 没有别的 per-scenario 元数据位）；筛选面上不让使用者反推这层实现细节（`--tags scope:x` 仍可用，那是通用 tag 筛选顺带覆盖的）。
- **`--tags TAG[,TAG…]`**：一个值内逗号分隔为**或**（任一命中）；flag 重复为**且**；`@` 可带可不带。tag 集 = gherkin 已合并的 feature 级 + scenario 级。
- **`--scenario SEL`**：可重复、彼此为**或**。`SEL` 三种写法**按序试、互斥**：等于 scenario id（`<uri>:<声明行>[:<Examples 行>]`）；ASCII 纯数字或 `:数字` = 行号（只当行号、不回落标题匹配，否则 `--scenario 3` 会连带选中标题「重试3次」；Scenario Outline 给声明行 = 选中它全部 example，给数据行 = 只选那一条）；否则按 scenario 标题**子串**匹配（大小写敏感）。三个 flag 同给为**且**。
- **筛后为空 → 退 2**，并列出本批全部 scenario（`id  标题  tags`）供改参数——不静默跑空批。筛掉了 scenario 时在 stderr 打一行「筛选：N/M」。
- **有意的语义代价**：named scope（`@scope:X`）里只选其中几个 scenario，会话仍按 scope 建，只是少跑几条——这是迭代用法，不是回归用法；scope 内 scenario 若互相依赖，筛掉前置即可能失败，由使用者判断。
- 被拒：cucumber 风格 tag 表达式（`@a and not @b`）——多一门小语言，agent 与人都得学；两个 flag 的且/或已覆盖迭代场景。行号范围、glob 同理不做。

### 二、`--quiet` 把 worker 日志落盘

- `run --quiet`（local 执行档）：worker 的 stdout/stderr 透传改写到 **`<report_dir>/<run_id>/worker.log`**（`--no-report` 时落系统临时目录 `gherkai-worker-<run_id>.log`），结束时只打一行位置；`--json` 的 `artifacts` 加 `worker_log`。默认档（不 quiet）行为不变——人看流水仍是最快的排障方式。cloud 执行档 worker 在云端跑、日志在 CloudWatch，无此文件、`artifacts` 无此键；`submit` 的 local per-run 进程本就落 `reconcile.log`，不变。
- **真跑坐实**（跳板机本机 novaact run）：`--quiet` 下终端只多一行 `worker 日志: file://…/worker.log`、无 SDK 流水；worker.log 38 行、零 ANSI 颜色码；`--backend cloud --quiet` 不建该文件、无未定义变量。`status --json` 的 `artifacts` 两档都对（local 全 `file://`；cloud `s3://` 报告与判定明细 + `ddb://` 元信息），且同步 `run` 落的 run_state 确实没有 `high_water_mark`（与本 ADR 决策五的契约页所记一致）。`deploy list-workers --json` 的 stdout 可被严格解析，skew 提示走 stderr。
- 机制：`SubprocessEngine(log_sink=…)` 注入一个文件句柄，`_pump_log` 有 sink 则写 sink（无颜色码）、无 sink 则照旧写 stderr；组合根（`compose.build_engines(worker_log=…)`）只转发。**句柄生命周期**：CLI 在 schedule 返回后关句柄，而透传是两条 daemon 线程——为让日志尾部（多半是失败原因）落完再关，`stop()` 与事件迭代器结束（自然 EOF / 被放弃）两处都对 pump 线程做**有界** join（进程已退即 EOF；带超时是因为定位链第 4 级 uvx 是包装进程、孙进程可能仍持写端）；join 超时后残余的写入撞上已关句柄只静默停转发，不让 traceback 打到 stderr（那正是 `--quiet` 要挡的东西）。
- 被拒：另开 `--worker-logs off|file` 旋钮——「少进上下文」是同一个意图，两个旋钮让 agent 多记一条；env 开关——不可见、难发现。

### 三、JSON 覆盖补齐：查询类命令都有机读形态

边界：`submit` 的机读形态就是 stdout 那一个 `run_id`（进度/结果走 `status --json`）；`deploy` / `destroy` / `push-worker` 是变更类命令，机读面 = 退出码，只读查询面留给 `list-workers --json` 与 `doctor --json`。`--json` 下 stdout 只有一个 JSON 文档，诊断（含 skew 提示、读失败）一律走 stderr；退出码非 0 的前置/读取失败路径 stdout 可为空，按退出码分流。

- `list-engines --json`：每引擎 `{engine, available, cmd, cwd, source, hint}`。
- `deploy list-workers --json`：`{prefix, version, default_variant, engines: {<engine>: {family, ecr_repo, variants: […], pending_cleanup: […]}}}`。
- `status --json`：在 RunState 之外**附加** `artifacts`（与 `run --json` 同键：`run_meta` / `run_state` / `jobs_dir` / `report_index`），位置由 compose 单点拼、始终给出（是否已写成看 status 是否终态）。RunState 部分形状不变（加法兼容）。
- 原则：stdout 只放数据、诊断走 stderr、`--json` 下不打人读提示（沿用既有）。

### 四、`doctor`：一个入口、按组件分组

- `gherkai doctor [--backend cloud --prefix P] [--steps-dir DIR] [--json]`：**只读**自检，按组件分组输出，每项 `{ok, required, 一句诊断（怎么办）}`。**退出码只看 `required` 项**：全过退 0，任一 `required` 项 fail 退 2（agent 可直接分流）；`required=false` 的项失败只作能力展示、不改退出码（另一个引擎没定位到、容器引擎 daemon 没起、未装 `[deploy-aws]` extra；未查的云端项标 ok + `required=false`）。人读形态 `✗` = 必修、`-` = 可选项未过。`required` 的判据 = **这次要跑的档真跑得起来吗**。字段与项名取值见 `docs/guides/cli-json-contract.md`（单一事实源，不在此复述）。
- 组件与归属（**按 extra 实施、单入口汇总**——自检能力跟着它检查的组件走，入口只做编排）：
  - `cli`：版本、Python。
  - `engines`：两引擎的定位链结果（同 `list-engines`），各自 `required=false`（缺一个不算故障）；聚合项「至少一个可用」为 required 闸门——两个都定位不到时 local 档一个 job 也起不来；`--backend cloud` 时该聚合项降为可选（只提交、不在本机跑的人不需要 worker）。
  - `steps`：解析到的 `steps/` 目录（显式给的目录不存在 = 必修失败，原因进 detail）；对每个可用引擎跑一次 worker 自述（`--list-deterministic`）——有 steps 目录时是使用方 step 能否加载（必修，加载失败会静默降级成 AI），没有时只验 worker 起得来（可选，单引擎不连坐）。
  - `aws`（给了 `--backend cloud` 或 `--prefix` 才查）：region 解析（解析不出即必修失败、云端其余项标未查）、凭证身份（STS；profile 名不存在等解析期错误与探针失败同一句诊断）。
  - `backend`（同上）：版本戳与 skew 三态、资源 preflight（表/桶/cluster/两引擎 task-def/三 Lambda——复用 submit 的 `preflight_cloud_resources`）、默认 worker variant：先读指针（缺失 = 必修失败），再**逐引擎**解析（各自可选——单引擎团队不必为另一个引擎推镜像，同 submit 只按用到的引擎判）+ 聚合「至少一个引擎可用」为必修。
  - `provider`：按 entry point 结构化判——没装 `[deploy-aws]` extra → 一行「部署方才需要」（可选）；装了多个未指名 → 未查（可选）；装了但加载失败 → 必修失败（明确装了的东西坏了）；装了且提供可选的 `doctor(args) -> list[dict]`（每项 `{name, ok, detail}` + 可选 `required`，缺省 False；只读、不返退出码，[0037](./0037-distribution-and-packaging.md) 决策 6 契约）→ 并入输出。AWS provider 报 Node ≥ 22、cdk 可定位、容器引擎可用，**三项都可选**：provider 段是部署能力清单，doctor 不知道这台机器要不要部署；真正的硬拦在 `gherkai deploy` 自身。人读尾行单独点出「部署工具链有缺口」。
- 被拒：另起 `gherkai-deploy doctor` 独立入口——agent 要记两条、且「后端可达」这类检查本就横跨两包；把自检做成 `plan` 的副作用——plan 要保持零费用、零网络。

### 五、JSON 字段契约文档 + 护栏

- 文档住 repo：`docs/guides/cli-json-contract.md`（给使用者/agent 的参考层，读者是「拿 `--json` 写脚本或 skill 的人」；不进发行包、不写 why）。skill 只链接它，不复制字段表——复制即第二事实源。
- **护栏 = 真值集对照**（CLAUDE.md 文档纪律）：`cli/tests/test_cli_json_contract.py` 用真渲染器生成各命令的 JSON 样例，递归收集全部键名，逐个断言文档里以反引号出现——文档漏键即红。
- 被拒：`gherkai schema <cmd>` 输出 JSON Schema——更机读，但要维护一套 schema 生成；先用文档 + 护栏，需求出现再升级（重议闸门）。

## 影响

- README（根 / cli）：新增 flag、`--quiet` 语义、`doctor`、`--json` 覆盖表；deploy_aws README：`list-workers --json`。
- 与 [0039](./0039-user-facing-surfaces-no-internal-references.md)：`doctor` 与筛选提示的文案同受产品面约束。
- agent skill（另立，不在本 ADR）：以本命令面为教学对象；skill 里的流程 = `doctor → plan（--tags/--scenario）→ run --quiet --json → 读 jobs/*.json → 改 → 重跑`。

## 重议闸门

- 失败证据的机读化（trajectory `.json` 引用 / `explain` 子命令）：本轮未做，agent 排障仍需人读 HTML 或按命名规则找 `_trajectory.json`；出现真实需求时立项。
- JSON Schema 生成：见决策五被拒项。
