#!/usr/bin/env python3
"""校验 `uv build --all-packages` 的产物：成员齐、版本一致、兄弟包 pin 已渲染。

发布链的静态闸门（ADR 0037 决策 8「gate：断言算出的版本 == 触发 tag」），也在 CI 里作
`uv build` smoke 的断言体——把「元数据/metadata hook 回归」挡在推索引之前，而不是等发行后
用户装不上才发现（ADR 0037「现状实测」记的原始故障就是 `Requires-Dist: core` 裸名）。

三条断言都对照**真值集**（根 pyproject 的 `[tool.uv.workspace] members` → 各成员
`[project] name`），不靠人读产物清单——新增一个 workspace 成员却忘了它进不进发布链，
只有逐条比对真值集才照得出来：

1. 每个成员都产出 sdist + wheel；
2. 全部产物同一个版本，且给了 `--expect-version` 时逐字等于它（版本真源 = git tag，
   ADR 0037 决策 2b）；
3. wheel METADATA 里凡指向兄弟发行包的 `Requires-Dist` 都带 `==<版本>` lockstep pin
   （ADR 0037 决策 2b；uv-dynamic-versioning 的 metadata hook 没生效时这里会退化成裸名，
   而 wheel 本身照样构建成功——即「绿≠对」，故须显式断言）。

用法：
    python3 .github/scripts/check_dist_metadata.py --dist dist [--expect-version 1.4.0]
"""

from __future__ import annotations

import argparse
import re
import sys
import tomllib
import zipfile
from email.parser import BytesParser
from pathlib import Path

REPO_ROOT_DEFAULT = Path(__file__).resolve().parents[2]


def normalize(name: str) -> str:
    """发行名 → 产物文件名里的形态（PEP 503 规范化后 `-`/`.` 变 `_`，见 PEP 427/625）。"""
    return re.sub(r"[-_.]+", "_", name).lower()


def fail(msg: str) -> None:
    # GitHub Actions 的 error 注解：在 job 摘要与 diff 上都能看见。
    print(f"::error::{msg}", file=sys.stderr)


def member_dist_names(repo_root: Path) -> dict[str, str]:
    """真值集：workspace 成员目录 → 其 `[project] name`（发行名）。"""
    root_pyproject = repo_root / "pyproject.toml"
    with root_pyproject.open("rb") as fh:
        root = tomllib.load(fh)
    members = root.get("tool", {}).get("uv", {}).get("workspace", {}).get("members")
    if not members:
        raise SystemExit(f"{root_pyproject} 里没有 [tool.uv.workspace] members——真值集读不到，拒绝继续")

    result: dict[str, str] = {}
    for pattern in members:
        # members 支持 glob（本项目当前全是字面路径，仍按 uv 的语义展开，避免将来加 glob 时静默漏成员）
        matched = sorted(repo_root.glob(pattern)) if any(c in pattern for c in "*?[") else [repo_root / pattern]
        for member_dir in matched:
            pyproject = member_dir / "pyproject.toml"
            if not pyproject.is_file():
                raise SystemExit(f"workspace 成员 {member_dir} 下没有 pyproject.toml")
            with pyproject.open("rb") as fh:
                data = tomllib.load(fh)
            name = data.get("project", {}).get("name")
            if not name:
                raise SystemExit(f"{pyproject} 的 [project] 没有 name")
            result[str(member_dir.relative_to(repo_root))] = name
    return result


