"""使用者向文档的护栏：包页面（各包 README 即发行包长描述，逐字上 PyPI / npm 页面；GitHub Release 正文的固定块）、根 README、包 Summary（CLAUDE.md 文档纪律「文档按读者三分类归位」；决策与理由：ADR 0039）。

读者是「装了包、没有仓库的人」：ADR 编号 / 决策号 / 内部机制名对他们是噪声，`../docs/...` 这类相对链接在
PyPI/npm 上全是死链。contributor 内容（布局、测试、spike、ADR 指针）归同目录 `DEVELOPMENT.md`，不进包。
包页面的扫描面与规则束在 `_doc_rules`（`package_pages()` / `scan("package-page", …)`）：用户文档的整套规则（内部指代、口头语、
退役旧名、符号当谓语、「退 N」、正文箭头、悬空指针）再加零相对链接，Release 固定块另要求仓库链接锁定 tag；hook 与提交闸门
用同一束，本文件是 CI 兜底，另断言扫描面本身完整（每个包都带 README、release.yml 仍走这条渲染链）。
"""
from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path

import pytest
from _doc_rules import (  # 禁词、扫描面与规则束的单一事实源（见该模块 docstring）
    COLLOQUIAL, FORBIDDEN, NPM_PACKAGES, PY_PACKAGES, RELEASE_FOOTER, RELEASE_FOOTER_SAMPLE, REPO, RETIRED_TERMS, classify,
    package_pages, scan,
)

SHIPPED_READMES = [p for p in package_pages() if p != RELEASE_FOOTER]


def _hits(page: Path) -> list[str]:
    return [f"{page.relative_to(REPO)}:{line_no}: {label} · {text}" for line_no, label, text in scan("package-page", page)]


def test_package_pages_cover_every_package():
    """扫描面完整：每个发行包恰有一份进包的 README（pyproject `readme` 字段 / npm `files` 含 README.md，且文件存在），
    Release 固定块也在面内，classify 把它们全归到包页面（hook 与提交闸门靠它选规则束）。包搬家或改元数据不许让护栏静默变绿。"""
    per_pkg = {pkg: [p for p in SHIPPED_READMES if REPO / pkg in p.parents] for pkg in PY_PACKAGES + NPM_PACKAGES}
    missing = [pkg for pkg, found in per_pkg.items() if len(found) != 1]
    assert not missing, ("这些包在包页面里没有恰好一份 README（pyproject 缺 `readme` 字段、npm `files` 未列 README.md，"
                         f"或文件不存在）：{missing}")
    assert RELEASE_FOOTER in package_pages(), "缺 .github/release_body_footer.md（Release 正文的固定块）"
    wrong = [str(p.relative_to(REPO)) for p in package_pages() if classify(p) != "package-page"]
    assert not wrong, f"这些包页面没有被 classify 归到包页面，hook 与提交闸门会按别的规则束扫：{wrong}"


def test_package_page_rules_catch_each_form(tmp_path):
    """包页面规则束是用户文档的整套规则加零相对链接：内部指代、「退 N」、正文箭头、相对链接各写一处，逐类都报。"""
    page = tmp_path / "README.md"
    page.write_text("见 ADR 0039。\n失败时退 2。\n安装然后 → 运行。\n详见 [指南](../docs/user-guide/README.md)。\n",
                    encoding="utf-8")
    labels = {(line_no, label) for line_no, label, _ in scan("package-page", page)}
    assert labels == {(1, "内部指代"), (2, "省略中心词的「退 N」"), (3, "正文箭头"),
                      (4, "相对链接（包页面与 Release 页面上是死链）")}


def test_release_footer_rules_catch_unpinned_links(tmp_path, monkeypatch):
    """Release 固定块先代入占位符样例值再扫：仓库链接写 blob/HEAD/ 照报，锁定 tag 的链接不报。"""
    import _doc_rules
    footer = tmp_path / "release_body_footer.md"
    footer.write_text("文档：https://github.com/{{OWNER}}/{{REPO}}/blob/HEAD/README.md\n"
                      "文档：https://github.com/{{OWNER}}/{{REPO}}/blob/v{{VERSION}}/README.md\n", encoding="utf-8")
    monkeypatch.setattr(_doc_rules, "RELEASE_FOOTER", footer)
    hits = _doc_rules.scan("package-page", footer)
    assert {(n, label) for n, label, _ in hits} == {(1, "未锁定 tag 的仓库链接（blob/HEAD/）")}
    assert "github.com/o/r/blob/HEAD/" in hits[0][2], "报出的应是代入占位符样例值之后的形态"


