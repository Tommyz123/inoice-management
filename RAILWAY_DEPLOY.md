# 🚂 Railway 部署完整指南

Railway 是最简单的部署方式之一，5分钟即可完成部署！

---

## 📋 前提条件

1. GitHub 账号
2. Railway 账号（使用 GitHub 登录即可）
3. 项目已推送到 GitHub

---

## 🚀 快速部署步骤

### 第一步：准备 GitHub 仓库

```bash
# 进入项目目录
cd invoice_system

# 初始化 Git（如果还没有）
git init

# 添加所有文件
git add .

# 提交
git commit -m "Initial commit: Invoice Management System"

# 添加远程仓库（替换为你的 GitHub 仓库地址）
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git

# 推送到 GitHub
git push -u origin main
```

### 第二步：部署到 Railway

1. **访问 Railway**
   - 打开 https://railway.app
   - 点击 "Login" 使用 GitHub 账号登录

2. **创建新项目**
   - 点击 "New Project"
   - 选择 "Deploy from GitHub repo"
   - 选择你的发票管理系统仓库

3. **等待自动部署**
   - Railway 会自动检测到 Python 项目
   - 自动安装依赖并启动应用
   - 通常需要 2-5 分钟

4. **配置环境变量**（重要！）
   - 在项目页面点击 "Variables"
   - 添加以下环境变量：

   ```env
   SECRET_KEY=你的随机密钥字符串
   DEBUG=False
   ```

   **生成安全的 SECRET_KEY**：
   ```python
   # 在本地运行
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

5. **获取部署地址**
   - 点击 "Settings" → "Domains"
   - 点击 "Generate Domain"
   - 复制自动生成的域名（格式：yourapp.railway.app）

---

## 🔧 配置选项

### 基础配置（本地 SQLite）

只需要设置 SECRET_KEY 即可：

```env
SECRET_KEY=your-secret-key-here
DEBUG=False
```

### 完整配置（Supabase 数据库 + 云存储）

```env
# 必需
SECRET_KEY=your-secret-key-here
DEBUG=False

# Supabase 数据库
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=your-anon-key
DATA_BACKEND=supabase

# Supabase Storage（可选）
USE_SUPABASE_STORAGE=true

# 数据库直连（用于自动建表）
SUPABASE_DB_PASSWORD=your-database-password
```

---

## 📁 重要文件说明

### `nixpacks.toml`（已创建）

这个文件告诉 Railway 如何构建和运行你的应用：

```toml
[phases.setup]
nixPkgs = ["poppler_utils"]

[phases.install]
cmds = ["pip install -r requirements.txt"]

