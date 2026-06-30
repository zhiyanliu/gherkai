"""step argument（DataTable/DocString）拼接单测（ADR 0024/0025）。

验证 _argument_text / _instruction：多行参数拼成附加文本接在 step 人话后喂 AI。
两腿（Nova/Midscene）须同一拼法——Midscene 侧对称测见 run-scope.ts 的 node:test。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # 便于 import run_scope
import run_scope as rs


# ---- dataTable → markdown 表格 ----
def test_datatable_to_markdown():
    arg = {"kind": "dataTable", "rows": [["字段", "值"], ["用户名", "alice"], ["邮箱", "a@t.com"]]}
    assert rs._argument_text(arg) == "| 字段 | 值 |\n| 用户名 | alice |\n| 邮箱 | a@t.com |"


def test_datatable_empty_rows():
    assert rs._argument_text({"kind": "dataTable", "rows": []}) == ""


# ---- docString → 原样多行 ----
def test_docstring_passthrough():
    arg = {"kind": "docString", "content": "第一行\n第二行"}
    assert rs._argument_text(arg) == "第一行\n第二行"


# ---- 无 argument / 未知 kind ----
def test_no_argument():
    assert rs._argument_text(None) == ""
    assert rs._argument_text({}) == ""
    assert rs._argument_text({"kind": "weird"}) == ""


# ---- _instruction：人话 + 参数拼接（去引号）----
def test_instruction_appends_argument():
    step = {"text": '"填写注册表单"', "argument": {"kind": "dataTable", "rows": [["字段", "值"], ["用户名", "alice"]]}}
    # 去外引号 + 换行接表格
    assert rs._instruction(step["text"], step) == "填写注册表单\n| 字段 | 值 |\n| 用户名 | alice |"


def test_instruction_no_argument_is_bare_unquoted():
    step = {"text": '"搜索 OpenAI"'}
    assert rs._instruction(step["text"], step) == "搜索 OpenAI"  # 无参数 → 仅去引号，行为不变


def test_instruction_docstring():
    step = {"text": "在反馈框填入以下内容", "argument": {"kind": "docString", "content": "很满意\n但要暗色模式"}}
    assert rs._instruction(step["text"], step) == "在反馈框填入以下内容\n很满意\n但要暗色模式"


# ---- 边界：cell 含 | / 换行（两腿同规则清洗，保表格结构）----
def test_cell_with_pipe_escaped():
    arg = {"kind": "dataTable", "rows": [["a|b", "c"]]}
    assert rs._argument_text(arg) == "| a\\|b | c |"  # | 转义，不破坏列结构


def test_cell_with_newline_flattened():
    arg = {"kind": "dataTable", "rows": [["第一行\n第二行", "x"]]}
    assert rs._argument_text(arg) == "| 第一行 第二行 | x |"  # 换行压空格，cell 仍占一格


# ---- 边界：unquote 只剥 ASCII 空白（BOM 不剥，与 Midscene 对称）----
def test_unquote_ascii_ws_only_keeps_bom():
    # 尾部 BOM(U+FEFF)：两腿都不剥 → 外引号不成对 → 原样（不会一腿剥一腿不剥造成分叉）
    assert rs._unquote('"login"﻿') == '"login"﻿'
    # 纯 ASCII 空白外包裹 → 正常剥 + 去引号
    assert rs._unquote('  "搜索"  ') == "搜索"
