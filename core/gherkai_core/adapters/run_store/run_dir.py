"""本机 run 目录的存储形态：名字规则、建 run 的暂存与改名、生命期锁、边界检查、试拿与清理暂存目录（ADR 0030 决定四，ADR 0054
决策三、四）。

- **名字规则**（`is_run_name`）：run 标识即 run 目录的名字，读写两侧共用同一条规则。以点开头的名字留给暂存目录，列举与按
  标识的读写都不认它们，建 run 也拒绝这样的标识；按文件系统编码超过 `RUN_NAME_MAX_BYTES` 字节的名字同样不是 run 标识。
  暂存目录的名字形态（`staging_name` 生成、`is_staging_name` 认）只在这里定义，建 run 的一方与清理方共用。
- **建 run**（`create_run_dir`）：先对报告目录做一次边界检查；再在报告目录里建暂存目录（`staging_name`），以只读
  方式打开它，对这次打开的描述符做边界检查、取排他的 `flock`，核对名字仍指向打开的那个目录；然后写记录，写完才原子改名成
  run 标识，最后把描述符交给持有者。锁随这次打开留在改名之后的 run 目录上；取锁与写两个文件都在改名之前做，试拿的一方只碰以
  run 标识命名的目录（先改名、后取锁的问题见 ADR 0054「被拒方案」）。入口里只处理同步的失败：前台 `run` 在这一次调用期间推迟
  SIGINT，后台推进进程对 SIGINT 取缺省处置、收到即结束（ADR 0054 决策三），调用不被异步的异常打断。
- **换名**：暂存目录建不出（名字已被占用）、打开时已不存在、取锁得到「已被持有」（另一个进程正在处理它）、或拿到锁之后名字已
  不指向它时，换一个名字重来，至多 `STAGING_ATTEMPTS` 次；都不成即 `StagingContended`。
- **持有者**（`LockHolder`）：收下持锁的描述符。生产用的 `HoldUntilExit` 不关闭也不交出它，锁随进程退出释放；构造
  `LocalRunStore` 时注入，不带持有者的 store 不能建 run。锁不被子进程带着：经 exec 启动的子进程靠描述符不可继承，fork 而不 exec 的
  子进程靠 `HoldUntilExit` 登记的 fork 钩子在子进程里关掉那一份；钩子先核对这个号仍指向持锁的目录（号被关闭并另作他用时不关到别的
  打开），不经解释器的 fork 不触发它（ADR 0054 决策三「不被子进程继承」）。
- **边界检查**（`check_fd`、`check_report_dir`、`check_existing_dir`）：对打开的目录的描述符取文件系统类型（由内核解析路径），只放行
  `ALLOWED_FILESYSTEMS` 里本平台的类型；判断与取锁对同一次打开做。
- **试拿**（`probe_run_dir`，处置的一方用）：以只读方式打开 run 目录，对这次打开做边界检查，过了才不阻塞地试拿，持有到块结束
  （ADR 0054 决策三「谁在何时试拿」与「结果的判读」）。
- **清理暂存目录**（`staging_names`、`sweep_staging_dir`，`settle-runs` 不给 run 标识时用）：只认 `is_staging_name` 的形态、本身是
  目录的条目；打开、边界检查、试拿、核对名字仍指向打开的目录，都过了才持着锁删去（ADR 0054 决策三「谁在何时试拿」）。

异常放在这里、不放 `gherkai_core.errors`：它们只属于本机 adapter。`RunAlreadyExists` 仍在 errors 里，由 `create_run_dir` 抛出。
"""
from __future__ import annotations

import ctypes
import errno
import functools
import os
import re
import secrets
import shutil
import stat
import sys
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from types import MappingProxyType
from typing import Final, Protocol

from gherkai_core.errors import RunAlreadyExists

