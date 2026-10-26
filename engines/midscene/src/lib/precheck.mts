// 建会话前的自检（ADR 0049 决策 7）：用与能力自述同一份 targets 核对 Job 携带的测试目标与墙钟预算。
// 目标不在 targets 里，或墙钟预算超过该目标的 max_session_s，即返回一句产品语言的原因；worker 据此发
// scope_done{status: error, errorType: precheck_failed, message}、不发 scope_started、零会话费用退出（ADR 0051 决策 4 的执行前失败）。
// 纯函数、不读 env、不建会话；Job 缺 target 即桌面网页——这是桌面 job 的正常形态（core 只在非桌面才写该键，ADR 0024 可选键），
// 1.5 之前的 CLI 也不写它。对称 Nova 的 lib/precheck.py。
import type { Job } from "./job-source.mjs";

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

/** 返回拒绝原因（产品语言）；null 表示通过。 */
export function precheckTarget(job: Pick<Job, "target" | "timeoutS">, targets: ReadonlyArray<TargetEntry>): string | null {
  const device = job.target?.device ?? "desktop";
  const uiKind = job.target?.uiKind ?? "web";
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
