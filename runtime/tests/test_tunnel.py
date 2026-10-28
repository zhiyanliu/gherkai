"""tunnel 模块单测（ADR 0035）：origin 映射（纯逻辑）+ NgrokTunnel 编排（fake spawn/API，不真起 ngrok）。

绿即够的边界（CLAUDE.md「绿≠对·别过度」）：映射是纯函数、provider 编排的 fake 覆盖「参数拼装/
轮询/超时/报错」逻辑；「ngrok 真起得来、URL 真可达」是真实边界，由真实运行验证（本机应用 + 真 AgentCore）。
"""
from __future__ import annotations

import io
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

from gherkai_core.model import Job, Scenario, Step, StepArgument
from gherkai_runtime import tunnel
from gherkai_runtime.tunnel import NgrokTunnel, TunnelError, TunnelInfo, make_tunnel, map_origin_in_jobs, stop_tunnel, warmup_url_for


# ---------- TunnelInfo 与边缘契约常量 ----------

FIXTURE = Path(__file__).resolve().parents[2] / "engines" / "fixtures" / "tunnel-warmup.json"


def test_tunnel_info_carries_clean_url_and_token_only_in_warmup_url():
    """隧道事实：url 干净、无凭据；预热地址形态精确；令牌不进 repr（ADR 0051 决策 13）。"""
    info = TunnelInfo(url="https://abc.ngrok-free.app", pid=1, local_origin="http://localhost:3000",
                      warmup_url=warmup_url_for("https://abc.ngrok-free.app", "f" * 32))
    assert "@" not in info.url
    assert info.warmup_url == "https://abc.ngrok-free.app/.well-known/gherkai-tunnel-auth?gherkai_tunnel_token=" + "f" * 32
    assert "f" * 32 not in repr(info)


def test_edge_contract_constants_match_the_cross_language_fixture():
    """路径、参数名、cookie 名、页面标题与正文标记：runtime 与两个 worker 各持一份同值，三方都对同一份 fixture（ADR 0051 决策 13）。"""
    fx = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert (tunnel.WARMUP_PATH, tunnel.CHECK_PATH, tunnel.TOKEN_PARAM, tunnel.COOKIE_NAME) == (
        fx["warmup_path"], fx["check_path"], fx["token_param"], fx["cookie_name"])
    assert tunnel.WARMUP_TITLES == fx["titles"] and tunnel.WARMUP_MARKERS == fx["markers"]


# ---------- 流量策略（边缘契约的四条规则） ----------

def test_traffic_policy_has_four_rules_cookie_spec_and_markers():
    """ADR 0051 决策 13「边缘策略」：恰 4 条规则（免费层上限 5）、不含 basic-auth 与 remove-headers、Set-Cookie 精确等于规格、预热响应带
    no-store 与 no-referrer、四个页面标记与四个标题都在、令牌与 cookie 值各出现在该出现的规则里。"""
    policy = tunnel.render_traffic_policy("a" * 32, "b" * 32)
    assert len(re.findall(r"^  - name:", policy, re.M)) == 4 and 4 <= tunnel.POLICY_RULE_LIMIT
    assert "basic-auth" not in policy and "remove-headers" not in policy
    assert 'set-cookie: "__Host-gherkai_tunnel=' + "b" * 32 + '; Secure; HttpOnly; Path=/; SameSite=None"' in policy
    assert "Domain=" not in policy and "Max-Age" not in policy
    assert policy.count('cache-control: "no-store"') == 4 and 'referrer-policy: "no-referrer"' in policy
    for marker in tunnel.WARMUP_MARKERS.values():
        assert marker in policy, marker
    for title in tunnel.WARMUP_TITLES.values():
        assert title in policy, title
    assert "'" + "a" * 32 + "' in req.url.query_params['gherkai_tunnel_token']" in policy  # 令牌只在预热放行规则里比对
    assert policy.count("b" * 32) == 3  # cookie 值：Set-Cookie、校验路径放行、总闸三处
    with pytest.raises(ValueError):
        tunnel.render_traffic_policy("short", "b" * 32)  # 形态不对的秘密不进策略（模板替换无转义面）


