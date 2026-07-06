"""act 边界抢传单测（ADR 0029「act 边界抢传」，为 Fargate 预演——subprocess+cloud 先建好并验证）。

验 `_presend_act_siblings`：在 step_done 安全点，把本 step 各 act 的配套 `_trajectory.json` 也即时上传
（不等 scope 末 flush）——中断落 flush 前时（Fargate 盘销毁）这些 json 才不丢。

与 test_run_step.py 同风格：注 fake nova / spy uploader、不连 AWS。重点护 ADR 0029：
- 抢传配套 json（.html 反推 _trajectory.json）；json 不进 reportRefs（只 .html 进）。
- 复用幂等 to_report_ref（distinct key）；best-effort（失败吞、不打断 step）。
- no-op（未注入落点）时不抢传、不抛。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_scope as rs


class _SpyUploader:
    """记录 to_report_ref 被调的路径（验抢传）；enabled 可控 no-op。"""
    def __init__(self, *, enabled=True, fail_paths=()):
        self.enabled = enabled
        self.calls = []
        self._fail = set(fail_paths)

    def to_report_ref(self, path):
        self.calls.append(path)
        if path in self._fail:
            raise RuntimeError(f"s3 fail: {path}")
        return f"s3://bkt/{Path(path).name}" if self.enabled else f"file://{path}"


def _make_act_pair(tmp_path, name="act_0"):
    """造一对 act 产物（.html + 配套 _trajectory.json），返回 (html 路径, json 路径)。"""
    html = tmp_path / f"{name}.html"; html.write_text("<html>traj</html>")
    js = tmp_path / f"{name}_trajectory.json"; js.write_text("{}")
    return str(html), str(js)


# ---- 抢传：step_traj 里每个 .html 的配套 json 被 to_report_ref（distinct key）----
def test_presend_uploads_sibling_json(tmp_path, monkeypatch):
    html, js = _make_act_pair(tmp_path)
    spy = _SpyUploader()
    monkeypatch.setattr(rs, "_uploader", spy)
    rs._presend_act_siblings([html])
    # 配套 json 被抢传（abspath 形式）
    assert any(c.endswith("_trajectory.json") for c in spy.calls)
    assert str(Path(js).resolve()) in [str(Path(c).resolve()) for c in spy.calls]


# ---- json 不存在（如确定性 step 无 act 产物）→ 不抢传、不抛 ----
def test_presend_skips_when_no_sibling_json(tmp_path, monkeypatch):
    html = tmp_path / "act_0.html"; html.write_text("<html>x</html>")  # 只有 html、无配套 json
    spy = _SpyUploader()
    monkeypatch.setattr(rs, "_uploader", spy)
    rs._presend_act_siblings([str(html)])
    assert spy.calls == []  # 无配套 json → 不调


# ---- 非 .html 路径（防御）→ 跳过 ----
def test_presend_ignores_non_html(tmp_path, monkeypatch):
    spy = _SpyUploader()
    monkeypatch.setattr(rs, "_uploader", spy)
    rs._presend_act_siblings(["/logs/act_0_trajectory.json"])  # 传的是 json 本身、非 .html
    assert spy.calls == []


# ---- best-effort：抢传失败吞掉、不抛（不打断 step）----
def test_presend_swallows_upload_failure(tmp_path, monkeypatch):
    html, js = _make_act_pair(tmp_path)
    spy = _SpyUploader(fail_paths={str(Path(js).resolve()), js})
    monkeypatch.setattr(rs, "_uploader", spy)
    # 不抛（失败被吞）——若抛则测试 error
    rs._presend_act_siblings([html])
    assert any(c.endswith("_trajectory.json") for c in spy.calls)  # 试过传（即便失败）


# ---- 多 act（N 票）：每个 .html 的配套 json 都抢传 ----
def test_presend_all_act_siblings(tmp_path, monkeypatch):
    h0, j0 = _make_act_pair(tmp_path, "act_0")
    h1, j1 = _make_act_pair(tmp_path, "act_1")
    spy = _SpyUploader()
    monkeypatch.setattr(rs, "_uploader", spy)
    rs._presend_act_siblings([h0, h1])
    json_calls = [c for c in spy.calls if c.endswith("_trajectory.json")]
    assert len(json_calls) == 2  # 两个 act 的配套 json 都抢传
