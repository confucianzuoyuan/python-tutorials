"""
一个简单的模板引擎，Django模板引擎的子集
参考文档：https://juejin.im/post/5a52e87f5188257340261417
"""


import re


class TempliteSyntaxError(ValueError):
    """渲染出现错误时，自定义的异常"""
    pass


class CodeBuilder(object):
    """这是一个代码生成器，用来添加缩进之类的，退回缩进等等功能。"""

    def __init__(self, indent=0):
        self.code = [] # 代码
        self.indent_level = indent # 缩进等级，以空格数来定义。

    # 这里重写了__str__方法，而且会递归调用。
    def __str__(self):
        return "".join(str(c) for c in self.code)

    def add_line(self, line):
        """
        添加一行代码

        缩进和换行符的提供

        """
        self.code.extend([" " * self.indent_level, line, "\n"])

    def add_section(self):
        """添加一个代码块"""
        section = CodeBuilder(self.indent_level)
        self.code.append(section)
        return section

    INDENT_STEP = 4      # PEP8标准

    def indent(self):
        """添加4个空格的缩进"""
        self.indent_level += self.INDENT_STEP

    def dedent(self):
        """删除4个空格的缩进"""
        self.indent_level -= self.INDENT_STEP

    def get_globals(self):
        """执行代码，并收集定义的全局变量，global_namespace是一个字典"""
        # 做一个断言，看看现在的缩进等级是否为0，只有当缩进等级为0时，代码块才能执行。
        assert self.indent_level == 0
        # python_source是源码字符串，注意这里str调用了自身的重写过的__str__方法，所以有可能递归调用。
        python_source = str(self)
        # 使用exec执行代码，并返回全局变量字典。
        global_namespace = {}
        exec(python_source, global_namespace)
        return global_namespace


