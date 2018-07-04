# 装饰器就是高阶函数的语法糖，也可以叫做闭包
def my_shiny_new_decorator(a_function_to_decorate):

    def the_wrapper_around_the_original_function():
        print("Before the function runs")
        a_function_to_decorate()
        print("After the function runs")

    return the_wrapper_around_the_original_function

def a_stand_alone_function():
    print("I am a stand alone function, don't you dare modify me")

a_stand_alone_function_decorated = my_shiny_new_decorator(a_stand_alone_function)
a_stand_alone_function_decorated()

# 使用装饰器就是
@my_shiny_new_decorator
def another_stand_alone_function():
    print("Leave me alone")

another_stand_alone_function()

# 下一个例子
def bread(func):
    def wrapper():
        print("</''''''\>")
        func()
        print("<\______/>")
    return wrapper

def ingredients(func):
    def wrapper():
        print("#tomatoes#")
        func()
        print("~salad~")
    return wrapper

def snadwich(food="--ham--"):
    print(food)

sandwich()
sandwich = bread(ingredients(sandwich))
sandwich()

# 以上等于
@bread
@ingredients
def sandwich(food="--ham--")
    print(food)
sandwich()

# 装饰器是有顺序的
@ingredients
@bread
def strange_sandwich(food="--ham--")
    print(food)

strange_sandwich()

# 向装饰器函数传递参数
def a_decorator_passing_arguments(function_to_decorate):
    def a_wrapper_accepting_arguments(arg1, arg2):
        print("I got args! Look: {0}, {1}").format(arg1, arg2)
        function_to_decorate(arg1, arg2)
    return a_wrapper_accepting_arguments

@a_decorator_passing_arguments
def print_full_name(first_name, last_name):
    print("My name is {0} {1}".format(first_name, last_name))

print_full_name("Peter", "Venkman")

# 如果要装饰类里的方法，需要考虑self
# 例如

def method_friendly_decorator(method_to_decorate):
    def wrapper(self, lie):
        lie = lie - 3
        # 下面这句会执行method_to_decorate(self, lie)这个函数
        return method_to_decorate(self, lie)
    return wrapper

class Lucy(object):

    def __init__(self):
        self.age = 32

    @method_friendly_decorator
    def sayYourAge(self, lie):
        print("I am {0}, what did you think?".format(self.age + lie))

l = Lucy()
l.sayYourAge(-3)


# 传递任意参数
def a_decorator_passing_arbitrary_arguments(function_to_decorate):
    def a_wrapper_accepting_arbitrary_arguments(*args, **kwargs):
        print("Do I have args?:")
        print(args)
        print(kwargs)
        function_to_decorate(*args, **kwargs)
    return a_wrapper_accepting_arbitrary_arguments

@a_decorator_passing_arbitrary_arguments
def function_with_no_argument():
    print("Python is cool, no argument here.")

function_with_no_argument()

@a_decorator_passing_arbitrary_arguments
def function_with_arguments(a,b,c):
    print(a, b, c)

function_with_arguments(1, 2, 3)

@a_decorator_passing_arbitrary_arguments
def function_with_named_arguments(a, b, c, platypus="Why not ?"):
    print("Do {0}, {1} and {2} like platypus? {3}".format(a, b, c, platypus))

function_with_named_arguments("Bill", "Linus", "Steve", platypus="Indeed!")

class Mary(object):
    def __init__(self):
        self.age = 31

    @a_decorator_passing_arbitrary_arguments
    def sayYourAge(self, lie=-3):
        print("I am {0}, what did you think?".format(self.age + lie))

# 以上的例子是向被装饰的函数发送参数，下面的例子是向装饰器传参数
def decorator_maker():
    print("I make decorators! I am executed only once: "
          "when you make me create a decorator.")

    def my_decorator(func):
        print("I am a decorator! I am executed only when you decorate a function.")
        def wrapped():
            print("I am the wrapper around the decorated function. "
                  "I am called when you call the decorated function. "
                  "As the wrapper, I return the RESULT of the decorated function.")
            return func()
        print("As the decorator, I return the wrapped function.")
        return wrapped
    print("As a decorator maker, I return a decorator")
    return my_decorator

new_decorator = decorator_maker()
#outputs:
#I make decorators! I am executed only once: when you make me create a decorator.
#As a decorator maker, I return a decorator

def decorated_function():
    print("I am the decorated function.")

decorated_function = new_decorator(decorated_function)
#outputs:
#I am a decorator! I am executed only when you decorate a function.
#As the decorator, I return the wrapped function
# 省去中间变量的话是这样
def decorated_function():
    print("I am the decorated function.")
decorated_function = decorator_maker()(decorated_function)

@decorator_maker()
def decorated_function():
    print("I am the decorated function.")
decorated_function()

