"""使用者向文档的护栏：根 README 与包 README（发行包长描述，逐字上 PyPI / npm 页面）、包 Summary（CLAUDE.md 文档纪律「README / DEVELOPMENT 分层」；决策与理由：ADR 0039）。

读者是「装了包、没有仓库的人」：ADR 编号 / 决策号 / 内部机制名对他们是噪声，`../docs/...` 这类相对链接在
PyPI/npm 上全是死链。contributor 内容（布局、测试、spike、ADR 指针）归同目录 `DEVELOPMENT.md`，不进包。
本测试只扫**真正进包**的那几份：pyproject `readme =` 指向的文件 + npm `files` 里的 README。
"""
from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
PY_PACKAGES = ("cli", "core", "runtime", "deploy_aws", "engines/novaact")
NPM_PACKAGES = ("engines/midscene",)

FORBIDDEN = re.compile(
    r"\bADR\b"                       # ADR 编号 / 「见 ADR」
    r"|决策\s*[0-9A-Za-z]"            # 决策 N
    r"|不变量|定位链|被拒方案|重议闸门|实测项|接缝契约|模块头|组合根"
)
RELATIVE_LINK = re.compile(r"\]\((?:\.\.?/|(?![a-z][a-z0-9+.-]*:|#)[^)\s]+\.md)")  # ](../x) / ](./x) / ](foo.md)


def _shipped_readmes() -> list[Path]:
    files: list[Path] = []
    for pkg in PY_PACKAGES:
        meta = tomllib.loads((REPO / pkg / "pyproject.toml").read_text(encoding="utf-8"))
        readme = meta["project"].get("readme")
        assert readme, f"{pkg}/pyproject.toml 没有 readme 字段——发行包必须带长描述"
        files.append(REPO / pkg / (readme if isinstance(readme, str) else readme["file"]))
    for pkg in NPM_PACKAGES:
        pj = json.loads((REPO / pkg / "package.json").read_text(encoding="utf-8"))
        assert "README.md" in pj.get("files", []), f"{pkg}/package.json 的 files 须含 README.md"
        files.append(REPO / pkg / "README.md")
    for f in files:
        assert f.is_file(), f"进包的 README 不存在：{f}"
    return files


@pytest.mark.parametrize("readme", _shipped_readmes(), ids=lambda p: str(p.relative_to(REPO)))
def test_shipped_readme_is_for_users_only(readme: Path):
    text = readme.read_text(encoding="utf-8")
    hits = [f"{readme.relative_to(REPO)}:{i}: {line.strip()[:120]}"
            for i, line in enumerate(text.splitlines(), 1) if FORBIDDEN.search(line)]
    assert not hits, "包 README 上 PyPI/npm 页面，不得含内部指代（ADR/决策号/内部机制名）——搬去同目录 DEVELOPMENT.md：\n" + "\n".join(hits)
    rel = [f"{readme.relative_to(REPO)}:{i}: {line.strip()[:120]}"
           for i, line in enumerate(text.splitlines(), 1) if RELATIVE_LINK.search(line)]
    assert not rel, "包 README 里的相对链接在 PyPI/npm 页面上是死链，改绝对 URL：\n" + "\n".join(rel)


def test_every_package_dir_has_a_development_md():
    """contributor 内容有明确去处（不是被删掉）：根目录与每个包目录各一份 DEVELOPMENT.md。"""
    missing = [pkg for pkg in ("",) + PY_PACKAGES + NPM_PACKAGES if not (REPO / pkg / "DEVELOPMENT.md").is_file()]
    assert not missing, f"缺 DEVELOPMENT.md：{missing}"


def test_root_readme_is_for_users_only():
    """根 README = 仓库首页、给使用者：不写 ADR 编号/决策号/内部机制名（目录结构、开发环境、测试、发布归 DEVELOPMENT.md）。
    相对链接在 GitHub 上正常渲染，故这里不查链接形态。"""
    text = (REPO / "README.md").read_text(encoding="utf-8")
    hits = [f"README.md:{i}: {line.strip()[:120]}" for i, line in enumerate(text.splitlines(), 1) if FORBIDDEN.search(line)]
    assert not hits, "根 README 面向使用者，内部指代搬去 DEVELOPMENT.md：\n" + "\n".join(hits)


def test_package_summaries_are_for_users_only():
    """pyproject `description` / package.json `description` = PyPI/npm 页顶的 Summary 一行，同属包页面。"""
    hits = []
    for pkg in PY_PACKAGES:
        meta = tomllib.loads((REPO / pkg / "pyproject.toml").read_text(encoding="utf-8"))
        d = meta["project"].get("description", "")
        if FORBIDDEN.search(d):
            hits.append(f"{pkg}/pyproject.toml description: {d[:100]}")
    for pkg in NPM_PACKAGES:
        d = json.loads((REPO / pkg / "package.json").read_text(encoding="utf-8")).get("description", "")
        if FORBIDDEN.search(d):
            hits.append(f"{pkg}/package.json description: {d[:100]}")
    assert not hits, "包 Summary 不得含内部指代：\n" + "\n".join(hits)
