"""隧道口子（ADR 0035）：把 CLI 所在机器可达的被测应用暴露成云端浏览器可访问的公网 URL。

TunnelProvider 的形状为 `start(local_origin) -> TunnelInfo`；停止用 `stop_tunnel(pid)`——隧道生命周期
可能跨进程（local submit 的 per-run 进程 / cloud submit 的守护进程收尾），进程对象句柄传不过去，
故 TunnelInfo 携带 pid、由收尾者 kill（ADR 0035 决策 3 的三形态宿主）。

鉴权是「令牌换 cookie」（ADR 0051 决策 13；取代曾用的 basic-auth 凭据内嵌地址）：组合根每 run 生成访问令牌 T 与会话 cookie 值 C，
写进本 run 的 ngrok 流量策略（边缘节点拦截，不带 cookie 的请求到不了本机）；worker 在第一个 scenario 之前对「会话预热地址」
导航一次换到 cookie。step 文本只做「origin 到干净隧道地址」的映射，不内嵌凭据、不附令牌；T 与 C 只出现在预热地址
（经 definition 的 `RunMeta.session_warmup_url` 下发）与策略文件（0600）里。

worker/core 对隧道无知：URL 映射（map_origin_in_jobs）在组合根完成、job-in 前替换进 definition
（ADR 0035 决策 2——对 worker/引擎/AI 完全透明）。
"""
from __future__ import annotations

import os
import re
import secrets
import signal
import subprocess
import tempfile
import time
from dataclasses import dataclass, field, replace
from pathlib import Path

from gherkai_core.model import Job

# ---- 令牌换 cookie 的边缘契约常量（ADR 0051 决策 13）----
# 两个 worker 各持一份同值（Nova `lib/constants.py`、Midscene `lib/tunnel-warmup.mts`），由 engines/fixtures/tunnel-warmup.json 对拍。
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
# ngrok 免费层的两条硬约束（真账户实测）：每个策略至多 5 条规则；remove-headers 是付费功能。四条规则留一条余量。
POLICY_RULE_LIMIT = 5


class TunnelError(Exception):
    """隧道起不来 / provider 未知 / 前置缺失——调用方接住归「没开始执行就被拒」（退出码 2）。"""


