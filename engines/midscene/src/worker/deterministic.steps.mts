// 确定性 step 脚手架（ADR 0020/0022）——随包发布的注册表内容：**只有内建导航一条**（零使用方内容，ADR 0037 决策 5 基础镜像同理）。
//
// 机制（ADR 0022）：worker 派发每个 step 时**先查确定性注册表**（命中走 handler），未命中才落 AI catch-all。
// `deterministic(正则, handler, { description, example, keywords? })` 注册（元数据必填、缺则 fail-loud——ADR 0036
// 「注册即暴露」）；worker 启动时 import 本模块，顶层的 deterministic(...) 副作用把本文件里的条目登记进表。
//
// 内建导航（ADR 0020 第 3 条）：一条 step 去掉关键字后**整句只是一个地址**（加不加引号都一样）、且关键字是 Given 或
// When，才是导航。判据是结构、不是措辞：不用动词词表，也不再按「引号里出现网址」判断。
//     Given "https://www.wikipedia.org/"
//     When https://en.wikipedia.org/wiki/OpenAI
// 句子里还有别的内容（`When 在输入框输入 "https://…"`）不是导航、走 AI；`Then` 后只有一个地址按注册表的关键字声明
// 记 error（裸地址已是导航语法，Then 没有断言谓词）。网页目标只能打开 http(s) 地址。
//
// **产品不内置任何有措辞的 step**（ADR 0020 第 2 条）：曾内置的 `页面地址匹配 "<正则>"` 已退役。精确核对地址这类
// step 由使用方（测试开发）写在**使用方项目的 `steps/` 目录**（`*.mts`，`import { deterministic } from
// "@gherkai/worker-midscene"`），由 worker 启动时加载进同一张表（见 user-steps.mts，ADR 0037 决策 4）。本文件是发行
// 包内容，改它等于 fork。撞 pattern 按 ADR 0036 的 conflict 语义处理，**内建与使用方之间没有优先级覆盖**。
//
// handler 约定（见 deterministic.mts）：
//   - 签名 (ctx, groups) => void | Promise<void>：ctx.page 是 Playwright Page、ctx.navigate(url) 是引擎的导航原语；
//     groups 是正则具名组。
//   - 判定失败抛 DeterministicAssertion（或 node:assert AssertionError）→ step 记 failed；抛其它 → error。
//
// Nova Act 侧的对称脚手架见 gherkai_worker_novaact 的 deterministic_steps 模块。
import { deterministic } from "./deterministic.mjs";

// 地址的形态是 scheme://rest：scheme 按 RFC 3986（字母开头，字母、数字、`+ - .`），rest 非空且不含空白与双引号；
// 只允许一对包住整句的双引号（q1 / q2 两组用来核对配对），不剥标点——末尾多一个句号就不是「整句是地址」、走 AI。
// `tel:123`（没有 `://`）、含未编码空格的地址、一个普通裸词都不命中。与 Nova 侧的 ADDRESS_PATTERN 逐字相同
// （Python 的 `(?P<name>` 对应这里的 `(?<name>`），跨语言 fixture 对拍。
export const ADDRESS_PATTERN = '^\\s*(?<q1>"?)(?<url>[A-Za-z][A-Za-z0-9+.\\-]*://[^"\\s]+)(?<q2>"?)\\s*$';
export const WEB_SCHEMES = ["http", "https"];

deterministic(
  ADDRESS_PATTERN,
  async ({ navigate }, { q1, url, q2 }) => {
    if (q1 !== q2) {
      throw new Error(`地址两侧的引号不配对：${JSON.stringify(q1 + url + q2)}——要么都加双引号，要么都不加`);
    }
    const scheme = url.split("://", 1)[0].toLowerCase();
    if (!WEB_SCHEMES.includes(scheme)) {
      throw new Error(`网页目标只能打开 http(s) 地址，这一步写的是 ${scheme}:// 地址：${JSON.stringify(url)}`);
    }
    await navigate(url);
  },
  {
    description: "内建导航：整句只是一个地址时直接打开它（网页目标只接受 http(s) 地址）",
    example: 'Given "https://www.wikipedia.org/"',
    keywords: ["Given", "When"],
  },
);

// 使用方确定性 step 的写法示例（**抄进你项目的 `steps/*.mts` 里改**，别改本文件——见上「产品不内置任何有措辞的 step」）：
//
// import { deterministic, DeterministicAssertion } from "@gherkai/worker-midscene";
//
// deterministic('页面地址匹配 "(?<pattern>[^"]+)"', ({ page }, { pattern }) => {
//   const url = page.url();
//   if (!new RegExp(pattern).test(url)) {
//     throw new DeterministicAssertion(`页面地址应匹配 ${JSON.stringify(pattern)}，实际 ${JSON.stringify(url)}`);
//   }
// }, { description: "断言当前页面地址匹配给定正则（精确判定，不走 AI、不投票）", example: 'Then 页面地址匹配 "/wiki/OpenAI"', keywords: ["Then"] });
//
// deterministic('元素 "(?<sel>[^"]+)" 可见', async ({ page }, { sel }) => {
//   if (!(await page.locator(sel).isVisible())) {
//     throw new DeterministicAssertion(`元素 ${JSON.stringify(sel)} 应可见`);
//   }
// }, { description: "断言选择器命中的元素可见", example: 'Then 元素 "#submit" 可见' });

export {}; // ESM 模块标记
