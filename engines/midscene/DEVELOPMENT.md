# 开发笔记（contributor）

> 面向使用者的文档是同目录的 [`README.md`](./README.md)（它逐字上 npm 页面）；**本文件面向 contributor**，不随包发行（`package.json` 的 `files` 不含它）。

## 包身份

| | |
|---|---|
| 发行名 | `@gherkai/worker-midscene`（npm，public） |
| 命令名 | `gherkai-worker-midscene`（bin = `dist/bin.mjs`） |
| 运行时 | Node ≥ 22，统一 ESM（`"type": "module"`，源码 `.mts` → 产物 `.mjs`） |
| 版本 | 与 CLI（`gherkai`）lockstep；仓库里是占位 `0.0.0-dev`，发行版本由 CI 在 publish 时写入 |

以 npm 包分发的理由见 [ADR 0037](../../docs/adr/0037-distribution-and-packaging.md) 决策 3。

## 模型 / 鉴权（无需任何 API key）

不用 `MIDSCENE_MODEL_API_KEY` bearer，改用进程内 SigV4 自签（复用本机 AWS 默认凭证链，[ADR 0008](../../docs/adr/0008-midscene-bedrock-auth-sigv4-selfsign.md)）：

- 模型：`qwen.qwen3-vl-235b-a22b`，`MIDSCENE_USE_QWEN3_VL=true`（[ADR 0003](../../docs/adr/0003-midscene-grounding-qwen3vl-bedrock.md)）
- base URL：`https://bedrock-runtime.${AWS_REGION}.amazonaws.com/openai/v1`（region 惰性读 `AWS_REGION`、未设即 fail-loud，不硬编码 east——见 `src/lib/agentcore-sigv4.mts` 的 `getRegion()` / `getBaseUrl()`、[ADR 0033](../../docs/adr/0033-iac-aws-backend-and-composition-wiring.md)）
- 接线：经 Midscene `createOpenAIClient` 注入带 SigV4 签名的自定义 `fetch`
- 配方与失败模式：[`spikes/SIGV4-FETCH-RECIPE.md`](./spikes/SIGV4-FETCH-RECIPE.md)

> ⚠️ **历史坑**：早期文档曾写「用 Bedrock GPT-5.5 / `MIDSCENE_MODEL_FAMILY=gpt-5`」——**已废弃**。实测 Bedrock 上的 gpt-5.5 不支持 chat-completions（[ADR 0002](../../docs/adr/0002-midscene-not-driven-by-gpt55.md)）。

## 布局

```
src/
├── bin.mts            ← 唯一入口（npm bin + 容器 CMD）：装 tsx loader + 注册 resolve hook + 调 worker main
├── index.mts          ← 包的公开 API：使用方 step 文件 import 的 { deterministic, DeterministicAssertion, 类型 }
├── resolve-hook.mts   ← 裸 specifier "@gherkai/worker-midscene" → worker 自身安装位置（随 dist 发布的独立入口）
├── worker/            ← 薄 worker：run-scope（派发/会话/事件）、确定性注册表、内建脚手架、使用方 steps 加载、step 多行参数拼接（DataTable/DocString → 附加文本；两引擎须同一拼法）
└── lib/               ← I/O 边缘组件：job 入口 / 事件出口 / 产物上传 / SigV4
dist/                  ← tsc 产物（*.mjs + *.d.mts），发布物；不入库
spikes/                ← 五段式自检脚本（不进包、不编译）
```

测试与源码同处（`src/**/*.test.mts`），不进 `dist`。

## 执行形态：薄 worker（cucumber 已退役）

进程入口是 `src/bin.mts`——**它本身就是 worker 进程**：装好 loader 与 resolve hook 后直接调 `src/worker/run-scope.mts` 的 `main`，**不 spawn 子 node**（core 用 `pass_fds` 把事件通道 fd 继承给它直接起的那个进程，中间多一层包装就把 fd3 吞了，[ADR 0024](../../docs/adr/0024-worker-core-protocol.md) 三通道）。core 自解析 `.feature`、把每个 step 经 ADR 0024 协议派发进来（[ADR 0022](../../docs/adr/0022-bdd-runner-retired-core-parses-thin-worker.md)），cucumber-js 入口已随 v0.x BDD 层退役删除。