def decorator_maker_with_arguments(decorator_arg1, decorator_arg2):
    print("I make decorators! And I accept arguments: {0}, {1}".format(decorator_arg1, decorator_arg2))

    def my_decorator(func):
        print("I am the decorator. Somehow you passed me arguments: {0}, {1}".format(decorator_arg1, decorator_arg2))

        def wrapped(function_arg1, function_arg2):
            print("I am the wrapper around the decorated function.\n"
                  "I can access all the variables\n"
                  "\t- from the decorator: {0} {1}\n"
                  "\t- from the function call: {2} {3}\n"
                  "Then I can pass them to the decorated function"
                  .format(decorator_arg1, decorator_arg2,
                          function_arg1, function_arg2))
            return func(function_arg1, function_arg2)
        return wrapped
    return my_decorator

@decorator_maker_with_arguments("Leonard", "Sheldon")
def decorated_function_with_arguments(function_arg1, function_arg2):
    print("I am the decorated function and only knows about my arguments: {0}"
          " {1}".format(function_arg1, function_arg2))
decorated_function_with_arguments("Rajesh", "Howard")

c1 = "Penny"
c2 = "Leslie"

@decorator_maker_with_arguments("Leonard", c1)
def decorated_function_with_arguments(function_arg1, function_arg2):
    print("I am the decorated function and only knows about my arguments:"
          " {0} {1}".format(function_arg1, function_arg2))

decorated_function_with_arguments(c2, "Howard")
#outputs:
#I make decorators! And I accept arguments: Leonard Penny
#I am the decorator. Somehow you passed me arguments: Leonard Penny
#I am the wrapper around the decorated function.
#I can access all the variables
#   - from the decorator: Leonard Penny
#   - from the function call: Leslie Howard
#Then I can pass them to the decorated function
#I am the decorated function and only knows about my arguments: Leslie Howard

# 给装饰器加装饰器
def decorator_with_args(decorator_to_enhance):
    def decorator_maker(*args, **kwargs):
        def decorator_wrapper(func):
            return decorator_to_enhance(func, *args, **kwargs)
        return decorator_wrapper
    return decorator_maker

@decorator_with_args
def decorated_decorator(func, *args, **kwargs):
    def wrapper(function_arg1, function_arg2):
        print("Decorated with {0} {1}".format(args, kwargs))
        return func(function_arg1, function_arg2)
    return wrapper

@decorated_decorator(42, 404, 1024)
def decorated_function(function_arg1, function_arg2):
    print("Hello {0} {1}".format(function_arg1, function_arg2))

decorated_function("Universe and", "everything")
# 等价于以下，闭包太复杂，N层闭包
decorator_with_args(decorated_decorator)(42, 404, 1024)(decorated_function)("Universe and", "everything")

def foo():
    print("foo")

print(foo.__name__)
#outputs: foo
def bar(func):
    def wrapper():
        print("bar")
        return func()
    return wrapper

@bar
def foo():
    print("foo")

print(foo.__name__)
#outputs: wrapper

#functools.wraps()可以拷贝被装饰函数的name, module, docstring到它的wrapper
import functools
def bar(func):
    @functools.wraps(func)
    def wrapper():
        print("bar")
        return func()
    return wrapper

@bar
def foo():
    print("foo")

print(foo.__name__)
#outputs: foo

# 装饰器的一些应用，可以不断添加
def benchmark(func):
    """
    A decorator that prints the time a function takes
    to execute
    """
    import time
    def wrapper(*args, **kwargs):
        t = time.clock()
        res = func(*args, **kwargs)
        print("{0} {1}".format(func.__name__, time.clock()-t))
        return res
    return wrapper

def logging(func):
    """
    A decorator that logs the activity of the script.
    (it actually just prints it, but it could be logging!)
    """
    def wrapper(*args, **kwargs):
        res = func(*args, **kwargs)
        print("{0} {1} {2}".format(func.__name__, args, kwargs))
        return res
    return wrapper

def counter(func):
    """
    A decorator that counts and prints the number of times a function has been executed
    """
    def wrapper(*args, **kwargs):
        wrapper.count = wrapper.count + 1
        res = func(*args, **kwargs)
        print("{0} has been used: {1}x".format(func.__name__, wrapper.count))
    # 为函数添加属性
    wrapper.count = 0
    return wrapper

@counter
@benchmark
@logging
def reverse_string(string):
    return str(reversed(string))

# 参考资料 https://wiki.python.org/moin/PythonDecoratorLibrary#Memoize
# http://stackoverflow.com/questions/739654/how-to-make-a-chain-of-function-decorators-in-python/1594484#1594484


# 一个使用装饰器做缓存的例子
# 存储函数的返回值，如果下次调用的参数一样，那么久不需要再次调用，直接返回结果就好

class memoized(object):
    def __init__(self, func):
        self.func = func
        self.cache = {}
    def __call__(self, *args):
        # 如果无法哈希，例如list这种，就运行函数
        if not isinstance(args, collections.Hashable):
            return self.func(*args)
        if args in self.cache:
            return self.cache[args]
        else:
            value = self.func(*args)
            self.cache[args] = value
            return value
    def __repr__(self):
        return self.func.__doc.__
    def __get__(self, obj, objtype):
        return functools.partial(self.__call__, obj)

@memoized
def fibonacci(n):
    if n in (0, 1):
        return n
    return fibonacci(n-1) + fibonacci(n-2)
print fibonacci(12)

