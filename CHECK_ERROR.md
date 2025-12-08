# 🔍 检查SiliconFlow错误

**时间**: 2025-12-06 03:37

---

## 🎯 目标

查看SiliconFlow API返回的具体错误信息

---

## ✅ 已修改

在 `backend/server.py` 第490-494行添加了详细日志：

```python
if response.status_code != 200:
    error_text = response.text
    print(f"[SiliconFlow] HTTP {response.status_code} 错误")
    print(f"[SiliconFlow] 响应内容: {error_text[:500]}")
    raise HTTPException(...)
```

---

## 🧪 测试步骤

### 1. 重启后端

```bash
# 停止当前后端 Ctrl+C
# 重新启动
python backend\server.py
```

### 2. 运行测试

```bash
python test_one_request.py
```

### 3. 查看后端日志

应该能看到类似这样的输出：

```
[SiliconFlow] HTTP 400 错误
[SiliconFlow] 响应内容: {"error": {"message": "...", "type": "...", "code": "..."}}
```

---

## 💡 可能的错误原因

### 1. API Key问题
```
"error": "Invalid API key"
```

### 2. 请求格式问题
```
"error": "Invalid request format"
```

### 3. Token超限
```
"error": "Token limit exceeded"
```

### 4. 模型不存在
```
"error": "Model not found"
```

---

**重启后端，运行测试，查看具体错误！** 🔍
