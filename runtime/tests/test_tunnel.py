"""tunnel 模块单测（ADR 0035）：origin 映射与流量策略（纯逻辑）、NgrokTunnel 交给 SDK 的参数与失败的说法（假 SDK）、时限与关闭
（真实线程与 Event）。

绿即够的边界（CLAUDE.md「绿≠对·别过度」）：映射与策略是纯函数；假 SDK 只模仿 SDK 的外部表面（`forward` 记录参数并返回只有 `url()`
的对象，`disconnect` 记录调用，失败时抛装置真实记录到的异常形态），断言落在交给 SDK 的参数、TunnelError 的文字、时限内返回与迟到的
监听被关闭上。SDK 真实是否这样表现（建成、到点拒绝、关闭之后公网不在线、等网络时释放解释器锁）是真实边界，由 ADR 0035 的实测项核，
单测不算这部分的证据。测试从不起真实的隧道：`conftest.py` 的自动夹具拦下对真实 SDK 的导入。
"""
from __future__ import annotations

import gc
import json
import logging
import os
import re
import shutil
import signal
import subprocess
import sys
import threading
import time
import weakref
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import yaml

from gherkai_core.model import Job, Scenario, Step, StepArgument
from gherkai_runtime import tunnel
from gherkai_runtime.tunnel import (
    NgrokTunnel, TunnelError, TunnelInfo, make_tunnel, map_origin_in_jobs, normalize_origin, policy_instant, warmup_url_for,
)


# ---------- TunnelInfo 与边缘契约常量 ----------

FIXTURE = Path(__file__).resolve().parents[2] / "engines" / "fixtures" / "tunnel-warmup.json"


def test_tunnel_info_carries_clean_url_and_keeps_token_and_closer_out_of_repr():
    """隧道事实：url 干净、无凭据；预热地址形态精确；令牌与关闭函数不进 repr（ADR 0051 决策 13）；close() 交给关闭函数。"""
    closed: list[int] = []

    def closer_marker() -> None:
        closed.append(1)

    info = TunnelInfo(url="https://abc.ngrok-free.app", local_origin="http://localhost:3000",
                      warmup_url=warmup_url_for("https://abc.ngrok-free.app", "f" * 32), closer=closer_marker)
    assert "@" not in info.url
    assert info.warmup_url == "https://abc.ngrok-free.app/.well-known/gherkai-tunnel-auth?gherkai_tunnel_token=" + "f" * 32
    assert "f" * 32 not in repr(info) and "closer_marker" not in repr(info)
    info.close()
    assert closed == [1]


def test_edge_contract_constants_match_the_cross_language_fixture():
    """边缘契约常量与跨语言 fixture 一致（ADR 0051 决策 13）：路径、参数名、cookie 名只在 runtime 持有；页面标题与正文标记
    与消费它们的 worker 同值（Nova 只持标题，Midscene 持标题与正文标记），各方测试都与同一份 fixture 比对。"""
    fx = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert (tunnel.WARMUP_PATH, tunnel.CHECK_PATH, tunnel.TOKEN_PARAM, tunnel.COOKIE_NAME) == (
        fx["warmup_path"], fx["check_path"], fx["token_param"], fx["cookie_name"])
    assert tunnel.WARMUP_TITLES == fx["titles"] and tunnel.WARMUP_MARKERS == fx["markers"]


# ---------- 流量策略（到点拒绝加边缘鉴权的四条规则） ----------

POLICY_CLOSES = datetime(2026, 11, 20, 10, 5, 0, tzinfo=timezone.utc)


def _policy(token: str = "a" * 32, cookie: str = "b" * 32, closes_at: datetime = POLICY_CLOSES) -> str:
    return tunnel.render_traffic_policy(token, cookie, closes_at=closes_at)


def test_traffic_policy_has_five_rules_cookie_spec_and_markers():
    """ADR 0051 决策 13「边缘策略」：恰 5 条规则（等于免费层上限）、不含 basic-auth 与 remove-headers、Set-Cookie 精确等于规格、每条
    回答都带 no-store、预热响应另带 no-referrer、四个页面标记与四个标题都在、令牌与 cookie 值各出现在该出现的规则里。"""
    policy = _policy()
    assert len(re.findall(r"^  - name:", policy, re.M)) == 5 == tunnel.POLICY_RULE_LIMIT
    assert "basic-auth" not in policy and "remove-headers" not in policy
    assert 'set-cookie: "__Host-gherkai_tunnel=' + "b" * 32 + '; Secure; HttpOnly; Path=/; SameSite=None"' in policy
    assert "Domain=" not in policy and "Max-Age" not in policy
    assert policy.count('cache-control: "no-store"') == 5 and 'referrer-policy: "no-referrer"' in policy
    for marker in tunnel.WARMUP_MARKERS.values():
        assert marker in policy, marker
    for title in tunnel.WARMUP_TITLES.values():
        assert title in policy, title
    assert "'" + "a" * 32 + "' in req.url.query_params['gherkai_tunnel_token']" in policy  # 令牌只在预热放行规则里比对
    assert policy.count("a" * 32) == 1
    assert policy.count("b" * 32) == 3  # cookie 值：Set-Cookie、校验路径放行、总闸三处
    with pytest.raises(ValueError):
        tunnel.render_traffic_policy("short", "b" * 32, closes_at=POLICY_CLOSES)  # 形态不对的秘密不进策略（模板替换无转义面）


