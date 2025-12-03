"""
IcySaint AI - Python 后端服务器
使用 FastAPI 框架替代 Vercel Serverless Functions
"""

import os
import json
import asyncio
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import httpx
from dotenv import load_dotenv
import uvicorn

# 加载环境变量 - 明确指定.env文件路径
import sys
from pathlib import Path
env_file = Path(__file__).parent.parent / '.env'
if env_file.exists():
    load_dotenv(env_file)
    print(f"✅ 加载环境变量文件: {env_file}")
else:
    load_dotenv()  # 尝试默认加载
    print("⚠️ 使用默认环境变量加载")

# 导入API路由
from backend.api.news_api import router as news_router
from backend.api.debate_api import router as debate_router
from backend.api.trading_api import router as trading_router
from backend.api.verification_api import router as verification_router

# ==================== 配置 ====================

# API Keys 从环境变量读取
API_KEYS = {
    "gemini": os.getenv("GEMINI_API_KEY", ""),
    "deepseek": os.getenv("DEEPSEEK_API_KEY", ""),
    "qwen": os.getenv("DASHSCOPE_API_KEY", "") or os.getenv("QWEN_API_KEY", ""),  # 支持两种环境变量名
    "siliconflow": os.getenv("SILICONFLOW_API_KEY", ""),
    "juhe": os.getenv("JUHE_API_KEY", "")
}

# API 端点
API_ENDPOINTS = {
    "gemini": "https://generativelanguage.googleapis.com/v1beta/models",
    "deepseek": "https://api.deepseek.com/chat/completions",
    "qwen": "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
    "siliconflow": "https://api.siliconflow.cn/v1/chat/completions",
    "siliconflow_models": "https://api.siliconflow.cn/v1/models",
    "juhe": "http://web.juhe.cn/finance/stock/hs"
}

# ==================== HTTP连接池 ====================
# 全局HTTP客户端连接池，避免重复创建连接
http_clients = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化连接池
    global http_clients
    
    # 通用连接限制配置
    limits = httpx.Limits(
        max_keepalive_connections=20,  # 保持活动连接数
        max_connections=50,            # 最大连接数
        keepalive_expiry=30            # 连接保持时间（秒）
    )
    
    # AI API的超时配置（需要长时间）
    # 注意：httpx不支持total参数，使用timeout参数代替
    ai_timeout = httpx.Timeout(
        connect=5.0,      # 连接超时：建立TCP连接的时间
        read=180.0,       # 读取超时：3分钟，适应AI长响应
        write=10.0,       # 写入超时：发送请求的时间
        pool=5.0          # 连接池超时：获取连接的等待时间
    )
    
    # 普通API的超时配置（股票数据等）
    normal_timeout = httpx.Timeout(
        connect=5.0,      
        read=30.0,        # 普通API 30秒足够
        write=10.0,       
        pool=5.0         
    )
    
    # 为每个API服务创建专用客户端
    http_clients['gemini'] = httpx.AsyncClient(
        limits=limits,
        timeout=ai_timeout,  # AI API使用长超时
        verify=True
    )
    
    http_clients['deepseek'] = httpx.AsyncClient(
        limits=limits,
        timeout=ai_timeout,  # AI API使用长超时
        verify=True
    )
    
    http_clients['qwen'] = httpx.AsyncClient(
        limits=limits,
        timeout=ai_timeout,  # AI API使用长超时
        verify=True
    )
    
    http_clients['siliconflow'] = httpx.AsyncClient(
        limits=limits,
        timeout=ai_timeout,  # AI API使用长超时
        verify=True
    )
    
    # 股票API专用客户端（使用普通超时）
    http_clients['juhe'] = httpx.AsyncClient(
        limits=limits,
        timeout=normal_timeout,  # 股票API使用短超时
        verify=True
    )
    
    # 通用客户端（用于其他请求）
    http_clients['default'] = httpx.AsyncClient(
        limits=limits,
        timeout=ai_timeout,  # 默认使用AI超时配置
        verify=True
    )
    
    print("✅ HTTP连接池初始化成功")
    
    # yield 控制权给应用
    yield
    
    # 关闭时清理连接池
    for name, client in http_clients.items():
        await client.aclose()
        print(f"✅ 关闭 {name} 连接池")
    
    http_clients.clear()
    print("✅ 所有HTTP连接池已关闭")

