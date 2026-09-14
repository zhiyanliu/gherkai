#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 fixture 物化成一个仓库外的「使用方项目」舞台，供 skill 评测的两臂（with-skill / baseline）用。

做什么（设计见 docs/adr/0043-agent-skill-for-driving-gherkai.md 决策七）：
1. 把 `fixtures/<case>/` 拷到仓库外的一次性目录（缺省 `$TMPDIR/gherkai-eval-<case>-<随机>/`）；
2. 把文本文件里的占位符 `{{FIXTURE_ROOT}}` 替换成舞台的绝对路径——fixture 入库时不得含产出机器的绝对路径，
   `run_meta.json` 的 steps_dir、`jobs/*.json` 的 report_refs[].ref、evidence.json 的截图地址都以占位符存；
3. 生成 `bin/gherkai` shim：unset AWS_PROFILE / AWS_REGION / AWS_DEFAULT_REGION、把 AWS_CONFIG_FILE 与
   AWS_SHARED_CREDENTIALS_FILE 指向舞台里的空文件、注入 GHERKAI_WORKER_MIDSCENE_CMD（仓库内已构建的 dist/bin.mjs，
   两臂对称、零 npm 零网络），再 exec 仓库 `.venv/bin/gherkai`。只在启动器父进程 unset 无效——宿主用户级设置会给新会话
   重新注入 env，所以放在 shim 这一层；
4. 前置断言：舞台及其上溯路径、用户级目录下没有已装的 gherkai skill（dogfood 安装态与评测互斥）；
5. 物化后完整性断言（只挡物化真会造成的缺口）：对每个 run 跑 `explain --json`——有记录的 step 其 evidence_missing
   不得为 unreadable / unsupported_schema；至少一条 step 拿到非空 evidence；每个非 null 的 file:// 截图地址文件存在且非空。

用法：
  python skills/gherkai-evals/materialize.py wiki-search            # 物化并打印舞台目录
  python skills/gherkai-evals/materialize.py wiki-search --stage /tmp/x --keep
  python skills/gherkai-evals/materialize.py --snapshot <录好的项目目录> wiki-search
                                                                    # 反向：把真跑过的项目快照进 fixtures/<case>
不联网、不装东西、不碰 AWS。

`--snapshot` 是物化的逆操作（录 fixture 用）：拷贝 features/ steps/ reports/，把项目目录的绝对路径（含 file:// 形态）换成
占位符，删掉 worker.log / reconcile.log（含绝对路径、对评测无用），把截图裁成极小的合法 PNG（评测只要求文件存在且非空），
最后扫一遍不得再有绝对路径。录制约束：录时 feature 必须用**相对路径**调用（scope_id / scenario_id 与 jobs/ 文件名里都带
它，绝对路径进了文件名占位符救不了），且 cwd = 项目目录、`--report-dir reports`。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
FIXTURES = HERE / "fixtures"
PLACEHOLDER = "{{FIXTURE_ROOT}}"
TEXT_SUFFIXES = {".json", ".html", ".feature", ".py", ".mts", ".mjs", ".md", ".txt", ".example"}
SKILL_DIRS = (Path(".claude/skills/gherkai"), Path(".agents/skills/gherkai"))


def fail(msg: str) -> None:
    print(f"materialize: {msg}", file=sys.stderr)
    sys.exit(2)


def assert_no_installed_skill(stage: Path) -> None:
    probes: list[Path] = []
    for base in [stage, *stage.parents]:
        probes += [base / d for d in SKILL_DIRS]
    home = Path.home()
    probes += [home / d for d in SKILL_DIRS]
    hits = [p for p in probes if p.exists()]
    if hits:
        fail("评测要求舞台上溯路径与用户级目录里没有已装的 gherkai skill，先移走：\n  " + "\n  ".join(map(str, hits)))


def copy_fixture(case: str, stage: Path) -> None:
    src = FIXTURES / case
    if not src.is_dir():
        fail(f"fixture 不存在：{src}")
    shutil.copytree(src, stage, dirs_exist_ok=True)


