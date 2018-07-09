# 读写分离，主从，master-slave

- master机器只用来写入
- slave机器只能用来读取
- 读写分离的问题：数据同步的问题，master机器会把新写入数据的同步到slave机器上，毫秒级别

django配置如下

```py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    },
    'db2': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db2.sqlite3'),
    },
}
```

手动进行读写分离的orm操作

```py
def write(request):
    models.Products.objects.using('default').create(prod_name='熊猫公仔', prod_price=12.99)
    return HttpResponse('写入成功')


def read(request):
    obj = models.Products.objects.filter(id=1).using('db2').first()
    return HttpResponse(obj.prod_name)
```

# mysql binlog的作用

- binlog日志用于记录所有更新了数据或者已经潜在更新了数据（例如，没有匹配任何行的一个DELETE）的所有语句。语句以“事件”的形式保存，它描述数据更改。

# mysql 慢查询日志

```sql
# 慢查询日志存放路径
log slow queries = /data/mysqldata/slowquery.log

# 多慢才叫慢查询的定义
long_query_time = 2
```


# mysql explain语句

```sql
explain select * from s_books;
```

```
+----+-------------+---------+------------+------+---------------+------+---------+------+------+----------+-------+
| id | select_type | table   | partitions | type | possible_keys | key  | key_len | ref  | rows | filtered | Extra |
+----+-------------+---------+------------+------+---------------+------+---------+------+------+----------+-------+
|  1 | SIMPLE      | s_books | NULL       | ALL  | NULL          | NULL | NULL    | NULL |    2 |   100.00 | NULL  |
+----+-------------+---------+------------+------+---------------+------+---------+------+------+----------+-------+
1 row in set, 1 warning (0.01 sec)
```

# 不能漫无目的的建索引(create index)

- 因为索引建的多了以后，同样会带来性能问题，因为每多一个索引，都会增加写操作的开销和磁盘空间的开销。

- 有针对性的建索引，通过explain和查看慢查询日志，来找出性能的瓶颈

# django程序如何进行优化
- 缓存策略，redis
- 耗时任务异步化，celery
- 优化orm查询，优化queryset查询
- 静态资源存到cdn(阿里云图片云存储，七牛云，又拍云)
- 负载均衡

# 几个链接

- [MySQL慢查询&分析SQL执行效率浅谈](https://www.jianshu.com/p/43091bfa8aa7)
- [MYSQL性能优化的最佳20+条经验](https://coolshell.cn/articles/1846.html)
- [我必须得告诉大家的 MySQL 优化原理](https://juejin.im/entry/590427815c497d005832dab9)
- [MySQL 备份和恢复机制](https://juejin.im/entry/5a0aa2026fb9a045132a369f)
- [ACID 原理](https://www.jianshu.com/p/907c9dd99ee5)

# mysql建索引
- CREATE INDEX indexName ON mytable(username(length)); 
- ALTER table tableName ADD INDEX indexName(columnName)

# mysql复合索引，针对多个字段一起建索引
- CREATE INDEX idx_example ON table1 (col1 ASC, col2 DESC, col3 ASC)