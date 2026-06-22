"""実行エンジンの単体テスト."""

import pytest

from app.engine.runner import WorkflowExecutionError, run_workflow
from app.models import Workflow


def _grading_workflow() -> Workflow:
    """点数に応じて grade を分岐させるワークフロー."""
    return Workflow.model_validate(
        {
            "name": "grading",
            "start": "start",
            "nodes": [
                {
                    "id": "start",
                    "type": "start",
                    "transitions": [{"to": "decide"}],
                },
                {
                    "id": "decide",
                    "type": "decision",
                    "transitions": [
                        {"to": "pass_high", "condition": "score >= 80"},
                        {"to": "pass_low", "condition": "score >= 60"},
                        {"to": "fail"},
                    ],
                },
                {
                    "id": "pass_high",
                    "type": "task",
                    "assign": {"grade": "'A'"},
                    "transitions": [{"to": "end"}],
                },
                {
                    "id": "pass_low",
                    "type": "task",
                    "assign": {"grade": "'B'"},
                    "transitions": [{"to": "end"}],
                },
                {
                    "id": "fail",
                    "type": "task",
                    "assign": {"grade": "'F'"},
                    "transitions": [{"to": "end"}],
                },
                {"id": "end", "type": "end"},
            ],
        }
    )


def test_high_score_path():
    wf = _grading_workflow()
    result = run_workflow(wf, {"score": 95})
    assert result.status == "completed"
    assert result.context["grade"] == "A"
    assert result.final_node == "end"
    assert [s.node_id for s in result.trace] == ["start", "decide", "pass_high", "end"]


def test_mid_score_path():
    result = run_workflow(_grading_workflow(), {"score": 70})
    assert result.context["grade"] == "B"


def test_default_transition_path():
    result = run_workflow(_grading_workflow(), {"score": 40})
    assert result.context["grade"] == "F"


def test_assignment_uses_context():
    wf = Workflow.model_validate(
        {
            "name": "calc",
            "start": "a",
            "nodes": [
                {
                    "id": "a",
                    "type": "task",
                    "assign": {"total": "x + y"},
                    "transitions": [{"to": "end"}],
                },
                {"id": "end", "type": "end"},
            ],
        }
    )
    result = run_workflow(wf, {"x": 2, "y": 3})
    assert result.context["total"] == 5


def test_infinite_loop_protection():
    wf = Workflow.model_validate(
        {
            "name": "loop",
            "start": "a",
            "nodes": [
                {"id": "a", "type": "task", "transitions": [{"to": "b"}]},
                {"id": "b", "type": "task", "transitions": [{"to": "a"}]},
            ],
        }
    )
    with pytest.raises(WorkflowExecutionError):
        run_workflow(wf, {}, max_steps=50)


def test_no_matching_transition_errors():
    wf = Workflow.model_validate(
        {
            "name": "stuck",
            "start": "a",
            "nodes": [
                {
                    "id": "a",
                    "type": "decision",
                    "transitions": [{"to": "b", "condition": "False"}],
                },
                {"id": "b", "type": "end"},
            ],
        }
    )
    with pytest.raises(WorkflowExecutionError):
        run_workflow(wf, {})
