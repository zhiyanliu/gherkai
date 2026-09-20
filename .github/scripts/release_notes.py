#!/usr/bin/env python3
"""CHANGELOG.md 与根 README 的发布链接口：gate 校验「本 tag 在 CHANGELOG 里有节」与「README 里的 skill 安装命令钉的是本 tag」，
Release job 渲染正文。

ADR 0045 决策五：每版说明「不写发不出」——发布链 gate 断言 `## [X.Y.Z]` 节存在且非空；GitHub Release
正文为该节正文 + 固定的装法 / 升级块（`.github/release_body_footer.md`，占位符 `{{VERSION}}` /
`{{OWNER}}` / `{{REPO}}`），块里指向仓库文档的链接锁定到 `blob/vX.Y.Z/`，每版说明与它链到的文档永远同版。
ADR 0043 决策三：根 README 里 `npx skills add …/tree/vX.Y.Z/cli/gherkai_cli/skills/gherkai` 写死当前发行 tag（占位符不能直接
复制），gate 断言它等于本版、README 里没有这条命令也算失败；user guide 里这条 URL 若带具体版本号也须等于本版（占位符
`v<版本>` 不算）——tag 从「记得改」变成「不改发不出」。
护栏：`cli/tests/test_release_notes.py`（本脚本的行为，另对照真 CHANGELOG / README）与 `cli/tests/test_package_readmes.py`
（footer 的使用者面规则：零内部指代、零相对链接）。

用法：
    python3 .github/scripts/release_notes.py check  --version 1.4.4 [--changelog CHANGELOG.md] [--readme README.md] \
        [--user-guide docs/user-guide]
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
# README / user guide 里 skill 安装命令的 URL：`tree/` 后恰好一段 `vX.Y.Z`（安装器把这一段当 ref）。owner / repo 不写死，fork 也能用。
SKILL_INSTALL_URL = re.compile(r"github\.com/[^/\s`]+/[^/\s`]+/tree/v(?P<version>\d+\.\d+\.\d+)/cli/gherkai_cli/skills/gherkai(?![\w/])")


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


def skill_install_tag_problems(text: str, version: str, *, required: bool) -> list[str]:
    """文档里 skill 安装命令钉的版本逐处对照 version；required 时一处都没有也算问题。返回带行号的问题描述，空列表即通过。"""
    problems: list[str] = []
    seen = 0
    for no, line in enumerate(text.splitlines(), 1):
        for m in SKILL_INSTALL_URL.finditer(line):
            seen += 1
            if m.group("version") != version:
                problems.append(f"第 {no} 行 skill 安装命令钉的是 v{m.group('version')}，本版是 v{version}")
    if required and seen == 0:
        problems.append(f"没有 `npx skills add …/tree/v{version}/cli/gherkai_cli/skills/gherkai` 这条 skill 安装命令")
    return problems


def render(changelog: str, footer: str, version: str, owner: str, repo: str) -> str:
    body = section(changelog, version)
    tail = footer.replace("{{VERSION}}", version).replace("{{OWNER}}", owner).replace("{{REPO}}", repo)
    return f"{body}\n\n{tail.strip()}\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    chk = sub.add_parser("check", help="断言 CHANGELOG 里有该版本的非空节、README 里的 skill 安装命令钉的是该版本")
    rnd = sub.add_parser("render", help="渲染 GitHub Release 正文")
    for p in (chk, rnd):
        p.add_argument("--version", required=True, help="不带 v 前缀，如 1.4.4")
        p.add_argument("--changelog", default="CHANGELOG.md", type=Path)
    chk.add_argument("--readme", default=Path("README.md"), type=Path, help="须含钉本版 tag 的 skill 安装命令")
    chk.add_argument("--user-guide", default=Path("docs/user-guide"), type=Path,
                     help="目录；其中同一命令若带具体版本号也须等于本版，占位符不算")
    rnd.add_argument("--owner", required=True)
    rnd.add_argument("--repo", required=True)
    rnd.add_argument("--footer", default=Path(".github/release_body_footer.md"), type=Path)
    rnd.add_argument("--out", required=True, type=Path)
    ns = ap.parse_args(argv)

    try:
        changelog = ns.changelog.read_text(encoding="utf-8")
        if ns.cmd == "check":
            section(changelog, ns.version)
            problems = [f"{ns.readme}：{p}" for p in
                        skill_install_tag_problems(ns.readme.read_text(encoding="utf-8"), ns.version, required=True)]
            docs = sorted(ns.user_guide.rglob("*.md")) if ns.user_guide.is_dir() else []
            for doc in docs:
                problems += [f"{doc}：{p}" for p in
                             skill_install_tag_problems(doc.read_text(encoding="utf-8"), ns.version, required=False)]
            if problems:
                raise ValueError(f"skill 安装命令没钉到本版 tag，发版前改成 v{ns.version}：" + "；".join(problems))
            print(f"CHANGELOG 有版本 {ns.version} 的节；README 的 skill 安装命令钉 v{ns.version}")
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
