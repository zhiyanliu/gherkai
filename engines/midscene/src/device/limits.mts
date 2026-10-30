// 设备目标的预算常量：时间上界、次数上限与截断阈值的单一来源（ADR 0052 决策 6 的超时分层表；ADR 0051 决策 2、3、5、8、9）。
//
// **本文件不 import 任何 SDK，也不 import 设备模块的其它文件**：能力自述（`--capabilities` 的 targets[].max_session_s）与
// 收尾下限（min_grace_s）要用这里推出的值，而桌面路径与能力自述不加载 WebdriverIO 与 Device Farm SDK（ADR 0052 决策 3
// 「设备模块动态加载」）。这里一旦 import 了 SDK，「能力自述零依赖」就会被悄悄打破；由 `worker/no-device-deps.test.mts` 守。
// 唯一的 import 是与桌面预热共用的尝试次数（`lib/tunnel-warmup.mts` 只依赖本包的脱敏模块）。
//
// 单位写在名字里：`_MS` 是毫秒，用于计时器与请求超时；`_S` 是秒，用于协议面的值（能力自述）、Appium 能力项与 S3 预签名。
// 标注「实施期校准、真机验收后可调」的，是 ADR 原文标明的校准值；改它们只改这里，消费方不另写字面量。
// 次数上限里只有重规划上限可由使用方经 env 覆盖，覆盖键的读取与校验也在本文件（replanningCycleLimit，ADR 0044 决策 2）：
// worker 启动时的校验与设备 Agent 的构造项共用这一份，不各写一套解析。
import { WARMUP_ATTEMPTS } from "../lib/tunnel-warmup.mjs";

// ---- 会话寿命（ADR 0051 决策 2；ADR 0049 决策 4）----

/** Device Farm 远程访问会话的硬上限 150 分钟，从发出 CreateRemoteAccessSession 起算（超时分层表 ②）。 */
export const SESSION_CAP_S = 9000;
/** Fargate 任务停止宽限 `stopTimeout` 的硬上限：会话年龄到点后收尾最多能拿到的时间。 */
export const FARGATE_STOP_TIMEOUT_CAP_S = 120;
/** 设备目标的单次会话上限：会话硬上限减去停止宽限的硬上限，即 8880 秒。写进能力自述的 max_session_s，同时是
 *  worker 自检的阈值（墙钟预算超过它即 precheck_failed）与会话年龄后备的触发点（到点归 session_lost）。
 *  余量取停止宽限的硬上限、不取收尾各段之和：后者会随网络退化实测调整，且收尾挂住到硬上限时会话会越过 150 分钟
 *  （ADR 0049 决策 4 的被拒读法）。 */
export const MAX_SESSION_S = SESSION_CAP_S - FARGATE_STOP_TIMEOUT_CAP_S;

// ---- Device Farm 单次调用（ADR 0051 决策 3；超时分层表 ④）----
// 客户端 maxAttempts 为 1，每次调用显式带请求超时，重试一律由 worker 在获取预算内手写退避。

/** Create、Get、List 的单次请求超时。 */
export const DEVICE_FARM_CALL_TIMEOUT_MS = 10_000;
/** StopRemoteAccessSession 的单次请求超时（换台时先停被替换的会话、终结的释放阶段都用它；在释放阶段内是子预算，不是收尾下限的加数）。 */
export const STOP_CALL_TIMEOUT_MS = 3_000;
/** 终结期（释放阶段内）GetRemoteAccessSession 的单次请求超时（同为释放阶段内的子预算）。 */
export const FINALIZE_GET_TIMEOUT_MS = 5_000;

// ---- 获取期（ADR 0051 决策 2、3、9；超时分层表 ③ ⑤）----
// 获取预算本身不在这里：worker 只读 Job 设备请求里的 acquireTimeoutS，缺省的填入与上界的校验都在 core（ADR 0051 决策 2）。

/** 设备解析首轮零候选时，间隔这么久再列举一次，仍为零即 precheck_failed。实施期校准、真机验收后可调。 */
export const DEVICE_RELIST_DELAY_MS = 2_000;
/** 全部候选繁忙时重列间隔的起点与封顶：按 5、10、20 秒递增，之后封顶 30 秒。实施期校准、真机验收后可调。 */
export const BUSY_BACKOFF_INITIAL_MS = 5_000;
export const BUSY_BACKOFF_CAP_MS = 30_000;
/** 第 waitIndex 次（从 0 起）繁忙等待的间隔：起点逐次翻倍，不超过封顶。 */
export function busyBackoffMs(waitIndex: number): number {
  return Math.min(BUSY_BACKOFF_INITIAL_MS * 2 ** waitIndex, BUSY_BACKOFF_CAP_MS);
}
/** 换台重建的条件：剩余获取预算不少于这个值；不足即不再换台（预算跨换台不重置）。 */
export const REPLACE_DEVICE_MIN_REMAINING_MS = 150_000;
/** newSession 单请求超时的下限：Appium 单条命令上限 4 分钟（含 `appium:app` 安装）加老 iPhone 建连实测的 65 秒。
 *  封顶优先：剩余获取预算小于它时，newSession 以剩余预算为超时（超时分层表 ⑤）。 */
