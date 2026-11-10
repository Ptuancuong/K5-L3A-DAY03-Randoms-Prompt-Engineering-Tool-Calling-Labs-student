from __future__ import annotations

import ast
import operator
from typing import Any

OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _eval_node(node: ast.AST) -> float | int:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in OPERATORS:
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        return OPERATORS[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in OPERATORS:
        operand = _eval_node(node.operand)
        return OPERATORS[type(node.op)](operand)
    raise ValueError(f"Unsupported node type: {type(node).__name__}")


def calculate(expression: str = "") -> dict[str, Any]:
    expr = (expression or "").strip()
    if not expr:
        return {"tool": "calculator", "error": "ValueError", "message": "Biểu thức rỗng"}
    try:
        parsed = ast.parse(expr, mode="eval")
        result = _eval_node(parsed.body)
        return {"tool": "calculator", "expression": expr, "result": result}
    except Exception as exc:
        return {"tool": "calculator", "error": type(exc).__name__, "message": str(exc)}