def test_traffic_policy_parses_as_yaml_with_rule_order_statuses_and_gate_semantics():
    """ngrok 读的是解析后的结构、不是字面量，所以按 YAML 解析后核：五条规则按序 expired / warmup-ok / warmup-reject / check-ok / gate，
    状态码 403 / 200 / 401 / 200 / 401；到点拒绝只看时刻、答固定正文；预热放行限 GET 且带令牌比对；no-referrer 只在预热放行页；校验路径
    放行是空响应体、只带 cache-control；总闸只认 cookie、不认令牌（令牌只用来换一次 cookie，ADR 0051 决策 13）。"""
    token, cookie = "a" * 32, "b" * 32
    rules = yaml.safe_load(_policy(token, cookie))["on_http_request"]
    assert [r["name"] for r in rules] == ["expired", "warmup-ok", "warmup-reject", "check-ok", "gate"]
    assert [r["actions"][0]["config"]["status_code"] for r in rules] == [403, 200, 401, 200, 401]
    assert all(len(r["actions"]) == 1 and r["actions"][0]["type"] == "custom-response" for r in rules)
    assert all(r["actions"][0]["config"]["headers"]["cache-control"] == "no-store" for r in rules)
    expired, ok, reject, check, gate = rules
    assert expired["expressions"] == [f"timestamp(time.now) >= timestamp('{policy_instant(POLICY_CLOSES)}')"]
    assert expired["actions"][0]["config"]["content"] == tunnel.EXPIRED_TEXT == "GHERKAI TUNNEL EXPIRED"
    assert expired["actions"][0]["config"]["headers"] == {"content-type": "text/plain; charset=utf-8", "cache-control": "no-store"}
    assert f"req.url.path == '{tunnel.WARMUP_PATH}'" in ok["expressions"] and "req.method == 'GET'" in ok["expressions"]
    assert f"'{token}' in req.url.query_params['{tunnel.TOKEN_PARAM}']" in ok["expressions"]
    assert ok["actions"][0]["config"]["headers"]["referrer-policy"] == "no-referrer"
    assert sum("referrer-policy" in r["actions"][0]["config"]["headers"] for r in rules) == 1
    assert reject["expressions"] == [f"req.url.path == '{tunnel.WARMUP_PATH}'"]
    assert check["actions"][0]["config"]["content"] == "" and check["actions"][0]["config"]["headers"] == {"cache-control": "no-store"}
    assert check["expressions"][0] == f"req.url.path == '{tunnel.CHECK_PATH}'"
    assert tunnel.COOKIE_NAME in check["expressions"][1] and cookie in check["expressions"][1] and token not in check["expressions"][1]
    assert len(gate["expressions"]) == 1 and tunnel.CHECK_PATH in gate["expressions"][0] and cookie in gate["expressions"][0]
    assert token not in gate["expressions"][0]


def test_only_the_expiry_rule_depends_on_the_closing_time():
    """到点时刻只进第一条规则：换一个时刻，其余四条逐字不变。"""
    a = _policy(closes_at=POLICY_CLOSES)
    b = _policy(closes_at=POLICY_CLOSES + timedelta(days=3, seconds=7))
    cut = "  - name: warmup-ok"
    assert a != b and a[a.index(cut):] == b[b.index(cut):]


@pytest.mark.parametrize("closes_at, written", [
    (datetime(2026, 11, 20, 10, 5, 0, tzinfo=timezone.utc), "2026-11-20T10:05:00Z"),           # 整秒不变
    (datetime(2026, 11, 20, 18, 5, 0, tzinfo=timezone(timedelta(hours=8))), "2026-11-20T10:05:00Z"),  # 换算成 UTC
    (datetime(2026, 11, 20, 10, 5, 0, 1, tzinfo=timezone.utc), "2026-11-20T10:05:01Z"),        # 小数秒向上取整
    (datetime(2026, 11, 20, 10, 5, 0, 999999, tzinfo=timezone.utc), "2026-11-20T10:05:01Z"),
    (datetime(2026, 12, 31, 23, 59, 59, 500000, tzinfo=timezone.utc), "2027-01-01T00:00:00Z"),  # 进位跨日跨年
])
def test_policy_instant_is_utc_whole_seconds_rounded_up(closes_at, written):
    assert policy_instant(closes_at) == written


def test_policy_instant_and_policy_reject_a_naive_closing_time():
    naive = datetime(2026, 11, 20, 10, 5, 0)
    with pytest.raises(ValueError, match="须带时区"):
        policy_instant(naive)
    with pytest.raises(ValueError, match="须带时区"):
        _policy(closes_at=naive)


def test_policy_refuses_an_instant_that_could_break_the_string_literal(monkeypatch):
    """写进策略之前按固定形态全匹配：形态不对的时刻（这里模拟一个带引号的值）不进策略。"""
    monkeypatch.setattr(tunnel, "policy_instant", lambda t: "2026-11-20T10:05:00Z') || true || ('")
    with pytest.raises(ValueError, match="写法不对"):
        _policy()


_NODE = shutil.which("node")


