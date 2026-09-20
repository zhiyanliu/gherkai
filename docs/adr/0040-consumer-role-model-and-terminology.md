# 0040. 使用方角色模型与术语

> **Status:** Accepted（2026-09-09；2026-09-18 增决策 6「两侧 AI agent 是执行者、不立新帽子」）—— 术语面已落（全仓「test engineer」统一为「测试开发」）；派生视图在 `docs/user-guide/getting-started.md`「按角色选安装形态」表与 `CONTEXT.md`「角色与权限」节词条组，改这里再改那里。

## 背景与问题

角色早已是多处设计的键，却没有单一真源：

- **安装**按角色切：裸 `gherkai` 给只提交的人、`[local]` 给本机跑 worker 的人、`[deploy-aws]` 给改云端环境的人（[0037](./0037-distribution-and-packaging.md) 决策 2/5/6）。
- **权限**按主体登记：[0033](./0033-iac-aws-backend-and-composition-wiring.md)「资源清单」末段分编排进程 / detached 提交 / 部署方 / 提交者；[0038](./0038-worker-image-delivery.md)「权限面增量」分部署方 / 提交者 / 云端推进器。
- **所有权**按角色分：镜像构建归写 step 的人、推送与注册归部署方（0038）；`steps/` 归使用方项目（0037 决策 4）；QA 永不碰 steps（[0020](./0020-step-phrasing-default-ai-deterministic-scaffold.md)）。
- **文档分层**按读者分：[0039](./0039-user-facing-surfaces-no-internal-references.md) 的「使用者向 / contributor 向」二分，已被 [0045](./0045-documentation-layering-and-placement.md) 决策一的读者三分类取代（contributor 侧 AI agent / 技术文档 / 用户文档）。
- **执行**按执行方式分级：0033 登记的权限随执行方式与执行后端而异——detached `submit` / `status` 只要 runs 表读写 + 只读探活 + `lambda:GetFunction` / `InvokeFunction`；同步 `run --backend cloud` 是另一套（ECS 起停 task + `iam:PassRole` + runs 表写，不含那两个 lambda 动作）；local 用本机凭证；`plan` 不需要凭证。

漂移已经发生：同一顶「会写代码的测试角色」在文档与注释里有三个名字（test engineer 28 处 / developer / 测试开发 3 处）；写 `.feature` 的角色也有两个（QA 57 处 / feature 作者 15 处）。README 三处按角色说话（首段、安装块注释、feature 写法节）却从未定义角色，读者要先猜自己是谁才知道装哪行、哪些命令是自己的。

本地开发时同一个人常在写被测应用代码与对应的 step 代码之间切换，build 完自己推——**角色重合是常态、不是例外**。

把「用 plan / run / submit / status」这类执行动作写进某顶帽子的定义，等于把执行权限挂在帽子上；而「跑」是每顶帽子都做、CI 机器也做的事，且两种执行方式（`run` / `submit`）权限不同——故执行单独成轴（决策 3）。

## 决策 1：四顶帽子与正名

| 帽子 | 正名 | 同义 / 弃用 | 一句话 |
|---|---|---|---|
| 写 `.feature` | **feature 作者** | 同义 **QA**（「QA 零代码」口号与既有文档保留，含义等同） | 只写自然语言、零代码；产物 = `.feature`，验证用 `plan`（不需要凭证）。要执行，按决策 3 的执行权限梯级取一级 |
| 写确定性 step | **测试开发** | 弃用 test engineer / test-engineer；「developer」只在指「被测应用的开发者」时用 | 使用方项目 `steps/`（两引擎各一份、模式对称）；本机 local 验证；build 定制 worker 镜像 |
| 改云端环境 | **部署方** | — | `gherkai deploy` / `gherkai deploy push-worker`；唯一因帽子本身就需要云端写权限的帽子（执行所需权限按决策 3 另算） |
| 开发 gherkai 本身 | **contributor** | 「发布方」专指发布 / GHCR 基础镜像的一方 | clone 仓库、读根 `CONTRIBUTING.md` |

**「使用方」= 前三顶的统称**（用 gherkai 做测试的团队），与 contributor 相对——0039 的「使用者向 / contributor 向」即此分界。**「提交者」不是帽子，是权限类别**：决策 3 的执行权限梯级里两级云端组合的权限持有者（人或机器身份都行），0033 / 0038 的权限登记用它。

## 决策 2：帽子不是人

