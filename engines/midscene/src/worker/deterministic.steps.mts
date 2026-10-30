// 确定性 step 脚手架（ADR 0020/0022）——随包发布的注册表内容：**只有内建导航一条**（零使用方内容，ADR 0037 决策 5 基础镜像同理）。
//
// 机制（ADR 0022）：worker 派发每个 step 时**先查确定性注册表**（命中走 handler），未命中才落 AI catch-all。
// 本文件的条目经 `registerBuiltin("navigation", 正则, handlers, { description, example, keywords })` 注册：校验与使用方的
// `deterministic(...)` 同一套（元数据必填、缺则 fail-loud——ADR 0036「注册即暴露」），另带内建标记（ADR 0050 决策 1），
// run-scope 据此把这条 step 的 step_kind 定为 navigation。worker 启动时 import 本模块，顶层的注册副作用把条目登记进表。
//
// 内建导航（ADR 0020 第 3 条）：一条 step 去掉关键字后**整句只是一个地址**（加不加引号都一样）、且关键字是 Given 或
// When，才是导航。判据是结构、不是措辞：不用动词词表，也不再按「引号里出现网址」判断。
//     Given "https://www.wikipedia.org/"
//     When https://en.wikipedia.org/wiki/OpenAI
// 句子里还有别的内容（`When 在输入框输入 "https://…"`）不是导航、走 AI；`Then` 后只有一个地址按注册表的关键字声明
// 记 error（裸地址已是导航语法，Then 没有断言谓词）。网页目标只能打开 http(s) 地址；应用目标上任意 scheme（含 http(s)）
// 都经 DeepLink 交给被测应用（ADR 0048 决策 7）。
//
// **产品不内置任何有措辞的 step**（ADR 0020 第 2 条）：曾内置的 `页面地址匹配 "<正则>"` 已退役。精确核对地址这类
// step 由使用方（测试开发）写在**使用方项目的 `steps/` 目录**（`*.mts`，`import { deterministic } from
// "@gherkai/worker-midscene"`），由 worker 启动时加载进同一张表（见 user-steps.mts，ADR 0037 决策 4）。本文件是发行
// 包内容，改它等于 fork。撞 pattern 按 ADR 0036 的 conflict 语义处理，**内建与使用方之间没有优先级覆盖**。
//
// handler 约定（见 deterministic.mts）：
//   - playwright 句柄签名 (ctx, groups) => void | Promise<void>：ctx.page 是 Playwright Page、ctx.navigate(url) 是引擎的导航
//     原语；groups 是正则具名组。webdriver 句柄的 ctx 是七个字段（ADR 0050 决策 2），内建导航不从 ctx 取导航原语（见下）。
//   - 判定失败抛 DeterministicAssertion（或 node:assert AssertionError）→ step 记 failed；抛其它 → error。
//
// Nova Act 侧的对称脚手架见 gherkai_worker_novaact 的 deterministic_steps 模块。
import { registerBuiltin } from "./deterministic.mjs";

// 地址的形态是 scheme://rest：scheme 按 RFC 3986（字母开头，字母、数字、`+ - .`），rest 非空且不含空白与双引号。
// 只允许一对包住整句的双引号（q1 / q2 两组用来核对配对；不带引号时 q2 组不参与匹配、取值为 undefined）。
// 不剥标点：不带引号的地址末尾若是句号、逗号、分号、冒号、叹号、问号、省略号这类标点，或右括号、右引号（ASCII 与
// 全角都算，见模式里的否定后顾字符集），整句就不是「一个地址」、走 AI——`When https://example.com/。` 多半是把地址
// 写进了一句话；地址本身以这些字符结尾时加引号即可（`"https://en.wikipedia.org/wiki/Foo_(bar)"`，引号内一律原样当地址）。
// 空白显式列出、不用 `\s`：ASCII 空白加不换行空格（U+00A0）与全角空格（U+3000，中文输入法在行尾容易多打一个）。
// JS 与 Python 两种正则方言的 `\s` 字符集不同（JS 含 U+FEFF、Python 含 U+0085 与 U+001C 到 U+001F），用 `\s` 会让
// 同一条 step 在两引擎上派发不同；BOM 因此不算空白，开头带 BOM 的整句不命中（BOM 不是字母、也不是空白）。
// `tel:123`（没有 `://`）、含未编码空格的地址、一个普通裸词都不命中。与 Nova 侧的 ADDRESS_PATTERN 除具名组写法
// （Python 的 `(?P<name>` 对应这里的 `(?<name>`）外逐字相同，由 engines/fixtures/navigation-address-cases.json 对拍。
export const ADDRESS_PATTERN = String.raw`^[ \t\r\n\f\v\u00a0\u3000]*(?<q1>"?)(?<url>[A-Za-z][A-Za-z0-9+.\-]*://[^" \t\r\n\f\v\u00a0\u3000]+)(?:(?<q2>")|(?<![.,;:!?)\]}。，、；：！？）】」』〉》］｝〕．…”’〗]))[ \t\r\n\f\v\u00a0\u3000]*$`;
export const WEB_SCHEMES = ["http", "https"];

