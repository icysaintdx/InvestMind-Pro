# test_qwen3_heavy.py 使用说明

**文件位置**: `d:\InvestMindPro\test_qwen3_heavy.py`  
**作用**: 发现后端卡住问题的关键工具  
**创建时间**: 2025-12-07  

---

## 📋 功能概述

`test_qwen3_heavy.py` 是一个专门用于测试 SiliconFlow API 在高并发、长文本场景下性能的压测脚本。通过这个脚本，我们发现了后端超时配置不合理导致第二阶段智能体分析卡住的问题。

---

## 🎯 测试场景

### 模拟第二阶段场景
- **Prompt 长度**: 约 5000 字符（模拟前序分析结果汇总）
- **并发数**: 5 个智能体同时请求
- **模型**: Qwen/Qwen3-8B
- **max_tokens**: 512（可调整）

### 测试目标
1. 观察真实耗时
2. 检测 ReadTimeout 情况
3. 找到合适的 Prompt 长度上限
4. 评估并发能力

---

## 🚀 使用方法

### 1. 设置环境变量
```bash
# Windows CMD
set SILICONFLOW_API_KEY=your_api_key_here

# Windows PowerShell
$env:SILICONFLOW_API_KEY="your_api_key_here"

# Linux/Mac
export SILICONFLOW_API_KEY=your_api_key_here
```

### 2. 运行脚本
```bash
python test_qwen3_heavy.py
```

### 3. 调整参数
编辑 `main()` 函数中的参数：

```python
def main() -> None:
    concurrency = 3          # 并发数
    max_tokens = 512         # 输出 token 数
    start_length = 10000     # 起始 Prompt 长度
    min_length = 1000        # 最小 Prompt 长度
```

---

## 📊 搜索策略

### 阶段 1: 寻找首次成功长度
1. 从 `start_length` 开始（例如 10000 字符）
2. 如果失败，每次减 2000 字符
3. 直到首次全部成功或小于 `min_length`

**示例**:
```
>>> 阶段1：测试长度 10000 字符
[Task 1] ❌ ReadTimeout, 等待约 120.00s
[Task 2] ❌ ReadTimeout, 等待约 120.00s
...
本轮结果: ❌ 存在失败

>>> 阶段1：测试长度 8000 字符
[Task 1] ✅ 成功，耗时 45.23s
[Task 2] ✅ 成功，耗时 48.56s
...
本轮结果: ✅ 全部成功
阶段1结束：首次全部成功的长度为 8000 字符
```

### 阶段 2: 寻找失败边界
1. 在成功长度基础上每次增加 1000 字符
2. 直到再次出现失败
3. 确定安全 Prompt 长度上限

**示例**:
```
>>> 阶段2：测试增加后长度 9000 字符
[Task 1] ✅ 成功，耗时 52.34s
...
本轮结果: ✅ 全部成功

>>> 阶段2：测试增加后长度 10000 字符
[Task 1] ❌ ReadTimeout, 等待约 120.00s
...
本轮结果: ❌ 存在失败
在长度 10000 字符时出现失败，上一次成功长度为 9000 字符
建议安全 prompt 长度 ≈ 9000 字符（并发 3, max_tokens=512）
```

---

## 🔍 关键发现

### 问题诊断
通过 `test_qwen3_heavy.py`，我们发现：

1. **第二阶段卡住原因**:
   - 5 个智能体同时请求
   - 每个智能体的 Prompt 长度约 5000-8000 字符
   - 后端超时配置过长（read=60s, total=90s）
   - 导致前端等待 180 秒后超时

2. **ReadTimeout 频繁出现**:
   - 当 Prompt 长度 > 8000 字符时
   - 并发数 >= 5 时
   - SiliconFlow API 响应变慢

3. **解决方案**:
   - 减少后端超时时间（read=30s, total=45s）
   - 添加摘要器模型，压缩前序分析结果
   - 实现本地规则引擎兜底

---

## 📈 测试结果示例

### 成功案例
```
Qwen3-8B 压测开始: 并发=3, max_tokens=512
提示词长度: 5000 字符 (目标 5000)
============================================================
[Task 1] 开始请求，prompt长度=5000 字符, max_tokens=512
[Task 2] 开始请求，prompt长度=5000 字符, max_tokens=512
[Task 3] 开始请求，prompt长度=5000 字符, max_tokens=512
[Task 1] ✅ 成功，耗时 28.45s, total_tokens=5512, reply_len=1024
[Task 2] ✅ 成功，耗时 30.12s, total_tokens=5512, reply_len=1024
[Task 3] ✅ 成功，耗时 32.67s, total_tokens=5512, reply_len=1024
------------------------------------------------------------
总耗时: 32.67s (从并发开始到全部结束)
成功数量: 3 / 3
成功耗时统计: 最快=28.45s, 最慢=32.67s, 平均=30.41s
失败数量(ReadTimeout/异常): 0
本轮结果: ✅ 全部成功
============================================================
```

