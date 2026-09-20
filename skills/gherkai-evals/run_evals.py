#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""运行 skill 的行为评测：每条 eval × 每臂（with_skill / without_skill）× --runs 次，各自一个独立舞台与
独立 `claude -p` 进程。

设计见 docs/adr/0043-agent-skill-for-driving-gherkai.md 决策七。要点：
- **隔离**：舞台由 materialize.py 物化到仓库外，cwd = 舞台、PATH 前置舞台 `bin/`；舞台里的 CLI 来自装进仓库外
  目录的 wheel，任何路径都不指仓库（`--prepare-cli` 那步保证），两臂只差「有没有拿到 skill」一个变量。
- **with-skill 臂只给中立路径**：每次运行把 skill 拷进一个随机命名的临时目录、提示里只给这个路径，结束后即删——给仓库路径
  等于邀请它顺着仓库读原始教材；放在 `<cli-dir>/skill/` 也不行（ADR 0043 验证节第三轮 eval 3 的 baseline 顺着 shim 指向的 cli-dir
  `grep` 到了它、读了 references/engines.md），必须是 baseline 无从枚举到的位置。
- **过程断言只认工具流水**：每次运行都存 `tool_calls.json`（用了哪些命令、有没有实际执行、有没有装东西），答案自述不算证据；
  `timing.json` 另记三个每轮必报的污染 / 效率指标（repo_touches / network_calls / skill_copy_touches）。
- **一次运行多遍**：跨 run 的方差是判「两臂差值是不是噪声」的前提，缺省 3 次。

结果布局（评分者再往同目录写 grading.json，聚合脚本按这棵树读）：
  <repo>/skills/gherkai-workspace/iteration-<N>/
    eval-<id>-<slug>/eval_metadata.json
    eval-<id>-<slug>/<arm>/run-<K>/{transcript.json, tool_calls.json, timing.json, outputs/}

前置：`python skills/gherkai-evals/materialize.py --prepare-cli`（一次性，几分钟）。

用法：
  python skills/gherkai-evals/run_evals.py --iteration 3 --runs 3
  python skills/gherkai-evals/run_evals.py --iteration 3 --ids 5 --arms with_skill --runs 1
  python skills/gherkai-evals/run_evals.py --iteration 3 --include-opt-in --ids 6   # 实际运行 run / submit，要真 AWS
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
EVALS = HERE / "evals.json"
MATERIALIZE = HERE / "materialize.py"
WORKSPACE = REPO / "skills" / "gherkai-workspace"
# skill 的唯一真源（与 wheel 内那份同树）；只用来拷进临时目录，这个路径绝不进提示。
SKILL_SRC = REPO / "cli" / "gherkai_cli" / "skills" / "gherkai"
DEFAULT_CLI_DIR = Path("/tmp/gherkai-eval-cli")
STAGE_ROOT = Path("/tmp/gherkai-eval-stages")
DEFAULT_FIXTURE = "wiki-search"
# 只认这两个臂名：写错了会静默当 baseline 运行（提示里不给 skill），白费一整轮还看不出来。
KNOWN_ARMS = ("with_skill", "without_skill")
# 本会话模型即评测模型（env 覆写便于换模型比对）。
DEFAULT_MODEL = os.environ.get("GHERKAI_EVAL_MODEL") or "global.anthropic.claude-fable-5-1[1m]"

COMMON_SUFFIX = ("\n\n（这个目录就是项目本身。不要安装任何东西——npm i / uv tool install / pip install 一律不要执行。"
                 "做完用中文给我一段汇报。）")
# 只剥「嵌套会话」相关变量；Bedrock 鉴权 / 模型映射（CLAUDE_CODE_USE_BEDROCK、AWS_BEARER_TOKEN_BEDROCK、
# ANTHROPIC_*）必须保留——`--setting-sources project` 已把用户级 settings 的 env 块排除，全靠进程 env 提供。
STRIP_ENV = {"CLAUDECODE", "CLAUDE_CODE_ENTRYPOINT", "CLAUDE_CODE_SESSION_ID", "CLAUDE_CODE_CHILD_SESSION",
             "CLAUDE_PID", "CLAUDE_CODE_MESSAGING_SOCKET", "CLAUDE_CODE_MESSAGING_TOKEN",
             "CLAUDE_CODE_SUBAGENT_MODEL", "CLAUDE_EFFORT", "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS",
             "CLAUDE_CODE_ENABLE_AUTO_MODE", "CLAUDE_CODE_DISABLE_AGENT_VIEW", "CLAUDE_CODE_EXECPATH"}
