# 引擎：怎么选、语言限制、证据填充差异、确定性 step 模板

本文给选引擎与写确定性 step 所需的最小事实，离线也能写；把 step 代码写稳、写得能诊断、写得能单测，见 `references/deterministic-steps.md`。完整写法以用户指南为准：
确定性 step（两引擎并排） https://github.com/zhiyanliu/gherkai/blob/HEAD/docs/user-guide/writing-deterministic-steps.md ，
安装与前置 https://github.com/zhiyanliu/gherkai/blob/HEAD/docs/user-guide/getting-started.md 。

## 1 选择依据

| | Nova Act（`novaact`，默认引擎） | Midscene（`midscene`） |
|---|---|---|
| 被测 UI 语言 | **英文 UI**。非英文页面上能导航、能判页面级语义，但「正文里是否出现某个中文词」这类文本包含断言会系统性判否（同一页面上的英文词仍可靠），增加投票也无法纠正 | 不限。中文 UI 上的动作与 AI 断言和在英文 UI 上同样可靠 |
| 本机安装 | `uv tool install 'gherkai[local]'` 与 CLI 同环境；正式发行版还能临时拉起 | `npm i -g @gherkai/worker-midscene`（Node ≥ 22），必须实际安装 |
| 确定性 step 语言 | Python，`steps/*.py` | TypeScript / JS，`steps/*.mts` 或 `*.mjs` |
| 测试目标 | 桌面网页 | 桌面网页，Android 与 iOS 真机上的网页与原生应用（第 7 节） |
| 云端依赖 | Nova Act 服务与模型 nova-act-v1.0（默认锁定，环境变量 NOVA_MODEL_ID 可换）、AgentCore Browser | Bedrock 模型 us.openai.gpt-5.6-terra（默认锁定，环境变量 MIDSCENE_MODEL_ID 可换，家族识别不了时再给 MIDSCENE_MODEL_FAMILY）、AgentCore Browser |

两者都纯 IAM 鉴权、不要 API key；region 要能解析出来（解析顺序见 `references/setup-and-diagnosis.md` 第 4 节；哪一处都没有就报错，不采用默认值）；浏览器运行在云端、本机不装 Chromium。

**诊断规则**：Nova Act 引擎下非英文页面的断言判否，先排查语言面，再怀疑被测应用。三条出路：scenario 标 `@engine:midscene`（或整个 run 用 `--default-engine midscene`）；断言改写成页面级语义陈述（「当前是 X 的词条页」「页面没有报错」）；文本与结构检查改成确定性 step。

## 2 证据字段的引擎填充差异

`explain --json` 的证据 schema 两引擎结构相同、读法一套，但填充有系统性差异。这些是引擎事实，不是抽取失败；判「这一步有没有判定记录」一律看 `record_missing`，`evidence_missing` 只回答「为什么没读到这一步的机读证据」；别把证据里的 `null` 或空数组读成「没导航 / 没运行 / 证据坏了」。

| 字段 | Nova Act | Midscene |
|---|---|---|
| frame 级 `url` | 有值 | 恒为 null |
| act 级 `time_worked_s` | 有值（SDK 的计费量） | 恒为 null（它的计时是另一种量，不混用） |
| act 抛错时 | `error` 非空、`prompt` 与 `time_worked_s` 仍填，`frames` 为空数组（SDK 不落轨迹） | `error` 非空，`frames` 仍有已完成的帧 |

## 3 确定性 step 最小模板

自然语言步默认交给 AI；「必须精确、不容抖动」的判定写成确定性 step，命中即走你的函数，不问 AI、不投票、可复现。写在**项目自己**的 `steps/` 目录里（不改引擎包）。目录按 `--steps-dir` > 环境变量 `GHERKAI_STEPS_DIR` > 配置文件的 `steps-dir`（相对配置文件所在目录）> `./steps` 解析。

Nova Act（`steps/login.py`）：

```python
from gherkai_worker_novaact.deterministic import deterministic


@deterministic(r'以 "(?P<user>[^"]+)" 登录',
               description="确定性填表登录（不走 AI）",
               example='Given 以 "alice" 登录')
def login(ctx, user):
    ctx.page.fill("#user", user)      # ctx.page 就是 Playwright 的 Page
    ctx.page.click("#submit")
```

Midscene（`steps/login.mts`）：

