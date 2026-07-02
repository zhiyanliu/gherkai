"""第二根穿刺针 · Nova Act 引擎 —— 对标 Midscene 引擎（ADR 0010 苹果对苹果）。

用例（与 Midscene 同）：打开 wikipedia.org → 搜 "OpenAI" → 断言进入 OpenAI 词条页。
鉴权：纯 IAM，经 @workflow 装饰器（ADR 0004），不用 NOVA_ACT_API_KEY。
浏览器：AgentCore 云端（aws.browser.v1，ADR 0011），经 AgentCoreBrowserSessionProvider.cdp_session()。
断言：
  A 确定性：nova.page.url 含 /wiki/OpenAI（底层 Playwright，可复现）
  B AI 断言：nova.act("...", schema=BOOL_SCHEMA) 跑 N=10 次测抖动
度量：动作成功率、A/B 是否一致、B 的 10 次抖动率、各步耗时。

跑：cd novaact && AWS_REGION=us-east-1 .venv/bin/python spikes/wikipedia_benchmark.py
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from nova_act import (
    NovaAct,
    AgentCoreBrowserSessionProvider,
    BOOL_SCHEMA,
    workflow,
)

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # novaact/ 根，便于 import lib
from lib.workflow_setup import ensure_workflow_definition
from lib.constants import MODEL_ID, WORKFLOW_DEF  # 共享常量（与生产 worker 共用单一真理源）

REGION = "us-east-1"
N_FLAKE = 10


@workflow(
    model_id=MODEL_ID,
    boto_session_kwargs={"region_name": REGION},  # 纯 IAM 路径（ADR 0004）
    workflow_definition_name=WORKFLOW_DEF,
)
def run() -> None:
    metrics: dict = {"region": REGION, "model": MODEL_ID, "case": "wikipedia/OpenAI"}

    provider = AgentCoreBrowserSessionProvider(region=REGION)  # 系统默认 aws.browser.v1
    with provider.cdp_session() as (ws_url, headers):
        print(f"[NA] cdp ws={ws_url[:70]}...")
        with NovaAct(
            cdp_endpoint_url=ws_url,
            cdp_headers=headers,
            browser_auth=provider,
            starting_page="https://www.wikipedia.org/",
        ) as nova:
            # === 动作：搜 OpenAI 并进入词条 ===
            t_act = time.monotonic()
            act_ok = False
            try:
                nova.act('search for "OpenAI" and open the OpenAI article')
                act_ok = True
            except Exception as e:  # noqa: BLE001
                metrics["actError"] = str(e)
            metrics["actMs"] = int((time.monotonic() - t_act) * 1000)
            metrics["actOk"] = act_ok
            url_after = nova.page.url
            metrics["urlAfterAct"] = url_after

            # === A：确定性断言（Playwright url）===
            a_pass = "/wiki/OpenAI" in url_after
            metrics["assertA_deterministic"] = {"pass": a_pass, "url": url_after}

            # === B：AI 断言，N 次抖动 ===
            b_results: list[bool] = []
            b_ms: list[int] = []
            for i in range(N_FLAKE):
                t = time.monotonic()
                try:
                    r = nova.act_get(
                        "Is this page the Wikipedia article about OpenAI?",
                        BOOL_SCHEMA,
                    )
                    val = bool(r.parsed_response) if r.matches_schema else False
                    b_results.append(val)
                except Exception:  # noqa: BLE001
                    b_results.append(False)
                b_ms.append(int((time.monotonic() - t) * 1000))
                print(f"  B[{i+1}/{N_FLAKE}]={'pass' if b_results[i] else 'FAIL'}", end="  ", flush=True)

            b_pass = sum(b_results)
            metrics["assertB_ai"] = {
                "runs": N_FLAKE,
                "passCount": b_pass,
                "flakeRate": (N_FLAKE - b_pass) / N_FLAKE,
                "consistentWithA": all(r == a_pass for r in b_results),
                "avgMs": sum(b_ms) // len(b_ms),
            }

            print("\n\n[NA] ===== 对标基准（Nova Act 引擎）=====")
            print(json.dumps(metrics, indent=2, ensure_ascii=False))
            print("[NA] PASS — 合体全通" if (act_ok and a_pass) else "[NA] PARTIAL — 见 metrics")


if __name__ == "__main__":
    # 端到端闭环：首次自动建 workflow definition，之后探测到即跳过（无需手动 CLI）
    print("[NA] ensure workflow definition ->", ensure_workflow_definition(WORKFLOW_DEF, region=REGION))
    run()
