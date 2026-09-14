#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 fixture 物化成一个仓库外的「使用方项目」舞台，供 skill 评测的两臂（with-skill / baseline）用；
并一次性把舞台要用的 CLI 装到仓库外（`--prepare-cli`）。

做什么（设计见 docs/adr/0043-agent-skill-for-driving-gherkai.md 决策七）：
0. `--prepare-cli <dir>`（一次性、要联网、几分钟）：`uv build --all-packages` 出 wheel → `uv venv` 建 `<dir>/venv`
   并装 gherkai / core / runtime / novaact worker 四个 wheel → **删掉装进去的 `gherkai_cli/skills`**（wheel 一定带
   skill，留着等于把 with-skill 臂的自变量搬进 baseline 的发现面）→（skill 副本**不放这里**：run_evals.py 每次运行拷进随机命名的临时目录、只出现在 with-skill 臂的提示里）→ 把已构建的 midscene（`dist/` + `package.json` + `node_modules/`）拷到 `<dir>/midscene/`
   （包自引用与 tsx loader 都要它，缺一个 `.mts` step 就加载不了）→ 写 `<dir>/PREPARED.json`。
   **为什么整套搬出仓库**：舞台里任何指向仓库的路径都是一条教材泄漏渠道——首轮 baseline 顺着 shim 里的
   `exec <repo>/.venv/bin/gherkai` 读到了 CLI 源码、根 README、退出码表，甚至 skill 自己的 references，148 次工具
   调用里 53 次触到仓库，两臂 delta 因此只是下界。
1. 把 `fixtures/<case>/` 拷到仓库外的一次性目录（缺省 `$TMPDIR/gherkai-eval-<case>-<随机>/`）；
2. 把文本文件里的占位符 `{{FIXTURE_ROOT}}` 替换成舞台的绝对路径——fixture 入库时不得含产出机器的绝对路径，
   `run_meta.json` 的 steps_dir、`jobs/*.json` 的 report_refs[].ref、evidence.json 的截图地址都以占位符存；
3. 生成 `bin/gherkai` shim：unset AWS_PROFILE / AWS_REGION / AWS_DEFAULT_REGION、把 AWS_CONFIG_FILE 与
   AWS_SHARED_CREDENTIALS_FILE 指向舞台里的空文件、注入 GHERKAI_WORKER_MIDSCENE_CMD（指 `<dir>/midscene/dist/bin.mjs`，
   两臂对称、零 npm 零网络），再 exec `<dir>/venv/bin/gherkai`。只在启动器父进程 unset 无效——宿主用户级设置会给新会话
   重新注入 env，所以放在 shim 这一层；
4. 前置断言：舞台及其上溯路径、用户级目录下没有已装的 gherkai skill（dogfood 安装态与评测互斥）；
5. 物化后隔离断言（恒开，`--no-check` 不关它）：舞台里没有任何文件含仓库根路径的字面量、舞台里找不到 SKILL.md
   （前者挡「顺着路径读原始教材」，后者挡「wheel 自带的 skill 混进 baseline 舞台」）；
6. 物化后完整性断言（只挡物化真会造成的缺口）：对每个 run 跑 `explain --json`——有记录的 step 其 evidence_missing
   不得为 unreadable / unsupported_schema；至少一条 step 拿到非空 evidence；每个非 null 的 file:// 截图地址文件存在且非空。

用法：
  python skills/gherkai-evals/materialize.py --prepare-cli          # 一次性备好仓库外的 CLI（缺省 /tmp/gherkai-eval-cli）
  python skills/gherkai-evals/materialize.py wiki-search            # 物化并打印舞台目录
  python skills/gherkai-evals/materialize.py wiki-search --stage /tmp/x --keep
  python skills/gherkai-evals/materialize.py --snapshot <录好的项目目录> wiki-search
                                                                    # 反向：把真跑过的项目快照进 fixtures/<case>
