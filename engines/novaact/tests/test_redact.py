"""凭据脱敏三条规则的单测（Nova worker 的那份实现，ADR 0035 决策 5；0051 决策 11）。

用例表只有一份：`engines/fixtures/redaction-cases.json`，与 core、Midscene 三份实现各自读它、逐条断言。本包零 core 依赖，故不 import core。
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from gherkai_worker_novaact.lib.redact import MASK, SECRET_MASK, redact_secrets

CASES = [tuple(c) for c in json.loads((Path(__file__).resolve().parents[2] / "fixtures" / "redaction-cases.json")
                                      .read_text(encoding="utf-8"))["cases"]]


@pytest.mark.parametrize(("text", "expected"), CASES)
def test_redact_secrets_cases(text, expected):
    assert redact_secrets(text) == expected


def test_masks():
    assert MASK == "***@" and SECRET_MASK == "***"


def test_none_passes_through():
    assert redact_secrets(None) is None


def test_serialized_json_line_stays_valid_and_loses_credentials():
    """规则直接作用在已序列化的整行上：结果仍能解析，字段值里的凭据被换掉。"""
    line = json.dumps({"type": "step_done", "message": "页面停在 https://u1:p1@h.example/x 未跳转",
                       "url": "https://h/.well-known/gherkai-tunnel-auth?gherkai_tunnel_token=abc"}, ensure_ascii=False)
    out = redact_secrets(line)
    assert out is not None and "u1:p1@" not in out and "=abc" not in out
    assert json.loads(out) == {"type": "step_done", "message": "页面停在 https://***@h.example/x 未跳转",
                               "url": "https://h/.well-known/gherkai-tunnel-auth?gherkai_tunnel_token=***"}


def test_json_field_boundary_is_not_crossed():
    """前一个字段的地址不带 @、后一个字段里有 @：匹配停在引号处，不跨字段吞掉内容。"""
    line = '{"url":"https://h.example","who":"x@y"}'
    assert redact_secrets(line) == line
