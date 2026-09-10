"""LocalReportStore（ADR 0027）：把一次 run 的报告产物归集成本地一份自包含目录。

产出 <report_root>/<run_id>/{manifest.json, index.html}：
- manifest.json = 薄信封（schema_version/run_id/created_at）+ report_index（扁平投影，便于 CI/WebUI 遍历）。
  **不内嵌 result 真值副本**——靠 run_id 软引用那次 run，判定真值由 ResultStore 持有（report 是纯派生视图、
  可删可重建、永不作判定源，ADR 0027/0016）。
- index.html = 最小人可导航入口：每条报告产物一行链接（引擎原生产物 + gherkai 自有 schema 的 step 级 evidence），点开看**原样**文件。摘要直接用内存 RunResult。

不透明搬运（ADR 0027）：对 ReportRef 只「算一个链接」，绝不解析/重写/抽内容、不按 kind 分支。
href 是 core 自算的导航链接（不受不透明铁律约束，铁律圈的是 ref）：local 把落在 run 树内的
file:// 产物相对化（目录可整体搬走、链接不断），否则 href==ref；ref 永远原样保留、不改写。
（产物拷贝式 materialize 已否决——见 ADR 0027「被拒方案」；自包含由 href 相对化零成本达成。）

无重型依赖：index.html 纯 Python 字符串拼装 + html.escape，单文件、零外链 JS/CSS
（对齐 core 薄编排层定位）。
"""
from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Callable
from urllib.parse import urlparse
from urllib.request import url2pathname

from gherkai_core.model import ReportRef, ResourceUri, RunResult

SCHEMA_VERSION = 1


def collect_report_index(result: RunResult, *, make_href: Callable[[ReportRef], str]) -> list[dict]:
    """遍历 result 树，把每个 ReportRef 投影成一条扁平 index 项（三级，ADR 0027）——**local/s3 共享的单一真理源**。

    粒度由 scenario_id/step_index 是否为 None 表达：都 None=scope 级；仅 step_index None=scenario 级；
    两者都非 None=step 级（Nova trajectory 下沉，同 scenario 多 trajectory 靠 step_index 区分）。
    遍历顺序（每 job：scope 级 report_refs → 各 scenario 级 → 各 step 级）两 adapter 必须一致，故抽此共享函数。

    href（导航链接）由 make_href(rr) 回调注入：Local 把 run 树内 file:// 产物相对化、否则 ==ref；S3 恒 ==ref。
    **注意**：投影只产 href（导航用），不产 ref——原始 ref 的权威落盘处是 jobs/*.json（ResultStore 判定真值）
    与内存 RunResult，manifest（派生视图）不留 ref（无人读 + href 相对后 ref 会成绝对泄漏，ADR 0027）。
    """
    entries: list[dict] = []

    def _entry(scope_id: str, scenario_id: str | None, step_index: int | None, engine: str, rr: ReportRef) -> dict:
        return {
            "scope_id": scope_id,
            "scenario_id": scenario_id,
            "step_index": step_index,  # None=scope/scenario 级；非 None=step 级（同 scenario 多 trajectory 区分）
            "engine": engine,
            "kind": rr.kind,
            "href": make_href(rr),    # 导航用链接（Local 相对化 / S3 恒 ==ref）；原始 ref 不进 manifest
            "label": rr.label,
        }

    for jr in result.jobs:
        for rr in jr.report_refs:  # scope 级（Midscene report / Nova session summary）
            entries.append(_entry(jr.scope_id, None, None, jr.engine, rr))
        for sr in jr.scenarios:
            for rr in sr.report_refs:  # scenario 级（当前引擎均不填，留作扩展）
                entries.append(_entry(jr.scope_id, sr.scenario_id, None, jr.engine, rr))
            for st in sr.steps:
                for rr in st.report_refs:  # step 级（Nova trajectory 下沉）
                    entries.append(_entry(jr.scope_id, sr.scenario_id, st.index, jr.engine, rr))
    return entries


