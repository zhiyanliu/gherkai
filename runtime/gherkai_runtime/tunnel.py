"""隧道口子（ADR 0035）：把 CLI 所在机器可达的被测应用暴露成云端浏览器与真机浏览器都可访问的公网 URL。

TunnelProvider 有两个入口（ADR 0035 决策 1）：前置检查 `check_prerequisites()`，与起隧道 `start(local_origin, *, closes_at,
timeout_s) -> TunnelInfo`。隧道是宿主进程里由 ngrok 官方 Python SDK 建立的一个会话：起隧道的进程就是宿主，也是唯一关闭它的一方
（`TunnelInfo.close()`）；宿主怎样退出，会话都随进程消失（ADR 0035 决策 3「寿命」），所以隧道事实里没有进程号，也没有按进程号停止的
入口。

本模块顶层不导入 SDK：CLI 建解析器时就导入本模块，没给 `--expose-local` 时装不装 SDK 都没有影响（ADR 0037 决策 2c）。SDK 只在
前置检查与起隧道时经 `_load_sdk` 导入，两处对「没有装」与「装了但无法加载」给出同一句说明。

鉴权是「令牌换 cookie」（ADR 0051 决策 13；取代曾用的 basic-auth 凭据内嵌地址）：组合根每 run 生成访问令牌 T 与会话 cookie 值 C，
写进本 run 的 ngrok 流量策略（边缘节点拦截，不带 cookie 的请求到不了本机）；worker 在第一个 scenario 之前对「会话预热地址」
导航一次换到 cookie。step 文本只做「origin 到干净隧道地址」的映射，不内嵌凭据、不附令牌；T 与 C 只出现在预热地址
（经 definition 的 `RunMeta.session_warmup_url` 下发）与交给 SDK 的流量策略里，策略只在内存里、不落盘。策略最前面一条在到点时刻
之后一律拒绝（ADR 0035 决策 3「边缘到点拒绝」）。

core 对隧道无知，worker 只做一次预热导航、不感知令牌与 cookie 的值（ADR 0035「边界与不变量」）。
URL 映射（map_origin_in_jobs）在组合根完成、job-in 前替换进 definition（ADR 0035 决策 2——映射对 worker/引擎/AI 透明）。
"""
from __future__ import annotations

import importlib
import logging
import os
import re
import secrets
import threading
from collections.abc import Callable
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta, timezone
from typing import Any, Final, Protocol, TypeVar
from urllib.parse import urlsplit

from gherkai_core.model import Job

# ---- 令牌换 cookie 的边缘契约常量（ADR 0051 决策 13）----
# 预热路径、校验路径、令牌参数名与 cookie 名只在本模块持有（worker 只读预热地址、不感知令牌与 cookie）；页面标题与正文标记
# 与消费它们的 worker 同值（Nova `lib/constants.py` 只持标题，Midscene `lib/tunnel-warmup.mts` 持标题与正文标记），
# 全部由 engines/fixtures/tunnel-warmup.json 对拍。
WARMUP_PATH = "/.well-known/gherkai-tunnel-auth"   # 预热路径：凭令牌换 cookie
CHECK_PATH = "/.well-known/gherkai-tunnel-check"   # 校验路径：只凭 cookie 放行，预热页面的脚本请求它一次
TOKEN_PARAM = "gherkai_tunnel_token"
COOKIE_NAME = "__Host-gherkai_tunnel"
# 预热页面的四种可见结果：标题给桌面 worker 读（document.title），正文标记给设备 worker 在控件树里找
WARMUP_TITLES = {
    "ready": "gherkai-tunnel-ready",
    "denied": "gherkai-tunnel-denied",
    "error": "gherkai-tunnel-error",
    "auth_required": "gherkai-tunnel-auth-required",
}
WARMUP_MARKERS = {
    "ready": "GHERKAI TUNNEL READY",
    "denied": "GHERKAI TUNNEL DENIED",
    "error": "GHERKAI TUNNEL ERROR",
    "auth_required": "GHERKAI TUNNEL AUTH REQUIRED",
}
# ngrok 免费层的两条硬约束（真账户实测）：较早注册的账号上每个策略至多 5 条规则；remove-headers 是付费功能。
# 产品的策略是五条规则（到点拒绝加鉴权的四条），正好用满。
POLICY_RULE_LIMIT = 5
# 到点之后边缘的固定回答正文（ADR 0051 决策 13「边缘策略」）。
EXPIRED_TEXT: Final = "GHERKAI TUNNEL EXPIRED"
# 起隧道的时限缺省值（秒）：SDK 建立监听的调用不带时限，宿主按它放弃等待（ADR 0035 决策 1「起隧道的时限」）。计入运行期限里
# 900 秒的一次性余量（ADR 0054 决策二）。
START_TIMEOUT_S: Final = 20.0
# 关闭会话的时限（秒）：到时即放弃等待，宿主进程退出时会话照样消失。
CLOSE_TIMEOUT_S: Final = 5.0
# 令牌只取这个环境变量，经 SDK 的 `authtoken_from_env` 取用，gherkai 不读出、不转交它的值（ADR 0035 决策 1「前置条件」）。
TOKEN_ENV: Final = "NGROK_AUTHTOKEN"
# SDK 原生库用到的日志目标各族：原生库的日志经桥接交给 Python 的 logging，日志目标名换成 logger 名（`ngrok::tunnel_ext` 成为
# `ngrok.tunnel_ext`，`muxado::heartbeat`、`rustls::client`、`tokio::runtime` 同理），所以 `ngrok` 之外的几族同样落在 logging 上。
# 族名取自原生库里出现的日志目标；导入之后各族的根 logger 都接空处理器、不向上传播。
_SDK_LOGGER_FAMILIES: Final = ("ngrok", "muxado", "rustls", "tokio")