默认画像 = 一人多帽的本地开发循环：写被测应用 ↔ 写 step ↔ local 跑 ↔ build 完自己推。0038「默认画像 = 一人兼测试开发与部署方两顶帽子」是它的一个实例。由此两条设计约束：

- **合帽零摩擦**：一个人戴全时不需要在角色间「切换身份」——同一台机器、同一套凭证、同一条命令链（`run` → `push-worker` → `submit`）走得通。
- **拆帽有现成边界**：团队分工时权限 / 安装 / 产物按帽子切开即可、不需要新设计。所以 extras 与权限登记必须按帽子切（已是）；新增功能在设计时要说清落在哪顶帽子上。

## 决策 3：执行是正交轴——执行权限梯级

「产出什么」由帽子回答，「怎么跑」是另一根轴：执行方式（`run` / `submit`）× 执行后端（`--backend local` / `cloud`）两个独立的选择（使用者视图见 `docs/user-guide/running-and-results.md`）。权限挂在这根轴上、不挂在帽子上，因为跑是每顶帽子都做的事，机器身份也做。按 0033 的登记分四级，下表大体从轻到重排——但**各级不构成逐级累加的阶梯**（两级云端所需权限互不包含，本机组合要的又是另一套凭证）：

| 组合（执行方式 × 执行后端） | 需要什么（登记处 = 0033「资源清单」末段） | 费用记到 |
|---|---|---|
| `plan` | 无凭证；装了 worker 才有确定性 step 标注（[0036](./0036-deterministic-capability-discovery.md) 决策 4 的 best-effort） | 无 |
| `run` / `submit` `--backend local` | 本机 AWS 凭证（Bedrock 模型 / AgentCore Browser / Nova Act 服务）+ 两个 worker | 自己 |
| `submit` / `status --wait` `--backend cloud` | 最小云端权限：runs 表读写 + 只读探活 + `lambda:GetFunction` / `InvokeFunction` + variant 解析只读（0038）+ 报告桶 `s3:PutObject`（feature 含 DataTable / DocString 时，提交即把正文搬 S3，[0030](./0030-realtime-persistence-seam.md) 决定六）；**无任何 ECS 写**——起 task 全走 Lambda 执行角色 | 部署方 |
| `run --backend cloud`（同步） | 另一套云端权限（**不含**上一级的 `lambda:GetFunction` / `InvokeFunction`）：`ecs:RunTask` / `StopTask` / `DescribeTasks` + `iam:PassRole` + `dynamodb:Query` / `PutItem` + 报告桶 `s3:PutObject`（此级恒需：进程内起 task、自己上传 job、自己推进）+ 同一套只读探活 + variant 解析只读（0038） | 部署方 |

两条推论：**detached 提交不需要任何 ECS 写权限**（起 task 全走 Lambda 执行角色），CI 与低权限机器应走 `submit`——这是 [0034](./0034-detached-batch-reconciler.md)「最小权限」的角色化表述；**CI 不是帽子**，是「无帽子、持有一级执行权限的机器身份」。feature 作者的写作本身不需要任何凭证，「QA 零代码」因此更纯：零代码、零凭证即可写与 `plan`。

## 决策 4：边界矩阵

| 帽子 | 写什么 | 装什么（0037） | 权限面（登记处 = 0033「资源清单」末段） | 明确不做 |
|---|---|---|---|---|
| feature 作者 | `.feature` | `gherkai`；本机跑还要 `gherkai[local]` + `@gherkai/worker-midscene` | 写本身不需要凭证；执行按决策 3 的执行权限梯级取一级 | 不碰 `steps/`；不学任何关键词措辞 |
| 测试开发 | `steps/*.py` + `steps/*.mts`、定制 worker 镜像 | 同上 + 容器引擎（docker / podman） | 同 feature 作者；**不需要云端写权限**——镜像交给部署方推 | 不改 worker 包内脚手架（改它等于 fork，0037 决策 4） |
| 部署方 | 后端（CDK）、worker 镜像的推送与注册 | `gherkai[deploy-aws]` + Node ≥22 + 容器引擎 | 独有：CDK 部署本身 + VPC 三态比对读 + ECR 推送域 + ECS task-def 注册 / 退休 + `iam:PassRole` + SSM `/{prefix}backend/*` 读写 + runs 表 Query（含 `status-index`）；执行用例同样按决策 3 的执行权限梯级取一级 | 不拥有镜像构建（那是测试开发的容器工作）；不替提交侧决定并发，只留 cap（[0034](./0034-detached-batch-reconciler.md) 机制四） |
| contributor | 工具自身的代码、ADR、发布链 | clone + `uv sync` + `npm ci` | 发布走 CI trusted publishing，个人无需长期发布凭证（0037 决策 8） | 不把 contributor 内容写进使用者面（0039） |

