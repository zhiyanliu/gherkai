"""A · 负向用例（expect-failure 探针）：验证"该红能红"——Nova Act 引擎。

对标 midscene/spikes/05-negative-assertions.ts：故意造必假断言，
验证 act_get(各 schema) 在"不符"时给出 false / 不匹配的值（→ 上层会判失败），
并带一个对照正向（防"全假"假象）。一次性证伪探针。

跑（从 repo 根，worker 包已在根 venv 里）：AWS_REGION=us-east-1 uv run python engines/novaact/spikes/negative_assertions.py
"""
from __future__ import annotations

import sys

from nova_act import NovaAct, AgentCoreBrowserSessionProvider, BOOL_SCHEMA, STRING_SCHEMA, Workflow
from nova_act.types.workflow import set_current_workflow, get_current_workflow

from gherkai_worker_novaact.lib.workflow_setup import ensure_workflow_definition
from gherkai_worker_novaact.lib.constants import MODEL_ID, WORKFLOW_DEF  # 共享常量（与生产 worker 共用单一真理源）

REGION = "us-east-1"


def main() -> int:
    ensure_workflow_definition(WORKFLOW_DEF, region=REGION)
    wf = Workflow(model_id=MODEL_ID, boto_session_kwargs={"region_name": REGION}, workflow_definition_name=WORKFLOW_DEF)
    checks = []  # (name, expect_red, got_red, detail)
    with wf:
        outer = get_current_workflow()
        set_current_workflow(wf)
        try:
            provider = AgentCoreBrowserSessionProvider(region=REGION)
            with provider.cdp_session() as (ws_url, headers):
                with NovaAct(
                    cdp_endpoint_url=ws_url, cdp_headers=headers, browser_auth=provider,
                    starting_page="https://en.wikipedia.org/wiki/OpenAI",
                ) as nova:
                    # (a) 布尔必假：这页不是关于 Python
                    r = nova.act_get("当前页面是关于 Python 编程语言的维基词条", BOOL_SCHEMA)
                    v = bool(r.matches_schema and r.parsed_response)
                    checks.append(("act_get 布尔必假(说成Python)", True, v is False, f"got={v}（期望 False）"))

                    # (b) 取数必假：语言版本数不可能 > 9999
                    r = nova.act_get("页面顶部展示了多少种语言版本？返回数字", {"type": "integer"})
                    cnt = int(r.parsed_response) if r.matches_schema else -1
                    checks.append(("act_get 取数必假(>9999)", True, not (cnt > 9999), f"count={cnt}, >9999={cnt > 9999}（期望 False）"))

                    # (c) 取串必假：首段不含杜撰词
                    r = nova.act_get("返回词条第一段的文字内容", STRING_SCHEMA)
                    para = str(r.parsed_response) if r.matches_schema else ""
                    has = "zzqx-not-a-real-word" in para.lower()
                    checks.append(("act_get 取串必假(含杜撰词)", True, not has, f"包含杜撰词={has}（期望 False）"))

                    # (d) 对照必真：确实是 OpenAI 页
                    r = nova.act_get("当前页面是关于 OpenAI 的维基词条", BOOL_SCHEMA)
                    v = bool(r.matches_schema and r.parsed_response)
                    checks.append(("act_get 布尔必真(对照)", False, v is False, f"got={v}（期望 True）"))
        finally:
            set_current_workflow(outer)

    print("\n[neg] ===== 负向断言验证（Nova Act）=====")
    all_good = True
    for name, expect_red, got_red, detail in checks:
        ok = got_red == expect_red
        all_good = all_good and ok
        print(f"  {'✅' if ok else '❌'} {name}: {detail}  {'' if ok else '←判定与预期不符!'}")
    print("\n[neg] PASS — 该红的都红、对照绿正常：AI 断言判定可信（此组用例上）"
          if all_good else "\n[neg] FAIL — 有断言判定与预期不符，AI 断言可信度存疑")
    return 0 if all_good else 1


if __name__ == "__main__":
    sys.exit(main())
