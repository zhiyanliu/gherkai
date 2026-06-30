"""LocalReportStore（ADR 0027）：把一次 run 的报告产物归集成本地一份自包含目录。

产出 <report_root>/<run_id>/{manifest.json, index.html}：
- manifest.json = 薄信封（schema_version/run_id/created_at）+ report_index（扁平投影，便于 CI/WebUI 遍历）。
  **不内嵌 result 真值副本**——靠 run_id 软引用那次 run，判定真值由 ResultStore 持有（report 是纯派生视图、
  可删可重建、永不作判定源，ADR 0027/0016）。
- index.html = 最小人可导航入口：每条报告产物一行链接，点开看**原样的**原生产物。摘要直接用内存 RunResult。

不透明搬运（ADR 0027）：对 ReportRef 只「算一个链接（+可选按字节拷贝）」，绝不解析/重写/抽内容、
不按 kind 分支。materialize=False（默认）不拷贝、链接直指 ref；=True 拷进 artifacts/ 求自包含。

无重型依赖：index.html 纯 Python 字符串拼装 + html.escape，单文件、零外链 JS/CSS
（对齐 core 薄编排层定位）。
"""
from __future__ import annotations

import html
import json
import shutil
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import url2pathname

from core.model import ResourceUri, RunResult

SCHEMA_VERSION = 1


