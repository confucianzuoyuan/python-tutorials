### 题目一

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

### 题目二

Table: `Employee`

```
+----+--------+
| Id | Salary |
+----+--------+
| 1  | 100    |
| 2  | 200    |
| 3  | 300    |
+----+--------+
```

从这张表中查询`第二高薪`，并将查询到的列命名为`SecondHighestSalary`。

结果为：

```
+---------------------+
| SecondHighestSalary |
+---------------------+
| 200                 |
+---------------------+
```

解答：

```sql
SELECT MAX(Salary)
FROM Employee
WHERE Salary < (SELECT MAX(Salary) FROM Employee);
```

### 题目三

Table: `Person`

```
+----+---------+
| Id | Email   |
+----+---------+
| 1  | a@b.com |
| 2  | c@d.com |
| 3  | a@b.com |
+----+---------+
```

题目：寻找重复的`Email`。

解答：

```sql
SELECT Email FROM Person GROUP BY Email HAVING COUNT(*) > 1;
```

### 题目四

Table: `Employee`

```
+----+-------+--------+--------------+
| Id | Name  | Salary | DepartmentId |
+----+-------+--------+--------------+
| 1  | Joe   | 70000  | 1            |
| 2  | Henry | 80000  | 2            |
| 3  | Sam   | 60000  | 2            |
| 4  | Max   | 90000  | 1            |
+----+-------+--------+--------------+
```

Table: `Department`

```
+----+----------+
| Id | Name     |
+----+----------+
| 1  | IT       |
| 2  | Sales    |
+----+----------+
```

题意：要求查询每个部门的最高工资的员工。

结果为：

```
+------------+----------+--------+
| Department | Employee | Salary |
+------------+----------+--------+
| IT         | Max      | 90000  |
| Sales      | Henry    | 80000  |
+------------+----------+--------+
```

解答：

```sql
SELECT D.Name AS Department, E.Name AS Employee, MAXS_D.MAXS AS Salary
FROM Employee AS E, Department AS D, (
  SELECT MAX(Salary) AS MAXS, DepartmentId
  FROM Employee
  GROUP BY DepartmentId) AS MAXS_D
WHERE E.Salary = MAXS_D.MAXS AND E.DepartmentId = D.Id AND 
  E.DepartmentId = MAXS_D.DepartmentId;
```