# 创建 FastAPI 应用（使用新的lifespan）
app = FastAPI(
    title="IcySaint AI Backend",
    version="1.0.0",
    lifespan=lifespan
)

# 注册API路由
app.include_router(news_router)
app.include_router(debate_router)
app.include_router(trading_router)
app.include_router(verification_router)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有源，包括Vue开发服务器
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== 数据模型 ====================

class GeminiRequest(BaseModel):
    model: str = "gemini-2.5-flash"
    prompt: str
    temperature: float = 0.7
    tools: Optional[List[Dict]] = None
    apiKey: Optional[str] = None

class DeepSeekRequest(BaseModel):
    model: str = "deepseek-chat"
    systemPrompt: str
    prompt: str
    temperature: float = 0.7
    apiKey: Optional[str] = None

class QwenRequest(BaseModel):
    model: str = "qwen-plus"
    systemPrompt: str
    prompt: str
    temperature: float = 0.7
    apiKey: Optional[str] = None

class SiliconFlowRequest(BaseModel):
    model: str = "Qwen/Qwen2.5-7B-Instruct"
    systemPrompt: str
    prompt: str
    temperature: float = 0.7
    apiKey: Optional[str] = None

class StockRequest(BaseModel):
    symbol: str
    apiKey: Optional[str] = None

class AnalyzeRequest(BaseModel):
    agent_id: str
    stock_code: str
    stock_data: Optional[Dict[str, Any]] = {}
    previous_outputs: Optional[Dict[str, Any]] = {}

# ==================== AI API 端点 ====================

@app.post("/api/ai/gemini")
async def gemini_api(request: GeminiRequest):
    """Google Gemini API 代理"""
    try:
        api_key = request.apiKey or API_KEYS["gemini"]
        if not api_key:
            raise HTTPException(status_code=500, detail="未配置 Gemini API Key")
        
        # 使用全局连接池客户端
        client = http_clients.get('gemini', http_clients['default'])
        
        # 简化的实现，实际需要按照 Google API 格式
        headers = {"x-api-key": api_key}
        data = {
            "contents": [{"parts": [{"text": request.prompt}]}],
            "generationConfig": {"temperature": request.temperature}
        }
        
        response = await client.post(
            f"{API_ENDPOINTS['gemini']}/{request.model}:generateContent",
            headers=headers,
            json=data
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Gemini API 错误")
        
        result = response.json()
        text = result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        
        return {"success": True, "text": text}
    
    except HTTPException as e:
        import traceback
        error_detail = f"HTTP {e.status_code}: {e.detail}"
        print(f"[Gemini] HTTP错误: {error_detail}")
        print(traceback.format_exc())
        return {"success": False, "error": error_detail}
    except Exception as e:
        import traceback
        error_msg = f"{type(e).__name__}: {str(e)}"
        print(f"[Gemini] 错误: {error_msg}")
        print(f"[Gemini] 详细信息:")
        print(traceback.format_exc())
        return {"success": False, "error": error_msg}

@app.post("/api/ai/deepseek")
async def deepseek_api(request: DeepSeekRequest):
    """DeepSeek API 代理"""
    try:
        api_key = request.apiKey or API_KEYS["deepseek"]
        if not api_key:
            raise HTTPException(status_code=500, detail="未配置 DeepSeek API Key")
        
        # 使用全局连接池客户端
        client = http_clients.get('deepseek', http_clients['default'])
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        data = {
            "model": request.model,
            "messages": [
                {"role": "system", "content": request.systemPrompt},
                {"role": "user", "content": request.prompt}
            ],
            "temperature": request.temperature,
            "stream": False
        }
        
        # 重试机制
        max_retries = 2
        for attempt in range(max_retries):
            try:
                response = await client.post(
                    API_ENDPOINTS["deepseek"],
                    headers=headers,
                    json=data,
                    timeout=httpx.Timeout(180.0, connect=60.0)
                )
                break
            except httpx.ReadTimeout:
                if attempt < max_retries - 1:
                    print(f"[DeepSeek] 超时，正在重试... (尝试 {attempt + 2}/{max_retries})")
                    await asyncio.sleep(2)
                else:
                    print(f"[DeepSeek] 所有重试都失败")
                    raise
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="DeepSeek API 错误")
        
        result = response.json()
        text = result.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        return {"success": True, "text": text}
    
    except HTTPException as e:
        import traceback
        error_detail = f"HTTP {e.status_code}: {e.detail}"
        print(f"[DeepSeek] HTTP错误: {error_detail}")
        print(traceback.format_exc())
        return {"success": False, "error": error_detail}
    except Exception as e:
        import traceback
        error_msg = f"{type(e).__name__}: {str(e)}"
        print(f"[DeepSeek] 错误: {error_msg}")
        print(f"[DeepSeek] 详细信息:")
        print(traceback.format_exc())
        return {"success": False, "error": error_msg}

