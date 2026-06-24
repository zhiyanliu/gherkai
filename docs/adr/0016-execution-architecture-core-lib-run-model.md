# 执行架构：核心库（窄腰）+ Run 数据模型 + 留好状态存储的口子

界定 v0.x/v1.0 起、并向云端无缝演进的执行架构。本 ADR 是多轮形态讨论的总成，约束 lib 的设计，确保本地与云端、CLI 与 WebUI 不埋返工雷。

## 分层：核心库是窄腰，CLI/WebUI 是可替换前端

```
  CLI(人/CI/skill)   WebUI 后端        ← 前端「皮」（薄）；都直接调核心，平级
        └──────┬──────┘
          执行核心库（窄腰：解析 .feature → 分组 scope → 调度 → 收集结果）
                │  runScope(scope, sink)
        本地执行实现  /  Fargate 执行实现   ← 执行面，可替换
```

- **窄腰是「核心库」，不是 CLI**（早先措辞修正）。CLI 是核心的第一个、最薄的前端；WebUI 是另一个前端，**直接调核心、不 shell-out CLI**（后者才是"难集成"的错误做法）。
- CI / AI-skill 通过 CLI 这个皮间接用核心；都契合"调命令→等结果→看退出码"。
- **阻塞 vs 非阻塞是调用方的选择，不是核心的属性**：CLI 可轮询到完成（像阻塞）；WebUI 提交即返回 runId、之后轮询。同一核心两种皮都满足。

## 数据模型（现在钉死；耐久，决定 DDB 表 / WebUI / 报告）

| 概念 | 是什么 | 产出 |
|---|---|---|
| **Scenario** | Gherkin 单个 `Scenario:` | pass/fail、A/B 断言、抖动数据（投票）、原生报告引用 |
| **Feature**（`.feature`） | 含 1..N scenario | **组织轴**（正交，非执行单元） |
| **Scope**（session scope） | 共享操作上下文的 scenario 分组 | **执行单元**：scope 内串行、scope 间并行；语义层配置（用例的上下文依赖在此显式表达） |
| **Job** | 提交给执行面的单元 | **= Scope**（被 session-scope 语义强制：若 job=scenario，有依赖的 scenario 会被拆到不同 microVM 无法共享会话） |
| **Run** | 一次执行，封装多个 job | `runId`、总状态、起止、**RunResult**、**RunReport** |

- **RunResult** = 机器可读汇总判定（退出码 / CI / WebUI 状态）。
- **RunReport** = 人看的归集报告（把两腿割裂的 Midscene html / Nova trajectory 归到一处）。**这就是原 M5「报告统一」的归宿**——它不再是孤立 TODO，而是 RunReport 实体的实现。

**已定 = 概念/层级（上表）；未定 = 字段级 schema**（runId / jobId(scopeId) / 会话血缘 sessionId / 起止时间 / 每 scenario 判定与抖动投票记录 / 报告产物指针 …）。字段级**有意留到 v0.x** 用真实跑批产物逼出（"报告要展示什么、CI 要读什么"届时自然浮现），避免现在纸上列错。它决定将来 DDB 表结构与 WebUI 读取面，故 v0.x 必须坐实、那时补全本节。

## 引擎选择 & 并发（已定）

- 用例可配"用哪条腿"（默认单腿），经 `@engine:` tag 选腿（ADR 0019）。**双腿交叉验证 v1.0 不做**（价值可疑、复杂度高，见 ADR 0019）；未来若需，在跑批层展开两次独立运行。
- 并发：**scope 内串行**（上下文依赖），**scope 间并行**（互相独立）。

## 留口子：Ports & Adapters（六边形架构），组合根注入

可替换的外部依赖不散落成 `runScope` 的一堆参数，而是收成一个 **ports 层**（类比 DAO 层）：导出稳定接口，核心只依赖接口、不知实现是谁。

