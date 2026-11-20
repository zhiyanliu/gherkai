"""本机 run 目录的存储形态：名字规则、建 run 的暂存与改名、生命期锁、边界检查（ADR 0030 决定四，ADR 0054 决策三、四）。

- **名字规则**（`is_run_name`）：run 标识即 run 目录的名字，读写两侧共用同一条规则。以点开头的名字留给暂存目录，列举与按
  标识的读写都不认它们，建 run 也拒绝这样的标识。
- **建 run**（`create_run_dir`）：先对报告目录做一次边界检查；再在报告目录里建暂存目录（`STAGING_PREFIX` 加随机尾），以只读
  方式打开它，对这次打开的描述符做边界检查、取排他的 `flock`，核对名字仍指向打开的那个目录；然后写记录，写完才原子改名成
  run 标识，最后把描述符交给持有者。锁随这次打开留在改名之后的 run 目录上；取锁与写两个文件都在改名之前做，试拿的一方只碰以
  run 标识命名的目录（先改名、后取锁的问题见 ADR 0054「被拒方案」）。
- **换名**：暂存目录建不出（名字已被占用）、打开时已不存在、取锁得到「已被持有」（另一个进程正在处理它）、或拿到锁之后名字已
  不指向它时，换一个名字重来，至多 `STAGING_ATTEMPTS` 次；都不成即 `StagingContended`。
- **持有者**（`LockHolder`）：收下持锁的描述符。生产用的 `HoldUntilExit` 不关闭也不交出它，锁随进程退出释放；构造
  `LocalRunStore` 时注入，不带持有者的 store 不能建 run。
- **边界检查**（`check_fd`、`check_report_dir`）：对打开的目录的描述符取文件系统类型（由内核解析路径），只放行
  `ALLOWED_FILESYSTEMS` 里本平台的类型；判断与取锁对同一次打开做。

异常放在这里、不放 `gherkai_core.errors`：它们只属于本机 adapter。`RunAlreadyExists` 仍在 errors 里，由 `create_run_dir` 抛出。
"""
from __future__ import annotations

import ctypes
import errno
import functools
import os
import secrets
import shutil
import sys
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from types import MappingProxyType
from typing import Final, Protocol

from gherkai_core.errors import RunAlreadyExists

STAGING_PREFIX: Final = ".gherkai-creating-"  # 后接 secrets.token_hex(8)
STAGING_ATTEMPTS: Final = 3
# 本机后端放行的文件系统类型，按 sys.platform 分；有序，给使用者的说明里的清单按这个次序拼出。只收照 ADR 0054 决策三的理由
# 实测过的类型，先实测再加（决策四「边界检查」一条）
ALLOWED_FILESYSTEMS: Final[Mapping[str, tuple[str, ...]]] = MappingProxyType({
    "darwin": ("apfs",),
    "linux": ("ext4", "tmpfs", "overlay", "xfs", "btrfs", "ext3"),
})

# 判断不了时的原因片段（产品语言，`BoundaryCheck.unknown_reason` 与 `FilesystemUnknown` 的 str() 取这些）
_OTHER_PLATFORM = "这个平台不是 macOS 或 Linux"
_INCOMPLETE = "系统返回的文件系统信息不完整"
_NO_MOUNT = "挂载信息里找不到这个目录所在的挂载"


def is_run_name(name: str) -> bool:
    """本机 run 目录的名字规则，读写两侧共用：非空、不以「.」开头、不含「/」（ADR 0030 决定四「run 标识即 run 目录的名字」条）。"""
    return bool(name) and not name.startswith(".") and "/" not in name


# ---- 边界检查（ADR 0054 决策四） ----

class Boundary(Enum):
    INSIDE = "inside"
    OUTSIDE = "outside"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class BoundaryCheck:
    """一次边界检查的结果。判断只看 `verdict`；`unknown_reason` 只作说明。"""

    verdict: Boundary
    requested: str               # 要判断的目录（报告目录）
    checked: str                 # 实际打开并判断的目录：requested 不存在时为最近一层已存在的上级
    fs_type: str | None          # 检测到的类型；UNKNOWN 时为 None
    unknown_reason: str | None   # UNKNOWN 时的原因（产品语言片段）


class FilesystemUnknown(Exception):
    """`filesystem_type` 判断不了：str() 即原因片段（产品语言）。"""


