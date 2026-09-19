"""agent skill 里 `deploy` / `destroy` 那批命令 token 对照 provider 的真 parser（ADR 0043 决策六）。

**为什么这条护栏在这里、不在 `cli/tests/test_skill.py`**：`deploy` 段的 flag 按来源分两刀——前端自己声明的中立
flag（`--provider` / `--diff` / `--synth-only` / `--bootstrap` / `--require-approval` / `--allow-vpc-change`）
在 provider 未加载时也挂在主 parser 上，仍在 `cli/tests` 比对；provider 贴的选项与子动词（`--prefix` /
`--vpc` / `--stop-timeout` / `--region` / `--profile`、`push-worker` / `list-workers`）在 provider=None 时**不存在**。
provider 住 `gherkai[deploy-aws]` optional extra、只有部署方装（ADR 0037 决策 6），前端的测试不该强依赖它，故这批
放本包。

parser 按**真实接线顺序**建（同 `test_provider.py::_parse`）：`prog` 末段是 `deploy` 还是 `destroy` 决定
provider 贴什么（它按 prog 末段判 destroy 专属 flag 与 worker 子动词）→ 先贴前端的中立 flag → 再
`Provider().add_arguments(parser)`，`conflict_handler="resolve"` 让 provider 的重声明生效。

代码跨的抽取器与 `cli/tests` 共用（`cli/tests/_doc_rules.py`）：两处各写一份正则，迟早对同一段文字给出
不同判断。
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pytest

from gherkai_deploy_aws.cli import Provider

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "cli" / "tests"))
from _doc_rules import (  # noqa: E402
    PROVIDER_ONLY_FLAGS,
    extract_command_spans,
    is_placeholder,
    skill_markdown_files,
)

VERBS = ("deploy", "destroy")


def _build(verb: str) -> argparse.ArgumentParser:
    """前端 + provider 拼出的真 parser。前端那半边逐条照 `cli/gherkai_cli/deploy.py` 的声明抄——
    只抄 flag 面（名字/是否带值），help 与默认值归那边、这里不复述。"""
    parser = argparse.ArgumentParser(prog=f"gherkai {verb}", conflict_handler="resolve")
    parser.add_argument("--provider", default=None)
    if verb == "deploy":
        # 三个互斥的「不真部署」动作 + 两个被 provider 精确化的中立 flag（destroy 上前端只声明 --provider）
        action = parser.add_mutually_exclusive_group()
        action.add_argument("--diff", action="store_true")
        action.add_argument("--synth-only", default=None)
        action.add_argument("--bootstrap", action="store_true")
        parser.add_argument("--require-approval", default=None)
        parser.add_argument("--allow-vpc-change", action="store_true")
    Provider().add_arguments(parser)
    return parser


def _nodes(parser: argparse.ArgumentParser) -> dict[tuple[str, ...], set[str]]:
    """子动词路径 → 该节点声明的 `--flag` 集（`()` = `gherkai <verb>` 本身）。"""
    out: dict[tuple[str, ...], set[str]] = {}

    def walk(p: argparse.ArgumentParser, path: tuple[str, ...]) -> None:
        out[path] = {s for a in p._actions for s in a.option_strings if s.startswith("--")}
        for action in p._actions:
            if isinstance(action, argparse._SubParsersAction):
                for name, sub in action.choices.items():
                    walk(sub, path + (name,))

    walk(parser, ())
    return out


NODES = {verb: _nodes(_build(verb)) for verb in VERBS}


def _deploy_spans():
    return [span for md in skill_markdown_files()
            for span in extract_command_spans(md.read_text(encoding="utf-8"), md)
            if span.words and span.words[0] in VERBS]


def test_deploy_flags_are_attached_to_the_right_subverb():
    """`gherkai deploy [<子动词>] --flag` 逐对比对。父层给法合法（`deploy --prefix p push-worker …`），
    故允许集 = 路径上各级之并；挂到别的子动词上即红。"""
    spans = _deploy_spans()
    if not spans:
        pytest.skip("skill 里没有 deploy / destroy 的命令 token")
    problems = []
    for span in spans:
        verb, rest = span.words[0], span.words[1:]
        nodes = NODES[verb]
        path: tuple[str, ...] = ()
        for word in rest:
            if is_placeholder(word):
                break
            if path + (word,) in nodes:
                path += (word,)
            else:
                # `deploy` / `destroy` 本身没有位置参数，故紧跟其后的裸词只能是子动词——不认识就是拼错了
                # （`push-worker` 自己的 `<本地镜像>` 是占位符形态，上一支已跳过）。
                problems.append(f"{span.path.relative_to(REPO)}:{span.line}: `{span.span}`——"
                                f"`gherkai {verb}` 没有 {word!r} 这个子动词")
                break
        allowed = {f for i in range(len(path) + 1) for f in nodes[path[:i]]}
        for flag in span.flags:
            if flag not in allowed:
                problems.append(f"{span.path.relative_to(REPO)}:{span.line}: `{span.span}`——"
                                f"{flag} 不是 `gherkai {verb}{' ' + ' '.join(path) if path else ''}` 的 flag")
    assert not problems, "skill 里 deploy/destroy 的子动词/flag 组合对不上 provider 真 parser：\n" + "\n".join(problems)


def test_provider_only_flag_table_is_backed_by_the_real_parser():
    """`cli/tests` 那边对 `PROVIDER_ONLY_FLAGS` 里的裸 flag 放行（它 import 不到 provider）。这条守住那张表：
    每一项都必须真在 provider 的 parser 树上——否则它就成了「写错的 flag 也能过」的万能旁路。"""
    everywhere = {f for verb in VERBS for flags in NODES[verb].values() for f in flags}
    missing = sorted(PROVIDER_ONLY_FLAGS - everywhere)
    assert not missing, f"这些 flag 已不在 provider 上了，从 _doc_rules.PROVIDER_ONLY_FLAGS 里删掉：{missing}"