export const NEW_SESSION_TIMEOUT_FLOOR_MS = 4 * 60_000 + 65_000;
/** 安装包预签名地址的有效期，只需覆盖 newSession 期间的下载。实施期校准、真机验收后可调。 */
export const APP_PRESIGN_EXPIRES_S = 3600;
/** activateApp 之后的应用状态采样：次数与间隔，任一次回到「未运行」即判启动即自退。实施期校准、真机验收后可调。 */
export const LAUNCH_SAMPLE_COUNT = 3;
export const LAUNCH_SAMPLE_INTERVAL_MS = 1_000;
/** 能力探测的短预算：探测实例的单请求超时，网页上下文「可用」须在这段时间内成功执行一条只读命令（ADR 0052 决策 5）。
 *  scenario 前核对的存活探测同样受它约束（ADR 0052 决策 2）。 */
export const PROBE_TIMEOUT_MS = 5_000;
/** 设备目标上会话预热的导航尝试次数，与桌面预热共用同一常量（3 次，实施期校准、真机验收后可调；ADR 0052 决策 6）。
 *  设备预热的导航上界是执行期单请求超时，不套用桌面预热的 30 秒导航超时。 */
export const DEVICE_WARMUP_ATTEMPTS = WARMUP_ATTEMPTS;

// ---- 执行期（ADR 0052 决策 5、6；超时分层表 ⑥ ⑦ ⑧ ⑨）----

/** 执行实例的单请求超时，是单条命令的真实上界；须大于页面加载上限加余量，给服务端先报超时的机会。
 *  实施期校准、真机验收后可调。 */
export const EXEC_REQUEST_TIMEOUT_MS = 180_000;
/** W3C `pageLoad` 超时，暂定值；只是尽力而为，不能当上界（Android 上报得迟，iOS 上设置不被反映）。 */
export const PAGE_LOAD_TIMEOUT_MS = 150_000;
/** `appium:newCommandTimeout`（Appium 能力项，单位秒）：命令之间的最长空闲，须不小于单次模型规划等最长空闲加余量；
 *  缺省的 60 秒会让会话在规划期间被回收。实施期校准、真机验收后可调。 */
export const NEW_COMMAND_TIMEOUT_S = 900;
/** 设备 Agent 的重规划上限缺省值：原生应用的翻页类动作每翻一页消耗一轮规划，实测需要到 12，且必须有限。
 *  桌面不传；覆盖走 SDK 同名 env `MIDSCENE_REPLANNING_CYCLE_LIMIT`（ADR 0044 决策 2）。 */
export const DEVICE_REPLANNING_CYCLE_LIMIT = 12;
/** 重规划上限的覆盖键，与 Midscene SDK 自己读的 env 同名，使用方在两类目标上只需记一个键（ADR 0044 决策 2）。 */
export const REPLANNING_LIMIT_ENV = "MIDSCENE_REPLANNING_CYCLE_LIMIT";
/** 重规划上限的取值：env 里没有覆盖键时取缺省值；有则须为十进制正整数（首尾空白与前导零按 SDK 的读法忽略），否则抛出、点名
 *  该键，空串同样非法（上限必须有限）。只读传入的 env、无副作用。
 *
 *  两个调用点：worker 启动时（读 job 之后、建界面接缝之前）调一次做校验，桌面与设备都校验；设备 Agent 的构造项只经它取值。
 *  桌面不把取值传给 SDK，由 SDK 按同名 env 自行处理。设备路径必须自己读这个键，是因为 SDK 的取值顺序是构造项优先于 env，
 *  传了缺省值就会遮住 SDK 对同名 env 的读取（ADR 0044 决策 2）。 */