def substitute_placeholders(stage: Path) -> int:
    n = 0
    for p in stage.rglob("*"):
        if not p.is_file() or p.suffix not in TEXT_SUFFIXES:
            continue
        text = p.read_text(encoding="utf-8")
        if PLACEHOLDER in text:
            p.write_text(text.replace(PLACEHOLDER, str(stage)), encoding="utf-8")
            n += 1
    return n


def write_shim(stage: Path) -> Path:
    venv_cli = REPO / ".venv" / "bin" / "gherkai"
    if not venv_cli.exists():
        fail(f"仓库 .venv 里没有 gherkai：{venv_cli}（先在仓库根 uv sync）")
    midscene_bin = REPO / "engines" / "midscene" / "dist" / "bin.mjs"
    aws_dir = stage / ".eval-aws"
    aws_dir.mkdir(exist_ok=True)
    (aws_dir / "config").write_text("", encoding="utf-8")
    (aws_dir / "credentials").write_text("", encoding="utf-8")
    bin_dir = stage / "bin"
    bin_dir.mkdir(exist_ok=True)
    shim = bin_dir / "gherkai"
    lines = [
        "#!/bin/sh",
        "# 评测 shim：让两臂在同一个受控环境里调用仓库 .venv 的 gherkai（见 materialize.py 头注释）。",
        "unset AWS_PROFILE AWS_REGION AWS_DEFAULT_REGION",
        f'export AWS_CONFIG_FILE="{aws_dir / "config"}"',
        f'export AWS_SHARED_CREDENTIALS_FILE="{aws_dir / "credentials"}"',
    ]
    if midscene_bin.exists():
        lines.append(f'export GHERKAI_WORKER_MIDSCENE_CMD="node {midscene_bin}"')
    else:
        print(f"materialize: 警告：{midscene_bin} 不存在，midscene 引擎在舞台里不可用（engines/midscene 下 npm run build 可补）",
              file=sys.stderr)
    lines.append(f'exec "{venv_cli}" "$@"')
    shim.write_text("\n".join(lines) + "\n", encoding="utf-8")
    shim.chmod(shim.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return shim


def integrity_check(stage: Path, shim: Path) -> None:
    reports = stage / "reports"
    if not reports.is_dir():
        return
    for run_dir in sorted(p for p in reports.iterdir() if p.is_dir()):
        proc = subprocess.run([str(shim), "explain", run_dir.name, "--json", "--report-dir", str(reports)],
                              cwd=stage, capture_output=True, text=True)
        if proc.returncode != 0:
            fail(f"explain --json 退 {proc.returncode}（run {run_dir.name}）：{proc.stderr.strip()[:400]}")
        data = json.loads(proc.stdout)
        got_evidence = False
        for scope in data.get("scopes", []):
            for sc in scope.get("scenarios", []):
                for step in sc.get("steps", []):
                    if step.get("record_missing"):
                        continue
                    em = step.get("evidence_missing")
                    if em in ("unreadable", "unsupported_schema"):
                        fail(f"run {run_dir.name} scope {scope.get('scope_id')} step {step.get('index')}: "
                             f"evidence_missing={em}（占位符没替对 / 路径错 / 字节被吞）")
                    ev = step.get("evidence")
                    if ev:
                        got_evidence = True
                        for act in ev.get("acts", []):
                            for fr in act.get("frames", []):
                                shot = fr.get("screenshot")
                                if shot and shot.startswith("file://"):
                                    f = Path(shot[len("file://"):])
                                    if not f.is_file() or f.stat().st_size == 0:
                                        fail(f"截图缺失或为空：{f}")
        if not got_evidence:
            fail(f"run {run_dir.name} 没有任何一条 step 拿到非空 evidence")


TINY_PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000d49444154789c6360000002000105"
    "1b0e2d0e0000000049454e44ae426082"
)
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
DROP_NAMES = {"worker.log", "reconcile.log"}
# 引擎 SDK 的原生产物（每次 act 一份 HTML + trajectory JSON，动辄几 MB、内嵌截图）：skill 教 agent 不去解析它们，
# 评测只靠 evidence.json + 截图 + session_summary.json，故不入库。判定明细里指向它们的 ref 保留原样（只是指向不存在的文件）。
DROP_GLOBS = ("act_*.html", "act_*_trajectory.json")
# 漏扫判据 = 已知机器根（与 cli/tests/test_skill.py 的 ABSOLUTE_PATH 同一组；URL 路径与机器路径只有根目录名能分）。
MACHINE_ROOT = re.compile(r"(?:file://)?/(?:Users|home|private|var|tmp|opt|Volumes|root|mnt|srv|app|workspace|work|data|etc|usr|nix|run)/")


