# 协程

## 同步

我们用两个函数来模拟两个客户端请求，并依次进行处理：
```py
def req_a():
    """模拟请求a"""
    print('开始处理请求req_a')
    print('完成处理请求req_a')

def req_b():
    """模拟请求b"""
    print('开始处理请求req_b')
    print('完成处理请求req_b')

def main():
    """处理两个请求"""
    req_a()
    req_b()

if __name__ == "__main__":
    main()
```
执行结果：
```
开始处理请求req_a
完成处理请求req_a
开始处理请求req_b
完成处理请求req_b
```
同步是按部就班的依次执行，始终按照同一个步调执行，上一个步骤未执行完不会执行下一步。

想一想，如果在处理请求req_a时需要执行一个耗时的工作（如IO），其执行过程如何？

```py
import time

def long_io():
    """模拟耗时IO操作"""
    print("开始执行IO操作")
    time.sleep(5)
    print("完成IO操作")
    return "io result"

def req_a():
    print("开始处理请求req_a")
    ret = long_io()
    print("ret: %s" % ret)
    print("完成处理请求req_a")

def req_b():
    print("开始处理请求req_b")
    print("完成处理请求req_b")

def main():
    req_a()
    req_b()

if __name__=="__main__":
    main()
```
执行过程：
```
开始处理请求req_a
开始执行IO操作
完成IO操作
完成处理请求req_a
开始处理请求req_b
完成处理请求req_b
```
在上面的测试中，我们看到耗时的操作会将代码执行阻塞住，即req_a未处理完req_b是无法执行的。

我们怎么解决耗时操作阻塞代码执行？

## 异步

对于耗时的过程，我们将其交给别人（如其另外一个线程）去执行，而我们继续往下处理，当别人执行完耗时操作后再将结果反馈给我们，这就是我们所说的异步。

我们用容易理解的线程机制来实现异步。

### 回调写法实现原理

```py
import time
import thread

def long_io(callback):
    """将耗时的操作交给另一线程来处理"""
    def fun(cb): # 回调函数作为参数
        """耗时操作"""
        print("开始执行IO操作")
        time.sleep(5)
        print("完成IO操作，并执行回调函数")
        cb("io result")  # 执行回调函数
    thread.start_new_thread(fun, (callback,))  # 开启线程执行耗时操作

def on_finish(ret):
    """回调函数"""
    print("开始执行回调函数on_finish")
    print("ret: %s" % ret)
    print("完成执行回调函数on_finish")

def req_a():
    print("开始处理请求req_a")
    long_io(on_finish)
    print("离开处理请求req_a")

def req_b():
    print("开始处理请求req_b")
    time.sleep(2) # 添加此句来突出显示程序执行的过程
    print("完成处理请求req_b")

def main():
    req_a()
    req_b()
    while 1: # 添加此句防止程序退出，保证线程可以执行完
        pass

if __name__ == '__main__':
    main()
```
执行过程：
```
开始处理请求req_a
离开处理请求req_a
开始处理请求req_b
开始执行IO操作
完成处理请求req_b
完成IO操作，并执行回调函数
开始执行回调函数on_finish
ret: io result
完成执行回调函数on_finish
```
异步的特点是程序存在多个步调，即本属于同一个过程的代码可能在不同的步调上同时执行。

### 协程写法实现原理

在使用回调函数写异步程序时，需将本属于一个执行逻辑（处理请求a）的代码拆分成两个函数req_a和on_finish，这与同步程序的写法相差很大。而同步程序更便于理解业务逻辑，所以我们能否用同步代码的写法来编写异步程序？

回想yield关键字的作用？

#### 初始版本

