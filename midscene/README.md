# midscene (TS 引擎子工程)

Midscene.js (TypeScript) 侧的执行引擎。用 **Qwen3-VL 235B on Bedrock** 做视觉定位大脑，经 **SigV4 自签** 接入，浏览器跑在 **AgentCore 云端**。

> ⚠️ 早期 README 曾写"用 Bedrock GPT-5.5 / `MIDSCENE_MODEL_FAMILY=gpt-5`"——**已废弃**。实测 Bedrock 上的 gpt-5.5 不支持 chat-completions（见根目录 ADR 0002）。当前大脑见 ADR 0003，鉴权见 ADR 0008。

## 模型 / 鉴权（无需任何 API key）

不用 `MIDSCENE_MODEL_API_KEY` bearer，改用进程内 SigV4 自签（复用本机 AWS 默认凭证链）：

- 模型：`qwen.qwen3-vl-235b-a22b`，`MIDSCENE_USE_QWEN3_VL=true`
- base URL：`https://bedrock-runtime.us-east-1.amazonaws.com/openai/v1`
- 接线：经 Midscene `createOpenAIClient` 注入带 SigV4 签名的自定义 `fetch`
- 配方与失败模式：`spikes/midscene-sigv4/SIGV4-FETCH-RECIPE.md`

## 跑 BDD（cucumber-js，加载根 `features/`）

```bash
NODE_OPTIONS="--import tsx/esm" AWS_REGION=us-east-1 \
  node_modules/.bin/cucumber-js -c cucumber.mjs
```

## 跑 spike（三段式自检，可独立跑）

```bash
AWS_REGION=us-east-1 node_modules/.bin/tsx spikes/midscene-sigv4/01-model-sigv4.ts      # 模型跳
AWS_REGION=us-east-1 node_modules/.bin/tsx spikes/midscene-sigv4/02-agentcore-cdp.ts    # CDP 跳
AWS_REGION=us-east-1 node_modules/.bin/tsx spikes/midscene-sigv4/03-midscene-grounding.ts # 合体
```

## 注意

- 本子工程是 `commonjs`；`bdd/` 下有局部 `package.json` 标 `type:module` 使 step 走 ESM。
- 依赖全在本地 `node_modules`，不污染全局。
