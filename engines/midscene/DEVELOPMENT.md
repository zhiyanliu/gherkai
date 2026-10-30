# 开发笔记（contributor）

> 使用者向文档是 [user guide](../../docs/user-guide/README.md)，同目录的 [`README.md`](./README.md) 是它的入口页（内容逐字发布到 npm 包页面）；contributor 的总入口是根 [`CONTRIBUTING.md`](../../CONTRIBUTING.md)。**本文件面向 contributor**，不随包发行（`package.json` 的 `files` 只含 `dist` / `README.md` / `LICENSE`）。

## 包身份

| | |
|---|---|
| 发行名 | `@gherkai/worker-midscene`（npm，public） |
| 命令名 | `gherkai-worker-midscene`（bin = `dist/bin.mjs`） |
| 运行时 | Node ≥ 22，统一 ESM（`"type": "module"`，源码 `.mts` → 产物 `.mjs`） |
| 版本 | 与 CLI（`gherkai`）同版本发行；仓库里是占位 `0.0.0-dev`，发行版本由 CI 在 publish 时写入 |

以 npm 包分发的理由见 [ADR 0037](../../docs/adr/0037-distribution-and-packaging.md) 决策 3。

> **工作目录基线**：本页命令除注明外一律在 `engines/midscene/` 目录下执行（`npm` 脚本、`dist/bin.mjs`、`node_modules/.bin/tsx` 都以此为基准，`tsx` 只装在本目录的 `node_modules/.bin`）。只有「容器镜像」一节的两条命令从 repo 根执行。

## 模型 / 鉴权（无需任何 API key）

不使用 `MIDSCENE_MODEL_API_KEY` bearer，改用进程内 SigV4 自签（复用本机 AWS 默认凭证链，[ADR 0008](../../docs/adr/0008-midscene-bedrock-auth-sigv4-selfsign.md)）：

- 模型：默认 `us.openai.gpt-5.6-terra`（`lib/agentcore-sigv4.mts` 的 `DEFAULT_MODEL`，选定依据 [ADR 0044](../../docs/adr/0044-engine-model-selection-and-override.md)「现值」），env `MIDSCENE_MODEL_ID` 覆盖取值、`MIDSCENE_MODEL_FAMILY` 覆盖家族；缺省 family 按模型 id 推断，推断表是同文件的 `MODEL_FAMILY_PATTERNS`（**唯一一份，不得在别处复制**；决策与理由见 ADR 0044 决策 2），推不出即在 worker 启动期抛错，不回落到任意 family。family 决定 Midscene 用哪套提示词与请求参数，经 `worker/run-scope.mts` 的 `modelConfig()` 交给 SDK。
- base URL：`https://bedrock-runtime.${AWS_REGION}.amazonaws.com/openai/v1`（region 惰性读 `AWS_REGION`，未设即 fail-loud，不硬编码 `us-east-1`；见 `src/lib/agentcore-sigv4.mts` 的 `getRegion()` / `getBaseUrl()`、[ADR 0033](../../docs/adr/0033-iac-aws-backend-and-composition-wiring.md)）
- 接线：经 Midscene `createOpenAIClient` 注入带 SigV4 签名的自定义 `fetch`
- 签名契约与失败模式：[`docs/internals/midscene-bedrock-sigv4-signing.md`](../../docs/internals/midscene-bedrock-sigv4-signing.md)

> **历史事实已变**：2026-06 实测 Bedrock 上的 gpt-5.5 不支持 chat-completions，据此把 GPT 系排除在主力模型之外（[ADR 0002](../../docs/adr/0002-midscene-not-driven-by-gpt55.md)，Status 已 Superseded-by 0044）；2026-09 实查 GPT-5.6 与 GPT-6 经 inference profile 支持 `/openai/v1/chat/completions` 且视觉通道可用，默认因此改为 GPT-5.6 Terra、family 取 `gpt-5`；对 GPT 系的排除结论随之作废。Qwen3-VL 仍是 `MIDSCENE_MODEL_ID` 的可选值（选型历史见 [ADR 0003](../../docs/adr/0003-midscene-grounding-qwen3vl-bedrock.md)）。

## 布局

