# 引擎：怎么选、语言限制、证据填充差异、确定性 step 模板

本文给选引擎与写确定性 step 所需的最小事实，离线也能写。完整写法与安装细节以两引擎的说明页为准：
Nova Act https://github.com/zhiyanliu/gherkai/blob/HEAD/engines/novaact/README.md ，
Midscene https://github.com/zhiyanliu/gherkai/blob/HEAD/engines/midscene/README.md 。

## 1 选择依据

| | Nova Act（`novaact`，默认引擎） | Midscene（`midscene`） |
|---|---|---|
| 被测 UI 语言 | **英文 UI**。非英文页面上能导航、能判页面级语义，但「正文里是否出现某个词」这类断言会系统性判否，投票治不了 | 不限。中文 UI 上动作与 AI 断言实测与英文同级可靠 |
| 本机安装 | `uv tool install 'gherkai[local]'` 与 CLI 同环境；正式发行版还能临时拉起 | `npm i -g @gherkai/worker-midscene`（Node ≥ 22），必须真装 |
| 确定性 step 语言 | Python，`steps/*.py` | TypeScript / JS，`steps/*.mts` 或 `*.mjs` |
| 云端依赖 | Nova Act 服务与模型 nova-act-v1.0（默认钉死，环境变量 NOVA_MODEL_ID 可换）、AgentCore Browser | Bedrock 模型 qwen.qwen3-vl-235b-a22b（默认钉死，环境变量 MIDSCENE_MODEL_ID 可换，家族识别不了时再给 MIDSCENE_MODEL_FAMILY）、AgentCore Browser |

两者都纯 IAM 鉴权、不要 API key；region 要能解析出来（`--region` > `AWS_REGION` > `AWS_DEFAULT_REGION` > profile 配置，四级全空才响亮失败、不猜默认，见 `references/setup-and-diagnosis.md` 第 4 节）；浏览器跑在云端、本机不装 Chromium。

**诊断规则**：Nova 档下非英文页面的断言判否，先排查语言面，再怀疑被测应用。三条出路：scenario 标 `@engine:midscene`（或整批 `--default-engine midscene`）；断言改写成页面级语义陈述（「当前是 X 的词条页」「页面没有报错」）；文本与结构检查改成确定性 step。

## 2 证据字段的引擎填充差异

`explain --json` 的证据 schema 两引擎同形、读法一套，但填充有系统性差异。这些是引擎事实，不是抽取失败；判「这一步有没有判定记录」一律看 `record_missing`，`evidence_missing` 只回答「为什么没读到这一步的机读证据」；别把证据里的 `null` 或空数组读成「没导航 / 没跑 / 证据坏了」。

| 字段 | Nova Act | Midscene |
|---|---|---|
| frame 级 `url` | 有值 | 恒为 null |
| act 级 `time_worked_s` | 有值（SDK 的计费量） | 恒为 null（它的计时是另一种量，不混用） |
| act 抛错时 | `error` 非空、`prompt` 与 `time_worked_s` 仍填，`frames` 为空数组（SDK 不落轨迹） | `error` 非空，`frames` 仍有已完成的帧 |

## 3 确定性 step 最小模板

