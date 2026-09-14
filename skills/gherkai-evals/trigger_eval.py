#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""量 skill 的**触发率**（description 优化的那半个循环）：把真 skill 装进临时项目的真实安装位，对
`trigger-eval.json` 的每条查询跑 `claude -p`，看它是否调用 `Skill(gherkai)` 或读了 SKILL.md。

设计见 docs/adr/0043-agent-skill-for-driving-gherkai.md 决策七。与 skill-creator 自带的 `run_eval.py` 两点不同：
- 走**真实 skills 机制**（`gherkai skill install` 进 `.claude/skills/gherkai/`），不是 `.claude/commands/<name>.md`
  ——commands 早已不等于 skills，那条路在当前 Claude Code 上对本 skill 恒 0；
- **容忍触发前先有别的工具调用**（前几次调用里出现即算触发），不是「首个工具调用必须是 Skill/Read」。
查询集里 `project: no-feature` 的条目不放 `.feature`，覆盖「项目里没有 .feature 时只在用户明说 gherkai 才接管」那一档。

用法：
  python skills/gherkai-evals/trigger_eval.py --runs 3
  python skills/gherkai-evals/trigger_eval.py --runs 1 --limit 2      # 冒烟：只跑前两条
产物：`--out` 指定的 JSON（缺省落 skills/gherkai-workspace/trigger/），每条查询一行 trigger_rate / passed + 工具流水。
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import tempfile
import threading
import time
from pathlib import Path

# 与行为评测同一份 env 剥离表与缺省模型（同源，避免两个脚本漂）。
from run_evals import DEFAULT_MODEL, STRIP_ENV

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
EVAL_SET = HERE / "trigger-eval.json"
WORKSPACE = REPO / "skills" / "gherkai-workspace"
DEFAULT_CLI_DIR = Path("/tmp/gherkai-eval-cli")
FEATURE = ('Feature: 登录\n  Scenario: 正常登录\n    Given 打开 "https://example.com/"\n'
           '    Then "页面标题是 Example Domain"\n')
# 判触发：Skill(gherkai)，或读了装进去的那份 SKILL.md。
SKILL_MD_TAIL = "skills/gherkai/SKILL.md"
# 前几次调用里没出现就算没触发（skill 是「一上手就该被想起」的东西，越靠后越不是触发而是摸索）。
MAX_FIRST_TOOLS = 4


def fail(msg: str) -> None:
    raise SystemExit(f"trigger_eval: {msg}")


def resolve_installer(cli_dir: Path) -> Path:
    """用哪个 gherkai 装 skill：优先仓库外那套；它被 `--prepare-cli` 剥掉了包内 skill 时回落到仓库 `.venv`。

    回落在这里是安全的：触发率只量「装好之后被不被调用」，没有 baseline 臂、没有两臂 delta，装的人是谁不进结论；
    行为评测那边则相反（舞台里任何仓库路径都是教材泄漏渠道），故那边只许仓库外那套、不给回落。
    """
    cli = cli_dir / "venv" / "bin" / "gherkai"
    packaged = sorted(cli_dir.glob("venv/lib/python3.*/site-packages/gherkai_cli/skills/gherkai/SKILL.md"))
    if cli.exists() and packaged:
        return cli
    repo_cli = REPO / ".venv" / "bin" / "gherkai"
    if not repo_cli.exists():
        fail(f"没有能装 skill 的 gherkai：{cli} 与 {repo_cli} 都不可用（仓库根 uv sync）")
    why = "它包内的 skill 已被 --prepare-cli 剥掉" if cli.exists() else f"{cli} 不在"
    print(f"trigger_eval: 警告：用仓库 .venv 的 gherkai 装 skill（{why}）", flush=True)
    return repo_cli


