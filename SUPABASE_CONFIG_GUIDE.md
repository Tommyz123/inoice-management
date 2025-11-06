# Supabase 配置指南

## 📋 问题说明

如果您上传发票后在 Supabase 中找不到数据，说明应用正在使用**本地 SQLite 数据库**而不是 Supabase。

---

## ✅ 解决方案：配置 Supabase 环境变量

### 步骤 1: 获取 Supabase 凭证

1. 登录 **Supabase Dashboard**: https://app.supabase.com
2. 选择您的项目
3. 点击左侧菜单的 **Settings** (齿轮图标)
4. 点击 **API** 选项卡
5. 找到以下两个值：
   - **Project URL** (例如：`https://xxxxx.supabase.co`)
   - **anon public key** (一串很长的字符串)

---

### 步骤 2: 创建 `.env` 文件

在项目根目录创建 `.env` 文件：

```bash
# 在项目根目录执行
cd /path/to/inoice-management
nano .env
```

或者在 Windows 上用记事本创建 `.env` 文件。

---

### 步骤 3: 添加配置到 `.env` 文件

将以下内容粘贴到 `.env` 文件中，**替换成您自己的值**：

```env
# Supabase Configuration
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-anon-public-key-here

# Flask Secret Key (可选，用于会话加密)
SECRET_KEY=your-random-secret-key-here

# 存储配置（可选）
USE_SUPABASE_STORAGE=true
STORAGE_BUCKET_NAME=invoices
```

**重要提示**：
- `SUPABASE_URL` 和 `SUPABASE_KEY` 从 Supabase Dashboard > Settings > API 获取
- **不要**将 `.env` 文件提交到 Git！（已在 `.gitignore` 中）

---

### 步骤 4: 运行数据库迁移

首次使用 Supabase 时，需要运行迁移脚本创建数据表：

#### 方法 A: 使用 Supabase SQL Editor（推荐）

1. 登录 Supabase Dashboard
2. 点击左侧菜单的 **SQL Editor**
3. 点击 **New Query**
4. 复制粘贴 `supabase_migration.sql` 文件的内容
5. 点击 **Run** 执行

#### 方法 B: 使用 Python 迁移脚本

如果您有数据库密码，可以使用 Python 脚本自动迁移：

```bash
# 1. 设置数据库密码环境变量
export SUPABASE_DB_PASSWORD="your-database-password"

# 2. 安装依赖（如果还没安装）
pip install psycopg

# 3. 运行迁移
python migrate_database.py
```

**如何获取数据库密码？**
- Supabase Dashboard > Settings > Database
- 找到 "Database password"
- 如果忘记了，点击 "Reset database password"

---

### 步骤 5: 配置 Supabase Storage（可选，用于存储 PDF 文件）

#### 5.1 创建 Storage Bucket

1. Supabase Dashboard > **Storage**
2. 点击 **New Bucket**
3. Bucket 名称：`invoices`
4. 设置为 **Public bucket**（允许公开访问 PDF）
5. 点击 **Create Bucket**

#### 5.2 设置 Bucket 策略

在 SQL Editor 中运行以下 SQL：

```sql
-- 允许匿名用户上传文件
CREATE POLICY "Allow anon upload"
ON storage.objects FOR INSERT
TO anon
WITH CHECK (bucket_id = 'invoices');

-- 允许所有人读取文件
CREATE POLICY "Allow public read"
ON storage.objects FOR SELECT
TO public
USING (bucket_id = 'invoices');

-- 允许匿名用户删除文件
CREATE POLICY "Allow anon delete"
ON storage.objects FOR DELETE
TO anon
USING (bucket_id = 'invoices');
```

---

### 步骤 6: 重启应用

配置完成后，重启应用：

```bash
python app.py
```

应用启动时会显示：

```
🗄️ Current database backend: supabase
```

如果显示 `sqlite`，说明配置有误，请检查 `.env` 文件。

---

## 🔍 验证配置

### 检查数据库后端

运行以下命令检查当前使用的后端：

