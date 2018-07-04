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

# 微型解释器

为了让说明更具体，让我们从一个非常小的解释器开始。它只能计算两个数的和，只能理解三个指令。它执行的所有代码只是这三个指令的不同组合。下面就是这三个指令：
- LOAD_VALUE
- ADD_TWO_VALUES
- PRINT_ANSWER

我们不关心词法、语法和编译，所以我们也不在乎这些指令集是如何产生的。你可以想象，当你写下 7 + 5，然后一个编译器为你生成那三个指令的组合。如果你有一个合适的编译器，你甚至可以用 Lisp 的语法来写，只要它能生成相同的指令。
假设
```
7 + 5
```
生成这样的指令集：
```python
what_to_execute = {
    "instructions": [("LOAD_VALUE", 0),  # the first number
                     ("LOAD_VALUE", 1),  # the second number
                     ("ADD_TWO_VALUES", None),
                     ("PRINT_ANSWER", None)],
    "numbers": [7, 5] }
```

Python 解释器是一个栈机器（stack machine），所以它必须通过操作栈来完成这个加法（见下图）。解释器先执行第一条指令，LOAD_VALUE，把第一个数压到栈中。接着它把第二个数也压到栈中。然后，第三条指令，ADD_TWO_VALUES，先把两个数从栈中弹出，加起来，再把结果压入栈中。最后一步，把结果弹出并输出。

