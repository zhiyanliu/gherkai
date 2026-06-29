"""Nova Act 薄 worker（ADR 0022/0024）：读 stdin 的 job JSON → 跑一个 scope → 吐 ADR 0024 事件到事件通道。

不含 BDD runner 装饰器：会话/act/投票/派发逻辑直接在本进程跑（ADR 0022 薄 worker）。
core 经子进程 adapter 起本 worker（ADR 0026 机制层），讲 ADR 0024 协议。

三通道分离（ADR 0024）：协议事件吐到 EVENTS_FD 指定的 fd（无则回落 stdout，便于手动直跑调试）；
引擎 SDK 的进度噪声留 stdout；worker 自身诊断/日志走 stderr。

一生（ADR 0024）：
  读 stdin job → 开 AgentCore 会话 → 按 scope 串行跑 scenarios（每 step 派发）→ 逐事件吐事件通道
  → scope_done → 退出。SIGTERM：handler raise _Terminated → 三层 with 解栈释放会话（终止契约）。

派发（ADR 0020/0024）：
  step.text 含 URL 字面量（引号内 https?://）→ 内建确定性导航 go_to_url（不浪费 AI）
  keyword=When → act（AI 动作，无 votes）
  keyword=Then → act_get(BOOL) + N 次投票（AI 断言，带 votes）
  keyword=Given 且非 URL → 也走 act（前置动作）

cost（ADR 0024）：Nova SDK 原生给 time_worked_s，worker 只报该原生量；core 合计、美元折算交消费者（不内置费率）。

跑（一般由 core adapter spawn，也可手动）：
  echo '<job json>' | AWS_REGION=us-east-1 .venv/bin/python worker/run_scope.py
"""
from __future__ import annotations

import inspect
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

# 确定性 step 注册表（ADR 0022）+ test engineer 的锚点脚手架。
# 先 import 注册机制（提供 @deterministic 装饰器），再 import 脚手架——脚手架顶层的
# @deterministic 在 import 时执行，把锚点登记进 _deterministic._REGISTRY。
import deterministic as _deterministic  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "bdd"))  # 便于 import deterministic_steps
import deterministic_steps  # noqa: E402,F401  仅为触发注册（其顶层 @deterministic 副作用）

REGION = os.environ.get("AWS_REGION", "us-east-1")
MODEL_ID = "nova-act-latest"
WORKFLOW_DEF = "spike-wikipedia-benchmark"
VOTES = 3  # AI 断言投票次数（治种类A抖动，ADR 0014）

_URL_IN_QUOTES = re.compile(r'"(https?://[^"]+)"')


class _DeterministicCtx:
    """传给确定性 handler 的上下文：暴露 Playwright `page`（精确 DOM/URL 查，不走 AI）。

    Nova 把底层 Playwright Page 暴露在 `nova.page`（spike 已验证）。handler 拿它做
    `ctx.page.url` / `ctx.page.locator(...)` 这类确定性判定。
    """

    def __init__(self, nova) -> None:
        self._nova = nova

    @property
    def page(self):
        return self._nova.page

# 三通道分离（ADR 0024）：协议事件走专用 fd（core adapter 读这个），与 SDK 打到 stdout 的进度噪声、
# worker 自己的诊断（stderr）物理隔离。adapter 经环境变量 EVENTS_FD 告知该 fd 号（pass_fds 继承，号不固定）。
# 无 EVENTS_FD（手动直跑、无 adapter）时回落 stdout，便于调试（`echo job | worker` 仍能看事件）。
_events_fd = os.environ.get("EVENTS_FD")
try:
    _events_out = os.fdopen(int(_events_fd), "w", encoding="utf-8") if _events_fd else sys.stdout
except (OSError, ValueError):
    _events_out = sys.stdout


def emit(obj: dict) -> None:
    """吐一条 ADR 0024 事件到事件通道（fd3，JSON Lines，字段名 camelCase 与 core/wire.py 一致）。"""
    _events_out.write(json.dumps(obj, ensure_ascii=False) + "\n")
    _events_out.flush()


def log(msg: str) -> None:
    sys.stderr.write(f"{msg}\n")
    sys.stderr.flush()


def _cost_from_result(r) -> dict | None:
    """报 Nova SDK 原生量 time_worked_s（ADR 0024：engine 只报原生量，core 不算美元）。"""
    md = getattr(r, "metadata", None)
    if md is None:
        return None
    tw = getattr(md, "time_worked_s", None)
    if tw is None:
        return None
    return {"time_worked_s": tw}


