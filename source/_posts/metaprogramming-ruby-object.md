title: ruby元编程-对象模型
date: 2014-12-02 12:46:45
tags: ruby
---
ruby中的对象
=================
在ruby中任何东西都是对象，甚至是nil、类等都是对象。
比如下面的例子：
```ruby
>> 1.methods
=> [:to_s, :inspect, :-@, :+, :-, :*, :/, :div, :%, :modulo, :divmod, :fdiv, :**, :abs, :magnitude, :==, :===, :<=>, :>, :>=, :<, :<=, :~, :&, :|, :^, :[], :<<, :>>, :to_f, :size, :bit_length, :zero?, :odd?, :even?, :succ, :integer?, :upto, :downto, :times, :next, :pred, :chr, :ord, :to_i, :to_int, :floor, :ceil, :truncate, :round, :gcd, :lcm, :gcdlcm, :numerator, :denominator, :to_r, :rationalize, :singleton_method_added, :coerce, :i, :+@, :eql?, ......]
>> 1.class
=> Fixnum
>> Fixnum.class
=> Class
>> Class.class
=> Class
```
在ruby中对象是由一组实例变量和一个类的引用组成的，对象的方法存在于对象所在的类中。

猴子补丁
===================
所谓猴子补丁就是不改变源代码而对功能进行追加和变更。
### 开放类
```ruby
class Foo
    def hello
        "hello world !"
    end
end
class Foo
    def plus(arg1,arg2)
        arg1 + arg2
    end
end
>> foo = Foo.new
=> #<Foo:0xb8c2b574>
>> foo.hello
=> "hello world !"
>> foo.plus(3,4)
=> 7
```
第二个class Foo中并不是新建了一个Foo类，而是重新打开了Foo类，给其新增了一个叫plus的方法。在ruby中所有的类都是开放类，你可以自由的开发String、Fixnum等基本的数据类型给它增加功能.

ruby中的类
===================
上文说类也是一个对象，那么什么是类呢？所谓类就是一个Class类的实例加一组实例方法和一个对其父类的引用。既然这样，就可以这样定义一个类，虽然结果也会产生一个类：
```
hello = Class.new
```
一般情况下，类这么定义：
```
class Hello
end
```
其区别在于Hello是个常量（在ruby中，任何以大写字母开头的引用即为常量）而已。那么，class 包裹起来的一块东西又是什么呢？其只不过是个作用域。
```ruby
class Hello
    puts "hello world"
    123
    def say
        "hello sllt"
    end
end
```

self
====================
每一行代码都会在一个对象中执行，这个对象就是当前对象（self)。
```ruby
class MyClass
    self
end

=> MyClass

class MyClass
    def say
        "hello"
    end
    def put_self
        self
        say
    end
end

>> m = MyClass.new
>> m.put_self
=> #<MyClass:0xb93de870> "hello"
```
通过上面代码可以看出：
* 当定义一个模块和类时，其自身扮演self的角色。
* 当调用一个方法时，接收者会扮演self的角色。
