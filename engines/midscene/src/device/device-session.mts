// 远程访问会话对外的两份记录（ADR 0051 决策 4、8）：会话事件的线上形状，与 scope 诊断文件 device-session.json。
//
// 会话事件：session_opened / session_closed 由 Device Farm 会话与终结两块在各自的时机发出（Create 返回之后、按名找回孤儿时、
// 终结核对结束仍待核时、每个会话的处置最终结束时），形状只在本文件组装一次，字段名与取值集合以 core 的协议解码为准
// （core/gherkai_core/wire.py 的 session_opened / session_closed 分支）：origin 只取 created / discovered / attempted，release 只取
// confirmed / unconfirmed，name 必须非空（sessionId 为 null 时它是配对键），observedS 是数值或 null（null 不等于 0，ADR 0051 决策 7）。
// 端点地址不进任何字段。每个会话恰一条 session_closed（ADR 0051 决策 5）：同一配对键的第二条在这里被丢弃，不会先发 unconfirmed
// 再补 confirmed。
//
// device-session.json：能力探测结论（含候选数、Appium 版本、坐标比例与它的来源）、执行所用的会话 ARN、设备、换台记录与获取期
// 各阶段的时刻。best-effort，以 kind 为 device_session 的普通产物链接只挂在 scope_done 上；explain 只渲染链接、不解析内容，
// 所以键是诊断用的、不是协议。整份写盘前经脱敏出口（ADR 0051 决策 11），端点与预签名地址本就不写进来。
import fs from "node:fs";
import path from "node:path";
import { redactSecrets } from "../lib/redact.mjs";
import type { Device } from "../worker/deterministic.mjs";

// ---- 会话事件 ----

/** session_opened 的来源（ADR 0051 决策 4）：Create 返回、按名找回的孤儿、终结时仍未排除的创建尝试。 */
export type SessionOrigin = "created" | "discovered" | "attempted";
/** session_closed 的处置结果：只认状态确认停止为 confirmed（ADR 0051 决策 4）。 */
export type SessionRelease = "confirmed" | "unconfirmed";

/** session_opened.device：对 core 不透明（ADR 0051 决策 4）。model 与 osVersion 取自设备选择所用的 Device Farm 设备描述，
 *  unit 取远程访问会话的 instanceArn（没有时为 null），用来区分同一机型的不同设备单元。 */
export interface SessionDeviceInfo {
  platform: Device;
  model: string | null;
  osVersion: string | null;
  unit: string | null;
}

/** Device Farm 的设备分钟原形（DeviceMinutes），可缺。 */
export interface ProviderMinutes {
  total?: number;
  metered?: number;
  unmetered?: number;
}

export interface SessionOpenedFact {
  /** 会话 ARN；attempted 恒为 null。 */
  sessionId: string | null;
  /** 请求时携带的会话名，非空。 */
  name: string;
  origin: SessionOrigin;
  /** created 时给出；discovered 可缺；attempted 不带。 */
  device?: SessionDeviceInfo | null;
}

export interface SessionClosedFact {
  sessionId: string | null;
  name: string;
  release: SessionRelease;
  /** worker 观察到该会话的秒数：起点为 Create 返回（孤儿为发现时刻），止点为发出 Stop 或确认已停止；缺失为 null。 */
  observedS: number | null;
  providerMinutes?: ProviderMinutes | null;
}

/** 设备侧发会话事件的唯一出口：组装线上形状、核对字段，经 run-scope 的事件出口发出。 */
export interface SessionEventSink {
  opened(fact: SessionOpenedFact): Promise<void>;
  closed(fact: SessionClosedFact): Promise<void>;
}

/** session_opened 的线上形状。违反协议的组合（空名、attempted 带 sessionId 或 device）是实现错误，直接抛出。 */
export function sessionOpenedEvent(scopeId: string, fact: SessionOpenedFact): Record<string, unknown> {
  requireName(fact.name, "session_opened");
  if (fact.origin === "attempted" && (fact.sessionId !== null || (fact.device !== undefined && fact.device !== null))) {
    throw new Error("session_opened 的 attempted 只带会话名：sessionId 须为 null、不带 device");
  }
  const event: Record<string, unknown> = {
    type: "session_opened", scopeId, sessionId: fact.sessionId, name: fact.name, origin: fact.origin,
  };
  if (fact.device !== undefined && fact.device !== null) event.device = { ...fact.device };
  return event;
}

