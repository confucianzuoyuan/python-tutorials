# 读写分离，主从，master-slave
- master机器只用来写入
- slave机器只能用来读取
- 读写分离的问题：数据同步的问题，master机器会把新写入数据的同步到slave机器上，毫秒级别

# mysql binlog的作用

# mysql 慢查询日志
# mysql explain语句

# 不能漫无目的的建索引(create index)，因为索引建的多了以后，同样会带来性能问题，因为每多一个索引，都会增加写操作的开销和磁盘空间的开销。
- 有针对性的建索引，通过explain和查看慢查询日志，来找出性能的瓶颈

# django程序如何进行优化
- 缓存策略，redis
- 耗时任务异步化，celery
- 优化orm查询，优化queryset查询
- 静态资源存到cdn(阿里云图片云存储，七牛云，又拍云)
- 负载均衡

![](https://www.jianshu.com/p/43091bfa8aa7)
![](https://coolshell.cn/articles/1846.html)
![](https://juejin.im/entry/590427815c497d005832dab9)

# 分布式强一致性的解决算法
- Paxos
- Raft

# mysql建索引
- CREATE INDEX indexName ON mytable(username(length)); 
- ALTER table tableName ADD INDEX indexName(columnName)

# mysql复合索引，针对多个字段一起建索引
- CREATE INDEX idx_example ON table1 (col1 ASC, col2 DESC, col3 ASC)