STAGING_PREFIX: Final = ".gherkai-creating-"
# 暂存目录名字里随机尾的长度：16 个小写十六进制字符（64 位）。同一个报告目录里两个创建者的名字不相撞是前提（ADR 0054 决策三
# 「删去自己的暂存目录只凭自己那次打开」一条），不为相撞另设防
STAGING_TAIL_HEX: Final = 16
_STAGING_TAIL = re.compile(f"[0-9a-f]{{{STAGING_TAIL_HEX}}}")
STAGING_ATTEMPTS: Final = 3
# 一层目录名的长度上限，按文件系统编码的字节数计：Linux 清单里的类型以 255 字节为限，APFS 以 255 个 UTF-16 代码单元为限；一个字符的
# UTF-8 字节数不少于它的 UTF-16 代码单元数，所以 255 字节之内的名字在两个平台上都建得出（ADR 0030 决定四「run 标识即 run 目录的
# 名字」条）。只管一层名字：整条路径的长度由入口对报告目录的检查管（同一决定「报告目录的路径长度」条）
RUN_NAME_MAX_BYTES: Final = 255
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
_NO_QUERY = "查询文件系统失败：系统库里没有查询文件系统的接口"


def is_run_name(name: str) -> bool:
    """本机 run 目录的名字规则，读写两侧共用：非空、不以「.」开头、不含「/」、按文件系统编码不超过 `RUN_NAME_MAX_BYTES` 字节
    （ADR 0030 决定四「run 标识即 run 目录的名字」条）。超长的名字按 run 不存在处理，读写入口因此不会因这一层名字太长而失败（整条
    路径的长度不在这里管）；编码不出来的名字同样不是 run 标识。"""
    if not name or name.startswith(".") or "/" in name:
        return False
    try:
        return len(os.fsencode(name)) <= RUN_NAME_MAX_BYTES
    except UnicodeEncodeError:
        return False


