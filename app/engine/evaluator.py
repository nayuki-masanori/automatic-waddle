"""安全な式評価器.

ワークフローの条件分岐 (`condition`) を評価するために使う。
組み込み ``eval`` は任意コード実行の危険があるため使わず、Python の AST を
ホワイトリストで制限して評価する。

サポートする構文:
    - リテラル: 数値, 文字列, True/False/None, リスト, タプル, 辞書, 集合
    - 比較演算: ==, !=, <, <=, >, >=, in, not in, is, is not
    - 論理演算: and, or, not
    - 算術演算: + - * / // % **, 単項 + -
    - 変数参照 (context から解決), 属性アクセス, 添字アクセス
    - 一部の組み込み関数 (len, min, max, abs, round, str, int, float, bool)
"""

from __future__ import annotations

import ast
import operator
from typing import Any, Mapping

__all__ = ["evaluate", "EvaluationError"]


class EvaluationError(Exception):
    """式の評価に失敗したときに送出される例外."""


# 利用を許可する二項演算子
_BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

# 比較演算子
_CMP_OPS = {
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
    ast.In: lambda a, b: a in b,
    ast.NotIn: lambda a, b: a not in b,
    ast.Is: operator.is_,
    ast.IsNot: operator.is_not,
}

# 単項演算子
_UNARY_OPS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
    ast.Not: operator.not_,
}

# 呼び出しを許可する組み込み関数
_ALLOWED_FUNCS = {
    "len": len,
    "min": min,
    "max": max,
    "abs": abs,
    "round": round,
    "str": str,
    "int": int,
    "float": float,
    "bool": bool,
    "sum": sum,
    "sorted": sorted,
    "any": any,
    "all": all,
}


def evaluate(expression: str, context: Mapping[str, Any]) -> Any:
    """``expression`` を ``context`` 上で評価して結果を返す.

    :param expression: 評価する式 (例: ``"score >= 80 and not blocked"``)
    :param context: 変数名から値へのマッピング
    :raises EvaluationError: パースや評価に失敗した場合
    """
    if not isinstance(expression, str):
        raise EvaluationError(f"expression must be a string, got {type(expression).__name__}")
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise EvaluationError(f"syntax error in expression: {expression!r} ({exc})") from exc
    return _eval_node(tree.body, context)


def _eval_node(node: ast.AST, ctx: Mapping[str, Any]) -> Any:
    if isinstance(node, ast.Constant):
        return node.value

    if isinstance(node, ast.Name):
        if node.id in ctx:
            return ctx[node.id]
        raise EvaluationError(f"unknown variable: {node.id!r}")

    if isinstance(node, ast.BoolOp):
        if isinstance(node.op, ast.And):
            result: Any = True
            for value in node.values:
                result = _eval_node(value, ctx)
                if not result:
                    return result
            return result
        if isinstance(node.op, ast.Or):
            result = False
            for value in node.values:
                result = _eval_node(value, ctx)
                if result:
                    return result
            return result
        raise EvaluationError(f"unsupported boolean operator: {type(node.op).__name__}")

    if isinstance(node, ast.UnaryOp):
        op = _UNARY_OPS.get(type(node.op))
        if op is None:
            raise EvaluationError(f"unsupported unary operator: {type(node.op).__name__}")
        return op(_eval_node(node.operand, ctx))

    if isinstance(node, ast.BinOp):
        op = _BIN_OPS.get(type(node.op))
        if op is None:
            raise EvaluationError(f"unsupported operator: {type(node.op).__name__}")
        return op(_eval_node(node.left, ctx), _eval_node(node.right, ctx))

    if isinstance(node, ast.Compare):
        left = _eval_node(node.left, ctx)
        for op_node, comparator in zip(node.ops, node.comparators):
            op = _CMP_OPS.get(type(op_node))
            if op is None:
                raise EvaluationError(f"unsupported comparison: {type(op_node).__name__}")
            right = _eval_node(comparator, ctx)
            if not op(left, right):
                return False
            left = right
        return True

    if isinstance(node, ast.IfExp):  # x if cond else y
        return _eval_node(node.body, ctx) if _eval_node(node.test, ctx) else _eval_node(node.orelse, ctx)

    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        values = [_eval_node(elt, ctx) for elt in node.elts]
        if isinstance(node, ast.List):
            return values
        if isinstance(node, ast.Set):
            return set(values)
        return tuple(values)

    if isinstance(node, ast.Dict):
        return {
            _eval_node(k, ctx): _eval_node(v, ctx)
            for k, v in zip(node.keys, node.values)
        }

    if isinstance(node, ast.Subscript):
        container = _eval_node(node.value, ctx)
        key = _eval_node(node.slice, ctx)
        try:
            return container[key]
        except (KeyError, IndexError, TypeError) as exc:
            raise EvaluationError(f"invalid subscript access: {exc}") from exc

    if isinstance(node, ast.Attribute):
        # 安全のためダンダー属性は禁止する
        if node.attr.startswith("__"):
            raise EvaluationError(f"access to dunder attribute is forbidden: {node.attr!r}")
        obj = _eval_node(node.value, ctx)
        try:
            return getattr(obj, node.attr)
        except AttributeError as exc:
            raise EvaluationError(f"no such attribute: {node.attr!r}") from exc

    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name):
            raise EvaluationError("only simple function calls are allowed")
        func = _ALLOWED_FUNCS.get(node.func.id)
        if func is None:
            raise EvaluationError(f"function not allowed: {node.func.id!r}")
        args = [_eval_node(a, ctx) for a in node.args]
        kwargs = {kw.arg: _eval_node(kw.value, ctx) for kw in node.keywords}
        return func(*args, **kwargs)

    raise EvaluationError(f"unsupported expression element: {type(node).__name__}")
