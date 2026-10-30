// Midscene worker 写 stderr 的出口清单的静态差集（ADR 0051 决策 11、ADR 0035 决策 5）。运行：npx tsx --test src/worker/stderr-outlets.test.mts。
//
// worker 自己写 stderr 的出口都在写出时经 lib/redact.mts 的 redactSecrets：云端没有 core 的转发层，worker 的 stderr 原样进入
// CloudWatch。出口恰为五处：bin.mts 的 worker fatal 行、ArtifactUploader 的缺省 logFn、loadUserSteps 的缺省 logFn、run-scope 的
// log() 与 stepEvidenceRef 的缺省 logFn。脱敏规则由 redact.test.mts 用跨语言用例表守，各出口写出的文字由 redact.test.mts 与
// evidence.test.mts 的运行期用例逐处核对；本文件守的是出口集合本身：只靠人记录清单时，新加的出口容易漏掉脱敏。与 Nova worker
// 的 engines/novaact/tests/test_stderr_redaction.py 的静态差集对称。
//
// 用 TypeScript 编译器的语法树扫 src/ 下全部非测试的 .mts（含 bin.mts、lib/、worker/、device/）。出口按「文件相对 src 的路径加
// 所在声明」标识，不用行号。所在声明是由外到内各层带名字的类、函数、方法、类字段与模块级变量，以点连接，都不在其中时记作
// (module)；函数里的局部变量与箭头函数不单独成层，所以缺省 logFn 的箭头函数归到它所在的函数或类字段。
//
// 计入写入的写法，逐处核对写入的实参：
//   - process.stderr.write(...) 与 process.stderr.end(...)，含 process["stderr"]、globalThis.process，以及从 node:process 缺省导入
//     或整体导入的名字；
//   - console.error / warn / trace / assert(...)，含 console["error"]、globalThis.console，以及从 node:console 缺省导入或整体导入的
//     名字（assert 只核对第一个参数之后的实参）；console.log / info / debug 写 stdout，不计入；
//   - 第一个参数为整数字面量 2 的 write / writeSync / writev / writevSync / writeFile / writeFileSync / appendFile / appendFileSync
//     调用，按被调函数的名字认、不核对它是否来自 fs，核对第二个参数。
// 实参经过脱敏，指它是 redactSecrets(...) 的调用，或由这样的调用与字符串字面量以 + 或不带标签的模板拼成、且至少含一处这样的
// 调用。redactSecrets 这个名字须从 lib/redact.mts 导入：静态 import（含改名导入与整体导入）与 await import(...) 的解构都算。
//
// 无法登记为出口的写法，出现即报，因为无法核对它写出的实参：
//   - process.stderr 不以 .write(...) 或 .end(...) 直接写出的用法：赋给变量（别名）、解构、作为参数传出、把 .write 当作值取出、
//     读取它的其他属性；
//   - 从 node:process 导入或解构出 stderr、emitWarning、_rawDebug，调用 process.emitWarning 与 process._rawDebug（两者直接写 stderr）；
//   - 把 console 对象或 console.error 一类方法当作值使用、以计算出的名字取 process 或 console 的成员、从 node:console 按名导入、
//     新建 Console 实例（new console.Console(...) 等）；
//   - 以 import() 或 require 动态加载 process 与 console 模块；
//   - 以文件描述符 2 建流：对象字面量里的 fd: 2（如 fs.createWriteStream(null, { fd: 2 })），以及第一个参数为 2 的 WriteStream、
//     SyncWriteStream 与 Socket；
//   - 字符串字面量 /dev/stderr、/dev/fd/2 与 /proc/self/fd/2；
//   - util.debuglog（NODE_DEBUG 打开时写 stderr）；
//   - 在文件里另行绑定 redactSecrets 这个名字。
//
// 已知无法识别的写法：文件描述符来自变量或表达式（如 lib/event-sink.mts 按 EVENTS_FD 写出的 fs.writeSync(this.fd, ...)）；process
// 对象经变量、参数或返回值传出后再取 stderr（device/surface.mts 把 process 作为事件源交给进程级兜底，这类传递不报）；以拼接出的
// 属性名取 stderr（如 process["std" + "err"]）；经 createRequire 或计算出的模块名加载 process 与 console 模块；eval 与 new Function；
// 子进程继承的 stderr；Node 运行时自己写出的内容（未捕获异常的缺省输出、进程警告）；第三方库自己写的 stderr：WebdriverIO 的
// @wdio/logger 由 device/wdio-log.mts 装上的掩码覆盖、不在本差集内，Midscene SDK 与 Playwright 自己写出的内容同样不经这些出口。
// 检查的是写入实参的形状，不核对脱敏后的值是否就是要写出的全部内容，写出结果由上面所列的运行期用例核对。
//
// 拒绝用例对构造的源码片段，或把真实源码的内存副本改一处，再交给同一套检查；正向对照是真实 src 的差集为空。
import { test } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import ts from "typescript";

const SRC = path.resolve(import.meta.dirname, "..");

/** 登记的出口：文件（相对 src）、所在声明与说明。新出口先经 redactSecrets，再登记进这里。 */
const STDERR_OUTLETS: ReadonlyArray<readonly [string, string, string]> = [
  ["bin.mts", "(module)", "worker fatal 行"],
  ["lib/artifact-upload.mts", "ArtifactUploader.logFn", "ArtifactUploader 的缺省 logFn"],
  ["worker/evidence.mts", "stepEvidenceRef", "stepEvidenceRef 的缺省 logFn"],
  ["worker/run-scope.mts", "log", "run-scope 的 log()"],
  ["worker/user-steps.mts", "loadUserSteps", "loadUserSteps 的缺省 logFn"],
];

