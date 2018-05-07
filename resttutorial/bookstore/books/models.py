from django.db import models
PYTHON = 1
JAVASCRIPT = 2
ALGORITHMS = 3
MACHINELEARNING = 4
OPERATINGSYSTEM = 5
DATABASE = 6

BOOKS_TYPE = {
    PYTHON: 'Python',
    JAVASCRIPT: 'Javascript',
    ALGORITHMS: '数据结构与算法',
    MACHINELEARNING: '机器学习',
    OPERATINGSYSTEM: '操作系统',
    DATABASE: '数据库',
}

OFFLINE = 0
ONLINE = 1

STATUS_CHOICE = {
    OFFLINE: '下线',
    ONLINE: '上线'
}

# Create your models here.
class Books(models.Model):
    '''商品模型类'''
    books_type_choices = ((k, v) for k,v in BOOKS_TYPE.items())
    status_choices = ((k, v) for k,v in STATUS_CHOICE.items())
    type_id = models.SmallIntegerField(default=PYTHON, choices=books_type_choices, verbose_name='商品种类')
    name = models.CharField(max_length=20, verbose_name='商品名称')
    desc = models.CharField(max_length=128, verbose_name='商品简介')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='商品价格')
    unit = models.CharField(max_length=20, verbose_name='商品单位')
    stock = models.IntegerField(default=1, verbose_name='商品库存')
    sales = models.IntegerField(default=0, verbose_name='商品销量')
    status = models.SmallIntegerField(default=ONLINE, choices=status_choices, verbose_name='商品状态')
    is_delete = models.BooleanField(default=False, verbose_name='删除标记')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    update_time = models.DateTimeField(auto_now=TabError, verbose_name='更新时间')


    class Meta:
        db_table = 's_books'