def staging_name() -> str:
    """新的暂存目录名字：`STAGING_PREFIX` 加 `STAGING_TAIL_HEX` 个小写十六进制字符的随机尾。建 run 的一方只用它生成名字。"""
    return STAGING_PREFIX + secrets.token_hex(STAGING_TAIL_HEX // 2)


def is_staging_name(name: str) -> bool:
    """name 是不是 `staging_name` 生成的形态：前缀之后恰好 `STAGING_TAIL_HEX` 个小写十六进制字符。清理方只认这个形态，使用者恰好
    以前缀起名的目录（如 `.gherkai-creating-user-named`）不碰（ADR 0054 决策三「谁在何时试拿」）。"""
    return name.startswith(STAGING_PREFIX) and _STAGING_TAIL.fullmatch(name[len(STAGING_PREFIX):]) is not None


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
        raise FilesystemUnknown(_NO_QUERY)
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


def check_existing_dir(path: Path) -> BoundaryCheck | None:
    """对一个应当已经存在的目录做边界检查，什么都不建：以只读方式打开 path 本身（不向上找上级），对描述符判断、关闭。打开得到
    「不存在」（FileNotFoundError，含悬空的符号链接）返回 None；别的打开失败（路径上有文件、没有权限、符号链接成环）原样抛出，
    与 `check_report_dir` 的取法相同（ADR 0054 决策四「边界检查」一条）。处置的一方据此判断报告目录：报告目录不存在时没有可处理的
    run，不像建 run 那样改按上级判断。"""
    try:
        fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    except FileNotFoundError:
        return None
    try:
        return check_fd(fd, requested=str(path), checked=str(path))
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
    `pass_fds`，别处也拿不到这个号去把它设为可继承。

    锁按打开的文件描述计，子进程手里还有这次打开的副本时，本进程退出之后锁仍在。子进程不带着它，按起子进程的方式分两条做法
    （ADR 0054 决策三「不被子进程继承」）：
    - 经 exec 启动的子进程（worker）：描述符不可继承，exec 时即没有它。
    - fork 而不 exec 的子进程（直接 fork、fork 方式的 `multiprocessing`、停在 `preexec_fn` 里的子进程）：`hold` 收下描述符时登记一个
      fork 之后在子进程里执行的钩子（`os.register_at_fork`），子进程里关掉自己这一份。关掉子进程里的副本不放开锁，锁仍由本进程的那一份
      持有。

    钩子执行之前先核对这个号仍指向持锁的那个目录（设备号与 inode 与收下时相同）：这个号之后若被关闭并另作他用，钩子不关到别的打开。
    不经解释器的 fork（C 扩展、`ctypes` 直接调系统库）不触发钩子，不在其内。登记之后撤不掉，钩子随进程存在到退出，与持有的期限相同。

    已知的间隔：钩子在 `hold` 被调用时才登记，而锁在 `create_run_dir` 里更早就取到了。两者之间本进程别的线程 fork 而不 exec 出的
    子进程没有这个钩子，会带着锁活过本进程（ADR 0054 决策三「已知的间隔」）。现在不可达：两种推进器在建 run 的这一段不 fork。往持锁
    的进程里加会这样 fork 的线程之前，先按 ADR 0054「重议闸门」里「持锁的进程里出现 fork 而不 exec 的线程」一条处理。"""

    def __init__(self) -> None:
        self._held: list[int] = []  # 只记下，不关闭、不交出

    def hold(self, fd: int) -> None:
        self._held.append(fd)
        try:
            st = os.fstat(fd)
        except OSError:
            # 取不到身份就无从在子进程里核对，不登记钩子。不把错误抛给建 run 的一方：改名已经完成，run 已经建成、锁由这个描述符持有
            return
        os.register_at_fork(after_in_child=functools.partial(_close_in_child, fd, (st.st_dev, st.st_ino)))


def _close_in_child(fd: int, identity: tuple[int, int]) -> None:
    """fork 之后在子进程里执行（`HoldUntilExit.hold` 登记）：fd 仍指向 identity（设备号与 inode）所指的目录才关闭它。核对不过、
    任何 OSError 都什么也不做。"""
    try:
        st = os.fstat(fd)
        if (st.st_dev, st.st_ino) == identity:
            os.close(fd)
    except OSError:
        pass


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
    """这次建 run 已经占下的暂存目录与它的描述符。路径在建出目录之后记下，描述符在打开之后记下，`create_run_dir` 的保护区据它
    收拾：某一步同步地失败时（系统调用报错、写记录的回调抛出），已建出的目录与已打开的描述符都有去处。"""

    def __init__(self) -> None:
        self.path: Path | None = None
        self.fd: int | None = None
        self.locked = False

    def forget(self) -> int | None:
        """放下当前这个暂存目录、不动它（它已不是自己的、换名重来，或已建成 run）：清掉记录，交回描述符，由调用方关闭或交给持有者。"""
        fd, self.fd, self.path, self.locked = self.fd, None, None, False
        return fd

    def discard(self) -> None:
        """删去自己的暂存目录并关闭描述符。删除的依据是自己那次打开：名字仍指向打开的那个目录才删，持着锁时连同里面的文件删去
        （清理方拿不到它），还没取到锁时（对它的边界检查不过、取锁出错）只删空目录。建出了目录而打开没有成功时不删，留给清理方：
        没有打开成功就无从核对这个名字是否仍指向自己建出的那个目录，按名字删可能删到别的进程换上来的目录（ADR 0054 决策三）。"""
        path, locked = self.path, self.locked
        fd = self.forget()
        if fd is None:
            return
        try:
            if path is not None and same_dir(fd, path):
                if locked:
                    shutil.rmtree(path, ignore_errors=True)
                else:
                    _rmdir_quietly(path)
        finally:
            os.close(fd)


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
        path = root / staging_name()
        try:
            os.mkdir(path)
        except FileExistsError:
            continue  # 名字已被占用：那个目录不是自己的，不记下、不动它，换名；别的 OSError 原样抛出
        staging.path = path  # 建出之后才记下：记下的名字只会是自己建出的目录
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
    原样抛出，改名的错误把文件名换成 run 目录的路径；建暂存目录或打开它以别的错误失败时 OSError 原样抛出。这些失败都按
    `_Staging.discard` 删去自己的暂存目录、关闭描述符（建出之后没有打开成功的那一个留给清理方）。

    调用方保证这一次调用不被异步的异常打断（前台 `run` 在调用期间推迟 SIGINT，后台推进进程对 SIGINT 取缺省处置，ADR 0054
    决策三）：保护区只处理同步的失败，改名成功之后到交给持有者之间没有会失败的步骤。

    从在暂存目录上取到锁到 `holder.hold` 之间，别的线程 fork 而不 exec 出的子进程会带着锁（持有者的钩子这时还没有登记）：见
    `HoldUntilExit` 文档串里「已知的间隔」与 ADR 0054 决策三同名一条。"""
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
        staging.discard()
        raise
    holder.hold(staging.forget())


# ---- 试拿：处置的一方打开 run 目录、做边界检查、不阻塞地试拿（ADR 0054 决策三「谁在何时试拿」「结果的判读」） ----

class RunDirGone(Exception):
    """这个名字下已没有 run 目录：打开得到「不存在」（FileNotFoundError 或 NotADirectoryError）。不是 OSError：它不是读写失败，
    处置的一方按这个名字下已没有 run 处理（ADR 0054 决策八「处置的次序」）。"""


@dataclass(frozen=True)
class RunDirProbe:
    """一次试拿的结果。`boundary` 是对这次打开的边界检查；`lock` 是试拿的结果，边界检查不过时为 None（没有试拿）。"""

    boundary: BoundaryCheck
    lock: LockAttempt | None


@contextmanager
def probe_run_dir(path: Path) -> Iterator[RunDirProbe]:
    """以只读方式打开 run 目录 path（跟随符号链接：锁与随后按路径的写落在同一个目录上），对这次打开的描述符做边界检查，INSIDE 才
    不阻塞地试拿；拿到的锁持有到块结束，块结束时关闭描述符、锁随之放开。

    打开得到「不存在」抛 `RunDirGone`；别的打开失败（没有权限、描述符用尽、符号链接成环）原样抛出 OSError：没有打开成功就没有可做
    边界检查与试拿的描述符，它是读写记录失败，不是锁不可用，也不是判断不了文件系统（ADR 0054 决策三「结果的判读」）。

    这里的描述符不登记 fork 钩子（与 `HoldUntilExit` 不同）：它只持有到块结束，处置的一方在块里做结束写与生成报告，不启动子进程；
    描述符本身不可继承，经 exec 启动的子进程拿不到它。"""
    try:
        fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)  # 不可继承（PEP 446）
    except (FileNotFoundError, NotADirectoryError) as e:
        raise RunDirGone(str(path)) from e
    try:
        check = check_fd(fd, requested=str(path), checked=str(path))
        attempt = try_lock(fd) if check.verdict is Boundary.INSIDE else None
        yield RunDirProbe(check, attempt)
    finally:
        os.close(fd)