const keyOf = (rel: string, scope: string): string => `${rel} 的 ${scope}`;
const REGISTERED: ReadonlySet<string> = new Set(STDERR_OUTLETS.map(([rel, scope]) => keyOf(rel, scope)));

const REDACT_MODULE = "lib/redact.mts";
const REDACT_EXPORT = "redactSecrets";

/** src/ 下全部非测试的 .mts 源文件，路径相对 src、以 / 分隔。 */
function sourceFiles(): string[] {
  const out: string[] = [];
  const walk = (dir: string): void => {
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      const full = path.join(dir, entry.name);
      if (entry.isDirectory()) walk(full);
      else if (entry.name.endsWith(".mts") && !entry.name.endsWith(".test.mts")) out.push(path.relative(SRC, full).split(path.sep).join("/"));
    }
  };
  walk(SRC);
  return out.sort();
}

let realSourcesCache: ReadonlyMap<string, string> | undefined;

/** 真实 src 的源码，键是相对 src 的路径。 */
function realSources(): ReadonlyMap<string, string> {
  realSourcesCache ??= new Map(sourceFiles().map((rel) => [rel, fs.readFileSync(path.join(SRC, rel), "utf-8")]));
  return realSourcesCache;
}

function parse(rel: string, text: string): ts.SourceFile {
  return ts.createSourceFile(rel, text, ts.ScriptTarget.Latest, true, ts.ScriptKind.TS);
}

function visit(node: ts.Node, fn: (n: ts.Node) => void): void {
  fn(node);
  ts.forEachChild(node, (child) => visit(child, fn));
}

function lineOf(sf: ts.SourceFile, node: ts.Node): number {
  return sf.getLineAndCharacterOfPosition(node.getStart(sf)).line + 1;
}

// ---- 所在声明 ----

function propertyNameText(name: ts.PropertyName | ts.BindingName | undefined): string | null {
  if (name === undefined) return null;
  if (ts.isIdentifier(name) || ts.isStringLiteralLike(name) || ts.isPrivateIdentifier(name)) return name.text;
  return null;
}

/** 带名字的声明给出它的名字，其余节点为 null。写法与 device/read-points.test.mts 的所在声明一致。 */
function scopeName(p: ts.Node): string | null {
  if (ts.isConstructorDeclaration(p)) return "constructor";
  if (ts.isClassDeclaration(p) || ts.isFunctionDeclaration(p) || ts.isMethodDeclaration(p) || ts.isGetAccessorDeclaration(p)
    || ts.isSetAccessorDeclaration(p) || ts.isPropertyDeclaration(p)) {
    return p.name !== undefined ? propertyNameText(p.name) ?? "(computed)" : "(anonymous)";
  }
  if (ts.isVariableDeclaration(p) && ts.isIdentifier(p.name) && ts.isSourceFile(p.parent.parent.parent)) return p.name.text;
  return null;
}

/** 节点所在声明的名字（由外到内以点连接，都不在其中时为 (module)）与最内层的那个声明节点。 */
function scopeOf(n: ts.Node): { scope: string; decl: ts.Node | null } {
  const names: string[] = [];
  let decl: ts.Node | null = null;
  for (let p = n.parent; p !== undefined; p = p.parent) {
    const name = scopeName(p);
    if (name === null) continue;
    names.unshift(name);
    decl ??= p;
  }
  return { scope: names.length > 0 ? names.join(".") : "(module)", decl };
}

// ---- 名字与模块 ----

type Member = ts.PropertyAccessExpression | ts.ElementAccessExpression;

function isMember(n: ts.Node): n is Member {
  return ts.isPropertyAccessExpression(n) || ts.isElementAccessExpression(n);
}

/** 成员名：属性访问取名字，下标取字符串字面量；下标不是字面量时为 null。 */
function memberName(n: Member): string | null {
  if (ts.isPropertyAccessExpression(n)) return n.name.text;
  return ts.isStringLiteralLike(n.argumentExpression) ? n.argumentExpression.text : null;
}

function isBaseOfMember(n: ts.Node): boolean {
  return isMember(n.parent) && n.parent.expression === n;
}

/** 去掉不改变取值的外层：括号、类型断言、非空断言与 satisfies。 */
function strip(e: ts.Expression): ts.Expression {
  let x = e;
  while (ts.isParenthesizedExpression(x) || ts.isAsExpression(x) || ts.isNonNullExpression(x) || ts.isTypeAssertionExpression(x)
    || ts.isSatisfiesExpression(x)) x = x.expression;
  return x;
}

function isBuiltin(spec: string, name: string): boolean {
  return spec === name || spec === `node:${name}`;
}

/** 相对路径的模块说明符解析成相对 src 的源文件路径（.mjs 对应源码的 .mts）；包名与内建模块为 null。 */
function resolveLocal(rel: string, spec: string): string | null {
  if (!spec.startsWith(".")) return null;
  return path.posix.normalize(path.posix.join(path.posix.dirname(rel), spec)).replace(/\.mjs$/, ".mts");
}

/** `import("x")`、`await import("x")` 与 `require("x")` 的模块说明符。 */
function dynamicImportSpecifier(e: ts.Expression): string | null {
  let x = strip(e);
  if (ts.isAwaitExpression(x)) x = strip(x.expression);
  if (!ts.isCallExpression(x) || x.arguments.length === 0) return null;
  const dynamic = x.expression.kind === ts.SyntaxKind.ImportKeyword || (ts.isIdentifier(x.expression) && x.expression.text === "require");
  const arg = x.arguments[0]!;
  return dynamic && ts.isStringLiteralLike(arg) ? arg.text : null;
}

