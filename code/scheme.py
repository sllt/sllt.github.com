#!/usr/bin/env python3
"""A self-contained Scheme interpreter in Python, built around Pair and nil."""

from __future__ import annotations

import json
import math
import operator
import sys
from dataclasses import dataclass
from functools import reduce
from pathlib import Path
from typing import Any, Callable, Iterable, Iterator


# 1. Errors & Basic Types ------------------------------------------------


class SchemeError(Exception):
    """Base exception for Scheme evaluation and syntax errors."""


class SchemeSyntaxError(SchemeError):
    pass


class IncompleteInput(SchemeSyntaxError):
    pass


class String(str):
    """A Scheme string literal (distinct from a Scheme symbol, which is a plain str)."""

    def __repr__(self) -> str:
        return json.dumps(str(self), ensure_ascii=False)


Symbol = str


class _Unspecified:
    def __repr__(self) -> str:
        return "UNSPECIFIED"


UNSPECIFIED = _Unspecified()


# 2. Pair and nil (S-Expression Linked Lists) ----------------------------


class _Nil:
    """The empty list () in Scheme."""

    def __repr__(self) -> str:
        return "nil"

    def __str__(self) -> str:
        return "()"

    def __len__(self) -> int:
        return 0

    def __iter__(self) -> Iterator[Any]:
        return iter(())

    def __bool__(self) -> bool:
        return False

    def map(self, fn: Callable[[Any], Any]) -> _Nil:
        return self


nil = _Nil()


class Pair:
    """A cons cell (first, second) representing Scheme pairs and lists."""

    def __init__(self, first: Any, second: Any = nil) -> None:
        self.first = first
        self.second = second

    def __repr__(self) -> str:
        return f"Pair({self.first!r}, {self.second!r})"

    def __str__(self) -> str:
        return to_scheme(self)

    def __len__(self) -> int:
        count = 0
        current: Any = self
        while isinstance(current, Pair):
            count += 1
            current = current.second
        if current is not nil:
            raise SchemeError("length requires a proper list")
        return count

    def __iter__(self) -> Iterator[Any]:
        current: Any = self
        while isinstance(current, Pair):
            yield current.first
            current = current.second
        if current is not nil:
            raise SchemeError("expected a proper list, got dotted pair")

    def __getitem__(self, index: int) -> Any:
        if index < 0:
            raise IndexError("negative index not supported")
        for i, item in enumerate(self):
            if i == index:
                return item
        raise IndexError("Pair index out of range")

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, Pair)
            and self.first == other.first
            and self.second == other.second
        )

    def map(self, fn: Callable[[Any], Any]) -> Pair:
        if not isinstance(self.second, (Pair, _Nil)):
            raise SchemeError("map requires a proper list")
        return Pair(fn(self.first), self.second.map(fn))


def as_scheme_list(*items: Any) -> Pair | _Nil:
    """Convert a sequence of Python values into a Scheme linked list."""
    result: Pair | _Nil = nil
    for item in reversed(items):
        result = Pair(item, result)
    return result


def is_symbol(value: Any) -> bool:
    return isinstance(value, str) and not isinstance(value, String)


def is_proper_list(value: Any) -> bool:
    while isinstance(value, Pair):
        value = value.second
    return value is nil


def to_scheme(value: Any) -> str:
    """Format a runtime value using standard Scheme notation."""
    if value is True:
        return "#t"
    if value is False:
        return "#f"
    if value is nil:
        return "()"
    if value is UNSPECIFIED:
        return ""
    if isinstance(value, String):
        return json.dumps(str(value), ensure_ascii=False)
    if isinstance(value, str):
        return value
    if isinstance(value, Pair):
        parts: list[str] = []
        current: Any = value
        while isinstance(current, Pair):
            parts.append(to_scheme(current.first))
            current = current.second
        if current is not nil:
            parts.append(".")
            parts.append(to_scheme(current))
        return "(" + " ".join(parts) + ")"
    if isinstance(value, Procedure):
        return "<procedure>"
    if callable(value):
        return "<builtin-procedure>"
    return str(value)


