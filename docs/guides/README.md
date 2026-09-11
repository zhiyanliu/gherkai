# docs/guides 索引

给**人**读的横切导览层：只讲机制如何协同（how），权威永远在 ADR 与 code，每篇正文带指针；写作与审计判据见 [CLAUDE.md](../../CLAUDE.md)「文档纪律」guides 条。**一个机制只有一篇是 owner**，其余篇只给链接——本表同时是「主题归属表」，新增 guide 时在此登记、并让相关篇的延伸阅读指过来。

| 篇 | 回答什么问题 | 拥有的主题（别处只链不讲） |
|---|---|---|
| [`execution-and-reconciliation.md`](./execution-and-reconciliation.md) | run / submit × local / cloud 四种跑法下，谁在推进、事件怎么流、超时怎么兜、云端为何不抢前台 | 推进链（同步 `schedule` / 四个 `tick` 宿主）、三 Lambda 事件级联、事件流四条物理通道与键空间、退出观察者、job 超时三路 enforce、投影与提交点的时序、读侧的落地时机、诊断落哪 |
| [`verdict-model.md`](./verdict-model.md) | 一票怎么变成 step / scenario / job / run 的判定；七个状态各是什么、我该做什么；各命令退出码分别在回答什么 | 四层归约、status 与 shortcircuited 两根轴、error_type 家族、severity 数值序、`TERMINAL_STATUSES` / `_NON_VERDICT` 两把刀、退出码按命令分工 |
| [`artifacts-and-evidence.md`](./artifacts-and-evidence.md) | 跑完了东西在哪、哪一份答哪个问题；证据链怎么串；失败先看哪 | local × cloud 产物地理、五类产物（definition / 运行态 / 判定真值 / 派生导航 / 现场证据）的分工、`kind=evidence` 与 explain 的解引用边界、失败阅读三步、诚实空缺与边角 |
| [`deterministic-step-lifecycle.md`](./deterministic-step-lifecycle.md) | 一条确定性 step 从写下到云端命中经过谁；为什么本机与云端真源不同；哪些情形响亮失败 | worker 侧注册表与派发决策链、两个自述入口（`--list-deterministic` / `--match-steps`）、steps 目录解析与 variant 镜像的分叉、响亮失败表、两引擎对称面 |
| [`cloud-backend-carriers.md`](./cloud-backend-carriers.md) | 云端后端由哪几个载体拼成；一次改动要推到哪几处才生效；症状怎么反查载体 | stack / Lambda asset / 基底镜像 / variant 镜像 / SSM 五种载体、版本升级传播顺序、症状→载体反查、提交侧 revision 解析与退休规则、prefix 隔离 |
| [`cli-json-contract.md`](./cli-json-contract.md) | `--json` 各命令有什么字段、什么意思、何时出现 | 全部机读字段的名、类型、出现条件（唯一字段级参考，有护栏钉着；其它篇只链不列） |

不在这一层的东西：使用者操作手册在各包 `README.md`，contributor 的目录/测试/发布链在各 `DEVELOPMENT.md`，决策与理由在 [`docs/adr/`](../adr/)，术语在 [`CONTEXT.md`](../../CONTEXT.md)，驾驭本工具的 AI agent 用 skill（另立）。
