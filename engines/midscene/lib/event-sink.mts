// 事件 sink（Midscene worker，ADR 0024「I/O 边缘可注入接口」）：worker 主流程唯一的事件出口。
//
// 对称 Nova 的 lib/event_sink.py（各语言各写、语义契约对称，ADR 0024）+ 对称本引擎 ArtifactUploader 的结构骨架
// （fromEnv 唯一读 env、退化态是同类实例非 undefined/分支、外部 client 惰性建）。
//
// 三通道分离（ADR 0024）：协议事件走专用 fd（core adapter 读这个），与 SDK 打到 stdout 的进度噪声、worker
// 自己的诊断（stderr、走模块级 log()、**不经本 sink**）物理隔离。adapter 经环境变量 EVENTS_FD 告知 fd 号
// （pass_fds 继承、号不固定）。无 / 非法 EVENTS_FD（手动直跑、无 adapter；或值非数字、fd 已关）时回落
// fd 1=stdout，便于调试（`echo job | worker` 仍见事件）。
//
// **emit 为 async（合理不对称，ADR 0024）**：Midscene worker 是 Node 事件循环模型、Fargate 化后 aws-sdk-js DDB
// PutItem 本就 async——emit 定 async 免二次改签名 + 污染调用点。Nova 那个引擎 emit 同步（Nova 同步 + greenlet 模型、
// boto3 同步 SDK）。根源=语言/SDK 执行模型差异，非「该对称却漏」。
//
// **两态（ADR 0024「DynamoDB 作 events-out」）**：
// - fd 态（subprocess）：写 EVENTS_FD fd（fs.writeSync 同步保序——async 签名下 await 立即完成的同步写、时序不变）；无 / 非法 → 回落 fd 1=stdout。
// - DDB 态（Fargate 化）：EVENTS_DDB_TABLE+RUN_ID+SCOPE_ID 注入 → PutItem 到 events 表（PK=run_id#scope_id、
//   SK=进程内自增 seq、body=JSON line）。判据=有没有注入 EVENTS_DDB_TABLE，非「是否 Fargate」（ADR 0016 红线）。
import * as fs from "node:fs";
import { DynamoDBClient, PutItemCommand } from "@aws-sdk/client-dynamodb";

// 单次 PutItem 超时（ADR 0024，对称 ArtifactUploader.uploadOne 的 AbortSignal.timeout / Nova boto Config）：
// aws-sdk-js v3 默认无超时，退化网络下 PutItem 挂起会拖住 worker 退出。硬性封顶、best-effort。
const PUT_TIMEOUT_MS = 10_000;

// events 表 TTL（ADR 0033 / 0024，对称 Nova _EVENTS_TTL_S）：每条 event item 写 expires_at=now+7d（epoch 秒），
// IaC 在该属性开 DDB TTL 自动过期。events 是进度脚手架（权威在 RunReport/ResultStore），留 7 天供事后调查。
// **改值须同步全部解码方（反向依赖）**：下游把本值当共享常量反解 emit 时刻——core 侧 event_log/ddb.py 的
// `_emit_ts`（emit_epoch = expires_at − 本值，用于算时长）与 tools/events_wallclock.py 各自硬编码同一个 7d；
// 只改这里会让它们把 midscene scope 的 emit 时刻算偏（且无人报错）。
const EVENTS_TTL_S = 7 * 24 * 60 * 60;

// EVENTS_FD 解析（ADR 0024「EVENTS_FD 无 / 非法 → 回落 stdout」调试兜底；语义对称 Nova 的
// `try: os.fdopen(int(events_fd)) except (OSError, ValueError): sys.stdout`）：无 / 非整数 / 负 / 已关闭的
// fd 号一律回落 1=stdout。**不能只判「有没有」**——fs.writeSync 对非法 fd 直抛（NaN→ERR_OUT_OF_RANGE、
// 坏 fd→EBADF），而首条 emit 是 scope_started，抛在那里 = 整个 scope 零事件的 engine_error。
// fstatSync 是廉价的存活探测（Node 无「这个 fd 可写吗」的直接问法，坏 fd 在此即 EBADF）。
function resolveEventsFd(raw: string | undefined): number {
  const n = Number(raw);
  if (!raw?.trim() || !Number.isInteger(n) || n < 0) return 1;  // 空/空白（Number 会给 0/NaN）、非整数、负数
  try {
    fs.fstatSync(n);
  } catch {
    return 1;  // fd 号合法但没开着
  }
  return n;
}