@pytest.mark.skipif(_NODE is None, reason="需要 node 执行预热页脚本（CI 的 pytest 作业装了 Node 22）")
@pytest.mark.parametrize("status, kind, marker_suffix", [
    (200, "ready", ""), (401, "denied", ""), (429, "error", " 429"), (500, "error", " 500"), ("reject", "error", ""),
])
def test_warmup_page_script_classifies_only_401_as_denied(status, kind, marker_suffix):
    """预热页脚本的分类（ADR 0051 决策 13）：校验响应 200 → READY；只有 401 → DENIED（确定性拒绝、worker 归 precheck_failed）；
    429、5xx 与请求失败 → ERROR（拿不准，worker 有界重试）。把生成的 <script> 交给 node 执行、注入桩 fetch 与桩 document，
    断言标题、正文标记与校验请求的形态——只核字面量守不住这段分支逻辑。"""
    rules = yaml.safe_load(_policy())["on_http_request"]
    warmup_ok = next(r for r in rules if r["name"] == "warmup-ok")
    script = re.search(r"<script>(.*?)</script>", warmup_ok["actions"][0]["config"]["content"], re.S).group(1)
    harness = (
        "const STATUS = process.env.S; const el = { textContent: '' }; const doc = { title: '', getElementById: () => el };\n"
        "globalThis.document = doc;\n"
        "globalThis.fetch = (u, o) => { globalThis.__req = { u, o }; return STATUS === 'reject' ? Promise.reject(new Error('net')) : Promise.resolve({ status: Number(STATUS) }); };\n"
        + script + "\n"
        "setTimeout(() => process.stdout.write(JSON.stringify({ title: doc.title, marker: el.textContent, req: globalThis.__req })), 0);\n"
    )
    out = subprocess.run([_NODE, "-e", harness], env={**os.environ, "S": str(status)}, capture_output=True, text=True, timeout=30)
    assert out.returncode == 0, out.stderr
    got = json.loads(out.stdout)
    assert got["title"] == tunnel.WARMUP_TITLES[kind]
    assert got["marker"] == tunnel.WARMUP_MARKERS[kind] + marker_suffix
    assert got["req"] == {"u": tunnel.CHECK_PATH, "o": {"credentials": "same-origin", "cache": "no-store"}}


# ---------- map_origin_in_jobs：带边界的识别（ADR 0035 决策 2） ----------

ADR_TRAILING_PUNCT = ".,;:!)]'"  # ADR 0035 决策 2 原文的收尾标点，独立于实现写死：实现少一个字符时样本不会跟着消失


def test_trailing_punct_set_matches_adr():
    assert tunnel._TRAILING_PUNCT == set(ADR_TRAILING_PUNCT)

def _job_with(text: str, argument: StepArgument | None = None) -> Job:
    return Job(
        scope_id="s", scope_name="s", engine="midscene",
        scenarios=(Scenario(id="s:1", name="sc", steps=(
            Step(0, "Given", text, argument=argument),
        )),), timeout_s=300.0,
    )


BASE = "https://abc.ngrok-free.app"
ORIGIN = "http://localhost:3000"


@pytest.mark.parametrize("text, expected", [
    ("http://localhost:3000/x", "https://abc.ngrok-free.app/x"),
    ("http://localhost:3000", "https://abc.ngrok-free.app"),
    ("next=http://localhost:3000/x", "next=https://abc.ngrok-free.app/x"),
    ("去 http://localhost:3000。", "去 https://abc.ngrok-free.app。"),
    ("Go to http://localhost:3000.", "Go to https://abc.ngrok-free.app."),
    ("(see http://localhost:3000)", "(see https://abc.ngrok-free.app)"),
    ("打开http://localhost:3000/a页面", "打开https://abc.ngrok-free.app/a页面"),
    ("先 http://localhost:3000/a 再 http://localhost:3000/b", "先 https://abc.ngrok-free.app/a 再 https://abc.ngrok-free.app/b"),
    # 不命中：别的主机或端口、不是 scheme 起点
    ("http://localhost:3000.evil/", "http://localhost:3000.evil/"),
    ("http://localhost:30001/x", "http://localhost:30001/x"),
    ("xhttp://localhost:3000", "xhttp://localhost:3000"),
    ("http://localhost:3000abc", "http://localhost:3000abc"),
    # 不命中：紧跟的是地址字符、但不是路径 / 查询 / 片段起点，也不只是收尾标点——它是另一个地址
    ("http://localhost:3000:8080/x", "http://localhost:3000:8080/x"),
    ("http://localhost:3000@evil/", "http://localhost:3000@evil/"),
    ("http://localhost:3000%2Fx", "http://localhost:3000%2Fx"),
    ("http://localhost:3000http://localhost:3000/x", "http://localhost:3000http://localhost:3000/x"),
    # 嵌套与相邻：地址出现在另一个地址的查询值里、或只隔一个逗号，逐处识别
    ("http://localhost:3000/go?next=http://localhost:3000/x", "https://abc.ngrok-free.app/go?next=https://abc.ngrok-free.app/x"),
    ("http://localhost:3000/a,http://localhost:3000/b", "https://abc.ngrok-free.app/a,https://abc.ngrok-free.app/b"),
    ("http://localhost:3000.evil/?next=http://localhost:3000/x", "http://localhost:3000.evil/?next=https://abc.ngrok-free.app/x"),  # 外层不命中也不影响内层
] + [(f"见 {ORIGIN}{ch} 处", f"见 {BASE}{ch} 处") for ch in ADR_TRAILING_PUNCT]  # 每个收尾标点单独核，不只核组合
  + [(f"（{ORIGIN}）。", f"（{BASE}）。")])
def test_replace_origin_boundaries(text, expected):
    assert tunnel.replace_origin(text, ORIGIN, BASE) == expected


def test_map_replaces_step_text_prefix():
    out = map_origin_in_jobs([_job_with('打开 "http://localhost:3000/login"')], ORIGIN, BASE)
    assert out[0].scenarios[0].steps[0].text == '打开 "https://abc.ngrok-free.app/login"'


def test_map_replaces_docstring_and_datatable_cells_independently():
    arg = StepArgument(kind="dataTable", rows=(("http://localhost:3000/a", "x"), ("y", "http://localhost:3000.evil/")))
    out = map_origin_in_jobs([_job_with("表", arg)], ORIGIN, BASE)
    assert out[0].scenarios[0].steps[0].argument.rows == (("https://abc.ngrok-free.app/a", "x"), ("y", "http://localhost:3000.evil/"))
    doc = StepArgument(kind="docString", content="第一行 http://localhost:3000/p\n第二行 http://localhost:3000")
    out2 = map_origin_in_jobs([_job_with("文", doc)], ORIGIN, BASE)
    assert out2[0].scenarios[0].steps[0].argument.content == "第一行 https://abc.ngrok-free.app/p\n第二行 https://abc.ngrok-free.app"