物化与快照不联网、不装东西、不碰 AWS；只有 `--prepare-cli` 构建并联网取依赖。

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
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
FIXTURES = HERE / "fixtures"
PLACEHOLDER = "{{FIXTURE_ROOT}}"
TEXT_SUFFIXES = {".json", ".html", ".feature", ".py", ".mts", ".mjs", ".md", ".txt", ".example"}
SKILL_DIRS = (Path(".claude/skills/gherkai"), Path(".agents/skills/gherkai"))
# 舞台用的 CLI 装在这里（仓库外）：舞台里的一切只许指向它，不许指向仓库（见模块头注释第 0 步）。
DEFAULT_CLI_DIR = Path("/tmp/gherkai-eval-cli")
SKILL_SRC = REPO / "cli" / "gherkai_cli" / "skills" / "gherkai"
MIDSCENE_SRC = REPO / "engines" / "midscene"
# 装进舞台 CLI 的发行包（deploy-aws 不装：改云端环境是部署方的事，评测的两臂都不该有这套子命令）。
PREPARE_PACKAGES = ("gherkai", "gherkai-core", "gherkai-runtime", "gherkai-worker-novaact")
# midscene 要拷的三样：dist（含 bin.mjs 与 index.mjs）、package.json（包自引用靠它的 name/exports 解析裸
# specifier）、node_modules（tsx loader 与 midscene 运行时都在里面）。约 222 MB，源侧没更新就复用。
MIDSCENE_COPY = ("dist", "package.json", "node_modules")


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
    # 本机对 fixture 跑过 plan / list-deterministic 就会在 steps/ 下留 .pyc（内嵌编译机绝对路径）——不能带进舞台
    shutil.copytree(src, stage, dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))


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


def _uv() -> str:
    found = shutil.which("uv") or str(Path.home() / ".local" / "bin" / "uv")
    if not Path(found).exists():
        fail("找不到 uv（--prepare-cli 要它构建 wheel、建 venv）")
    return found


def _run(cmd: list[str], cwd: Path | None = None) -> None:
    print("materialize: $ " + " ".join(cmd), file=sys.stderr)
    if subprocess.run(cmd, cwd=str(cwd) if cwd else None).returncode != 0:
        fail(f"命令失败：{' '.join(cmd)}")


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


