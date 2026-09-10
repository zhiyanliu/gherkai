# 0041. 面向 AI agent 驾驭的 CLI 能力：scenario 筛选、静默落盘、JSON 全覆盖、doctor 自检、JSON 契约

> **Status:** Accepted（2026-09-10）—— 五项均已实装并有护栏；agent skill（另立）以本 ADR 的命令面为教学对象。

## 背景与问题

gherkai 的直接操作者越来越多是 AI coding agent（Claude Code / Codex 这类），替人写 `.feature`、跑、读结果、改确定性 step。agent 的工作循环与人不同：每一轮都要把命令输出读进上下文，每一次真跑都花几分钟与真金白银的 AI 费用，且它只能靠机读输出与退出码分流、不会「看一眼」HTML。对照 [0039](./0039-user-facing-surfaces-no-internal-references.md)（产品面文案）、[0036](./0036-deterministic-capability-discovery.md)（worker 自述）与 [0037](./0037-distribution-and-packaging.md) 决策 3（定位链）已经给出的底子（退出码 0/1/2 边界清楚、错误带「怎么办」、`plan` 零费用预检、`run/plan/status/list-deterministic` 有 `--json`、stdout 只放数据），复盘一轮真实 agent 使用后仍有五个洞，全部落在「迭代循环成本」与「机读完备性」两条线上：

1. 只能整文件跑：改一句断言想验证，`.feature` 里全部 scenario 重跑一遍——最贵的一格。
2. `--quiet` 只静音 core 的逐事件进度，worker 的 stdout/stderr（SDK 的 think/act 噪声，每步数百字符）无条件透传，agent 的上下文被灌满。
3. JSON 覆盖有洞：`list-engines` / `deploy list-workers` 只有文本；`status --json` 没有产物位置。
4. 没有一条自检：「凭证/region、两个引擎、`steps/` 能否加载、后端可达、版本 skew」散在四处，agent 要试错才知道环境缺什么。
5. `--json` 的字段没有契约文档，agent 靠猜字段名，写进 skill 又必漂移。

## 决策

### 一、scenario 筛选：`--tags` / `--scenario`，run / plan / submit 三命令同形

- 两个可重复 flag，都在 **parse 之后、scope 分组之前**筛（core `plan(features, config, select=…)` 收一个 `ParsedScenario → bool` 谓词，筛掉的 scenario 不进任何 job）。三个命令同一套解析（`_load_and_plan`），definition 即筛后的 job 集——`submit` 落库的就是它，`plan` 标注的也是它。
- **`--tags TAG[,TAG…]`**：一个值内逗号分隔为**或**（任一命中）；flag 重复为**且**；`@` 可带可不带。tag 集 = gherkin 已合并的 feature 级 + scenario 级。
- **`--scenario SEL`**：可重复、彼此为**或**。`SEL` 三种写法按序试：等于 scenario id（`<uri>:<行>`）；纯数字或 `:数字` = 行号；否则按 scenario 标题**子串**匹配（大小写敏感）。`--tags` 与 `--scenario` 同给为**且**。
- **筛后为空 → 退 2**，并列出本批全部 scenario（`id  标题  tags`）供改参数——不静默跑空批。筛掉了 scenario 时在 stderr 打一行「筛选：N/M」。
- **有意的语义代价**：named scope（`@scope:X`）里只选其中几个 scenario，会话仍按 scope 建，只是少跑几条——这是迭代用法，不是回归用法；scope 内 scenario 若互相依赖，筛掉前置即可能失败，由使用者判断。
- 被拒：cucumber 风格 tag 表达式（`@a and not @b`）——多一门小语言，agent 与人都得学；两个 flag 的且/或已覆盖迭代场景。行号范围、glob 同理不做。

### 二、`--quiet` 把 worker 日志落盘

- `run --quiet`（local 执行档）：worker 的 stdout/stderr 透传改写到 **`<report_dir>/<run_id>/worker.log`**（`--no-report` 时落系统临时目录 `gherkai-worker-<run_id>.log`），结束时只打一行位置；`--json` 的 `artifacts` 加 `worker_log`。默认档（不 quiet）行为不变——人看流水仍是最快的排障方式。
- 机制：`SubprocessEngine(log_sink=…)` 注入一个文件句柄，`_pump_log` 有 sink 则写 sink（无颜色码）、无 sink 则照旧写 stderr；组合根（`compose.build_engines(worker_log=…)`）只转发。cloud 执行档 worker 日志在 CloudWatch，本条不涉及；`submit` 的 local per-run 进程本就落 `reconcile.log`，不变。
- 被拒：另开 `--worker-logs off|file` 旋钮——「少进上下文」是同一个意图，两个旋钮让 agent 多记一条；env 开关——不可见、难发现。

### 三、JSON 全覆盖：每条命令都有机读形态

- `list-engines --json`：每引擎 `{engine, available, cmd, cwd, source, hint}`。
- `deploy list-workers --json`：`{prefix, version, default_variant, engines: {<engine>: {family, ecr_repo, variants: […], pending_cleanup: […]}}}`。
- `status --json`：在 RunState 之外**附加** `artifacts`（与 `run --json` 同键：`run_meta` / `run_state` / `jobs_dir` / `report_index`），位置由 compose 单点拼、始终给出（是否已写成看 status 是否终态）。RunState 部分形状不变（加法兼容）。
- 原则：stdout 只放数据、诊断走 stderr、`--json` 下不打人读提示（沿用既有）。

### 四、`doctor`：一个入口、按组件分组

- `gherkai doctor [--backend cloud --prefix P] [--steps-dir DIR] [--json]`：**只读**自检，按组件分组输出，每项 `ok/fail + 一句诊断（怎么办）`；全 ok 退 0，任一 fail 退 2（agent 可直接分流）。
- 组件与归属（**按 extra 实施、单入口汇总**——自检能力跟着它检查的组件走，入口只做编排）：
  - `cli`：版本、Python。
  - `engines`：两引擎的定位链结果（同 `list-engines`）。
  - `steps`：解析到的 `steps/` 目录；对每个可用引擎跑一次 worker 自述（`--list-deterministic`），加载失败原样转述。
  - `aws`（给了 `--backend cloud` 或 `--prefix` 才查）：region 解析、凭证身份（STS）。
  - `backend`（同上）：版本戳与 skew 三态、资源 preflight（表/桶/cluster/三 Lambda——复用 submit 的 `preflight_cloud_resources`）、默认 worker variant 能否解析到各引擎 revision。
  - `provider`：装了 `[deploy-aws]` extra 时，经既有 provider 接缝（[0037](./0037-distribution-and-packaging.md) 决策 6）调它可选的 `doctor(args) -> dict`：Node ≥ 22、cdk 可定位、容器引擎可用；没装则一行说明「部署方才需要」。
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