# 3. Lexer & Parser (Read) -----------------------------------------------


def tokenize(source: str) -> list[str]:
    """Split Scheme source code into tokens, ignoring comments and whitespace."""
    tokens: list[str] = []
    i = 0

    while i < len(source):
        char = source[i]

        if char.isspace():
            i += 1
            continue

        if char == ";":
            newline = source.find("\n", i)
            i = len(source) if newline == -1 else newline + 1
            continue

        if char in "()'":
            tokens.append(char)
            i += 1
            continue

        if char == '"':
            start = i
            i += 1
            escaped = False
            while i < len(source):
                if escaped:
                    escaped = False
                elif source[i] == "\\":
                    escaped = True
                elif source[i] == '"':
                    i += 1
                    tokens.append(source[start:i])
                    break
                i += 1
            else:
                raise IncompleteInput("unterminated string literal")
            continue

        start = i
        while i < len(source) and not source[i].isspace() and source[i] not in "()'\";":
            i += 1
        tokens.append(source[start:i])

    return tokens


def atom(token: str) -> Any:
    """Convert an atomic token into a boolean, String, number, or symbol (str)."""
    if token == "#t":
        return True
    if token == "#f":
        return False
    if token.startswith('"'):
        try:
            return String(json.loads(token))
        except json.JSONDecodeError as err:
            raise SchemeSyntaxError(f"invalid string literal: {token}") from err
    try:
        return int(token)
    except ValueError:
        try:
            return float(token)
        except ValueError:
            return token


class Buffer:
    """A simple token stream with lookahead for recursive-descent parsing."""

    def __init__(self, tokens: Iterable[str]) -> None:
        self.tokens = list(tokens)
        self.index = 0

    @property
    def more(self) -> bool:
        return self.index < len(self.tokens)

    def current(self) -> str | None:
        return self.tokens[self.index] if self.more else None

    def pop_first(self) -> str:
        if not self.more:
            raise IncompleteInput("unexpected end of input")
        token = self.tokens[self.index]
        self.index += 1
        return token


def scheme_read(src: Buffer) -> Any:
    """Read the next complete Scheme expression from token buffer src."""
    if not src.more:
        raise IncompleteInput("unexpected end of input")

    token = src.pop_first()
    if token == "(":
        return read_tail(src)
    if token == "'":
        return Pair("quote", Pair(scheme_read(src), nil))
    if token in (")", "."):
        raise SchemeSyntaxError(f"unexpected token: {token}")
    return atom(token)


def read_tail(src: Buffer) -> Pair | _Nil:
    """Read the remainder of a parenthesized list until the matching ')'."""
    if not src.more:
        raise IncompleteInput("unexpected end of input while reading list")

    if src.current() == ")":
        src.pop_first()
        return nil

    if src.current() == ".":
        src.pop_first()
        rest = scheme_read(src)
        if not src.more:
            raise IncompleteInput("unexpected end of input after '.'")
        if src.pop_first() != ")":
            raise SchemeSyntaxError("expected ')' after dotted tail")
        return rest

    first = scheme_read(src)
    rest = read_tail(src)
    return Pair(first, rest)


def parse_program(source: str) -> list[Any]:
    """Parse all top-level Scheme expressions from source string."""
    src = Buffer(tokenize(source))
    expressions: list[Any] = []
    while src.more:
        expressions.append(scheme_read(src))
    return expressions


# 4. Environments & Procedures -------------------------------------------


