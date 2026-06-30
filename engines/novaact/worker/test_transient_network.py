"""_is_transient_network 单测（ADR 0028）：白名单瞬时识别 + 异常链遍历 + gaierror errno 细分。

重点护住 gaierror 的 errno 区分（EAI_AGAIN 临时 vs EAI_NONAME 永久）——这是与 Midscene
isTransientNetwork 对称的关键，易回归（曾一律把 gaierror 当永久，误判 DNS 临时抖动）。
"""
import socket
import ssl
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_scope as rs


# ---- 白名单具体瞬时类型 → True ----
def test_ssl_error_is_transient():
    assert rs._is_transient_network(ssl.SSLError("boom")) is True


def test_connection_error_is_transient():
    assert rs._is_transient_network(ConnectionError("reset")) is True


def test_timeout_is_transient():
    assert rs._is_transient_network(TimeoutError()) is True
    assert rs._is_transient_network(socket.timeout()) is True


# ---- 非网络 → False ----
def test_value_error_not_transient():
    assert rs._is_transient_network(ValueError("nope")) is False


# ---- gaierror errno 细分（核心护栏）----
def test_gaierror_eai_again_is_transient():
    # EAI_AGAIN = DNS 临时失败 → 瞬时（对齐 Midscene），可重试
    assert rs._is_transient_network(socket.gaierror(socket.EAI_AGAIN, "Temporary failure")) is True


def test_gaierror_eai_noname_is_permanent():
    # EAI_NONAME = DNS 永久（域名不存在，≈ENOTFOUND）→ 不重试
    assert rs._is_transient_network(socket.gaierror(socket.EAI_NONAME, "Name or service not known")) is False


def test_gaierror_no_args_is_permanent():
    # 无 errno 信息 → 保守当永久（不盲目重试）
    assert rs._is_transient_network(socket.gaierror()) is False


# ---- 异常链遍历：底层瞬时被外层包裹仍能识别 ----
def test_transient_in_cause_chain():
    outer = RuntimeError("wrapped by SDK")
    outer.__cause__ = ssl.SSLError("underlying")
    assert rs._is_transient_network(outer) is True


def test_eai_again_in_context_chain():
    outer = RuntimeError("wrapped")
    outer.__context__ = socket.gaierror(socket.EAI_AGAIN, "temp")
    assert rs._is_transient_network(outer) is True
