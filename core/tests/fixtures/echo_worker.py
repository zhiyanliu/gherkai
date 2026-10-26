"""测试用假 worker：读 stdin 的 job JSON，吐预设 ADR 0024 事件到 stdout。

不接任何真引擎——只验证子进程 adapter 的 spawn/stdin/stdout/SIGTERM 管道（不产生 AWS 费用）。
行为由环境变量控制：
  WORKER_MODE=pass   → 对每个 scenario 吐 started/step_done(passed)/scenario_done，最后 scope_done
  WORKER_MODE=hang   → 吐一个 started 后死循环（测 SIGTERM 停止 + 会话清理 finally）
  WORKER_MODE=crash  → 吐一个 started 后非零退出（测 worker 崩 → schedule 记 error）
  WORKER_MODE=net    → 不吐任何事件，直接以 EX_WORKER_NETWORK(80) 退出
                       （模拟建连失败先于事件 emit → adapter 翻 WorkerNetworkError → schedule 记 network_error，ADR 0028）
  WORKER_MODE=silent → 先吐 scope_started（带 sessionId）+ scenario_started，然后**静默死循环不再吐任何事件**
                       （模拟 act 卡在单次调用内、fd3 无新事件 → 测 adapter 读超时心跳让 schedule 超时能触发 +
                        session_id 经 scope_started 提前回传，ADR 0028）
  WORKER_MODE=deaf   → **忽略 SIGTERM**（SIG_IGN），吐 scope_started 后死循环不退——模拟 worker 无视优雅停
                       （如真卡死、handler 失效）。测 adapter 的 terminate→grace 超时→**SIGKILL 兜底**分支
                       （SubprocessWorkerHandle.stop 的 TimeoutExpired→proc.kill()），这条尾路径其余 mode 都不踩。
  WORKER_MODE=done_then_deaf → 发完全部事件（含 scope_done）后忽略 SIGTERM、永不退出（模拟收尾挂死）——测 schedule 在
                       内容完整后 deadline 到点催停、宽限耗尽强杀、管道 EOF 后按负退出码回判（ADR 0034 机制二）
  WORKER_MODE=done_then_deaf_fdholder → 同 done_then_deaf，但先起一个持有事件管道写端的子进程（pid 追加进 WORKER_PID_FILE）：
                       本进程被强杀后管道仍不 EOF，core 只能靠排空上界结束消费（模拟包装进程留下的孙进程仍持有写端）
  WORKER_MODE=done_then_slow → 发完全部事件后等 SIGTERM 再以 0 退出（模拟收尾拖过预算但协作退出）——判定按内容、不记超时
  WORKER_MODE=bad_line → 吐 scope_started 后写一行不是 JSON 的东西，然后等 SIGTERM——测 core 解析失败后仍停掉活着的 worker
  mode 也可以由 job 的 scope.name 以 "mode:<名>" 指定：同一个 engine 实例下的各个 job 由此使用不同的行为（需要多个 job 同时运行的 fail-fast 测试会用到）。
  WORKER_PID_FILE=<路径> → 启动时把自己的 pid 写进去（测试据此确认进程确已被回收）。

EVENTS: 真 worker 的 scope_started 带 sessionId（ADR 0028 血缘随首事件回传），echo 也带，保协议一致。
"""
import json
import os
import signal
import sys
import time

_stopped = False


def _on_sigterm(signum, frame):
    global _stopped
    _stopped = True
    # 模拟 worker 的会话清理（ADR 0024 终止契约）：打一条到 stderr 证明 finally 执行了
    sys.stderr.write("echo_worker: SIGTERM received, cleaning up session\n")
    sys.stderr.flush()
    sys.exit(0)


# ADR 0024 事件走 EVENTS_FD 指定的 fd（与真 worker 一致，ADR 0024 三通道分离）；无则回落 stdout
_events_fd = os.environ.get("EVENTS_FD")
try:
    _events_out = os.fdopen(int(_events_fd), "w", encoding="utf-8") if _events_fd else sys.stdout
except (OSError, ValueError):
    _events_out = sys.stdout


def emit(obj):
    _events_out.write(json.dumps(obj, ensure_ascii=False) + "\n")
    _events_out.flush()


