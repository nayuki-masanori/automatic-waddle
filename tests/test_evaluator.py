"""evaluator の単体テスト."""

import pytest

from app.engine.evaluator import EvaluationError, evaluate


def test_arithmetic():
    assert evaluate("1 + 2 * 3", {}) == 7
    assert evaluate("(1 + 2) * 3", {}) == 9
    assert evaluate("10 / 4", {}) == 2.5
    assert evaluate("10 // 4", {}) == 2
    assert evaluate("2 ** 8", {}) == 256


def test_comparison_and_logic():
    ctx = {"score": 85, "blocked": False}
    assert evaluate("score >= 80 and not blocked", ctx) is True
    assert evaluate("score < 80 or blocked", ctx) is False
    assert evaluate("60 <= score < 90", ctx) is True


def test_variables_and_membership():
    ctx = {"role": "admin", "roles": ["admin", "editor"]}
    assert evaluate("role in roles", ctx) is True
    assert evaluate("'guest' not in roles", ctx) is True


def test_subscript_and_attribute():
    ctx = {"data": {"a": 1}, "items": [10, 20, 30]}
    assert evaluate("data['a']", ctx) == 1
    assert evaluate("items[1]", ctx) == 20


def test_builtins():
    ctx = {"items": [3, 1, 2]}
    assert evaluate("len(items)", ctx) == 3
    assert evaluate("max(items)", ctx) == 3
    assert evaluate("sorted(items)", ctx) == [1, 2, 3]


def test_unknown_variable_raises():
    with pytest.raises(EvaluationError):
        evaluate("missing > 1", {})


def test_forbidden_dunder():
    with pytest.raises(EvaluationError):
        evaluate("x.__class__", {"x": 1})


def test_disallowed_function():
    with pytest.raises(EvaluationError):
        evaluate("open('secret')", {})


def test_syntax_error():
    with pytest.raises(EvaluationError):
        evaluate("1 +", {})
