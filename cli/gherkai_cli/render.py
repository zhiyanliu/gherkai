"""渲染：把 ADR 0024 事件流与 RunResult 变成人看的文本 / 机器读的 JSON（cli 表层）。

core 产出纯数据（RunResult、Event）；怎么展示是皮的事，故渲染逻辑留在 cli。
"""
from __future__ import annotations

from gherkai_core.model import Event, Job, JobResult, RunResult, RunState, Status
from gherkai_core.serialize import to_dict  # 单一真理源（ADR 0027）：cli --json 与 manifest 共用
# ReportRef → dict 与 jobs/*.json、run --json 同一份（单一序列化真源，ADR 0027）；explain 的 report_refs 原样搬。
from gherkai_core.serialize import _ref_to_dict


def format_event(ev: Event) -> str:
    """单个 ADR 0024 事件 → 一行进度文本（不含 scope_id——scope 归调用方的 `[core <scope>:event]` 前缀，
    见 cli/gherkai_cli/__main__.py 的 sink；行内只留前缀没有的 scenario_id/step_index/status/votes/cost）。"""
    parts: list[str] = [ev.type]
    for attr in ("scenario_id", "step_index", "status"):
        v = getattr(ev, attr, None)
        if v is not None:
            parts.append(f"{attr}={getattr(v, 'value', v)}")
    votes = getattr(ev, "votes", None)
    if votes and votes.total > 1:  # total==1=单次判定，无抖动 tally 意义，不显（避免 1/1 噪声）
        parts.append(f"votes={votes.yes}/{votes.total}")
    cost = getattr(ev, "cost", None)
    if cost:
        if cost.tokens is not None:
            parts.append(f"tokens={cost.tokens}")
        if cost.time_worked_s is not None:
            parts.append(f"time_worked_s={cost.time_worked_s}")
    return " ".join(str(p) for p in parts)


def _cost_bits(tokens: int | None, time_worked_s: float | None) -> list[str]:
    """原生量成本拼装（core 只合计原生量，美元折算交消费者，ADR 0024）。"""
    bits: list[str] = []
    if tokens is not None:
        bits.append(f"{tokens} tokens")
    if time_worked_s is not None:
        bits.append(f"{time_worked_s:.1f}s agent-time")
    return bits


def _one_line(text) -> str:
    """多行/带多余空白的原因文本折叠成一行（防御：引擎异常的 repr 可能多行，版式不该被它撑开）。"""
    return " ".join(str(text).split()) if text is not None else ""


def _ms(duration_ms: float | None) -> str:
    return f"{duration_ms / 1000:.1f}s" if duration_ms is not None else "?"