自然语言步默认交给 AI；「必须精确、不容抖动」的判定写成确定性 step，命中即走你的函数，不问 AI、不投票、可复现。写在**项目自己**的 `steps/` 目录里（不改引擎包）。目录按 `--steps-dir` > 环境变量 `GHERKAI_STEPS_DIR` > `./steps` 解析。

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
    if (!(await page.locator(sel).isVisible())) {
      throw new DeterministicAssertion(`元素 ${sel} 应可见，实际没找到或不可见`);
    }
  },
  { description: "断言选择器命中的元素可见（精确判定，不走 AI）", example: 'Then 元素 "#submit" 可见' },
);
```

共同规则：

- 签名 = `(ctx, 具名组…)`：Nova 是 `handler(ctx, **groups)`，Midscene 是 `(ctx, groups) => …`；`ctx.page` 都是 Playwright 的 Page，具名组 Python 写 `(?P<name>…)`、JS 写 `(?<name>…)`。**Nova 的 handler 必须是同步函数**（不能 `async def`——写成 async 的那一步直接记 error，不会静默通过）；Midscene 的可以是 async 箭头函数（上面示例就是）。要写异步判定，只能落在 Midscene 侧。
- `description` / `example` **必填**：它们就是 `gherkai list-deterministic` 与 `gherkai plan` 打给用例作者看的那两行，缺了启动即报错、点名 pattern。
- 判定映射：Nova 抛 `AssertionError`、Midscene 抛 `DeterministicAssertion`（或 node:assert 的 AssertionError）→ 该步 **failed**；抛其它异常 → **error**。
- 遍历：目录排序递归。两引擎都跳过**以 `_` 开头的文件或目录**（`_selectors.py` / `_pages/` 都算，整棵目录都不加载）——不注册 step 的辅助模块（页面对象、选择器常量、共享 helper）放那里，step 文件相对 import 它照样可用。Nova 只认 `*.py`、另跳过 `test_*.py`；Midscene 只认 `.mts` / `.mjs`（恒为 ESM，与项目 package.json 无关；`.ts` / `.js` 会进 CJS 域、import 直接 SyntaxError）、另跳过 `*.test.*`。
- 内建一条示范锚点 `Then 页面地址匹配 "<正则>"`，两引擎都带，装上即可用。撞上同一 pattern 不做覆盖，按冲突处理。

## 4 两侧成对

同一 feature 要在两个引擎上跑（或团队两引擎都用），每条确定性 step 两侧都要注册：正则语义相同、`description` / `example` 同文，只是方言不同。只写一侧，另一引擎上这一步会静默换回 AI 判定，前置检查不替你发现（它只查本次用到的引擎）。核对法：`gherkai list-deterministic --engine novaact` 与 `gherkai list-deterministic --engine midscene` 各查一遍，再 `gherkai plan` 看标注。

## 5 用错了会怎样（一律响亮失败，不静默降级）

| 情况 | 表现 | 怎么办 |
|---|---|---|
| 注册时缺 `description` / `example` | 启动即报错退出，点名那条 pattern | 补齐元数据 |
| `steps/` 下某个文件 import 失败（语法错、缺依赖、Midscene 用了 `.ts`） | `plan` / `run` / `submit` 在起第一个 job 前整批退 2，点名文件与异常，**不跳过** | 先修那个文件，不是怀疑 feature |
| Midscene 某个 step 文件一条都没注册 | 非 0 退出并点名 | 多半 import 到了第二份 `@gherkai/worker-midscene`，检查项目里有没有另一份 |
| `--steps-dir`（或 `GHERKAI_STEPS_DIR`）指的目录不存在 | 直接退 2：明确指了一个地方而那里没东西 | 改路径；缺省 `./steps` 不存在不算错 |
| 一个 step 文本命中多条 pattern | 该步记 error 并列出撞上的 pattern；`plan` 会提前暴露 | 收窄其中一条正则 |
| 明明写了 `steps/` 却全走 AI | 目录没被读到、或正则与 step 文本不匹配 | 确认 `--steps-dir` 指对；`list-deterministic --steps-dir …` 看清单里有没有你那条；对照 `example` 改 step 文本 |
| `engine_error` 说起 worker 失败 | worker 没装或版本与 CLI 不一致 | 见 `references/setup-and-diagnosis.md` |

## 6 把 steps 带到云端

`--backend cloud` 时 worker 跑在云端容器里、读不到本机 `steps/`，`--steps-dir` 只警告不生效。步骤要烙进一个定制 worker 镜像并 `gherkai deploy push-worker` 推上去，提交时用 `--worker-variant` 选。流程在 `references/cloud-backend.md`。
