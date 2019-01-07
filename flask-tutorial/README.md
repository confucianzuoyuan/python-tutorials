# 1. clone项目

```sh
$ git clone https://github.com/miguelgrinberg/flasky-first-edition.git
```

# 2. 新建虚拟环境

```sh
$ cd
$ pip install virtualenv -i https://pypi.tuna.tsinghua.edu.cn/simple/
$ virtualenv -p python3 flask-tutorial
$ source flask-tutorial/bin/activate # 进入虚拟环境
$ deactivate # 推出虚拟环境
```

# 3. 安装所需要的包

注意要进入虚拟环境

```sh
$ cd flasky-first-edition
$ pip install -r requirements/dev.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
```

# 4. 删库跑路

```sh
$ rm data-*.sqlite
$ rm -rf migrations/
$ python manage.py db init
$ python manage.py db migrate -m "xxxx"
$ python manage.py db upgrade
```

# 5. linux常用操作

```sh
$ cp -r folder1 folder2 # 递归拷贝
$ rm -rf folder # 递归强制删除
$ mv folder1 folder2 # 移动文件夹，或者重命名
$ ps -ef | grep python # 查看正在执行的python进程
$ kill -9 pid # 强制杀死进程号为pid的进程
```
