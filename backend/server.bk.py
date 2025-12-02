"""
IcySaint AI - Python 后端服务器
使用 FastAPI 框架替代 Vercel Serverless Functions
"""

import os
import json
import asyncio
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import httpx
from dotenv import load_dotenv
import uvicorn

# 加载环境变量
load_dotenv('../.env')

# 创建 FastAPI 应用
app = FastAPI(title="IcySaint AI Backend", version="1.0.0")

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== 配置 ====================

# API Keys 从环境变量读取
API_KEYS = {
    "gemini": os.getenv("GEMINI_API_KEY", ""),
    "deepseek": os.getenv("DEEPSEEK_API_KEY", ""),
    "qwen": os.getenv("QWEN_API_KEY", ""),
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

# ==================== AI API 端点 ====================

@app.post("/api/ai/gemini")
async def gemini_api(request: GeminiRequest):
    """Google Gemini API 代理"""
    try:
        api_key = request.apiKey or API_KEYS["gemini"]
        if not api_key:
            raise HTTPException(status_code=500, detail="未配置 Gemini API Key")
        
        # 这里需要使用 Google 的官方 SDK，简化实现
        # 实际实现需要安装 google-generativeai 包
        async with httpx.AsyncClient() as client:
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
        
        async with httpx.AsyncClient() as client:
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
        
        async with httpx.AsyncClient() as client:
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
        
        async with httpx.AsyncClient() as client:
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

@app.get("/api/ai/siliconflow-models")
async def siliconflow_models(apiKey: Optional[str] = None):
    """获取硅基流动可用模型列表"""
    try:
        api_key = apiKey or API_KEYS["siliconflow"]
        if not api_key:
            return {"success": False, "error": "未配置 SiliconFlow API Key", "models": []}
        
        async with httpx.AsyncClient() as client:
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
        
        async with httpx.AsyncClient() as client:
            params = {
                "gid": formatted_symbol,
                "key": api_key
            }
            
            response = await client.get(
                API_ENDPOINTS["juhe"],
                params=params,
                timeout=10.0
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
    return {
        "configured": {
            "gemini": bool(API_KEYS["gemini"]),
            "deepseek": bool(API_KEYS["deepseek"]),
            "qwen": bool(API_KEYS["qwen"]),
            "siliconflow": bool(API_KEYS["siliconflow"]),
            "juhe": bool(API_KEYS["juhe"])
        },
        "endpoints": list(API_ENDPOINTS.keys())
    }

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
    
    # 检查 API Keys 配置
    print("📋 API Keys 配置状态:")
    for name, key in API_KEYS.items():
        status = "✅ 已配置" if key else "❌ 未配置"
        print(f"  {name.upper()}: {status}")
    
    print("\n🚀 启动服务器...")
    print("📍 后端地址: http://localhost:8000")
    print("📍 前端界面: http://localhost:8000 (已集成)")
    print("📍 API 文档: http://localhost:8000/docs")
    print("\n✨ 新架构: 纯Python后端 + HTML前端")
    print("💡 提示: 直接访问 http://localhost:8000 即可使用")
    print("🎯 无需 npm，无需 Node.js，一键启动！")
    print("-" * 60)
    
    # 启动服务器
    uvicorn.run(
        "server:app",  # 使用字符串导入以支持reload
        host="0.0.0.0",
        port=8000,
        reload=True,  # 开发模式下自动重载
        log_level="info"
    )