class _StatFS(ctypes.Structure):
    """macOS 64 位 inode 形态的 `struct statfs`（<sys/mount.h>），2168 字节：`f_flags` 在偏移 64、`f_fstypename` 在 72、
    `f_mntonname` 在 88。x86_64 上的符号是 `fstatfs$INODE64`、arm64 上是 `fstatfs`，两者结构大小与各字段偏移相同（ADR 0054
    决策四 macOS 一条）。布局出错时读回的两项核对（`_darwin_fs_type`）不过，结果是判断不了，不会变成放行。"""

    _fields_ = [
        ("f_bsize", ctypes.c_uint32),
        ("f_iosize", ctypes.c_int32),
        ("f_blocks", ctypes.c_uint64),
        ("f_bfree", ctypes.c_uint64),
        ("f_bavail", ctypes.c_uint64),
        ("f_files", ctypes.c_uint64),
        ("f_ffree", ctypes.c_uint64),
        ("f_fsid", ctypes.c_int32 * 2),
        ("f_owner", ctypes.c_uint32),
        ("f_type", ctypes.c_uint32),
        ("f_flags", ctypes.c_uint32),
        ("f_fssubtype", ctypes.c_uint32),
        ("f_fstypename", ctypes.c_char * 16),
        ("f_mntonname", ctypes.c_char * 1024),
        ("f_mntfromname", ctypes.c_char * 1024),
        ("f_reserved", ctypes.c_uint32 * 8),
    ]


@functools.cache
def _darwin_fstatfs():
    """libc 的 fstatfs：先找 `fstatfs$INODE64`，找不到再用 `fstatfs`。都没有时返回 None。"""
    libc = ctypes.CDLL(None, use_errno=True)
    for name in ("fstatfs$INODE64", "fstatfs"):
        try:
            fn = libc[name]
        except AttributeError:
            continue
        fn.argtypes = (ctypes.c_int, ctypes.POINTER(_StatFS))
        fn.restype = ctypes.c_int
        return fn
    return None


def _darwin_fs_type(fd: int) -> str:
    fstatfs = _darwin_fstatfs()
    if fstatfs is None:
        raise FilesystemUnknown("查询文件系统失败：系统库里没有 fstatfs")
    buf = _StatFS()
    if fstatfs(fd, ctypes.byref(buf)) != 0:
        raise FilesystemUnknown(f"查询文件系统失败：{os.strerror(ctypes.get_errno())}")
    name = buf.f_fstypename  # c_char 数组读出的是第一个 NUL 之前的字节
    # 读回之后核两项：类型名非空且是可打印 ASCII，挂载点以 / 开头。不合即判断不了（布局出错只会变成拒绝）
    if not name or not all(0x21 <= b <= 0x7E for b in name) or not buf.f_mntonname.startswith(b"/"):
        raise FilesystemUnknown(_INCOMPLETE)
    return name.decode("ascii")


def _fs_type_from_proc(fdinfo: str, mountinfo: str) -> str:
    """Linux：由 `/proc/self/fdinfo/<fd>` 的 `mnt_id:` 行，在 `/proc/self/mountinfo` 里取第一字段等于它的那一行，返回分隔字段
    `-` 之后的第一个字段（文件系统类型）。判断不了时抛 `FilesystemUnknown`。

    mountinfo 一行的字段以单个空格分隔：挂载 ID、父 ID、设备号、根、挂载点、挂载选项、零到多个可选字段、`-`、类型、来源、超级块
    选项。路径里的空格转义为 `\\040`，所以按空格切分是安全的；可选字段的形态是 `tag[:value]`，不会是 `-`，根与挂载点都以 `/`
    开头，所以分隔字段从第 7 个字段起找第一个 `-`。"""
    mnt_id = None
    for line in fdinfo.splitlines():
        if line.startswith("mnt_id:"):
            mnt_id = line[len("mnt_id:"):].strip()
            break
    if not mnt_id:
        raise FilesystemUnknown(_INCOMPLETE)
    for line in mountinfo.splitlines():
        fields = line.split(" ")
        if fields[0] != mnt_id:
            continue
        try:
            sep = fields.index("-", 6)
        except ValueError:
            raise FilesystemUnknown(_INCOMPLETE) from None
        fs_type = fields[sep + 1] if sep + 1 < len(fields) else ""
        if not fs_type:
            raise FilesystemUnknown(_INCOMPLETE)
        return fs_type
    raise FilesystemUnknown(_NO_MOUNT)