def render_text(result: RunResult) -> str:
    """RunResult → 人看的多行汇总（嵌套 job/scenario/step + 时长 + 成本 + 报告指针）。

    面向人的文本模式：用自然的词、不用变量名式术语（RunResult/sessionId/step[0] 这类）；
    但 job/scenario/step/scope 是领域概念（用户写 feature/看 plan 都在用），保留原词。JSON 模式（to_dict）是
    机器读的、字段名照旧。
    """
    out: list[str] = ["", "===== 运行结果 =====", f"  总状态: {result.status.value}"]
    if result.duration_ms is not None:
        out.append(f"  总墙钟时长: {_ms(result.duration_ms)}")
    cost_bits = _cost_bits(result.total_tokens, result.total_time_worked_s)
    if cost_bits:
        out.append(f"  成本原生量合计: {' + '.join(cost_bits)}")

    for jr in result.jobs:
        jbits = _cost_bits(jr.total_tokens, jr.total_time_worked_s)
        cost_str = f"  [{', '.join(jbits)}]" if jbits else ""
        # 说明文字：error 类带分类前缀；fail-fast 派生态（skipped/aborted）的 error_type 恒 None、「为什么没跑」
        # 只在 message 里（ADR 0031 决定一），故无分类时也显 message——否则人读视图只剩一个光秃的态、原因得改用 --json。
        if jr.error_type:
            err = f"  ({jr.error_type}: {jr.message})"
        else:
            err = f"  ({jr.message})" if jr.message else ""
        out.append(f"  job {jr.scope_id!r}: {jr.status.value}{cost_str}{err}")
        if jr.duration_ms is not None:
            out.append(f"    scope 墙钟: {_ms(jr.duration_ms)}")
        for sr in jr.scenarios:
            dur = f"  ({_ms(sr.duration_ms)})" if sr.duration_ms is not None else ""
            out.append(f"    scenario {sr.scenario_id!r}: {sr.status.value}{dur}")
            for st in sr.steps:
                # total>1 才显投票 tally（与 format_event/index.html 一致；1/1 无抖动意义，不显）
                v = f" 投票 {st.votes.yes}/{st.votes.total}" if st.votes and st.votes.total > 1 else ""
                # 连锁失败旁注（ADR 0031 决定六）：被 scope 内短路的 step（shortcircuited=True，status=skipped）——
                # 上游 error 后 worker 跳过了它、没在损坏环境上跑。旁注解释"为何 skipped"，读 shortcircuited 这个
                # 正交布尔（比旧的"按 status 顺序猜 error 后 failed"精确）；不改判定/severity（守纯 reducer 红线）。
                note = "  ⚠ 因前置 step error 被跳过（未执行）" if st.shortcircuited else ""
                out.append(f"      step {st.index}: {st.status.value} ({_ms(st.duration_ms)}){v}{note}")
                # step 级失败原因（ADR 0042 决策三）：与 job 行同款——有 message 就显，人读视图不只剩一个光秃的态
                if st.message:
                    out.append(f"        原因: {_one_line(st.message)}")
                # step 级原生报告产物（Nova trajectory 挂这层，来自 step_done 下沉，ADR 0027）——缩进深一级
                for rr in st.report_refs:
                    out.append(f"        report（{rr.label or rr.kind}）: {rr.ref}")
            # scenario 级原生报告产物：当前引擎均不填（Nova 已下沉 step 级、Midscene 报 scope 级），
            # 保留作扩展兜底——未来引擎若在 scenario_done 报 report_refs 仍能显示（不透明搬运哲学，ADR 0027）
            for rr in sr.report_refs:
                out.append(f"      report（{rr.label or rr.kind}）: {rr.ref}")
        if jr.session_id:
            out.append(f"    session id: {jr.session_id}")
        # scope 级原生报告产物（Midscene report.html 挂这层，来自 scope_done）
        for rr in jr.report_refs:
            out.append(f"    report（{rr.label or rr.kind}）: {rr.ref}")
    return "\n".join(out)


def render_run_state(state: RunState) -> str:
    """`status` 的 RunState 人读渲染（轻量；权威判定明细读 jobs/*.json 或 --json）。

    local/cloud 两路共用一份（保两路一致，ADR 0034）——渲染是皮的事，故住这里而非产品本体层。
    """
    lines = [f"run {state.run_id}: {state.status.value}"]
    for sid, js in state.jobs.items():
        sess = f"  session={js.session_id}" if js.session_id else ""
        lines.append(f"  - {sid}: {js.status.value}{sess}")
    if state.ended_at:
        lines.append(f"ended_at={state.ended_at}")
    return "\n".join(lines)


# ---- plan 预检（dry-run）渲染：纯本地、零费用，展示 .feature → scope/job 分组 ----

def render_plan_text(jobs: list[Job], default_engine: str, dispatch: dict | None = None) -> str:
    """plan 产出 Job[] → 人看的多行预检视图（scope/engine/scenario/step，不真跑）。

    dispatch（可选，ADR 0036 决策 4）：{(scope_id, scenario_id, step_index): probe}——worker 的命中
    自述。命中 → 行尾标「← 确定性:」；冲突 → 标 ⚠（真跑该 step 将 error）；None/缺失 → 不标（默认 AI，少噪声）。
    """
    n_scenarios = sum(len(j.scenarios) for j in jobs)
    out: list[str] = [
        "===== plan（预检，未执行）=====",
        f"  {len(jobs)} job(scope)  ·  {n_scenarios} scenario  ·  default_engine={default_engine}",
    ]
    for j in jobs:
        votes = f"  votes={j.assertion_votes}" if j.assertion_votes != 1 else ""
        # name 只在与 scope_id 不同时显示：named scope 二者同为 @scope 值（重复无信息）；未标 scope 时 id=uri:line、name=标题
        name = f" (name={j.scope_name!r})" if j.scope_name != j.scope_id else ""
        out.append(f"  job scope={j.scope_id!r}{name} engine={j.engine}{votes}")
        for sc in j.scenarios:
            out.append(f"    scenario {sc.id!r}  ({len(sc.steps)} step)")
            for st in sc.steps:
                out.append(f"      [{st.index}] {st.keyword} {st.text}{_arg_hint(st.argument)}"
                           f"{_dispatch_hint(dispatch, j.scope_id, sc.id, st.index)}")
    return "\n".join(out)


