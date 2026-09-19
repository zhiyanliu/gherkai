# Nova Act 用纯 IAM 鉴权（经 Workflow 构造），不用 NOVA_ACT_API_KEY

> **Status:** Accepted

为契合「统一走 AWS、不引入额外凭证」，Nova Act 引擎用本账号已有的 IAM 凭证鉴权，**不**申请/设置 `NOVA_ACT_API_KEY`。

经核实 nova-act 3.4.187.0 源码，IAM 可同时覆盖两个鉴权关注点，但有一个反直觉的前提：

- **AgentCore 浏览器会话**：本就走纯 IAM SigV4（`AgentCoreBrowserSessionProvider`），不需要 key。
- **模型推理**：`NOVA_ACT_API_KEY` 未设时，**必须把调用包进 Nova Act 的 `Workflow` 构造**（带 `workflow_definition_name`），SDK 才会选 `StarburstBackend`（IAM 签名的 `nova-act` boto client）；否则报 `ValueError` 要求改用 Workflow。**裸用 AgentCore provider 不包 Workflow 仍会要 API key。**

**决定**：代码形态固定为 `NOVA_ACT_API_KEY` 不设 + `AgentCoreBrowserSessionProvider` + `Workflow(workflow_definition_name=..., model_id=...)`，让浏览器与模型都跑在 IAM 上。

**代码形态的两个强制细节**（漏了直接崩、非可选风格）：① `Workflow(...)` 必须被 `with` 进入才建出 `workflow_run`，只构造不进入会在 `NovaAct` 初始化时报 `ValidationFailed: Workflow does not have workflow run set. Please use Workflow as a context manager`；② `NovaAct` 未显式收到 workflow 时经 contextvar 找它，故用 `@workflow` 装饰器（它内部即 `with Workflow` + 设 contextvar）或自己 `with Workflow` 时手工 `set_current_workflow(wf)`、退出时还原——worker 走后者（见 `engines/novaact/gherkai_worker_novaact/run_scope.py` 的 `with wf` + `set_current_workflow`）。

## ✅ 已实测全通（2026-06-23，`engines/novaact/spikes/wikipedia_benchmark.py`）

纯 IAM 经 `@workflow` 端到端跑通：维基用例动作成功、AgentCore 云端浏览器连上、workflow run 状态 `SUCCEEDED`、模型访问授予（当时经别名 `nova-act-latest` 拿到的 GA 模型 = 今天钉死的 `nova-act-v1.0`；别名已按下方「模型版本选择策略」弃用）。**ADR 早先标记的"IAM 经 Workflow 能否授权 nova-act 服务"残余风险——已关闭。**

**关键前提**：`@workflow` 走 IAM 路径时，`workflow_definition_name` **必须指向一个 AWS 侧已注册存在的 workflow definition**，不能随便起名——否则 `CreateWorkflowRun` 报 `ResourceNotFoundException: Workflow definition not found` (404)。注意：IAM 鉴权本身此时已通过（不是 AccessDenied），仅仅是 definition 不存在。

definition 由 create-if-not-exists 的 `ensure_workflow_definition()` 自动建（见 `engines/novaact/gherkai_worker_novaact/lib/workflow_setup.py`）：首次建、之后探测到即跳过，幂等；worker（`run_scope.py`）与 spike 均已接入，无手动前置。boto3 的 `create_workflow_definition`/`get_workflow_definition` 与 CLI `aws nova-act create-workflow-definition`（region us-east-1）等价。**已实证（2026-06）**：删掉 definition 后代码能从零自动建回。
本项目用的 definition 名：`gherkai-worker`（产品名——definition 建在**使用方**账户里、名字露在他们自己的 AWS 控制台，故不留试验期代号；旧名 `spike-wikipedia-benchmark` 系 spike 期遗留，分发化后改掉。**改名无迁移成本**：create-if-not-exists 按新名自动建，部署侧 IAM 用 `workflow-definition/*` 通配、不 pin 具体名（见 [0033](./0033-iac-aws-backend-and-composition-wiring.md)）；代价仅是旧名的 definition 留在账户里不再被引用；v1.4.2 发行版在使用方账户首跑 novaact 的真跑已核：`gherkai-worker` 自动建出并 ACTIVE、run 到终态 passed，旧名并存）。若要跨账号预建 definition 或收紧 worker 的 create 权限，可改由 IaC / 部署脚本建——代价是 worker 失去 create-if-not-exists 的自愈、首跑依赖部署顺序；当前不改，理由见下并发档的幂等决定。

