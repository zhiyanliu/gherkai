# @gherkai/worker-midscene

gherkai 的 **Midscene 执行引擎**：把 `.feature` 里的每个 step 在**云端浏览器**（Amazon Bedrock AgentCore Browser）上真跑一遍——自然语言 step 交给 **Qwen3-VL 235B on Bedrock** 看图定位并操作，你自己写的确定性 step 用 Playwright 精确判定。

它是一个被 `gherkai` CLI 拉起并驱动的 **worker 进程**：日常你敲的是 `gherkai run` / `gherkai submit`，**不用直接调用本包的命令**。装上它 = 让 `gherkai` 能在本机用 midscene 引擎跑起来。

## 安装

```bash
npm i -g @gherkai/worker-midscene      # 需 Node ≥ 22
```

CLI 在 PATH 上找 `gherkai-worker-midscene` 命令（`npm i -g` 的结果）；要指向自建或本地构建，用环境变量 `GHERKAI_WORKER_MIDSCENE_CMD`（+ 可选 `GHERKAI_WORKER_MIDSCENE_CWD`）显式覆写。本 worker 与 CLI 版本同号锁定，**必须真装**（没有临时拉起的兜底）；没装时 `gherkai run` / `gherkai list-deterministic` 退 2 并打印装法。

## AWS 前置

- **纯 IAM 鉴权**：进程内 SigV4 自签，复用本机 AWS 默认凭证链（profile / 环境变量 / 实例角色皆可）。**不需要任何 API key**（无 bearer token）。
- **region 必须显式给**：`AWS_REGION`，或 `gherkai run --region <R>`；未设即报错，不猜默认 region。
- 该 region 下账号需可用：**Bedrock 模型** `qwen.qwen3-vl-235b-a22b`（视觉定位大脑），以及 **AgentCore Browser**（`bedrock-agentcore`）。浏览器跑在云端，本机**不需要装 Chromium**。

## 写确定性 step（`steps/*.mts`）

自然语言 step 默认交给 AI；「必须精确、不容抖动」的判定（URL、关键 DOM……）写成确定性 step——命中即走你的函数，不问 AI、可复现。写在你**自己项目**的 `steps/` 目录里（不改本包源码）：

```ts
// steps/login.mts
import { deterministic, DeterministicAssertion } from "@gherkai/worker-midscene";

deterministic(
  '元素 "(?<sel>[^"]+)" 可见',                    // 具名组 (?<name>...) = handler 收到的 groups
  async ({ page }, { sel }) => {                  // page = Playwright Page；不投票、可复现
    if (!(await page.locator(sel).isVisible())) {
      throw new DeterministicAssertion(`元素 ${sel} 应可见，实际没找到或不可见`);
    }
  },
  { description: "断言选择器命中的元素可见（精确判定，不走 AI）", example: 'Then 元素 "#submit" 可见' },
);
```

- 签名 `(ctx, groups) => void | Promise<void>`：`ctx.page` 是 Playwright `Page`，`groups` = 正则具名组的对象。
- **扩展名只认 `.mts` / `.mjs`**：这两个恒为 ESM，与你项目里有没有 `package.json`、`type` 写什么无关（`.ts` / `.js` 会落进 CJS 域、`import` 直接 SyntaxError）。
- `description` / `example` **必填**——它们就是 `gherkai list-deterministic` 与 `gherkai plan` 打给用例作者看的那两行，缺了启动即报错。
- 判定失败抛 `DeterministicAssertion`（或 `node:assert` 的 `AssertionError`）→ 该 step 记 **failed**；抛其它 → 记 **error**。
- 目录**排序递归**遍历，`*.test.*` 跳过。
- 本包内建一条示范锚点 `页面地址匹配 "<正则>"`，装上即可在 `.feature` 里直接写 `Then 页面地址匹配 "/wiki/OpenAI"`。撞上同一 pattern **不做覆盖**，按冲突处理（见下表）。

目录怎么告诉 CLI：`gherkai run --steps-dir ./steps`（`run` / `submit` / `plan` / `list-deterministic` 四处都有此选项），缺省 `./steps`。

### 用错了会怎样（一律响亮失败，绝不静默降级）

