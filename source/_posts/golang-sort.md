title: 经典排序算法的golang实现
date: 2014-07-29 10:32:19
tags: 算法
---
> 冒泡排序

![Bubble Sort](http://upload.wikimedia.org/wikipedia/commons/0/06/Bubble-sort.gif)

```golang
    func (a Array) BubbleSort() {
        for i := 0; i < len(a); i++ {
            for j := 0; j < len(a)-i-1; j++ {
                if a[j] > a[j+1] {
                    a[j], a[j+1] = a[j+1], a[j]
                }
            }
        }
    }
```

 > 插入排序

![Insert Sort](http://upload.wikimedia.org/wikipedia/commons/0/0f/Insertion-sort-example-300px.gif)

```golang
    func (a Array) InsertSort() {
        for i := 0; i < len(a); i++ {
            tmp := a[i]
            j := i - 1
            for j >= 0 && a[j] > tmp {
                a[j+1] = a[j]
                j--
            }
            a[j+1] = tmp
        }
    }
```

> 快速排序

![Quick Sort](http://upload.wikimedia.org/wikipedia/commons/9/9c/Quicksort-example.gif)

```golang
    func (a Array) QuickSort(left, right int) {
        if left < right {
            key := a[left]
            low := left
            high := right
            for low < high {
                for low < high && a[high] > key {
                    high--
                }
                a[low] = a[high]
                for low < high && a[low] < key {
                    low++
                }
                a[high] = a[low]
            }
            a[low] = key
            a.QuickSort(left, low-1)
            a.QuickSort(low+1, right)
        }
    }
```

> 完整代码

```golang
    package main

    type Array []int32

    func (a Array) BubbleSort() {
        for i := 0; i < len(a); i++ {
            for j := 0; j < len(a)-i-1; j++ {
                if a[j] > a[j+1] {
                    a[j], a[j+1] = a[j+1], a[j]
                }
            }
        }
    }
    func (a Array) InsertSort() {
        for i := 0; i < len(a); i++ {
            tmp := a[i]
            j := i - 1
            for j >= 0 && a[j] > tmp {
                a[j+1] = a[j]
                j--
            }
            a[j+1] = tmp
        }

    }
    func (a Array) QuickSort(left, right int) {
        if left < right {
            key := a[left]
            low := left
            high := right
            for low < high {
                for low < high && a[high] > key {
                    high--
                }
                a[low] = a[high]
                for low < high && a[low] < key {
                    low++
                }
                a[high] = a[low]
            }
            a[low] = key
            a.QuickSort(left, low-1)
            a.QuickSort(low+1, right)
        }
    }
    func main() {
        var a Array = []int32{1, 5, 2, 6, 3, 9, 7, 4}

        //a.Bubble()
        //a.Insert()
        a.QuickSort(0, len(a)-1)
        for _, i := range a {
            print(i)
        }

    }
```