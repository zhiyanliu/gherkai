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
    # 模拟 worker 的会话清理（ADR 0024 终止契约）：打一条到 stderr 证明 finally 跑了
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
    job = json.loads(sys.stdin.readline())
    mode = os.environ.get("WORKER_MODE", "pass")
    scope = job["scope"]

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


if __name__ == "__main__":
    main()