def test_map_leaves_other_jobs_and_original_untouched():
    job = _job_with('打开 "http://localhost:3000/login"')
    out = map_origin_in_jobs([job, _job_with("别的")], ORIGIN, BASE)
    assert job.scenarios[0].steps[0].text == '打开 "http://localhost:3000/login"'  # 原 jobs 不变
    assert out[1].scenarios[0].steps[0].text == "别的"


# ---------- normalize_origin：--expose-local 的取值只接受 origin（ADR 0035 决策 2） ----------

@pytest.mark.parametrize("value, expected", [
    ("http://localhost:3000", "http://localhost:3000"),
    ("http://localhost:3000/", "http://localhost:3000"),  # 末尾恰好一个斜杠：去掉
    ("https://127.0.0.1:8443/", "https://127.0.0.1:8443"),
    ("http://192.168.1.50:3000", "http://192.168.1.50:3000"),
    ("http://[::1]:3000/", "http://[::1]:3000"),
    ("http://Example.test:3000", "http://Example.test:3000"),  # 大小写原样保留：映射按 feature 的书写形式逐字匹配
])
def test_normalize_origin_accepts_origins_and_drops_one_trailing_slash(value, expected):
    assert normalize_origin(value) == expected


@pytest.mark.parametrize("value", [
    "http://localhost:3000/login",       # 路径：不隐式截断，截掉会静默改变意图
    "http://localhost:3000//",           # 不止一个斜杠
    "http://localhost:3000?x=1",         # 查询串
    "http://localhost:3000/?",           # 空查询串也算
    "http://localhost:3000#top",         # 片段
    "http://user:pw@localhost:3000",     # 用户信息
    "ftp://localhost:3000",              # http 与 https 之外的 scheme
    "localhost:3000",                    # 缺 scheme
    "http://",                           # 缺主机
    "http:///",
    "http://localhost:99999",            # 端口越界
    "http://localhost:abc",              # 端口不是数字
    "http://localhost:3000:8080",
    "http://localhost:",                 # 冒号之后缺少端口号
    "http://[::1]:/",
    "http://localhost:0",                # 0 号端口
    " http://localhost:3000",            # 含空白
    "http://localhost:3000\n",
])
def test_normalize_origin_rejects_non_origin_values(value):
    with pytest.raises(TunnelError, match="不是 origin"):
        normalize_origin(value)


def test_map_with_trailing_slash_origin_still_maps_paths():
    """取值带末尾斜杠时，step 里的 `http://localhost:3000/login` 照常映射：不归一化的话 origin 之后剩下 `login`、
    判为不命中，job 文本里留着本机地址，云端浏览器导航失败。"""
    out = map_origin_in_jobs([_job_with('打开 "http://localhost:3000/login"')], ORIGIN + "/", BASE)
    assert out[0].scenarios[0].steps[0].text == '打开 "https://abc.ngrok-free.app/login"'


def test_map_rejects_origin_with_path():
    with pytest.raises(TunnelError, match="不是 origin"):
        map_origin_in_jobs([_job_with('打开 "http://localhost:3000/login"')], ORIGIN + "/login", BASE)


# ---------- NgrokTunnel（假 SDK：只模仿 SDK 的外部表面） ----------

CLOSES = datetime(2026, 11, 20, 10, 5, 0, tzinfo=timezone.utc)
PUBLIC_URL = "https://xyz.ngrok-free.app"


class _FakeListener:
    def __init__(self, url: str) -> None:
        self._url = url

    def url(self) -> str:
        return self._url


class _FakeSdk:
    """SDK 的外部表面：`forward(addr, **options)` 记录参数、返回只有 `url()` 的监听对象；`disconnect(url)` 记录调用。失败时抛装置
    真实记录到的异常形态。`forward_gate` / `disconnect_gate` 让调用阻塞在一个 Event 上（等待时释放解释器锁，同 SDK 等网络时）。
    自己只保留监听对象的弱引用，好让「谁持有它」可观察。"""

    def __init__(self, url: str = PUBLIC_URL, *, forward_error: Exception | None = None,
                 forward_gate: threading.Event | None = None, disconnect_error: Exception | None = None,
                 disconnect_gate: threading.Event | None = None) -> None:
        self.url = url
        self.forward_error, self.forward_gate = forward_error, forward_gate
        self.disconnect_error, self.disconnect_gate = disconnect_error, disconnect_gate
        self.forwards: list[tuple[str, dict]] = []
        self.forward_entered = threading.Event()
        self.disconnects: list[str | None] = []
        self.disconnect_entered = threading.Event()
        self.disconnect_returned = threading.Event()
        self.listener_refs: list[weakref.ref] = []

    def forward(self, addr=None, **options):
        self.forwards.append((addr, options))
        self.forward_entered.set()
        if self.forward_gate is not None:
            self.forward_gate.wait(5.0)
        if self.forward_error is not None:
            raise self.forward_error
        listener = _FakeListener(self.url)
        self.listener_refs.append(weakref.ref(listener))
        return listener

    def disconnect(self, url=None):
        self.disconnects.append(url)
        self.disconnect_entered.set()
        try:
            if self.disconnect_gate is not None:
                self.disconnect_gate.wait(5.0)
            if self.disconnect_error is not None:
                raise self.disconnect_error
        finally:
            self.disconnect_returned.set()


def _start(sdk: _FakeSdk, origin: str = "http://localhost:3000", **kw) -> TunnelInfo:
    return NgrokTunnel(load_sdk=lambda: sdk).start(origin, closes_at=CLOSES, **kw)