```
src/
├── bin.mts            ← 唯一入口（npm bin + 容器 CMD）：装 tsx loader + 注册 resolve hook + 调 worker main
├── index.mts          ← 包的公开 API：使用方 step 文件 import 的 { deterministic, DeterministicAssertion, 类型 }
├── resolve-hook.mts   ← 裸 specifier "@gherkai/worker-midscene" → worker 自身安装位置（随 dist 发布的独立入口）
├── worker/            ← 薄 worker：`run-scope.mts`（派发 / 按目标选一次界面接缝 / 事件 / 信号收尾 / 两个非 job 入口的分派）、`surface.mts`（界面接缝的类型契约：五个操作、四项边界义务与执行异常的归类标记，只有 `import type`，[ADR 0052](../../docs/adr/0052-appium-interface-adapter-and-platform-differences.md) 决策 2）、`surface-desktop.mts`（界面接缝的桌面实现：AgentCore 浏览器会话、Playwright 的 CDP 建连、会话预热与会话事件）、`deterministic.mts`（确定性注册表）、`deterministic.steps.mts`（内建脚手架）、`user-steps.mts`（使用方 steps 加载）、`argument.mts`（step 多行参数拼接：DataTable/DocString → 附加文本；两引擎须同一拼法）、`evidence.mts`（step 级机读证据：引擎 dump 裁剪为 evidence.json 供 explain 消费，[ADR 0042](../../docs/adr/0042-step-evidence-and-explain.md)）、`error-text.mts`（失败原因压缩为一行有界文本，与 Nova 的 `_error_text` 规则一致）；本目录下还有各模块的 `*.test.mts` 与测试夹具 `fixtures/`
├── device/            ← 设备模块（Android、iOS 经 Device Farm 与 Appium，按 ADR 0052 决策 3 的职责划分）：`surface.mts`（界面接缝的设备实现：只做编排，各块经端口类型 `DeviceParts` 注入）、`parts.mts`（部件的缺省装配 `defaultDeviceParts`，接缝模块静态 import 它）、`limits.mts`（设备目标的预算常量：超时、次数上限与截断阈值的单一来源，另有重规划上限覆盖键的读取与校验；零 SDK 依赖，能力自述与收尾下限只 import 它）、`session-name.mts`（会话名编码，零 SDK，桌面路径的 StartBrowserSession 请求名同样用它）、`session.mts`（Device Farm 会话：设备解析、Create、等到 RUNNING、查状态、换台、按 Stop 规则停止不再使用的会话（换台时被替换的、获取期按名找回的）；执行期唯一构造 Device Farm 客户端的地方）、`finalize.mts`（终结：两种释放模式与终结四阶段的前三段，与会话块共享同一份会话登记）、`appium.mts`（Appium 建连与上下文切换：建连、执行、探测三个客户端实例）、`web-context.mts`（网页上下文的重新定位）、`probe.mts`（能力探测）、`guard.mts`（命令守卫：执行令牌与结果未知标志）、`interface.mts`（界面实现 `AppiumInterface`、设备 Agent 的构造、驱动适配器的公共面与 `adapterRegistry`）、`adapters/`（驱动适配器 `uiautomator2.mts` 与 `xcuitest.mts`，`mobile:` 命令只出现在这里；`fixtures/` 放两个适配器的命令契约快照与控件树样例）、`warmup.mts`（设备上的会话预热）、`app.mts`（应用启停：安装包存在性检查与预签名、启动采样、`app.restart()`）、`device-session.mts`（会话事件的线上形状与 scope 诊断文件 `device-session.json`）、`wdio-log.mts`（WebdriverIO 自身日志的凭据掩码）；本目录下另有各模块的 `*.test.mts`，以及两条差集护栏 `read-points.test.mts`（读取点与依赖位置）与 `adapters/adapters.contract.test.mts`（命令契约快照）。划分与加载约定见下文「设备模块」节
└── lib/               ← I/O 边缘组件：`job-source.mts`（job 入口）· `event-sink.mts`（事件出口）· `artifact-upload.mts`（产物上传）· `agentcore-sigv4.mts`（SigV4 与模型常量）· `redact.mts`（凭据脱敏，三条规则：URL 中的 userinfo、签名类查询参数与隧道令牌、设备端点路径令牌；后两条的正则对象另供 `device/wdio-log.mts` 生成 WebdriverIO 日志掩码）· `precheck.mts`（建会话前按自己的 targets 核对 job 的目标与墙钟预算）· `tunnel-warmup.mts`（隧道会话预热：与组合根、Nova 侧同值的常量，导航预热地址并按页面结果归因）
dist/                  ← tsc 产物（*.mjs + *.d.mts），发布物；不入库
spikes/                ← 分段自检脚本（不进包、不编译）：01 到 05 为桌面链路（模型连接、浏览器连接、模型与浏览器联合、规划探针、负向断言），06 为移动真机方向的 Device Farm 加 Appium 探针
```

测试都是 `src/**/*.test.mts`，按 tsconfig 的 `exclude` 不进 `dist`。测试位置按模块分两处：**worker 与 lib 的测试在 `src/worker/`**——`lib/` 各模块的测试（`agentcore-sigv4.test.mts` / `artifact-upload.test.mts` / `event-sink.test.mts` / `job-source.test.mts` / `redact.test.mts` / `precheck.test.mts` / `tunnel-warmup.test.mts`）与夹具 `fixtures/` 都落在这里，不另起 `src/lib/*.test.mts`；**设备模块的测试在 `src/device/`**，与所测模块同目录。

## 执行形态：薄 worker（cucumber 已退役）

进程入口是 `src/bin.mts`，**它本身即 worker 进程**：装好 loader 与 resolve hook 后直接调 `src/worker/run-scope.mts` 的 `main`，**不 spawn 子 node**（core 用 `pass_fds` 把事件通道 fd 继承给它直接启动的那个进程，中间多一层包装会导致 fd3 丢失，[ADR 0024](../../docs/adr/0024-worker-core-protocol.md) 三通道）。core 自行解析 `.feature`，把每个 step 经 ADR 0024 协议派发进来（[ADR 0022](../../docs/adr/0022-bdd-runner-retired-core-parses-thin-worker.md)）；cucumber-js 入口已随 v0.x BDD 层退役删除。

正常经 `gherkai` CLI 运行；调试时也可手动直接启动 worker：先按下节「从本 checkout 运行」执行 `npm ci && npm run build`，再在本目录下执行（`<job json>` 的字段说明与可直接改用的样例见 [ADR 0024](../../docs/adr/0024-worker-core-protocol.md)「输入（core → worker）」一节）：

