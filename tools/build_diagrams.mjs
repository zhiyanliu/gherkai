#!/usr/bin/env node
// docs 图的两段式构建（ADR 0045 决策七）：
//   ① 渲染  JSON 图源 --archify deliver--> 可交互 HTML   纯 CLI、确定性、无 LLM；Pages 上暴露的就是它，CI 也运行同一条命令
//   ② 导出  HTML --headless Chrome 点导出菜单--> SVG      只为嵌进 markdown 的静态图；可选再导 PNG 供目视检查
// 作者化（写 JSON）是唯一需要智能的一步，由 AI 在 push 前完成，本脚本不碰。
//
// 为什么要脚本化第 ② 段：archify 的导出是 viewer 页面里的菜单动作、CLI 没有导出子命令，十几张图每次改动都手点一遍
// 不现实，所以用 Playwright 驱动本机 Chrome 打开交付好的 HTML、点导出菜单项、接住下载、核对回执。
//
// 依赖与脆弱点（明知的取舍）：
// - archify 住 ~/.agents/skills/archify（可用 ARCHIFY_HOME 覆盖）；Playwright 复用 engines/midscene 的 node_modules
//   （先在那里 `npm ci`），浏览器用本机 Chrome（channel: "chrome"），不下载。
// - 导出靶点是 viewer 内部结构：`button[data-format="svg"|"png"]` 与 `<html data-last-export-*>` 回执属性。
//   archify skill 升级后这些名字可能变——脚本会响亮失败（找不到按钮 / 回执不符），届时对照新版 HTML 改这两处即可。
//
// 用法：
//   node tools/build_diagrams.mjs                       # docs/diagrams/*.json 全部：① 渲染 + ② 导出 SVG
//   node tools/build_diagrams.mjs docs/diagrams/x.json  # 只做这几张
//   node tools/build_diagrams.mjs --png                 # 另导 PNG（只供目视检查，不入库）
//   node tools/build_diagrams.mjs --no-deliver          # 跳过 ①，只从现有 HTML 导出
//   node tools/build_diagrams.mjs --html some.html      # 只导出一个现成 HTML（不需要 JSON）
//   node tools/build_diagrams.mjs --dir <目录>          # 换图源目录（缺省 docs/diagrams）
// 退出码：0 全成；1 有失败（逐张打出原因）。入库的是 JSON 与 SVG（同 commit）；HTML 只对发布到 Pages 的图入库。
// 导出的 SVG 末尾带一行图源 sha256 指纹注释，护栏与 hook 靠它判「改了 JSON 没重导」。
import { createRequire } from 'node:module';
import { spawnSync } from 'node:child_process';
import { appendFileSync, existsSync, readFileSync, readdirSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { homedir } from 'node:os';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const REPO = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const ARCHIFY = process.env.ARCHIFY_HOME || path.join(homedir(), '.agents', 'skills', 'archify');
const DEFAULT_DIR = path.join(REPO, 'docs', 'diagrams');

const args = process.argv.slice(2);
const flag = (name) => { const i = args.indexOf(name); if (i >= 0) { args.splice(i, 1); return true; } return false; };
const wantPng = flag('--png');
const noDeliver = flag('--no-deliver');
const htmlOnly = (() => { const i = args.indexOf('--html'); if (i >= 0) { const v = args[i + 1]; args.splice(i, 2); return v; } return null; })();
const dirIdx = args.indexOf('--dir');
const dir = dirIdx >= 0 ? path.resolve(args.splice(dirIdx, 2)[1]) : DEFAULT_DIR;

function deliver(jsonPath, htmlPath) {
  const spec = JSON.parse(readFileSync(jsonPath, 'utf8'));
  const type = spec.diagram_type;
  if (!type) throw new Error(`${jsonPath} 缺 diagram_type`);
  const cli = path.join(ARCHIFY, 'bin', 'archify.mjs');
  if (!existsSync(cli)) throw new Error(`找不到 archify：${cli}（设 ARCHIFY_HOME）`);
  const r = spawnSync('node', [cli, 'deliver', type, jsonPath, htmlPath, '--quality', 'showcase', '--json'], { encoding: 'utf8' });
  if (r.status !== 0) throw new Error(`archify deliver 失败（exit ${r.status}）：\n${(r.stderr || r.stdout || '').slice(-1500)}`);
  return type;
}

// 导出的 SVG 末尾追加图源指纹（XML 允许根元素之后有注释；浏览器与 GitHub 的 <img> 都照常渲染）。
// 用途：CI 与 hook 不只靠 mtime（git checkout 后 mtime 无意义）也能判「JSON 改了、SVG 没重导」——
// cli/tests/test_user_docs.py 逐张比对 sha256(json) 与这行指纹（ADR 0045 决策七）。
function sourceFingerprint(jsonPath) {
  return createHash('sha256').update(readFileSync(jsonPath)).digest('hex');
}
function stampWith(svgPath, hex) {
  appendFileSync(svgPath, `\n<!-- gherkai:source-sha256=${hex} -->\n`);
}
function stampSource(svgPath, jsonPath) {
  stampWith(svgPath, sourceFingerprint(jsonPath));
}
// 读回既有 SVG 尾部那行指纹（没有 SVG、或它没盖过指纹，返回 null）。
function readStampedFingerprint(svgPath) {
  if (!existsSync(svgPath)) return null;
  const m = readFileSync(svgPath, 'utf8').slice(-4096).match(/gherkai:source-sha256=([0-9a-f]{64})/);
  return m ? m[1] : null;
}

async function exportFrom(page, htmlPath, format, outPath) {
  await page.goto(pathToFileURL(htmlPath).href, { waitUntil: 'load' });
  const selector = `button[data-format="${format}"]`;
  await page.waitForSelector(selector, { state: 'attached', timeout: 15000 });
  const download = page.waitForEvent('download', { timeout: 60000 });
  await page.evaluate((sel) => document.querySelector(sel).click(), selector);
  const d = await download;
  await d.saveAs(outPath);
  const receipt = await page.evaluate(() => {
    const h = document.documentElement;
    return { format: h.getAttribute('data-last-export-format'), canonical: h.getAttribute('data-last-export-canonical'), bytes: h.getAttribute('data-last-export-bytes'), error: h.getAttribute('data-last-export-error') };
  });
  if (receipt.error) throw new Error(`viewer 报导出错误：${receipt.error}`);
  if (receipt.format !== format) throw new Error(`回执格式 ${receipt.format} ≠ ${format}`);
  if (receipt.canonical !== 'true') throw new Error('回执 canonical=false：导出时 viewer 状态不干净');
  return receipt;
}

async function main() {
  const require = createRequire(import.meta.url);
  let chromium;
  try { ({ chromium } = require(path.join(REPO, 'engines', 'midscene', 'node_modules', 'playwright'))); }
  catch { console.error('需要 Playwright：先在 engines/midscene 里 npm ci'); return 1; }

  const jobs = [];
  if (htmlOnly) {
    const html = path.resolve(htmlOnly);
    jobs.push({ json: null, html, stem: html.replace(/\.html$/, '') });
  } else {
    const jsons = args.length ? args.map((a) => path.resolve(a)) : readdirSync(dir).filter((f) => f.endsWith('.json')).map((f) => path.join(dir, f));
    for (const json of jsons) jobs.push({ json, html: json.replace(/\.json$/, '.html'), stem: json.replace(/\.json$/, '') });
  }
  if (!jobs.length) { console.error(`没有可处理的图（目录 ${dir}）`); return 1; }

  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  const context = await browser.newContext({ acceptDownloads: true, viewport: { width: 1600, height: 1000 } });
  const page = await context.newPage();
  const failures = [];
  for (const job of jobs) {
    const name = path.relative(REPO, job.stem);
    try {
      let type = '';
      if (job.json && !noDeliver) type = deliver(job.json, job.html);
      if (!existsSync(job.html)) throw new Error(`没有 HTML：${job.html}（先 deliver）`);
      // --no-deliver 复用旧 HTML，导出的图形来自旧图源，指纹必须沿用旧的，否则会把「改了图源没重导」盖成绿
      //（ADR 0045 决策七的护栏）。沿用值只能在导出覆写 SVG 之前读出来。
      const carried = job.json && noDeliver ? readStampedFingerprint(`${job.stem}.svg`) : null;
      const svg = await exportFrom(page, job.html, 'svg', `${job.stem}.svg`);
      let note = '';
      if (carried) {
        stampWith(`${job.stem}.svg`, carried);
        note = '  指纹沿用旧 SVG（--no-deliver 没重渲染 HTML，导出的图形仍来自旧图源）';
      } else if (job.json) {
        stampSource(`${job.stem}.svg`, job.json);
        if (noDeliver) note = '  指纹按当前 JSON 算（旧 SVG 没有可沿用的指纹）';
      }
      let line = `ok   ${name}${type ? ` [${type}]` : ''}  svg ${svg.bytes} B${note}`;
      if (wantPng) { const png = await exportFrom(page, job.html, 'png', `${job.stem}.png`); line += `  png ${png.bytes} B`; }
      console.log(line);
    } catch (e) {
      failures.push(`${name}: ${e.message}`);
      console.log(`FAIL ${name}`);
    }
  }
  await browser.close();
  console.log(`\n${jobs.length} 张，${failures.length} 失败`);
  for (const f of failures) console.error(`\n${f}`);
  return failures.length ? 1 : 0;
}

process.exitCode = await main();
