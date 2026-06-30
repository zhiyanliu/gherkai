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
# AI 断言投票次数由 job.assertionVotes 决定（ADR 0014/0024，组合根经 --assertion-votes 设）。
# 默认 1（不抖动检测，结果直观）；调高才跑 N 次取多数票。

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


def _collect_traj(r, traj_sink: list[str]) -> None:
    """从 act/act_get 结果的 metadata 收集本次 act 的 trajectory **HTML** 路径（ADR 0027）。

    Nova 每次 act 出一对产物：`act_<id>_<prompt>_trajectory.json`（数据）+ `act_<id>_<prompt>.html`
    （人看的轨迹页）。metadata.trajectory_file_path 给的是 .json；归集索引要指向人能看的 .html，
    故从 json 路径推导 html（去 `_trajectory.json` 加 `.html`）。html 不存在则回退 json。
    收集进 traj_sink，scenario_done 边界聚合成 act 级 reportRefs（对称 Midscene 的 scope 级）。
    """
    md = getattr(r, "metadata", None)
    p = getattr(md, "trajectory_file_path", None) if md else None
    if not p:
        return
    p = str(p)
    if p.endswith("_trajectory.json"):
        html = p[: -len("_trajectory.json")] + ".html"
        if os.path.exists(html):
            p = html
    # 绝对化兜底：reportRef 是 file://<path>，相对路径会成坏 URI（host 被当成路径首段）且跨进程
    # cwd 歧义。SDK 通常已回绝对路径（cli 传绝对 NOVA_LOGS_DIR）；此处再 abspath 一道，防御相对漏网。
    traj_sink.append(os.path.abspath(p))


