"""`--capabilities` 自述入口单测（ADR 0036「5.」/ ADR 0024「引擎自报下限」，Nova 侧）。

全部走**真子进程**：这条入口的契约恰好都在进程边界上——argv 分派、`NOVA_ACT_TIMEOUT_S` /
`NOVA_GRACE_MARGIN_S` 两个 env 旋钮在 import 期读、stdout 只此一个 JSON 对象、不读 stdin、不建会话。
in-process 调 `_capabilities()` 证不到这些（env 已在 import 期定型、stdin/AWS 更碰不到）。

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
    """形状 + `min_grace_s` = 注入的 `NOVA_ACT_TIMEOUT_S` + worker 侧 margin（组合根查询它当 grace 下限）。"""
    proc = subprocess.run(_CMD, capture_output=True, timeout=60,
                          env=_clean_env(NOVA_ACT_TIMEOUT_S="7"))
    assert proc.returncode == 0, proc.stderr.decode()[-500:]
    out = proc.stdout.decode("utf-8")
    assert len(out.strip().splitlines()) == 1, out  # stdout 只此一个 JSON 对象（消费侧整段 json.loads）
    caps = json.loads(out)
    assert caps == {"schema_version": 1, "engine": "novaact", "min_grace_s": 7 + NOVA_GRACE_MARGIN_S}
    assert NOVA_GRACE_MARGIN_S > 0  # margin 须 > 0（ADR 0024：act 有界返回之后还要会话释放 + 截图排空）


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
    """steps 加载失败在这个入口也 fail-loud（ADR 0037 决策 4「三个自述入口同样加载 steps」）：
    非 0 退出、stderr 指名文件、stdout 不吐半份能力声明（组合根宁可 fail-loud 也不要静默的下限）。"""
    from gherkai_worker_novaact.user_steps import EX_STEPS_LOAD

    (tmp_path / "broken.py").write_text("def h(:\n", encoding="utf-8")
    proc = subprocess.run(_CMD, capture_output=True, timeout=60,
                          env=_clean_env(GHERKAI_STEPS_DIR=str(tmp_path)))
    assert proc.returncode == EX_STEPS_LOAD, (proc.returncode, proc.stderr.decode()[-500:])
    assert "broken.py" in proc.stderr.decode("utf-8")
    assert proc.stdout.decode("utf-8").strip() == ""