def _dispatch_hint(dispatch: dict | None, scope_id: str, scenario_id: str, step_index: int) -> str:
    """step 的派发预期标注（ADR 0036）：确定性命中/冲突才标，AI 默认不标（噪声控制）。"""
    probe = (dispatch or {}).get((scope_id, scenario_id, step_index))
    if not probe:
        return ""
    if "conflict" in probe:
        return "  ← ⚠ 命中多条确定性模式（真跑该 step 将 error；请工程侧收紧注册表模式）"
    return f"  ← 确定性: {probe.get('description', probe.get('pattern', ''))}"


def _arg_hint(arg) -> str:
    """step 多行参数的轻量标注（文本视图保持紧凑；完整 content/rows 用 --json 看）。
    dataTable → +dataTable(行×列)；docString → +docString(N 行)。"""
    if arg is None:
        return ""
    if arg.kind == "dataTable":
        rows = arg.rows or ()
        cols = len(rows[0]) if rows else 0
        return f"  +dataTable({len(rows)}×{cols})"
    if arg.kind == "docString":
        n = len((arg.content or "").splitlines())
        return f"  +docString({n} 行)"
    return f"  +{arg.kind}"


def plan_to_dict(jobs: list[Job], default_engine: str, dispatch: dict | None = None) -> dict:
    """plan 产出 → 机器可读 dict（--json）。复用 gherkai_core.serialize 的 job 序列化保单一真理源。

    dispatch 非 None 时给每个 step dict 注入 "deterministic" 键（plan 视图字段、非 definition——
    值 = worker 自述的命中结果：null / {"pattern","description"} / {"conflict":[...]}，ADR 0036）。
    """
    from gherkai_core.serialize import job_to_dict
    job_dicts = []
    for j in jobs:
        d = job_to_dict(j)
        if dispatch is not None:
            for sc_j, sc_d in zip(j.scenarios, d["scenarios"]):
                for st_j, st_d in zip(sc_j.steps, sc_d["steps"]):
                    st_d["deterministic"] = dispatch.get((j.scope_id, sc_j.id, st_j.index))
        job_dicts.append(d)
    return {
        "default_engine": default_engine,
        "job_count": len(jobs),
        "scenario_count": sum(len(j.scenarios) for j in jobs),
        "jobs": job_dicts,
    }


# ---- explain：step 级证据视图（ADR 0042 决策四）——判定树骨架 + evidence 合成 ----
# 文本与 JSON **同源**：`explain_to_dict` 产一份文档，`--json` 直接 dump，文本模式喂 `render_explain_text`。
# 两路分头组装必漂移（run/status 的教训），故这里只有一个组装器。IO（读 evidence）不在本模块：
# 由调用方注入 `evidence_reader`（皮的 IO 归 __main__，渲染层保持无副作用、可测）。

_NO_RECORD = "无记录（未执行或未上报）"          # 骨架有、判定记录没有的 step / scenario
_THOUGHT_BUDGET = 800                            # 单段推理文本的字符预算（ADR 0042 决策四「文本预算」）
# 中止 job 的提示语：evidence 已产、ref 只在事件记录里（explain 不读事件流，ADR 0042 决策四「记录缺口」）
_ABORTED_PARTIAL_HINT = "本 job 被中止，部分已执行 step 的证据未进判定记录"
_EVIDENCE_MISSING_TEXT = {
    "no_ref": "无 AI 证据",
    "unreadable": "AI 证据读不到（文件不在或内容已损坏）",
    "unsupported_schema": "AI 证据的格式版本这个版本的 gherkai 认不出（升级后再看）",
}


