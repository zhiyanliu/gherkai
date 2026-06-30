// step 多行参数（DataTable / DocString，ADR 0024/0025）拼接——Midscene 腿（Nova 腿 run_scope.py
// 的 _argument_text/_instruction 的对称 TS 版）。提成独立模块以便单测（对称 deterministic.ts）。
//
// 现状：core/parse 把 .feature 的 DataTable/DocString 归一成 StepArgument（dataTable.rows 二维数组 /
// docString.content），经 wire 协议传到 worker。worker 把它拼成附加文本、接在 step 人话后喂 AI
// （ADR 0024：text(+argument) 一起喂引擎）。**两腿须同一拼法**，保同一 feature 行为对称。

export interface StepArgument {
  kind?: string;
  rows?: string[][];   // dataTable：行×单元格的二维字符串数组
  content?: string;    // docString：多行文本
}

// 单元格清洗（两腿须同一规则）：cell 内的 | 与换行会破坏 markdown 表格行结构 →
// | 转义成 \|、换行（\r\n/\n/\r）压成空格，使每个 cell 仍占一格、表格结构忠实。
function cleanCell(c: string): string {
  return String(c).replace(/\|/g, "\\|").replace(/\r\n|\r|\n/g, " ");
}

// 把 argument 拼成附加文本：dataTable→markdown 表格（| 分隔，还原 .feature 原貌、LLM 友好）；
// docString→content 原样。无 / 空 / 未知 kind → 空串。
// 注：rows 单元恒为字符串（core/wire 只发字符串，见 model.py rows: tuple[tuple[str,...]]）；cleanCell 的
// String() 仅防御，正常管线不可达非字符串。
export function argumentText(arg: StepArgument | undefined | null): string {
  if (!arg) return "";
  if (arg.kind === "dataTable") {
    const rows = arg.rows ?? [];
    if (rows.length === 0) return "";
    return rows.map((row) => "| " + row.map(cleanCell).join(" | ") + " |").join("\n");
  }
  if (arg.kind === "docString") return arg.content ?? "";
  return "";
}

// 去 step 人话外层引号（QA 写 When "搜索 X"）。只剥 **ASCII 空白**（与 Nova 的 strip 同集合）——
// 不用 trim()：JS trim 剥 U+FEFF(BOM) 而 Python strip 不剥，两腿分叉（BOM 能穿透 gherkin 进 text）。
const ASCII_WS = /^[ \t\r\n\f\v]+|[ \t\r\n\f\v]+$/g;
export function unquote(text: string): string {
  const t = text.replace(ASCII_WS, "");
  return t.length >= 2 && t.startsWith('"') && t.endsWith('"') ? t.slice(1, -1) : t;
}

// 喂 AI 的完整指令 = 去引号人话 + （可选）多行参数。无参数时退化为仅去引号（行为不变）。
export function buildInstruction(text: string, arg: StepArgument | undefined | null): string {
  const base = unquote(text);
  const extra = argumentText(arg);
  return extra ? `${base}\n${extra}` : base;
}
