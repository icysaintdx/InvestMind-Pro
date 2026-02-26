# 动态API提供商管理系统 - 设计文档

## 1. 背景与目标

当前 InvestMindPro 的 API 提供商（硅基流动、千问、Gemini、DeepSeek、kirocpa 等）全部硬编码在代码中：
- `server.py` 中的 `API_KEYS` 和 `API_ENDPOINTS` 字典
- `backend/services/llm_service.py` 中的 `API_URLS` 和 `DEFAULT_MODELS`
- `backend/services/llm/llm_client.py` 中的 `LLMProvider` 枚举和各 `_init_*` 方法

每次新增一个 API 提供商都需要修改多处代码。本系统的目标是：
1. 提供商配置存储在数据库中，支持运行时动态增删改
2. 自动检测提供商可用模型（通过 `/v1/models` 端点）
3. LLM 请求动态路由到已配置的提供商，失败自动切换

## 2. 系统架构

```
┌─────────────────────────────────────────────────┐
│                   前端设置页面                      │
│         (API提供商管理 / 模型选择 / 连通性测试)       │
└──────────────────────┬──────────────────────────┘
                       │ REST API
┌──────────────────────▼──────────────────────────┐
│          api_provider_api.py (路由层)              │
│   GET/POST/PUT/DELETE /api/api-providers          │
│   POST /api/api-providers/{id}/detect-models      │
│   POST /api/api-providers/{id}/test               │
└──────────────────────┬──────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────┐
│       api_provider_service.py (服务层)             │
│   SQLite CRUD + 模型检测 + 连通性测试               │
└──────────────────────┬──────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────┐
│        dynamic_llm_client.py (动态路由层)           │
│   根据数据库配置动态选择提供商                        │
│   失败自动切换到下一个可用提供商                      │
│   支持 OpenAI兼容 / Anthropic / Google 三种SDK      │
└─────────────────────────────────────────────────┘
```

## 3. 数据库设计

### api_providers 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PRIMARY KEY | 自增主键 |
| name | TEXT NOT NULL | 提供商显示名称（如"硅基流动"、"DeepSeek官方"） |
| base_url | TEXT NOT NULL | API基础URL（如 `https://api.siliconflow.cn/v1`） |
| api_key | TEXT NOT NULL | API密钥 |
| sdk_type | TEXT NOT NULL | SDK类型：`openai` / `anthropic` / `google` |
| models | TEXT DEFAULT '[]' | 可用模型列表（JSON数组） |
| enabled | INTEGER DEFAULT 1 | 是否启用（0/1） |
| priority | INTEGER DEFAULT 0 | 优先级（数字越大越优先，用于故障切换排序） |
| created_at | TEXT | 创建时间 |
| updated_at | TEXT | 更新时间 |

### SDK类型说明

- **openai**: OpenAI 兼容 API。大部分国内提供商都兼容此协议（硅基流动、DeepSeek、kirocpa、Ollama 等）。使用 `openai` Python SDK 的 `AsyncOpenAI(base_url=..., api_key=...)`。
- **anthropic**: Anthropic Claude API。使用 `anthropic` Python SDK。
- **google**: Google Gemini API。使用 `google-generativeai` SDK 或 OpenAI 兼容模式。

## 4. API 设计

### 4.1 提供商 CRUD

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/api-providers` | 列出所有提供商 |
| POST | `/api/api-providers` | 添加新提供商 |
| GET | `/api/api-providers/{id}` | 获取单个提供商详情 |
| PUT | `/api/api-providers/{id}` | 修改提供商配置 |
| DELETE | `/api/api-providers/{id}` | 删除提供商 |

### 4.2 功能端点

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/api-providers/{id}/detect-models` | 调用 `/v1/models` 自动检测可用模型 |
| POST | `/api/api-providers/{id}/test` | 发送简单请求测试连通性 |

### 4.3 请求/响应示例

**POST /api/api-providers**
```json
{
  "name": "硅基流动",
  "base_url": "https://api.siliconflow.cn/v1",
  "api_key": "sk-xxx",
  "sdk_type": "openai",
  "priority": 10
}
```

**POST /api/api-providers/{id}/detect-models 响应**
```json
{
  "success": true,
  "models": ["Qwen/Qwen2.5-7B-Instruct", "deepseek-ai/DeepSeek-V2.5", ...],
  "count": 42
}
```

**POST /api/api-providers/{id}/test 响应**
```json
{
  "success": true,
  "latency_ms": 320,
  "model_used": "Qwen/Qwen2.5-7B-Instruct",
  "message": "连接成功"
}
```

## 5. 动态路由策略

`dynamic_llm_client.py` 的路由逻辑：

1. 从数据库加载所有 `enabled=1` 的提供商，按 `priority` 降序排列
2. 如果调用方指定了 `provider_id`，直接使用该提供商
3. 如果调用方指定了 `model`，查找包含该模型的提供商
4. 否则使用优先级最高的提供商
5. 请求失败时，自动切换到下一个可用提供商（最多尝试3个）

### 缓存策略

- 提供商列表缓存 60 秒，避免每次请求都查数据库
- 模型检测结果直接写入数据库的 `models` 字段

## 6. 文件清单

| 文件 | 说明 |
|------|------|
| `backend/services/api_provider_service.py` | 提供商服务层（SQLite CRUD + 检测 + 测试） |
| `backend/api/api_provider_api.py` | FastAPI 路由层 |
| `backend/services/llm/dynamic_llm_client.py` | 动态 LLM 路由客户端 |
| `API_PROVIDER_FRONTEND_SPEC.md` | 前端界面规格说明 |

## 7. 与现有系统的关系

- **不修改 `server.py`**：新路由文件需要在 `server.py` 中注册（`app.include_router`），但本次不自动修改，需手动添加一行导入。
- **不替换现有 LLM 调用**：`dynamic_llm_client.py` 作为新的可选调用方式，现有的 `llm_client.py` 和 `llm_service.py` 保持不变。
- **渐进式迁移**：未来可逐步将各模块的 LLM 调用切换到动态客户端。

## 8. 注册路由（需手动添加到 server.py）

```python
from backend.api.api_provider_api import router as api_provider_router
app.include_router(api_provider_router)  # 动态API提供商管理
```
