"""Nova Act 薄 worker（ADR 0022/0024）：读 stdin 的 job JSON → 跑一个 scope → 吐 0024 事件到 stdout。

这是从 bdd/test_generic_steps.py 改造而来：脱掉 pytest-bdd 装饰器，逻辑（开会话/act/投票/派发）原样复用。
core 经子进程 adapter 起本 worker（ADR 0026 机制层），讲 0024 协议。

一生（ADR 0024）：
  读 stdin job → 开 AgentCore 会话 → 按 scope 串行跑 scenarios（每 step 派发）→ 逐事件吐 stdout
  → scope_done → 退出。捕获 SIGTERM：finally 停会话（终止契约）。

派发（ADR 0020/0024）：
  step.text 含 URL 字面量（引号内 https?://）→ 内建确定性导航 go_to_url（不浪费 AI）
  keyword=When → act（AI 动作，无 votes）
  keyword=Then → act_get(BOOL) + N 次投票（AI 断言，带 votes）
  keyword=Given 且非 URL → 也走 act（前置动作）

cost（ADR 0024）：Nova Act 按 agent-hour 计费，cost_usd = time_worked_s/3600 × rate（默认 4.75）。

跑（一般由 core adapter spawn，也可手动）：
  echo '<job json>' | AWS_REGION=us-east-1 .venv/bin/python worker/run_scope.py
"""
from __future__ import annotations

import json
import os
import re
import signal
import sys
from pathlib import Path

from nova_act import NovaAct, AgentCoreBrowserSessionProvider, BOOL_SCHEMA, Workflow
from nova_act.types.workflow import set_current_workflow, get_current_workflow

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # novaact/ 根，便于 import lib
from lib.workflow_setup import ensure_workflow_definition

REGION = os.environ.get("AWS_REGION", "us-east-1")
MODEL_ID = "nova-act-latest"
WORKFLOW_DEF = "spike-wikipedia-benchmark"
VOTES = 3  # AI 断言投票次数（治种类A抖动，ADR 0014）
NOVA_USD_PER_AGENT_HOUR = 4.75  # ADR 0024，来源 aws.amazon.com/nova/pricing

_URL_IN_QUOTES = re.compile(r'"(https?://[^"]+)"')

# 三通道分离（ADR 0024）：0024 事件走专用 fd（core adapter 读这个），与 SDK 打到 stdout 的进度噪声、
# worker 自己的诊断（stderr）物理隔离。adapter 经环境变量 EVENTS_FD 告知该 fd 号（pass_fds 继承，号不固定）。
# 无 EVENTS_FD（手动直跑、无 adapter）时回落 stdout，便于调试（`echo job | worker` 仍能看事件）。
_events_fd = os.environ.get("EVENTS_FD")
try:
    _events_out = os.fdopen(int(_events_fd), "w", encoding="utf-8") if _events_fd else sys.stdout
except (OSError, ValueError):
    _events_out = sys.stdout


def emit(obj: dict) -> None:
    """吐一条 0024 事件到事件通道（fd3，JSON Lines，字段名 camelCase 与 core/wire.py 一致）。"""
    _events_out.write(json.dumps(obj, ensure_ascii=False) + "\n")
    _events_out.flush()


def log(msg: str) -> None:
    sys.stderr.write(f"{msg}\n")
    sys.stderr.flush()


def _cost_from_result(r) -> dict | None:
    """从 act/act_get 结果的 metadata.time_worked_s 算 agent_time cost（ADR 0024）。"""
    md = getattr(r, "metadata", None)
    if md is None:
        return None
    tw = getattr(md, "time_worked_s", None)
    if tw is None:
        return None
    cost_usd = tw / 3600.0 * NOVA_USD_PER_AGENT_HOUR
    return {
        "cost_usd": round(cost_usd, 6),
        "precision": "estimated",  # agent_time → estimated（ADR 0024）
        "basis": "agent_time",
        "evidence": {
            "time_worked_s": tw,
            "human_wait_time_s": getattr(md, "human_wait_time_s", 0.0),
            "num_steps_executed": getattr(md, "num_steps_executed", None),
        },
    }