[start]
cmd = "gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 app:app"
```

### `Procfile`（已存在）

备用配置文件：

```
web: gunicorn --bind 0.0.0.0:$PORT --workers 4 --timeout 120 app:app
```

### `runtime.txt`（已存在）

指定 Python 版本：

```
python-3.11
```

---

## ✅ 部署后检查清单

访问你的 Railway 域名并测试：

- [ ] 首页可以正常访问
- [ ] 可以上传 PDF 发票
- [ ] OCR 自动提取功能正常
- [ ] 可以编辑发票
- [ ] 可以删除发票
- [ ] 可以搜索和筛选
- [ ] PDF 文件可以查看

---

## 🐛 常见问题排查

### 问题 1: Application failed to respond

**原因：**
- 应用启动失败
- 依赖安装错误
- 环境变量配置错误

**解决方法：**

1. **查看构建日志**
   - 在 Railway 项目页面点击 "Deployments"
   - 点击最新的部署
   - 查看 "Build Logs" 和 "Deploy Logs"

2. **检查常见错误**
   ```
   # 如果看到 "Module not found"
   → 检查 requirements.txt 是否完整

   # 如果看到 "Port already in use"
   → 确保使用 $PORT 环境变量（已配置）

   # 如果看到 "No module named 'app'"
   → 检查 app.py 是否存在
   ```

3. **确保文件已推送到 GitHub**
   ```bash
   git status
   git add nixpacks.toml
   git commit -m "Add Railway configuration"
   git push
   ```

### 问题 2: 数据库连接失败

**解决方法：**
- 检查 Supabase URL 和 Key 是否正确
- 确保 `DATA_BACKEND=supabase` 已设置
- 检查 Supabase 项目是否处于活动状态

### 问题 3: 文件上传失败

**本地存储问题：**
- Railway 的文件系统是临时的
- 建议使用 Supabase Storage

**切换到 Supabase Storage：**
```env
USE_SUPABASE_STORAGE=true
SUPABASE_URL=your-url
SUPABASE_KEY=your-key
```

### 问题 4: 应用运行缓慢

**优化建议：**

1. **减少 Worker 数量**（节省内存）
   - 编辑 nixpacks.toml
   - 将 `--workers 2` 改为 `--workers 1`

2. **增加超时时间**
   - 保持 `--timeout 120`（已设置）

3. **使用 Supabase 数据库**
   - 避免 SQLite 在云环境的性能问题

---

## 💰 费用说明

### Railway 定价

- **免费额度**：$5/月
- **计费方式**：按使用量计费
- **预估费用**：小型项目通常 $5-10/月

### 节省费用技巧

1. **减少 Worker 数量**
   ```toml
   cmd = "gunicorn --bind 0.0.0.0:$PORT --workers 1 --timeout 120 app:app"
   ```

2. **使用休眠功能**
   - Railway 支持自动休眠
   - 无流量时自动停止，有请求时自动启动

3. **使用 Supabase 免费层**
   - 数据库：500MB 免费
   - Storage：1GB 免费

---

## 🔄 更新部署

每次推送代码到 GitHub，Railway 会自动重新部署：

```bash
# 修改代码后
git add .
git commit -m "Update features"
git push

# Railway 自动检测并重新部署
```

---

## 📊 监控和日志

### 查看应用日志

1. 进入 Railway 项目
2. 点击你的服务
3. 点击 "Deployments"
4. 查看实时日志

### 常用日志命令

Railway CLI（可选安装）：

```bash
# 安装 Railway CLI
npm i -g @railway/cli

# 登录
railway login

# 查看日志
railway logs

# 查看环境变量
railway variables
```

---

## 🔐 安全建议

### 必须配置的安全项

1. **强 SECRET_KEY**
   ```python
   # 至少 32 位随机字符串
   import secrets
   print(secrets.token_hex(32))
   ```

2. **关闭 DEBUG 模式**
   ```env
   DEBUG=False
   ```

3. **使用 HTTPS**
   - Railway 自动提供 HTTPS
   - 无需额外配置

4. **环境变量保护**
   - 不要将 `.env` 推送到 GitHub
   - 在 Railway 后台配置环境变量

---

## 🎓 推荐配置方案

### 个人使用

```env
SECRET_KEY=随机密钥
DEBUG=False
# 使用默认 SQLite
```

### 小团队使用

```env
SECRET_KEY=随机密钥
DEBUG=False
DATA_BACKEND=supabase
SUPABASE_URL=your-url
SUPABASE_KEY=your-key
USE_SUPABASE_STORAGE=true
```

### 生产环境

```env
SECRET_KEY=强随机密钥
DEBUG=False
DATA_BACKEND=supabase
SUPABASE_URL=your-url
SUPABASE_KEY=your-key
USE_SUPABASE_STORAGE=true
SUPABASE_DB_PASSWORD=your-db-password
```

---

## 📞 获取帮助

### Railway 文档
- https://docs.railway.app

### Railway 社区
- Discord: https://discord.gg/railway

### 项目问题排查顺序

1. 检查 Railway 部署日志
2. 检查环境变量配置
3. 确认所有文件已推送到 GitHub
4. 参考本文档的常见问题部分

---

## 🎉 部署成功！

完成部署后，你将拥有：

✅ 全功能的发票管理系统
✅ 自动 HTTPS 证书
✅ 公网可访问的域名
✅ 自动构建和部署
✅ 实时日志监控

**开始使用你的在线发票管理系统吧！** 🚀

---

**创建日期**：2025-10-18
**适用于**：Railway 云平台部署
