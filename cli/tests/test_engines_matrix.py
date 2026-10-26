"""引擎能力矩阵（docs/user-guide/engines.md）的差集护栏（ADR 0049 决策 8）——Nova 侧与表格结构。

真值集是 worker 在无环境变量覆盖时的能力自述：目标列对 `targets`、默认模型列对 `model_id`、句柄列由目标按 ADR 0050
决策 1 的固定规则推出（desktop → playwright，设备 → webdriver）。本文件真起 Nova worker 子进程核它那几行；Midscene 的行由
engines/midscene/src/worker/engines-matrix.test.mts 在 npm 测试里真起 Midscene worker 核（pytest 的 CI job 装不出 Midscene
的 dist，分开核才不会被跳过）。两侧共同覆盖「多一行、少一行、值不符都失败」。计价公式列没有机读真值，不在此核。
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

from gherkai_cli.render import target_label
from gherkai_runtime import names

REPO = Path(__file__).resolve().parents[2]
MATRIX = REPO / "docs" / "user-guide" / "engines.md"
HANDLE_BY_DEVICE = {"desktop": "playwright", "android": "webdriver", "ios": "webdriver"}  # ADR 0050 决策 1 的固定规则


def matrix_rows() -> list[dict]:
    """解析 engines.md 里以「| 引擎 |」开头的那张表：每行 {engine, target, handle, model}。"""
    lines = MATRIX.read_text(encoding="utf-8").splitlines()
    start = next(i for i, ln in enumerate(lines) if ln.startswith("| 引擎 |"))
    rows: list[dict] = []
    for ln in lines[start + 2:]:
        if not ln.startswith("|"):
            break
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        code = re.search(r"`([a-z]+)`", cells[0])
        handle = re.search(r"`([a-z]+)`", cells[2])
        model = re.search(r"`([^`]+)`", cells[3])
        assert code and handle and model, f"矩阵行形态不对（引擎 / 句柄 / 模型都应放在反引号里）：{ln}"
        rows.append({"engine": code.group(1), "target": cells[1], "handle": handle.group(1), "model": model.group(1)})
    return rows


def expected_rows(caps: dict) -> list[dict]:
    """由一份自述推出该引擎应有的矩阵行（一行一个目标，按 targets 顺序、ui_kinds 顺序）。"""
    return [{"engine": caps["engine"], "target": target_label(t["device"], k), "handle": HANDLE_BY_DEVICE[t["device"]],
             "model": caps["model_id"]}
            for t in caps["targets"] for k in t["ui_kinds"]]


def test_matrix_lists_exactly_the_two_engines():
    """表里的引擎集合与产品的引擎集合相等：少一个引擎的行、或多出一个不存在的引擎名都失败。"""
    assert {r["engine"] for r in matrix_rows()} == set(names.ENGINES)


def test_matrix_target_names_are_the_product_labels():
    """目标列只能用产品语言名称（render.target_label 产出的那一套）：Midscene 行由 npm 侧按手抄的名称映射核，这里把两侧
    名称拼法钉在同一来源上，改了 render 的名称而没改矩阵或 TS 测试里的副本时在此失败。"""
    labels = {target_label(d, k) for d in ("desktop", "android", "ios") for k in ("web", "app")} - {target_label("desktop", "app")}
    for r in matrix_rows():
        assert r["target"] in labels, f"矩阵目标名 {r['target']!r} 不是产品名称之一：{sorted(labels)}"


def test_matrix_rows_for_novaact_match_the_worker_self_description():
    """Nova 行逐行对照真子进程的自述（剥掉 NOVA_* / GHERKAI_* / AWS_* 等覆盖，取无覆盖时的默认值）。"""
    keep = ("PATH", "PYTHONPATH", "PYTHONHOME", "HOME", "TMPDIR", "LANG", "LC_ALL", "SYSTEMROOT", "VIRTUAL_ENV")
    env = {k: v for k, v in os.environ.items() if k in keep}
    env["AWS_EC2_METADATA_DISABLED"] = "true"
    proc = subprocess.run([sys.executable, "-m", "gherkai_worker_novaact", "--capabilities"],
                          capture_output=True, timeout=60, env=env)
    assert proc.returncode == 0, proc.stderr.decode()[-500:]
    caps = json.loads(proc.stdout.decode("utf-8"))
    assert caps["engine"] == "novaact"
    documented = [r for r in matrix_rows() if r["engine"] == "novaact"]
    assert documented == expected_rows(caps), (
        "docs/user-guide/engines.md 的 Nova Act 行与 worker 自述不一致（多一行、少一行或值不符）：\n"
        f"文档：{documented}\n自述推出：{expected_rows(caps)}")
