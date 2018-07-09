Table: `Person`

```
+-------------+---------+
| Column Name | Type    |
+-------------+---------+
| PersonId    | int     |
| FirstName   | varchar |
| LastName    | varchar |
+-------------+---------+
PersonId 是这张表的主键
```

Table: `Address`

```
+-------------+---------+
| Column Name | Type    |
+-------------+---------+
| AddressId   | int     |
| PersonId    | int     |
| City        | varchar |
| State       | varchar |
+-------------+---------+
AddressId 是这张表的主键。
PersonId 是这张表的外键。
```

题目：查询所有人的以下字段
```
FirstName, LastName, City, State
```

```sql
SELECT p.FirstName, p.LastName, a.City, a.State FROM Person as p LEFT OUTER JOIN Address as a on p.PersonId = a.PersonId
```