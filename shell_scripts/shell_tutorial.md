```sh
$ echo '#!/bin/sh' > my-script.sh
$ echo 'echo Hello World' >> my-script.sh
$ chmod 755 my-script.sh
$ ./my-script.sh
Hello World
$
```

上面这段代码中，`echo`是打印的意思，而`>`是重定向的意思，`chmod`是修改权限的意思。`shell`脚本以`.sh`为结尾。

```sh
#!/bin/sh
# This is a comment!
echo Hello World	# This is a comment, too!
```

以上为`my-script.sh`中的代码，可以学习一下如何写注释。

```sh
$ chmod a+rx my-script.sh
$ ./my-script.sh
```

想要将`shell`脚本变成可执行的，可以使用以上语句。

```sh
grep "mystring" /tmp/myfile
```

这句的意思是将在`/tmp/myfile`中的`"mystring"`字符串搜索出来。

```sh
#!/bin/sh
# This is a comment!
echo Hello World        # This is a comment, too!
```

以上是`first.sh`中的代码。可以使用以下代码执行：

```sh
$ chmod 755 first.sh
$ ./first.sh
Hello World
$
```

得到结果：

```sh
$ echo Hello World
Hello World
$
```

```sh
#!/bin/sh
MY_MESSAGE="Hello World"
echo $MY_MESSAGE
```

以上是`var.sh`的代码。用来学习变量的使用。环境变量使用以下代码实现：

```sh
$ export name=zuoyuan
```

```sh
#!/bin/sh
echo What is your name?
read MY_NAME
echo "Hello $MY_NAME - hope you're well."
```

以上是`var2.sh`的代码。

```sh
#!/bin/sh
echo "What is your name?"
read USER_NAME
echo "Hello $USER_NAME"
echo "I will create you a file called ${USER_NAME}_file"
touch "${USER_NAME}_file"
```

以上代码可以创建一个文件，`touch`关键字的作用是如果有这个文件，不做任何操作，如果没有这个文件，就创建一个这个文件。

```sh
#!/bin/sh
for i in 1 2 3 4 5
do
  echo "Looping ... number $i"
done
```

以上是`for`循环。写入`for.sh`。

```sh
#!/bin/sh
for i in hello 1 * 2 goodbye
do
  echo "Looping ... i is set to $i"
done
```

继续`for`循环。写入`for2.sh`中。

```sh
#!/bin/sh
INPUT_STRING=hello
while [ "$INPUT_STRING" != "bye" ]
do
  echo "Please type something in (bye to quit)"
  read INPUT_STRING
  echo "You typed: $INPUT_STRING"
done
```

`while`循环。

```sh
#!/bin/sh
while :
do
  echo "Please type something in (^C to quit)"
  read INPUT_STRING
  echo "You typed: $INPUT_STRING"
done
```

继续`while`循环。

```sh
#!/bin/sh
while read f
do
  case $f in
	hello)		echo English	;;
	howdy)		echo American	;;
	gday)		echo Australian	;;
	bonjour)	echo French	;;
	"guten tag")	echo German	;;
	*)		echo Unknown Language: $f
		;;
   esac
done < myfile
```

使用`while`循环读取文件。

```sh
for runlevel in 0 1 2 3 4 5 6 S
do
  mkdir rc${runlevel}.d
done
```

批量建文件。

```sh
if [ ... ]
then
  # if-code
else
  # else-code
fi
```

```sh
if [ ... ]; then
  # do something
fi
```

```sh
if  [ something ]; then
 echo "Something"
 elif [ something_else ]; then
   echo "Something else"
 else
   echo "None of the above"
fi
```

以上是几种条件结构。

```sh
#!/bin/sh
if [ "$X" -lt "0" ]
then
  echo "X is less than zero"
fi
if [ "$X" -gt "0" ]; then
  echo "X is more than zero"
fi
[ "$X" -le "0" ] && \
      echo "X is less than or equal to  zero"
[ "$X" -ge "0" ] && \
      echo "X is more than or equal to zero"
[ "$X" = "0" ] && \
      echo "X is the string or number \"0\""
[ "$X" = "hello" ] && \
      echo "X matches the string \"hello\""
[ "$X" != "hello" ] && \
      echo "X is not the string \"hello\""
[ -n "$X" ] && \
      echo "X is of nonzero length"
[ -f "$X" ] && \
      echo "X is the path of a real file" || \
      echo "No such file: $X"
[ -x "$X" ] && \
      echo "X is the path of an executable file"
[ "$X" -nt "/etc/passwd" ] && \
      echo "X is a file which is newer than /etc/passwd"
```

```sh
echo -en "Please guess the magic number: "
read X
echo $X | grep "[^0-9]" > /dev/null 2>&1
if [ "$?" -eq "0" ]; then
  # If the grep found something other than 0-9
  # then it's not an integer.
  echo "Sorry, wanted a number"
else
  # The grep found only 0-9, so it's an integer. 
  # We can safely do a test on it.
  if [ "$X" -eq "7" ]; then
    echo "You entered the magic number!"
  fi
fi
```

```sh
#!/bin/sh
X=0
while [ -n "$X" ]
do
  echo "Enter some text (RETURN to quit)"
  read X
  echo "You said: $X"
done
```

```sh
#!/bin/sh
X=0
while [ -n "$X" ]
do
  echo "Enter some text (RETURN to quit)"
  read X
  if [ -n "$X" ]; then
    echo "You said: $X"
  fi
done
```

```sh
if [ "$X" -lt "0" ]
then
  echo "X is less than zero"
fi

..........  and  ........

if [ ! -n "$X" ]; then
  echo "You said: $X"
fi
```

以上是几个条件结构的例子。
