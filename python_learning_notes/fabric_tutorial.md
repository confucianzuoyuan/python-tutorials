`fabric`是python很有名的一个库，用来做运维执行脚本部署程序很方便。只支持python2。

不需要进虚拟环境，直接`pip install fabric==1.14.0`。

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

再举一个例子。

```py
#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
from fabric.api import *

# 登录用户和主机名：
env.user = 'root'
env.hosts = ['www.example.com'] # 如果有多个主机，fabric会自动依次部署

def pack():
    ' 定义一个pack任务 '
    # 打一个tar包：
    tar_files = ['*.py', 'static/*', 'templates/*', 'favicon.ico']
    local('rm -f example.tar.gz')
    local('tar -czvf example.tar.gz --exclude=\'*.tar.gz\' --exclude=\'fabfile.py\' %s' % ' '.join(tar_files))

def deploy():
    ' 定义一个部署任务 '
    # 远程服务器的临时文件：
    remote_tmp_tar = '/tmp/example.tar.gz'
    tag = datetime.now().strftime('%y.%m.%d_%H.%M.%S')
    run('rm -f %s' % remote_tmp_tar)
    # 上传tar文件至远程服务器：
    put('shici.tar.gz', remote_tmp_tar)
    # 解压：
    remote_dist_dir = '/srv/www.example.com@%s' % tag
    remote_dist_link = '/srv/www.example.com'
    run('mkdir %s' % remote_dist_dir)
    with cd(remote_dist_dir):
        run('tar -xzvf %s' % remote_tmp_tar)
    # 设定新目录的www-data权限:
    run('chown -R www-data:www-data %s' % remote_dist_dir)
    # 删除旧的软链接：
    run('rm -f %s' % remote_dist_link)
    # 创建新的软链接指向新部署的目录：
    run('ln -s %s %s' % (remote_dist_dir, remote_dist_link))
    run('chown -R www-data:www-data %s' % remote_dist_link)
    # 重启fastcgi：
    fcgi = '/etc/init.d/py-fastcgi'
    with settings(warn_only=True):
        run('%s stop' % fcgi)
    run('%s start' % fcgi)
```

然后执行

```
$ fab pack
$ fab deploy
```

`Fabric`提供几个简单的`API`来完成所有的部署，最常用的是`local()`和`run()`，分别在本地和远程执行命令，`put()`可以把本地文件上传到远程，当需要在远程指定当前目录时，只需用`with cd('/path/to/dir/'):`即可。

默认情况下，当命令执行失败时，`Fabric`会停止执行后续命令。有时，我们允许忽略失败的命令继续执行，比如`run('rm /tmp/abc')`在文件不存在的时候有可能失败，这时可以用`with settings(warn_only=True):`执行命令，这样`Fabric`只会打出警告信息而不会中断执行。

`Fabric`是如何在远程执行命令的呢？其实`Fabric`所有操作都是基于`SSH`执行的，必要时它会提示输入口令，所以非常安全。更好的办法是在指定的部署服务器上用证书配置无密码的`ssh`连接。

如果是基于团队开发，可以让`Fabric`利用版本库自动检出代码，自动执行测试、打包、部署的任务。由于`Fabric`运行的命令都是基本的`Linux`命令，所以根本不需要用`Fabric`本身来扩展，会敲`Linux`命令就能用`Fabric`部署。
