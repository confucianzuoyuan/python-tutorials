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
