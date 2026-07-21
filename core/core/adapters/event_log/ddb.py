"""DdbEventLog（ADR 0034 P4）：cloud 无状态跑批的 EventLog——从 DDB events 表读全量重放 + 写 task_exited。

cloud 对位 local 的 SqliteEventLog：reconciler Lambda 经它读某 run 全量 events（worker PutItem 的执行事件
+ 退出观察者写的 task_exited）→ project 重放推演。**worker 侧不改**——worker 仍按 [0024] PutItem 执行事件到
events 表（FargateEngine 已真跑），本类只是**读**它们 + 提供 task_exited 的**写**（退出观察者 Lambda 调）。

**表 schema 复用现有 events 表**（[0024]/[0033]：PK=pk(run_id#scope_id) / SK=seq(NUMBER) / body=JSON行）——不加 GSI、
不改 schema：
- **读全量**：reconciler 有 RunMeta（definition 含全部 job.scope_id），故**逐 scope Query** `PK=run_id#scope_id`
  拼出全 run records（复用 FargateEngine._read_events 的单 scope Query 形状）。DDB PK 复合、不能只按 run_id 前缀查，
  但 scope_id 集合从 definition 已知，逐个 Query 即可、无需 GSI。
- **task_exited 独立键空间**（机制一）：DDB SK 是 NUMBER、不能用字符串前缀 `exit#`，故用**保留高位数值 SK**
  （`_EXIT_SK`）——worker seq 从 1 递增、远不到它，故退出记录不入 worker 连续 seq 段、不参与断号检测（机制一等价落地）。
  用属性 `item_type='exit'` + `exit_code` 承载。
"""
from __future__ import annotations

from core.adapters._boto import require_boto3
from core.adapters.fargate_engine import events_pk
from core.project import EventRecord, TaskExited
from core.wire import event_from_line

# events 表键/属性（复用 fargate_engine 的约定，[0024]）
_PK_ATTR = "pk"
_SK_ATTR = "seq"
_BODY_ATTR = "body"
# task_exited 的保留高位 SK（机制一独立键空间在 NUMBER SK 下的落地）：worker seq 从 1 递增、永不到此。
# 取一个远超任何真实 scope 事件数的大数（10^18，DDB Number 精度内、JSON 安全整数外但 DDB 存字符串数值 OK）。
_EXIT_SK = 10 ** 18
_ITEM_TYPE_ATTR = "item_type"
_EXIT_CODE_ATTR = "exit_code"


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
            kwargs = {"KeyConditionExpression": Key(_PK_ATTR).eq(pk), "ScanIndexForward": True}
            while True:
                resp = self._table.query(**kwargs)
                for it in resp.get("Items", []):
                    if it.get(_ITEM_TYPE_ATTR) == "exit":
                        ec = it.get(_EXIT_CODE_ATTR)
                        recs.append(EventRecord(
                            scope_id=scope_id, kind="exit",
                            exited=TaskExited(scope_id=scope_id,
                                              exit_code=int(ec) if ec is not None else None),
                        ))
                    else:
                        recs.append(EventRecord(
                            scope_id=scope_id, kind="event", seq=int(it[_SK_ATTR]),
                            event=event_from_line(it[_BODY_ATTR]),
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

        worker 写 expires_at=now+7d（[0033]/[0024]）——减 7d TTL 常量即 emit epoch 秒（见 tools/events_wallclock.py
        同源换算）。缺 expires_at（不该发生）→ 0.0（时长算不准、但不影响判定，判定不依赖墙钟）。
        """
        exp = item.get("expires_at")
        if exp is None:
            return 0.0
        return float(exp) - 7 * 24 * 3600

    def record_exit(self, scope_id: str, exit_code: int | None) -> None:
        """退出观察者 Lambda 调：写 task_exited 到保留高位 SK（独立键空间，机制一）。INSERT 幂等（覆盖同键）。

        exit_code=None 仅用于「payload 缺 exitCode 的宽限态」（机制二兜底，观察者应尽量带值）。"""
        item = {
            _PK_ATTR: events_pk(self._run_id, scope_id),
            _SK_ATTR: _EXIT_SK,
            _ITEM_TYPE_ATTR: "exit",
        }
        if exit_code is not None:
            item[_EXIT_CODE_ATTR] = exit_code
        self._table.put_item(Item=item)