```bash
python -c "
import database
backend = database.current_backend()
print(f'当前数据库后端: {backend}')
if backend == 'supabase':
    print('✅ 正在使用 Supabase')
else:
    print('❌ 正在使用本地 SQLite')
"
```

### 检查 Supabase 表

在 Supabase Dashboard 中：

1. 点击 **Table Editor**
2. 查看 `invoices` 表
3. 应该看到以下列：
   - id
   - invoice_date
   - invoice_number
   - company_name
   - total_amount
   - entered_by
   - notes
   - pdf_path
   - **payment_status** ✨ (新增)
   - **payment_proof_path** ✨ (新增)
   - **payment_date** ✨ (新增)
   - inserted_at

---

## ⚙️ 环境变量完整列表

| 变量名 | 必填 | 默认值 | 说明 |
|--------|------|--------|------|
| `SUPABASE_URL` | ✅ | - | Supabase 项目 URL |
| `SUPABASE_KEY` | ✅ | - | Supabase anon public key |
| `SECRET_KEY` | ❌ | "change-me" | Flask 密钥 |
| `DATA_BACKEND` | ❌ | 自动检测 | 强制指定后端（sqlite/supabase）|
| `USE_SUPABASE_STORAGE` | ❌ | false | 是否使用 Supabase Storage |
| `STORAGE_BUCKET_NAME` | ❌ | "invoices" | Storage bucket 名称 |
| `SUPABASE_DB_PASSWORD` | ❌ | - | 数据库密码（仅迁移时需要）|

---

## 🆘 常见问题

### Q1: 配置了环境变量，但仍然使用 SQLite？

**A:** 检查以下几点：
1. `.env` 文件是否在项目根目录
2. `.env` 文件格式是否正确（无多余空格）
3. 重启应用
4. 检查终端输出是否有错误信息

### Q2: 出现 "Supabase credentials are missing" 错误？

**A:** 说明环境变量未正确加载：
1. 确认 `.env` 文件存在
2. 确认 `python-dotenv` 已安装：`pip install python-dotenv`
3. 检查 `SUPABASE_URL` 和 `SUPABASE_KEY` 是否正确

### Q3: 表不存在错误？

**A:** 需要运行数据库迁移：
- 在 Supabase SQL Editor 中运行 `supabase_migration.sql`
- 或者运行 `python migrate_database.py`

### Q4: 文件上传失败？

**A:** 需要配置 Storage：
1. 创建 `invoices` bucket
2. 设置为 public
3. 添加必要的 Storage 策略
4. 在 `.env` 中设置 `USE_SUPABASE_STORAGE=true`

### Q5: 如何从 SQLite 迁移数据到 Supabase？

**A:** 可以使用以下脚本导出和导入数据：

```python
# export_sqlite.py
import sqlite3
import json

conn = sqlite3.connect('invoices.db')
cursor = conn.cursor()
cursor.execute('SELECT * FROM invoices')
columns = [desc[0] for desc in cursor.description]
rows = cursor.fetchall()

data = [dict(zip(columns, row)) for row in rows]
with open('invoices_backup.json', 'w') as f:
    json.dump(data, f, indent=2)

print(f'✅ Exported {len(data)} invoices')
```

然后在 Supabase SQL Editor 中手动导入或使用 Python 脚本批量插入。

---

## 📚 相关文档

- [Supabase 官方文档](https://supabase.com/docs)
- [Supabase Python 客户端](https://github.com/supabase-community/supabase-py)
- [项目设置指南](PAYMENT_FEATURE_SETUP.md)

---

## ✅ 配置检查清单

在启动应用前，确保完成：

- [ ] 已创建 `.env` 文件
- [ ] 已添加 `SUPABASE_URL` 和 `SUPABASE_KEY`
- [ ] 已运行数据库迁移（`supabase_migration.sql`）
- [ ] 已创建 Supabase Storage bucket（如果使用文件存储）
- [ ] 已设置 Storage 策略
- [ ] 应用启动时显示 "backend: supabase"

完成后，您的发票数据将自动保存到 Supabase 云数据库！🎉
