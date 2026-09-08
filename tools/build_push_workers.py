#!/usr/bin/env python
"""两个引擎 worker 镜像 build & push 到 ECR（固化手动步骤，ADR 0033）。

**为何存在**：`--backend cloud` 的 worker 跑在 Fargate 容器里，镜像须 build & push 到 ECR
（`{prefix}{engine}-worker` repo，CDK 只建 repo、不 build）。此前是手敲 README 里散落的
`docker login` + 两轮 `docker build --platform linux/amd64` + `docker push`——步骤多、易漏
`--platform`（arm Mac 不加则 build 出 arm64、Fargate 启动期 `exec format error` 挂死，ADR 0033）、
易手抖错 repo 名/tag。本脚本把这套固化成一条命令、消除手敲错。**不是 CI**——CI（GitHub Actions
+ OIDC 免密钥）是更外部的一步（远端仓库/凭证配置），本脚本是"比纯手敲进一步、比 CI 轻"的中间态，
本地能真跑验证（真 build + push 一轮）。CI 流水线仍是 ADR 0033/iac README 记的待做。

**必须 `--platform linux/amd64`（ADR 0033 陷阱，本脚本硬编码保证）**：Fargate task-def 默认 X86_64
runtime；不加则 arm Mac build 出 arm64、容器启动期挂死（错误在启动期、不易一眼看出是架构问题）。

**repo 名规则** = `{prefix}{engine}-worker`（ADR 0033 硬契约）。命名真源 = `runtime/gherkai_runtime/names.py`
（`task_def_name` / `DEFAULT_PREFIX` / `ENGINES`），cli 与 iac 都直接 import 它（无复刻）。本脚本
按「零依赖单文件、裸 `python` 跑、不设 PYTHONPATH」内联同一规则——故改命名规则须同步这里。

**build context** = 各引擎目录（`engines/{engine}/`，Dockerfile 在其下）。

前置：Docker daemon 运行中；AWS 凭证（region 默认 us-east-1）；ECR repo 已由 CDK 建
（`gherkai deploy`，见 deploy_aws/README.md）——本脚本不建 repo、只 push。

用法（从仓库根）：
    python tools/build_push_workers.py                       # 两个引擎都 build&push，tag=latest，prefix=gherkai-
    python tools/build_push_workers.py --engine novaact      # 只一个引擎
    python tools/build_push_workers.py --tag v2 --prefix prod-
    python tools/build_push_workers.py --dry-run             # 只打印将执行的命令，不真跑
"""
from __future__ import annotations

import argparse
import subprocess
import sys

ENGINES = ("novaact", "midscene")  # 引擎规范名（真源 gherkai_runtime.names.ENGINES 的内联副本，见 docstring）
DEFAULT_PREFIX = "gherkai-"        # 真源 gherkai_runtime.names.DEFAULT_PREFIX 的内联副本
DEFAULT_REGION = "us-east-1"
PLATFORM = "linux/amd64"           # 硬编码：Fargate X86_64，绝不可省（见模块 docstring 陷阱）

# 仓库根 = 本脚本的上上级（tools/ 的父）。避免依赖调用方 cwd。
from pathlib import Path
REPO_ROOT = Path(__file__).resolve().parents[1]


def _repo_name(prefix: str, engine: str) -> str:
    """ECR repo 名 = {prefix}{engine}-worker（对齐 gherkai_runtime.names.task_def_name，见 docstring）。"""
    return f"{prefix}{engine}-worker"


def _run(cmd: list[str], *, dry_run: bool, cwd: Path | None = None) -> None:
    """跑一条命令；dry-run 只打印。失败即抛（subprocess.run check=True）——不吞错、让调用者见真况。"""
    shown = " ".join(cmd) + (f"   (cwd={cwd})" if cwd else "")
    print(f"$ {shown}", flush=True)
    if dry_run:
        return
    subprocess.run(cmd, cwd=cwd, check=True)


def _account_id(region: str, dry_run: bool) -> str:
    """取当前账户 id（拼 ECR registry host）。dry-run 时用占位符（不真调 AWS）。"""
    if dry_run:
        return "<account>"
    out = subprocess.run(
        ["aws", "sts", "get-caller-identity", "--query", "Account", "--output", "text"],
        check=True, capture_output=True, text=True,
    )
    return out.stdout.strip()


def _ecr_login(registry: str, region: str, dry_run: bool) -> None:
    """登录 ECR（push 前必须）。get-login-password | docker login --password-stdin。region 决定 ECR 端点。"""
    print(f"# ECR 登录 {registry}", flush=True)
    if dry_run:
        print(f"$ aws ecr get-login-password --region {region} | docker login --username AWS --password-stdin {registry}", flush=True)
        return
    pw = subprocess.run(
        ["aws", "ecr", "get-login-password", "--region", region],
        check=True, capture_output=True, text=True,
    ).stdout
    subprocess.run(
        ["docker", "login", "--username", "AWS", "--password-stdin", registry],
        input=pw, check=True, text=True,
    )


def build_push(engine: str, *, prefix: str, tag: str, registry: str, dry_run: bool) -> None:
    """一个引擎：build（--platform linux/amd64）+ tag + push（registry host 已含 region）。"""
    repo = _repo_name(prefix, engine)
    image = f"{registry}/{repo}:{tag}"
    context = REPO_ROOT / "engines" / engine
    print(f"\n===== {engine} → {image} =====", flush=True)
    # build 直接打成完整 ECR image ref（省一步 docker tag）；--platform 硬编码 amd64（陷阱护栏）
    _run(["docker", "build", "--platform", PLATFORM, "-t", image, "."], dry_run=dry_run, cwd=context)
    _run(["docker", "push", image], dry_run=dry_run)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="两个引擎 worker 镜像 build & push 到 ECR（ADR 0033）")
    p.add_argument("--engine", choices=ENGINES, help="只构建一个引擎（默认两个都构建）")
    p.add_argument("--prefix", default=DEFAULT_PREFIX, help=f"ECR repo 名前缀（默认 {DEFAULT_PREFIX}；须与 `gherkai deploy --prefix` 一致）")
    p.add_argument("--tag", default="latest", help="镜像 tag（默认 latest）")
    p.add_argument("--region", default=DEFAULT_REGION, help=f"AWS region（默认 {DEFAULT_REGION}）")
    p.add_argument("--dry-run", action="store_true", help="只打印将执行的命令，不真 build/push/调 AWS")
    args = p.parse_args(argv)

    engines = [args.engine] if args.engine else list(ENGINES)
    account = _account_id(args.region, args.dry_run)
    registry = f"{account}.dkr.ecr.{args.region}.amazonaws.com"

    try:
        _ecr_login(registry, args.region, args.dry_run)
        for engine in engines:
            build_push(engine, prefix=args.prefix, tag=args.tag, registry=registry, dry_run=args.dry_run)
    except subprocess.CalledProcessError as e:
        print(f"\n✗ 失败（exit {e.returncode}）：{' '.join(e.cmd)}", file=sys.stderr)
        return 1
    print(f"\n✓ 完成：{', '.join(engines)}（tag={args.tag}, prefix={args.prefix}）", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