```py
import time
import thread

gen = None # 全局生成器，供long_io使用

def long_io():
    def fun():
        print("开始执行IO操作")
        global gen
        time.sleep(5)
        try:
            print("完成IO操作，并send结果唤醒挂起程序继续执行")
            gen.send("io result")  # 使用send返回结果并唤醒程序继续执行
        except StopIteration: # 捕获生成器完成迭代，防止程序退出
            pass
    thread.start_new_thread(fun, ())

def req_a():
    print("开始处理请求req_a")
    ret = yield long_io()
    print("ret: %s" % ret)
    print("完成处理请求req_a")

def req_b():
    print("开始处理请求req_b")
    time.sleep(2)
    print("完成处理请求req_b")

def main():
    global gen
    gen = req_a()
    gen.next() # 开启生成器req_a的执行
    req_b()
    while 1:
        pass

if __name__ == '__main__':
    main()
```

执行过程

```
开始处理请求req_a
开始处理请求req_b
开始执行IO操作
完成处理请求req_b
完成IO操作，并send结果唤醒挂起程序继续执行
ret: io result
完成处理请求req_a
```

#### 升级版本

我们在上面编写出的版本虽然req_a的编写方式很类似与同步代码，但是在main中调用req_a的时候却不能将其简单的视为普通函数，而是需要作为生成器对待。

现在，我们试图尝试修改，让req_a与main的编写都类似与同步代码。

```py
import time
import thread

gen = None # 全局生成器，供long_io使用

def gen_coroutine(f):
    def wrapper(*args, **kwargs):
        global gen
        gen = f()
        gen.next()
    return wrapper

def long_io():
    def fun():
        print("开始执行IO操作")
        global gen
        time.sleep(5)
        try:
            print("完成IO操作，并send结果唤醒挂起程序继续执行")
            gen.send("io result")  # 使用send返回结果并唤醒程序继续执行
        except StopIteration: # 捕获生成器完成迭代，防止程序退出
            pass
    thread.start_new_thread(fun, ())

@gen_coroutine
def req_a():
    print("开始处理请求req_a")
    ret = yield long_io()
    print("ret: %s" % ret)
    print("完成处理请求req_a")

def req_b():
    print("开始处理请求req_b")
    time.sleep(2)
    print("完成处理请求req_b")

def main():
    req_a()
    req_b()
    while 1:
        pass

if __name__ == '__main__':
    main()
```

执行过程：

```
开始处理请求req_a
开始处理请求req_b
开始执行IO操作
完成处理请求req_b
完成IO操作，并send结果唤醒挂起程序继续执行
ret: io result
完成处理请求req_a
```

#### 最终版本

刚刚完成的版本依然不理想，因为存在一个全局变量gen来供long_io使用。我们现在再次改写程序，消除全局变量gen。

```py
import time
import thread

def gen_coroutine(f):
    def wrapper(*args, **kwargs):
        gen_f = f()  # gen_f为生成器req_a
        r = gen_f.next()  # r为生成器long_io
        def fun(g):
            ret = g.next() # 执行生成器long_io
            try:
                gen_f.send(ret) # 将结果返回给req_a并使其继续执行
            except StopIteration:
                pass
        thread.start_new_thread(fun, (r,))
    return wrapper

def long_io():
    print "开始执行IO操作"
    time.sleep(5)
    print "完成IO操作，yield回操作结果"
    yield "io result"

@gen_coroutine
def req_a():
    print "开始处理请求req_a"
    ret = yield long_io()
    print "ret: %s" % ret
    print "完成处理请求req_a"

def req_b():
    print "开始处理请求req_b"
    time.sleep(2)
    print "完成处理请求req_b"

def main():
    req_a()
    req_b()
    while 1:
        pass

if __name__ == '__main__':
    main()
```

执行过程：

```
开始处理请求req_a
开始处理请求req_b
开始执行IO操作
完成处理请求req_b
完成IO操作，yield回操作结果
ret: io result
完成处理请求req_a
```

这个最终版本就是理解Tornado异步编程原理的最简易模型，但是，Tornado实现异步的机制不是线程，而是epoll，即将异步过程交给epoll执行并进行监视回调。

需要注意的一点是，我们实现的版本严格意义上来说不能算是协程，因为两个程序的挂起与唤醒是在两个线程上实现的，而Tornado利用epoll来实现异步，程序的挂起与唤醒始终在一个线程上，由Tornado自己来调度，属于真正意义上的协程。虽如此，并不妨碍我们理解Tornado异步编程的原理。

