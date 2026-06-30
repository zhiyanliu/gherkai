"""core 领域模型 ↔ 朴素 dict（单一序列化真理源，ADR 0027/0016）。

序列化的是 core 的领域模型，故属 core——cli 的 --json、ReportStore 的 manifest、
RunStore（RunMeta/RunState）、ResultStore（JobResult）的落盘都复用这里，不各写一份（避免漂移）。
手写映射（不靠 dataclasses.asdict/反射）：形状是对外契约（CI/WebUI/manifest 消费），须显式、稳定。

往返一致（round-trip）：`X_to_dict` 与 `X_from_dict` 须保持 from_dict(to_dict(x)) == x——有 round-trip 单测护栏。

注：worker 协议的 Job 序列化在 wire.py（单向 Job→JSON 喂 worker，协议形状）；这里的 Job↔dict 是
**双向持久化**（RunMeta 落盘要能读回完整 Job），用途不同、各自一份、各自被 round-trip 测护。

cost 只含 engine 报的原生量、不折美元（ADR 0024）；report_refs 是不透明搬运（kind/ref/label 原样，ADR 0027）。
"""
from __future__ import annotations

from core.model import (
    Job,
    JobResult,
    JobState,
    ReportRef,
    ResourceUri,
    RunMeta,
    RunResult,
    RunState,
    Scenario,
    Status,
    Step,
    StepArgument,
    StepResult,
    Votes,
)


# ============================================================================
# definition：Job / Scenario / Step ↔ dict（双向，RunMeta 落盘用）
# ============================================================================


def _argument_to_dict(arg: StepArgument | None) -> dict | None:
    if arg is None:
        return None
    if arg.kind == "docString":
        return {"kind": "docString", "content": arg.content}
    return {"kind": "dataTable", "rows": [list(r) for r in (arg.rows or ())]}


def _argument_from_dict(d: dict | None) -> StepArgument | None:
    if d is None:
        return None
    if d["kind"] == "docString":
        return StepArgument(kind="docString", content=d.get("content"))
    return StepArgument(kind="dataTable", rows=tuple(tuple(r) for r in d.get("rows", [])))


def _step_to_dict(s: Step) -> dict:
    d: dict = {"index": s.index, "keyword": s.keyword, "text": s.text}
    arg = _argument_to_dict(s.argument)
    if arg is not None:
        d["argument"] = arg
    return d


def _step_from_dict(d: dict) -> Step:
    return Step(index=d["index"], keyword=d["keyword"], text=d["text"],
                argument=_argument_from_dict(d.get("argument")))


def _scenario_def_to_dict(sc: Scenario) -> dict:
    return {"id": sc.id, "name": sc.name, "steps": [_step_to_dict(s) for s in sc.steps]}


def _scenario_def_from_dict(d: dict) -> Scenario:
    return Scenario(id=d["id"], name=d["name"], steps=tuple(_step_from_dict(s) for s in d.get("steps", [])))


def job_to_dict(job: Job) -> dict:
    """Job(definition) → dict（双向，RunMeta 落盘）。"""
    return {
        "scope_id": job.scope_id,
        "scope_name": job.scope_name,
        "engine": job.engine,
        "scenarios": [_scenario_def_to_dict(sc) for sc in job.scenarios],
        "assertion_votes": job.assertion_votes,
    }


def job_from_dict(d: dict) -> Job:
    return Job(
        scope_id=d["scope_id"],
        scope_name=d["scope_name"],
        engine=d["engine"],
        scenarios=tuple(_scenario_def_from_dict(sc) for sc in d.get("scenarios", [])),
        assertion_votes=d.get("assertion_votes", 1),  # 向后兼容旧落盘（无此键 → 默认 1）
    )


# ============================================================================
# 判定：JobResult / RunResult ↔ dict
# ============================================================================


def _ref_to_dict(rr: ReportRef) -> dict:
    return {"kind": rr.kind, "ref": rr.ref, "label": rr.label}


def _ref_from_dict(d: dict) -> ReportRef:
    # ref 包成 ResourceUri 仅为命名意图（带 scheme 的资源指针）；运行时仍是原字符串。
    return ReportRef(kind=d["kind"], ref=ResourceUri(d["ref"]), label=d.get("label"))


