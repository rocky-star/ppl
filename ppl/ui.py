__all__ = ['UICmd']

from typing import Final, Literal, Tuple
import cmd
from funcparserlib.lexer import LexerError
from funcparserlib.parser import NoParseError
from .parser import Expr, Symbol, UnaryExpr, BinaryExpr, parse, tokenize
from .eval import TruthTable, evaluate, get_variables

_precedence: Final = ['=', '~', '|', '&', '!']
_unicode_ops: Final = {
    '=': '↔', '~': '→', '|': '∨', '&': '∧', '!': '¬'}


def _format_expr(expr: Expr, *, unicode: bool = False) -> str:
    def format_subexpr(e: Expr, op: str) -> str:
        if isinstance(e, Symbol):
            return str(e)
        elif isinstance(e, UnaryExpr):
            return _format_expr(e, unicode=u)
        elif isinstance(e, BinaryExpr):
            if _precedence.index(e.op) < _precedence.index(op):
                return f'({_format_expr(e, unicode=u)})'
            else:
                return _format_expr(e, unicode=u)
        else:
            raise RuntimeError

    buf = []
    u = unicode
    if isinstance(expr, Symbol):
        return str(expr)
    elif isinstance(expr, UnaryExpr):
        buf.append(_unicode_ops[expr.op] if u else expr.op)
        if isinstance(expr.value, Symbol):
            buf.append(str(expr.value))
        else:
            buf.append('(')
            buf.append(_format_expr(expr.value, unicode=u))
            buf.append(')')
    elif isinstance(expr, BinaryExpr):
        buf.append(format_subexpr(expr.left, expr.op))
        buf.append(' ')
        buf.append(_unicode_ops[expr.op] if u else expr.op)
        buf.append(' ')
        buf.append(format_subexpr(expr.right, expr.op))
    return ''.join(buf)


def _format_tt(tt: TruthTable, expr_str: str, *, unicode: bool = False) -> str:
    def values_key(values: Tuple[bool, ...]) -> int:
        return int(''.join('1' if v else '0' for v in values), 2)

    u = unicode
    buf = []
    col_1_width = len(tt.variables) * 2 + 1
    col_2_width = len(expr_str) + 2

    buf.append('┌' if u else '/')
    buf.append(('─' if u else '-') * col_1_width)
    buf.append('┬' if u else '+')
    buf.append(('─' if u else '-') * col_2_width)
    buf.append('┐' if u else '\\')
    buf.append('\n')

    buf.append('│' if u else '|')
    buf.append(' ')
    buf.append(' '.join(str(s) for s in tt.variables))
    buf.append(' ')
    buf.append('│' if u else '|')
    buf.append(' ')
    buf.append(expr_str)
    buf.append(' ')
    buf.append('│' if u else '|')
    buf.append('\n')

    for i, values in enumerate(sorted(tt.data, key=values_key)):
        result = tt.data[values]
        if i:
            buf.append('├' if u else '+')
            buf.append(('─' if u else '-') * col_1_width)
            buf.append('┼' if u else '+')
            buf.append(('─' if u else '-') * col_2_width)
            buf.append('┤' if u else '+')
        else:
            buf.append('┝' if u else '+')
            buf.append(('━' if u else '-') * col_1_width)
            buf.append('┿' if u else '+')
            buf.append(('━' if u else '-') * col_2_width)
            buf.append('┥' if u else '+')
        buf.append('\n')

        buf.append('│' if u else '|')
        buf.append(' ')
        buf.append(' '.join('1' if v else '0' for v in values))
        buf.append(' │')
        buf.append(('1' if result else '0').center(col_2_width))
        buf.append('│\n')

    buf.append('└' if u else '\\')
    buf.append(('─' if u else '-') * col_1_width)
    buf.append('┴' if u else '+')
    buf.append(('─' if u else '-') * col_2_width)
    buf.append('┘\n')

    return ''.join(buf)


class UICmd(cmd.Cmd):
    intro = '输入 ? 或 help 以显示所有命令。'
    prompt = '? '

    def __init__(self) -> None:
        super().__init__()
        self._exprs = {}

    def _get_valid_name(self, letter: str, *, no_exist: bool = False) -> Symbol:
        if letter:
            try:
                s = Symbol.from_letter(letter)
            except ValueError:
                print(f'{letter!r} 不是有效的表达式名。')
                raise ValueError
            if s not in self._exprs and not no_exist:
                print(f'{s} 表达式尚未被定义。')
                raise ValueError
            elif no_exist and s in self._exprs:
                print(f'{s} 表达式已被定义。')
                raise ValueError
            return s
        else:
            print('表达式名未指定。')
            raise ValueError

    def do_exit(self, arg: str) -> Literal[True]:
        """退出程序。

        exit
        """
        return True

    def do_EOF(self, arg: str) -> Literal[True]:
        return self.do_exit(arg)

    def do_list(self, arg: str, *, unicode: bool = False) -> None:
        """列出所有已添加的表达式，或指定的表达式。\n\nlist [表达式名]"""
        if not self._exprs:
            print('尚未加入任何表达式。')
            return

        if arg:
            try:
                s = self._get_valid_name(arg)
            except ValueError:
                return
            print(f'{s}: {_format_expr(self._exprs[s], unicode=unicode)}')
        else:
            for symbol, expr in self._exprs.items():
                print(f'{symbol}: {_format_expr(expr, unicode=unicode)}')

    def do_listu(self, arg: str) -> None:
        """以 Unicode 字符列出所有已添加的表达式，或指定的表达式。另见 list 命令。"""
        self.do_list(arg, unicode=True)

    def do_new(self, arg: str) -> None:
        """添加新表达式。\n\nnew 表达式名"""
        try:
            expr_name = self._get_valid_name(arg, no_exist=True)
        except ValueError:
            return

        try:
            expr = parse(tokenize(input('输入表达式: ')))
        except LexerError as e:
            print(f'词法分析错误: {e}')
            return
        except NoParseError as e:
            print(f'语法分析错误: {e}')
            return
        self._exprs[expr_name] = expr

    def do_del(self, arg: str) -> None:
        """删除已有的表达式。\n\ndel 表达式名"""
        try:
            s = self._get_valid_name(arg)
        except ValueError:
            return
        self._exprs.pop(s)

    def do_tt(self, arg: str, *, unicode: bool = False) -> None:
        """打印表达式的真值表。\n\ntt 表达式名"""
        try:
            s = self._get_valid_name(arg)
        except ValueError:
            return
        tt = TruthTable.from_expr(self._exprs[s])
        if tt.variables:
            print(_format_tt(tt, _format_expr(self._exprs[s], unicode=unicode), unicode=unicode), end='')
        else:
            print('给定的表达式没有变量。')

    def do_ttu(self, arg: str) -> None:
        """以 Unicode 字符打印真值表。另见 tt 命令。"""
        self.do_tt(arg, unicode=True)

    def do_eval(self, arg: str) -> None:
        """以给定解释对表达式求值。\n\neval 表达式名"""
        try:
            expr_name = self._get_valid_name(arg)
        except ValueError:
            return
        expr = self._exprs[expr_name]
        variables = list(get_variables(expr))
        variables.sort()
        if not variables:
            print('给定表达式不包含任何变量。')
            return

        interpt = {}
        print('分别为每个变量指定值。')
        for var_name in variables:
            interpt[var_name] = bool(int(input(f'{var_name} = ')))
        print(f'值是 {int(evaluate(expr, interpt))}。')