**按关注点拆成独立 port（不揉成上帝 module）**：
- `ResultStore` —— 写/读 Run/Job/Scenario 的状态与结果（local 文件 → 云端 DynamoDB）
- `ReportStore` —— 存归集报告产物（local FS → S3）
- `ExecutionBackend` —— 真正跑 scope 的地方（local 进程 → Fargate），即 `runScope` 的执行实现
- （其余按需，如凭证源；保持各自独立、生命周期不同）

**选实现 = 组合根注入，不是 module 自选**（关键，避开本会话踩过的坑）：
- 接口定义在 ports module；**具体 adapter 由调用方（CLI 的 main / WebUI 的 bootstrap = 组合根）在启动时注入**给核心。核心只认接口。
- **禁止** ports module 内部用全局单例 + `env`-sniff 自选实现——那正是本项目踩过的 Midscene `GlobalConfigManager` 反模式（import 时缓存 env、运行时改不动、难测）。注入式可测、无隐藏全局。

**rule-of-three 克制**：接口现在定（廉价，还逼清边界），但**只写 local adapter**；DDB/S3/Fargate adapter 等云端真需要时再填。

这样无状态化、上云、WebUI 接入都成了"加 adapter + 组合根换注入"，核心与接口不动。

## 版本切分（按完成线，非时间）

- **spike（已完成）**：技术链路全通。
- **v0.x**：验证核心假设 + 报告能看。糙、小范围。本地执行。
  - **核心假设（可证伪，带验收标准）**：QA **只写 `.feature`、零 step 代码**，靠通用 step（`When {自然语言} → aiAct`）即可跑通真实用例。
  - **验收**：≥N 个真实用例（N 待定，建议 ≥3 含不同动作类型）**全部由 QA 不写任何 step 代码跑通**；每处需要破例写代码的地方都记录下来作为反证。若破例过多 → 假设不成立，回头重想"不写代码"如何兑现。
- **v1.0**：团队 QA 日常可用——多用例组织、跑批入口（CLI 阻塞跑一批）、RunReport 归集、抖动治理（投票）落地。本地执行。
- **v1.x+**：云端执行（CLI 提交 → Fargate 跑 → 轮询收集），**job = scope** 粒度（强候选，上云时坐实，见 [0017](./0017-cloud-execution-fargate-over-runtime.md)）；引入外置状态存储（DDB）+ 无状态核心。
- **v2.0**：WebUI 前端（直接调核心）、规模化。

## v0.x 待决设计点（验证时用真实用例逼出，不纸上硬定）

G1/G2 原是 v1.0 核心库 `.feature` 解析的前置，留到 B 步坐实——**现已定（ADR 0019）**：

- **G1 — session scope 声明**：✅ `@scope:<name>` tag（相同值同 scope、串行共享会话；不同值并行；未标各自独立）。tag 两腿可读已验证。
- **G2 — 引擎选择**：✅ `@engine:<x>` tag 选腿（scope 级属性、容错缺省、冲突报错）；v1.0 只选腿不交叉。两腿路由已验证。
- 声明语法已定，但**调度实现**（scope 串/并行、会话共享、冲突校验）仍待 C（核心库）。

## 现在做 / 现在不做

- **现在做（v1.0）**：核心库可被调用（逻辑不焊死在 CLI main 里）；钉死上面数据模型；定义 ports 接口（`ResultStore`/`ReportStore`/`ExecutionBackend`）+ 写 local adapter + 组合根注入。
- **现在不做**：DynamoDB / S3 / Fargate adapter / 无状态机制 / WebUI ——接口已留好，等云端真需要时填 adapter + 组合根换注入。**避免为想象中的云端预先盖机器。**
- **G1/G2 声明语法已定**（ADR 0019）；其**调度实现**（scope 串/并行、会话共享、engine 冲突校验）留给 C 核心库。
- **多用例组织**（feature 分目录/命名约定、跑批入口、跑批层选择 feature/tag）同样留给 C——它依赖核心库的调度层，在 bdd 直跑层做是临时的、C 来会重做。当前 `features/` 下多个文件仅是 v0.x 打磨产物，未做有意组织。（cucumber 侧用 `--tags` 选子集的临时约定见 `midscene/cucumber.mjs` 注释。）