_T = TypeVar("_T")


class TunnelError(Exception):
    """隧道起不来 / provider 未知 / 前置缺失 / `--expose-local` 的取值不是 origin——调用方接住归「没开始执行就被拒」（退出码 2）。
    消息是给使用者的整句，调用方原样输出。"""


@dataclass(frozen=True)
class TunnelInfo:
    """一条已建立隧道的事实（ADR 0035 决策 1）：公网地址、归一化之后的 origin、会话预热地址，外加关闭会话的那个可调用对象。

    warmup_url 含令牌，只进 definition（`RunMeta.session_warmup_url`），不进 repr；closer 不进 repr、不参与比较。没有进程号：
    会话在宿主进程里，只能由宿主自己关闭。"""

    url: str  # 公网地址（干净、不含凭据），替换进 job 文本、进度行展示
    local_origin: str  # 被暴露的 origin，经 normalize_origin 归一化（替换源，如 http://localhost:3000）
    warmup_url: str = field(repr=False)  # 会话预热地址 https://<隧道主机>/.well-known/gherkai-tunnel-auth?gherkai_tunnel_token=T
    closer: Callable[[], None] = field(repr=False, compare=False)

    def close(self) -> None:
        """关闭会话：可以重复调用（只有第一次动作），自身有时限，失败不外抛。正常路径上的礼貌动作，关闭不成功时宿主进程退出，会话照样
        消失。"""
        self.closer()


class TunnelProvider(Protocol):
    """隧道实现的口子（ADR 0035 决策 1）。"""

    def check_prerequisites(self) -> None:
        """缺前置时抛 TunnelError（没有装隧道组件或无法加载、没有令牌）。"""
        ...

    def start(self, local_origin: str, *, closes_at: datetime, timeout_s: float = START_TIMEOUT_S) -> TunnelInfo:
        """起隧道：流量策略带到 `closes_at` 为止的到点拒绝；`timeout_s` 内没有建成即抛 TunnelError。"""
        ...


def _gen_secret() -> str:
    """每 run 一换的随机串：128 位、十六进制——不需要 URL 编码，可原样进 CEL 字符串与 cookie 值。"""
    return secrets.token_hex(16)


def warmup_url_for(url: str, token: str) -> str:
    return f"{url}{WARMUP_PATH}?{TOKEN_PARAM}={token}"


