"""RunResult → 朴素 dict（单一真理源，ADR 0027）。

序列化的是 core 的领域模型，故属 core——cli 的 --json、ReportStore 的 manifest.json
都复用此函数，不各写一份（避免漂移）。手写映射（不靠 dataclasses.asdict），与 wire.py 同理：
输出形状是对外契约（CI/WebUI/manifest 消费），须显式、稳定。

cost 只含 engine 报的原生量、不折美元（ADR 0024）；report_refs 是不透明搬运
（kind/ref/label 原样，core 不解释，ADR 0027）。
"""
from __future__ import annotations

from core.model import ReportRef, RunResult


def _ref_to_dict(rr: ReportRef) -> dict:
    return {"kind": rr.kind, "ref": rr.ref, "label": rr.label}


def to_dict(result: RunResult) -> dict:
    """RunResult → 朴素 dict（机器可读：CI / WebUI / manifest 消费）。"""
    return {
        "run_id": result.run_id,
        "status": result.status.value,
        "duration_ms": result.duration_ms,
        "total_tokens": result.total_tokens,
        "total_time_worked_s": result.total_time_worked_s,
        "jobs": [
            {
                "scope_id": jr.scope_id,
                "engine": jr.engine,
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
                                "votes": (
                                    {"yes": st.votes.yes, "total": st.votes.total}
                                    if st.votes
                                    else None
                                ),
                                "error_type": st.error_type,
                            }
                            for st in sr.steps
                        ],
                    }
                    for sr in jr.scenarios
                ],
            }
            for jr in result.jobs
        ],
    }
