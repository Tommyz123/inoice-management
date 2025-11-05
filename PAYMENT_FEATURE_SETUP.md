# 付款凭证功能 - 数据库设置指南

本指南说明如何为不同的数据库后端设置新的付款凭证功能。

## 📋 需要添加的字段

- `payment_status` (TEXT, NOT NULL, DEFAULT 'unpaid') - 付款状态
- `payment_proof_path` (TEXT, NULLABLE) - 付款凭证文件路径
- `payment_date` (TEXT, NULLABLE) - 付款日期

---

## 🔹 场景 1: 新安装（没有现有数据库）

### ✅ SQLite
**无需任何操作！** 启动应用时会自动创建包含所有新字段的数据库。

### ✅ Supabase
**无需任何操作！** 首次连接时会自动创建包含所有新字段的表。

---

## 🔹 场景 2: 现有 SQLite 数据库

### 选项 A: 使用自动迁移脚本（推荐）

```bash
python migrate_database.py
```

### 选项 B: 手动运行 SQL

```bash
sqlite3 invoices.db < add_payment_fields.sql
```

### 选项 C: 使用 SQLite 命令行

```bash
sqlite3 invoices.db
```

然后执行：

```sql
ALTER TABLE invoices ADD COLUMN payment_status TEXT DEFAULT 'unpaid' NOT NULL;
ALTER TABLE invoices ADD COLUMN payment_proof_path TEXT;
ALTER TABLE invoices ADD COLUMN payment_date TEXT;
UPDATE invoices SET payment_status = 'unpaid' WHERE payment_status IS NULL;
.quit
```

---

## 🔹 场景 3: 现有 Supabase 数据库 ⚠️

**需要手动迁移！** Supabase 不会自动添加新列到现有表。

### 方法 1: 通过 Supabase SQL Editor（最简单）

1. 登录 Supabase Dashboard: https://app.supabase.com
2. 选择您的项目
3. 点击左侧菜单的 **SQL Editor**
4. 创建新查询
5. 复制粘贴 `supabase_migration.sql` 文件的内容
6. 点击 **Run** 执行

### 方法 2: 使用 Python 迁移脚本

1. 设置环境变量：

```bash
export SUPABASE_DB_PASSWORD="your_database_password"
```

> **如何获取数据库密码？**
> 1. 进入 Supabase Project Settings > Database
> 2. 找到 "Database password"
> 3. 如果忘记了，点击 "Reset database password"

2. 安装依赖：

```bash
pip install psycopg
```

3. 运行迁移：

```bash
python migrate_database.py
```

### 验证迁移是否成功

在 Supabase SQL Editor 中运行：

```sql
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'invoices'
  AND table_schema = 'public'
ORDER BY column_name;
```

应该看到新增的三个字段：
- `payment_date`
- `payment_proof_path`
- `payment_status`

---

## 🔍 如何检查是否需要迁移？

### SQLite

```bash
sqlite3 invoices.db "PRAGMA table_info(invoices);"
```

查找是否有 `payment_status`, `payment_proof_path`, `payment_date` 列。

### Supabase

在 SQL Editor 中运行：

```sql
SELECT EXISTS (
    SELECT 1
    FROM information_schema.columns
    WHERE table_name = 'invoices'
      AND column_name = 'payment_status'
);
```

- 返回 `true` = 已迁移 ✅
- 返回 `false` = 需要迁移 ⚠️

---

## ⚠️ 常见问题

### Q: 迁移后现有发票的付款状态是什么？
**A:** 所有现有发票会自动设置为 "unpaid"（未付款）。

### Q: 迁移会删除数据吗？
**A:** 不会！迁移只是添加新列，不会修改或删除任何现有数据。

### Q: 可以回滚吗？
**A:** 可以，但不推荐。如果需要回滚：

**SQLite:**
```sql
ALTER TABLE invoices DROP COLUMN payment_status;
ALTER TABLE invoices DROP COLUMN payment_proof_path;
ALTER TABLE invoices DROP COLUMN payment_date;
```

**Supabase (SQL Editor):**
```sql
ALTER TABLE public.invoices
DROP COLUMN IF EXISTS payment_status,
DROP COLUMN IF EXISTS payment_proof_path,
DROP COLUMN IF EXISTS payment_date;
```

### Q: 我用的是 Supabase，但不想设置数据库密码？
**A:** 直接在 Supabase Dashboard 的 SQL Editor 中运行 `supabase_migration.sql` 即可，无需密码。

---

## 📝 迁移文件说明

| 文件 | 用途 |
|-----|------|
| `add_payment_fields.sql` | 通用 SQL 迁移脚本（SQLite/PostgreSQL） |
| `supabase_migration.sql` | Supabase 专用迁移脚本（带验证） |
| `migrate_database.py` | Python 自动迁移工具（支持两种后端） |

---

## ✅ 迁移完成后

启动应用：

```bash
python app.py
```

或使用 Gunicorn：

```bash
gunicorn --bind 0.0.0.0:8000 --workers 4 app:app
```

访问发票编辑页面，您应该能看到新的 "Payment Information" 部分！

---

## 🆘 需要帮助？

如果遇到问题，请检查：

1. ✅ 数据库连接是否正常
2. ✅ 环境变量是否正确设置
3. ✅ 依赖包是否已安装（`pip install -r requirements.txt`）
4. ✅ 迁移脚本是否成功执行

查看应用日志获取详细错误信息。
