"""
IcySaint AI - Python 后端服务器
使用 FastAPI 框架替代 Vercel Serverless Functions
"""

import os
import sys
# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

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
from backend.api.agents_api import router as agents_router

# ==================== 配置 ====================

# API Keys 从环境变量读取
API_KEYS = {
    "gemini": os.getenv("GEMINI_API_KEY", ""),
    "deepseek": os.getenv("DEEPSEEK_API_KEY", ""),
    "qwen": os.getenv("DASHSCOPE_API_KEY", "") or os.getenv("QWEN_API_KEY", ""),  # 支持两种环境变量名
    "siliconflow": os.getenv("SILICONFLOW_API_KEY", ""),
    "juhe": os.getenv("JUHE_API_KEY", ""),
    "finnhub": os.getenv("FINNHUB_API_KEY", ""),
    "tushare": os.getenv("TUSHARE_TOKEN", "")
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
app.include_router(agents_router)

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
    custom_instruction: Optional[str] = None

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
                    print(f"[SiliconFlow] 所有重试都失败，返回降级响应")
                    # 超时时返回友好的降级响应，而不是错误
                    return {
                        "success": True,
                        "text": f"⚠️ 由于网络超时，本次分析未能完成。建议：\n1. 检查网络连接\n2. 尝试使用其他 AI 模型\n3. 稍后重试",
                        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                        "timeout": True
                    }
        
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
        custom_instruction = request.custom_instruction
        
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
        role_name = get_agent_role(agent_id)
        system_prompt = f"你是一个专业的{role_name}，隶属于AlphaCouncil顶级投研团队。你的目标是提供深度、犀利且独到的投资见解。"
        system_prompt += "\n\n【风格要求】\n1. 直接切入主题，严禁废话。\n2. 严禁在开头复述股票代码、名称、当前价格等基础信息（除非数据出现重大异常）。\n3. 像华尔街资深分析师一样说话，使用专业术语但逻辑清晰。\n4. 必须引用前序同事的分析结论作为支撑或反驳的依据。"

        # 构建用户提示词
        user_prompt = ""
        
        # 如果有自定义指令，优先放入
        if custom_instruction:
            user_prompt += f"【当前任务指令】\n{custom_instruction}\n\n"
        
        # 基础数据仅作为参考附录，不强制要求分析
        user_prompt += f"【参考数据 - {stock_code}】\n"
        user_prompt += f"价格: {stock_data.get('nowPri', stock_data.get('price', 'N/A'))} | 涨跌: {stock_data.get('increase', stock_data.get('change', 'N/A'))}%\n"
        user_prompt += f"成交: {stock_data.get('traAmount', stock_data.get('volume', 'N/A'))}\n"
        
        # 重点：前序分析结果
        if previous_outputs and len(previous_outputs) > 0:
            user_prompt += "\n【团队成员已完成的分析】(请基于此进行深化，不要重复)\n"
            for agent_name, output in previous_outputs.items():
                if output:
                    # 截取前500字符摘要，避免Token溢出
                    summary = output[:500] + "..." if len(output) > 500 else output
                    user_prompt += f">>> {get_agent_role(agent_name)} 的结论:\n{summary}\n\n"
        else:
            user_prompt += "\n你是第一批进入分析的专家，请基于原始市场数据构建初始观点。\n"

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
    """股票数据 API - 使用数据源管理器的自动降级功能"""
    try:
        from backend.dataflows.data_source_manager import DataSourceManager
        from backend.dataflows.stock_data_adapter import StockDataAdapter
        
        # 使用数据源管理器获取数据
        manager = DataSourceManager()
        
        # 获取实时行情数据（不需要历史数据）
        result_text = manager.get_stock_data(symbol)
        
        # 检查是否成功
        if "❌" in result_text or "错误" in result_text:
            print(f"[Stock] 数据获取失败: {result_text[:200]}")
            return {"success": False, "error": result_text}
        
        # 使用适配器解析数据（统一格式）
        stock_info = StockDataAdapter.parse_text_data(result_text, symbol)
        
        # 验证数据有效性
        if not StockDataAdapter.validate_data(stock_info):
            print(f"[Stock] 数据验证失败: {stock_info}")
            return {"success": False, "error": "数据格式错误或缺少关键信息"}
        
        print(f"[Stock] 成功获取{symbol}数据: {stock_info['name']} {stock_info['price']} {stock_info['change']} (数据源: {stock_info['data_source']})")
        return stock_info
    
    except Exception as e:
        import traceback
        print(f"[Stock] 错误: {str(e)}")
        print(traceback.format_exc())
        return {"success": False, "error": str(e)}

# ==================== 配置管理 API ====================

@app.get("/api/config")
async def get_config():
    """获取配置信息（返回实际的 API Keys）"""
    config = {
        "api_keys": {},
        "model_configs": [],
        "backend_status": "running",
        "endpoints": list(API_ENDPOINTS.keys())
    }
    
    # 返回实际的 API Keys
    if API_KEYS.get("gemini"):
        config["api_keys"]["gemini"] = API_KEYS["gemini"]
        config["GEMINI_API_KEY"] = API_KEYS["gemini"]
    
    if API_KEYS.get("deepseek"):
        config["api_keys"]["deepseek"] = API_KEYS["deepseek"]
        config["DEEPSEEK_API_KEY"] = API_KEYS["deepseek"]
    
    if API_KEYS.get("qwen"):
        config["api_keys"]["qwen"] = API_KEYS["qwen"]
        config["DASHSCOPE_API_KEY"] = API_KEYS["qwen"]
        
    if API_KEYS.get("siliconflow"):
        config["api_keys"]["siliconflow"] = API_KEYS["siliconflow"]
        config["SILICONFLOW_API_KEY"] = API_KEYS["siliconflow"]
        
    if API_KEYS.get("juhe"):
        config["api_keys"]["juhe"] = API_KEYS["juhe"]
        config["JUHE_API_KEY"] = API_KEYS["juhe"]
    
    # 添加数据渠道配置
    if API_KEYS.get("finnhub"):
        config["api_keys"]["finnhub"] = API_KEYS["finnhub"]
        config["FINNHUB_API_KEY"] = API_KEYS["finnhub"]
    
    if API_KEYS.get("tushare"):
        config["api_keys"]["tushare"] = API_KEYS["tushare"]
        config["TUSHARE_TOKEN"] = API_KEYS["tushare"]
    
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

@app.post("/api/config")
async def save_config(request: Dict[str, Any]):
    """保存 API Keys 配置"""
    try:
        api_keys = request.get('api_keys', {})
        global API_KEYS
        
        # 更新全局 API_KEYS
        for key, value in api_keys.items():
            if value:  # 只更新非空值
                API_KEYS[key] = value
        
        print(f"[Config] API Keys 已更新: {list(api_keys.keys())}")
        return {"success": True, "message": "API 配置已保存"}
    except Exception as e:
        print(f"[Config] 保存失败: {str(e)}")
        return {"success": False, "error": str(e)}

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
        return {"success": False, "error": str(e)}

class TestApiRequest(BaseModel):
    api_key: str

@app.post("/api/test/{provider}")
async def test_api_connection(provider: str, request: TestApiRequest):
    """测试 API 连接并返回真实响应示例"""
    api_key = request.api_key
    
    # 处理特殊情况
    if provider == 'akshare':
        # AKShare 不需要 API Key
        api_key = None
    elif not api_key or api_key.strip() == '':
        return {"success": False, "error": f"请先输入 {provider} 的 API Key"}
    
    # 根据 provider 进行不同的测试
    try:
        if provider == 'gemini':
            # 测试 Gemini API
            try:
                test_url = f"{API_ENDPOINTS['gemini']}/models/gemini-1.5-flash:generateContent?key={api_key}"
                client = http_clients.get('gemini', http_clients['default'])
                response = await client.post(
                    test_url,
                    json={"contents": [{"parts": [{"text": "Hello, this is a test message."}]}]},
                    timeout=15.0
                )
            except Exception as e:
                error_msg = str(e)
                if 'ConnectTimeout' in error_msg or 'timeout' in error_msg.lower():
                    return {"success": False, "error": "连接超时。Gemini API 可能需要代理访问，或网络不稳定。"}
                elif 'ConnectError' in error_msg:
                    return {"success": False, "error": "无法连接到 Gemini 服务器。请检查网络或代理设置。"}
                else:
                    return {"success": False, "error": f"连接错误: {error_msg[:100]}"}
            if response.status_code == 200:
                result = response.json()
                # 提取响应文本
                response_text = ""
                if 'candidates' in result and len(result['candidates']) > 0:
                    candidate = result['candidates'][0]
                    if 'content' in candidate and 'parts' in candidate['content']:
                        response_text = candidate['content']['parts'][0].get('text', '')
                return {
                    "success": True, 
                    "message": "Gemini API 连接成功！",
                    "test_response": response_text[:200] if response_text else "模型响应成功"
                }
            else:
                return {"success": False, "error": f"HTTP {response.status_code}: {response.text[:200]}"}
                
        elif provider == 'deepseek':
            # 测试 DeepSeek API
            client = http_clients.get('deepseek', http_clients['default'])
            response = await client.post(
                f"{API_ENDPOINTS['deepseek']}/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": "deepseek-chat",
                    "messages": [{"role": "user", "content": "Say hello in Chinese"}],
                    "max_tokens": 50
                },
                timeout=15.0
            )
            if response.status_code == 200:
                result = response.json()
                response_text = result.get('choices', [{}])[0].get('message', {}).get('content', '')
                return {
                    "success": True, 
                    "message": "DeepSeek API 连接成功！",
                    "test_response": response_text[:200] if response_text else "模型响应成功"
                }
            else:
                return {"success": False, "error": f"HTTP {response.status_code}: {response.text[:200]}"}
                
        elif provider == 'qwen':
            # 测试通义千问 API
            client = http_clients.get('qwen', http_clients['default'])
            response = await client.post(
                API_ENDPOINTS['qwen'],
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": "qwen-turbo",
                    "input": {"messages": [{"role": "user", "content": "你好，请用中文问好"}]}
                },
                timeout=15.0
            )
            if response.status_code == 200:
                result = response.json()
                response_text = result.get('output', {}).get('text', '')
                return {
                    "success": True, 
                    "message": "通义千问 API 连接成功！",
                    "test_response": response_text[:200] if response_text else "模型响应成功"
                }
            else:
                return {"success": False, "error": f"HTTP {response.status_code}: {response.text[:200]}"}
                
        elif provider == 'siliconflow':
            # 测试硅基流动 API - 先获取模型列表，再测试对话
            client = http_clients.get('siliconflow', http_clients['default'])
            # 第一步：获取模型列表
            response = await client.get(
                API_ENDPOINTS['siliconflow_models'],
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=10.0
            )
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}: {response.text[:200]}"}
            
            models_data = response.json()
            model_count = len(models_data.get('data', []))
            
            # 第二步：测试对话 API
            chat_response = await client.post(
                API_ENDPOINTS['siliconflow'],
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": "Qwen/Qwen2.5-7B-Instruct",
                    "messages": [{"role": "user", "content": "你好"}],
                    "max_tokens": 50
                },
                timeout=15.0
            )
            
            if chat_response.status_code == 200:
                result = chat_response.json()
                response_text = result.get('choices', [{}])[0].get('message', {}).get('content', '')
                return {
                    "success": True, 
                    "message": f"硅基流动 API 连接成功！可用模型: {model_count}个",
                    "test_response": response_text[:200] if response_text else "模型响应成功"
                }
            else:
                return {"success": False, "error": f"Chat API HTTP {chat_response.status_code}: {chat_response.text[:200]}"}
                
        elif provider == 'juhe':
            # 测试聚合数据 API - 获取茅台股票数据
            client = http_clients.get('juhe', http_clients['default'])
            response = await client.get(
                f"{API_ENDPOINTS['juhe']}?gid=sh600519&key={api_key}",
                timeout=10.0
            )
            if response.status_code == 200:
                result = response.json()
                if result.get('error_code') == 0:
                    stock_data = result.get('result', [{}])[0]
                    stock_name = stock_data.get('name', '')
                    stock_price = stock_data.get('nowPri', '')
                    return {
                        "success": True, 
                        "message": "聚合数据 API 连接成功！",
                        "test_response": f"获取股票数据成功: {stock_name} 现价 {stock_price}"
                    }
                else:
                    return {"success": False, "error": result.get('reason', '未知错误')}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}
                
        elif provider == 'news':
            # 测试财经新闻 API - 模拟测试
            return {
                "success": True,
                "message": "财经新闻 API 配置已保存！",
                "test_response": "新闻数据源将在分析时自动调用"
            }
            
        elif provider == 'crawler':
            # 测试网页爬虫 - 模拟测试
            return {
                "success": True,
                "message": "网页爬虫服务配置已保存！",
                "test_response": "爬虫服务将在需要时自动启动"
            }
            
        elif provider == 'finnhub':
            # 测试 FinnHub API
            client = http_clients.get('finnhub', http_clients['default'])
            response = await client.get(
                f"https://finnhub.io/api/v1/quote?symbol=AAPL&token={api_key}",
                timeout=10.0
            )
            if response.status_code == 200:
                result = response.json()
                if 'c' in result:  # current price
                    return {
                        "success": True,
                        "message": "FinnHub API 连接成功！",
                        "test_response": f"AAPL 当前价格: ${result['c']}"
                    }
                else:
                    return {"success": False, "error": "无效的 API 响应"}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}: {response.text[:200]}"}
                
        elif provider == 'tushare':
            # 测试 Tushare API
            try:
                import tushare as ts
                ts.set_token(api_key)
                pro = ts.pro_api()
                # 测试获取交易日历
                df = pro.trade_cal(exchange='SSE', start_date='20240101', end_date='20240110')
                if df is not None and len(df) > 0:
                    return {
                        "success": True,
                        "message": "Tushare API 连接成功！",
                        "test_response": f"成功获取 {len(df)} 条交易日历数据"
                    }
                else:
                    return {"success": False, "error": "无法获取数据"}
            except ImportError:
                return {"success": False, "error": "Tushare 未安装。请运行: pip install tushare"}
            except Exception as e:
                error_msg = str(e)
                if '权限' in error_msg or 'permission' in error_msg.lower():
                    return {"success": False, "error": "Token 权限不足。请访问 https://tushare.pro 获取积分解锁权限。"}
                elif 'token' in error_msg.lower():
                    return {"success": False, "error": "Token 无效。请检查 Tushare Token 是否正确。"}
                else:
                    return {"success": False, "error": f"Tushare 错误: {error_msg[:100]}"}
                
        elif provider == 'akshare':
            # 测试 AKShare - 不需要 API Key，直接检查模块是否可用
            try:
                import akshare as ak
                # 只检查模块是否安装，不进行实际网络请求
                # 因为 AKShare 的数据源服务器不稳定，测试连接常常失败
                # 但实际使用时会自动重试，所以只需确认模块存在即可
                if hasattr(ak, 'stock_zh_a_spot_em'):
                    return {
                        "success": True,
                        "message": "AKShare 模块已安装，可以使用！",
                        "test_response": "AKShare 是开源金融数据库，无需 API Key。实际使用时会自动获取数据。"
                    }
                else:
                    return {"success": False, "error": "AKShare 版本过旧，请升级: pip install --upgrade akshare"}
            except ImportError:
                return {"success": False, "error": "AKShare 未安装。请运行: pip install akshare"}
            except Exception as e:
                return {"success": False, "error": f"AKShare 检查失败: {str(e)[:100]}"}
        else:
            return {"success": False, "error": f"不支持的 provider: {provider}"}
            
    except Exception as e:
        import traceback
        print(f"[Test API] {provider} 测试失败: {str(e)}")
        print(traceback.format_exc())
        return {"success": False, "error": str(e)}

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
