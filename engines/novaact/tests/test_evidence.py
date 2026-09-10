"""step 级机读证据（evidence，ADR 0042 决策一/二/六）单测：映射 / 截图上界 / 目录键 / best-effort 钩子。

纯 python：不连 AWS、不起浏览器、不解真 SDK。映射由**真产物裁成的 fixture** 钉住
（`fixtures/nova_*_traj.json` = 真 `_trajectory.json`，base64 图裁成短前缀）——SDK 格式漂移在升版跑测试时变红
（ADR 0042 决策六防线 2）。钩子侧注 fake nova + fake sink（与 test_run_step.py 同风格）。
"""
from __future__ import annotations

import base64
import json
from pathlib import Path

import pytest

from gherkai_worker_novaact import evidence as ev
from gherkai_worker_novaact import run_scope as rs

FIXTURES = Path(__file__).parent / "fixtures"


def _fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


# ---- 映射：断言 act（act_get：think + return）----
def test_assert_fixture_maps_thought_result_url_vote():
    traj = _fixture("nova_assert_traj.json")
    rec = ev.ActRecord(index=0, prompt="当前页面是关于 OpenAI 的维基百科词条页", vote=False, time_worked_s=9.82)
    act = ev.act_evidence(rec, traj)
    assert len(act["frames"]) == 1
    frame = act["frames"][0]
    assert frame["thought"].startswith("I am on the Wikipedia page for OpenAI.")
    assert frame["actions"] == []                       # think/return 都不算动作
    assert frame["url"] == "https://en.wikipedia.org/wiki/OpenAI"
    assert frame["screenshot"] is None                  # 未被截图策略选中前一律 null
    assert act["result"] == {"value": "true"}           # return call 的 kwargs 原样
    assert act["url"] == "https://en.wikipedia.org/wiki/OpenAI"  # 末 frame 的 active_url
    assert act["vote"] is False                         # 票不从 result 反推（这里 result 看似为真、票记 no）
    assert act["error"] is None and act["time_worked_s"] == 9.82


def test_prompt_is_worker_instruction_not_sdk_rewritten_one():
    """SDK 在 act_get 的 prompt 尾部追加了 jsonschema 样板 → evidence 必须用 worker 自己那串（ADR 0042 决策六防线 1）。"""
    traj = _fixture("nova_assert_traj.json")
    assert "jsonschema" in traj["prompt"]               # 真产物如此（漂移即此断言先红）
    act = ev.act_evidence(ev.ActRecord(index=0, prompt="当前页面是关于 OpenAI 的维基百科词条页"), traj)
    assert act["prompt"] == "当前页面是关于 OpenAI 的维基百科词条页"
    assert "jsonschema" not in act["prompt"]


# ---- 映射：动作 act（act：think + agentType + waitForPageToSettle + takeObservation，两 frame）----
def test_act_fixture_maps_actions_by_name_and_last_frame_url():
    traj = _fixture("nova_act_traj.json")
    act = ev.act_evidence(ev.ActRecord(index=1, prompt="在搜索框输入 OpenAI 并提交搜索"), traj)
    assert len(act["frames"]) == 2
    assert [a["name"] for a in act["frames"][0]["actions"]] == [
        "agentType", "waitForPageToSettle", "takeObservation"]
    assert act["frames"][0]["actions"][0]["args"]["value"] == "OpenAI"     # args = kwargs 原样透传
    assert act["frames"][0]["url"] == "https://www.wikipedia.org/"
    assert act["frames"][1]["actions"] == []                              # 末 frame 只有 think + return
    assert act["result"] == {"value": ""}                                 # 末 frame 的 return
    assert act["url"] == "https://en.wikipedia.org/wiki/OpenAI"           # 末 frame，不是首 frame
    assert act["vote"] is None                                            # 动作 act 不投票
    assert act["time_worked_s"] == pytest.approx(26.921343088150024)      # 容缺回落读 json 的 metadata


