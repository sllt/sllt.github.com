title: brainfuck解释器的实现(一)
date: 2015-03-26 13:41:46
tags: nim
---

Brainfuck，是一种极小化的，符合图灵完全思想的编程语言。更多资料[Brainfuck](http://zh.wikipedia.org/wiki/Brainfuck)

这种语言基于一个简单的机器模型，除了指令，这个机器还包括：一个以字节为单位、被初始化为零的数组、一个指向该数组的指针（初始时指向数组的第一个字节）、以及用于输入输出的两个字节流。

开始实现（使用nim）：
1 . 读取输入的代码

```
import os

let code = if paramCount() > 0: readFile paramStr(1)
           else: readAll stdin
```
2 . 创建初始值为0的数组，并初始一个指向它的指针

```
var
  tape: seq[char] = newSeq[char]()
  codePos: int = 0
  tapePos: int = 0
```
3 . 根据输入来做相应操作

```
case code[codePos]
of '+': inc tape[tapePos]
of '-': dec tape[tapePos]
of '>': inc tapePos
of '<': dec tapePos
of '.': stdout.write tape[tapePos]
of ',': tape[tapePos] = stdin.readChar
else: discard
```
4 . 处理“[”跟“]”

```
if code[codePos] == '[':
  inc codePos
  let oldPos = codePos
  while run(tape[tapePos] == '\0'):
    codePos = oldPos
elif code[codePos] == ']':
  return tape[tapePos] != '\0'
```
至此，解释器完成，但是处理速度相当慢...
完整代码如下:
```
import os

let code = if paramCount() > 0: readFile paramStr(1)
           else: readAll stdin

var
  tape: seq[char] = newSeq[char]()
  codePos: int = 0
  tapePos: int = 0
  
proc run(skip = false): bool =
  # echo "codePos: ", codePos, " tapePos:", tapePos
  while tapePos >= 0 and codePos < code.len:
    if tapePos >= tape.len:
      tape.add '\0'
    if code[codePos] == '[':
      inc codePos
      let oldPos = codePos
      while run(tape[tapePos] == '\0'):
        codePos = oldPos
    elif code[codePos] == ']':
      return tape[tapePos] != '\0'
    elif not skip:
      case code[codePos]
      of '+': inc tape[tapePos]
      of '-': dec tape[tapePos]
      of '>': inc tapePos
      of '<': dec tapePos
      of '.': stdout.write tape[tapePos]
      of ',': tape[tapePos] = stdin.readChar
      else: discard
    
    inc codePos

discard run()
```
