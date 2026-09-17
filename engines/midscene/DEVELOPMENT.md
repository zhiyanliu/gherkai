# 开发笔记（contributor）

> 使用者向文档是 [user guide](../../docs/user-guide/README.md)，同目录的 [`README.md`](./README.md) 是它的入口页（逐字上 npm 页面）；contributor 的总入口是根 [`CONTRIBUTING.md`](../../CONTRIBUTING.md)。**本文件面向 contributor**，不随包发行（`package.json` 的 `files` 只含 `dist` / `README.md` / `LICENSE`）。

## 包身份

| | |
|---|---|
| 发行名 | `@gherkai/worker-midscene`（npm，public） |
| 命令名 | `gherkai-worker-midscene`（bin = `dist/bin.mjs`） |
| 运行时 | Node ≥ 22，统一 ESM（`"type": "module"`，源码 `.mts` → 产物 `.mjs`） |
| 版本 | 与 CLI（`gherkai`）同版本发行；仓库里是占位 `0.0.0-dev`，发行版本由 CI 在 publish 时写入 |

以 npm 包分发的理由见 [ADR 0037](../../docs/adr/0037-distribution-and-packaging.md) 决策 3。

> **工作目录基线**：本页命令除注明外一律在 `engines/midscene/` 下跑（`npm` 脚本、`dist/bin.mjs`、`node_modules/.bin/tsx` 都以此为基准，`tsx` 只装在本目录的 `node_modules/.bin`）。只有「容器镜像」一节的两条命令从 repo 根跑。

## 模型 / 鉴权（无需任何 API key）

不用 `MIDSCENE_MODEL_API_KEY` bearer，改用进程内 SigV4 自签（复用本机 AWS 默认凭证链，[ADR 0008](../../docs/adr/0008-midscene-bedrock-auth-sigv4-selfsign.md)）：

- 模型：默认 `us.openai.gpt-5.6-terra`（`lib/agentcore-sigv4.mts` 的 `DEFAULT_MODEL`，选定依据 [ADR 0044](../../docs/adr/0044-engine-model-selection-and-override.md)「现值」），env `MIDSCENE_MODEL_ID` 覆盖取值、`MIDSCENE_MODEL_FAMILY` 覆盖家族；缺省 family 按模型 id 推断，推断表是同文件的 `MODEL_FAMILY_PATTERNS`（**唯一一份，别在别处再写一份**；决策与理由见 ADR 0044 决策 2），推不出即在 worker 启动期抛错、不兜底猜。family 决定 Midscene 用哪套提示词与请求参数，经 `worker/run-scope.mts` 的 `modelConfig()` 交给 SDK。
- base URL：`https://bedrock-runtime.${AWS_REGION}.amazonaws.com/openai/v1`（region 惰性读 `AWS_REGION`、未设即 fail-loud，不硬编码 east——见 `src/lib/agentcore-sigv4.mts` 的 `getRegion()` / `getBaseUrl()`、[ADR 0033](../../docs/adr/0033-iac-aws-backend-and-composition-wiring.md)）
- 接线：经 Midscene `createOpenAIClient` 注入带 SigV4 签名的自定义 `fetch`
- 配方与失败模式：[`spikes/SIGV4-FETCH-RECIPE.md`](./spikes/SIGV4-FETCH-RECIPE.md)

> **历史事实已变**：2026-06 实测 Bedrock 上的 gpt-5.5 不支持 chat-completions，据此把 GPT 系排除在主力模型之外（[ADR 0002](../../docs/adr/0002-midscene-not-driven-by-gpt55.md)，Status 已 Superseded-by 0044）；2026-09 实查 GPT-5.6 与 GPT-6 经 inference profile 支持 `/openai/v1/chat/completions` 且视觉通道可用，默认因此改为 GPT-5.6 Terra、family 走 `gpt-5`。别再按旧结论排除 GPT 系。Qwen3-VL 仍是 `MIDSCENE_MODEL_ID` 的可选值（选型历史见 [ADR 0003](../../docs/adr/0003-midscene-grounding-qwen3vl-bedrock.md)）。

## 布局

