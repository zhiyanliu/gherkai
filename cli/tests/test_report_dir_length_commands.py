"""报告目录路径长度的入口检查在命令行一侧的测试（ADR 0030 决定四「报告目录的路径长度」条）：凡用本机报告目录的命令在第一次访问报告
目录之前检查，不过即以一句说明、退出码 2 结束，什么都不建；云端后端与 `run --no-report` 不查。判据与上限的推导在 runtime 的 compose，
它的用例在 runtime/tests；这里核六个命令都经同一处检查、同一句说明，以及恰在上限上的报告目录真的能用（事件库真实建成、报告写成）。

路径都建在真实文件系统上（系统临时目录之下），长度按解析之后的绝对路径、按文件系统编码计。超长那一次用真实进程执行六个命令：说明、
退出码与「什么都没建、没有回溯」都是进程对外的表现。"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

import gherkai_cli.__main__ as m

from test_main import _fake_schedule_factory, _write_feature
from test_tunnel_cli import _isolated_child_env

LIMIT = 470  # ADR 0030 决定四「报告目录的路径长度」条的现值
HOW = "请换一个路径较短的报告目录（--report-dir 选项，或配置文件里的 report-dir）。"


def _path_of(base: Path, total: int) -> Path:
    """base 之下一条解析之后恰好 total 字节的路径（各层是 ASCII、每层不超过 200 字节），一层都不建。"""
    path = base.resolve()
    while (rest := total - len(os.fsencode(str(path)))) > 201:
        path = path / ("d" * 150)
    assert rest >= 2, rest
    path = path / ("e" * (rest - 1))
    assert len(os.fsencode(str(path))) == total
    return path


def _too_long(path: Path, total: int) -> str:
    return (f"报告目录 {path} 的路径太长（解析之后共 {total} 字节）：本机后端只使用路径不超过 {LIMIT} 字节的报告目录，每个 run 的记录、"
            f"事件库与产物都放在它下面，路径再长就建不出或打不开。{HOW}")


def _everything_under(root: Path) -> list[str]:
    return sorted(str(p.relative_to(root)) for p in root.rglob("*"))


def _six_commands(feature: Path, report_dir: Path) -> dict[str, list[str]]:
    rid = "20300101T000000Z-aaaaaa"
    loc = ["--report-dir", str(report_dir)]
    return {"run": ["run", str(feature), *loc], "submit": ["submit", str(feature), *loc], "status": ["status", rid, *loc],
            "explain": ["explain", rid, *loc], "list-runs": ["list-runs", *loc], "settle-runs": ["settle-runs", *loc]}


def test_six_commands_refuse_a_report_dir_one_byte_over_the_limit_in_real_processes(tmp_path):
    """真实进程：报告目录解析之后 471 字节时，run、submit、status、explain、list-runs、settle-runs 都以退出码 2 与同一句结束，标准输出
    为空、没有回溯，什么目录都没建；run 与 submit 在前置检查里就停下，没有输出「plan:」那一行之后的任何进度。"""
    work = tmp_path / "work"
    work.mkdir()
    feature = _write_feature(work)
    report_dir = _path_of(tmp_path / "long", LIMIT + 1)
    env = _isolated_child_env(work)
    before = _everything_under(tmp_path)
    for name, argv in _six_commands(feature, report_dir).items():
        proc = subprocess.run([sys.executable, "-P", "-m", "gherkai_cli", *argv], cwd=work, env=env, stdin=subprocess.DEVNULL,
                              capture_output=True, text=True, timeout=120)
        assert (proc.returncode, proc.stdout) == (2, ""), (name, proc.stderr)
        assert "Traceback" not in proc.stderr and "plan:" not in proc.stderr, (name, proc.stderr)
        assert proc.stderr.splitlines()[-1] == _too_long(report_dir, LIMIT + 1), name
        assert _everything_under(tmp_path) == before, name
    assert not (tmp_path / "long").exists()


@pytest.mark.parametrize("under", ["existing", "missing"])
@pytest.mark.parametrize("command", ["run", "submit", "status", "explain", "list-runs", "settle-runs"])
def test_a_name_too_long_for_the_filesystem_is_refused(command, under, tmp_path, capsys):
    """路径总长没有超过上限，但其中一层名字（256 个 ASCII 字符）文件系统不接受：紧接在已存在的目录之下（打开整条路径即得到「名字太长」，
    run 与 submit 先查长度、再做边界检查，所以不会被报成写记录失败），或在一层还不存在的上级之下（打开整条路径只得到「不存在」）。六个
    命令都以说明这一层名字太长的那一句、退出码 2 结束，什么都不建。"""
    work = tmp_path / "work"
    work.mkdir()
    name = "n" * 256
    report_dir = ((tmp_path / "missing") if under == "missing" else tmp_path).resolve() / name / "reports"
    assert len(os.fsencode(str(report_dir))) <= LIMIT
    with pytest.raises(OSError):  # 前提：这个文件系统确实不接受这样长的一层名字
        os.mkdir(tmp_path / name)
    rc = m.main(_six_commands(_write_feature(work), report_dir)[command])
    cap = capsys.readouterr()
    assert (rc, cap.out) == (2, "")
    assert cap.err.splitlines()[-1] == (f"报告目录 {report_dir} 的路径里有一层名字太长（{name}）：所在的文件系统不接受这样长的名字，"
                                        f"这个报告目录建不出来。{HOW}")
    assert sorted(os.listdir(tmp_path)) == ["work"]


@pytest.mark.skipif(sys.platform != "darwin", reason="APFS 按 UTF-16 代码单元计一层名字的长度；Linux 的 ext4 按字节计、会拒绝它")
def test_a_layer_of_one_hundred_hanzi_passes_on_apfs(tmp_path, capsys):
    """一层 100 个汉字（300 字节）的名字：APFS 接受，所以长度检查放行，status 照常往下走、说未找到 run（报告目录不存在）。"""
    report_dir = (tmp_path / ("汉" * 100) / "reports").resolve()
    rc = m.main(["status", "20300101T000000Z-aaaaaa", "--report-dir", str(report_dir)])
    assert rc == 2 and capsys.readouterr().err.startswith("未找到 run：")


def test_a_report_dir_exactly_at_the_limit_works_end_to_end(tmp_path, monkeypatch, capsys):
    """报告目录解析之后恰好 470 字节：run 照常建 run，事件库（SQLite）真实建成、报告写成，status 与 list-runs 读得到它。"""
    monkeypatch.setattr(m, "schedule", _fake_schedule_factory())
    report_dir = _path_of(tmp_path / "long", LIMIT)
    assert m.main(["run", str(_write_feature(tmp_path)), "--report-dir", str(report_dir)]) == 0
    [run_id] = [n for n in os.listdir(report_dir) if not n.startswith(".")]
    assert (report_dir / run_id / "events.db").is_file() and (report_dir / run_id / "index.html").is_file()
    assert len(os.fsencode(str(report_dir / run_id / "events.db"))) == LIMIT + 34
    capsys.readouterr()
    assert m.main(["status", run_id, "--report-dir", str(report_dir)]) == 0
    assert m.main(["list-runs", "--report-dir", str(report_dir)]) == 0


def test_cloud_backend_and_no_report_are_not_checked(tmp_path, monkeypatch, capsys):
    """云端后端（报告落点是键前缀）与 run --no-report 不查：同一个超长的值下，前者照常走到云端那一侧（这里是 settle-runs 对云端后端的
    那一句），后者照常执行完。"""
    monkeypatch.setattr(m, "schedule", _fake_schedule_factory())
    long = _path_of(tmp_path / "long", LIMIT + 1)
    assert m.main(["run", str(_write_feature(tmp_path)), "--report-dir", str(long), "--no-report"]) == 0
    assert "路径太长" not in capsys.readouterr().err
    assert m.main(["settle-runs", "--backend", "cloud", "--report-dir", str(long)]) == 2
    assert capsys.readouterr().err.splitlines() == [
        "这个版本的 gherkai settle-runs 只处理本机后端（--backend local）的 run，还不能处理云端后端的 run。"]
    assert not (tmp_path / "long").exists()
