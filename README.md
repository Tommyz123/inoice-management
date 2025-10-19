# Invoice Management System – 数据存储配置

该项目同时支持 **SQLite 本地数据库** 和 **Supabase** 两种后端。默认情况下，如果检测到 `.env` 中配置了 `SUPABASE_URL` 与 `SUPABASE_KEY`，系统会自动切换到 Supabase；否则落在本地 SQLite。

## 环境准备

1. 安装依赖  
   ```bash
   pip install -r requirements.txt
   ```
2. 复制 `.env.example`（如果存在）到 `.env`，并填入必要的环境变量。

## Supabase 配置步骤

1. 在 `.env` 写入：
   ```
   SUPABASE_URL=<你的 Supabase 项目 URL>
   SUPABASE_KEY=<你的服务密钥>
   SUPABASE_DB_PASSWORD=<Project Settings → Database → Password>
   DATA_BACKEND=supabase
   ```
2. 可选：通过额外环境变量覆盖数据库连接细节（通常无需修改）：  
   ```
   SUPABASE_DB_USER=postgres
   SUPABASE_DB_NAME=postgres
   SUPABASE_DB_HOST=db.<project-ref>.supabase.co
   SUPABASE_DB_PORT=5432
   SUPABASE_DB_SSLMODE=require
   ```
3. 首次运行时，应用会尝试使用 `psycopg` 连接 Supabase Postgres：若 `invoices` 表或匿名策略不存在，会自动创建以下对象：  
   - `public.invoices` 表（字段：`id`, `invoice_date`, `invoice_number`, `company_name`, `total_amount`, `entered_by`, `notes`, `pdf_path`, `inserted_at`）  
   - `allow anon insert`、`allow anon select` 两条 RLS 策略（仅在缺失时创建）  
   如果你需要更严格的访问控制，可在执行后在 Supabase 控制台修改这些策略。

## 文件上传

本系统支持两种文件存储方式：

### 1. Supabase Storage (云端存储，推荐) ☁️
- **优点**：文件安全存储在云端，自动备份，高可用性，节省本地空间
- **配置**：参见 [SUPABASE_STORAGE_SETUP.md](SUPABASE_STORAGE_SETUP.md) 详细配置指南
- **启用方式**：在 `.env` 中设置 `USE_SUPABASE_STORAGE=true`
- **注意**：需要先在 Supabase 控制台创建 `invoices` bucket 并配置 RLS 策略

### 2. 本地存储 (备用方案) 💾
- **优点**：无需额外配置，适合开发测试
- **位置**：PDF 文件存放在 `uploads/` 目录
- **启用方式**：在 `.env` 中设置 `USE_SUPABASE_STORAGE=false` 或不设置该变量

**推荐使用 Supabase Storage 以获得更好的可靠性和扩展性。**

配置示例（在 `.env` 文件中）：
```
USE_SUPABASE_STORAGE=true
STORAGE_BUCKET_NAME=invoices
```

## 常见问题

- **提示缺少 supabase-py**：说明运行环境未安装 Supabase SDK，执行 `pip install supabase-py` 或重新安装依赖。  
- **Supabase 连接报错**：检查 `SUPABASE_URL`、`SUPABASE_KEY` 是否有效，以及防火墙/网络代理是否允许外网访问。  
- **仍在使用 SQLite**：确认是否在 `.env` 中遗漏 Supabase 配置，或手动设置了 `DATA_BACKEND=sqlite`。
