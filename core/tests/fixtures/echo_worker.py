"""测试用假 worker：读 stdin 的 job JSON，吐预设 ADR 0024 事件到 stdout。

不接任何真引擎——只验证子进程 adapter 的 spawn/stdin/stdout/SIGTERM 管道（不烧 AWS）。
行为由环境变量控制：
  WORKER_MODE=pass   → 对每个 scenario 吐 started/step_done(passed)/scenario_done，最后 scope_done
  WORKER_MODE=hang   → 吐一个 started 后死循环（测 SIGTERM 停止 + 会话清理 finally）
  WORKER_MODE=crash  → 吐一个 started 后非零退出（测 worker 崩 → schedule 记 error）
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
    signal.signal(signal.SIGTERM, _on_sigterm)
    job = json.loads(sys.stdin.readline())
    mode = os.environ.get("WORKER_MODE", "pass")
    scope = job["scope"]

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
