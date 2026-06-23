"""Nova Act 侧 step definitions（pytest-bdd + Python）。

加载根级共享 features/wikipedia_search.feature —— 与 Midscene 侧 cucumber-js 同一份文件（ADR 0005）。
接线复用 spike（wikipedia_benchmark.py）验证过的：纯 IAM @workflow + AgentCore 云端浏览器。

跑：cd novaact && AWS_REGION=us-east-1 .venv/bin/python -m pytest bdd/test_wikipedia.py -s
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest
from pytest_bdd import scenarios, given, when, then, parsers

from nova_act import NovaAct, AgentCoreBrowserSessionProvider, BOOL_SCHEMA, Workflow
from nova_act.types.workflow import set_current_workflow, get_current_workflow

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # novaact/ 根，便于 import lib
from lib.workflow_setup import ensure_workflow_definition

REGION = os.environ.get("AWS_REGION", "us-east-1")
MODEL_ID = "nova-act-latest"
WORKFLOW_DEF = "spike-wikipedia-benchmark"  # create-if-not-exists，见 ADR 0004

# 指向 git 根的共享 feature（本文件在 novaact/bdd/，故 ../../features）
FEATURE = Path(__file__).resolve().parents[2] / "features" / "wikipedia_search.feature"
scenarios(str(FEATURE))


@pytest.fixture
def nova_ctx():
    """每个 scenario 一套：Workflow（纯 IAM）+ AgentCore 云端浏览器 + NovaAct。"""
    # 端到端闭环：首次自动建 workflow definition，之后探测到即跳过（无需手动 CLI）
    ensure_workflow_definition(WORKFLOW_DEF, region=REGION, description="Nova Act BDD wikipedia benchmark")
    wf = Workflow(
        model_id=MODEL_ID,
        boto_session_kwargs={"region_name": REGION},
        workflow_definition_name=WORKFLOW_DEF,
    )
    with wf:
        # 关键：provider.cdp_session() 靠 contextvar get_current_workflow() 识别鉴权上下文，
        # 而 `with Workflow(...)` 的 __enter__ 不会 set_current_workflow（只有 @workflow 装饰器会）。
        # 故在此手动设置，模拟装饰器行为。
        outer = get_current_workflow()
        set_current_workflow(wf)
        try:
            provider = AgentCoreBrowserSessionProvider(region=REGION)
            with provider.cdp_session() as (ws_url, headers):
                with NovaAct(
                    cdp_endpoint_url=ws_url,
                    cdp_headers=headers,
                    browser_auth=provider,
                    starting_page="https://www.wikipedia.org/",
                ) as nova:
                    yield nova
        finally:
            set_current_workflow(outer)


@given("the Wikipedia home page is open")
def _home(nova_ctx):
    # NovaAct 已用 starting_page 打开 wikipedia.org
    assert "wikipedia.org" in nova_ctx.page.url


@when(parsers.parse('I search for "{term}" and open its article'))
def _search(nova_ctx, term):
    nova_ctx.act(f'search for "{term}" and open the {term} article')


@then(parsers.parse('the page is the Wikipedia article about "{term}"'))
def _assert_article(nova_ctx, term):
    # A 确定性断言（Playwright url）+ B AI 断言（act_get + BOOL_SCHEMA），与 spike/Midscene 对齐
    assert f"/wiki/{term}" in nova_ctx.page.url, f"url should contain /wiki/{term}, got {nova_ctx.page.url}"
    r = nova_ctx.act_get(f"Is this page the Wikipedia article about {term}?", BOOL_SCHEMA)
    assert r.matches_schema and bool(r.parsed_response), "AI assertion failed"
