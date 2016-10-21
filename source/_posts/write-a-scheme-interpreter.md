title: 如何写一个Scheme解释器
date: 2015-11-17 14:02:14
tags: [scheme, python]
---

本文假设你会使用python。

我们会先实现一个scheme语法的简单计算器，以便了解实现一个解释器的简单步骤，接着会逐步给此计算器增加功能，使其成为一个完整的scheme解释器。

[Scheme-wikipedia](https://zh.wikipedia.org/wiki/Scheme)这里有关于scheme的更详细的介绍。

## 1.1 Scheme语法式的计算器
此简化的计算器包含加（+）、减（-）、乘（*）、除（/）四个表达式。

加法和乘法表达式可以接收任意数量的参数：

```scheme
> (+ 1 2 3 4 )
10
> (+)
0
> (* 1 2 3 4)
24
> (*)
1
```

减法(`-`)有两种情况，当传入一个参数时，会求这个数的相反数；传入两个或两个以上的操作时，会
进行减法操作， 例如`(- 10 1 2 3)` 等同于`10 - 1 - 2 - 3`。除法(`/`)也有两种情况。

```scheme
> (- 10 1 2 3)
4
> (- 3)
-3
> (/ 15 12)
1.25
> (/ 30 5 2)
3
> (/ 10)
0.1
```

一个表达式执行的时候，先会对其子表达式求值，将所得结果再执行所返回的值。

```scheme
> (- 100 ( * 7 ( + 8 (/ -12 -3))))
16.0
```
接下来我们将会用python编写此求值器的解释器。大致步骤是读取一串字符串(例如: `(+ 1 2)` )，将其转换成表达式树，然后遍历表达式树，对其求值，再将求得的值输出出来。

## 1.2 表达式树

通过观察会发现所有的scheme表达式都是一个列表，这个列表的第一个值是函数名， 后面的值是这个函数
的参数。



```python
>>>> s = Pair(1, Pair(2, nil))
>>>> s
Pair(1, Pair(2, nil))
>>>> print(s)
(1 2)
```

next

```python
>>>> len(s)
2
>>>> s[1]
2
>>>> print(s.map(lambda x: x + 4))
(5 6)
```

next

```python
>>>> expr = Pair('+', Pair('*', Pair(3, Pair(4, nil))), Pair(5, nil)))
>>>> print(expr)
(+ （* 3 4） 5）
>>>> expr.second.first.second.first.second.first
3
```

## 1.3 解析表达式

```python
>>>> tokenize_line('(+ 1 (* 2.3 45))')
['(', '+', 1, '(', '*', 2.3, 45, ')', ')', ')']
```


next

```python
>>> lines = ['(+ 1', '   (* 2.3 45))']
>>> expression = scheme_read(Buffer(tokenize_lines(lines)))
>>> expression
Pair('+', Pair(1, Pair(Pair('*', Pair(2.3, Pair(45, nil))), nil)))
>>> print(expression)
(+ 1 (* 2.3 45))
```

## 1.4 求值


```python
>>> def calc_eval(exp):
        """Evaluate a Calculator expression."""
        if type(exp) in (int, float):
            return simplify(exp)
        elif isinstance(exp, Pair):
            arguments = exp.second.map(calc_eval)
            return simplify(calc_apply(exp.first, arguments))
        else:
            raise TypeError(exp + ' is not a number or call expression')


```

next

```python
>>> def calc_apply(operator, args):
        """Apply the named operator to a list of args."""
        if not isinstance(operator, str):
            raise TypeError(str(operator) + ' is not a symbol')
        if operator == '+':
            return reduce(add, args, 0)
        elif operator == '-':
            if len(args) == 0:
                raise TypeError(operator + ' requires at least 1 argument')
            elif len(args) == 1:
                return -args.first
            else:
                return reduce(sub, args.second, args.first)
        elif operator == '*':
            return reduce(mul, args, 1)
        elif operator == '/':
            if len(args) == 0:
                raise TypeError(operator + ' requires at least 1 argument')
            elif len(args) == 1:
                return 1/args.first
            else:
                return reduce(truediv, args.second, args.first)
        else:
            raise TypeError(operator + ' is an unknown operator')

```

next


```python
>>> calc_apply('+', as_scheme_list(1, 2, 3))
6
>>> calc_apply('-', as_scheme_list(10, 1, 2, 3))
4
>>> calc_apply('*', nil)
1
>>> calc_apply('*', as_scheme_list(1, 2, 3, 4, 5))
120
>>> calc_apply('/', as_scheme_list(40, 5))
8.0

```

next

```python

>>> print(exp)
(+ (* 3 4) 5)
>>> calc_eval(exp)
17
```

next

```python
>>> def read_eval_print_loop():
        """Run a read-eval-print loop for calculator."""
        while True:
            src = buffer_input()
            while src.more_on_line:
                expression = scheme_read(src)
                print(calc_eval(expression))
```

next

```python

> (* 1 2 3)
6
> (+)
0
> (+ 2 (/ 4 8))
2.5
> (+ 2 2) (* 3 3)
4
9
> (+ 1
     (- 23)
     (* 4 2.5))
-12

```

next

```python
>>> def read_eval_print_loop():
        """Run a read-eval-print loop for calculator."""
        while True:
            try:
                src = buffer_input()
                while src.more_on_line:
                    expression = scheme_read(src)
                    print(calc_eval(expression))
            except (SyntaxError, TypeError, ValueError, ZeroDivisionError) as err:
                print(type(err).__name__ + ':', err)
            except (KeyboardInterrupt, EOFError):  # <Control>-D, etc.
                print('Calculation completed.')
                return
```

next

```python

> )
SyntaxError: unexpected token: )
> 2.3.4
ValueError: invalid numeral: 2.3.4
> +
TypeError: + is not a number or call expression
> (/ 5)
TypeError: / requires exactly 2 arguments
> (/ 1 0)
ZeroDivisionError: division by zero

```

next


未完待续...