def test_real_output_has_is_return_false_everywhere_so_we_map_by_name():
    """真产物里 `is_tool`/`is_return` 对所有 call 都是 False——按标志判会静默取空（ADR 0042 决策六防线 1）。"""
    for name in ("nova_assert_traj.json", "nova_act_traj.json"):
        for step in _fixture(name)["steps"]:
            for call in step["program"]["calls"]:
                assert call.get("is_tool") is False and call.get("is_return") is False
    # 而按 name 判仍取到了 return 与 actions（上面两个 test 已断言），故防线成立


# ---- error act 契约：抛错的 act 无 json → frames []，且不算抽取失败 ----
def test_missing_trajectory_json_reads_as_none(tmp_path):
    assert ev.read_trajectory(None) is None
    assert ev.read_trajectory(str(tmp_path / "act_9_trajectory.json")) is None  # SDK 抛错时不写 json
    bad = tmp_path / "bad_trajectory.json"
    bad.write_text("{ not json", encoding="utf-8")
    assert ev.read_trajectory(str(bad)) is None
    arr = tmp_path / "arr_trajectory.json"
    arr.write_text("[]", encoding="utf-8")
    assert ev.read_trajectory(str(arr)) is None                                # 非 dict 也当读不到


def test_error_act_keeps_prompt_and_cost_with_empty_frames():
    rec = ev.ActRecord(index=0, prompt="点击登录", error="ActTimeoutError: 超时", time_worked_s=12.0)
    act = ev.act_evidence(rec, None)
    assert act["frames"] == [] and act["url"] is None and act["result"] is None
    assert act["error"] == "ActTimeoutError: 超时"
    assert act["prompt"] == "点击登录" and act["time_worked_s"] == 12.0


# ---- 文档骨架：键名与 ADR 0042 决策一的 schema 逐字一致 ----
def test_step_evidence_schema_keys():
    doc = ev.step_evidence(
        scope_id="features/login.feature:6", scenario_id="features/login.feature:12", step_index=2,
        keyword="Then", text="页面显示「登录成功」", status="failed", message="AI 断言未过多数票（0/1）：…",
        acts=[ev.ActRecord(index=0, prompt="页面显示「登录成功」", vote=False)],
        trajectories=[_fixture("nova_assert_traj.json")])
    assert list(doc) == ["schema_version", "engine", "scope_id", "scenario_id", "step_index",
                         "step", "status", "message", "acts"]
    assert doc["schema_version"] == 1 and doc["engine"] == "novaact"
    assert doc["step"] == {"keyword": "Then", "text": "页面显示「登录成功」"}
    assert list(doc["acts"][0]) == ["index", "prompt", "vote", "url", "frames", "result",
                                    "error", "time_worked_s"]
    assert list(doc["acts"][0]["frames"][0]) == ["url", "thought", "actions", "screenshot"]


def test_missing_trajectory_for_an_act_is_tolerated():
    doc = ev.step_evidence(scope_id=None, scenario_id=None, step_index=0, keyword=None, text=None,
                           status="error", acts=[ev.ActRecord(index=0)], trajectories=[])
    assert doc["acts"][0]["frames"] == []


# ---- 截图选择的上界（ADR 0042 决策一 截图策略）----
def _synthetic(n_frames: int, thought_at=()) -> dict:
    """n 帧的合成 trajectory：thought_at 里的帧带 think call，每帧都有可解的 data URL 图。"""
    img = "data:image/jpeg;base64," + base64.b64encode(b"\xff\xd8\xff\xd9jpg").decode()
    steps = []
    for j in range(n_frames):
        calls = [{"name": "agentClick", "kwargs": {"box": f"<box>{j}</box>"}}]
        if j in thought_at:
            calls.insert(0, {"name": "think", "kwargs": {"value": f"thought {j}"}})
        steps.append({"active_url": f"https://x/{j}", "image": img, "program": {"calls": calls}})
    return {"steps": steps}


def _picks(status: str, trajs) -> list[tuple[int, int]]:
    acts = [ev.ActRecord(index=i) for i in range(len(trajs))]
    doc = ev.step_evidence(scope_id="s", scenario_id="sc:1", step_index=0, keyword="Then", text="t",
                           status=status, acts=acts, trajectories=trajs)
    return ev.select_screenshots(doc)