# ---- 清理暂存目录（ADR 0054 决策三「谁在何时试拿」，决策八「settle-runs」一条） ----

class StagingOutcome(Enum):
    REMOVED = "removed"
    WOULD_REMOVE = "would_remove"
    SKIPPED = "skipped"


class StagingSkip(Enum):
    """跳过一个暂存目录的原因。值即 `settle-runs --json` 里 `staging_dirs[].reason` 的取值。"""

    HELD = "held"                                       # 另一个进程持有它的锁（建 run 的一方，或另一个清理方）
    UNSUPPORTED_FILESYSTEM = "unsupported_filesystem"   # 对这次打开的边界检查不过
    LOCK_UNAVAILABLE = "lock_unavailable"               # 取锁出错，且不是「已被持有」
    UNOPENABLE = "unopenable"                           # 打开它（或读它的属性）以「不存在」之外的错误失败
    REMOVE_FAILED = "remove_failed"                     # 持着锁删除时中途出错，已删去的部分不恢复


@dataclass(frozen=True)
class StagingSweep:
    """对一个暂存目录的处理结果。判断只看 `outcome` 与 `skip`；`boundary`（UNSUPPORTED_FILESYSTEM 时）与 `error`（LOCK_UNAVAILABLE、
    UNOPENABLE、REMOVE_FAILED 时，原错误）只供说明。"""

    name: str
    outcome: StagingOutcome
    skip: StagingSkip | None = None
    boundary: BoundaryCheck | None = None
    error: OSError | None = None


