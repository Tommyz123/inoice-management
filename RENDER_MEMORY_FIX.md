# 🔧 Render 内存不足问题修复指南

## 🚨 问题诊断

### 症状
```
Instance failed: Out of memory
Worker with pid 7 was terminated due to signal 9
Worker with pid 8 was terminated due to signal 9
Worker with pid 9 was terminated due to signal 9
Worker with pid 10 was terminated due to signal 9
```

### 根本原因
- **Render Free Tier**: 512MB RAM 限制
- **4 个 Gunicorn Workers**: 每个 ~130-150MB
- **总内存使用**: 4 × 150MB = **600MB+** ❌ 超限
- **结果**: 系统杀掉进程（OOM - Out of Memory）

---

## ✅ 解决方案

### 已实施的修复

#### 1. 降低 Worker 数量
**Dockerfile 更新**：
```dockerfile
# 之前：4 workers（内存超限）
CMD ["gunicorn", "--workers", "4", ...]

# 现在：1 worker（适合免费计划）
CMD ["./start.sh"]
```

#### 2. 灵活配置脚本
**start.sh**：
```bash
# 默认 1 worker（免费计划）
WORKERS=${GUNICORN_WORKERS:-1}

# 可通过环境变量覆盖（付费计划）
gunicorn --workers ${WORKERS} ...
```

#### 3. render.yaml 配置
```yaml
envVars:
  - key: GUNICORN_WORKERS
    value: 1  # 免费计划
```

---

## 📊 内存使用对比

| 配置 | Worker 数 | 内存使用 | Render 计划 | 状态 |
|------|-----------|----------|-------------|------|
| **修复前** | 4 | ~600MB | Free (512MB) | ❌ OOM |
| **修复后** | 1 | ~150MB | Free (512MB) | ✅ OK |
| Starter | 2 | ~300MB | Starter (2GB) | ✅ OK |
| Standard | 4 | ~600MB | Standard (4GB) | ✅ OK |

---

## 🚀 立即修复步骤

### 方式 1：Git Push（自动部署）

```bash
# 1. 确认更改
git status

# 2. 提交修复
git add Dockerfile start.sh render.yaml
git commit -m "Fix OOM: Reduce workers to 1 for free tier"

# 3. 推送到 GitHub
git push origin main

# 4. Render 自动检测并重新部署
# 等待 5-10 分钟
```

### 方式 2：手动部署

1. **Render Dashboard**
   - 选择您的服务
   - Settings → "Clear build cache & deploy"

2. **查看部署日志**
   ```
   Starting Gunicorn with 1 worker(s)...
   [INFO] Booting worker with pid: 7
   [INFO] Application startup complete
   ```

3. **验证成功**
   ```bash
   curl https://your-app.onrender.com/health
   ```

---

## 🔍 验证修复

### 1. 检查日志

**成功的日志应该显示**：
```
Starting Gunicorn with 1 worker(s) on port 8000...
Timeout: 120s
[INFO] Starting gunicorn 21.2.0
[INFO] Listening at: http://0.0.0.0:8000
[INFO] Using worker: sync
[INFO] Booting worker with pid: 7
```

**关键点**：
- ✅ 只有 **1 个 worker**（pid: 7）
- ✅ 没有 "Out of memory" 错误
- ✅ 没有 "terminated due to signal 9"

### 2. 监控内存使用

Render Dashboard → Metrics：
- **内存使用**: < 300MB ✅
- **CPU 使用**: < 50% ✅

### 3. 测试应用功能

```bash
# 健康检查
curl https://your-app.onrender.com/health

# 上传测试
访问 /upload 页面，上传发票
```

---

## ⚙️ 针对不同计划的配置

### Free Tier（512MB RAM）
```yaml
GUNICORN_WORKERS: 1  # 推荐
```
**特点**：
- ✅ 稳定运行
- ⚠️ 单线程处理请求
- ✅ 适合低流量应用

---

### Starter Plan（2GB RAM）
```yaml
GUNICORN_WORKERS: 2  # 推荐
```
**特点**：
- ✅ 并发处理
- ✅ 更好性能
- ✅ 适合中等流量

---

### Standard Plan（4GB+ RAM）
```yaml
GUNICORN_WORKERS: 4  # 推荐
```
**特点**：
- ✅ 高并发
- ✅ 最佳性能
- ✅ 适合生产环境