def test_passed_step_keeps_only_last_frame_per_act():
    assert _picks("passed", [_synthetic(5, thought_at=(1, 4)), _synthetic(3, thought_at=(0,))]) == [(0, 4), (1, 2)]


def test_failed_step_takes_last_frame_and_first_frame_with_thought():
    assert _picks("failed", [_synthetic(5, thought_at=(1, 4))]) == [(0, 4), (0, 1)]


def test_error_step_uses_same_bounds_as_failed():
    assert _picks("error", [_synthetic(3, thought_at=(2,))]) == [(0, 2)]  # 末帧即首个含 thought 帧 → 去重后一张


def test_no_thought_frames_yields_only_last_frame():
    assert _picks("failed", [_synthetic(4)]) == [(0, 3)]


def test_per_act_cap_is_three():
    # Nova 侧候选只有「末帧 + 首个含 thought 帧」两项（frame 无出错标记、抛错 act 更无 json）→ 不会超 K
    assert len(_picks("failed", [_synthetic(30, thought_at=tuple(range(30)))])) <= ev.MAX_SHOTS_PER_ACT


def test_per_step_cap_truncates_at_twelve():
    picks = _picks("failed", [_synthetic(5, thought_at=(1, 4)) for _ in range(9)])  # 9 act × 2 = 18 张候选
    assert len(picks) == ev.MAX_SHOTS_PER_STEP == 12
    assert picks[-1] == (5, 1)                       # 逐 act 依序取满即停（第 6 个 act 的第二张为止）
    assert not any(i >= 6 for i, _ in picks)


def test_empty_frames_act_contributes_no_screenshot():
    assert _picks("error", [None, _synthetic(2)]) == [(1, 1)]


# ---- scenario 键：确定性、不二次撞名、不用显示名（ADR 0042 决策一）----
def test_scenario_key_is_deterministic_and_escapes_separators():
    k = ev.scenario_key("features/login.feature:12")
    assert k == ev.scenario_key("features/login.feature:12")
    assert "/" not in k and ":" not in k and " " not in k


def test_scenario_key_no_collision_after_escaping():
    """转义会把这两个 id 压成同一串（uri 里的分隔符差异），短哈希把它们分开——撞了 = evidence 静默互相覆盖。"""
    a = ev.scenario_key("features/login.feature:12")
    b = ev.scenario_key("features-login.feature-12")
    assert a != b
    assert ev.scenario_key("a/b:1:2") != ev.scenario_key("a/b:1-2")


def test_scenario_key_survives_non_ascii_and_empty_ids():
    assert ev.scenario_key("特性/登录.feature:12") != ev.scenario_key("特性/登录.feature:13")
    assert ev.scenario_key("") and ev.scenario_key(None)     # 容缺：至少给出哈希段
    assert ev.scenario_key("///") not in (".", "..", "")      # 不产出危险目录名


def test_scenario_key_does_not_use_display_name():
    """同一份显示名可属不同 scenario（同文件重名 / @scope 跨文件合并）→ 键只由 id 派生。"""
    assert ev.scenario_key("features/a.feature:3") != ev.scenario_key("features/b.feature:3")


# ---- 落盘：目录形态 + 截图文件名 + 只有被选中的 frame 带 URI ----
def test_write_step_evidence_layout_and_screenshots(tmp_path):
    traj_path = tmp_path / "act_0_trajectory.json"
    traj_path.write_text(json.dumps(_synthetic(5, thought_at=(1, 4))), encoding="utf-8")
    path = ev.write_step_evidence(
        base_dir=tmp_path, scope_id="features/login.feature:6", scenario_id="features/login.feature:12",
        step_index=2, keyword="Then", text="页面显示「登录成功」", status="failed",
        message="AI 断言未过多数票（0/1）：页面显示「登录成功」",
        acts=[ev.ActRecord(index=0, prompt="页面显示「登录成功」", vote=False,
                           trajectory_path=str(traj_path))],
        ref_for=lambda p: f"file://{p}")
    out = ev.step_dir(tmp_path, "features/login.feature:12", 2)
    assert Path(path) == out / "evidence.json"
    assert out.parent.parent == tmp_path / "evidence" and out.name == "step-2"
    assert sorted(p.name for p in out.iterdir()) == [
        "act-0-frame-1.jpg", "act-0-frame-4.jpg", "evidence.json"]
    doc = json.loads(Path(path).read_text(encoding="utf-8"))
    shots = [f["screenshot"] for f in doc["acts"][0]["frames"]]
    assert shots[1].endswith("act-0-frame-1.jpg") and shots[4].endswith("act-0-frame-4.jpg")
    assert shots[0] is None and shots[2] is None and shots[3] is None   # 未选中的 frame 仍留 thought/actions
    assert doc["acts"][0]["frames"][0]["actions"][0]["name"] == "agentClick"
    assert (out / "act-0-frame-4.jpg").read_bytes().startswith(b"\xff\xd8")


