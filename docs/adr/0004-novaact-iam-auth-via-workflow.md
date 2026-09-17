# Nova Act 用纯 IAM 鉴权（经 Workflow 构造），不用 NOVA_ACT_API_KEY

> **Status:** Accepted

为契合「统一走 AWS、不引入额外凭证」，Nova Act 引擎用本账号已有的 IAM 凭证鉴权，**不**申请/设置 `NOVA_ACT_API_KEY`。

经核实 nova-act 3.4.187.0 源码，IAM 可同时覆盖两个鉴权关注点，但有一个反直觉的前提：

- **AgentCore 浏览器会话**：本就走纯 IAM SigV4（`AgentCoreBrowserSessionProvider`），不需要 key。
- **模型推理**：`NOVA_ACT_API_KEY` 未设时，**必须把调用包进 Nova Act 的 `Workflow` 构造**（带 `workflow_definition_name`），SDK 才会选 `StarburstBackend`（IAM 签名的 `nova-act` boto client）；否则报 `ValueError` 要求改用 Workflow。**裸用 AgentCore provider 不包 Workflow 仍会要 API key。**

**决定**：代码形态固定为 `NOVA_ACT_API_KEY` 不设 + `AgentCoreBrowserSessionProvider` + `Workflow(workflow_definition_name=..., model_id=...)`，让浏览器与模型都跑在 IAM 上。

**代码形态的两个强制细节**（漏了直接崩、非可选风格）：① `Workflow(...)` 必须被 `with` 进入才建出 `workflow_run`，只构造不进入会在 `NovaAct` 初始化时报 `ValidationFailed: Workflow does not have workflow run set. Please use Workflow as a context manager`；② `NovaAct` 未显式收到 workflow 时经 contextvar 找它，故用 `@workflow` 装饰器（它内部即 `with Workflow` + 设 contextvar）或自己 `with Workflow` 时手工 `set_current_workflow(wf)`、退出时还原——worker 走后者（见 `engines/novaact/gherkai_worker_novaact/run_scope.py` 的 `with wf` + `set_current_workflow`）。

## ✅ 已实测全通（2026-06-23，`engines/novaact/spikes/wikipedia_benchmark.py`）

纯 IAM 经 `@workflow` 端到端跑通：维基用例动作成功、AgentCore 云端浏览器连上、workflow run 状态 `SUCCEEDED`、`nova-act-latest` 模型访问授予。**ADR 早先标记的"IAM 经 Workflow 能否授权 nova-act 服务"残余风险——已关闭。**

**关键前提**：`@workflow` 走 IAM 路径时，`workflow_definition_name` **必须指向一个 AWS 侧已注册存在的 workflow definition**，不能随便起名——否则 `CreateWorkflowRun` 报 `ResourceNotFoundException: Workflow definition not found` (404)。注意：IAM 鉴权本身此时已通过（不是 AccessDenied），仅仅是 definition 不存在。

definition 由 create-if-not-exists 的 `ensure_workflow_definition()` 自动建（见 `engines/novaact/gherkai_worker_novaact/lib/workflow_setup.py`）：首次建、之后探测到即跳过，幂等；worker（`run_scope.py`）与 spike 均已接入，无手动前置。boto3 的 `create_workflow_definition`/`get_workflow_definition` 与 CLI `aws nova-act create-workflow-definition`（region us-east-1）等价。**已实证（2026-06）**：删掉 definition 后代码能从零自动建回。
本项目用的 definition 名：`gherkai-worker`（产品名——definition 建在**使用方**账户里、名字露在他们自己的 AWS 控制台，故不留试验期代号；旧名 `spike-wikipedia-benchmark` 系 spike 期遗留，分发化后改掉。**改名无迁移成本**：create-if-not-exists 按新名自动建，部署侧 IAM 用 `workflow-definition/*` 通配、不 pin 具体名（见 [0033](./0033-iac-aws-backend-and-composition-wiring.md)）；代价仅是旧名的 definition 留在账户里不再被引用；v1.4.2 发行版在使用方账户首跑 novaact 的真跑已核：`gherkai-worker` 自动建出并 ACTIVE、run 到终态 passed，旧名并存）。若要跨账号预建 definition 或收紧 worker 的 create 权限，可改由 IaC / 部署脚本建——代价是 worker 失去 create-if-not-exists 的自愈、首跑依赖部署顺序；当前不改，理由见下并发档的幂等决定。

**幂等必须覆盖并发档**：worker 是**每 scope 一个进程**（本地并发 spawn / 云端多 task 同时起），definition 尚不存在的首跑会让多个进程同时 `get`→404→`create`，赢家外的进程吃 `CreateWorkflowDefinition` 的 `ConflictException`（409，nova-act 服务模型里是该 API 的声明错误之一；`get` 侧没有此错误）。**决定**：把 `ConflictException` 按「已存在」吞掉、归 `exists`——并发赢家已建即目标达成，对外语义仍是 create-if-not-exists。否则裸异常落在**会话尚未起、退出码通道未走**的时点：worker traceback exit 1 → core 归 `engine_error`（既不重试也归错类），且 [0028](./0028-transient-network-ssl-resilience.md) 把本 helper 列为「建连段可安全重放」的幂等依据只在串行下成立。

**退路**：若某账号/region IAM 路径不可用，退回 `NOVA_ACT_API_KEY`（从 nova.amazon.com/act 生成）。

## 模型版本选择策略（待定，等 A/B 数据）

`Workflow(model_id=...)` 现传别名 `nova-act-latest`（`lib/constants.py`）。服务端 `ListModels`（2026-09-17 实查，SDK 兼容版本 1）：GA 只有 `nova-act-v1.0`（ACTIVE），另有 preview `nova-act-v1.1_2026-02-09`；别名 `nova-act-latest` → v1.0、`nova-act-preview` → v1.1；SDK 3.4.187.0 两者都支持。两条路各有代价，**默认用哪条尚未定**：

- **别名（现状）**：AWS 发新 GA 时自动换模型，零改动跟进；代价是判定基线在零提交的情况下漂移——本工具的 pass / fail 靠 AI 投票，模型一换形态就变，且事后无从对照。
- **钉版本（`nova-act-v1.0`）**：判定可复现、升级是一次有意识的提交（与包版本用 `==` 同版本 pin 同一逻辑），GA 承诺支持至少一年；代价是每个新 GA 要手动跟进、评估后再切。

判据 = 同一批 Nova 用例在 v1.0 与 v1.1 上各跑三遍的 pass / fail 稳定性、单 act 耗时、超时率差异：差异明显 → 钉版本并把「切模型」当作有评估的升级动作；差异不明显 → 别名的漂移风险可接受。**preview 不作生产默认**（无支持承诺、不可钉），无论 A/B 结果如何。按项目选模型的旋钮（`NOVA_MODEL_ID` env 经组合根注入）暂不做：近期唯一消费者是这次 A/B，四个注入面就是四个会漂的地方，等有用户要按项目选模型或新 GA 需新旧并行验证时再加。
