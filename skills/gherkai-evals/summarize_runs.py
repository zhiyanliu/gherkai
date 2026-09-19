#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""汇总一轮（或几轮）评测的 timing.json：每条 eval × 每臂的次数、平均用时、花费、三个污染 / 可重放指标与错误数。

run_evals.py 运行结束后先看这张表再评分（设计见 docs/adr/0043-agent-skill-for-driving-gherkai.md 决策七）：
baseline 臂的 repo_touches / skill_copy_touches 非零 = 污染样本，先隔离再谈通过率；network_calls 非零 = 结果依赖活网、不可重放。

用法：
  python skills/gherkai-evals/summarize_runs.py iteration-3            # 一轮
  python skills/gherkai-evals/summarize_runs.py iteration-4 iteration-5  # 几轮并排
  python skills/gherkai-evals/summarize_runs.py iteration-3 --json      # 机读
"""
from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent.parent / "gherkai-workspace"


def collect(iteration: str) -> dict[tuple[str, str], list[dict]]:
    rows: dict[tuple[str, str], list[dict]] = collections.defaultdict(list)
    for f in sorted((WORKSPACE / iteration).glob("eval-*/*/run-*/timing.json")):
        ev, arm = f.parts[-4], f.parts[-3]
        d = json.loads(f.read_text(encoding="utf-8"))
        g = f.with_name("grading.json")
        d["_pass_rate"] = json.loads(g.read_text(encoding="utf-8")).get("summary", {}).get("pass_rate") if g.is_file() else None
        rows[(ev, arm)].append(d)
    return rows


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("iterations", nargs="+", help="skills/gherkai-workspace/ 下的轮次目录名")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    out = []
    for it in a.iterations:
        rows = collect(it)
        if not rows:
            print(f"{it}: 没有 timing.json", file=sys.stderr)
            continue
        if not a.json:
            print(f"\n== {it}")
            print(f"{'eval':40} {'arm':14} {'n':>2} {'秒':>5} {'usd':>6} {'repo':>4} {'skill':>5} {'net':>3} {'err':>3} {'pass':>5}")
        for (ev, arm), ds in sorted(rows.items()):
            n = len(ds)
            rec = {
                "iteration": it, "eval": ev, "arm": arm, "runs": n,
                "avg_seconds": round(sum(x["total_duration_seconds"] for x in ds) / n),
                "cost_usd": round(sum((x.get("cost_usd") or 0) for x in ds), 2),
                "repo_touches": sum(x.get("repo_touches", 0) for x in ds),
                "skill_copy_touches": sum(x.get("skill_copy_touches", 0) for x in ds),
                "network_calls": sum(x.get("network_calls", 0) for x in ds),
                "errors": sum(1 for x in ds if x.get("num_turns") is None),
                "graded": sum(1 for x in ds if x["_pass_rate"] is not None),
                "pass_rate": (round(sum(x["_pass_rate"] for x in ds if x["_pass_rate"] is not None)
                                    / max(1, sum(1 for x in ds if x["_pass_rate"] is not None)), 3)
                              if any(x["_pass_rate"] is not None for x in ds) else None),
                "contaminated": arm == "without_skill" and any((x.get("repo_touches", 0) or x.get("skill_copy_touches", 0)) for x in ds),
            }
            out.append(rec)
            if not a.json:
                flag = " ← 污染" if rec["contaminated"] else ""
                pr = f"{rec['pass_rate']:.2f}" if rec["pass_rate"] is not None else "-"
                print(f"{ev[:40]:40} {arm:14} {n:>2} {rec['avg_seconds']:>5} {rec['cost_usd']:>6.2f} {rec['repo_touches']:>4} "
                      f"{rec['skill_copy_touches']:>5} {rec['network_calls']:>3} {rec['errors']:>3} {pr:>5}{flag}")
        if not a.json:
            for arm in ("with_skill", "without_skill"):
                ds = [x for (ev, a_), xs in rows.items() if a_ == arm for x in xs]
                if ds:
                    print(f"{'合计 ' + arm:55} {len(ds):>2} {round(sum(x['total_duration_seconds'] for x in ds) / len(ds)):>5} "
                          f"{sum((x.get('cost_usd') or 0) for x in ds):>6.2f}")
    if a.json:
        print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