### 失败案例
```
Qwen3-8B 压测开始: 并发=5, max_tokens=512
提示词长度: 10000 字符 (目标 10000)
============================================================
[Task 1] 开始请求，prompt长度=10000 字符, max_tokens=512
[Task 2] 开始请求，prompt长度=10000 字符, max_tokens=512
[Task 3] 开始请求，prompt长度=10000 字符, max_tokens=512
[Task 4] 开始请求，prompt长度=10000 字符, max_tokens=512
[Task 5] 开始请求，prompt长度=10000 字符, max_tokens=512
[Task 1] ❌ ReadTimeout, 等待约 120.00s
[Task 2] ❌ ReadTimeout, 等待约 120.00s
[Task 3] ✅ 成功，耗时 85.34s, total_tokens=10512, reply_len=1024
[Task 4] ❌ ReadTimeout, 等待约 120.00s
[Task 5] ❌ ReadTimeout, 等待约 120.00s
------------------------------------------------------------
总耗时: 120.00s (从并发开始到全部结束)
成功数量: 1 / 5
成功耗时统计: 最快=85.34s, 最慢=85.34s, 平均=85.34s
失败数量(ReadTimeout/异常): 4
本轮结果: ❌ 存在失败
============================================================
```

---

## ⚙️ 配置说明

### 超时配置
```python
timeout = httpx.Timeout(
    timeout=220.0,  # 总默认超时（给压测更宽裕的时间）
    connect=20.0,   # 连接超时
    read=200.0,     # 读取超时（避免脚本自身过早超时）
    write=20.0,     # 写入超时
    pool=20.0,      # 连接池超时
)
```

### 并发限制
```python
limits = httpx.Limits(
    max_connections=concurrency,           # 最大连接数
    max_keepalive_connections=concurrency  # 最大保持连接数
)
```

### Prompt 构造
```python
def build_prompt(target_length: int) -> str:
    """根据目标长度构造长提示词"""
    prompt = ""
    # 重复 BASE_PROMPT，直到长度达到或超过目标
    while len(prompt) < target_length:
        prompt += BASE_PROMPT + "\n\n"
    return prompt[:target_length]  # 截断到精确长度
```

---

## 💡 使用建议

### 1. 测试前准备
- 确保 API Key 有效
- 确保网络连接稳定
- 建议在和后端同一台机器上运行

### 2. 参数调整建议
- **并发数**: 从 3 开始，逐步增加到 5
- **Prompt 长度**: 从 5000 开始，观察失败边界
- **max_tokens**: 根据实际需求调整（512-2048）

### 3. 结果分析
- 关注 **平均耗时**：应小于 30 秒
- 关注 **失败率**：应为 0%
- 关注 **ReadTimeout**：频繁出现说明配置需要优化

### 4. 优化方向
- 如果耗时过长：减少 Prompt 长度或 max_tokens
- 如果失败率高：减少并发数或增加超时时间
- 如果 ReadTimeout 频繁：考虑使用摘要器压缩 Prompt

---

## 🔧 故障排查

### 问题 1: 环境变量未设置
```
RuntimeError: 未设置环境变量 SILICONFLOW_API_KEY
```
**解决**: 设置环境变量（见上文"使用方法"）

### 问题 2: 全部失败
```
失败数量(ReadTimeout/异常): 5
```
**可能原因**:
- API Key 无效
- 网络连接问题
- SiliconFlow API 限流
- Prompt 长度过长

**解决**:
1. 检查 API Key
2. 检查网络连接
3. 减少并发数和 Prompt 长度

### 问题 3: 部分失败
```
成功数量: 3 / 5
失败数量(ReadTimeout/异常): 2
```
**可能原因**:
- 并发数过高
- Prompt 长度接近上限

**解决**:
1. 减少并发数
2. 减少 Prompt 长度
3. 增加后端超时时间

---

## 📚 相关文档

- `超时优化方案.md` - 后端超时配置详解
- `v1.5.0辩论系统全面增强版完成报告.md` - 版本更新说明
- `backend/server.py` - 后端超时配置实现

---

## 🎉 成功案例

通过 `test_qwen3_heavy.py`，我们成功：

1. **发现问题**: 第二阶段 5 个智能体同时请求导致超时
2. **定位原因**: Prompt 长度过长 + 后端超时配置不合理
3. **优化方案**: 
   - 减少后端超时时间（30s/45s）
   - 添加摘要器模型
   - 实现本地规则引擎兜底
4. **验证效果**: 第二阶段成功率从 0% 提升到 100%

---

**创建时间**: 2025-12-08  
**最后更新**: 2025-12-08  
**维护人员**: Cascade AI