_WARMUP_PAGE = (
    '<!doctype html><html><head><meta charset="utf-8"><title>gherkai-tunnel-warmup</title>'
    '<meta name="viewport" content="width=device-width"></head>'
    '<body style="font-size:40px"><h1 id="m">GHERKAI TUNNEL WARMUP</h1>'
    "<script>fetch('__CHECK_PATH__',{credentials:'same-origin',cache:'no-store'})"
    ".then(function(r){var s=r.status;"
    "document.title=s===200?'__T_READY__':s===401?'__T_DENIED__':'__T_ERROR__';"
    "document.getElementById('m').textContent=s===200?'__M_READY__':s===401?'__M_DENIED__':'__M_ERROR__ '+s;})"
    ".catch(function(e){document.title='__T_ERROR__';document.getElementById('m').textContent='__M_ERROR__';});</script>"
    "</body></html>"
)
_AUTH_REQUIRED_PAGE = (
    "<!doctype html><html><head><title>__T_AUTH__</title></head>"
    "<body style='font-size:40px'><h1>__M_AUTH__</h1><p>This address needs a test session.</p></body></html>"
)
# 预热页面的脚本只把 401 判为 DENIED（确定性拒绝）；429、5xx 这类拿不准的响应与请求失败一样判 ERROR，由 worker 有界重试（ADR 0051 决策 13
# 的归因：只有鉴权失败才是 precheck_failed）。
# 五条规则（ADR 0051 决策 13「边缘策略」，与真账户实测通过的那份逐条相同），按次序判断、第一条命中即回答：
# ⓪ 当前时刻不早于到点时刻 → 403 固定正文，不看路径与 cookie（ADR 0035 决策 3「边缘到点拒绝」）；
# ① 预热路径 + GET + 令牌相等 → 200 预热页，下发 cookie；② 预热路径其余情形 → 401；③ 校验路径只凭 cookie 放行 → 200 空体；
# ④ 其余路径 cookie 不等于 C → 401，命中则原样转发（校验路径的拒绝也落到这条）。同名 cookie 任一命中即放行。
# `time.now` 是 ngrok 流量策略成文的变量（当前 UTC 时刻）；到点时刻的写法见 policy_instant。
_POLICY_TEMPLATE = """on_http_request:
  - name: expired
    expressions:
      - "timestamp(time.now) >= timestamp('__CLOSES_AT__')"
    actions:
      - type: custom-response
        config:
          status_code: 403
          headers:
            content-type: "text/plain; charset=utf-8"
            cache-control: "no-store"
          content: "__EXPIRED_TEXT__"
  - name: warmup-ok
    expressions:
      - "req.url.path == '__WARMUP_PATH__'"
      - "req.method == 'GET'"
      - "'__TOKEN_PARAM__' in req.url.query_params"
      - "'__T__' in req.url.query_params['__TOKEN_PARAM__']"
    actions:
      - type: custom-response
        config:
          status_code: 200
          headers:
            content-type: "text/html; charset=utf-8"
            set-cookie: "__COOKIE_NAME__=__C__; Secure; HttpOnly; Path=/; SameSite=None"
            cache-control: "no-store"
            referrer-policy: "no-referrer"
          content: |
            __WARMUP_PAGE__
  - name: warmup-reject
    expressions:
      - "req.url.path == '__WARMUP_PATH__'"
    actions:
      - type: custom-response
        config:
          status_code: 401
          headers:
            content-type: "text/html; charset=utf-8"
            cache-control: "no-store"
          content: "__AUTH_REQUIRED_PAGE__"
  - name: check-ok
    expressions:
      - "req.url.path == '__CHECK_PATH__'"
      - "'__COOKIE_NAME__' in req.cookies && req.cookies['__COOKIE_NAME__'].exists(c, c.value == '__C__')"
    actions:
      - type: custom-response
        config:
          status_code: 200
          headers:
            cache-control: "no-store"
          content: ""
  - name: gate
    expressions:
      - "req.url.path == '__CHECK_PATH__' || !('__COOKIE_NAME__' in req.cookies) || !req.cookies['__COOKIE_NAME__'].exists(c, c.value == '__C__')"
    actions:
      - type: custom-response
        config:
          status_code: 401
          headers:
            content-type: "text/html; charset=utf-8"
            cache-control: "no-store"
          content: "__AUTH_REQUIRED_PAGE__"
"""


_POLICY_INSTANT_SHAPE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z")