```
src/
├── bin.mts            ← 唯一入口（npm bin + 容器 CMD）：装 tsx loader + 注册 resolve hook + 调 worker main
├── index.mts          ← 包的公开 API：使用方 step 文件 import 的 { deterministic, DeterministicAssertion, 类型 }
├── resolve-hook.mts   ← 裸 specifier "@gherkai/worker-midscene" → worker 自身安装位置（随 dist 发布的独立入口）
├── worker/            ← 薄 worker：`run-scope.mts`（派发 / 会话 / 事件 / 信号收尾 / 两个非 job 入口的分派）、`deterministic.mts`（确定性注册表）、`deterministic.steps.mts`（内建脚手架）、`user-steps.mts`（使用方 steps 加载）、`argument.mts`（step 多行参数拼接：DataTable/DocString → 附加文本；两引擎须同一拼法）、`evidence.mts`（step 级机读证据：引擎 dump 裁成 evidence.json 供 explain 消费，[ADR 0042](../../docs/adr/0042-step-evidence-and-explain.md)）、`error-text.mts`（失败原因压成一行有界文本，与 Nova 的 `_error_text` 同形）；本目录下还有各模块的 `*.test.mts` 与测试夹具 `fixtures/`
└── lib/               ← I/O 边缘组件：`job-source.mts`（job 入口）· `event-sink.mts`（事件出口）· `artifact-upload.mts`（产物上传）· `agentcore-sigv4.mts`（SigV4 与模型常量）
dist/                  ← tsc 产物（*.mjs + *.d.mts），发布物；不入库
spikes/                ← 五段式自检脚本（不进包、不编译）
```

测试都是 `src/**/*.test.mts`，按 tsconfig 的 `exclude` 不进 `dist`。**但测试并非一律与源码同目录**：`lib/` 四个模块的测试（`agentcore-sigv4.test.mts` / `artifact-upload.test.mts` / `event-sink.test.mts` / `job-source.test.mts`）与夹具 `fixtures/` 都落在 `src/worker/` 下，新增测试跟这个位置、别另起 `src/lib/*.test.mts`。

## 执行形态：薄 worker（cucumber 已退役）

进程入口是 `src/bin.mts`——**它本身就是 worker 进程**：装好 loader 与 resolve hook 后直接调 `src/worker/run-scope.mts` 的 `main`，**不 spawn 子 node**（core 用 `pass_fds` 把事件通道 fd 继承给它直接起的那个进程，中间多一层包装就把 fd3 吞了，[ADR 0024](../../docs/adr/0024-worker-core-protocol.md) 三通道）。core 自解析 `.feature`、把每个 step 经 ADR 0024 协议派发进来（[ADR 0022](../../docs/adr/0022-bdd-runner-retired-core-parses-thin-worker.md)），cucumber-js 入口已随 v0.x BDD 层退役删除。

正常经 `gherkai` CLI 跑；也可手动直跑调试——先按下节「从本 checkout 跑」做 `npm ci && npm run build`，再在本目录下跑（`<job json>` 的字段说明与可直接改用的样例见 [ADR 0024](../../docs/adr/0024-worker-core-protocol.md)「输入（core → worker）」一节）：

```bash
echo '<job json>' | AWS_REGION=us-east-1 node dist/bin.mjs

# 两个非 job 入口（不建会话、不跑 job、零 AWS，[ADR 0036](../../docs/adr/0036-deterministic-capability-discovery.md)）——cli 的 `list-deterministic` / `doctor` / run 前置 / plan 标注即转述它们：
node dist/bin.mjs --capabilities                          # 能力自述：{schema_version, engine, min_grace_s, deterministic_steps, model_id}（清单 = 注册表 pattern + description + example）
echo '["页面地址匹配 \"/wiki/OpenAI\""]' | node dist/bin.mjs --match-steps   # 批量问这些 step 各命中什么
```

