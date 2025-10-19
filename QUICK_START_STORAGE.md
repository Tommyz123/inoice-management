# ⚡ Supabase Storage 快速入门

这是一个5分钟的快速配置指南,帮助你立即启用 Supabase Storage 文件上传功能。

## ✅ 前提条件

确认以下配置已完成:
- [x] 已安装依赖: `pip install supabase`
- [x] `.env` 文件中已配置 `SUPABASE_URL` 和 `SUPABASE_KEY`
- [x] `.env` 文件中已添加 `USE_SUPABASE_STORAGE=true`

## 🚀 三步配置

### 第一步: 创建 Storage Bucket (2分钟)

1. 访问 [Supabase Dashboard](https://app.supabase.com)
2. 选择你的项目
3. 左侧菜单点击 **Storage**
4. 点击 **New bucket** 按钮
5. 填写以下信息:
   - **Bucket name**: `invoices`
   - **Public bucket**: ✅ **勾选此项**
   - 点击 **Create bucket**

![](https://i.imgur.com/storage-bucket.png)

---

### 第二步: 配置访问策略 (2分钟)

1. 在 Supabase Dashboard 左侧点击 **SQL Editor**
2. 点击 **New query**
3. 复制粘贴以下 SQL:

```sql
-- 允许上传、读取和删除文件
CREATE POLICY "Allow anon upload to invoices"
ON storage.objects FOR INSERT TO anon
WITH CHECK (bucket_id = 'invoices');

CREATE POLICY "Public read access to invoices"
ON storage.objects FOR SELECT
USING (bucket_id = 'invoices');

CREATE POLICY "Allow delete invoices"
ON storage.objects FOR DELETE TO anon
USING (bucket_id = 'invoices');
```

4. 点击 **Run** 执行
5. 看到 `Success` 即为成功

---

### 第三步: 验证配置 (1分钟)

在项目目录运行:

```bash
cd invoice_system
python -c "import storage_handler; print(storage_handler.test_connection())"
```

预期输出:
```
(True, 'Connection successful. Found 1 bucket(s).')
```

如果输出 `Found 0 bucket(s)` 或出现错误,请返回第一步检查bucket是否创建成功。

---

## 🎉 完成!

现在你可以:

1. **启动应用**:
   ```bash
   python app.py
   ```

2. **访问上传页面**: http://localhost:5000/upload

3. **上传PDF文件**:
   - 选择PDF文件
   - 填写发票信息
   - 点击 "Save Invoice"

4. **验证文件存储**:
   - 在 Supabase Dashboard → Storage → invoices 中查看上传的文件
   - 点击主页的 "View PDF" 按钮应能正常打开文件

---

## ❌ 常见问题

### Q1: 上传失败,提示 "Bucket 'invoices' does not exist"

**解决**:
- 返回第一步,确认bucket名称为 `invoices` (小写)
- 检查bucket是否真的创建成功

### Q2: 提示 "Upload permission denied" 或 403 错误

**解决**:
- 返回第二步,重新执行SQL语句
- 确认SQL执行成功无错误

### Q3: 点击 "View PDF" 显示 404

**解决**:
- 检查 Supabase Storage 中文件是否存在
- 确认第二步的 SELECT 策略已创建
- 检查 `.env` 中 `USE_SUPABASE_STORAGE=true`

---

## 📚 更多帮助

- 详细配置指南: [SUPABASE_STORAGE_SETUP.md](SUPABASE_STORAGE_SETUP.md)
- 官方文档: https://supabase.com/docs/guides/storage

---

**配置遇到问题?** 查看详细文档 [SUPABASE_STORAGE_SETUP.md](SUPABASE_STORAGE_SETUP.md) 的"故障排查"章节。