# 生成器

如果一个函数包含yield关键字，这个函数就会变为一个生成器。

生成器并不会一次返回所有结果，而是每次遇到yield关键字后返回相应结果，并保留函数当前的运行状态，等待下一次的调用。

由于生成器也是一个迭代器，那么它就应该支持next方法来获取下一个值。

```py
# 通过`yield`来创建生成器
def func():
   for i in range(10);
        yield i

# 通过列表来创建生成器
[i for i in range(10)]
```

```py
# 调用如下
>>> f = func()
>>> f # 此时生成器还没有运行
<generator object func at 0x7fe01a853820>
>>> f.next() # 当i=0时，遇到yield关键字，直接返回
0
>>> f.next() # 继续上一次执行的位置，进入下一层循环
1
...
>>> f.next()
9
>>> f.next() # 当执行完最后一次循环后，结束yield语句，生成StopIteration异常
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
StopIteration
>>>
```

除了next函数，生成器还支持send函数。该函数可以向生成器传递参数。

```py
>>> def func():
...     n = 0
...     while 1:
...         n = yield n #可以通过send函数向n赋值
... 
>>> f = func()
>>> f.next() # 默认情况下n为0
0
>>> f.send(1) #n赋值1
1
>>> f.send(2)
2
>>> 
```

## 应用

最经典的例子，生成无限序列。

常规的解决方法是，生成一个满足要求的很大的列表，这个列表需要保存在内存中，很明显内存限制了这个问题。

```py
def get_primes(start):
    for element in magical_infinite_range(start):
        if is_prime(element):
            return element
```

如果使用生成器就不需要返回整个列表，每次都只是返回一个数据，避免了内存的限制问题。

```py
def get_primes(number):
    while True:
        if is_prime(number):
            yield number
        number += 1
```

## 生成器源码分析

生成器的源码在`Objects/genobject.c`。

### 调用栈

在解释生成器之前，需要讲解一下Python虚拟机的调用原理。

Python虚拟机有一个栈帧的调用栈，其中栈帧的是`PyFrameObject`，位于`Include/frameobject.h`。

```c
typedef struct _frame {
    PyObject_VAR_HEAD
    struct _frame *f_back;  /* previous frame, or NULL */
    PyCodeObject *f_code;   /* code segment */
    PyObject *f_builtins;   /* builtin symbol table (PyDictObject) */
    PyObject *f_globals;    /* global symbol table (PyDictObject) */
    PyObject *f_locals;     /* local symbol table (any mapping) */
    PyObject **f_valuestack;    /* points after the last local */
    /* Next free slot in f_valuestack.  Frame creation sets to f_valuestack.
       Frame evaluation usually NULLs it, but a frame that yields sets it
       to the current stack top. */
    PyObject **f_stacktop;
    PyObject *f_trace;      /* Trace function */
 
    /* If an exception is raised in this frame, the next three are used to
     * record the exception info (if any) originally in the thread state.  See
     * comments before set_exc_info() -- it's not obvious.
     * Invariant:  if _type is NULL, then so are _value and _traceback.
     * Desired invariant:  all three are NULL, or all three are non-NULL.  That
     * one isn't currently true, but "should be".
     */
    PyObject *f_exc_type, *f_exc_value, *f_exc_traceback;
 
    PyThreadState *f_tstate;
    int f_lasti;        /* Last instruction if called */
    /* Call PyFrame_GetLineNumber() instead of reading this field
       directly.  As of 2.3 f_lineno is only valid when tracing is
       active (i.e. when f_trace is set).  At other times we use
       PyCode_Addr2Line to calculate the line from the current
       bytecode index. */
    int f_lineno;       /* Current line number */
    int f_iblock;       /* index in f_blockstack */
    PyTryBlock f_blockstack[CO_MAXBLOCKS]; /* for try and loop blocks */
    PyObject *f_localsplus[1];  /* locals+stack, dynamically sized */
} PyFrameObject;
```
栈帧保存了给出代码的的信息和上下文，其中包含最后执行的指令，全局和局部命名空间，异常状态等信息。f_valueblock保存了数据，b_blockstack保存了异常和循环控制方法。

