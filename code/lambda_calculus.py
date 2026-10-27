#!/usr/bin/env python3
"""Simulating Lambda Calculus (Church Encoding) in Python."""

# 1. Numbers & Arithmetic ------------------------------------------------

ZERO = lambda p: lambda x: x
SUCC = lambda n: lambda p: lambda x: p(n(p)(x))

ONE = SUCC(ZERO)
TWO = SUCC(ONE)
THREE = SUCC(TWO)
FOUR = SUCC(THREE)
FIVE = SUCC(FOUR)

ADD = lambda m: lambda n: n(SUCC)(m)
MULTIPLY = lambda m: lambda n: lambda p: m(n(p))
POWER = lambda m: lambda n: n(m)

TEN = MULTIPLY(TWO)(FIVE)
TWENTY = MULTIPLY(FOUR)(FIVE)


# 2. Booleans & Conditionals ---------------------------------------------

TRUE = lambda x: lambda y: x
FALSE = lambda x: lambda y: y
IF = lambda b: b

NOT = lambda b: b(FALSE)(TRUE)
AND = lambda a: lambda b: a(b)(FALSE)
OR = lambda a: lambda b: a(TRUE)(b)


# 3. Pairs, Predecessor & Predicates -------------------------------------

PAIR = lambda x: lambda y: lambda f: f(x)(y)
LEFT = lambda p: p(TRUE)
RIGHT = lambda p: p(FALSE)

SLIDE = lambda p: PAIR(RIGHT(p))(SUCC(RIGHT(p)))
PRED = lambda n: LEFT(n(SLIDE)(PAIR(ZERO)(ZERO)))
SUB = lambda m: lambda n: n(PRED)(m)

IS_ZERO = lambda n: n(lambda _: FALSE)(TRUE)
LEQ = lambda m: lambda n: IS_ZERO(SUB(m)(n))
EQ = lambda m: lambda n: AND(LEQ(m)(n))(LEQ(n)(m))


# 4. Recursion (Z Combinator) & Modulo -----------------------------------

Z = lambda f: (lambda x: f(lambda y: x(x)(y)))(lambda x: f(lambda y: x(x)(y)))

MOD = Z(
    lambda recurse: lambda m: lambda n: IF(LEQ(n)(m))(
        lambda _: recurse(SUB(m)(n))(n)
    )(
        lambda _: m
    )(ZERO)
)


# 5. Lists, Range & High-Order List Operations ---------------------------

# A list node is encoded as PAIR(is_empty)(PAIR(head)(tail)).
EMPTY = PAIR(TRUE)(TRUE)
UNSHIFT = lambda l: lambda x: PAIR(FALSE)(PAIR(x)(l))
IS_EMPTY = LEFT
FIRST = lambda l: LEFT(RIGHT(l))
REST = lambda l: RIGHT(RIGHT(l))

RANGE = Z(
    lambda recurse: lambda m: lambda n: IF(LEQ(m)(n))(
        lambda _: UNSHIFT(recurse(SUCC(m))(n))(m)
    )(
        lambda _: EMPTY
    )(ZERO)
)

FILTER = Z(
    lambda recurse: lambda f: lambda l: IF(IS_EMPTY(l))(
        lambda _: EMPTY
    )(
        lambda _: IF(f(FIRST(l)))(
            lambda _: UNSHIFT(recurse(f)(REST(l)))(FIRST(l))
        )(
            lambda _: recurse(f)(REST(l))
        )(ZERO)
    )(ZERO)
)

MAP = Z(
    lambda recurse: lambda l: lambda f: IF(IS_EMPTY(l))(
        lambda _: EMPTY
    )(
        lambda _: UNSHIFT(recurse(REST(l))(f))(f(FIRST(l)))
    )(ZERO)
)

EACH = Z(
    lambda recurse: lambda l: lambda f: IF(IS_EMPTY(l))(
        lambda _: ZERO
    )(
        lambda _: (lambda _: recurse(REST(l))(f))(f(FIRST(l)))
    )(ZERO)
)


# 6. Helper Functions (Bridge to Python) ---------------------------------

to_integer = lambda n: n(lambda x: x + 1)(0)
to_boolean = lambda b: b(True)(False)


def to_list(l):
    """Convert a Church-encoded list into a Python list."""
    result = []
    while not to_boolean(IS_EMPTY(l)):
        result.append(FIRST(l))
        l = REST(l)
    return result


# 7. Target Program: Numbers in 1..19 divisible by 3 or 5 ----------------

IS_DIVISIBLE_BY = lambda d: lambda n: IS_ZERO(MOD(n)(d))
WANTED = lambda n: OR(IS_DIVISIBLE_BY(THREE)(n))(IS_DIVISIBLE_BY(FIVE)(n))

NUMBERS = RANGE(ONE)(PRED(TWENTY))
RESULT = FILTER(WANTED)(NUMBERS)


if __name__ == "__main__":
    EACH(RESULT)(lambda n: print(to_integer(n)))