```bash
echo '<job json>' | AWS_REGION=us-east-1 RUN_ID=<本次运行的编号> node dist/bin.mjs

# 两个非 job 入口（不建会话、不执行 job、零 AWS，[ADR 0036](../../docs/adr/0036-deterministic-capability-discovery.md)）；cli 的 `list-deterministic` / `doctor` / run 前置 / plan 标注即转述它们：
node dist/bin.mjs --capabilities                          # 能力自述：{schema_version, engine, min_grace_s, targets, deterministic_steps, model_id, session_warmup}（清单每项 pattern、description、example、keywords、targets）
echo '[{"keyword":"Given","text":"\"https://example.com/\""}]' | node dist/bin.mjs --match-steps   # 批量查询这些 step 各自命中的确定性 pattern（内建导航在表里）
```

worker 侧**只有这两个 flag**：确定性清单是 `--capabilities` 对象的 `deterministic_steps` 键，**没有 `--list-deterministic` 入口**（加键不加入口，ADR 0036「5.」）。`min_grace_s` 由收尾各段的预算常量算出（`worker/run-scope.mts` 的 `minGraceSeconds()`），**不另写字面量**：取两条收尾路径各自之和的较大者、不相加（[ADR 0049](../../docs/adr/0049-worker-capabilities-targets-keys.md) 决策 5）——桌面路径为在途窗口 + 会话 Stop + 关 browser（三者在 `worker/surface-desktop.mts`）+ 单次上传超时 + 截图队列退出段排空 + `MIN_GRACE_MARGIN_MS`，按当前常量为 31 秒；设备路径为终结四阶段的前三段（等在途 Create、终结核对、释放，`device/limits.mts` 的 `deviceGraceSeconds()`）加同一组尾段，为 63.5 秒；`--capabilities` 因此报 **63.5**。模型 family 的校验同样在入口分派之前，因此非法配置在 `--capabilities` 这条 run 前置检查里即被拦下。

下表列出引擎特定的 env（worker 侧读取）。使用者向的完整 env 清单与「在哪里设才生效」见 [`docs/user-guide/configuration.md`](../../docs/user-guide/configuration.md)；取值的权威在 code 与那一页。本表只补 contributor 所需的定位信息：常量与推断表所在文件、下限的计算方式。

| env | 缺省 | 作用 |
|---|---|---|
| `MIDSCENE_MODEL_ID` | `us.openai.gpt-5.6-terra`（`lib/agentcore-sigv4.mts` 的 `DEFAULT_MODEL`） | 交给 Midscene SDK 的模型名，同时是 `--capabilities` 的 `model_id`（空串视为未设）；默认值的更换随发版评估（[ADR 0044](../../docs/adr/0044-engine-model-selection-and-override.md) 决策 1，现值登记在该 ADR） |
| `MIDSCENE_MODEL_FAMILY` | 按模型 id 推断 | 覆盖 family 推断（推断表 `MODEL_FAMILY_PATTERNS` 在同一文件，唯一一份）；取值合法性由 SDK 自行拒绝 |
| `MIDSCENE_RUN_DIR` | 无（SDK 写入进程 cwd 下的 `midscene_run`） | Midscene SDK 的 run 根目录（report / dump / log 全在其下），组合根注入绝对路径（子目录名的单一真源是 `runtime/gherkai_runtime/names.py` 的 `ARTIFACT_SUBDIR`） |
| `AWS_REGION` | 无（惰性读，未设即 fail-loud） | SigV4 签名与 base URL 的 region |
| `RUN_ID` | 无（缺失时接缝构造即报错，worker 在建会话前以 1 退出、不发事件） | 本次运行的编号，编码会话名的 run 段：设备的远程访问会话名与桌面的 StartBrowserSession 请求名都带它（规则在 `device/session-name.mts`，[ADR 0051](../../docs/adr/0051-device-session-lifecycle-and-app-distribution.md) 决策 3、4）；本机由组合根注入，云端由 RunTask overrides 注入（ADR 0024）；有 `EVENTS_DDB_TABLE` 时事件出口也读它 |
| `MIDSCENE_REPLANNING_CYCLE_LIMIT` | 设备目标 12（`device/limits.mts` 的 `DEVICE_REPLANNING_CYCLE_LIMIT`） | Midscene 的重规划上限。读取与校验只有一份，即 `device/limits.mts` 的 `replanningCycleLimit()`：`main` 在读 job 之后、建界面接缝之前调用它一次，非正整数（含空串）即抛出、点名该键，桌面与设备都核对；设备 Agent 的构造项经 `device/surface.mts` 的 `deviceAgentOpts()` 取它的值传入（SDK 的取值是构造项优先于同名 env，传了缺省值就会遮住 env）；桌面不传，由 SDK 按同名 env 自行处理（[ADR 0044](../../docs/adr/0044-engine-model-selection-and-override.md) 决策 2、ADR 0052 决策 6） |
| `GHERKAI_EXTRA_HTTP_HEADERS` | 无（未设即零行为变化） | JSON 对象；组合根在 `--expose-local` 方式下注入，worker 在 browser context 级设为额外请求头（[ADR 0035](../../docs/adr/0035-local-app-testing-via-tunnel.md)） |
| `GHERKAI_SESSION_WARMUP_URL` | 无（未设即不预热） | 隧道会话预热地址；组合根在 `--expose-local` 方式下与 `GHERKAI_EXTRA_HTTP_HEADERS` 一并注入，worker 在第一个 scenario 之前对网页目标导航一次以换取会话 cookie；只有额外请求头而没有预热地址时记 `precheck_failed`、不建会话（[ADR 0051](../../docs/adr/0051-device-session-lifecycle-and-app-distribution.md) 决策 13）；常量与预热逻辑在 `lib/tunnel-warmup.mts` |