/** 一个文件里指 process、console 与 redactSecrets 的名字。 */
interface Bindings {
  process: Set<string>;
  console: Set<string>;
  /** 指 lib/redact.mts 的 redactSecrets 的名字。 */
  redact: Set<string>;
  /** 指整个 lib/redact.mts 模块的名字（整体导入或 await import 的结果）。 */
  redactNs: Set<string>;
  /** 上面两组 redact 名字的绑定处；文件里同名的其他声明是另行绑定。 */
  redactBindings: Set<ts.Node>;
}

function bindingsOf(rel: string, sf: ts.SourceFile): Bindings {
  const b: Bindings = {
    process: new Set(["process"]), console: new Set(["console"]), redact: new Set(), redactNs: new Set(), redactBindings: new Set(),
  };
  const bindRedact = (name: ts.Identifier, whole: boolean): void => {
    (whole ? b.redactNs : b.redact).add(name.text);
    b.redactBindings.add(name);
  };
  visit(sf, (n) => {
    if (ts.isImportDeclaration(n) && ts.isStringLiteral(n.moduleSpecifier) && n.importClause !== undefined) {
      const spec = n.moduleSpecifier.text;
      const clause = n.importClause;
      const nb = clause.namedBindings;
      const builtin = isBuiltin(spec, "process") ? b.process : isBuiltin(spec, "console") ? b.console : null;
      if (builtin !== null) {
        if (clause.name !== undefined) builtin.add(clause.name.text);
        if (nb !== undefined && ts.isNamespaceImport(nb)) builtin.add(nb.name.text);
      } else if (resolveLocal(rel, spec) === REDACT_MODULE && clause.phaseModifier !== ts.SyntaxKind.TypeKeyword) {
        if (nb !== undefined && ts.isNamespaceImport(nb)) bindRedact(nb.name, true);
        if (nb !== undefined && ts.isNamedImports(nb)) {
          for (const el of nb.elements) if (!el.isTypeOnly && (el.propertyName ?? el.name).text === REDACT_EXPORT) bindRedact(el.name, false);
        }
      }
    } else if (ts.isVariableDeclaration(n) && n.initializer !== undefined) {
      const spec = dynamicImportSpecifier(n.initializer);
      if (spec === null || resolveLocal(rel, spec) !== REDACT_MODULE) return;
      if (ts.isIdentifier(n.name)) bindRedact(n.name, true);
      else if (ts.isObjectBindingPattern(n.name)) {
        for (const el of n.name.elements) {
          if (propertyNameText(el.propertyName ?? el.name) === REDACT_EXPORT && ts.isIdentifier(el.name)) bindRedact(el.name, false);
        }
      }
    }
  });
  return b;
}

function isGlobalObject(e: ts.Expression): boolean {
  const x = strip(e);
  return ts.isIdentifier(x) && (x.text === "globalThis" || x.text === "global");
}

/** 表达式指 process（或 console）对象：绑定到它的名字，或 globalThis 上的同名成员。 */
function isBuiltinObject(e: ts.Expression, names: ReadonlySet<string>, member: string): boolean {
  const x = strip(e);
  if (ts.isIdentifier(x)) return names.has(x.text);
  return isMember(x) && memberName(x) === member && isGlobalObject(x.expression);
}

const DECLARATION_KINDS: ReadonlySet<ts.SyntaxKind> = new Set([
  ts.SyntaxKind.VariableDeclaration, ts.SyntaxKind.Parameter, ts.SyntaxKind.FunctionDeclaration, ts.SyntaxKind.FunctionExpression,
  ts.SyntaxKind.ClassDeclaration, ts.SyntaxKind.ClassExpression, ts.SyntaxKind.BindingElement, ts.SyntaxKind.ImportSpecifier,
  ts.SyntaxKind.ImportClause, ts.SyntaxKind.NamespaceImport, ts.SyntaxKind.ImportEqualsDeclaration,
]);

/** 标识符是某个声明绑定的名字。 */
function isDeclarationName(id: ts.Identifier): boolean {
  const p = id.parent as ts.Node & { name?: ts.Node };
  return DECLARATION_KINDS.has(p.kind) && p.name === id;
}

/** 节点在类型里（含 `typeof x` 这类类型查询）。 */
function inType(n: ts.Node): boolean {
  for (let p = n.parent; p !== undefined; p = p.parent) if (ts.isTypeNode(p)) return true;
  return false;
}

/** 标识符在取值位置：不是类型、声明名、属性名、导入导出说明符或解构键。简写属性 `{ console }` 是取值。 */
function isValueReference(id: ts.Identifier): boolean {
  if (inType(id)) return false;
  const p = id.parent as ts.Node & { name?: ts.Node; propertyName?: ts.Node };
  if (ts.isShorthandPropertyAssignment(p)) return true;
  if (p.name === id || p.propertyName === id) return false;
  return !(ts.isQualifiedName(p) || ts.isLabeledStatement(p) || ts.isBreakOrContinueStatement(p));
}

// ---- 写入实参 ----

function isRedactCall(e: ts.CallExpression, b: Bindings): boolean {
  const callee = strip(e.expression);
  if (ts.isIdentifier(callee)) return b.redact.has(callee.text);
  if (!isMember(callee) || memberName(callee) !== REDACT_EXPORT) return false;
  const base = strip(callee.expression);
  return ts.isIdentifier(base) && b.redactNs.has(base.text);
}

function isText(e: ts.Expression): boolean {
  return ts.isStringLiteralLike(strip(e));
}