def one(query: str, project: str, installer: Path, model: str, timeout: int) -> tuple[bool | None, list[str]]:
    """跑一条查询，返回（是否触发, 前几次工具名）。"""
    proj = Path(tempfile.mkdtemp(prefix="gherkai-trig-"))
    triggered = False
    first_tools: list[str] = []
    try:
        if project != "no-feature":
            (proj / "features").mkdir()
            (proj / "features" / "login.feature").write_text(FEATURE, encoding="utf-8")
        install = subprocess.run([str(installer), "skill", "install", "--dir", str(proj), "--pointer", "no"],
                                 capture_output=True, text=True)
        if install.returncode != 0:
            fail(f"skill install 退 {install.returncode}：{install.stderr.strip()[-400:]}")
        env = {k: v for k, v in os.environ.items() if k not in STRIP_ENV}
        cmd = ["claude", "-p", query, "--output-format", "stream-json", "--verbose", "--no-session-persistence",
               "--allowedTools", "Skill", "Read", "Glob", "Grep", "LS",
               # 与行为评测同理：`-p` 会在后台子代理未完时就返回，那时首几次调用里看不到真正的选择。
               "--disallowedTools", "Workflow", "Agent", "Task", "TodoWrite"]
        if model:
            cmd += ["--model", model]
        proc = subprocess.Popen(cmd, cwd=proj, env=env, stdout=subprocess.PIPE,
                                stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL, text=True)
        t0 = time.time()
        try:
            while time.time() - t0 < timeout:
                line = proc.stdout.readline()
                if not line:
                    if proc.poll() is not None:
                        break
                    continue
                try:
                    ev = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if ev.get("type") == "assistant":
                    for c in ev.get("message", {}).get("content", []):
                        if c.get("type") != "tool_use":
                            continue
                        name = c.get("name", "")
                        inp = c.get("input") or {}
                        first_tools.append(name)
                        if name == "Skill" and "gherkai" in f"{inp.get('skill', '')}{inp.get('command', '')}":
                            triggered = True
                        if name == "Read" and SKILL_MD_TAIL in str(inp.get("file_path", "")):
                            triggered = True
                    if triggered or len(first_tools) >= MAX_FIRST_TOOLS:
                        break
                if ev.get("type") == "result":
                    break
        finally:
            if proc.poll() is None:
                proc.kill()
                proc.wait()
    finally:
        shutil.rmtree(proj, ignore_errors=True)
    return triggered, first_tools[:MAX_FIRST_TOOLS]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--runs", type=int, default=3, help="每条查询跑几次（触发是随机变量，单次没有意义）")
    ap.add_argument("--parallel", type=int, default=4, help="并发的 claude -p 进程数上限")
    ap.add_argument("--timeout", type=int, default=150, help="单次的墙钟上限（秒）")
    ap.add_argument("--out", help="结果 JSON 路径（缺省 skills/gherkai-workspace/trigger/trigger-<时间戳>.json）")
    ap.add_argument("--model", default=DEFAULT_MODEL, help=f"固定模型（缺省 {DEFAULT_MODEL}）")
    ap.add_argument("--cli-dir", default=str(DEFAULT_CLI_DIR),
                    help=f"已备好的仓库外 CLI 目录（缺省 {DEFAULT_CLI_DIR}）；装不了就回落仓库 .venv")
    ap.add_argument("--limit", type=int, default=0, help="只跑前 N 条查询（冒烟用；缺省全跑）")
    a = ap.parse_args()

    if not shutil.which("claude"):
        fail("PATH 里没有 claude")
    installer = resolve_installer(Path(a.cli_dir).resolve())
    items = json.loads(EVAL_SET.read_text(encoding="utf-8"))
    if a.limit:
        items = items[:a.limit]
    out = Path(a.out) if a.out else WORKSPACE / "trigger" / f"trigger-{time.strftime('%Y%m%dT%H%M%S')}.json"
    results: dict[int, list[tuple[bool | None, list[str]]]] = {i: [] for i in range(len(items))}
    lock = threading.Lock()
    sem = threading.Semaphore(a.parallel)

    def work(i: int, item: dict) -> None:
        with sem:
            try:
                r = one(item["query"], item.get("project", "with-feature"), installer, a.model, a.timeout)
            except Exception as e:  # 一条炸了不算触发也不算未触发（下面按 None 剔除）
                r = (None, [repr(e)])
            with lock:
                results[i].append(r)
                print(f"[{i}] 应触发={item['should_trigger']} 实触发={r[0]} tools={r[1]} :: {item['query'][:50]}",
                      flush=True)

    threads = [threading.Thread(target=work, args=(i, item))
               for i, item in enumerate(items) for _ in range(a.runs)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    rows, passed_n = [], 0
    for i, item in enumerate(items):
        got = [r for r in results[i] if r[0] is not None]
        rate = sum(1 for r in got if r[0]) / len(got) if got else None
        passed = rate is not None and (rate >= 0.5) == item["should_trigger"]
        passed_n += bool(passed)
        rows.append({"query": item["query"], "project": item.get("project", "with-feature"),
                     "should_trigger": item["should_trigger"], "trigger_rate": rate, "passed": passed,
                     "runs_ok": len(got), "tools": [r[1] for r in results[i]]})
    summary = {"total": len(items), "passed": passed_n, "runs_per_query": a.runs, "model": a.model,
               "installed_with": str(installer)}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"summary": summary, "results": rows}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"SUMMARY {summary} → {out}", flush=True)


if __name__ == "__main__":
    main()
