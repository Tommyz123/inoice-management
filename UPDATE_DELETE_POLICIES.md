# 添加更新和删除策略

如果您使用 Supabase 作为数据库后端,需要添加以下策略以支持编辑和删除功能。

## 选项 1: 自动创建(推荐)

系统会在启动时自动创建所需的策略。只需确保您的 `.env` 文件中配置了 `SUPABASE_DB_PASSWORD`。

## 选项 2: 手动在 Supabase Dashboard 创建

1. 访问 [Supabase Dashboard](https://app.supabase.com)
2. 选择您的项目
3. 左侧菜单点击 **SQL Editor**
4. 点击 **New query**
5. 复制粘贴以下 SQL:

```sql
-- 允许更新发票
CREATE POLICY "Allow anon update invoices"
ON storage.objects FOR UPDATE TO anon
USING (bucket_id = 'invoices')
WITH CHECK (bucket_id = 'invoices');

-- 允许删除发票
CREATE POLICY "Allow anon delete invoices"
ON storage.objects FOR DELETE TO anon
USING (bucket_id = 'invoices');

-- 允许更新发票表数据
CREATE POLICY "allow anon update"
ON public.invoices FOR UPDATE
USING (auth.role() IN ('anon', 'authenticated'))
WITH CHECK (auth.role() IN ('anon', 'authenticated'));

-- 允许删除发票表数据
CREATE POLICY "allow anon delete"
ON public.invoices FOR DELETE
USING (auth.role() IN ('anon', 'authenticated'));
```

6. 点击 **Run** 执行
7. 看到 `Success` 即为成功

## 验证

访问 http://localhost:5000 查看发票列表,每个发票旁边应该会显示 "Edit" 和 "Delete" 按钮。
