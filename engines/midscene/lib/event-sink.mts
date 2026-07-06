// 事件 sink（Midscene worker，ADR 0024「I/O 边缘可注入接口」第一期）：worker 主流程唯一的事件出口。
//
// 对称 Nova 的 lib/event_sink.py（各语言各写、语义契约对称，ADR 0024）+ 对称本腿 ArtifactUploader 的结构骨架
// （fromEnv 唯一读 env、退化态是同类实例非 undefined/分支、外部 client 惰性建）。
//
// 三通道分离（ADR 0024）：协议事件走专用 fd（core adapter 读这个），与 SDK 打到 stdout 的进度噪声、worker
// 自己的诊断（stderr、走模块级 log()、**不经本 sink**）物理隔离。adapter 经环境变量 EVENTS_FD 告知 fd 号
// （pass_fds 继承、号不固定）。无 EVENTS_FD（手动直跑、无 adapter）时回落 fd 1=stdout，便于调试（`echo job | worker` 仍见事件）。
//
// **emit 为 async（合理不对称，ADR 0024）**：Midscene worker 是 Node 事件循环模型、且未来 SQS 传输用 aws-sdk-js
// SendMessage 本就 async——emit 定 async 为 WP-Fargate 预留、免二次改签名 + 污染调用点。Nova 那腿 emit 同步
// （Nova 是同步 + greenlet 模型、boto3 同步 SDK）。根源=语言/SDK 执行模型差异，非「该对称却漏」。
//
// 第一期只实现 subprocess 态（写 EVENTS_FD fd，fs.writeSync 同步保序——async 签名下 await 一个立即完成的同步写、
// 时序不变）；SQS 态（SendMessage、MessageGroupId=scopeId）属 WP-Fargate、本组件形状须能容纳但不实现
// （判据=有没有注入 EVENTS_SQS_URL 等，非「是否 Fargate」）。
import * as fs from "node:fs";

export class EventSink {
  private fd: number;

  private constructor(fd: number) {
    // 私有构造只吃已解析好的 fd（对称 ArtifactUploader 构造只吃解析值、不碰 env）。
    this.fd = fd;
  }

  // 从注入的 env 造（唯一读 env 处）。EVENTS_FD 有→写该 fd；无→回落 fd 1=stdout（调试直跑）。
  static fromEnv(): EventSink {
    // SQS 态（Fargate 化，未实现）fail-loud（对称 JobSource 的 JOB_S3_URI 守卫）：注入了 EVENTS_SQS_URL 却
    // 跑到这 = 配置错，显式报错、不静默走 fd/stdout（否则 Fargate 事件写进无人读的 fd、静默丢）。实现时惰性建
    // SQS client + SendMessage(MessageGroupId=scopeId)。空串（|| undefined）统一当「未注入」（对称 EVENTS_FD 回落）。
    if (process.env.EVENTS_SQS_URL) throw new Error("EventSink: SQS 态未实现（注入了 EVENTS_SQS_URL）——属 Fargate 化");
    return new EventSink(process.env.EVENTS_FD ? Number(process.env.EVENTS_FD) : 1);
  }

  // 吐一条 ADR 0024 事件（JSON Lines，字段名 camelCase 与 core/wire.py 一致）。
  // subprocess 态：fs.writeSync 裸 fd 同步写保序（ADR 0024 顺序不变量）——async 签名下 await 立即完成的同步写、
  // 时序与旧内联 emit 逐字节一致。**只暴露 emit、绝不暴露底层 fd/stdout 句柄、绝不把事件挪回 stdout**
  // （守三通道分离，事件出 stdout 会重引入被隔离掉的 SDK 噪声污染）。worker 是 producer/client、不 listen。
  async emit(event: unknown): Promise<void> {
    fs.writeSync(this.fd, JSON.stringify(event) + "\n");
  }
}
