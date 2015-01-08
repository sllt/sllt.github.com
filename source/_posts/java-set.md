title: HashSet的实现
date: 2014-10-07 20:24:25
tags: java
---
Set是由若干个无序且不重复的对象所组成。它既包含Array的运算功能,同时又兼有Hash的高速搜索功能。HashSet是基于HashMap实现的.
```java
import java.util.Collection;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Set;

public class MySet<E> implements Set<E>{
    private HashMap<E, Object> map;
    private static final Object notUse=new Object();
    
    public MySet() {
        map = new HashMap<E,Object>();
    }
    @Override
    public Iterator<E> iterator() {
        return map.keySet().iterator();
    }

    @Override
    public boolean add(E e) {
        return map.put(e, notUse) == null;
    }

    @Override
    public boolean addAll(Collection<? extends E> c) {
        return false;
    }

    @Override
    public void clear() {
        map.clear();
    }

    @Override
    public boolean contains(Object o) {
        return map.containsKey(o);
    }

    @Override
    public boolean containsAll(Collection<?> c) {
        return false;
    }

    @Override
    public boolean isEmpty() {
        return map.isEmpty();
    }

    @Override
    public boolean remove(Object o) {
        return map.remove(o) == notUse;
    }

    @Override
    public boolean removeAll(Collection<?> c) {
        return false;
    }

    @Override
    public boolean retainAll(Collection<?> c) {
        return false;
    }

    @Override
    public int size() {
        return map.size();
    }

    @Override
    public Object[] toArray() {
        
        return null;
    }

    @Override
    public <T> T[] toArray(T[] a) {
        return null;
    }
}
```