**幂等必须覆盖并发档**：worker 是**每 scope 一个进程**（本地并发 spawn / 云端多 task 同时起），definition 尚不存在的首跑会让多个进程同时 `get`→404→`create`，赢家外的进程吃 `CreateWorkflowDefinition` 的 `ConflictException`（409，nova-act 服务模型里是该 API 的声明错误之一；`get` 侧没有此错误）。**决定**：把 `ConflictException` 按「已存在」吞掉、归 `exists`——并发赢家已建即目标达成，对外语义仍是 create-if-not-exists。否则裸异常落在**会话尚未起、退出码通道未走**的时点：worker traceback exit 1 → core 归 `engine_error`（既不重试也归错类），且 [0028](./0028-transient-network-ssl-resilience.md) 把本 helper 列为「建连段可安全重放」的幂等依据只在串行下成立。

**退路**：若某账号/region IAM 路径不可用，退回 `NOVA_ACT_API_KEY`（从 nova.amazon.com/act 生成）。

## 模型版本选择策略：默认钉 GA 版本，换模型是有评估的显式升级

`Workflow(model_id=...)` 传**钉死的 GA 版本 id**（现为 `nova-act-v1.0`，住 `lib/constants.py`），不传 `nova-act-latest` 别名。服务端 `ListModels`（2026-09 实查，SDK 兼容版本 1）：GA 只有 `nova-act-v1.0`（ACTIVE，承诺支持至少一年），另有 preview `nova-act-v1.1_2026-02-09`；别名 `nova-act-latest` → 最新 GA、`nova-act-preview` → 最新 preview。

**为何钉而不是别名**：别名的语义是「AWS 发新 GA 时自动换模型」，换模型的时点由 AWS 定；而本工具的 pass / fail 靠 AI 投票，模型一换判定就变。2026-09 对 v1.0 与 v1.1 preview 做的 A/B（同一批 9 个 Nova scenario、各跑三遍、每次 run 经 `GetWorkflowRun.modelId` 坐实模型）：耗时等价（AI 步中位约 10 s、p90 约 28 s）、v1.1 无超时而 v1.0 一次单 act 越过 120 s 上界；但 **9 个 scenario 里有 1 个在两模型间三遍一致地翻转**——「搜索并进入 Python 词条」两模型都落在维基消歧页，布尔断言「当前页面是关于 Python 编程语言的词条」上 v1.0 先替用例点进目标词条再答 true、v1.1 停在原页如实答 false。这是行为差异不是噪声：换模型会稠密地改判定，且 v1.1 更守「断言不动作」，按 v1.0 写通的用例在 v1.1 上会翻红。这类变化必须随一次有 changelog 的显式发布落地，而不是藏在别名里在用户账户中静默发生。**升级流程**：新 GA 出现 → 按同一批用例重跑 A/B → 评估通过 → 改常量、发版并在 Release 正文点明模型换代。

**opt-in 旋钮 = worker 侧 env `NOVA_MODEL_ID`**（与 `NOVA_GRACE_MARGIN_S` 同形：worker 读、缺省即钉死值）：本机跑在 shell 里设即生效；云端 Fargate 容器 env 是显式枚举，要用就烙进定制 worker 镜像的 `ENV`——这正是 variant 机制（[0038](./0038-worker-image-delivery.md)）的用途。可设 `nova-act-preview` 试新模型，但 **preview 不作产品默认**：无支持承诺、随 AWS 移动，且**不可钉**——服务端拒绝直接引用带日期的 preview id（实测 400「Preview models cannot be referenced directly. Use the 'nova-act-preview' alias instead」），只有别名一条路，正是钉版本要消掉的那种不受控变化。**被拒方案**：经组合根四个注入面（本机 spawn / 前台 Fargate / detached Lambda / 能力自述）注入的产品级旋钮——近期无消费者，四个注入面就是四个会漂的地方；等有用户要按项目选模型或新 GA 需新旧并行验证时再议。

worker 的能力自述（[0036](./0036-deterministic-capability-discovery.md)「5.」）自报 `model_id`，`doctor` 据此显示当前模型，让 env 覆盖可见。两引擎通用的「默认模型锁定 + 按引擎 env 覆盖」策略与 Midscene 侧旋钮见 [0044](./0044-engine-model-selection-and-override.md)；本节保留 Nova 特有的选型证据。