## 从本 checkout 运行

```bash
npm ci              # 装依赖（含 devDeps 里的 typescript，build 期需要）
npm run build       # tsc → dist/*.mjs
npm test            # node --import tsx --test "src/**/*.test.mts"
```

改依赖后更新 `package-lock.json` 要用与 CI 相同的 npm 大版本（Node 22 自带的 npm 10；CI 的 Node 版本由 `.github/workflows/ci.yml` 的 `NODE_VERSION` 指定，worker 镜像的由本目录 `Dockerfile` 的 `FROM node:22-slim` 指定，两处同为 22）：本机 npm 更新时执行 `npx npm@10 install --package-lock-only`。更新的 npm 写出的锁，npm 10 可能读不出完整依赖树（出现过嵌套包的依赖列表缺项），CI 的 `npm ci` 会以「package.json 与锁不同步」失败。

让 CLI 指向本 checkout（dev 态没有已安装的 npm 包，走 worker 定位链**第一级** env 覆写，ADR 0037 决策 3）：

```bash
export GHERKAI_WORKER_MIDSCENE_CMD="node $(pwd)/dist/bin.mjs"
# 配套的 GHERKAI_WORKER_MIDSCENE_CWD 一般不需要：bin 在进程内注册 tsx，
# 不再靠 cwd 上溯 node_modules 解析裸 specifier（旧的 `node --import tsx …` 形态才需要）。
```

免 build 的快速迭代形态（改完源码直接运行，已验证）：

```bash
GHERKAI_WORKER_MIDSCENE_CMD="node $(pwd)/src/bin.mts"     # 需 Node ≥ 22.18（原生 type stripping）
```

**`node --import tsx src/bin.mts` 不可用**：`tsx` 是裸 specifier，按**进程 cwd** 上溯 `node_modules` 解析，CLI 从别处启动 worker 时直接 `Cannot find package 'tsx'`（实测）。`node src/bin.mts` 无此问题（bin 自身 import tsx，按文件位置解析）。

## 使用方 `steps/` 的加载（实现要点）

约定解析（`--steps-dir` > env > `./steps`）在组合根，worker 只认 env `GHERKAI_STEPS_DIR`，不重解析（ADR 0037 决策 4；[ADR 0016](../../docs/adr/0016-execution-architecture-core-lib-run-model.md) 分层）。`src/worker/user-steps.mts` 排序递归遍历 `.mts` / `.mjs`（排除 `_*` 与 `*.test.*`；`_` 的判定作用于路径任一段，`_*` 目录整棵跳过，与 Nova 侧同规则）逐个 `await import`，三条 fail-loud：

- import 失败 → 立即抛出，带文件名与原异常；
- **零注册检查**：某文件加载后注册表条数未增加 → 抛出（双实例守卫；症状与两道防线的全景见 [`docs/internals/deterministic-step-lifecycle.md`](../../docs/internals/deterministic-step-lifecycle.md)）。实现约束：`index.mts` 与 worker 自身 import 的必须是同一个 `worker/deterministic.mjs` URL，靠 bin 注册的 resolve hook 保证（见 `resolve-hook.mts` 头注释）。
- **目录本身**：env 已设但目录不存在 / 不是目录 → 在进入遍历之前抛出。组合根只在目录存在时才注入，因此执行到这里说明提交后目录被移走或路径写错：显式指定的目录不存在属于配置错误，而非「未定制」（Nova 侧同处理）。

抛出而非在本模块 `process.exit`：退出码由入口（`bin.mts`）统一落地（非零、且不是 [ADR 0028](../../docs/adr/0028-transient-network-ssl-resilience.md) 的网络专用 80），本模块保持可单测。

内建脚手架在 `src/worker/deterministic.steps.mts`（只有内建导航一条；曾内置的「页面地址匹配」已退役，示范进仓库 `features/steps/`）；使用方 step 与内建 **pattern 冲突时不做覆盖**，按 ADR 0036 的 conflict 语义在用例预检（`plan`）暴露。使用方侧的写法见 [user guide](../../docs/user-guide/writing-deterministic-steps.md)。

## 报告与产物落点

组合根经 `MIDSCENE_RUN_DIR` 注入 run 专属目录（`reports/<run_id>/midscene-run`，**必须绝对路径**：SDK 用 `path.resolve(process.cwd(), …)`），`report.html` 与 log/dump 全在其下；产物经 uploader 上传至 S3（[ADR 0029](../../docs/adr/0029-engine-artifacts-to-s3.md)），含 act 边界与中断时的 report 安全点提前上传（best-effort：失败不抛出、只记日志，不影响退出码）。`--no-report` 方式由组合根经 env `GHERKAI_NO_ARTIFACTS=1` 告知：关闭 agent 的 `generateReport`、不提前上传、不带 report ref；SDK 仍可能往 `./midscene_run` 写 log/dump，故该方式下若无 `MIDSCENE_RUN_DIR`，即把它导向一次性临时目录，不写入用户 CWD。一次 run 的全部产物落点（两引擎横向、local 与 cloud 两个后端）见 [`docs/internals/artifacts-and-evidence.md`](../../docs/internals/artifacts-and-evidence.md)。

