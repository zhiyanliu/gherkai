"""Nova Act 侧 *通用 step*（v0.x：验证通用 step 跨两腿对称成立）。

加载与 Midscene 腿**同一份** features/wikipedia_generic.feature（ADR 0005：一份 .feature 双引擎）。
通用 step 对标 midscene/bdd/steps/generic.steps.ts：
  Given 打开 → go_to_url
  When AI 执行 → act
  Then AI 确认 → act_get(BOOL_SCHEMA) + 投票（对称布尔路径，ADR 0014）
  And 页面地址包含 → nova.page.url 确定性锚点（ADR 0015）
鉴权/会话复用 test_wikipedia.py 的纯 IAM @workflow 接线。

跑：cd novaact && AWS_REGION=us-east-1 .venv/bin/python -m pytest bdd/test_generic_steps.py -s
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from pytest_bdd import scenarios, given, when, then, parsers

from nova_act import NovaAct, AgentCoreBrowserSessionProvider, BOOL_SCHEMA, STRING_SCHEMA, Workflow
from nova_act.types.workflow import set_current_workflow, get_current_workflow

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # novaact/ 根，便于 import lib
from lib.workflow_setup import ensure_workflow_definition

REGION = os.environ.get("AWS_REGION", "us-east-1")
MODEL_ID = "nova-act-latest"
WORKFLOW_DEF = "spike-wikipedia-benchmark"
VOTES = 3  # AI 断言投票次数（治种类A抖动，ADR 0014）；取多数

# 与 Midscene 腿共享 features/ 下全部通用 step feature（一份份共享，ADR 0005）
FEATURES_DIR = Path(__file__).resolve().parents[2] / "features"
scenarios(str(FEATURES_DIR))


@pytest.fixture
def nova_ctx():
    ensure_workflow_definition(WORKFLOW_DEF, region=REGION, description="Nova Act generic-step v0.x")
    wf = Workflow(model_id=MODEL_ID, boto_session_kwargs={"region_name": REGION}, workflow_definition_name=WORKFLOW_DEF)
    with wf:
        outer = get_current_workflow()
        set_current_workflow(wf)  # provider.cdp_session() 靠 contextvar 识别鉴权（见 test_wikipedia.py）
        try:
            provider = AgentCoreBrowserSessionProvider(region=REGION)
            with provider.cdp_session() as (ws_url, headers):
                with NovaAct(
                    cdp_endpoint_url=ws_url,
                    cdp_headers=headers,
                    browser_auth=provider,
                    starting_page="about:blank",  # 实际起始页由通用 step「打开」决定
                ) as nova:
                    yield nova
        finally:
            set_current_workflow(outer)


# === 通用 step（任何用例复用，QA 不写代码）===

@given(parsers.parse('打开 "{url}"'))
def _open(nova_ctx, url):
    nova_ctx.go_to_url(url)


@when(parsers.parse('AI 执行 "{instruction}"'))
def _act(nova_ctx, instruction):
    nova_ctx.act(instruction)


@then(parsers.parse('AI 确认 "{claim}"'))
def _ai_confirm(nova_ctx, claim):
    # 对称布尔路径 + N 次投票取多数（ADR 0014）。
    # 与 Midscene aiBoolean(claim) 对齐：直接传 QA 原话，不污染——BOOL_SCHEMA 负责"返回布尔"，
    # 模型按 schema 判断该陈述真假（act_get docstring 示例即"原问句 + schema"）。
    votes = []
    for _ in range(VOTES):
        r = nova_ctx.act_get(claim, BOOL_SCHEMA)
        votes.append(bool(r.matches_schema and r.parsed_response))
    yes = sum(votes)
    assert yes > VOTES / 2, f"AI 断言未过多数票（{yes}/{VOTES}）：{claim}"


@then(parsers.parse('页面地址包含 "{fragment}"'))
def _url_contains(nova_ctx, fragment):
    # 确定性断言锚点（ADR 0015；不靠 AI）
    assert fragment in nova_ctx.page.url, f'url 应含 "{fragment}"，实际 {nova_ctx.page.url}'


# === 第一批打磨新增：断言类能力（对标 Midscene 的 aiBoolean/aiNumber/aiString）===

@then(parsers.parse('确认页面没有 "{text}" 的提示'))
def _absent(nova_ctx, text):
    # ⑤ 否定：问肯定句"是否存在"再取反（与 Midscene 侧同策略）
    votes = []
    for _ in range(VOTES):
        r = nova_ctx.act_get(f'页面上是否存在"{text}"这样的提示或文字？', BOOL_SCHEMA)
        votes.append(bool(r.matches_schema and r.parsed_response))
    present = sum(votes)
    assert present <= VOTES / 2, f'不该出现"{text}"，但多数票认为存在（{present}/{VOTES}）'


@then(parsers.parse('页面上展示的语言版本数量应该大于 "{n}"'))
def _count_gt(nova_ctx, n):
    # ① 提取数字：act_get + integer schema（对标 Midscene aiNumber）
    r = nova_ctx.act_get("页面上展示了多少种语言版本？返回数字", {"type": "integer"})
    assert r.matches_schema, "未取到整数"
    count = int(r.parsed_response)
    assert count > int(n), f"语言版本数应 > {n}，实际 {count}"


@then(parsers.parse('词条首段应该提到 "{kw}"'))
def _para_contains(nova_ctx, kw):
    # ① 提取字符串：act_get + string schema（对标 Midscene aiString）
    r = nova_ctx.act_get("返回词条第一段的文字内容", STRING_SCHEMA)
    assert r.matches_schema, "未取到字符串"
    para = str(r.parsed_response)
    assert kw.lower() in para.lower(), f'首段应含"{kw}"，实际："{para[:120]}…"'