def explain_step_expands(step: dict, *, expand_passed: bool) -> bool:
    """这个 step 要不要展开证据（ADR 0042 决策四）：默认只展开 failed / error / skipped / 无记录，`--all` 也展开 passed。

    **同时兼作「要不要去读 evidence」的判据**（`explain_to_dict` 的 `wants_evidence`）：文本模式下不展开就不读，
    省掉云端逐 step 一次 GetObject 的白下载；`--json` 契约要求全给，那一路不传本谓词。
    """
    if step["record_missing"]:
        return False  # 无记录 = 没有 ref 可读，展不出东西（状态行已说明它没跑/没上报）
    return expand_passed or step["status"] != "passed"


def explain_to_dict(*, run_id: str, status: str | None, results: list[JobResult],
                    evidence_reader, wants_evidence=None,
                    scenario_ids: "set[str] | None" = None, step_index: int | None = None) -> dict:
    """把 JobResult 列表 + evidence 合成 explain 的机读文档（形状即 ADR 0042 决策四的 JSON 形态）。

    **骨架 = job 定义**（`JobResult.job`）而非判定记录：worker 被外部中止时未完成的 scenario 不进 `jobs/*.json`，
    以判定记录为骨架会让这些 step 直接消失（看不出「没跑」与「没这步」的区别）。故逐 scenario / 逐 step 按定义走、
    没有记录的给 `status: null` + `record_missing: true`。

    evidence_reader(report_refs) → `(evidence | None, evidence_missing | None)`：读 kind=evidence 的 ref（IO 在调用方）。
    wants_evidence(step_dict) → bool：None = 每个有记录的 step 都读（`--json` 契约要求全给）；文本模式传
    `explain_step_expands` 的绑定版，跳过不渲染的 step（见其 docstring）。
    scenario_ids / step_index：`--scenario` / `--step` 的筛选结果（None = 不筛）；匹配器在皮层（它还要出候选清单）。
    """
    scopes = []
    for jr in results:
        by_scenario = {sr.scenario_id: sr for sr in jr.scenarios}
        # 记录缺口按**整个 job 定义**算、不受 --scenario/--step 影响：aborted_hint 说的是这个 job 的事实，
        # 不该随筛选闪烁。
        recorded = {(sr.scenario_id, st.index) for sr in jr.scenarios for st in sr.steps}
        total_steps = sum(len(sc.steps) for sc in jr.job.scenarios)
        scenarios = []
        for sc in jr.job.scenarios:
            if scenario_ids is not None and sc.id not in scenario_ids:
                continue
            sr = by_scenario.get(sc.id)
            by_index = {st.index: st for st in (sr.steps if sr is not None else ())}
            steps = []
            for sd in sc.steps:
                if step_index is not None and sd.index != step_index:
                    continue
                st = by_index.get(sd.index)
                d = {
                    "index": sd.index,
                    "keyword": sd.keyword,
                    "text": sd.text,
                    "status": None if st is None else st.status.value,
                    "votes": ({"yes": st.votes.yes, "total": st.votes.total}
                              if st is not None and st.votes else None),
                    "error_type": None if st is None else st.error_type,
                    "message": None if st is None else st.message,
                    "shortcircuited": bool(st is not None and st.shortcircuited),
                    "duration_ms": None if st is None else st.duration_ms,
                    "report_refs": [] if st is None else [_ref_to_dict(rr) for rr in st.report_refs],
                    "record_missing": st is None,
                    "evidence": None,
                    # 无记录的 step 没有任何 ref，故与「有记录但没挂 evidence」同归 no_ref
                    "evidence_missing": "no_ref" if st is None else None,
                }
                if st is not None and (wants_evidence is None or wants_evidence(d)):
                    d["evidence"], d["evidence_missing"] = evidence_reader(st.report_refs)
                steps.append(d)
            scenarios.append({
                "scenario_id": sc.id,
                "name": sc.name,
                "status": None if sr is None else sr.status.value,
                "steps": steps,
            })
        if (scenario_ids is not None or step_index is not None) and not scenarios:
            continue  # 筛选生效且本 scope 无一命中：不产空壳 scope（文本/JSON 同律）
        scopes.append({
            "scope_id": jr.scope_id,
            "engine": jr.engine,
            "status": jr.status.value,
            "error_type": jr.error_type,
            "message": jr.message,
            "session_id": jr.session_id,
            "report_refs": [_ref_to_dict(rr) for rr in jr.report_refs],
            # 中止的 job 里已跑完的 step 其证据已产，但 ref 只在事件记录里、不进判定记录 → 明说，别让读者以为没产
            "aborted_hint": (_ABORTED_PARTIAL_HINT
                             if jr.status in (Status.ABORTED, Status.ERROR) and 0 < len(recorded) < total_steps
                             else None),
            # 「这个 job 有没有任何 step 记录」是 job 的事实、按未筛的判定树算一次——渲染层据此打 job 判定块；
            # 曾在筛后的 scenarios 上重算，--scenario/--step 筛剩无记录 step 时会把有完整记录的 job 误打成零记录。
            "has_step_records": bool(recorded),
            "scenarios": scenarios,
        })
    return {"run_id": run_id, "status": status, "scopes": scopes}