@pytest.mark.parametrize("readme", SHIPPED_READMES, ids=lambda p: str(p.relative_to(REPO)))
def test_shipped_readme_is_for_users_only(readme: Path):
    hits = _hits(readme)
    assert not hits, ("包 README 上 PyPI/npm 页面，按用户文档写：内部指代搬去同目录 DEVELOPMENT.md，旧名换成 CONTEXT.md 词表里的"
                      "规范名，符号与缩写写成完整句，相对链接改绝对 URL：\n" + "\n".join(hits))


def test_every_package_dir_has_a_development_md():
    """contributor 内容有明确去处（不是被删掉）：根目录一份 CONTRIBUTING.md（GitHub 惯例名）、每个包目录各一份 DEVELOPMENT.md。"""
    missing = [pkg for pkg in PY_PACKAGES + NPM_PACKAGES if not (REPO / pkg / "DEVELOPMENT.md").is_file()]
    assert not missing, f"缺 DEVELOPMENT.md：{missing}"
    assert (REPO / "CONTRIBUTING.md").is_file(), "缺根 CONTRIBUTING.md（contributor 入口，原 DEVELOPMENT.md）"


def test_root_readme_is_for_users_only():
    """根 README 是仓库首页、给使用者看：不写 ADR 编号/决策号/内部机制名（目录结构、开发环境、测试、发布归根 CONTRIBUTING.md）。
    相对链接在 GitHub 上正常渲染，故这里不查链接形态。"""
    text = (REPO / "README.md").read_text(encoding="utf-8")
    hits = [f"README.md:{i}: {line.strip()[:120]}" for i, line in enumerate(text.splitlines(), 1)
            if FORBIDDEN.search(line) or COLLOQUIAL.search(line) or RETIRED_TERMS.search(line)]
    assert not hits, "根 README 面向使用者：内部指代搬去根 CONTRIBUTING.md，退役旧名换成词表里的规范名：\n" + "\n".join(hits)


def test_package_summaries_are_for_users_only():
    """pyproject `description` / package.json `description` 是 PyPI/npm 页顶的 Summary 一行，同属包页面。"""
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


def test_github_release_body_is_for_users_only():
    """GitHub Release 正文由 CHANGELOG.md 本版节与 `.github/release_body_footer.md` 拼成（`.github/scripts/release_notes.py`
    渲染，占位符 `{{VERSION}}` / `{{OWNER}}` / `{{REPO}}`）。Releases 页面是没有仓库上下文的使用者面：按包页面规则束扫，
    仓库内文件只用绝对 URL 且锁定 tag（`blob/v<版本>/`，不用 HEAD——本版说明要与它链到的文档同版）。
    release.yml 必须还在用这条渲染链（改形态别让护栏静默变绿）。"""
    assert RELEASE_FOOTER.is_file(), "缺 .github/release_body_footer.md（Release 正文的固定块）"
    footer = RELEASE_FOOTER.read_text(encoding="utf-8")
    for ph in RELEASE_FOOTER_SAMPLE:
        assert ph in footer, f"footer 模板缺占位符 {ph}"
    hits = _hits(RELEASE_FOOTER)  # scan 先代入占位符样例值再扫，与读者在 Releases 页面看到的形态一致
    assert not hits, ("Release 正文面向使用者，按用户文档写：内部指代改产品语言、符号与缩写写成完整句、"
                      "仓库文件用锁定 tag 的绝对 URL：\n" + "\n".join(hits))
    wf = (REPO / ".github/workflows/release.yml").read_text(encoding="utf-8")
    assert "release_notes.py render" in wf and "body_path:" in wf, "release.yml 不再经 release_notes.py 渲染正文——护栏与实际形态脱节"
    assert "release_notes.py check" in wf, "release.yml 的 gate 少了 CHANGELOG 节校验（每版说明「不写发不出」）"
    assert re.search(r"^\s*body:\s*\|", wf, re.M) is None, "release.yml 里不该再有内联 body: |（正文只从 CHANGELOG + footer 渲染）"
