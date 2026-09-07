"""ensure_workflow_definition 单测（ADR 0004 create-if-not-exists）：串行 + **并发**档都幂等。

mock boto3 client（不连真 AWS）。护 ADR 0004/0028 的幂等断言：
- 已存在 → 'exists' 且不 create；不存在 → create → 'created'（description 只在给了时进 kwargs）。
- **并发赢家已建**（create 吃 ConflictException 409）→ 归 'exists'、不抛：worker 每 scope 一个进程，
  首跑时多进程同时 get→404→create 是真实档；裸抛会在会话未起、退出码通道未走时 traceback exit 1，
  被 core 归 engine_error（既不重试也归错类）。
- 其它 create 错误照常抛（fail-loud，别把对 409 的宽容扩成吞一切）。
"""
import pytest

from gherkai_worker_novaact.lib import workflow_setup as ws


class _FakeNovaActClient:
    """nova-act client 替身：get 按 `exists` 决定是否 404，create 按 `create_error` 决定抛什么。"""

    class exceptions:  # noqa: N801 —— 模仿 boto3 client.exceptions 命名
        class ResourceNotFoundException(Exception):
            pass

        class ConflictException(Exception):
            pass

    def __init__(self, *, exists: bool, create_error: Exception | None = None) -> None:
        self._exists = exists
        self._create_error = create_error
        self.created_kwargs: list[dict] = []

    def get_workflow_definition(self, **kw):
        if not self._exists:
            raise self.exceptions.ResourceNotFoundException("Workflow definition not found")
        return {"name": kw["workflowDefinitionName"]}

    def create_workflow_definition(self, **kw):
        self.created_kwargs.append(kw)
        if self._create_error is not None:
            raise self._create_error
        return {"name": kw["name"]}


def _patch(monkeypatch, client: _FakeNovaActClient) -> None:
    monkeypatch.setattr(ws.boto3, "client", lambda *a, **kw: client)


def test_exists_short_circuits_without_create(monkeypatch):
    c = _FakeNovaActClient(exists=True)
    _patch(monkeypatch, c)
    assert ws.ensure_workflow_definition("wf") == "exists"
    assert c.created_kwargs == []


def test_missing_definition_is_created(monkeypatch):
    c = _FakeNovaActClient(exists=False)
    _patch(monkeypatch, c)
    assert ws.ensure_workflow_definition("wf", description="d") == "created"
    assert c.created_kwargs == [{"name": "wf", "description": "d"}]


def test_create_omits_description_when_absent(monkeypatch):
    c = _FakeNovaActClient(exists=False)
    _patch(monkeypatch, c)
    assert ws.ensure_workflow_definition("wf") == "created"
    assert c.created_kwargs == [{"name": "wf"}]


def test_concurrent_create_conflict_counts_as_exists(monkeypatch):
    """并发赢家已建（409）→ 'exists' 且不抛，使 create-if-not-exists 的幂等在并发下也成立（ADR 0004）。"""
    err = _FakeNovaActClient.exceptions.ConflictException("already exists")
    c = _FakeNovaActClient(exists=False, create_error=err)
    _patch(monkeypatch, c)
    assert ws.ensure_workflow_definition("wf") == "exists"
    assert len(c.created_kwargs) == 1  # 真尝试过 create（不是靠先探测绕过——并发窗口就在探测之后）


def test_other_create_error_propagates(monkeypatch):
    """只对 409 宽容；配额/校验/权限类错误照常抛（否则会静默跑到 CreateWorkflowRun 才 404，ADR 0004）。"""
    c = _FakeNovaActClient(exists=False, create_error=RuntimeError("ServiceQuotaExceeded"))
    _patch(monkeypatch, c)
    with pytest.raises(RuntimeError):
        ws.ensure_workflow_definition("wf")