@app.post("/api/ai/qwen")
async def qwen_api(request: QwenRequest):
    """通义千问 API 代理"""
    try:
        api_key = request.apiKey or API_KEYS["qwen"]
        if not api_key:
            raise HTTPException(status_code=500, detail="未配置 Qwen API Key")
        
        # 使用全局连接池客户端
        client = http_clients.get('qwen', http_clients['default'])
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        data = {
            "model": request.model,
            "messages": [
                {"role": "system", "content": request.systemPrompt},
                {"role": "user", "content": request.prompt}
            ],
            "temperature": request.temperature,
            "stream": False
        }
        
        # 重试机制
        max_retries = 2
        for attempt in range(max_retries):
            try:
                response = await client.post(
                    API_ENDPOINTS["qwen"],
                    headers=headers,
                    json=data,
                    timeout=httpx.Timeout(180.0, connect=60.0)
                )
                break
            except httpx.ReadTimeout:
                if attempt < max_retries - 1:
                    print(f"[Qwen] 超时，正在重试... (尝试 {attempt + 2}/{max_retries})")
                    await asyncio.sleep(2)
                else:
                    print(f"[Qwen] 所有重试都失败")
                    raise
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Qwen API 错误")
        
        result = response.json()
        text = result.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        return {"success": True, "text": text}
    
    except HTTPException as e:
        import traceback
        error_detail = f"HTTP {e.status_code}: {e.detail}"
        print(f"[Qwen] HTTP错误: {error_detail}")
        print(traceback.format_exc())
        return {"success": False, "error": error_detail}
    except Exception as e:
        import traceback
        error_msg = f"{type(e).__name__}: {str(e)}"
        print(f"[Qwen] 错误: {error_msg}")
        print(f"[Qwen] 详细信息:")
        print(traceback.format_exc())
        return {"success": False, "error": error_msg}

@app.post("/api/ai/siliconflow")
async def siliconflow_api(request: SiliconFlowRequest):
    """硅基流动 API 代理"""
    try:
        api_key = request.apiKey or API_KEYS["siliconflow"]
        if not api_key:
            raise HTTPException(status_code=500, detail="未配置 SiliconFlow API Key")
        
        # 使用全局连接池客户端
        client = http_clients.get('siliconflow', http_clients['default'])
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        data = {
            "model": request.model,
            "messages": [
                {"role": "system", "content": request.systemPrompt},
                {"role": "user", "content": request.prompt}
            ],
            "temperature": request.temperature,
            "max_tokens": 99999999,
            "stream": False
        }
        
        # 增加超时时间并添加重试机制
        max_retries = 2
        for attempt in range(max_retries):
            try:
                response = await client.post(
                    API_ENDPOINTS["siliconflow"],
                    headers=headers,
                    json=data,
                    timeout=httpx.Timeout(180.0, connect=60.0)  # 3分钟超时，60秒连接超时
                )
                break  # 成功则跳出循环
            except httpx.ReadTimeout:
                if attempt < max_retries - 1:
                    print(f"[SiliconFlow] 超时，正在重试... (尝试 {attempt + 2}/{max_retries})")
                    await asyncio.sleep(2)  # 等待2秒后重试
                else:
                    print(f"[SiliconFlow] 所有重试都失败")
                    raise
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="SiliconFlow API 错误")
        
        result = response.json()
        text = result.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        # 获取token使用信息
        usage = result.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        total_tokens = usage.get("total_tokens", 0)
        
        print(f"[SiliconFlow] Token使用: {total_tokens} (输入: {prompt_tokens}, 输出: {completion_tokens})")
        
        return {
            "success": True, 
            "text": text,
            "usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens
            }
        }
    
    except HTTPException as e:
        import traceback
        error_detail = f"HTTP {e.status_code}: {e.detail}"
        print(f"[SiliconFlow] HTTP错误: {error_detail}")
        print(traceback.format_exc())
        return {"success": False, "error": error_detail}
    except Exception as e:
        import traceback
        error_msg = f"{type(e).__name__}: {str(e)}"
        print(f"[SiliconFlow] 错误: {error_msg}")
        print(f"[SiliconFlow] 详细信息:")
        print(traceback.format_exc())
        return {"success": False, "error": error_msg}

