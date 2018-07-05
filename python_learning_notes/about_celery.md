安装`celery`。

```sh
$ pip install celery
```

新建一个文件`tasks.py`

```py
from celery import Celery

app = Celery('tasks', broker='redis://localhost:6379')

@app.task
def add(x, y):
    return x + y
```

以上将一个加法任务定义为一个任务。

前提需要启动`redis`进程，使用`redis`作为`celery`的`broker`。

然后新开一个终端，执行以下命令。

```sh
$ celery -A tasks worker --loglevel=info
```

在`python`解释器中运行以下程序。

```py
>>> from tasks import add
>>> add.delay(4, 4)
```

`delay`关键字用来将`add`任务推到消息队列中去。