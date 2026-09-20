#!/usr/bin/env python3
"""校验 `uv build --all-packages` 的产物：成员齐、版本一致、兄弟包 pin 已渲染。

发布链的静态闸门（ADR 0037 决策 8「gate：断言算出的版本 == 触发 tag」），也在 CI 里作
`uv build` smoke 的断言体——把「元数据/metadata hook 回归」挡在推索引之前，而不是等发行后
用户装不上才发现（ADR 0037「现状实测」记的原始故障就是 `Requires-Dist: core` 裸名）。

五条断言都对照**真值集**（前三条：根 pyproject 的 `[tool.uv.workspace] members` → 各成员
`[project] name`；第四条：源目录的文件系统遍历；
第五条：各包 pyproject 的 `[tool.hatch.build.targets.sdist] include`），不靠人读产物清单——新增一个 workspace 成员却忘了
它进不进发布链，只有逐条比对真值集才照得出来：

1. 每个成员都产出 sdist + wheel；
2. 全部产物同一个版本，且给了 `--expect-version` 时逐字等于它（版本真源是 git tag，
   ADR 0037 决策 2b）；
3. wheel METADATA 里凡指向兄弟发行包的 `Requires-Dist` 都带 `==<版本>` 同版本 pin
   （ADR 0037 决策 2b；uv-dynamic-versioning 的 metadata hook 没生效时这里会退化成裸名，
   而 wheel 本身照样构建成功——即「绿≠对」，故须显式断言）；
4. `gherkai` wheel 内 `gherkai_cli/skills/gherkai/` 的文件集**逐条等于**源目录（agent skill 随 wheel
   发行，ADR 0043 决策一/六），且不含评测资产（`evals`）。为何必须是集合相等：hatchling 默认认从项目根
   向上找到的第一份 `.gitignore`（即 `cli/.gitignore`，今含 `reports/`），命中的路径**静默**不进
   wheel（sdist 侧已改 include 白名单 + `ignore-vcs`、不再受它影响，见断言 5），`git add -f` 强跟踪
   也救不回来——「文件受 git 跟踪」式护栏对这一格无效。
5. 每个 sdist 的顶层条目集**逐条等于**该包 pyproject 的 `[tool.hatch.build.targets.sdist] include`
   白名单（去前导 `/`）加 `PKG-INFO`（ADR 0037 工程布局条：随包分发的只有各包源码目录与其声明的内容）。
   白名单是字面量，没有护栏就会静默漂回默认全收——而默认全收不只多带测试与 spike，还会把本机未跟踪的
   产物一并封进 sdist（hatchling 只认从项目根向上第一份 `.gitignore`，包内那份会挡住仓库根的规则）。
   例外一项：hatchling 把它认到的 `.gitignore` 强制塞进 sdist，不受 include / exclude / ignore-vcs 约束，
   故该文件只容许、不要求。没写 include 白名单的包只剩「顶层不含 `tests` / `spikes`」这条恒真红线。

用法：
    python3 .github/scripts/check_dist_metadata.py --dist dist [--expect-version 1.4.0]
"""

from __future__ import annotations

import argparse
import re
import sys
import tarfile
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


# hatchling 的 sdist 里恒有两样超出白名单的东西：`PKG-INFO`（它按元数据生成）与它认到的 `.gitignore`
# （sdist target 的默认 force-include，不受 include / exclude / ignore-vcs 约束；包内没有就认仓库根那份）。
# 前者必须在，后者只容许不要求——哪天 hatchling 不再塞它，这道闸门不该因此变红。
SDIST_GENERATED = frozenset({"PKG-INFO"})
SDIST_TOLERATED = frozenset({".gitignore"})


def sdist_whitelists(repo_root: Path, members: dict[str, str]) -> dict[str, set[str]]:
    """真值集：发行名 → 该包 pyproject 的 sdist `include` 白名单（去前导 `/`，模式锚在包根）。

    没写 `include` 的成员不进这张表，其 sdist 只受「顶层不含 `tests` / `spikes`」那条恒真红线约束
    （见模块 docstring 断言 5）。
    """
    result: dict[str, set[str]] = {}
    for member_dir, name in members.items():
        with (repo_root / member_dir / "pyproject.toml").open("rb") as fh:
            data = tomllib.load(fh)
        sdist_target = (
            data.get("tool", {}).get("hatch", {}).get("build", {}).get("targets", {}).get("sdist", {})
        )
        if include := sdist_target.get("include"):
            result[name] = {entry.lstrip("/") for entry in include}
    return result


SKILL_DIST_NAME = "gherkai"                          # 带 skill 的那个发行包（CLI）
SKILL_PACKAGE_DIR = "gherkai_cli/skills/gherkai"     # 包内路径与 wheel 内路径相同（hatchling 直收包目录下的非 .py）
SKILL_SOURCE_DIR = "cli/" + SKILL_PACKAGE_DIR


