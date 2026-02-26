# API提供商管理 - 前端界面规格说明

## 1. 页面入口

在系统设置页面（或侧边栏）新增「API提供商管理」入口，路由建议：`/settings/api-providers`

## 2. 主列表页

### 布局
- 顶部：标题「API提供商管理」+ 右侧「添加提供商」按钮
- 中部：提供商卡片列表（每个提供商一张卡片）

### 卡片内容
每张卡片显示：
- 提供商名称（如"硅基流动"）
- SDK类型标签（openai / anthropic / google）
- base_url（脱敏显示）
- API Key（脱敏显示，仅显示前4位和后4位）
- 可用模型数量（如"已检测 42 个模型"）
- 启用/禁用开关
- 优先级数字
- 操作按钮：编辑 / 删除 / 检测模型 / 测试连接

### 交互
- 点击「检测模型」→ 调用 `POST /api/api-providers/{id}/detect-models`，loading状态，成功后刷新模型数量
- 点击「测试连接」→ 调用 `POST /api/api-providers/{id}/test`，显示延迟和结果（绿色成功/红色失败）
- 启用/禁用开关 → 调用 `PUT /api/api-providers/{id}` 更新 enabled 字段
- 删除需二次确认

## 3. 添加/编辑弹窗

### 表单字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| 名称 | 文本输入 | 是 | 提供商显示名称 |
| API基础URL | 文本输入 | 是 | 如 `https://api.siliconflow.cn/v1` |
| API Key | 密码输入 | 是 | 支持显示/隐藏切换 |
| SDK类型 | 下拉选择 | 是 | openai（默认）/ anthropic / google |
| 优先级 | 数字输入 | 否 | 默认0，数字越大越优先 |
| 启用 | 开关 | 否 | 默认启用 |

### 预设模板（可选）
提供快捷填充按钮，点击自动填入常用提供商的 base_url 和 sdk_type：
- 硅基流动：`https://api.siliconflow.cn/v1` / openai
- DeepSeek：`https://api.deepseek.com/v1` / openai
- 通义千问：`https://dashscope.aliyuncs.com/compatible-mode/v1` / openai
- Google Gemini：`https://generativelanguage.googleapis.com` / google
- Ollama本地：`http://localhost:11434` / openai
- 自定义中转：空 / openai

### 保存后自动操作
保存成功后，自动触发「检测模型」，获取可用模型列表。

## 4. 模型详情展开

点击卡片上的模型数量，展开显示完整模型列表：
- 模型ID列表（如 `Qwen/Qwen2.5-7B-Instruct`）
- 支持搜索过滤
- 「刷新模型列表」按钮

## 5. API 端点汇总

| 操作 | 方法 | 端点 |
|------|------|------|
| 列出所有 | GET | `/api/api-providers` |
| 添加 | POST | `/api/api-providers` |
| 获取详情 | GET | `/api/api-providers/{id}` |
| 修改 | PUT | `/api/api-providers/{id}` |
| 删除 | DELETE | `/api/api-providers/{id}` |
| 检测模型 | POST | `/api/api-providers/{id}/detect-models` |
| 测试连接 | POST | `/api/api-providers/{id}/test` |

## 6. 响应格式

所有接口返回统一格式：
```json
{
  "success": true,
  "provider": { ... },   // 单个操作
  "providers": [ ... ],  // 列表操作
  "count": 5
}
```

## 7. 错误处理

- 网络错误 → 显示 toast 提示"网络连接失败"
- 400 → 显示后端返回的 detail 信息
- 404 → 提示"提供商不存在"
- 500 → 提示"服务器内部错误"