```ts
import { deterministic, DeterministicAssertion } from "@gherkai/worker-midscene";

deterministic(
  '元素 "(?<sel>[^"]+)" 可见',
  async ({ page }, { sel }) => {
    try {
      await page.locator(sel).waitFor({ state: "visible", timeout: 5000 });   // 带等待，不读瞬时值
    } catch (e) {
      throw new DeterministicAssertion(`元素 ${sel} 应可见但没有（页面 ${page.url()}）`);  // 超时转成断言失败，带现场
    }
  },
  { description: "断言选择器命中的元素可见（精确判定，不走 AI）", example: 'Then 元素 "#submit" 可见' },
);
```

共同规则：

- webdriver 句柄（设备目标）的 ctx 有七个字段：`driver`（WebdriverIO 客户端，step 结束后不可再用）、`device`（platform / osVersion / scale）、`uiKind`、`appId` 与 `app`（只在应用目标上有值，`app.restart()` 重启被测应用）、`log`、`withWebContext(fn)`（切进被测对象的网页上下文执行、结束后切回）；step 结束时会话须处在原生上下文。Nova Act 没有设备路径，Python 侧的 webdriver 条目只进清单、不被调用。
- 签名为 `(ctx, 具名组…)`：Nova 是 `handler(ctx, **groups)`，Midscene 是 `(ctx, groups) => …`；`ctx.page` 都是 Playwright 的 Page，具名组 Python 写 `(?P<name>…)`、JS 写 `(?<name>…)`。**Nova 的 handler 必须是同步函数**（不能 `async def`——写成 async 的那一步直接记 error，不会静默通过）；Midscene 的可以是 async 箭头函数（上面示例就是）。要写异步判定，只能落在 Midscene 侧。
- `description` / `example` **必填**：它们就是 `gherkai list-deterministic` 的「示例」「说明」两列与 `gherkai plan` 命中标注里的那句说明，缺了启动即报错、点名 pattern。
- 判定映射：Nova 抛 `AssertionError`、Midscene 抛 `DeterministicAssertion`（或 node:assert 的 AssertionError）时该步判 **failed**；抛其它异常时判 **error**。
- 遍历：目录排序递归。两引擎都跳过**以 `_` 开头的文件或目录**（`_selectors.py` / `_pages/` 都算，整棵目录都不加载）——不注册 step 的辅助模块（页面对象、选择器常量、共享 helper）放那里，step 文件相对 import 它照样可用。Nova 只认 `*.py`、另跳过 `test_*.py`；Midscene 只认 `.mts` / `.mjs`（恒为 ESM，与项目 package.json 无关；`.ts` / `.js` 在收集阶段就被跳过——不 import、不报错、清单里没有）、另跳过 `*.test.*`。
- 可选 `keywords` 声明这条 step 接受的关键字（Nova `keywords=("Then",)`、Midscene `keywords: ["Then"]`，缺省三个都接受）；命中了模式而关键字不符的步记 error、不转 AI。断言类 step 声明只接受 `Then`。
- 引擎只内建一条确定性 step：导航（`Given` / `When` 后整句是一个地址），它在清单与 `plan` 标注里与其它条目一样出现、只接受 `Given` / `When`。判定类 step 一律由项目注册，注册了同一个模式不做覆盖，按冲突处理。地址核对的现成模板（两侧成对的 `Then 页面地址匹配 "<正则>"`）与 Midscene 侧重启被测应用的模板（`Given 重新启动应用`，只有应用目标上的实现）在 https://github.com/zhiyanliu/gherkai/tree/HEAD/features/steps ，复制进项目 `steps/` 即可。

## 4 两侧成对

同一 feature 要在两个引擎上运行（或团队两引擎都用），每条确定性 step 两侧都要注册：正则语义相同、`description` / `example` 同文，只是方言不同。只写一侧，另一引擎上这一步会静默换回 AI 判定，执行前预检不替你发现（它只查本次用到的引擎）。核对法：`gherkai list-deterministic --engine novaact` 与 `gherkai list-deterministic --engine midscene` 各查一遍，再 `gherkai plan` 看标注。

## 5 用错了会怎样（一律响亮失败，不静默降级）

