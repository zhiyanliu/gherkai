# docs/internals 索引

这一层解释系统如何运转：每篇把散在多份 ADR 里的一个机制拼成完整的一张，只讲怎么运转、不复述为什么这样设计；权威始终在 ADR 与代码，正文带指针。写作与审计判据见 [CLAUDE.md](../../CLAUDE.md)「文档纪律」`docs/internals/` 条。**一个机制只有一篇是 owner**，其余篇只给链接——本表同时是「主题归属表」，新增一篇时在此登记、并让相关篇的延伸阅读指过来。

| 篇 | 回答什么问题 | 拥有的主题（别处只链不讲） |
|---|---|---|
| [`architecture-overview.md`](./architecture-overview.md) | 系统由哪些部件拼成、五层各自负责什么、一次 run 依次经过谁、发行物有哪几个 | 全景架构图、五层职责与各自的「不负责」、一次 run 的生命周期主干（各步细节归下面各篇）（各阶段细节归下面各篇）、本机与云端两档的载体对照总表、包与发行物对应表 |
| [`execution-and-reconciliation.md`](./execution-and-reconciliation.md) | run / submit × local / cloud 四种跑法下，谁在推进、事件怎么流、超时怎么兜、云端为何不抢前台 | 推进链（同步 `schedule`，以及四处调用 `reconcile.tick` 的进程与 Lambda）、三 Lambda 事件级联、事件流四条物理通道与键空间、退出观察者、job 超时三路 enforce、投影与提交点的时序、读侧的落地时机、诊断落哪 |
| [`verdict-model.md`](./verdict-model.md) | 一票怎么变成 step / scenario / job / run 的判定；七个状态各是什么、我该做什么；各命令退出码分别在回答什么 | 四层归约、status 与 shortcircuited 两根轴、error_type 家族、severity 数值序、`TERMINAL_STATUSES` / `_NON_VERDICT` 两把刀、退出码按命令分工 |
| [`artifacts-and-evidence.md`](./artifacts-and-evidence.md) | 跑完了东西在哪、哪一份答哪个问题；证据链怎么串；失败先看哪 | local × cloud 产物地理、五类产物（definition / 运行态 / 判定真值 / 派生导航 / 现场证据）的分工、`kind=evidence` 与 explain 的解引用边界、失败阅读三步、诚实空缺与边角 |
| [`deterministic-step-lifecycle.md`](./deterministic-step-lifecycle.md) | 一条确定性 step 从写下到云端命中经过谁；为什么本机与云端真源不同；哪些情形响亮失败 | worker 侧注册表与派发决策链、worker 的两个非 job 入口（能力自述 `--capabilities`、match 查询 `--match-steps`）、steps 目录解析与 variant 镜像的分叉、响亮失败表、两引擎对称面 |
| [`cloud-backend-carriers.md`](./cloud-backend-carriers.md) | 云端后端由哪几个载体拼成；一次改动要推到哪几处才生效；症状怎么反查载体 | stack / Lambda asset / 基底镜像 / variant 镜像 / SSM 五种载体、版本升级传播顺序、症状→载体反查、提交侧 revision 解析与退休规则、prefix 隔离 |
| [`cli-json-contract.md`](./cli-json-contract.md) | `--json` 各命令有什么字段、什么意思、何时出现 | 全部机读字段的名、类型、出现条件（唯一字段级参考，有护栏钉着；其它篇只链不列） |

**图统一用 archify**，图源与静态图在仓库级的 [`docs/diagrams/`](../diagrams/)：`<name>.json`（图源，改图改它）+ `<name>.svg`（正文以图片形式嵌入的同名导出）同 commit；可交互 HTML 只对发布到 Pages 的两张大图入库，其余只是 `tools/build_diagrams.mjs` 导出 SVG 的中间物；站点 https://zhiyanliu.github.io/gherkai/ 由 [`.github/workflows/pages.yml`](../../.github/workflows/pages.yml) 原样上传该目录。形态与门槛见 [ADR 0045](../adr/0045-documentation-layering-and-placement.md) 决策七。

不在这一层的东西：使用者的操作与流程在 [`docs/user-guide/`](../user-guide/)（各包 `README.md` 只是入口页），contributor 的目录/测试/发布链在根 [`CONTRIBUTING.md`](../../CONTRIBUTING.md) 与各包 `DEVELOPMENT.md`，决策与理由在 [`docs/adr/`](../adr/)，术语在 [`CONTEXT.md`](../../CONTEXT.md)，驾驭本工具的 AI agent 用随 CLI 发行的 skill（`cli/gherkai_cli/skills/gherkai/`，`gherkai skill install` 装进项目；它的机读字段页是本目录 [`cli-json-contract.md`](./cli-json-contract.md) 的确定性转换副本，为何不 link、如何转换见 [ADR 0043](../adr/0043-agent-skill-for-driving-gherkai.md)）。