def _linux_fs_type(fd: int) -> str:
    try:
        with open(f"/proc/self/fdinfo/{fd}", encoding="utf-8", errors="surrogateescape") as f:
            fdinfo = f.read()
        with open("/proc/self/mountinfo", encoding="utf-8", errors="surrogateescape") as f:
            mountinfo = f.read()
    except OSError as e:
        raise FilesystemUnknown(f"读不到挂载信息：{e.strerror or e}") from e
    return _fs_type_from_proc(fdinfo, mountinfo)


def filesystem_type(fd: int) -> str:
    """打开的目录的描述符所在的文件系统类型（macOS 由 fstatfs，Linux 由描述符的挂载 ID 在挂载表里取）。判断不了时抛
    `FilesystemUnknown`。测试替换这个模块属性，让结论不依赖宿主的文件系统；`check_fd` 每次调用时按名字取它。"""
    if sys.platform == "darwin":
        return _darwin_fs_type(fd)
    if sys.platform == "linux":
        return _linux_fs_type(fd)
    raise FilesystemUnknown(_OTHER_PLATFORM)


def check_fd(fd: int, *, requested: str, checked: str) -> BoundaryCheck:
    """对打开的目录的描述符做边界检查：类型在本平台的清单里为 INSIDE、不在为 OUTSIDE，判断不了为 UNKNOWN（带原因）。"""
    allowed = ALLOWED_FILESYSTEMS.get(sys.platform)
    if allowed is None:
        return BoundaryCheck(Boundary.UNKNOWN, requested, checked, None, _OTHER_PLATFORM)
    try:
        fs_type = filesystem_type(fd)
    except FilesystemUnknown as e:
        return BoundaryCheck(Boundary.UNKNOWN, requested, checked, None, str(e))
    verdict = Boundary.INSIDE if fs_type in allowed else Boundary.OUTSIDE
    return BoundaryCheck(verdict, requested, checked, fs_type, None)


def check_report_dir(path: Path) -> BoundaryCheck:
    """对报告目录做边界检查，什么都不建。从 path 起逐层向上以只读方式打开目录：只有「不存在」（FileNotFoundError，含悬空的
    符号链接）才取上一层；别的打开失败（路径上有文件、没有权限、符号链接成环）原样抛出，由调用方按写记录失败报出——那是权限
    或路径的问题，按「换到本机磁盘」说会误导（ADR 0054 决策四「边界检查」一条）。打开成功即对它判断、关闭。"""
    requested = str(path)
    current = path
    while True:
        try:
            fd = os.open(current, os.O_RDONLY | os.O_DIRECTORY)
        except FileNotFoundError:
            parent = current.parent
            if parent == current:
                raise
            current = parent
            continue
        try:
            return check_fd(fd, requested=requested, checked=str(current))
        finally:
            os.close(fd)


# ---- 生命期锁（ADR 0054 决策三） ----

class LockState(Enum):
    ACQUIRED = "acquired"
    HELD = "held"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True)
class LockAttempt:
    state: LockState
    error: OSError | None        # UNAVAILABLE 时的原错误


def try_lock(fd: int) -> LockAttempt:
    """不阻塞地对描述符取排他的 flock。成功为 ACQUIRED；`EWOULDBLOCK` 为 HELD（别的打开持有它，同一进程的另一次打开也算）；
    其余错误一律 UNAVAILABLE，带原错误（ADR 0054 决策三「结果的判读」）。"""
    import fcntl  # 只在本机后端真正取锁时需要；模块本身在没有 fcntl 的平台上也能导入

    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError as e:
        if e.errno == errno.EWOULDBLOCK:
            return LockAttempt(LockState.HELD, None)
        return LockAttempt(LockState.UNAVAILABLE, e)
    return LockAttempt(LockState.ACQUIRED, None)


def same_dir(fd: int, path: Path) -> bool:
    """path 这个名字是否仍指向 fd 打开的那个目录：`fstat(fd)` 与 `lstat(path)` 的 (st_dev, st_ino) 相同。path 取不到（任何
    OSError）即 False。取 lstat：名字本身得是那个目录，指向它的符号链接不算。"""
    try:
        st = os.stat(path, follow_symlinks=False)
    except OSError:
        return False
    fst = os.fstat(fd)
    return (fst.st_dev, fst.st_ino) == (st.st_dev, st.st_ino)