def skill_source_files(repo_root: Path) -> set[str]:
    """真值集：源目录的文件系统遍历（**不用 `git ls-files`**——见模块 docstring 断言 4 的理由：
    受不受 git 跟踪与进不进 wheel 是两件事，这里要比的是「磁盘上有什么」）。排除 `__pycache__/` 与 `*.pyc`。"""
    root = repo_root / SKILL_SOURCE_DIR
    if not root.is_dir():
        raise SystemExit(f"源目录不存在：{root}——skill 搬家了？先修本脚本的路径，别让闸门静默变绿")
    return {
        str(p.relative_to(root)) for p in root.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"
    }


def check_skill_payload(wheel: Path, repo_root: Path) -> list[str]:
    """断言 4：wheel 内 skill 文件集 == 源目录文件集，且 wheel 里不含评测资产。"""
    expected = skill_source_files(repo_root)
    with zipfile.ZipFile(wheel) as zf:
        names = zf.namelist()

    prefix = SKILL_PACKAGE_DIR + "/"
    shipped = {n[len(prefix):] for n in names if n.startswith(prefix) and not n.endswith("/")}
    errors: list[str] = []
    if missing := sorted(expected - shipped):
        errors.append(
            f"{wheel.name} 里缺这些 skill 文件：{missing}——最可能是被 `cli/.gitignore` 静默吞了"
            "（hatchling 默认认项目根向上第一份 .gitignore）；改名或在 cli/pyproject 的 wheel target 显式 include"
        )
    if extra := sorted(shipped - expected):
        errors.append(f"{wheel.name} 里多出这些 skill 文件（源目录没有）：{extra}——产物目录不干净或构建配置多收了")
    if evals := sorted(n for n in names if "evals" in n):
        errors.append(f"{wheel.name} 里带上了评测资产：{evals}——评测资产住仓库根 skills/gherkai-evals/，不该进发行包")
    return errors


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
        fail(f"{dist_dir} 下没有 wheel——`uv build --all-packages` 未运行或产物目录传错了")
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

        # 断言 3：兄弟包必须带 `==<版本>` 的同版本 pin
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

    # 断言 4：agent skill 随 wheel 带走，逐文件对齐源目录
    if SKILL_DIST_NAME in seen_wheels:
        errors.extend(check_skill_payload(seen_wheels[SKILL_DIST_NAME], repo_root))

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

    # 断言 5：sdist 顶层 == 该包的打包白名单（include 是字面量、无护栏会静默漂回默认全收）
    whitelists = sdist_whitelists(repo_root, members)
    for s in sdists:
        with tarfile.open(s) as t:
            tops = {p[1] for p in (m.name.split("/") for m in t.getmembers()) if len(p) > 1}
        # 产物名形态为 `<规范化发行名>-<版本>.tar.gz`（PEP 625），版本段不含 `-`
        sdist_dist_name = normalized_to_dist.get(s.name[: -len(".tar.gz")].rsplit("-", 1)[0])
        if sdist_dist_name is None:
            errors.append(f"{s.name} 的发行名不是任何 workspace 成员——产物目录不干净（旧产物没清）")
            continue
        # 恒真红线（与白名单无关，防「把 /tests 写进白名单」这类自洽却违 ADR 的改动）
        if hard := sorted(tops & {"tests", "spikes"}):
            errors.append(
                f"{s.name} 顶层含 {hard}：测试与 spike 恒不进发行包（ADR 0037 工程布局条）"
                "——白名单里若列了它们，是白名单写错了"
            )
        expected = whitelists.get(sdist_dist_name)
        if expected is None:
            # 该包还没写 include 白名单：顶层集合相等这一格照不出来，只剩上面那条红线
            continue
        expected = expected | SDIST_GENERATED
        if missing := sorted(expected - tops):
            errors.append(
                f"{s.name} 顶层缺 {missing}：该包 pyproject 的 sdist include 列了、产物里没有"
                "（磁盘上不存在，或被 readme / license-files 字段的改动带走了）"
            )
        if extra := sorted(tops - expected - SDIST_TOLERATED):
            errors.append(
                f"{s.name} 顶层多出 {extra}（白名单外）：pyproject 的 sdist include 漂回默认全收，"
                "或有人往白名单外的顶层塞了东西（ADR 0037 工程布局条）"
            )

    if args.expect_version and version and version != args.expect_version:
        errors.append(
            f"构建算出的版本 {version} 不等于期望的 {args.expect_version}。"
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
    print("产物校验通过：成员齐、版本一致（无旧版本残留）、兄弟包 pin 已渲染、skill 文件集与源目录一致、sdist 顶层与打包白名单一致。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