export class EventSink {
  private fd: number | undefined;         // fd 态：写这个 fd
  private tableName: string | undefined;  // DDB 态：events 表名
  private runId: string | undefined;
  private scopeId: string | undefined;
  private client: DynamoDBClient | undefined;  // 惰性建（仅 DDB 态、首次 emit）
  private seq = 0;                              // DDB 态：scope 内自增序号（SK）——单进程串行 emit 天然单调

  private constructor(opts: { fd?: number; tableName?: string; runId?: string; scopeId?: string }) {
    // 私有构造只吃已解析值（对称 ArtifactUploader 不碰 env）。fd 有=fd 态；tableName 有=DDB 态。
    this.fd = opts.fd;
    this.tableName = opts.tableName;
    this.runId = opts.runId;
    this.scopeId = opts.scopeId;
  }

  // 从注入的 env 造（唯一读 env 处）。EVENTS_DDB_TABLE 非空 → DDB 态；否则 fd 态（EVENTS_FD 合法→写该 fd、无 / 非法→回落 fd 1=stdout）。
  // DDB 态判据 = 有没有注入 EVENTS_DDB_TABLE（非「是否 Fargate」，ADR 0016 红线）；空串（|| undefined）当未注入。
  static fromEnv(): EventSink {
    const tableName = process.env.EVENTS_DDB_TABLE || undefined;
    if (tableName !== undefined) {
      const runId = process.env.RUN_ID || undefined;
      const scopeId = process.env.SCOPE_ID || undefined;
      if (runId === undefined || scopeId === undefined) {
        // fail-loud（对齐 JobSource/Nova event_sink.py）：缺其一则 PK 拼成 "undefined#undefined"，事件
        // 静默写进无主键空间、adapter 永远读不到（run 永不收敛）+ 多 scope 撞号（破 ADR 0034 机制一）。
        throw new Error(
          `EventSink DDB 态：EVENTS_DDB_TABLE 已注入但缺 RUN_ID/SCOPE_ID——组合根装配错误（RUN_ID=${runId} SCOPE_ID=${scopeId}）`);
      }
      return new EventSink({ tableName, runId, scopeId });
    }
    return new EventSink({ fd: resolveEventsFd(process.env.EVENTS_FD) });
  }

  private client_(): DynamoDBClient {
    if (!this.client) this.client = new DynamoDBClient({ region: process.env.AWS_REGION });
    return this.client;
  }

  // 吐一条 ADR 0024 事件（JSON Lines，字段名 camelCase 与 core/wire.py 一致）。
  // fd 态：fs.writeSync 裸 fd 同步写保序（与旧内联逐字节一致）。
  // DDB 态：PutItem(PK=run_id#scope_id, SK=自增 seq, body=JSON line)，套 AbortSignal.timeout 封顶（退出有界，ADR 0024）。
  // **只暴露 emit、绝不暴露底层 fd/stdout 句柄、绝不把事件挪回 stdout**（守三通道分离）。worker 是 producer/client、不 listen。
  async emit(event: unknown): Promise<void> {
    const line = JSON.stringify(event);
    if (this.tableName !== undefined) {
      this.seq += 1;
      await this.client_().send(
        new PutItemCommand({
          TableName: this.tableName,
          Item: {
            pk: { S: `${this.runId}#${this.scopeId}` },
            seq: { N: String(this.seq) },
            body: { S: line },
            expires_at: { N: String(Math.floor(Date.now() / 1000) + EVENTS_TTL_S) },  // DDB TTL 自动过期（ADR 0033/0024）
          },
        }),
        { abortSignal: AbortSignal.timeout(PUT_TIMEOUT_MS) },
      );
      return;
    }
    fs.writeSync(this.fd!, line + "\n");
  }
}
