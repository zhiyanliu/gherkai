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


# ---- botocore ClientError 按码/状态码细分（ADR 0028：AgentCore 起会话服务端瞬时故障）----
def _client_error(code=None, status=None):
    """造一个 botocore ClientError（response 里带 Error.Code / ResponseMetadata.HTTPStatusCode）。"""
    from botocore.exceptions import ClientError
    resp = {}
    if code is not None:
        resp["Error"] = {"Code": code, "Message": "x"}
    if status is not None:
        resp["ResponseMetadata"] = {"HTTPStatusCode": status}
    return ClientError(resp, "StartBrowserSession")


def test_client_error_throttling_is_transient():
    # 节流码 → 瞬时（AgentCore 起会话限流，可重试）
    assert rs._is_transient_network(_client_error(code="ThrottlingException")) is True
    assert rs._is_transient_network(_client_error(code="TooManyRequestsException")) is True
    assert rs._is_transient_network(_client_error(code="SlowDown")) is True


def test_client_error_5xx_status_is_transient():
    # 5xx 服务端错 → 瞬时（即便 Error.Code 缺失，凭 HTTPStatusCode 判）
    for st in (500, 502, 503, 504):
        assert rs._is_transient_network(_client_error(status=st)) is True, st


def test_client_error_transient_code_is_transient():
    assert rs._is_transient_network(_client_error(code="RequestTimeout")) is True


def test_client_error_validation_is_permanent():
    # 永久错（4xx 客户端错/配置错）→ 不重试，绝不当瞬时
    assert rs._is_transient_network(_client_error(code="ValidationException", status=400)) is False
    assert rs._is_transient_network(_client_error(code="AccessDeniedException", status=403)) is False


def test_connect_read_timeout_are_transient():
    # botocore ConnectTimeoutError/ReadTimeoutError（建连/读超时）→ 瞬时（本次新加白名单）
    from botocore.exceptions import ConnectTimeoutError, ReadTimeoutError
    assert rs._is_transient_network(ConnectTimeoutError(endpoint_url="https://x")) is True
    assert rs._is_transient_network(ReadTimeoutError(endpoint_url="https://x")) is True


def test_agentcore_startfailed_wrapping_chain_is_transient():
    # 真实场景（ADR 0028）：AgentCore 起会话失败，底层 boto ClientError(节流) 被 Nova SDK 包成
    # BrowserAuthError ← StartFailed（每层 from）。遍历异常链必须穿透两层包装命中底层 ClientError。
    boto_err = _client_error(code="ThrottlingException", status=429)
    browser_auth = RuntimeError("Failed to manage AgentCore browser session")  # 模拟 BrowserAuthError
    browser_auth.__cause__ = boto_err
    start_failed = RuntimeError("Failed to start")  # 模拟 StartFailed
    start_failed.__cause__ = browser_auth
    assert rs._is_transient_network(start_failed) is True


def test_agentcore_permanent_wrapping_chain_not_transient():
    # 反向护栏：底层是永久错（ValidationException），包两层后仍判永久（不误重试烧钱）
    boto_err = _client_error(code="ValidationException", status=400)
    browser_auth = RuntimeError("browser auth"); browser_auth.__cause__ = boto_err
    start_failed = RuntimeError("start failed"); start_failed.__cause__ = browser_auth
    assert rs._is_transient_network(start_failed) is False


# ---- Playwright TargetClosedError 按阶段判定（ADR 0028：CDP 连接被网络断的下游症状）----
# 真跑 r2 复现：会话已 start_browser_session 成功，with NovaAct.__enter__ 内 CDPSession.send 撞网络断，
# Playwright 抛 TargetClosedError（不继承 OSError、__cause__ 为 None，白名单无从穿透）→ 曾误判 engine_error。
def _target_closed():
    from playwright._impl._errors import TargetClosedError
    return TargetClosedError("CDPSession.send: Target page, context or browser has been closed")


def test_target_closed_transient_only_when_connecting():
    # 建连阶段（connecting=True）：认作瞬时 → 触发建连重试
    assert rs._is_transient_network(_target_closed(), connecting=True) is True


def test_target_closed_not_transient_by_default():
    # 默认（act 中途分类 _classify_act_error 走此路径）：不认——守「拿不准→不归 network」铁律，
    # 避免把会话正常关/浏览器真崩误判为可重试。
    assert rs._is_transient_network(_target_closed()) is False
    assert rs._is_transient_network(_target_closed(), connecting=False) is False


def test_target_closed_wrapped_chain_transient_when_connecting():
    # 真实包装链：TargetClosedError ← StartFailed ← BrowserAuthError（每层 from），建连阶段遍历链命中
    inner = _target_closed()
    start_failed = RuntimeError("Failed to start and initialize Playwright"); start_failed.__cause__ = inner
    browser_auth = RuntimeError("Failed to manage AgentCore browser session"); browser_auth.__cause__ = start_failed
    assert rs._is_transient_network(browser_auth, connecting=True) is True
    # 反向：同一条链在非建连阶段不认（TargetClosedError 语义模糊，只建连期安全）
    assert rs._is_transient_network(browser_auth, connecting=False) is False


def test_connecting_flag_does_not_widen_permanent_errors():
    # connecting=True 不是"放宽一切"：真永久错（ValidationException）即便建连阶段仍判永久
    assert rs._is_transient_network(_client_error(code="ValidationException"), connecting=True) is False
    # 普通 Playwright Error（非 TargetClosedError，如参数/协议错）建连阶段也不当瞬时（精确匹配 TargetClosedError）
    from playwright._impl._errors import Error as PWError
    assert rs._is_transient_network(PWError("some protocol error"), connecting=True) is False


def test_target_closed_by_name_fallback_hits_inside_chain(monkeypatch):
    """按名兜底（playwright 私有路径 import 失败时）也必须在**链内**命中——曾只查最外层 e,
    而真实故障链最外层是 BrowserAuthError,兜底形同虚设(私有路径挪位即误判 engine_error 不重试)。"""
    import builtins

    real_import = builtins.__import__

    def block_pw(name, *a, **kw):
        if name == "playwright._impl._errors":
            raise ImportError("模拟 SDK 版本挪位")
        return real_import(name, *a, **kw)

    monkeypatch.setattr(builtins, "__import__", block_pw)

    class TargetClosedError(Exception):  # 按名匹配的替身(真类 import 不到)
        pass

    inner = TargetClosedError("closed")
    start_failed = RuntimeError("StartFailed"); start_failed.__cause__ = inner
    outer = RuntimeError("BrowserAuthError"); outer.__cause__ = start_failed
    assert rs._is_transient_network(outer, connecting=True) is True  # 链内按名命中
    assert rs._is_transient_network(outer, connecting=False) is False  # 非建连期不认(铁律不变)
