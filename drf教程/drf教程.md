# 1, 序列化 Serialization
## 创建一个新环境
在做其他事之前，我们会用virtualenv创建一个新的虚拟环境。这将确保我们的包配置与我们正在工作的其他项目完全隔离。
```
virtualenv env          # 创建虚拟环境，命名: env
source env/bin/activate # 进入虚拟环境env
```
既然我们已经在虚拟环境中，那么我们就可以安装我们依赖的包了。
```
pip install django
pip install djangorestframework
pip install pygments # 代码高亮插件
```
## 开始
首先，我们来创建一个新项目。
```
cd ~
django-admin.py startproject tutorial
cd tutorial
```
输完以上命令，我们就可以创建一个应用，我们将会用他来创建简单的Web API。
```
python manage.py startapp snippets
```
我们会添加一个新的`snippets`应用和`rest_framework`应用到`INSTALLED_APPS`。让我们编辑`tutorial/settings.py`文件:
```
INSTALLED_APPS = (
    ...
    'rest_framework',
    'snippets.apps.SnippetsConfig',
)
```
Ok, 我们准备下一步。
## 创建一个 Model
为了实现本教程的目的，我们将创建一个简单的`Snippet`模型，这个模型用来保存`snippets`代码。开始编辑`snippets/models.py`文件。
```
from django.db import models
from pygments.lexers import get_all_lexers
from pygments.styles import get_all_styles

LEXERS = [item for item in get_all_lexers() if item[1]]
LANGUAGE_CHOICES = sorted([(item[1][0], item[0]) for item in LEXERS])
STYLE_CHOICES = sorted((item, item) for item in get_all_styles())


class Snippet(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=100, blank=True, default='')
    code = models.TextField()
    linenos = models.BooleanField(default=False)
    language = models.CharField(choices=LANGUAGE_CHOICES, default='python', max_length=100)
    style = models.CharField(choices=STYLE_CHOICES, default='friendly', max_length=100)

    class Meta:
        ordering = ('created',)
```
我们也需要为我们的snippet模型创建一个初始迁移(initial migration)，然后第一次同步数据库。
```
python manage.py makemigrations snippets
python manage.py migrate
```
## 创建一个序列化类（Serializer class）
着手我们的Web API，首先要做的是，提供一种将我们的`snippet`实例序列化/反序列化成例如`json`这样的表述形式。我们可以通过声明序列来完成，这些序列与`Django`的表单`(forms)`工作相似。在`snippets`目录创建一个新文件`serializers.py`，添加下列代码。
```
from rest_framework import serializers
from snippets.models import Snippet, LANGUAGE_CHOICES, STYLE_CHOICES


class SnippetSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    title = serializers.CharField(required=False, allow_blank=True, max_length=100)
    code = serializers.CharField(style={'base_template': 'textarea.html'})
    linenos = serializers.BooleanField(required=False)
    language = serializers.ChoiceField(choices=LANGUAGE_CHOICES, default='python')
    style = serializers.ChoiceField(choices=STYLE_CHOICES, default='friendly')

    def create(self, validated_data):
        """
        Create and return a new `Snippet` instance, given the validated data.
        """
        return Snippet.objects.create(**validated_data)

    def update(self, instance, validated_data):
        """
        Update and return an existing `Snippet` instance, given the validated data.
        """
        instance.title = validated_data.get('title', instance.title)
        instance.code = validated_data.get('code', instance.code)
        instance.linenos = validated_data.get('linenos', instance.linenos)
        instance.language = validated_data.get('language', instance.language)
        instance.style = validated_data.get('style', instance.style)
        instance.save()
        return instance
```
序列化类(serializer class)的第一部分定义了一些需要被序列化/反序列化字段。`create()`和`update()`方法定义了在调用`serializer.save()`时成熟的实例是如何被创建和修改的。 序列化类(serializer class)与Django的表单类(Form class)非常相似，包括对各种字段有相似的确认标志(flag)，例如`required`，`max_length`和`default`。 在某些情况下，这些字段标志也能控制序列应该怎么表现，例如在将序列渲染成HTML时。`{'base_template': 'textarea.html}'`标志相当于对Django表单(Form)类使用`widget=widgets.Textarea`。这对控制API的显示尤其有用，以后的教程将会看到。 事实上，以后我们可以通过使用`ModelSerializer`类来节约我们的时间，但是现在为了让我们序列化定义更清晰，我们用Serializer类。
## 用序列化(Serializers)工作
在我们深入之前，我们需要熟练使用新的序列化列(Serializer class)。然我们开始使用Django命令行吧。
```
python manage.py shell
```
Okay，让我们写一些snippets代码来使序列化工作。
```
from snippets.models import Snippet
from snippets.serializers import SnippetSerializer
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser

snippet = Snippet(code='foo = "bar"\n')
snippet.save()

snippet = Snippet(code='print "hello, world"\n')
snippet.save()
```
现在我们已经有了一些snippet实例。让我们看看如何将其中一个实例序列化。
> 注: Model -> Serializer
```
serializer = SnippetSerializer(snippet)
serializer.data
# {'id': 2, 'title': u'', 'code': u'print "hello, world"\n', 'linenos': False, 'language': u'python', 'style': u'friendly'}
```
现在，我们已经将模型实例(model instance)转化成Python原生数据类型。为了完成实例化过程，我们要将数据渲染成json。
> 注: Serializer -> JSON
```
content = JSONRenderer().render(serializer.data)
content
# '{"id": 2, "title": "", "code": "print \\"hello, world\\"\\n", "linenos": false, "language": "python", "style": "friendly"}'
```
反序列化也一样。首先，我们需要将流(stream)解析成Python原生数据类型...
> 注: stream -> json
```
from django.utils.six import BytesIO

stream = BytesIO(content)
data = JSONParser().parse(stream)
```
...然后我们要将Python原生数据类型恢复成正常的对象实例。
```
serializer = SnippetSerializer(data=data)
serializer.is_valid()
# True
serializer.validated_data
# OrderedDict([('title', ''), ('code', 'print "hello, world"\n'), ('linenos', False), ('language', 'python'), ('style', 'friendly')])
serializer.save()
# <Snippet: Snippet object>
```
可以看到，API和表单(forms)是多么相似啊。当我们用我们的序列写视图的时候，相似性会相当明显。 除了将模型实例`(model instance)`序列化外，我们也能序列化查询集`(querysets)`，只需要添加一个序列化参数`many=True`。
```
serializer = SnippetSerializer(Snippet.objects.all(), many=True)
serializer.data
# [OrderedDict([('id', 1), ('title', u''), ('code', u'foo = "bar"\n'), ('linenos', False), ('language', 'python'), ('style', 'friendly')]), OrderedDict([('id', 2), ('title', u''), ('code', u'print "hello, world"\n'), ('linenos', False), ('language', 'python'), ('style', 'friendly')]), OrderedDict([('id', 3), ('title', u''), ('code', u'print "hello, world"'), ('linenos', False), ('language', 'python'), ('style', 'friendly')])]
```
## 使用模型序列化ModelSerializers
我们的`SnippetSerializer`类复制了包含`Snippet`模型在内的很多信息。如果我们能简化我们的代码，那就更好了。 以`Django`提供表单`(Form)`类和模型表单`(ModelForm)`类相同的方式，`REST` 框架包括了实例化`(Serializer)`类和模型实例化`(ModelSerializer)`类。 我们来看看用`ModelSerializer`类创建的序列。再次打开`snippets/serializers.py`文件，用下面的代码重写`SnippetSerializer`类。
```
class SnippetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Snippet
        fields = ('id', 'title', 'code', 'linenos', 'language', 'style')
```
序列一个非常棒的属性就是，你能够通过打印序列实例的结构`(representation)`查看它的所有字段。输入`python manage.py shell`打开命令行，然后尝试以下代码:
```
from snippets.serializers import SnippetSerializer
serializer = SnippetSerializer()
print(repr(serializer))
# SnippetSerializer():
#    id = IntegerField(label='ID', read_only=True)
#    title = CharField(allow_blank=True, max_length=100, required=False)
#    code = CharField(style={'base_template': 'textarea.html'})
#    linenos = BooleanField(required=False)
#    language = ChoiceField(choices=[('Clipper', 'FoxPro'), ('Cucumber', 'Gherkin'), ('RobotFramework', 'RobotFramework'), ('abap', 'ABAP'), ('ada', 'Ada')...
#    style = ChoiceField(choices=[('autumn', 'autumn'), ('borland', 'borland'), ('bw', 'bw'), ('colorful', 'colorful')...
```
记住，`ModelSerializer`类并没有做什么有魔力的事情，它们仅仅是一个创建序列化类的快捷方式。
- 一个自动决定的字段集合。
- 简单的默认`create()`和`update()`方法的实现。
## 用我们的序列化来写常规的Django视图
让我们看看，使用我们新的序列化类，我们怎么写一些API视图。此刻，我们不会使用REST框架的其他特性，仅仅像写常规Django视图一样。 通过创建`HttpResponse`的一个子类来开始，其中，我们可以用这个自雷来渲染任何我们返回的`json`数据。 编辑`snippets/views.py`文件，添加以下代码。
```
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from snippets.models import Snippet
from snippets.serializers import SnippetSerializer
```
我们的根API将是一个支持列出所有存在的`snippets`的视图，或者创建一个新的`snippet`对象。
```
@csrf_exempt
def snippet_list(request):
    """
    List all code snippets, or create a new snippet.
    """
    if request.method == 'GET':
        snippets = Snippet.objects.all()
        serializer = SnippetSerializer(snippets, many=True)
        return JsonResponse(serializer.data, safe=False)

    elif request.method == 'POST':
        data = JSONParser().parse(request)
        serializer = SnippetSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data, status=201)
        return JsonResponse(serializer.errors, status=400)
```
注意，因为我们希望可以从没有`CSRF token`的客户端`POST`数据到这个视图，我们需要标记这个视图为`csrf_exempt`。通常，你并不想这么做，并且事实上REST框架视图更实用的做法不是这样的，但是目前来说，这足以到达我们的目的。 我们也需要一个与单个`snippet`对象相应的视图，并且我们使用这个视图来读取、更新或者删除这个`snippet`对象。
```
@csrf_exempt
def snippet_detail(request, pk):
    """
    Retrieve, update or delete a code snippet.
    """
    try:
        snippet = Snippet.objects.get(pk=pk)
    except Snippet.DoesNotExist:
        return HttpResponse(status=404)

    if request.method == 'GET':
        serializer = SnippetSerializer(snippet)
        return JsonResponse(serializer.data)

    elif request.method == 'PUT':
        data = JSONParser().parse(request)
        serializer = SnippetSerializer(snippet, data=data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data)
        return JsonResponse(serializer.errors, status=400)

    elif request.method == 'DELETE':
        snippet.delete()
        return HttpResponse(status=204)
```
最终，我们需要用线将这些视图连起来。创建`snippets/urls.py`文件:
```
from django.conf.urls import url
from snippets import views

urlpatterns = [
    url(r'^snippets/$', views.snippet_list),
    url(r'^snippets/(?P<pk>[0-9]+)/$', views.snippet_detail),
]
```
我们也需要在根url配置文件tutorial/urls.py中添加我们的snippet应用URL。
```
from django.conf.urls import url, include

urlpatterns = [
    url(r'^', include('snippets.urls')),
]
```
有一些当时我们没有正确处理的边缘事件是没有价值的。如果我们发送不正确的json数据，或者如果我们制造了一个视图没有写处理的方法(method)，那么我们会得到500“服务器错误”的响应。当然，现在也会出现这个问题。
## 测试我们Web API的第一次努力
现在我们开始创建一个测试服务器来服务我们的snippets应用。 退出命令行......
```
quit()
```
...然后启动Django开发服务器。
```
python manage.py runserver

Validating models...

0 errors found
Django version 1.11, using settings 'tutorial.settings'
Development server is running at http://127.0.0.1:8000/
Quit the server with CONTROL-C.
```
我们可以在另一个终端测试服务器。 我们可以用curl和httpie来测试我们的API。Httpie是一个面向用户的非常友好的http客户端，它是用Python写的。让我们来安装它。 你可以通过pip来安装httpie：
```
pip install httpie
```
最后，我们来获取一个包含所有snippets的列表：
```
http http://127.0.0.1:8000/snippets/

HTTP/1.1 200 OK
...
[
  {
    "id": 1,
    "title": "",
    "code": "foo = \"bar\"\n",
    "linenos": false,
    "language": "python",
    "style": "friendly"
  },
  {
    "id": 2,
    "title": "",
    "code": "print \"hello, world\"\n",
    "linenos": false,
    "language": "python",
    "style": "friendly"
  }
]
```
或者我们可以通过id来获取指定的snippet：
```
http http://127.0.0.1:8000/snippets/2/

HTTP/1.1 200 OK
...
{
  "id": 2,
  "title": "",
  "code": "print \"hello, world\"\n",
  "linenos": false,
  "language": "python",
  "style": "friendly"
}
```
相似地，你可以通过在浏览器中访问这些链接来获得相同的json数据。
## 我们现在在哪
到目前为止，我们做的都很好，我们已经获得一个序列化API，这和Django的表单API非常相似，并且我们写好了一些常用的Django视图。 现在，我们的API视图除了服务于json外，不会做任何其他特别的东西，并且有一些错误我们仍然需要清理，但是它是一个可用的Web API。 我们将会在本教程的第二部分改善这里东西。