def prepare_cli(cli_dir: Path) -> None:
    """一次性把舞台要用的 CLI 与 midscene 装到仓库外（见模块头注释第 0 步）。"""
    uv = _uv()
    cli_dir.mkdir(parents=True, exist_ok=True)
    dist = cli_dir / "dist"
    if dist.exists():
        shutil.rmtree(dist)  # 版本号随 git 走，旧 wheel 留着会让下面「恰好一个」的挑选变歧义
    _run([uv, "build", "--all-packages", "--out-dir", str(dist)], cwd=REPO)
    venv = cli_dir / "venv"
    if venv.exists():
        shutil.rmtree(venv)
    _run([uv, "venv", "--python", "3.13", str(venv)])
    wheels = []
    for pkg in PREPARE_PACKAGES:
        hits = sorted(dist.glob(pkg.replace("-", "_") + "-*.whl"))
        if len(hits) != 1:
            fail(f"{dist} 里 {pkg} 的 wheel 不是恰好一个：{[h.name for h in hits]}")
        wheels.append(str(hits[0]))
    # 四个 wheel 显式给全（版本一致，uv 会用给的这几份而不是去 PyPI 找同名包）；第三方依赖（boto3 / nova-act /
    # playwright）从 uv 缓存或 PyPI 取——一次性准备步骤，允许联网，与「整轮评测内环境冻结」不冲突。
    _run([uv, "pip", "install", "--python", str(venv / "bin" / "python"), *wheels])
    stripped = [p for p in venv.glob("lib/python3.*/site-packages/gherkai_cli/skills") if p.is_dir()]
    for p in stripped:
        shutil.rmtree(p)
    if not stripped:
        fail("装完没找到 gherkai_cli/skills（wheel 布局变了？）——没确认剥掉就不能开跑，baseline 会发现 skill")
    # 这个目录里**不能**有 skill 副本：baseline 顺着 shim 指向的路径 `grep` 一下就翻到（第三轮 eval 3 实测）。
    # with-skill 臂要读的那份由 run_evals.py 每次运行拷进随机命名的临时目录、只出现在它的提示里。
    stale_skill = cli_dir / "skill"
    if stale_skill.exists():
        shutil.rmtree(stale_skill)
    src_bin = MIDSCENE_SRC / "dist" / "bin.mjs"
    if not src_bin.is_file():
        fail(f"midscene 还没构建：{src_bin}（engines/midscene 下 npm run build）")
    midscene_dst = cli_dir / "midscene"
    dst_bin = midscene_dst / "dist" / "bin.mjs"
    reused = dst_bin.is_file() and dst_bin.stat().st_mtime >= src_bin.stat().st_mtime
    if reused:
        print(f"materialize: 复用已拷好的 midscene：{midscene_dst}", file=sys.stderr)
    else:
        if midscene_dst.exists():
            shutil.rmtree(midscene_dst)
        midscene_dst.mkdir(parents=True)
        for name in MIDSCENE_COPY:
            src = MIDSCENE_SRC / name
            if not src.exists():
                fail(f"midscene 缺 {name}：{src}（engines/midscene 下 npm ci && npm run build）")
            if src.is_dir():
                # symlinks=True：node_modules/.bin 全是相对软链，跟随会把树复制成几倍大、还可能撞上悬空链
                shutil.copytree(src, midscene_dst / name, symlinks=True, ignore_dangling_symlinks=True)
            else:
                shutil.copy2(src, midscene_dst / name)
    marker = cli_dir / "PREPARED.json"
    old = json.loads(marker.read_text(encoding="utf-8")) if marker.is_file() else {}
    sha = subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"],
                         capture_output=True, text=True).stdout.strip()
    # 刻意不记仓库路径：被测 agent 顺着 shim 就能走到这个目录，写进来等于自己开第二条泄漏渠道。
    marker.write_text(json.dumps({
        "git_sha": sha,
        "prepared_at": _now(),
        "midscene_copied_at": (old.get("midscene_copied_at") or _now()) if reused else _now(),
        "wheels": [Path(w).name for w in wheels],
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"materialize: CLI 备好：{cli_dir}（CLI={venv / 'bin' / 'gherkai'}；目录里刻意不放 skill 副本）", file=sys.stderr)
    print(str(cli_dir))


def assert_prepared(cli_dir: Path) -> tuple[Path, Path]:
    """舞台只许指向已备好的仓库外 CLI；没备好就响亮失败，绝不回落到仓库 .venv。"""
    cli = cli_dir / "venv" / "bin" / "gherkai"
    midscene_bin = cli_dir / "midscene" / "dist" / "bin.mjs"
    missing = [str(x) for x in (cli_dir / "PREPARED.json", cli, midscene_bin) if not x.exists()]
    if missing:
        fail("舞台要用的 CLI 还没备好，缺：\n  " + "\n  ".join(missing)
             + f"\n先跑：python skills/gherkai-evals/materialize.py --prepare-cli {cli_dir}")
    left = [str(x) for x in cli_dir.glob("venv/lib/python3.*/site-packages/gherkai_cli/skills")]
    if (cli_dir / "skill").exists():      # 旧版 --prepare-cli 放过一份副本，baseline 会 grep 到（第三轮实测）
        left.append(str(cli_dir / "skill"))
    if left:
        fail("这套 CLI 里又出现了 wheel 自带的 skill（baseline 会发现它），重跑 --prepare-cli：\n  " + "\n  ".join(left))
    return cli, midscene_bin


def assert_stage_isolated(stage: Path) -> None:
    """舞台里不得有仓库根路径、不得有 SKILL.md（见模块头注释第 5 步）。"""
    needle = str(REPO).encode()
    leaks, skills = [], []
    for p in stage.rglob("*"):
        if p.is_symlink() or not p.is_file():
            continue
        if p.name == "SKILL.md":
            skills.append(str(p.relative_to(stage)))
        try:
            if needle in p.read_bytes():
                leaks.append(str(p.relative_to(stage)))
        except OSError:
            continue
    if leaks:
        fail("舞台里出现仓库根路径（顺着它就能读到 skill 想替代的原始教材）：\n  " + "\n  ".join(leaks[:20]))
    if skills:
        fail("舞台里出现 SKILL.md（baseline 臂会发现自变量）：\n  " + "\n  ".join(skills[:20]))


def write_shim(stage: Path, cli_dir: Path) -> Path:
    venv_cli, midscene_bin = assert_prepared(cli_dir)
    aws_dir = stage / ".eval-aws"
    aws_dir.mkdir(exist_ok=True)
    (aws_dir / "config").write_text("", encoding="utf-8")
    (aws_dir / "credentials").write_text("", encoding="utf-8")
    bin_dir = stage / "bin"
    bin_dir.mkdir(exist_ok=True)
    shim = bin_dir / "gherkai"
    lines = [
        "#!/bin/sh",
        "# 评测 shim：让两臂在同一个受控环境里调用仓库外那套 gherkai（见 materialize.py 头注释）。",
        "unset AWS_PROFILE AWS_REGION AWS_DEFAULT_REGION",
        f'export AWS_CONFIG_FILE="{aws_dir / "config"}"',
        f'export AWS_SHARED_CREDENTIALS_FILE="{aws_dir / "credentials"}"',
    ]
    lines.append(f'export GHERKAI_WORKER_MIDSCENE_CMD="node {midscene_bin}"')
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
# 引擎 SDK 的原生产物（Nova 每次 act 一份 HTML + trajectory JSON；Midscene 一份 playwright-*.html 报告 + 每次执行一份 *.execution.json，动辄几 MB、内嵌截图）：skill 教 agent 不去解析它们，
# 评测只靠 evidence.json + 截图 + session_summary.json，故不入库。判定明细里指向它们的 ref 保留原样（只是指向不存在的文件）。
DROP_GLOBS = ("act_*.html", "act_*_trajectory.json", "playwright-*.html", "*.execution.json")
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
    ap.add_argument("case", nargs="?", help="fixtures/ 下的用例目录名")
    ap.add_argument("--prepare-cli", nargs="?", const=str(DEFAULT_CLI_DIR), metavar="DIR",
                    help=f"一次性把舞台要用的 CLI 装到 DIR（缺省 {DEFAULT_CLI_DIR}）后退出：构建 wheel、建 venv、"
                         "剥掉 wheel 自带的 skill、拷 midscene（要联网、几分钟）")
    ap.add_argument("--cli-dir", default=str(DEFAULT_CLI_DIR),
                    help=f"物化时 shim 指向的、已备好的 CLI 目录（缺省 {DEFAULT_CLI_DIR}）")
    ap.add_argument("--snapshot", metavar="PROJECT_DIR", help="反向：把真跑过的项目目录快照进 fixtures/<case>，不物化")
    ap.add_argument("--stage", help="舞台目录（缺省在 $TMPDIR 下新建；必须在仓库之外）")
    ap.add_argument("--keep", action="store_true", help="舞台已存在时不清空（缺省先删再拷）")
    ap.add_argument("--no-check", action="store_true", help="跳过物化后的完整性断言")
    args = ap.parse_args()

    if args.prepare_cli:
        if "/" not in args.prepare_cli and (FIXTURES / args.prepare_cli).is_dir():
            ap.error(f"--prepare-cli 的值是目标目录、不是用例名（你给的 {args.prepare_cli} 是个 fixture）："
                     "准备与物化分两次跑")
        prepare_cli(Path(args.prepare_cli).resolve())
        return
    if not args.case:
        ap.error("要给用例名（物化 / --snapshot），或者给 --prepare-cli")
    if args.snapshot:
        snapshot(Path(args.snapshot), args.case)
        return

    stage = Path(args.stage).resolve() if args.stage else Path(tempfile.mkdtemp(prefix=f"gherkai-eval-{args.case}-"))
    if REPO in stage.parents or stage == REPO:
        fail(f"舞台必须在仓库之外：{stage}")
    if stage.exists() and not args.keep:
        shutil.rmtree(stage)
    stage.mkdir(parents=True, exist_ok=True)

    cli_dir = Path(args.cli_dir).resolve()
    assert_no_installed_skill(stage)
    copy_fixture(args.case, stage)
    n = substitute_placeholders(stage)
    shim = write_shim(stage, cli_dir)
    assert_stage_isolated(stage)  # 恒开：隔离面坏了，这一轮数据就没意义
    if not args.no_check:
        integrity_check(stage, shim)
    print(f"舞台：{stage}", file=sys.stderr)
    print(f"占位符替换：{n} 个文件；CLI：{shim} → {cli_dir}"
          f"（前置 PATH：export PATH=\"{stage / 'bin'}:$PATH\"）", file=sys.stderr)
    print(stage)


if __name__ == "__main__":
    main()
