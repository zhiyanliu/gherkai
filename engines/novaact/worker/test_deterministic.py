"""确定性注册表单测（ADR 0022）——纯单元，不连 AWS、不起浏览器。

跑：cd engines/novaact && .venv/bin/python -m pytest worker/test_deterministic.py -q
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))  # 便于 import deterministic
import deterministic as d


@pytest.fixture(autouse=True)
def _isolate():
    d.clear()
    yield
    d.clear()


def test_register_and_match_with_named_groups():
    seen = []
    d.deterministic(r'页面地址匹配 "(?P<pattern>.+)"')(lambda ctx, pattern: seen.append(pattern))
    hit = d.match('页面地址匹配 "/wiki/OpenAI"')
    assert hit is not None
    handler, groups = hit
    assert groups == {"pattern": "/wiki/OpenAI"}


def test_miss_returns_none():
    d.deterministic(r'页面地址匹配 "(?P<pattern>.+)"')(lambda ctx, pattern: None)
    assert d.match("搜索 OpenAI") is None


def test_multiple_hits_raises_conflict():
    d.deterministic(r"地址(?P<a>.+)")(lambda ctx, a: None)
    d.deterministic(r"(?P<b>地址.+)")(lambda ctx, b: None)
    with pytest.raises(d.DeterministicConflict):
        d.match("地址匹配 x")


def test_handler_assertion_propagates():
    @d.deterministic(r"必假")
    def _h(ctx):
        raise AssertionError("故意失败")

    hit = d.match("必假")
    assert hit is not None
    handler, groups = hit
    with pytest.raises(AssertionError, match="故意失败"):
        handler(object(), **groups)


def test_no_named_groups_empty_dict():
    d.deterministic(r"固定文本")(lambda ctx: None)
    hit = d.match("固定文本")
    assert hit is not None
    _, groups = hit
    assert groups == {}
