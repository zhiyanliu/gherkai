# @gherkai/worker-midscene

gherkai 的 Midscene 执行引擎 worker：在云端浏览器（Amazon Bedrock AgentCore Browser）上执行 `.feature` 的每个 step，标了 `@device` 的 scope 改在 AWS Device Farm（us-west-2）的 Android / iOS 真机上执行，网页与原生应用都能测——AI step 交给 Bedrock 上的视觉模型看图定位、操作与判定，确定性 step 交给你自己写的函数执行（桌面浏览器上 handler 拿到 Playwright 的页面对象，真机上拿到连到设备上那个会话的 WebdriverIO 客户端）。它由 `gherkai` 命令行按需拉起，**不必手动运行**；本机装上它，就是让 `gherkai` 能用 `midscene` 引擎执行测试。被测 UI 的语言不限，中文界面上的动作与断言与英文界面同级可靠。

## 安装

```bash
npm i -g @gherkai/worker-midscene@<版本号>   # 需 Node ≥ 22；版本号须与命令行一致，用 gherkai --version 查
```

本 worker 由命令行 `gherkai` 拉起。请先安装命令行、配置 AWS 凭证与 region，并开通 Amazon Bedrock 上默认模型与 AgentCore Browser 的访问：https://github.com/zhiyanliu/gherkai/blob/HEAD/docs/user-guide/getting-started.md 。在真机上执行另需 us-west-2 的 AWS Device Farm 访问（设备资源固定在 us-west-2，与所配 region 无关），所需权限见 https://github.com/zhiyanliu/gherkai/blob/HEAD/docs/user-guide/running-and-results.md#本机后端的凭证需要什么权限

## 最小用法：写一条确定性 step

确定性 step 写在你自己项目的 `steps/` 目录里（扩展名只认 `.mts` / `.mjs`），用 `gherkai run --steps-dir ./steps` 带上（缺省即 `./steps`）：

```ts
// steps/login.mts
import { deterministic, DeterministicAssertion } from "@gherkai/worker-midscene";

deterministic(
  '元素 "(?<sel>[^"]+)" 可见',
  async ({ page }, { sel }) => {                  // page 是 Playwright 的 Page
    if (!(await page.locator(sel).isVisible())) {
      throw new DeterministicAssertion(`元素 ${sel} 应可见，实际没找到或不可见`);
    }
  },
  { description: "断言选择器命中的元素可见", example: 'Then 元素 "#submit" 可见' },
);
```

用 `gherkai list-deterministic --engine midscene --steps-dir ./steps` 查当前注册了哪些。

同一条 step 要在设备目标上也执行时，第二个参数换成按句柄种类分键的对象 `{ playwright, webdriver: [...] }`，写法与字段见下面「确定性 step 的完整写法」一页。

## 文档

- 装什么、要哪些 AWS 前置、第一次怎么完整运行：https://github.com/zhiyanliu/gherkai/blob/HEAD/docs/user-guide/getting-started.md
- 确定性 step 的完整写法与两侧对照：https://github.com/zhiyanliu/gherkai/blob/HEAD/docs/user-guide/writing-deterministic-steps.md
- `.feature` 怎么写才能稳定运行：https://github.com/zhiyanliu/gherkai/blob/HEAD/docs/user-guide/writing-features.md
- 模型、region、超时等环境变量与选项：https://github.com/zhiyanliu/gherkai/blob/HEAD/docs/user-guide/configuration.md
- 报错了先看哪：https://github.com/zhiyanliu/gherkai/blob/HEAD/docs/user-guide/troubleshooting.md
- 每版变更：https://github.com/zhiyanliu/gherkai/blob/HEAD/CHANGELOG.md

项目主页与问题反馈：https://github.com/zhiyanliu/gherkai#readme
