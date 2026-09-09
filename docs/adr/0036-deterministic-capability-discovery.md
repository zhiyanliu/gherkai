# 0036. 确定性能力暴露：worker 自述注册表，CLI 按引擎查询

> **Status:** Accepted —— 清单查询（`list-deterministic`）与 plan 命中标注均已实现。

## 背景与问题

确定性 step 由 test engineer 在 **worker 侧注册表**维护（[0022](./0022-bdd-runner-retired-core-parses-thin-worker.md)：`(模式 → handler)`，TS/Python 两份、模式对称），feature 作者写自然语言、默认走 AI（[0020](./0020-step-phrasing-default-ai-deterministic-scaffold.md)）。信息不对称由此而生：**写 feature 的人无从得知当前引擎支持哪些确定性能力**——哪些措辞会命中精确 handler（确定性、免投票、省钱），哪些落到 AI。此前唯一的"可发现性"是脚手架文件里的代码注释，消费者只能是读代码的人。

**与 [0020](./0020-step-phrasing-default-ai-deterministic-scaffold.md)「QA 零预设」的关系（澄清而非反转）**：零预设说的是「QA **不必学**任何措辞也能写 feature」（AI 兜底），本 ADR 加的是「QA **可以查**当前有什么确定性能力可复用」——可选的查询面不构成预设，默认 AI 的哲学不变。

## 决策

### 1. 注册面扩元数据（暴露的前提）

注册一条确定性 step 时**必须**带人话元数据（裸正则对 feature 作者不可读）：

- `description`：这步做什么（一句话）；
- `example`：feature 里怎么写（可直接抄的 step 文本示例）。

TS `deterministic(pattern, handler, { description, example })` / Python `@deterministic(pattern, description=…, example=…)`——两侧 API 形态各随语言习惯、字段对称（[0022](./0022-bdd-runner-retired-core-parses-thin-worker.md) 对称要求延伸到元数据）。

### 2. worker 自述：`--list-deterministic` dump 模式

worker argv 带 `--list-deterministic` 时：**不建会话、不读 stdin、零费用**，把注册表（pattern 原始串 + description + example）dump 成 JSON 数组到 stdout、退出 0。

- **真值单一**：清单直接从注册表代码生成，engine 侧加/改锚点，查询结果即时跟随——零第二事实源。
- **跨语言被既有架构吸收**：TS/Python 注册表无法被 CLI（Python）直接 import，「spawn 子进程 + 结构化输出」正是本项目 worker 交互的既有形态（[0024](./0024-worker-core-protocol.md)）；dump 模式是 worker 的第二个入口形态（第一个是跑 job），不触碰 job 协议本身。
- 与 [0022](./0022-bdd-runner-retired-core-parses-thin-worker.md)「设计要点」节「匹配放 worker，不放核心」条（核心对 step 语义无知）的红线相容：core/CLI 仍不持有、不解释 pattern——只是转述 worker 的自述。

### 3. CLI 子命令 `list-deterministic --engine <name>`

- **按引擎查询**（对齐 `run` 的引擎选择逻辑）：`--engine` 默认 `novaact`（与 `--default-engine` 缺省一致）、choices 来自引擎注册表——只返回指定引擎的清单，不做全量聚合。
- `--json` 输出机器可读（stdout 只放核心产出，对齐既有输出契约）；文本模式渲染 description/example/pattern。
- 纯本地 spawn（秒级）、零 AWS；worker 起不来/输出非 JSON → 退 2 带诊断。

### 4. plan 命中标注：「我写的这句会不会命中」

清单查询解决「有什么可用」；feature 作者还需要「**我写的这句会不会命中**」——`plan` 预检对每个 step 标注路由预期。**不做 CLI 侧复刻匹配**（TS/Python 正则方言不同：`(?<n>)` vs `(?P<n>)`；复刻匹配语义 = 对 [0022](./0022-bdd-runner-retired-core-parses-thin-worker.md)「设计要点」节「匹配放 worker，不放核心」条的漂移面），机制 = **worker 批量 match 查询**：

- worker 第三入口 `--match-steps`：stdin 收 step 文本 JSON 数组，对每条用**同一注册表、同一 search 实现**回答 `null`（走 AI）/ `{pattern, description}`（命中）/ `{conflict:[patterns]}`（命中多条），stdout 一行 JSON 即退——匹配语义 100% 留在 worker。match 用**裸 step 文本**，与真跑派发的匹配面完全一致（不 unquote、不拼 argument，[0024](./0024-worker-core-protocol.md)）。
- plan 按引擎分组 step、每引擎至多 spawn 一次；文本视图行尾标 `← 确定性: <description>`（AI 不标——噪声控制）、`--json` 给每 step 注 `deterministic` 键（plan 视图字段、非 definition）。
- **标注默认开 + best-effort 按引擎降级**：引擎环境未装/查询失败只让该引擎的 job 无标注（stderr 警告），plan 核心功能保持零依赖不受影响。plan 的承诺从「不起 worker」校准为「零 AWS、零花费、零副作用」——本地瞬时 worker 子进程（自述模式）不违本质。
- **冲突预检是附加价值**：命中多条模式在真跑时该 step 会 error（[0022](./0022-bdd-runner-retired-core-parses-thin-worker.md)），plan 提前以 ⚠ 标注 + stderr 警告暴露；**退出码仍 0**——注册表冲突是工程侧资产问题（feature 作者改措辞可避开、但无权修注册表），不该挡 feature 作者的 plan（与 PlanError=definition 层矛盾退 2 分层）。

## 被拒方案（护栏）

- **外置清单文件**（engine 侧维护 YAML/JSON、CLI 直接读）——双事实源：代码里的 pattern 与清单必然漂移（本项目文档纪律反复打击的形态）；且违 [0022](./0022-bdd-runner-retired-core-parses-thin-worker.md)「设计要点」节「匹配放 worker，不放核心」条（清单文件若被 CLI 用于匹配即"核心懂 step 语义"）。
- **run 时在协议事件上标记确定性命中**——[0024](./0024-worker-core-protocol.md) 已主动删除 step 的 `kind` 字段（派发细节 core 不消费），为查询反转该收窄不值；且"跑后知道"不解决"写前不知道"。
- **全量（多引擎聚合）清单**——查询语义按引擎（QA 的 scope 用哪个引擎查哪个）；两引擎对称性审计不为此保留全量模式（查两次 diff 即可）。

## 边界与互链

- **与 [0027](./0027-runreport-aggregation-index.md)「确定性 step 产物可观测性」口子的区分**：那是「跑完之后看见做了什么」（run 产物层），本 ADR 是「跑之前知道有什么/会命中什么」（definition 前的查询层）——同源（确定性对外不透明）不同事，各自演进。
- 元数据是注册契约的一部分：缺 description/example 的注册应 fail-loud（防"能力存在但不可发现"回潮）。
