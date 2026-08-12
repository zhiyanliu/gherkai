"""事件 sink（Nova worker，ADR 0024「I/O 边缘可注入接口」）：worker 主流程唯一的事件出口。

对称 Midscene 的 lib/event-sink.mts（各语言各写、语义契约对称，ADR 0024）+ 对称本引擎 ArtifactUploader
的结构骨架（from_env 唯一读 env、退化态是同类实例非 None/分支、外部 client 惰性建）。

三通道分离（ADR 0024）：协议事件走专用 fd（core adapter 读这个），与 SDK 打到 stdout 的进度噪声、worker
自己的诊断（stderr、走模块级 log()、**不经本 sink**）物理隔离。adapter 经环境变量 EVENTS_FD 告知 fd 号
（pass_fds 继承、号不固定）。无 EVENTS_FD（手动直跑、无 adapter）时回落 stdout，便于调试（`echo job | worker` 仍见事件）。

**emit 同步（合理不对称，ADR 0024）**：Nova worker 是同步 + greenlet 模型、全链路零 async，emit 同步；
Midscene 那个引擎 emit 为 async（Node 事件循环 + Fargate 化后 aws-sdk-js DDB PutItem 本就 async）。Fargate 化后
Nova 用 boto3（同步 SDK）put_item、同步 emit 天然容纳，无需 async 化（那是本 ADR 终止契约被拒的 asyncio 路）。

**两态（ADR 0024「DynamoDB 作 events-out」）**：
- **fd 态（subprocess）**：写 EVENTS_FD fd（无/非法 → 回落 stdout 调试）。
- **DDB 态（Fargate 化）**：`EVENTS_DDB_TABLE`+`RUN_ID`+`SCOPE_ID` 注入 → PutItem 到 events 表（PK=run_id#scope_id、
  SK=进程内自增 seq、body=JSON line）。判据=有没有注入 `EVENTS_DDB_TABLE`，非「是否 Fargate」（ADR 0016 红线）。
"""
from __future__ import annotations

import json
import os
import sys
import time
from typing import TextIO

# events 表 TTL（ADR 0033 / 0024）：每条 event item 写 expires_at=now+7d（epoch 秒），IaC 在该属性开 DDB TTL
# 自动过期。events 是进度脚手架（权威在 RunReport/ResultStore），留 7 天供事后调查失败 run。
# **改值须同步全部解码方（反向依赖）**：下游把本值当共享常量反解 emit 时刻——core 侧 event_log/ddb.py 的
# `_emit_ts`（emit_epoch = expires_at − 本值，用于算时长）与 tools/events_wallclock.py 各自硬编码同一个 7d；
# 只改这里会让它们把 emit 时刻算偏（且无人报错）。
_EVENTS_TTL_S = 7 * 24 * 60 * 60


class EventSink:
    """按注入的 env 把 ADR 0024 事件写到事件通道。fd 态：写 EVENTS_FD fd；DDB 态：PutItem 到 events 表。

    worker 是事件的 producer/client、不 listen（无 receive/listen）——「停」走 SIGTERM out-of-band、不经本 sink。
    只暴露 emit：**绝不暴露底层 fd/stdout 句柄、绝不把事件挪回 stdout**（守三通道分离，事件出 stdout 会重引入
    被隔离掉的 SDK 噪声污染）。
    """

    def __init__(self, *, out: TextIO | None = None, table_name: str | None = None,
                 run_id: str | None = None, scope_id: str | None = None) -> None:
        # 私有构造只吃已解析好的值（对称 ArtifactUploader.__init__ 不碰 env）。out 有=fd 态；table_name 有=DDB 态。
        self._out = out
        self._table_name = table_name
        self._run_id = run_id
        self._scope_id = scope_id
        self._client = None   # 惰性建 boto3 dynamodb client（仅 DDB 态、首次 emit 时）
        self._seq = 0         # DDB 态：scope 内单调自增序号（SK）——单进程串行 emit 天然单调，无需协调

    @classmethod
    def from_env(cls) -> "EventSink":
        """从注入的 env 造（唯一读 env 处）。EVENTS_DDB_TABLE 非空 → DDB 态；否则 fd 态（EVENTS_FD 无/非法 → 回落 stdout）。

        DDB 态判据 = 有没有注入 `EVENTS_DDB_TABLE`（非「是否 Fargate」，ADR 0016 红线）；空串当未注入（`or None`）。
        DDB 态还需 `RUN_ID`+`SCOPE_ID` 拼 PK=run_id#scope_id（组合根/FargateEngine RunTask overrides 注入）。
        """
        table_name = os.environ.get("EVENTS_DDB_TABLE") or None
        if table_name is not None:
            run_id = os.environ.get("RUN_ID") or None
            scope_id = os.environ.get("SCOPE_ID") or None
            if run_id is None or scope_id is None:
                # fail-loud（对齐 JobSource 对残缺配置的态度）：缺其一则 PK 拼成 "None#None"，全部事件
                # 静默写进无主键空间、adapter 按真 PK Query 永远读不到（无 scope_done → run 永不收敛），
                # 且多 scope 挤同一假 PK 各自 seq 从 1 起 → 撞号覆盖（破 ADR 0034 机制一「每 PK 单写者」）。
                raise ValueError(
                    "EventSink DDB 态：EVENTS_DDB_TABLE 已注入但缺 RUN_ID/SCOPE_ID——组合根装配错误"
                    f"（RUN_ID={run_id!r} SCOPE_ID={scope_id!r}）")
            return cls(table_name=table_name, run_id=run_id, scope_id=scope_id)
        events_fd = os.environ.get("EVENTS_FD")
        try:
            out = os.fdopen(int(events_fd), "w", encoding="utf-8") if events_fd else sys.stdout
        except (OSError, ValueError):
            out = sys.stdout
        return cls(out=out)

    def _ddb(self):
        # 惰性建 boto3 dynamodb resource + 超时（对称 ArtifactUploader._s3 的 Config：快速失败、退出有界，ADR 0024）。
        if self._client is None:
            import boto3
            from botocore.config import Config
            cfg = Config(connect_timeout=5, read_timeout=10, retries={"max_attempts": 0})
            self._client = boto3.resource(
                "dynamodb", region_name=os.environ.get("AWS_REGION"), config=cfg
            ).Table(self._table_name)
        return self._client

    def emit(self, event: dict) -> None:
        """吐一条 ADR 0024 事件（JSON Lines，字段名 camelCase 与 core/wire.py 一致）。

        fd 态：write+flush（每条 flush 保序、ensure_ascii=False 保中文，与旧内联逐字节一致）。
        DDB 态：PutItem(PK=run_id#scope_id, SK=自增 seq, body=JSON line)——SK 单调自增（scope 内串行、无需协调）。
        """
        line = json.dumps(event, ensure_ascii=False)
        if self._table_name is not None:
            self._seq += 1
            self._ddb().put_item(Item={
                "pk": f"{self._run_id}#{self._scope_id}",
                "seq": self._seq,
                "body": line,
                "expires_at": int(time.time()) + _EVENTS_TTL_S,  # DDB TTL 自动过期（ADR 0033/0024）
            })
            return
        self._out.write(line + "\n")
        self._out.flush()