@app.get("/api/models")
async def get_all_models():
    """获取所有可用模型的综合列表"""
    all_models = []
    
    # 1. 获取硅基流动模型
    if API_KEYS.get("siliconflow"):
        try:
            # 使用全局连接池客户端
            client = http_clients.get('siliconflow', http_clients['default'])
            headers = {"Authorization": f"Bearer {API_KEYS['siliconflow']}"}
            response = await client.get(
                API_ENDPOINTS["siliconflow_models"],
                headers=headers
            )
            
            if response.status_code == 200:
                result = response.json()
                for model in result.get("data", []):
                    model_id = model.get("id", "")
                    # 解析provider
                    provider = "UNKNOWN"
                    if "qwen" in model_id.lower():
                        provider = "QWEN"
                    elif "llama" in model_id.lower():
                        provider = "LLAMA"
                    elif "deepseek" in model_id.lower():
                        provider = "DEEPSEEK"
                    elif "mistral" in model_id.lower():
                        provider = "MISTRAL"
                    elif "yi-" in model_id.lower() or "/yi" in model_id.lower():
                        provider = "YI"
                    elif "glm" in model_id.lower() or "chatglm" in model_id.lower():
                        provider = "GLM"
                    elif "gemma" in model_id.lower():
                        provider = "GEMMA"
                    elif "baichuan" in model_id.lower():
                        provider = "BAICHUAN"
                    elif "internlm" in model_id.lower():
                        provider = "INTERNLM"
                    elif "phi" in model_id.lower():
                        provider = "PHI"
                    elif model.get("owned_by") == "siliconflow":
                        provider = model_id.split("/")[0].upper() if "/" in model_id else "OTHER"
                    
                    # 判断模型类型
                    model_type = "llm"  # 默认为LLM
                    if any(keyword in model_id.lower() for keyword in ["stable-diffusion", "sdxl", "flux", "playground", "dall-e", "midjourney"]):
                        model_type = "vision"
                    elif any(keyword in model_id.lower() for keyword in ["embedding", "bge", "jina-embed", "text-embedding"]):
                        model_type = "embedding"
                    elif any(keyword in model_id.lower() for keyword in ["whisper", "speech", "audio", "voice", "bark"]):
                        model_type = "audio"
                    
                    all_models.append({
                        "provider": provider,
                        "name": model_id,
                        "label": model_id.split("/")[-1] if "/" in model_id else model_id,
                        "type": model_type,
                        "channel": "硅基流动"
                    })
        except Exception as e:
            print(f"[Models] 获取硅基流动模型失败: {str(e)}")
    
    # 2. 添加通义千问模型
    if API_KEYS.get("qwen"):
        qwen_models = [
            {"provider": "QWEN", "name": "qwen-max", "label": "通义千问 Max", "type": "llm", "channel": "阿里云"},
            {"provider": "QWEN", "name": "qwen-max-longcontext", "label": "通义千问 Max 长文本", "type": "llm", "channel": "阿里云"},
            {"provider": "QWEN", "name": "qwen-plus", "label": "通义千问 Plus", "type": "llm", "channel": "阿里云"},
            {"provider": "QWEN", "name": "qwen-turbo", "label": "通义千问 Turbo", "type": "llm", "channel": "阿里云"},
            {"provider": "QWEN", "name": "qwen-turbo-latest", "label": "通义千问 Turbo 最新", "type": "llm", "channel": "阿里云"},
            {"provider": "QWEN", "name": "qwen2.5-72b-instruct", "label": "Qwen2.5 72B", "type": "llm", "channel": "阿里云"},
            {"provider": "QWEN", "name": "qwen2.5-32b-instruct", "label": "Qwen2.5 32B", "type": "llm", "channel": "阿里云"},
            {"provider": "QWEN", "name": "qwen2.5-14b-instruct", "label": "Qwen2.5 14B", "type": "llm", "channel": "阿里云"},
            {"provider": "QWEN", "name": "qwen2.5-7b-instruct", "label": "Qwen2.5 7B", "type": "llm", "channel": "阿里云"},
            {"provider": "QWEN", "name": "qwen2.5-3b-instruct", "label": "Qwen2.5 3B", "type": "llm", "channel": "阿里云"},
            {"provider": "QWEN", "name": "qwen2.5-coder-32b-instruct", "label": "Qwen2.5 Coder 32B", "type": "llm", "channel": "阿里云"},
            {"provider": "QWEN", "name": "qwen2.5-coder-7b-instruct", "label": "Qwen2.5 Coder 7B", "type": "llm", "channel": "阿里云"},
        ]
        all_models.extend(qwen_models)
    
    # 3. 添加DeepSeek模型
    if API_KEYS.get("deepseek"):
        deepseek_models = [
            {"provider": "DEEPSEEK", "name": "deepseek-chat", "label": "DeepSeek Chat", "type": "llm", "channel": "DeepSeek"},
            {"provider": "DEEPSEEK", "name": "deepseek-coder", "label": "DeepSeek Coder", "type": "llm", "channel": "DeepSeek"},
            {"provider": "DEEPSEEK", "name": "deepseek-reasoner", "label": "DeepSeek Reasoner", "type": "llm", "channel": "DeepSeek"},
        ]
        all_models.extend(deepseek_models)
    
    # 4. 添加Gemini模型
    if API_KEYS.get("gemini"):
        gemini_models = [
            {"provider": "GEMINI", "name": "gemini-2.0-flash-exp", "label": "Gemini 2.0 Flash (实验版)", "type": "llm", "channel": "Google"},
            {"provider": "GEMINI", "name": "gemini-exp-1206", "label": "Gemini 实验版 1206", "type": "llm", "channel": "Google"},
            {"provider": "GEMINI", "name": "gemini-exp-1121", "label": "Gemini 实验版 1121", "type": "llm", "channel": "Google"},
            {"provider": "GEMINI", "name": "gemini-1.5-pro-002", "label": "Gemini 1.5 Pro 002", "type": "llm", "channel": "Google"},
            {"provider": "GEMINI", "name": "gemini-1.5-pro", "label": "Gemini 1.5 Pro", "type": "llm", "channel": "Google"},
            {"provider": "GEMINI", "name": "gemini-1.5-flash", "label": "Gemini 1.5 Flash", "type": "llm", "channel": "Google"},
            {"provider": "GEMINI", "name": "gemini-1.5-flash-8b", "label": "Gemini 1.5 Flash 8B", "type": "llm", "channel": "Google"},
        ]
        all_models.extend(gemini_models)
    
    print(f"[Models] 返回 {len(all_models)} 个模型")
    return {"success": True, "models": all_models, "total": len(all_models)}