举一个例子来说明，

```py
def foo():
    x = 1
    def bar(y):
        z = y + 2  # 
```

那么，相应的调用栈如下，一个py文件，一个类，一个函数都是一个代码块，对应者一个Frame，保存着上下文环境以及字节码指令。

```
c   ---------------------------
a  | bar Frame                 | -> block stack: []
l  |     (newest)              | -> data stack: [1, 2]
l   ---------------------------
   | foo Frame                 | -> block stack: []
s  |                           | -> data stack: [.bar at 0x10d389680>, 1]
t   ---------------------------
a  | main (module) Frame       | -> block stack: []
c  |       (oldest)            | -> data stack: []
k   ---------------------------
```

每一个栈帧都拥有自己的数据栈和block栈，独立的数据栈和block栈使得解释器可以中断和恢复栈帧（生成器正式利用这点）。

Python代码首先被编译为字节码，再由Python虚拟机来执行。一般来说，一条Python语句对应着多条字节码（由于每条字节码对应着一条C语句，而不是一个机器指令，所以不能按照字节码的数量来判断代码性能）。

调用dis模块可以分析字节码，

```py
from dis import dis
 
dis(foo)
 
  5           0 LOAD_CONST               1 (1) # 加载常量1
              3 STORE_FAST               0 (x) # x赋值为1
 
  6           6 LOAD_CONST               2 (<code>) # 加载常量2
              9 MAKE_FUNCTION            0 # 创建函数
             12 STORE_FAST               1 (bar) 
 
  9          15 LOAD_FAST                1 (bar) 
             18 LOAD_FAST                0 (x)
             21 CALL_FUNCTION            1  # 调用函数
             24 RETURN_VALUE        </code>
```

其中，

```
第一行为代码行号；
第二行为偏移地址；
第三行为字节码指令；
第四行为指令参数；
第五行为参数解释。
```

### 生成器源码分析

由了上面对于调用栈的理解，就可以很容易的明白生成器的具体实现。

生成器的源码位于object/genobject.c。

#### 生成器的创建

```c
PyObject *
PyGen_New(PyFrameObject *f)
{
    PyGenObject *gen = PyObject_GC_New(PyGenObject, &PyGen_Type); # 创建生成器对象
    if (gen == NULL) {
        Py_DECREF(f);
        return NULL;
    }
    gen->gi_frame = f; # 赋予代码块
    Py_INCREF(f->f_code); # 引用计数+1
    gen->gi_code = (PyObject *)(f->f_code);
    gen->gi_running = 0; # 0表示为执行，也就是生成器的初始状态
    gen->gi_weakreflist = NULL;
    _PyObject_GC_TRACK(gen); # GC跟踪
    return (PyObject *)gen;
}
```

#### send与next

next与send函数，如下

```c
static PyObject *
gen_iternext(PyGenObject *gen)
{
    return gen_send_ex(gen, NULL, 0);
}
 
 
static PyObject *
gen_send(PyGenObject *gen, PyObject *arg)
{
    return gen_send_ex(gen, arg, 0);
}
```

从上面的代码中可以看到，send和next都是调用的同一函数gen_send_ex，区别在于是否带有参数。

