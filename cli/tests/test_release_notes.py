"""`.github/scripts/release_notes.py` 的行为护栏：gate 的「本 tag 在 CHANGELOG 里有节」（ADR 0045 决策五）与「README 的 skill
安装命令钉本 tag」（ADR 0043 决策三），以及 Release 正文渲染。

脚本只用标准库：发布链的 CHANGELOG gate 步用 `uv run --no-project python`（那个 job 已装 uv），Release 正文渲染步用
runner 自带 `python3`，两条路径都不带项目依赖。这里按模块直接 import 测纯函数，再执行一次 CLI 面
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
    assert "blob/HEAD/" not in out, "Release 正文的文档链接锁定 tag，不随 HEAD 漂"
    assert "gherkai[local]==1.4.4" in out and "@gherkai/worker-midscene@1.4.4" in out


SKILL_CMD = "npx skills add https://github.com/zhiyanliu/gherkai/tree/v{v}/cli/gherkai_cli/skills/gherkai -a claude-code -a codex"


def test_skill_install_tag_problems():
    m = _mod()
    assert m.skill_install_tag_problems(SKILL_CMD.format(v="1.4.4"), "1.4.4", required=True) == []
    stale = m.skill_install_tag_problems("x\n" + SKILL_CMD.format(v="1.4.3"), "1.4.4", required=True)
    assert len(stale) == 1 and "第 2 行" in stale[0] and "v1.4.3" in stale[0] and "v1.4.4" in stale[0]
    absent = m.skill_install_tag_problems("没有命令", "1.4.4", required=True)
    assert len(absent) == 1 and "没有" in absent[0], "README 里丢了这条命令也要红"
    assert m.skill_install_tag_problems("没有命令", "1.4.4", required=False) == [], "user guide 允许没有"
    placeholder = SKILL_CMD.replace("v{v}", "v<版本>")
    assert m.skill_install_tag_problems(placeholder, "1.4.4", required=False) == [], "占位符不是具体版本，不算"
    fork = SKILL_CMD.format(v="1.4.4").replace("zhiyanliu/gherkai", "someone/fork")
    assert m.skill_install_tag_problems(fork, "1.4.4", required=True) == [], "owner / repo 不写死"


def _check(tmp_path: Path, version: str, readme_tag: str, guide_tag: str | None = None) -> subprocess.CompletedProcess[str]:
    cl = tmp_path / "CHANGELOG.md"
    cl.write_text(SAMPLE, encoding="utf-8")
    readme = tmp_path / "README.md"
    readme.write_text(f"# x\n\n```bash\n{SKILL_CMD.format(v=readme_tag)}\n```\n" if readme_tag else "# x\n", encoding="utf-8")
    guide = tmp_path / "user-guide"
    guide.mkdir(exist_ok=True)
    (guide / "getting-started.md").write_text(SKILL_CMD.format(v=guide_tag) if guide_tag else SKILL_CMD.replace("v{v}", "v<版本>"),
                                              encoding="utf-8")
    return subprocess.run([sys.executable, str(SCRIPT), "check", "--version", version, "--changelog", str(cl),
                           "--readme", str(readme), "--user-guide", str(guide)], capture_output=True, text=True)


def test_cli_check_exit_codes(tmp_path: Path):
    ok = _check(tmp_path, "1.4.4", readme_tag="1.4.4")
    assert ok.returncode == 0, ok.stderr
    bad = _check(tmp_path, "1.4.5", readme_tag="1.4.5")
    assert bad.returncode == 1 and "::error::" in bad.stderr, "缺节必须非零退出并用 ::error:: 标注（gate 靠它红）"
    stale = _check(tmp_path, "1.4.4", readme_tag="1.4.3")
    assert stale.returncode == 1 and "v1.4.3" in stale.stderr and "README.md" in stale.stderr, "README 的 tag 忘了改要红"
    missing = _check(tmp_path, "1.4.4", readme_tag="")
    assert missing.returncode == 1 and "没有" in missing.stderr, "README 里没有这条命令要红"
    guide_stale = _check(tmp_path, "1.4.4", readme_tag="1.4.4", guide_tag="1.4.2")
    assert guide_stale.returncode == 1 and "getting-started.md" in guide_stale.stderr, "user guide 里带具体旧版本也要红"


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


def test_repo_readme_pins_skill_install_to_changelog_top_version():
    """真 README / user guide 对照真值集：skill 安装命令钉的 tag 等于 CHANGELOG 顶部已发行版本（发版前两处同一次改）。"""
    m = _mod()
    changelog = (REPO / "CHANGELOG.md").read_text(encoding="utf-8")
    released = [mt.group("version") for line in changelog.splitlines() if (mt := m.HEADING.match(line)) and mt.group("version") != "Unreleased"]
    assert released, "CHANGELOG 里没有已发行版本节？"
    top = released[0]
    problems = [f"README.md：{p}" for p in m.skill_install_tag_problems((REPO / "README.md").read_text(encoding="utf-8"), top, required=True)]
    for doc in sorted((REPO / "docs/user-guide").rglob("*.md")):
        problems += [f"{doc.relative_to(REPO)}：{p}" for p in m.skill_install_tag_problems(doc.read_text(encoding="utf-8"), top, required=False)]
    assert not problems, f"skill 安装命令没钉到 CHANGELOG 顶部版本 v{top}：\n" + "\n".join(problems)