export function replanningCycleLimit(env: NodeJS.ProcessEnv = process.env): number {
  const raw = env[REPLANNING_LIMIT_ENV];
  if (raw === undefined) return DEVICE_REPLANNING_CYCLE_LIMIT;
  const text = raw.trim();
  const value = Number(text);
  if (!/^[0-9]+$/.test(text) || !Number.isSafeInteger(value) || value < 1) {
    throw new Error(
      `环境变量 ${REPLANNING_LIMIT_ENV} 的值 ${JSON.stringify(raw)} 不是正整数；请改为正整数（设备目标上缺省为 ` +
      `${DEVICE_REPLANNING_CYCLE_LIMIT}），或删除这个环境变量`,
    );
  }
  return value;
}
/** 定位网页上下文时零候选的等待间隔，之后再列一次，仍为零记 engine_error（ADR 0052 决策 5）。
 *  实施期校准、真机验收后可调。 */
export const WEB_CONTEXT_RELIST_DELAY_MS = 2_000;
/** Android 应用目标上 DeepLink 成功之后核对前台包名的轮询：次数（含第一次，第一次不等待）与间隔（UiAutomator2 适配器的
 *  foregroundPoll，由部件装配传入）。ADR 0048 决策 7 只写了「允许短暂轮询」、没有定数，这里取 activateApp 之后启动采样的同一组值：
 *  两者都是应用切到前台之后的短暂观察。真机验收后可调。 */
export const DEEP_LINK_FOREGROUND_POLL_ATTEMPTS = LAUNCH_SAMPLE_COUNT;
export const DEEP_LINK_FOREGROUND_POLL_INTERVAL_MS = LAUNCH_SAMPLE_INTERVAL_MS;

// ---- evidence 采集（ADR 0051 决策 8）----
// 读地址、控件摘要与原始控件树共用一段独立短预算，不占 step 的执行预算。实施期校准、真机验收后可调。

export const SNAPSHOT_CAPTURE_BUDGET_MS = 10_000;
/** 控件摘要截断条数；截断时 controls.truncated 为 true。 */
export const CONTROLS_MAX_ITEMS = 200;
/** 原始控件树截断字节数（1 MiB）；截断时 page_source_truncated 为 true。 */
export const PAGE_SOURCE_MAX_BYTES = 1024 * 1024;

// ---- 收尾（ADR 0051 决策 5；超时分层表 ⑩）----
// 终结四阶段的截止线相对进入终结的时刻计。各段上限以网络退化实测校准后定数（ADR 0049 决策 5）。

/** 正常收尾、Appium 会话建成后的执行前失败与 scope 级终止（会话丢失、scenario 前核对终止）里 deleteSession 的预算：不重试，不阻塞 Stop；远程访问会话已是 STOPPING 或 COMPLETED 时不调。SIGTERM 与进程级异常路径不调。 */
export const DELETE_SESSION_TIMEOUT_MS = 5_000;
/** 阶段 1：等在途的 Create 返回并登记 ARN，超时即标为结果未知。 */
export const FINALIZE_AWAIT_CREATE_MS = 10_000;
/** 阶段 2：终结核对，按名列举（含分页）处理全部待核尝试。 */
export const FINALIZE_RECONCILE_MS = 5_000;
/** 阶段 3：释放，全部待清理会话并行、共享这一条截止线；Stop 与终结期 Get 的单次超时是它内部的子预算。 */
export const FINALIZE_RELEASE_MS = 25_000;

/** 两条收尾路径共用的尾段（阶段 4 的中断兜底上传、截图队列退出段排空，以及事件写出与余量）。三者的单一来源分别是
 *  `lib/artifact-upload.mts` 的 UPLOAD_TIMEOUT_MS、`worker/run-scope.mts` 的 QUEUE_DRAIN_EXIT_MS 与 MIN_GRACE_MARGIN_MS，
 *  由调用方传入而不在这里 import：前者会带进 S3 SDK，后者与本文件互相引用，都会破坏本文件零 SDK 依赖的分层。 */
export interface SharedShutdownTailMs {
  uploadMs: number;
  queueDrainExitMs: number;
  marginMs: number;
}

/** 设备路径收尾各段之和，单位秒：阶段 1 到 3 加共用尾段，按当前常量为 10 + 5 + 25 + 10 + 6 + 7.5，即 63.5。
 *  能力自述的 min_grace_s 取它与桌面路径之和的较大者，不相加（一个 job 只走其中一条收尾路径；ADR 0049 决策 5、
 *  ADR 0051 决策 5），不取整。 */
export function deviceGraceSeconds(tail: SharedShutdownTailMs): number {
  const totalMs = FINALIZE_AWAIT_CREATE_MS + FINALIZE_RECONCILE_MS + FINALIZE_RELEASE_MS
    + tail.uploadMs + tail.queueDrainExitMs + tail.marginMs;
  return totalMs / 1000;
}