def wheel_metadata(wheel: Path):
    with zipfile.ZipFile(wheel) as zf:
        entries = [n for n in zf.namelist() if n.endswith(".dist-info/METADATA")]
        if len(entries) != 1:
            raise SystemExit(f"{wheel.name} 里 METADATA 不是恰好一份：{entries}")
        with zf.open(entries[0]) as fh:
            return BytesParser().parse(fh)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist", default="dist", help="uv build 的产物目录（默认 dist）")
    parser.add_argument(
        "--expect-version",
        default=None,
        help="期望版本（release 链传触发 tag 去掉前导 v 的值）；不给则只校验内部一致性",
    )
    parser.add_argument("--repo-root", default=str(REPO_ROOT_DEFAULT), help="仓库根（读 workspace 真值集）")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    dist_dir = Path(args.dist).resolve()
    if not dist_dir.is_dir():
        fail(f"产物目录不存在：{dist_dir}")
        return 1

    members = member_dist_names(repo_root)
    dist_names = set(members.values())
    normalized_to_dist = {normalize(n): n for n in dist_names}

    wheels = sorted(dist_dir.glob("*.whl"))
    sdists = sorted(dist_dir.glob("*.tar.gz"))
    if not wheels:
        fail(f"{dist_dir} 下没有 wheel——`uv build --all-packages` 没跑或产物目录传错了")
        return 1

    errors: list[str] = []
    versions_seen: dict[str, set[str]] = {}  # 发行名 → 该成员在 dist 里出现过的**全部**版本（脏目录会 >1）
    seen_wheels: dict[str, Path] = {}

    for wheel in wheels:
        meta = wheel_metadata(wheel)
        name = meta.get("Name")
        version = meta.get("Version")
        if not name or not version:
            errors.append(f"{wheel.name} 的 METADATA 缺 Name/Version")
            continue
        if name not in dist_names:
            errors.append(f"{wheel.name} 的发行名 {name} 不是任何 workspace 成员——产物目录不干净（旧产物没清）")
            continue
        seen_wheels[name] = wheel
        versions_seen.setdefault(name, set()).add(version)

        # 断言 3：兄弟包必须带 `==<版本>` 的 lockstep pin
        for entry in meta.get_all("Requires-Dist") or []:
            dep_raw = re.split(r"[\s;\[=<>!~(]", entry.strip(), maxsplit=1)[0]
            dep = normalize(dep_raw)
            if dep not in normalized_to_dist or normalized_to_dist[dep] == name:
                continue
            if f"=={version}" not in entry.replace(" ", ""):
                errors.append(
                    f"{wheel.name} 的 Requires-Dist 兄弟包没 pin 成 `=={version}`：{entry!r}"
                    "——uv-dynamic-versioning 的 metadata hook 没生效（检查该包 pyproject 的"
                    " [tool.hatch.metadata.hooks.uv-dynamic-versioning] 与 dynamic 声明，ADR 0037 决策 2b）"
                )

    # 断言 1：成员齐（sdist + wheel 各一）
    for member_dir, name in sorted(members.items()):
        if name not in seen_wheels:
            errors.append(f"workspace 成员 {member_dir}（发行名 {name}）没有 wheel 产物——它没进发布链")

    # 断言 2：版本一致——先按成员查「同名多版本并存」（脏 dist：旧产物没清；`uv publish` 默认推 dist/* 全部文件，
    # 会把上一次 build 的旧版本一并推上索引），再查跨成员一致。按发行名收单值会让后者覆盖前者、照不出这一格。
    for name, vs in sorted(versions_seen.items()):
        if len(vs) > 1:
            errors.append(f"dist 目录里 {name} 同时存在 {sorted(vs)} 多个版本——旧产物没清，先 rm -rf 产物目录再 build")
    distinct = sorted({v for vs in versions_seen.values() for v in vs})
    if len(distinct) > 1:
        errors.append(
            f"产物版本不一致：{distinct}——同 repo 全成员应从同一 git 状态派生出同一版本（ADR 0037 决策 2b）"
        )
    version = distinct[0] if distinct else ""

    if version:
        for member_dir, name in sorted(members.items()):
            if name not in seen_wheels:
                continue
            expected_sdist = dist_dir / f"{normalize(name)}-{version}.tar.gz"
            if not expected_sdist.is_file():
                errors.append(
                    f"{name} 缺 sdist {expected_sdist.name}（现有：{[p.name for p in sdists]}）"
                )

    if args.expect_version and version and version != args.expect_version:
        errors.append(
            f"构建算出的版本 {version} ≠ 期望 {args.expect_version}。"
            "常见原因：checkout 不在 tag commit 上；工作树非纯净（dirty=true 会带 `+` 本地段，"
            "而 PyPI 拒收带本地段的版本）；tag 不是 `vX.Y.Z` 形态。版本真源是 git tag，"
            "对不上就绝不往索引上推（ADR 0037 决策 2b/8）"
        )

    print(f"产物目录 {dist_dir}：{len(wheels)} wheel / {len(sdists)} sdist，版本 {version or '?'}")
    for member_dir, name in sorted(members.items()):
        mark = "ok" if name in seen_wheels else "缺"
        print(f"  [{mark}] {member_dir:<16} {name}")

    if errors:
        for err in errors:
            fail(err)
        return 1
    print("产物校验通过：成员齐、版本一致（无旧版本残留）、兄弟包 pin 已渲染。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