def test_undecodable_image_leaves_screenshot_null(tmp_path):
    """真 fixture 的 base64 被裁短（解不开）→ 截图给 null、evidence.json 照落（逐字段容缺）。"""
    traj_path = tmp_path / "act_0_trajectory.json"
    traj_path.write_text(json.dumps(_fixture("nova_assert_traj.json")), encoding="utf-8")
    path = ev.write_step_evidence(
        base_dir=tmp_path, scope_id="s", scenario_id="sc:1", step_index=0, keyword="Then", text="t",
        status="failed", message=None,
        acts=[ev.ActRecord(index=0, prompt="t", vote=False, trajectory_path=str(traj_path))],
        ref_for=lambda p: f"file://{p}")
    doc = json.loads(Path(path).read_text(encoding="utf-8"))
    assert doc["acts"][0]["frames"][0]["screenshot"] is None
    assert not list(ev.step_dir(tmp_path, "sc:1", 0).glob("*.jpg"))


# ---- _run_step 钩子（ADR 0042 决策一「怎么挂」/ 决策二 best-effort）----
class _Result:
    def __init__(self, value=True, traj=None, tw=None):
        self.matches_schema = True
        self.parsed_response = value
        self.metadata = type("M", (), {"time_worked_s": tw, "trajectory_file_path": traj})()


class _Nova:
    """fake nova：act/act_get 回带 trajectory 路径的结果；act_raises 时抛（模拟 act 中途失败）。"""

    def __init__(self, traj=None, value=True, act_raises=None, tw=None):
        self._traj = traj
        self._value = value
        self._raises = act_raises
        self._tw = tw

    def go_to_url(self, url):
        pass

    def act(self, instr, timeout=None):
        if self._raises:
            raise self._raises
        return _Result(True, self._traj, self._tw)

    def act_get(self, instr, schema, timeout=None):
        if self._raises:
            raise self._raises
        return _Result(self._value, self._traj, self._tw)


class _Sink(list):
    def emit(self, obj):
        self.append(obj)


def _done(sink):
    return next(e for e in sink if e["type"] == "step_done")


@pytest.fixture
def logs_dir(tmp_path, monkeypatch):
    """注入产物落点（NOVA_LOGS_DIR），并重置 uploader 单例（no-op 档：ref 报 file://、不连 AWS）。"""
    d = tmp_path / "reports" / "rid" / "nova-trajectories"
    d.mkdir(parents=True)
    monkeypatch.setenv("NOVA_LOGS_DIR", str(d))
    monkeypatch.delenv("ARTIFACT_S3_BUCKET", raising=False)
    monkeypatch.delenv("GHERKAI_NO_ARTIFACTS", raising=False)
    monkeypatch.setattr(rs, "_uploader_singleton", None)
    return d


def _write_traj(logs_dir: Path, name: str, doc: dict) -> str:
    p = logs_dir / name
    p.write_text(json.dumps(doc), encoding="utf-8")
    return str(p)