def policy_instant(closes_at: datetime) -> str:
    """到点时刻在策略里的写法（ADR 0051 决策 13「边缘策略」）：UTC、精确到秒、以 `Z` 结尾（`YYYY-MM-DDTHH:MM:SSZ`，到点规则在 SDK
    起的隧道上实测生效时用的就是这种写法）。

    不带时区即抛 ValueError：无从换算成 UTC。有小数秒时向上取整到下一整秒，边缘因此不早于记录里的时刻关闭；差额不到 1 秒，不是另加的
    余量。"""
    if closes_at.tzinfo is None or closes_at.utcoffset() is None:
        raise ValueError(f"到点时刻须带时区，现为 {closes_at!r}")
    t = closes_at.astimezone(timezone.utc)
    if t.microsecond:
        t = t.replace(microsecond=0) + timedelta(seconds=1)
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def render_traffic_policy(token: str, cookie: str, *, closes_at: datetime) -> str:
    """本 run 的 ngrok 流量策略 YAML（ADR 0051 决策 13）：手写模板替换，不为此引 yaml 依赖——结构固定，令牌与 cookie 值是十六进制、
    到点时刻只由数字与固定字符组成，都没有转义面。不出现 basic-auth 与 remove-headers；规则数等于 POLICY_RULE_LIMIT。

    `closes_at` 是本 run 的到点时刻（运行期限加 300 秒，`run_deadline.overdue_at`），由调用方算好传入，这里只换成策略里的写法。"""
    for v in (token, cookie):
        if not re.fullmatch(r"[0-9a-f]{32,}", v):
            raise ValueError("隧道令牌与 cookie 值须是至少 32 位的十六进制串")
    instant = policy_instant(closes_at)
    if not _POLICY_INSTANT_SHAPE.fullmatch(instant):
        # 时刻写进策略里的字符串字面量：形态不对的值可能破坏引号，不进策略
        raise ValueError(f"到点时刻的写法不对：{instant!r}")
    subs = {
        "__CLOSES_AT__": instant, "__EXPIRED_TEXT__": EXPIRED_TEXT,
        "__WARMUP_PATH__": WARMUP_PATH, "__CHECK_PATH__": CHECK_PATH, "__TOKEN_PARAM__": TOKEN_PARAM, "__COOKIE_NAME__": COOKIE_NAME,
        "__T_READY__": WARMUP_TITLES["ready"], "__T_DENIED__": WARMUP_TITLES["denied"], "__T_ERROR__": WARMUP_TITLES["error"],
        "__T_AUTH__": WARMUP_TITLES["auth_required"],
        "__M_READY__": WARMUP_MARKERS["ready"], "__M_DENIED__": WARMUP_MARKERS["denied"], "__M_ERROR__": WARMUP_MARKERS["error"],
        "__M_AUTH__": WARMUP_MARKERS["auth_required"],
    }
    page = _WARMUP_PAGE
    auth_page = _AUTH_REQUIRED_PAGE
    for k, v in subs.items():
        page = page.replace(k, v)
        auth_page = auth_page.replace(k, v)
    out = _POLICY_TEMPLATE.replace("__WARMUP_PAGE__", page).replace("__AUTH_REQUIRED_PAGE__", auth_page)
    for k, v in subs.items():
        out = out.replace(k, v)
    return out.replace("__T__", token).replace("__C__", cookie)


# ---- 给使用者的说明（ADR 0035 决策 1「启动失败的说法按原因分」；调用方原样输出，都以退出码 2 结束）----
_NOT_INSTALLED = (
    "--expose-local 要用的隧道组件没有安装。请在安装 gherkai 时加上 tunnel 组件后重新执行，"
    "例如 uv tool install 'gherkai[local,tunnel]'（已经装了别的组件的，要一并列出）。")
_NO_TOKEN = (
    "--expose-local 需要 ngrok 的令牌，但环境变量 NGROK_AUTHTOKEN 没有设置。"
    "请在 ngrok 控制台取得令牌，设置 NGROK_AUTHTOKEN 后重新执行。")
_ADDRESS_IN_USE = (
    "隧道没有建成：这个 ngrok 账号上另一条在线的隧道占用了同一个地址（ERR_NGROK_334）。"
    "请等那条隧道下线之后再试；如果它属于另一个带 --expose-local 的 gherkai 运行，持有它的进程退出之后它就会下线。")
# 错误码是 SDK 异常里的结构字段（实测三项参数，第三项为 ERR_NGROK_<数字>）；分类只看它，不解析说明文字。
_ERROR_CODE = re.compile(r"ERR_NGROK_[0-9]+")
_CODE_ADDRESS_IN_USE = "ERR_NGROK_334"


def _one_line(text: str) -> str:
    return " ".join(text.split())


def _cannot_load(e: BaseException) -> str:
    return (f"--expose-local 要用的隧道组件已经安装，但无法加载：{_one_line(str(e)) or type(e).__name__}。"
            "请重新安装带 tunnel 组件的 gherkai 后重新执行。")


def _timed_out(timeout_s: float) -> str:
    return f"隧道没有建成：{timeout_s:g} 秒内没有连上隧道服务。请确认本机能访问外网后重新执行。"


