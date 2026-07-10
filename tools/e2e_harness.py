#!/usr/bin/env python
"""worker 端到端真跑验证 harness（ADR 0024 worker↔core 协议 / 终止契约 / 0029 act 边界抢传；跨引擎）。

**这是 opt-in 手动端到端验证脚本，不进 pytest 默认套件**——它真 spawn worker、真喂 job（stdin）、真收
事件流（EVENTS_FD）、真开 AgentCore 会话、真写 S3（**烧真 AWS 钱、需网络/凭证、单次 ~1-2min**）。它补的是
单测的 mock 覆盖不到、只能真跑的那层（对齐 CLAUDE.md「绿≠对」）：真 greenlet / 真会话 / 真进程退出码 /
真事件流字节 / 真中断丢失量。纯逻辑回归仍由各引擎单测覆盖（Nova worker/test_*.py、core tests/ 等）。

**中断只是能力之一**（--interrupt）：--interrupt none 的 baseline 可验「事件流端到端正常 + 三通道分离 +
零行为变化」（如 worker I/O 边缘重构后的回归）；--interrupt <时机> 才验中断韧性。

忠实复现 SubprocessEngine adapter 的 spawn 环境（自建 events pipe + EVENTS_FD、注入产物落点 env +
S3 上传 env），起真 worker 跑一个 scope，按事件时机外部 SIGTERM 命中中断点，中断后快照：
  - 盘上有什么（NOVA_LOGS_DIR / MIDSCENE_RUN_DIR 递归）
  - S3 有什么（list prefix）
  - 差集（盘有 S3 无）= **Fargate 容器盘销毁时会丢的**（subprocess 下留本地盘、非真丢）
并测 grace 秒数（SIGTERM→worker 退出实测耗时）、检测 worker 是否 hung（SIGKILL 兜底）。

用法（需 AWS 凭证 + region us-east-1）：
  # 从仓库根跑：
  HARNESS_S3_BUCKET=<你的可写桶> PYTHONPATH=core core/.venv/bin/python tools/e2e_harness.py \\
      --engine novaact --feature wikipedia_assertions --interrupt scope_end --run-id verify-1
  # --interrupt: connect(建连中) / act(act 跑一半) / between(step 边界) / scenario(第一个 scenario 完成后、
  #              下一 scenario 运行中——验 scenario 边界 log 抢传，需多 scenario feature) / scope_end(flush 前) /
  #              none(baseline 不中断)
  # 桶经环境变量 HARNESS_S3_BUCKET 传（勿硬编码；跑完自行清理桶内 <prefix>）。

历史：中断丢失预演、Nova 中断模型改造验证、抢传验证都用它（历次实测见 docs/journey/0001）。
"""
from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "core"))

from core.scope import plan, PlanConfig, FeatureSource  # noqa: E402
from core.wire import job_to_line  # noqa: E402

BUCKET = os.environ.get("HARNESS_S3_BUCKET")  # 可写桶，经 env 传（勿硬编码账号相关值）
_TMP = Path(os.environ.get("CLAUDE_JOB_DIR", "/tmp")) / "harness-runs"


def build_job(feature: str, engine: str, votes: int):
    """复用真实 plan 链路生成 job（不手搓 JSON，防 schema 漂移）。

    取**匹配 `--engine` 的第一个 job** 作靶子（回退 jobs[0]）——否则混引擎 feature（如 engine_routing 用
    @engine: tag 把 scenario 分到不同引擎）下 jobs[0] 可能是另一引擎的 job，会拿它喂错引擎的 worker（worker
    不看 engine tag、照跑，但语义错乱）。单引擎 feature 下 jobs 全同引擎、此选择 = jobs[0]，行为不变。
    """
    txt = (REPO / "features" / f"{feature}.feature").read_text(encoding="utf-8")
    fs = FeatureSource(uri=f"features/{feature}.feature", text=txt)
    jobs = plan([fs], PlanConfig(default_engine=engine, default_assertion_votes=votes))
    return next((j for j in jobs if j.engine == engine), jobs[0])


def worker_cmd(engine: str) -> tuple[list[str], str]:
    if engine == "novaact":
        d = REPO / "engines" / "novaact"
        return [str(d / ".venv" / "bin" / "python"), str(d / "worker" / "run_scope.py")], str(d)
    d = REPO / "engines" / "midscene"
    return ["node", "--import", "tsx", str(d / "worker" / "run-scope.ts")], str(d)


