# python虚拟机
- Python是⼀种半编译半解释型运⾏环境。
- 首先，它会在模块“载入”时将源码编译成字节码（Byte Code）。
- 而后，这些字节码会被虚拟机在一个“巨大”的核心函数里解释执行。

# 类型和对象
python中一切都是对象。

```c
#define PyObject_HEAD
    Py_ssize_t ob_refcnt;
    struct _typeobject *ob_type;

typedef struct _object {
    PyObject_HEAD
} PyObject;

typedef struct {
    PyObject_HEAD
    long ob_ival;
} PyIntObject;
```
可以用sys中的函数测试一下。
```python
>>> import sys

>>> x = 0x1234

>>> sys.getsizeof(x)

>>> sys.getrefcount(x) # 获取引用计数

>>> y = x
>>> sys.getrefcount(x) # 引用计数会增加

>>> def y
>>> sys.getrefcount(x) # 引用计数减少
```

# 内存管理
为提升执行性能，Python在内存管理上做了大量工作。最直接的做法就是用内存池来减少操作系统内存分配和回收操作，那些小于等于256字节对象，将直接从内存池中获取存储空间。
根据需要，虚拟机每次从操作系统申请一块256KB，取名为arena的大块内存。并按系统页大小，划分成多个pool。每个pool继续分割成n个大小相同的block，这是内存池最小存储单位。
block ⼤⼩是 8 的倍数，也就是说存储 13 字节大⼩的对象，需要找 block 大⼩为 16 的 pool 获取空闲块。所有这些都⽤头信息和链表管理起来，以便快速查找空闲区域进⾏行分配。
⼤于 256 字节的对象，直接⽤ malloc 在堆上分配内存。程序运⾏中的绝⼤多数对象都⼩于这个阈值，因此内存池策略可有效提升性能。
当所有 arena 的总容量超出限制 (64MB) 时，就不再请求新的 arena 内存。⽽是如同 "⼤对象" 一 样，直接在堆上为对象分配内存。另外，完全空闲的 arena 会被释放，其内存交还给操作系统。

# 不可变类型
- int, long, str, tuple, frozenset

# 引用计数
Python 默认采⽤引⽤计数来管理对象的内存回收。当引⽤计数为 0 时，将⽴即回收该对象内存， 要么将对应的 block 块标记为空闲，要么返还给操作系统。
为观察回收行为，我们用__del__监控对象释放。

```python
>>> class User(object):
...     def __del__(self):
...         print("Will be dead!")
>>> a = User()
>>> b = a
>>> import sys
>>> sys.getrefcount(a)
3
>>> del a
>>> sys.getrefcount(b)  # 删除引用，计数减小。
2
>>> del b               # 删除最后一个引用，计数器为 0，对象被回收。
Will be dead!
```
某些内置类型，比如小整数，因为缓存的缘故，计数永远不会为 0，直到进程结束才由虚拟机清理函数释放。
除了直接引⽤外，Python 还⽀持弱引用。允许在不增加引⽤计数，不妨碍对象回收的情况下间接引⽤对象。但不是所有类型都⽀持弱引⽤，比如 list、dict ，弱引⽤会引发异常。
改用弱引用回调监控对象回收。
```python
>>> import sys, weakref
>>> class User(object): pass

>>> def callback(r):                    # 回调函数会在原对象被回收时调⽤。
...     print("weakref object:", r)
...     print("target object dead!")



 
>>> a = User()

>>> r = weakref.ref(a, callback)         # 创建弱引⽤对象。

>>> sys.getrefcount(a)              # 可以看到弱引⽤没有导致目标对象引用计数增加。
2                                   # 计数 2 是因为 getrefcount 形参造成的。
>>> r() is a                        # 透过弱引用可以访问原对象。
True

>>> del a                           # 原对象回收，callback 被调用。
weakref object: <weakref at 0x10f99a368; dead>
target object dead!
>>> hex(id(r))                      # 通过对比，可以看到 callback 参数是弱引用对象。
'0x10f99a368'                       # 因为原对象已经死亡。
>>> r() is None                     # 此时弱引⽤只能返回 None。也可以此判断原对象死亡。
True
```

引⽤计数是⼀种简单直接，并且⼗分⾼效的内存回收⽅式。⼤多数时候它都能很好地⼯作，除了循环引⽤造成计数故障。简单明显的循环引⽤，可以⽤弱引⽤打破循环关系。但在实际开发中，循环引⽤的形成往往很复杂，可能由 n 个对象间接形成⼀个⼤的循环体，此时只有靠 GC 去回收了。

