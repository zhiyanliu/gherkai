"""事件 sink（Nova worker，ADR 0024「I/O 边缘可注入接口」第一期）：worker 主流程唯一的事件出口。

对称 Midscene 的 lib/event-sink.mts（各语言各写、语义契约对称，ADR 0024）+ 对称本腿 ArtifactUploader
的结构骨架（from_env 唯一读 env、退化态是同类实例非 None/分支、外部 client 惰性建）。

三通道分离（ADR 0024）：协议事件走专用 fd（core adapter 读这个），与 SDK 打到 stdout 的进度噪声、worker
自己的诊断（stderr、走模块级 log()、**不经本 sink**）物理隔离。adapter 经环境变量 EVENTS_FD 告知 fd 号
（pass_fds 继承、号不固定）。无 EVENTS_FD（手动直跑、无 adapter）时回落 stdout，便于调试（`echo job | worker` 仍见事件）。

**emit 同步（合理不对称，ADR 0024）**：Nova worker 是同步 + greenlet 模型、全链路零 async，emit 同步；
Midscene 那腿 emit 为 async（Node 事件循环 + 未来 SQS aws-sdk-js 本就 async）。WP-Fargate 时 Nova 用 boto3
（同步 SDK）send_message、同步 emit 天然容纳，无需 async 化（那是本 ADR 终止契约被拒的 asyncio 路）。

第一期只实现 subprocess 态（写 EVENTS_FD fd）；S3/SQS 态（SendMessage、MessageGroupId=scope_id）属
WP-Fargate、本组件形状须能容纳但不实现（判据=有没有注入 EVENTS_SQS_URL 等，非「是否 Fargate」）。
"""
from __future__ import annotations

import json
import os
import sys
from typing import TextIO


class EventSink:
    """按注入的 env 把 ADR 0024 事件写到事件通道。subprocess 态：写 EVENTS_FD fd（无/非法 → 回落 stdout）。

    worker 是事件的 producer/client、不 listen（无 receive/listen）——「停」走 SIGTERM out-of-band、不经本 sink。
    只暴露 emit：**绝不暴露底层 fd/stdout 句柄、绝不把事件挪回 stdout**（守三通道分离，事件出 stdout 会重引入
    被隔离掉的 SDK 噪声污染）。
    """

    def __init__(self, *, out: TextIO) -> None:
        # 私有构造只吃已解析好的输出流（对称 ArtifactUploader.__init__ 只吃解析值、不碰 env）。
        self._out = out

    @classmethod
    def from_env(cls) -> "EventSink":
        """从注入的 env 造（唯一读 env 处）。EVENTS_FD 无 / int() 失败 / fdopen 失败 → 回落 stdout（调试直跑）。

        SQS 态（Fargate 化，未实现）fail-loud（对称 JobSource 的 JOB_S3_URI 守卫）：注入了 EVENTS_SQS_URL 却
        跑到这 = 配置错，显式报错、不静默走 fd/stdout（否则 Fargate 事件会写进无人读的 fd、静默丢）。实现时
        惰性建 SQS client + SendMessage(MessageGroupId=scopeId)。空串统一当「未注入」（对称 EVENTS_FD `or None`）。
        """
        if os.environ.get("EVENTS_SQS_URL") or None:
            raise NotImplementedError("EventSink: SQS 态未实现（注入了 EVENTS_SQS_URL）——属 Fargate 化")
        events_fd = os.environ.get("EVENTS_FD")
        try:
            out = os.fdopen(int(events_fd), "w", encoding="utf-8") if events_fd else sys.stdout
        except (OSError, ValueError):
            out = sys.stdout
        return cls(out=out)

    def emit(self, event: dict) -> None:
        """吐一条 ADR 0024 事件（JSON Lines，字段名 camelCase 与 core/wire.py 一致）。

        每条 flush 保序（ADR 0024 顺序不变量）；ensure_ascii=False 保中文（与旧内联 emit 逐字节一致）。
        """
        self._out.write(json.dumps(event, ensure_ascii=False) + "\n")
        self._out.flush()