def _run_step(nova, scenario_id: str, step: dict) -> str:
    """派发执行一个 step，吐 step_done 事件，返回该 step 的 status（passed/failed/error）。"""
    idx = step["index"]
    keyword = step["keyword"]
    text = step["text"]

    try:
        url_match = _URL_IN_QUOTES.search(text)
        if url_match:
            # 内建确定性导航（ADR 0020）：抽 URL 直接 go_to_url，不浪费 AI
            nova.go_to_url(url_match.group(1))
            emit({"type": "step_done", "scenarioId": scenario_id, "stepIndex": idx, "status": "passed"})
            return "passed"

        if keyword == "Then":
            # AI 断言 + N 次投票（ADR 0014/0024）
            votes = []
            last_cost = None
            for _ in range(VOTES):
                r = nova.act_get(_unquote(text), BOOL_SCHEMA)
                votes.append(bool(r.matches_schema and r.parsed_response))
                last_cost = _cost_from_result(r)
            yes = sum(votes)
            passed = yes > VOTES / 2
            ev = {
                "type": "step_done", "scenarioId": scenario_id, "stepIndex": idx,
                "status": "passed" if passed else "failed",
                "votes": {"yes": yes, "total": VOTES},
            }
            if last_cost:
                ev["cost"] = last_cost
            if not passed:
                ev["errorType"] = "assertion_failed"
                ev["message"] = f"AI 断言未过多数票（{yes}/{VOTES}）：{text}"
            emit(ev)
            return "passed" if passed else "failed"

        # When / Given（非 URL）→ AI 动作（无 votes）
        r = nova.act(_unquote(text))
        ev = {"type": "step_done", "scenarioId": scenario_id, "stepIndex": idx, "status": "passed"}
        cost = _cost_from_result(r)
        if cost:
            ev["cost"] = cost
        emit(ev)
        return "passed"

    except Exception as e:
        emit({
            "type": "step_done", "scenarioId": scenario_id, "stepIndex": idx,
            "status": "error", "errorType": "engine_error", "message": f"{type(e).__name__}: {e}",
        })
        return "error"


def _unquote(text: str) -> str:
    """step 人话外层若整体被引号包裹（QA 写 When "搜索 X"），剥掉外引号喂引擎。"""
    t = text.strip()
    if len(t) >= 2 and t[0] == '"' and t[-1] == '"':
        return t[1:-1]
    return t


def _aggregate(statuses: list[str]) -> str:
    if any(s == "error" for s in statuses):
        return "error"
    if any(s == "failed" for s in statuses):
        return "failed"
    return "passed"


def main() -> int:
    job = json.loads(sys.stdin.readline())
    scope = job["scope"]
    scenarios = job["scenarios"]

    nova = None
    session_id = None

    def _on_sigterm(signum, frame):
        # 终止契约（ADR 0024）：收到 SIGTERM → 关会话再退。with 块的 __exit__ 在 sys.exit 时不一定跑，
        # 故这里显式关。
        log("worker: SIGTERM received, closing AgentCore session")
        try:
            if nova is not None:
                nova.close()
        except Exception:
            pass
        sys.exit(0)

    signal.signal(signal.SIGTERM, _on_sigterm)

    ensure_workflow_definition(WORKFLOW_DEF, region=REGION, description="Nova Act worker (ADR 0024)")
    wf = Workflow(model_id=MODEL_ID, boto_session_kwargs={"region_name": REGION}, workflow_definition_name=WORKFLOW_DEF)
    with wf:
        outer = get_current_workflow()
        set_current_workflow(wf)
        try:
            provider = AgentCoreBrowserSessionProvider(region=REGION)
            with provider.cdp_session() as (ws_url, headers):
                with NovaAct(
                    cdp_endpoint_url=ws_url, cdp_headers=headers, browser_auth=provider,
                    starting_page="about:blank",
                ) as nova:
                    # 取真实 AgentCore 会话 id（血缘，进 scope_done → RunStore，ADR 0016/0024）。
                    # NovaAct 已 started，get_session_id() 安全。
                    session_id = nova.get_session_id()
                    # scope 内串行跑 scenarios，共享同一会话（ADR 0019/0024）
                    for sc in scenarios:
                        sid = sc["id"]
                        emit({"type": "scenario_started", "scenarioId": sid})
                        statuses = [_run_step(nova, sid, st) for st in sc["steps"]]
                        emit({"type": "scenario_done", "scenarioId": sid, "status": _aggregate(statuses)})
        finally:
            set_current_workflow(outer)

    emit({
        "type": "scope_done", "scopeId": scope["id"], "sessionId": session_id,
        "costRate": {"nova_act_usd_per_agent_hour": NOVA_USD_PER_AGENT_HOUR},
    })
    return 0


if __name__ == "__main__":
    sys.exit(main())
