// 会话名的编码、解码与匹配（ADR 0051 决策 3）：规则在 TypeScript 侧的唯一实现。Device Farm 远程访问会话的名字与两个桌面 worker 的
// StartBrowserSession 请求名（决策 4）都按它生成；Nova Act worker 是 Python 写的，按同一规则另有一份实现，改规则两处同改。
//
// 形态：gherkai:<run_id>:<scope 哈希>:<尝试序号>:<scope_id 编码>
// - scope 哈希：完整 scope_id 按 UTF-8 求 SHA-256，取前 16 位小写十六进制（64 位）。截断从不影响它。
// - 尝试序号：十进制非负整数、无前导零。同名会话可以并行创建、名字没有唯一性，所以每次 Create（含限流重试与换台）都由
//   调用方给一个新序号，否则结果未知的尝试与它的重试分不开。起始值由调用方定，本模块不假设。
// - scope_id 编码段：A-Z a-z 0-9 . _ - 之外的字符按 UTF-8 字节编成大写 %XX。与 encodeURIComponent 不同，! ' ( ) * ~ 也编码；
//   冒号与百分号同样编码，编码段里因此不会出现分隔符，解码可以从右往左拆。十六进制取大写，与 RFC 3986 的规范化写法
//   一致；Python 侧若用 urllib.parse.quote，要另把 ~ 编码（它缺省放行 ~）。
// - 长度：总长超过上限时只截编码段（它只供人在控制台辨认），其余四段永不截断。上限缺省 256（Device Farm：实测 256 接受、
//   257 拒绝）；桌面请求名取 100（AgentCore 对会话名只限长度 1 到 100、不限字符集，决策 4）。截断按 scope_id 的完整
//   字符进行（一个字符的编码是 1 到 12 个字符的整体），不切开 %XX，截后的编码段仍能解码成 scope_id 的前缀。
//   名字只含 ASCII（run_id 由 gherkai 生成、形如 20260629T141207Z-a3f9c1），所以按 UTF-16 码元数的 length 就是字符数。
//
// 匹配只认整名相等（决策 3）：用同一规则按 (run_id, scope_id, 尝试序号, 上限) 重算，再与列举到的名字逐字比较；不按前缀、
// 不按哈希段匹配。同一 run 内两个 scope 要互认，须 64 位哈希与截断后的编码段同时相同。
//
// 本模块只依赖 node:crypto，不 import 任何 SDK：桌面路径也在每次 StartBrowserSession 前调用它。
import { createHash } from "node:crypto";

export const SESSION_NAME_PREFIX = "gherkai";
export const DEVICE_FARM_SESSION_NAME_MAX = 256;
export const AGENTCORE_SESSION_NAME_MAX = 100;
const SCOPE_HASH_HEX_LENGTH = 16;
// run_id 的来源（ADR 0024「run_id + scope_id 注入 worker」条）：云端由 RunTask overrides 注入，本机由起 worker 的进程经
// 组合根拥有的 worker env 注入（ADR 0037 决策 4）。两条路径同名。
export const RUN_ID_ENV = "RUN_ID";

const UNRESERVED_CHAR = /^[A-Za-z0-9._-]$/;
// 编码段不含冒号，run_id 段取余下的全部，因此从右往左拆是唯一的。
const NAME_PATTERN = new RegExp(
  `^${SESSION_NAME_PREFIX}:(.+):([0-9a-f]{${SCOPE_HASH_HEX_LENGTH}}):(0|[1-9][0-9]*):((?:[A-Za-z0-9._-]|%[0-9A-F]{2})*)$`);
const UTF8 = new TextEncoder();

export interface SessionNameOptions {
  /** 名字总长上限，缺省 DEVICE_FARM_SESSION_NAME_MAX；桌面请求名传 AGENTCORE_SESSION_NAME_MAX。 */
  maxLength?: number;
}

export interface MatchOptions extends SessionNameOptions {
  /** 给出时只认这一次尝试的名字；缺省时认同一 run、同一 scope 的任一尝试。逐个待核尝试判定时应传它，免得一条会话被几个尝试同时认领。 */
  attempt?: number;
}

export interface DecodedSessionName {
  runId: string;
  scopeHash: string;
  attempt: number;
  /** 编码段原文（可能已截断），不还原成 scope_id。 */
  scopeIdSegment: string;
}

