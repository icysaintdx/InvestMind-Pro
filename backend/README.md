# IcySaint AI - Python 后端服务器

## 📋 概述

这是 IcySaint AI 的 Python 后端服务器，使用 FastAPI 框架构建，替代原有的 Vercel Serverless Functions。

## ✨ 功能特性

- ✅ 完整的 API 代理功能
- ✅ 支持所有 AI 模型（Gemini、DeepSeek、Qwen、SiliconFlow）
- ✅ 聚合数据股票 API 代理
- ✅ API Key 集中管理
- ✅ CORS 自动处理
- ✅ 自动重载（开发模式）
- ✅ API 文档（Swagger UI）

## 🚀 快速开始

### Windows 用户

```cmd
cd backend
start.bat
```

### Mac/Linux 用户

```bash
cd backend
chmod +x start.sh
./start.sh
```

### 手动启动

```bash
# 1. 进入后端目录
cd backend

# 2. 创建虚拟环境（首次）
python -m venv venv

# 3. 激活虚拟环境
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# 4. 安装依赖
pip install -r requirements.txt

# 5. 启动服务器
python server.py
```

## 📊 API 端点

### AI 模型端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/ai/gemini` | POST | Google Gemini API |
| `/api/ai/deepseek` | POST | DeepSeek API |
| `/api/ai/qwen` | POST | 通义千问 API |
| `/api/ai/siliconflow` | POST | 硅基流动 API |
| `/api/ai/siliconflow-models` | GET | 获取硅基流动模型列表 |

### 股票数据端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/stock/{symbol}` | POST | 获取股票实时数据 |

### 配置管理端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/config` | GET | 获取配置状态 |
| `/api/config/update` | POST | 更新 API Keys |

### 健康检查

| 端点 | 方法 | 说明 |
|------|------|------|
| `/` | GET | 根路径信息 |
| `/health` | GET | 健康检查 |

## 🔧 配置说明

### 环境变量

在项目根目录的 `.env` 文件中配置：

```bash
# AI 模型 API Keys
GEMINI_API_KEY=your_gemini_key
DEEPSEEK_API_KEY=your_deepseek_key
QWEN_API_KEY=your_qwen_key
SILICONFLOW_API_KEY=your_siliconflow_key

# 股票数据 API
JUHE_API_KEY=your_juhe_key
```

### 服务器配置

默认配置：
- **主机**: 0.0.0.0（所有网络接口）
- **端口**: 8000
- **自动重载**: 启用（开发模式）
- **CORS**: 允许 localhost:3000

## 📚 API 文档

启动服务器后，访问以下地址查看交互式 API 文档：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔍 调试

### 查看日志

服务器运行时会在控制台输出详细日志：

```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 测试端点

使用 curl 测试健康检查：

```bash
curl http://localhost:8000/health
```

应返回：
```json
{"status": "healthy"}
```

### 查看配置状态

```bash
curl http://localhost:8000/api/config
```

应返回各 API Key 的配置状态。

## 🎯 与前端集成

### 1. 启动后端

```bash
cd backend
start.bat  # Windows
# 或
./start.sh  # Mac/Linux
```

### 2. 启动前端

在另一个终端：

```bash
cd ..
npm run dev
```

### 3. 访问应用

- 前端: http://localhost:3000
- 后端 API: http://localhost:8000
- API 文档: http://localhost:8000/docs

## ⚠️ 注意事项

1. **端口冲突**: 确保 8000 端口未被占用
2. **Python 版本**: 需要 Python 3.8+
3. **虚拟环境**: 建议使用虚拟环境避免依赖冲突
4. **API Keys**: 确保 `.env` 文件配置正确

## 🐛 常见问题

### Q: 端口 8000 被占用？

修改 `server.py` 最后的端口号：

```python
uvicorn.run(app, host="0.0.0.0", port=8001)  # 改为其他端口
```

同时更新 `apiConfig.ts`：

```typescript
const PYTHON_BACKEND_URL = 'http://localhost:8001';
```

### Q: CORS 错误？

确保前端运行在 `localhost:3000`，或在 `server.py` 中添加允许的源：

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "你的前端地址"],
    ...
)
```

### Q: API Key 未配置？

检查 `.env` 文件是否在项目根目录，且格式正确：

```bash
GEMINI_API_KEY=sk-xxxxx  # 不要有引号
```

## 📊 性能优化

### 生产环境部署

```bash
# 使用 gunicorn（需要额外安装）
pip install gunicorn
gunicorn server:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### 使用 Docker

创建 `Dockerfile`：

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
```

构建并运行：

```bash
docker build -t IcySaint-backend .
docker run -p 8000:8000 --env-file ../.env IcySaint-backend
```

## 📝 开发说明

### 添加新的 API 端点

1. 在 `server.py` 中添加新的路由：

```python
@app.post("/api/your-endpoint")
async def your_endpoint(request: YourRequestModel):
    # 处理逻辑
    return {"success": True, "data": ...}
```

2. 在 `apiConfig.ts` 中添加端点配置：

```typescript
export const API_ENDPOINTS = {
  // ...
  yourEndpoint: `${getBackendUrl()}/api/your-endpoint`,
};
```

3. 在前端调用：

```typescript
const response = await fetch(API_ENDPOINTS.yourEndpoint, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(data)
});
```

## 📄 许可证

MIT License

---

**开发者**: IcySaint Team  
**更新时间**: 2025-12-02