| 情况 | 表现 |
|---|---|
| 注册时缺 `description` / `example` | 启动即报错退出，点名那条 pattern |
| 某个 step 文件 import 失败（语法错、缺依赖、用了 `.ts`……） | worker 非 0 退出并点名该文件——**不跳过**（跳过等于把确定性判定悄悄换回 AI，run 还可能「通过」） |
| 某个 step 文件**一条都没注册** | 同样非 0 退出并点名。多半是它 `import` 的不是本包（解析到了第二份副本）——检查你项目里有没有另一份 `@gherkai/worker-midscene` |
| `--steps-dir`（或 `GHERKAI_STEPS_DIR`）指的目录不存在 | 直接退 **2** 并说明：明确指了一个地方而那里没东西 = 配置错。（缺省的 `./steps` 不存在**不算错**） |
| 一个 step 文本命中多条 pattern | 该 step 记 error 并列出撞上的 pattern；`gherkai plan` 会提前把冲突暴露出来 |

## 查有哪些确定性 step

```bash
gherkai list-deterministic --engine midscene --steps-dir ./steps   # 人读清单（pattern + 说明 + 可抄的示例）
gherkai list-deterministic --engine midscene --json                # 机器可读
gherkai plan features/                                             # 每个 step 会走确定性还是 AI
```

两者都不建浏览器会话、不调模型，**不产生 AWS 费用**。

## 把 steps 带到云端

`--backend cloud` 时 worker 跑在 Fargate 容器里、读不到你本机的 `steps/`——把它烙进一个定制镜像（三行）：

```dockerfile
FROM ghcr.io/zhiyanliu/gherkai-worker-midscene:<你的 CLI 版本>
COPY steps/ /app/steps
ENV GHERKAI_STEPS_DIR=/app/steps
```

```bash
docker build --platform linux/amd64 -t acme-midscene:login .
```

> ⚠️ **必须 `--platform linux/amd64`**：在 arm Mac 上漏了会 build 出 arm64 镜像，容器**启动期** `exec format error` 挂死，现象离原因很远。

推送、选用（`--worker-variant`）与默认指针见部署方文档 https://github.com/zhiyanliu/gherkai/blob/HEAD/deploy_aws/README.md 。

## 报告与产物

Midscene 每个 worker 出一份 `report.html`（可视化回放：每步的截图、定位框与模型判断）：

- `--backend local`：落 `reports/<run_id>/midscene-run/`，run 报告里带引用。
- `--backend cloud`：随 run 传到 S3（中途被打断也会尽力抢传已写出的那份），`gherkai status` 给出引用。
- `--no-report`：**不生成、不上报**引擎原生产物（引擎自己可能写的 log/dump 落一次性临时目录，不进你的工作目录）。

## 退出码与常见错误

日常看 CLI 的退出码即可；直接跑 worker 时：`0` 正常、非 0 表示装配/执行失败（steps 加载失败即在此列）、`80` 连云端浏览器的重试耗尽（网络或额度问题——换 region 或稍后重试）。

| 你看到 | 怎么办 |
|---|---|
| `engine_error: 起 worker 失败` | worker 没装或版本与 CLI 不一致：`npm i -g @gherkai/worker-midscene`（Node ≥ 22） |
| `import` 你的 step 文件时 `SyntaxError` | 文件扩展名改成 `.mts` / `.mjs`（`.ts` / `.js` 会被当 CJS） |
| `AccessDenied` / 模型不可用 | 该 region 未开通 `qwen.qwen3-vl-235b-a22b`，或凭证缺 Bedrock / `bedrock-agentcore` 权限 |
| 启动即抱怨 region 未设 | 设 `AWS_REGION`（或给 `--region`）——本引擎不猜默认 region |
| 明明写了 `steps/` 却全走 AI | 确认 `--steps-dir` 指对，并用 `gherkai list-deterministic --steps-dir …` 看清单里有没有你那条 |

## 帮助

用法、装法与命令全景见项目主页 https://github.com/zhiyanliu/gherkai#readme ；问题请提 issue：https://github.com/zhiyanliu/gherkai/issues 。

设计文档（架构决策记录）见 https://github.com/zhiyanliu/gherkai/tree/HEAD/docs/adr 。