/** 写入的实参经过脱敏：redactSecrets 的调用，或这样的调用与字符串字面量以 + 或不带标签的模板拼成（至少含一处调用）。 */
function isRedacted(expr: ts.Expression | undefined, b: Bindings): boolean {
  if (expr === undefined) return false;
  const e = strip(expr);
  if (ts.isCallExpression(e)) return isRedactCall(e, b);
  if (ts.isBinaryExpression(e) && e.operatorToken.kind === ts.SyntaxKind.PlusToken) {
    const left = isRedacted(e.left, b);
    const right = isRedacted(e.right, b);
    return (left || right) && (left || isText(e.left)) && (right || isText(e.right));
  }
  if (ts.isTemplateExpression(e)) return e.templateSpans.every((s) => isRedacted(s.expression, b));
  return false;
}

// ---- 扫描 ----

/** 计入 stderr 的 console 方法；log / info / debug 写 stdout。 */
const CONSOLE_STDERR: ReadonlySet<string> = new Set(["error", "warn", "trace", "assert"]);
/** 从 process 取出即写 stderr 或即为 stderr 的成员。 */
const PROCESS_DIRECT: ReadonlySet<string> = new Set(["stderr", "emitWarning", "_rawDebug"]);
/** 第一个参数是文件描述符、第二个参数是写入内容的函数名。 */
const FD_WRITERS: ReadonlySet<string> = new Set([
  "write", "writeSync", "writev", "writevSync", "writeFile", "writeFileSync", "appendFile", "appendFileSync",
]);
/** 第一个参数是文件描述符时建出一条流的构造器与函数名。 */
const FD_STREAMS: ReadonlySet<string> = new Set(["WriteStream", "SyncWriteStream", "Socket"]);
const STDERR_PATHS = /^(?:\/dev\/stderr|\/dev\/fd\/2|\/proc\/self\/fd\/2)$/;

function isFd2(e: ts.Expression | undefined): boolean {
  if (e === undefined) return false;
  const x = strip(e);
  return ts.isNumericLiteral(x) && Number(x.text) === 2;
}

function calleeName(callee: ts.Expression): string | null {
  const x = strip(callee);
  if (ts.isIdentifier(x)) return x.text;
  return isMember(x) ? memberName(x) : null;
}

interface Write {
  scope: string;
  decl: ts.Node | null;
  line: number;
  form: string;
  redacted: boolean;
}

interface Unregistrable {
  scope: string;
  line: number;
  form: string;
}

interface FileScan {
  writes: Write[];
  unregistrable: Unregistrable[];
}

const fileScanCache = new Map<string, FileScan>();

