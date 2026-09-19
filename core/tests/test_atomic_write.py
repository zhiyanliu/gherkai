"""共享原子落盘助手（`gherkai_core.adapters._atomic`）的通用性质：并发读者只看到完整内容、权限按声明、失败不留 tmp。

三个 local adapter（RunStore 控制面 / ResultStore 数据面 / ReportStore 报告面）共用它，故原子性与权限在此
统一锁定一次；各 adapter 自己的用例只覆盖自己的落点与内容。文本面（index.html）与 JSON 面都要覆盖——只验
`json.loads` 失败会漏掉 HTML 那一半（HTML 读者靠「非空且以 </html> 收尾」判完整）。

真起子进程读、不 mock（绿≠对：进程间文件可见性是 mock 之外的真实行为）。
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

import pytest

from gherkai_core.adapters._atomic import atomic_write_json, atomic_write_text

_HTML_READER = r"""
import json, sys, pathlib
p = pathlib.Path(sys.argv[1]); stop = pathlib.Path(sys.argv[2])
reads = empty = truncated = 0
while not stop.exists():
    try:
        raw = p.read_text(encoding="utf-8")
    except FileNotFoundError:
        continue
    reads += 1
    if raw == "":
        empty += 1
    elif not raw.endswith("</html>"):
        truncated += 1
print(json.dumps({"reads": reads, "empty": empty, "truncated": truncated}))
"""


def _page(tick: int) -> str:
    """报告 index.html 量级（几十 KB）的页面：内容长度随 tick 变，防「两次写恰好等长」掩盖撕裂。"""
    rows = "".join(f"<li>run {tick} · 第 {i} 行 · {'产物 ' * 10}</li>" for i in range(400 + tick % 7))
    return f"<!doctype html><html><body><ul>{rows}</ul></body></html>"


def test_concurrent_reader_never_sees_empty_or_truncated_text(tmp_path):
    path = tmp_path / "index.html"
    atomic_write_text(path, _page(0))  # 先落一份，让读者从第一拍就有文件可读
    assert path.stat().st_size > 20_000, path.stat().st_size  # 够大才有撞窗机会（否则用例无判别力）
    stop = tmp_path / "stop"
    reader = subprocess.Popen([sys.executable, "-c", _HTML_READER, str(path), str(stop)],
                              stdout=subprocess.PIPE, text=True)
    try:
        for tick in range(1, 300):
            atomic_write_text(path, _page(tick))
    finally:
        stop.touch()
        out, _ = reader.communicate(timeout=30)
    stats = json.loads(out)
    assert stats["reads"] >= 10, stats  # 读者确实在写的期间反复读到了（否则本用例空转）
    assert stats["empty"] == 0, stats      # truncate 窗口：write_text 写法在此处会计出非 0
    assert stats["truncated"] == 0, stats  # 写了一半的页面
    assert path.read_text(encoding="utf-8") == _page(299)
    assert not list(tmp_path.glob("*.tmp"))


def test_json_round_trip_and_default_mode_readable_by_others(tmp_path):
    """默认权限给 group/other 读：判定真值与报告产物的消费者是 CI/人/静态 server（ADR 0034 / 0027），
    而 tmp 文件本身是 0600——不显式 chmod 就会静默变 owner-only。"""
    path = tmp_path / "manifest.json"
    atomic_write_json(path, {"schema_version": 1, "中文": ["a", 2]})
    assert json.loads(path.read_text(encoding="utf-8")) == {"schema_version": 1, "中文": ["a", 2]}
    assert path.read_text(encoding="utf-8").startswith("{\n  ")  # indent=2，与全仓落盘口径一致
    assert "中文" in path.read_text(encoding="utf-8")            # ensure_ascii=False
    assert path.stat().st_mode & 0o044, oct(path.stat().st_mode & 0o777)


def test_mode_can_be_narrowed(tmp_path):
    """控制面（run_meta/run_state）要 0600：调用方声明的 mode 必须被照落，别被默认值顶掉。"""
    path = tmp_path / "run_state.json"
    atomic_write_json(path, {"run_id": "r1"}, mode=0o600)
    assert path.stat().st_mode & 0o777 == 0o600, oct(path.stat().st_mode & 0o777)


def test_target_name_at_name_max_still_writable(tmp_path):
    """目标名顶到文件名长度上限时也要写得进：tmp 名不许比目标名长出一截。

    per-scope 结果文件名由 scope_id percent-encode 而来（scope_id 是不透明标识符、显式允许中文，
    每字 9 字符，ADR 0025「id 派生」），落点名会顶到上限。tmp 名若在完整目标名后再接随机段与后缀，
    「非原子写时写得进」的落点会在建 tmp 时就 ENAMETOOLONG——而这条落盘路径上抛异常会掀掉整个 run
    （结果落盘失败即停全部 worker 并重抛，ADR 0030）。
    """
    name_max = os.pathconf(str(tmp_path), "PC_NAME_MAX")
    path = tmp_path / ("x" * (name_max - len(".json")) + ".json")
    assert len(path.name) == name_max, len(path.name)
    atomic_write_json(path, {"scope_id": "顶到上限的落点名"})
    assert json.loads(path.read_text(encoding="utf-8")) == {"scope_id": "顶到上限的落点名"}
    assert not list(tmp_path.glob("*.tmp"))


def test_failed_replace_leaves_no_tmp_behind(tmp_path):
    """写失败（这里让目标是个目录，os.replace 必炸）时 tmp 要清掉、异常照常冒泡——不留残骸给 glob 到。"""
    target = tmp_path / "occupied"
    target.mkdir()
    with pytest.raises(OSError):
        atomic_write_text(target, "x")
    assert not list(tmp_path.glob("*.tmp"))
