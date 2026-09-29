"""隧道凭据脱敏的规则单测（Nova worker 的那份实现，ADR 0035 决策 5）。

同一组用例在三份实现上各有一份：本文件、`core/tests/test_redact.py`、`engines/midscene/src/worker/redact.test.mts`。
本包零 core 依赖，所以用例表照抄而不 import；改规则时三处实现与三份用例一起改，输入与期望逐条一致。
"""
from __future__ import annotations

import json

import pytest

from gherkai_worker_novaact.lib.redact import MASK, redact_url_userinfo

# (输入, 期望)。三份用例表逐条相同。
CASES = [
    # 凭据内嵌的地址：userinfo 段换成 ***，主机与路径保留
    ("https://u1:p1@h.example/login", "https://***@h.example/login"),
    # 只有用户名（令牌形态）也算 userinfo
    ("https://token@h.example/", "https://***@h.example/"),
    # 没有 @ 的地址原样保留
    ("https://h.example/login", "https://h.example/login"),
    # @ 出现在路径或查询串里，不是 userinfo，不动
    ("https://h.example/users/@alice", "https://h.example/users/@alice"),
    ("https://h.example/?email=a@b.example", "https://h.example/?email=a@b.example"),
    # 一段文字里有多个地址：逐个处理，端口与路径保留
    ("先开 https://u1:p1@a.example/ 再开 http://u2:p2@b.example:8080/x",
     "先开 https://***@a.example/ 再开 http://***@b.example:8080/x"),
    # 已知残余：缺少 scheme:// 的「用户:口令@主机」规则抓不到，保持原样
    ("u1:p1@h.example/login", "u1:p1@h.example/login"),
    # 普通邮箱地址不受影响
    ("联系 alice@example.com", "联系 alice@example.com"),
    # 中文叙述里地址后紧跟全角标点再接邮箱：字符集不含中文与全角标点，不会一路吞到邮箱的 @
    ("打开https://example.com，用admin@corp.com登录", "打开https://example.com，用admin@corp.com登录"),
    # 已知残余：纯 ASCII 逗号把地址与邮箱连写，逗号是合法 userinfo 字符，会误吞到邮箱的 @
    ("https://a.example,x@b.example", "https://***@b.example"),
    ("", ""),
]


@pytest.mark.parametrize(("text", "expected"), CASES)
def test_redact_url_userinfo_cases(text, expected):
    assert redact_url_userinfo(text) == expected


def test_mask_is_three_stars_before_at():
    assert MASK == "***@"


def test_none_passes_through():
    assert redact_url_userinfo(None) is None


def test_serialized_json_line_stays_valid_and_loses_credentials():
    """规则直接作用在已序列化的整行上：结果仍能解析，字段值里的凭据被换掉。"""
    line = json.dumps({"type": "step_done", "message": "页面停在 https://u1:p1@h.example/x 未跳转"},
                      ensure_ascii=False)
    out = redact_url_userinfo(line)
    assert out is not None and "u1:p1@" not in out
    assert json.loads(out) == {"type": "step_done", "message": "页面停在 https://***@h.example/x 未跳转"}


def test_json_field_boundary_is_not_crossed():
    """前一个字段的地址不带 @、后一个字段里有 @：匹配停在引号处，不跨字段吞掉内容。"""
    line = '{"url":"https://h.example","who":"x@y"}'
    assert redact_url_userinfo(line) == line
