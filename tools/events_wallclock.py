#!/usr/bin/env python
"""events 表单 act 墙钟分析（Fargate grace 校准数据前置，ADR 0032 / 0024「DynamoDB 作 events-out」）。

**为何存在**：Nova grace 下限 = `NOVA_ACT_TIMEOUT_S` + `NOVA_GRACE_MARGIN_S`（见 runtime/gherkai_runtime/compose.py），
margin 的取值需实测「单 act 正常墙钟」与「act 中途中断退出耗时」来标定（是否过保守）。答它需要**单 act 墙钟分布**的实测——而
events 表的每条 item 恰好带 `expires_at`（worker emit 时写 `int(time.time())+7d`，见 engines/*/lib/event_sink），
减去 7d TTL 常量即还原 **worker emit 的 epoch 秒**（1s 分辨率、跨机一致、不受 core 侧 0.5s 轮询 + DDB 最终
一致抖动污染——不像 `RunResult.StepResult.duration_ms` 含轮询噪声）。

**单 act 墙钟** = 同一 scope（pk）内、同一 (scenario_id, step_index) 的 `step_done.emit - step_started.emit`。
**硬约束**：`--assertion-votes 1` 才能拆出单 act——votes>1 时 worker 把 N 次 act 合进一个 step_done（见
run_scope.py 的 tw_total 累加），墙钟会是 N 个 act 之和、拆不出单 act。测单 act 墙钟时务必 votes=1。

**1s 分辨率的坑**：emit epoch 只到秒。act 耗时 <1s 或跨秒边界会显示 0s/1s——本脚本对 wall≤1s 打
`coarse` 标记（勿把 0s 误读成「act 瞬时完成」）。真实 act（连模型）通常数秒~数十秒。

用法（需 AWS 凭证）：
  uv run python tools/events_wallclock.py \\
      --events-table gherkai-events --run-id <run_id> [--region us-east-1] [--json]

  --run-id：Scan events 表、按 `begins_with(pk, "<run_id>#")` 圈出本 run 所有 scope（test 表低量、Scan 可接受）。
  --pk：或直接给完整 pk（run_id#scope_id）Query 单 scope（精确、免 Scan）。
  --json：吐机读 JSON（默认吐人读表格 + 分位数摘要）。

输出：每 act 一行（scope / scenario / step / wall_s / time_worked_s / seq 区间 / 标记），末尾 wall_s 的
min/p50/p90/p99/max 摘要——直接回答「grace margin 是否过保守」（对照 NOVA_ACT_TIMEOUT_S，默认 120）。
"""
from __future__ import annotations

import argparse
import json
import sys

# events 表 TTL 常量：emit_epoch = expires_at - 此值。须与**两端 worker**（写端）TTL 常量一致（各引擎符号名不同）：
# Nova = engines/novaact/gherkai_worker_novaact/lib/event_sink.py 的 `_EVENTS_TTL_S`；Midscene = engines/midscene/src/lib/event-sink.mts 的
# `EVENTS_TTL_S`（无前导下划线）。另一个读端同样反解：core/gherkai_core/adapters/event_log/ddb.py 的 `_EVENTS_TTL_S`
# （`_emit_ts`）。四端各自硬编码 7d、语义契约对齐（ADR 0033/0024）；此处复刻、改动须同步全部解码方。
_EVENTS_TTL_S = 7 * 24 * 60 * 60

_PK_ATTR = "pk"
_SK_ATTR = "seq"
_BODY_ATTR = "body"
_TTL_ATTR = "expires_at"


def _table(events_table: str, region: str | None):
    import boto3

    return boto3.resource("dynamodb", region_name=region).Table(events_table)


