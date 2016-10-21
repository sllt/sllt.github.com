title: 使用Python模拟Lambda演算
date: 2016-04-24 15:34:47
tags: ['python', 'lambda']
---

我们将从下面这段程序开始：

```python
for i in range(1,20):
    if i % 3 == 0 or i % 5 == 0:
        print(i)
```

这段程序将打印出1~19之间能被3或5整除的数字。我们将不使用任何Python内建类型及方法来实现上面程序的功能。



## 1 数字

数字的特征可以简单的描述为某一个动作的迭代。比如吃了6个苹果，6就表示重复的进行了n次的吃这个动作。相同的，我们也可以在程序中用某一个函数被调用了几次来表示数字。

比如数字`1`可以表示成如下代码：

```python
def one(p, x):
  return p(x)
```

依照同样的定义，我们可以这么表示`2`:

```python
def two(p, x):
   return p(p(x))
```

那么， 如何表示`0`呢？ 我们传入`p`但是不进行调用，就可以表示0了：

```python
def zero(p, x):
    return x
```

用`lambda`表达式表示如下：

```python
ZERO = lambda p: lambda x: x
ONE = lambda p: lambda x: p(x)
TWO = lambda p: lambda x: p(p(x))
THREE = lambda p: lambda x: p(p(p(x)))
```

让我们来实现一个函数来将这些lambda表达式这换成Python的数字，依次来支持一些其他特性，比如使用`range`函数：

```python
to_integer = lambda n: n(lambda x: x+1)(0)
```

同样的，`5`、`20`可以这么表示：

```python
FIVE = lambda p: lambda x: p(p(p(p(p(x)))))

TWENTY = lambda p: lambda x: p(p(p(p(p(p(p(p(p(p(p(p(p(p(p(p(p(p(p(p(x))))))))))))))))))))
```

现在，我们的程序可以这么表示：

```python
for i in range(to_integer(ONE), to_integer(TWENTY)):
    if i % to_integer(THREE) == to_integer(ZERO) or i % to_integer(FIVE) == to_integer(ZERO):
        print(i)
```

# 2 布尔值    


待写...