def _import_sdk() -> Any:
    """导入 SDK 模块。只在 `_load_sdk` 里经调用方给的函数调用：测试的自动夹具对本函数打桩，缺省参数因此不在定义时绑定它。"""
    return importlib.import_module("ngrok")


def _load_sdk(load: Callable[[], Any]) -> Any:
    """导入 SDK 并静默它的日志；导入失败译成 TunnelError。前置检查与起隧道都经这一处，同一情形在三种宿主里给出同一句说明。

    分类只看异常类型：找不到 `ngrok` 这个模块本身是「没有装」；导入期间其余的异常（SDK 内部的模块找不到、原生库载入失败、
    初始化出错等）都是「装了但无法加载」，不让其中一类落成回溯与别的退出码。

    SDK 经 Python 的 logging 发日志（被测应用连不上时每个请求一条警告，没有配置 logging 时写到标准错误）：这些不是产品的输出，使用者
    从 job 的失败证据里看到同一原因，所以把原生库用到的各族 logger（`_SDK_LOGGER_FAMILIES`）都接到空处理器、不向上传播（ADR 0035
    决策 1「公网地址是 SDK 调用的返回值」）。后台进程在回报之前不往标准错误写字（ADR 0035 决策 3「输出」），漏掉一族就会破坏这一条。
    重复导入不重复加处理器。"""
    try:
        sdk = load()
    except ModuleNotFoundError as e:
        if e.name == "ngrok":
            raise TunnelError(_NOT_INSTALLED) from e
        raise TunnelError(_cannot_load(e)) from e
    except Exception as e:
        raise TunnelError(_cannot_load(e)) from e
    for name in _SDK_LOGGER_FAMILIES:
        logger = logging.getLogger(name)
        if not any(isinstance(h, logging.NullHandler) for h in logger.handlers):
            logger.addHandler(logging.NullHandler())
        logger.propagate = False
    return sdk


class _CallTimedOut(TimeoutError):
    """`_call_with_timeout` 自己的超时：与被调函数抛出的 TimeoutError 区分开。"""


@dataclass
class _CallState:
    lock: threading.Lock = field(default_factory=threading.Lock)
    abandoned: bool = False
    done: bool = False
    value: Any = None
    error: BaseException | None = None


def _call_with_timeout(fn: Callable[[], _T], timeout_s: float, *, on_late: Callable[[_T], None]) -> _T:
    """在一个守护线程里调用 `fn`，最多等 `timeout_s` 秒；到时没有结果即抛 TimeoutError（ADR 0035 决策 1「起隧道的时限」）。

    「主线程放弃」与「线程交出结果」由同一把锁判定先后，两者之间没有空隙：线程调完 `fn` 后在锁内看主线程是否已放弃，已放弃即对迟到的
    结果调 `on_late`（起隧道时是关闭迟到建成的监听），否则把结果交给主线程；主线程等待结束后在锁内判断，没有结果才置「已放弃」。主线程
    等待期间被异常打断（如 KeyboardInterrupt）时同样置「已放弃」，已经交来的结果当场交给 `on_late`。

    线程是守护线程，进程退出不等它。截得住的前提是 `fn` 在阻塞时释放解释器锁（SDK 建立监听时释放，ADR 0035 决策 1「实测依据」）。
    线程里的异常与 `on_late` 的异常不外抛到线程之外，不经线程的缺省异常处理写到标准错误。"""
    st = _CallState()

    def _late(value: _T) -> None:
        try:
            on_late(value)
        except Exception:
            pass  # 迟到结果的处理是尽力而为：宿主在起隧道失败之后随即退出，会话随进程消失

    def _target() -> None:
        try:
            value = fn()
        except BaseException as e:  # noqa: BLE001 —— 交给主线程原样抛出，不在线程里输出
            with st.lock:
                if not st.abandoned:
                    st.error, st.done = e, True
            return
        with st.lock:
            late = st.abandoned
            if not late:
                st.value, st.done = value, True
        if late:
            _late(value)

    t = threading.Thread(target=_target, name="gherkai-tunnel-call", daemon=True)
    try:
        t.start()  # 在 try 里：start 要等线程起来，这段等待里被打断时线程可能已经在调用 fn
        t.join(timeout_s)
    except BaseException:
        with st.lock:
            st.abandoned = True
            delivered = st.done and st.error is None
        if delivered:
            _late(st.value)
        raise
    with st.lock:
        if not st.done:
            st.abandoned = True
            raise _CallTimedOut(f"{timeout_s:g} 秒内没有返回")
    if st.error is not None:
        raise st.error
    return st.value


