"""Nova Act 侧 *通用 step*（v0.x：验证通用 step 跨两腿对称成立）。

加载与 Midscene 腿**同一份** features/wikipedia_generic.feature（ADR 0005：一份 .feature 双引擎）。
通用 step 对标 midscene/bdd/steps/generic.steps.ts（措辞见 ADR 0020）：
  Given 打开 "url" → go_to_url
  When "{自然语言}" → act
  Then "{自然语言}" → act_get(BOOL_SCHEMA) + 投票（对称布尔路径，ADR 0014）
  确定性锚点见 deterministic_steps.py 脚手架（按需自建，不预置；ADR 0020）
鉴权/会话复用 test_wikipedia.py 的纯 IAM @workflow 接线。

跑：cd novaact && AWS_REGION=us-east-1 .venv/bin/python -m pytest bdd/test_generic_steps.py -s
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from pytest_bdd import scenarios, given, when, then, parsers

from nova_act import NovaAct, AgentCoreBrowserSessionProvider, BOOL_SCHEMA, Workflow
from nova_act.types.workflow import set_current_workflow, get_current_workflow

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # novaact/ 根，便于 import lib
from lib.workflow_setup import ensure_workflow_definition

# 引入确定性锚点脚手架（ADR 0020/0021）：import 使其内的 @then step 对本测试模块可见、被 pytest-bdd 收集。
# 这是 wiring 的**明确约定**——test engineer 在 deterministic_steps.py 加锚点后，无需再改这里即可生效。
sys.path.insert(0, str(Path(__file__).resolve().parent))  # bdd/ 入 path
import deterministic_steps  # noqa: F401,E402（仅为注册 step，不直接引用）

REGION = os.environ.get("AWS_REGION", "us-east-1")
MODEL_ID = "nova-act-latest"
WORKFLOW_DEF = "spike-wikipedia-benchmark"
VOTES = 3  # AI 断言投票次数（治种类A抖动，ADR 0014）；取多数

# 与 Midscene 腿共享 features/ 下全部通用 step feature（一份份共享，ADR 0005）
# 本文件在 engines/novaact/bdd/，上溯 3 级到仓库根：bdd → novaact → engines → 根，故 parents[3]
FEATURES_DIR = Path(__file__).resolve().parents[3] / "features"
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


# 默认 AI 动作（ADR 0020）：无关键词的 When "{自然语言}" → act。QA 写人话，不需路由关键词。
@when(parsers.parse('"{instruction}"'))
def _act(nova_ctx, instruction):
    nova_ctx.act(instruction)


# 默认 AI 判断（ADR 0020）：无关键词的 Then "{自然语言}" → AI 布尔判断 + N 次投票取多数。
# 与 Midscene 的 Then "{string}" 对齐；QA 写人话——含**否定**陈述（如"页面没有出现服务器错误"），
# AI 能直接判否定，无需专门的否定 step。
@then(parsers.parse('"{claim}"'))
def _ai_confirm(nova_ctx, claim):
    votes = []
    for _ in range(VOTES):
        r = nova_ctx.act_get(claim, BOOL_SCHEMA)
        votes.append(bool(r.matches_schema and r.parsed_response))
    yes = sum(votes)
    assert yes > VOTES / 2, f"AI 断言未过多数票（{yes}/{VOTES}）：{claim}"


# 注：① 确定性锚点（不走 AI 的精确 URL/DOM 查）见 deterministic_steps.py 脚手架（ADR 0020，按需自建）。
#     ② 不设「否定断言」「取数/取文本」「AI 确认/AI 执行」等带关键词的专用 step——
#        一律走无关键词的 When/Then "{人话}"（ADR 0020：QA 零预设、默认走 AI）。