class LockHolder(Protocol):
    def hold(self, fd: int) -> None:
        """收下持锁的描述符；收下之后建 run 的一方不再关闭它。"""
        ...


class HoldUntilExit:
    """生产用的持有者：收下的描述符不再关闭，锁随进程退出释放。没有放开的方法，也不交出描述符，所以锁描述符到不了子进程的
    `pass_fds`（ADR 0054 决策三「不被子进程继承」）。"""

    def __init__(self) -> None:
        self._held: list[int] = []  # 只记下，不关闭、不交出

    def hold(self, fd: int) -> None:
        self._held.append(fd)


# ---- 建 run 失败时的异常（本机 adapter 特有；调用方据类型分别说明，见 ADR 0031 决定五「退出码 2」） ----

class RunDirRejected(Exception):
    """边界检查不过：报告目录所在的文件系统不在本平台的清单里，或判断不了（ADR 0054 决策四）。不是 OSError：它不是写失败，
    处理办法是换报告目录。`check` 带检查的结果，说明由调用方据它生成。"""

    def __init__(self, check: BoundaryCheck) -> None:
        if check.verdict is Boundary.OUTSIDE:
            text = f"报告目录 {check.requested} 所在的文件系统是 {check.fs_type}，本机后端不支持，没有建立 run"
        else:
            text = f"无法判断报告目录 {check.requested} 所在的文件系统（{check.unknown_reason}），没有建立 run"
        super().__init__(text)
        self.check = check


class LifetimeLockUnavailable(OSError):
    """在暂存目录上取锁出错、且不是「已被持有」：`OSError(errno, strerror, <报告目录>)`，错误码与文字取 flock 的原错误。"""


class StagingContended(Exception):
    """暂存目录连续 `STAGING_ATTEMPTS` 次被别的进程持有或换掉，没有建立 run。"""

    def __init__(self, root: str, attempts: int) -> None:
        super().__init__(f"在报告目录 {root} 里准备 run 的目录时，连续 {attempts} 次遇到另一个进程同时在处理同一个暂存目录")
        self.root = root
        self.attempts = attempts


# ---- 建 run：暂存、取锁、写、改名（ADR 0030 决定四，ADR 0054 决策三） ----

class _Staging:
    """这次建 run 已经占下的暂存目录与它的描述符。路径在建目录之前记下，描述符在打开之后立刻记下，`create_run_dir` 的保护区
    据它收拾：保护区从建暂存目录之前就开始，所以任何一步收到异常（含 KeyboardInterrupt），已建出的目录与已打开的描述符都有去处。"""

    def __init__(self) -> None:
        self.path: Path | None = None
        self.fd: int | None = None
        self.locked = False

    def forget(self) -> int | None:
        """放下当前这个暂存目录、不动它（它已不是自己的，或换名重来）：先清掉记录、再交回描述符由调用方关闭，所以清掉记录之后
        才到的异常不会让 `discard` 去碰一个已关闭的号。"""
        fd, self.fd, self.path, self.locked = self.fd, None, None, False
        return fd

    def discard(self) -> None:
        """删去自己的暂存目录并关闭描述符。描述符已打开时，名字仍指向打开的那个目录才删：持着锁时连同里面的文件删去（清理方
        拿不到它），还没取到锁时只删空目录；描述符还没打开时只删空目录。"""
        path, locked = self.path, self.locked
        fd = self.forget()
        if fd is not None:
            try:
                if path is not None and same_dir(fd, path):
                    if locked:
                        shutil.rmtree(path, ignore_errors=True)
                    else:
                        _rmdir_quietly(path)
            finally:
                os.close(fd)
        elif path is not None:
            _rmdir_quietly(path)


def _rmdir_quietly(path: Path) -> None:
    try:
        os.rmdir(path)
    except OSError:
        pass