@app.get("/api/ai/siliconflow-models")
async def siliconflow_models(apiKey: Optional[str] = None):
    """获取硅基流动可用模型列表"""
    try:
        api_key = apiKey or API_KEYS["siliconflow"]
        if not api_key:
            return {"success": False, "error": "未配置 SiliconFlow API Key", "models": []}
        
        # 使用全局连接池客户端
        client = http_clients.get('siliconflow', http_clients['default'])
        headers = {"Authorization": f"Bearer {api_key}"}
        response = await client.get(
            API_ENDPOINTS["siliconflow_models"],
            headers=headers
        )
        
        if response.status_code != 200:
            return {"success": False, "error": "获取模型列表失败", "models": []}
        
        result = response.json()
        models = []
        for model in result.get("data", []):
            model_id = model.get("id", "")
            # 不过滤，返回所有模型
            models.append({
                "id": model_id,
                "name": model_id,
                "label": model_id.split("/")[-1] if "/" in model_id else model_id,
                "owned_by": model.get("owned_by", "unknown")
            })
        
        print(f"[SiliconFlow] 加载了 {len(models)} 个模型")
        return {"success": True, "models": models}
    
    except Exception as e:
        print(f"[SiliconFlow Models] 错误: {str(e)}")
        return {"success": False, "error": str(e), "models": []}

# ==================== 分析 API ====================

