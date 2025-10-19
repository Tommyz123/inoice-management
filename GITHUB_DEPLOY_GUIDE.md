# 📦 GitHub 上传和云平台部署完整指南

本指南将手把手教您如何将项目上传到 GitHub,然后部署到云平台。

---

## 🎯 为什么需要 GitHub?

大多数云平台(Railway, Render, Heroku)都是从 GitHub 仓库自动部署的,所以需要:
1. ✅ 将代码上传到 GitHub
2. ✅ 连接 GitHub 到云平台
3. ✅ 自动部署

**好处:**
- 代码有版本控制
- 自动化部署
- 团队协作方便
- 免费备份

---

## 📋 准备工作

### 1. 检查是否安装 Git

打开命令行,运行:
```bash
git --version
```

**如果没有安装:**
- Windows: 下载安装 https://git-scm.com/download/win
- Mac: `brew install git`
- Linux: `sudo apt-get install git`

### 2. 注册 GitHub 账号

如果还没有账号:
1. 访问 https://github.com
2. 点击 "Sign up"
3. 按提示完成注册

### 3. 配置 Git (首次使用)

```bash
git config --global user.name "你的名字"
git config --global user.email "your-email@example.com"
```

---

## 🚀 步骤 1: 初始化 Git 仓库

打开命令行,进入项目目录:

```bash
# 进入项目目录
cd C:\Users\zhi89\Desktop\ai\sample\invotery\invoice_system

# 初始化 Git 仓库
git init

# 添加所有文件
git add .

# 查看将要提交的文件
git status

# 提交到本地仓库
git commit -m "Initial commit: Invoice Management System with CRUD and beautiful UI"
```

**重要:** `.gitignore` 文件已经创建好了,会自动排除敏感文件(.env, *.db等)。

---

## 🌐 步骤 2: 创建 GitHub 仓库

### 方法 1: 网页创建(推荐)

1. **登录 GitHub** → https://github.com

2. **创建新仓库:**
   - 点击右上角 "+" → "New repository"
   - Repository name: `invoice-management-system` (或其他名字)
   - Description: `Modern invoice management system with OCR and cloud storage`
   - **不要勾选** "Initialize this repository with a README"
   - 点击 "Create repository"

3. **记住仓库地址:**
   ```
   https://github.com/你的用户名/invoice-management-system.git
   ```

### 方法 2: 命令行创建(需要 GitHub CLI)

```bash
# 安装 GitHub CLI (可选)
# Windows: winget install GitHub.cli
# Mac: brew install gh

# 登录
gh auth login

# 创建仓库
gh repo create invoice-management-system --public --source=. --remote=origin
```

---

## 📤 步骤 3: 推送到 GitHub

在项目目录执行:

```bash
# 添加远程仓库地址 (替换成你的仓库地址)
git remote add origin https://github.com/你的用户名/invoice-management-system.git

# 推送到 GitHub
git branch -M main
git push -u origin main
```

**如果需要登录:**
- GitHub 现在使用 Personal Access Token (PAT)
- 创建 Token: GitHub → Settings → Developer settings → Personal access tokens → Generate new token
- 权限选择: `repo` (全部勾选)
- 复制 Token (只显示一次!)
- 推送时输入 Token 而不是密码

---

## ✅ 验证上传成功

访问您的仓库地址:
```
https://github.com/你的用户名/invoice-management-system
```

应该能看到所有项目文件!

---

## 🚀 步骤 4: 部署到云平台

现在可以选择任意云平台部署!

### 选项 1: Railway 部署(最推荐)

**优点:** 简单、快速、自动 HTTPS、免费额度

**步骤:**

1. **访问 Railway** → https://railway.app

2. **登录:**
   - 使用 GitHub 账号登录
   - 授权 Railway 访问你的仓库

3. **创建新项目:**
   - 点击 "New Project"
   - 选择 "Deploy from GitHub repo"
   - 选择 `invoice-management-system` 仓库

4. **Railway 会自动检测:**
   - Python 项目
   - 读取 `Procfile` 和 `runtime.txt`
   - 自动安装依赖

5. **添加环境变量:**
   - 点击项目 → "Variables" 标签
   - 添加以下变量:
     ```
     SECRET_KEY=你生成的随机密钥
     DEBUG=False
     ```

   如果使用 Supabase:
   ```
   SUPABASE_URL=你的Supabase URL
   SUPABASE_KEY=你的Supabase Key
   USE_SUPABASE_STORAGE=true
   DATA_BACKEND=supabase
   ```

6. **等待部署:**
   - 自动构建 (约2-3分钟)
   - 部署完成后会显示 URL

7. **获取域名:**
   - 点击 "Settings" → "Domains"
   - Railway 自动分配域名: `xxx.up.railway.app`
   - 也可以绑定自己的域名

8. **访问应用:**
   ```
   https://your-app.up.railway.app
   ```

**费用:**
- 免费额度: $5/月
- 超出按使用量计费

---

### 选项 2: Render 部署

**优点:** 有免费层、操作简单

**步骤:**

1. **访问 Render** → https://render.com

2. **创建账号并登录**

3. **创建 Web Service:**
   - 点击 "New +" → "Web Service"
   - 连接 GitHub 账号
   - 选择 `invoice-management-system` 仓库

