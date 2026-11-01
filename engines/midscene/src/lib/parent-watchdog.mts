// 父进程消失视同停止信号（ADR 0024 终止契约「父进程消失」条）。
//
// worker 作为 CLI 的子进程启动时记下父进程号，按固定间隔核对；父进程号变了（CLI 被 SIGTERM 或 SIGKILL 杀死、崩溃，本进程被过继）
// 即调一次 onGone，由调用方走与收到 SIGTERM 相同的收尾。没有它，执行期的孤儿 worker 要等下一次写事件撞上 EPIPE 才知道父进程没了，
// 建会话期的孤儿要等排队、等待 RUNNING 这类长等待结束，期间远程访问会话或云端浏览器会话照常计费。
// 只在作为子进程启动时启用：父进程号不大于 1 表示本进程是容器主进程（Fargate）或已被过继，没有可核对的父进程。
// 计时器 unref：它不维持事件循环，worker 正常结束时不必显式停。

export const PARENT_POLL_MS = 5000;

export interface ParentWatchdogDeps {
  getPpid?: () => number;
  intervalMs?: number;
}

/** 启动核对，返回停止函数（测试与正常收尾时可提前停）。父进程号不大于 1 时不启动、返回空函数。 */
export function startParentWatchdog(onGone: () => void, deps: ParentWatchdogDeps = {}): () => void {
  const getPpid = deps.getPpid ?? (() => process.ppid);
  const initial = getPpid();
  if (initial <= 1) return () => {};
  const timer = setInterval(() => {
    if (getPpid() === initial) return;
    clearInterval(timer);
    onGone();
  }, deps.intervalMs ?? PARENT_POLL_MS);
  timer.unref();
  return () => clearInterval(timer);
}