正常经 `gherkai` CLI 跑；也可手动直跑调试（`npm ci && npm run build` 之后）：

```bash
echo '<job json>' | AWS_REGION=us-east-1 node dist/bin.mjs

# 两个「自述」入口（不建会话、不跑 job、零 AWS，[ADR 0036](../../docs/adr/0036-deterministic-capability-discovery.md)）——cli 的 list-deterministic / plan 标注即转述它们：
node dist/bin.mjs --list-deterministic                    # dump 确定性注册表（pattern + description + example）
echo '["页面地址匹配 \"/wiki/OpenAI\""]' | node dist/bin.mjs --match-steps   # 批量问这些 step 各命中什么
```

## 从本 checkout 跑

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

## 使用方 `steps/` 的加载（实现要点）

约定解析（`--steps-dir` > env > `./steps`）在组合根，worker 只认 env `GHERKAI_STEPS_DIR`、不重解析（ADR 0037 决策 4；[ADR 0016](../../docs/adr/0016-execution-architecture-core-lib-run-model.md) 分层）。`src/worker/user-steps.mts` 排序递归遍历 `.mts` / `.mjs`（排除 `*.test.*`）逐个 `await import`，两条 fail-loud：

- import 失败 → 立刻抛，带文件名与原异常；
- **零注册检查**：某文件加载后注册表条数没涨 → 抛。这是「双实例」风险的显式化——裸 specifier 若解析到第二份包副本，注册会落进 worker 永远不读的表，症状本来是「全部 step 静默走 AI、run 还可能通过」。`index.mts` 与 worker 自身 import 的必须是同一个 `worker/deterministic.mjs` URL（靠 bin 注册的 resolve hook 保证，见 `resolve-hook.mts` 头注释）。

抛出而非自己 `process.exit`：退出码由入口（`bin.mts`）统一落地（非零、且不是 [ADR 0028](../../docs/adr/0028-transient-network-ssl-resilience.md) 的网络专用 80），本模块保持可单测。

内建脚手架 step 在 `src/worker/deterministic.steps.mts`（一条 URL 锚点作范例）；使用方 step 与内建**撞 pattern 不做覆盖**，按 ADR 0036 的 conflict 语义在 `plan` 预检暴露。

## 报告与产物落点

组合根经 `MIDSCENE_RUN_DIR` 注入 run 专属目录（`reports/<run_id>/midscene-run`，**必须绝对路径**：SDK 用 `path.resolve(process.cwd(), …)`），`report.html` 与 log/dump 全在其下；产物经 uploader 传 S3（[ADR 0029](../../docs/adr/0029-engine-artifacts-to-s3.md)），含 act 边界与中断兜底的 report 抢传（best-effort、失败吞+log、不影响退出码）。`--no-report` 档由组合根经 env `GHERKAI_NO_ARTIFACTS=1` 告知：关 agent 的 `generateReport`、不抢传、不带 report ref；SDK 仍可能往 `./midscene_run` 写 log/dump，故此档下若无 `MIDSCENE_RUN_DIR` 就把它导到一次性临时目录、不进用户 CWD。

## 跑 spike（五段式自检，可独立跑）

```bash
AWS_REGION=us-east-1 node_modules/.bin/tsx spikes/01-model-sigv4.ts        # 模型连接（SigV4）
AWS_REGION=us-east-1 node_modules/.bin/tsx spikes/02-agentcore-cdp.ts      # 浏览器连接（CDP）
AWS_REGION=us-east-1 node_modules/.bin/tsx spikes/03-midscene-grounding.ts # 合体（grounding）
AWS_REGION=us-east-1 node_modules/.bin/tsx spikes/04-planning-probe.ts     # planning 候选探针（纯文本模型能否当 planner，[ADR 0012](../../docs/adr/0012-planning-shares-qwen3vl-no-text-planner.md)）
AWS_REGION=us-east-1 node_modules/.bin/tsx spikes/05-negative-assertions.ts # 负向断言（"该红能红"，防永远绿）
```

## 依赖分类（踩过的坑）