def snapshot(project: Path, case: str) -> None:
    """把一个真跑过的项目目录快照进 fixtures/<case>（物化的逆操作，见模块头注释）。"""
    # 录制机上的路径字面量可能与本机解析后的不同（macOS 的 /tmp → /private/tmp），两种写法都替。
    roots = {str(project), str(project.resolve())}
    project = project.resolve()
    if not project.is_dir():
        fail(f"项目目录不存在：{project}")
    dst = FIXTURES / case
    if dst.exists():
        shutil.rmtree(dst)
    for sub in ("features", "steps", "reports"):
        if (project / sub).is_dir():
            shutil.copytree(project / sub, dst / sub, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    dropped = images = replaced = 0
    for p in list(dst.rglob("*")):
        if not p.is_file():
            continue
        if p.name in DROP_NAMES or p.suffix == ".log" or any(p.match(g) for g in DROP_GLOBS):
            p.unlink(); dropped += 1
            continue
        if p.suffix.lower() in IMAGE_SUFFIXES:
            p.write_bytes(TINY_PNG); images += 1
            continue
        if p.suffix in TEXT_SUFFIXES:
            text = p.read_text(encoding="utf-8")
            new = text
            for r in sorted(roots, key=len, reverse=True):
                new = new.replace(r, PLACEHOLDER)
            if new != text:
                p.write_text(new, encoding="utf-8"); replaced += 1
    leaks = []
    for p in dst.rglob("*"):
        if p.is_file() and p.suffix in TEXT_SUFFIXES:
            for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
                if MACHINE_ROOT.search(line) and PLACEHOLDER not in line:
                    leaks.append(f"{p.relative_to(dst)}:{i}")
    if leaks:
        fail("快照里仍有绝对路径（占位符没覆盖到）：\n  " + "\n  ".join(leaks[:20]))
    print(f"快照 → {dst}：删 {dropped} 个日志、裁 {images} 张截图、占位符替换 {replaced} 个文件", file=sys.stderr)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("case", help="fixtures/ 下的用例目录名")
    ap.add_argument("--snapshot", metavar="PROJECT_DIR", help="反向：把真跑过的项目目录快照进 fixtures/<case>，不物化")
    ap.add_argument("--stage", help="舞台目录（缺省在 $TMPDIR 下新建；必须在仓库之外）")
    ap.add_argument("--keep", action="store_true", help="舞台已存在时不清空（缺省先删再拷）")
    ap.add_argument("--no-check", action="store_true", help="跳过物化后的完整性断言")
    args = ap.parse_args()

    if args.snapshot:
        snapshot(Path(args.snapshot), args.case)
        return

    stage = Path(args.stage).resolve() if args.stage else Path(tempfile.mkdtemp(prefix=f"gherkai-eval-{args.case}-"))
    if REPO in stage.parents or stage == REPO:
        fail(f"舞台必须在仓库之外：{stage}")
    if stage.exists() and not args.keep:
        shutil.rmtree(stage)
    stage.mkdir(parents=True, exist_ok=True)

    assert_no_installed_skill(stage)
    copy_fixture(args.case, stage)
    n = substitute_placeholders(stage)
    shim = write_shim(stage)
    if not args.no_check:
        integrity_check(stage, shim)
    print(f"舞台：{stage}", file=sys.stderr)
    print(f"占位符替换：{n} 个文件；CLI：{shim}（前置 PATH：export PATH=\"{stage / 'bin'}:$PATH\"）", file=sys.stderr)
    print(stage)


if __name__ == "__main__":
    main()
