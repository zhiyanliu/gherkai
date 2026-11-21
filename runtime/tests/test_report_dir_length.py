"""本机后端报告目录的路径长度（`compose.report_dir_too_long`，ADR 0030 决定四「报告目录的路径长度」条）。

上限由推导算出、两条判据的回答来自真实的内核与真实的 SQLite，都是 mock 之外的行为（绿≠对），所以用例在真实文件系统上构造真实的
超长路径：总长恰在上限上的报告目录之下真的建出一个完整的 run（事件库、判定明细、结束写与报告都写成），产品构造的各条路径都在内核
的整条路径上限之内；超长一字节、某一层名字太长（在已存在的上级之下、在还不存在的上级之下）都被拒；检查本身什么都不建。
"""
from __future__ import annotations

import errno
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

from gherkai_core.adapters.event_log.sqlite import DB_PATH_MAX_BYTES, SqliteEventLog
from gherkai_core.adapters.run_store.local import LocalRunStore
from gherkai_core.model import Job, JobResult, JobState, RunMeta, Scenario, Status, Step
from gherkai_core.named_details import new_result_id
from gherkai_core.persist import initial_run_state
from gherkai_runtime import compose, settle


def _path_of(base: Path, total: int) -> Path:
    """base（解析之后）之下按文件系统编码恰好 total 字节的路径，各层名字不超过 200 字节；不建任何目录。"""
    base = base.resolve()
    left = total - len(os.fsencode(str(base)))
    assert left >= 2, left
    parts = []
    while left > 0:
        n = min(200, left - 1)
        if left - (n + 1) == 1:  # 剩一个字节拼不出「/」加一个字符
            n -= 1
        parts.append("d" * n)
        left -= n + 1
    path = base.joinpath(*parts)
    assert len(os.fsencode(str(path))) == total
    return path


def _tree(root: Path) -> list[str]:
    return sorted(str(p.relative_to(root)) for p in root.rglob("*"))


def test_the_limit_is_the_events_db_path_limit_less_what_the_product_appends():
    """上限现值 470 字节（ADR 0030 决定四）：总长恰是上限的报告目录之下，产品为新生成的 run 构造的事件库路径恰是 SQLite 按缺省构建时
    的库文件路径上限。run 标识的形态或事件库的文件名变了，这里与上限一起变。"""
    assert compose.REPORT_DIR_MAX_BYTES == 470
    report_dir = "/" + "r" * (compose.REPORT_DIR_MAX_BYTES - 1)
    db = compose.events_db_path(report_dir, compose.new_run_id())
    assert len(os.fsencode(str(db))) == DB_PATH_MAX_BYTES


def test_a_whole_run_fits_under_a_report_dir_of_exactly_the_limit(tmp_path, monkeypatch, lock_holder):
    """总长恰是上限的报告目录通过检查，在它之下照生产的各个入口建 run、写事件库（库文件路径恰是 SQLite 的上限）、存判定明细、处置
    （结束写）并生成报告，都写成。原子写的临时文件里最长的是判定明细的那一个，比报告目录长 64 字节，加上它仍在内核的整条路径上限之内。"""
    root = _path_of(tmp_path, compose.REPORT_DIR_MAX_BYTES)
    assert compose.report_dir_too_long(root) is None
    temps: list[str] = []
    real_replace = os.replace

    def replace(src, dst, **kw):
        temps.append(os.fsdecode(src))
        return real_replace(src, dst, **kw)

    monkeypatch.setattr(os, "replace", replace)
    run_id = compose.new_run_id(datetime(2026, 11, 21, tzinfo=timezone.utc))
    job_a, job_b = (Job(scope_id=s, scope_name=s, engine="midscene", timeout_s=300.0,
                        scenarios=(Scenario(id=f"{s}:1", name="sc", steps=(Step(0, "Given", "x"),)),)) for s in "ab")
    meta = RunMeta(run_id=run_id, created_at="2026-11-21T00:00:00+00:00", jobs=(job_a, job_b),
                   deadline_at="2999-01-01T00:00:00+00:00")
    store = LocalRunStore(root, lock_holder=lock_holder)
    store.create_run(meta, initial_run_state(meta, started_at=meta.created_at))
    assert store.try_claim_job(run_id, "a", claimed_at=meta.created_at) is True

    db_path = compose.events_db_path(root, run_id)
    assert len(os.fsencode(str(db_path))) == DB_PATH_MAX_BYTES
    log = SqliteEventLog(db_path)
    log.append_event("a", 1, '{"type":"scope_started","scopeId":"a","sessionId":"s"}', 1.0)
    log.record_exit("a", 0)
    assert [r.kind for r in log.records()] == ["event", "exit"]

    result_id = new_result_id()
    compose.local_result_store(root).save_job_result(run_id, result_id, JobResult(job=job_a, status=Status.PASSED))
    store.commit_job_states(run_id, [JobState("a", Status.PASSED, result_id=result_id)], ended_at=meta.created_at)
    lock_holder.close_all()
    r = settle.settle_run(settle.local_target(root), run_id, clock=compose.now, dry_run=False)
    assert (r.outcome, r.report_written) == (settle.Outcome.SETTLED, True)
    assert (root / run_id / "index.html").is_file()

    lengths = {t: len(os.fsencode(t)) - len(os.fsencode(str(root))) for t in temps}
    longest = max(lengths, key=lengths.get)
    assert Path(longest).parent == root / run_id / "jobs" and lengths[longest] == 64, lengths
    assert compose.REPORT_DIR_MAX_BYTES + lengths[longest] < os.pathconf(root, "PC_PATH_MAX")