def _cookie_in(policy: str) -> str:
    return re.search(r"__Host-gherkai_tunnel=([0-9a-f]+);", policy).group(1)


def test_start_hands_the_sdk_the_origin_env_token_and_this_runs_policy():
    """交给 SDK 的参数（ADR 0035 决策 1）：上游地址是归一化之后的 origin；令牌经 `authtoken_from_env` 取、不显式传入；流量策略就是用
    这次的令牌、cookie 与到点时刻渲染的那份。返回的地址来自监听对象，预热地址带这次的令牌，repr 里没有预热地址与关闭函数。"""
    sdk = _FakeSdk()
    info = _start(sdk, "http://localhost:3000/")
    [(addr, options)] = sdk.forwards
    assert addr == "http://localhost:3000"
    assert set(options) == {"authtoken_from_env", "traffic_policy"} and options["authtoken_from_env"] is True
    token = info.warmup_url.rsplit("=", 1)[1]
    cookie = _cookie_in(options["traffic_policy"])
    assert re.fullmatch(r"[0-9a-f]{32}", token) and re.fullmatch(r"[0-9a-f]{32}", cookie) and cookie != token
    assert options["traffic_policy"] == tunnel.render_traffic_policy(token, cookie, closes_at=CLOSES)
    assert info.url == PUBLIC_URL and info.local_origin == "http://localhost:3000"
    assert info.warmup_url == warmup_url_for(PUBLIC_URL, token)
    assert token not in repr(info) and tunnel.WARMUP_PATH not in repr(info) and "closer" not in repr(info)
    assert sdk.disconnects == []  # 建成之后不自行关闭：由宿主调 close()


def test_each_start_uses_fresh_secrets_and_has_no_switch_to_turn_auth_off():
    """令牌与 cookie 每次都换（ADR 0051 决策 13）；没有关掉鉴权的开关（ADR 0035「边界与不变量」）。"""
    sdk = _FakeSdk()
    a, b = _start(sdk), _start(sdk)
    assert a.warmup_url != b.warmup_url
    assert _cookie_in(sdk.forwards[0][1]["traffic_policy"]) != _cookie_in(sdk.forwards[1][1]["traffic_policy"])
    with pytest.raises(TypeError):
        NgrokTunnel(load_sdk=lambda: sdk).start("http://localhost:3000", closes_at=CLOSES, with_auth=False)


@pytest.mark.parametrize("origin, addr, verify_off", [
    ("http://localhost:3000", "http://localhost:3000", False),
    ("https://127.0.0.1:8443", "https://127.0.0.1:8443", True),
    ("HTTP://Example.test:3000", "http://Example.test:3000", False),   # 只有 scheme 转成小写
    ("HTTPS://Example.test:8443/", "https://Example.test:8443", True),  # 判断是不是 https 看转换之后的那一份
])
def test_upstream_address_lowercases_scheme_and_https_skips_upstream_verification(origin, addr, verify_off):
    """ADR 0035 决策 1「交给 SDK 的上游地址」：scheme 转小写、其余原样；https 的上游给 `verify_upstream_tls=False`，http 的不给这个键。
    origin 本身保留书写形式（映射按书写形式逐字匹配）。"""
    sdk = _FakeSdk()
    info = _start(sdk, origin)
    [(got_addr, options)] = sdk.forwards
    assert got_addr == addr
    if verify_off:
        assert options["verify_upstream_tls"] is False
    else:
        assert "verify_upstream_tls" not in options
    assert info.local_origin == normalize_origin(origin)


def test_start_rejects_a_non_origin_before_loading_the_sdk():
    loads: list[int] = []

    def load():
        loads.append(1)
        return _FakeSdk()

    with pytest.raises(TunnelError, match="不是 origin"):
        NgrokTunnel(load_sdk=load).start("http://localhost:3000/login", closes_at=CLOSES)
    assert loads == []


def test_default_loader_is_looked_up_at_call_time(monkeypatch):
    """不给 `load_sdk` 时在调用那一刻取模块里的 `_import_sdk`：`make_tunnel` 构造的实例同样经它导入。"""
    sdk = _FakeSdk()
    monkeypatch.setattr(tunnel, "_import_sdk", lambda: sdk)
    monkeypatch.setenv("NGROK_AUTHTOKEN", "tok")
    t = make_tunnel("ngrok")
    t.check_prerequisites()
    info = t.start("http://localhost:3000", closes_at=CLOSES)
    assert info.url == PUBLIC_URL and len(sdk.forwards) == 1


# ---------- 启动失败的说法（ADR 0035 决策 1「启动失败的说法按原因分」第 3、4 种） ----------

_ADDRESS_IN_USE_TEXT = (
    "隧道没有建成：这个 ngrok 账号上另一条在线的隧道占用了同一个地址（ERR_NGROK_334）。"
    "请等那条隧道下线之后再试；如果它属于另一个带 --expose-local 的 gherkai 运行，持有它的进程退出之后它就会下线。")
_RULE_LIMIT_DESC = ("Policy configuration has exceeded its rule per policy limit of 5. Please check "
                    "https://ngrok.com/features/traffic-policy to view your options or contact us at support@ngrok.com.")