function scanFile(rel: string, text: string): FileScan {
  const cacheKey = `${rel}\u0000${text}`;
  const cached = fileScanCache.get(cacheKey);
  if (cached !== undefined) return cached;
  const sf = parse(rel, text);
  const b = bindingsOf(rel, sf);
  const result: FileScan = { writes: [], unregistrable: [] };
  const write = (n: ts.Node, form: string, args: readonly ts.Expression[]): void => {
    const { scope, decl } = scopeOf(n);
    result.writes.push({ scope, decl, line: lineOf(sf, n), form, redacted: args.length > 0 && args.every((a) => isRedacted(a, b)) });
  };
  const reject = (n: ts.Node, form: string): void => {
    result.unregistrable.push({ scope: scopeOf(n).scope, line: lineOf(sf, n), form });
  };
  const isProcess = (e: ts.Expression): boolean => isBuiltinObject(e, b.process, "process");
  const isConsole = (e: ts.Expression): boolean => isBuiltinObject(e, b.console, "console");
  const isStderr = (e: ts.Expression): boolean => {
    const x = strip(e);
    return isMember(x) && memberName(x) === "stderr" && isProcess(x.expression);
  };

  /** process.stderr 的一处引用：直接以 .write(...) 或 .end(...) 写出时计入写入，其余用法无法登记。 */
  const stderrReference = (ref: Member): void => {
    const m = ref.parent;
    if (isMember(m) && m.expression === ref) {
      const method = memberName(m);
      const call = m.parent;
      if ((method === "write" || method === "end") && ts.isCallExpression(call) && call.expression === m) {
        write(ref, `process.stderr.${method}`, call.arguments.slice(0, 1));
        return;
      }
    }
    reject(ref, "process.stderr 不以 .write(...) 或 .end(...) 直接写出（别名、解构、传参、把方法当作值或读取其他属性）");
  };

  const memberRule = (n: Member): void => {
    const name = memberName(n);
    if (isProcess(n.expression)) {
      if (name === null) reject(n, "以计算出的名字取 process 的成员");
      else if (name === "stderr") stderrReference(n);
      else if (PROCESS_DIRECT.has(name)) reject(n, `process.${name}`);
    } else if (isConsole(n.expression)) {
      if (name === null) reject(n, "以计算出的名字取 console 的成员");
      else if (CONSOLE_STDERR.has(name)) {
        const call = n.parent;
        if (ts.isCallExpression(call) && call.expression === n) write(n, `console.${name}`, name === "assert" ? call.arguments.slice(1) : call.arguments);
        else reject(n, `把 console.${name} 当作值使用`);
      } else if (name === "Console") reject(n, "新建 Console 实例");
    } else if (name === "debuglog") {
      reject(n, "util.debuglog");
    } else if (name === "console" && isGlobalObject(n.expression) && !isBaseOfMember(n)) {
      reject(n, "把 console 对象当作值使用");
    }
  };

  const callRule = (n: ts.CallExpression | ts.NewExpression): void => {
    const args = n.arguments ?? [];
    if (ts.isCallExpression(n)) {
      const spec = dynamicImportSpecifier(n);
      if (spec !== null) {
        if (isBuiltin(spec, "process") || isBuiltin(spec, "console")) reject(n, `动态加载 ${spec}`);
        return;
      }
    }
    const name = calleeName(n.expression);
    if (name === null || !isFd2(args[0])) return;
    const callee = strip(n.expression);
    if (ts.isCallExpression(n) && FD_WRITERS.has(name) && !(isMember(callee) && isStderr(callee.expression))) {
      write(n, `${name}(2, ...)`, args.slice(1, 2));
    } else if (FD_STREAMS.has(name)) {
      reject(n, `以文件描述符 2 建流（${name}）`);
    }
  };

  const importRule = (n: ts.ImportDeclaration): void => {
    const clause = n.importClause;
    if (!ts.isStringLiteral(n.moduleSpecifier) || clause === undefined || clause.phaseModifier === ts.SyntaxKind.TypeKeyword) return;
    const spec = n.moduleSpecifier.text;
    const nb = clause.namedBindings;
    if (nb === undefined || !ts.isNamedImports(nb)) return;
    for (const el of nb.elements) {
      if (el.isTypeOnly) continue;
      const imported = (el.propertyName ?? el.name).text;
      if ((isBuiltin(spec, "process") && PROCESS_DIRECT.has(imported)) || isBuiltin(spec, "console")
        || (isBuiltin(spec, "util") && imported === "debuglog")) reject(el, `从 ${spec} 导入 ${imported}`);
    }
  };

  /** 从 process 解构：取出直接写 stderr 的成员、以计算出的名字或剩余元素解构都无法登记。 */
  const processKeys = (n: ts.Node, keys: ReadonlyArray<string | null>): void => {
    for (const key of keys) {
      if (key === null) reject(n, "以计算出的名字解构 process");
      else if (key === "...") reject(n, "以剩余元素解构 process");
      else if (PROCESS_DIRECT.has(key)) reject(n, `解构取出 process.${key}`);
    }
  };

  visit(sf, (n) => {
    if (isMember(n)) memberRule(n);
    else if (ts.isIdentifier(n)) {
      if (b.console.has(n.text) && isValueReference(n) && !isBaseOfMember(n)) reject(n, "把 console 对象当作值使用");
      if ((b.redact.has(n.text) || b.redactNs.has(n.text)) && isDeclarationName(n) && !b.redactBindings.has(n)) {
        reject(n, `在文件里另行绑定 ${n.text}`);
      }
    } else if (ts.isCallExpression(n) || ts.isNewExpression(n)) callRule(n);
    else if (ts.isImportDeclaration(n)) importRule(n);
    else if ((ts.isVariableDeclaration(n) || ts.isParameter(n) || ts.isBindingElement(n)) && ts.isObjectBindingPattern(n.name)
      && n.initializer !== undefined && isProcess(n.initializer)) {
      processKeys(n, n.name.elements.map((el) => (el.dotDotDotToken !== undefined ? "..." : propertyNameText(el.propertyName ?? el.name))));
    } else if (ts.isBinaryExpression(n) && n.operatorToken.kind === ts.SyntaxKind.EqualsToken
      && ts.isObjectLiteralExpression(strip(n.left)) && isProcess(n.right)) {
      const pattern = strip(n.left) as ts.ObjectLiteralExpression;
      processKeys(n, pattern.properties.map((p) => (ts.isSpreadAssignment(p) ? "..."
        : ts.isShorthandPropertyAssignment(p) ? p.name.text : ts.isPropertyAssignment(p) ? propertyNameText(p.name) : null)));
    } else if (ts.isPropertyAssignment(n) && propertyNameText(n.name) === "fd" && isFd2(n.initializer)) {
      reject(n, "以 { fd: 2 } 建流或打开文件描述符 2");
    } else if (ts.isStringLiteralLike(n) && STDERR_PATHS.test(n.text)) {
      reject(n, `按路径打开标准错误（${n.text}）`);
    }
  });
  result.writes.sort((x, y) => x.line - y.line);
  result.unregistrable.sort((x, y) => x.line - y.line);
  fileScanCache.set(cacheKey, result);
  return result;
}

// ---- 差集 ----

const UNREGISTERED = "未登记的出口";
const GONE = "登记的出口不再写 stderr";
const DUPLICATE = "同一个名字有多个声明";
const UNREDACTED = "写入的实参没有经过 redactSecrets";
const UNREGISTRABLE = "无法登记的写法";

interface Violation {
  kind: string;
  rel: string;
  scope: string;
  detail: string;
}

interface Outlet {
  rel: string;
  scope: string;
  decls: Set<ts.Node | null>;
  writes: Write[];
}

function outletsOf(sources: ReadonlyMap<string, string>): { outlets: Outlet[]; unregistrable: Violation[] } {
  const outlets = new Map<string, Outlet>();
  const unregistrable: Violation[] = [];
  for (const [rel, text] of [...sources].sort(([a], [b]) => a.localeCompare(b))) {
    const scanned = scanFile(rel, text);
    for (const w of scanned.writes) {
      const key = keyOf(rel, w.scope);
      const outlet = outlets.get(key) ?? { rel, scope: w.scope, decls: new Set<ts.Node | null>(), writes: [] };
      outlet.decls.add(w.decl);
      outlet.writes.push(w);
      outlets.set(key, outlet);
    }
    unregistrable.push(...scanned.unregistrable.map((u) => ({ kind: UNREGISTRABLE, rel, scope: u.scope, detail: `${u.line} 行 ${u.form}` })));
  }
  return { outlets: [...outlets.values()], unregistrable };
}