# 全局缓存配置
_agent_configs_cache = None
_cache_timestamp = 0

def get_agent_config(agent_id: str):
    """获取智能体配置（带缓存）"""
    global _agent_configs_cache, _cache_timestamp
    
    config_file = os.path.join(os.path.dirname(__file__), "agent_configs.json")
    
    # 检查文件是否更新（每5秒最多读一次）
    current_time = asyncio.get_event_loop().time()
    if _agent_configs_cache is None or (current_time - _cache_timestamp) > 5:
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                _agent_configs_cache = json.load(f)
                _cache_timestamp = current_time
    
    if _agent_configs_cache:
        for agent in _agent_configs_cache.get('agents', []):
            if agent.get('id') == agent_id:
                return agent
    return None

@app.post("/api/analyze")
async def analyze_stock(request: AnalyzeRequest):
    """统一的智能体分析接口"""
    try:
        agent_id = request.agent_id
        stock_code = request.stock_code
        stock_data = request.stock_data
        previous_outputs = request.previous_outputs
        
        # 从缓存获取配置
        agent_config = get_agent_config(agent_id)
        
        # 如果没有找到配置，使用默认值
        if not agent_config:
            agent_config = {
                "modelName": "deepseek-chat",
                "modelProvider": "DEEPSEEK",
                "temperature": 0.3
            }
        
        model_name = agent_config.get("modelName", "deepseek-chat")
        temperature = agent_config.get("temperature", 0.3)
        
        # 根据模型名称判断使用哪个API
        # 优先判断：如果包含斜杠，说明是平台模型（如 Qwen/Qwen3-8B），使用硅基流动
        api_endpoint = None
        if "/" in model_name:
            # 包含斜杠的都是平台模型，通过硅基流动访问
            api_endpoint = "/api/ai/siliconflow"
            provider = "SILICONFLOW"
        elif model_name.startswith("gemini"):
            # Gemini官方模型
            api_endpoint = "/api/ai/gemini"
            provider = "GEMINI"
        elif model_name in ["deepseek-chat", "deepseek-coder", "deepseek-reasoner"]:
            # DeepSeek官方模型（明确列举）
            api_endpoint = "/api/ai/deepseek"
            provider = "DEEPSEEK"
        elif model_name in ["qwen-max", "qwen-plus", "qwen-turbo", "qwen-max-longcontext", "qwen-turbo-latest"] or "通义千问" in model_name:
            # Qwen官方模型（明确列举）
            api_endpoint = "/api/ai/qwen"
            provider = "QWEN"
        else:
            # 默认使用硅基流动（支持最多模型）
            api_endpoint = "/api/ai/siliconflow"
            provider = "SILICONFLOW"
        
        # 构建系统提示词
        system_prompt = f"你是一个专业的{get_agent_role(agent_id)}。请基于提供的股票数据进行深入分析。"
        
        # 构建用户提示词
        user_prompt = f"请分析股票代码 {stock_code} 的以下数据：\n"
        user_prompt += f"当前价格: {stock_data.get('nowPri', 'N/A')}\n"
        user_prompt += f"今日涨跌幅: {stock_data.get('increase', 'N/A')}%\n"
        user_prompt += f"成交量: {stock_data.get('traAmount', 'N/A')}\n"
        user_prompt += f"成交额: {stock_data.get('traNumber', 'N/A')}\n"
        
        # 如果有之前的分析结果，添加到上下文
        if previous_outputs:
            user_prompt += "\n其他团队的分析结果：\n"
            for agent_name, output in previous_outputs.items():
                if output:
                    user_prompt += f"{agent_name}: {output[:200]}...\n"
        
        # 调用相应的AI API
        if provider == "GEMINI":
            req = GeminiRequest(
                prompt=user_prompt,
                systemPrompt=system_prompt,
                model=model_name,
                temperature=temperature
            )
            result = await gemini_api(req)
        elif provider == "DEEPSEEK":
            req = DeepSeekRequest(
                prompt=user_prompt,
                systemPrompt=system_prompt,
                model=model_name,
                temperature=temperature
            )
            result = await deepseek_api(req)
        elif provider == "QWEN":
            req = QwenRequest(
                prompt=user_prompt,
                systemPrompt=system_prompt,
                model=model_name,
                temperature=temperature
            )
            result = await qwen_api(req)
        else:
            req = SiliconFlowRequest(
                prompt=user_prompt,
                systemPrompt=system_prompt,
                model=model_name,
                temperature=temperature
            )
            result = await siliconflow_api(req)
        
        if result.get("success"):
            return {"success": True, "result": result.get("text", "")}
        else:
            return {"success": False, "error": result.get("error", "分析失败")}
            
    except Exception as e:
        import traceback
        print(f"[Analyze] 错误: {str(e)}")
        print(traceback.format_exc())
        return {"success": False, "error": str(e)}

