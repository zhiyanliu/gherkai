#!/usr/bin/env python3
"""CHANGELOG.md 的发布链接口：gate 校验「本 tag 在 CHANGELOG 里有节」，Release job 渲染正文。

ADR 0045 决策五：每版说明「不写发不出」——发布链 gate 断言 `## [X.Y.Z]` 节存在且非空；GitHub Release
正文为该节正文 + 固定的装法 / 升级块（`.github/release_body_footer.md`，占位符 `{{VERSION}}` /
`{{OWNER}}` / `{{REPO}}`），块里指向仓库文档的链接锁定到 `blob/vX.Y.Z/`，每版说明与它链到的文档永远同版。
护栏：`cli/tests/test_release_notes.py`（本脚本的行为）与 `cli/tests/test_package_readmes.py`（footer 的
使用者面规则：零内部指代、零相对链接）。

用法：
    python3 .github/scripts/release_notes.py check  --version 1.4.4 [--changelog CHANGELOG.md]
    python3 .github/scripts/release_notes.py render --version 1.4.4 --owner zhiyanliu --repo gherkai \
        [--changelog CHANGELOG.md] [--footer .github/release_body_footer.md] --out release_body.md

只用标准库：发布链的 CHANGELOG gate 步用 `uv run --no-project python`（那个 job 已装 uv），Release 正文渲染步用
runner 自带 `python3`，两条路径都不带项目依赖。
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

HEADING = re.compile(r"^## \[(?P<version>[^\]]+)\](?:\s*-\s*(?P<date>\S+))?\s*$")


def section(changelog: str, version: str) -> str:
    """`## [version]` 到下一个 `## ` 之间的正文（不含标题行），两端空行去掉。找不到节 → ValueError。"""
    lines = changelog.splitlines()
    start = None
    for i, line in enumerate(lines):
        m = HEADING.match(line)
        if m and m.group("version") == version:
            start = i + 1
            break
    if start is None:
        raise ValueError(f"CHANGELOG 里没有版本 {version} 的节（需要一行 `## [{version}] - YYYY-MM-DD`）")
    body: list[str] = []
    for line in lines[start:]:
        if line.startswith("## "):
            break
        body.append(line)
    text = "\n".join(body).strip("\n")
    if not any(s.strip() and not s.lstrip().startswith("#") for s in text.splitlines()):
        raise ValueError(f"CHANGELOG 里版本 {version} 的节是空的：至少写一条使用者可见的变化")
    return text


def render(changelog: str, footer: str, version: str, owner: str, repo: str) -> str:
    body = section(changelog, version)
    tail = footer.replace("{{VERSION}}", version).replace("{{OWNER}}", owner).replace("{{REPO}}", repo)
    return f"{body}\n\n{tail.strip()}\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    chk = sub.add_parser("check", help="断言 CHANGELOG 里有该版本的非空节")
    rnd = sub.add_parser("render", help="渲染 GitHub Release 正文")
    for p in (chk, rnd):
        p.add_argument("--version", required=True, help="不带 v 前缀，如 1.4.4")
        p.add_argument("--changelog", default="CHANGELOG.md", type=Path)
    rnd.add_argument("--owner", required=True)
    rnd.add_argument("--repo", required=True)
    rnd.add_argument("--footer", default=Path(".github/release_body_footer.md"), type=Path)
    rnd.add_argument("--out", required=True, type=Path)
    ns = ap.parse_args(argv)

    try:
        changelog = ns.changelog.read_text(encoding="utf-8")
        if ns.cmd == "check":
            section(changelog, ns.version)
            print(f"CHANGELOG 有版本 {ns.version} 的节")
            return 0
        out = render(changelog, ns.footer.read_text(encoding="utf-8"), ns.version, ns.owner, ns.repo)
        ns.out.write_text(out, encoding="utf-8")
        print(f"Release 正文已写到 {ns.out}（{len(out.splitlines())} 行）")
        return 0
    except (OSError, ValueError) as e:
        print(f"::error::{e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