worker 侧**只有这两个 flag**：确定性清单是 `--capabilities` 对象的 `deterministic_steps` 键，**没有 `--list-deterministic` 入口**（加键不加入口，ADR 0036「5.」）。`min_grace_s` 由 `worker/run-scope.mts` 的收尾各段预算常量算出（`minGraceSeconds()`：在途窗口兜底 + 会话 Stop + 关 browser + 单次上传超时 + 截图队列退出档排空 + `MIN_GRACE_MARGIN_MS`），**不另写字面量**；缺省即 **31** 秒。模型 family 的校验也在入口分派之前，故坏配置在 `--capabilities` 这条 run 前置检查里就被挡下。

引擎特定的 env（worker 侧读）。使用者向的完整 env 清单与「在哪里设才生效」见 [`docs/user-guide/configuration.md`](../../docs/user-guide/configuration.md)——取值的权威在 code 与那一页；下表只补 contributor 要的定位：常量与推断表住哪个文件、下限怎么算出来的。

| env | 缺省 | 作用 |
|---|---|---|
| `MIDSCENE_MODEL_ID` | `us.openai.gpt-5.6-terra`（`lib/agentcore-sigv4.mts` 的 `DEFAULT_MODEL`） | 交给 Midscene SDK 的模型名，同时是 `--capabilities` 的 `model_id`（空串按未设算）；换默认随发版评估（[ADR 0044](../../docs/adr/0044-engine-model-selection-and-override.md) 决策 1，现值登记在该 ADR） |
| `MIDSCENE_MODEL_FAMILY` | 按模型 id 推断 | 覆盖 family 推断（推断表 `MODEL_FAMILY_PATTERNS` 在同一文件，唯一一份）；取值合法性交 SDK 自己拒 |
| `MIDSCENE_RUN_DIR` | 无（SDK 落进程 cwd 下的 `midscene_run`） | Midscene SDK 的 run 根目录（report / dump / log 全在其下），组合根注入绝对路径（子目录名的单一真源是 `runtime/gherkai_runtime/names.py` 的 `ARTIFACT_SUBDIR`） |
| `AWS_REGION` | 无（惰性读，未设即 fail-loud） | SigV4 签名与 base URL 的 region |
| `GHERKAI_EXTRA_HTTP_HEADERS` | 无（未设即零行为变化） | JSON 对象；组合根在 `--expose-local` 档注入，worker 在 browser context 级设为额外请求头（[ADR 0035](../../docs/adr/0035-local-app-testing-via-tunnel.md)） |

## 从本 checkout 跑