## 设备模块（Android、iOS）

设备代码集中在 `src/device/`，按 [ADR 0052](../../docs/adr/0052-appium-interface-adapter-and-platform-differences.md) 决策 3 的职责划分。界面接缝的设备实现 `device/surface.mts` 只做编排：按固定次序调用各块，把它们的结论变成接缝的返回值；各块对它的依赖面写成端口类型，即 `DeviceParts` 的字段，由部件工厂一次装配：

| 职责 | 端口（`DeviceParts` 字段） | 实现 | 决策出处 |
|---|---|---|---|
| Device Farm 会话：设备解析、Create、查状态、Stop、按名列举 | `sessions` | `session.mts` | ADR 0051 决策 2、3 |
| 终结：正常收尾与终结四阶段，每个会话恰一条 `session_closed` | `finalizer` | `finalize.mts`（与会话块是同一份会话登记） | ADR 0051 决策 5 |
| Appium 建连与上下文切换：建连、执行、探测三个客户端实例 | `appium` | `appium.mts`、`web-context.mts` | ADR 0052 决策 3、6 |
| 能力探测 | `probe` | `probe.mts` | ADR 0052 决策 5 |
| 驱动适配器（UiAutomator2、XCUITest） | `adapters` | `adapters/uiautomator2.mts`、`adapters/xcuitest.mts`，经 `interface.mts` 的 `adapterRegistry` 按会话回报的 automationName 选 | ADR 0052 决策 4 |
| 命令守卫：执行令牌与结果未知标志 | `guards` | `guard.mts` | ADR 0052 决策 6 |
| 界面实现与设备 Agent（`AbstractInterface`）；Input 动作带 `autoDismissKeyboard` 为 true 时输入后收起键盘一次，失败只记一行日志 | `agents` | `interface.mts`（Agent 工厂的日志出口必填，缺省装配接部件环境的日志出口） | ADR 0052 决策 7 |
| 会话预热 | `warmup` | `warmup.mts` | ADR 0052 决策 6、ADR 0051 决策 13 |
| 应用启停：存在性检查、预签名、启动采样、`app.restart()` | `appStore`（安装包存储）加 `device/app.mts` 的原语 | `app.mts` | ADR 0051 决策 9、14 |

缺省装配是 `device/parts.mts` 的 `defaultDeviceParts`，接缝每个 scope 装配一次；Device Farm 与 S3 客户端惰性构造，WebdriverIO 实例到建连时才建。`device/surface.test.mts` 经 `DeviceSurfaceOptions.parts` 注入假部件，核对编排次序与各条出口；各块的单测用假客户端与假 driver，不连 AWS、不连设备。离线测试证不到的结论（真机上的命令形态、探测时机、超时与连接池的真实行为）列在下文「真机验收矩阵」节。

加载与读取约定（ADR 0052 决策 3、4、8）：

1. run-scope 按 `job.target.device` 选一次接缝实现（`worker/run-scope.mts` 的 `createSurface`）：桌面实现静态加载，设备实现经 `await import("../device/surface.mjs")` 动态加载。run-scope 对 `device/` 的静态导入只有 `limits.mts`（能力自述与收尾下限），桌面实现另可静态导入 `session-name.mts`；这两个文件都不 import 任何 SDK。
2. WebdriverIO（含 webdriver 与 `@wdio/` 下的包）与 `@aws-sdk/client-device-farm` 的值导入只出现在 `src/device/` 下。`import type` 不受限：它在编译期擦除、运行期不加载，注册面 `worker/deterministic.mts` 的 `import type { Browser } from "webdriverio"` 即属此类。
3. `new DeviceFarmClient` 只出现在 Device Farm 会话块，它是执行期唯一调用 Device Farm SDK 的地方。
4. `mobile:` 命令字面量只出现在 `src/device/adapters/` 下；命令守卫、能力探测与会话预热只调用适配器导出的原语与只读命令名集合。
5. 系统版本与机型只从会话能力对象读取，读出的值只进诊断与 evidence，不作分支条件；设备选择的输入、协议载荷与句柄上下文的透传是三类显式豁免。豁免按声明逐处列出（`device/read-points.test.mts` 的 `VERSION_MODEL_ALLOWED`），除设备选择的输入外，豁免里读出的值只原样透传（按白名单判：填进字段、数组或模板插值，作初值、单独成句的赋值（外面带括号、类型断言或非空断言也算）、返回值，用 `??` 与 `||` 给缺省值，以及存在性判断（直接判断真假，或与 null / undefined 作相等或不等比较；大小比较、`in`、`instanceof` 报红）；括号、类型断言、非空断言与赋值表达式穿过后沿外层再判），参与运算、用作下标、调方法、与非空值比较、按它 switch 或用作 case 标签、交给函数处理等其余写法都报红。另有一条结构差集：会话能力对象只在 Appium 块（`device/appium.mts`）读取。
6. run-scope 的主流程不写按设备的条件分支：差异落在接缝实现里，或由实现返回的数据表达。执行异常的 step 级归类由命令守卫与设备实现挂到异常对象上（`worker/surface.mts` 的 `attachClassification`），runStep 先认这个标记，设备路径因此不会归成 `network_error`；桌面路径只有派发出错的防御分支（句柄不适用于桌面浏览器）带标记，其余异常不带标记、沿用瞬时网络判定。