def staging_names(root: Path) -> list[str]:
    """报告目录 root 里合 `is_staging_name` 形态的名字，按名字升序；不看它们是不是目录（`sweep_staging_dir` 逐个核）。root 不存在
    返回空列表；别的列目录失败原样抛出。"""
    try:
        names = os.listdir(root)
    except FileNotFoundError:
        return []
    return sorted(n for n in names if is_staging_name(n))


def sweep_staging_dir(root: Path, name: str, *, dry_run: bool) -> StagingSweep | None:
    """按协议清理 root 里名为 name 的暂存目录（ADR 0054 决策三「谁在何时试拿」）。返回 None 表示这个名字下已不是暂存目录，不列出：
    名字不合 `is_staging_name` 的形态；不在了；不是真实的目录（文件、符号链接，不跟随）；打开时已不存在；拿到锁之后名字已不指向
    打开的那个目录（建它的进程已改名成 run 并退出，或它被换掉，按旧名字删会删错）。

    依次：读名字本身的属性（不跟随符号链接）；以只读方式打开；对这次打开做边界检查，不过即跳过；不阻塞地试拿，被持有、锁不可用都
    跳过；核对名字仍指向打开的那个目录；`dry_run` 时到此为止、给出「会删除」；否则持着锁删去整个目录，删除中途出错即跳过并带上原错误，
    已删去的部分不恢复，下一次接着删。最后关闭描述符，锁随之放开（只看不删的这一次拿到的锁也随即放开）。不看时间、不看内容。

    持着锁时这个名字不会被建 run 的一方改名（它只改名自己持锁的暂存目录），也不会被另一个清理方删去（它试拿得到「已被持有」），
    所以核对之后按名字删的就是打开的那个目录。"""
    if not is_staging_name(name):
        return None
    path = root / name
    try:
        st = os.lstat(path)
    except FileNotFoundError:
        return None
    except OSError as e:
        return StagingSweep(name, StagingOutcome.SKIPPED, StagingSkip.UNOPENABLE, error=e)
    if not stat.S_ISDIR(st.st_mode):
        return None
    try:
        fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)  # 不可继承（PEP 446）
    except (FileNotFoundError, NotADirectoryError):
        return None
    except OSError as e:
        return StagingSweep(name, StagingOutcome.SKIPPED, StagingSkip.UNOPENABLE, error=e)
    try:
        check = check_fd(fd, requested=str(path), checked=str(path))
        if check.verdict is not Boundary.INSIDE:
            return StagingSweep(name, StagingOutcome.SKIPPED, StagingSkip.UNSUPPORTED_FILESYSTEM, boundary=check)
        attempt = try_lock(fd)
        if attempt.state is LockState.HELD:
            return StagingSweep(name, StagingOutcome.SKIPPED, StagingSkip.HELD)
        if attempt.state is LockState.UNAVAILABLE:
            return StagingSweep(name, StagingOutcome.SKIPPED, StagingSkip.LOCK_UNAVAILABLE, error=attempt.error)
        if not same_dir(fd, path):
            return None
        if dry_run:
            return StagingSweep(name, StagingOutcome.WOULD_REMOVE)
        try:
            shutil.rmtree(path)
        except OSError as e:
            return StagingSweep(name, StagingOutcome.SKIPPED, StagingSkip.REMOVE_FAILED, error=e)
        return StagingSweep(name, StagingOutcome.REMOVED)
    finally:
        os.close(fd)
