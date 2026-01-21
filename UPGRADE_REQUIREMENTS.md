# 发票管理系统升级需求文档

## 📋 需求概述

本次升级旨在增强发票管理系统的财务管理能力,主要增加两个核心功能:

1. **Credit (信用额度)管理** - 记录公司退款产生的信用额度
2. **Paid Amount (实付金额)管理** - 支持部分付款记录

---

## 🎯 功能需求详细说明

### 1. Credit (信用额度) 功能

#### 业务场景
- 公司有时会因为退货、服务问题等原因给予 refund credit
- 这些 credit 可以在下次付款时抵扣使用
- 需要记录每张发票关联的 credit 金额

#### 功能要求
- **字段名称**: `credit`
- **数据类型**: 浮点数 (Float/Numeric)
- **默认值**: `0.00`
- **可为空**: 否
- **显示位置**: 
  - 发票上传表单(可选填)
  - 发票编辑页面
  - 发票列表展示
- **业务规则**:
  - Credit 金额必须 >= 0
  - Credit 可以在录入发票时填写
  - Credit 可以在编辑发票时修改

#### 用户界面需求
- 在发票上传表单添加 "Credit Amount" 输入框
- 在发票编辑页面显示并允许修改 Credit
- 在发票列表中显示 Credit 金额(如果 > 0)
- 使用货币格式显示(例如: $100.00)

---

### 2. Paid Amount (实付金额) 功能

#### 业务场景
- 并非所有发票都会一次性全额支付
- 有时候客户可能只支付部分金额
- 需要记录实际支付的金额,而不仅仅是"已付/未付"状态

#### 功能要求
- **字段名称**: `paid_amount`
- **数据类型**: 浮点数 (Float/Numeric)
- **默认值**: `0.00`
- **可为空**: 否
- **显示位置**:
  - 付款确认表单
  - 发票编辑页面
  - 发票列表展示
- **业务规则**:
  - Paid Amount 必须 >= 0
  - Paid Amount 不应超过 Total Amount
  - 当 Paid Amount > 0 时,可以标记为部分付款
  - 当 Paid Amount >= Total Amount 时,可以标记为全额付款
  - 支持多次部分付款(累加)

#### 用户界面需求
- 在付款确认表单添加 "Paid Amount" 输入框
- 在发票编辑页面显示已付金额
- 在发票列表显示:
  - 已付金额 / 总金额
  - 剩余应付金额
  - 付款状态标识(未付/部分付款/已付清)
- 使用进度条或百分比显示付款进度

---

## 💾 数据库变更

### 新增字段

在 `invoices` 表中添加以下字段:

| 字段名 | 类型 | 默认值 | 可空 | 说明 |
|--------|------|--------|------|------|
| `credit` | FLOAT/NUMERIC | 0.00 | NO | 信用额度金额 |
| `paid_amount` | FLOAT/NUMERIC | 0.00 | NO | 实际已支付金额 |

### 数据迁移

需要为现有数据添加默认值:
- 所有现有记录的 `credit` 设为 `0.00`
- 所有现有记录的 `paid_amount`:
  - 如果 `payment_status = 'paid'`,设为 `total_amount`
  - 如果 `payment_status = 'unpaid'`,设为 `0.00`

---

## 🔄 付款状态逻辑升级

### 当前逻辑
- `payment_status`: 'paid' 或 'unpaid' (二元状态)

### 新逻辑
基于 `paid_amount` 和 `total_amount` 的关系:

```
if paid_amount == 0:
    status = "未付款" (Unpaid)
elif paid_amount >= total_amount:
    status = "已付清" (Paid in Full)
else:
    status = "部分付款" (Partially Paid)
```

### 剩余应付金额计算

```
remaining_amount = total_amount - paid_amount - credit
```

> **注意**: Credit 可以抵扣应付金额

---

## 🎨 用户界面变更

### 1. 发票上传页面 (`upload.html`)

**新增字段**:
```html
<label>Credit Amount (Optional)</label>
<input type="number" name="credit" step="0.01" min="0" value="0.00">
```

### 2. 发票编辑页面 (`edit.html`)

**新增/修改区域**:
- 显示和编辑 Credit 金额
- 在付款确认区域添加 "Paid Amount" 输入框
- 显示剩余应付金额
- 显示付款进度

**付款确认表单示例**:
```html
<form action="/upload_payment/{{ invoice.id }}" method="POST">
    <label>Payment Date</label>
    <input type="date" name="paymentDate" required>
    
    <label>Paid Amount</label>
    <input type="number" name="paidAmount" step="0.01" min="0" 
           max="{{ invoice.total_amount }}" required>
    
    <label>Payment Proof (Optional)</label>
    <input type="file" name="paymentFile">
    
    <button type="submit">Confirm Payment</button>
</form>
```