def _ref_line(rr: dict) -> str:
    """产物 ref 一行（与 render_text 的 step/scope 行同款措辞，label 缺省回落 kind）。"""
    return f"report（{rr.get('label') or rr['kind']}）: {rr['ref']}"


def _evidence_ref(step: dict) -> str:
    """该 step 的 evidence ref（截断提示里指给读者的「完整内容在哪」）；没有则空串。"""
    for rr in step["report_refs"]:
        if rr["kind"] == "evidence":
            return rr["ref"]
    return ""


def _thought_lines(thought: str, indent: str, *, ref: str, full: bool) -> list[str]:
    """一段推理文本 → 文本行（超预算截断，除 --full；多行原文的续行对齐到 `thought: ` 之后）。

    文本形态的 key 一律用 `--json` 的字段名（thought / screenshot / message / error，与 vote= / url= 同律）——
    agent 读文本再对 JSON 零翻译；中文只留给整句提示。
    """
    text = thought
    if not full and len(text) > _THOUGHT_BUDGET:
        text = text[:_THOUGHT_BUDGET] + f"…（已截断；完整内容见 --json 或 evidence.json：{ref}）"
    head = f"{indent}thought: "
    cont = indent + " " * len("thought: ")
    parts = text.split("\n")
    return [head + parts[0]] + [cont + p for p in parts[1:]]


def _act_lines(act: dict, *, ref: str, full: bool) -> list[str]:
    """一次 AI 调用（evidence 的 act）→ 文本行。

    默认预算：只渲染**最后一个带推理的 frame**（判否理由通常落在末次观察）及其截图，其余 frame 只报个数；
    `--full` 逐 frame 全文。frames 为空是 Nova 出错 act 的正常形态（SDK 不落轨迹 json，ADR 0042 决策一），
    不当异常报——`错误:` 那行才是这种 act 的信息所在。
    """
    vote = act.get("vote")
    # vote 用 json 的写法（true/false/null）：null = 本次调用不是投票调用（Given/When 的动作），与「投否」不同
    bits = [f"act {act.get('index')}", "vote=" + ("null" if vote is None else ("true" if vote else "false"))]
    if act.get("url"):
        bits.append(f"url={act['url']}")
    lines = ["      " + "  ".join(bits)]
    if act.get("error"):
        lines.append(f"        error: {_one_line(act['error'])}")
    frames = act.get("frames") or []
    if full:
        for j, fr in enumerate(frames):
            url = fr.get("url")
            lines.append(f"        frame {j}" + (f"  url={url}" if url else ""))
            if fr.get("thought"):
                lines += _thought_lines(fr["thought"], "          ", ref=ref, full=True)
            if fr.get("screenshot"):
                lines.append(f"          screenshot: {fr['screenshot']}")
        return lines
    last = next((i for i in range(len(frames) - 1, -1, -1) if frames[i].get("thought")), None)
    if last is not None:
        lines += _thought_lines(frames[last]["thought"], "        ", ref=ref, full=False)
        if frames[last].get("screenshot"):
            lines.append(f"        screenshot: {frames[last]['screenshot']}")
    omitted = len(frames) - (0 if last is None else 1)
    if omitted > 0:
        lines.append(f"        其余 {omitted} 个 frame 已省略（--full 查看）")
    return lines