@pytest.mark.parametrize("error, expected", [
    # 装置记录到的真实形态：三项参数，第三项是错误码；334 的说明里带换行
    (ValueError("failed to start listener",
                "The endpoint 'https://x.ngrok-free.dev' is already online. Either\n1. stop your existing endpoint first, or\n"
                "2. start both endpoints with `--pooling-enabled` to load balance between them.", "ERR_NGROK_334"),
     _ADDRESS_IN_USE_TEXT),
    (ValueError("failed to start listener", _RULE_LIMIT_DESC, "ERR_NGROK_2264"),
     f"隧道没有建成：{_RULE_LIMIT_DESC}（ERR_NGROK_2264）。"),
    (ValueError("failed to connect session", "line one\n  line two", "ERR_NGROK_105"),
     "隧道没有建成：line one line two（ERR_NGROK_105）。"),
    # 连不上隧道服务时的真实形态：两项参数、没有错误码
    (ValueError("failed to connect session", "tls handshake error"),
     "隧道没有建成：failed to connect session: tls handshake error。"),
    (ValueError("a", "b", "not a code"), "隧道没有建成：a: b: not a code。"),  # 第三项不是错误码：不按错误码分类
    (RuntimeError("x"), "隧道没有建成：x。"),
    (RuntimeError(), "隧道没有建成：RuntimeError。"),
    (TimeoutError("sdk's own timeout"), "隧道没有建成：sdk's own timeout。"),  # SDK 自己抛的 TimeoutError 不当作产品的时限
])
def test_start_failures_map_to_one_line_messages(error, expected):
    sdk = _FakeSdk(forward_error=error)
    with pytest.raises(TunnelError) as ei:
        _start(sdk)
    assert str(ei.value) == expected
    assert sdk.disconnects == []  # 没有建成，没有要关闭的会话


def test_start_failure_message_masks_the_token_value(monkeypatch):
    monkeypatch.setenv("NGROK_AUTHTOKEN", "2xSeCrEtToKeN")
    sdk = _FakeSdk(forward_error=ValueError("failed to connect session", "token 2xSeCrEtToKeN is invalid", "ERR_NGROK_105"))
    with pytest.raises(TunnelError) as ei:
        _start(sdk)
    assert str(ei.value) == "隧道没有建成：token *** is invalid（ERR_NGROK_105）。"


# ---------- 起隧道的时限与迟到的监听（ADR 0035 决策 1「起隧道的时限」） ----------

def test_start_timeout_default_is_twenty_seconds():
    """起隧道的时限缺省 20 秒：这个取值写在 ADR 0035 决策 1「起隧道的时限」里，用户文档也引用了它（「20 秒内没有连上隧道服务」）。
    其余用例只拿这个符号互相比较，取值变了只有这一条报出；改它时 ADR 与用户文档一并改。"""
    assert tunnel.START_TIMEOUT_S == 20.0


def test_start_gives_up_after_timeout_and_closes_the_listener_that_arrives_late():
    """`forward` 阻塞在一个 Event 上（释放解释器锁）：按时限放弃、给出超时那一句；随后放开，迟到建成的监听被关闭。"""
    gate = threading.Event()
    sdk = _FakeSdk(forward_gate=gate)
    t0 = time.monotonic()
    with pytest.raises(TunnelError) as ei:
        _start(sdk, timeout_s=0.2)
    elapsed = time.monotonic() - t0
    assert 0.2 <= elapsed < 1.0
    assert str(ei.value) == "隧道没有建成：0.2 秒内没有连上隧道服务。请确认本机能访问外网后重新执行。"
    assert sdk.disconnects == []
    gate.set()
    assert sdk.disconnect_entered.wait(1.0)
    assert sdk.disconnects == [PUBLIC_URL]


def test_call_with_timeout_returns_the_result_and_does_not_hand_it_to_on_late():
    late: list = []
    assert tunnel._call_with_timeout(lambda: "v", 1.0, on_late=late.append) == "v"
    assert late == []


def test_call_with_timeout_reraises_the_callees_error():
    late: list = []
    with pytest.raises(KeyError):
        tunnel._call_with_timeout(lambda: {}["k"], 1.0, on_late=late.append)
    assert late == []


def test_call_with_timeout_hands_a_late_result_to_on_late_exactly_once():
    gate, late_seen = threading.Event(), threading.Event()
    late: list = []

    def fn():
        gate.wait(5.0)
        return "late"

    def on_late(v):
        late.append(v)
        late_seen.set()

    with pytest.raises(TimeoutError):
        tunnel._call_with_timeout(fn, 0.1, on_late=on_late)
    assert late == []
    gate.set()
    assert late_seen.wait(1.0)
    time.sleep(0.05)
    assert late == ["late"]


def test_call_with_timeout_writes_nothing_when_an_abandoned_call_fails(capfd):
    """被放弃之后才失败的调用、以及抛错的 on_late，都不经线程的缺省异常处理写到标准错误：后台进程在回报之前不往标准错误写字。"""
    gate, finished = threading.Event(), threading.Event()

    def fn():
        gate.wait(5.0)
        try:
            raise RuntimeError("late failure")
        finally:
            finished.set()

    with pytest.raises(TimeoutError):
        tunnel._call_with_timeout(fn, 0.05, on_late=lambda v: None)
    gate.set()
    assert finished.wait(1.0)

    gate2, late_raised = threading.Event(), threading.Event()

    def on_late(_v):
        late_raised.set()
        raise RuntimeError("on_late failure")

    def fn2():
        gate2.wait(5.0)
        return "v"

    with pytest.raises(TimeoutError):
        tunnel._call_with_timeout(fn2, 0.05, on_late=on_late)
    gate2.set()
    assert late_raised.wait(1.0)
    time.sleep(0.1)  # 让两个线程都走完
    assert capfd.readouterr().err == ""