# 垃圾收集
事实上，Python 拥有两套垃圾回收机制。除了引⽤计数，还有个专⻔处理循环引⽤用的 GC。通常我们提到垃圾回收时，都是指这个 "Reference Cycle Garbage Collection"。
能引发循环引⽤问题的，都是那种容器类对象，⽐如 list、set、object 等。对于这类对象，虚拟机在为其分配内存时，会额外添加⽤于追踪的 PyGC_Head。这些对象被添加到特殊链表⾥，以便 GC 进⾏行管理。
```c
typedef union _gc_head {
    struct {
        union _gc_head *gc_next;
        union _gc_head *gc_prev;
    } gc;
    long double dummy;
} PyGC_Head;
```
当然，这并不表⽰示此类对象⾮得 GC 才能回收。如果不存在循环引⽤，自然是积极性更⾼的引用计数机制抢先给处理掉。也就是说，只要不存在循环引⽤，理论上可以禁⽤ GC。当执⾏某些密集运算时，临时关掉 GC 有助于提升性能。
```python
>>> import gc

>>> class User(object):
...     def __del__(self):
...         print(hex(id(self)), "will be dead!")

>>> gc.disable()    # 关掉 GC

>>> a = User()
>>> del a           # 对象正常回收，引用计数不会依赖 GC.
0x10fddf590 will be dead!
```
Python GC 同样将要回收的对象分成 3 级代龄。GEN0 管理新近加⼊的年轻对象，GEN1 则是在上次回收后依然存活的对象，剩下 GEN2 存储的都是⽣命周期极⻓的家伙。 每级代龄都有⼀个最⼤容量阈值，每次 GEN0 对象数量超出阈值时，都将引发垃圾回收操作。
```c
#define NUM_GENERATIONS 3

/* linked lists of container objects */
static struct gc_generation generations[NUM_GENERATIONS] = {
    /* PyGC_Head,                       threshold,      count */
    {{{GEN_HEAD(0), GEN_HEAD(0), 0}},   700,            0},
    {{{GEN_HEAD(1), GEN_HEAD(1), 0}},   10,             0},
    {{{GEN_HEAD(2), GEN_HEAD(2), 0}},   10,             0},
};
```
GC ⾸先检查 GEN2，如阈值被突破，那么合并 GEN2、GEN1、GEN0 ⼏个追踪链表。如果没有超出，则检查 GEN1。GC 将存活的对象提升代龄，而那些可回收对象则被打破循环引⽤，放到专⻔的列表等待回收。
```python
>>> gc.get_threshold()      # 获取各级代龄阈值
(700, 10, 10)

>>> gc.get_count()          # 各级代龄链表跟踪的对象数量
(203, 0, 5)
```
包含__del__方法的循环引用对象，永远不会被GC回收，直至进程终止。
这回不能偷懒用__del__监控对象回收了，改用weakref。
```python
>>> import gc, weakref

>>> class User(object): pass
>>> def callback(r): print(r, "dead")

>>> gc.disable()

>>> a = User(); wa = weakref.ref(a, callback)
>>> b = User(); wb = weakref.ref(b, callback)

>>> a.b = b; b.a = a            # 形成循环引用关系。

>>> del a; del b                # 删除名字引用。
>>> wa(), wb()                  # 显然，计数机制对循环引用无效。

>>> gc.enable()                 # 开启 GC。
>>> gc.isenabled()              # 可以用 isenabled 确认。
True

>>> gc.collect()                # 因为没有达到阈值，我们手工启动回收。
```
一旦有了__del__，GC 就拿循环引用没办法了。

```python
>>> import gc, weakref

>>> class User(object):
...     def __del__(self): pass             # 难道连空的 __del__ 也不行？

>>> def callback(r): print(r, "dead!")

>>> gc.set_debug(gc.DEBUG_STATS | gc.DEBUG_LEAK)    # 输出更详细的回收状态信息。
>>> gc.isenabled()                                  # 确保 GC 在工作。

>>> a = User(); wa = weakref.ref(a, callback)
>>> b = User(); wb = weakref.ref(b, callback)
>>> a.b = b; b.a = a

>>> del a; del b
>>> gc.collect()                    # 从输出信息看，回收失败。
```
关于⽤不用 __del__ 的争论很多。⼤多数人的结论是坚决抵制，诸多 "⽜⼈" 也是这样教导新⼿的。 可毕竟 __del__ 承担了析构函数的⾓角⾊色，某些时候还是有其特定的作⽤的。⽤弱引⽤回调会造成逻辑分离，不便于维护。对于⼀些简单的脚本，我们还是能保证避免循环引⽤的，那不妨试试。就像前⾯例⼦中⽤来监测对象回收，就很⽅便。

# 编译
Python 实现了栈式虚拟机 (Stack-Based VM) 架构，通过与机器⽆关的字节码来实现跨平台执⾏能⼒。这种字节码指令集没有寄存器，完全以栈 (抽象层⾯) 进⾏指令运算。尽管很简单，但对普通开发⼈员⽽言，是⽆需关⼼的细节。
要运⾏Python语⾔编写的程序，必须将源码编译成字节码。通常情况下，编译器会将源码转换成字节码后保存在 pyc 文件中。
```python
>>> def foo(a):
...     x = 3
...     return x + a
>>> import dis
>>> dis.dis(foo.func_code)    
```