def _scan_by_run_id(table, run_id: str) -> list[dict]:
    """Scan + FilterExpression begins_with(pk, "<run_id>#") 圈本 run 全 scope 的 items（test 表低量可接受）。"""
    from boto3.dynamodb.conditions import Attr

    items, kwargs = [], {"FilterExpression": Attr(_PK_ATTR).begins_with(f"{run_id}#")}
    while True:
        resp = table.scan(**kwargs)
        items.extend(resp.get("Items", []))
        last = resp.get("LastEvaluatedKey")
        if not last:
            return items
        kwargs["ExclusiveStartKey"] = last


def _query_by_pk(table, pk: str) -> list[dict]:
    """Query 单 scope（PK=pk），强一致读全事件（免最终一致漏读；分析是事后一次性、成本忽略）。"""
    from boto3.dynamodb.conditions import Key

    items, kwargs = [], {
        "KeyConditionExpression": Key(_PK_ATTR).eq(pk),
        "ScanIndexForward": True,
        "ConsistentRead": True,
    }
    while True:
        resp = table.query(**kwargs)
        items.extend(resp.get("Items", []))
        last = resp.get("LastEvaluatedKey")
        if not last:
            return items
        kwargs["ExclusiveStartKey"] = last


def _emit_epoch(item: dict) -> int | None:
    """从 item 的 expires_at 还原 worker emit epoch 秒（= expires_at - 7d）。缺 expires_at（老数据/异常）→ None。"""
    raw = item.get(_TTL_ATTR)
    if raw is None:
        return None
    return int(raw) - _EVENTS_TTL_S


def _acts_from_scope(pk: str, items: list[dict]) -> list[dict]:
    """一个 scope（pk）的 items → 单 act 墙钟列表。

    按 seq 升序，配对同 (scenario_id, step_index) 的 step_started→step_done。用 dict 暂存已见 step_started 的
    emit epoch（防交错——理论上 scope 内串行、step_started 紧邻 step_done，但配对不假设相邻、按 key 精确匹配）。
    """
    ordered = sorted(items, key=lambda it: int(it[_SK_ATTR]))
    pending: dict[tuple, tuple[int, int | None]] = {}  # (scenario_id, step_index) -> (seq, emit_epoch)
    acts: list[dict] = []
    for it in ordered:
        try:
            ev = json.loads(it[_BODY_ATTR])
        except (ValueError, KeyError):
            continue
        et = ev.get("type")
        if et not in ("step_started", "step_done"):
            continue
        key = (ev.get("scenarioId"), ev.get("stepIndex"))
        seq = int(it[_SK_ATTR])
        emit = _emit_epoch(it)
        if et == "step_started":
            pending[key] = (seq, emit)
        else:  # step_done
            start = pending.pop(key, None)
            if start is None:
                continue  # 无配对 step_started（中断/丢事件）——跳过，不误算
            start_seq, start_emit = start
            wall = None if (start_emit is None or emit is None) else (emit - start_emit)
            # step_done 的 cost.time_worked_s（Nova SDK 原生量，对照墙钟——含 SDK 内部时间 vs 端到端墙钟差）
            cost = ev.get("cost") or {}
            # votes.total（AI 断言投票次数；step_done 的 votes 字段，见 core/gherkai_core/wire.py 与 Nova worker _run_step
            # 的投票循环）：**硬约束检测**——votes>1 时 worker 把 N 次 act 合进一对 step_started/step_done
            # （emit 在 N 票循环之后），此时 wall 是 N 个 act 之和、**不是单 act**。
            # 单 act 墙钟标定要求 --assertion-votes 1；votes 缺省(动作 step 无投票)或 =1 才是干净单 act。打 multi_act
            # 标记，供 _summary/_print_human 把这些排除出分位数 + 醒目告警（否则 p99 被膨胀、误判 grace 过保守）。
            votes = ev.get("votes") or {}
            votes_total = votes.get("total")
            multi_act = votes_total is not None and votes_total > 1
            acts.append({
                "pk": pk,
                "scenario_id": ev.get("scenarioId"),
                "step_index": ev.get("stepIndex"),
                "status": ev.get("status"),
                "seq_started": start_seq,
                "seq_done": seq,
                "wall_s": wall,
                "time_worked_s": cost.get("time_worked_s"),
                "votes_total": votes_total,
                # 1s 分辨率坑：wall≤1 打 coarse（勿把 0s 误读成瞬时；见本文件 docstring「1s 分辨率的坑」）
                "coarse": wall is not None and wall <= 1,
                # votes>1：wall 是 N 个 act 合计、非单 act——排除出分位数 + 告警（硬约束违反）
                "multi_act": multi_act,
            })
    return acts


