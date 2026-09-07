# @gherkai/worker-midscene（Midscene TS 引擎 worker）

gherkai 的 Midscene.js (TypeScript) 侧执行引擎，以 **npm 包**分发（ADR 0037 决策 3）。用 **Qwen3-VL 235B on Bedrock** 做视觉定位大脑，经 **SigV4 自签** 接入，浏览器跑在 **AgentCore 云端**。

| | |
|---|---|
| 发行名 | `@gherkai/worker-midscene`（npm，public） |
| 命令名 | `gherkai-worker-midscene`（bin = `dist/bin.mjs`） |
| 运行时 | Node ≥ 22，统一 ESM（`"type": "module"`，源码 `.mts` → 产物 `.mjs`） |
| 版本 | 与 CLI（`gherkai`）lockstep；仓库里是占位 `0.0.0-dev`，发行版本由 CI 在 publish 时写入 |

使用方（测试工程师）一般**不直接跑它**：装上之后由 `gherkai` CLI 按 worker 定位链拉起（ADR 0037 决策 3）。

```bash
npm i -g @gherkai/worker-midscene     # 或让 CLI 走 npx 兜底
```

> ⚠️ 早期 README 曾写"用 Bedrock GPT-5.5 / `MIDSCENE_MODEL_FAMILY=gpt-5`"——**已废弃**。实测 Bedrock 上的 gpt-5.5 不支持 chat-completions（见根目录 ADR 0002）。当前大脑见 ADR 0003，鉴权见 ADR 0008。

## 模型 / 鉴权（无需任何 API key）

不用 `MIDSCENE_MODEL_API_KEY` bearer，改用进程内 SigV4 自签（复用本机 AWS 默认凭证链）：

- 模型：`qwen.qwen3-vl-235b-a22b`，`MIDSCENE_USE_QWEN3_VL=true`
- base URL：`https://bedrock-runtime.${AWS_REGION}.amazonaws.com/openai/v1`（region 惰性读 `AWS_REGION`、未设即 fail-loud，不硬编码 east——见 `src/lib/agentcore-sigv4.mts` 的 `getRegion()`/`getBaseUrl()`、ADR 0033）
- 接线：经 Midscene `createOpenAIClient` 注入带 SigV4 签名的自定义 `fetch`
- 配方与失败模式：`spikes/SIGV4-FETCH-RECIPE.md`

## 布局

```
src/
├── bin.mts            ← 唯一入口（npm bin + 容器 CMD）：装 tsx loader + 注册 resolve hook + 调 worker main
├── index.mts          ← 包的公开 API：使用方 step 文件 import 的 { deterministic, DeterministicAssertion, 类型 }
├── resolve-hook.mts   ← 裸 specifier "@gherkai/worker-midscene" → worker 自身安装位置（随 dist 发布的独立入口）
├── worker/            ← 薄 worker：run-scope（派发/会话/事件）、确定性注册表、内建脚手架、使用方 steps 加载
└── lib/               ← I/O 边缘组件：job 入口 / 事件出口 / 产物上传 / SigV4
dist/                  ← tsc 产物（*.mjs + *.d.mts），发布物；不入库
spikes/                ← 五段式自检脚本（不进包、不编译）
```

测试与源码同处（`src/**/*.test.mts`），不进 `dist`。

## 执行形态：薄 worker（cucumber 已退役）

进程入口是 `src/bin.mts`——**它本身就是 worker 进程**：装好 loader 与 resolve hook 后直接调 `src/worker/run-scope.mts` 的 `main`，**不 spawn 子 node**（core 用 `pass_fds` 把事件通道 fd 继承给它直接起的那个进程，中间多一层包装就把 fd3 吞了，ADR 0024 三通道）。core 自解析 `.feature`、把每个 step 经 ADR 0024 协议派发进来（ADR 0022），cucumber-js 入口已随 v0.x BDD 层退役删除。

正常经 `gherkai` CLI 跑；也可手动直跑调试（`npm ci && npm run build` 之后）：

```bash
echo '<job json>' | AWS_REGION=us-east-1 node dist/bin.mjs

# 另有两个「自述」入口（不建会话、不跑 job、零 AWS，ADR 0036）——cli 的 list-deterministic / plan 标注即转述它们：
node dist/bin.mjs --list-deterministic                    # dump 确定性注册表（pattern + description + example）
echo '["页面地址匹配 \"/wiki/OpenAI\""]' | node dist/bin.mjs --match-steps   # 批量问这些 step 各命中什么
```

## 确定性 step 的定制：使用方 `steps/` 目录

「必须精确、不容 AI 抖动」的判定写成确定性 step（ADR 0015 逃生舱 / 0020 角色边界：由 test engineer 写，QA 只写自然语言）。**定制面在使用方自己的项目里**，不改本包源码（ADR 0037 决策 4）：

```
<你的项目>/
├── features/          ← QA 的 .feature
└── steps/             ← 确定性 step（本引擎取 *.mts / *.mjs；Nova 引擎取 *.py）
    └── login.mts
```