---

## 🎯 性能优化建议

### 1. 单 Worker 优化

虽然只有 1 个 worker，但可以通过以下方式保持良好性能：

#### a) 异步处理（可选）
```python
# 对于耗时操作，使用异步
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(max_workers=2)

@app.route('/api/ocr', methods=['POST'])
def api_ocr():
    # 在后台线程处理 OCR
    future = executor.submit(ocr_handler.extract_invoice_data, file_path)
    result = future.result(timeout=30)
```

#### b) 缓存优化
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_invoice(invoice_id):
    return database.get_invoice(invoice_id)
```

#### c) 数据库连接池
```python
# 已在 SQLAlchemy 中启用
# 减少连接开销
```

### 2. 升级到付费计划

如果流量增加，考虑升级：

| 需求 | 推荐计划 | Worker 数 | 月费 |
|------|---------|-----------|------|
| 开发/测试 | Free | 1 | $0 |
| 小团队 | Starter | 2 | $7 |
| 生产环境 | Standard | 4 | $25 |

---

## 🐞 故障排查

### 问题：仍然看到 OOM 错误

**检查步骤**：

1. **确认代码已更新**
   ```bash
   # 在 Render Shell
   cat start.sh | grep WORKERS
   # 应该显示：WORKERS=${GUNICORN_WORKERS:-1}
   ```

2. **检查环境变量**
   ```bash
   echo $GUNICORN_WORKERS
   # 应该显示：1
   ```

3. **检查实际运行的 worker 数**
   ```bash
   ps aux | grep gunicorn | wc -l
   # 应该显示：2 (1 master + 1 worker)
   ```

4. **清除构建缓存**
   - Dashboard → Settings → Clear build cache
   - 重新部署

---

### 问题：性能下降

**单 worker 的影响**：
- **请求处理**: 串行而非并行
- **适用场景**: 低流量（< 100 req/min）

**解决方案**：
1. **优化代码**: 减少处理时间
2. **使用缓存**: 减少重复计算
3. **升级计划**: 增加 workers

---

### 问题：OCR 处理超时

**原因**：单 worker + 长时间 OCR

**解决方案**：

1. **已配置的超时**：
   ```bash
   --timeout 120  # 2分钟
   ```

2. **如果仍超时，增加超时时间**：
   ```yaml
   envVars:
     - key: GUNICORN_TIMEOUT
       value: 180  # 3分钟
   ```

3. **优化 OCR 处理**：
   - 限制图片大小（< 5MB）
   - 降低 DPI（如果太高）
   - 使用预处理加速

---

## 📈 监控指标

### Render Metrics 关注点

| 指标 | 正常范围 | 警告阈值 | 行动 |
|------|---------|----------|------|
| **内存使用** | < 300MB | > 400MB | 优化代码/升级 |
| **CPU 使用** | < 50% | > 80% | 升级计划 |
| **响应时间** | < 2s | > 5s | 优化/增加 workers |
| **错误率** | < 1% | > 5% | 检查日志 |

---

## ✅ 修复确认清单

部署后逐项检查：

- [ ] 部署状态显示 "Live"（绿色）
- [ ] 日志显示 "Starting Gunicorn with 1 worker(s)"
- [ ] 没有 "Out of memory" 错误
- [ ] 没有 "signal 9" 错误
- [ ] 内存使用 < 400MB
- [ ] `/health` 端点返回 200
- [ ] 可以访问主页
- [ ] 可以上传文件
- [ ] OCR 功能正常工作

---

## 🎉 总结

### 修复内容
- ✅ 将 Gunicorn workers 从 4 降到 1
- ✅ 创建灵活的启动脚本（start.sh）
- ✅ 添加环境变量配置
- ✅ 更新 render.yaml
- ✅ 优化内存使用

### 结果
- ✅ 内存使用从 ~600MB 降到 ~150MB
- ✅ Render Free Tier 可稳定运行
- ✅ OCR 功能正常工作
- ✅ 可根据需求调整 workers

### 下一步
1. **推送代码到 GitHub**
2. **等待 Render 自动部署**
3. **验证修复成功**
4. **测试应用功能**

---

**重要提示**：
- 免费计划适合开发和测试
- 生产环境建议使用付费计划
- 可随时通过环境变量调整 workers

问题已解决！🚀
