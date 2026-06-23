# 权威信息源（自查用）

> 抢救自原 `midscene-novaact-prototype-guide.md` §10（该文档已退役），并补入本项目实测中用到的关键路径。
> 注意：决策与"事实现状"以 `CONTEXT.md` + `docs/adr/` 为准——下面是**外部一手来源**，用于查证细节。

## Midscene（任意页加 `.md` 取 markdown）

- https://midscenejs.com/model-config.md — 全部环境变量（含 `MIDSCENE_*_MODEL_*` 分槽）
- https://midscenejs.com/model-strategy.md — grounding 排名 + 多模型分工（planning 需 multimodal）
- https://midscenejs.com/model-common-config.md — family 列表 + 配置块
- https://midscenejs.com/integrate-with-playwright.md
- https://midscenejs.com/bridge-mode.md — 连桌面 Chrome（CDP 接法参考）
- 安装的源码（本机 ground truth）：`midscene/node_modules/@midscene/core/dist/`、`.../shared/dist/`
  - `createOpenAIClient` 注入点：`@midscene/core .../service-caller/index`（见 ADR 0008）
  - 隔离 ModelConfigManager：`@midscene/core .../agent/agent.js`（传 createOpenAIClient/modelConfig 即切隔离，见 spike 配方 §7）
  - planning 无条件附图：`@midscene/core .../ai-model/llm-planning.js`（见 ADR 0012）
  - 取结构化 API：`aiBoolean/aiNumber/aiString/aiQuery/aiAsk`（`.../agent/agent.d.ts`，见 ADR 0010/0014）

## Nova Act

- https://github.com/aws/nova-act — README（AgentCore 接法、`nova.page`、HITL）
- https://nova.amazon.com/act — API key 生成、Playground
- 安装的源码：`novaact/.venv/lib/python3.13/site-packages/nova_act/`
  - AgentCore provider：`browser_auth/agentcore_session_provider.py`（`cdp_session()` yield `(ws_url, headers)`）
  - workflow contextvar：`types/workflow.py`（`@workflow` 设 `set_current_workflow`；`with Workflow` 不设，见 ADR 0004 / bdd 修复）
- 多语言 SDK（形态 B 探路，能力存疑，见 ADR 0006）：npm `@aws-sdk/client-nova-act`、Go `aws-sdk-go-v2/service/novaact`

## AWS Bedrock / AgentCore

- https://docs.aws.amazon.com/bedrock/latest/userguide/inference-chat-completions-mantle.html — **OpenAI chat-completions 端点**（`bedrock-mantle` /v1 与 `bedrock-runtime` /openai/v1；SigV4 或 Bedrock API key）
- https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/browser-tool.html — AgentCore Browser
- https://docs.aws.amazon.com/bedrock/latest/userguide/ — Bedrock 模型卡、API keys、各模型"支持的 API"矩阵

## 常用 CLI（本项目实测用到）

```bash
# 列模型 + 过滤（确认账号/region 可用性）
aws bedrock list-foundation-models --region us-east-1 --query "modelSummaries[?contains(modelId,'qwen')].[modelId,inputModalities]" --output text

# Nova Act IAM 路径必需：注册 workflow definition（一次性，见 ADR 0004）
aws nova-act create-workflow-definition --region us-east-1 --name <name>

# AgentCore 浏览器会话（数据面）
aws bedrock-agentcore start-browser-session --region us-east-1 --browser-identifier aws.browser.v1 --name <name>
aws bedrock-agentcore stop-browser-session  --region us-east-1 --browser-identifier aws.browser.v1 --session-id <id>
```
