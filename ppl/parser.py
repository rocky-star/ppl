__all__ = [
    'Symbol', 'UnaryExpr', 'BinaryExpr', 'Expr', 'tokenize', 'parse']

import string
from dataclasses import dataclass
from typing import List, Literal, Sequence, Tuple, Union, cast

from funcparserlib.lexer import Token, TokenSpec, make_tokenizer
from funcparserlib.parser import Parser, finished, forward_decl, many, tok


class Symbol(int):
    @classmethod
    def from_letter(cls, letter: str) -> 'Symbol':
        try:
            return cls(string.ascii_uppercase.find(letter.upper()))
        except IndexError:
            raise ValueError('invalid symbol letter')

    def __str__(self) -> str:
        return string.ascii_uppercase[self]

    def __repr__(self) -> str:
        return f'{type(self).__name__}({int(self)!r})'


_UnaryOp = Literal['!']
_BinaryOp = Literal['&', '|', '~', '=']


@dataclass
class UnaryExpr:
    op: _UnaryOp
    value: 'Expr'


@dataclass
class BinaryExpr:
    op: _BinaryOp
    left: 'Expr'
    right: 'Expr'


Expr = Union[UnaryExpr, BinaryExpr, Symbol]


def tokenize(s: str) -> List[Token]:
    specs = [
        TokenSpec('ws', r'\s+'),
        TokenSpec('symbol', r'[A-Za-z]'),
        TokenSpec('op', r'[!&|~=()]'),
    ]
    return [t for t in make_tokenizer(specs)(s) if t.type != 'ws']


def _op(name: str) -> Parser[Token, str]:
    return tok('op', name)


def _to_unary_expr(args: Tuple[str, Expr]) -> UnaryExpr:
    op, expr = args
    # FIXME
    return UnaryExpr(cast(_UnaryOp, op), expr)


def _to_binary_expr(
        args: Tuple[Expr, List[Tuple[str, Expr]]]) -> Expr:
    first, rest = args
    result = first
    for op, expr in rest:
        # FIXME
        result = BinaryExpr(cast(_BinaryOp, op), result, expr)
    return result


def parse(tokens: Sequence[Token]) -> Expr:
    symbol = tok('symbol') >> Symbol.from_letter

    expr = forward_decl()

    paren = -_op('(') + expr + -_op(')')
    primary: Parser[Token, Expr] = forward_decl()
    neg = _op('!') + primary >> _to_unary_expr
    primary.define(symbol | neg | paren)

    conj = primary + many(_op('&') + primary) >> _to_binary_expr
    disj = conj + many(_op('|') + conj) >> _to_binary_expr
    matcond = disj + many(_op('~') + disj) >> _to_binary_expr
    bicond = matcond + many(_op('=') + matcond) >> _to_binary_expr
    expr.define(bicond)

    document = expr + -finished
    return document.parse(tokens)


if __name__ == '__main__':
    import pprint
    while True:
        pprint.pprint(parse(tokenize(input('? '))))