def main():
    # WORKER_NOISE_BYTES：**读 stdin 之前**往 stdout 灌 N 字节（模拟 SDK import 期噪声）——只有发生在读 stdin 之前才能
    # 复现「父卡 stdin.write、子卡 stdout.write」的互锁；放在读 stdin 之后就测不到（adapter 的 pump 线程顺序护栏用）。
    noise = int(os.environ.get("WORKER_NOISE_BYTES", "0"))
    if noise:
        sys.stdout.write("x" * noise + "\n")
        sys.stdout.flush()
    job = json.loads(sys.stdin.readline())
    scope = job["scope"]
    mode = os.environ.get("WORKER_MODE", "pass")
    if isinstance(scope.get("name"), str) and scope["name"].startswith("mode:"):
        mode = scope["name"][len("mode:"):]
    pid_file = os.environ.get("WORKER_PID_FILE")
    if pid_file:
        with open(pid_file, "a", encoding="utf-8") as fh:
            fh.write(f"{os.getpid()}\n")

    if mode == "deaf":
        # 忽略 SIGTERM（模拟无视优雅停/handler 失效）→ 逼 adapter 走 grace 超时 → SIGKILL 兜底。
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
    else:
        signal.signal(signal.SIGTERM, _on_sigterm)

    if mode == "net":
        # 建连失败先于任何事件 emit（ADR 0028）：直接以网络专用退出码退出，不吐 scope_started。
        sys.stderr.write("echo_worker: simulated connect failure, exiting EX_WORKER_NETWORK\n")
        sys.exit(80)

    # scope_started 带 sessionId（ADR 0028：血缘随首事件回传，超时/中止 scope_done 缺席时 core 仍记得到）。
    emit({"type": "scope_started", "scopeId": scope["id"], "sessionId": "echo-sess"})

    if mode == "deaf":
        # 吐 scope_started 后死循环、**不响应 SIGTERM**（SIG_IGN）→ adapter grace 超时后 SIGKILL 强杀。
        while True:
            time.sleep(0.05)

    if mode == "bad_line":
        # 一行不是 JSON 的东西：core 的 wire 解析抛错 → schedule 走普通异常分支，须向本进程发停止请求（否则本进程一直活着）
        _events_out.write("this is not json\n")
        _events_out.flush()
        while not _stopped:
            time.sleep(0.05)
        return

    if mode == "silent":
        # 吐 scope_started + scenario_started 后**静默死循环**（不再吐任何事件、不退出）——模拟
        # act 卡在单次调用内 fd3 无新事件。测 adapter 读超时心跳让 schedule 的 deadline 检查能触发（ADR 0028）。
        emit({"type": "scenario_started", "scenarioId": job["scenarios"][0]["id"]})
        while not _stopped:
            time.sleep(0.05)
        return

    for sc in job["scenarios"]:
        sid = sc["id"]
        emit({"type": "scenario_started", "scenarioId": sid})
        if mode == "hang":
            while not _stopped:
                time.sleep(0.05)
            return
        if mode == "crash":
            sys.stderr.write("echo_worker: simulated crash\n")
            sys.exit(3)
        for step in sc["steps"]:
            ev = {"type": "step_done", "scenarioId": sid, "stepIndex": step["index"], "status": "passed"}
            if step["keyword"] == "Then":
                ev["votes"] = {"yes": 3, "total": 3}
            emit(ev)
        emit({"type": "scenario_done", "scenarioId": sid, "status": "passed"})

    emit({"type": "scope_done", "scopeId": scope["id"], "sessionId": "echo-sess"})

    if mode in ("done_then_deaf", "done_then_deaf_fdholder"):
        if mode == "done_then_deaf_fdholder" and _events_fd:
            # 一个只会睡觉的子进程继承事件管道的写端：本进程被强杀后它仍持有写端、管道不 EOF；pid 追加进 pid 文件供测试回收
            import subprocess
            child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(120)"], pass_fds=(int(_events_fd),))
            if pid_file:
                with open(pid_file, "a", encoding="utf-8") as fh:
                    fh.write(f"{child.pid}\n")
        # 内容已完整，收尾却挂死且无视 SIGTERM：只有 SIGKILL 能结束本进程（无孙进程持写端时管道随之 EOF、退出码为负）
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        while True:
            time.sleep(0.05)
    if mode == "done_then_slow":
        # 内容已完整，收尾拖到被催停才退出（协作、退出码 0）
        while not _stopped:
            time.sleep(0.05)


if __name__ == "__main__":
    main()