/** 对照登记清单的全部违例；真实 src 应为空。 */
function violations(sources: ReadonlyMap<string, string>): Violation[] {
  const { outlets, unregistrable } = outletsOf(sources);
  const found = new Set(outlets.map((o) => keyOf(o.rel, o.scope)));
  const out: Violation[] = [];
  for (const o of outlets) {
    const forms = o.writes.map((w) => `${w.line} 行 ${w.form}`).join("，");
    if (!REGISTERED.has(keyOf(o.rel, o.scope))) out.push({ kind: UNREGISTERED, rel: o.rel, scope: o.scope, detail: forms });
    if (o.decls.size > 1) out.push({ kind: DUPLICATE, rel: o.rel, scope: o.scope, detail: `${o.decls.size} 个声明，${forms}` });
    for (const w of o.writes) if (!w.redacted) out.push({ kind: UNREDACTED, rel: o.rel, scope: o.scope, detail: `${w.line} 行 ${w.form}` });
  }
  for (const [rel, scope] of STDERR_OUTLETS) if (!found.has(keyOf(rel, scope))) out.push({ kind: GONE, rel, scope, detail: "" });
  return [...out, ...unregistrable];
}

function describe(vs: readonly Violation[]): string {
  return vs.map((v) => `${v.kind}：${keyOf(v.rel, v.scope)}${v.detail === "" ? "" : `（${v.detail}）`}`).join("\n");
}

function has(vs: readonly Violation[], kind: string, rel: string, scope: string): boolean {
  return vs.some((v) => v.kind === kind && v.rel === rel && v.scope === scope);
}

/** 真实 src 的内存副本，只改一个文件：old 为 null 时把 added 追加到文件末尾，否则把恰好出现一次的 old 换成 added。 */
function withSource(rel: string, old: string | null, added: string): Map<string, string> {
  const sources = new Map(realSources());
  const text = sources.get(rel);
  assert.ok(text !== undefined, `扫描面里没有 ${rel}`);
  if (old === null) sources.set(rel, `${text}\n${added}\n`);
  else {
    assert.equal(text.split(old).length - 1, 1, `${rel} 里应恰有一处 ${JSON.stringify(old)}：源码改过就同步更新这条用例`);
    sources.set(rel, text.replace(old, () => added));
  }
  return sources;
}

// ---- 检测函数的正向对照（构造的片段） ----

const FRAGMENT = "worker/probe.mts";  // 片段的文件名：相对导入 ../lib/redact.mjs 解析到 lib/redact.mts

function fragment(lines: readonly string[], rel: string = FRAGMENT): FileScan {
  return scanFile(rel, lines.join("\n"));
}

test("检测函数在构造的片段上认出计入写入的写法，并逐处核对实参", () => {
  const scanned = fragment([
    "import { redactSecrets } from \"../lib/redact.mjs\";",
    "import { redactSecrets as r } from \"../lib/redact.mjs\";",
    "import * as R from \"../lib/redact.mjs\";",
    "import proc from \"node:process\";",
    "import * as con from \"node:console\";",
    "import fs from \"node:fs\";",
    "function a(m: string) { process.stderr.write(redactSecrets(m) + \"\\n\"); }",
    "function b(m: string) { process[\"stderr\"].write(`${r(m)}\\n`); }",
    "function c(m: string) { globalThis.process.stderr.write(R.redactSecrets(m)); }",
    "function d(m: string) { proc.stderr.end(m); }",
    "function e(m: string) { console.error(m); }",
    "function f(m: string) { console.warn(redactSecrets(m), m); }",
    "function g(m: string) { console[\"trace\"](redactSecrets(m)); }",
    "function h(m: string) { con.assert(false, redactSecrets(m)); }",
    "function i(m: string) { globalThis.console.error(\"前缀 \" + redactSecrets(m)); }",
    "function j(m: string) { fs.writeSync(2, redactSecrets(m)); }",
    "function k(m: string) { fs.writeFileSync(0x2, m); }",
    "function l(m: string) { fs.promises.appendFile(2, redactSecrets(m) + m); }",
    "class C { warn(m: string) { process.stderr.write(redactSecrets(m)); } }",
    "const late = (m: string) => process.stderr.write(m);",
  ]);
  assert.deepEqual(scanned.writes.map((w) => [w.line, w.scope, w.form, w.redacted]), [
    [7, "a", "process.stderr.write", true], [8, "b", "process.stderr.write", true], [9, "c", "process.stderr.write", true],
    [10, "d", "process.stderr.end", false], [11, "e", "console.error", false], [12, "f", "console.warn", false],
    [13, "g", "console.trace", true], [14, "h", "console.assert", true], [15, "i", "console.error", true],
    [16, "j", "writeSync(2, ...)", true], [17, "k", "writeFileSync(2, ...)", false], [18, "l", "appendFile(2, ...)", false],
    [19, "C.warn", "process.stderr.write", true], [20, "late", "process.stderr.write", false],
  ]);
  assert.deepEqual(scanned.unregistrable, []);
});

test("检测函数在构造的片段上不把 stdout、变量文件描述符、类型位置与子进程的 stderr 计入", () => {
  const scanned = fragment([
    "import fs from \"node:fs\";",
    "import { spawnSync } from \"node:child_process\";",
    "process.stdout.write(m);",
    "console.log(m); console.info(m); console.debug(m);",
    "fs.writeSync(1, m);",
    "fs.writeSync(fd, m);",
    "type W = typeof process.stderr.write;",
    "type C = typeof console;",
    "const { stderr } = spawnSync(\"x\");",
    "const pick = (s: { stderr: string }) => s.stderr;",
    "const env = process.env.GHERKAI_STEPS_DIR;",
    "const { env: e2 } = process;",
    "const opts = { fd: 1, console: false };",
  ]);
  assert.deepEqual(scanned.writes, []);
  assert.deepEqual(scanned.unregistrable, []);
});