def _step_lines(step: dict, *, expand_passed: bool, full: bool) -> list[str]:
    """一个 step → 文本行：状态行（+ 投票 / 归因 / 时长 / 短路旁注）、原因行，展开时再加证据。"""
    head = f"    step {step['index']}  {step['keyword']} {step['text']}"
    if step["record_missing"]:
        return [f"{head}  {_NO_RECORD}"]
    bits = [step["status"]]
    if step["votes"]:
        bits.append(f"votes {step['votes']['yes']}/{step['votes']['total']}")
    # 归因只在 error 步显示：断言没过的归因恒是「断言未过」、原因行已说清，再打一遍只是噪声
    if step["status"] == "error" and step["error_type"]:
        bits.append(f"({step['error_type']})")
    if step["duration_ms"] is not None:
        bits.append(f"({_ms(step['duration_ms'])})")
    if step["shortcircuited"]:
        bits.append("⚠ 因前置 step error 被跳过（未执行）")
    lines = [head + "  " + "  ".join(bits)]
    if step["message"]:
        lines.append(f"      message: {_one_line(step['message'])}")
    if not explain_step_expands(step, expand_passed=expand_passed):
        return lines
    ev = step["evidence"]
    if ev is None:
        miss = step["evidence_missing"]
        # 短路的 step 不打「无 AI 证据」：它根本没跑，状态行的旁注已说明，再说一遍是废话
        if miss and not (miss == "no_ref" and step["shortcircuited"]):
            lines.append(f"      {_EVIDENCE_MISSING_TEXT.get(miss, _EVIDENCE_MISSING_TEXT['no_ref'])}")
        # 兜底指针：证据缺了，把该 step 的其它产物 ref 列出来，让人还有地方看（ADR 0042 决策四「文本预算」末条）
        lines += [f"      {_ref_line(rr)}" for rr in step["report_refs"]]
        return lines
    ref = _evidence_ref(step)
    for act in ev.get("acts") or []:
        lines += _act_lines(act, ref=ref, full=full)
    return lines


def render_explain_text(doc: dict, *, expand_passed: bool = False, full: bool = False) -> str:
    """explain 的人/agent 可读文本（`explain_to_dict` 的文档 → 多行摘要，ADR 0042 决策四「文本形态」）。

    文本是「一次读进上下文的摘要」而非 evidence 全文转写，故默认带预算（见 `_act_lines`）；`--full` 关掉预算。
    """
    out: list[str] = [f"run {doc['run_id']}  status={doc['status']}"]
    for sc in doc["scopes"]:
        sess = f"  session={sc['session_id']}" if sc["session_id"] else ""
        out.append(f"scope {sc['scope_id']}  engine={sc['engine']}  status={sc['status']}{sess}")
        out += [f"  {_ref_line(rr)}" for rr in sc["report_refs"]]
        # 一个 step 记录都没有的 job（worker 没起来 / 起来就被掐）：判定只剩 job 级这一层，单独打一段，
        # 免得读者在一片「无记录」里找不到「到底为什么」。
        if not sc["has_step_records"]:  # job 级事实（explain_to_dict 按未筛判定树算），不在筛后的 steps 上重算
            why = ""
            if sc["error_type"]:
                why = f"  ({sc['error_type']}: {sc['message'] or ''})"
            elif sc["message"]:
                why = f"  ({sc['message']})"
            out.append(f"  判定：{sc['status']}{why}")
            out.append("  诊断细节见 worker 日志")
        if sc["aborted_hint"]:
            out.append(f"  {sc['aborted_hint']}")
        for scen in sc["scenarios"]:
            out.append(f"  scenario {scen['scenario_id']}  {scen['name']}  {scen['status'] or _NO_RECORD}")
            for step in scen["steps"]:
                out += _step_lines(step, expand_passed=expand_passed, full=full)
    return "\n".join(out)


# to_dict 已移入 gherkai_core.serialize（单一真理源，cli 与 manifest 共用），从那里 re-export。
__all__ = ["format_event", "render_text", "render_run_state", "render_plan_text", "plan_to_dict", "to_dict",
           "explain_to_dict", "render_explain_text", "explain_step_expands"]
