"""core 领域模型 ↔ 朴素 dict（单一序列化真理源，ADR 0027/0016）。

序列化的是 core 的领域模型，故属 core——cli 的 --json、ReportStore 的 manifest、
RunStore（RunMeta/RunState）、ResultStore（JobResult）的落盘都复用这里，不各写一份（避免漂移）。
手写映射（不靠 dataclasses.asdict/反射）：形状是对外契约（CI/WebUI/manifest 消费），须显式、稳定。

往返一致（round-trip）：`X_to_dict` 与 `X_from_dict` 须保持 from_dict(to_dict(x)) == x——有 round-trip 单测护栏。
**规范化一律归写端**（读端只忠实还原落盘内容）：这样 to_dict 的产物本身是规范形、往返恒等；反之（读端规范化）
落盘内容会随内存值的偶然形态漂、且往返把值悄悄变形。唯一带规范化的字段是 `RunMeta.extra_http_headers`
（无序 header 表、tuple 只是 frozen 载体）：写端按键排序 + 空表当 None，故往返保 mapping 恒等、键序落定字典序。

注：worker 协议的 Job 序列化在 wire.py（单向 Job→JSON 喂 worker，协议形状）；这里的 Job↔dict 是
**双向持久化**（RunMeta 落盘要能读回完整 Job），用途不同、各自一份、各自被 round-trip 测护。

cost 只含 engine 报的原生量、不折美元（ADR 0024）；report_refs 是不透明搬运（kind/ref/label 原样，ADR 0027）。
"""
from __future__ import annotations