```c
static PyObject *
gen_send_ex(PyGenObject *gen, PyObject *arg, int exc)
{
    PyThreadState *tstate = PyThreadState_GET();
    PyFrameObject *f = gen->gi_frame;
    PyObject *result;
 
    if (gen->gi_running) { # 判断生成器是否已经运行
        PyErr_SetString(PyExc_ValueError,
                        "generator already executing");
        return NULL;
    }
    if (f==NULL || f->f_stacktop == NULL) { # 如果代码块为空或调用栈为空，则抛出StopIteration异常
        /* Only set exception if called from send() */
        if (arg && !exc)
            PyErr_SetNone(PyExc_StopIteration);
        return NULL;
    }
 
    if (f->f_lasti == -1) { # f_lasti=1 代表首次执行
        if (arg && arg != Py_None) { # 首次执行不允许带有参数
            PyErr_SetString(PyExc_TypeError,
                            "can't send non-None value to a "
                            "just-started generator");
            return NULL;
        }
    } else {
        /* Push arg onto the frame's value stack */
        result = arg ? arg : Py_None;
        Py_INCREF(result); # 该参数引用计数+1
        *(f->f_stacktop++) = result; # 参数压栈
    }
 
    /* Generators always return to their most recent caller, not
     * necessarily their creator. */
    f->f_tstate = tstate;
    Py_XINCREF(tstate->frame);
    assert(f->f_back == NULL);
    f->f_back = tstate->frame;
 
    gen->gi_running = 1; # 修改生成器执行状态
    result = PyEval_EvalFrameEx(f, exc); # 执行字节码
    gen->gi_running = 0; # 恢复为未执行状态
 
    /* Don't keep the reference to f_back any longer than necessary.  It
     * may keep a chain of frames alive or it could create a reference
     * cycle. */
    assert(f->f_back == tstate->frame);
    Py_CLEAR(f->f_back);
    /* Clear the borrowed reference to the thread state */
    f->f_tstate = NULL;
 
    /* If the generator just returned (as opposed to yielding), signal
     * that the generator is exhausted. */
    if (result == Py_None && f->f_stacktop == NULL) {
        Py_DECREF(result);
        result = NULL;
        /* Set exception if not called by gen_iternext() */
        if (arg)
            PyErr_SetNone(PyExc_StopIteration);
    }
 
    if (!result || f->f_stacktop == NULL) {
        /* generator can't be rerun, so release the frame */
        Py_DECREF(f);
        gen->gi_frame = NULL;
    }
 
    return result;
}
```

#### 字节码的执行

PyEval_EvalFrameEx函数的功能为执行字节码并返回结果。

```c
# 主要流程如下，
for (;;) {
   switch(opcode) { # opcode为操作码，对应着各种操作
        case NOP:
            goto  fast_next_opcode;
        ...
        ...
        case YIELD_VALUE: # 如果操作码是yield
            retval = POP(); 
            f->f_stacktop = stack_pointer;
            why = WHY_YIELD;
            goto fast_yield; # 利用goto跳出循环
    }
}
 
fast_yield:
    ... 
return vetval; # 返回结果
```

举一个例子，f_back上一个Frame，f_lasti上一次执行的指令的偏移量，

```py
import sys
from dis import dis
 
 
def func():
    f = sys._getframe(0)
    print f.f_lasti
    print f.f_back
    yield 1
 
    print f.f_lasti
    print f.f_back
    yield 2
 
 
a = func()
dis(func)
a.next()
a.next()
```

结果如下，其中第三行的英文为操作码，对应着上面的opcode，每次switch都是在不同的opcode之间进行选择。

```py
  6           0 LOAD_GLOBAL              0 (sys)
              3 LOAD_ATTR                1 (_getframe)
              6 LOAD_CONST               1 (0)
              9 CALL_FUNCTION            1
             12 STORE_FAST               0 (f)
 
  7          15 LOAD_FAST                0 (f)
             18 LOAD_ATTR                2 (f_lasti) 
             21 PRINT_ITEM          
             22 PRINT_NEWLINE       
 
  8          23 LOAD_FAST                0 (f)
             26 LOAD_ATTR                3 (f_back)
             29 PRINT_ITEM          
             30 PRINT_NEWLINE       
 
  9          31 LOAD_CONST               2 (1)
             34 YIELD_VALUE     # 此时操作码为YIELD_VALUE，直接跳转上述goto语句，此时f_lasti为当前指令，f_back为当前frame
             35 POP_TOP             
 
 11          36 LOAD_FAST                0 (f)
             39 LOAD_ATTR                2 (f_lasti)
             42 PRINT_ITEM          
             43 PRINT_NEWLINE       
 
 12          44 LOAD_FAST                0 (f)
             47 LOAD_ATTR                3 (f_back)
             50 PRINT_ITEM          
             51 PRINT_NEWLINE       
 
 13          52 LOAD_CONST               3 (2)
             55 YIELD_VALUE         
             56 POP_TOP             
             57 LOAD_CONST               0 (None)
             60 RETURN_VALUE        
 18
 <frame object at 0x7fa75fcebc20> #和下面的frame相同，属于同一个frame，也就是说在同一个函数（命名空间）内，frame是同一个。
 39
 <frame object at 0x7fa75fcebc20>
```

