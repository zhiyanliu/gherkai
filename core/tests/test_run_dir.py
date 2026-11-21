"""本机 run 目录：边界检查、生命期锁、建 run 的暂存与改名、处置方的试拿、清理暂存目录（`adapters/run_store/run_dir`；ADR 0030
决定四，ADR 0054 决策三、四）。

断言落在真实的文件系统与内核上：报告目录里有哪些名字、文件的字节、是不是同一个 inode、另开一次（或另一个进程）取锁得到什么。故障
注入只换边界上的原语（`os.mkdir`、`os.open`、`os.replace`、`os.fstat`、`os.unlink`、`fcntl.flock`、取文件系统类型的那一步），被换的
原语照样真实执行，或以同步的系统错误失败，或在那一刻停住、让另一方先走；模拟清理方或别的进程插进来时做的也是真实动作（真的删
目录、换目录、另开一次取锁）。清理方与创建者的各种交错用真实的创建者进程（生产的 `create_run_dir`，在第一个暂存目录的指定几步
停下）固定先后。建 run 的那一次调用不被异步的异常打断（前台 run 在建 run 之前已装上只记标志的中断处理器，后台推进进程对 SIGINT
取缺省处置），那一侧的用例在 cli 的测试里。

生产用的持有者 `HoldUntilExit` 收下描述符时登记 fork 钩子，登记之后在进程里撤不掉：用到它的用例都在子进程里执行，测试进程里只用
conftest 的测试持有者。

边界检查取文件系统类型的那一步由 conftest 换成本平台清单的第一项，结论不依赖宿主的文件系统；带 `real_filesystem` 标记的用例
用宿主真实的类型，起真实进程的用例都带这个标记（子进程里没有替换）。
"""
from __future__ import annotations

import contextlib
import errno
import fcntl
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest

from gherkai_core.adapters.run_store import run_dir
from gherkai_core.adapters.run_store.local import LocalRunStore
from gherkai_core.adapters.run_store.run_dir import Boundary, LockState
from gherkai_core.errors import RunAlreadyExists
from gherkai_core.model import Job, JobState, RunMeta, RunState, Scenario, Status, Step

# conftest 的自动替身在用例开始时才换上，导入时取到的是真实的取法
_REAL_FILESYSTEM_TYPE = run_dir.filesystem_type
_ALLOWED = run_dir.ALLOWED_FILESYSTEMS.get(sys.platform, ())
_TIMEOUT_S = 30


def _meta(run_id: str, scope_ids=("a",), created_at: str = "2026-11-21T00:00:00Z") -> RunMeta:
    jobs = tuple(Job(scope_id=s, scope_name=s, engine="midscene", timeout_s=300.0,
                     scenarios=(Scenario(id=f"{s}:1", name="sc", steps=(Step(0, "Given", "x"),)),)) for s in scope_ids)
    return RunMeta(run_id=run_id, created_at=created_at, jobs=jobs, deadline_at="2026-11-21T01:00:00+00:00")


def _pending(run_id: str, scope_ids=("a",)) -> RunState:
    return RunState(run_id=run_id, status=Status.PENDING, started_at="2026-11-21T00:00:00Z",
                    jobs={s: JobState(s, Status.PENDING) for s in scope_ids})


def _try(path: Path) -> LockState:
    """另开一次 path、不阻塞地取排他锁，随即关闭（拿到的锁随之放开）。"""
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        return run_dir.try_lock(fd).state
    finally:
        os.close(fd)


def _staging_names(root: Path) -> list[str]:
    return sorted(n for n in os.listdir(root) if n.startswith(run_dir.STAGING_PREFIX))


def _tree(path: Path) -> dict[str, object]:
    """path 之下每个名字（相对路径）及其内容：文件记字节，符号链接记它指向的路径，目录记为 None。"""
    out: dict[str, object] = {}
    for p in sorted(path.rglob("*")):
        key = str(p.relative_to(path))
        if p.is_symlink():
            out[key] = ("symlink", os.readlink(p))
        else:
            out[key] = None if p.is_dir() else p.read_bytes()
    return out


def _same_inode(fd: int, path: Path) -> bool:
    a, b = os.fstat(fd), os.stat(path)
    return (a.st_dev, a.st_ino) == (b.st_dev, b.st_ino)


# ============================================================================
# 名字规则
# ============================================================================


@pytest.mark.parametrize("name, ok", [
    ("20260629T141207Z-a3f9c1", True), ("run-1", True), ("r", True),
    ("", False), (".x", False), (".gherkai-creating-0123456789abcdef", False), ("..", False), ("a/b", False),
    # 长度按文件系统编码的字节数计，上限 255：多字节的字符按编码之后的长度算
    ("a" * 255, True), ("a" * 256, False), ("a" * 300, False), ("é" * 127, True), ("é" * 128, False),
    ("a\ud800", False),  # 按文件系统编码编不出来：不是 run 标识，也不抛编码错误
])
def test_is_run_name(name, ok):
    assert run_dir.is_run_name(name) is ok


@pytest.mark.parametrize("name, ok", [
    (".gherkai-creating-0123456789abcdef", True), (".gherkai-creating-ffffffffffffffff", True),
    (".gherkai-creating-user-named", False),        # 使用者恰好以前缀起名的目录
    (".gherkai-creating-0123456789ABCDEF", False),  # 大写不是生成的形态
    (".gherkai-creating-0123456789abcde", False), (".gherkai-creating-0123456789abcdef0", False),  # 15、17 位
    (".gherkai-creating-0123456789abcdeg", False), (".gherkai-creating-", False),
    (".gherkai-creating-0123456789abcdef\n", False), ("x.gherkai-creating-0123456789abcdef", False),
    ("0123456789abcdef", False), ("r", False), (".hidden", False),
    (".gherkai-creating-٠١٢٣٤٥٦٧٨٩abcdef", False),  # 别的文字里的数字不是十六进制
])
def test_is_staging_name_accepts_only_the_generated_shape(name, ok):
    assert run_dir.is_staging_name(name) is ok


def test_every_generated_staging_name_has_the_recognized_shape():
    """建 run 的一方生成的名字都合清理方认的形态（同一处定义），也都不是 run 标识（列举与按标识的读写不认它们）。"""
    names = {run_dir.staging_name() for _ in range(2000)}
    assert len(names) == 2000
    assert all(run_dir.is_staging_name(n) and not run_dir.is_run_name(n) for n in names)
    assert {len(n) for n in names} == {len(run_dir.STAGING_PREFIX) + run_dir.STAGING_TAIL_HEX}


# ============================================================================
# 边界检查
# ============================================================================