def _percentile(sorted_vals: list[float], q: float) -> float:
    """线性插值分位数（q∈[0,1]）。sorted_vals 非空、已升序。"""
    if len(sorted_vals) == 1:
        return sorted_vals[0]
    pos = q * (len(sorted_vals) - 1)
    lo = int(pos)
    frac = pos - lo
    if lo + 1 >= len(sorted_vals):
        return sorted_vals[-1]
    return sorted_vals[lo] + frac * (sorted_vals[lo + 1] - sorted_vals[lo])


def _summary(acts: list[dict]) -> dict | None:
    n_multi = sum(1 for a in acts if a.get("multi_act"))
    # **只对干净单 act 算分布**（排除 votes>1 的 N-act 合计墙钟——否则 p99 被膨胀、误判 grace 过保守）。
    walls = sorted(a["wall_s"] for a in acts if a["wall_s"] is not None and not a.get("multi_act"))
    if not walls:
        # 全被 multi_act 排除（或无有效墙钟）：仍返回 n_multi_act 让上层告警，不静默给空。
        return {"n_acts": 0, "n_multi_act": n_multi} if n_multi else None
    return {
        "n_acts": len(walls),
        "min": walls[0], "p50": round(_percentile(walls, 0.5), 1),
        "p90": round(_percentile(walls, 0.9), 1), "p99": round(_percentile(walls, 0.99), 1),
        "max": walls[-1],
        "n_coarse_le_1s": sum(1 for a in acts if a.get("coarse") and not a.get("multi_act")),
        "n_multi_act": n_multi,  # votes>1 被排除的 act 数（>0 即违反 --assertion-votes 1 硬约束）
    }


def analyze(events_table: str, run_id: str | None, pk: str | None, region: str | None) -> dict:
    table = _table(events_table, region)
    if pk is not None:
        by_pk = {pk: _query_by_pk(table, pk)}
    else:
        items = _scan_by_run_id(table, run_id)
        by_pk: dict[str, list[dict]] = {}
        for it in items:
            by_pk.setdefault(it[_PK_ATTR], []).append(it)
    acts: list[dict] = []
    for scope_pk, scope_items in sorted(by_pk.items()):
        acts.extend(_acts_from_scope(scope_pk, scope_items))
    return {
        "events_table": events_table, "run_id": run_id, "pk": pk,
        "n_scopes": len(by_pk), "acts": acts, "summary": _summary(acts),
    }


