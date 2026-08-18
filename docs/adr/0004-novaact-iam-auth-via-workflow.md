# Nova Act 用纯 IAM 鉴权（经 Workflow 构造），不用 NOVA_ACT_API_KEY

> **Status:** Accepted

为契合「统一走 AWS、不引入额外凭证」，Nova Act 引擎用本账号已有的 IAM 凭证鉴权，**不**申请/设置 `NOVA_ACT_API_KEY`。

经核实 nova-act 3.4.187.0 源码，IAM 可同时覆盖两个鉴权关注点，但有一个反直觉的前提：

- **AgentCore 浏览器会话**：本就走纯 IAM SigV4（`AgentCoreBrowserSessionProvider`），不需要 key。
- **模型推理**：`NOVA_ACT_API_KEY` 未设时，**必须把调用包进 Nova Act 的 `Workflow` 构造**（带 `workflow_definition_name`），SDK 才会选 `StarburstBackend`（IAM 签名的 `nova-act` boto client）；否则报 `ValueError` 要求改用 Workflow。**裸用 AgentCore provider 不包 Workflow 仍会要 API key。**

**决定**：代码形态固定为 `NOVA_ACT_API_KEY` 不设 + `AgentCoreBrowserSessionProvider` + `Workflow(workflow_definition_name=..., model_id=...)`，让浏览器与模型都跑在 IAM 上。

## ✅ 已实测全通（2026-06-23，`engines/novaact/spikes/wikipedia_benchmark.py`）

纯 IAM 经 `@workflow` 端到端跑通：维基用例动作成功、AgentCore 云端浏览器连上、workflow run 状态 `SUCCEEDED`、`nova-act-latest` 模型访问授予。**ADR 早先标记的"IAM 经 Workflow 能否授权 nova-act 服务"残余风险——已关闭。**

**关键前提**：`@workflow` 走 IAM 路径时，`workflow_definition_name` **必须指向一个 AWS 侧已注册存在的 workflow definition**，不能随便起名——否则 `CreateWorkflowRun` 报 `ResourceNotFoundException: Workflow definition not found` (404)。注意：IAM 鉴权本身此时已通过（不是 AccessDenied），仅仅是 definition 不存在。

注册可用 CLI 或 boto3（等价）：
```
aws nova-act create-workflow-definition --region us-east-1 --name "<name>"
```
**但已做成代码端到端闭环（2026-06，实证）**：boto3 有等价的 `create_workflow_definition`/`get_workflow_definition`，故用 create-if-not-exists 的 `ensure_workflow_definition()`（见 `engines/novaact/lib/workflow_setup.py`）——首次自动建、之后探测到即跳过，幂等。worker（`run_scope.py`）与 spike 都已接入，**无需手动 CLI 前置**。已实证：删掉 definition 后代码能从零自动建回。
本项目用的 definition 名：`spike-wikipedia-benchmark`。生产化时也可改由 IaC / 部署脚本统一管理。

**幂等必须覆盖并发档**：worker 是**每 scope 一个进程**（本地并发 spawn / 云端多 task 同时起），definition 尚不存在的首跑会让多个进程同时 `get`→404→`create`，赢家外的进程吃 `CreateWorkflowDefinition` 的 `ConflictException`（409，nova-act 服务模型里是该 API 的声明错误之一；`get` 侧没有此错误）。**决定**：把 `ConflictException` 按「已存在」吞掉、归 `exists`——并发赢家已建即目标达成，对外语义仍是 create-if-not-exists。否则裸异常落在**会话尚未起、退出码通道未走**的时点：worker traceback exit 1 → core 归 `engine_error`（既不重试也归错类），且 [0028](./0028-transient-network-ssl-resilience.md) 把本 helper 列为「建连段可安全重放」的幂等依据只在串行下成立。

**退路**：若某账号/region IAM 路径不可用，退回 `NOVA_ACT_API_KEY`（从 nova.amazon.com/act 生成）。
