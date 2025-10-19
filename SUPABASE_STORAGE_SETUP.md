# 📦 Supabase Storage 配置指南

本文档介绍如何配置 Supabase Storage 用于存储发票 PDF 文件。

---

## 🎯 配置目标

将 PDF 文件从本地存储迁移到 Supabase Storage 云端存储,实现:
- ✅ 文件安全存储在云端
- ✅ 公开访问 PDF 文件(无需登录)
- ✅ 自动备份和高可用性
- ✅ 节省本地磁盘空间

---

## 📋 前置条件

1. ✅ 已有 Supabase 账号和项目
2. ✅ 已在 `.env` 文件中配置了 `SUPABASE_URL` 和 `SUPABASE_KEY`
3. ✅ Python 环境已安装 `supabase` 库 (`pip install supabase`)

---

## 🛠️ 配置步骤

### 第一步: 创建 Storage Bucket

1. **登录 Supabase Dashboard**
   - 访问 https://app.supabase.com
   - 选择你的项目

2. **进入 Storage 页面**
   - 在左侧菜单点击 **Storage**
   - 点击 **New bucket** 按钮

3. **创建 bucket**
   - **Name**: `invoices`
   - **Public bucket**: ✅ **勾选** (允许公开访问)
   - **File size limit**: `10485760` (10MB)
   - **Allowed MIME types**: `application/pdf`
   - 点击 **Create bucket**

   ![创建 Bucket 示例](https://supabase.com/docs/img/storage/new-bucket.png)

---

### 第二步: 配置 Row Level Security (RLS) 策略

Storage 使用 RLS 策略控制文件访问权限。我们需要创建策略允许:
- ✅ 匿名用户上传文件 (INSERT)
- ✅ 所有人读取文件 (SELECT)
- ✅ 删除文件 (DELETE, 用于后续编辑功能)

#### 方法一: 通过 SQL Editor (推荐)

1. 在 Supabase Dashboard 左侧点击 **SQL Editor**
2. 点击 **New query**
3. 复制粘贴以下 SQL 语句:

```sql
-- 1. 允许匿名用户上传 PDF 到 invoices bucket
CREATE POLICY "Allow anon upload to invoices"
ON storage.objects
FOR INSERT
TO anon
WITH CHECK (bucket_id = 'invoices');

-- 2. 允许所有人读取 invoices bucket 的文件
CREATE POLICY "Public read access to invoices"
ON storage.objects
FOR SELECT
USING (bucket_id = 'invoices');

-- 3. 允许删除文件 (用于编辑功能)
CREATE POLICY "Allow delete invoices"
ON storage.objects
FOR DELETE
TO anon
USING (bucket_id = 'invoices');
```

4. 点击 **Run** 执行 SQL
5. 看到 `Success. No rows returned` 表示创建成功

#### 方法二: 通过 Storage Policies UI

1. 在 Storage 页面点击 `invoices` bucket
2. 点击 **Policies** 标签
3. 点击 **New Policy** 创建以下策略:

**策略 1: 允许上传**
- Policy name: `Allow anon upload to invoices`
- Allowed operation: `INSERT`
- Target roles: `anon`
- Policy definition: `bucket_id = 'invoices'`

**策略 2: 允许读取**
- Policy name: `Public read access to invoices`
- Allowed operation: `SELECT`
- Target roles: `anon`, `authenticated`
- USING expression: `bucket_id = 'invoices'`

**策略 3: 允许删除**
- Policy name: `Allow delete invoices`
- Allowed operation: `DELETE`
- Target roles: `anon`
- USING expression: `bucket_id = 'invoices'`

---

### 第三步: 更新环境变量

编辑项目根目录的 `.env` 文件,添加以下配置:

```env
# Supabase Storage 配置
USE_SUPABASE_STORAGE=true
STORAGE_BUCKET_NAME=invoices
```

**说明**:
- `USE_SUPABASE_STORAGE=true`: 启用 Supabase Storage (设为 `false` 将使用本地存储)
- `STORAGE_BUCKET_NAME=invoices`: Storage bucket 名称

完整的 `.env` 文件示例:

```env
# Supabase 数据库配置
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_DB_PASSWORD=your_db_password

# 数据库后端
DATA_BACKEND=supabase

# Supabase Storage 配置
USE_SUPABASE_STORAGE=true
STORAGE_BUCKET_NAME=invoices

# 应用密钥 (可选)
SECRET_KEY=your-secret-key-here
```

---

### 第四步: 验证配置

1. **重启应用**
   ```bash
   python app.py
   ```

2. **测试连接**

   在 Python 环境中运行:
   ```python
   import storage_handler

   # 测试连接
   success, message = storage_handler.test_connection()
   print(message)
   # 预期输出: Connection successful. Found X bucket(s).
   ```

3. **测试上传功能**
   - 访问 http://localhost:5000/upload
   - 选择一个 PDF 文件
   - 填写表单并提交
   - 检查是否上传成功

4. **验证文件存储**
   - 在 Supabase Dashboard → Storage → invoices
   - 应该能看到上传的文件
   - 点击文件查看是否可以正常访问

---

## ✅ 验收清单

配置完成后,请验证以下项目:

- [ ] ✅ Supabase Storage 中存在 `invoices` bucket
- [ ] ✅ Bucket 设置为 Public (公开访问)
- [ ] ✅ 已创建 3 个 RLS 策略 (INSERT, SELECT, DELETE)
- [ ] ✅ `.env` 中 `USE_SUPABASE_STORAGE=true`
- [ ] ✅ 上传 PDF 文件成功
- [ ] ✅ 文件出现在 Supabase Storage 中
- [ ] ✅ 点击 "View PDF" 可以正常打开文件
- [ ] ✅ 本地 `uploads/` 目录不再生成新文件

---

## 🔧 故障排查

### 问题 1: 上传失败,提示 "Bucket 'invoices' does not exist"

**原因**: Bucket 未创建

**解决方案**:
1. 检查 Supabase Dashboard → Storage 中是否存在 `invoices` bucket
2. 确保 bucket 名称拼写正确(区分大小写)
3. 重新按照"第一步"创建 bucket

---

### 问题 2: 上传失败,提示 "Upload permission denied" 或 403 错误

**原因**: RLS 策略未配置或配置错误

**解决方案**:
1. 检查 Storage → invoices → Policies
2. 确认存在 INSERT 策略且 Target roles 包含 `anon`
3. 重新执行"第二步"的 SQL 语句

---

### 问题 3: 点击 "View PDF" 无法打开,显示 404

**原因**: SELECT 策略未配置,或文件不存在

**解决方案**:
1. 检查是否创建了 SELECT 策略
2. 在 Supabase Storage 中确认文件存在
3. 检查数据库中 `pdf_path` 字段的值是否正确

---

### 问题 4: 仍在使用本地存储,文件未上传到 Supabase

**原因**: `USE_SUPABASE_STORAGE` 未启用

**解决方案**:
1. 检查 `.env` 文件中 `USE_SUPABASE_STORAGE=true` (注意大小写)
2. 重启 Flask 应用
3. 运行测试:
   ```python
   import storage_handler
   print(storage_handler.should_use_storage())
   # 应该输出: True
   ```

---

### 问题 5: 提示 "supabase library not installed"

**原因**: Python 环境缺少 supabase 库

**解决方案**:
```bash
pip install supabase
# 或
pip install -r requirements.txt
```

---

## 📊 存储空间管理

### 免费版限制

Supabase 免费版提供:
- 💾 **1 GB** Storage 空间
- 📤 **2 GB** 每月流量

### 空间计算

- 平均每个 PDF 文件: **500 KB - 2 MB**
- 1 GB 可存储约: **500 - 2000** 个发票文件

### 监控用量

1. Supabase Dashboard → Settings → Usage
2. 查看 Storage 使用情况
3. 接近限制时考虑:
   - 升级到付费计划 ($25/月)
   - 删除旧文件
   - 压缩 PDF 文件

---

## 🔒 安全建议

### 当前配置 (开发/内部使用)
- ✅ 允许匿名上传 (适合内部局域网使用)
- ✅ 公开读取 (所有人可查看文件)

### 生产环境建议

如果系统需要对外开放,建议:

1. **添加用户认证**
   ```sql
   -- 仅允许已认证用户上传
   CREATE POLICY "Authenticated users can upload"
   ON storage.objects
   FOR INSERT
   TO authenticated
   WITH CHECK (bucket_id = 'invoices');
   ```

2. **限制删除权限**
   ```sql
   -- 仅允许文件所有者删除
   CREATE POLICY "Users can delete their own files"
   ON storage.objects
   FOR DELETE
   TO authenticated
   USING (bucket_id = 'invoices' AND owner = auth.uid());
   ```

3. **添加文件大小验证**
   - 在 bucket 设置中限制单文件大小
   - 在应用层二次验证

---

## 📚 相关文档

- [Supabase Storage 官方文档](https://supabase.com/docs/guides/storage)
- [Python Storage API 参考](https://supabase.com/docs/reference/python/storage-from-upload)
- [RLS 策略编写指南](https://supabase.com/docs/guides/storage/security/access-control)

---

## 🆘 获取帮助

如果遇到问题:
1. 查看本文档的"故障排查"部分
2. 检查 Supabase Dashboard 的日志
3. 在项目 Issues 中提问

---

**配置完成!** 🎉

现在你的发票系统已经使用 Supabase Storage 云端存储,享受安全、可靠的文件管理服务。