def test_step_done_carries_evidence_ref_appended_after_trajectory(logs_dir):
    traj = _write_traj(logs_dir, "act_0_x_trajectory.json", _synthetic(2, thought_at=(0,)))
    sink = _Sink()
    assert rs._run_step(_Nova(traj=traj), "features/login.feature:12",
                        {"index": 2, "keyword": "Then", "text": '"页面显示登录成功"'}, 1, sink,
                        scope_id="features/login.feature:6") == "passed"
    refs = _done(sink)["reportRefs"]
    assert [r["kind"] for r in refs] == ["trajectory", "evidence"]   # 两者组合、不互相覆盖
    assert refs[1]["label"] == "evidence"
    doc = json.loads(Path(refs[1]["ref"][len("file://"):]).read_text(encoding="utf-8"))
    assert doc["scope_id"] == "features/login.feature:6"
    assert doc["scenario_id"] == "features/login.feature:12" and doc["step_index"] == 2
    assert doc["status"] == "passed" and doc["step"]["keyword"] == "Then"
    assert doc["acts"][0]["vote"] is True and doc["acts"][0]["prompt"] == "页面显示登录成功"
    assert doc["acts"][0]["frames"][1]["screenshot"].endswith("act-0-frame-1.jpg")  # passed → 每 act 末帧一张


def test_failed_assertion_evidence_has_all_votes_and_message(logs_dir):
    traj = _write_traj(logs_dir, "act_0_x_trajectory.json", _synthetic(1, thought_at=(0,)))
    sink = _Sink()
    assert rs._run_step(_Nova(traj=traj, value=False), "sc:1",
                        {"index": 0, "keyword": "Then", "text": '"对吗"'}, 3, sink, scope_id="sc") == "failed"
    doc = json.loads(Path(_done(sink)["reportRefs"][-1]["ref"][len("file://"):]).read_text(encoding="utf-8"))
    assert doc["status"] == "failed" and doc["message"].startswith("AI 断言未过多数票（0/3）")
    assert [a["index"] for a in doc["acts"]] == [0, 1, 2]           # N 票 = N 个 act
    assert all(a["vote"] is False for a in doc["acts"])


def test_raised_act_evidence_records_error_with_empty_frames(logs_dir):
    boom = RuntimeError("act 挂了")
    boom.metadata = type("M", (), {"time_worked_s": 3.5,
                                   "trajectory_file_path": str(logs_dir / "act_9_trajectory.json")})()
    sink = _Sink()
    assert rs._run_step(_Nova(act_raises=boom), "sc:1",
                        {"index": 1, "keyword": "When", "text": '"点击登录"'}, 1, sink, scope_id="sc") == "error"
    doc = json.loads(Path(_done(sink)["reportRefs"][-1]["ref"][len("file://"):]).read_text(encoding="utf-8"))
    assert doc["status"] == "error"
    assert doc["acts"][0]["error"] == "RuntimeError: act 挂了"      # 抛出的异常 type: message
    assert doc["acts"][0]["frames"] == [] and doc["acts"][0]["prompt"] == "点击登录"
    assert doc["acts"][0]["time_worked_s"] == 3.5                   # 异常 metadata 仍带费用


def test_deterministic_and_nav_steps_produce_no_evidence(logs_dir):
    sink = _Sink()
    rs._run_step(_Nova(), "sc:1", {"index": 0, "keyword": "Given", "text": '打开 "https://example.com"'},
                 1, sink, scope_id="sc")
    assert "reportRefs" not in _done(sink)
    assert not (logs_dir / "evidence").exists()


def test_no_artifacts_skips_evidence(logs_dir, monkeypatch):
    monkeypatch.setenv("GHERKAI_NO_ARTIFACTS", "1")
    sink = _Sink()
    rs._run_step(_Nova(traj=_write_traj(logs_dir, "a_trajectory.json", _synthetic(1))), "sc:1",
                 {"index": 0, "keyword": "When", "text": '"做事"'}, 1, sink, scope_id="sc")
    assert "reportRefs" not in _done(sink)
    assert not (logs_dir / "evidence").exists()