第 1 条与第 2 条的运行期效果由 `worker/no-device-deps.test.mts` 守：它在真实子进程里执行 `--capabilities` 与一条桌面 job，记录被解析的模块，断言 WebdriverIO（含 webdriver 与 `@wdio/` 下的包）、Device Farm SDK 与 `limits.mts`、`session-name.mts` 之外的设备模块都没有被加载。第 2 到 5 条由 `device/read-points.test.mts` 用语法树扫 `src/` 的非测试源文件做差集（每条带正向对照，检测失效时不会空过）。两个驱动适配器每个原语发出的命令由 `device/adapters/adapters.contract.test.mts` 对照 `adapters/fixtures/<适配器>.commands.json` 的快照核对，改命令须显式改快照（ADR 0052 决策 8）；同一份快照也是真机重新探测工具的对照基准，见下节。

## 真机验收矩阵（人工触发，发版后验证项）

升级 `@midscene/core` 与 `@midscene/web`、升级 `webdriverio`，或 Device Farm 的 Appium 服务端版本变化（`device-session.json` 记录的 Appium 版本与上一轮不同）时，由人触发一轮真机验收，并列入 [CONTRIBUTING](../../CONTRIBUTING.md)「发布与版本」节的发版后验证项。它不进 CI：需要远程访问会话与模型费用，失败要由人判断是平台变化还是用例问题（ADR 0052 决策 8）。在有凭证的机器上同步工作树的做法见 CONTRIBUTING「在有凭证的机器上验证未发布的工作树」；本机后端需在 `gherkai.toml` 的 `[devices]` 给 `project-arn` 与 `app-bucket`，设备按分钟计费。每一行的结论回写所列 ADR 的对应条与「实测依据」节。

同一时机先执行一次真机重新探测工具 `tools/device_reprobe.mts`（用法与判读见 [`tools/device_reprobe.md`](../../tools/device_reprobe.md)）：它经设备侧接缝在一台真机上建会话、记下能力探测的逐项结果，逐个执行两个适配器快照里的原语，把真机拒绝的命令形态、没有执行到的形态与控件树样例里真机没有的属性写成能力矩阵。差集不为空时先按它修适配器与快照，再执行下面的矩阵；改了本工具或快照格式之后，先用它的 `--offline` 方式在本机核对一次。

**基础矩阵**：Android 一台，iOS 取两代系统版本（其中一代为 iOS 26），每台都执行网页目标（Android Chrome、iOS Safari）与应用目标。每一格核对：能力探测结论与坐标比例（`device-session.json`）、AI step 与确定性 step 的判定、导航（网页目标按探测结论选路线，应用目标经 DeepLink）、失败 step 的证据（截图、控件摘要、原始控件树）、每个会话恰有一对 `session_opened` / `session_closed` 且为 confirmed、job 不判 `release_failed`、设备占用时长与服务商计费分钟。

| 单列行 | 做法 | 判据与回写 |
|---|---|---|
| iOS 26 网页目标的整条链路 | 网页上下文探测超时 → 恢复原生上下文 → 经 DeepLink 打开 → 预热标记 READY；同时记录探测实例的网页命令挂住期间，执行实例的原生命令延迟多少；用真机重新探测工具记下首次只读命令超时之后，重试时列上下文与切入各自是否成功 | 整条链路走通；延迟说明 Appium 服务端是否对同一会话串行执行，回写 ADR 0052 决策 5；重试的切入失败时探测判成「探测出错」而不是「不提供」，回写 ADR 0052 决策 5 的判据 |
| 刚建好、尚未导航的 Safari / Chrome 会话是否已有网页上下文候选 | iOS 两代与 Android 各建一次网页目标会话，看探测时的候选数 | 网页上下文本可用的设备被判成「不提供」时，探测改为先经探测实例导航预热地址、再列上下文，回写 ADR 0052 决策 5 |
| 没有 Swipe 动作时模型能否用 Scroll 完成横向翻页 | 应用目标上写一条横向翻页（引导页、轮播）的 AI step | 这一项只在本行确认，不另做单独的真机 spike；不能完成时改为注册 Swipe、原语由驱动适配器的滑动命令实现，回写 ADR 0052 决策 7 |
| Android 应用目标的能力集是否还需要 `appium:appActivity` | Android 应用目标建连并启动被测应用 | 回写 ADR 0052 决策 3 |
| 输入后收起键盘 | 两平台的应用目标与网页目标各写一条要求输入后收起键盘的 AI step；另在键盘未显示时触发一次收起 | 键盘已显示时两平台都能收起，iOS 网页目标在原生上下文发出的命令同样能收起 Safari 的键盘；Android 上 ESC 无效时驱动补发的返回键没有把 Chrome 或被测应用带回上一页；iOS 键盘上没有标识或标签恰为 `done` 的键时能否收起；键盘未显示时记下驱动是否报错与耗时，报错时 worker 日志恰记一行、判定不变；结论回写 ADR 0052 决策 4、7 |
| 会话预热的三个失败分支 | 设备网页目标经本机应用隧道，分别让边缘节点拒收 cookie、让校验返回 401、让预热请求失败 | 前两种归 `precheck_failed`，请求失败在重试耗尽后归 `engine_error`，都不归 `network_error`（ADR 0051 决策 13） |

**故障演练**：

