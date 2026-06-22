"""動的フロー実行エンジン.

入力やそれまでの実行結果 (context) に応じて、各ノードの遷移条件を評価し、
次に進むノードを動的に決定しながらワークフローを実行する。
"""

from __future__ import annotations

from typing import Any, Dict

from app.engine.evaluator import EvaluationError, evaluate
from app.models import NodeType, RunResult, TraceStep, Workflow


class WorkflowExecutionError(Exception):
    """ワークフロー実行中のエラー."""


def run_workflow(
    workflow: Workflow,
    inputs: Dict[str, Any],
    max_steps: int = 100,
) -> RunResult:
    """``workflow`` を ``inputs`` を初期 context として実行する.

    :param workflow: 実行するワークフロー定義
    :param inputs: 初期入力 (context の初期値)
    :param max_steps: 無限ループ防止のための最大ステップ数
    """
    nodes = workflow.node_map()
    context: Dict[str, Any] = dict(inputs)
    trace: list[TraceStep] = []

    current_id = workflow.start
    steps = 0

    while True:
        if steps >= max_steps:
            raise WorkflowExecutionError(
                f"max steps ({max_steps}) exceeded — possible infinite loop"
            )
        steps += 1

        node = nodes[current_id]
        assigned: Dict[str, Any] = {}

        # task ノードなら代入式を評価して context を更新
        if node.assign:
            for var, expr in node.assign.items():
                try:
                    value = evaluate(expr, context)
                except EvaluationError as exc:
                    raise WorkflowExecutionError(
                        f"node {node.id!r}: failed to evaluate assignment {var!r}: {exc}"
                    ) from exc
                context[var] = value
                assigned[var] = value

        # 終端ノード
        if node.type == NodeType.END or not node.transitions:
            trace.append(
                TraceStep(
                    node_id=node.id,
                    node_type=node.type,
                    assigned=assigned,
                )
            )
            return RunResult(
                status="completed",
                final_node=node.id,
                context=context,
                trace=trace,
            )

        # 条件を順に評価して遷移先を決定。
        # condition=None はデフォルトとして最後に採用する。
        chosen = None
        default_transition = None
        for tr in node.transitions:
            if tr.condition is None:
                if default_transition is None:
                    default_transition = tr
                continue
            try:
                if evaluate(tr.condition, context):
                    chosen = tr
                    break
            except EvaluationError as exc:
                raise WorkflowExecutionError(
                    f"node {node.id!r}: failed to evaluate condition {tr.condition!r}: {exc}"
                ) from exc

        if chosen is None:
            chosen = default_transition

        if chosen is None:
            raise WorkflowExecutionError(
                f"node {node.id!r}: no transition matched and no default transition defined"
            )

        trace.append(
            TraceStep(
                node_id=node.id,
                node_type=node.type,
                assigned=assigned,
                chosen_transition=chosen.to,
                condition=chosen.condition,
            )
        )
        current_id = chosen.to