# 舞台里被测 agent 可写的东西全收进 outputs/；这几支是评测脚手架自己铺的，不算它的产出。
# （features/ steps/ 单独整目录拷，见 collect_outputs。）
SKIP_TOP = {"reports", "bin", ".eval-aws", "features", "steps"}
# 网络调用判据：WebFetch / WebSearch 已被 --disallowedTools 挡掉，剩下的口子是 Bash 里自己发请求。
# 首轮 baseline 用 5 次 curl / 维基 API 拿回了 eval 的事实基准，结果既不可比也不可重放，故列进必报指标。
NETWORK_RE = re.compile(r"\b(?:curl|wget)\b|urllib\.request|requests\.get|http\.client|\bnc\s+-", re.I)


def fail(msg: str) -> None:
    print(f"run_evals: {msg}", file=sys.stderr)
    sys.exit(2)


def load_evals(ids: str, include_opt_in: bool) -> list[dict]:
    data = json.loads(EVALS.read_text(encoding="utf-8"))["evals"]
    wanted = [int(x) for x in ids.replace(" ", "").split(",") if x]
    picked = []
    for ev in data:
        if wanted:
            if ev["id"] not in wanted:
                continue
        elif ev.get("opt_in") and not include_opt_in:
            continue
        if ev.get("opt_in") and not include_opt_in:
            fail(f"eval {ev['id']} 标了 opt_in（实际运行 run / submit、要真 AWS），要运行就显式给 --include-opt-in")
        if not ev.get("slug"):
            fail(f"eval {ev['id']} 没有 slug 字段（结果目录名由它派生），先在 evals.json 里补一条")
        picked.append(ev)
    missing = sorted(set(wanted) - {ev["id"] for ev in picked})
    if missing:
        fail(f"evals.json 里没有这些 id：{missing}")
    return picked


def parse_events(raw: str) -> list[dict]:
    events = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events


def tool_calls_of(events: list[dict]) -> list[dict]:
    calls = []
    for e in events:
        if e.get("type") != "assistant":
            continue
        for c in e.get("message", {}).get("content", []):
            if c.get("type") == "tool_use":
                calls.append({"tool": c.get("name"), "input": c.get("input")})
    return calls


def _purge_session_dir(stage: Path) -> None:
    """删掉 Claude Code 为这个舞台路径建的会话目录（含 memory/），保证每次运行从零开始。"""
    key = re.sub(r"[^A-Za-z0-9]", "-", str(stage.resolve() if stage.exists() else Path("/private") / stage.relative_to("/")
                                             if str(stage).startswith("/tmp/") else stage))
    for cand in {key, re.sub(r"[^A-Za-z0-9]", "-", str(stage))}:
        d = Path.home() / ".claude" / "projects" / cand
        if d.is_dir():
            shutil.rmtree(d, ignore_errors=True)


def pollution_metrics(calls: list[dict], skill_dirs: list[Path]) -> dict:
    """每轮必报的三个指标：污染（触仓库 / 触 skill 副本）与不可重放（联网）。事后 grep 才知道 = 太晚。
    skill_dirs = 本次运行的临时 skill 目录 + 旧版 `<cli-dir>/skill/`（若还在）；with-skill 臂天然 ≥1，baseline 臂 >0 即污染。"""
    repo_touches = network_calls = skill_copy_touches = 0
    for c in calls:
        blob = json.dumps(c.get("input"), ensure_ascii=False)
        if str(REPO) in blob:
            repo_touches += 1
        if any(str(d) in blob for d in skill_dirs):
            skill_copy_touches += 1
        if c.get("tool") in ("WebFetch", "WebSearch"):
            network_calls += 1
        elif c.get("tool") == "Bash" and NETWORK_RE.search(str((c.get("input") or {}).get("command", ""))):
            network_calls += 1
    return {"repo_touches": repo_touches, "network_calls": network_calls,
            "skill_copy_touches": skill_copy_touches}


def collect_outputs(stage: Path, out_dir: Path, final_answer: str) -> None:
    outputs = out_dir / "outputs"
    outputs.mkdir(parents=True, exist_ok=True)
    (outputs / "final_answer.md").write_text(final_answer, encoding="utf-8")
    for sub in ("features", "steps"):
        if (stage / sub).is_dir():
            shutil.copytree(stage / sub, outputs / sub, dirs_exist_ok=True,
                            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    # 递归收其余新建 / 改动的文件：首轮 baseline 把 CI 脚本写在 ci/ 子目录里，只拷顶层就漏收了它的主要产出。
    for p in stage.rglob("*"):
        rel = p.relative_to(stage)
        if not p.is_file() or p.is_symlink() or rel.parts[0] in SKIP_TOP:
            continue
        if "__pycache__" in rel.parts or "node_modules" in rel.parts:
            continue
        dst = outputs / "stage-extra" / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, dst)
    listing = subprocess.run(["find", ".", "-type", "f", "-not", "-path", "./reports/*",
                              "-not", "-path", "./bin/*", "-not", "-path", "./.eval-aws/*"],
                             cwd=stage, capture_output=True, text=True).stdout
    (outputs / "stage_files.txt").write_text(listing, encoding="utf-8")


