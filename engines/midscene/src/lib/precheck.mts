// 建会话前的自检（ADR 0049 决策 7）：用与能力自述同一份 targets 核对 Job 携带的测试目标与墙钟预算。
// 目标不在 targets 里，或墙钟预算超过该目标的 max_session_s，即返回一句产品语言的原因；worker 据此发
// scope_done{status: error, errorType: precheck_failed, message}、不发 scope_started、零会话费用退出（ADR 0051 决策 4 的执行前失败）。
// 纯函数、不读 env、不建会话；Job 缺 target 即桌面网页（1.5 之前的 CLI 不写该键，ADR 0024 可选键）。对称 Nova 的 lib/precheck.py。

export interface TargetEntry { device: string; ui_kinds: string[]; max_session_s?: number }
export interface JobTarget { device: string; uiKind: string; app?: unknown }

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

/** 返回拒绝原因（产品语言）；null 表示通过。 */
export function precheckTarget(job: { target?: JobTarget; timeoutS?: number }, targets: ReadonlyArray<TargetEntry>): string | null {
  const device = job.target?.device ?? "desktop";
  const uiKind = job.target?.uiKind ?? "web";
  const entry = targets.find((t) => t.device === device);
  if (!entry || !entry.ui_kinds.includes(uiKind)) {
    return `这个 worker 不支持在${targetLabel(device, uiKind)}上执行测试（它支持：${supportedLabel(targets)}）。` +
      "请改用支持该目标的引擎，或使用与命令行工具同版本的 worker 镜像。";
  }
  const limit = entry.max_session_s;
  const timeoutS = job.timeoutS;
  if (limit !== undefined && typeof timeoutS === "number" && timeoutS > limit) {
    return `这个 job 的墙钟预算 ${timeoutS} 秒超过了${targetLabel(device, uiKind)}的会话上限 ${limit} 秒。` +
      "请调低这个 scope 的 @timeout 或 --default-job-timeout。";
  }
  return null;
}