- **运行时依赖全在 `dependencies`**（`@midscene/web`、`@playwright/test`、`playwright`、各 `@aws-sdk/*`、`openai`、`tsx`）：npm 包的消费者只会装 `dependencies`，留在 `devDependencies` 里的运行时依赖必崩（ADR 0033 记的「不能 `--production`」陷阱在包化后变成必然）。`devDependencies` 只剩 build/类型（`typescript`、`@types/node`）。
- `@playwright/test` 是 `@midscene/web` 声明为 optional peer、但 `@midscene/web/playwright` 子入口**无条件 import** 的包——故它也是运行时依赖（真跑打包安装才暴露）。

## 容器镜像（维护者向）

`Dockerfile` = Fargate 档的 worker **基底**镜像（同版本 `@gherkai/worker-midscene` + SDK 运行时 + 协议层，**零使用方内容**）；使用方的定制层模板（`FROM <基底>` + `COPY steps/` + `GHERKAI_STEPS_DIR`）在 README 与 [ADR 0038](../../docs/adr/0038-worker-image-delivery.md)。

同一份 Dockerfile **两态**，`--build-arg WORKER_SOURCE=` 选（ADR 0037 决策 5）：

- `index`（默认，CI 态）：`--build-arg WORKER_VERSION=X.Y.Z` 从 npm 装已发行包（`npm install -g`）；本态不 COPY，build context 任意。
- `local`（发行前本地验镜像）：装 build context 里 `npm pack` 出的 tarball：

```bash
(cd engines/midscene && npm ci && npm run build && npm pack --pack-destination ../../dist)
docker build --platform linux/amd64 -f engines/midscene/Dockerfile \
  --build-arg WORKER_SOURCE=local --build-arg WORKER_TARBALL=gherkai-worker-midscene-<ver>.tgz \
  -t gherkai-worker-midscene:dev dist/        # context = 放 tarball 的目录
```

真 build 踩过的两条：

- **必须 `--platform linux/amd64`**：Fargate task-def 固定 X86_64；arm Mac 不加则 build 出 arm64、容器启动期 `exec format error` 挂死（ADR 0033/0038）。
- **经典 builder（无 buildx）会把未选中的 stage 也跑一遍**，故两个 stage 都对「自己的参数没给」保持容忍（`if [ -n … ]`）；真正的把关在 final stage 的冒烟（`--list-deterministic`，不需要 AWS），漏 build-arg 在那里 fail-loud、不拖到 Fargate 启动期。

容器入口与 npm bin 同一个（`gherkai-worker-midscene` → `dist/bin.mjs`）：bin 是带 shebang 的文件、内核直接 exec node，**本进程即 worker**、不套包装进程（同上 fd3 理由）。**不装 chromium 二进制**：连的是 AgentCore 云浏览器（`chromium.connectOverCDP(wsUrl)`），playwright 只作 CDP 客户端库。

## 相关 ADR

[0002](../../docs/adr/0002-midscene-not-driven-by-gpt55.md) 不用 gpt-5.5 ·
[0003](../../docs/adr/0003-midscene-grounding-qwen3vl-bedrock.md) Qwen3-VL 定位 ·
[0008](../../docs/adr/0008-midscene-bedrock-auth-sigv4-selfsign.md) SigV4 自签 ·
[0012](../../docs/adr/0012-planning-shares-qwen3vl-no-text-planner.md) planning 共用同一模型 ·
[0016](../../docs/adr/0016-execution-architecture-core-lib-run-model.md) 执行架构 ·
[0020](../../docs/adr/0020-step-phrasing-default-ai-deterministic-scaffold.md) step 措辞与角色边界 ·
[0022](../../docs/adr/0022-bdd-runner-retired-core-parses-thin-worker.md) 薄 worker ·
[0024](../../docs/adr/0024-worker-core-protocol.md) worker↔core 协议 ·
[0028](../../docs/adr/0028-transient-network-ssl-resilience.md) 网络韧性与退出码 80 ·
[0029](../../docs/adr/0029-engine-artifacts-to-s3.md) 产物上传 ·
[0033](../../docs/adr/0033-iac-aws-backend-and-composition-wiring.md) IaC 与装配 ·
[0036](../../docs/adr/0036-deterministic-capability-discovery.md) 能力自述 ·
[0037](../../docs/adr/0037-distribution-and-packaging.md) 分发与打包 ·
[0038](../../docs/adr/0038-worker-image-delivery.md) 镜像交付
