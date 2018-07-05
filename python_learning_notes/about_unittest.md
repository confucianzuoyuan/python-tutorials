```py
import unittest

class TestStringMethods(unittest.TestCase):

	# setUp函数是测试前的准备工作
	def setUp(self):
		pass

    def test_upper(self):
        self.assertEqual('foo'.upper(), 'FOO')

    def test_isupper(self):
        self.assertTrue('FOO'.isupper())
        self.assertFalse('Foo'.isupper())

    def test_split(self):
        s = 'hello world'
        self.assertEqual(s.split(), ['hello', 'world'])
        # check that s.split fails when the separator is not a string
        with self.assertRaises(TypeError):
            s.split(2)

    # 测试用例全部执行完以后，运行的清理工作
    def tearDown(self):
    	pass

if __name__ == '__main__':
    unittest.main()
```

在编写python的测试用例时，首先要看到测试用例的类继承自`unittest.TestCase`，其次测试用例的类中的测试用例函数必须以`test_`开头。

然后是要熟悉`assert`也就是`断言`的用法。`assert`后面的表达式如果为`True`，则不会报异常，什么都不发生，相当于`pass`。如果表达式为`False`，则报异常。

```
>>>assert 1 == 1 # 不会报异常
>>>assert 1 == 2 # 报异常
```