test("检测函数在构造的片段上核对写入实参的形状：只认 redactSecrets 的调用与字符串字面量拼成的实参", () => {
  const args: ReadonlyArray<readonly [string, boolean]> = [
    ["redactSecrets(m)", true],
    ["redactSecrets(m) + \"\\n\"", true],
    ["\"前缀 \" + redactSecrets(m) + \"\\n\"", true],
    ["`${redactSecrets(m)}\\n`", true],
    ["(redactSecrets(m) as string) + `\\n`", true],
    ["m", false],
    ["redactSecrets(m) + n", false],
    ["`${m}\\n`", false],
    ["`${redactSecrets(m)}${m}`", false],
    ["\"\\n\"", false],
    ["String(redactSecrets(m))", false],
    ["tag`${redactSecrets(m)}`", false],
  ];
  const scanned = fragment([
    "import { redactSecrets } from \"../lib/redact.mjs\";",
    ...args.map(([arg]) => `process.stderr.write(${arg});`),
  ]);
  assert.deepEqual(scanned.writes.map((w) => w.redacted), args.map(([, redacted]) => redacted));
});

test("检测函数在构造的片段上只认从 lib/redact.mts 导入的 redactSecrets，文件里另行绑定这个名字即报", () => {
  const other = fragment([
    "import { redactSecrets } from \"../device/redact.mjs\";",
    "function a(m: string) { process.stderr.write(redactSecrets(m)); }",
  ]);
  assert.deepEqual(other.writes.map((w) => w.redacted), [false]);
  const dynamic = fragment([
    "const { redactSecrets: mask } = await import(\"./lib/redact.mjs\");",
    "process.stderr.write(mask(`worker fatal: ${e}`) + \"\\n\");",
  ], "bin.mts");
  assert.deepEqual(dynamic.writes.map((w) => [w.scope, w.redacted]), [["(module)", true]]);
  const shadowed = fragment([
    "import { redactSecrets } from \"../lib/redact.mjs\";",
    "function a(m: string) { const redactSecrets = (s: string) => s; process.stderr.write(redactSecrets(m)); }",
    "function b(redactSecrets: (s: string) => string) { return redactSecrets; }",
  ]);
  assert.deepEqual(shadowed.unregistrable.map((u) => [u.line, u.scope, u.form]), [
    [2, "a", "在文件里另行绑定 redactSecrets"], [3, "b", "在文件里另行绑定 redactSecrets"],
  ]);
});

test("检测函数在构造的片段上把无法登记的写法逐一报出", () => {
  const cases: ReadonlyArray<readonly [string, string]> = [
    ["const out = process.stderr; out.write(m);", "process.stderr 不以 .write(...) 或 .end(...) 直接写出"],
    ["const w = process.stderr.write.bind(process.stderr);", "process.stderr 不以 .write(...) 或 .end(...) 直接写出"],
    ["if (process.stderr.isTTY) {}", "process.stderr 不以 .write(...) 或 .end(...) 直接写出"],
    ["sink(process.stderr);", "process.stderr 不以 .write(...) 或 .end(...) 直接写出"],
    ["const { stderr } = process;", "解构取出 process.stderr"],
    ["const { stderr: e } = globalThis.process;", "解构取出 process.stderr"],
    ["({ stderr: e } = process);", "解构取出 process.stderr"],
    ["function f({ stderr } = process) {}", "解构取出 process.stderr"],
    ["const { ...rest } = process;", "以剩余元素解构 process"],
    ["import { stderr } from \"node:process\";", "从 node:process 导入 stderr"],
    ["import { emitWarning as w } from \"process\";", "从 process 导入 emitWarning"],
    ["process.emitWarning(m);", "process.emitWarning"],
    ["process._rawDebug(m);", "process._rawDebug"],
    ["process[key].write(m);", "以计算出的名字取 process 的成员"],
    ["const c = console;", "把 console 对象当作值使用"],
    ["const deps = { logger: console };", "把 console 对象当作值使用"],
    ["const opts = { console };", "把 console 对象当作值使用"],
    ["const g = globalThis.console;", "把 console 对象当作值使用"],
    ["const logFn = console.error;", "把 console.error 当作值使用"],
    ["console[level](m);", "以计算出的名字取 console 的成员"],
    ["const c = new console.Console({ stdout: process.stdout });", "新建 Console 实例"],
    ["import { error } from \"node:console\";", "从 node:console 导入 error"],
    ["import { Console } from \"console\";", "从 console 导入 Console"],
    ["const p = await import(\"node:process\");", "动态加载 node:process"],
    ["const c = require(\"console\");", "动态加载 console"],
    ["const s = fs.createWriteStream(null as any, { fd: 2 });", "以 { fd: 2 } 建流或打开文件描述符 2"],
    ["const t = new tty.WriteStream(2);", "以文件描述符 2 建流（WriteStream）"],
    ["const fd = fs.openSync(\"/dev/stderr\", \"w\");", "按路径打开标准错误（/dev/stderr）"],
    ["fs.appendFileSync(\"/proc/self/fd/2\", m);", "按路径打开标准错误（/proc/self/fd/2）"],
    ["const d = util.debuglog(\"x\");", "util.debuglog"],
    ["import { debuglog } from \"node:util\";", "从 node:util 导入 debuglog"],
  ];
  for (const [snippet, form] of cases) {
    const scanned = fragment([snippet]);
    assert.ok(scanned.unregistrable.some((u) => u.form.startsWith(form)),
      `${snippet} 应报出「${form}」，实际 ${JSON.stringify(scanned.unregistrable)}`);
  }
});

// ---- 真实 src ----

test("扫描面：src/ 下的源文件都被扫到，测试文件不在其中", () => {
  const files = [...realSources().keys()];
  for (const known of ["bin.mts", "lib/artifact-upload.mts", "lib/redact.mts", "worker/evidence.mts", "worker/run-scope.mts",
    "worker/user-steps.mts", "device/surface.mts", "device/wdio-log.mts", "device/adapters/xcuitest.mts"]) {
    assert.ok(files.includes(known), `扫描面缺少 ${known}`);
  }
  assert.ok(files.every((f) => !f.endsWith(".test.mts")));
});