def _votes_from_dict(d: dict | None) -> Votes | None:
    return Votes(yes=d["yes"], total=d["total"]) if d else None


def job_result_to_dict(jr: JobResult, *, include_job: bool = True) -> dict:
    """JobResult → dict。两种形态，由 include_job 选，顶层 def 字段也随之不同（避免任一形态里出现冗余）：

    - include_job=True（默认，ResultStore 落单 job）：嵌完整 `job`(definition) → 文件**自包含**，
      CI 单独读一个 jobs/<scope_id>.json 不依赖 run_meta 即可拿到完整 def。**不再另抄顶层 scope_id/
      scope_name/engine**——def 已自包含，消费者从 `d["job"]["scope_id"]` 取（唯一真值源、无"读哪个"歧义）。
    - include_job=False（聚合 to_dict(RunResult)）：**不嵌** def——def 唯一地活在同一 dict 的 run_meta.jobs[]
      里（三层切分：definition 层）；jobs[] 只背判定 + **顶层 `scope_id` 作 join key**（from_dict 按它从
      run_meta join 回 Job）。这样整 RunResult 序列化时同一批 Job 不出现两份（normalize），又能重建。

    即：顶层 scope_id 仅在【聚合形态】出现（join key，结构必需）；【自包含形态】顶层无 def 字段、全在 `job` 里。
    """
    d: dict = {}
    if include_job:
        d["job"] = job_to_dict(jr.job)   # 自包含：def 真值全在此，顶层不再抄
    else:
        d["scope_id"] = jr.scope_id      # 聚合：唯一的顶层 def 字段 = join key（from_dict 据此 join run_meta）
    d.update({
        "status": jr.status.value,
        "duration_ms": jr.duration_ms,
        "total_tokens": jr.total_tokens,
        "total_time_worked_s": jr.total_time_worked_s,
        "session_id": jr.session_id,
        "error_type": jr.error_type,
        "message": jr.message,
        "report_refs": [_ref_to_dict(rr) for rr in jr.report_refs],
        "scenarios": [
            {
                "scenario_id": sr.scenario_id,
                "status": sr.status.value,
                "duration_ms": sr.duration_ms,
                "report_refs": [_ref_to_dict(rr) for rr in sr.report_refs],
                "steps": [
                    {
                        "index": st.index,
                        "status": st.status.value,
                        "duration_ms": st.duration_ms,
                        "votes": ({"yes": st.votes.yes, "total": st.votes.total} if st.votes else None),
                        "error_type": st.error_type,
                    }
                    for st in sr.steps
                ],
            }
            for sr in jr.scenarios
        ],
    })
    return d


def job_result_from_dict(d: dict, *, job: Job | None = None) -> JobResult:
    """dict → JobResult（ResultStore 读单 job 复用；也被 from_dict(RunResult) 复用）。

    definition 来源（二选一，对应 to_dict 的两种形态）：
    - 自包含形态：dict 内嵌 `job` → 直接重建（ResultStore 单 job 文件走这条）。
    - 聚合形态：dict 无 `job`，由调用方经 `job=` 传入（from_dict(RunResult) 按 scope_id 从 run_meta join）。
    顶层 scope_id/engine 只是便利冗余，不作 def 来源。
    """
    from core.model import ScenarioResult  # 局部 import 避免顶层顺序耦合

    if job is None:
        job = job_from_dict(d["job"])  # 自包含形态：从嵌套 def 重建

    return JobResult(
        job=job,
        status=Status(d["status"]),
        scenarios=[
            ScenarioResult(
                scenario_id=s["scenario_id"],
                status=Status(s["status"]),
                duration_ms=s.get("duration_ms"),
                report_refs=tuple(_ref_from_dict(r) for r in s.get("report_refs", [])),
                steps=[
                    StepResult(
                        index=st["index"],
                        status=Status(st["status"]),
                        duration_ms=st.get("duration_ms"),
                        votes=_votes_from_dict(st.get("votes")),
                        error_type=st.get("error_type"),
                    )
                    for st in s.get("steps", [])
                ],
            )
            for s in d.get("scenarios", [])
        ],
        session_id=d.get("session_id"),
        total_tokens=d.get("total_tokens"),
        total_time_worked_s=d.get("total_time_worked_s"),
        duration_ms=d.get("duration_ms"),
        report_refs=tuple(_ref_from_dict(r) for r in d.get("report_refs", [])),
        error_type=d.get("error_type"),
        message=d.get("message"),
    )


