"""`gherkai skill install` 的行为护栏（ADR 0043 决策三）：纯文件系统、零网络、零 AWS。

覆盖：首装（包内那份逐字节 + 版本标记）、`--print`（stdout 只此一处）、跨版本收敛（旧 reference 必须消失）、
自护判据（不像本命令装的目录 → 退 2 且一个字节都不动）、`--agent all` 两处落点、`--global` 认 HOME、
那行提示的追加语义（幂等、按 agent 挑 CLAUDE.md / AGENTS.md、非交互缺省不写）、取不到版本时的标记、
裸 `gherkai skill` 由 argparse 退 2。
"""
from __future__ import annotations

from pathlib import Path

import pytest

from gherkai_cli import __main__ as m
from gherkai_cli import skill_install

# 包内那份 skill 的真身（安装的源）。定位与被测 code 一样只有这一条路：包目录下 skills/gherkai，无仓库根回落。
SRC = Path(m.__file__).resolve().parent / "skills" / "gherkai"
CLAUDE_SKILLS = Path(".claude") / "skills" / "gherkai"
CODEX_SKILLS = Path(".agents") / "skills" / "gherkai"


def _tree(root: Path) -> dict[str, bytes]:
    """{相对路径: 字节}（排除 __pycache__ / *.pyc，与拷贝侧同口径）。"""
    return {
        str(p.relative_to(root)): p.read_bytes()
        for p in sorted(root.rglob("*"))
        if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"
    }


def test_source_tree_is_locatable():
    # 扫描面为空即红：包内 skill 搬家 / 打包漏掉时，下面每条断言都会退化成空集比空集。
    assert (SRC / "SKILL.md").is_file(), f"包内没找到 skill 源：{SRC}"


def test_fresh_install_writes_packaged_tree_plus_marker(tmp_path, capsys):
    rc = m.main(["skill", "install", "--dir", str(tmp_path)])
    assert rc == 0
    dst = tmp_path / CLAUDE_SKILLS
    installed = _tree(dst)
    marker = installed.pop(skill_install.MARKER_NAME)
    assert installed == _tree(SRC)          # 装完 = 包内那份逐字节
    assert marker.decode("utf-8").strip() == (m._installed_version() or skill_install.UNKNOWN_VERSION)
    out, err = capsys.readouterr()
    assert out == ""                        # stdout 只属 --print
    assert str(dst) in err                  # 落点提示走 stderr


