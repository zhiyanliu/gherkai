"""本机 run 目录：边界检查、生命期锁、建 run 的暂存与改名（`adapters/run_store/run_dir`；ADR 0030 决定四，ADR 0054 决策三、四）。

断言落在真实的文件系统与内核上：报告目录里有哪些名字、文件的字节、是不是同一个 inode、另开一次取锁得到什么。故障注入只换边界上的
原语（`os.mkdir`、`os.open`、`os.rename`、`os.replace`、`fcntl.flock`），被换的原语照样真实执行；模拟清理方插进来时做的也是真实
动作（真的删目录、真的另开一次取锁）。

边界检查取文件系统类型的那一步由 conftest 换成本平台清单的第一项，结论不依赖宿主的文件系统；带 `real_filesystem` 标记的用例
用宿主真实的类型，起真实进程的用例都带这个标记（子进程里没有替换）。
"""
from __future__ import annotations

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


# ---- 改名的目标与改名前后的异常 ----


@pytest.mark.parametrize("after", [True, False], ids=["after-rename", "before-rename"])
@pytest.mark.parametrize("detached", [False, True], ids=["foreground", "background"])
def test_an_interrupt_around_the_rename_is_judged_by_what_the_filesystem_shows(tmp_path, monkeypatch, lock_holder, after, detached):
    """Ctrl-C 引起的异常落在改名之后：run 目录已以标识出现，异常照常抛出，持有者收下描述符，另开一次得到「已被持有」，两个文件完整、
    没有暂存目录。落在改名之前：没有 run 目录，暂存目录已删去，持有者什么都没收到。"""
    real_rename = os.rename

    def rename(src, dst, *args, **kwargs):
        if _staging(src):
            if after:
                real_rename(src, dst, *args, **kwargs)
            raise KeyboardInterrupt
        return real_rename(src, dst, *args, **kwargs)

    monkeypatch.setattr(os, "rename", rename)
    root = tmp_path / "runs"
    store = LocalRunStore(root, detached=detached, lock_holder=lock_holder)
    with pytest.raises(KeyboardInterrupt):
        store.create_run(_meta("r"), _pending("r"))
    if after:
        assert os.listdir(root) == ["r"]
        assert sorted(os.listdir(root / "r")) == ["run_meta.json", "run_state.json"]
        assert store.load_run_state("r") == _pending("r") and store.is_detached("r") is detached
        [fd] = lock_holder.fds
        assert _same_inode(fd, root / "r") and _try(root / "r") is LockState.HELD
    else:
        assert os.listdir(root) == []
        assert lock_holder.fds == []


@pytest.mark.parametrize("where", ["mkdir", "open"])
def test_an_interrupt_right_after_the_staging_directory_is_made_or_opened_leaves_nothing(tmp_path, monkeypatch, lock_holder, where):
    """异常在建出暂存目录、或打开它之后才从那一次调用里抛出（信号在系统调用期间到达）：暂存目录已删去，报告目录里什么都不留。"""
    real_mkdir, real_open = os.mkdir, os.open
    opened: list[int] = []

    def mkdir(path, *args, **kwargs):
        real_mkdir(path, *args, **kwargs)
        if where == "mkdir" and _staging(path):
            raise KeyboardInterrupt

    def open_(path, flags, *args, **kwargs):
        fd = real_open(path, flags, *args, **kwargs)
        if where == "open" and _staging(path):
            opened.append(fd)
            raise KeyboardInterrupt
        return fd

    monkeypatch.setattr(os, "mkdir", mkdir)
    monkeypatch.setattr(os, "open", open_)
    root = tmp_path / "runs"
    try:
        with pytest.raises(KeyboardInterrupt):
            LocalRunStore(root, lock_holder=lock_holder).create_run(_meta("r"), _pending("r"))
        assert os.listdir(root) == []
        assert lock_holder.fds == []
    finally:
        for fd in opened:
            os.close(fd)


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
