"""第二个 spike · Nova Act 引擎 —— 对标 Midscene 引擎（ADR 0010 苹果对苹果）。

用例（与 Midscene 同）：打开 wikipedia.org → 执行动作指令 ACTION（在搜索框输入 "OpenAI" 并提交搜索）→ 断言进入
OpenAI 词条页。ACTION 与 ASSERTION 两句与 Midscene 侧 engines/midscene/spikes/03-midscene-grounding.ts 逐字相同，
改一侧必须同步另一侧。
鉴权：纯 IAM，经 @workflow 装饰器（ADR 0004），不用 NOVA_ACT_API_KEY。
浏览器：AgentCore 云端（aws.browser.v1，ADR 0011），经 AgentCoreBrowserSessionProvider.cdp_session()。
断言：
  A 确定性：nova.page.url 含 /wiki/OpenAI（底层 Playwright，可复现）
  B AI 断言：nova.act_get(ASSERTION, BOOL_SCHEMA) 执行 N=10 次测抖动；与生产 worker 的 AI 断言投票用同一个 API（ADR 0014）。
    Midscene 侧用 aiBoolean(ASSERTION)：两者都是问是非、取布尔值、判否不抛错，调用形式不同、断言句相同
    （两者的对应关系见 ADR 0010 洞察 ③）。调用本身出错或返回不合 schema 按判否计。
度量（两侧共有的度量键名与口径一致；本引擎另多两项计费时长 actTimeWorkedS / avgTimeWorkedS）：
  actOk / actMs：动作是否成功、动作耗时。actMs 只包住 nova.act 调用本身（含 SDK 在调用内部的等待）。
  loadWaitMs：动作之后等页面到 domcontentloaded 的耗时，单独一列，不并入 actMs。
  actTokens：动作的 token 用量，本引擎恒为 null（SDK 不暴露，证据见下）。
  actTimeWorkedS：动作的计费时长，取 ActResult.metadata.time_worked_s（Nova 按 agent 工作时长计费，ADR 0024「成本信封」）。
  assertA_deterministic：A 的结论与当时的 url。
  assertB_ai：B 的通过次数、抖动率、与 A 是否一致、每次平均耗时 avgMs、每次平均 token 用量 avgTokens（恒为 null）、
    每次平均计费时长 avgTimeWorkedS。
token 用量 SDK 不暴露（nova-act 3.4.x 查证）：act / act_get 返回的 ActResult 与 ActGetResult 只带 metadata
（ActMetadata 的字段是 session_id、act_id、num_steps_executed、start_time、end_time、prompt、step_server_times_s、
time_worked_s、human_wait_time_s、trajectory_file_path）；每一步的服务响应模型 InvokeActStepResponse 只有 calls 与
step_id；trajectory 的 TrajectoryMetadata 同样没有 token 字段；botocore 自带的 nova-act 服务模型里 InvokeActStep
的输出也只定义了 calls 与 stepId，整份服务模型没有任何用量字段。故汇总表的 token 两行标「SDK 不暴露」，
成本只能用 time_worked_s 表示。
输出：先打印 metrics 的 JSON，再打印一张汇总表；表的行名两侧一致，可以直接并排填进 ADR 0010 的对标表。

运行（从 repo 根，worker 包已在根 venv 里）：AWS_REGION=us-east-1 uv run python engines/novaact/spikes/wikipedia_benchmark.py
"""
from __future__ import annotations

import json
import time

from nova_act import (
    NovaAct,
    AgentCoreBrowserSessionProvider,
    BOOL_SCHEMA,
    workflow,
)

from gherkai_worker_novaact.lib.workflow_setup import ensure_workflow_definition
from gherkai_worker_novaact.lib.constants import MODEL_ID, WORKFLOW_DEF  # 共享常量（与生产 worker 共用单一真理源）

REGION = "us-east-1"
N_FLAKE = 10
# 动作指令与断言句：与 Midscene 侧 03-midscene-grounding.ts 的 ACTION / ASSERTION 逐字相同（ADR 0010「同一用例」）。
ACTION = 'type "OpenAI" into the search input and submit the search'
ASSERTION = "the page is the Wikipedia article about OpenAI"
LOAD_WAIT_TIMEOUT_MS = 60000
TOKENS_UNAVAILABLE = "SDK 不暴露"


def _time_worked_s(obj) -> float | None:
    """取 act / act_get 的返回值或其抛出的异常上 metadata.time_worked_s；没有则返回 None。

    失败的 act 同样已计费，SDK 的异常对象也带 metadata（ADR 0024「失败/超时的 act 同样带 cost」）。
    """
    md = getattr(obj, "metadata", None)
    return getattr(md, "time_worked_s", None) if md is not None else None