/** 完整 scope_id 的 SHA-256 前 16 位小写十六进制。 */
export function scopeHash(scopeId: string): string {
  return createHash("sha256").update(scopeId, "utf8").digest("hex").slice(0, SCOPE_HASH_HEX_LENGTH);
}

// 按码点切成编码单元：保留字符是它自己，其余字符是它 UTF-8 字节的 %XX 串。截断以单元为粒度。
// 孤立的代理码元（scope_id 来自 JSON，正常不会出现）按 U+FFFD 编码，与 createHash 的 utf8 编码一致。
function encodedUnits(scopeId: string): string[] {
  const units: string[] = [];
  for (const ch of scopeId) {
    if (UNRESERVED_CHAR.test(ch)) {
      units.push(ch);
      continue;
    }
    let unit = "";
    for (const byte of UTF8.encode(ch)) unit += `%${byte.toString(16).toUpperCase().padStart(2, "0")}`;
    units.push(unit);
  }
  return units;
}

function resolveMaxLength(opts: SessionNameOptions): number {
  const maxLength = opts.maxLength ?? DEVICE_FARM_SESSION_NAME_MAX;
  if (!Number.isSafeInteger(maxLength) || maxLength < 1) {
    throw new RangeError(`会话名长度上限须为正整数，收到 ${maxLength}`);
  }
  return maxLength;
}

/** 按规则生成会话名。固定四段放不下时报错（它们永不截断）。 */
export function encode(runId: string, scopeId: string, attempt: number, opts: SessionNameOptions = {}): string {
  if (runId === "") throw new RangeError("会话名缺少本次运行的编号");
  if (!Number.isSafeInteger(attempt) || attempt < 0) {
    throw new RangeError(`会话名的尝试序号须为非负整数，收到 ${attempt}`);
  }
  const maxLength = resolveMaxLength(opts);
  const head = `${SESSION_NAME_PREFIX}:${runId}:${scopeHash(scopeId)}:${attempt}:`;
  if (head.length > maxLength) {
    // 正常不会发生：run_id 由 gherkai 生成、长度固定在二十余字符。出现即说明运行编号的形态变了，名字无法按规则生成。
    throw new RangeError(`本次运行的编号过长（${runId.length} 个字符），会话名超过 ${maxLength} 个字符的上限`);
  }
  let segment = "";
  let room = maxLength - head.length;
  for (const unit of encodedUnits(scopeId)) {
    if (unit.length > room) break;
    segment += unit;
    room -= unit.length;
  }
  return head + segment;
}

/** 拆出各段；不是按本规则生成的名字返回 null。只做形态解析，归属判定用 matches。 */
export function decode(name: string): DecodedSessionName | null {
  const m = NAME_PATTERN.exec(name);
  if (m === null) return null;
  const attempt = Number(m[3]);
  if (!Number.isSafeInteger(attempt)) return null;
  return { runId: m[1]!, scopeHash: m[2]!, attempt, scopeIdSegment: m[4]! };
}

/**
 * 名字是否属于这个 run 的这个 scope：取名字里的尝试序号（或 opts.attempt）按同一规则重算，整名相等才算。
 * opts.maxLength 须与生成名字时所用的一致——被截断的名字换个上限重算就不再相等。
 */
export function matches(name: string, runId: string, scopeId: string, opts: MatchOptions = {}): boolean {
  const attempt = opts.attempt ?? decode(name)?.attempt;
  if (attempt === undefined) return false;
  return name === encode(runId, scopeId, attempt, { maxLength: opts.maxLength });
}

/** 读 env 里的本次运行编号；缺失或为空时报错（会话名不能缺 run 段）。 */
export function runIdFromEnv(env: NodeJS.ProcessEnv = process.env): string {
  const runId = env[RUN_ID_ENV];
  if (!runId) {
    throw new Error(
      `缺少环境变量 ${RUN_ID_ENV}（本次运行的编号），无法为浏览器会话或远程访问会话命名。` +
      "worker 应由 gherkai 命令行工具或云端后端启动，两者都会设置该变量；若已如此启动，请把命令行工具与后端更新到同一版本后重试");
  }
  return runId;
}