/** 设备界面接缝的导航原语：拿到 step 里的地址，择路（应用目标经 DeepLink 带包名或 bundle id 交给被测应用、网页目标按能力
 *  探测结论在网页上下文里打开或交给系统浏览器）与失败归类都在接缝实现里（ADR 0052 决策 2、4、5；0048 决策 7）。 */
export type DeviceNavigate = (address: string) => Promise<void>;

// 内建导航的 webdriver 句柄取导航原语的模块私有通道（ADR 0050 决策 1「内建导航取导航原语经模块私有通道」）：设备模块建立
// 接缝时经 injectDeviceNavigate 把原语以闭包注入这里，句柄拿到的 ctx 仍只有七个字段（不加 navigate）。注入方向是设备模块到
// 本模块，本模块不 import 设备模块，能力自述入口因而不加载设备依赖；本模块不在包的公开导出面上，使用方取不到这个通道。
let deviceNavigate: DeviceNavigate | null = null;

/** 设备模块建立界面接缝时调用：注入导航原语，返回撤销函数（接缝释放时调用，重复调用无害、不撤销后来注入的原语）。
 *  一个 worker 进程同一时刻只有一个远程访问会话：已有注入时再注入即抛错，不静默替换。 */
export function injectDeviceNavigate(navigate: DeviceNavigate): () => void {
  if (deviceNavigate !== null) {
    throw new Error("这个 worker 进程已经连着一个远程访问会话，不能再接入第二个");
  }
  deviceNavigate = navigate;
  return () => {
    if (deviceNavigate === navigate) deviceNavigate = null;
  };
}

/** 从命中的具名组取出地址：只允许一对包住整句的双引号，两侧不配对即记 error。 */
function addressOf({ q1, url, q2 }: Record<string, string>): string {
  const close = q2 ?? "";  // 不带引号的写法里 q2 组不参与匹配
  if (q1 !== close) {
    throw new Error(`地址两侧的引号不配对：${JSON.stringify(q1 + url + close)}——要么都加双引号，要么都不加`);
  }
  return url;
}

/** 网页目标（桌面与设备）只打开 http(s) 地址，别的 scheme 由句柄记 error、不转 AI（ADR 0020 第 3 条）。 */
function requireWebScheme(url: string): void {
  const scheme = url.split("://", 1)[0].toLowerCase();
  if (!WEB_SCHEMES.includes(scheme)) {
    throw new Error(`网页目标只能打开 http(s) 地址，这一步写的是 ${scheme}:// 地址：${JSON.stringify(url)}`);
  }
}

/** 把地址交给设备接缝；没有注入（没有远程访问会话）时记 error。 */
async function navigateOnDevice(url: string): Promise<void> {
  if (deviceNavigate === null) {
    throw new Error(`当前没有可用的远程访问会话，无法打开地址：${JSON.stringify(url)}`);
  }
  await deviceNavigate(url);
}

// 一条条目、三份句柄：playwright 给桌面网页；webdriver 按界面类型拆两个条目（ADR 0050 决策 1：差异用条目过滤表达，不在
// handler 里按目标分支）——网页条目先核 scheme，应用条目任意 scheme 原样交出。两个 webdriver 条目都不声明前提：网页目标上
// 网页上下文不可用时，接缝按探测结论改走系统浏览器，导航仍可执行（ADR 0052 决策 4）。
registerBuiltin(
  "navigation",
  ADDRESS_PATTERN,
  {
    playwright: async ({ navigate }, groups) => {
      const url = addressOf(groups);
      requireWebScheme(url);
      await navigate(url);
    },
    webdriver: [
      {
        uiKinds: ["web"],
        handler: async (_ctx, groups) => {
          const url = addressOf(groups);
          requireWebScheme(url);
          await navigateOnDevice(url);
        },
      },
      {
        uiKinds: ["app"],
        handler: async (_ctx, groups) => {
          await navigateOnDevice(addressOf(groups));
        },
      },
    ],
  },
  {
    description: "内建导航：整句只是一个地址时直接打开它（网页目标只接受 http(s) 地址；应用目标上经 DeepLink 交给被测应用）",
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