def to_dict(result: RunResult) -> dict:
    """RunResult → 朴素 dict（机器可读：CI / WebUI / manifest 消费）。

    normalize（ADR 0016 三层切分）：definition 只在 run_meta.jobs[] 序列化一次；jobs[] 只背判定、
    经 scope_id 引 def（include_job=False）。同一批 Job 不再出现两份。
    """
    return {
        "run_id": result.run_id,         # 便利：消费端/manifest 直读（经 property，真值在 run_meta）
        "run_meta": run_meta_to_dict(result.run_meta),
        "status": result.status.value,
        "duration_ms": result.duration_ms,
        "total_tokens": result.total_tokens,
        "total_time_worked_s": result.total_time_worked_s,
        "jobs": [job_result_to_dict(jr, include_job=False) for jr in result.jobs],
    }


def from_dict(d: dict) -> RunResult:
    """朴素 dict → RunResult。与 to_dict 往返一致（round-trip 单测护栏）。

    def 唯一真值在 run_meta.jobs[]；jobs[] 的 JobResult 经 scope_id 从中 join 回 Job（不读嵌套 job）。
    """
    run_meta = run_meta_from_dict(d["run_meta"])
    job_by_scope = {j.scope_id: j for j in run_meta.jobs}  # scope_id → Job（join 表）
    return RunResult(
        run_meta=run_meta,
        status=Status(d["status"]),
        jobs=[job_result_from_dict(j, job=job_by_scope.get(j["scope_id"])) for j in d.get("jobs", [])],
        total_tokens=d.get("total_tokens"),
        total_time_worked_s=d.get("total_time_worked_s"),
        duration_ms=d.get("duration_ms"),
    )


# ============================================================================
# definition 信封 RunMeta + 控制面 RunState ↔ dict（RunStore 落盘，ADR 0016）
# ============================================================================


def run_meta_to_dict(meta: RunMeta) -> dict:
    return {
        "run_id": meta.run_id,
        "created_at": meta.created_at,
        "jobs": [job_to_dict(j) for j in meta.jobs],
    }


def run_meta_from_dict(d: dict) -> RunMeta:
    return RunMeta(
        run_id=d["run_id"],
        created_at=d.get("created_at", ""),
        jobs=tuple(job_from_dict(j) for j in d.get("jobs", [])),
    )


def run_state_to_dict(state: RunState) -> dict:
    # started_at/ended_at 用 omit-when-None：本轮同步 cli 不取时钟、两字段恒 None，
    # 写成永远的 "null" 是噪音（读者会当 bug）。键缺失语义（=未取时钟）比 null（=取了为空）更诚实；
    # 未来真支持异步/续跑填了值，键自然出现（from_dict 用 .get 容忍缺失，round-trip 不破）。
    d: dict = {"run_id": state.run_id, "status": state.status.value}
    if state.started_at is not None:
        d["started_at"] = state.started_at
    if state.ended_at is not None:
        d["ended_at"] = state.ended_at
    # state.jobs 是 Map（scope_id → JobState，ADR 0030）：落盘 JSON 仍是 list（保 run_state.json 向后兼容）。
    # 必须 .values() 迭代——直接 `for js in state.jobs` 会迭代 dict 的 key（str）、js.scope_id 即 AttributeError。
    d["jobs"] = [
        {"scope_id": js.scope_id, "status": js.status.value, "session_id": js.session_id}
        for js in state.jobs.values()
    ]
    return d


def run_state_from_dict(d: dict) -> RunState:
    # JSON 里 jobs 是 list；内存模型是 Map（scope_id → JobState，ADR 0030）——读回时按 scope_id 重建 Map。
    return RunState(
        run_id=d["run_id"],
        status=Status(d["status"]),
        started_at=d.get("started_at"),
        ended_at=d.get("ended_at"),
        jobs={
            j["scope_id"]: JobState(scope_id=j["scope_id"], status=Status(j["status"]), session_id=j.get("session_id"))
            for j in d.get("jobs", [])
        },
    )