class _SessionCloser:
    """关闭一个隧道会话：第一次调用时用 SDK 同步的 `disconnect(url)` 关闭，之后的调用不再动作；按 CLOSE_TIMEOUT_S 放弃等待；关闭期间的
    任何异常都不外抛，含 KeyboardInterrupt（ADR 0035 决策 1）。并发调用时后来者等前一次的关闭结束（或到时放弃）才返回；后来者在等待期间
    被打断时不再等、同样不外抛。

    同时持有 SDK 给出的监听对象：实测这个对象不再被引用、被回收之后隧道仍在线，持有它是为了不依赖这一行为。不用监听对象自己的
    `close()`：它返回可等待对象，宿主都是同步代码；也不用 `kill()`：它关掉进程里全部会话。"""

    def __init__(self, sdk: Any, url: str, listener: Any) -> None:
        self._sdk = sdk
        self._url = url
        self._listener = listener
        self._lock = threading.Lock()
        self._closed = False

    def __call__(self) -> None:
        # 取锁、状态转换与等待关闭都在保护区里：后来者等锁期间同样可能被打断（POSIX 上等锁可以被信号打断）
        try:
            with self._lock:
                if self._closed:
                    return
                self._closed = True
                _call_with_timeout(lambda: self._sdk.disconnect(self._url), CLOSE_TIMEOUT_S, on_late=lambda _: None)
        except BaseException:  # noqa: BLE001
            # 关闭只是正常路径上的收尾动作：失败、到时或被打断，宿主进程退出时会话照样消失。被打断也不外抛：前台 run 在 atexit 里
            # 关闭会话，这时 SIGINT 的处置已经恢复成 Python 的缺省处理，等待关闭期间按下 Ctrl-C 成为 KeyboardInterrupt，外抛就会
            # 在使用者的终端上留下回溯
            pass


def _upstream_addr(origin: str) -> str:
    """交给 SDK 的上游地址：归一化之后的 origin，只把 scheme 转成小写（ADR 0035 决策 1「交给 SDK 的上游地址」）。scheme 不区分大小写；
    映射按书写形式逐字匹配、所以 origin 保留原样，交给隧道服务的这一份统一写法，判断是不是 https 也看这一份。"""
    scheme, sep, rest = origin.partition("://")
    return f"{scheme.lower()}{sep}{rest}"


def _start_failure(e: Exception) -> TunnelError:
    """把起隧道时 SDK 抛出的异常译成给使用者的一句（ADR 0035 决策 1「启动失败的说法按原因分」第 3、4 种）。

    错误码只认「参数恰为三项、第三项是 ERR_NGROK_<数字>」，说明取第二项；其余情形说明取各项参数以「: 」相连（连不上隧道服务时是两项
    参数、没有错误码），没有参数时取异常类型名。说明压成一行。输出之前把说明里出现的令牌值替换成 `***`：实测无效令牌的说明里不带令牌，
    这是对其余错误的防备。"""
    args = e.args
    code: str | None = None
    if len(args) == 3 and isinstance(args[2], str) and _ERROR_CODE.fullmatch(args[2]):
        code, text = args[2], str(args[1])
    elif args:
        text = ": ".join(str(a) for a in args)
    else:
        text = type(e).__name__
    if code == _CODE_ADDRESS_IN_USE:
        return TunnelError(_ADDRESS_IN_USE)
    token = os.environ.get(TOKEN_ENV, "")
    if token:
        text = text.replace(token, "***")
    text = _one_line(text)
    return TunnelError(f"隧道没有建成：{text}（{code}）。" if code else f"隧道没有建成：{text}。")