![微型虚拟机](http://jbcdn2.b0.upaiyun.com/2016/09/d4ab3c3b1c2df4a34ffb60fc2f32485d.png)

LOAD_VALUE这条指令告诉解释器把一个数压入栈中，但指令本身并没有指明这个数是多少。指令需要一个额外的信息告诉解释器去哪里找到这个数。所以我们的指令集有两个部分：指令本身和一个常量列表。（在 Python 中，字节码就是我们所称的“指令”，而解释器“执行”的是代码对象。）

为什么不把数字直接嵌入指令之中？想象一下，如果我们加的不是数字，而是字符串。我们可不想把字符串这样的东西加到指令中，因为它可以有任意的长度。另外，我们这种设计也意味着我们只需要对象的一份拷贝，比如这个加法 7 + 7, 现在常量表 "numbers"只需包含一个[7]。

你可能会想为什么会需要除了ADD_TWO_VALUES之外的指令。的确，对于我们两个数加法，这个例子是有点人为制作的意思。然而，这个指令却是建造更复杂程序的轮子。比如，就我们目前定义的三个指令，只要给出正确的指令组合，我们可以做三个数的加法，或者任意个数的加法。同时，栈提供了一个清晰的方法去跟踪解释器的状态，这为我们增长的复杂性提供了支持。

现在让我们来完成我们的解释器。解释器对象需要一个栈，它可以用一个列表来表示。它还需要一个方法来描述怎样执行每条指令。比如，LOAD_VALUE会把一个值压入栈中。

```python
class Interpreter:
    def __init__(self):
        self.stack = []
 
    def LOAD_VALUE(self, number):
        self.stack.append(number)
 
    def PRINT_ANSWER(self):
        answer = self.stack.pop()
        print(answer)
 
    def ADD_TWO_VALUES(self):
        first_num = self.stack.pop()
        second_num = self.stack.pop()
        total = first_num + second_num
        self.stack.append(total)
```
这三个方法完成了解释器所理解的三条指令。但解释器还需要一样东西：一个能把所有东西结合在一起并执行的方法。这个方法就叫做`run_code`，它把我们前面定义的字典结构`what-to-execute`作为参数，循环执行里面的每条指令，如果指令有参数就处理参数，然后调用解释器对象中相应的方法。
```python
    def run_code(self, what_to_execute):
        instructions = what_to_execute["instructions"]
        numbers = what_to_execute["numbers"]
        for each_step in instructions:
            instruction, argument = each_step
            if instruction == "LOAD_VALUE":
                number = numbers[argument]
                self.LOAD_VALUE(number)
            elif instruction == "ADD_TWO_VALUES":
                self.ADD_TWO_VALUES()
            elif instruction == "PRINT_ANSWER":
                self.PRINT_ANSWER()
```
为了测试，我们创建一个解释器对象，然后用前面定义的`7 + 5`的指令集来调用`run_code`。
```python
    interpreter = Interpreter()
    interpreter.run_code(what_to_execute)
```
显然，它会输出 12。
尽管我们的解释器功能十分受限，但这个过程几乎和真正的 Python 解释器处理加法是一样的。这里，我们还有几点要注意。

# 小整数池

在 64 位平台上，int 类型是 64 位整数 (sys.maxint)，这显然能应对绝⼤多数情况。整数是虚拟机特殊照顾对象:
- 从堆上按需申请名为 PyIntBlock 的缓存区域存储整数对象。
- 使⽤用固定数组缓存 [-5, 257) 之间的⼩数字，只需计算下标就能获得指针。
- PyIntBlock 内存不会返还给操作系统，直⾄至进程结束。
看看 "⼩数字" 和 "⼤数字" 的区别:
```python
>>> a = 15
>>> b = 15

>>> a is b
True

>>> sys.getrefcount(a)
47

>>> a = 257
>>> b = 257

>>> a is b
False

>>> sys.getrefcount(a)
2
```
因`PyIntBlock`内存只复⽤不回收，同时持有⼤量整数对象将导致内存暴涨，且不会在这些对象被回收后释放内存，造成事实上的内存泄露。

# 上下文
上下⽂管理协议`(Context Management Protocol)`为代码块提供了包含初始化和清理操作的安全上下⽂环境。即便代码块发⽣异常，清理操作也会被执⾏。
- __enter__: 初始化环境，返回上下文对象。
- __exit__: 执行清理操作。返回True时，将阻止异常向外传递。

```python
>>> class MyContext(object):
...     def __init__(self, *args):
...         self._data = args
...     def __enter__(self):
...         print("__enter__")
...         return self._data
...     def __exit__(self, exc_type, exc_value, traceback):
...         if exc_type: print("Exception: ", exc_value)
...         print("__exit__")
...         return True

>>> with MyContext(1, 2, 3) as data:
...     print(data)

>>> with MyContext(1, 2, 3):
...     raise Exception("data error!")
```

# python垃圾回收

python采用的是`引用计数`机制为主，`标记-清除`和`分代收集`两种机制为辅的策略。

## 引用计数机制

python里每一个东西都是对象，它们的核心就是一个结构体：`PyObject`

```c
typedef struct_object {
    int ob_refcnt;
    struct_typeobject *ob_type;
} PyObject;
```
`PyObject`是每个对象必有的内容，其中`ob_refcnt`就是做为引用计数。当一个对象有新的引用时，它的`ob_refcnt`就会增加，当引用它的对象被删除，它的`ob_refcnt`就会减少。

```c
#define Py_INCREF(op)   ((op)->ob_refcnt++) // 增加计数
#define Py_DECREF(op) \ // 减少计数
    if (--(op)->ob_refcnt != 0) \
        ; \
    else \
        __Py_Dealloc((PyObject *)(op))
```
当引用计数为0时，该对象生命就结束了。

引用计数机制的优点：
- 简单
- 实时性：一旦没有引用，内存就直接释放了。不用像其他机制等到特定时机。实时性还带来一个好处：处理回收内存的时间分摊到了平时。

引用计数机制的缺点：
- 维护引用计数消耗资源
- 循环引用

```python
list1 = []
list2 = []
list1.append(list2)
list2.append(list1)
```

list1与list2相互引用，如果不存在其他对象对它们的引用，list1与list2的引用计数也仍然为1，所占用的内存永远无法被回收，这将是致命的。

对于如今的强大硬件，缺点1尚可接受，但是循环引用导致内存泄露，注定python还将引入新的回收机制。(标记清除和分代收集)

## 标记-清除和分代回收

GC系统所承担的工作远比"垃圾回收"多得多。实际上，它们负责三个重要任务。它们

- 为新生成的对象分配内存
- 识别那些垃圾对象，并且
- 从垃圾对象那回收内存。

### 一个简单的例子
```python
class Node:
    def __init__(self, val):
        self.value = val

print(Node(1))
print(Node(2))
```

### python的对象分配

我们用Pyhon来创建一个Node对象：

![](https://upload-images.jianshu.io/upload_images/311496-988d8ea64a9536db.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/247)

当创建对象时Python立即向操作系统请求内存。

当我们创建第二个对象的时候，再次向OS请求内存：

![](https://upload-images.jianshu.io/upload_images/311496-86f30cfff557708f.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/247)

看起来够简单吧，在我们创建对象的时候，Python会花些时间为我们找到并分配内存。

让我们回到前面提到的三个Python Node对象：

![](https://upload-images.jianshu.io/upload_images/311496-ee6ec5dc7d0494b0.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/225)

在内部，创建一个对象时，Python总是在对象的C结构体里保存一个整数，称为 引用数。期初，Python将这个值设置为1：

![](https://upload-images.jianshu.io/upload_images/311496-dafd8b72ccb56513.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/225)

值为1说明分别有个一个指针指向或是引用这三个对象。假如我们现在创建一个新的Node实例，JKL：

![](https://upload-images.jianshu.io/upload_images/311496-8269bfa7610aa83d.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/301)

与之前一样，Python设置JKL的引用数为1。然而，请注意由于我们改变了n1指向了JKL，不再指向ABC，Python就把ABC的引用数置为0了。

此刻，Python垃圾回收器立刻挺身而出！每当对象的引用数减为0，Python立即将其释放，把内存还给操作系统：

![](https://upload-images.jianshu.io/upload_images/311496-cce83cebee32f363.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/301)

上面Python回收了ABC Node实例使用的内存。Python的这种垃圾回收算法被称为引用计数。

现在来看第二例子。加入我们让n2引用n1：

![](https://upload-images.jianshu.io/upload_images/311496-ce225ae9c6aefc87.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/223)

上图中左边的DEF的引用数已经被Python减少了，垃圾回收器会立即回收DEF实例。同时JKL的引用数已经变为了2 ，因为n1和n2都指向它。

有许多原因使得不许多语言不像Python这样使用引用计数GC算法：

- 首先，它不好实现。Python不得不在每个对象内部留一些空间来处理引用数。这样付出了一小点儿空间上的代价。但更糟糕的是，每个简单的操作（像修改变量或引用）都会变成一个更复杂的操作，因为Python需要增加一个计数，减少另一个，还可能释放对象。

- 第二点，它相对较慢。虽然Python随着程序执行GC很稳健（一把脏碟子放在洗碗盆里就开始洗啦），但这并不一定更快。Python不停地更新着众多引用数值。特别是当你不再使用一个大数据结构的时候，比如一个包含很多元素的列表，Python可能必须一次性释放大量对象。减少引用数就成了一项复杂的递归过程了。

- 最后，它不是总奏效的。引用计数不能处理环形数据结构--也就是含有循环引用的数据结构。

### Python中的循环数据结构以及引用计数

通过上篇，我们知道在Python中，每个对象都保存了一个称为引用计数的整数值，来追踪到底有多少引用指向了这个对象。无论何时，如果我们程序中的一个变量或其他对象引用了目标对象，Python将会增加这个计数值，而当程序停止使用这个对象，则Python会减少这个计数值。一旦计数值被减到零，Python将会释放这个对象以及回收相关内存空间。

从六十年代开始，计算机科学界就面临了一个严重的理论问题，那就是针对引用计数这种算法来说，如果一个数据结构引用了它自身，即如果这个数据结构是一个循环数据结构，那么某些引用计数值是肯定无法变成零的。为了更好地理解这个问题，让我们举个例子。下面的代码展示了一些上周我们所用到的节点类：

![](https://upload-images.jianshu.io/upload_images/311496-f3b8a99b7a4aac48.jpg?imageMogr2/auto-orient/strip%7CimageView2/2/w/676)

我们有一个构造器(在Python中叫做 init )，在一个实例变量中存储一个单独的属性。在类定义之后我们创建两个节点，ABC以及DEF，在图中为左边的矩形框。两个节点的引用计数都被初始化为1，因为各有两个引用指向各个节点(n1和n2)。

现在，让我们在节点中定义两个附加的属性，next以及prev：

![](https://upload-images.jianshu.io/upload_images/311496-2646466e5aa4711d.jpg?imageMogr2/auto-orient/strip%7CimageView2/2/w/487)

Python中你可以在代码运行的时候动态定义实例变量或对象属性。我们设置 n1.next 指向 n2，同时设置 n2.prev 指回 n1。现在，我们的两个节点使用循环引用的方式构成了一个双端链表。同时请注意到 ABC 以及 DEF 的引用计数值已经增加到了2。这里有两个指针指向了每个节点：首先是 n1 以及 n2，其次就是 next 以及 prev。

现在，假定我们的程序不再使用这两个节点了，我们将 n1 和 n2 都设置为None。

![](https://upload-images.jianshu.io/upload_images/311496-28ee4d77afde09b0.jpg?imageMogr2/auto-orient/strip%7CimageView2/2/w/441)

好了，Python会像往常一样将每个节点的引用计数减少到1。

### 在Python中的零代(Generation Zero)

请注意在以上刚刚说到的例子中，我们以一个不是很常见的情况结尾：我们有一个“孤岛”或是一组未使用的、互相指向的对象，但是谁都没有外部引用。换句话说，我们的程序不再使用这些节点对象了，所以我们希望Python的垃圾回收机制能够足够智能去释放这些对象并回收它们占用的内存空间。但是这不可能，因为所有的引用计数都是1而不是0。Python的引用计数算法不能够处理互相指向自己的对象。

当然，上边举的是一个故意设计的例子，但是你的代码也许会在不经意间包含循环引用并且你并未意识到。事实上，当你的Python程序运行的时候它将会建立一定数量的“浮动的垃圾”，Python的GC不能够处理未使用的对象因为应用计数值不会到零。

这就是为什么Python要引入Generational GC算法的原因！Python使用链表来持续追踪活跃的对象。Python的内部C代码将其称为零代(Generation Zero)。每次当你创建一个对象或其他什么值的时候，Python会将其加入零代链表：

![](https://upload-images.jianshu.io/upload_images/311496-7c9e91a54318d569.jpg?imageMogr2/auto-orient/strip%7CimageView2/2/w/580)

从上边可以看到当我们创建ABC节点的时候，Python将其加入零代链表。请注意到这并不是一个真正的列表，并不能直接在你的代码中访问，事实上这个链表是一个完全内部的Python运行时。

相似的，当我们创建DEF节点的时候，Python将其加入同样的链表：

![](https://upload-images.jianshu.io/upload_images/311496-22b239ca5974128f.jpg?imageMogr2/auto-orient/strip%7CimageView2/2/w/649)

现在零代包含了两个节点对象。(它还将包含Python创建的每个其他值，与一些Python自己使用的内部值。)

### 检测循环引用

随后，Python会循环遍历零代列表上的每个对象，检查列表中每个互相引用的对象，根据规则减掉其引用计数。在这个过程中，Python会一个接一个的统计内部引用的数量以防过早地释放对象。

为了便于理解，来看一个例子：

![](https://upload-images.jianshu.io/upload_images/311496-05e563a1ddcd9cd1.jpg?imageMogr2/auto-orient/strip%7CimageView2/2/w/687)

从上面可以看到 ABC 和 DEF 节点包含的引用数为1.有三个其他的对象同时存在于零代链表中，蓝色的箭头指示了有一些对象正在被零代链表之外的其他对象所引用。(接下来我们会看到，Python中同时存在另外两个分别被称为一代和二代的链表)。这些对象有着更高的引用计数因为它们正在被其他指针所指向着。

接下来你会看到Python的GC是如何处理零代链表的。

![](https://upload-images.jianshu.io/upload_images/311496-4da43891c8aaef04.jpg?imageMogr2/auto-orient/strip%7CimageView2/2/w/688)

通过识别内部引用，Python能够减少许多零代链表对象的引用计数。在上图的第一行中你能够看见ABC和DEF的引用计数已经变为零了，这意味着收集器可以释放它们并回收内存空间了。剩下的活跃的对象则被移动到一个新的链表：一代链表。

Python的GC算法周期性地从一个对象到另一个对象追踪引用以确定对象是否还是活跃的。

### Python中的GC阈值
Python什么时候会进行这个标记过程？随着你的程序运行，Python解释器保持对新创建的对象，以及因为引用计数为零而被释放掉的对象的追踪。从理论上说，这两个值应该保持一致，因为程序新建的每个对象都应该最终被释放掉。

当然，事实并非如此。因为循环引用的原因，并且因为你的程序使用了一些比其他对象存在时间更长的对象，从而被分配对象的计数值与被释放对象的计数值之间的差异在逐渐增长。一旦这个差异累计超过某个阈值，则Python的收集机制就启动了，并且触发上边所说到的零代算法，释放“浮动的垃圾”，并且将剩下的对象移动到一代列表。

随着时间的推移，程序所使用的对象逐渐从零代列表移动到一代列表。而Python对于一代列表中对象的处理遵循同样的方法，一旦被分配计数值与被释放计数值累计到达一定阈值，Python会将剩下的活跃对象移动到二代列表。

通过这种方法，你的代码所长期使用的对象，那些你的代码持续访问的活跃对象，会从零代链表转移到一代再转移到二代。通过不同的阈值设置，Python可以在不同的时间间隔处理这些对象。Python处理零代最为频繁，其次是一代然后才是二代。

### 弱代假说

来看看代垃圾回收算法的核心行为：垃圾回收器会更频繁的处理新对象。一个新的对象即是你的程序刚刚创建的，而一个来的对象则是经过了几个时间周期之后仍然存在的对象。Python会在当一个对象从零代移动到一代，或是从一代移动到二代的过程中提升(promote)这个对象。

为什么要这么做？这种算法的根源来自于弱代假说(weak generational hypothesis)。这个假说由两个观点构成：首先是年亲的对象通常死得也快，而老对象则很有可能存活更长的时间。

假定现在我用Python创建一个新对象：

```python
n1 = Node("ABC")
```

根据假说，我的代码很可能仅仅会使用ABC很短的时间。这个对象也许仅仅只是一个方法中的中间结果，并且随着方法的返回这个对象就将变成垃圾了。大部分的新对象都是如此般地很快变成垃圾。然而，偶尔程序会创建一些很重要的，存活时间比较长的对象-例如web应用中的session变量或是配置项。

通过频繁的处理零代链表中的新对象，Python的垃圾收集器将把时间花在更有意义的地方：它处理那些很快就可能变成垃圾的新对象。同时只在很少的时候，当满足阈值的条件，收集器才回去处理那些老变量。