| 场景 | 做法 | 判据与回写 |
|---|---|---|
| 停止信号落在各阶段 | 分别在 Create 在途、会话排队中（PENDING_CONCURRENCY）、释放阶段网络退化时停止 run；另在正常收尾的 `deleteSession` 发出之前与在途时各停止一次 | 每个会话恰一条 `session_closed`，`doctor --backend cloud` 的 `backend.devices.sessions` 没有遗留；终结四阶段在 Fargate 停止宽限内收完，63.5 秒的下限是否够用按网络退化的实测校准 ADR 0051 决策 5；正常收尾中途停止的两次，尚未发出的 `deleteSession` 不再发出、`device-session.json` 交给退出前的队列排空、在预算内尽力上传（预算内没传完时，本机后端留在本地产物目录） |
| 会话中途丢失 | 外部停止会话；另用测试构建注入较小的会话年龄上限，触发年龄后备 | 当前 step 记 error、本 scenario 余下 step 为 skipped、scope 归 `session_lost`，后续 scenario 由 core 标为 skipped（ADR 0051 决策 4） |
| 命令结果未知 | 让一条点击或输入命令在客户端超时 | 命令不被重复执行；下一条 scenario 开始前的截图存活探测按会话状态分流（ADR 0052 决策 6、ADR 0051 决策 12） |
| 进程级兜底 | 让 newSession 的客户端超时以未处理的 Promise 拒绝形式出现 | worker 记录后进入终结，会话不泄漏（ADR 0051 决策 5） |
| 脱敏 | 故意让建连失败一次；会话执行中外部停止一次（WebdriverIO 报 `UND_ERR_CLOSED`） | stderr（含 WebdriverIO 自身的日志）、事件、evidence、`device-session.json` 与原始控件树里的签名与端点令牌都已盖住（ADR 0051 决策 11） |

## 运行 spike（分段自检，可独立运行）

```bash
AWS_REGION=us-east-1 node_modules/.bin/tsx spikes/01-model-sigv4.ts        # 模型连接（SigV4）
AWS_REGION=us-east-1 node_modules/.bin/tsx spikes/02-agentcore-cdp.ts      # 浏览器连接（CDP）
AWS_REGION=us-east-1 node_modules/.bin/tsx spikes/03-midscene-grounding.ts # 模型与浏览器联合（grounding）
AWS_REGION=us-east-1 node_modules/.bin/tsx spikes/04-planning-probe.ts     # planning 候选探针（纯文本模型是否可作 planner，[ADR 0012](../../docs/adr/0012-planning-shares-qwen3vl-no-text-planner.md)）
AWS_REGION=us-east-1 node_modules/.bin/tsx spikes/05-negative-assertions.ts # 负向断言探针：构造必假断言，验证失败可被判为失败（防止永远绿）
```

`spikes/06-devicefarm-appium.mts` 是移动真机方向的探针，也是设备模块的原型，需要 Device Farm 项目与真机，设备按分钟计费；运行命令与可选环境变量写在该文件开头的注释里。其中几处写法是 ADR 0052 的被拒方案（以 `Promise.race` 放弃挂住的探测命令、输入在运行期多路线试错回落、滚动失败后回落到 W3C 指针拖动、按 `PLATFORM` 与 `SCENARIO` 全局变量分支、比例回退不取整且窗口尺寸不取自 page source 根节点、单个客户端实例、日志级别 `warn` 与缺省的传输层重试），设备模块借用它的原语时不照搬这些写法。spike 不在 `tsc` 的编译范围内（tsconfig 只含 `src/`），却 import 了 `src/` 的接口（如 `worker/evidence.mts` 的 `buildEvidence`）：改这些接口时同步改 spike，并用下面的命令核对它仍能通过类型检查：

```bash
npx tsc --ignoreConfig --noEmit --module nodenext --moduleResolution nodenext --target es2022 --types node \
  --skipLibCheck --strict --exactOptionalPropertyTypes false --esModuleInterop spikes/06-devicefarm-appium.mts
```

## 依赖分类（实测约束）

