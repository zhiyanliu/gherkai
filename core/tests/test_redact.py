"""凭据脱敏三条规则的单测（ADR 0035 决策 5；0051 决策 11）。

用例表只有一份：`engines/fixtures/redaction-cases.json`，本文件、`engines/novaact/tests/test_redact.py`、
`engines/midscene/src/worker/redact.test.mts` 三份实现各自读它、逐条断言——任何一份实现漏改规则即红。
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from gherkai_core.redact import MASK, SECRET_MASK, redact_deep, redact_secrets

CASES = [tuple(c) for c in json.loads((Path(__file__).resolve().parents[2] / "engines" / "fixtures" / "redaction-cases.json")
                                      .read_text(encoding="utf-8"))["cases"]]


@pytest.mark.parametrize(("text", "expected"), CASES)
def test_redact_secrets_cases(text, expected):
    assert redact_secrets(text) == expected


def test_fixture_covers_all_three_rules():
    """fixture 不是空集也不是只有规则 ①：三条规则各至少一例（删掉某条规则的实现时有用例能红）。"""
    inputs = [i for i, _ in CASES]
    assert any("://" in i and "@" in i for i in inputs)
    assert any("gherkai_tunnel_token=" in i for i in inputs) and any("X-Amz-Signature=" in i for i in inputs)
    assert any("/remote-endpoint/" in i for i in inputs)


def test_masks():
    assert MASK == "***@" and SECRET_MASK == "***"


def test_none_passes_through():
    assert redact_secrets(None) is None


def test_serialized_json_line_stays_valid_and_loses_credentials():
    """规则直接作用在已序列化的整行上：结果仍能解析，字段值里的凭据被换掉（三条规则的停止字符都含引号与反斜杠）。"""
    line = json.dumps({"type": "step_done", "message": "页面停在 https://u1:p1@h.example/x 未跳转",
                       "url": "https://h/.well-known/gherkai-tunnel-auth?gherkai_tunnel_token=abc",
                       "ep": "https://x.amazonaws.com/remote-endpoint/tok123/wd/hub"}, ensure_ascii=False)
    out = redact_secrets(line)
    assert out is not None and "u1:p1@" not in out and "=abc" not in out and "tok123" not in out
    assert json.loads(out) == {"type": "step_done", "message": "页面停在 https://***@h.example/x 未跳转",
                               "url": "https://h/.well-known/gherkai-tunnel-auth?gherkai_tunnel_token=***",
                               "ep": "https://x.amazonaws.com/remote-endpoint/***/wd/hub"}


def test_json_field_boundary_is_not_crossed():
    """前一个字段的地址不带 @、后一个字段里有 @：匹配停在引号处，不跨字段吞掉内容。"""
    line = '{"url":"https://h.example","who":"x@y"}'
    assert redact_secrets(line) == line


def test_redact_deep_recurses_values_and_leaves_keys_and_non_strings():
    cred = "https://u1:p1@h.example/"
    doc = {
        "text": f'打开 "{cred}login"',
        cred: "键里的地址不改",
        "nested": {"list": [cred, 3, None, True, 1.5], "tuple": (cred, 7)},
        "count": 2,
        "missing": None,
        "warmup": "https://h/.well-known/gherkai-tunnel-auth?gherkai_tunnel_token=abc",
    }
    out = redact_deep(doc)
    assert out == {
        "text": '打开 "https://***@h.example/login"',
        cred: "键里的地址不改",
        "nested": {"list": ["https://***@h.example/", 3, None, True, 1.5], "tuple": ("https://***@h.example/", 7)},
        "count": 2,
        "missing": None,
        "warmup": "https://h/.well-known/gherkai-tunnel-auth?gherkai_tunnel_token=***",
    }
    assert isinstance(out["nested"]["tuple"], tuple)       # 容器类型保持
    assert doc["text"] == f'打开 "{cred}login"'            # 返回新对象，入参不被就地改写


def test_redact_deep_scalars():
    assert redact_deep("https://u1:p1@h.example/") == "https://***@h.example/"
    assert redact_deep(None) is None
    assert redact_deep(42) == 42