def test_one_byte_more_than_the_limit_is_rejected_and_nothing_is_created(tmp_path):
    """超出上限一字节即拒绝，带实际字节数与上限；上限上的那一个通过。只看字符串，什么都不建。"""
    at_limit = _path_of(tmp_path, compose.REPORT_DIR_MAX_BYTES)
    over = _path_of(tmp_path, compose.REPORT_DIR_MAX_BYTES + 1)
    assert compose.report_dir_too_long(at_limit) is None
    assert compose.report_dir_too_long(over) == compose.ReportDirPathTooLong(
        path=str(over), total_bytes=471, limit_bytes=470)
    assert _tree(tmp_path) == []


def test_a_name_too_long_right_under_an_existing_dir_is_rejected(tmp_path):
    """已存在的上级之下紧接着一层超长的名字：打开整条路径得到的就是「名字太长」，检查向上越过它找到已存在的上级，再问这一层，给出
    这一层的名字。什么都不建。"""
    long = "n" * 256
    report_dir = tmp_path.resolve() / long / "reports"
    assert len(os.fsencode(str(report_dir))) <= compose.REPORT_DIR_MAX_BYTES
    with pytest.raises(OSError) as e:
        os.open(report_dir, os.O_RDONLY | os.O_DIRECTORY)
    assert e.value.errno == errno.ENAMETOOLONG  # 前提：内核在这一层就答「名字太长」
    assert compose.report_dir_too_long(report_dir) == compose.ReportDirNameTooLong(path=str(report_dir), name=long)
    assert _tree(tmp_path) == []


def test_a_name_too_long_under_a_parent_that_does_not_exist_yet_is_rejected(tmp_path):
    """超长的一层在一层还不存在的上级之下：打开整条路径只得到「不存在」（内核在第一层不存在的名字处就停下，看不到后面那一层），检查
    对已存在的上级之下每一层还不存在的名字各问一次，问出超长的那一层。什么都不建。"""
    long = "n" * 256
    report_dir = tmp_path.resolve() / "missing" / long / "reports"
    assert len(os.fsencode(str(report_dir))) <= compose.REPORT_DIR_MAX_BYTES
    with pytest.raises(FileNotFoundError):  # 前提：只打开整条路径查不出
        os.open(report_dir, os.O_RDONLY | os.O_DIRECTORY)
    assert compose.report_dir_too_long(report_dir) == compose.ReportDirNameTooLong(path=str(report_dir), name=long)
    assert _tree(tmp_path) == []


def test_an_unrelated_symlink_of_the_same_name_under_the_existing_parent_does_not_mislead(tmp_path):
    """已存在的上级之下恰好有一个与报告目录某一层同名的符号链接，指向超长的名字；报告目录本身不经过它（那一层在一层还不存在的上级
    之下）。查的是这一层名字本身、不跟随链接：这个名字可用，检查放行。跟随的话得到的「名字太长」说的是链接的目标。"""
    base = tmp_path.resolve()
    os.symlink("x" * 256, base / "alias")
    with pytest.raises(OSError) as e:
        os.open(base / "alias", os.O_RDONLY | os.O_DIRECTORY)
    assert e.value.errno == errno.ENAMETOOLONG  # 前提：跟随这个链接得到的是「名字太长」
    report_dir = base / "missing" / "alias" / "reports"
    assert compose.report_dir_too_long(report_dir) is None
    assert _tree(tmp_path) == ["alias"]


def test_a_level_of_one_hundred_chinese_characters_is_answered_by_the_filesystem(tmp_path):
    """一层 100 个汉字（300 字节）：每一层不另定字节数，由文件系统回答。macOS 的 APFS 按 UTF-16 代码单元计、放行；Linux 清单里的类型
    按字节计、以 255 为限，拒绝。"""
    name = "汉" * 100
    report_dir = tmp_path.resolve() / name
    if sys.platform == "darwin":
        assert compose.report_dir_too_long(report_dir) is None
        report_dir.mkdir()  # 放行的确实建得出
    elif sys.platform.startswith("linux"):
        assert compose.report_dir_too_long(report_dir) == compose.ReportDirNameTooLong(path=str(report_dir), name=name)
    else:
        pytest.skip(f"本机后端在 {sys.platform} 上不可用")


def test_an_existing_report_dir_and_short_new_levels_pass(tmp_path):
    assert compose.report_dir_too_long(tmp_path.resolve()) is None
    assert compose.report_dir_too_long(tmp_path.resolve() / "a" / "b" / "c") is None
    assert _tree(tmp_path) == []


@pytest.mark.skipif(hasattr(os, "geteuid") and os.geteuid() == 0, reason="root 不受目录权限限制")
def test_failures_other_than_length_are_left_to_the_later_steps(tmp_path):
    """向上找已存在的上级时遇到长度之外的打开失败（路径上有文件、没有权限）：这一项不判断，返回通过，由随后的各步按各自的说法报出；
    后面即便有超长的一层也不在这里报。什么都不建。"""
    base = tmp_path.resolve()
    (base / "file").write_text("x", encoding="utf-8")
    closed = base / "closed"
    closed.mkdir()
    os.chmod(closed, 0)
    try:
        assert compose.report_dir_too_long(base / "file" / ("n" * 256)) is None
        assert compose.report_dir_too_long(closed / "x" / ("n" * 256)) is None
    finally:
        os.chmod(closed, 0o700)
    assert _tree(tmp_path) == ["closed", "file"]