/** session_closed 的线上形状。observedS 必须是有限数值或 null（不用 0 代缺失）。 */
export function sessionClosedEvent(scopeId: string, fact: SessionClosedFact): Record<string, unknown> {
  requireName(fact.name, "session_closed");
  if (fact.observedS !== null && (typeof fact.observedS !== "number" || !Number.isFinite(fact.observedS))) {
    throw new Error(`session_closed 的 observedS 须为有限数值或 null，收到 ${String(fact.observedS)}`);
  }
  const event: Record<string, unknown> = {
    type: "session_closed", scopeId, sessionId: fact.sessionId, name: fact.name, release: fact.release,
    observedS: fact.observedS,
  };
  if (fact.providerMinutes !== undefined && fact.providerMinutes !== null) event.providerMinutes = { ...fact.providerMinutes };
  return event;
}

function requireName(name: unknown, type: string): void {
  if (typeof name !== "string" || name === "") throw new Error(`${type} 缺会话名：会话名是配对键的回退，必须非空`);
}

/** 会话事件出口。closed 按配对键（sessionId，没有时用 name）去重：每个会话恰一条，后到的同键事件被丢弃。 */
export function sessionEventSink(scopeId: string, emit: (event: Record<string, unknown>) => Promise<void>): SessionEventSink {
  const closedKeys = new Set<string>();
  return {
    opened: (fact) => emit(sessionOpenedEvent(scopeId, fact)),
    async closed(fact) {
      const event = sessionClosedEvent(scopeId, fact);
      const key = fact.sessionId !== null ? `arn:${fact.sessionId}` : `name:${fact.name}`;
      if (closedKeys.has(key)) return;
      closedKeys.add(key);
      await emit(event);
    },
  };
}

// ---- scope 诊断文件 device-session.json ----

/** 文件名与 scope_done.reportRefs 里的产物种类（ADR 0051 决策 8）。 */
export const DEVICE_SESSION_FILE = "device-session.json";
export const DEVICE_SESSION_REPORT_KIND = "device_session";

/** 网页上下文的探测结论（ADR 0052 决策 5）：提供、不提供、探测出错；应用目标不探测，记 not_applicable。 */
export type WebContextRecord = "available" | "unavailable" | "probe_error" | "not_applicable";
/** 坐标比例的来源：deviceScreenInfo 的 scale、原生 page source 根节点的回退、Android 恒为 1。 */
export type ScaleSource = "device_screen_info" | "page_source" | "fixed";

export interface DeviceSessionRecord {
  target: { device: string; ui_kind: string; app_id: string | null };
  /** 执行所用的远程访问会话（换台后是新的那个）；没建成会话时为 null。 */
  session: { arn: string; name: string; device: SessionDeviceInfo } | null;
  /** 换台时被替换的会话与原因（至多一条，ADR 0051 决策 3）。 */
  replaced_sessions: { arn: string; name: string; reason: string }[];
  automation_name: string | null;
  /** 探测结论；探测前就结束的 scope 为 null。 */
  probe: {
    web_context: WebContextRecord;
    web_context_candidates: number | null;
    input_context: "web" | "native" | null;
    scale: number;
    scale_source: ScaleSource;
    appium_version: string | null;
  } | null;
  /** 各阶段的时刻（ISO 8601）；没到达的为 null。 */
  timings: {
    acquire_started_at: string | null;
    session_created_at: string | null;
    session_running_at: string | null;
    appium_connected_at: string | null;
    probe_done_at: string | null;
    ready_at: string | null;
    warmup_done_at: string | null;
    released_at: string | null;
  };
  /** 执行前失败的归因与消息；就绪的 scope 为 null。 */
  acquire_failure: { error_type: string; message: string } | null;
  /** 释放是否有会话未能确认停止或有结果未知的创建尝试；未释放时为 null。 */
  release_failed: boolean | null;
}

/** 写 device-session.json 到 dir（不存在即创建），返回文件路径。整份经脱敏出口；写盘失败原样抛出，调用方按 best-effort 处理。 */
export function writeDeviceSessionFile(dir: string, record: DeviceSessionRecord): string {
  fs.mkdirSync(dir, { recursive: true });
  const file = path.join(dir, DEVICE_SESSION_FILE);
  fs.writeFileSync(file, redactSecrets(JSON.stringify(record, null, 2)) + "\n", "utf-8");
  return file;
}
