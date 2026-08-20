import ast
import operator


_ALLOWED_OPERATORS = {
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


def _evaluate(node: ast.AST) -> float | int:
    """Safely evaluate an arithmetic AST."""

    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value

        raise ValueError("Only numbers are allowed.")

    if isinstance(node, ast.UnaryOp):
        operator_function = _ALLOWED_OPERATORS.get(
            type(node.op)
        )

        if operator_function is None:
            raise ValueError("Unsupported operator.")

        return operator_function(
            _evaluate(node.operand)
        )

    if isinstance(node, ast.BinOp):
        operator_function = _ALLOWED_OPERATORS.get(
            type(node.op)
        )

        if operator_function is None:
            raise ValueError("Unsupported operator.")

        return operator_function(
            _evaluate(node.left),
            _evaluate(node.right),
        )

    raise ValueError("Unsupported expression.")


def calculate(expression: str) -> str:
    """Safely calculate a basic arithmetic expression."""

    try:
        tree = ast.parse(
            expression,
            mode="eval",
        )

        result = _evaluate(tree.body)

        return str(result)

    except Exception:
        return "I couldn't calculate that expression."