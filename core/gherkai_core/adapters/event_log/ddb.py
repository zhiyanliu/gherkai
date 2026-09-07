"""DdbEventLog（ADR 0034 cloud 侧）：cloud 无状态跑批的 EventLog——从 DDB events 表读全量重放 + 写 task_exited。

cloud 对位 local 的 SqliteEventLog：reconciler Lambda 经它读某 run 全量 events（worker PutItem 的执行事件
+ 退出观察者写的 task_exited）→ project 重放推演。**worker 侧不改**——worker 仍按 [0024] PutItem 执行事件到
events 表（FargateEngine 已真跑），本类只是**读**它们 + 提供 task_exited 的**写**（退出观察者 Lambda 调）。

**表 schema 复用现有 events 表**（[0024]/[0033]：PK=pk(run_id#scope_id) / SK=seq(NUMBER) / body=JSON行）——不加 GSI、
不改 schema：
- **读全量**：reconciler 有 RunMeta（definition 含全部 job.scope_id），故**逐 scope Query** `PK=run_id#scope_id`
  拼出全 run records（复用 FargateEngine._read_events 的单 scope Query 形状）。DDB PK 复合、不能只按 run_id 前缀查，
  但 scope_id 集合从 definition 已知，逐个 Query 即可、无需 GSI。
- **task_exited 独立键空间**（机制一）：DDB SK 是 NUMBER、不能用字符串前缀 `exit#`，故用**保留高位数值 SK**
  （`EXIT_SK`）——worker seq 从 1 递增、远不到它，故退出记录不入 worker 连续 seq 段、不参与断号检测（机制一等价落地）。
  用属性 `item_type='exit'` + `exit_code` 承载。键字段名/`EXIT_SK` 等 schema 常量单一事实源在 `fargate_engine`（见下 import）。
"""
from __future__ import annotations

from gherkai_core.adapters._boto import require_boto3
# events 表 schema 单一事实源在 fargate_engine（键字段名 + task_exited 独立键空间常量 + PK 拼法）——
# 本模块只 import、不再抄一份（两处各抄会漂移；反向 import 会成环，故 schema 归 fargate_engine）。
from gherkai_core.adapters.fargate_engine import (
    BODY_ATTR,
    EXIT_CODE_ATTR,
    EXIT_ITEM_TYPE,
    EXIT_SK,
    ITEM_TYPE_ATTR,
    PK_ATTR,
    SK_ATTR,
    events_pk,
)
from gherkai_core.project import EventRecord, TaskExited
from gherkai_core.wire import event_from_line

# events 表 TTL（[0033] 决定：events 是进度脚手架、只留 7 天）——写端（worker 的 EventSink）给每条 event item
# 写 `expires_at = emit 时刻 + 本值`，故读端反解 emit 墙钟 = expires_at − 本值（见 _emit_ts）。
# **与写端同一个数**：写端改 TTL 必须同步这里，否则反解出的墙钟整体偏移。
_EVENTS_TTL_S = 7 * 24 * 60 * 60


class DdbEventLog:
    """cloud EventLog：从 events 表读全量重放（逐 scope Query）+ 写 task_exited（保留高位 SK）。

    组合根/Lambda 注入 boto3 events 表资源 + run_id + 该 run 的 scope_id 列表（从 RunMeta 拿）。
    """

    def __init__(self, events_table, run_id: str, scope_ids: list[str]) -> None:
        require_boto3("DdbEventLog")
        self._table = events_table
        self._run_id = run_id
        self._scope_ids = list(scope_ids)

    def records(self) -> list[EventRecord]:
        """读某 run 全量 records（逐 scope Query worker 段 events + 取 task_exited）→ 供 project 全量重放。"""
        from boto3.dynamodb.conditions import Key

        recs: list[EventRecord] = []
        for scope_id in self._scope_ids:
            pk = events_pk(self._run_id, scope_id)
            # 逐 scope 全量 Query（含翻页；SK 升序保序）。worker 段 + 可能的 task_exited 高位 item 都在同 PK 下。
            kwargs = {"KeyConditionExpression": Key(PK_ATTR).eq(pk), "ScanIndexForward": True}
            while True:
                resp = self._table.query(**kwargs)
                for it in resp.get("Items", []):
                    if it.get(ITEM_TYPE_ATTR) == EXIT_ITEM_TYPE:
                        ec = it.get(EXIT_CODE_ATTR)
                        recs.append(EventRecord(
                            scope_id=scope_id, kind="exit",
                            exited=TaskExited(scope_id=scope_id,
                                              exit_code=int(ec) if ec is not None else None,
                                              timed_out=bool(it.get("timed_out", False))),
                        ))
                    else:
                        recs.append(EventRecord(
                            scope_id=scope_id, kind="event", seq=int(it[SK_ATTR]),
                            event=event_from_line(it[BODY_ATTR]),
                            emit_ts=self._emit_ts(it),
                        ))
                last_key = resp.get("LastEvaluatedKey")
                if not last_key:
                    break
                kwargs["ExclusiveStartKey"] = last_key
        return recs

    @staticmethod
    def _emit_ts(item) -> float:
        """从 events item 还原 worker emit 墙钟（reduce_event 的 now，供算时长）。

        写端（worker EventSink）写 `expires_at = emit 时刻 + TTL`（[0033]/[0024]），故减 `_EVENTS_TTL_S` 即 emit
        epoch 秒。缺 expires_at（不该发生）→ 0.0（时长算不准、但不影响判定，判定不依赖墙钟）。
        """
        exp = item.get("expires_at")
        if exp is None:
            return 0.0
        return float(exp) - _EVENTS_TTL_S

    def has_exit(self, scope_id: str) -> bool:
        """单个 scope 有没有退出记录（**只读**，退出记录键位确定 → 单 item 点查、不走 records() 重放整 run）。

        超时处置的「退出记录已在即让路」判断用（`lambdas/reconciler.py`，ADR 0034「job timeout」节被拒方案
        「处置者直接写 task_exited」的护栏）：一个 scope 的问题不该逐 scope Query 整 run。**强一致读**——
        判据正是「刚落的退出记录在不在」，最终一致读会漏看在途写、去 StopTask 一个已收敛的 job。
        """
        got = self._table.get_item(
            Key={PK_ATTR: events_pk(self._run_id, scope_id), SK_ATTR: EXIT_SK},
            ConsistentRead=True,
        )
        return got.get("Item") is not None

    def record_exit(self, scope_id: str, exit_code: int | None, *, timed_out: bool = False) -> None:
        """退出观察者 Lambda 调：写 task_exited 到保留高位 SK（独立键空间，机制一）。INSERT 幂等（覆盖同键）。

        exit_code=None 仅用于「payload 缺 exitCode 的宽限态」（机制二兜底，观察者应尽量带值）。
        timed_out：STOPPED 事件 stoppedReason 含超时哨兵（ADR 0034「job timeout」节归因链）；omit-when-False。"""
        item = {
            PK_ATTR: events_pk(self._run_id, scope_id),
            SK_ATTR: EXIT_SK,
            ITEM_TYPE_ATTR: EXIT_ITEM_TYPE,
        }
        if exit_code is not None:
            item[EXIT_CODE_ATTR] = exit_code
        if timed_out:
            item["timed_out"] = True
        self._table.put_item(Item=item)