def _fmt_seconds(s: float | None) -> str:
    return f"{s:.1f} s" if s is not None else "SDK 未返回"


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
            # === 动作：执行 ACTION。计时只包住 nova.act 本身 ===
            act_ok = False
            act_out = None  # ActResult，或 act 抛出的异常：两者都可能带 metadata.time_worked_s
            t_act = time.monotonic()
            try:
                act_out = nova.act(ACTION)
                act_ok = True
            except Exception as e:  # noqa: BLE001
                act_out = e
                metrics["actError"] = str(e)
            act_ms = int((time.monotonic() - t_act) * 1000)
            act_tw = _time_worked_s(act_out)
            metrics["actOk"] = act_ok
            metrics["actMs"] = act_ms
            metrics["actTokens"] = None  # SDK 不暴露，见模块头
            metrics["actTimeWorkedS"] = act_tw

            # === 页面加载等待：单独计时，不并入 actMs ===
            t_load = time.monotonic()
            try:
                nova.page.wait_for_load_state("domcontentloaded", timeout=LOAD_WAIT_TIMEOUT_MS)
            except Exception:  # noqa: BLE001
                pass
            load_wait_ms = int((time.monotonic() - t_load) * 1000)
            metrics["loadWaitMs"] = load_wait_ms
            url_after = nova.page.url
            metrics["urlAfterAct"] = url_after

            # === A：确定性断言（Playwright url）===
            a_pass = "/wiki/OpenAI" in url_after
            metrics["assertA_deterministic"] = {"pass": a_pass, "url": url_after}

            # === B：AI 断言，N 次抖动 ===
            b_results: list[bool] = []
            b_ms: list[int] = []
            b_tw: list[float] = []
            for i in range(N_FLAKE):
                out = None
                t = time.monotonic()
                try:
                    out = nova.act_get(ASSERTION, BOOL_SCHEMA)
                    val = bool(out.parsed_response) if out.matches_schema else False
                except Exception as e:  # noqa: BLE001
                    out = e
                    val = False
                b_ms.append(int((time.monotonic() - t) * 1000))
                b_results.append(val)
                tw = _time_worked_s(out)
                if tw is not None:
                    b_tw.append(tw)
                print(f"  B[{i+1}/{N_FLAKE}]={'pass' if b_results[i] else 'FAIL'}", end="  ", flush=True)

            b_pass = sum(b_results)
            flake_rate = (N_FLAKE - b_pass) / N_FLAKE
            consistent = all(r == a_pass for r in b_results)
            b_avg_ms = sum(b_ms) // len(b_ms)
            b_avg_tw = round(sum(b_tw) / len(b_tw), 2) if b_tw else None
            metrics["assertB_ai"] = {
                "runs": N_FLAKE,
                "passCount": b_pass,
                "flakeRate": flake_rate,
                "consistentWithA": consistent,
                "avgMs": b_avg_ms,
                "avgTokens": None,  # SDK 不暴露，见模块头
                "avgTimeWorkedS": b_avg_tw,
            }

            print("\n\n[NA] ===== 对标基准（Nova Act 引擎）=====")
            print(json.dumps(metrics, indent=2, ensure_ascii=False))

            # 汇总表：行名与 Midscene 侧 03-midscene-grounding.ts 的汇总表逐行一致
            rows = [
                ("动作成功", "是" if act_ok else "否"),
                ("动作耗时（只计引擎 act 调用）", f"{act_ms} ms"),
                ("页面加载等待（动作之后，单独计时）", f"{load_wait_ms} ms"),
                ("动作 token（输入 / 输出）", TOKENS_UNAVAILABLE),
                ("动作计费时长 time_worked_s", _fmt_seconds(act_tw)),
                ("A 确定性断言（url 含 /wiki/OpenAI）", "pass" if a_pass else "FAIL"),
                (f"B AI 断言 ×{N_FLAKE}", f"{b_pass}/{N_FLAKE}，抖动 {round(flake_rate * 100)}%"),
                ("A/B 一致", "是" if consistent else "否"),
                ("B 平均耗时/次", f"{b_avg_ms} ms"),
                ("B 平均 token/次（输入 / 输出）", TOKENS_UNAVAILABLE),
                ("B 平均计费时长/次 time_worked_s", _fmt_seconds(b_avg_tw)),
            ]
            print(f"\n[NA] ===== 汇总表（Nova Act {MODEL_ID}）=====")
            print("| 度量 | Nova Act |\n|---|---|")
            for k, v in rows:
                print(f"| {k} | {v} |")

            print("[NA] PASS — 合体全通" if (act_ok and a_pass) else "[NA] PARTIAL — 见 metrics")


if __name__ == "__main__":
    # 端到端闭环：首次自动建 workflow definition，之后探测到即跳过（无需手动 CLI）
    print("[NA] ensure workflow definition ->", ensure_workflow_definition(WORKFLOW_DEF, region=REGION))
    run()