from gherkai_core.model import (
    DEFAULT_ACQUIRE_TIMEOUT_S,
    AppRef,
    DeviceFarmRequest,
    Job,
    JobResult,
    JobState,
    ReportRef,
    ResourceUri,
    RunMeta,
    RunResult,
    RunState,
    Scenario,
    SessionRecord,
    Status,
    Step,
    StepArgument,
    StepResult,
    Target,
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
    """step 的多行参数（可省：无参数的 step 不带 argument 键，契约页如此登记）；有则 kind 与对应正文键必在，不补空值。"""
    if d is None:
        return None
    kind = _require(d, "kind", "step 参数")
    if kind == "docString":
        return StepArgument(kind="docString", content=_require(d, "content", "docString 参数"))
    if kind == "dataTable":
        return StepArgument(kind="dataTable", rows=tuple(tuple(r) for r in _require(d, "rows", "dataTable 参数")))
    from gherkai_core.errors import DefinitionContractError
    raise DefinitionContractError(f"definition 里的 step 参数 kind 未知：{kind!r}")


def _step_to_dict(s: Step) -> dict:
    d: dict = {"index": s.index, "keyword": s.keyword, "text": s.text}
    arg = _argument_to_dict(s.argument)
    if arg is not None:
        d["argument"] = arg
    return d


def _step_from_dict(d: dict) -> Step:
    return Step(index=_require(d, "index", "step"), keyword=_require(d, "keyword", "step"), text=_require(d, "text", "step"),
                argument=_argument_from_dict(d.get("argument")))


def _scenario_def_to_dict(sc: Scenario) -> dict:
    return {"id": sc.id, "name": sc.name, "steps": [_step_to_dict(s) for s in sc.steps]}


def _scenario_def_from_dict(d: dict) -> Scenario:
    return Scenario(id=_require(d, "id", "scenario"), name=_require(d, "name", "scenario"),
                    steps=tuple(_step_from_dict(s) for s in _require(d, "steps", "scenario")))


# definition 的结构版本（ADR 0037 决策 7）：同一结构版本下 definition 的**键集固定、不适用的值写 null**；读端只认当前这一个版本
# （缺键读作 0，与任何不等于它的值一律按版本不符拒绝），不为旧版本留分支或缺省——结构变化一律靶在这一个整数比较上。
# 读端据此可以要求每个键都在（缺键是定义违约、不是「用缺省值」）。1.5 写出的第一个版本是 1。
DEFINITION_SCHEMA_VERSION = 1


def definition_schema_version(d: dict) -> int:
    """从 definition 的 dict 读结构版本：缺键读作 0（早于结构版本号的写端）；不是整数即定义违约。"""
    v = d.get("schema_version", 0)
    if isinstance(v, bool) or not isinstance(v, int):
        from gherkai_core.errors import DefinitionContractError
        raise DefinitionContractError(f"definition 的 schema_version 须为整数，现为 {v!r}")
    return v


def require_definition_schema(d: dict) -> None:
    """读 definition 的第一步：结构版本不等于本读端支持的那一个即抛 UnsupportedDefinitionSchema（带写端 CLI 版本供点名）。"""
    found = definition_schema_version(d)
    if found != DEFINITION_SCHEMA_VERSION:
        from gherkai_core.errors import UnsupportedDefinitionSchema
        raise UnsupportedDefinitionSchema(found, DEFINITION_SCHEMA_VERSION, cli_version=d.get("cli_version"))


def _require(d: dict, key: str, what: str):
    """固定键集的读法：键必须在（值可为 null），缺键按定义违约报——不再用缺省值兜（那是结构版本号之前的兼容手法）。"""
    if not isinstance(d, dict) or key not in d:
        from gherkai_core.errors import DefinitionContractError
        # 诊断只列已有键、不附整份 dict：run 级 dict 内联还原后可达数百 KB、还含隧道请求头，整份 repr 既无界也会把密文带进日志
        have = f"已有键 {sorted(d)}" if isinstance(d, dict) else f"它不是对象而是 {type(d).__name__}"
        raise DefinitionContractError(f"definition 里的 {what} 缺键 {key}（结构版本 {DEFINITION_SCHEMA_VERSION} 的键集固定，不适用的值写 null）；{have}")
    return d[key]


def job_to_dict(job: Job) -> dict:
    """Job(definition) → dict（双向，RunMeta 落盘）。键集固定（ADR 0037 决策 7）：timeout_s 不超时写 null、target 桌面也写
    desktop/web、device_request 非设备 job 写 null。"""
    return {
        "scope_id": job.scope_id,
        "scope_name": job.scope_name,
        "engine": job.engine,
        "scenarios": [_scenario_def_to_dict(sc) for sc in job.scenarios],
        "assertion_votes": job.assertion_votes,
        "timeout_s": job.timeout_s,  # None 表示不超时（只对桌面 scope；ADR 0034「job timeout」节）
        "target": _target_to_dict(job.target),  # ADR 0048 决策 3
        "device_request": _device_request_to_dict(job.device_request) if job.device_request is not None else None,
    }


def job_from_dict(d: dict, *, validate: bool = True) -> Job:
    """dict → Job（键集固定，缺任一键即定义违约）。validate=True 时按 ADR 0048 决策 3 做推进器读 definition 时的那次结构校验
    （违约抛 DefinitionContractError）；plan 形态或测试夹具可传 False。"""
    job = Job(
        scope_id=_require(d, "scope_id", "job"),
        scope_name=_require(d, "scope_name", "job"),
        engine=_require(d, "engine", "job"),
        scenarios=tuple(_scenario_def_from_dict(sc) for sc in _require(d, "scenarios", "job")),
        assertion_votes=_require(d, "assertion_votes", "job"),
        timeout_s=_require(d, "timeout_s", "job"),
        target=_target_from_dict(_require(d, "target", "job")),
        device_request=_device_request_from_dict(_require(d, "device_request", "job")),
    )
    if validate:
        from gherkai_core.target import validate_job_definition  # 读时校验（ADR 0048 决策 3）；延迟导入避免 model/serialize 环
        validate_job_definition(job)
    return job


def _definition_error(what: str, d, e: Exception) -> "DefinitionContractError":
    from gherkai_core.errors import DefinitionContractError
    return DefinitionContractError(f"definition 里的 {what} 形态不对（{type(e).__name__}：{e}）：{d!r}")


def _target_to_dict(t: Target) -> dict:
    out: dict = {"device": t.device, "ui_kind": t.ui_kind}
    if t.app is not None:
        # plan 形态只有 alias 与 app_id、位置三项省略；definition 形态五项齐全（ADR 0048 决策 3）
        app = {"alias": t.app.alias, "app_id": t.app.app_id}
        for k in ("bucket", "key", "sha256"):
            v = getattr(t.app, k)
            if v is not None:
                app[k] = v
        out["app"] = app
    return out


def _target_from_dict(d) -> Target:
    """target 恒为对象（桌面网页也写 desktop/web，ADR 0048 决策 3 / 0037 决策 7）。形态不对（不是对象、缺 device / ui_kind、
    应用条目缺别名或包名）按定义违约报，不让 KeyError / TypeError 漏出去——读时校验承诺的是 DefinitionContractError。"""
    if not isinstance(d, dict):
        raise _definition_error("target", d, TypeError("target 须为对象（桌面网页也写 desktop/web）"))
    try:
        app = d.get("app")
        app_ref = None
        if app is not None:
            app_ref = AppRef(alias=app.get("alias"), app_id=app.get("app_id"), bucket=app.get("bucket"), key=app.get("key"),
                             sha256=app.get("sha256"))  # 缺项留 None，由 validate_job_definition 按「五项齐全」拒绝
        return Target(device=d.get("device"), ui_kind=d.get("ui_kind"), app=app_ref)
    except (AttributeError, TypeError) as e:
        raise _definition_error("target", d, e) from None


def _device_request_to_dict(r: DeviceFarmRequest) -> dict:
    out: dict = {"provider": r.provider, "billing_method": r.billing_method, "project_arn": r.project_arn,
                 "acquire_timeout_s": r.acquire_timeout_s}
    if r.device_arn is not None:
        out["device_arn"] = r.device_arn
    if r.os_version is not None:
        out["os_version"] = r.os_version
    return out


def _device_request_from_dict(d: dict | None) -> DeviceFarmRequest | None:
    """读端不补缺省值：definition 里存的是组合根解析出的具体值（ADR 0048 决策 3 / 0053），缺键就留 None、由 validate_job_definition 拒绝；
    形态不对按定义违约报。"""
    if d is None:
        return None
    try:
        return DeviceFarmRequest(project_arn=d.get("project_arn"), device_arn=d.get("device_arn"), os_version=d.get("os_version"),
                                 billing_method=d.get("billing_method"), acquire_timeout_s=d.get("acquire_timeout_s"),
                                 provider=d.get("provider"))
    except (AttributeError, TypeError) as e:
        raise _definition_error("device_request", d, e) from None


# ============================================================================
# 判定：JobResult / RunResult ↔ dict
# ============================================================================


def ref_to_dict(rr: ReportRef) -> dict:
    """ReportRef → dict。**公开名**：与 `job_to_dict`/`to_dict` 同列的共享入口——`jobs/*.json`、`run --json`
    与 cli 的 explain 文档都用这一份（不透明搬运 kind/ref/label，ADR 0027），故不做私有符号被外部依赖。"""
    return {"kind": rr.kind, "ref": rr.ref, "label": rr.label}


def _ref_from_dict(d: dict) -> ReportRef:
    # ref 包成 ResourceUri 仅为命名意图（带 scheme 的资源指针）；运行时仍是原字符串。
    return ReportRef(kind=d["kind"], ref=ResourceUri(d["ref"]), label=d.get("label"))


def _votes_from_dict(d: dict | None) -> Votes | None:
    return Votes(yes=d["yes"], total=d["total"]) if d else None


def _session_to_dict(s: SessionRecord) -> dict:
    """SessionRecord → dict（ADR 0051 决策 7，机读键见 cli-json-contract 的 jobs[].sessions[]）。release 为 None（没收到
    session_closed）时写端归为 unconfirmed：契约只列 confirmed / unconfirmed，终结时没收到即视为未确认（ADR 0034 机制二 U 集）。"""
    return {"session_id": s.session_id, "name": s.name, "origin": s.origin,
            "release": s.release if s.release is not None else "unconfirmed",
            "observed_s": s.observed_s, "provider_minutes": s.provider_minutes, "device": s.device}


def _session_from_dict(d: dict) -> SessionRecord:
    return SessionRecord(session_id=d.get("session_id"), name=d["name"], origin=d["origin"],
                         release=d.get("release"), observed_s=d.get("observed_s"),
                         provider_minutes=d.get("provider_minutes"), device=d.get("device"))


def _device_keys(sessions: list[SessionRecord], observed_s: float | None, missing: int | None) -> dict:
    """会话记录与两个设备计量键（ADR 0051 决策 4、7），出现条件各自独立：

    - `sessions`：有会话记录或计量键有值即写出。桌面 worker 也发会话事件，桌面 job 因此也可带它；设备 job 没有会话记录时随计量键写成空数组。
    - `device_observed_s` / `device_observed_missing`：两键同层成对，只在有值时写出。有值与否由 `project.apply_device_metering` 按目标
      决定（只给设备 job 填），本函数不按会话记录推断——桌面 job 带会话记录时也不出现两个 null 计量键。
    """
    metered = observed_s is not None or missing is not None
    d: dict = {}
    if sessions or metered:
        d["sessions"] = [_session_to_dict(s) for s in sessions]
    if metered:
        d["device_observed_s"] = observed_s
        d["device_observed_missing"] = missing
    return d


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
        d["scope_id"] = jr.scope_id      # 聚合：唯一的顶层 def 字段就是 join key（from_dict 据此 join run_meta）
    d.update({
        "status": jr.status.value,
        "duration_ms": jr.duration_ms,
        "total_tokens": jr.total_tokens,
        "total_time_worked_s": jr.total_time_worked_s,
        "session_id": jr.session_id,
        "error_type": jr.error_type,
        "message": jr.message,
        **_device_keys(jr.sessions, jr.device_observed_s, jr.device_observed_missing),
        "report_refs": [ref_to_dict(rr) for rr in jr.report_refs],
        "scenarios": [
            {
                "scenario_id": sr.scenario_id,
                "status": sr.status.value,
                "duration_ms": sr.duration_ms,
                "report_refs": [ref_to_dict(rr) for rr in sr.report_refs],
                "steps": [
                    {
                        "index": st.index,
                        "status": st.status.value,
                        "duration_ms": st.duration_ms,
                        "votes": ({"yes": st.votes.yes, "total": st.votes.total} if st.votes else None),
                        "error_type": st.error_type,
                        "message": st.message,  # step 级失败原因原文（ADR 0042 决策三）
                        "report_refs": [ref_to_dict(rr) for rr in st.report_refs],  # step 级产物：两引擎的 kind=evidence + Nova 的 kind=trajectory（ADR 0042 决策一 / 0027）
                        "shortcircuited": st.shortcircuited,  # scope 内短路标记（ADR 0031 决定六）
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
    顶层 scope_id 仅在【聚合形态】出现、是 join key（非 def 来源）；【自包含形态】顶层无 def 字段。
    """
    from gherkai_core.model import ScenarioResult  # 局部 import 避免顶层顺序耦合

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
                        message=st.get("message"),  # 向后兼容：ADR 0042 之前的落盘无此键 → None
                        report_refs=tuple(_ref_from_dict(r) for r in st.get("report_refs", [])),  # 向后兼容：旧落盘无此键
                        shortcircuited=st.get("shortcircuited", False),  # 向后兼容：旧落盘无此键 → 默认 False（ADR 0031）
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
        # 会话记录与计量（ADR 0051 决策 4、7）：缺键（旧落盘、没有会话记录的桌面 job）→ 空列表与 None；带会话记录的桌面 job 只有 sessions
        sessions=[_session_from_dict(s) for s in d.get("sessions", [])],
        device_observed_s=d.get("device_observed_s"),
        device_observed_missing=d.get("device_observed_missing"),
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
        # 设备计量的 run 级合计（ADR 0051 决策 7）：run 里没有设备 job 时省键
        **({"device_observed_s": result.device_observed_s, "device_observed_missing": result.device_observed_missing}
           if result.device_observed_s is not None or result.device_observed_missing is not None else {}),
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
        device_observed_s=d.get("device_observed_s"),
        device_observed_missing=d.get("device_observed_missing"),
    )


# ============================================================================
# definition 信封 RunMeta + 控制面 RunState ↔ dict（RunStore 落盘，ADR 0016）
# ============================================================================


def run_meta_to_dict(meta: RunMeta) -> dict:
    """RunMeta → dict（run_meta.json / DDB META 的 meta_json）。键集固定、不适用写 null（ADR 0037 决策 7）：
    序列化层忠实往返、不替语义层把关（0 的 max_concurrency、空串的 steps_dir、空 dict 的 worker_task_defs 都原样落）。"""
    return {
        "schema_version": DEFINITION_SCHEMA_VERSION,
        "cli_version": meta.cli_version,  # 只记不比（ADR 0037 决策 7）
        "run_id": meta.run_id,
        "created_at": meta.created_at,
        "jobs": [job_to_dict(j) for j in meta.jobs],
        # extra_http_headers（ADR 0035 决策 4）：落盘存 dict 形式（可读）、**键序在写端规范化**（sorted）——规范化归写端、读端原样
        # 保序，from_dict 才是 to_dict 的忠实逆。判真而非 `is not None`：空表与 None 语义合一（都是「不注入额外头」），一律写 null，
        # 别落个 {} 让读端再把 `()` 悄悄变形（往返不恒等）。
        "extra_http_headers": dict(sorted(meta.extra_http_headers)) if meta.extra_http_headers else None,
        "max_concurrency": meta.max_concurrency,  # ADR 0034 机制四；None 表示提交侧没有给（推进器按各自口径回落）
        "steps_dir": meta.steps_dir,  # ADR 0037 决策 4；None 表示无使用方 step（云端后端恒 None）
        "worker_variant": meta.worker_variant,  # ADR 0038；本机后端 None。两者各自独立，序列化层不做「有 A 必有 B」的把关
        "worker_task_defs": dict(meta.worker_task_defs) if meta.worker_task_defs is not None else None,
        "session_warmup_url": meta.session_warmup_url,  # ADR 0051 决策 13；不经隧道为 None
    }


def run_meta_from_dict(d: dict) -> RunMeta:
    """dict → RunMeta。第一步核结构版本（不等于本读端支持的即抛 UnsupportedDefinitionSchema），其后每个键都必须在（缺键是定义违约）。"""
    require_definition_schema(d)
    hdrs = _require(d, "extra_http_headers", "run_meta")
    wtd = _require(d, "worker_task_defs", "run_meta")
    return RunMeta(
        run_id=_require(d, "run_id", "run_meta"),
        created_at=_require(d, "created_at", "run_meta"),
        jobs=tuple(job_from_dict(j) for j in _require(d, "jobs", "run_meta")),
        extra_http_headers=tuple(hdrs.items()) if hdrs else None,  # 原样保序（键序已由写端规范化）；null 与空表都读回 None
        max_concurrency=_require(d, "max_concurrency", "run_meta"),
        steps_dir=_require(d, "steps_dir", "run_meta"),
        worker_variant=_require(d, "worker_variant", "run_meta"),
        worker_task_defs=dict(wtd) if wtd is not None else None,  # dict 原样复制（键是 engine 名，值是 revision ARN）
        cli_version=_require(d, "cli_version", "run_meta"),
        session_warmup_url=_require(d, "session_warmup_url", "run_meta"),
    )


def run_state_to_dict(state: RunState) -> dict:
    # started_at/ended_at 用 omit-when-None：无值时（如 --no-report 下零落盘运行不取时钟、或未来接力推进的部分态）
    # 写成永远的 "null" 是噪音（读者会当 bug）。键缺失语义（即未取时钟）比 null（即取了为空）更诚实；
    # 有值时（正常 run 经 RunPersistence.begin/finalize 落 started_at/ended_at，ADR 0030）键自然出现
    # （from_dict 用 .get 容忍缺失，round-trip 不破）。
    d: dict = {"run_id": state.run_id, "status": state.status.value}
    if state.started_at is not None:
        d["started_at"] = state.started_at
    if state.ended_at is not None:
        d["ended_at"] = state.ended_at
    # high_water_mark：仅无状态批量运行投影写时有值（ADR 0034 机制三）；同步 run 路径为 None。
    # omit-when-None（同 started_at/ended_at）——旧 run_state.json 无此键、from_dict .get 容忍，round-trip 不破。
    if state.high_water_mark is not None:
        d["high_water_mark"] = state.high_water_mark
    if state.message is not None:  # run 级消息（ADR 0037 决策 7）：只在推进器不经任何 job 就终结 run 时有；omit-when-None
        d["message"] = state.message
    # state.jobs 是 Map（scope_id → JobState，ADR 0030）：落盘 JSON 仍是 list（保 run_state.json 向后兼容）。
    # 必须 .values() 迭代——直接 `for js in state.jobs` 会迭代 dict 的 key（str）、js.scope_id 即 AttributeError。
    d["jobs"] = [
        {"scope_id": js.scope_id, "status": js.status.value, "session_id": js.session_id,
         **({"claimed_at": js.claimed_at} if js.claimed_at is not None else {})}  # omit-when-None（ADR 0034 job timeout）
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
        high_water_mark=d.get("high_water_mark"),  # 向后兼容：旧落盘无此键 → None（ADR 0034 机制三）
        message=d.get("message"),
        jobs={
            j["scope_id"]: JobState(scope_id=j["scope_id"], status=Status(j["status"]),
                                    session_id=j.get("session_id"), claimed_at=j.get("claimed_at"))
            for j in d.get("jobs", [])
        },
    )
