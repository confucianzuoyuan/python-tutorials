埃拉特斯托尼筛法产生素数

```py
def get_primes():
    D = {}

    q = 2

    while True:
        if q not in D:
            yield q
            D[q * q] = [q]
        else:
            for p in D[q]:
                D.setdefault(p + q, []).append(p)
            del D[q]
        q += 1
```

生成器产生素数的普通写法

```py
def gen_primes():
    n = 2
    primes = set()
    while True:
        for i in primes:
            if n % i == 0:
                break
        else:
            primes.add(n)
            yield n
        n += 1

g = gen_primes()
print(next(g))
print(next(g))
```

装饰器缓存斐波那契数列

```py
def cache(fib):
    c = {}
    def wrapper(n):
        r = c.get(n)
        if r is None:
            r = c[n] = fib(n)
        return r
    return wrapper

@cache
def fib(n):
    if n <= 1:
        return 1
    return fib(n-2) + fib(n-1)

print(fib(25))
```