### 3. 发票列表页面 (`index.html`)

**新增显示列**:
- Credit 金额
- 已付金额 / 总金额
- 剩余应付
- 付款状态徽章

**示例显示**:
```
Total: $1,000.00
Credit: $100.00
Paid: $500.00
Remaining: $400.00
Status: [部分付款]
```

---

## 🔧 技术实现要点

### 1. 后端变更 (`database.py`)

- 在 `Invoice` 模型添加 `credit` 和 `paid_amount` 字段
- 更新 `_to_dict()` 方法包含新字段
- 在 Supabase 后端的 DDL 中添加新字段

### 2. 路由变更 (`app.py`)

**修改路由**:
- `/upload` - 接收 credit 参数
- `/edit/<invoice_id>` - 显示和编辑 credit
- `/upload_payment/<invoice_id>` - 接收 paidAmount 参数,累加到 paid_amount
- `/mark_unpaid/<invoice_id>` - 重置 paid_amount 为 0

**新增计算逻辑**:
```python
def calculate_payment_status(invoice):
    if invoice['paid_amount'] == 0:
        return 'unpaid'
    elif invoice['paid_amount'] >= invoice['total_amount']:
        return 'paid'
    else:
        return 'partial'

def calculate_remaining(invoice):
    return invoice['total_amount'] - invoice['paid_amount'] - invoice['credit']
```

### 3. 前端变更

- 添加表单验证(Paid Amount 不能超过剩余应付金额)
- 添加实时计算显示(输入 Paid Amount 时显示剩余金额)
- 使用 Bootstrap 徽章显示付款状态

---

## ✅ 验收标准

### 功能验收
- [ ] 可以在创建发票时输入 Credit 金额
- [ ] 可以在编辑发票时修改 Credit 金额
- [ ] 可以在确认付款时输入 Paid Amount
- [ ] 支持多次部分付款,金额正确累加
- [ ] 剩余应付金额计算正确(考虑 Credit)
- [ ] 付款状态正确显示(未付/部分付款/已付清)
- [ ] 发票列表正确显示所有新字段

### 数据验收
- [ ] 新字段在 SQLite 和 Supabase 都正确创建
- [ ] 现有数据迁移成功,无数据丢失
- [ ] 新字段默认值正确

### 界面验收
- [ ] 所有输入框有合适的验证和提示
- [ ] 金额显示格式统一(保留两位小数)
- [ ] 付款状态徽章颜色区分明显
- [ ] 移动端界面适配良好

---

## 📅 实施计划

### 阶段 1: 数据库升级
1. 修改 `database.py` 中的模型定义
2. 创建数据库迁移脚本
3. 测试迁移脚本

### 阶段 2: 后端逻辑
1. 修改 `app.py` 路由处理
2. 添加新的计算逻辑
3. 更新数据验证规则

### 阶段 3: 前端界面
1. 修改 `upload.html` 添加 Credit 输入
2. 修改 `edit.html` 添加付款金额输入
3. 修改 `index.html` 显示新字段
4. 添加 JavaScript 验证和实时计算

### 阶段 4: 测试
1. 单元测试
2. 集成测试
3. 用户验收测试

### 阶段 5: 部署
1. 更新文档
2. 部署到测试环境
3. 部署到生产环境

---

## 🚨 风险与注意事项

1. **数据迁移风险**
   - 需要备份现有数据库
   - 测试迁移脚本的正确性
   - 准备回滚方案

2. **业务逻辑复杂度**
   - Credit 和 Paid Amount 的交互逻辑需要清晰定义
   - 多次部分付款的累加逻辑需要严格测试

3. **向后兼容性**
   - 确保现有功能不受影响
   - 现有的"已付/未付"逻辑需要平滑过渡

4. **用户体验**
   - 新增字段不应让界面过于复杂
   - 需要提供清晰的使用说明

---

## 📝 附加说明

### Credit 使用场景示例

**场景**: 公司退货获得 $100 credit

1. 用户创建新发票,Total Amount = $500
2. 在 Credit 字段填入 $100
3. 实际应付金额 = $500 - $100 = $400
4. 用户支付 $200 (部分付款)
5. 剩余应付 = $400 - $200 = $200

### Paid Amount 使用场景示例

**场景**: 分期付款

1. 发票总额 $1,000
2. 第一次付款 $400 → Paid Amount = $400, Status = "部分付款"
3. 第二次付款 $300 → Paid Amount = $700, Status = "部分付款"
4. 第三次付款 $300 → Paid Amount = $1,000, Status = "已付清"

---

**文档版本**: v1.0  
**创建日期**: 2026-01-20  
**最后更新**: 2026-01-20