def _print_human(result: dict) -> None:
    acts = result["acts"]
    print(f"events_table={result['events_table']} run_id={result['run_id']} pk={result['pk']} "
          f"scopes={result['n_scopes']} acts={len(acts)}")
    if not acts:
        # 无任何配对：中断过早（没跑到 step_done）/ run_id 不匹配。**注意**：votes>1 不会导致 acts 为空——它仍产
        # 一对 step_started/step_done（只是墙钟含 N act），会被下面标 multi_act 排除出分布、而非在此消失。
        print("（无 step_started/step_done 配对——中断过早没跑到 step_done / run_id 不匹配？）")
        return
    print(f"{'scope':<40} {'scenario':<28} {'step':>4} {'status':<8} {'wall_s':>7} {'worked_s':>9} {'seq':>12}  flag")
    for a in acts:
        wall = "n/a" if a["wall_s"] is None else str(a["wall_s"])
        worked = "n/a" if a["time_worked_s"] is None else f"{a['time_worked_s']:.1f}"
        flags = []
        if a.get("multi_act"):
            flags.append(f"MULTI-ACT(votes={a.get('votes_total')})")
        if a.get("coarse"):
            flags.append("coarse≤1s")
        scope_short = a["pk"] if len(a["pk"]) <= 40 else "…" + a["pk"][-39:]
        scen = str(a["scenario_id"])
        scen_short = scen if len(scen) <= 28 else "…" + scen[-27:]
        print(f"{scope_short:<40} {scen_short:<28} {a['step_index']!s:>4} {a['status'] or '':<8} "
              f"{wall:>7} {worked:>9} {a['seq_started']}-{a['seq_done']:<5}  {' '.join(flags)}")
    s = result["summary"]
    n_multi = (s or {}).get("n_multi_act", 0)
    if n_multi:
        # 硬约束违反告警（醒目）：votes>1 的 act 墙钟是 N 票合计、非单 act，已排除出分布——否则 p99 被膨胀。
        print(f"\n⚠️  {n_multi} 个 act 带 votes>1（MULTI-ACT）——其 wall_s 是 N 票（N 个 act）合计、非单 act，"
              f"已排除出下面分布。单 act 墙钟标定须 --assertion-votes 1 重跑（见 docstring 硬约束）。")
    if s and s.get("n_acts", 0) > 0:
        print(f"\n=== 单 act wall_s 分布（n={s['n_acts']}，coarse≤1s={s['n_coarse_le_1s']}"
              f"{f'，已排除 {n_multi} 个 MULTI-ACT' if n_multi else ''}）===")
        print(f"min={s['min']}  p50={s['p50']}  p90={s['p90']}  p99={s['p99']}  max={s['max']}")
        # 下面的 120 是本脚本自带的对照基线（缺省值副本），**真值住 runtime/gherkai_runtime/compose.py 的 NOVA_ACT_TIMEOUT_S**
        # （可经同名 env 覆盖）——用非缺省 act timeout 跑时，这里的判语只是参考，按真值重读分位数。
        print(f"对照 NOVA_ACT_TIMEOUT_S=120：p99={s['p99']}s → "
              f"{'单 act 远低于 act_timeout，grace margin 有压缩空间' if s['p99'] < 120 else '有 act 逼近/超 120，act_timeout 不宜降'}")
    elif n_multi:
        print("\n（无干净单 act 可算分布——全部 votes>1 被排除。--assertion-votes 1 重跑。）")


def main() -> None:
    ap = argparse.ArgumentParser(description="events 表单 act 墙钟分析（Fargate grace 校准，ADR 0032）")
    ap.add_argument("--events-table", required=True, help="events 表名（如 gherkai-events）")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--run-id", help="Scan 圈本 run 全 scope（test 表低量可接受）")
    g.add_argument("--pk", help="直接给完整 pk（run_id#scope_id）Query 单 scope（精确、免 Scan）")
    ap.add_argument("--region", default=None, help="AWS region（默认走 boto 默认链）")
    ap.add_argument("--json", action="store_true", help="吐机读 JSON（默认人读表格）")
    a = ap.parse_args()
    result = analyze(a.events_table, a.run_id, a.pk, a.region)
    if a.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    else:
        _print_human(result)
    # 无**可用单 act 样本**即非 0 退出（脚本编排可判）——不只是「无任何配对」：全 votes>1（MULTI-ACT 被排除出分布）
    # 时 acts 非空但 summary.n_acts=0、零干净样本，同属「拿不到单 act 墙钟」，须让编排感知（否则误判成功、拿空分布）。
    summary = result.get("summary") or {}
    if not result["acts"] or summary.get("n_acts", 0) == 0:
        sys.exit(2)


if __name__ == "__main__":
    main()