@pytest.mark.parametrize("fs_type", _ALLOWED)
def test_check_fd_lets_through_every_listed_type(tmp_path, monkeypatch, fs_type):
    monkeypatch.setattr(run_dir, "filesystem_type", lambda fd: fs_type)
    fd = os.open(tmp_path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        check = run_dir.check_fd(fd, requested="/r", checked="/c")
    finally:
        os.close(fd)
    assert check == run_dir.BoundaryCheck(Boundary.INSIDE, "/r", "/c", fs_type, None)


@pytest.mark.parametrize("fs_type", ["nfs4", "nfs", "fuse.sshfs", "msdos", "hfs", "autofs", "fakeowner", "devfs", "APFS"])
def test_check_fd_rejects_types_outside_the_list(tmp_path, monkeypatch, fs_type):
    if not _ALLOWED:
        pytest.skip("这个平台没有清单")
    monkeypatch.setattr(run_dir, "filesystem_type", lambda fd: fs_type)
    fd = os.open(tmp_path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        check = run_dir.check_fd(fd, requested="/r", checked="/c")
    finally:
        os.close(fd)
    assert check == run_dir.BoundaryCheck(Boundary.OUTSIDE, "/r", "/c", fs_type, None)


def test_check_fd_is_unknown_with_the_reason_when_the_type_cannot_be_read(tmp_path, monkeypatch):
    if not _ALLOWED:
        pytest.skip("这个平台没有清单")

    def unknown(fd):
        raise run_dir.FilesystemUnknown("读不到挂载信息：No such file or directory")

    monkeypatch.setattr(run_dir, "filesystem_type", unknown)
    fd = os.open(tmp_path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        check = run_dir.check_fd(fd, requested="/r", checked="/c")
    finally:
        os.close(fd)
    assert check == run_dir.BoundaryCheck(Boundary.UNKNOWN, "/r", "/c", None, "读不到挂载信息：No such file or directory")


def test_other_platforms_cannot_be_judged(tmp_path, monkeypatch):
    """平台不是 macOS 与 Linux：判断不了。check_fd 不去取类型，真实的取法本身也给出同一个原因。"""
    monkeypatch.setattr(run_dir.sys, "platform", "freebsd14")
    fd = os.open(tmp_path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        check = run_dir.check_fd(fd, requested="/r", checked="/c")
        with pytest.raises(run_dir.FilesystemUnknown) as exc:
            _REAL_FILESYSTEM_TYPE(fd)
    finally:
        os.close(fd)
    assert check == run_dir.BoundaryCheck(Boundary.UNKNOWN, "/r", "/c", None, "这个平台不是 macOS 或 Linux")
    assert str(exc.value) == "这个平台不是 macOS 或 Linux"


def test_check_report_dir_climbs_only_past_missing_levels_and_creates_nothing(tmp_path):
    """不存在的多层路径、悬空的符号链接、悬空链接之下的子路径：向上取最近一层已存在的上级判断；什么都不建。"""
    (tmp_path / "dangling").symlink_to(tmp_path / "nowhere")
    (tmp_path / "exists").mkdir()
    before = _tree(tmp_path)
    for requested in (tmp_path / "a" / "b" / "c", tmp_path / "dangling", tmp_path / "dangling" / "sub",
                      tmp_path / "exists" / "x" / "y"):
        check = run_dir.check_report_dir(requested)
        expected_checked = tmp_path / "exists" if "exists" in requested.parts else tmp_path
        assert (check.verdict, check.requested, check.checked) == (Boundary.INSIDE, str(requested), str(expected_checked))
    check = run_dir.check_report_dir(tmp_path / "exists")
    assert (check.requested, check.checked) == (str(tmp_path / "exists"),) * 2
    assert _tree(tmp_path) == before


@pytest.mark.skipif(hasattr(os, "geteuid") and os.geteuid() == 0, reason="root 无视文件权限")
def test_check_report_dir_raises_other_open_failures_as_they_are(tmp_path):
    """路径上有文件（ENOTDIR）、没有权限（EACCES，含上级没有执行权限）、符号链接成环（ELOOP）：原样抛出，不当作判断不了，也不越过。"""
    (tmp_path / "file").write_text("x", encoding="utf-8")
    (tmp_path / "loop-a").symlink_to(tmp_path / "loop-b")
    (tmp_path / "loop-b").symlink_to(tmp_path / "loop-a")
    unreadable = tmp_path / "unreadable"
    unreadable.mkdir(mode=0o000)
    no_exec = tmp_path / "no-exec"
    (no_exec / "child").mkdir(parents=True)
    no_exec.chmod(0o600)
    try:
        cases = [(tmp_path / "file", errno.ENOTDIR), (tmp_path / "file" / "sub", errno.ENOTDIR),
                 (tmp_path / "loop-a", errno.ELOOP), (tmp_path / "loop-a" / "sub", errno.ELOOP),
                 (unreadable, errno.EACCES), (no_exec / "child", errno.EACCES), (no_exec / "child" / "x", errno.EACCES)]
        for path, code in cases:
            with pytest.raises(OSError) as exc:
                run_dir.check_report_dir(path)
            assert exc.value.errno == code, (path, exc.value)
    finally:
        unreadable.chmod(0o700)
        no_exec.chmod(0o700)


def test_check_existing_dir_judges_the_directory_itself_and_reads_a_missing_one_as_none(tmp_path, monkeypatch):
    """已存在的目录：对它本身判断（不向上找上级），类型不在清单里即 OUTSIDE；不存在（含悬空的符号链接）返回 None、不越过它去判断
    上级；什么都不建。"""
    (tmp_path / "exists").mkdir()
    (tmp_path / "dangling").symlink_to(tmp_path / "nowhere")
    before = _tree(tmp_path)
    check = run_dir.check_existing_dir(tmp_path / "exists")
    assert (check.verdict, check.requested, check.checked) == (Boundary.INSIDE, str(tmp_path / "exists"), str(tmp_path / "exists"))
    assert run_dir.check_existing_dir(tmp_path / "missing" / "deeper") is None
    assert run_dir.check_existing_dir(tmp_path / "dangling") is None
    monkeypatch.setattr(run_dir, "filesystem_type", lambda fd: "nfs4")
    assert run_dir.check_existing_dir(tmp_path / "exists").verdict is Boundary.OUTSIDE
    assert _tree(tmp_path) == before


@pytest.mark.skipif(hasattr(os, "geteuid") and os.geteuid() == 0, reason="root 无视文件权限")
def test_check_existing_dir_raises_other_open_failures_as_they_are(tmp_path):
    """路径上有文件（ENOTDIR）、没有权限（EACCES）：原样抛出，不读作不存在。"""
    (tmp_path / "file").write_text("x", encoding="utf-8")
    unreadable = tmp_path / "unreadable"
    unreadable.mkdir(mode=0o000)
    try:
        for path, code in [(tmp_path / "file", errno.ENOTDIR), (tmp_path / "file" / "sub", errno.ENOTDIR),
                           (unreadable, errno.EACCES)]:
            with pytest.raises(OSError) as exc:
                run_dir.check_existing_dir(path)
            assert exc.value.errno == code, (path, exc.value)
    finally:
        unreadable.chmod(0o700)


# ---- 平台取法 ----

_FDINFO = "pos:\t0\nflags:\t02200000\nmnt_id:\t{}\nino:\t131\n"
# 真实格式的 mountinfo 行：可选字段零到多个，路径里的空格转义为 \040，挂载 ID 互为前缀
_MOUNTINFO = "\n".join([
    "22 28 0:21 / /sys rw,nosuid,nodev,noexec,relatime shared:7 - sysfs sysfs rw",
    "29 1 259:2 / / rw,relatime shared:1 - ext4 /dev/nvme0n1p2 rw,errors=remount-ro",
    "290 29 0:26 / /run/user/1000 rw,nosuid,nodev,relatime shared:2 master:3 - tmpfs tmpfs rw,size=1600000k,mode=700",
    r"45 29 0:40 / /mnt/with\040space rw,relatime - nfs4 server:/export rw,vers=4.2",
    "50 29 0:45 / /home/u/remote rw,nosuid,nodev,relatime shared:30 - fuse.sshfs u@h:/ rw,user_id=1000",
    "61 29 0:50 /x /var/lib/docker/overlay2/l/merged rw,relatime master:9 - overlay overlay rw,lowerdir=/a:/b",
    "70 29 0:55 / /broken rw,relatime shared:4",
    "",
])


@pytest.mark.parametrize("mnt_id, fs_type", [("29", "ext4"), ("290", "tmpfs"), ("45", "nfs4"), ("50", "fuse.sshfs"),
                                             ("61", "overlay"), ("22", "sysfs")])
def test_linux_type_is_the_field_after_the_separator_on_the_line_of_the_mount_id(mnt_id, fs_type):
    assert run_dir._fs_type_from_proc(_FDINFO.format(mnt_id), _MOUNTINFO) == fs_type


@pytest.mark.parametrize("fdinfo, reason", [
    (_FDINFO.format("2"), "挂载信息里找不到这个目录所在的挂载"),     # 只是别的挂载 ID 的前缀
    (_FDINFO.format("999"), "挂载信息里找不到这个目录所在的挂载"),
    ("pos:\t0\nflags:\t02200000\n", "系统返回的文件系统信息不完整"),  # 没有 mnt_id 一行
    (_FDINFO.format("70"), "系统返回的文件系统信息不完整"),            # 那一行没有分隔字段
])
def test_linux_type_cannot_be_judged_without_a_matching_complete_line(fdinfo, reason):
    with pytest.raises(run_dir.FilesystemUnknown) as exc:
        run_dir._fs_type_from_proc(fdinfo, _MOUNTINFO)
    assert str(exc.value) == reason


@pytest.mark.skipif(os.path.exists("/proc/self/mountinfo"), reason="这台机器有 /proc")
def test_linux_reading_without_proc_cannot_be_judged(tmp_path):
    fd = os.open(tmp_path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        with pytest.raises(run_dir.FilesystemUnknown) as exc:
            run_dir._linux_fs_type(fd)
    finally:
        os.close(fd)
    assert str(exc.value).startswith("读不到挂载信息：")


@pytest.mark.skipif(sys.platform != "darwin", reason="只在 macOS 上")
def test_darwin_query_failure_cannot_be_judged():
    """fstatfs 返回失败（已关闭的描述符）：判断不了，原因带系统给的错误文字。"""
    r, w = os.pipe()
    os.close(r)
    os.close(w)
    with pytest.raises(run_dir.FilesystemUnknown) as exc:
        run_dir._darwin_fs_type(r)
    assert str(exc.value) == f"查询文件系统失败：{os.strerror(errno.EBADF)}"


@pytest.mark.skipif(sys.platform != "darwin", reason="只在 macOS 上")
@pytest.mark.parametrize("fstypename, mntonname", [(b"", b"/"), (b"ap\x01fs", b"/"), (b"apfs", b""), (b"apfs", b"Volumes")])
def test_darwin_read_back_that_fails_the_sanity_check_cannot_be_judged(monkeypatch, fstypename, mntonname):
    """读回的类型名不是非空的可打印 ASCII、或挂载点不以 / 开头：判断不了，不会变成放行。"""
    def fake_fstatfs(fd, buf):
        buf._obj.f_fstypename = fstypename
        buf._obj.f_mntonname = mntonname
        return 0

    monkeypatch.setattr(run_dir, "_darwin_fstatfs", lambda: fake_fstatfs)
    with pytest.raises(run_dir.FilesystemUnknown) as exc:
        run_dir._darwin_fs_type(0)
    assert str(exc.value) == "系统返回的文件系统信息不完整"


@pytest.mark.real_filesystem
def test_the_detected_type_matches_an_independent_tool(tmp_path):
    """真实的取法与系统自带工具对同一个目录给出的类型相同：macOS 由 df 取挂载点、mount 取它的类型，Linux 由 findmnt。精简的 Linux
    环境（如容器）可能没有装 findmnt，这时取不到对照值，跳过。"""
    if sys.platform == "linux" and shutil.which("findmnt") is None:
        pytest.skip("这台机器上没有 findmnt（属于 util-linux），取不到对照值")
    fd = os.open(tmp_path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        detected = _REAL_FILESYSTEM_TYPE(fd)
    finally:
        os.close(fd)
    if sys.platform == "darwin":
        df = subprocess.run(["df", "-P", str(tmp_path)], capture_output=True, text=True, check=True, stdin=subprocess.DEVNULL)
        mount_point = df.stdout.splitlines()[1].split(None, 5)[5]
        mounts = subprocess.run(["mount"], capture_output=True, text=True, check=True, stdin=subprocess.DEVNULL).stdout
        types = [m.group(2) for m in re.finditer(r"^.* on (.*) \(([^,)]+)", mounts, re.M) if m.group(1) == mount_point]
        assert types == [detected], (mount_point, types)
    elif sys.platform == "linux":
        out = subprocess.run(["findmnt", "-n", "-o", "FSTYPE", "--target", str(tmp_path)],
                             capture_output=True, text=True, check=True, stdin=subprocess.DEVNULL)
        assert out.stdout.strip() == detected
    else:
        pytest.skip("只核 macOS 与 Linux")


# 两个平台上不用挂载就有的、不在清单里的文件系统：macOS 的 /dev（devfs），Linux 的 /proc（proc）
_PSEUDO_FILESYSTEM = {"darwin": ("/dev", "devfs"), "linux": ("/proc", "proc")}


@pytest.mark.real_filesystem
def test_the_real_detection_rejects_a_pseudo_filesystem_of_the_kernel():
    """真实内核上的拒绝：真实的取法对 macOS 的 /dev 给出 devfs、对 Linux 的 /proc 给出 proc，边界检查判为不在边界之内。取法坏成
    一律给出清单里的类型时，这条变红。"""
    if sys.platform not in _PSEUDO_FILESYSTEM:
        pytest.skip("只核 macOS 与 Linux")
    path, expected = _PSEUDO_FILESYSTEM[sys.platform]
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        assert _REAL_FILESYSTEM_TYPE(fd) == expected
    finally:
        os.close(fd)
    assert run_dir.check_report_dir(Path(path)) == run_dir.BoundaryCheck(Boundary.OUTSIDE, path, path, expected, None)


# ============================================================================
# 生命期锁的原语
# ============================================================================


def test_try_lock_on_real_descriptors(tmp_path):
    """第一次打开取锁成功；同一进程另开一次即「已被持有」；关掉持有的那次打开之后，另一次即可取到。"""
    first = os.open(tmp_path, os.O_RDONLY | os.O_DIRECTORY)
    second = os.open(tmp_path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        assert run_dir.try_lock(first) == run_dir.LockAttempt(LockState.ACQUIRED, None)
        assert run_dir.try_lock(second) == run_dir.LockAttempt(LockState.HELD, None)
        os.close(first)
        first = None
        assert run_dir.try_lock(second).state is LockState.ACQUIRED
    finally:
        for fd in (first, second):
            if fd is not None:
                os.close(fd)


def test_try_lock_reports_other_errors_as_unavailable_with_the_original_error(tmp_path, monkeypatch):
    def flock(fd, op):
        raise OSError(errno.ENOLCK, os.strerror(errno.ENOLCK))

    monkeypatch.setattr(fcntl, "flock", flock)
    fd = os.open(tmp_path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        attempt = run_dir.try_lock(fd)
    finally:
        os.close(fd)
    assert attempt.state is LockState.UNAVAILABLE and attempt.error.errno == errno.ENOLCK


def test_same_dir_is_true_only_while_the_name_itself_is_the_opened_directory(tmp_path):
    d = tmp_path / "d"
    d.mkdir()
    fd = os.open(d, os.O_RDONLY | os.O_DIRECTORY)
    try:
        assert run_dir.same_dir(fd, d) is True
        (tmp_path / "link").symlink_to(d)
        assert run_dir.same_dir(fd, tmp_path / "link") is False  # 指向它的符号链接不是这个名字本身
        d.rename(tmp_path / "moved")
        assert run_dir.same_dir(fd, d) is False                  # 名字已不在
        assert run_dir.same_dir(fd, tmp_path / "moved") is True
        d.mkdir()
        assert run_dir.same_dir(fd, d) is False                  # 名字换成了另一个目录
    finally:
        os.close(fd)


# ============================================================================
# 建 run
# ============================================================================


@pytest.mark.parametrize("detached", [False, True])
def test_create_run_leaves_only_the_complete_run_directory_locked_by_the_holder(tmp_path, lock_holder, detached):
    """建成之后报告目录里只有以 run 标识命名的目录，里面只有两个文件（建 run 不建短锁的锁文件），没有暂存目录；持有者收到一个描述符，
    它与 run 目录是同一个 inode，另开一次取锁得到「已被持有」。后台的运行态带后台执行标记。"""
    root = tmp_path / "runs"
    store = LocalRunStore(root, detached=detached, lock_holder=lock_holder)
    store.create_run(_meta("r", ("a", "b")), _pending("r", ("a", "b")))

    assert os.listdir(root) == ["r"]
    assert sorted(os.listdir(root / "r")) == ["run_meta.json", "run_state.json"]
    [fd] = lock_holder.fds
    assert _same_inode(fd, root / "r")
    assert _try(root / "r") is LockState.HELD
    assert store.load_run_meta("r") == _meta("r", ("a", "b"))
    assert store.load_run_state("r") == _pending("r", ("a", "b"))
    raw = json.loads((root / "r" / "run_state.json").read_text(encoding="utf-8"))
    assert raw.get("detached") is (True if detached else None)
    # 建 run 之后的写入口照常取短锁：与生命期锁是两个对象，互不阻挡
    assert store.try_claim_job("r", "a", claimed_at="t") is True
    assert ".runstate.lock" in os.listdir(root / "r")


def test_create_run_creates_a_missing_report_directory(tmp_path, lock_holder):
    root = tmp_path / "a" / "b" / "runs"
    LocalRunStore(root, lock_holder=lock_holder).create_run(_meta("r"), _pending("r"))
    assert os.listdir(root) == ["r"]
    assert _try(root / "r") is LockState.HELD


@pytest.mark.parametrize("missing", [True, False], ids=["report-dir-missing", "report-dir-exists"])
def test_a_rejected_report_directory_creates_nothing(tmp_path, monkeypatch, lock_holder, missing):
    """报告目录所在的文件系统不在清单里：建暂存目录之前就被拒，什么都不建，含还不存在的报告目录本身；检查结果随异常带出。"""
    monkeypatch.setattr(run_dir, "filesystem_type", lambda fd: "nfs4")
    root = tmp_path / "runs"
    if not missing:
        root.mkdir()
    with pytest.raises(run_dir.RunDirRejected) as exc:
        LocalRunStore(root, lock_holder=lock_holder).create_run(_meta("r"), _pending("r"))
    assert not isinstance(exc.value, OSError)
    assert exc.value.check == run_dir.BoundaryCheck(Boundary.OUTSIDE, str(root), str(tmp_path if missing else root), "nfs4", None)
    assert os.listdir(tmp_path) == ([] if missing else ["runs"])
    if not missing:
        assert os.listdir(root) == []
    assert lock_holder.fds == []


@pytest.mark.parametrize("second", ["outside", "unknown"])
def test_a_rejected_staging_descriptor_removes_the_staging_directory(tmp_path, monkeypatch, lock_holder, second):
    """对报告目录的检查放行、对暂存目录描述符的检查不过（两次之间报告目录被换成了别的文件系统）：删去这个空的暂存目录，
    不取锁、不写，报告目录里什么都不留。类型按描述符指向哪个目录给出，不按调用次数。"""
    root = tmp_path / "runs"
    root.mkdir()
    root_id = (os.stat(root).st_dev, os.stat(root).st_ino)

    def by_directory(fd):
        st = os.fstat(fd)
        if (st.st_dev, st.st_ino) == root_id:
            return _ALLOWED[0]
        if second == "outside":
            return "nfs4"
        raise run_dir.FilesystemUnknown("读不到挂载信息：Permission denied")

    monkeypatch.setattr(run_dir, "filesystem_type", by_directory)
    with pytest.raises(run_dir.RunDirRejected) as exc:
        LocalRunStore(root, lock_holder=lock_holder).create_run(_meta("r"), _pending("r"))
    expected = (Boundary.OUTSIDE, "nfs4", None) if second == "outside" else (Boundary.UNKNOWN, None, "读不到挂载信息：Permission denied")
    assert (exc.value.check.verdict, exc.value.check.fs_type, exc.value.check.unknown_reason) == expected
    assert os.listdir(root) == []
    assert lock_holder.fds == []


def test_a_lock_error_other_than_held_removes_the_staging_directory(tmp_path, monkeypatch, lock_holder):
    """取锁出错且不是「已被持有」：抛锁不可用（OSError 的子类，错误码原样，文件名是报告目录），删去空的暂存目录，不写。"""
    def flock(fd, op):
        raise OSError(errno.ENOLCK, os.strerror(errno.ENOLCK))

    monkeypatch.setattr(fcntl, "flock", flock)
    root = tmp_path / "runs"
    with pytest.raises(run_dir.LifetimeLockUnavailable) as exc:
        LocalRunStore(root, lock_holder=lock_holder).create_run(_meta("r"), _pending("r"))
    assert isinstance(exc.value, OSError)
    assert (exc.value.errno, exc.value.strerror, exc.value.filename) == (errno.ENOLCK, os.strerror(errno.ENOLCK), str(root))
    assert os.listdir(root) == []
    assert lock_holder.fds == []


# ---- 换名：暂存目录被别的进程持有、建出之后被删去、打开之后被删去或换掉 ----


def _staging(path) -> bool:
    return os.path.basename(os.fspath(path)).startswith(run_dir.STAGING_PREFIX)


def test_staging_directories_held_by_another_open_are_left_alone_and_a_new_name_is_tried(tmp_path, monkeypatch, lock_holder):
    """前两个暂存目录一建出就被另一次打开取了锁（清理方正在处理它）：建 run 的一方得到「已被持有」，不动它们，换名，第三次建成。"""
    real_mkdir = os.mkdir
    held: list[int] = []

    def mkdir(path, *args, **kwargs):
        real_mkdir(path, *args, **kwargs)
        if _staging(path) and len(held) < 2:
            fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            held.append(fd)

    monkeypatch.setattr(os, "mkdir", mkdir)
    root = tmp_path / "runs"
    try:
        LocalRunStore(root, lock_holder=lock_holder).create_run(_meta("r"), _pending("r"))
        left = _staging_names(root)
        assert len(left) == 2 and all(os.listdir(root / n) == [] for n in left)
        assert all(any(run_dir.same_dir(fd, root / n) for n in left) for fd in held)  # 留着的正是被持有的那两个
        assert sorted(os.listdir(root)) == sorted(left + ["r"])
        assert _try(root / "r") is LockState.HELD
    finally:
        for fd in held:
            os.close(fd)


def test_a_staging_name_already_taken_is_left_alone_and_a_new_name_is_tried(tmp_path, monkeypatch, lock_holder):
    """暂存目录的名字已被占用（建它的那一次 mkdir 得到「已存在」，那个目录是别人的）：不动它，换名，建成；先前那个目录原样留着。
    注入只换 `os.mkdir`：第一次对暂存名字真的先建出那个目录、在里面放一个文件，再抛「已存在」，像另一个进程抢先建了同名的目录。"""
    real_mkdir = os.mkdir
    taken: list[tuple[str, int]] = []

    def mkdir(path, *args, **kwargs):
        if _staging(path) and not taken:
            real_mkdir(path, *args, **kwargs)
            (Path(path) / "theirs").write_bytes(b"x")
            taken.append((os.path.basename(os.fspath(path)), os.stat(path).st_ino))
            raise FileExistsError(errno.EEXIST, os.strerror(errno.EEXIST), os.fspath(path))
        return real_mkdir(path, *args, **kwargs)

    monkeypatch.setattr(os, "mkdir", mkdir)
    root = tmp_path / "runs"
    LocalRunStore(root, lock_holder=lock_holder).create_run(_meta("r"), _pending("r"))
    [(first, ino)] = taken
    assert sorted(os.listdir(root)) == sorted([first, "r"])
    assert os.stat(root / first).st_ino == ino and _tree(root / first) == {"theirs": b"x"}
    [fd] = lock_holder.fds
    assert _same_inode(fd, root / "r") and _try(root / "r") is LockState.HELD


def test_three_held_staging_directories_end_in_contention(tmp_path, monkeypatch, lock_holder):
    real_mkdir = os.mkdir
    held: list[int] = []

    def mkdir(path, *args, **kwargs):
        real_mkdir(path, *args, **kwargs)
        if _staging(path):
            fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            held.append(fd)

    monkeypatch.setattr(os, "mkdir", mkdir)
    root = tmp_path / "runs"
    try:
        with pytest.raises(run_dir.StagingContended) as exc:
            LocalRunStore(root, lock_holder=lock_holder).create_run(_meta("r"), _pending("r"))
        assert (exc.value.root, exc.value.attempts) == (str(root), run_dir.STAGING_ATTEMPTS) == (str(root), 3)
        assert len(held) == 3 and len(_staging_names(root)) == 3 and "r" not in os.listdir(root)
        # 建 run 的一方生成的名字正是清理方认的形态：三个都列得出
        assert run_dir.staging_names(root) == _staging_names(root)
        assert lock_holder.fds == []
    finally:
        for fd in held:
            os.close(fd)


@pytest.mark.parametrize("when", ["before-open", "after-open", "replaced-after-open"])
def test_a_staging_directory_removed_or_replaced_by_another_process_is_given_up(tmp_path, monkeypatch, lock_holder, when):
    """第一个暂存目录在建 run 的一方打开之前被删去（打开得到「不存在」）、打开之后取锁之前被删去或换成另一个目录（取到锁但名字已不
    指向它）：都换名重来、建成；换上来的那个目录不是自己的，原样留着。"""
    real_mkdir, real_open = os.mkdir, os.open
    hit: list[str] = []

    def mkdir(path, *args, **kwargs):
        real_mkdir(path, *args, **kwargs)
        if when == "before-open" and _staging(path) and not hit:
            hit.append(os.fspath(path))
            os.rmdir(path)

    def open_(path, flags, *args, **kwargs):
        fd = real_open(path, flags, *args, **kwargs)
        if when != "before-open" and _staging(path) and not hit:
            hit.append(os.fspath(path))
            if when == "after-open":
                os.rmdir(path)
            else:
                os.rename(path, os.fspath(path) + "-moved")
                real_mkdir(path)
        return fd

    monkeypatch.setattr(os, "mkdir", mkdir)
    monkeypatch.setattr(os, "open", open_)
    root = tmp_path / "runs"
    LocalRunStore(root, lock_holder=lock_holder).create_run(_meta("r"), _pending("r"))
    assert len(hit) == 1
    first = os.path.basename(hit[0])
    expected = {"before-open": ["r"], "after-open": ["r"], "replaced-after-open": sorted([first, first + "-moved", "r"])}[when]
    assert sorted(os.listdir(root)) == expected
    [fd] = lock_holder.fds
    assert _same_inode(fd, root / "r") and _try(root / "r") is LockState.HELD


# ---- 同步的失败：建暂存目录、打开它、没取到锁的两个出口、写记录 ----
# 建 run 的那一次调用不被异步的异常打断（前台 run 在建 run 之前已装上只记标志的中断处理器，后台推进进程对 SIGINT 取缺省处置，
# 那一侧的用例在 cli 的测试里），这里只核同步的失败


def test_a_failure_to_make_the_staging_directory_other_than_a_taken_name_is_raised_as_it_is(tmp_path, monkeypatch, lock_holder):
    """建暂存目录以「已存在」之外的错误失败（没有权限）：错误原样抛出，不换名重来；报告目录里什么都没有，持有者什么都没收到。"""
    real_mkdir = os.mkdir
    calls: list[str] = []
    injected = PermissionError(errno.EACCES, os.strerror(errno.EACCES))

    def mkdir(path, *args, **kwargs):
        if _staging(path):
            calls.append(os.fspath(path))
            raise injected
        return real_mkdir(path, *args, **kwargs)

    monkeypatch.setattr(os, "mkdir", mkdir)
    root = tmp_path / "runs"
    root.mkdir()
    with pytest.raises(PermissionError) as exc:
        LocalRunStore(root, lock_holder=lock_holder).create_run(_meta("r"), _pending("r"))
    assert exc.value is injected and len(calls) == 1
    assert os.listdir(root) == []
    assert lock_holder.fds == []


def _fail_opening_the_staging_directory(monkeypatch, *, replace_first: bool) -> tuple[PermissionError, list]:
    """把打开暂存目录的那一次 `os.open` 换成以「没有权限」失败。replace_first 为真时，失败之前先把那个名字换成另一个同名目录
    （删去建出的空目录、再建一个、在里面放一个文件），像别的进程在建出与打开之间换上了自己的目录。返回注入的异常与记下的
    （名字, 换上的目录的 inode）。"""
    real_open = os.open
    injected = PermissionError(errno.EACCES, os.strerror(errno.EACCES))
    seen: list[tuple[str, int | None]] = []

    def open_(path, flags, *args, **kwargs):
        if _staging(path):
            ino = None
            if replace_first:
                os.rmdir(path)
                os.mkdir(path)
                (Path(path) / "theirs").write_bytes(b"x")
                ino = os.stat(path).st_ino
            seen.append((os.path.basename(os.fspath(path)), ino))
            raise injected
        return real_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(os, "open", open_)
    return injected, seen


def test_a_failed_open_of_the_staging_directory_is_raised_and_the_directory_is_left_for_the_cleaner(tmp_path, monkeypatch,
                                                                                                    lock_holder):
    """打开暂存目录以「没有权限」失败：错误原样抛出；没有打开成功就无从核对名字仍指向自己建出的那个目录，所以不删，那个空的暂存
    目录留在原处、留给清理方；没有以 run 标识命名的目录，持有者什么都没收到。"""
    root = tmp_path / "runs"
    root.mkdir()
    injected, seen = _fail_opening_the_staging_directory(monkeypatch, replace_first=False)
    with pytest.raises(PermissionError) as exc:
        LocalRunStore(root, lock_holder=lock_holder).create_run(_meta("r"), _pending("r"))
    [(name, _)] = seen
    assert exc.value is injected
    assert os.listdir(root) == [name] and os.listdir(root / name) == []
    assert lock_holder.fds == []


def test_a_directory_put_in_place_of_the_staging_directory_before_a_failed_open_is_left_untouched(tmp_path, monkeypatch,
                                                                                                  lock_holder):
    """建出暂存目录之后、打开之前，那个名字被换成了另一个同名目录（里面有文件），随后打开失败：换上来的目录与里面的文件原样留着。"""
    root = tmp_path / "runs"
    root.mkdir()
    injected, seen = _fail_opening_the_staging_directory(monkeypatch, replace_first=True)
    with pytest.raises(PermissionError) as exc:
        LocalRunStore(root, lock_holder=lock_holder).create_run(_meta("r"), _pending("r"))
    [(name, ino)] = seen
    assert exc.value is injected
    assert os.listdir(root) == [name]
    assert os.stat(root / name).st_ino == ino and _tree(root / name) == {"theirs": b"x"}
    assert lock_holder.fds == []


@pytest.mark.parametrize("exit_", ["rejected-descriptor", "lock-error"])
def test_without_the_lock_a_name_that_no_longer_points_to_the_opened_directory_is_left_alone(tmp_path, monkeypatch, lock_holder,
                                                                                             exit_):
    """没有取到锁的两个出口（对暂存目录描述符的边界检查不过、取锁出错）：名字仍指向自己打开的那个目录时删去它（见
    `test_a_rejected_staging_descriptor_removes_the_staging_directory` 与
    `test_a_lock_error_other_than_held_removes_the_staging_directory`），名字已被换成另一个目录时不动。这里在判断类型或取锁的那一刻把名字换掉：原来的目录挪到别的名字下，同名处另建一个空目录（空的，
    所以只删空目录的做法按名字删也删得掉它，不动它只能是因为核对了名字）；出口照常抛出，换上来的目录原样留着。"""
    root = tmp_path / "runs"
    root.mkdir()
    root_id = (os.stat(root).st_dev, os.stat(root).st_ino)
    swapped: list[tuple[str, int]] = []

    def swap_name(fd: int) -> None:
        [name] = _staging_names(root)
        path = root / name
        assert run_dir.same_dir(fd, path)
        os.rename(path, root / "moved-away")
        path.mkdir()
        swapped.append((name, os.stat(path).st_ino))

    def by_directory(fd):
        st = os.fstat(fd)
        if (st.st_dev, st.st_ino) == root_id:
            return _ALLOWED[0]
        if exit_ == "rejected-descriptor":
            swap_name(fd)
            return "nfs4"
        return _ALLOWED[0]

    def flock(fd, op):
        swap_name(fd)
        raise OSError(errno.ENOLCK, os.strerror(errno.ENOLCK))

    monkeypatch.setattr(run_dir, "filesystem_type", by_directory)
    if exit_ == "lock-error":
        monkeypatch.setattr(fcntl, "flock", flock)
    expected = run_dir.RunDirRejected if exit_ == "rejected-descriptor" else run_dir.LifetimeLockUnavailable
    with pytest.raises(expected):
        LocalRunStore(root, lock_holder=lock_holder).create_run(_meta("r"), _pending("r"))
    [(name, ino)] = swapped
    assert sorted(os.listdir(root)) == sorted([name, "moved-away"])
    assert os.stat(root / name).st_ino == ino and os.listdir(root / name) == []
    assert lock_holder.fds == []


def test_a_write_failure_removes_the_staging_directory_and_raises_as_it_is(tmp_path, monkeypatch, lock_holder):
    """写运行态失败（磁盘满）：OSError 原样抛出，不是「已存在」；暂存目录连同已写下的运行定义删去，没有 run 目录。"""
    real_replace = os.replace

    def replace(src, dst, *args, **kwargs):
        if os.path.basename(os.fspath(dst)) == "run_state.json":
            raise OSError(errno.ENOSPC, os.strerror(errno.ENOSPC), os.fspath(dst))
        return real_replace(src, dst, *args, **kwargs)

    monkeypatch.setattr(os, "replace", replace)
    root = tmp_path / "runs"
    with pytest.raises(OSError) as exc:
        LocalRunStore(root, lock_holder=lock_holder).create_run(_meta("r"), _pending("r"))
    assert exc.value.errno == errno.ENOSPC and not isinstance(exc.value, RunAlreadyExists)
    assert os.listdir(root) == []
    assert lock_holder.fds == []


# ============================================================================
# 真实进程：锁随建 run 的进程，到它退出为止
# ============================================================================

# 建 run 的子进程：用生产的 LocalRunStore 与 HoldUntilExit 建 run，把就绪消息原子写进 ready 文件，然后等着被杀。只用 ASCII，
# 参数经一个 JSON 串传入。low-fd 模式先关掉标准输入，让暂存目录打开在 0 号上；建成之后照后台推进进程回报之后的做法，把日志接到
# 0、1、2 号上。grandchild 模式建成之后以缺省方式起一个孙进程
_CREATOR = r"""
import json, os, subprocess, sys, time
from gherkai_core.adapters.run_store.local import LocalRunStore
from gherkai_core.adapters.run_store.run_dir import HoldUntilExit
from gherkai_core.model import Job, JobState, RunMeta, RunState, Scenario, Status, Step
a = json.loads(sys.argv[1])
job = Job(scope_id="a", scope_name="a", engine="midscene", timeout_s=300.0,
          scenarios=(Scenario(id="a:1", name="sc", steps=(Step(0, "Given", "x"),)),))
meta = RunMeta(run_id="r", created_at="t", jobs=(job,), deadline_at="2026-11-21T01:00:00+00:00")
state = RunState(run_id="r", status=Status.PENDING, jobs={"a": JobState("a", Status.PENDING)}, started_at="t")
held = []

class Recording(HoldUntilExit):
    def hold(self, fd):
        held.append(fd)
        super().hold(fd)

msg = {}
if a["mode"] == "low-fd":
    os.close(0)
store = LocalRunStore(a["root"], lock_holder=Recording())
store.create_run(meta, state)
msg["held"] = held
if a["mode"] == "grandchild":
    msg["grandchild"] = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(120)"]).pid
if a["mode"] == "low-fd":
    log = os.open(a["log"], os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    for n in (0, 1, 2):
        os.dup2(log, n)
with open(a["ready"] + ".tmp", "w") as f:
    json.dump(msg, f)
os.replace(a["ready"] + ".tmp", a["ready"])
time.sleep(120)
"""


def _start_creator(tmp_path: Path, mode: str) -> tuple[subprocess.Popen, dict]:
    ready = tmp_path / "ready.json"
    args = {"root": str(tmp_path / "runs"), "ready": str(ready), "mode": mode, "log": str(tmp_path / "advancer.log")}
    proc = subprocess.Popen([sys.executable, "-I", "-c", _CREATOR, json.dumps(args)],
                            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    deadline = time.monotonic() + _TIMEOUT_S
    while not ready.exists():
        if proc.poll() is not None:
            raise AssertionError(proc.stderr.read())
        assert time.monotonic() < deadline, "建 run 的子进程没有在时限内就绪"
        time.sleep(0.01)
    return proc, json.loads(ready.read_text(encoding="utf-8"))


def _stop(proc: subprocess.Popen) -> None:
    if proc.poll() is None:
        proc.kill()
    proc.wait(timeout=_TIMEOUT_S)
    proc.stderr.close()


def _acquired_within(path: Path, seconds: float) -> bool:
    deadline = time.monotonic() + seconds
    while True:
        if _try(path) is LockState.ACQUIRED:
            return True
        if time.monotonic() >= deadline:
            return False
        time.sleep(0.01)


@pytest.mark.real_filesystem
def test_the_creating_process_holds_the_lock_while_paused_and_releases_it_when_killed(tmp_path):
    proc, _ = _start_creator(tmp_path, "hold")
    run = tmp_path / "runs" / "r"
    try:
        assert os.listdir(tmp_path / "runs") == ["r"]
        assert _try(run) is LockState.HELD
        os.kill(proc.pid, signal.SIGSTOP)
        _, status = os.waitpid(proc.pid, os.WUNTRACED)
        assert os.WIFSTOPPED(status)
        assert _try(run) is LockState.HELD
        os.kill(proc.pid, signal.SIGKILL)
        proc.wait(timeout=_TIMEOUT_S)
        assert _acquired_within(run, 2.0)
    finally:
        _stop(proc)


@pytest.mark.real_filesystem
def test_a_child_started_the_default_way_does_not_keep_the_lock(tmp_path):
    """建 run 之后以缺省方式起的孙进程还活着时杀掉建 run 的进程：锁随即可拿，孙进程不延长持有。"""
    proc, msg = _start_creator(tmp_path, "grandchild")
    grandchild = msg["grandchild"]
    run = tmp_path / "runs" / "r"
    try:
        assert _try(run) is LockState.HELD
        os.kill(proc.pid, signal.SIGKILL)
        proc.wait(timeout=_TIMEOUT_S)
        os.kill(grandchild, 0)  # 孙进程还在
        assert _acquired_within(run, 2.0)
        os.kill(grandchild, 0)
    finally:
        _stop(proc)
        try:
            os.kill(grandchild, signal.SIGKILL)
        except ProcessLookupError:
            pass


@pytest.mark.real_filesystem
def test_the_lock_survives_redirecting_the_standard_streams_when_it_was_opened_on_a_low_number(tmp_path):
    """标准输入已关闭、暂存目录打开在 0 号上：持有者收到的号不小于 3，之后把日志接到 0、1、2 号上，另一个进程取锁仍得到「已被持有」。"""
    proc, msg = _start_creator(tmp_path, "low-fd")
    try:
        assert _try(tmp_path / "runs" / "r") is LockState.HELD
        [fd] = msg["held"]
        assert fd >= 3
    finally:
        _stop(proc)


# ============================================================================
# 真实进程：fork 而不 exec 的子进程不带着锁（ADR 0054 决策三「不被子进程继承」）
# ============================================================================

# 持有方子进程：用生产的 LocalRunStore 与 HoldUntilExit 建 run（持有者记下收到的号），再按 mode 起一个停住的子进程，就绪消息原子写进
# work/ready.json，然后等着被杀。只用 ASCII，参数经一个 JSON 串传入。
# - fork：os.fork，子进程把它在持锁的号上看到的东西（"closed"，或所指的设备号与 inode）写进 child.json 后停住；父进程等它写完再就绪。
# - reuse：同 fork，只是 fork 之前先把持锁的号改接到 other 文件上（这个号被关闭并另作他用）。
# - no-identity：同 fork，只是持有者收下描述符时 os.fstat 失败一次。
# - mp-fork：multiprocessing 的 fork 上下文起一个停住的进程。
# - preexec_fn：subprocess.Popen 带 preexec_fn，子进程停在 preexec_fn 里。Popen 在父进程里要等子进程 exec 之后才返回，所以就绪消息由
#   调用 Popen 之前起的线程在子进程报出自己的进程号之后写出。
_FORKING_CREATOR = r"""
import json, os, subprocess, sys, threading, time
from gherkai_core.adapters.run_store.local import LocalRunStore
from gherkai_core.adapters.run_store.run_dir import HoldUntilExit
from gherkai_core.model import Job, JobState, RunMeta, RunState, Scenario, Status, Step
a = json.loads(sys.argv[1])
work, mode = a["work"], a["mode"]
job = Job(scope_id="a", scope_name="a", engine="midscene", timeout_s=300.0,
          scenarios=(Scenario(id="a:1", name="sc", steps=(Step(0, "Given", "x"),)),))
meta = RunMeta(run_id="r", created_at="t", jobs=(job,), deadline_at="2026-11-21T01:00:00+00:00")
state = RunState(run_id="r", status=Status.PENDING, jobs={"a": JobState("a", Status.PENDING)}, started_at="t")
held = []
real_fstat = os.fstat

def failing_fstat(fd):
    raise OSError(5, "Input/output error")

class Recording(HoldUntilExit):
    def hold(self, fd):
        held.append(fd)
        if mode == "no-identity":
            os.fstat = failing_fstat
        try:
            super().hold(fd)
        finally:
            os.fstat = real_fstat

def put(name, obj):
    path = os.path.join(work, name)
    with open(path + ".tmp", "w") as f:
        json.dump(obj, f)
    os.replace(path + ".tmp", path)

def wait_for(name):
    path = os.path.join(work, name)
    while not os.path.exists(path):
        time.sleep(0.01)
    with open(path) as f:
        return json.load(f)

def view(fd):
    try:
        st = os.fstat(fd)
    except OSError:
        return "closed"
    return [st.st_dev, st.st_ino]

LocalRunStore(a["root"], lock_holder=Recording()).create_run(meta, state)
[fd] = held
if mode == "reuse":
    other = os.open(a["other"], os.O_RDONLY)
    os.dup2(other, fd)
    os.close(other)
if mode in ("fork", "reuse", "no-identity"):
    pid = os.fork()
    if pid == 0:
        put("child.json", view(fd))
        time.sleep(120)
        os._exit(0)
    put("ready.json", {"child": pid, "view": wait_for("child.json")})
elif mode == "mp-fork":
    import multiprocessing
    p = multiprocessing.get_context("fork").Process(target=time.sleep, args=(120,))
    p.start()
    put("ready.json", {"child": p.pid})
elif mode == "preexec_fn":
    def stay():
        put("child.json", os.getpid())
        time.sleep(120)

    threading.Thread(target=lambda: put("ready.json", {"child": wait_for("child.json")}), daemon=True).start()
    subprocess.Popen([sys.executable, "-c", "pass"], preexec_fn=stay)
time.sleep(120)
"""


class _ForkingCreator:
    """一个持有方子进程（以新会话启动）与它起的那个停住的子进程。`end` 结束两者：先杀持有方，再杀子进程与整个会话。"""

    def __init__(self, tmp_path: Path, mode: str, **extra: str) -> None:
        args = {"root": str(tmp_path / "runs"), "work": str(tmp_path), "mode": mode, **extra}
        self._stderr = tmp_path / "creator.stderr"
        with open(self._stderr, "w", encoding="utf-8") as err:
            self.proc = subprocess.Popen([sys.executable, "-I", "-c", _FORKING_CREATOR, json.dumps(args)],
                                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=err,
                                         start_new_session=True)
        self.msg: dict = {}
        ready = tmp_path / "ready.json"
        deadline = time.monotonic() + _TIMEOUT_S
        try:
            while not ready.exists():
                assert self.proc.poll() is None, self._stderr.read_text(encoding="utf-8")
                assert time.monotonic() < deadline, "持有方子进程没有在时限内就绪"
                time.sleep(0.01)
            self.msg = json.loads(ready.read_text(encoding="utf-8"))
        except BaseException:
            self.end()
            raise

    def kill_creator(self) -> None:
        os.kill(self.proc.pid, signal.SIGKILL)
        self.proc.wait(timeout=_TIMEOUT_S)

    def child_alive(self) -> bool:
        try:
            os.kill(self.msg["child"], 0)
        except ProcessLookupError:
            return False
        return True

    def end(self) -> None:
        if self.proc.poll() is None:
            self.proc.kill()
        self.proc.wait(timeout=_TIMEOUT_S)
        if "child" in self.msg:
            with contextlib.suppress(ProcessLookupError):
                os.kill(self.msg["child"], signal.SIGKILL)
        with contextlib.suppress(OSError):
            os.killpg(self.proc.pid, signal.SIGKILL)  # 会话里留下的其余进程


@pytest.mark.real_filesystem
@pytest.mark.parametrize("mode", ["fork", "mp-fork", "preexec_fn"])
def test_a_child_forked_without_exec_does_not_keep_the_lock(tmp_path, mode):
    """持有方建 run 之后以 fork 而不 exec 的方式起一个停住的子进程（直接 fork、fork 方式的 multiprocessing、停在 preexec_fn 里）：
    持有方活着时试拿得到「已被持有」；持有方被 SIGKILL 之后子进程还在，锁随即拿得到。"""
    creator = _ForkingCreator(tmp_path, mode)
    run = tmp_path / "runs" / "r"
    try:
        assert _try(run) is LockState.HELD
        creator.kill_creator()
        assert creator.child_alive()
        assert _acquired_within(run, 2.0)
        assert creator.child_alive()
    finally:
        creator.end()


@pytest.mark.real_filesystem
def test_closing_the_copy_in_the_forked_child_does_not_release_the_lock(tmp_path):
    """持有方活着时 fork 出的子进程里，持锁的号已经关闭；别的进程试拿仍得到「已被持有」：锁由持有方的那一份持有。"""
    creator = _ForkingCreator(tmp_path, "fork")
    try:
        assert creator.msg["view"] == "closed"
        assert creator.child_alive()
        assert _try(tmp_path / "runs" / "r") is LockState.HELD
        assert _try_in_another_process(tmp_path / "runs" / "r") == "held"
    finally:
        creator.end()


@pytest.mark.real_filesystem
def test_the_fork_hook_leaves_a_reused_number_open(tmp_path):
    """持锁的号被关闭并另作他用（改接到另一个文件）之后 fork：子进程里这个号仍开着、仍指向那个文件，钩子核对身份不过即不关。"""
    other = tmp_path / "other.txt"
    other.write_text("x", encoding="utf-8")
    creator = _ForkingCreator(tmp_path, "reuse", other=str(other))
    try:
        st = os.stat(other)
        assert creator.msg["view"] == [st.st_dev, st.st_ino]
    finally:
        creator.end()


@pytest.mark.real_filesystem
def test_a_holder_that_cannot_read_the_identity_still_holds_and_registers_no_hook(tmp_path):
    """持有者收下描述符时取不到它所指目录的身份（os.fstat 失败）：不报错，run 照常建成、锁照常持有；没有可核对的身份，不登记钩子，
    fork 出的子进程里这个号仍开着。"""
    creator = _ForkingCreator(tmp_path, "no-identity")
    run = tmp_path / "runs" / "r"
    try:
        st = os.stat(run)
        assert creator.msg["view"] == [st.st_dev, st.st_ino]
        assert _try(run) is LockState.HELD
    finally:
        creator.end()


# ============================================================================
# 试拿：处置的一方打开 run 目录、做边界检查、不阻塞地试拿（ADR 0054 决策三「谁在何时试拿」「结果的判读」）
# ============================================================================

# 另一个进程试拿一次：不阻塞地取排他锁，打印 acquired 或 held，随即退出（拿到的锁随之放开）。只用 ASCII
_TRY_IN_ANOTHER_PROCESS = r"""
import errno, fcntl, os, sys
fd = os.open(sys.argv[1], os.O_RDONLY | os.O_DIRECTORY)
try:
    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    print("acquired")
except OSError as e:
    print("held" if e.errno == errno.EWOULDBLOCK else "error %d" % e.errno)
"""


def _try_in_another_process(path: Path) -> str:
    out = subprocess.run([sys.executable, "-I", "-c", _TRY_IN_ANOTHER_PROCESS, str(path)], capture_output=True, text=True,
                         check=True, stdin=subprocess.DEVNULL, timeout=_TIMEOUT_S)
    return out.stdout.strip()


def _probe_state(path: Path) -> LockState:
    with run_dir.probe_run_dir(path) as probe:
        assert probe.boundary.verdict is Boundary.INSIDE
        return probe.lock.state


@pytest.mark.real_filesystem
def test_probe_sees_the_creating_process_hold_the_lock_until_it_is_killed(tmp_path):
    """建 run 的进程活着、被暂停时，试拿都得到「已被持有」；被 SIGKILL 之后拿得到。对这次打开做的边界检查用宿主真实的类型。"""
    proc, _ = _start_creator(tmp_path, "hold")
    run = tmp_path / "runs" / "r"
    try:
        with run_dir.probe_run_dir(run) as probe:
            assert probe.boundary == run_dir.BoundaryCheck(Boundary.INSIDE, str(run), str(run), probe.boundary.fs_type, None)
            assert probe.lock == run_dir.LockAttempt(LockState.HELD, None)
        os.kill(proc.pid, signal.SIGSTOP)
        _, status = os.waitpid(proc.pid, os.WUNTRACED)
        assert os.WIFSTOPPED(status)
        assert _probe_state(run) is LockState.HELD
        os.kill(proc.pid, signal.SIGKILL)
        proc.wait(timeout=_TIMEOUT_S)
        deadline = time.monotonic() + 2.0
        while _probe_state(run) is not LockState.ACQUIRED:
            assert time.monotonic() < deadline, "建 run 的进程被杀之后两秒内仍拿不到锁"
            time.sleep(0.01)
    finally:
        _stop(proc)


@pytest.mark.real_filesystem
def test_a_probe_holds_the_lock_until_its_block_ends(tmp_path, lock_holder):
    """拿到的锁持有到块结束：块里同一进程另开一次、另一个进程试拿都得到「已被持有」；块结束之后另一个进程即拿得到（只判断不写的
    处置方离开块即放开）。"""
    store = LocalRunStore(tmp_path / "runs", lock_holder=lock_holder)
    store.create_run(_meta("r"), _pending("r"))
    lock_holder.close_all()  # 建 run 的一方已不在
    run = tmp_path / "runs" / "r"
    with store.probe_run_dir("r") as probe:
        assert probe.lock.state is LockState.ACQUIRED
        assert _try(run) is LockState.HELD
        assert _try_in_another_process(run) == "held"
    assert _try_in_another_process(run) == "acquired"
    assert _try(run) is LockState.ACQUIRED


@pytest.mark.parametrize("occupant", ["missing", "file", "dangling-symlink"])
def test_probe_reads_a_name_without_a_directory_as_gone(tmp_path, occupant):
    """这个名字下没有目录（不存在、是文件、是悬空的符号链接）：抛 RunDirGone，不是 OSError；报告目录里什么都不多出来。"""
    root = tmp_path / "runs"
    root.mkdir()
    if occupant == "file":
        (root / "r").write_text("x", encoding="utf-8")
    elif occupant == "dangling-symlink":
        (root / "r").symlink_to(tmp_path / "nowhere")
    before = _tree(tmp_path)
    with pytest.raises(run_dir.RunDirGone) as exc:
        with run_dir.probe_run_dir(root / "r"):
            pass
    assert not isinstance(exc.value, OSError)
    with pytest.raises(run_dir.RunDirGone):
        with LocalRunStore(root).probe_run_dir("r"):
            pass
    assert _tree(tmp_path) == before


@pytest.mark.skipif(hasattr(os, "geteuid") and os.geteuid() == 0, reason="root 无视文件权限")
def test_probe_raises_other_open_failures_as_they_are_and_changes_nothing(tmp_path, lock_holder):
    """run 目录没有读权限（0o300，运行态照样读得出）：打开得到 EACCES，原样抛出 PermissionError，不当作锁不可用、也不是「已不在」；
    两个记录文件逐字节不变。"""
    store = LocalRunStore(tmp_path / "runs", lock_holder=lock_holder)
    store.create_run(_meta("r"), _pending("r"))
    lock_holder.close_all()
    run = tmp_path / "runs" / "r"
    before = {n: (run / n).read_bytes() for n in ("run_meta.json", "run_state.json")}
    run.chmod(0o300)
    try:
        assert store.load_run_state("r") == _pending("r")  # 前提：运行态照样读得出
        with pytest.raises(PermissionError) as exc:
            with store.probe_run_dir("r"):
                pass
        assert exc.value.errno == errno.EACCES
    finally:
        run.chmod(0o700)
    assert {n: (run / n).read_bytes() for n in before} == before


def test_probe_does_not_try_the_lock_when_the_boundary_check_fails(tmp_path, monkeypatch, lock_holder):
    """对这次打开的边界检查不过：不试拿（lock 为 None），块里另开一次照样拿得到；检查结果随探查给出。"""
    store = LocalRunStore(tmp_path / "runs", lock_holder=lock_holder)
    store.create_run(_meta("r"), _pending("r"))
    lock_holder.close_all()
    monkeypatch.setattr(run_dir, "filesystem_type", lambda fd: "nfs4")
    run = tmp_path / "runs" / "r"
    with store.probe_run_dir("r") as probe:
        assert probe == run_dir.RunDirProbe(run_dir.BoundaryCheck(Boundary.OUTSIDE, str(run), str(run), "nfs4", None), None)
        assert _try(run) is LockState.ACQUIRED


def test_probe_reports_a_lock_error_other_than_held_as_unavailable(tmp_path, monkeypatch, lock_holder):
    store = LocalRunStore(tmp_path / "runs", lock_holder=lock_holder)
    store.create_run(_meta("r"), _pending("r"))
    lock_holder.close_all()

    def flock(fd, op):
        raise OSError(errno.ENOLCK, os.strerror(errno.ENOLCK))

    monkeypatch.setattr(fcntl, "flock", flock)
    with store.probe_run_dir("r") as probe:
        assert probe.lock.state is LockState.UNAVAILABLE and probe.lock.error.errno == errno.ENOLCK


def test_probe_follows_a_symlinked_run_directory_to_the_directory_it_writes(tmp_path, lock_holder):
    """run 目录的名字是指向一个目录的符号链接：打开跟随它，锁取在链接指向的那个目录上（之后按路径的写也落在那里）。"""
    elsewhere = tmp_path / "elsewhere"
    LocalRunStore(elsewhere, lock_holder=lock_holder).create_run(_meta("r"), _pending("r"))
    lock_holder.close_all()
    root = tmp_path / "runs"
    root.mkdir()
    (root / "r").symlink_to(elsewhere / "r")
    with LocalRunStore(root).probe_run_dir("r") as probe:
        assert probe.lock.state is LockState.ACQUIRED
        assert _try(elsewhere / "r") is LockState.HELD


# ============================================================================
# 清理暂存目录（ADR 0054 决策三「谁在何时试拿」）
# ============================================================================


def _make_staging(root: Path, files: int = 2, name: str = ".gherkai-creating-0123456789abcdef") -> Path:
    """在 root 里放一个暂存目录形态的目录，里面有 files 个文件（像建 run 中途被强杀留下的）。"""
    path = root / name
    path.mkdir(parents=True)
    for i in range(files):
        (path / f"f{i:04d}").write_bytes(b"x")
    return path


def test_staging_names_lists_only_the_shape_and_reads_a_missing_root_as_empty(tmp_path):
    root = tmp_path / "runs"
    assert run_dir.staging_names(root) == []
    _make_staging(root, name=".gherkai-creating-ffffffffffffffff")
    _make_staging(root, name=".gherkai-creating-0123456789abcdef")
    _make_staging(root, name=".gherkai-creating-user-named")
    (root / "r").mkdir()
    assert run_dir.staging_names(root) == [".gherkai-creating-0123456789abcdef", ".gherkai-creating-ffffffffffffffff"]
    assert LocalRunStore(root).staging_names() == run_dir.staging_names(root)
    (tmp_path / "file").write_text("x", encoding="utf-8")
    with pytest.raises(NotADirectoryError):
        run_dir.staging_names(tmp_path / "file")


def test_sweep_removes_an_unheld_staging_directory_with_its_contents(tmp_path):
    root = tmp_path / "runs"
    path = _make_staging(root, files=3)
    swept = LocalRunStore(root).sweep_staging_dir(path.name, dry_run=False)
    assert swept == run_dir.StagingSweep(path.name, run_dir.StagingOutcome.REMOVED)
    assert os.listdir(root) == []


def test_a_dry_run_sweep_removes_nothing_and_lets_the_lock_go(tmp_path):
    """只看不删：给出「会删除」，目录与里面的文件逐字节不变；拿到的锁随即放开，另一个进程立即拿得到。"""
    root = tmp_path / "runs"
    path = _make_staging(root, files=3)
    before = _tree(root)
    swept = run_dir.sweep_staging_dir(root, path.name, dry_run=True)
    assert swept == run_dir.StagingSweep(path.name, run_dir.StagingOutcome.WOULD_REMOVE)
    assert _tree(root) == before
    assert _try(path) is LockState.ACQUIRED


def test_a_held_staging_directory_is_skipped_and_removed_once_released(tmp_path):
    """另一次打开持有它的锁（另一个清理方，或正在建 run 的一方）：跳过、什么都不删；放开之后再清即删去。"""
    root = tmp_path / "runs"
    path = _make_staging(root)
    before = _tree(root)
    other = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        fcntl.flock(other, fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert run_dir.sweep_staging_dir(root, path.name, dry_run=False) == run_dir.StagingSweep(
            path.name, run_dir.StagingOutcome.SKIPPED, run_dir.StagingSkip.HELD)
        assert _tree(root) == before
    finally:
        os.close(other)
    assert run_dir.sweep_staging_dir(root, path.name, dry_run=False).outcome is run_dir.StagingOutcome.REMOVED
    assert os.listdir(root) == []


def test_a_staging_directory_outside_the_boundary_is_skipped_before_trying_the_lock(tmp_path, monkeypatch):
    """对这次打开的边界检查不过：跳过并带上检查结果，什么都不删。另一次打开正持锁时结果仍是这一条（检查先于试拿）。"""
    root = tmp_path / "runs"
    path = _make_staging(root)
    before = _tree(root)
    monkeypatch.setattr(run_dir, "filesystem_type", lambda fd: "nfs4")
    other = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        fcntl.flock(other, fcntl.LOCK_EX | fcntl.LOCK_NB)
        swept = run_dir.sweep_staging_dir(root, path.name, dry_run=False)
    finally:
        os.close(other)
    assert swept == run_dir.StagingSweep(path.name, run_dir.StagingOutcome.SKIPPED, run_dir.StagingSkip.UNSUPPORTED_FILESYSTEM,
                                         boundary=run_dir.BoundaryCheck(Boundary.OUTSIDE, str(path), str(path), "nfs4", None))
    assert _tree(root) == before


def test_a_lock_error_other_than_held_skips_the_staging_directory(tmp_path, monkeypatch):
    root = tmp_path / "runs"
    path = _make_staging(root)
    before = _tree(root)

    def flock(fd, op):
        raise OSError(errno.ENOLCK, os.strerror(errno.ENOLCK))

    monkeypatch.setattr(fcntl, "flock", flock)
    swept = run_dir.sweep_staging_dir(root, path.name, dry_run=False)
    assert (swept.outcome, swept.skip, swept.error.errno) == (
        run_dir.StagingOutcome.SKIPPED, run_dir.StagingSkip.LOCK_UNAVAILABLE, errno.ENOLCK)
    assert _tree(root) == before


def test_entries_that_are_not_staging_directories_are_neither_listed_nor_touched(tmp_path, lock_holder):
    """形态不符的名字（使用者以前缀起名的目录、大写）、以暂存目录形态命名的文件与符号链接（链接指向的目录完好）、已经不在的名字、
    run 目录（建它的进程已不在、锁拿得到）：清理方都返回 None、什么都不碰。"""
    root = tmp_path / "runs"
    LocalRunStore(root, lock_holder=lock_holder).create_run(_meta("r"), _pending("r"))
    lock_holder.close_all()
    _make_staging(root, name=".gherkai-creating-user-named")
    _make_staging(root, name=".gherkai-creating-0123456789ABCDEF")
    (root / ".gherkai-creating-aaaaaaaaaaaaaaaa").write_bytes(b"a file")
    target = tmp_path / "target"
    target.mkdir()
    (target / "keep").write_bytes(b"k")
    (root / ".gherkai-creating-bbbbbbbbbbbbbbbb").symlink_to(target)
    before, target_before = _tree(root), _tree(target)
    assert run_dir.staging_names(root) == [".gherkai-creating-aaaaaaaaaaaaaaaa", ".gherkai-creating-bbbbbbbbbbbbbbbb"]
    held_target = os.open(target, os.O_RDONLY | os.O_DIRECTORY)  # 链接指向的目录正被持有：符号链接也不因此列成「被持有」
    try:
        fcntl.flock(held_target, fcntl.LOCK_EX | fcntl.LOCK_NB)
        for name in (".gherkai-creating-user-named", ".gherkai-creating-0123456789ABCDEF", ".gherkai-creating-aaaaaaaaaaaaaaaa",
                     ".gherkai-creating-bbbbbbbbbbbbbbbb", ".gherkai-creating-cccccccccccccccc", "r"):
            assert run_dir.sweep_staging_dir(root, name, dry_run=False) is None, name
            assert LocalRunStore(root).sweep_staging_dir(name, dry_run=False) is None, name
    finally:
        os.close(held_target)
    assert _tree(root) == before and _tree(target) == target_before


@pytest.mark.skipif(hasattr(os, "geteuid") and os.geteuid() == 0, reason="root 无视文件权限")
def test_an_unopenable_staging_directory_is_skipped_with_the_error(tmp_path):
    """没有读权限（0o300）：打开得到 EACCES，跳过并带上原错误，什么都不删。"""
    root = tmp_path / "runs"
    path = _make_staging(root)
    path.chmod(0o300)
    try:
        swept = run_dir.sweep_staging_dir(root, path.name, dry_run=False)
    finally:
        path.chmod(0o700)
    assert (swept.outcome, swept.skip, swept.error.errno) == (
        run_dir.StagingOutcome.SKIPPED, run_dir.StagingSkip.UNOPENABLE, errno.EACCES)
    assert sorted(os.listdir(path)) == ["f0000", "f0001"]


@pytest.mark.skipif(hasattr(os, "geteuid") and os.geteuid() == 0, reason="root 无视文件权限")
def test_a_removal_that_fails_midway_is_skipped_and_the_next_sweep_finishes_it(tmp_path):
    """删除中途出错（里面有一个不可写的子目录，删它里面的文件得到 EACCES）：跳过并带上原错误，已删去的部分不恢复，删不掉的留着，锁随之
    放开；原因消除之后下一次清理接着删去。"""
    root = tmp_path / "runs"
    path = _make_staging(root, files=3)
    sub = path / "sub"
    sub.mkdir()
    (sub / "inner").write_bytes(b"i")
    sub.chmod(0o500)
    try:
        swept = run_dir.sweep_staging_dir(root, path.name, dry_run=False)
        assert (swept.outcome, swept.skip) == (run_dir.StagingOutcome.SKIPPED, run_dir.StagingSkip.REMOVE_FAILED)
        assert isinstance(swept.error, PermissionError) and swept.error.errno == errno.EACCES
        assert os.listdir(sub) == ["inner"]
        assert _try(path) is LockState.ACQUIRED
    finally:
        sub.chmod(0o700)
    assert run_dir.sweep_staging_dir(root, path.name, dry_run=False).outcome is run_dir.StagingOutcome.REMOVED
    assert os.listdir(root) == []


# ---- 清理方与创建者的交错：创建者是真实进程，执行生产的 create_run_dir，在第一个暂存目录的指定几步停下 ----

# 创建者：把 os.mkdir、os.open、fcntl.flock 包一层（被包的原语照样真实执行），记下第一个暂存目录上的各步，在给定的几步停下：向标准
# 输出写一行，等标准输入来一行再继续。建成之后报告做过的各步并持锁等着，标准输入再来一行才退出。只用 ASCII
_STAGED_CREATOR = r"""
import errno, fcntl, json, os, sys
from pathlib import Path
from gherkai_core.adapters.run_store import run_dir
a = json.loads(sys.argv[1])
stops = set(a["stops"])
attempt = [0]
steps = []
real_mkdir, real_open, real_flock = os.mkdir, os.open, fcntl.flock

def say(obj):
    sys.stdout.write(json.dumps(obj) + "\n")
    sys.stdout.flush()

def wait_for_go():
    if not sys.stdin.readline():
        os._exit(3)

def stop(phase, path):
    if attempt[0] == 1 and phase in stops:
        say({"stop": phase, "name": os.path.basename(os.fspath(path))})
        wait_for_go()

def is_staging(path):
    return isinstance(path, (str, os.PathLike)) and run_dir.is_staging_name(os.path.basename(os.fspath(path)))

def mkdir(path, *args, **kwargs):
    real_mkdir(path, *args, **kwargs)
    if is_staging(path):
        attempt[0] += 1
        steps.append(["mkdir", os.path.basename(os.fspath(path))])
        stop("after-mkdir", path)

def open_(path, flags, *args, **kwargs):
    if not is_staging(path):
        return real_open(path, flags, *args, **kwargs)
    try:
        fd = real_open(path, flags, *args, **kwargs)
    except OSError as e:
        steps.append(["open", errno.errorcode[e.errno]])
        raise
    steps.append(["open", "ok"])
    stop("after-open", path)
    return fd

def flock(fd, op):
    try:
        real_flock(fd, op)
    except OSError as e:
        steps.append(["flock", "held" if e.errno == errno.EWOULDBLOCK else errno.errorcode[e.errno]])
        raise
    steps.append(["flock", "ok"])

os.mkdir, os.open, fcntl.flock = mkdir, open_, flock

class Holder:
    def hold(self, fd):
        steps.append(["hold"])

def write(staging):
    (staging / "run_meta.json").write_bytes(b"meta")
    (staging / "run_state.json").write_bytes(b"state")
    stop("before-rename", staging)

run_dir.create_run_dir(Path(a["root"]), "r", write, holder=Holder())
say({"done": steps})
wait_for_go()
"""


class _StagedCreator:
    """建 run 的真实子进程（`_STAGED_CREATOR`）：next() 取它的下一行消息，go() 放行，finish() 让建成之后的它退出。"""

    def __init__(self, tmp_path: Path, stops: list[str]) -> None:
        import queue
        import threading

        args = {"root": str(tmp_path / "runs"), "stops": stops}
        self.proc = subprocess.Popen([sys.executable, "-I", "-c", _STAGED_CREATOR, json.dumps(args)],
                                     stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self._lines: queue.Queue = queue.Queue()
        self._empty = queue.Empty
        threading.Thread(target=self._pump, daemon=True).start()

    def _pump(self) -> None:
        for line in self.proc.stdout:
            self._lines.put(json.loads(line))
        self._lines.put(None)

    def next(self) -> dict:
        try:
            msg = self._lines.get(timeout=_TIMEOUT_S)
        except self._empty:
            raise AssertionError("建 run 的子进程没有在时限内给出下一步") from None
        if msg is None:
            self.proc.wait(timeout=_TIMEOUT_S)
            raise AssertionError(f"建 run 的子进程提前退出：{self.proc.stderr.read()}")
        return msg

    def go(self) -> None:
        self.proc.stdin.write("go\n")
        self.proc.stdin.flush()

    def finish(self) -> None:
        """让建成 run 之后等着的子进程退出，等它结束（锁随之放开）。"""
        self.go()
        assert self.proc.wait(timeout=_TIMEOUT_S) == 0, self.proc.stderr.read()

    def close(self) -> None:
        if self.proc.poll() is None:
            self.proc.kill()
        self.proc.wait(timeout=_TIMEOUT_S)
        for stream in (self.proc.stdin, self.proc.stderr):
            try:
                stream.close()
            except OSError:
                pass


def _built_run(root: Path) -> None:
    """报告目录里只剩建成的 run：两个文件是创建者写的字节。"""
    assert os.listdir(root) == ["r"]
    assert {n: (root / "r" / n).read_bytes() for n in os.listdir(root / "r")} == {
        "run_meta.json": b"meta", "run_state.json": b"state"}


@pytest.mark.real_filesystem
def test_a_sweep_between_the_creators_mkdir_and_open_makes_the_creator_retry_under_a_new_name(tmp_path):
    """清理方在创建者建出暂存目录之后、打开之前删去它：清理方 removed；创建者打开得到「不存在」，换名，第二个名字建成 run。"""
    root = tmp_path / "runs"
    creator = _StagedCreator(tmp_path, ["after-mkdir"])
    try:
        first = creator.next()["name"]
        assert run_dir.sweep_staging_dir(root, first, dry_run=False) == run_dir.StagingSweep(first, run_dir.StagingOutcome.REMOVED)
        creator.go()
        steps = creator.next()["done"]
        second = steps[2][1]
        assert steps == [["mkdir", first], ["open", "ENOENT"], ["mkdir", second], ["open", "ok"], ["flock", "ok"], ["hold"]]
        assert second != first
        _built_run(root)
        assert _try(root / "r") is LockState.HELD
    finally:
        creator.close()


@pytest.mark.real_filesystem
def test_a_sweep_between_the_creators_open_and_lock_makes_the_creator_retry_under_a_new_name(tmp_path):
    """清理方在创建者打开之后、取锁之前拿到锁、删去、放开：创建者取锁成功而名字已不指向它打开的目录，换名建成。"""
    root = tmp_path / "runs"
    creator = _StagedCreator(tmp_path, ["after-open"])
    try:
        first = creator.next()["name"]
        assert run_dir.sweep_staging_dir(root, first, dry_run=False).outcome is run_dir.StagingOutcome.REMOVED
        creator.go()
        steps = creator.next()["done"]
        second = steps[3][1]
        assert steps == [["mkdir", first], ["open", "ok"], ["flock", "ok"],
                         ["mkdir", second], ["open", "ok"], ["flock", "ok"], ["hold"]]
        _built_run(root)
    finally:
        creator.close()


@pytest.mark.real_filesystem
@pytest.mark.parametrize("dry_run", [False, True], ids=["remove", "dry-run"])
def test_a_creator_that_meets_the_sweepers_lock_gets_held_and_retries_under_a_new_name(tmp_path, monkeypatch, dry_run):
    """清理方持着锁时创建者取锁：创建者得到「已被持有」，换名建成 run。真删的清理方随后删去被丢下的空目录；只看不删的放开之后留下
    那个空的暂存目录，下一次真删时删去。清理方在核对名字（`same_dir` 里的 fstat）那一刻停住、放行创建者，等它建成再继续。"""
    root = tmp_path / "runs"
    creator = _StagedCreator(tmp_path, ["after-open"])
    try:
        first = creator.next()["name"]
        real_fstat = os.fstat
        seen: list = []

        def fstat(fd):
            if not seen:
                assert _try(root / first) is LockState.HELD  # 清理方此刻持锁
                seen.append(fd)
                creator.go()
                seen.append(creator.next()["done"])
            return real_fstat(fd)

        monkeypatch.setattr(os, "fstat", fstat)
        swept = run_dir.sweep_staging_dir(root, first, dry_run=dry_run)
        monkeypatch.setattr(os, "fstat", real_fstat)
        steps = seen[1]
        second = steps[3][1]
        assert steps == [["mkdir", first], ["open", "ok"], ["flock", "held"],
                         ["mkdir", second], ["open", "ok"], ["flock", "ok"], ["hold"]]
        if dry_run:
            assert swept == run_dir.StagingSweep(first, run_dir.StagingOutcome.WOULD_REMOVE)
            assert sorted(os.listdir(root)) == sorted([first, "r"]) and os.listdir(root / first) == []
            assert run_dir.sweep_staging_dir(root, first, dry_run=False).outcome is run_dir.StagingOutcome.REMOVED
        else:
            assert swept == run_dir.StagingSweep(first, run_dir.StagingOutcome.REMOVED)
        _built_run(root)
        assert _try(root / "r") is LockState.HELD
    finally:
        creator.close()


@pytest.mark.real_filesystem
def test_a_staging_directory_whose_creator_is_writing_is_skipped_as_held(tmp_path):
    """创建者写完两个文件、改名之前：清理方得到「已被持有」，什么都不删；创建者随后照常改名建成。"""
    root = tmp_path / "runs"
    creator = _StagedCreator(tmp_path, ["before-rename"])
    try:
        first = creator.next()["name"]
        before = _tree(root)
        assert run_dir.sweep_staging_dir(root, first, dry_run=False) == run_dir.StagingSweep(
            first, run_dir.StagingOutcome.SKIPPED, run_dir.StagingSkip.HELD)
        assert _tree(root) == before
        creator.go()
        assert creator.next()["done"][-1] == ["hold"]
        _built_run(root)
    finally:
        creator.close()


@pytest.mark.real_filesystem
def test_a_descriptor_opened_before_the_creator_renamed_fails_the_check_and_deletes_nothing(tmp_path, monkeypatch):
    """清理方在创建者持锁期间打开了暂存目录；在它试拿之前，创建者改名成 run 并退出：清理方此前打开的描述符拿到锁，但名字已不指向
    它打开的目录，不删、不列出（返回 None）；run 目录与两个文件完好。清理方在对这次打开做边界检查的那一刻停住，等创建者建成并退出。"""
    root = tmp_path / "runs"
    creator = _StagedCreator(tmp_path, ["before-rename"])
    try:
        first = creator.next()["name"]

        def filesystem_type(fd):
            creator.go()
            assert creator.next()["done"][-1] == ["hold"]
            creator.finish()
            return _REAL_FILESYSTEM_TYPE(fd)

        monkeypatch.setattr(run_dir, "filesystem_type", filesystem_type)
        assert run_dir.sweep_staging_dir(root, first, dry_run=False) is None
        _built_run(root)
        assert _try(root / "r") is LockState.ACQUIRED  # 建 run 的进程已退出：上面的 None 不是因为拿不到锁
    finally:
        creator.close()


@pytest.mark.real_filesystem
def test_a_staging_directory_left_by_a_killed_creator_is_cleared_and_a_dry_run_leaves_it(tmp_path):
    """创建者在改名之前被 SIGKILL：留下带两个文件的暂存目录，锁随进程释放；只看不删给出「会删除」、目录原样；真删时删去。"""
    root = tmp_path / "runs"
    creator = _StagedCreator(tmp_path, ["before-rename"])
    try:
        first = creator.next()["name"]
        creator.proc.kill()
        creator.proc.wait(timeout=_TIMEOUT_S)
        before = _tree(root)
        assert before == {first: None, f"{first}/run_meta.json": b"meta", f"{first}/run_state.json": b"state"}
        assert run_dir.sweep_staging_dir(root, first, dry_run=True) == run_dir.StagingSweep(
            first, run_dir.StagingOutcome.WOULD_REMOVE)
        assert _tree(root) == before
        assert run_dir.sweep_staging_dir(root, first, dry_run=False) == run_dir.StagingSweep(first, run_dir.StagingOutcome.REMOVED)
        assert os.listdir(root) == []
    finally:
        creator.close()


# 清理方：把 os.unlink 包一层（被包的原语照样真实执行），删到第 pause_after 个文件时报告并停住，等着被杀。只用 ASCII
_PAUSING_SWEEPER = r"""
import json, os, sys, time
from pathlib import Path
from gherkai_core.adapters.run_store import run_dir
a = json.loads(sys.argv[1])
real_unlink = os.unlink
count = [0]

def unlink(*args, **kwargs):
    real_unlink(*args, **kwargs)
    count[0] += 1
    if count[0] == a["pause_after"]:
        sys.stdout.write("paused\n")
        sys.stdout.flush()
        time.sleep(120)

os.unlink = unlink
run_dir.sweep_staging_dir(Path(a["root"]), a["name"], dry_run=False)
"""


@pytest.mark.real_filesystem
def test_a_sweeper_killed_midway_leaves_the_rest_unlocked_and_the_next_sweep_removes_it(tmp_path):
    """清理方在删除中途被 SIGKILL（300 个文件删到 100 个）：目录与余下的 200 个文件留下，锁随进程释放；下一次清理删去。"""
    root = tmp_path / "runs"
    path = _make_staging(root, files=300)
    args = {"root": str(root), "name": path.name, "pause_after": 100}
    proc = subprocess.Popen([sys.executable, "-I", "-c", _PAUSING_SWEEPER, json.dumps(args)],
                            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        assert proc.stdout.readline() == "paused\n", proc.stderr.read()
        assert _try(path) is LockState.HELD  # 删除期间持着锁
        proc.kill()
        proc.wait(timeout=_TIMEOUT_S)
        assert len(os.listdir(path)) == 200
        assert _try(path) is LockState.ACQUIRED
        assert run_dir.sweep_staging_dir(root, path.name, dry_run=False).outcome is run_dir.StagingOutcome.REMOVED
        assert os.listdir(root) == []
    finally:
        if proc.poll() is None:
            proc.kill()
        proc.wait(timeout=_TIMEOUT_S)
        proc.stdout.close()
        proc.stderr.close()