test("正向对照：真实 src 里写 stderr 的出口恰为登记的五处，各自恰有一个声明、每处写入都经过 redactSecrets", () => {
  const vs = violations(realSources());
  assert.deepEqual(vs, [], `写 stderr 的出口有变化：新出口的写入实参要经 redactSecrets，并登记进本文件的 STDERR_OUTLETS。\n${describe(vs)}`);
  const { outlets } = outletsOf(realSources());
  assert.deepEqual(outlets.map((o) => keyOf(o.rel, o.scope)).sort(), [...REGISTERED].sort());
  for (const o of outlets) {
    assert.equal(o.decls.size, 1, keyOf(o.rel, o.scope));
    assert.ok(o.writes.length > 0 && o.writes.every((w) => w.redacted), keyOf(o.rel, o.scope));
  }
});

test("拒绝：新加一处 process.stderr.write 不经脱敏，未登记与未脱敏都判出", () => {
  const vs = violations(withSource("worker/run-scope.mts", null, "function warn(m: string): void { process.stderr.write(m + \"\\n\"); }"));
  assert.ok(has(vs, UNREGISTERED, "worker/run-scope.mts", "warn"), describe(vs));
  assert.ok(has(vs, UNREDACTED, "worker/run-scope.mts", "warn"), describe(vs));
});

test("拒绝：经别名 const out = process.stderr 后再写出，判为无法登记的写法", () => {
  const vs = violations(withSource("worker/run-scope.mts", null,
    "function warn(m: string): void { const out = process.stderr; out.write(redactSecrets(m)); }"));
  assert.ok(has(vs, UNREGISTRABLE, "worker/run-scope.mts", "warn"), describe(vs));
});

test("拒绝：新加一处 console.error，未登记与未脱敏都判出", () => {
  const vs = violations(withSource("lib/job-source.mts", null, "export function warn(m: string): void { console.error(m); }"));
  assert.ok(has(vs, UNREGISTERED, "lib/job-source.mts", "warn"), describe(vs));
  assert.ok(has(vs, UNREDACTED, "lib/job-source.mts", "warn"), describe(vs));
});

test("拒绝：新加的出口即使经过脱敏也要先登记，类里与登记出口同名的方法不并入模块级函数", () => {
  const vs = violations(withSource("worker/run-scope.mts", null,
    "class Probe { log(m: string): void { process.stderr.write(redactSecrets(m) + \"\\n\"); } }"));
  assert.ok(has(vs, UNREGISTERED, "worker/run-scope.mts", "Probe.log"), describe(vs));
  assert.ok(!vs.some((v) => v.kind === UNREDACTED), describe(vs));
});

/** 每处登记出口的写出语句与去掉 redactSecrets 之后的写法。 */
const STRIPPED: ReadonlyArray<readonly [string, string, string, string]> = [
  ["bin.mts", "(module)", "process.stderr.write(redactSecrets(`worker fatal: ${e}`) + \"\\n\")",
    "process.stderr.write(`worker fatal: ${e}` + \"\\n\")"],
  ["lib/artifact-upload.mts", "ArtifactUploader.logFn", "process.stderr.write(redactSecrets(m) + \"\\n\")", "process.stderr.write(m + \"\\n\")"],
  ["worker/evidence.mts", "stepEvidenceRef", "process.stderr.write(redactSecrets(m) + \"\\n\")", "process.stderr.write(m + \"\\n\")"],
  ["worker/run-scope.mts", "log", "process.stderr.write(redactSecrets(msg) + \"\\n\")", "process.stderr.write(msg + \"\\n\")"],
  ["worker/user-steps.mts", "loadUserSteps", "process.stderr.write(redactSecrets(m) + \"\\n\")", "process.stderr.write(m + \"\\n\")"],
];

test("拒绝：登记的每处出口去掉 redactSecrets 都判出（含 evidence 的缺省 logFn）", () => {
  assert.deepEqual(STRIPPED.map(([rel, scope]) => keyOf(rel, scope)).sort(), [...REGISTERED].sort(), "每处登记出口都要有一条去掉脱敏的用例");
  for (const [rel, scope, old, stripped] of STRIPPED) {
    const vs = violations(withSource(rel, old, stripped));
    assert.ok(has(vs, UNREDACTED, rel, scope), `${keyOf(rel, scope)} 去掉 redactSecrets 应判出：\n${describe(vs)}`);
    assert.ok(!vs.some((v) => v.kind === UNREGISTERED || v.kind === GONE), describe(vs));
  }
});

test("拒绝：登记的出口改写到 stdout 后判为不再写 stderr", () => {
  const vs = violations(withSource("worker/run-scope.mts", "process.stderr.write(redactSecrets(msg) + \"\\n\")",
    "process.stdout.write(redactSecrets(msg) + \"\\n\")"));
  assert.ok(has(vs, GONE, "worker/run-scope.mts", "log"), describe(vs));
});

test("拒绝：模块末尾再定义一个同名的 log，判为同一个名字有多个声明", () => {
  const vs = violations(withSource("worker/run-scope.mts", null, "function log(m: string): void { process.stderr.write(redactSecrets(m)); }"));
  assert.ok(has(vs, DUPLICATE, "worker/run-scope.mts", "log"), describe(vs));
});

test("拒绝：登记出口所在的函数里另行绑定 redactSecrets，判为无法登记的写法", () => {
  const vs = violations(withSource("worker/run-scope.mts", "function log(msg: string): void {",
    "function log(msg: string): void {\n  const redactSecrets = (s: string): string => s;"));
  assert.ok(has(vs, UNREGISTRABLE, "worker/run-scope.mts", "log"), describe(vs));
});
