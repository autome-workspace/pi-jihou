"""Safe template engine.

Evaluates ``{{ ... }}`` expressions. Only whitelisted macros (see
:mod:`app.voice.macros`) and user-defined variables are allowed. The engine
uses ``ast`` to parse each expression and refuses anything that is not a plain
name lookup or a call to a whitelisted function.
"""

from __future__ import annotations

import ast
import re
from datetime import datetime

from app.voice.macros import MACRO_NAMES, MacroRegistry

_EXPR_RE = re.compile(r"\{\{\s*(.*?)\s*\}\}")


class TemplateError(ValueError):
    pass


def _to_variable_values(variables: dict) -> dict:
    """Convert stored string values to Python types based on their declared type."""
    result: dict = {}
    for var in variables:
        name = var.name
        vtype = var.value_type
        raw = var.value
        try:
            if vtype == "integer":
                result[name] = int(raw)
            elif vtype == "float":
                result[name] = float(raw)
            elif vtype == "date":
                result[name] = datetime.strptime(raw, "%Y-%m-%d").date()
            elif vtype == "datetime":
                result[name] = datetime.strptime(raw, "%Y-%m-%d %H:%M:%S")
            elif vtype == "boolean":
                result[name] = raw.lower() in {"true", "1", "yes"}
            else:
                result[name] = raw
        except (ValueError, TypeError):
            result[name] = raw
    return result


def _eval_expr(expr_ast: ast.AST, registry: MacroRegistry, variables: dict):
    """Safely evaluate a whitelisted AST node."""
    if isinstance(expr_ast, ast.Constant):
        return expr_ast.value
    if isinstance(expr_ast, ast.Name):
        if expr_ast.id in variables:
            return variables[expr_ast.id]
        raise TemplateError(f"unknown variable: {expr_ast.id}")
    if isinstance(expr_ast, ast.Call):
        func = expr_ast.func
        if not isinstance(func, ast.Name):
            raise TemplateError("unsupported call expression")
        if func.id not in MACRO_NAMES:
            raise TemplateError(f"macro not allowed: {func.id}")
        args = [_eval_expr(a, registry, variables) for a in expr_ast.args]
        if expr_ast.keywords:
            raise TemplateError("keyword arguments are not supported")
        method = getattr(registry, func.id)
        return method(*args)
    raise TemplateError("unsupported expression")


def evaluate(template: str, variables: dict, now: datetime) -> str:
    """Expand ``{{ ... }}`` expressions in *template*.

    ``variables`` is a mapping of name -> typed value. ``now`` is the reference
    time used by time/date macros.
    """
    registry = MacroRegistry(now)

    def _replace(match: re.Match) -> str:
        source = match.group(1).strip()
        try:
            tree = ast.parse(source, mode="eval")
            value = _eval_expr(tree.body, registry, variables)
        except (SyntaxError, TemplateError, ValueError, TypeError) as exc:
            raise TemplateError(f"invalid expression '{source}': {exc}") from exc
        return "" if value is None else str(value)

    return _EXPR_RE.sub(_replace, template)


def expand_template(template_text: str, variables: dict, now: datetime) -> str:
    """Convenience wrapper for :func:`evaluate`."""
    return evaluate(template_text, variables, now)