class NgrokTunnel:
    """ngrok 实现（ADR 0035 决策 1，当前唯一 provider）：经 ngrok 官方 Python SDK 在宿主进程里建立会话，不启动 ngrok 可执行文件。

    - **前置**：装了 SDK（`gherkai[tunnel]`）、设了环境变量 NGROK_AUTHTOKEN；`check_prerequisites` 真正导入一次 SDK，能导入才算装好。
    - **鉴权恒开**（令牌换 cookie，ADR 0051 决策 13）：隧道模式下 definition 必带额外请求头与预热地址（ADR 0035「边界与不变量」
      的完整性判据），所以没有「不带鉴权」的开关——那只会产出残缺的 definition、让 worker 判 precheck_failed。
    - **就绪判据**：SDK 建立监听的调用返回即就绪，不另加就绪等待（ADR 0035 决策 1）。

    `load_sdk` 给出导入 SDK 的函数，测试经它注入假 SDK；为 None 时在调用那一刻取本模块的 `_import_sdk`。
    """

    def __init__(self, *, load_sdk: Callable[[], Any] | None = None) -> None:
        self._load_sdk_fn = load_sdk

    def _sdk(self) -> Any:
        return _load_sdk(self._load_sdk_fn if self._load_sdk_fn is not None else _import_sdk)

    def check_prerequisites(self) -> None:
        """两项前置（ADR 0035 决策 1「前置条件」）：先导入一次 SDK，再看令牌的环境变量非空；缺了以 TunnelError 拒绝。"""
        self._sdk()
        if not os.environ.get(TOKEN_ENV, "").strip():
            raise TunnelError(_NO_TOKEN)

    def start(self, local_origin: str, *, closes_at: datetime, timeout_s: float = START_TIMEOUT_S) -> TunnelInfo:
        # 先校验取值再导入 SDK：取值不是 origin 时在这里以 TunnelError 拒绝，不碰 SDK
        origin = normalize_origin(local_origin)
        token, cookie = _gen_secret(), _gen_secret()
        policy = render_traffic_policy(token, cookie, closes_at=closes_at)  # 只在内存里，随调用交给 SDK
        sdk = self._sdk()
        addr = _upstream_addr(origin)
        options: dict[str, Any] = {"authtoken_from_env": True, "traffic_policy": policy}
        if addr.startswith("https://"):
            # 这一跳只在宿主与它可达的被测应用之间，本机开发常用自签证书（ADR 0035 决策 1「交给 SDK 的上游地址」）
            options["verify_upstream_tls"] = False

        def _forward() -> tuple[Any, str]:
            listener = sdk.forward(addr, **options)
            return listener, listener.url()

        def _close_late(result: tuple[Any, str]) -> None:
            _SessionCloser(sdk, result[1], result[0])()

        try:
            listener, url = _call_with_timeout(_forward, timeout_s, on_late=_close_late)
        except _CallTimedOut:
            raise TunnelError(_timed_out(timeout_s)) from None
        except Exception as e:
            raise _start_failure(e) from e
        return TunnelInfo(url=url, local_origin=origin, warmup_url=warmup_url_for(url, token),
                          closer=_SessionCloser(sdk, url, listener))


PROVIDERS = {"ngrok": NgrokTunnel}


def make_tunnel(name: str) -> TunnelProvider:
    """按 `--tunnel <provider>` 选实现（ADR 0035 决策 1；当前唯一 ngrok，机制先行）。构造不导入 SDK。"""
    try:
        return PROVIDERS[name]()
    except KeyError:
        raise TunnelError(f"未知隧道 provider：{name!r}（可用：{sorted(PROVIDERS)}）") from None


# ---- origin → 隧道地址的带边界识别（ADR 0035 决策 2）----
# RFC 3986 的 URL 字符（unreserved + reserved + 百分号）：origin 之后最长的这样一段是「这个地址的其余部分」。
_URL_CHARS = r"A-Za-z0-9\-._~:/?#\[\]@!$&'()*+,;=%"
# 左边界：串首，或前一个字符不是 scheme 字符（字母、数字、+ . -）——`xhttp://…` 不命中；`=http://…`、中文后紧跟地址命中。
_LEFT_BOUNDARY = r"(?<![A-Za-z0-9+.\-])"
_TRAILING_PUNCT = set(".,;:!)]'")
# origin 的整体形状：scheme、`://`、authority（到第一个 / ? # 为止），其余部分另行判定
_ORIGIN_SHAPE = re.compile(r"(?P<scheme>[^:/?#]+)://(?P<authority>[^/?#]*)(?P<rest>.*)", re.DOTALL)
_ORIGIN_EXAMPLE = "http://localhost:3000"


