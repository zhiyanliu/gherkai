"""`--capabilities` 自述入口单测（ADR 0036「5.」/ ADR 0024「引擎自报下限」，Nova 侧）。

全部走**真子进程**：这条入口的契约恰好都在进程边界上——argv 分派（含「`--list-deterministic` 不再被
识别」这条不留别名的红线）、`NOVA_ACT_TIMEOUT_S` / `NOVA_GRACE_MARGIN_S` / `NOVA_MODEL_ID` 三个 env 旋钮
在 import 期读、stdout 只此一个 JSON 对象、不读 stdin、不建会话。in-process 调 `_capabilities()` 证不到
这些（env 已在 import 期定型、argv/stdin/AWS 更碰不到）；尤其 env 旋钮的缺省值——本进程继承的 env 里若
设过同名变量，in-process 断言就是假绿。

跑（从 repo 根）：uv run pytest -q engines/novaact/tests/test_capabilities.py
"""
import json
import os
import subprocess
import sys

from gherkai_worker_novaact.lib.constants import NOVA_GRACE_MARGIN_S

_CMD = [sys.executable, "-m", "gherkai_worker_novaact", "--capabilities"]


def _clean_env(**extra: str) -> dict:
    """子进程 env：保留运行必需项，剥掉 GHERKAI_* / AWS_* / NOVA_*（含本机 region 与凭证落点）。

    剥 AWS 是断言的一部分——「不建会话、零费用」在这个 env 下若被违背（起 Workflow / AgentCore 会话）
    必炸或挂，退 0 才成立。
    """
    keep = ("PATH", "PYTHONPATH", "PYTHONHOME", "HOME", "TMPDIR", "LANG", "LC_ALL", "SYSTEMROOT", "VIRTUAL_ENV")
    env = {k: v for k, v in os.environ.items() if k in keep}
    env["AWS_EC2_METADATA_DISABLED"] = "true"  # 别让 boto 去问实例元数据（无凭证时那是几秒挂等）
    env.update(extra)
    return env


def test_capabilities_shape_and_min_grace_from_injected_act_timeout():
    """键集恰五个 + `min_grace_s` = 注入的 `NOVA_ACT_TIMEOUT_S` + worker 侧 margin（组合根查它当 grace 下限）。

    键集**全等**断言（非「至少含」）：ADR 0036「5.」的自述对象是消费侧按键取的契约面，多一个未声明的键
    或少一个键都要连 `schema_version` 一起议——「至少含」照不出多出来的键。
    """
    proc = subprocess.run(_CMD, capture_output=True, timeout=60,
                          env=_clean_env(NOVA_ACT_TIMEOUT_S="7"))
    assert proc.returncode == 0, proc.stderr.decode()[-500:]
    out = proc.stdout.decode("utf-8")
    assert len(out.strip().splitlines()) == 1, out  # stdout 只此一个 JSON 对象（消费侧整段 json.loads）
    caps = json.loads(out)
    assert set(caps) == {"schema_version", "engine", "min_grace_s", "deterministic_steps", "model_id"}, caps
    assert caps["schema_version"] == 1  # 只加键不改既有键语义 → 版本不递增（ADR 0036「5.」）
    assert caps["engine"] == "novaact"
    assert caps["min_grace_s"] == 7 + NOVA_GRACE_MARGIN_S
    assert NOVA_GRACE_MARGIN_S > 0  # margin 须 > 0（ADR 0024：act 有界返回之后还要会话释放 + 截图排空）
    steps = caps["deterministic_steps"]  # 注册表清单（ADR 0036「2.」），内建脚手架至少一条
    assert isinstance(steps, list) and steps, caps
    assert all(set(e) == {"pattern", "description", "example"} for e in steps), steps
    assert all(e["pattern"] and e["description"] and e["example"] for e in steps), steps
    assert any("页面地址" in e["pattern"] for e in steps), steps  # 脚手架注册的真锚点在表里
    assert isinstance(caps["model_id"], str) and caps["model_id"], caps  # 组合根按「非空字符串」校验这一位


def test_model_id_defaults_to_pinned_ga_version():
    """不设 `NOVA_MODEL_ID` 时自报**钉死的 GA 版本 id，不是 `nova-act-latest` 别名**。

    这是 ADR 0004「模型版本选择策略」的红线：别名意味着 AWS 发新 GA 时静默换模型，而 pass / fail 靠 AI
    投票、换模型就换判定。字面量写在这里是**故意的闸门**——真要升 GA 就得连这条一起改，即「改常量 +
    发版点明模型换代」那条流程；不是脆弱断言。
    """
    proc = subprocess.run(_CMD, capture_output=True, timeout=60, env=_clean_env())
    assert proc.returncode == 0, proc.stderr.decode()[-500:]
    model_id = json.loads(proc.stdout.decode("utf-8"))["model_id"]
    assert model_id == "nova-act-v1.0", model_id