class LocalReportStore:
    """ReportStore 的本地文件实现（组合根注入；S3 版只换落点/链接前缀）。"""

    def __init__(self, report_root: str | Path) -> None:
        self._root = Path(report_root)

    def write(self, run_id: str, result: RunResult, *, created_at: str = "") -> ResourceUri:
        """归集出 <root>/<run_id>/{manifest.json, index.html}，返回 index.html 的 file:// ResourceUri。

        返回 file:// URI（而非裸 Path）以对齐 ReportStore 契约：与 S3 adapter（同包 `s3.py`）的 s3:// 返回同形（ADR 0027）。
        resolve() 成绝对路径再 as_uri()——as_uri 要求绝对路径，而 cli 默认 report_dir 是相对的（"reports"）。
        """
        run_dir = self._root / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        # 扁平投影 report_index：从 result 树一次遍历（result 已含全部 report_refs，不逐条 append）。
        # href 把 run 树内的 file:// 产物相对化（目录可整体搬走、链接不断，ADR 0027）；不拷贝产物。
        index_entries = self._collect(result, run_dir)

        # manifest = **纯派生导航视图**（ADR 0027）：不内嵌 result 真值副本——靠 run_id 软引用那次 run。
        # 判定真值由 ResultStore（local 的 jobs/*.json 或 S3ResultStore 的同形 key）持有，运行态/身份由 RunStore
        # （local 的 run_meta.json + run_state.json 或 DynamoDBRunStore 的两 item）持有（三层切分，ADR 0016）。这样 RunReport 是真·派生品（可删可重建、
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

    def preflight(self) -> None:
        """探活 no-op（ADR 0030 决定七）：本地文件后端无「桶不存在」问题，目录随写随建。"""

    def _collect(self, result: RunResult, run_dir: Path) -> list[dict]:
        """遍历 result 树投影 report_index（复用共享 collect_report_index）。

        make_href：把落在 run 树内的本地产物相对化（→ index.html 所在 run_dir 的相对路径，目录可整体
        搬走、链接不断）；远端（s3/http…）或落在树外的产物回落 ==ref（绝对，该条不可移植）。ref 全程不改写
        （不透明铁律圈的是 ref、不是 href，ADR 0027）。（S3ReportStore 传自己的 make_href：href 恒==ref，见 s3.py。）

        run_dir.resolve() 循环外算一次（run 期间不变）——避免逐 ref 重复同一系统调用。
        """
        resolved_run_dir = run_dir.resolve()
        return collect_report_index(result, make_href=lambda rr: _relative_href(rr.ref, resolved_run_dir))


def _relative_href(ref: str, resolved_run_dir: Path) -> str:
    """把 run 树内的本地产物 ref 转成相对 run_dir 的 href；否则原样返回 ref（ADR 0027 href 相对化）。

    只对本地文件（file:// 或裸本地路径，见 local_path_from_uri）相对化，远端 scheme（s3/http…）原样——
    **只按 scheme 分支、绝不按 kind 分支**。产物路径 resolve() 后与已解析的 run_dir 算相对：防 macOS
    /tmp↔/private/tmp 等 symlink 造假 ValueError → 误回落绝对（resolved_run_dir 已由调用方 resolve）。
    产物落在 run_dir 树外（worker 没吃到落点环境变量、落了 SDK 临时目录）→ relative_to 抛错 → 回落 ref（绝对，不可移植）。
    """
    local = local_path_from_uri(ref)
    if local is None:
        return ref  # 非本地文件（s3/http…）：无相对概念，原样
    try:
        rel = local.resolve().relative_to(resolved_run_dir)
    except (ValueError, OSError):
        return ref  # 落在 run 树外 / 解析失败：回落绝对（该条不可移植，已知取舍）
    return rel.as_posix()  # 相对 run_dir（index.html 所在目录）；POSIX 分隔符，URL/跨平台友好