class LocalReportStore:
    """ReportStore 的本地文件实现（组合根注入；S3 版只换落点/链接前缀）。"""

    def __init__(self, report_root: str | Path) -> None:
        self._root = Path(report_root)

    def write(self, run_id: str, result: RunResult, *, created_at: str = "", materialize: bool = False) -> ResourceUri:
        """归集出 <root>/<run_id>/{manifest.json, index.html}，返回 index.html 的 file:// ResourceUri。

        返回 file:// URI（而非裸 Path）以对齐 ReportStore 契约：与未来 S3 adapter 的 s3:// 返回同形（ADR 0027）。
        resolve() 成绝对路径再 as_uri()——as_uri 要求绝对路径，而 cli 默认 report_dir 是相对的（"reports"）。
        """
        run_dir = self._root / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        # 扁平投影 report_index：从 result 树一次遍历（result 已含全部 report_refs，不逐条 append）。
        # materialize=True 时顺带把本地产物按字节拷进 artifacts/，并把 ref 改成相对链接。
        index_entries = self._collect(result, run_dir, materialize)

        # manifest = **纯派生导航视图**（ADR 0027）：不内嵌 result 真值副本——靠 run_id 软引用那次 run。
        # 判定真值由 ResultStore（jobs/*.json / 未来对象存储）持有，运行态/身份由 RunStore（run_meta.json
        # + run_state.json / 未来 DDB）持有（三层切分，ADR 0016）。这样 RunReport 是真·派生品（可删可重建、
        # 永不作判定源），无真值冗余、无一致性风险。CI 要判定 → 用 run_id 找 ResultStore。
        manifest = {
            "schema_version": SCHEMA_VERSION,
            "run_id": run_id,        # 软引用那次 run（判定真值在 ResultStore 的 jobs/*.json，按此 id 取）
            "created_at": created_at,
            "report_index": index_entries,
        }
        (run_dir / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        # index.html 摘要直接用内存 result（不从 manifest 取——manifest 已不含 result）
        index_path = run_dir / "index.html"
        index_path.write_text(_render_index_html(manifest, result), encoding="utf-8")
        return ResourceUri(index_path.resolve().as_uri())

    def _collect(self, result: RunResult, run_dir: Path, materialize: bool) -> list[dict]:
        """遍历 result 树，把每个 ReportRef 投影成一条扁平 index 项。

        scenario_id=None 表 scope 级 ref（来自 scope_done）；否则是 scenario 级（来自 scenario_done）。
        """
        entries: list[dict] = []
        seq = 0  # 单调序号：materialize 时给 artifact 目标名加前缀去碰撞（不同源目录同 basename 不互相覆盖）
        for jr in result.jobs:
            for rr in jr.report_refs:
                entries.append(self._entry(jr.scope_id, None, jr.engine, rr, run_dir, materialize, seq))
                seq += 1
            for sr in jr.scenarios:
                for rr in sr.report_refs:
                    entries.append(
                        self._entry(jr.scope_id, sr.scenario_id, jr.engine, rr, run_dir, materialize, seq)
                    )
                    seq += 1
        return entries

    def _entry(self, scope_id, scenario_id, engine, rr, run_dir: Path, materialize: bool, seq: int) -> dict:
        href = rr.ref
        if materialize:
            local = _local_path(rr.ref)
            if local is not None and local.exists():
                href = _materialize(local, run_dir, seq)
        return {
            "scope_id": scope_id,
            "scenario_id": scenario_id,
            "engine": engine,
            "kind": rr.kind,
            "ref": rr.ref,            # 原始 ref（不透明，原样保留）
            "href": href,             # 导航用链接（materialize 时为相对路径，否则 == ref）
            "label": rr.label,
        }


def _local_path(ref: str) -> Path | None:
    """若 ref 指向本地文件（file:// 或裸路径），返回 Path；远端（http/s3 等）返回 None。

    用 url2pathname 正确还原 file:// URI：解 percent-encoding（如 %20→空格——Nova trajectory
    文件名含中文/空格会被编码），并把 netloc(host) 并回路径。带非 localhost host 的（远端/UNC）→ None。
    """
    parsed = urlparse(ref)
    if parsed.scheme == "":  # 裸路径（无 scheme），原样
        return Path(ref)
    if parsed.scheme == "file":
        if parsed.netloc not in ("", "localhost"):
            return None  # file://host/... 远端/UNC，不当本地拷
        return Path(url2pathname(parsed.path))  # 解 percent-encoding
    return None  # http/https/s3… 远端，不拷贝


def _materialize(src: Path, run_dir: Path, seq: int) -> str:
    """把本地产物按字节拷进 <run_dir>/artifacts/，返回相对 run_dir 的链接（不解析内容）。

    目标名加 seq 前缀去碰撞：一次 run 内不同源目录的同 basename 产物不会互相覆盖（数据丢失）。
    """
    artifacts = run_dir / "artifacts"
    artifacts.mkdir(exist_ok=True)
    name = f"{seq:03d}_{src.name}"
    dest = artifacts / name
    if src.is_dir():
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(src, dest)
    else:
        shutil.copy2(src, dest)
    return f"artifacts/{name}"


# ---- index.html 渲染（纯字符串，无模板引擎；按 kind 不分支，只回显）----

# 终态判定色 + core 派生态/前置态色（ADR 0031 touch point）：每态各配可区分的视觉，否则新态全走兜底灰
# #57606a，aborted（severity 最高、最该被看）会与 error/兜底混淆。
_STATUS_COLOR = {
    "passed": "#1a7f37",   # 绿
    "failed": "#cf222e",   # 红
    "error": "#9a6700",    # 琥珀
    "skipped": "#8c959f",  # 弱化灰（没执行、最该被无视；须与兜底 #57606a 可分）
    "aborted": "#8250df",  # 紫（有现场、最该被看；与 error 琥珀 + 兜底灰都可区分）
    "pending": "#0969da",  # 蓝（进行中前置态；当前到不了 report，为未来 RunState 视图兜底）
    "running": "#0969da",  # 蓝（进行中）
}


def _fmt_ms(ms: float | None) -> str:
    return f"{ms / 1000:.1f}s" if ms is not None else "?"


def _render_index_html(manifest: dict, result: RunResult) -> str:
    """渲染入口页。manifest 提供 run_id/created_at/report_index；result（内存 RunResult）提供判定明细 + 摘要。

    两块内容（ADR 0027/0016）：
    ① 判定明细（job→scenario→step，status/时长/sessionId）——直接从内存 RunResult 渲染，让纯确定性
       run（无原生产物）也一眼看懂结果（判定真值仍以 ResultStore 的 jobs/*.json 为准，本页只是人看视图）。
    ② 报告产物导航——report_index 的扁平投影，链接指向各引擎原样产物（不透明搬运，不解析内容）。
    """
    esc = html.escape
    run_id = manifest["run_id"]
    status = result.status.value
    color = _STATUS_COLOR.get(status, "#57606a")

    dur_s = _fmt_ms(result.duration_ms)
    cost_bits = []
    if result.total_tokens is not None:
        cost_bits.append(f"{result.total_tokens} tokens")
    if result.total_time_worked_s is not None:
        cost_bits.append(f"{result.total_time_worked_s:.1f}s agent-time")
    cost = " · ".join(cost_bits) if cost_bits else "—"

    # ① 判定明细：job → scenario → step 树（从内存 RunResult 渲染）
    def _dot(st: str) -> str:
        return f'<span class="dot" style="background:{_STATUS_COLOR.get(st, "#57606a")}"></span>'

    job_blocks = []
    for jr in result.jobs:
        jbits = []
        if jr.total_tokens is not None:
            jbits.append(f"{jr.total_tokens} tokens")
        if jr.total_time_worked_s is not None:
            jbits.append(f"{jr.total_time_worked_s:.1f}s agent-time")
        meta_bits = [f"{esc(jr.engine)}", f"墙钟 {_fmt_ms(jr.duration_ms)}"]
        if jbits:
            meta_bits.append(" · ".join(jbits))
        if jr.session_id:
            meta_bits.append(f"会话 <code>{esc(jr.session_id)}</code>")
        err = f' <span class="err">{esc(jr.error_type)}: {esc(jr.message or "")}</span>' if jr.error_type else ""

        scen_blocks = []
        for sr in jr.scenarios:
            step_rows = []
            for st in sr.steps:
                # total>1 才显投票 tally（1/1 无抖动意义，不显，避免噪声）
                votes = (
                    f' <span class="votes">{st.votes.yes}/{st.votes.total} 票</span>'
                    if st.votes and st.votes.total > 1 else ""
                )
                serr = f' <span class="err">{esc(st.error_type)}</span>' if st.error_type else ""
                step_rows.append(
                    f'<li>{_dot(st.status.value)}<span class="stp">step[{st.index}]</span> '
                    f'{esc(st.status.value)} <span class="t">{_fmt_ms(st.duration_ms)}</span>{votes}{serr}</li>'
                )
            steps_html = ("<ul class=\"steps\">" + "".join(step_rows) + "</ul>") if step_rows else ""
            scen_blocks.append(
                f'<li>{_dot(sr.status.value)}<span class="scn">{esc(sr.scenario_id)}</span> '
                f'{esc(sr.status.value)} <span class="t">{_fmt_ms(sr.duration_ms)}</span>{steps_html}</li>'
            )
        scen_html = ("<ul class=\"scns\">" + "".join(scen_blocks) + "</ul>") if scen_blocks else ""
        job_blocks.append(
            f'<div class="job">'
            f'<div class="jobhd">{_dot(jr.status.value)}'
            f'<code>{esc(jr.scope_id)}</code> <b>{esc(jr.status.value)}</b>{err}'
            f'<div class="jobmeta">{" · ".join(meta_bits)}</div></div>'
            f'{scen_html}</div>'
        )
    jobs_html = "\n".join(job_blocks) if job_blocks else '<p class="empty">本次 run 无 job。</p>'

    # ② 报告产物导航（report_index 扁平投影）
    job_status = {j.scope_id: j.status.value for j in result.jobs}
    rows = []
    for e in manifest["report_index"]:
        anchor = e.get("label") or e["kind"]
        scen = f" · {esc(e['scenario_id'])}" if e.get("scenario_id") else ""
        rows.append(
            f'<li>{_dot(job_status.get(e["scope_id"], ""))}'
            f'<code>{esc(e["scope_id"])}{scen}</code> '
            f'<span class="eng">{esc(e.get("engine") or "")}</span> '
            f'<span class="kind">[{esc(e["kind"])}]</span> '
            f'<a href="{esc(e["href"])}">{esc(anchor)}</a></li>'
        )
    if rows:
        refs_body = "<ul class=\"refs\">\n" + "\n".join(rows) + "\n</ul>"
    else:
        refs_body = '<p class="empty">本次 run 无原生报告产物（纯确定性步骤不产引擎报告；判定明细见上）。</p>'

    return f"""<!doctype html>
<html lang="zh"><head><meta charset="utf-8">
<title>RunReport {esc(run_id)}</title>
<style>
  body {{ font: 14px/1.5 -apple-system, system-ui, sans-serif; margin: 2rem; color: #1f2328; }}
  h1 {{ font-size: 1.2rem; }}
  h2 {{ font-size: 1rem; margin: 1.4rem 0 .5rem; }}
  .summary {{ padding: .6rem .9rem; border-left: 4px solid {color}; background: #f6f8fa; margin: 1rem 0; }}
  .status {{ font-weight: 700; color: {color}; text-transform: uppercase; }}
  .job {{ margin: .8rem 0; padding: .5rem .8rem; border: 1px solid #e1e4e8; border-radius: 6px; }}
  .jobhd b {{ text-transform: uppercase; font-size: .85em; }}
  .jobmeta {{ color: #57606a; font-size: .85em; margin: .2rem 0 .3rem 1.1rem; }}
  ul.scns, ul.steps {{ list-style: none; padding-left: 1.1rem; margin: .2rem 0; }}
  ul.steps {{ padding-left: 1.6rem; }}
  ul.scns li, ul.steps li {{ padding: .15rem 0; }}
  .scn {{ color: #1f2328; }}
  .stp {{ color: #57606a; }}
  .t {{ color: #8c959f; font-size: .85em; }}
  .votes {{ color: #0969da; font-size: .85em; }}
  .err {{ color: #cf222e; font-size: .85em; }}
  ul.refs {{ list-style: none; padding: 0; }}
  ul.refs li {{ padding: .35rem 0; border-bottom: 1px solid #eee; }}
  .dot {{ display: inline-block; width: .6rem; height: .6rem; border-radius: 50%; margin-right: .5rem; vertical-align: middle; }}
  .eng {{ color: #57606a; }}
  .kind {{ color: #8250df; font-size: .85em; }}
  code {{ background: #eff1f3; padding: .1rem .3rem; border-radius: 4px; }}
  .empty {{ color: #57606a; }}
</style></head>
<body>
<h1>RunReport</h1>
<div class="summary">
  <div>run_id: <code>{esc(run_id)}</code></div>
  <div>总状态: <span class="status">{esc(status)}</span> · 墙钟 {esc(dur_s)} · 成本 {esc(cost)}</div>
</div>
<h2>判定明细（{len(result.jobs)} job）</h2>
{jobs_html}
<h2>原生报告产物（{len(manifest["report_index"])}）</h2>
{refs_body}
</body></html>
"""