def test_model_id_follows_env_override():
    """`NOVA_MODEL_ID` 真穿到自述（opt-in 旋钮，ADR 0004「模型版本选择策略」）：`doctor` 据此显示当前模型，
    烙了 env 的机器一眼可见。

    取值用 `nova-act-preview` 别名——试新模型只有别名一条路（服务端拒绝直接引用带日期的 preview id）。
    worker 侧**不校验取值**（合法性由服务端判），故这条只证「env 到自述」这一段：本入口不建会话、不碰
    服务端，_clean_env 还剥掉了 AWS_*。
    """
    proc = subprocess.run(_CMD, capture_output=True, timeout=60,
                          env=_clean_env(NOVA_MODEL_ID="nova-act-preview"))
    assert proc.returncode == 0, proc.stderr.decode()[-500:]
    assert json.loads(proc.stdout.decode("utf-8"))["model_id"] == "nova-act-preview"


def test_min_grace_tracks_both_env_knobs():
    """两个旋钮都真参与（不是硬编码的 150）：act timeout 与 margin 各覆盖一次，结果按和变。"""
    proc = subprocess.run(_CMD, capture_output=True, timeout=60,
                          env=_clean_env(NOVA_ACT_TIMEOUT_S="7", NOVA_GRACE_MARGIN_S="11"))
    assert proc.returncode == 0, proc.stderr.decode()[-500:]
    assert json.loads(proc.stdout.decode("utf-8"))["min_grace_s"] == 18


def test_default_min_grace_covers_act_timeout_default():
    """不注入任何 env（旧宿主 / 手动直跑）：下限仍 ≥ 缺省 act 上界 120 + margin，不退化成小值。"""
    proc = subprocess.run(_CMD, capture_output=True, timeout=60, env=_clean_env())
    assert proc.returncode == 0, proc.stderr.decode()[-500:]
    assert json.loads(proc.stdout.decode("utf-8"))["min_grace_s"] == 120 + NOVA_GRACE_MARGIN_S


def test_does_not_read_stdin():
    """不读 stdin：stdin 是一根**写端一直开着**的管子——真去读就永远阻塞、这里就 timeout 失败。

    （`subprocess.run(input=…)` 证不到：communicate 会立刻关写端，读到 EOF 也「不阻塞」。）
    """
    read_fd, write_fd = os.pipe()
    proc = subprocess.Popen(_CMD, stdin=read_fd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            env=_clean_env(NOVA_ACT_TIMEOUT_S="7"))
    os.close(read_fd)
    try:
        out, err = proc.communicate(timeout=30)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.communicate()
        raise AssertionError("--capabilities 阻塞在 stdin 上（契约是不读 stdin）")
    finally:
        os.close(write_fd)
    assert proc.returncode == 0, err.decode()[-500:]
    assert json.loads(out.decode("utf-8"))["min_grace_s"] == 7 + NOVA_GRACE_MARGIN_S


def test_broken_steps_dir_makes_capabilities_exit_nonzero(tmp_path):
    """steps 加载失败在这个入口也 fail-loud（ADR 0037 决策 4「两个非 job 入口同样加载 steps」）：
    非 0 退出、stderr 指名文件、stdout 不吐半份能力声明（组合根宁可 fail-loud 也不要静默的下限）。"""
    from gherkai_worker_novaact.user_steps import EX_STEPS_LOAD

    (tmp_path / "broken.py").write_text("def h(:\n", encoding="utf-8")
    proc = subprocess.run(_CMD, capture_output=True, timeout=60,
                          env=_clean_env(GHERKAI_STEPS_DIR=str(tmp_path)))
    assert proc.returncode == EX_STEPS_LOAD, (proc.returncode, proc.stderr.decode()[-500:])
    assert "broken.py" in proc.stderr.decode("utf-8")
    assert proc.stdout.decode("utf-8").strip() == ""


def test_list_deterministic_flag_no_longer_recognized():
    """`--list-deterministic` 已删、**不留别名**（ADR 0036 被拒方案末条「每个自述项一个独立 flag」）。

    只有真 argv 证得到：这个 flag 认不出 → 落进 job 模式去读 stdin，stdin 给 DEVNULL（无 job 载荷）→
    非 0 退出、stdout 一个 JSON 对象都不吐；若哪天有人为兼容偷偷把它接回自述，这条即红。
    """
    proc = subprocess.run([sys.executable, "-m", "gherkai_worker_novaact", "--list-deterministic"],
                          stdin=subprocess.DEVNULL, capture_output=True, timeout=60, env=_clean_env())
    assert proc.returncode != 0, proc.stdout.decode("utf-8")[-500:]
    out = proc.stdout.decode("utf-8")
    assert "deterministic_steps" not in out and "min_grace_s" not in out, out
    assert not [ln for ln in out.splitlines() if ln.strip().startswith("{")], out  # 没有半份 JSON 对象