def test_traffic_policy_parses_as_yaml_with_rule_order_statuses_and_gate_semantics():
    """ngrok 读的是解析后的结构、不是字面量，所以按 YAML 解析后核：四条规则按序 warmup-ok / warmup-reject / check-ok / gate，
    状态码 200 / 401 / 200 / 401；预热放行限 GET 且带令牌比对；no-referrer 只在预热放行页；校验路径放行是空响应体、只带 cache-control；
    总闸只认 cookie、不认令牌（令牌只用来换一次 cookie，ADR 0051 决策 13）。"""
    token, cookie = "a" * 32, "b" * 32
    rules = yaml.safe_load(tunnel.render_traffic_policy(token, cookie))["on_http_request"]
    assert [r["name"] for r in rules] == ["warmup-ok", "warmup-reject", "check-ok", "gate"]
    assert [r["actions"][0]["config"]["status_code"] for r in rules] == [200, 401, 200, 401]
    assert all(len(r["actions"]) == 1 and r["actions"][0]["type"] == "custom-response" for r in rules)
    assert all(r["actions"][0]["config"]["headers"]["cache-control"] == "no-store" for r in rules)
    ok, reject, check, gate = rules
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


_NODE = shutil.which("node")


@pytest.mark.skipif(_NODE is None, reason="需要 node 执行预热页脚本（CI 的 pytest 作业装了 Node 22）")
@pytest.mark.parametrize("status, kind, marker_suffix", [
    (200, "ready", ""), (401, "denied", ""), (429, "error", " 429"), (500, "error", " 500"), ("reject", "error", ""),
])
def test_warmup_page_script_classifies_only_401_as_denied(status, kind, marker_suffix):
    """预热页脚本的分类（ADR 0051 决策 13）：校验响应 200 → READY；只有 401 → DENIED（确定性拒绝、worker 归 precheck_failed）；
    429、5xx 与请求失败 → ERROR（拿不准，worker 有界重试）。把生成的 <script> 交给 node 执行、注入桩 fetch 与桩 document，
    断言标题、正文标记与校验请求的形态——只核字面量守不住这段分支逻辑。"""
    rules = yaml.safe_load(tunnel.render_traffic_policy("a" * 32, "b" * 32))["on_http_request"]
    script = re.search(r"<script>(.*?)</script>", rules[0]["actions"][0]["config"]["content"], re.S).group(1)
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
        )),),
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


# ---------- NgrokTunnel（fake spawn/API） ----------

class _FakeProc:
    def __init__(self, alive: bool = True):
        self.pid = 4242
        self._alive = alive

    def poll(self):
        return None if self._alive else 1


def _fake_popen_writing_log(url_value: str | None, spawned: dict, alive: bool = True):
    """fake agent：spawn 时往 --log 指定的文件写 started tunnel 行（None 表示不写，覆盖超时路径）。"""
    from pathlib import Path

    def popen(cmd, **kw):
        spawned["cmd"] = cmd
        if url_value is not None:
            log = cmd[cmd.index("--log") + 1]
            Path(log).write_text(
                json.dumps({"lvl": "info", "msg": "started tunnel", "url": url_value}) + "\n",
                encoding="utf-8")
        return _FakeProc(alive=alive)

    return popen


