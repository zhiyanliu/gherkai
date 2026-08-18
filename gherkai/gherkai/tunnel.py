"""隧道口子（ADR 0035）：把「跑 CLI 的机器可达」的被测应用暴露成云端浏览器可访问的公网 URL。

TunnelProvider 形状 = `start(local_origin) -> TunnelInfo`；停止用 `stop_tunnel(pid)`——隧道生命周期
可能跨进程（local submit 的 per-run 进程 / cloud submit 的守护进程收尾），进程对象句柄传不过去，
故 TunnelInfo 携带 pid、由收尾者 kill（ADR 0035 决策 3 的三形态宿主）。

worker/core 对隧道无知：URL 映射（map_origin_in_jobs）在组合根完成、job-in 前替换进 definition
（ADR 0035 决策 2——对 worker/引擎/AI 完全透明）。
"""
from __future__ import annotations

import os
import secrets
import signal
import string
import subprocess
import tempfile
import time
from dataclasses import dataclass, replace
from pathlib import Path

from core.model import Job


class TunnelError(Exception):
    """隧道起不来 / provider 未知 / 前置缺失——调用方接住归「没开跑就被拒」（退 2）。"""


@dataclass(frozen=True)
class TunnelInfo:
    """一条已建立隧道的事实（可序列化落盘 tunnel.json，供跨进程收尾）。"""

    url: str  # 公网 URL（不含凭据），进度行/诊断展示用
    auth: str | None  # "user:pass"（basic-auth 凭据，ADR 0035 决策 4；None=未开认证）
    pid: int  # 隧道 agent 进程 pid（收尾者 stop_tunnel(pid)）
    local_origin: str  # 被暴露的原始 origin（替换源，如 http://localhost:3000）

    @property
    def mapped_base(self) -> str:
        """替换进 job 文本的形态：凭据内嵌 URL（`https://user:pass@host`，ADR 0035 决策 4 方案①——
        浏览器首次导航后凭据进按域 auth cache，同域后续请求自动带、只发隧道域）。"""
        if not self.auth:
            return self.url
        scheme, rest = self.url.split("://", 1)
        return f"{scheme}://{self.auth}@{rest}"


def _gen_auth() -> str:
    """生成隧道专用短命凭据：纯字母数字（规避 URL-encode，ADR 0035 决策 4），每 run 一换。"""
    alphabet = string.ascii_letters + string.digits
    user = "".join(secrets.choice(alphabet) for _ in range(8))
    pwd = "".join(secrets.choice(alphabet) for _ in range(16))
    return f"{user}:{pwd}"


class NgrokTunnel:
    """ngrok 实现（ADR 0035 决策 1，当前唯一 provider）。

    spawn `ngrok http <origin> --log <file> --log-format json` agent 进程 → 轮询日志文件、
    从 `started tunnel` 事件行拿公网 URL。**不走本地 agent API**——v3 的 `ngrok http` 无 `--web-addr`
    flag（真跑暴露：unknown flag；web_addr 是配置文件项、注入需劫持用户 config），日志文件通道
    无端口冲突、天然留诊断（authtoken 缺失等 err 行同在其中）。
    - **authtoken 前置**：用户自配（`NGROK_AUTHTOKEN` env 或 ngrok 配置文件）——未配时 agent 起不来，
      start() 以日志尾部报 TunnelError（点名 authtoken 引导排错）。
    - **basic-auth 默认开启**：Traffic Policy 文件（边缘节点拦截，不带凭据的请求到不了本机）。
    """

    def __init__(self, binary: str = "ngrok", *, popen=subprocess.Popen,
                 sleep=time.sleep, monotonic=time.monotonic) -> None:
        # 依赖可注入（测试 fake spawn；生产默认真物）
        self._binary = binary
        self._popen = popen
        self._sleep = sleep
        self._monotonic = monotonic

    def start(self, local_origin: str, *, with_auth: bool = True, timeout_s: float = 20.0) -> TunnelInfo:
        auth = _gen_auth() if with_auth else None
        log_path = Path(tempfile.mkstemp(prefix="gherkai-tunnel-", suffix=".log")[1])
        cmd = [self._binary, "http", local_origin,
               "--log", str(log_path), "--log-format", "json"]
        policy_path: str | None = None
        if auth:
            # Traffic Policy：basic-auth 在 ngrok 边缘拦（免费 action，ADR 0035 决策 4）。
            # 手写 YAML（结构固定且凭据纯字母数字，无转义面），不为此引 yaml 依赖。
            policy = (
                "on_http_request:\n"
                "  - actions:\n"
                "      - type: basic-auth\n"
                "        config:\n"
                "          credentials:\n"
                f"            - \"{auth}\"\n"
            )
            fd, policy_path = tempfile.mkstemp(prefix="gherkai-tunnel-policy-", suffix=".yml")
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(policy)
            cmd += ["--traffic-policy-file", policy_path]

        try:
            # start_new_session=True（setsid）= agent 脱离 CLI 的会话/进程组：隧道的生命周期由**宿主**决定
            # （ADR 0035 决策 3 三形态宿主 + stop_tunnel(pid)），不该由终端的信号转发决定。否则 submit 时
            # CLI 收 SIGINT/SIGHUP 会连坐杀掉「还要交棒给后台宿主」的 agent（local 交 per-run 进程、cloud 交
            # 守护进程，两个宿主本身也都 setsid）。前台 run 档语义不变：Ctrl-C → KeyboardInterrupt → atexit
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
            try:
                os.kill(proc.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            tail = ""
            try:
                tail = log_path.read_text(encoding="utf-8", errors="replace")[-500:]
            except OSError:
                pass
            raise TunnelError(
                f"ngrok 隧道未就绪（{timeout_s:.0f}s 内拿不到公网 URL）。"
                f"常见原因：authtoken 未配置（NGROK_AUTHTOKEN 或 `ngrok config add-authtoken`）/ 无外网。"
                f"agent 日志尾部：{tail or '（空）'}")
        return TunnelInfo(url=url, auth=auth, pid=proc.pid, local_origin=local_origin)


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


def map_origin_in_jobs(jobs: list[Job], origin: str, base: str) -> list[Job]:
    """把 job 文本中的 origin 前缀替换成隧道 base（ADR 0035 决策 2：job-in 前、worker/AI 无感）。

    替换面 = step.text + step.argument（docString content / dataTable 各单元格）——URL 可能出现在任一处。
    前缀字符串级匹配（flag 值须与 feature 书写一致——`localhost` vs `127.0.0.1` 不互认，文档写明）。
    frozen dataclass 逐层重建，原 jobs 不变（definition 不可变惯例）。
    """
    def sub(s: str | None) -> str | None:
        return s.replace(origin, base) if s else s

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
