"""wire 协议（ADR 0024）：core↔worker 的 JSON 序列化层 + 退出码约定。

core 把 Job 序列化成 JSON 喂 worker stdin；worker 逐行吐 ADR 0024 事件到专用事件通道（fd，号经
EVENTS_FD 传给 worker；非 stdout——stdout 留给引擎 SDK 噪声，ADR 0024 三通道分离），
core 读行反序列化成 model.Event。这是两端（core 子进程 adapter + 语言无关的 worker）共用的形状约定。

事件行之外，协议还有一条 **out-of-band 通道：worker 退出码**（建连失败早于任何事件 emit，走不了事件
通道，ADR 0024「退出码约定」/ 0028）——故 `EX_WORKER_NETWORK` 与「退出码 → 异常」的翻译也归这里，
各 Engine adapter 只负责把自己传输里的码取出来交给它（见文件末段）。

设计：dataclass ↔ plain dict ↔ JSON。事件按 "type" 字段分派回正确的 Event 子类。
保持手写映射（不靠 dataclasses.asdict 自动），因为 wire 形状是跨语言契约——
worker 可能是 Python 或 Node，两端都按这里的 JSON 形状实现，必须显式、稳定。
"""
from __future__ import annotations

import json

from gherkai_core.errors import WorkerExitError, WorkerNetworkError
from gherkai_core.redact import redact_url_userinfo
from gherkai_core.model import (
    Cost,
    Event,
    Job,
    ReportRef,
    ResourceUri,
    Scenario,
    ScenarioDone,
    ScenarioStarted,
    ScopeDone,
    ScopeStarted,
    SessionClosed,
    SessionOpened,
    Status,
    Step,
    StepArgument,
    StepDone,
    StepSkipped,
    StepStarted,
    Votes,
)


# ============================================================================
# core → worker：Job 序列化
# ============================================================================


def _argument_to_json(arg: StepArgument | None) -> dict | None:
    if arg is None:
        return None
    if arg.kind == "docString":
        return {"kind": "docString", "content": arg.content}
    return {"kind": "dataTable", "rows": [list(r) for r in (arg.rows or ())]}


def _step_to_json(step: Step) -> dict:
    d: dict = {"index": step.index, "keyword": step.keyword, "text": step.text}
    arg = _argument_to_json(step.argument)
    if arg is not None:
        d["argument"] = arg
    return d


def _scenario_to_json(sc: Scenario) -> dict:
    return {
        "id": sc.id,
        "name": sc.name,
        "steps": [_step_to_json(s) for s in sc.steps],
    }


def job_to_json(job: Job) -> dict:
    """Job → JSON dict（喂 worker stdin，ADR 0024 输入形状）。"""
    return {
        "scope": {"id": job.scope_id, "name": job.scope_name},
        "engine": job.engine,
        "scenarios": [_scenario_to_json(sc) for sc in job.scenarios],
        # assertionVotes：AI 断言（Then）投票次数（治判定抖动，ADR 0014/0024）。worker 据此执行 N 次取多数票。
        # camelCase 与协议其余字段一致；前缀 assertion 点明只作用于 AI 断言（动作 step 无投票）。
        "assertionVotes": job.assertion_votes,
    }


def job_to_line(job: Job) -> str:
    """Job → 单行 JSON 字符串（写 worker stdin）。"""
    return json.dumps(job_to_json(job), ensure_ascii=False)


# ============================================================================
# worker → core：Event 反序列化
# ============================================================================


def _cost_from_json(d: dict | None) -> Cost | None:
    if d is None:
        return None
    # 只认 engine 报的原生量（平铺、各 optional，ADR 0024）：tokens / time_worked_s，无折算美元
    return Cost(
        tokens=d.get("tokens"),
        time_worked_s=d.get("time_worked_s"),
    )


def _votes_from_json(d: dict | None) -> Votes | None:
    if d is None:
        return None
    return Votes(yes=d["yes"], total=d["total"])


def _report_refs_from_json(items: list | None) -> tuple[ReportRef, ...]:
    if not items:
        return ()
    # 不透明搬运（ADR 0027）：原样读 kind/ref/label，不校验 kind 值、不解释 ref。
    # ref 包成 ResourceUri 仅为命名意图（worker 报的 file://…/s3://… 指针），运行时仍是该字符串。
    return tuple(
        ReportRef(kind=r["kind"], ref=ResourceUri(r["ref"]), label=r.get("label"))
        for r in items
    )


