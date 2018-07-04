`fabric`是python很有名的一个库，用来做运维执行脚本部署程序很方便。只支持python2。

不需要进虚拟环境，直接`pip install fabric`。

新建一个文件命名为`fabfile.py`，注意必须是这个名字，不能改。

```py
# fabfile.py
def hello():
    print("Hello world!")
```

然后执行

```
$ fab hello
Hello world!

Done.
```

使用参数。

```py
def hello(name="world"):
    print("Hello %s!" % name)
```

然后执行

```
$ fab hello:name=Jeff
Hello Jeff!

Done.
```

或者执行

```
$ fab hello:Jeff
Hello Jeff!

Done.
```

都一样。

执行本地命令。

```py
from fabric.api import local

def prepare_deploy():
    local("python manage.py test my_app")
    local("git add -p && git commit")
    local("git push")
```

然后执行

```
$ fab prepare_deploy
[localhost] run: python manage.py test my_app
Creating test database...
Creating tables
Creating indexes
..........................................
----------------------------------------------------------------------
Ran 42 tests in 9.138s

OK
Destroying test database...

[localhost] run: git add -p && git commit

<interactive Git add / git commit edit message session>

[localhost] run: git push

<git push session, possibly merging conflicts interactively>

Done.
```

多个函数

```py
from fabric.api import local

def test():
    local("python manage.py test my_app")

def commit():
    local("git add -p && git commit")

def push():
    local("git push")

def prepare_deploy():
    test()
    commit()
    push()
```

`cd`到一个目录里面进行操作。

```py
from __future__ import with_statement
from fabric.api import local, settings, abort, run, cd
from fabric.contrib.console import confirm

def deploy():
    code_dir = '/srv/django/myproject'
    with cd(code_dir):
        run("git pull")
        run("touch app.wsgi")
```

然后执行

```
$ fab deploy
```

`git clone`的使用

```py
def deploy():
    code_dir = '/srv/django/myproject'
    with settings(warn_only=True):
        if run("test -d %s" % code_dir).failed:
            run("git clone user@vcshost:/path/to/repo/.git %s" % code_dir)
    with cd(code_dir):
        run("git pull")
        run("touch app.wsgi")
```

连接远程服务器

```py
from __future__ import with_statement
from fabric.api import *
from fabric.contrib.console import confirm

env.hosts = ['my_server']

def test():
    do_test_stuff()
```

完整的程序。

```py
from __future__ import with_statement
from fabric.api import *
from fabric.contrib.console import confirm

env.hosts = ['my_server']

def test():
    with settings(warn_only=True):
        result = local('./manage.py test my_app', capture=True)
    if result.failed and not confirm("Tests failed. Continue anyway?"):
        abort("Aborting at user request.")

def commit():
    local("git add -p && git commit")

def push():
    local("git push")

def prepare_deploy():
    test()
    commit()
    push()

def deploy():
    code_dir = '/srv/django/myproject'
    with settings(warn_only=True):
        if run("test -d %s" % code_dir).failed:
            run("git clone user@vcshost:/path/to/repo/.git %s" % code_dir)
    with cd(code_dir):
        run("git pull")
        run("touch app.wsgi")
```