def materialize(fixture: str, stage: Path, cli_dir: Path) -> Path:
    proc = subprocess.run([sys.executable, str(MATERIALIZE), fixture,
                           "--stage", str(stage), "--cli-dir", str(cli_dir)],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"materialize {fixture} 退 {proc.returncode}：{proc.stderr.strip()[-600:]}")
    return Path(proc.stdout.strip())


def run_one(ev: dict, arm: str, run_no: int, it_dir: Path, cli_dir: Path, model: str, timeout: int) -> None:
    eid, slug = ev["id"], ev["slug"]
    out_dir = it_dir / f"eval-{eid}-{slug}" / arm / f"run-{run_no}"
    out_dir.mkdir(parents=True, exist_ok=True)
    # 舞台路径带随机后缀：Claude Code 按 cwd 给每个项目一个 ~/.claude/projects/<路径>/memory/，同名路径重新运行会把上一次
    # 的记忆（含上一次的结论）灌进新会话——ADR 0043 验证节第三轮的 baseline 复用同名路径就这样被自己的旧 run 喂了答案；运行前后再各清一次兜底
    stage = STAGE_ROOT / f"{it_dir.name}-{eid}-{arm}-run{run_no}-{os.urandom(3).hex()}"
    _purge_session_dir(stage)
    stage = materialize(ev.get("fixture") or DEFAULT_FIXTURE, stage, cli_dir)
    # skill 副本只给 with-skill 臂建，放 ~/.cache 下随机命名的目录（不在 cli-dir、不在舞台、也不在 $TMPDIR——
    # baseline 会 `ls $TMPDIR`，ADR 0043 验证节第三轮 eval 9 的一次 baseline 就这样翻到了并发 with-skill 运行的副本），只有提示知道它在哪
    skill_root = Path.home() / ".cache" / "gherkai-eval-skill"
    skill_root.mkdir(parents=True, exist_ok=True)
    skill_tmp = Path(tempfile.mkdtemp(prefix="s-", dir=skill_root))
    skill_dir = skill_tmp / "gherkai"
    prompt = ev["prompt"] + COMMON_SUFFIX
    if arm == "with_skill":
        shutil.copytree(SKILL_SRC, skill_dir, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        prompt += f"\n\n（先读这份 skill 并照它做：{skill_dir / 'SKILL.md'}）"
    env = {k: v for k, v in os.environ.items() if k not in STRIP_ENV}
    env["PATH"] = f"{stage / 'bin'}:" + env.get("PATH", "")
    # `--setting-sources project` 排除用户级设置（ultracode / 用户级 skills / 个人偏好）；禁 Workflow/Agent/Task：
    # `-p` 会在后台子代理未完时就返回，首轮 baseline 三条 eval 的答案因此只剩「等后台 workflow」、两臂不可比。
    # 禁 WebFetch/WebSearch：活网内容会把 eval 的事实基准喂给某一臂，也让结果不可重放。
    cmd = ["claude", "-p", prompt, "--output-format", "stream-json", "--verbose", "--no-session-persistence",
           "--setting-sources", "project",
           "--allowedTools", "Bash", "Read", "Write", "Edit", "Glob", "Grep", "LS",
           "--disallowedTools", "Workflow", "Agent", "Task", "TodoWrite", "WebFetch", "WebSearch"]
    if model:
        cmd += ["--model", model]
    t0 = time.time()
    try:
        proc = subprocess.run(cmd, cwd=stage, env=env, capture_output=True, text=True,
                              timeout=timeout, stdin=subprocess.DEVNULL)
        raw = proc.stdout
    except subprocess.TimeoutExpired as e:
        tail = e.stdout or b""
        raw = json.dumps({"is_error": True, "result": f"TIMEOUT after {timeout}s",
                          "stdout": (tail.decode("utf-8", "ignore") if isinstance(tail, bytes) else str(tail))[-2000:]})
    dur = time.time() - t0
    events = parse_events(raw)
    data = next((e for e in reversed(events) if e.get("type") == "result"), None) \
        or {"is_error": True, "result": raw[-4000:]}
    (out_dir / "transcript.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    calls = tool_calls_of(events)
    (out_dir / "tool_calls.json").write_text(json.dumps(calls, ensure_ascii=False, indent=2), encoding="utf-8")
    usage = data.get("usage") or {}
    total_tokens = sum(int(usage.get(k, 0) or 0) for k in
                       ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens"))
    metrics = pollution_metrics(calls, [skill_tmp, skill_root, cli_dir / "skill"])
    metrics["memory_reads"] = sum(1 for c in calls if "/.claude/projects/" in json.dumps(c.get("input"), ensure_ascii=False))
    shutil.rmtree(skill_tmp, ignore_errors=True)
    _purge_session_dir(stage)
    (out_dir / "timing.json").write_text(json.dumps({
        "total_tokens": total_tokens, "duration_ms": int(dur * 1000), "total_duration_seconds": round(dur, 1),
        "num_turns": data.get("num_turns"), "cost_usd": data.get("total_cost_usd"),
        "tool_calls": len(calls), **metrics,
    }, indent=2), encoding="utf-8")
    collect_outputs(stage, out_dir, str(data.get("result", "")))
    print(f"[done] eval {eid} {arm} run-{run_no}: {dur:.0f}s calls={len(calls)} tokens={total_tokens} "
          f"repo={metrics['repo_touches']} net={metrics['network_calls']} err={data.get('is_error')}", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--iteration", type=int, default=1, help="第几轮（结果落 iteration-<N>/）")
    ap.add_argument("--ids", default="", help="逗号分隔的 eval id；缺省 = 全部非 opt_in")
    ap.add_argument("--arms", default=",".join(KNOWN_ARMS), help=f"逗号分隔的臂名（{list(KNOWN_ARMS)}）")
    ap.add_argument("--runs", type=int, default=3, help="每个 (eval, 臂) 运行几次（跨 run 方差是判噪声的前提）")
    ap.add_argument("--parallel", type=int, default=10, help="并发的 claude -p 进程数上限")
    ap.add_argument("--timeout", type=int, default=1500, help="单次 claude -p 的墙钟上限（秒）")
    ap.add_argument("--model", default=DEFAULT_MODEL, help=f"两臂固定同一个模型（缺省 {DEFAULT_MODEL}）")
    ap.add_argument("--cli-dir", default=str(DEFAULT_CLI_DIR),
                    help=f"已备好的仓库外 CLI 目录（缺省 {DEFAULT_CLI_DIR}，见 materialize.py --prepare-cli）")
    ap.add_argument("--include-opt-in", action="store_true", help="连 opt_in 的 eval 一起运行（实际运行 run / submit、要真 AWS）")
    a = ap.parse_args()

    cli_dir = Path(a.cli_dir).resolve()
    if not (cli_dir / "venv" / "bin" / "gherkai").is_file():
        fail(f"{cli_dir} 没备好——先运行：python skills/gherkai-evals/materialize.py --prepare-cli {cli_dir}")
    if not (SKILL_SRC / "SKILL.md").is_file():
        fail(f"仓库里没有 skill：{SKILL_SRC}")
    if not shutil.which("claude"):
        fail("PATH 里没有 claude（两臂都靠 `claude -p` 运行）")
    evals = load_evals(a.ids, a.include_opt_in)
    arms = [x for x in a.arms.replace(" ", "").split(",") if x]
    unknown = [x for x in arms if x not in KNOWN_ARMS]
    if unknown:
        fail(f"不认识的臂名 {unknown}（只有 {list(KNOWN_ARMS)}）")
    it_dir = WORKSPACE / f"iteration-{a.iteration}"
    it_dir.mkdir(parents=True, exist_ok=True)
    for ev in evals:
        d = it_dir / f"eval-{ev['id']}-{ev['slug']}"
        d.mkdir(parents=True, exist_ok=True)
        (d / "eval_metadata.json").write_text(json.dumps(
            {"eval_id": ev["id"], "eval_name": ev["slug"], "prompt": ev["prompt"],
             "assertions": ev["expectations"]}, ensure_ascii=False, indent=2), encoding="utf-8")
    jobs = [(ev, arm, k) for ev in evals for arm in arms for k in range(1, a.runs + 1)]
    print(f"iteration-{a.iteration}：{len(evals)} 条 eval × {len(arms)} 臂 × {a.runs} 次 = {len(jobs)} 个进程"
          f"（并发 {a.parallel}，model {a.model}）", flush=True)
    sem = threading.Semaphore(a.parallel)
    threads = []

    def worker(ev: dict, arm: str, k: int) -> None:
        with sem:
            try:
                run_one(ev, arm, k, it_dir, cli_dir, a.model, a.timeout)
            except Exception as e:  # 一个格子炸了不能带走整轮
                print(f"[fail] eval {ev['id']} {arm} run-{k}: {e!r}", flush=True)

    for ev, arm, k in jobs:
        t = threading.Thread(target=worker, args=(ev, arm, k))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()
    print(f"all done {it_dir}", flush=True)


if __name__ == "__main__":
    main()
