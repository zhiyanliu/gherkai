# midscene (TS 引擎子工程)

Midscene.js (TypeScript) 侧的执行引擎。用 **Qwen3-VL 235B on Bedrock** 做视觉定位大脑，经 **SigV4 自签** 接入，浏览器跑在 **AgentCore 云端**。

> ⚠️ 早期 README 曾写"用 Bedrock GPT-5.5 / `MIDSCENE_MODEL_FAMILY=gpt-5`"——**已废弃**。实测 Bedrock 上的 gpt-5.5 不支持 chat-completions（见根目录 ADR 0002）。当前大脑见 ADR 0003，鉴权见 ADR 0008。

## 模型 / 鉴权（无需任何 API key）

不用 `MIDSCENE_MODEL_API_KEY` bearer，改用进程内 SigV4 自签（复用本机 AWS 默认凭证链）：

- 模型：`qwen.qwen3-vl-235b-a22b`，`MIDSCENE_USE_QWEN3_VL=true`
- base URL：`https://bedrock-runtime.us-east-1.amazonaws.com/openai/v1`
- 接线：经 Midscene `createOpenAIClient` 注入带 SigV4 签名的自定义 `fetch`
- 配方与失败模式：`spikes/SIGV4-FETCH-RECIPE.md`

## 执行形态：薄 worker（cucumber 已退役）

本引擎的执行入口是 `worker/run-scope.ts`——被根 `core/` spawn 的薄 worker（core 自解析 `.feature`、
把每个 step 经 0024 协议派发进来，ADR 0022）。**cucumber-js 入口（`cucumber.mjs` + patch）已随 v0.x BDD 层退役删除**。
正常经 cli 跑（根 `cli/`）；worker 也可手动直跑调试：

```bash
echo '<job json>' | AWS_REGION=us-east-1 node --import tsx worker/run-scope.ts
```

## 跑 spike（五段式自检，可独立跑）

```bash
AWS_REGION=us-east-1 node_modules/.bin/tsx spikes/01-model-sigv4.ts        # 模型连接（SigV4）
AWS_REGION=us-east-1 node_modules/.bin/tsx spikes/02-agentcore-cdp.ts      # 浏览器连接（CDP）
AWS_REGION=us-east-1 node_modules/.bin/tsx spikes/03-midscene-grounding.ts # 合体（grounding）
AWS_REGION=us-east-1 node_modules/.bin/tsx spikes/04-planning-probe.ts     # planning 候选探针（纯文本模型能否当 planner）
AWS_REGION=us-east-1 node_modules/.bin/tsx spikes/05-negative-assertions.ts # 负向断言（"该红能红"，防永远绿）
```

## 注意

- 本子工程是 `commonjs`；`worker/*.ts` 经 `--import tsx` 运行（无需 ESM 包配置——cucumber ESM 入口已退役）。
- 依赖全在本地 `node_modules`，不污染全局。