4. **配置:**
   - Name: `invoice-system`
   - Environment: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`

5. **环境变量:**
   - 点击 "Environment" 标签
   - 添加:
     ```
     SECRET_KEY=随机密钥
     DEBUG=False
     ```

6. **选择计划:**
   - Free: 免费但会休眠(15分钟无活动后)
   - Starter: $7/月,不休眠

7. **Create Web Service**

8. **等待部署** (约5分钟)

9. **访问:**
   ```
   https://your-app.onrender.com
   ```

---

### 选项 3: Heroku 部署

**优点:** 成熟稳定、功能完善

**步骤:**

1. **访问 Heroku** → https://heroku.com

2. **创建账号并安装 Heroku CLI**
   - Windows: https://devcenter.heroku.com/articles/heroku-cli
   - Mac: `brew install heroku/brew/heroku`

3. **登录:**
   ```bash
   heroku login
   ```

4. **创建应用:**
   ```bash
   cd invoice_system
   heroku create your-app-name
   ```

5. **添加环境变量:**
   ```bash
   heroku config:set SECRET_KEY=你的密钥
   heroku config:set DEBUG=False

   # 如果使用 Supabase
   heroku config:set SUPABASE_URL=xxx
   heroku config:set SUPABASE_KEY=xxx
   heroku config:set USE_SUPABASE_STORAGE=true
   ```

6. **部署:**
   ```bash
   git push heroku main
   ```

7. **打开应用:**
   ```bash
   heroku open
   ```

**费用:**
- Eco: $7/月 (不休眠)
- Basic: $7/月

---

## 🔐 重要: 环境变量配置

### 必需的环境变量

**所有平台都需要:**
```env
SECRET_KEY=随机64位字符串
DEBUG=False
```

**如果使用 Supabase:**
```env
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=你的anon key
USE_SUPABASE_STORAGE=true
DATA_BACKEND=supabase
SUPABASE_DB_PASSWORD=数据库密码
```

### 生成 SECRET_KEY

**方法 1: Python**
```python
import secrets
print(secrets.token_hex(32))
```

**方法 2: 在线生成**
访问: https://randomkeygen.com/

---

## 📝 后续更新代码

当您修改代码后,更新部署:

```bash
# 查看修改
git status

# 添加修改
git add .

# 提交
git commit -m "描述你的修改"

# 推送到 GitHub
git push origin main
```

**自动部署:**
- Railway/Render: 推送后自动重新部署
- Heroku: 需要 `git push heroku main`

---

## 🔍 常见问题

### Q1: git push 需要密码但密码不对?

**解决:**
GitHub 不再接受密码,需要使用 Personal Access Token:
1. GitHub → Settings → Developer settings → Personal access tokens
2. Generate new token (classic)
3. 权限选择 `repo`
4. 复制 Token
5. 推送时用 Token 替代密码

### Q2: 部署后显示 Application Error?

**检查:**
1. 查看平台的部署日志
2. 检查环境变量是否设置
3. 确认 `Procfile` 和 `requirements.txt` 正确

### Q3: 数据库文件丢失?

**注意:**
- SQLite 文件不应上传到 Git (已在 .gitignore)
- 云平台重启会清空文件
- **推荐使用 Supabase** 作为云数据库

### Q4: 文件上传后消失?

**解决:**
使用 Supabase Storage:
```env
USE_SUPABASE_STORAGE=true
```

---

## 📊 推荐方案对比

| 平台 | 免费层 | 价格 | 自动部署 | 推荐度 |
|-----|-------|------|---------|--------|
| **Railway** | $5/月额度 | 按用量 | ✅ | ⭐⭐⭐⭐⭐ |
| **Render** | 有(会休眠) | $7/月 | ✅ | ⭐⭐⭐⭐ |
| **Heroku** | 无 | $7/月 | ✅ | ⭐⭐⭐⭐ |
| **Vercel** | 有 | 免费-$20 | ✅ | ⭐⭐ (不适合此项目) |

**推荐:**
- 小项目/测试: Railway (免费额度够用)
- 生产环境: Render 或 Heroku (稳定)

---

## 🎯 完整流程总结

```bash
# 1. 进入项目目录
cd invoice_system

# 2. 初始化 Git
git init
git add .
git commit -m "Initial commit"

# 3. 创建 GitHub 仓库(网页操作)
# 访问 https://github.com/new

# 4. 推送到 GitHub
git remote add origin https://github.com/你的用户名/仓库名.git
git branch -M main
git push -u origin main

# 5. 部署到 Railway
# 访问 https://railway.app
# 连接 GitHub 仓库
# 添加环境变量
# 等待部署完成!
```

---

## ✅ 检查清单

部署前确认:
- [ ] `.gitignore` 文件存在
- [ ] `.env` 文件已排除(不会上传)
- [ ] 代码已推送到 GitHub
- [ ] SECRET_KEY 已设置
- [ ] (可选) Supabase 已配置

部署后测试:
- [ ] 应用可访问
- [ ] 可以上传发票
- [ ] 可以编辑/删除
- [ ] PDF 可以查看
- [ ] 搜索功能正常

---

## 🎉 恭喜!

完成这些步骤后,您的应用就会运行在云端,可以通过公网访问了!

**下一步:**
- 绑定自定义域名
- 配置 HTTPS (自动)
- 设置监控和告警
- 定期备份数据

---

**需要帮助?** 随时询问!
