"""`.github/scripts/release_notes.py` 的行为护栏：gate 的「本 tag 在 CHANGELOG 里有节」与 Release 正文渲染（ADR 0045 决策五）。

脚本只用标准库、在发布链里以 `uv run --no-project python` 运行；这里按模块直接 import 测纯函数，再执行一次 CLI 面
（子进程）确认退出码语义——gate 靠的就是非零退出。
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / ".github/scripts/release_notes.py"
FOOTER = REPO / ".github/release_body_footer.md"

SAMPLE = """# Changelog

## [Unreleased]

### 新增
- 还没发的东西

## [1.4.4] - 2026-09-20

### 变化
- Midscene 默认模型改为 GPT-5.6 Terra。

### 升级须知
- 部署方须重新运行 `gherkai deploy`。

## [1.4.3] - 2026-09-16

### 修复
- 一条修复。

## [1.4.2] - 2026-09-16

### 新增
"""


def _mod():
    spec = importlib.util.spec_from_file_location("release_notes", SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_section_extracts_exactly_one_version():
    m = _mod()
    body = m.section(SAMPLE, "1.4.4")
    assert "GPT-5.6 Terra" in body and "gherkai deploy" in body
    assert "还没发的东西" not in body and "一条修复" not in body, "节边界要停在下一个 `## `"
    assert not body.startswith("## ["), "正文不含版本标题行（Release 页已用 tag 作标题）"


def test_section_missing_or_empty_is_an_error():
    m = _mod()
    with pytest.raises(ValueError, match="没有版本 9.9.9"):
        m.section(SAMPLE, "9.9.9")
    with pytest.raises(ValueError, match="是空的"):
        m.section(SAMPLE, "1.4.2")  # 只有小标题、没有条目


def test_render_pins_links_to_the_tag():
    m = _mod()
    out = m.render(SAMPLE, FOOTER.read_text(encoding="utf-8"), "1.4.4", "zhiyanliu", "gherkai")
    assert out.startswith("### 变化"), "正文以 CHANGELOG 节开头"
    assert "{{" not in out, "占位符须全部替换"
    assert "blob/v1.4.4/docs/user-guide/README.md" in out and "blob/v1.4.4/CHANGELOG.md" in out
    assert "blob/HEAD/" not in out, "Release 正文的文档链接钉 tag，不随 HEAD 漂"
    assert "gherkai[local]==1.4.4" in out and "@gherkai/worker-midscene@1.4.4" in out


def test_cli_check_exit_codes(tmp_path: Path):
    cl = tmp_path / "CHANGELOG.md"
    cl.write_text(SAMPLE, encoding="utf-8")
    ok = subprocess.run([sys.executable, str(SCRIPT), "check", "--version", "1.4.4", "--changelog", str(cl)],
                        capture_output=True, text=True)
    assert ok.returncode == 0, ok.stderr
    bad = subprocess.run([sys.executable, str(SCRIPT), "check", "--version", "1.4.5", "--changelog", str(cl)],
                         capture_output=True, text=True)
    assert bad.returncode == 1 and "::error::" in bad.stderr, "缺节必须非零退出并用 ::error:: 标注（gate 靠它红）"


def test_repo_changelog_has_every_released_tag_and_unreleased():
    """真 CHANGELOG.md 对照真值集：每个已发行 tag `vX.Y.Z` 都要有非空节；`## [Unreleased]` 要在。"""
    m = _mod()
    changelog = (REPO / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "## [Unreleased]" in changelog
    tags = subprocess.run(["git", "-C", str(REPO), "tag", "--list", "v*"], capture_output=True, text=True, check=True).stdout.split()
    versions = sorted(t[1:] for t in tags if t.count(".") == 2 and t[1:].replace(".", "").isdigit())
    assert versions, "仓库里没有 vX.Y.Z tag？"
    missing = []
    for v in versions:
        try:
            m.section(changelog, v)
        except ValueError as e:
            missing.append(str(e))
    assert not missing, "已发行版本在 CHANGELOG.md 里缺节或为空：\n" + "\n".join(missing)
