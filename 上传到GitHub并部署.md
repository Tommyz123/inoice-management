# 🚀 上传到 GitHub 并部署 - 最简版本

## 两种方式选择:

### 方式 1: 不需要 GitHub (本地/内网部署)
如果只是**公司内网使用**或**个人电脑运行**,不需要 GitHub!

**直接运行:**
```bash
双击: start_production.bat
```
访问: http://localhost:8000

局域网访问: http://你的IP:8000

---

### 方式 2: 需要 GitHub (公网部署)
如果想要**公网访问**(从任何地方访问),需要先上传到 GitHub。

---

## ✅ 快速步骤 (5分钟)

### 第一步: 准备 Git

**检查 Git 是否安装:**
```bash
git --version
```

**如果没有安装:**
Windows: https://git-scm.com/download/win (下载安装)

**首次配置 Git:**
```bash
git config --global user.name "你的名字"
git config --global user.email "your-email@example.com"
```

---

### 第二步: 上传到 GitHub

#### A. 使用自动化脚本 (推荐)

```bash
# Windows: 双击运行
setup_git.bat

# 按照屏幕提示操作
```

#### B. 手动命令

```bash
# 1. 进入项目目录
cd invoice_system

# 2. 初始化 Git
git init

# 3. 添加所有文件
git add .

# 4. 提交
git commit -m "Initial commit"

# 5. 创建 GitHub 仓库
# 访问: https://github.com/new
# 创建名为 invoice-management-system 的仓库
# 不要勾选 "Initialize with README"

# 6. 连接并推送 (替换成你的仓库地址)
git remote add origin https://github.com/你的用户名/invoice-management-system.git
git branch -M main
git push -u origin main
```

**登录问题?**
- GitHub 现在需要 Personal Access Token,不是密码
- 创建 Token: https://github.com/settings/tokens
- 权限选择: repo (全选)
- 复制 Token 并保存

---

### 第三步: 部署到云平台

#### 推荐: Railway (最简单)

1. **访问 Railway**
   ```
   https://railway.app
   ```

2. **登录** (使用 GitHub 账号)

3. **新建项目**
   - 点击 "New Project"
   - 选择 "Deploy from GitHub repo"
   - 选择你的仓库

4. **添加环境变量**
   点击项目 → Variables → 添加:
   ```
   SECRET_KEY=随机字符串(至少32位)
   DEBUG=False
   ```

   **生成 SECRET_KEY:**
   ```python
   import secrets
   print(secrets.token_hex(32))
   ```

5. **等待部署** (约2分钟)

6. **获取域名**
   - Settings → Domains
   - Railway 自动分配: xxx.up.railway.app

7. **访问你的应用!**
   ```
   https://your-app.up.railway.app
   ```

**费用:** 免费额度 $5/月 (小项目够用)

---

## 🎯 完整流程图

```
本地代码
   ↓
运行 setup_git.bat (或手动 git 命令)
   ↓
在 GitHub 创建仓库
   ↓
git push 推送代码
   ↓
登录 Railway
   ↓
连接 GitHub 仓库
   ↓
添加环境变量
   ↓
自动部署完成!
   ↓
获得公网域名,随时访问
```

---

## 🔐 环境变量说明

### 最小配置 (必需)
```env
SECRET_KEY=64位随机字符串
DEBUG=False
```

### 使用 Supabase (可选,推荐)
```env
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=你的anon-key
USE_SUPABASE_STORAGE=true
DATA_BACKEND=supabase
```

**为什么推荐 Supabase?**
- 云平台会重启,SQLite 数据会丢失
- Supabase 提供云数据库和文件存储
- 免费额度: 500MB 数据库 + 1GB 存储

---

## 📱 其他部署选择

### Render (有免费层)
1. https://render.com
2. New → Web Service
3. 连接 GitHub 仓库
4. Build: `pip install -r requirements.txt`
5. Start: `gunicorn app:app`
6. 添加环境变量
7. Create Web Service

**费用:** 免费层会休眠,付费 $7/月

### Heroku (成熟稳定)
```bash
# 安装 Heroku CLI
# 然后运行:
heroku login
heroku create
git push heroku main
```

**费用:** $7/月起

---

## 🐛 常见问题

### Q: git push 要密码但密码不对?
**A:** GitHub 需要 Personal Access Token:
1. https://github.com/settings/tokens
2. Generate new token
3. 复制 Token
4. 用 Token 代替密码

### Q: 部署后打不开?
**A:** 检查:
1. 部署日志有无错误
2. 环境变量是否设置
3. SECRET_KEY 是否配置

### Q: 数据会丢失吗?
**A:**
- SQLite: 云平台重启会丢失
- **解决**: 使用 Supabase (推荐)

### Q: 文件上传后消失?
**A:** 设置环境变量:
```
USE_SUPABASE_STORAGE=true
```

---

## 📚 详细文档

- **完整 GitHub 指南**: [GITHUB_DEPLOY_GUIDE.md](GITHUB_DEPLOY_GUIDE.md)
- **所有部署方式**: [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- **快速部署**: [QUICK_DEPLOY.md](QUICK_DEPLOY.md)

---

## ✅ 检查清单

**上传前:**
- [ ] Git 已安装
- [ ] GitHub 账号已注册
- [ ] 代码已提交到本地 Git

**上传后:**
- [ ] 代码在 GitHub 可见
- [ ] .env 文件未上传 (检查)
- [ ] *.db 文件未上传 (检查)

**部署后:**
- [ ] 应用可访问
- [ ] 功能正常工作
- [ ] 环境变量已设置

---

## 🎉 成功后

您的应用现在可以:
- ✅ 从任何地方访问
- ✅ 自动 HTTPS 加密
- ✅ 代码更新自动部署
- ✅ 团队协作使用

**享受您的云端发票管理系统!** 🚀

---

**还有问题?** 查看详细文档或随时询问!