class Templite(object):
    """

    支持过滤器用法:

        {{var.modifer.modifier|filter|filter}}

    支持循环:

        {% for var in list %}...{% endfor %}

    支持if:

        {% if var %}...{% endif %}

    支持注释:

        {# This will be ignored #}

    一个示例：

        templite = Templite('''
            <h1>Hello {{name|upper}}!</h1>
            {% for topic in topics %}
                <p>You are interested in {{topic}}.</p>
            {% endif %}
            ''',
            {'upper': str.upper},
        )
        text = templite.render({
            'name': "Ned",
            'topics': ['Python', 'Geometry', 'Juggling'],
        })

    """
    def __init__(self, text, *contexts):
        """
        text是我们编写的模板，contexts是自定义的过滤器或者全局变量。
        """
        self.context = {}
        for context in contexts:
            self.context.update(context)
        print('self.context: ', self.context)

        self.all_vars = set() # 所有的变量的集合
        self.loop_vars = set() # for循环变量的集合，比如for i in range(10):，这个i就要被添加到loop_vars中。

        # 定义一个函数字符串，以供执行。
        code = CodeBuilder()

        code.add_line("def render_function(context, do_dots):")
        code.indent()
        vars_code = code.add_section()
        code.add_line("result = []")
        code.add_line("append_result = result.append") # 缓存append方法
        code.add_line("extend_result = result.extend") # 缓存extend方法
        code.add_line("to_str = str") # 缓存str方法

        buffered = []
        def flush_output():
            """建一个缓冲区，缓冲一段代码，add_line操作完之后，flush掉。"""
            if len(buffered) == 1:
                code.add_line("append_result(%s)" % buffered[0])
            elif len(buffered) > 1:
                code.add_line("extend_result([%s])" % ", ".join(buffered))
            del buffered[:]

        ops_stack = [] # 这是一个栈

        # 将模板text用正则匹配出一系列token。
        # '?s'为单行模式
        tokens = re.split(r"(?s)({{.*?}}|{%.*?%}|{#.*?#})", text)

        for token in tokens:
            if token.startswith('{#'):
                # 碰到注释忽略掉
                continue
            elif token.startswith('{{'):
                # 碰到两个花括号说明是需要求值
                expr = self._expr_code(token[2:-2].strip())
                print('expr: ', expr)
                buffered.append("to_str(%s)" % expr)
            elif token.startswith('{%'):
                # 碰到'{%'说明不是if就是for
                flush_output()
                words = token[2:-2].strip().split()
                if words[0] == 'if':
                    # 带if的代码，肯定len(words) == 2，要不就是语法错误。
                    if len(words) != 2:
                        self._syntax_error("if语句编写有问题", token)
                    ops_stack.append('if') # 入栈if
                    code.add_line("if %s:" % self._expr_code(words[1]))
                    code.indent()
                elif words[0] == 'for':
                    # for循环是4个token，比如for i in range(10):
                    # 第二个token肯定是in
                    if len(words) != 4 or words[2] != 'in':
                        self._syntax_error("for语句编写有问题", token)
                    ops_stack.append('for') # 入栈for
                    self._variable(words[1], self.loop_vars)
                    code.add_line(
                        "for c_%s in %s:" % (
                            words[1],
                            self._expr_code(words[3])
                        )
                    )
                    code.indent()
                elif words[0].startswith('end'):
                    # 不管是endif或者endfor，都必须以end开头。
                    if len(words) != 1:
                        self._syntax_error("end语句编写有问题", token)
                    end_what = words[0][3:] # 提取出是for还是if
                    if not ops_stack:
                        self._syntax_error("end太多了", token)
                    start_what = ops_stack.pop() # 出栈if或者for
                    if start_what != end_what:
                        self._syntax_error("end符号不能匹配if或者for", end_what)
                    code.dedent()
                else:
                    self._syntax_error("无法理解的标签", words[0])
            else:
                # Literal content.  If it isn't empty, output it.
                if token:
                    buffered.append(repr(token)) # repr()转化为供解释器读取的形式。str()用于将值转化为适于人阅读的形式。

        if ops_stack:
            self._syntax_error("无法匹配的动作标签", ops_stack[-1])

        flush_output()

        for var_name in self.all_vars - self.loop_vars: # 去掉循环中的变量，剩下的变量
            vars_code.add_line("c_%s = context[%r]" % (var_name, var_name))

        code.add_line("return ''.join(result)")
        code.dedent()
        print(code)
        print(code.get_globals()['render_function'])
        self._render_function = code.get_globals()['render_function']

    def _expr_code(self, expr):
        """产生一个可供执行的python表达式"""
        if "|" in expr:
            pipes = expr.split("|")
            code = self._expr_code(pipes[0]) # 递归调用
            for func in pipes[1:]:
                self._variable(func, self.all_vars)
                code = "c_%s(%s)" % (func, code)
        elif "." in expr:
            dots = expr.split(".")
            code = self._expr_code(dots[0]) # 递归调用
            args = ", ".join(repr(d) for d in dots[1:])
            code = "do_dots(%s, %s)" % (code, args)
        else:
            self._variable(expr, self.all_vars)
            code = "c_%s" % expr
        return code

    def _syntax_error(self, msg, thing):
        """抛异常"""
        raise TempliteSyntaxError("%s: %r" % (msg, thing))

    def _variable(self, name, vars_set):
        """
        检验变量名的合法性，并将变量添加到vars_set中。
        """
        if not re.match(r"[_a-zA-Z][_a-zA-Z0-9]*$", name): # 判断变量命名合法性
            self._syntax_error("Not a valid name", name)
        vars_set.add(name)

    def render(self, context=None):
        """
        render函数，和django中的render类似，context和django中的context也一样。
        """
        # Make the complete context we'll use.
        render_context = dict(self.context)
        if context:
            render_context.update(context)
        return self._render_function(render_context, self._do_dots)

    def _do_dots(self, value, *dots):
        """
        在运行时求值，主要用来处理'.'操作符。dots为key值，比如product.id，那么id就是dots。
        """
        print('value: ', value)
        print('dots: ', dots)
        for dot in dots:
            try:
                value = getattr(value, dot)
            except AttributeError:
                value = value[dot]
            if callable(value):
                value = value()
        return value

if __name__ == '__main__':
    templite = Templite('''
        <h1>Hello {{name|upper}}!</h1>
        <h2>product: {{product.id}}</h2>
        {% for topic in topics %}
            <p>You are interested in {{topic}}.</p>
        {% endfor %}
        ''',
        {'upper': str.upper},
    )
    def func():
        return 10
    text = templite.render({
        'name': "Ned",
        'topics': ['Python', 'Javascript'],
        'product': {'id': func},
    })
    print(text)