def test_call_with_timeout_interrupted_while_waiting_still_closes_the_late_result():
    """等待期间被 Ctrl-C 打断（真实的 SIGINT 送到主线程）：KeyboardInterrupt 照常传出，之后才到的结果交给 on_late，不留在宿主里
    无人关闭。"""
    gate, late_seen = threading.Event(), threading.Event()
    entered = threading.Event()
    late: list = []

    def fn():
        entered.set()
        gate.wait(5.0)
        return "late"

    def on_late(v):
        late.append(v)
        late_seen.set()

    main = threading.main_thread().ident
    assert threading.get_ident() == main  # SIGINT 只送到主线程

    def interrupt():
        entered.wait(5.0)
        time.sleep(0.05)
        signal.pthread_kill(main, signal.SIGINT)

    threading.Thread(target=interrupt, daemon=True).start()
    with pytest.raises(KeyboardInterrupt):
        tunnel._call_with_timeout(fn, 5.0, on_late=on_late)
    gate.set()
    assert late_seen.wait(1.0)
    assert late == ["late"]


# ---------- 关闭会话 ----------

def test_close_disconnects_once_and_later_calls_do_nothing():
    sdk = _FakeSdk()
    info = _start(sdk)
    info.close()
    info.close()
    assert sdk.disconnects == [PUBLIC_URL]


def test_close_swallows_disconnect_errors():
    sdk = _FakeSdk(disconnect_error=RuntimeError("boom"))
    info = _start(sdk)
    info.close()  # 不外抛
    info.close()
    assert sdk.disconnects == [PUBLIC_URL]


def _close_without_interrupt(info: TunnelInfo) -> None:
    """调 close()；KeyboardInterrupt 漏出来即判失败（否则它会中止整个测试会话）。"""
    try:
        info.close()
    except KeyboardInterrupt:
        pytest.fail("close() 把 KeyboardInterrupt 抛了出来")


def test_close_swallows_a_keyboard_interrupt_from_disconnect_and_does_nothing_afterwards():
    """关闭期间的任何异常都不外抛，含 KeyboardInterrupt（ADR 0035 决策 1）：之后再调不再动作。"""
    sdk = _FakeSdk(disconnect_error=KeyboardInterrupt())
    info = _start(sdk)
    _close_without_interrupt(info)
    _close_without_interrupt(info)
    assert sdk.disconnects == [PUBLIC_URL]


def test_close_interrupted_by_ctrl_c_while_waiting_returns_without_raising():
    """等待关闭期间主线程收到真实的 SIGINT（前台 run 在 atexit 里关闭会话时按 Ctrl-C）：close() 不外抛、随即返回，不等到关闭的时限。"""
    gate = threading.Event()
    sdk = _FakeSdk(disconnect_gate=gate)
    info = _start(sdk)
    main = threading.main_thread().ident
    assert threading.get_ident() == main  # SIGINT 只送到主线程

    def interrupt():
        sdk.disconnect_entered.wait(5.0)
        time.sleep(0.05)
        signal.pthread_kill(main, signal.SIGINT)

    threading.Thread(target=interrupt, daemon=True).start()
    t0 = time.monotonic()
    try:
        _close_without_interrupt(info)
    finally:
        gate.set()
    assert time.monotonic() - t0 < tunnel.CLOSE_TIMEOUT_S
    _close_without_interrupt(info)
    assert sdk.disconnects == [PUBLIC_URL]


def test_close_gives_up_when_disconnect_blocks(monkeypatch):
    monkeypatch.setattr(tunnel, "CLOSE_TIMEOUT_S", 0.2)
    gate = threading.Event()
    sdk = _FakeSdk(disconnect_gate=gate)
    info = _start(sdk)
    t0 = time.monotonic()
    info.close()
    elapsed = time.monotonic() - t0
    gate.set()
    assert 0.2 <= elapsed < 1.0
    assert sdk.disconnects == [PUBLIC_URL]


def test_a_second_close_waits_until_the_first_one_has_finished():
    """两个线程同时关闭：后来者在前一次关闭结束之前不返回，SDK 只被调用一次。"""
    gate = threading.Event()
    sdk = _FakeSdk(disconnect_gate=gate)
    info = _start(sdk)
    first, second = threading.Event(), threading.Event()
    threading.Thread(target=lambda: (info.close(), first.set()), daemon=True).start()
    assert sdk.disconnect_entered.wait(1.0)
    threading.Thread(target=lambda: (info.close(), second.set()), daemon=True).start()
    assert not second.wait(0.2)
    gate.set()
    assert first.wait(1.0) and second.wait(1.0)
    assert sdk.disconnect_returned.is_set() and sdk.disconnects == [PUBLIC_URL]


def test_tunnel_info_holds_the_listener_object():
    """返回的隧道事实持有 SDK 给出的监听对象（ADR 0035 决策 1）：不依赖「监听对象被回收之后隧道仍在线」。"""
    sdk = _FakeSdk()
    info = _start(sdk)
    [ref] = sdk.listener_refs
    gc.collect()
    assert ref() is not None
    del info
    gc.collect()
    assert ref() is None  # 只有隧道事实持有它


# ---------- 前置检查与导入 SDK（ADR 0035 决策 1「前置条件」） ----------

_NOT_INSTALLED_TEXT = ("--expose-local 要用的隧道组件没有安装。请在安装 gherkai 时加上 tunnel 组件后重新执行，"
                       "例如 uv tool install 'gherkai[local,tunnel]'（已经装了别的组件的，要一并列出）。")
_NO_TOKEN_TEXT = ("--expose-local 需要 ngrok 的令牌，但环境变量 NGROK_AUTHTOKEN 没有设置。"
                  "请在 ngrok 控制台取得令牌，设置 NGROK_AUTHTOKEN 后重新执行。")


def _raising(e: BaseException):
    def load():
        raise e
    return load