def snapshot_disk(run_dir: Path) -> list[tuple[str, int]]:
    out = []
    if run_dir.exists():
        for f in sorted(run_dir.rglob("*")):
            if f.is_file():
                out.append((str(f.relative_to(run_dir)), f.stat().st_size))
    return out


def snapshot_s3(prefix: str) -> list[tuple[str, int]]:
    import boto3
    s3 = boto3.client("s3", region_name="us-east-1")
    out, token = [], None
    while True:
        kw = {"Bucket": BUCKET, "Prefix": prefix}
        if token:
            kw["ContinuationToken"] = token
        resp = s3.list_objects_v2(**kw)
        for o in resp.get("Contents", []):
            rel = o["Key"][len(prefix):] if o["Key"].startswith(prefix) else o["Key"]
            out.append((rel, o["Size"]))
        if resp.get("IsTruncated"):
            token = resp["NextContinuationToken"]
        else:
            break
    return sorted(out)


def run(engine: str, feature: str, votes: int, interrupt: str, run_id: str, grace_cap: float):
    if not BUCKET:
        sys.exit("错误：需经环境变量 HARNESS_S3_BUCKET 提供可写 S3 桶")
    job = build_job(feature, engine, votes)
    cmd, cwd = worker_cmd(engine)

    run_dir = _TMP / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    if engine == "novaact":
        artifact_dir, local_key = run_dir / "nova-trajectories", "NOVA_LOGS_DIR"
    else:
        artifact_dir, local_key = run_dir / "midscene-run", "MIDSCENE_RUN_DIR"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    prefix = f"harness/{run_id}/"

    events_r, events_w = os.pipe()
    env = {**os.environ, local_key: str(artifact_dir),
           "ARTIFACT_S3_BUCKET": BUCKET, "ARTIFACT_S3_PREFIX": prefix,
           "EVENTS_FD": str(events_w), "AWS_REGION": "us-east-1"}

    print(f"[harness] engine={engine} feature={feature} interrupt={interrupt} run_id={run_id}", flush=True)
    print(f"[harness] scope={job.scope_id} scenarios={len(job.scenarios)} "
          f"steps={sum(len(s.steps) for s in job.scenarios)}", flush=True)

    proc = subprocess.Popen(cmd, cwd=cwd, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True, encoding="utf-8", bufsize=1,
                            pass_fds=(events_w,))
    os.close(events_w)
    proc.stdin.write(job_to_line(job) + "\n")
    proc.stdin.flush()
    proc.stdin.close()

    events, t0 = [], time.monotonic()
    kill_sent = {"t": None, "phase": None}
    hung = {"v": False}
    lock = threading.Lock()

    def log_pump(stream, tag):
        for line in stream:
            print(f"[worker {tag}] {line.rstrip()}", flush=True)

    threading.Thread(target=log_pump, args=(proc.stdout, "out"), daemon=True).start()
    threading.Thread(target=log_pump, args=(proc.stderr, "err"), daemon=True).start()

    def _watchdog():
        deadline = kill_sent["t"] + grace_cap
        while time.monotonic() < deadline:
            if proc.poll() is not None:
                return
            time.sleep(0.2)
        if proc.poll() is None:
            hung["v"] = True
            print(f"[harness] !!! worker HUNG > grace_cap={grace_cap}s — SIGKILL backstop", flush=True)
            proc.kill()

    def do_kill(phase):
        with lock:
            if kill_sent["t"] is not None:
                return
            kill_sent["t"], kill_sent["phase"] = time.monotonic(), phase
        print(f"[harness] >>> SIGTERM sent at phase={phase} (t={kill_sent['t']-t0:.2f}s)", flush=True)
        proc.send_signal(signal.SIGTERM)
        threading.Thread(target=_watchdog, daemon=True).start()

    if interrupt == "connect":
        threading.Timer(2.0, lambda: do_kill("connect")
                        if not any(e[1].get("type") == "scope_started" for e in events) else None).start()

    n_scen = len(job.scenarios)
    step_started = step_done = scen_done = 0
    events_fd = os.fdopen(events_r, "r", encoding="utf-8")
    for line in events_fd:
        line = line.strip()
        if not line:
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        events.append((time.monotonic() - t0, ev))
        et = ev.get("type")
        print(f"[harness] event t={time.monotonic()-t0:.2f}s {et}", flush=True)
        if et == "step_started":
            step_started += 1
            if interrupt == "act" and step_started == 1:
                threading.Timer(3.0, lambda: do_kill("act_midway")).start()
        elif et == "step_done":
            step_done += 1
            if interrupt == "between" and step_done == 1:
                do_kill("between_steps")
        elif et == "scenario_done":
            scen_done += 1
            # scenario 边界抢传验证时机（ADR 0029「第四级」，Midscene 单引擎）：第一个 scenario 完成后延迟 kill——
            # 让 scenario1 的 snapshotLogs 在其 scenario_done 后跑完（log 进 S3）、scenario2 起来，SIGTERM 落在
            # scenario2 运行中。验证：S3 应已有 scenario1 期间的 log（对照单 scenario scope_end 中断 S3 log=0）。
            # 需 jobs[0] 有 >1 scenario——即**多 scenario 归一个 @scope 的 feature**（如 concurrency_and_scope
            # 的 @scope:browse）；无 @scope tag 的 scenario 各自独立成单 scenario scope（ADR 0025）、jobs[0]=1、
            # 此时机不触发（跑成 baseline、无效样本）。选 feature 前用 core.scope.plan 确认 jobs[0] 的 scenario 数。
            if interrupt == "scenario" and scen_done == 1 and n_scen > 1:
                threading.Timer(3.0, lambda: do_kill("after_scenario1")).start()
            if interrupt == "scope_end" and scen_done == n_scen:
                do_kill("scope_end")

    proc.wait()
    grace_s = (time.monotonic() - kill_sent["t"]) if kill_sent["t"] else None

    time.sleep(1.0)  # S3 list 最终一致
    disk = snapshot_disk(artifact_dir)
    s3 = snapshot_s3(prefix)
    art_prefix = artifact_dir.name + "/"
    disk_as_s3 = {art_prefix + n for n, _ in disk}
    s3_names = {n for n, _ in s3}
    lost = sorted(disk_as_s3 - s3_names)  # 盘有 S3 无 → Fargate 会丢

    # 样本有效性（防假阳性）：`n_lost=0` 只在**确实产生过可丢的产物**时才有意义。若盘和 S3 都空——中断落得
    # 太早（产物还没写盘、S3 也没抢传），此时 n_lost=0 是「没东西可丢」而非「抢传救回了」，**不构成有效的
    # 丢失/抢传测量样本**。判据：盘或 S3 上有产物 = 有效样本（实测踩过：Midscene act 时机中断太早、盘空、
    # n_lost=0 曾被误读成抢传生效，实为无效样本——见 docs/journey/0001）。
    produced = bool(disk) or bool(s3)
    sample_valid = produced
    if not produced:
        note = "无效样本：中断过早，盘与 S3 均无产物，n_lost=0 是『没东西可丢』非『抢传救回』——换更晚的中断时机重跑"
    elif len(lost) == 0:
        note = "有效样本：产生了产物且 n_lost=0 → 抢传/上传真救回（非假阳性）"
    else:
        note = f"有效样本：丢失 {len(lost)} 文件 / {sum(sz for n, sz in disk if art_prefix + n in set(lost))} 字节"

    report = {
        "engine": engine, "feature": feature, "interrupt": interrupt, "run_id": run_id,
        "exit_code": proc.returncode, "grace_s": round(grace_s, 3) if grace_s else None,
        "hung": hung["v"], "kill_phase": kill_sent["phase"],
        "counts": {"step_started": step_started, "step_done": step_done,
                   "scenario_done": scen_done, "n_scenarios": n_scen},
        "scope_done_emitted": any(e[1].get("type") == "scope_done" for e in events),
        "disk_files": disk, "s3_files": s3,
        "lost_on_fargate": lost, "n_lost": len(lost),
        "bytes_lost": sum(sz for n, sz in disk if art_prefix + n in set(lost)),
        "sample_valid": sample_valid, "sample_note": note,
    }
    print("=== HARNESS_REPORT_JSON ===", flush=True)
    print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)
    if not sample_valid:
        print(f"[harness] ⚠️ {note}", flush=True)
    return report


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="worker 端到端真跑验证 harness（opt-in、烧真 AWS；中断只是能力之一）")
    ap.add_argument("--engine", choices=["novaact", "midscene"], default="novaact")
    ap.add_argument("--feature", default="wikipedia_assertions")
    ap.add_argument("--votes", type=int, default=1)
    ap.add_argument("--interrupt", choices=["connect", "act", "between", "scenario", "scope_end", "none"],
                    default="none")
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--grace-cap", type=float, default=30.0)
    a = ap.parse_args()
    run(a.engine, a.feature, a.votes, a.interrupt, a.run_id, a.grace_cap)