## 决策 5：术语单一真源与立新角色的门槛

- 本 ADR 是角色名与边界的单一真源；`CONTEXT.md`「角色与权限」节的词条组与 `docs/user-guide/getting-started.md`「按角色选安装形态」表都是派生视图。
- **立新角色的门槛 = 有独立权限边界或独立产物**。「只提交不写 feature 的人」「只看结果的人」是 feature 作者的子集、不另立；「提交者」维持为权限类别，不升格为帽子。
- 长期文档与 code 注释用正名；产品面文案里的角色词按 0039 说人话（「部署方」「写 step 的人」可用，不出现帽子矩阵与决策号）。

## 决策 6：两侧 AI agent 是执行者，不立新帽子

- **AI agent（Claude Code、Codex 这类工具）在本项目里出现在两个位置，各是一个稳定角色名，按位置命名、不按活动命名**：**使用者侧 AI agent**——装了 gherkai skill（0043）、在使用方项目里替人操作 gherkai 的 agent；**contributor 侧 AI agent**——在本仓库里干活（写代码、写文档、复盘）的 agent，是 ADR / CONTEXT / CLAUDE.md 约 80% 的读者。
- **两者都不是第五顶帽子**：agent 替人戴帽子——使用者侧 agent 戴 feature 作者 / 测试开发 / 部署方，contributor 侧 agent 戴 contributor；帽子决定权限与产物，「人手敲还是 agent 代劳」属决策 3 那根正交的执行轴。判据同决策 5：它们没有独立权限边界或独立产物。
- **用词规则**：角色名里不带「coding」——使用者侧 agent 多半不写代码，「coding」把活动说窄了；提到工具品类时写「AI agent（如 Claude Code、Codex）」，首次出现带括注即可，之后只写「AI agent」。「建造者 AI」（0045 曾用）废止，统一为「contributor 侧 AI agent」。撞词提醒：gherkai 自己的两个 AI 引擎一律称「引擎 / worker / 模型」，「AI agent」专指上述工具。
- 用户文档（README / user-guide / skill）的读者就是使用者侧 AI agent 或它的主人，正文写「AI agent」即可；contributor 侧文档（ADR / CONTEXT / CLAUDE.md / ai-eng）区分两侧时用全名。

## 代价

- 多一篇要与 0033 / 0037 / 0038 同步的 ADR：新增 extras、权限或所有权变化时，矩阵是第四个要改的地方。接受——它就是为了让「改了那三处却漏了角色叙事」这类漂移有一个审计点。
- 模型成了两根轴（帽子 × 执行），多一个概念。接受——换来的是权限不再挂错地方：挂帽子上会把「人人都跑」错记成某顶帽子的属性。
- 「QA」与「feature 作者」在历史 ADR 里并存。接受——两者被定义为同义，不做几十处的机械替换。

## 被拒方案

- **只放 CONTEXT.md**：词条给得了定义，装不下 why、边界矩阵与「帽子不是人」这两条设计约束。
- **放 docs/internals/**：guide 只讲 how、不做决策（CLAUDE.md 文档纪律）；正名与门槛都是决策。
- **维持分散**：现状，已证明会漂（三名一义、两名一义、README 有角色无定义）。
- **立「执行方」第五顶帽子**：能给 CI 一个名字，但另外三顶帽子在实际里永远与它同戴、机器也戴——人人都戴的帽子给不出可验证的边界。执行改为正交轴（决策 3）后 CI 自然有位置。
- **按岗位设 persona 而非按帽子**：岗位头衔在团队间不可比（同一头衔两家公司职责不同）；帽子按产物 / 权限切、可验证。

## 影响

- 用户文档（0045 决策一 / 二 归位后）：`getting-started.md`「按角色选安装形态」表承载帽子与安装形态，并以产品语言写「一个人可以同时承担多个角色」（隐喻「帽子不是人」按 0045 决策六不进使用者面）；`running-and-results.md`「两个独立的选择」节承载执行权限梯级表（决策 3 的派生视图，不带 ADR 编号），角色表的「需要什么凭证」列指向它。
- CONTEXT.md：加「角色与权限」节的词条组（使用方 vs contributor、四顶帽子、执行权限梯级、提交者），指向本 ADR。
- 0020「角色边界」节、0038「默认画像」句：加指向本 ADR 的指针；术语按决策 1。
