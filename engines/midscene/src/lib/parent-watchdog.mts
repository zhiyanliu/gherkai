// 所属进程消失视同停止信号（ADR 0024 终止契约「父进程消失」条）。
//
// 本机启动方（core 的子进程 adapter）经环境变量 GHERKAI_PARENT_PID 显式传入所属进程号：同步 run 为 CLI 进程，本机后台运行为推进进程。
// worker 启动时立即核验一次、此后按固定间隔核验所属进程是否仍存活（向它发空信号）；已退出即调一次 onGone，由调用方走与收到 SIGTERM
// 相同的收尾。核验对象不随包装进程（uvx、npx）改变，所属进程在本模块装上之前已退出且已被回收的情形也在首次核验时发现——这两点是不能只用
// 「启动时读到的父进程号」当基准的原因。本进程直接是所属进程的子进程时另看父进程号是否变化：所属进程一退出父进程号就变、不等回收。
// 没有它，执行期的孤儿 worker 要等下一次写事件撞上 EPIPE 才发现所属进程已退出，建会话期的孤儿要等排队、等待 RUNNING 这类长等待结束，
// 期间远程访问会话或云端浏览器会话照常计费。
// 边界：未传入该变量的入口（容器主进程）不启用；经包装进程启动时，所属进程退出后尚未被其父进程回收的窗口内空信号仍报告存在，要等回收后
// 才触发，一直不被回收则不触发；进程号被复用时核验会误判存活，退化为没有本模块时的行为。
// 计时器 unref：它不维持事件循环，worker 正常结束时不必显式停。

export const PARENT_POLL_MS = 5000;
export const PARENT_PID_ENV = "GHERKAI_PARENT_PID";

export interface ParentWatchdogDeps {
  ownerPid?: number | null;  // 缺省从环境变量取；null 表示未传入
  isAlive?: (pid: number) => boolean;
  getPpid?: () => number;  // 当前父进程号（直接子进程时父进程号变化即视同所属进程退出）
  intervalMs?: number;
}

/** 环境变量里的所属进程号；未设或不是正整数即 null。 */
export function ownerPidFromEnv(env: NodeJS.ProcessEnv = process.env): number | null {
  const raw = env[PARENT_PID_ENV];
  if (!raw || !/^\d+$/.test(raw)) return null;
  const pid = Number(raw);
  return pid > 0 ? pid : null;
}

/** 进程是否存活：空信号送达即存活；没有权限也算存活（进程在，只是不属于我们）；找不到即已退出。 */
export function processAlive(pid: number): boolean {
  try {
    process.kill(pid, 0);
    return true;
  } catch (e) {
    return (e as NodeJS.ErrnoException).code === "EPERM";
  }
}

/** 启动核验，返回停止函数。所属进程号未传入时不启动、返回空函数；启动时所属进程已不在则立即调 onGone。 */
export function startParentWatchdog(onGone: () => void, deps: ParentWatchdogDeps = {}): () => void {
  const ownerPid = deps.ownerPid === undefined ? ownerPidFromEnv() : deps.ownerPid;
  if (ownerPid === null) return () => {};
  const isAlive = deps.isAlive ?? processAlive;
  const getPpid = deps.getPpid ?? (() => process.ppid);
  const direct = getPpid() === ownerPid;  // 直接子进程：父进程号变化即所属进程已退出（不等回收）
  const gone = (): boolean => !isAlive(ownerPid) || (direct && getPpid() !== ownerPid);
  if (gone()) {
    onGone();
    return () => {};
  }
  const timer = setInterval(() => {
    if (!gone()) return;
    clearInterval(timer);
    onGone();
  }, deps.intervalMs ?? PARENT_POLL_MS);
  timer.unref();
  return () => clearInterval(timer);
}