def test_print_outputs_packaged_skill_md_exactly(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    rc = m.main(["skill", "install", "--print"])
    assert rc == 0
    assert capsys.readouterr().out == (SRC / "SKILL.md").read_text(encoding="utf-8")
    assert not (tmp_path / ".claude").exists()   # --print 只打印、不装


def test_reinstall_converges_and_drops_stale_files(tmp_path):
    assert m.main(["skill", "install", "--dir", str(tmp_path)]) == 0
    dst = tmp_path / CLAUDE_SKILLS
    (dst / "references" / "stale.md").write_text("上一版多出来的 reference", encoding="utf-8")
    (dst / "leftover").mkdir()
    (dst / "leftover" / "junk.md").write_text("x", encoding="utf-8")

    assert m.main(["skill", "install", "--dir", str(tmp_path)]) == 0
    installed = _tree(dst)
    assert skill_install.MARKER_NAME in installed
    installed.pop(skill_install.MARKER_NAME)
    assert installed == _tree(SRC)               # 整目录收敛：旧 reference 不留
    assert not (dst / "leftover").exists()


def test_empty_target_dir_is_accepted(tmp_path):
    dst = tmp_path / CLAUDE_SKILLS
    dst.mkdir(parents=True)
    assert m.main(["skill", "install", "--dir", str(tmp_path)]) == 0
    assert (dst / "SKILL.md").is_file()


def test_refuses_target_that_is_not_ours(tmp_path, capsys):
    dst = tmp_path / CLAUDE_SKILLS
    dst.mkdir(parents=True)
    (dst / "mine.md").write_text("用户自己的东西", encoding="utf-8")

    rc = m.main(["skill", "install", "--dir", str(tmp_path)])
    assert rc == 2
    assert (dst / "mine.md").read_text(encoding="utf-8") == "用户自己的东西"   # 一个字节都没动
    assert not (dst / skill_install.MARKER_NAME).exists()
    err = capsys.readouterr().err
    assert str(dst) in err and "挪走" in err


def test_agent_all_refuses_before_touching_the_other_location(tmp_path):
    # 两处目标只要一处不认，两处都不装（半装态更难收拾）
    foreign = tmp_path / CODEX_SKILLS
    foreign.mkdir(parents=True)
    (foreign / "mine.md").write_text("x", encoding="utf-8")

    assert m.main(["skill", "install", "--dir", str(tmp_path), "--agent", "all"]) == 2
    assert not (tmp_path / ".claude").exists()
    assert _tree(foreign) == {"mine.md": b"x"}


def test_agent_all_writes_both_locations(tmp_path):
    assert m.main(["skill", "install", "--dir", str(tmp_path), "--agent", "all"]) == 0
    for rel in (CLAUDE_SKILLS, CODEX_SKILLS):
        dst = tmp_path / rel
        assert (dst / "SKILL.md").is_file()
        assert (dst / skill_install.MARKER_NAME).is_file()


def test_agent_codex_writes_agents_skills_only(tmp_path):
    assert m.main(["skill", "install", "--dir", str(tmp_path), "--agent", "codex"]) == 0
    assert (tmp_path / CODEX_SKILLS / "SKILL.md").is_file()
    assert not (tmp_path / ".claude").exists()


def test_global_installs_under_home(tmp_path, monkeypatch):
    home, proj = tmp_path / "home", tmp_path / "proj"
    home.mkdir()
    proj.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.chdir(proj)

    assert m.main(["skill", "install", "--global", "--agent", "all"]) == 0
    assert (home / CLAUDE_SKILLS / "SKILL.md").is_file()
    assert (home / CODEX_SKILLS / "SKILL.md").is_file()
    assert list(proj.iterdir()) == []        # 用户级安装不往项目里写东西


def test_pointer_yes_appends_exactly_once_across_two_runs(tmp_path):
    for _ in range(2):
        assert m.main(["skill", "install", "--dir", str(tmp_path), "--pointer", "yes"]) == 0
    text = (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")    # 文件不存在时会建出来
    assert text.count(skill_install.POINTER_LINE) == 1
    assert not (tmp_path / "AGENTS.md").exists()


def test_pointer_yes_for_codex_appends_to_agents_md_keeping_existing(tmp_path):
    (tmp_path / "AGENTS.md").write_text("# 项目约定\n已有内容\n", encoding="utf-8")
    assert m.main(["skill", "install", "--dir", str(tmp_path), "--agent", "codex", "--pointer", "yes"]) == 0
    text = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert text.startswith("# 项目约定\n已有内容\n")
    assert text.count(skill_install.POINTER_LINE) == 1
    assert not (tmp_path / "CLAUDE.md").exists()


def test_pointer_no_leaves_instruction_file_alone(tmp_path, capsys):
    (tmp_path / "CLAUDE.md").write_text("原样\n", encoding="utf-8")
    assert m.main(["skill", "install", "--dir", str(tmp_path), "--pointer", "no"]) == 0
    assert (tmp_path / "CLAUDE.md").read_text(encoding="utf-8") == "原样\n"
    assert skill_install.POINTER_LINE in capsys.readouterr().err   # 只打印那一行让人自己贴


def test_non_tty_default_does_not_touch_pointer_file(tmp_path):
    # 缺 --pointer 且非交互（pytest 下 stdin 非 tty）→ 缺省否：不问、不写
    assert m.main(["skill", "install", "--dir", str(tmp_path)]) == 0
    assert not (tmp_path / "CLAUDE.md").exists()


class _Tty:
    """假交互 stdin（只需 isatty；答案由 monkeypatch 的 input 给）。"""

    def isatty(self) -> bool:
        return True


@pytest.mark.parametrize("reply, appended", [("y", True), ("Y", True), ("yes", True), ("", False), ("n", False)])
def test_tty_asks_once_and_honours_the_answer(tmp_path, monkeypatch, reply, appended):
    monkeypatch.setattr(skill_install.sys, "stdin", _Tty())
    calls: list[str] = []
    monkeypatch.setattr("builtins.input", lambda *a: (calls.append(reply), reply)[1])

    assert m.main(["skill", "install", "--dir", str(tmp_path), "--agent", "all"]) == 0
    assert len(calls) == 1                   # 只问一次（--agent all 也只问一次）
    for name in ("CLAUDE.md", "AGENTS.md"):
        assert (tmp_path / name).is_file() is appended
        if appended:
            assert (tmp_path / name).read_text(encoding="utf-8").count(skill_install.POINTER_LINE) == 1


def test_unknown_version_writes_the_unknown_token(tmp_path, monkeypatch):
    # 源码直跑（未装成包）：标记记「版本未知」、安装照常完成；--version 显示用的占位串不许进标记
    monkeypatch.setattr(m, "_installed_version", lambda: None)
    assert m.main(["skill", "install", "--dir", str(tmp_path)]) == 0
    dst = tmp_path / CLAUDE_SKILLS
    marker = (dst / skill_install.MARKER_NAME).read_text(encoding="utf-8").strip()
    assert marker == skill_install.UNKNOWN_VERSION == "版本未知"
    assert "unknown" not in marker
    assert (dst / "SKILL.md").is_file()      # 不拒装


def test_missing_dir_is_refused(tmp_path, capsys):
    rc = m.main(["skill", "install", "--dir", str(tmp_path / "nope")])
    assert rc == 2
    assert not (tmp_path / "nope").exists()  # 打错 --dir 不凭空造出一棵树
    assert "--dir" in capsys.readouterr().err


def test_dir_and_global_are_mutually_exclusive(tmp_path):
    with pytest.raises(SystemExit) as e:
        m.main(["skill", "install", "--dir", str(tmp_path), "--global"])
    assert e.value.code == 2


def test_bare_skill_exits_2():
    # 子动词必填：裸 `gherkai skill` 由 argparse 报错退 2
    with pytest.raises(SystemExit) as e:
        m.main(["skill"])
    assert e.value.code == 2


def test_write_failure_stays_inside_the_exit_code_set(tmp_path, capsys):
    # 落盘失败（这里：.claude 位上是个文件）也只许退 2，不许抛栈给使用者
    (tmp_path / ".claude").write_text("这是个文件、不是目录", encoding="utf-8")
    assert m.main(["skill", "install", "--dir", str(tmp_path)]) == 2
    assert "装不进去" in capsys.readouterr().err


def test_non_utf8_pointer_file_stays_inside_the_exit_code_set(tmp_path, capsys):
    # 使用方的 CLAUDE.md 不是 UTF-8（中文环境用 GBK 的编辑器存出来的）：读侧同样只许退 2、不许抛栈
    claude_md = tmp_path / "CLAUDE.md"
    before = "中文\n".encode("gb18030")
    claude_md.write_bytes(before)
    assert m.main(["skill", "install", "--dir", str(tmp_path), "--pointer", "yes"]) == 2
    err = capsys.readouterr().err
    assert "这一行请自己贴" in err and "不是 UTF-8 编码" in err  # 说真因（编码），不误导去查写权限
    # 宁可不写也不写坏：读不了就一个字节都别动（errors="replace" 那种写法会把用户文件的非 UTF-8 段落毁掉）
    assert claude_md.read_bytes() == before