def test_evidence_skipped_when_logs_dir_unset(monkeypatch, tmp_path):
    monkeypatch.delenv("NOVA_LOGS_DIR", raising=False)
    monkeypatch.delenv("GHERKAI_NO_ARTIFACTS", raising=False)
    monkeypatch.setattr(rs, "_uploader_singleton", None)
    sink = _Sink()
    rs._run_step(_Nova(traj=None), "sc:1", {"index": 0, "keyword": "When", "text": '"做事"'}, 1, sink)
    assert "reportRefs" not in _done(sink)


# ---- best-effort（ADR 0042 决策二）：evidence 任一环失败 → 判定/事件照常、一行日志、无 evidence ref ----
@pytest.mark.parametrize("status_case", ["passed", "failed", "error"])
def test_evidence_failure_never_changes_verdict(logs_dir, monkeypatch, capsys, status_case):
    def _boom(**kwargs):
        raise OSError("磁盘满了")

    monkeypatch.setattr(rs._evidence, "write_step_evidence", _boom)
    traj = _write_traj(logs_dir, "act_0_x_trajectory.json", _synthetic(1, thought_at=(0,)))
    if status_case == "error":
        nova, step = _Nova(act_raises=RuntimeError("boom")), {"index": 0, "keyword": "When", "text": '"做事"'}
    else:
        nova = _Nova(traj=traj, value=(status_case == "passed"))
        step = {"index": 0, "keyword": "Then", "text": '"对吗"'}
    sink = _Sink()
    assert rs._run_step(nova, "sc:1", step, 1, sink, scope_id="sc") == status_case
    done = _done(sink)
    assert done["status"] == status_case                      # 判定不因 evidence 失败改变（不翻 engine_error）
    assert all(r["kind"] != "evidence" for r in done.get("reportRefs", []))
    err = capsys.readouterr().err
    assert len([ln for ln in err.splitlines() if "本步证据未能保存" in ln]) == 1  # 只一行
    assert "磁盘满了" in err


def test_evidence_upload_failure_is_swallowed(logs_dir, monkeypatch, capsys):
    """evidence.json 的即时上传失败也只丢 ref（to_report_ref 的「失败即抛」契约不动，兜法在调用方）。

    只让 evidence.json 那次上传失败：同 step 的 trajectory 上传仍按 ADR 0029 原规则（失败即抛 → step 变
    error），best-effort 只承诺覆盖 evidence 自身失败。
    """
    real = rs._get_uploader()
    orig = real.to_report_ref

    def _fail(path):
        if path.endswith("evidence.json"):
            raise RuntimeError("s3 挂了")
        return orig(path)

    monkeypatch.setattr(real, "to_report_ref", _fail)
    monkeypatch.setattr(rs, "_uploader_singleton", real)
    traj = _write_traj(logs_dir, "act_0_x_trajectory.json", _synthetic(1, thought_at=(0,)))
    sink = _Sink()
    assert rs._run_step(_Nova(traj=traj), "sc:1", {"index": 0, "keyword": "Then", "text": '"对吗"'},
                        1, sink, scope_id="sc") == "passed"
    assert all(r["kind"] != "evidence" for r in _done(sink).get("reportRefs", []))
    assert "本步证据未能保存" in capsys.readouterr().err


def test_error_text_prefers_sdk_message_and_is_single_line():
    """SDK 异常的 str() 是多行 repr（真跑暴露：ActTimeoutError 把「原因」撑成十几行）——取 .message 首行、折叠空白、封顶。"""
    from gherkai_worker_novaact.run_scope import _error_text

    class ActTimeoutError(Exception):
        def __init__(self):
            self.message = "Timed out; try increasing the 'timeout' kwarg   on the 'act' call"
            super().__init__("\nActTimeoutError(\n    message = Timed out\n    metadata = ActMetadata(...)\n)\n\nPlease consider providing feedback: https://x")

    assert _error_text(ActTimeoutError()) == "ActTimeoutError: Timed out; try increasing the 'timeout' kwarg on the 'act' call"
    assert _error_text(RuntimeError("boom\nsecond line")) == "RuntimeError: boom"
    assert _error_text(RuntimeError("x" * 500)).endswith("x" * 10) and len(_error_text(RuntimeError("x" * 500))) == len("RuntimeError: ") + 300
    assert _error_text(RuntimeError("")) == "RuntimeError"
