# 发票管理系统部署指南

本指南提供多种部署方案,从简单到复杂,您可以根据需求选择合适的方式。

---

## 📋 目录

1. [准备工作](#准备工作)
2. [方案1: 本地/内网部署](#方案1-本地内网部署)
3. [方案2: Docker 部署](#方案2-docker-部署)
4. [方案3: 云平台部署](#方案3-云平台部署)
5. [方案4: Vercel 部署](#方案4-vercel-部署)
6. [环境变量配置](#环境变量配置)
7. [常见问题](#常见问题)

---

## 准备工作

### 1. 检查系统要求

- Python 3.8+
- 如果使用 OCR 功能,需要安装 Tesseract OCR
- 数据库: SQLite (默认) 或 Supabase/PostgreSQL

### 2. 克隆/复制项目

确保您有完整的项目文件夹。

---

## 方案1: 本地/内网部署

### 适用场景
- 公司内网使用
- 小团队协作
- 快速启动测试

### 部署步骤

#### Step 1: 安装生产服务器

当前使用的是 Flask 开发服务器,生产环境需要使用 **Gunicorn** 或 **Waitress**。

**Windows 用户推荐 Waitress:**
```bash
pip install waitress
```

**Linux/Mac 用户推荐 Gunicorn:**
```bash
pip install gunicorn
```

#### Step 2: 创建生产环境配置

创建 `.env` 文件 (如果还没有):
```bash
# 基础配置
SECRET_KEY=your-secret-key-change-this-to-random-string
DEBUG=False

# Supabase 配置 (可选)
SUPABASE_URL=your-supabase-url
SUPABASE_KEY=your-supabase-key
USE_SUPABASE_STORAGE=false

# 数据库配置 (可选)
DATA_BACKEND=sqlite
```

#### Step 3: 启动生产服务器

**Windows:**
```bash
cd invoice_system
waitress-serve --host=0.0.0.0 --port=8000 app:app
```

**Linux/Mac:**
```bash
cd invoice_system
gunicorn --bind 0.0.0.0:8000 --workers 4 app:app
```

#### Step 4: 访问应用

- 本地访问: `http://localhost:8000`
- 局域网访问: `http://你的IP地址:8000`

### 开机自启动 (可选)

**Windows - 创建批处理文件 `start_invoice.bat`:**
```batch
@echo off
cd C:\path\to\invoice_system
call venv\Scripts\activate
waitress-serve --host=0.0.0.0 --port=8000 app:app
```

**Linux - 创建 systemd 服务:**
```bash
sudo nano /etc/systemd/system/invoice-system.service
```

内容:
```ini
[Unit]
Description=Invoice Management System
After=network.target

[Service]
User=your-username
WorkingDirectory=/path/to/invoice_system
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/gunicorn --bind 0.0.0.0:8000 --workers 4 app:app

[Install]
WantedBy=multi-user.target
```

启动服务:
```bash
sudo systemctl daemon-reload
sudo systemctl enable invoice-system
sudo systemctl start invoice-system
```

---

## 方案2: Docker 部署

### 适用场景
- 跨平台部署
- 容器化环境
- 易于扩展和迁移

### 部署步骤

#### Step 1: 创建 Dockerfile

我已经为您准备好了 Dockerfile (见下方文件)。

#### Step 2: 创建 docker-compose.yml

我已经为您准备好了 docker-compose.yml (见下方文件)。

#### Step 3: 构建并运行

```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

#### Step 4: 访问应用

访问: `http://localhost:8000`

---

## 方案3: 云平台部署

### 选项 A: Heroku 部署

#### Step 1: 准备 Heroku 配置文件

需要创建:
- `Procfile` (已准备)
- `runtime.txt` (已准备)

#### Step 2: 部署到 Heroku

```bash
# 安装 Heroku CLI
# 访问: https://devcenter.heroku.com/articles/heroku-cli

# 登录
heroku login

# 创建应用
heroku create your-invoice-app

# 设置环境变量
heroku config:set SECRET_KEY=your-secret-key
heroku config:set SUPABASE_URL=your-supabase-url
heroku config:set SUPABASE_KEY=your-supabase-key

# 部署
git add .
git commit -m "Deploy to Heroku"
git push heroku main

# 打开应用
heroku open
```

### 选项 B: Railway 部署

Railway 是更简单的 Heroku 替代方案。

#### 步骤:
1. 访问 [railway.app](https://railway.app)
2. 连接 GitHub 仓库
3. 选择项目
4. 设置环境变量
5. 自动部署完成!

### 选项 C: Render 部署

1. 访问 [render.com](https://render.com)
2. 创建新的 Web Service
3. 连接 GitHub 仓库
4. 配置:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
5. 设置环境变量
6. 部署!

### 选项 D: AWS/Azure/GCP

如果需要企业级部署,可以使用:
- **AWS**: Elastic Beanstalk / EC2 + RDS
- **Azure**: App Service + Azure Database
- **GCP**: App Engine / Cloud Run

---

## 方案4: Vercel 部署

### 注意事项
Vercel 主要用于静态网站,但可以通过 serverless 函数部署 Flask。

不过对于这个项目,**不推荐 Vercel**,因为:
- 需要文件上传功能
- 有数据库连接
- 更适合传统服务器部署

---

## 环境变量配置

### 生产环境必需配置

```env
# 安全密钥 (必需)
SECRET_KEY=使用随机字符串,至少32位

# 调试模式 (生产环境设为 False)
DEBUG=False

# 数据库后端
DATA_BACKEND=sqlite  # 或 supabase

# Supabase 配置 (如果使用)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
USE_SUPABASE_STORAGE=true

# Supabase 数据库直连 (自动创建表)
SUPABASE_DB_PASSWORD=your-db-password
SUPABASE_DB_USER=postgres
SUPABASE_DB_NAME=postgres
```

### 生成安全的 SECRET_KEY

**Python:**
```python
import secrets
print(secrets.token_hex(32))
```

**或在线生成:**
访问: https://randomkeygen.com/

---

## 性能优化建议

### 1. 使用生产数据库
- 从 SQLite 迁移到 PostgreSQL (Supabase)
- 提高并发性能

### 2. 配置工作进程
```bash
# Gunicorn 推荐配置
gunicorn --workers 4 --threads 2 --bind 0.0.0.0:8000 app:app
```

工作进程数建议: `(2 × CPU核心数) + 1`

### 3. 使用反向代理
- 使用 Nginx 作为反向代理
- 处理静态文件
- SSL/HTTPS 配置

### 4. 启用缓存
- Redis 缓存查询结果
- 浏览器缓存静态资源

---

## 安全建议

### 1. HTTPS/SSL
生产环境**必须**使用 HTTPS:
- 使用 Let's Encrypt 免费证书
- 云平台通常自动提供 SSL

### 2. 防火墙配置
只开放必要端口:
```bash
# 示例 (ufw)
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable
```

### 3. 环境变量安全
- **不要**将 `.env` 文件提交到 Git
- 使用云平台的环境变量管理

### 4. 数据库安全
- 使用强密码
- 限制数据库访问 IP
- 定期备份

---

## 监控和日志

### 应用日志
```bash
# 查看 Docker 日志
docker-compose logs -f app

# 查看 systemd 日志
sudo journalctl -u invoice-system -f

# Gunicorn 日志文件
gunicorn --access-logfile access.log --error-logfile error.log app:app
```

### 推荐监控工具
- **Sentry**: 错误追踪
- **Datadog**: 性能监控
- **Uptime Robot**: 可用性监控

---

## 备份策略

### 数据库备份

**SQLite:**
```bash
# 手动备份
cp invoices.db invoices.db.backup

# 定时备份 (crontab)
0 2 * * * cp /path/to/invoices.db /backups/invoices-$(date +\%Y\%m\%d).db
```

**Supabase:**
- 使用 Supabase Dashboard 的自动备份功能
- 或使用 `pg_dump`:
```bash
pg_dump -h db.xxx.supabase.co -U postgres postgres > backup.sql
```

### 文件备份

如果使用本地存储:
```bash
tar -czf uploads-backup.tar.gz uploads/
```

---

## 常见问题

### Q1: 端口被占用怎么办?

**Windows:**
```cmd
netstat -ano | findstr :8000
taskkill /PID <进程ID> /F
```

**Linux:**
```bash
sudo lsof -i :8000
sudo kill -9 <PID>
```

### Q2: 文件上传失败

检查:
1. 上传目录权限: `chmod 755 uploads/`
2. 文件大小限制
3. Supabase Storage 配置

### Q3: 数据库连接失败

检查:
1. `.env` 文件配置
2. 网络连接
3. 数据库服务状态

### Q4: OCR 功能不可用

安装 Tesseract OCR:

**Ubuntu/Debian:**
```bash
sudo apt-get install tesseract-ocr tesseract-ocr-chi-sim
```

**Windows:**
下载安装: https://github.com/UB-Mannheim/tesseract/wiki

**Mac:**
```bash
brew install tesseract tesseract-lang
```

---

## 推荐部署方案

### 小型项目 (< 100 用户)
→ **Docker + VPS** 或 **Railway/Render**

### 中型项目 (100-1000 用户)
→ **Docker + 云服务器** + **PostgreSQL/Supabase**

### 大型项目 (> 1000 用户)
→ **Kubernetes** + **负载均衡** + **CDN**

---

## 下一步

部署完成后,建议:
1. ✅ 测试所有功能
2. ✅ 配置 HTTPS
3. ✅ 设置自动备份
4. ✅ 配置监控告警
5. ✅ 准备用户文档

---

**需要帮助?** 查看具体的配置文件或遇到问题请告诉我!
