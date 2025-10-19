# 🚀 快速部署指南

选择最适合您的部署方式,5分钟内完成部署!

---

## 🎯 推荐方案对比

| 方案 | 难度 | 时间 | 成本 | 适用场景 |
|-----|------|------|------|----------|
| **本地部署** | ⭐ | 5分钟 | 免费 | 个人使用/测试 |
| **Docker** | ⭐⭐ | 10分钟 | 免费 | 团队内网 |
| **Railway** | ⭐ | 5分钟 | $5/月起 | 小型项目 |
| **Heroku** | ⭐⭐ | 15分钟 | $7/月起 | 中型项目 |
| **VPS** | ⭐⭐⭐ | 30分钟 | $5/月起 | 完全控制 |

---

## 方案 1: 本地/局域网部署 (最简单)

### 适用于:
- ✅ 公司内网使用
- ✅ 个人电脑运行
- ✅ 局域网多人访问

### 步骤:

```bash
# 1. 进入项目目录
cd invoice_system

# 2. 安装生产服务器
pip install waitress

# 3. 启动服务
waitress-serve --host=0.0.0.0 --port=8000 app:app
```

### 访问:
- 本机: `http://localhost:8000`
- 局域网: `http://你的IP:8000`

### 查看IP地址:
```bash
# Windows
ipconfig

# Linux/Mac
ifconfig
```

---

## 方案 2: Docker 部署 (推荐!)

### 适用于:
- ✅ 跨平台部署
- ✅ 易于迁移
- ✅ 生产环境

### 前提条件:
安装 Docker Desktop: https://www.docker.com/products/docker-desktop

### 步骤:

```bash
# 1. 进入项目目录
cd invoice_system

# 2. 启动服务 (一键部署!)
docker-compose up -d

# 3. 查看日志
docker-compose logs -f

# 4. 停止服务
docker-compose down
```

### 访问:
`http://localhost:8000`

---

## 方案 3: Railway 部署 (最快速)

### 适用于:
- ✅ 公网访问
- ✅ 自动 HTTPS
- ✅ 零配置

### 步骤:

1. **访问 Railway**: https://railway.app
2. **登录** (使用 GitHub 账号)
3. **创建新项目**:
   - 点击 "New Project"
   - 选择 "Deploy from GitHub repo"
   - 选择您的项目仓库
4. **设置环境变量**:
   ```
   SECRET_KEY=随机字符串
   SUPABASE_URL=您的Supabase URL
   SUPABASE_KEY=您的Supabase Key
   ```
5. **等待部署完成** (约2分钟)
6. **获取域名** - Railway 自动分配域名

### 费用:
- 免费额度: $5/月
- 超出按使用量计费

---

## 方案 4: Render 部署

### 适用于:
- ✅ 免费试用
- ✅ 简单易用
- ✅ 自动 SSL

### 步骤:

1. **访问 Render**: https://render.com
2. **创建账号并登录**
3. **创建 Web Service**:
   - 点击 "New +"
   - 选择 "Web Service"
   - 连接 GitHub 仓库
4. **配置**:
   - **Name**: invoice-system
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
5. **添加环境变量**
6. **Create Web Service**

### 费用:
- 免费层: 可用,但服务会休眠
- 付费层: $7/月起

---

## 方案 5: VPS 部署 (完全控制)

### 推荐 VPS 提供商:
- **DigitalOcean**: $6/月
- **Vultr**: $5/月
- **阿里云**: ¥30/月
- **腾讯云**: ¥30/月

### 快速步骤:

```bash
# 1. SSH 连接到服务器
ssh root@your-server-ip

# 2. 安装 Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# 3. 克隆项目
git clone your-repo-url
cd invoice_system

# 4. 配置环境变量
nano .env
# 填入配置后保存 (Ctrl+X, Y, Enter)

# 5. 启动服务
docker-compose up -d

# 6. 配置防火墙
ufw allow 80
ufw allow 443
ufw enable
```

---

## 🔐 环境变量配置

无论选择哪种方式,都需要配置这些环境变量:

### 必需配置:
```env
SECRET_KEY=your-secret-random-string-here
```

### 可选配置 (如果使用 Supabase):
```env
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=your-anon-key
USE_SUPABASE_STORAGE=true
DATA_BACKEND=supabase
```

### 生成 SECRET_KEY:
```python
import secrets
print(secrets.token_hex(32))
```

---

## 📊 部署检查清单

部署完成后,检查以下项目:

- [ ] 应用可以正常访问
- [ ] 可以上传发票
- [ ] 可以编辑发票
- [ ] 可以删除发票
- [ ] PDF 文件可以查看
- [ ] 搜索功能正常
- [ ] 如果使用 Supabase,文件上传到云端成功

---

## 🐛 常见问题

### 问题 1: 应用无法启动

**检查:**
```bash
# 查看日志
docker-compose logs

# 或
python app.py
```

**解决:**
- 检查端口是否被占用
- 检查 Python 版本 (需要 3.8+)
- 检查依赖是否安装完整

### 问题 2: 文件上传失败

**检查:**
- uploads 目录是否存在且有写权限
- 文件大小是否超过限制 (默认 10MB)
- Supabase Storage 是否配置正确

**解决:**
```bash
chmod 755 uploads
```

### 问题 3: 数据库连接失败

**检查:**
- .env 文件配置是否正确
- Supabase 凭据是否有效
- 网络连接是否正常

---

## 🎓 推荐学习路径

### 新手入门:
1. 先本地部署测试
2. 熟悉功能后使用 Railway/Render
3. 需要自定义时考虑 VPS

### 进阶用户:
1. 使用 Docker 本地测试
2. 部署到 VPS
3. 配置 Nginx + SSL
4. 设置自动备份

---

## 📞 需要帮助?

如果遇到问题:

1. **查看完整文档**: [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
2. **检查日志**: 日志通常会显示错误原因
3. **环境变量**: 确保所有必需的环境变量都已设置

---

## 🎉 部署成功后

建议完成以下配置:

1. **配置 HTTPS** (如果是公网访问)
2. **设置定期备份**
3. **配置监控告警**
4. **准备用户手册**
5. **性能测试**

---

**祝部署顺利!** 🚀
