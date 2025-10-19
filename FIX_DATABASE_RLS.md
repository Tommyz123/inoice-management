# 🔧 修复数据库 RLS 策略问题

## 问题描述

上传发票时出现错误:
```
Failed to save invoice: new row violates row-level security policy for table "invoices"
```

这是因为 `invoices` 表的 Row Level Security (RLS) 策略配置不正确,阻止了数据插入。

---

## ⚡ 快速修复 (2分钟)

### 方法一: 使用SQL脚本 (推荐)

1. **打开 Supabase SQL Editor**
   - 访问 https://app.supabase.com
   - 选择你的项目
   - 左侧菜单点击 **SQL Editor**

2. **新建查询并执行SQL**
   - 点击 **New query**
   - 复制粘贴以下SQL:

```sql
-- 删除旧的错误策略
DROP POLICY IF EXISTS "allow anon insert" ON public.invoices;
DROP POLICY IF EXISTS "allow anon select" ON public.invoices;
DROP POLICY IF EXISTS "allow anon update" ON public.invoices;
DROP POLICY IF EXISTS "allow anon delete" ON public.invoices;

-- 创建正确的策略
CREATE POLICY "allow anon insert"
ON public.invoices
FOR INSERT
TO anon
WITH CHECK (true);

CREATE POLICY "allow anon select"
ON public.invoices
FOR SELECT
TO anon, authenticated
USING (true);

CREATE POLICY "allow anon update"
ON public.invoices
FOR UPDATE
TO anon
USING (true)
WITH CHECK (true);

CREATE POLICY "allow anon delete"
ON public.invoices
FOR DELETE
TO anon
USING (true);
```

3. **点击 Run 执行**
   - 应该看到 `Success` 消息
   - 可能会显示一些策略不存在的警告,这是正常的

4. **验证策略创建成功**

   执行以下查询查看所有策略:
   ```sql
   SELECT policyname, cmd as operation, roles
   FROM pg_policies
   WHERE tablename = 'invoices';
   ```

   应该看到4个策略:
   - `allow anon insert` - INSERT
   - `allow anon select` - SELECT
   - `allow anon update` - UPDATE
   - `allow anon delete` - DELETE

---

### 方法二: 通过 Supabase Dashboard

1. **进入表设置**
   - Supabase Dashboard → Database → Tables
   - 找到 `invoices` 表
   - 点击表名进入详情

2. **删除现有策略**
   - 点击 **Policies** 标签
   - 删除所有现有的策略

3. **创建新策略**

   **策略1: 允许插入**
   - Policy name: `allow anon insert`
   - Allowed operation: `INSERT`
   - Target roles: `anon`
   - WITH CHECK expression: `true`

   **策略2: 允许读取**
   - Policy name: `allow anon select`
   - Allowed operation: `SELECT`
   - Target roles: `anon`, `authenticated`
   - USING expression: `true`

   **策略3: 允许更新**
   - Policy name: `allow anon update`
   - Allowed operation: `UPDATE`
   - Target roles: `anon`
   - USING expression: `true`
   - WITH CHECK expression: `true`

   **策略4: 允许删除**
   - Policy name: `allow anon delete`
   - Allowed operation: `DELETE`
   - Target roles: `anon`
   - USING expression: `true`

---

## 🧪 测试修复

修复后,重新上传发票:

1. **访问上传页面**: http://localhost:5000/upload
2. **选择PDF文件并填写信息**
3. **点击 "Save Invoice"**
4. **应该看到成功消息**: "Invoice saved successfully."

---

## 🔍 问题原因

原代码中的RLS策略定义有误:

**错误的策略** (使用了 USING 子句):
```sql
CREATE POLICY "allow anon insert" ON public.invoices
FOR INSERT
USING (auth.role() = 'anon')  -- ❌ INSERT 不应该用 USING
WITH CHECK (auth.role() = 'anon');
```

**正确的策略**:
```sql
CREATE POLICY "allow anon insert"
ON public.invoices
FOR INSERT
TO anon
WITH CHECK (true);  -- ✅ INSERT 只用 WITH CHECK
```

**解释**:
- `USING` 子句: 用于 SELECT、UPDATE、DELETE,判断**哪些行**可以访问
- `WITH CHECK` 子句: 用于 INSERT、UPDATE,判断**新数据**是否允许
- INSERT 操作不需要 USING,因为没有"现有行"需要检查

---

## 📚 RLS 策略说明

### 当前策略: 完全开放 (适合内部使用)

- ✅ 任何人可以插入数据
- ✅ 任何人可以读取数据
- ✅ 任何人可以更新数据
- ✅ 任何人可以删除数据

**适用场景**: 公司内部局域网使用,无需用户认证

### 生产环境建议

如果需要对外开放,建议修改为:

```sql
-- 仅允许已认证用户操作
CREATE POLICY "authenticated users only"
ON public.invoices
FOR ALL
TO authenticated
USING (true)
WITH CHECK (true);
```

或者更严格的基于用户的策略:

```sql
-- 用户只能操作自己创建的记录
CREATE POLICY "users own records"
ON public.invoices
FOR ALL
TO authenticated
USING (entered_by = auth.email())
WITH CHECK (entered_by = auth.email());
```

---

## ✅ 验收清单

修复完成后,确认以下项目:

- [ ] SQL执行成功,无错误
- [ ] 可以看到4个策略(INSERT, SELECT, UPDATE, DELETE)
- [ ] 上传发票成功
- [ ] 主页能看到上传的记录
- [ ] 点击 "View PDF" 能打开文件

---

## 🆘 仍然有问题?

### 问题1: SQL执行失败,提示权限不足

**原因**: 使用的 API Key 权限不够

**解决**: 使用 `service_role` key 而不是 `anon` key:
- Supabase Dashboard → Settings → API
- 复制 `service_role` key (⚠️ 仅在服务端使用)

### 问题2: 修复后仍然报错

**排查步骤**:
1. 确认策略已创建: 运行验证查询
2. 检查表名是否正确: `public.invoices`
3. 清除浏览器缓存并刷新页面
4. 重启Flask应用

---

**修复完成!** 🎉

现在你可以正常使用发票管理系统了。