```bash
npm ci              # 装依赖（含 devDeps 里的 typescript——build 期需要）
npm run build       # tsc → dist/*.mjs
npm test            # node --import tsx --test "src/**/*.test.mts"（2026-09-17 实跑 183 pass / 0 fail）
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

约定解析（`--steps-dir` > env > `./steps`）在组合根，worker 只认 env `GHERKAI_STEPS_DIR`、不重解析（ADR 0037 决策 4；[ADR 0016](../../docs/adr/0016-execution-architecture-core-lib-run-model.md) 分层）。`src/worker/user-steps.mts` 排序递归遍历 `.mts` / `.mjs`（排除 `_*` 与 `*.test.*`；`_` 判在路径任一段上——`_*` 目录整棵跳过，与 Nova 侧同规则）逐个 `await import`，三条 fail-loud：

- import 失败 → 立刻抛，带文件名与原异常；
- **零注册检查**：某文件加载后注册表条数没涨 → 抛（双实例守卫；症状与两道防线的全景见 [`docs/internals/deterministic-step-lifecycle.md`](../../docs/internals/deterministic-step-lifecycle.md)）。实现约束：`index.mts` 与 worker 自身 import 的必须是同一个 `worker/deterministic.mjs` URL，靠 bin 注册的 resolve hook 保证（见 `resolve-hook.mts` 头注释）。
- **目录本身**：env 已设但目录不存在 / 不是目录 → 进遍历之前就抛。组合根只在目录存在时才注入，走到这里说明提交后目录被移走或路径写错——明确指了一个地方而那里没东西 = 配置错，不是「没定制」（Nova 侧同处理）。

抛出而非自己 `process.exit`：退出码由入口（`bin.mts`）统一落地（非零、且不是 [ADR 0028](../../docs/adr/0028-transient-network-ssl-resilience.md) 的网络专用 80），本模块保持可单测。

内建脚手架 step 在 `src/worker/deterministic.steps.mts`（一条 URL 锚点作范例）；使用方 step 与内建**撞 pattern 不做覆盖**，按 ADR 0036 的 conflict 语义在 `plan` 预检暴露。使用方侧的写法见 [user guide](../../docs/user-guide/writing-deterministic-steps.md)。

## 报告与产物落点

组合根经 `MIDSCENE_RUN_DIR` 注入 run 专属目录（`reports/<run_id>/midscene-run`，**必须绝对路径**：SDK 用 `path.resolve(process.cwd(), …)`），`report.html` 与 log/dump 全在其下；产物经 uploader 传 S3（[ADR 0029](../../docs/adr/0029-engine-artifacts-to-s3.md)），含 act 边界与中断兜底的 report 抢传（best-effort、失败吞+log、不影响退出码）。`--no-report` 档由组合根经 env `GHERKAI_NO_ARTIFACTS=1` 告知：关 agent 的 `generateReport`、不抢传、不带 report ref；SDK 仍可能往 `./midscene_run` 写 log/dump，故此档下若无 `MIDSCENE_RUN_DIR` 就把它导到一次性临时目录、不进用户 CWD。一次 run 的全部产物落点（两引擎横向、local 与 cloud 两档）见 [`docs/internals/artifacts-and-evidence.md`](../../docs/internals/artifacts-and-evidence.md)。

## 跑 spike（五段式自检，可独立跑）

```bash
AWS_REGION=us-east-1 node_modules/.bin/tsx spikes/01-model-sigv4.ts        # 模型连接（SigV4）
AWS_REGION=us-east-1 node_modules/.bin/tsx spikes/02-agentcore-cdp.ts      # 浏览器连接（CDP）
AWS_REGION=us-east-1 node_modules/.bin/tsx spikes/03-midscene-grounding.ts # 合体（grounding）
AWS_REGION=us-east-1 node_modules/.bin/tsx spikes/04-planning-probe.ts     # planning 候选探针（纯文本模型能否当 planner，[ADR 0012](../../docs/adr/0012-planning-shares-qwen3vl-no-text-planner.md)）
AWS_REGION=us-east-1 node_modules/.bin/tsx spikes/05-negative-assertions.ts # 负向断言探针：故意造必假断言，验证失败能被判为失败（防永远绿）
```

## 依赖分类（实测约束）

- **运行时依赖全在 `dependencies`**（`@midscene/web`、`@playwright/test`、`playwright`、各 `@aws-sdk/*`、`@aws-crypto/sha256-js`（SigV4 签名用的 sha256 实现，删了签名即崩）、`openai`、`tsx`）：npm 包的消费者只会装 `dependencies`，留在 `devDependencies` 里的运行时依赖必崩（ADR 0033 记的「不能 `--production`」陷阱在包化后变成必然）。`devDependencies` 只剩 build/类型（`typescript`、`@types/node`）。
- **SDK 与浏览器驱动钉精确版本**（`package.json` 里无 `^`）：`@midscene/web` `1.12.8`、`playwright` 与 `@playwright/test` 同为 `1.63.0`。发行的 npm 包与云端基底镜像都是装包时解析依赖、没有 lock，范围版本会让使用者跑的版本与测过的版本不同（Nova 侧同口径：`nova-act==3.4.187.0`）。升级 = 改 pin → 全套测试 + 评测集真跑 → 随发版点明，见 [ADR 0042](../../docs/adr/0042-step-evidence-and-explain.md) 决策六。其余依赖（各 `@aws-sdk/*`、`@aws-crypto/sha256-js`、`openai`、`tsx`）仍用 `^`。
- `@playwright/test` 是 `@midscene/web` 声明为 optional peer、但 `@midscene/web/playwright` 子入口**无条件 import** 的包——故它也是运行时依赖（真跑打包安装才暴露）。

## 容器镜像（维护者向）

`Dockerfile` = Fargate 档的 worker **基底**镜像（同版本 `@gherkai/worker-midscene` + SDK 运行时 + 协议层，**零使用方内容**）；使用方的定制层模板（`FROM <基底>` + `COPY steps/` + `GHERKAI_STEPS_DIR`）与推送流程见 [ADR 0038](../../docs/adr/0038-worker-image-delivery.md)（包 README 已降为入口页、不再带模板）。

同一份 Dockerfile **两态**，`--build-arg WORKER_SOURCE=` 选（ADR 0037 决策 5）：

- `index`（默认，CI 态）：`--build-arg WORKER_VERSION=X.Y.Z` 从 npm 装已发行包（`npm install -g`）；本态不 COPY，build context 任意。
- `local`（发行前本地验镜像）：装 build context 里 `npm pack` 出的 tarball（下面两条命令**从 repo 根跑**）：

```bash
(cd engines/midscene && npm ci && npm run build && npm pack --pack-destination ../../dist)
docker build --platform linux/amd64 -f engines/midscene/Dockerfile \
  --build-arg WORKER_SOURCE=local --build-arg WORKER_TARBALL=gherkai-worker-midscene-<ver>.tgz \
  -t gherkai-worker-midscene:dev dist/        # context = 放 tarball 的目录
```

真 build 已验证的两条约束：

- **必须 `--platform linux/amd64`**：Fargate task-def 固定 X86_64；arm Mac 不加则 build 出 arm64、容器启动期 `exec format error` 挂死（ADR 0033/0038）。
- **经典 builder（无 buildx）会把未选中的 stage 也跑一遍**，故两个 stage 都对「自己的参数没给」保持容忍（`if [ -n … ]`）；真正的把关在 final stage 的冒烟（`--capabilities`，不需要 AWS），漏 build-arg 在那里 fail-loud、不拖到 Fargate 启动期。

容器入口与 npm bin 同一个（`gherkai-worker-midscene` → `dist/bin.mjs`）：bin 是带 shebang 的文件、内核直接 exec node，**本进程即 worker**、不套包装进程（同上 fd3 理由）。**不装 chromium 二进制**：连的是 AgentCore 云浏览器（`chromium.connectOverCDP(wsUrl)`），playwright 只作 CDP 客户端库。

## 相关 ADR

[0002](../../docs/adr/0002-midscene-not-driven-by-gpt55.md) gpt-5.5 不作主力（Superseded-by 0044）·
[0003](../../docs/adr/0003-midscene-grounding-qwen3vl-bedrock.md) Qwen3-VL 定位（Superseded-by 0044）·
[0008](../../docs/adr/0008-midscene-bedrock-auth-sigv4-selfsign.md) SigV4 自签 ·
[0012](../../docs/adr/0012-planning-shares-qwen3vl-no-text-planner.md) planning 共用同一模型 ·
[0016](../../docs/adr/0016-execution-architecture-core-lib-run-model.md) 执行架构 ·
[0020](../../docs/adr/0020-step-phrasing-default-ai-deterministic-scaffold.md) step 措辞与角色边界 ·
[0022](../../docs/adr/0022-bdd-runner-retired-core-parses-thin-worker.md) 薄 worker ·
[0024](../../docs/adr/0024-worker-core-protocol.md) worker↔core 协议 ·
[0028](../../docs/adr/0028-transient-network-ssl-resilience.md) 网络韧性与退出码 80 ·
[0029](../../docs/adr/0029-engine-artifacts-to-s3.md) 产物上传 ·
[0033](../../docs/adr/0033-iac-aws-backend-and-composition-wiring.md) IaC 与装配 ·
[0035](../../docs/adr/0035-local-app-testing-via-tunnel.md) 本机应用隧道 ·
[0036](../../docs/adr/0036-deterministic-capability-discovery.md) 能力自述 ·
[0037](../../docs/adr/0037-distribution-and-packaging.md) 分发与打包 ·
[0038](../../docs/adr/0038-worker-image-delivery.md) 镜像交付 ·
[0042](../../docs/adr/0042-step-evidence-and-explain.md) step 级证据与 SDK 钉版本 ·
[0044](../../docs/adr/0044-engine-model-selection-and-override.md) 模型选择与覆盖