class Env(dict[Symbol, Any]):
    """An environment frame mapping symbols to values, chained to outer."""

    def __init__(
        self,
        params: Iterable[Symbol] = (),
        args: Iterable[Any] = (),
        outer: Env | None = None,
    ) -> None:
        params_list = list(params)
        args_list = list(args)
        if len(params_list) != len(args_list):
            raise SchemeError(
                f"expected {len(params_list)} arguments, got {len(args_list)}"
            )
        super().__init__(zip(params_list, args_list))
        self.outer = outer

    def find(self, name: Symbol) -> Env:
        """Return the innermost frame in which name is bound."""
        if name in self:
            return self
        if self.outer is not None:
            return self.outer.find(name)
        raise SchemeError(f"unbound symbol: {name}")


@dataclass
class Procedure:
    """A user-defined Scheme procedure (closure)."""

    params: list[Symbol]
    body: Pair
    env: Env

    def __call__(self, *args: Any) -> Any:
        local_env = Env(self.params, args, self.env)
        return eval_all(self.body, local_env)


# 5. Built-in Procedures & Standard Environment --------------------------


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SchemeError(message)


def is_true(value: Any) -> bool:
    """In Scheme, only #f is false; everything else (including 0 and ()) is true."""
    return value is not False


def calc_add(*args: Any) -> Any:
    return sum(args)


def calc_sub(*args: Any) -> Any:
    require(len(args) >= 1, "- requires at least 1 argument")
    if len(args) == 1:
        return -args[0]
    return reduce(operator.sub, args[1:], args[0])


def calc_mul(*args: Any) -> Any:
    return reduce(operator.mul, args, 1)


def calc_div(*args: Any) -> Any:
    require(len(args) >= 1, "/ requires at least 1 argument")
    try:
        if len(args) == 1:
            return 1 / args[0]
        return reduce(operator.truediv, args[1:], args[0])
    except ZeroDivisionError as err:
        raise SchemeError("division by zero") from err


def compare(name: str, op: Callable[[Any, Any], bool], *args: Any) -> bool:
    require(len(args) >= 2, f"{name} requires at least 2 arguments")
    return all(op(a, b) for a, b in zip(args, args[1:]))


def builtin_car(pair: Any) -> Any:
    require(isinstance(pair, Pair), "car requires a pair")
    return pair.first


def builtin_cdr(pair: Any) -> Any:
    require(isinstance(pair, Pair), "cdr requires a pair")
    return pair.second


def builtin_append(*lists: Any) -> Pair | _Nil:
    items: list[Any] = []
    for lst in lists:
        require(is_proper_list(lst), "append requires proper lists")
        items.extend(lst)
    return as_scheme_list(*items)


def builtin_list_ref(lst: Any, index: int) -> Any:
    require(isinstance(lst, Pair), "list-ref requires a non-empty list")
    try:
        return lst[index]
    except IndexError as err:
        raise SchemeError(str(err)) from err


def builtin_display(value: Any) -> _Unspecified:
    if isinstance(value, String):
        print(str(value), end="")
    else:
        print(to_scheme(value), end="")
    return UNSPECIFIED


def builtin_newline() -> _Unspecified:
    print()
    return UNSPECIFIED


def scheme_apply(procedure: Any, args: Pair | _Nil) -> Any:
    """Apply a built-in function or user-defined Procedure to a Scheme list of args."""
    require(callable(procedure), f"{to_scheme(procedure)} is not callable")
    py_args = list(args)
    try:
        return procedure(*py_args)
    except SchemeError:
        raise
    except (ArithmeticError, TypeError, ValueError) as err:
        raise SchemeError(str(err)) from err