def event_from_json(d: dict) -> Event:
    """JSON dict（worker 事件通道一行）→ model.Event，按 "type" 分派（ADR 0024）。

    事件通道随形态而异：子进程态下是专用 fd（号经 EVENTS_FD 传给 worker）；Fargate 态下是 DDB events 表
    记录的 body（ADR 0024 三通道分离）。两态的行内容同一形状，故都归这里反序列化。
    """
    t = d.get("type")
    if t == "scope_started":
        return ScopeStarted(scope_id=d["scopeId"], session_id=d.get("sessionId"))
    if t == "scenario_started":
        return ScenarioStarted(scenario_id=d["scenarioId"])
    if t == "step_started":
        return StepStarted(scenario_id=d["scenarioId"], step_index=d["stepIndex"])
    if t == "step_done":
        return StepDone(
            scenario_id=d["scenarioId"],
            step_index=d["stepIndex"],
            status=Status(d["status"]),
            votes=_votes_from_json(d.get("votes")),
            cost=_cost_from_json(d.get("cost")),
            error_type=d.get("errorType"),
            message=redact_url_userinfo(d.get("message")),  # 隧道凭据不进判定记录（ADR 0035 决策 5）：盖住解码后的视图（含第三方 worker），原始事件行不改
            report_refs=_report_refs_from_json(d.get("reportRefs")),  # step 级产物：两引擎的 kind=evidence + Nova 的 kind=trajectory（ADR 0042 决策一 / 0027 下沉）
        )
    if t == "step_skipped":
        # scope 内短路（ADR 0031 决定六 / 0024）：独立事件、无 status/votes/cost——加法解析，
        # 不碰上面 step_done 的三态 Status(d["status"]) 分支。core 据此本地赋 StepResult(SKIPPED, shortcircuited=True)。
        return StepSkipped(scenario_id=d["scenarioId"], step_index=d["stepIndex"])
    if t == "scenario_done":
        return ScenarioDone(
            scenario_id=d["scenarioId"],
            status=Status(d["status"]),
            report_refs=_report_refs_from_json(d.get("reportRefs")),
        )
    if t == "scope_done":
        # scope 级 error 的可选三字段（ADR 0051 决策 4 / 0024）：同进同出、status 只许 "error"。部分出现或 status 取别的值
        # 都是 worker 违约，按协议层 fail-loud（与未知事件类型同一口径）——core 要按 status 分支，猜不得。
        present = [k for k in ("status", "errorType", "message") if k in d]
        if present and len(present) != 3:
            raise ValueError(f"scope_done 的 status / errorType / message 须同时出现或同时缺省，现只有 {present}（不符合 worker↔core 协议）")
        if present and d["status"] != "error":
            raise ValueError(f"scope_done 的 status 只允许 \"error\"，收到 {d['status']!r}（不符合 worker↔core 协议）")
        return ScopeDone(
            scope_id=d["scopeId"],
            session_id=d.get("sessionId"),
            report_refs=_report_refs_from_json(d.get("reportRefs")),
            status=Status.ERROR if present else None,
            error_type=d.get("errorType") if present else None,
            message=redact_url_userinfo(d.get("message")) if present else None,  # 预热失败的消息可能带地址（ADR 0035 决策 5）
        )
    if t == "session_opened":
        # 设备会话打开（ADR 0051 决策 4）：origin 封闭集合（core 按它分支：attempted 不写代表会话、永远在未确认集里）；
        # sessionId 为 null 时 name 必须有值（配对键回退）。device 不透明原样搬运。
        origin = d.get("origin")
        if origin not in ("created", "discovered", "attempted"):
            raise ValueError(f"session_opened 的 origin 取值未知：{origin!r}（不符合 worker↔core 协议）")
        name = d.get("name")
        if not isinstance(name, str) or not name:
            raise ValueError("session_opened 缺 name（sessionId 可为 null，name 是配对键的回退，必须有值）")
        return SessionOpened(scope_id=d["scopeId"], name=name, origin=origin,
                             session_id=d.get("sessionId"), device=d.get("device"))
    if t == "session_closed":
        release = d.get("release")
        if release not in ("confirmed", "unconfirmed"):
            raise ValueError(f"session_closed 的 release 取值未知：{release!r}（不符合 worker↔core 协议）")
        name = d.get("name")
        if not isinstance(name, str) or not name:
            raise ValueError("session_closed 缺 name（sessionId 可为 null，name 是配对键的回退，必须有值）")
        return SessionClosed(scope_id=d["scopeId"], name=name, release=release,
                             session_id=d.get("sessionId"),
                             observed_s=d.get("observedS"),  # null 保持 None、不改成 0（null 不等于 0，ADR 0051 决策 7）
                             provider_minutes=d.get("providerMinutes"))
    raise ValueError(f"未知事件 type: {t!r}（不符合 worker↔core 协议）")


def event_from_line(line: str) -> Event:
    """worker 事件通道一行（子进程态下取 EVENTS_FD 的 fd，Fargate 态下取 DDB events 表 body）→ model.Event。"""
    return event_from_json(json.loads(line))


# ============================================================================
# worker → core：退出码（out-of-band 信号，ADR 0024「退出码约定」/ 0028）
# ============================================================================

# worker 网络故障专用退出码：建连失败、重试耗尽时 worker 以这个退出码退出（建连早于任何事件 emit，无法走事件通道）。
# 值避开 POSIX sysexits(64-78)/shell 保留(126-128+n)/信号区。**两个引擎 worker 各自硬编码同一个值**
# （Nova: engines/novaact/gherkai_worker_novaact/run_scope.py；Midscene: engines/midscene/src/worker/run-scope.mts
#  ——语言边界抄不掉）；core 侧只此一处，Engine adapter 一律 import 本常量与下面的翻译函数，别各抄一份
# （抄一份即两处漂移，靠注释维持一致的人工约束）。
EX_WORKER_NETWORK = 80


def raise_for_worker_exit(rc: int, *, code_label: str) -> None:
    """worker 退出码 → 异常（协议翻译，各 Engine adapter 共用的单一事实源）。

    80 → `WorkerNetworkError`（schedule 记 network_error、可重试整 job，ADR 0028）；其余非零（含负码：被信号强杀，
    SIGKILL 为 -9）→ `WorkerExitError`（带原码；进程非干净终止本身即终态信号，ADR 0034 机制二）；0 → 不抛。
    终结函数据异常上的 exit_code 判「退出码非零」一行，不从消息文本解析。

    code_label 只进消息文本：各传输的退出码字段名不同（子进程 `returncode` / ECS `exitCode`），诊断行
    须说该传输的话（也是既有测试匹配的措辞）。
    """
    if rc == EX_WORKER_NETWORK:
        raise WorkerNetworkError(f"worker 建连失败（网络/SSL 瞬时故障），退出码 {rc}", rc)
    if rc != 0:
        raise WorkerExitError(rc, f"worker 异常退出 {code_label}={rc}")