@dataclass(frozen=True)
class TunnelInfo:
    """一条已建立隧道的事实。url / pid / local_origin 可落盘 tunnel.json 供跨进程收尾；warmup_url 含令牌，只进 definition
    （`RunMeta.session_warmup_url`），不进 repr、不进 tunnel.json。"""

    url: str  # 公网地址（干净、不含凭据），替换进 job 文本、进度行展示
    pid: int  # 隧道 agent 进程 pid（收尾者 stop_tunnel(pid)）
    local_origin: str  # 被暴露的原始 origin（替换源，如 http://localhost:3000）
    warmup_url: str = field(repr=False)  # 会话预热地址 https://<隧道主机>/.well-known/gherkai-tunnel-auth?gherkai_tunnel_token=T


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
# 四条规则（ADR 0051 决策 13「边缘策略」，与真账户实测通过的那份逐条相同）：
# ① 预热路径 + GET + 令牌相等 → 200 预热页，下发 cookie；② 预热路径其余情形 → 401；③ 校验路径只凭 cookie 放行 → 200 空体；
# ④ 其余路径 cookie 不等于 C → 401，命中则原样转发（校验路径的拒绝也落到这条）。同名 cookie 任一命中即放行。
_POLICY_TEMPLATE = """on_http_request:
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


def render_traffic_policy(token: str, cookie: str) -> str:
    """本 run 的 ngrok 流量策略 YAML（ADR 0051 决策 13）：手写模板替换，不为此引 yaml 依赖——结构固定，令牌与 cookie 值是十六进制、无转义面。
    不出现 basic-auth 与 remove-headers；规则数见 POLICY_RULE_LIMIT。"""
    for v in (token, cookie):
        if not re.fullmatch(r"[0-9a-f]{32,}", v):
            raise ValueError("隧道令牌与 cookie 值须是至少 32 位的十六进制串")
    subs = {
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


class NgrokTunnel:
    """ngrok 实现（ADR 0035 决策 1，当前唯一 provider）。

    spawn `ngrok http <origin> --log <file> --log-format json --traffic-policy-file <file>` agent 进程 → 轮询日志文件、
    从 `started tunnel` 事件行拿公网 URL。**不走本地 agent API**——v3 的 `ngrok http` 无 `--web-addr`
    flag（实际运行暴露：unknown flag；web_addr 是配置文件项、注入需劫持使用方 config），日志文件通道
    无端口冲突、天然留诊断（authtoken 缺失等 err 行同在其中）。
    - **authtoken 前置**：使用方自配（`NGROK_AUTHTOKEN` env 或 ngrok 配置文件）——未配时 agent 起不来，
      start() 以日志尾部报 TunnelError（点名 authtoken 引导排错）。
    - **鉴权恒开**（令牌换 cookie，ADR 0051 决策 13）：隧道模式下 definition 必带额外请求头与预热地址（ADR 0035「边界与不变量」
      的完整性判据），所以没有「不带鉴权」的开关——那只会产出残缺的 definition、让 worker 判 precheck_failed。
    """

    def __init__(self, binary: str = "ngrok", *, popen=subprocess.Popen,
                 sleep=time.sleep, monotonic=time.monotonic) -> None:
        # 依赖可注入（测试 fake spawn；生产默认真物）
        self._binary = binary
        self._popen = popen
        self._sleep = sleep
        self._monotonic = monotonic

    def start(self, local_origin: str, *, timeout_s: float = 20.0) -> TunnelInfo:
        token, cookie = _gen_secret(), _gen_secret()
        # 只要路径：agent 自己打开写、我们只轮询读。fd 必须立刻关——留着就是进程存活期的 fd 泄漏。
        # 文件**有意不删**：隧道存活期 agent 一直在写，且它是唯一诊断通道（authtoken 缺失等 err 行在其中）。
        _log_fd, _log_name = tempfile.mkstemp(prefix="gherkai-tunnel-", suffix=".log")
        os.close(_log_fd)
        log_path = Path(_log_name)
        # 流量策略文件**有意不删**（与 log 文件同）：agent 可能在隧道存活期重读 policy，删掉就有把边缘鉴权拆成裸公网口的风险；
        # 令牌与 cookie 只对本隧道有效、随 stop_tunnel 即成死凭据，且 mkstemp 建出来就是 0600（仅本用户可读）。
        # 真要清理须先在真实边界上核实 agent 不重读——只靠单测证明不了。
        fd, policy_path = tempfile.mkstemp(prefix="gherkai-tunnel-policy-", suffix=".yml")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(render_traffic_policy(token, cookie))
        cmd = [self._binary, "http", local_origin,
               "--log", str(log_path), "--log-format", "json",
               "--traffic-policy-file", policy_path]

        try:
            # start_new_session=True（setsid）让 agent 脱离 CLI 的会话/进程组：隧道的生命周期由**宿主**决定
            # （ADR 0035 决策 3 三形态宿主 + stop_tunnel(pid)），不该由终端的信号转发决定。否则 submit 时
            # CLI 收 SIGINT/SIGHUP 会连坐杀掉「还要交棒给后台宿主」的 agent（local 交 per-run 进程、cloud 交
            # 守护进程，两个宿主本身也都 setsid）。前台 run 方式语义不变：Ctrl-C → KeyboardInterrupt → atexit
            # 拆（决策 3 表格「有意选 atexit 而非 finally」），只是不再额外挨一发终端广播的 SIGINT。
            proc = self._popen(cmd, stdin=subprocess.DEVNULL,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                               start_new_session=True)
        except FileNotFoundError as e:
            raise TunnelError(
                f"找不到 ngrok 可执行文件（{self._binary!r}）——未安装？"
                f"安装见 https://ngrok.com/download，并配置 authtoken（NGROK_AUTHTOKEN）。") from e

        # 轮询日志文件直到 `started tunnel` 行（agent 起动+边缘握手通常 <3s；超时→杀进程+带日志尾部报错）
        import json as _json

        deadline = self._monotonic() + timeout_s
        url: str | None = None
        while self._monotonic() < deadline:
            try:
                for line in log_path.read_text(encoding="utf-8", errors="replace").splitlines():
                    try:
                        rec = _json.loads(line)
                    except ValueError:
                        continue
                    if rec.get("msg") == "started tunnel" and rec.get("url"):
                        url = rec["url"]
                        break
            except OSError:
                pass  # 日志文件还没内容——继续等
            if url is not None:
                break
            if proc.poll() is not None:  # agent 已退出（authtoken 缺失/参数错的典型形态）→ 不再空等
                break
            self._sleep(0.2)

        if url is None:
            stop_tunnel(proc.pid)  # 唯一拆除面（幂等：进程已退则静默，ADR 0035 决策 3）
            tail = ""
            try:
                tail = log_path.read_text(encoding="utf-8", errors="replace")[-500:]
            except OSError:
                pass
            raise TunnelError(
                f"ngrok 隧道未就绪（{timeout_s:.0f}s 内拿不到公网 URL）。"
                f"常见原因：authtoken 未配置（NGROK_AUTHTOKEN 或 `ngrok config add-authtoken`）/ 无外网。"
                f"agent 日志尾部：{tail or '（空）'}")
        return TunnelInfo(url=url, pid=proc.pid, local_origin=local_origin, warmup_url=warmup_url_for(url, token))


def stop_tunnel(pid: int) -> None:
    """收尾：SIGTERM 隧道 agent 进程。幂等——进程已不在（重复收尾/自然退出）静默返回。"""
    try:
        os.kill(pid, signal.SIGTERM)
    except (ProcessLookupError, PermissionError):
        pass


PROVIDERS = {"ngrok": NgrokTunnel}


def make_tunnel(name: str):
    """按 `--tunnel <provider>` 选实现（ADR 0035 决策 1；当前唯一 ngrok，机制先行）。"""
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
    `replace_origin` 的边界规则。origin 的写法须与 feature 书写一致（`localhost` vs `127.0.0.1` 不互认，文档写明）。
    frozen dataclass 逐层重建，原 jobs 不变（definition 不可变惯例）。
    """
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