def local_path_from_uri(ref: str) -> Path | None:
    """若 ref 指向本地文件（file:// 或裸路径），返回 Path；远端（http/s3 等）返回 None。

    **公开小工具**（本模块 href 相对化之外的第二个消费者：皮层解引用自有 schema 的产物 ref，ADR 0042
    决策四）——`file://` → 路径的解析只此一份，别在别处再写第二份 urlparse+url2pathname。
    对 ReportRef 的不透明搬运铁律（ADR 0027）不受影响：本函数只算路径、不读内容、不按 kind 分支。

    用 url2pathname 正确还原 file:// URI：解 percent-encoding（如 %20→空格——Nova trajectory
    文件名含中文/空格会被编码），并把 netloc(host) 并回路径。带非 localhost host 的（远端/UNC）→ None。
    裸路径（无 scheme）当本地文件——生产不会出现（ADR 0024 保证 worker 报的 ref 恒带 scheme），是防御性分支。
    """
    parsed = urlparse(ref)
    if parsed.scheme == "":  # 裸路径（无 scheme）：当本地文件（防御性，生产 ref 恒带 scheme）
        return Path(ref)
    if parsed.scheme == "file":
        if parsed.netloc not in ("", "localhost"):
            return None  # file://host/... 远端/UNC，不当本地文件
        return Path(url2pathname(parsed.path))  # 解 percent-encoding
    return None  # http/https/s3… 远端


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
    ② 报告产物导航——report_index 的扁平投影，链接指向引擎原样产物与 gherkai 自有的 step 级 evidence（本页对二者都只
       链接、不解析内容；evidence 的解引用只在 CLI explain，ADR 0042 决策五）。
    """
    esc = html.escape
    run_id = manifest["run_id"]
    status = result.status.value
    color = _STATUS_COLOR.get(status, "#57606a")

    # 判定明细树 ↔ 原生产物列表的**结构关联**（锚点双向链接）：产物列表是平铺的，但判定明细树有 job→scenario→
    # step 层级；用锚点把每条产物和它所属的树节点互相链上，读者点 📎 从树跳到产物、点 ↑ 从产物跳回树节点。
    # 关联键 = 产物挂载层级的 (scope_id, scenario_id, step_index) 三元组（None 表该级为止，对齐 report_index 投影）。
    # node_anchor：把三元组编成 html-safe 的稳定 id（不含任意 UTF-8——scope_id 可能是中文/带 : 的路径，直接进
    # id/#fragment 易踩坑，故用层级前缀 + 在 report_index 里的序号，纯 ASCII、稳定、两边一致）。
    def _node_anchor(scope_id: str, scenario_id, step_index) -> str:
        # 用该节点在 result.jobs 里的位置编号（job i / scenario j / step k），纯 ASCII、确定性、树与列表共用同一算法。
        ji = _job_pos.get(scope_id)
        if ji is None:
            return ""
        if scenario_id is None:
            return f"node-j{ji}"
        si = _scen_pos.get((scope_id, scenario_id))
        if si is None:
            return ""
        if step_index is None:
            return f"node-j{ji}-s{si}"
        return f"node-j{ji}-s{si}-t{step_index}"

    _job_pos = {jr.scope_id: i for i, jr in enumerate(result.jobs)}
    _scen_pos: dict[tuple, int] = {}
    for jr in result.jobs:
        for j, sr in enumerate(jr.scenarios):
            _scen_pos[(jr.scope_id, sr.scenario_id)] = j

    # 每个树节点挂了哪些产物（按 report_index 序号）：树里据此渲染 📎（可多个）链到列表锚点 ref-{seq}。
    _node_refs: dict[str, list[int]] = {}
    for seq, e in enumerate(manifest["report_index"]):
        a = _node_anchor(e["scope_id"], e.get("scenario_id"), e.get("step_index"))
        if a:
            _node_refs.setdefault(a, []).append(seq)

    def _paperclips(anchor: str) -> str:
        # 树节点行尾的 📎 角标：链到该节点在产物列表里的条目（多个产物 → 📎×N，链到首个）。
        seqs = _node_refs.get(anchor)
        if not seqs:
            return ""
        n = f"×{len(seqs)}" if len(seqs) > 1 else ""
        return f' <a class="clip" href="#ref-{seqs[0]}" title="{len(seqs)} 个报告产物">📎{n}</a>'

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
        # 同 render_text 的口径：error 类红字带分类；fail-fast 派生态（skipped/aborted）error_type 恒 None、原因只在
        # message（ADR 0031 决定一）→ 中性 note 色显出来，不复用 err 红（决定二：颜色跟 status 走，别把没跑染成出错）。
        if jr.error_type:
            err = f' <span class="err">{esc(jr.error_type)}: {esc(jr.message or "")}</span>'
        else:
            err = f' <span class="note">{esc(jr.message)}</span>' if jr.message else ""

        scen_blocks = []
        for sr in jr.scenarios:
            step_rows = []
            for st in sr.steps:
                # total>1 才显投票 tally（1/1 无抖动意义，不显，避免噪声）
                votes = (
                    f' <span class="votes">{st.votes.yes}/{st.votes.total} 票</span>'
                    if st.votes and st.votes.total > 1 else ""
                )
                # step 级失败原因原文（ADR 0042 决策三）沿用 job 行的两分支：有 error_type → 并进同一个 err 红 span
                # （`error_type: message`）；无分类（派生态）→ 中性 note 色。别再造第三种样式。
                if st.error_type:
                    serr = f' <span class="err">{esc(st.error_type)}{(": " + esc(st.message)) if st.message else ""}</span>'
                else:
                    serr = f' <span class="note">{esc(st.message)}</span>' if st.message else ""
                # 连锁失败旁注（ADR 0031 决定六）：被 scope 内短路的 step（shortcircuited=True，status=skipped）——
                # 上游 error 后 worker 跳过了它、没在损坏环境上跑。读 shortcircuited 正交布尔（比旧的"按 status 顺序猜"
                # 精确）；不改判定/severity（守纯 reducer 红线）。
                taint = (
                    ' <span class="taint">⚠ 因前置 step error 被跳过（未执行）</span>'
                    if st.shortcircuited else ""
                )
                st_anchor = _node_anchor(jr.scope_id, sr.scenario_id, st.index)
                step_rows.append(
                    f'<li id="{st_anchor}">{_dot(st.status.value)}<span class="stp">step[{st.index}]</span> '
                    f'{esc(st.status.value)} <span class="t">{_fmt_ms(st.duration_ms)}</span>'
                    f'{votes}{serr}{taint}{_paperclips(st_anchor)}</li>'
                )
            steps_html = ("<ul class=\"steps\">" + "".join(step_rows) + "</ul>") if step_rows else ""
            sc_anchor = _node_anchor(jr.scope_id, sr.scenario_id, None)
            scen_blocks.append(
                f'<li id="{sc_anchor}">{_dot(sr.status.value)}<span class="scn">{esc(sr.scenario_id)}</span> '
                f'{esc(sr.status.value)} <span class="t">{_fmt_ms(sr.duration_ms)}</span>'
                f'{_paperclips(sc_anchor)}{steps_html}</li>'
            )
        scen_html = ("<ul class=\"scns\">" + "".join(scen_blocks) + "</ul>") if scen_blocks else ""
        job_anchor = _node_anchor(jr.scope_id, None, None)
        job_blocks.append(
            f'<div class="job" id="{job_anchor}">'
            f'<div class="jobhd">{_dot(jr.status.value)}'
            f'<code>{esc(jr.scope_id)}</code> <b>{esc(jr.status.value)}</b>{err}{_paperclips(job_anchor)}'
            f'<div class="jobmeta">{" · ".join(meta_bits)}</div></div>'
            f'{scen_html}</div>'
        )
    jobs_html = "\n".join(job_blocks) if job_blocks else '<p class="empty">本次 run 无 job。</p>'

    # ② 报告产物导航（report_index 扁平投影）——每条带 id=ref-{seq} 锚点 + ↑ 链回判定明细树里所属节点，
    # 与树节点行尾的 📎 构成双向关联：读者一眼知道这个产物属于哪个 job/scenario/step（结构由树表达，见上）。
    job_status = {j.scope_id: j.status.value for j in result.jobs}
    rows = []
    for seq, e in enumerate(manifest["report_index"]):
        anchor = e.get("label") or e["kind"]
        scen = f" · {esc(e['scenario_id'])}" if e.get("scenario_id") else ""
        # step 级 trajectory：拼 step[N]，否则同 scenario 多 trajectory 在导航里无法区分
        step = f" · step[{e['step_index']}]" if e.get("step_index") is not None else ""
        # ↑ 回链：跳到判定明细树里该产物所属的节点（scope/scenario/step 级各自的锚点）
        node = _node_anchor(e["scope_id"], e.get("scenario_id"), e.get("step_index"))
        backlink = f' <a class="uplink" href="#{node}" title="定位到判定明细">↑</a>' if node else ""
        rows.append(
            f'<li id="ref-{seq}">{_dot(job_status.get(e["scope_id"], ""))}'
            f'<code>{esc(e["scope_id"])}{scen}{step}</code>{backlink} '
            f'<span class="eng">{esc(e.get("engine") or "")}</span> '
            f'<span class="kind">[{esc(e["kind"])}]</span> '
            f'<a href="{esc(e["href"])}">{esc(anchor)}</a></li>'
        )
    if rows:
        refs_body = "<ul class=\"refs\">\n" + "\n".join(rows) + "\n</ul>"
    else:
        refs_body = '<p class="empty">本次 run 无报告产物（纯确定性步骤既不产引擎报告、也不产 AI 步骤证据；判定明细见上）。</p>'

    return f"""<!doctype html>
