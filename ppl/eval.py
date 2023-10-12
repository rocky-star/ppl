__all__ = [
    'get_variables', 'get_all_inputs',
    'Interpretation', 'evaluate',
    'TruthTable',
]

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Dict, Generator, Set, Tuple

from .parser import BinaryExpr, Expr, Symbol, UnaryExpr


def get_variables(expr: Expr) -> Set[Symbol]:
    variables = set()
    def visit(expr: Expr) -> None:
        if isinstance(expr, UnaryExpr):
            visit(expr.value)
        elif isinstance(expr, BinaryExpr):
            visit(expr.left)
            visit(expr.right)
        elif isinstance(expr, Symbol):
            variables.add(expr)
        else:
            raise RuntimeError

    visit(expr)
    return variables


def get_all_inputs(n: int) -> Generator[Tuple[bool, ...], None, None]:
    if n > 1:
        for subinput in get_all_inputs(n - 1):
            yield (False,) + subinput
            yield (True,) + subinput
    elif n == 1:
        yield (False,)
        yield (True,)
    else:
        raise ValueError(
            'number of variables must be a positive number')


Interpretation = Mapping[Symbol, bool]


def evaluate(expr: Expr, interpr: Interpretation) -> bool:
    def eval_subexpr(e: Expr) -> bool:
        if isinstance(e, Symbol):
            return interpr[e]
        elif isinstance(e, UnaryExpr):
            if e.op == '!':
                return not eval_subexpr(e.value)
            else:
                raise RuntimeError
        elif isinstance(e, BinaryExpr):
            left = eval_subexpr(e.left)
            right = eval_subexpr(e.right)

            if e.op == '&':
                return left and right
            elif e.op == '|':
                return left or right
            elif e.op == '~':
                return not (left and not right)
            elif e.op == '=':
                return left == right
            else:
                raise RuntimeError
        else:
            raise RuntimeError
    return eval_subexpr(expr)


@dataclass
class TruthTable:
    variables: Tuple[Symbol]
    data: Dict[Tuple[bool, ...], bool]

    @classmethod
    def from_expr(cls, expr: Expr) -> 'TruthTable':
        tt = cls(tuple(sorted(get_variables(expr))), {})
        for subinput in get_all_inputs(len(tt.variables)):
            interpl = {s: v for s, v in zip(tt.variables, subinput)}
            tt.data[subinput] = evaluate(expr, interpl)
        return tt
