// WebdriverIO 自身日志的凭据掩码（ADR 0051 决策 11）。
//
// 日志级别固定为 error，另给 webdriver 的 logger 按名配掩码正则。只限级别不够：error 级别下 webdriver 在请求最终失败时先把
// 错误消息记一条 error 再抛出、在 newSession 失败时记下错误对象，这些行由 @wdio/logger 直接写到 stderr，不经 worker 的日志出口，
// 而错误消息里带着整条设备端点地址（令牌在路径里）与服务端报错里的预签名应用地址。被拒的做法是把日志关到 silent：
// 丢掉的正是排查远程访问会话问题最需要的第一手诊断。
//
// 掩码正则取自 lib/redact.mts 的规则二（签名类查询参数与隧道令牌参数）与规则三（设备端点的路径令牌），用同一正则对象换算，
// 不另写一份；用 engines/fixtures/redaction-cases.json 校验（见 wdio-log.test.mts）。不收规则一（userinfo）：设备端点与预签名
// 地址都不带 userinfo，且它的字符集含逗号，而 @wdio/logger 按逗号切分掩码串。
//
// 换算方式：@wdio/logger 的掩码语义与 redactSecrets 不同。无捕获组时整段匹配换成固定的 **MASKED**；有捕获组时把每个组的文字
// 在匹配段内按首次出现替换。redactSecrets 的正则用开头的捕获组保住「参数名=」或「/remote-endpoint/」前缀、只换后面的值，
// 原样交给 @wdio/logger 会反过来换掉前缀、留下值。所以把开头那个捕获组改成非捕获组：前缀连同值整段换成掩码，匹配范围与
// redactSecrets 相同。另两种写法不取：值单独成组时，按首次出现替换会在值也出现在前缀里时（如参数值恰为 t）换掉前缀里那一处、
// 把值原样写出；用后行断言只匹配值时，@wdio/logger 先经 safe-regex2 筛掩码串，后者不认后行断言，规则会被静默丢弃。
//
// 掩码装在 @wdio/logger 的模块级状态上，本模块解析到的 @wdio/logger 必须与 webdriver 用的是同一个模块实例。发行的 npm 包装包时
// 解析依赖、没有 lock，使用方项目顶层另有一份别的版本时，两边可能解析到不同的两份，掩码就装到了 webdriver 不用的那一份上、装完的
// 核对也照样通过。所以 installWdioLogMasking 装掩码前先按包路径核对一次（webdriver 从 webdriverio 所在位置解析，与 webdriverio
// 实际加载它的路径一致），两边分成两份时抛出；wdio-log.test.mts 的真实运行层在本仓库的依赖树上核对掩码确实生效。
import { createRequire } from "node:module";
import getLogger from "@wdio/logger";
import { ENDPOINT_TOKEN, QUERY_SECRET } from "../lib/redact.mjs";

/** 三个 WebdriverIO 实例（建连、执行、探测）共用的日志级别（ADR 0051 决策 11）。 */
export const WDIO_LOG_LEVEL = "error" as const;

/** 配掩码的 logger 名：webdriver 包里的日志（含上述两种 error 行）都记在这个名下。 */
export const WDIO_LOGGER = "webdriver";

/** 把 redactSecrets 的一条规则换算成 @wdio/logger 认的掩码串（形态见模块头）。规则形态不符时抛出：换算会出错的规则不能装上去。 */
function maskingPatternFor(rule: RegExp): string {
  const source = rule.source;
  const capturingGroups = new RegExp(`${source}|`).exec("")!.length - 1;
  if (!source.startsWith("(") || source.startsWith("(?") || capturingGroups !== 1 || !rule.flags.includes("g") || source.includes(",")) {
    throw new Error(`脱敏规则无法换算成 WebdriverIO 的日志掩码：/${source}/${rule.flags}`);
  }
  return `/(?:${source.slice(1)}/${rule.flags}`;
}

/** 交给 `getLogger.setMaskingPatterns` 的掩码串：两条规则，逗号分隔。 */
export const WDIO_MASKING_PATTERNS = [QUERY_SECRET, ENDPOINT_TOKEN].map(maskingPatternFor).join(",");

/** webdriver logger 当前是否带着这组掩码（按正则源与标志逐条比对）。 */
export function wdioLogMaskingInstalled(): boolean {
  const installed = getLogger(WDIO_LOGGER).maskingPatterns ?? [];
  return WDIO_MASKING_PATTERNS.split(",").every((p) => installed.some((re) => String(re) === p));
}

/** 从 `from` 所在位置解析到的 @wdio/logger 与 webdriver 用的是否同一份（按两边解析到的 package.json 路径比对）。webdriver 不是
 *  本包的直接依赖，从 webdriverio 所在位置解析它。任一包解析不到时返回 false。`from` 缺省为本模块，测试用它换一棵依赖树。 */
export function sameLoggerAsWebdriver(from: string | URL = import.meta.url): boolean {
  try {
    const req = createRequire(from);
    const webdriverReq = createRequire(createRequire(req.resolve("webdriverio")).resolve("webdriver"));
    return req.resolve("@wdio/logger/package.json") === webdriverReq.resolve("@wdio/logger/package.json");
  } catch {
    return false;
  }
}

/** 给 webdriver logger 按名装上掩码；可重复调用。建任何 WebdriverIO 实例之前调用。先核对本模块与 webdriver 用的是同一份
 *  @wdio/logger，否则掩码装不到 webdriver 写日志的那一份上；@wdio/logger 又会静默丢弃它不接受的正则，所以装完再核对一次。
 *  两项任一不成立就抛出，不在没有掩码的情况下继续建会话。 */
export function installWdioLogMasking(): void {
  if (!sameLoggerAsWebdriver()) {
    throw new Error("本 worker 与 WebdriverIO 用的不是同一份日志模块 @wdio/logger，凭据掩码无法生效，设备端点可能被原样写进日志；请确认使用方项目没有安装与本 worker 要求不同版本的 @wdio/logger 或 WebdriverIO，再重新安装依赖");
  }
  getLogger.setMaskingPatterns({ [WDIO_LOGGER]: WDIO_MASKING_PATTERNS });
  if (!wdioLogMaskingInstalled()) {
    throw new Error("WebdriverIO 日志没有接受凭据掩码规则，设备端点可能被原样写进日志；请确认安装的 webdriverio 版本与本 worker 要求的一致");
  }
}