def get_agent_role(agent_id):
    """根据智能体ID获取角色描述"""
    roles = {
        "macro": "宏观经济分析师",
        "industry": "行业研究分析师",
        "technical": "技术分析师",
        "funds": "资金流向分析师",
        "fundamental": "基本面分析师",
        "manager_fundamental": "基本面投资经理",
        "manager_momentum": "动量投资经理",
        "risk_system": "系统性风险总监",
        "risk_portfolio": "组合风险总监",
        "gm": "投资决策总经理"
    }
    return roles.get(agent_id, "投资分析师")

# ==================== 股票数据 API ====================

@app.post("/api/stock/{symbol}")
async def stock_data(symbol: str, request: StockRequest):
    """聚合数据股票 API 代理"""
    try:
        api_key = request.apiKey or API_KEYS["juhe"]
        if not api_key:
            raise HTTPException(status_code=500, detail="未配置聚合数据 API Key")
        
        # 格式化股票代码（添加 sh/sz 前缀）
        formatted_symbol = symbol.lower()
        if not formatted_symbol.startswith(("sh", "sz")):
            first_digit = formatted_symbol[0]
            if first_digit in ['6', '9']:
                formatted_symbol = 'sh' + formatted_symbol
            elif first_digit in ['0', '2', '3']:
                formatted_symbol = 'sz' + formatted_symbol
        
        # 使用全局连接池客户端
        client = http_clients.get('juhe', http_clients['default'])
        params = {
            "gid": formatted_symbol,
            "key": api_key
        }
        response = await client.get(
            API_ENDPOINTS["juhe"],
            params=params
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="聚合数据 API 错误")
        
        result = response.json()
        
        # 检查错误
        if result.get("error_code") and result["error_code"] != 0:
            return {"success": False, "error": result.get("reason", "未知错误")}
        
        # 提取数据
        if result.get("result") and len(result["result"]) > 0:
            stock_data = result["result"][0]
            return {"success": True, "data": stock_data}
        else:
            return {"success": False, "error": "未找到股票数据"}
    
    except Exception as e:
        print(f"[Stock] 错误: {str(e)}")
        return {"success": False, "error": str(e)}

# ==================== 配置管理 API ====================

@app.get("/api/config")
async def get_config():
    """获取配置信息（不包含敏感的 API Keys）"""
    # 检查环境变量中的API密钥
    config = {
        "api_keys": {},
        "model_configs": [],
        "backend_status": "running",
        "endpoints": list(API_ENDPOINTS.keys())
    }
    
    # 检查各个API密钥 - 使用已加载的API_KEYS
    if API_KEYS.get("gemini"):
        config["api_keys"]["gemini"] = "configured"
        config["GEMINI_API_KEY"] = "configured"
    
    if API_KEYS.get("deepseek"):
        config["api_keys"]["deepseek"] = "configured"
        config["DEEPSEEK_API_KEY"] = "configured"
    
    if API_KEYS.get("qwen"):
        config["api_keys"]["qwen"] = "configured"
        config["DASHSCOPE_API_KEY"] = "configured"
        
    if API_KEYS.get("siliconflow"):
        config["api_keys"]["siliconflow"] = "configured"
        config["SILICONFLOW_API_KEY"] = "configured"
        
    if API_KEYS.get("juhe"):
        config["api_keys"]["juhe"] = "configured"
        config["JUHE_API_KEY"] = "configured"
    
    # 尝试从文件加载模型配置
    try:
        config_file = os.path.join(os.path.dirname(__file__), 'agent_configs.json')
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                saved_config = json.load(f)
                if 'model_configs' in saved_config:
                    config["model_configs"] = saved_config['model_configs']
        else:
            # 使用默认模型配置
            config["model_configs"] = [
                {"id": "macro", "model_name": "gemini-2.0-flash-exp", "temperature": 0.3},
                {"id": "industry", "model_name": "deepseek-chat", "temperature": 0.3},
                {"id": "technical", "model_name": "qwen-plus", "temperature": 0.2},
                {"id": "funds", "model_name": "Qwen/Qwen2.5-7B-Instruct", "temperature": 0.2},
                {"id": "fundamental", "model_name": "deepseek-chat", "temperature": 0.3}
            ]
    except Exception as e:
        print(f"加载模型配置失败: {e}")
        
    return config

