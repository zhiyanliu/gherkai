"""tunnel 模块单测（ADR 0035）：origin 映射（纯逻辑）+ NgrokTunnel 编排（fake spawn/API，不真起 ngrok）。

绿即够的边界（CLAUDE.md「绿≠对·别过度」）：映射是纯函数、provider 编排的 fake 覆盖「参数拼装/
轮询/超时/报错」逻辑；「ngrok 真起得来、URL 真可达」是真实边界，由真跑验证（本机应用 + 真 AgentCore）。
"""
from __future__ import annotations

import io
import json

import pytest

from core.model import Job, Scenario, Step, StepArgument
from gherkai.tunnel import NgrokTunnel, TunnelError, TunnelInfo, make_tunnel, map_origin_in_jobs, stop_tunnel


# ---------- TunnelInfo.mapped_base ----------

def test_mapped_base_embeds_credentials():
    info = TunnelInfo(url="https://abc.ngrok-free.app", auth="u1:p1", pid=1, local_origin="http://localhost:3000")
    assert info.mapped_base == "https://u1:p1@abc.ngrok-free.app"


def test_mapped_base_without_auth_is_plain_url():
    info = TunnelInfo(url="https://abc.ngrok-free.app", auth=None, pid=1, local_origin="http://localhost:3000")
    assert info.mapped_base == "https://abc.ngrok-free.app"


# ---------- map_origin_in_jobs ----------

def _job_with(text: str, argument: StepArgument | None = None) -> Job:
    return Job(
        scope_id="s", scope_name="s", engine="midscene",
        scenarios=(Scenario(id="s:1", name="sc", steps=(
            Step(0, "Given", text, argument=argument),
        )),),
    )


BASE = "https://u:p@abc.ngrok-free.app"


def test_map_replaces_step_text_prefix():
    jobs = [_job_with('打开 "http://localhost:3000/login?next=/home"')]
    out = map_origin_in_jobs(jobs, "http://localhost:3000", BASE)
    assert out[0].scenarios[0].steps[0].text == f'打开 "{BASE}/login?next=/home"'
    # 原 definition 不可变（frozen 重建，不是原地改）
    assert jobs[0].scenarios[0].steps[0].text.startswith('打开 "http://localhost:3000')


def test_map_replaces_docstring_and_datatable():
    arg_doc = StepArgument(kind="docString", content="POST http://localhost:3000/api/items")
    arg_tab = StepArgument(kind="dataTable", rows=(("url", "http://localhost:3000/a"), ("x", "y")))
    jobs = [_job_with("提交", arg_doc), _job_with("表格", arg_tab)]
    out = map_origin_in_jobs(jobs, "http://localhost:3000", BASE)
    assert out[0].scenarios[0].steps[0].argument.content == f"POST {BASE}/api/items"
    assert out[1].scenarios[0].steps[0].argument.rows == (("url", f"{BASE}/a"), ("x", "y"))


def test_map_leaves_non_matching_urls_untouched():
    jobs = [_job_with('打开 "https://wikipedia.org" 再看 "http://127.0.0.1:3000"')]
    out = map_origin_in_jobs(jobs, "http://localhost:3000", BASE)
    # 前缀字符串级匹配：localhost 与 127.0.0.1 不互认（ADR 0035 决策 2，文档写明）
    assert out[0].scenarios[0].steps[0].text == jobs[0].scenarios[0].steps[0].text


# ---------- NgrokTunnel（fake spawn/API） ----------

class _FakeProc:
    def __init__(self, alive: bool = True):
        self.pid = 4242
        self._alive = alive

    def poll(self):
        return None if self._alive else 1


def _fake_popen_writing_log(url_value: str | None, spawned: dict, alive: bool = True):
    """fake agent：spawn 时往 --log 指定的文件写 started tunnel 行（None=不写，覆盖超时路径）。"""
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


def test_ngrok_start_spawns_agent_and_reads_log():
    spawned: dict = {}
    t = NgrokTunnel(popen=_fake_popen_writing_log("https://xyz.ngrok-free.app", spawned),
                    sleep=lambda s: None)
    info = t.start("http://localhost:3000")
    assert info.url == "https://xyz.ngrok-free.app"
    assert info.pid == 4242
    assert info.auth and ":" in info.auth  # basic-auth 默认开启（ADR 0035 决策 4）
    cmd = spawned["cmd"]
    assert cmd[0] == "ngrok" and cmd[1] == "http" and cmd[2] == "http://localhost:3000"
    assert "--log" in cmd and "--log-format" in cmd  # 日志文件通道（v3 无 --web-addr，真跑暴露）
    assert "--traffic-policy-file" in cmd  # 凭据经 Traffic Policy 在边缘拦
    # policy 文件内容真含凭据
    policy = open(cmd[cmd.index("--traffic-policy-file") + 1], encoding="utf-8").read()
    assert "basic-auth" in policy and info.auth in policy


def test_ngrok_start_without_auth_skips_policy():
    spawned: dict = {}
    t = NgrokTunnel(popen=_fake_popen_writing_log("https://xyz.ngrok-free.app", spawned),
                    sleep=lambda s: None)
    info = t.start("http://localhost:3000", with_auth=False)
    assert info.auth is None and info.mapped_base == info.url
    assert "--traffic-policy-file" not in spawned["cmd"]


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
        assert os.getpgid(info.pid) != os.getpgid(0)  # 自成进程组 = 不吃终端广播的信号
        assert os.getpgid(info.pid) == info.pid       # setsid 后自身即组长
    finally:
        stop_tunnel(info.pid)  # 宿主按 pid 收尾（唯一拆除面，ADR 0035 决策 1）


def test_make_tunnel_unknown_provider():
    with pytest.raises(TunnelError, match="未知隧道 provider"):
        make_tunnel("nope")


def test_stop_tunnel_idempotent_on_dead_pid():
    stop_tunnel(2 ** 22 + 12345)  # 大概率不存在的 pid：不抛即过（幂等收尾）