<html lang="zh"><head><meta charset="utf-8">
<title>运行报告 {esc(run_id)}</title>
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
  .note {{ color: #57606a; font-size: .85em; }}
  .taint {{ color: #9a6700; font-size: .85em; }}
  ul.refs {{ list-style: none; padding: 0; }}
  ul.refs li {{ padding: .35rem 0; border-bottom: 1px solid #eee; }}
  .dot {{ display: inline-block; width: .6rem; height: .6rem; border-radius: 50%; margin-right: .5rem; vertical-align: middle; }}
  .eng {{ color: #57606a; }}
  .kind {{ color: #8250df; font-size: .85em; }}
  code {{ background: #eff1f3; padding: .1rem .3rem; border-radius: 4px; }}
  .empty {{ color: #57606a; }}
  /* 判定明细树 ↔ 产物列表的双向关联：📎（树→产物）、↑（产物→树），点击平滑滚动 + 高亮落点 */
  .clip, .uplink {{ text-decoration: none; font-size: .85em; }}
  .clip {{ color: #8250df; }}
  .uplink {{ color: #57606a; }}
  html {{ scroll-behavior: smooth; }}
  :target {{ background: #fff8c5; border-radius: 4px; box-shadow: 0 0 0 4px #fff8c5; }}
</style></head>
<body>
<h1>运行报告</h1>
<div class="summary">
  <div>run_id: <code>{esc(run_id)}</code></div>
  <div>总状态: <span class="status">{esc(status)}</span> · 墙钟 {esc(dur_s)} · 成本 {esc(cost)}</div>
</div>
<h2>判定明细（{len(result.jobs)} job）</h2>
{jobs_html}
<h2>报告产物（{len(manifest["report_index"])}）——引擎原生产物 + 每个 AI 步骤的证据</h2>
{refs_body}
</body></html>
"""