def normalize_origin(value: str) -> str:
    """把 `--expose-local` 的取值校验并归一化成 origin（`scheme://host[:port]`，ADR 0035 决策 2）。

    末尾恰好一个 `/` 时去掉：origin 语义没有歧义，这种写法也常见；不去掉的话 `http://localhost:3000/` 之后剩下的
    `login` 既不为空、也不以 `/ ? #` 开头，`http://localhost:3000/login` 就不会被映射，导航失败却看不出原因。
    其余非 origin 形态（路径、查询串、片段、用户信息、http 与 https 之外的 scheme、空主机、非法端口、含空白）一律以
    TunnelError 拒绝，不做隐式截断：截掉路径会静默改变使用方的意图。大小写原样保留，因为映射按 feature 的书写形式逐字匹配。
    """
    def _reject(reason: str) -> TunnelError:
        return TunnelError(
            f"--expose-local 的取值 {value!r} 不是 origin：{reason}。"
            f"请只写到端口为止，例如 {_ORIGIN_EXAMPLE}，路径写在 feature 的 step 里。")

    if re.search(r"\s", value):
        raise _reject("含有空白字符")
    m = _ORIGIN_SHAPE.fullmatch(value)
    if m is None:
        raise _reject("缺少 http:// 或 https:// 开头")
    scheme, authority, rest = m.group("scheme"), m.group("authority"), m.group("rest")
    if scheme.lower() not in ("http", "https"):
        raise _reject(f"只支持 http 与 https，这里是 {scheme}")
    if rest == "/":
        rest = ""
    if rest:
        raise _reject(f"含有路径、查询串或片段 {rest!r}")
    if "@" in authority:
        raise _reject("含有用户信息（@ 之前的部分）")
    try:
        parsed = urlsplit(f"{scheme}://{authority}")
        port = parsed.port  # 端口不是 0 到 65535 之间的整数时抛 ValueError；冒号之后为空时返回 None
    except ValueError:
        raise _reject("主机或端口无法解析") from None
    if not parsed.hostname:
        raise _reject("缺少主机名")
    if authority.endswith(":") or port == 0:
        # 冒号之后为空时，feature 里带端口号的地址不会被映射；0 号端口则无法连接
        raise _reject("冒号之后缺少端口号，或端口为 0")
    return f"{scheme}://{authority}"


def replace_origin(text: str, origin: str, base: str) -> str:
    """把文本里每个「作为一个地址出现」的 origin 换成 base：origin 之后的 URL 字符段 R 为空、以 / ? # 开头、或全部由句末标点组成才算命中
    （`http://localhost:3000/x`、`去 http://localhost:3000。`、`(see http://localhost:3000)` 命中；`http://localhost:3000.evil/`、
    `http://localhost:30001/x` 不命中——那是别的主机或端口）。一段文本里可以有多处命中，**逐处独立判定**：R 只向前看、不被消费，
    所以 `…/?next=http://localhost:3000/x` 里内层那一处同样参与识别（外层不命中也不影响内层）。"""
    pattern = re.compile(_LEFT_BOUNDARY + re.escape(origin) + "(?=(?P<rest>[" + _URL_CHARS + "]*))")

    def _sub(m: re.Match) -> str:
        rest = m.group("rest")
        if rest == "" or rest[0] in "/?#" or set(rest) <= _TRAILING_PUNCT:
            return base
        return m.group(0)

    return pattern.sub(_sub, text)


def map_origin_in_jobs(jobs: list[Job], origin: str, base: str) -> list[Job]:
    """把 job 文本中的 origin 替换成干净的隧道地址 base（ADR 0035 决策 2：job-in 前、worker/AI 无感）。

    替换面为 step.text + step.argument（docString content / dataTable 各单元格）——URL 可能出现在任一处，三处各自独立套用
    `replace_origin` 的边界规则。origin 的写法须与 feature 书写一致（`localhost` vs `127.0.0.1` 不互认，文档写明）；
    先经 `normalize_origin` 校验与归一化，与 `NgrokTunnel.start` 暴露的是同一个 origin（取值不是 origin 时抛 TunnelError）。
    frozen dataclass 逐层重建，原 jobs 不变（definition 不可变惯例）。
    """
    origin = normalize_origin(origin)

    def sub(s: str | None) -> str | None:
        return replace_origin(s, origin, base) if s else s

    mapped: list[Job] = []
    for job in jobs:
        scenarios = tuple(
            replace(sc, steps=tuple(
                replace(
                    st,
                    text=sub(st.text),
                    argument=(replace(
                        st.argument,
                        content=sub(st.argument.content),
                        rows=(tuple(tuple(sub(c) for c in row) for row in st.argument.rows)
                              if st.argument.rows is not None else None),
                    ) if st.argument is not None else None),
                )
                for st in sc.steps))
            for sc in job.scenarios)
        mapped.append(replace(job, scenarios=scenarios))
    return mapped