def standard_env() -> Env:
    """Create the default global environment with built-in procedures."""
    env = Env()
    env.update(
        {
            "+": calc_add,
            "-": calc_sub,
            "*": calc_mul,
            "/": calc_div,
            "abs": abs,
            "max": max,
            "min": min,
            "round": round,
            "sqrt": math.sqrt,
            "expt": pow,
            "quotient": lambda a, b: math.trunc(a / b),
            "modulo": operator.mod,
            "=": lambda *xs: compare("=", operator.eq, *xs),
            "<": lambda *xs: compare("<", operator.lt, *xs),
            "<=": lambda *xs: compare("<=", operator.le, *xs),
            ">": lambda *xs: compare(">", operator.gt, *xs),
            ">=": lambda *xs: compare(">=", operator.ge, *xs),
            "not": lambda x: x is False,
            "eq?": lambda a, b: a is b if isinstance(a, Pair) else a == b,
            "equal?": operator.eq,
            "number?": lambda x: isinstance(x, (int, float))
            and not isinstance(x, bool),
            "symbol?": is_symbol,
            "string?": lambda x: isinstance(x, String),
            "boolean?": lambda x: isinstance(x, bool),
            "procedure?": callable,
            "pair?": lambda x: isinstance(x, Pair),
            "null?": lambda x: x is nil,
            "list?": is_proper_list,
            "cons": Pair,
            "car": builtin_car,
            "cdr": builtin_cdr,
            "list": as_scheme_list,
            "append": builtin_append,
            "length": len,
            "list-ref": builtin_list_ref,
            "apply": lambda proc, args: scheme_apply(proc, args),
            "map": lambda proc, lst: lst.map(
                lambda x: scheme_apply(proc, Pair(x, nil))
            ),
            "filter": lambda pred, lst: as_scheme_list(
                *[x for x in lst if is_true(scheme_apply(pred, Pair(x, nil)))]
            ),
            "display": builtin_display,
            "newline": builtin_newline,
            "pi": math.pi,
        }
    )
    return env


# 6. Evaluator & Special Forms (Eval) ------------------------------------


def check_form(expr: Pair, min_len: int, max_len: int | None = None) -> None:
    if not is_proper_list(expr):
        raise SchemeSyntaxError(f"malformed expression: {to_scheme(expr)}")
    length = len(expr)
    if length < min_len or (max_len is not None and length > max_len):
        raise SchemeSyntaxError(f"bad syntax in {to_scheme(expr)}")


def check_params(params: Any) -> list[Symbol]:
    require(is_proper_list(params), "parameter list must be a proper list")
    result: list[Symbol] = []
    for p in params:
        require(is_symbol(p), f"invalid parameter name: {to_scheme(p)}")
        require(p not in result, f"duplicate parameter name: {p}")
        result.append(p)
    return result


def eval_all(expressions: Pair | _Nil, env: Env) -> Any:
    """Evaluate a sequence of expressions in order and return the last value."""
    result: Any = UNSPECIFIED
    for expr in expressions:
        result = scheme_eval(expr, env)
    return result