- **运行时依赖全在 `dependencies`**（`@midscene/web`、`@midscene/core`（设备模块直接使用它的 `Agent` 与 `AbstractInterface`，[ADR 0052](../../docs/adr/0052-appium-interface-adapter-and-platform-differences.md) 决策 7）、`@playwright/test`、`playwright`、各 `@aws-sdk/*`（含设备模块执行期调用的 `@aws-sdk/client-device-farm`）、`@aws-crypto/sha256-js`（SigV4 签名所用的 sha256 实现，缺失则签名不可用）、`openai`、`tsx`、`webdriverio`（设备模块的 WebDriver 客户端；注册面发布的类型声明也引用它，ADR 0050 决策 2））：npm 包的消费者只会装 `dependencies`，留在 `devDependencies` 里的运行时依赖必然在使用方环境失败（ADR 0033 记录的「不能 `--production`」陷阱在包化后成为必然）。`devDependencies` 只有 build 与类型所用的包（`typescript`、`@types/node`）。设备依赖装上不等于被加载：桌面路径与 `--capabilities` 不加载 WebdriverIO 与 Device Farm SDK（ADR 0052 决策 3），所以镜像冒烟另有一条只 import 设备接缝模块的检查（见本目录 `Dockerfile`），否则依赖缺失要到云端第一个设备 job 才暴露。设备接缝模块静态 import 缺省装配 `device/parts.mts`，后者再静态带到 WebdriverIO 与 Device Farm SDK，这条冒烟因此拦得住两项依赖没装进镜像；这条静态闭包由 `device/surface.test.mts` 守，改装配方式时不能把它断开。
- **SDK 与浏览器驱动锁定精确版本**（`package.json` 里无 `^`）：`@midscene/web` 与 `@midscene/core` 同为 `1.15.1`、`playwright` 与 `@playwright/test` 同为 `1.63.0`、`webdriverio` `10.0.2`、`@wdio/logger` `10.0.0`。发行的 npm 包与云端基础镜像都是装包时解析依赖、没有 lock，范围版本会使使用者运行的版本与验证过的版本不同（Nova 侧规则相同：`nova-act==3.4.187.0`、`bedrock-agentcore==1.22.0`）。升级的步骤是改 pin → 全套测试 + 模型评测集实际运行 → 随发版说明，见 [ADR 0042](../../docs/adr/0042-step-evidence-and-explain.md) 决策六；`webdriverio` 另有一条：设备模块的超时、重试与连接池共享结论都依据 10.0.2 的源码行为，升级须先过真机验收（ADR 0052 决策 7、8）。`@wdio/logger` 本是 webdriver 的传递依赖，显式声明是因为 `src/device/wdio-log.mts` 直接 import 它来装 WebdriverIO 日志的凭据掩码：掩码 API 按 logger 名设置、装在该包的模块级状态上，本包解析到的必须与 webdriver 用的是同一个模块实例，所以锁定为 webdriver `10.0.2` 所依赖的同一版本，随 `webdriverio` 一起升级（ADR 0051 决策 11、ADR 0052 决策 7）。设备依赖的分类、`@midscene/core` 与 `@midscene/web` 同版本、`webdriverio` 的精确版本、`@wdio/logger` 与 webdriver 所依赖的版本一致且锁文件里不另嵌一份，由 `src/worker/no-device-deps.test.mts` 核对（含锁文件与 `package.json` 同步）。其余依赖（各 `@aws-sdk/*`、`@aws-crypto/sha256-js`、`openai`、`tsx`）仍用 `^`。
- `@playwright/test` 是 `@midscene/web` 声明为 optional peer、但 `@midscene/web/playwright` 子入口**无条件 import** 的包，因此它也是运行时依赖（打包安装后实际运行才暴露）。

## 容器镜像（面向发布方）

`Dockerfile` 构建的是云端后端（Fargate）的 worker **基础镜像**（同版本 `@gherkai/worker-midscene` + SDK 运行时 + 协议层，**零使用方内容**）；使用方的定制层模板（`FROM <基础镜像>` + `COPY steps/` + `GHERKAI_STEPS_DIR`）与推送流程见 [ADR 0038](../../docs/adr/0038-worker-image-delivery.md)（包 README 已降为入口页、不再带模板）。

同一份 Dockerfile 有**两态**，由 `--build-arg WORKER_SOURCE=` 选择（ADR 0037 决策 5）：

- `index`（默认，CI 态）：以 `--build-arg WORKER_VERSION=X.Y.Z` 从 npm 安装已发行包（`npm install -g`）；本态不 COPY，build context 任意。
- `local`（发行前本地验证镜像）：安装 build context 里 `npm pack` 产出的 tarball（下面两条命令**从 repo 根执行**）：

```bash
(cd engines/midscene && npm ci && npm run build && npm pack --pack-destination ../../dist)
docker build --platform linux/amd64 -f engines/midscene/Dockerfile \
  --build-arg WORKER_SOURCE=local --build-arg WORKER_TARBALL=gherkai-worker-midscene-<ver>.tgz \
  -t gherkai-worker-midscene:dev dist/        # context = 放 tarball 的目录
```

真 build 已验证的两条约束：

- **必须 `--platform linux/amd64`**：Fargate task-def 固定 X86_64；arm Mac 上不加则 build 出 arm64，容器启动期报 `exec format error`、无法启动（ADR 0033/0038）。
- **经典 builder（无 buildx）会把未选中的 stage 一并执行**，故两个 stage 都对「自身参数未给」保持容忍（`if [ -n … ]`）；真正的校验点在 final stage 的两条冒烟：`--capabilities`（不需要 AWS）在 build-arg 漏给时 fail-loud，不延后到 Fargate 启动期；另一条只 import 已安装包的 `dist/device/surface.mjs`、不调用任何导出（零 AWS 调用），拦住设备依赖没装进镜像——`--capabilities` 按设计不加载设备模块，照不出这一类缺失。

容器入口与 npm bin 同一个（`gherkai-worker-midscene` → `dist/bin.mjs`）：bin 是带 shebang 的文件，内核直接 exec node，**本进程即 worker**，不额外套包装进程（同上 fd3 理由）。**不安装 chromium 二进制**：连接的是 AgentCore 云浏览器（`chromium.connectOverCDP(wsUrl)`），playwright 只作 CDP 客户端库。

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
[0042](../../docs/adr/0042-step-evidence-and-explain.md) step 级证据与 SDK 版本锁定 ·
[0044](../../docs/adr/0044-engine-model-selection-and-override.md) 模型选择与覆盖 ·
[0049](../../docs/adr/0049-worker-capabilities-targets-keys.md) 能力自述增键 ·
[0050](../../docs/adr/0050-deterministic-step-handles-and-testing.md) 确定性 step 的句柄 ·
[0051](../../docs/adr/0051-device-session-lifecycle-and-app-distribution.md) 远程访问会话的生命周期 ·
[0052](../../docs/adr/0052-appium-interface-adapter-and-platform-differences.md) Appium 界面适配与平台差异