def test_ngrok_start_spawns_agent_with_policy_and_fresh_secrets():
    """start：agent 命令带日志通道与流量策略文件；策略是四条规则的令牌换 cookie（不是 basic-auth）、文件 0600；预热地址带本次令牌；
    两次 start 的令牌与 cookie 值都不同、各 128 位；不再有关掉鉴权的开关（ADR 0051 决策 13；0035「边界与不变量」）。"""
    import os as _os

    spawned: dict = {}
    t = NgrokTunnel(popen=_fake_popen_writing_log("https://xyz.ngrok-free.app", spawned), sleep=lambda s: None)
    info = t.start("http://localhost:3000")
    assert info.url == "https://xyz.ngrok-free.app" and info.pid == 4242
    cmd = spawned["cmd"]
    assert cmd[0] == "ngrok" and cmd[1] == "http" and cmd[2] == "http://localhost:3000"
    assert "--log" in cmd and "--log-format" in cmd  # 日志文件通道（v3 无 --web-addr，实际运行暴露）
    policy_path = cmd[cmd.index("--traffic-policy-file") + 1]
    assert _os.stat(policy_path).st_mode & 0o777 == 0o600
    policy = open(policy_path, encoding="utf-8").read()
    token = info.warmup_url.rsplit("=", 1)[1]
    assert info.warmup_url == f"https://xyz.ngrok-free.app/.well-known/gherkai-tunnel-auth?gherkai_tunnel_token={token}"
    assert re.fullmatch(r"[0-9a-f]{32}", token) and token in policy and "basic-auth" not in policy
    cookie = re.search(r"__Host-gherkai_tunnel=([0-9a-f]+);", policy).group(1)
    assert len(cookie) == 32 and cookie != token
    info2 = NgrokTunnel(popen=_fake_popen_writing_log("https://xyz.ngrok-free.app", spawned), sleep=lambda s: None).start("http://localhost:3000")
    assert info2.warmup_url != info.warmup_url
    policy2 = open(spawned["cmd"][spawned["cmd"].index("--traffic-policy-file") + 1], encoding="utf-8").read()
    assert re.search(r"__Host-gherkai_tunnel=([0-9a-f]+);", policy2).group(1) != cookie  # cookie 值也每次不同，不只是令牌
    with pytest.raises(TypeError):
        t.start("http://localhost:3000", with_auth=False)  # 曾有的开关已删：隧道模式恒带鉴权


def test_ngrok_start_timeout_reports_authtoken_hint():
    """日志里一直没有 started tunnel（agent 挂着不就绪）→ 超时 TunnelError，点名 authtoken 引导排错。"""
    clock = {"t": 0.0}

    def monotonic():
        clock["t"] += 8.0  # 三跳即越过 20s deadline
        return clock["t"]

    t = NgrokTunnel(popen=_fake_popen_writing_log(None, {}),
                    sleep=lambda s: None, monotonic=monotonic)
    with pytest.raises(TunnelError, match="authtoken"):
        t.start("http://localhost:3000")


def test_ngrok_binary_missing_reports_install_hint():
    def popen(cmd, **kw):
        raise FileNotFoundError("ngrok")

    t = NgrokTunnel(popen=popen)
    with pytest.raises(TunnelError, match="ngrok"):
        t.start("http://localhost:3000")


def test_ngrok_agent_detaches_from_cli_process_group(tmp_path):
    """**真 spawn**（不 fake popen）：agent 必须落在自己的会话/进程组里（ADR 0035 决策 3）。

    这条不能用 fake popen 验——「进程组归属」正是 mock 之外的真实行为（CLAUDE.md「绿≠对」）。它承重：
    同组时 CLI 收终端广播的 SIGINT 会连坐杀掉「还要交棒给后台宿主」的 agent（两个后台宿主本身也 setsid）。
    用一个假 ngrok（写 started tunnel 行后 sleep）走真 subprocess.Popen 起来，只查 pgid、不碰网络。
    """
    import os

    fake = tmp_path / "fake-ngrok"
    fake.write_text(
        '#!/bin/sh\n'
        'while [ $# -gt 0 ]; do\n'
        '  if [ "$1" = "--log" ]; then LOG="$2"; fi\n'
        '  shift\n'
        'done\n'
        'printf \'%s\\n\' \'{"msg":"started tunnel","url":"https://fake.ngrok-free.app"}\' > "$LOG"\n'
        'exec sleep 30\n',
        encoding="utf-8")
    fake.chmod(0o755)

    info = NgrokTunnel(binary=str(fake), sleep=lambda s: None).start("http://localhost:3000")
    try:
        assert info.url == "https://fake.ngrok-free.app"
        assert os.getpgid(info.pid) != os.getpgid(0)  # 自成进程组，不吃终端广播的信号
        assert os.getpgid(info.pid) == info.pid       # setsid 后自身即组长
    finally:
        stop_tunnel(info.pid)  # 宿主按 pid 收尾（唯一拆除面，ADR 0035 决策 1）


def test_make_tunnel_unknown_provider():
    with pytest.raises(TunnelError, match="未知隧道 provider"):
        make_tunnel("nope")


def test_stop_tunnel_idempotent_on_dead_pid():
    stop_tunnel(2 ** 22 + 12345)  # 大概率不存在的 pid：不抛即过（幂等收尾）