def _run_step(nova, scenario_id: str, step: dict) -> str:
    """派发执行一个 step，吐 step_done 事件，返回该 step 的 status（passed/failed/error）。

    派发优先级（ADR 0022/0020/0024）：
      ① 确定性注册表命中（test engineer 注册的精确 handler，不投票、可复现）
      ② 内建 URL 导航（step 含引号内 URL）
      ③ Then → AI 断言 + 投票 / When·Given → AI 动作（默认 catch-all）
    """
    idx = step["index"]
    keyword = step["keyword"]
    text = step["text"]

    emit({"type": "step_started", "scenarioId": scenario_id, "stepIndex": idx})  # step 时长起点
    try:
        # ① 确定性注册表（ADR 0022）：命中走精确 handler、不投票；AssertionError→failed，其它→error
        hit = _deterministic.match(text)
        if hit is not None:
            handler, groups = hit
            ctx = _DeterministicCtx(nova)
            try:
                ret = handler(ctx, **groups)
                if inspect.isawaitable(ret):
                    # Nova 腿是同步 worker：async handler 的断言不会被执行（返回 coroutine 即静默判 passed）。
                    # 显式报错而非静默假阳性——确定性 handler 必须同步（与 Nova SDK 同步模型一致）。
                    raise TypeError(
                        f"确定性 handler 不能是 async（Nova 腿同步执行）：{getattr(handler, '__name__', handler)!r}"
                    )
            except AssertionError as ae:
                emit({
                    "type": "step_done", "scenarioId": scenario_id, "stepIndex": idx,
                    "status": "failed", "errorType": "assertion_failed",
                    "message": str(ae) or f"确定性断言未过：{text}",
                })
                return "failed"
            emit({"type": "step_done", "scenarioId": scenario_id, "stepIndex": idx, "status": "passed"})
            return "passed"

        url_match = _URL_IN_QUOTES.search(text)
        if url_match:
            # ② 内建确定性导航（ADR 0020）：抽 URL 直接 go_to_url，不浪费 AI
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


class _Terminated(BaseException):
    """SIGTERM 转成的异常（ADR 0024 终止契约）。

    继承 BaseException 而非 Exception——这样它不会被 _run_step 的 `except Exception` 误吞，
    而是穿透 step 级 catch、向上冒泡，触发三层 with（NovaAct / cdp_session / workflow）的
    __exit__ 按序跑完整清理链。AgentCore 会话释放在 cdp_session 内的 `with browser_session`
    那层（实测 agentcore_session_provider.cdp_session），靠它的 __exit__ 真正关会话——
    手动 nova.close() 只关 Playwright 连接、关不掉 AgentCore 会话（会继续烧钱）。
    """


def main() -> int:
    job = json.loads(sys.stdin.readline())
    scope = job["scope"]
    scenarios = job["scenarios"]
    session_id = None

    def _on_sigterm(signum, frame):
        # 不在这里 sys.exit（那样会跳过 with 的 __exit__、泄漏 AgentCore 会话）；
        # 而是 raise，让异常冒泡触发三层 with 的自然清理（ADR 0024）。
        log("worker: SIGTERM received, unwinding for clean session shutdown")
        raise _Terminated()

    signal.signal(signal.SIGTERM, _on_sigterm)

    ensure_workflow_definition(WORKFLOW_DEF, region=REGION, description="Nova Act worker (ADR 0024)")
    wf = Workflow(model_id=MODEL_ID, boto_session_kwargs={"region_name": REGION}, workflow_definition_name=WORKFLOW_DEF)
    try:
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
                        session_id = nova.get_session_id()
                        emit({"type": "scope_started", "scopeId": scope["id"]})  # 三级时长起点
                        # scope 内串行跑 scenarios，共享同一会话（ADR 0019/0024）
                        for sc in scenarios:
                            sid = sc["id"]
                            emit({"type": "scenario_started", "scenarioId": sid})
                            statuses = [_run_step(nova, sid, st) for st in sc["steps"]]
                            emit({"type": "scenario_done", "scenarioId": sid, "status": _aggregate(statuses)})
            finally:
                set_current_workflow(outer)
    except _Terminated:
        # SIGTERM：三层 with 的 __exit__ 已在冒泡过程中跑完（会话已释放）。干净退出，不吐 scope_done。
        log("worker: session shutdown complete after SIGTERM")
        return 0

    emit({"type": "scope_done", "scopeId": scope["id"], "sessionId": session_id})
    return 0


if __name__ == "__main__":
    sys.exit(main())
