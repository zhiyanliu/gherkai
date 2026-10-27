// 建会话前的自检（ADR 0049 决策 7；ADR 0024「job 行的结构版本与固定键集」）：先核 job 行的 schemaVersion，再用与能力自述同一份
// targets 核对 Job 携带的测试目标与墙钟预算。结构版本不等于本 worker 认的（含缺键）、目标不在 targets 里、墙钟预算超过该目标的
// max_session_s，都返回一句产品语言的原因；worker 据此发 scope_done{status: error, errorType: precheck_failed, message}、不发
// scope_started、零会话费用退出（ADR 0051 决策 4 的执行前失败）。纯函数、不读 env、不建会话。job 行的键集固定（target 恒为对象、
// 桌面也写 desktop/web），缺键不再当桌面：那是命令行工具与 worker 版本不一致的信号。对称 Nova 的 lib/precheck.py。
import { JOB_SCHEMA_VERSION, type Job } from "./job-source.mjs";

export interface TargetEntry { device: string; ui_kinds: string[]; max_session_s?: number }

const DEVICE_LABEL: Record<string, string> = { desktop: "桌面", android: "Android", ios: "iOS" };
const UI_KIND_LABEL: Record<string, string> = { web: "网页", app: "应用" };

/** (device, ui_kind) → 「桌面网页」「iOS 应用」这类名称（产品语言，与命令行工具的呈现同一口径）。 */
export function targetLabel(device: string, uiKind: string): string {
  const d = DEVICE_LABEL[device] ?? device;
  const k = UI_KIND_LABEL[uiKind] ?? uiKind;
  return device === "desktop" ? `${d}${k}` : `${d} ${k}`;
}

function supportedLabel(targets: ReadonlyArray<TargetEntry>): string {
  const names = targets.flatMap((t) => t.ui_kinds.map((k) => targetLabel(t.device, k)));
  return names.length ? names.join("、") : "无";
}

/** 名称嵌进中文句子时，拉丁字母开头或结尾处补一个空格（「在 Android 网页上」），全中文的名称原样；与命令行工具同一规则。 */
function spaced(label: string): string {
  const head = /^[A-Za-z0-9]/.test(label) ? " " : "";
  const tail = /[A-Za-z0-9]$/.test(label) ? " " : "";
  return `${head}${label}${tail}`;
}

/** job 行的结构版本不等于本 worker 认的（含缺键）→ 拒绝原因（产品语言）；null 表示通过。 */
export function precheckSchema(job: Partial<Pick<Job, "schemaVersion">>): string | null {
  const found = job.schemaVersion;
  if (found !== JOB_SCHEMA_VERSION) {
    const shown = found === undefined || found === null ? "缺失" : String(found);
    return `这个 job 的格式版本是 ${shown}，这个 worker 认的是 ${JOB_SCHEMA_VERSION}：命令行工具与 worker 的版本不一致，` +
      "请把两者装成同一版本（云端用与命令行工具同版本的 worker 镜像）。";
  }
  return null;
}

/** 建会话前的全部自检：结构版本先于目标与预算。返回拒绝原因；null 表示通过。 */
export function precheckJob(job: Partial<Pick<Job, "schemaVersion" | "target" | "timeoutS">>, targets: ReadonlyArray<TargetEntry>): string | null {
  return precheckSchema(job) ?? precheckTarget(job, targets);
}

/** 返回拒绝原因（产品语言）；null 表示通过。target 须为对象（键集固定、桌面也写 desktop/web）。 */
export function precheckTarget(job: Partial<Pick<Job, "target" | "timeoutS">>, targets: ReadonlyArray<TargetEntry>): string | null {
  if (job.target === undefined || job.target === null || typeof job.target !== "object") {
    return "这个 job 没有带测试目标：命令行工具与 worker 的版本不一致，请把两者装成同一版本。";
  }
  const device = job.target.device;
  const uiKind = job.target.uiKind;
  const entry = targets.find((t) => t.device === device);
  if (!entry || !entry.ui_kinds.includes(uiKind)) {
    return `这个 worker 不支持在${spaced(targetLabel(device, uiKind))}上执行测试（它支持：${supportedLabel(targets)}）。` +
      "请改用支持该目标的引擎，或使用与命令行工具同版本的 worker 镜像。";
  }
  const limit = entry.max_session_s;
  const timeoutS = job.timeoutS;
  if (limit !== undefined && typeof timeoutS === "number" && timeoutS > limit) {
    return `这个 job 的墙钟预算 ${timeoutS} 秒超过了${spaced(targetLabel(device, uiKind))}的会话上限 ${limit} 秒。` +
      "请调低这个 scope 的 @timeout 或 --default-job-timeout。";
  }
  return null;
}