#### 再来一个例子：

```py
from dis import dis
def func():
    i = 4
    yield i
    print i
    
dis(func)
a =func()
a.next()
a.next()
```

使用python的库dis可以直接查看python虚拟机运行的字节码。dis(func)的打印如下：

```py
6           0 LOAD_CONST               1 (4)
            3 STORE_FAST               0 (i)
7           6 LOAD_FAST                0 (i)
            9 YIELD_VALUE         
           10 POP_TOP             
8          11 LOAD_FAST                0 (i)
           14 PRINT_ITEM          
           15 PRINT_NEWLINE       
           16 LOAD_CONST               0 (None)
           19 RETURN_VALUE
```

我们猜测其中第二列(代表字节码偏移量)为9的指令`YIELD_VALUE`就是yield关键字的执行代码，进入Python2.7.12源码目录，在解释器执行字节码的主函数`PyEval_EvalFrameEx`中找到了下面一段：

```c
TARGET_NOARG(YIELD_VALUE)
{
    retval = POP();
    f->f_stacktop = stack_pointer;
    why = WHY_YIELD;
    // 跳转到fast_yield处。fast_yield里处理了一下状态位然后返回结果
    goto fast_yield;
}
```

其中`TARGET_NOARG`为封装了case语句的宏，这句话的意思是，如果字节码是`YIELD_VALUE`，就把栈顶元素赋值给`retval`，然后跳转到`fast_yield`处，`fast_yield`处代码进行了一些状态判断后直接返回了`retval`。

#### 生成器是如何记录代码返回位置的

显然，如果这时候调用代码`a.next()`就会直接返回yield后边的表达式结果。这对应了上面C代码的`fast_yield`部分，那生成器怎么记录上次执行的位置并在下一次调用`a.next()`的时候从上次的位置继续执行的呢？

Python在解释代码时，是将代码块加载为一个叫`PyFrameObject`的对象，这个对象代表了当前运行的栈帧。`PyFrameObject`里有个`f_lasti`变量用于保存代码当前执行到了字节码的哪个位置。在第二次执行`a.next()`时，生成器对象把之前携带了`f_lasti`的`PyFrameObject`当参数传给`PyEval_EvalFrameEx`，在`PyEval_EvalFrameEx`里的执行一个`JUMPTO`就直接跳转到了上一次结束生成器时的字节码位置：

```c
PyObject *
PyEval_EvalFrameEx(PyFrameObject *f, int throwflag)
{
...
#define FAST_DISPATCH() \
          { \
      if (!lltrace && !_Py_TracingPossible) { \
          f->f_lasti = INSTR_OFFSET(); \
          goto *opcode_targets[*next_instr++]; \
      } \
      // 跳转到fast_next_opcode处
      goto fast_next_opcode; \
          }
...
fast_next_opcode:
          f->f_lasti = INSTR_OFFSET();
  
          /* line-by-line tracing support */
  
          if (_Py_TracingPossible &&
              tstate->c_tracefunc != NULL && !tstate->tracing) {
              ...
              /* Reload possibly changed frame fields */
              // 按照f->f_lasti中的偏移量跳转字节码
              JUMPTO(f->f_lasti);
}
```

其中`INSTR_OFFSET`宏正是字节码的偏移量。

```c
#define INSTR_OFFSET()  ((int)(next_instr - first_instr))
// co->co_code里保存的是字节码
first_instr = (unsigned char*) PyString_AS_STRING(co->co_code);
next_instr = first_instr + f->f_lasti + 1;
```

所以生成器对象每次执行结束都把字节码的偏移量记录下来，并把运行状态保存在`PyFrameObject`里，下一次运行时生成器时，python解释器直接按照偏移量寻找下一个字节码指令。