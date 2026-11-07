"""失败原因等多行文本的一行化规则（ADR 0042 决策一「一行化规则」）——Nova 侧两份实现对跨语言夹具逐条相等。

用例表只有一份：`engines/fixtures/one-line-text-cases.json`，Midscene 的唯一一份实现 `lib/error-text.mts`（oneLineError）的测试
同样读它、逐条断言。两侧逐字相同是要求：同一段异常文本在两个引擎上该得出同一行。
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from gherkai_worker_novaact.lib import tunnel_warmup
from gherkai_worker_novaact.run_scope import _error_text, _one_line

_FIXTURE = Path(__file__).resolve().parents[2] / "fixtures" / "one-line-text-cases.json"
CASES = json.loads(_FIXTURE.read_text(encoding="utf-8"))["cases"]


@pytest.mark.parametrize("impl", [_one_line, tunnel_warmup._one_line], ids=["run_scope", "tunnel_warmup"])
def test_one_line_matches_cross_language_fixture(impl):
    assert CASES
    for c in CASES:
        assert impl(c["input"], c["max"]) == c["expected"], (c["input"], c["max"])


def test_fixture_expected_values_survive_python_default_folding():
    """输出只有词间的单个空格：交给 Python 缺省的折叠与分行都不再变化（CLI 文本渲染的防御性折叠因此对它不起作用）。"""
    for c in CASES:
        assert " ".join(c["expected"].split()) == c["expected"], c["expected"]
        assert c["expected"].splitlines() == ([c["expected"]] if c["expected"] else [])


def test_default_caps():
    """封顶长度各处可以不同：失败原因 300、预热失败消息里的原因 200；一行化本身不随封顶变。"""
    assert _one_line("x" * 500) == "x" * 300
    assert tunnel_warmup._one_line("x" * 500) == "x" * 200
    assert tunnel_warmup._one_line(RuntimeError("boom\nCall log: ...")) == "boom"


def test_error_text_falls_back_to_str_when_message_is_blank_after_one_line():
    """`.message` 按同一规则压成一行后是空串（如只含 U+0085）时回落 str(e)——与 Midscene 对 errorMessage 的判空同一判据。"""
    class SdkError(Exception):
        def __init__(self, message: str):
            self.message = message
            super().__init__("可读的原因\n第二行")

    for blank in ("\x85", " \u2028\ufeff", "\x1f\n\u3000", ""):
        assert _error_text(SdkError(blank)) == "SdkError: 可读的原因", repr(blank)
    assert _error_text(SdkError("\x85真正的原因")) == "SdkError: 真正的原因"
