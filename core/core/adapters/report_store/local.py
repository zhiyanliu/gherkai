"""LocalReportStore（ADR 0027）：把一次 run 的报告产物归集成本地一份自包含目录。

产出 <report_root>/<run_id>/{manifest.json, index.html}：
- manifest.json = 薄信封（run_id/created_at/tool/schema_version）+ to_dict(RunResult)（单一真理源）
  + report_index（扁平投影，便于 CI/WebUI 遍历）。
- index.html = 最小人可导航入口：每条报告产物一行链接，点开看**原样的**原生产物。

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

from core.model import RunResult
from core.serialize import to_dict

SCHEMA_VERSION = 1


class LocalReportStore:
    """ReportStore 的本地文件实现（组合根注入；S3 版只换落点/链接前缀）。"""

    def __init__(self, report_root: str | Path) -> None:
        self._root = Path(report_root)

    def write(self, run_id: str, result: RunResult, *, created_at: str = "", materialize: bool = False) -> Path:
        """归集出 <root>/<run_id>/{manifest.json, index.html}，返回 index.html 路径。"""
        run_dir = self._root / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        # 扁平投影 report_index：从 result 树一次遍历（result 已含全部 report_refs，不逐条 append）。
        # materialize=True 时顺带把本地产物按字节拷进 artifacts/，并把 ref 改成相对链接。
        index_entries = self._collect(result, run_dir, materialize)

        manifest = {
            "schema_version": SCHEMA_VERSION,
            "run_id": run_id,
            "created_at": created_at,
            "tool": "yaozhou",
            "result": to_dict(result),
            "report_index": index_entries,
        }
        (run_dir / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        index_path = run_dir / "index.html"
        index_path.write_text(_render_index_html(manifest), encoding="utf-8")
        return index_path

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

_STATUS_COLOR = {"passed": "#1a7f37", "failed": "#cf222e", "error": "#9a6700"}


def _render_index_html(manifest: dict) -> str:
    esc = html.escape
    result = manifest["result"]
    run_id = manifest["run_id"]
    status = result["status"]
    color = _STATUS_COLOR.get(status, "#57606a")

    dur = result.get("duration_ms")
    dur_s = f"{dur / 1000:.1f}s" if dur is not None else "?"
    cost_bits = []
    if result.get("total_tokens") is not None:
        cost_bits.append(f"{result['total_tokens']} tokens")
    if result.get("total_time_worked_s") is not None:
        cost_bits.append(f"{result['total_time_worked_s']:.1f}s agent-time")
    cost = " · ".join(cost_bits) if cost_bits else "—"

    # job.status 映射（按 scope_id），供每行上色
    job_status = {j["scope_id"]: j["status"] for j in result["jobs"]}

    rows = []
    for e in manifest["report_index"]:
        st = job_status.get(e["scope_id"], "")
        c = _STATUS_COLOR.get(st, "#57606a")
        anchor = e.get("label") or e["kind"]
        scen = f" · {esc(e['scenario_id'])}" if e.get("scenario_id") else ""
        rows.append(
            f'<li><span class="dot" style="background:{c}"></span>'
            f'<code>{esc(e["scope_id"])}{scen}</code> '
            f'<span class="eng">{esc(e.get("engine") or "")}</span> '
            f'<span class="kind">[{esc(e["kind"])}]</span> '
            f'<a href="{esc(e["href"])}">{esc(anchor)}</a></li>'
        )
    if rows:
        body = "<ul class=\"refs\">\n" + "\n".join(rows) + "\n</ul>"
    else:
        body = '<p class="empty">本次 run 无原生报告产物（report_refs 为空）。</p>'

    return f"""<!doctype html>
<html lang="zh"><head><meta charset="utf-8">
<title>RunReport {esc(run_id)}</title>
<style>
  body {{ font: 14px/1.5 -apple-system, system-ui, sans-serif; margin: 2rem; color: #1f2328; }}
  h1 {{ font-size: 1.2rem; }}
  .summary {{ padding: .6rem .9rem; border-left: 4px solid {color}; background: #f6f8fa; margin: 1rem 0; }}
  .status {{ font-weight: 700; color: {color}; text-transform: uppercase; }}
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
<h2>报告产物（{len(manifest["report_index"])}）</h2>
{body}
<p style="color:#57606a;font-size:.85em">归集索引（ADR 0027）：链接指向各引擎**原样的**原生产物；本页不解析其内容。</p>
</body></html>
"""