| 情况 | 表现 | 怎么办 |
|---|---|---|
| 注册时缺 `description` / `example` | 启动即报错退出，点名那条 pattern | 补齐元数据 |
| `steps/` 下某个文件 import 失败（语法错、缺依赖、Midscene 用了 `.ts`） | `plan` / `run` / `submit` 在起第一个 job 前整个 run 以退出码 2 结束，点名文件与异常，**不跳过** | 先修那个文件，不是怀疑 feature |
| Midscene 某个 step 文件一条都没注册 | 非 0 退出并点名 | 多半 import 到了第二份 `@gherkai/worker-midscene`，检查项目里有没有另一份 |
| `--steps-dir`（或 `GHERKAI_STEPS_DIR`、配置文件的 `steps-dir`）指的目录不存在 | 直接以退出码 2 结束：明确指了一个地方而那里没东西 | 改路径；缺省 `./steps` 不存在不算错 |
| 一个 step 文本命中多条 pattern | 该步记 error 并列出同时命中的 pattern；`plan` 会提前暴露 | 收窄其中一条正则 |
| 明明写了 `steps/` 却全走 AI | 目录没被读到、或正则与 step 文本不匹配 | 确认 `--steps-dir` 指对；`list-deterministic --steps-dir …` 看清单里有没有你那条；对照 `example` 改 step 文本 |
| `engine_error` 说起 worker 失败 | worker 没装或版本与 CLI 不一致 | 见 `references/setup-and-diagnosis.md` |

## 6 把 steps 带到云端

`--backend cloud` 时 worker 运行在云端容器里、读不到本机 `steps/`，`--steps-dir`（配置文件给的 `steps-dir` 同样）只警告不生效。步骤要构建进一个定制 worker 镜像并 `gherkai deploy push-worker` 推上去，提交时用 `--worker-variant` 选。流程在 `references/cloud-backend.md`。

## 7 设备目标（Android / iOS 真机）

只有 Midscene 支持设备目标，落到 Nova Act 的设备 scope 在 `plan` 与执行前被拒；本机 worker 实际支持什么，以 `gherkai doctor` 的 `engines.targets.<引擎>` 行为准（设备目标后附会话上限的分钟数）。

- **声明**：scope 标 `@device:android` 或 `@device:ios` 并标 `@engine:midscene`，测设备上的浏览器（Android 的 Chrome、iOS 的 Safari）；再标 `@app:<别名>` 测原生应用，别名在 `gherkai.toml` 的 `[apps.<别名>.<平台>]` 绑定安装包与包名或 bundle id。
- **设备选择**：不自动挑设备。按平台用 `--android-device-arn` / `--ios-device-arn`，或 `gherkai.toml` 的 `[devices.android]` / `[devices.ios]` 给设备 ARN（键 arn）或系统版本（键 `os-version`）；没有任何来源时 `run` / `submit` 以退出码 2 结束、`plan` 只警告。本机后端另要 Device Farm 项目（`--device-farm-project-arn` 或 `[devices]` 的 `project-arn`），应用目标还要放安装包的桶（`--app-bucket` 或 `[devices]` 的 `app-bucket`）；云端后端用部署时建立的项目。
- **费用**：一个设备 scope 一个远程访问会话，按设备分钟计费，设备的准备时间（创建到可用，约 1 到 2.5 分钟）与停止后的收尾都计入。`plan --json` 的 `device_session_count` 就是这次要开的会话数，首次运行前把它与设备选择一起报给人。
- **写法差异**：同一 scope 的 scenario 之间不重启应用，需要干净起点时在 `Background` 写一条重启应用的确定性 step（第 3 节末的模板）。导航步在网页目标上打开地址，在应用目标上把地址经 DeepLink 交给被测应用（Android 上地址里的 `;`、`'`、`(`、`)` 或空格、非 ASCII 字符要先百分号编码），后面照样紧跟一条落点核对。确定性 step 在设备上调用的是 webdriver 实现（第 3 节的七个字段）；只有 playwright 实现的 step 在设备上交给 AI，`gherkai plan` 会注明。
- **证据**：设备上判为 failed / error 的确定性与导航 step 也有证据（`acts` 为空），另带 `step_kind`、`url` / `url_missing`，失败 step 还有 `controls` 与 `page_source`，字段读法见 `references/cli-json-contract.md`；设备 job 的 `device_session` 链接指向这个 scope 的诊断文件 `device-session.json`（能力探测结论、所用会话与设备、换台记录与各阶段时刻），只给链接、不解析。
- **错误类别**：`precheck_failed`、`acquire_timeout`、`session_lost`、`capability_unavailable` 的处置见 `references/setup-and-diagnosis.md` 第 7 节的表。