def _run_step(nova, scenario_id: str, step: dict, traj_sink: list[str], votes_n: int) -> str:
    """派发执行一个 step，吐 step_done 事件，返回该 step 的 status（passed/failed/error）。

    traj_sink：本 scenario 的 trajectory 路径累积器（每次 AI act 收一个，ADR 0027）。
    votes_n：AI 断言（Then）投票次数（来自 job.assertionVotes，ADR 0014）；1=不抖动检测。

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
                    # Nova 引擎是同步 worker：async handler 的断言不会被执行（返回 coroutine 即静默判 passed）。
                    # 显式报错而非静默假阳性——确定性 handler 必须同步（与 Nova SDK 同步模型一致）。
                    raise TypeError(
                        f"确定性 handler 不能是 async（Nova 引擎同步执行）：{getattr(handler, '__name__', handler)!r}"
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
            # AI 断言 + N 次投票（ADR 0014/0024）；votes_n=1 即单次判定（仍发 votes 标记这是 AI 断言）
            instruction = _instruction(text, step)  # 自然语言 + 多行参数（DataTable/DocString，ADR 0024）
            votes = []
            tw_total = 0.0  # N 票 time_worked_s 累加（修：原 last_cost 只算最后一票，votes>1 时欠计 (N-1)/N）
            for _ in range(votes_n):
                r = nova.act_get(instruction, BOOL_SCHEMA)
                votes.append(bool(r.matches_schema and r.parsed_response))
                c = _cost_from_result(r)  # 每票各自的原生量（Nova 每 act 独立报，对称累加而非覆盖）
                if c and c.get("time_worked_s") is not None:
                    tw_total += c["time_worked_s"]
                _collect_traj(r, traj_sink)
            yes = sum(votes)
            passed = yes > votes_n / 2
            ev = {
                "type": "step_done", "scenarioId": scenario_id, "stepIndex": idx,
                "status": "passed" if passed else "failed",
                "votes": {"yes": yes, "total": votes_n},
            }
            if tw_total > 0:
                ev["cost"] = {"time_worked_s": tw_total}  # 全 N 票合计
            if not passed:
                ev["errorType"] = "assertion_failed"
                ev["message"] = f"AI 断言未过多数票（{yes}/{votes_n}）：{text}"
            emit(ev)
            return "passed" if passed else "failed"

        # When / Given（非 URL）→ AI 动作（无 votes）
        r = nova.act(_instruction(text, step))
        _collect_traj(r, traj_sink)
        ev = {"type": "step_done", "scenarioId": scenario_id, "stepIndex": idx, "status": "passed"}
        cost = _cost_from_result(r)
        if cost:
            ev["cost"] = cost
        emit(ev)
        return "passed"

    except Exception as e:
        # 失败的 act 最需要看 trajectory——Nova 的 ActError 也带 metadata.trajectory_file_path
        # （SDK 在 finally 已写盘），同一 helper 收集（ADR 0027：失败 act 的产物不丢）。
        _collect_traj(e, traj_sink)
        # 诊断分类细化（ADR 0028）：act 中途若是网络瞬时故障（CDP 闪断等），标 network_error 比笼统
        # engine_error 更准——便于排查"是网络抖动还是 AI 真出错"。**仅分类、不触发重试/恢复**：act 不幂等，
        # schedule 的 job 级重试要求「会话未起（零 step_done）」，而此处 step_started 早已 emit、saw_step=True，
        # 双条件 AND 天然不满足；且本失败走 step_done 事件流（非退出码 80），core 侧 is_network=False。
        # 故"act 中途恢复"仍是 defer（ADR 0028），这里只把失败原因记准。
        emit({
            "type": "step_done", "scenarioId": scenario_id, "stepIndex": idx,
            "status": "error", "errorType": _classify_act_error(e), "message": f"{type(e).__name__}: {e}",
        })
        return "error"


# 只剥 ASCII 空白（与 Midscene 的 unquote 同集合）——不用裸 strip()：Python strip 剥 U+001C-1F/U+0085
# 而 JS trim 不剥、却剥 U+FEFF(BOM)，两个引擎分叉（BOM 能穿透 gherkin 进 text）。显式同集合保对称。
_ASCII_WS = " \t\r\n\f\v"


def _unquote(text: str) -> str:
    """step 自然语言外层若整体被引号包裹（QA 写 When "搜索 X"），剥掉外引号喂引擎。"""
    t = text.strip(_ASCII_WS)
    if len(t) >= 2 and t[0] == '"' and t[-1] == '"':
        return t[1:-1]
    return t


def _clean_cell(c: str) -> str:
    """单元格清洗（与 Midscene cleanCell 同一规则）：cell 内 | 与换行会破坏 markdown 表格行结构
    → | 转义成 \\|、换行压成空格，使每个 cell 仍占一格、表格结构忠实。"""
    return str(c).replace("|", "\\|").replace("\r\n", " ").replace("\r", " ").replace("\n", " ")


def _argument_text(arg: dict | None) -> str:
    """把 step 的多行参数（DataTable/DocString，ADR 0024/0025）拼成附加文本，接在 step 指令后喂 AI。

    - dataTable：rows（二维字符串数组）拼回 markdown 表格（| 分隔，还原 QA 在 .feature 写的样子，LLM 友好）。
    - docString：content 多行文本原样。
    两个引擎（Nova/Midscene）须同一拼法，保同一 feature 行为对称（ADR 0024）。
    注：rows 单元恒为字符串（core/wire 只发字符串）；_clean_cell 的 str() 仅防御，正常管线不可达非字符串。
    """
    if not arg:
        return ""
    kind = arg.get("kind")
    if kind == "dataTable":
        rows = arg.get("rows") or []
        if not rows:
            return ""
        return "\n".join("| " + " | ".join(_clean_cell(c) for c in row) + " |" for row in rows)
    if kind == "docString":
        return arg.get("content") or ""
    return ""


def _instruction(text: str, step: dict) -> str:
    """喂 AI 的完整指令 = 去引号的 step 自然语言 + （可选）多行参数（ADR 0024：text(+argument) 一起喂引擎）。"""
    base = _unquote(text)
    extra = _argument_text(step.get("argument"))
    return f"{base}\n{extra}" if extra else base


def _aggregate(statuses: list[str]) -> str:
    if any(s == "error" for s in statuses):
        return "error"
    if any(s == "failed" for s in statuses):
        return "failed"
    return "passed"


import socket
import ssl
import time

# 网络专用退出码（ADR 0028）：与 core/adapters/subprocess_engine.py 的 EX_WORKER_NETWORK 同值。
EX_WORKER_NETWORK = 80

# 建连重试参数（ADR 0028）：仅裹幂等的建连段，act 永不重试。退避手写（不用 botocore 内部 retry，
# 否则 SIGTERM 穿不透）；总退避预算 ~3.5s < schedule 默认 grace 5s。
_CONNECT_ATTEMPTS = 4
_BACKOFF_S = [0.5, 1.0, 2.0]  # attempt 失败后的退避；±20% jitter 由调用处加（这里固定，本地 smoke 够用）


def _is_transient_network(e: BaseException) -> bool:
    """是否网络/SSL 瞬时故障（可重试，ADR 0028）。

    白名单匹配**具体**瞬时类型，不用宽 OSError 兜底——ssl.SSLError 与 socket.gaierror 都继承 OSError，
    宽匹配会把永久错也当瞬时重试。gaierror 按 errno 细分：EAI_AGAIN(临时) 当瞬时、其余(EAI_NONAME 等永久) 否决
    （对齐 Midscene 的 EAI_AGAIN 白名单，保两腿对 DNS 临时抖动恢复力对称，ADR 0028）。

    **遍历异常链**（__cause__/__context__）：Nova/boto SDK 常把底层 ssl.SSLError 包成自有异常
    （BrowserAuthError 等），只看最外层会漏判——任一层命中白名单即判瞬时（用 id 集防环）。
    """
    transient: tuple[type[BaseException], ...] = (ssl.SSLError, ConnectionError, TimeoutError, socket.timeout)
    try:
        from botocore.exceptions import EndpointConnectionError, ConnectionClosedError
        transient += (EndpointConnectionError, ConnectionClosedError)
    except ImportError:
        pass
    try:
        from urllib3.exceptions import ProtocolError
        transient += (ProtocolError,)
    except ImportError:
        pass

    seen: set[int] = set()
    cur: BaseException | None = e
    while cur is not None and id(cur) not in seen:
        seen.add(id(cur))
        if isinstance(cur, socket.gaierror):
            # DNS 解析失败：按 errno 细分（gaierror 同时覆盖临时与永久，不能一律否决）——
            # EAI_AGAIN(临时，可重试，对齐 Midscene 的 EAI_AGAIN 白名单) → 瞬时；其余(EAI_NONAME 等永久) → 否决。
            return cur.args[0] == socket.EAI_AGAIN if cur.args else False
        if isinstance(cur, transient):
            return True
        cur = cur.__cause__ or cur.__context__
    return False


def _classify_act_error(e: BaseException) -> str:
    """把 act/act_get 中途异常映射到规范化 errorType（ADR 0024/0028）。优先级：
    网络瞬时 > Nova SDK 异常树（timeout/guardrail/…）> engine_error 兜底。
    **仅诊断分类、不影响重试/恢复**（act 不幂等，恢复仍 defer，ADR 0028）。
    Nova SDK 异常树现成且结构化（act_errors.py），把 timeout/guardrail 从笼统 engine_error 拆出，
    便于排查与未来按类型处置（ADR 0024「errorType 已实现但粗粒度，留待细化」的兑现）。"""
    if _is_transient_network(e):
        return "network_error"
    try:
        from nova_act.types.act_errors import (
            ActTimeoutError, ActGuardrailsError, ActStateGuardrailError,
        )
        timeout_types: tuple[type[BaseException], ...] = (ActTimeoutError,)
        guardrail_types: tuple[type[BaseException], ...] = (ActGuardrailsError, ActStateGuardrailError)
    except ImportError:
        return "engine_error"
    if isinstance(e, timeout_types):
        return "timeout"
    if isinstance(e, guardrail_types):
        return "guardrail"
    return "engine_error"  # 其余执行故障（含未细分的 ActError 子类）仍归 engine_error


class _NetworkExhausted(BaseException):
    """建连重试耗尽（ADR 0028）。

    在重试循环里 raise——此时本次失败 attempt 的 `with cdp_session`/`with NovaAct`（在 _run_session 内）
    **已随该次异常解栈、__exit__ 已跑**（释放了本次可能部分建起的会话），故 raise 点已无会话级 with 在身上。
    继承 BaseException（同 _Terminated）使它穿过外层 `with wf` 的 finally（恢复 workflow contextvar）
    冒泡到 main 顶层 `except _NetworkExhausted` → `return EX_WORKER_NETWORK`。不在 with 内裸 sys.exit。
    """


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
    votes_n = int(job.get("assertionVotes", 1))  # AI 断言投票次数（ADR 0014/0024）；缺省 1
    session_id = None

    def _on_sigterm(signum, frame):
        # 不在这里 sys.exit（那样会跳过 with 的 __exit__、泄漏 AgentCore 会话）；
        # 而是 raise，让异常冒泡触发三层 with 的自然清理（ADR 0024）。
        log("worker: SIGTERM received, unwinding for clean session shutdown")
        raise _Terminated()

    signal.signal(signal.SIGTERM, _on_sigterm)

    ensure_workflow_definition(WORKFLOW_DEF, region=REGION, description="Nova Act worker (ADR 0024)")
    wf = Workflow(model_id=MODEL_ID, boto_session_kwargs={"region_name": REGION}, workflow_definition_name=WORKFLOW_DEF)
    # 建连重试状态（ADR 0028）：started 一旦 True（scope_started 已 emit、会话已起），
    # 任何后续异常都不再当「可重试建连失败」——act 已可能跑、有副作用，绝不重试。
    started = False

    def _run_session() -> None:
        """建连 + 跑完所有 scenarios。建连段异常可被外层重试；scope_started emit 后不可。"""
        nonlocal session_id, started
        provider = AgentCoreBrowserSessionProvider(region=REGION)
        with provider.cdp_session() as (ws_url, headers):
            # logs_directory：trajectory 落到 run 专属持久目录（ADR 0027）。cli 经环境变量
            # NOVA_LOGS_DIR 传入 reports/<run_id>/nova-trajectories；无则用 SDK 默认临时目录
            # （会被系统清理）。Nova 的 validate_path 要求该目录**已存在**，故先 mkdir。
            logs_dir = os.environ.get("NOVA_LOGS_DIR") or None
            if logs_dir:
                os.makedirs(logs_dir, exist_ok=True)
            with NovaAct(
                cdp_endpoint_url=ws_url, cdp_headers=headers, browser_auth=provider,
                starting_page="about:blank", logs_directory=logs_dir,
                # tty=False：worker 是 cli spawn 的子进程，stdout/stderr 是管道而非交互终端。
                # SDK 默认 tty=True 会喷逐帧刷新的思考动画（💭 . / 💭 .. / 🎬 …），在管道里成了刷屏噪声；
                # 关掉后输出干净的逐行日志（think/return/Approx. Time Worked 等有用行保留）。SDK 文档亦推荐非 tty 场景置 False。
                tty=False,
            ) as nova:
                # 取真实 AgentCore 会话 id（血缘，进 scope_done → RunStore，ADR 0016/0024）。
                session_id = nova.get_session_id()
                emit({"type": "scope_started", "scopeId": scope["id"]})  # 三级时长起点
                started = True  # 越过此点 = 会话已起、act 即将跑 → 退出建连重试域（ADR 0028）
                # scope 内串行跑 scenarios，共享同一会话（ADR 0019/0024）
                for sc in scenarios:
                    sid = sc["id"]
                    emit({"type": "scenario_started", "scenarioId": sid})
                    traj: list[str] = []  # 本 scenario 的 trajectory 路径累积（ADR 0027）
                    statuses = [_run_step(nova, sid, st, traj, votes_n) for st in sc["steps"]]
                    # act 级 reportRefs：每个 trajectory 一条，经 scenario_done 回传（对称 Midscene scope 级）
                    report_refs = [
                        {"kind": "act", "ref": f"file://{p}", "label": f"trajectory {i + 1}"}
                        for i, p in enumerate(traj)
                    ]
                    emit({
                        "type": "scenario_done", "scenarioId": sid,
                        "status": _aggregate(statuses), "reportRefs": report_refs,
                    })

    try:
        with wf:
            outer = get_current_workflow()
            set_current_workflow(wf)
            try:
                # 建连重试循环（ADR 0028）：仅裹建连段；scope_started 一 emit 即 started=True、跳出重试。
                # 每次 attempt 用全新 provider/cdp_session/NovaAct，with __exit__ 清掉本次部分建起的会话。
                for attempt in range(_CONNECT_ATTEMPTS):
                    try:
                        _run_session()
                        break  # 成功（跑完）
                    except _Terminated:
                        raise  # SIGTERM：交三层 with 清理，不重试
                    except BaseException as e:  # noqa: BLE001
                        if started or not _is_transient_network(e):
                            raise  # 会话已起 / 非瞬时网络错 → 不重试，原样冒泡
                        if attempt >= _CONNECT_ATTEMPTS - 1:
                            log(f"worker: 建连重试耗尽（{attempt + 1} 次），网络/SSL 瞬时故障：{e}")
                            raise _NetworkExhausted() from e
                        backoff = _BACKOFF_S[min(attempt, len(_BACKOFF_S) - 1)]
                        log(f"worker: 建连失败（attempt {attempt + 1}），{backoff}s 后重试：{e}")
                        time.sleep(backoff)  # 手写退避：SIGTERM handler raise 可中途打断（_Terminated 冒泡）
            finally:
                set_current_workflow(outer)
    except _Terminated:
        # SIGTERM：三层 with 的 __exit__ 已在冒泡过程中跑完（会话已释放）。干净退出，不吐 scope_done。
        log("worker: session shutdown complete after SIGTERM")
        return 0
    except _NetworkExhausted:
        # 建连重试耗尽（ADR 0028）：三层 with __exit__ 已清理。以网络专用退出码退出，
        # core 据此记 network_error 并可选择性重试整 job。不吐 scope_done。
        log("worker: connect retries exhausted, exiting with network code")
        return EX_WORKER_NETWORK

    emit({"type": "scope_done", "scopeId": scope["id"], "sessionId": session_id})
    return 0


if __name__ == "__main__":
    sys.exit(main())