def _claim_staging(root: Path, staging: _Staging) -> None:
    """在报告目录里占下一个暂存目录：建出、打开、对描述符做边界检查、取锁、核对名字仍指向它。成功时 staging 记着路径与持锁的
    描述符；失败抛出时由调用方的保护区按 staging 收拾。"""
    import fcntl

    for _ in range(STAGING_ATTEMPTS):
        path = root / f"{STAGING_PREFIX}{secrets.token_hex(8)}"
        # 建之前先记下：信号引起的异常（如 Ctrl-C）可能在 mkdir 已建出目录之后才从这一次调用里抛出，先记下才删得掉它。没有
        # 建出时收拾一步按这个名字删空目录，名字带 64 位随机尾，删到的只可能是自己的；建不出时立刻清掉记录，撞名时不碰别人的目录
        staging.path = path
        try:
            os.mkdir(path)
        except OSError as e:
            staging.path = None
            if isinstance(e, FileExistsError):
                continue  # 名字已被占用：不是自己的，不动它，换名
            raise
        try:
            fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)  # 不可继承（PEP 446）
        except FileNotFoundError:
            staging.forget()  # 建出之后、打开之前已被删去
            continue
        staging.fd = fd
        # 判断与取锁对同一次打开：打开之后路径上的变化（盖上挂载、换掉符号链接）不改变这个描述符所在的文件系统
        check = check_fd(fd, requested=str(root), checked=str(root))
        if check.verdict is not Boundary.INSIDE:
            raise RunDirRejected(check)
        attempt = try_lock(fd)
        if attempt.state is LockState.UNAVAILABLE:
            err = attempt.error
            raise LifetimeLockUnavailable(err.errno, err.strerror, str(root)) from err
        if attempt.state is LockState.ACQUIRED and same_dir(fd, path):
            staging.locked = True
            if fd < 3:
                # 后台推进进程回报之后把日志接到 0、1、2 号上，改接会关掉这几个号上原来的打开，锁落在其中一个号上就随之放开、
                # 没有任何报错（ADR 0054 决策三「持锁的描述符」）。锁随打开的文件描述走，复制到 3 号以上再关掉原号即可
                staging.fd = fcntl.fcntl(fd, fcntl.F_DUPFD_CLOEXEC, 3)
                os.close(fd)
            return
        # 另一个进程持有它（清理方，含只看不删的那一种），或拿到锁时名字已不指向它（取锁之前已被删去、换掉）：不动它，换名
        os.close(staging.forget())
    raise StagingContended(str(root), STAGING_ATTEMPTS)


def create_run_dir(root: Path, run_id: str, write: Callable[[Path], None], *, holder: LockHolder) -> None:
    """建一个本机 run 目录：边界检查，在暂存目录上取锁，`write(暂存目录)` 写记录，原子改名成 `root/run_id`，描述符交给
    `holder`（次序与理由见模块头）。调用方先核过 run_id 符合 `is_run_name`。

    失败时：报告目录检查不过抛 `RunDirRejected`，什么目录都不建；对暂存目录描述符的检查不过同样抛它，删去这个空目录；取锁出错
    （不是「已被持有」）抛 `LifetimeLockUnavailable`，删去这个空目录；换名用尽抛 `StagingContended`，别的进程持有的暂存目录不动；
    改名的目标已是非空目录抛 `RunAlreadyExists`，目标不变；写失败、改名以别的错误失败（目标是文件、符号链接或挂载点）时 OSError
    原样抛出，改名的错误把文件名换成 run 目录的路径。除改名已经成了的情形，这些失败都删去自己的暂存目录、关闭描述符。

    改名之后才到的异常（如 Ctrl-C 引起的 KeyboardInterrupt）按文件系统里的事实判断：run 目录的名字已指向持锁的那个目录，即
    run 已建成，描述符照样交给持有者、不关、不删，再把异常抛出。不靠标志变量，所以与改名返回之前还是之后收到异常无关。"""
    check = check_report_dir(root)
    if check.verdict is not Boundary.INSIDE:
        raise RunDirRejected(check)
    root.mkdir(parents=True, exist_ok=True)  # 路径上有悬空的符号链接时抛 FileExistsError、什么都不建：按写记录失败报出
    final = root / run_id
    staging = _Staging()
    try:
        _claim_staging(root, staging)
        write(staging.path)
        try:
            os.rename(staging.path, final)
        except OSError as e:
            if e.errno in (errno.ENOTEMPTY, errno.EEXIST):
                raise RunAlreadyExists(run_id) from e
            raise OSError(e.errno, e.strerror, str(final)) from e  # 按错误码还原子类（NotADirectoryError 等）
    except BaseException:
        if staging.fd is not None and same_dir(staging.fd, final):
            holder.hold(staging.forget())  # 改名已经成了：run 完整，锁不放
        else:
            staging.discard()
        raise
    holder.hold(staging.forget())