```ts
// steps/login.mts
import { deterministic, DeterministicAssertion } from "@gherkai/worker-midscene";

deterministic(
  '页面地址匹配 "(?<pattern>[^"]+)"',           // 具名组 (?<name>...) = handler 的 groups
  ({ page }, { pattern }) => {                   // ctx.page = Playwright Page；不投票、可复现
    if (!new RegExp(pattern).test(page.url())) {
      throw new DeterministicAssertion(`URL 应匹配 ${pattern}，实际 ${page.url()}`);
    }
  },
  { description: "断言当前页面 URL 匹配给定正则", example: 'Then 页面地址匹配 "/wiki/OpenAI"' },
);
```

要点：

- **扩展名只认 `.mts` / `.mjs`**：这两个恒为 ESM，与你的项目目录里有没有 `package.json`、`type` 写什么无关（`.ts`/`.js` 会落进 CJS 域、`import` 直接 SyntaxError）。脚手架与文档统一用 `.mts`。
- **`description` / `example` 必填**（ADR 0036「注册即暴露」）：缺则启动即报错——`gherkai list-deterministic` / `plan` 的标注就是从这张表生成的。
- 目录**排序递归**遍历，`*.test.*` 跳过；`gherkai run/submit` 的 `--steps-dir` flag > env `GHERKAI_STEPS_DIR` > 默认 `./steps` 由 CLI 解析、随 run 定义传给 worker（worker 只认 env `GHERKAI_STEPS_DIR`）。
- **加载失败 fail-loud**：任一文件 import 出错、或某文件一条都没注册 → worker 立刻非零退出并点名该文件。**绝不静默跳过**——跳过等于把确定性判定悄悄换成 AI 兜底、run 可能"通过"。「一条都没注册」多半意味着 `import` 的不是本包（解析到了第二份副本），这条检查把它从静默降级变成显式失败。
- 内建脚手架 step（URL 匹配那条）留在包内；使用方 step 与内建**撞 pattern 不做覆盖**，按 ADR 0036 的 conflict 语义在 `plan` 预检暴露。

## contributor：从本 checkout 跑

```bash
npm ci              # 装依赖（含 devDeps 里的 typescript——build 期需要）
npm run build       # tsc → dist/*.mjs
npm test            # node --import tsx --test "src/**/*.test.mts"
```

让 CLI 指向本 checkout（dev 态没有已安装的 npm 包，走 worker 定位链**第一级** env 覆写，ADR 0037 决策 3）：

```bash
export GHERKAI_WORKER_MIDSCENE_CMD="node $(pwd)/dist/bin.mjs"
# 配套的 GHERKAI_WORKER_MIDSCENE_CWD 一般不需要：bin 在进程内注册 tsx，
# 不再靠 cwd 上溯 node_modules 解析裸 specifier（旧的 `node --import tsx …` 形态才需要）。
```

免 build 的快速迭代形态（改完源码直接跑，验证过）：

```bash
GHERKAI_WORKER_MIDSCENE_CMD="node $(pwd)/src/bin.mts"     # 需 Node ≥ 22.18（原生 type stripping）
```

**不要用 `node --import tsx src/bin.mts`**：`tsx` 是裸 specifier，按**进程 cwd** 上溯 `node_modules` 解析——CLI 从别处起 worker 时直接 `Cannot find package 'tsx'`（实测）。`node src/bin.mts` 没这个问题（bin 自己 import tsx，按文件位置解析）。

## 跑 spike（五段式自检，可独立跑）

```bash
AWS_REGION=us-east-1 node_modules/.bin/tsx spikes/01-model-sigv4.ts        # 模型连接（SigV4）
AWS_REGION=us-east-1 node_modules/.bin/tsx spikes/02-agentcore-cdp.ts      # 浏览器连接（CDP）
AWS_REGION=us-east-1 node_modules/.bin/tsx spikes/03-midscene-grounding.ts # 合体（grounding）
AWS_REGION=us-east-1 node_modules/.bin/tsx spikes/04-planning-probe.ts     # planning 候选探针（纯文本模型能否当 planner）
AWS_REGION=us-east-1 node_modules/.bin/tsx spikes/05-negative-assertions.ts # 负向断言（"该红能红"，防永远绿）
```

## 注意

- **运行时依赖全在 `dependencies`**（`@midscene/web`、`@playwright/test`、`playwright`、各 `@aws-sdk/*`、`openai`、`tsx`）：npm 包的消费者只会装 `dependencies`，留在 `devDependencies` 里的运行时依赖必崩（ADR 0033 记的「不能 `--production`」陷阱在包化后变成必然）。`devDependencies` 只剩 build/类型（`typescript`、`@types/node`）。
- `@playwright/test` 是 `@midscene/web` 声明为 optional peer、但 `@midscene/web/playwright` 子入口**无条件 import** 的包——故它也是运行时依赖（真跑打包安装才暴露）。
- 容器镜像见 `Dockerfile`（基底镜像，ADR 0037 决策 5 / 0038）：`npm ci` → `npm run build` → `CMD ["node", "dist/bin.mjs"]`。