@pytest.mark.parametrize("error, expected", [
    (ModuleNotFoundError("No module named 'ngrok'", name="ngrok"), _NOT_INSTALLED_TEXT),
    (ModuleNotFoundError("No module named 'ngrok.ngrok'", name="ngrok.ngrok"),
     "--expose-local 要用的隧道组件已经安装，但无法加载：No module named 'ngrok.ngrok'。请重新安装带 tunnel 组件的 gherkai 后重新执行。"),
    (ImportError("dlopen failed: symbol not found"),
     "--expose-local 要用的隧道组件已经安装，但无法加载：dlopen failed: symbol not found。请重新安装带 tunnel 组件的 gherkai 后重新执行。"),
    (OSError("cannot map file"),
     "--expose-local 要用的隧道组件已经安装，但无法加载：cannot map file。请重新安装带 tunnel 组件的 gherkai 后重新执行。"),
    (RuntimeError("native runtime failed to initialize"),
     "--expose-local 要用的隧道组件已经安装，但无法加载：native runtime failed to initialize。请重新安装带 tunnel 组件的 gherkai 后重新执行。"),
    (SyntaxError("invalid syntax"),
     "--expose-local 要用的隧道组件已经安装，但无法加载：invalid syntax。请重新安装带 tunnel 组件的 gherkai 后重新执行。"),
])
def test_sdk_load_failures_are_told_apart_by_exception_type(monkeypatch, error, expected):
    """「没有装」与「装了但无法加载」只按异常类型分；前置检查与起隧道经同一处导入，给出同一句。"""
    monkeypatch.setenv("NGROK_AUTHTOKEN", "tok")
    with pytest.raises(TunnelError) as pre:
        NgrokTunnel(load_sdk=_raising(error)).check_prerequisites()
    with pytest.raises(TunnelError) as st:
        NgrokTunnel(load_sdk=_raising(error)).start("http://localhost:3000", closes_at=CLOSES)
    assert str(pre.value) == str(st.value) == expected


@pytest.mark.parametrize("value", [None, "", "   "])
def test_missing_or_empty_token_is_rejected_after_the_sdk_loads(monkeypatch, value):
    if value is not None:
        monkeypatch.setenv("NGROK_AUTHTOKEN", value)
    loads: list[int] = []

    def load():
        loads.append(1)
        return _FakeSdk()

    with pytest.raises(TunnelError) as ei:
        NgrokTunnel(load_sdk=load).check_prerequisites()
    assert str(ei.value) == _NO_TOKEN_TEXT
    assert loads == [1]


def test_prerequisites_pass_with_sdk_and_token_without_touching_the_network(monkeypatch):
    monkeypatch.setenv("NGROK_AUTHTOKEN", "tok")
    sdk = _FakeSdk()
    NgrokTunnel(load_sdk=lambda: sdk).check_prerequisites()
    assert sdk.forwards == [] and sdk.disconnects == []


_SDK_FAMILIES = ("ngrok", "muxado", "rustls", "tokio")


def test_loading_the_sdk_silences_every_log_family_of_its_native_library(monkeypatch, capfd):
    """SDK 原生库的日志经桥接落在 `ngrok`、`muxado`、`rustls`、`tokio` 几族 logger 上：导入之后各族都接空处理器、不向上传播，警告不写
    标准错误（后台进程在回报之前不往标准错误写字，ADR 0035 决策 3「输出」）。

    根 logger 的处理器在用例里清空，与没有配置 logging 的进程相同：这时 logging 用缺省处理器把警告写到标准错误，对照组的那一条因此
    真的写了出来，说明这条用例看得见漏网的警告。"""
    for name in (*_SDK_FAMILIES, ""):
        logger = logging.getLogger(name)
        monkeypatch.setattr(logger, "handlers", [])
        if name:
            monkeypatch.setattr(logger, "propagate", True)
    monkeypatch.setenv("NGROK_AUTHTOKEN", "tok")
    t = NgrokTunnel(load_sdk=lambda: _FakeSdk())
    t.check_prerequisites()
    t.check_prerequisites()
    for name in _SDK_FAMILIES:
        logger = logging.getLogger(name)
        assert logger.propagate is False, name
        assert [type(h) for h in logger.handlers] == [logging.NullHandler], name  # 重复导入不叠加处理器
    for name in ("ngrok.tunnel_ext", "muxado.heartbeat", "rustls.client", "tokio.runtime"):
        logging.getLogger(name).warning(f"{name}: simulated warning")
    logging.getLogger("gherkai-test-control").warning("control")
    assert capfd.readouterr().err == "control\n"


def test_importing_the_tunnel_module_does_not_import_the_sdk(tmp_path):
    """顶层不导入 SDK（ADR 0037 决策 2c）：CLI 建解析器时就导入本模块。同一进程里别的用例可能已导入 SDK，所以在子进程里看。"""
    code = ("import sys\n"
            "import gherkai_runtime.tunnel as t\n"
            "t.make_tunnel('ngrok')\n"
            "t.normalize_origin('http://localhost:3000')\n"
            "print('ngrok' in sys.modules)\n")
    out = subprocess.run([sys.executable, "-c", code], cwd=tmp_path, capture_output=True, text=True, timeout=60,
                         stdin=subprocess.DEVNULL)
    assert out.returncode == 0, out.stderr
    assert out.stdout.strip() == "False"


def test_installed_sdk_has_the_functions_the_tunnel_calls():
    """装了 SDK 时，真实模块上有本模块调用的两个函数（只看属性在不在，不调用、不联网）。绕开自动夹具：直接导入。"""
    sdk = pytest.importorskip("ngrok")
    assert hasattr(sdk, "forward") and hasattr(sdk, "disconnect")


def test_make_tunnel_unknown_provider():
    with pytest.raises(TunnelError, match="未知隧道 provider"):
        make_tunnel("nope")