def scheme_eval(expr: Any, env: Env) -> Any:
    """Evaluate a Scheme expression in environment env."""
    # 1. Symbols are looked up in the environment
    if is_symbol(expr):
        return env.find(expr)[expr]

    # 2. Self-evaluating atoms (numbers, booleans, String literals)
    if not isinstance(expr, Pair):
        if expr is nil:
            raise SchemeSyntaxError("cannot evaluate an empty list ()")
        return expr

    check_form(expr, 1)
    first = expr.first
    rest = expr.second
    form = first if is_symbol(first) else None

    # 3. Special forms
    if form == "quote":
        check_form(expr, 2, 2)
        return rest.first

    if form == "if":
        check_form(expr, 3, 4)
        if is_true(scheme_eval(rest.first, env)):
            return scheme_eval(rest.second.first, env)
        if len(expr) == 4:
            return scheme_eval(rest.second.second.first, env)
        return UNSPECIFIED

    if form == "define":
        check_form(expr, 3)
        target = rest.first
        if is_symbol(target):
            check_form(expr, 3, 3)
            env[target] = scheme_eval(rest.second.first, env)
            return UNSPECIFIED
        if isinstance(target, Pair) and is_symbol(target.first):
            name = target.first
            params = check_params(target.second)
            env[name] = Procedure(params, rest.second, env)
            return UNSPECIFIED
        raise SchemeSyntaxError(f"invalid define target: {to_scheme(target)}")

    if form == "set!":
        check_form(expr, 3, 3)
        target = rest.first
        require(is_symbol(target), "set! target must be a symbol")
        env.find(target)[target] = scheme_eval(rest.second.first, env)
        return UNSPECIFIED

    if form == "lambda":
        check_form(expr, 3)
        params = check_params(rest.first)
        return Procedure(params, rest.second, env)

    if form == "begin":
        return eval_all(rest, env)

    if form == "let":
        check_form(expr, 3)
        bindings = rest.first
        require(is_proper_list(bindings), "let bindings must be a list")
        names: list[Symbol] = []
        values: list[Any] = []
        for binding in bindings:
            require(
                isinstance(binding, Pair) and is_proper_list(binding) and len(binding) == 2,
                f"invalid let binding: {to_scheme(binding)}",
            )
            name = binding.first
            require(is_symbol(name), "let binding name must be a symbol")
            require(name not in names, f"duplicate let binding: {name}")
            names.append(name)
            values.append(scheme_eval(binding.second.first, env))
        return eval_all(rest.second, Env(names, values, env))

    if form == "and":
        result: Any = True
        for sub_expr in rest:
            result = scheme_eval(sub_expr, env)
            if not is_true(result):
                return False
        return result

    if form == "or":
        for sub_expr in rest:
            result = scheme_eval(sub_expr, env)
            if is_true(result):
                return result
        return False

    if form == "cond":
        for idx, clause in enumerate(rest):
            require(
                isinstance(clause, Pair) and is_proper_list(clause),
                f"invalid cond clause: {to_scheme(clause)}",
            )
            is_else = is_symbol(clause.first) and clause.first == "else"
            if is_else:
                require(idx == len(rest) - 1, "else must be the last clause in cond")
                test_val: Any = True
            else:
                test_val = scheme_eval(clause.first, env)
            if is_true(test_val):
                if clause.second is nil:
                    return test_val
                return eval_all(clause.second, env)
        return UNSPECIFIED

    # 4. Ordinary procedure call: evaluate operator and all operands, then apply
    operator_proc = scheme_eval(first, env)
    operands = rest.map(lambda sub_expr: scheme_eval(sub_expr, env))
    return scheme_apply(operator_proc, operands)


# 7. REPL & File Execution -----------------------------------------------


def evaluate(source: str, env: Env | None = None) -> tuple[list[Any], Env]:
    """Parse and evaluate all expressions in source string."""
    if env is None:
        env = standard_env()
    results = [scheme_eval(expr, env) for expr in parse_program(source)]
    return results, env


def repl(env: Env | None = None) -> None:
    """Run an interactive Read-Eval-Print Loop."""
    if env is None:
        env = standard_env()
    buffer_text = ""

    while True:
        try:
            prompt = "scm> " if not buffer_text else "...  "
            buffer_text += input(prompt) + "\n"
            try:
                expressions = parse_program(buffer_text)
            except IncompleteInput:
                continue

            for expr in expressions:
                value = scheme_eval(expr, env)
                if value is not UNSPECIFIED:
                    print(to_scheme(value))
            buffer_text = ""
        except SchemeError as err:
            print(f"{type(err).__name__}: {err}")
            buffer_text = ""
        except (EOFError, KeyboardInterrupt):
            print("\nbye")
            return


def run_file(filename: str, env: Env | None = None) -> Env:
    if env is None:
        env = standard_env()
    source = Path(filename).read_text(encoding="utf-8")
    for expr in parse_program(source):
        scheme_eval(expr, env)
    return env


if __name__ == "__main__":
    if len(sys.argv) > 2:
        raise SystemExit(f"Usage: {sys.argv[0]} [file.scm]")
    global_env = standard_env()
    if len(sys.argv) == 2:
        run_file(sys.argv[1], global_env)
    else:
        repl(global_env)