@app.post("/api/config/update")
async def update_config(keys: Dict[str, str]):
    """动态更新 API Keys（仅限开发环境）"""
    global API_KEYS
    for key, value in keys.items():
        if key in API_KEYS and value:
            API_KEYS[key] = value
    return {"success": True, "message": "配置已更新"}

@app.post("/api/config/agents")
async def save_agent_configs(config_data: Dict[str, Any]):
    """保存智能体配置到文件（包括模型选择）"""
    try:
        config_file = os.path.join(os.path.dirname(__file__), "agent_configs.json")
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, ensure_ascii=False, indent=2)
        
        agent_count = len(config_data.get('agents', []))
        model_count = len(config_data.get('selectedModels', []))
        print(f"[配置] 已保存 {agent_count} 个智能体配置和 {model_count} 个模型选择")
        return {"success": True, "message": "配置已保存"}
    except Exception as e:
        print(f"[配置] 保存失败: {str(e)}")
        return {"success": False, "error": str(e)}

@app.get("/api/config/agents")
async def load_agent_configs():
    """从文件加载智能体配置（包括模型选择）"""
    try:
        config_file = os.path.join(os.path.dirname(__file__), "agent_configs.json")
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # 兼容旧格式（直接是数组）
            if isinstance(config_data, list):
                config_data = {"agents": config_data, "selectedModels": []}
            
            agent_count = len(config_data.get('agents', []))
            model_count = len(config_data.get('selectedModels', []))
            print(f"[配置] 已加载 {agent_count} 个智能体配置和 {model_count} 个模型选择")
            return {"success": True, "data": config_data}
        else:
            return {"success": True, "data": {"agents": [], "selectedModels": []}}
    except Exception as e:
        print(f"[配置] 加载失败: {str(e)}")
        return {"success": False, "error": str(e), "data": {"agents": [], "selectedModels": []}}

# ==================== 静态文件服务 ====================

# 挂载静态文件目录（如果存在）
import os.path
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# ==================== 健康检查 ====================

@app.get("/")
async def root():
    """根路径 - 返回 HTML 页面（如果存在）"""
    html_file = os.path.join(static_dir, "index.html")
    if os.path.exists(html_file):
        return FileResponse(html_file)
    else:
        return {
            "status": "running",
            "service": "IcySaint AI Backend",
            "version": "1.0.0",
            "endpoints": [
                "/api/ai/gemini",
                "/api/ai/deepseek",
                "/api/ai/qwen",
                "/api/ai/siliconflow",
                "/api/ai/siliconflow-models",
                "/api/analyze",
                "/api/stock/{symbol}",
                "/api/config"
            ]
        }

@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy"}

# ==================== 启动服务器 ====================

if __name__ == "__main__":
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║         IcySaint AI - Python Backend Server          ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    # 检查 API Keys 配置（使用全局的API_KEYS，不要重新赋值）
    print("📋 API Keys 配置状态:")
    for name, key in API_KEYS.items():
        status = "✅ 已配置" if key else "❌ 未配置"
        print(f"  {name.upper()}: {status}")
    
    print("\n🚀 启动服务器...")
    print("📍 后端API: http://localhost:8000")
    print("📍 Vue前端: http://localhost:8080")
    print("📍 API文档: http://localhost:8000/docs")
    print("\n✨ 架构: FastAPI后端 + Vue3前端")
    print("💡 提示: 请确保Vue前端也在运行 (npm run serve)")
    print("🎯 使用 scripts/dev.py 可一键启动前后端！")
    print("-" * 60)
    
    # 启动服务器
    uvicorn.run(
        app,  # 直接使用app对象而不是字符串导入
        host="0.0.0.0",
        port=8000,
        reload=False,  # 关闭自动重载以避免CORS问题
        log_level="info"
    )
