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
from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime, date
import httpx
from dotenv import load_dotenv
import uvicorn
from asyncio import Semaphore

# 导入降级处理器
from backend.utils.llm_fallback_handler import get_fallback_handler

# 全局并发控制器 - 限制同时发送到SiliconFlow的请求数
# 增加到20个并发，避免分析时阻塞其他功能
siliconflow_semaphore = Semaphore(20)  # 最多20个并发请求

# 模型能力画像与静默压测的全局状态与结果文件
CALIBRATION_RESULTS_FILE = os.path.join(os.path.dirname(__file__), "model_calibration.json")
calibration_state = {
    "status": "idle",       # idle / running / completed / error
    "lastRunAt": None,
    "error": None,
    "results": {},           # {model_name: {provider, channel, tests: [...]}}
    "settings": None         # 最近一次压测使用的配置快照
}


def save_calibration_state():
    """将当前压测状态保存到文件，方便前端或重启后查看"""
    try:
        with open(CALIBRATION_RESULTS_FILE, "w", encoding="utf-8") as f:
            json.dump(calibration_state, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[Calibration] 保存结果失败: {str(e)}")


def load_calibration_state_from_file():
    """从文件加载最近一次压测状态（如果存在）"""
    global calibration_state
    try:
        if os.path.exists(CALIBRATION_RESULTS_FILE):
            with open(CALIBRATION_RESULTS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                calibration_state.update(data)
    except Exception as e:
        print(f"[Calibration] 加载结果失败: {str(e)}")


# 模块加载时尝试恢复一次历史压测结果
load_calibration_state_from_file()

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
from backend.api.agent_config_api import router as agent_config_router
from backend.api.unified_news_api_endpoint import router as unified_news_router
from backend.api.documents_api import router as documents_router
from backend.api.akshare_data_api import router as akshare_router
from backend.api.agent_logs_api import router as agent_logs_router
from backend.api.analysis_session_api import router as analysis_session_router  # 分析会话 API
from backend.api.analysis_session_db_api import router as analysis_session_db_router  # 数据库版会话 API
from backend.api.backtest_api import router as backtest_router  # 回测API
from backend.api.strategy_api import router as strategy_router  # 策略API
from backend.api.llm_config_api import router as llm_config_router  # LLM配置API（智能分析）
from backend.api.trading_llm_config_api import router as trading_llm_config_router  # 交易LLM配置API（新功能）
from backend.api.strategy_selection_api import router as strategy_selection_router  # 智能策略选择API
from backend.api.auto_trading_api import router as auto_trading_router  # 自动交易API
from backend.api.tracking_api import router as tracking_router  # 持续跟踪API
from backend.api.verification_api import router as verification_router  # 验证报告API
from backend.api.kline_api import router as kline_router  # K线API
from backend.api.scheduler_api import router as scheduler_router  # 调度器API
from backend.api.data_source_health_api import router as data_source_health_router  # 数据源健康检查API
from backend.api.dataflow_api import router as dataflow_router  # 数据流监控API
from backend.api.notification_api import router as notification_router  # 通知服务API
from backend.api.sse_api import router as sse_router  # SSE实时推送API
from backend.api.async_analysis_api import router as async_analysis_router  # 异步分析API
from backend.api.websocket_api import router as websocket_router  # WebSocket实时通知API
from backend.api.providers_api import router as providers_router  # 数据源Provider API (TDX/Wencai/TA-Lib)
from backend.api.report_api import router as report_router  # PDF报告生成API
from backend.api.longhubang_api import router as longhubang_router  # 龙虎榜分析API
from backend.api.wencai_api import router as wencai_router  # 问财智能选股API
from backend.api.sector_rotation_api import router as sector_rotation_router  # 板块轮动分析API
from backend.api.sentiment_api import router as sentiment_router  # 市场情绪分析API
from backend.api.realtime_monitor_api import router as realtime_monitor_router  # 实时盯盘监控API
from backend.api.market_data_api import router as market_data_router  # 市场数据API（盘口、排行榜等）
from backend.api.news_center_api import router as news_center_router  # 统一新闻监控中心API
from backend.api.cninfo_api import router as cninfo_router  # 巨潮资讯网官方API
from backend.api.system_api import router as system_router  # 系统设置API
from backend.api.api_monitor_api import router as api_monitor_router  # API监控API
from backend.api.datasource_api import router as datasource_router  # 数据源调度器API

# ==================== 配置 ====================

# API Keys 从环境变量读取
API_KEYS = {
    "gemini": os.getenv("GEMINI_API_KEY", ""),
    "deepseek": os.getenv("DEEPSEEK_API_KEY", ""),
    "qwen": os.getenv("DASHSCOPE_API_KEY", "") or os.getenv("QWEN_API_KEY", ""),  # 支持两种环境变量名
    "siliconflow": os.getenv("SILICONFLOW_API_KEY", ""),
    "juhe": os.getenv("JUHE_API_KEY", ""),
    "finnhub": os.getenv("FINNHUB_API_KEY", ""),
    "tushare": os.getenv("TUSHARE_TOKEN", ""),
    "cninfo_access_key": os.getenv("CNINFO_ACCESS_KEY", ""),
    "cninfo_access_secret": os.getenv("CNINFO_ACCESS_SECRET", ""),
    "cninfo_access_token": os.getenv("CNINFO_ACCESS_TOKEN", "")
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

    # 初始化 Redis 连接（用于异步任务和SSE）
    try:
        from backend.services.async_task.redis_client import redis_client
        await redis_client.connect()
        if redis_client.is_redis_available:
            print("✅ Redis 连接成功")
        else:
            print("⚠️ Redis 不可用，使用内存降级模式")
    except Exception as e:
        print(f"⚠️ Redis 初始化失败: {e}，使用内存降级模式")

    # 启动交易调度器（可选，根据环境变量控制）
    import os
    if os.getenv("ENABLE_SCHEDULER", "false").lower() == "true":
        try:
            from backend.services.scheduler_service import start_scheduler
            start_scheduler()
            print("✅ 交易调度器已启动")
        except Exception as e:
            print(f"⚠️ 交易调度器启动失败: {e}")
    
    # 启动数据清理调度器（默认启动）
    if os.getenv("ENABLE_DATA_CLEANUP", "true").lower() == "true":
        try:
            from backend.dataflows.data_cleanup_scheduler import start_cleanup_scheduler
            start_cleanup_scheduler()
            print("✅ 数据清理调度器已启动")
        except Exception as e:
            print(f"⚠️ 数据清理调度器启动失败: {e}")

    # 启动后台新闻服务（默认启动）
    # 该服务使用独立进程池处理新闻请求，完全不阻塞FastAPI主事件循环
    if os.getenv("ENABLE_BACKGROUND_NEWS", "true").lower() == "true":
        try:
            from backend.services.background_news_service import background_news_service
            await background_news_service.start()
            print("✅ 后台新闻服务已启动（独立进程池模式）")
        except Exception as e:
            print(f"⚠️ 后台新闻服务启动失败: {e}")

    # 启动统一后台数据更新服务（默认禁用）
    # 该服务会自动为所有监控股票调用48个接口，非常耗时
    # 如需启用，请设置环境变量 ENABLE_DATA_UPDATE_SERVICE=true
    if os.getenv("ENABLE_DATA_UPDATE_SERVICE", "false").lower() == "true":
        try:
            from backend.services.unified_data_update_service import start_background_update_service
            start_background_update_service()
            print("✅ 统一后台数据更新服务已启动")
        except Exception as e:
            print(f"⚠️ 统一后台数据更新服务启动失败: {e}")

    # 启动实时盯盘监控服务（默认禁用）
    # 该服务提供实时股票监控和AI决策功能
    # 如需启用，请设置环境变量 ENABLE_REALTIME_MONITOR=true
    if os.getenv("ENABLE_REALTIME_MONITOR", "false").lower() == "true":
        try:
            from backend.services.realtime_monitor_service import get_realtime_monitor_service
            realtime_monitor = get_realtime_monitor_service()
            # 尝试加载保存的配置并自动启动
            realtime_monitor.load_config()
            if realtime_monitor.config.get("auto_start", False):
                realtime_monitor.start_monitoring()
                print("✅ 实时盯盘监控服务已启动（自动启动模式）")
            else:
                print("✅ 实时盯盘监控服务已初始化（等待手动启动）")
        except Exception as e:
            print(f"⚠️ 实时盯盘监控服务启动失败: {e}")

    # 启动统一新闻监控中心（默认启动）
    # 该服务整合所有新闻数据源，提供统一缓存和实时推送
    if os.getenv("ENABLE_NEWS_MONITOR_CENTER", "true").lower() == "true":
        try:
            from backend.services.news_center import get_news_monitor_center
            news_monitor = get_news_monitor_center()
            await news_monitor.start()
            print("✅ 统一新闻监控中心已启动")
        except Exception as e:
            print(f"⚠️ 统一新闻监控中心启动失败: {e}")

    # 启动TDX数据缓存服务（默认启动）
    # 该服务在后台定时获取TDX数据，缓存到服务器端文件
    # 所有API请求直接读取缓存，不阻塞用户请求
    if os.getenv("ENABLE_TDX_CACHE_SERVICE", "true").lower() == "true":
        try:
            from backend.services.tdx_cache_service import get_tdx_cache_service
            tdx_cache = get_tdx_cache_service()
            tdx_cache.start()
            print("✅ TDX数据缓存服务已启动")
        except Exception as e:
            print(f"⚠️ TDX数据缓存服务启动失败: {e}")

    # yield 控制权给应用
    yield

    # 停止调度器
    try:
        from backend.services.scheduler_service import stop_scheduler
        stop_scheduler()
        print("✅ 交易调度器已停止")
    except:
        pass

    # 停止数据清理调度器
    try:
        from backend.dataflows.data_cleanup_scheduler import stop_cleanup_scheduler
        stop_cleanup_scheduler()
        print("✅ 数据清理调度器已停止")
    except:
        pass

    # 停止后台新闻服务
    try:
        from backend.services.background_news_service import background_news_service
        await background_news_service.stop()
        print("✅ 后台新闻服务已停止")
    except:
        pass

    # 停止统一后台数据更新服务
    try:
        from backend.services.unified_data_update_service import stop_background_update_service
        stop_background_update_service()
        print("✅ 统一后台数据更新服务已停止")
    except:
        pass

    # 停止实时盯盘监控服务
    try:
        from backend.services.realtime_monitor_service import get_realtime_monitor_service
        realtime_monitor = get_realtime_monitor_service()
        if realtime_monitor.is_running:
            realtime_monitor.stop_monitoring()
            print("✅ 实时盯盘监控服务已停止")
    except:
        pass

    # 停止统一新闻监控中心
    try:
        from backend.services.news_center import get_news_monitor_center
        news_monitor = get_news_monitor_center()
        await news_monitor.stop()
        print("✅ 统一新闻监控中心已停止")
    except:
        pass

    # 停止TDX数据缓存服务
    try:
        from backend.services.tdx_cache_service import get_tdx_cache_service
        tdx_cache = get_tdx_cache_service()
        tdx_cache.stop()
        print("✅ TDX数据缓存服务已停止")
    except:
        pass

    # 关闭 Redis 连接
    try:
        from backend.services.async_task.redis_client import redis_client
        await redis_client.disconnect()
        print("✅ Redis 连接已关闭")
    except:
        pass

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

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有源，包括Vue开发服务器
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册API路由
app.include_router(news_router)
app.include_router(debate_router)
app.include_router(trading_router)
app.include_router(verification_router)
app.include_router(agents_router)
app.include_router(agent_config_router)  # 智能体配置API
app.include_router(unified_news_router)  # 统一新闻API
app.include_router(documents_router)  # 文档API
app.include_router(akshare_router)  # AKShare数据 API
app.include_router(agent_logs_router)  # 智能体日志流API
app.include_router(analysis_session_router)  # 分析会话 API
app.include_router(analysis_session_db_router)  # 数据库版会话 API
app.include_router(backtest_router)  # 回测API
app.include_router(strategy_router)  # 策略API
app.include_router(llm_config_router)  # LLM配置API（智能分析）
app.include_router(trading_llm_config_router)  # 交易LLM配置API（新功能）
app.include_router(strategy_selection_router)  # 智能策略选择API
app.include_router(auto_trading_router)  # 自动交易API
app.include_router(tracking_router)  # 持续跟踪API
app.include_router(verification_router)  # 验证报告API
app.include_router(kline_router)  # K线API
app.include_router(scheduler_router)  # 调度器API
app.include_router(data_source_health_router)  # 数据源健康检查API
app.include_router(dataflow_router)  # 数据流监控API
app.include_router(notification_router)  # 通知服务API
app.include_router(sse_router)  # SSE实时推送API
app.include_router(async_analysis_router)  # 异步分析API
app.include_router(websocket_router)  # WebSocket实时通知API
app.include_router(providers_router)  # 数据源Provider API (TDX/Wencai/TA-Lib)
app.include_router(report_router)  # PDF报告生成API
app.include_router(longhubang_router)  # 龙虎榜分析API
app.include_router(wencai_router)  # 问财智能选股API
app.include_router(sector_rotation_router)  # 板块轮动分析API
app.include_router(sentiment_router)  # 市场情绪分析API
app.include_router(realtime_monitor_router)  # 实时盯盘监控API
app.include_router(market_data_router)  # 市场数据API（盘口、排行榜等）
app.include_router(news_center_router)  # 统一新闻监控中心API
app.include_router(cninfo_router)  # 巨潮资讯网官方API
app.include_router(system_router)  # 系统设置API
app.include_router(api_monitor_router)  # API监控API
app.include_router(datasource_router)  # 数据源调度器API


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
    # 仅用于能力画像/压测等高级用法：覆盖默认max_tokens与是否开启thinking能力
    maxTokens: Optional[int] = None
    enableThinking: Optional[bool] = None
    # 智能体角色（用于降级策略）
    agentRole: Optional[str] = None

class StockRequest(BaseModel):
    symbol: str
    apiKey: Optional[str] = None

class AnalyzeRequest(BaseModel):
    agent_id: str
    stock_code: str
    stock_data: Optional[Dict[str, Any]] = {}
    previous_outputs: Optional[Dict[str, Any]] = {}
    custom_instruction: Optional[str] = None


class CalibrationRunRequest(BaseModel):
    """触发模型能力画像与静默压测的请求体"""
    # 如果不指定，则默认使用 agent_configs.json 中的 selectedModels + summarizerModel
    models: Optional[List[str]] = None
    # 可选覆盖配置；如果为空则使用 agent_configs.json 中的 calibrationSettings
    calibrationSettings: Optional[Dict[str, Any]] = None

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
        
        if response.status_code == 402:
            # 402是余额不足
            print(f"[DeepSeek] 余额不足，返回降级响应")
            return {
                "success": True,
                "text": f"⚠️ DeepSeek API 余额不足。建议：\n1. 检查 API 余额\n2. 切换到 SiliconFlow 或其他模型\n3. 充值后重试",
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                "quota_exceeded": True
            }
        elif response.status_code != 200:
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
    # 使用全局并发控制器限制并发请求
    import datetime
    import time
    req_time = datetime.datetime.now().strftime("%H:%M:%S")
    request._start_time = time.time()  # 记录开始时间
    
    # 记录等待获取锁的时间
    lock_wait_start = time.time()
    async with siliconflow_semaphore:
        lock_wait_time = time.time() - lock_wait_start
        concurrent_count = 10 - siliconflow_semaphore._value
        print(f"[SiliconFlow] [{req_time}] 获取并发锁")
        print(f"  - 等待锁耗时: {lock_wait_time:.1f}秒")
        print(f"  - 当前并发数: {concurrent_count}/10")
        
        client = None
        try:
            api_key = request.apiKey or API_KEYS["siliconflow"]
            if not api_key:
                raise HTTPException(status_code=500, detail="未配置 SiliconFlow API Key")

            # ✅ 动态超时配置：根据智能体类型调整
            # 复杂智能体（news_analyst, fundamental）需要更长时间
            agent_role = request.agentRole if hasattr(request, 'agentRole') else None
            complex_agents = ['NEWS', 'FUNDAMENTAL', 'TECHNICAL', 'MACRO', 'INDUSTRY']

            if agent_role in complex_agents:
                read_timeout = 60.0  # 复杂智能体 60秒
                total_timeout = 90.0
            else:
                read_timeout = 45.0  # 普通智能体 45秒
                total_timeout = 60.0

            # 为每个请求创建独立的客户端，避免连接池死锁
            client = httpx.AsyncClient(
                timeout=httpx.Timeout(
                    timeout=total_timeout,
                    connect=15.0,
                    read=read_timeout,
                    write=15.0,
                    pool=15.0
                ),
                limits=httpx.Limits(
                    max_connections=10,        # 保守设置，避免过多连接
                    max_keepalive_connections=5  # 保守设置
                )
            )
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            is_qwen3_model = isinstance(request.model, str) and "qwen3" in request.model.lower()
            # 默认输出长度控制：支持通过请求覆盖
            # 增加默认值以支持更完整的分析报告
            max_tokens = 4096
            if request.maxTokens is not None:
                try:
                    max_tokens = int(request.maxTokens)
                except Exception:
                    max_tokens = 4096
            elif is_qwen3_model:
                # Qwen3 默认保守一些，避免长输出导致超时
                max_tokens = 2048
            data = {
                "model": request.model,
                "messages": [
                    {"role": "system", "content": request.systemPrompt},
                    {"role": "user", "content": request.prompt}
                ],
                "temperature": request.temperature,
                "max_tokens": max_tokens,
                "stream": False
            }
            # enable_thinking 仅在请求显式指定或针对 Qwen3 时设置
            enable_thinking = None
            if request.enableThinking is not None:
                enable_thinking = bool(request.enableThinking)
            elif is_qwen3_model:
                # 默认不开启 Qwen3 的 thinking，避免响应过慢
                enable_thinking = False
            if enable_thinking is not None:
                data["enable_thinking"] = enable_thinking
            
            # 使用降级处理器执行请求
            fallback_handler = get_fallback_handler()
            
            # 检查是否启用降级（可通过环境变量控制）
            use_fallback = os.getenv("USE_FALLBACK", "true").lower() == "true"
            
            if use_fallback and agent_role:
                try:
                    result, metrics = await fallback_handler.execute_with_fallback(
                        client=client,
                        url=API_ENDPOINTS["siliconflow"],
                        headers=headers,
                        data=data,
                        agent_role=agent_role,
                        max_retries=4
                    )
                    
                    # 记录指标
                    total_time = time.time() - request._start_time
                    print(f"[SiliconFlow] [{req_time}] 🏁 请求完成")
                    print(f"  - 总耗时: {total_time:.1f}秒")
                    print(f"  - 最终状态: {metrics.final_status}")
                    print(f"  - 尝试次数: {len(metrics.attempt_times)}")
                    
                    # 仅在实际发生降级（压缩或默认响应）时打印提示日志
                    fallback_level = result.get("fallback_level", 0)
                    if fallback_level and fallback_level > 0:
                        level_name = {
                            1: "轻度压缩",
                            2: "深度压缩",
                            3: "最小化",
                            99: "默认响应"
                        }.get(fallback_level, f"级别{fallback_level}")
                        print(f"[SiliconFlow] 使用降级处理器 (角色: {agent_role}, 级别: {fallback_level}, 模式: {level_name})")
                    
                    if metrics.final_status.startswith("success"):
                        print(f"  - ✅ 成功")
                    elif "cached" in metrics.final_status:
                        print(f"  - ⚡ 使用缓存")
                    elif "default" in metrics.final_status:
                        print(f"  - ⚠️ 使用默认响应")
                        
                    # 提取响应文本
                    text = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                    usage = result.get("usage", {})
                    
                    return {
                        "success": True,
                        "text": text,
                        "usage": usage,
                        "fallback_level": result.get("fallback_level", 0),
                        "metrics": {
                            "total_time": total_time,
                            "attempts": len(metrics.attempt_times),
                            "final_status": metrics.final_status
                        }
                    }
                    
                except Exception as e:
                    print(f"[SiliconFlow] 降级处理器错误: {e}")
                    # 降级处理器失败，使用原有逻辑
                    pass
            
            # 原有重试逻辑（作为后备）
            if not agent_role:
                # 从请求中尝试推断角色（analyze请求可能传递了agent_id）
                agent_role = "GENERAL"  # 通用请求
                print(f"[SiliconFlow] 通用请求（未指定角色）")
            
            print(f"[SiliconFlow] 使用原有重试逻辑（agent_role={agent_role}）")
            max_retries = 2
            response = None
            
            for attempt in range(max_retries):
                try:
                    print(f"[SiliconFlow] {request.model} 尝试 {attempt+1}/{max_retries} [提示词长度: {len(request.prompt)}字符]")
                    
                    # 如果是重试，重新创建客户端
                    if attempt > 0:
                        if client:
                            await client.aclose()
                        print(f"[SiliconFlow] 重新建立连接...")
                        client = httpx.AsyncClient(
                            timeout=httpx.Timeout(
                                timeout=total_timeout,
                                connect=15.0,
                                read=read_timeout,
                                write=15.0,
                                pool=15.0
                            ),
                            limits=httpx.Limits(
                                max_connections=10,
                                max_keepalive_connections=5
                            )
                        )
                    
                    # 测试连接（小请求验证）
                    if attempt > 0:
                        print(f"[SiliconFlow] 测试连接...")
                        try:
                            test_response = await client.post(
                                API_ENDPOINTS["siliconflow"],
                                headers=headers,
                                json={
                                    "model": request.model,
                                    "messages": [{"role": "user", "content": "test"}],
                                    "max_tokens": 1,
                                    "stream": False
                                },
                                timeout=5.0  # 5秒快速测试
                            )
                            if test_response.status_code == 200:
                                print(f"[SiliconFlow] 连接测试成功")
                            else:
                                print(f"[SiliconFlow] 连接测试失败: HTTP {test_response.status_code}")
                        except Exception as test_e:
                            print(f"[SiliconFlow] 连接测试异常: {type(test_e).__name__}")
                    
                    # 发送实际请求
                    import time
                    start_time = time.time()
                    request_size_kb = len(str(data)) / 1024
                    prompt_tokens_est = len(request.prompt) / 2  # 粗略估算token数
                    print(f"[SiliconFlow] [{time.strftime('%H:%M:%S')}] 发送请求")
                    print(f"  - 提示词: {len(request.prompt)} 字符 (~{prompt_tokens_est:.0f} tokens)")
                    print(f"  - 请求体: {request_size_kb:.1f} KB")
                    print(f"  - 模型: {request.model}")
                    
                    response = await asyncio.wait_for(
                        client.post(
                            API_ENDPOINTS["siliconflow"],
                            headers=headers,
                            json=data
                        ),
                        timeout=120.0  # 单次调用整体超时120秒（原45秒），给足时间
                    )
                    
                    elapsed = time.time() - start_time
                    print(f"[SiliconFlow] [{time.strftime('%H:%M:%S')}] ✅ 响应成功")
                    print(f"  - API响应时间: {elapsed:.2f}秒")
                    print(f"  - 速度: {len(request.prompt)/elapsed:.0f} 字符/秒")
                    break  # 成功则跳出循环
                except (asyncio.TimeoutError, httpx.ReadTimeout, httpx.RemoteProtocolError, httpx.ConnectError, httpx.NetworkError) as e:
                    error_type = type(e).__name__
                    elapsed = time.time() - start_time if 'start_time' in locals() else 0
                    print(f"[SiliconFlow] [{time.strftime('%H:%M:%S')}] {error_type} 发生在 {elapsed:.1f}秒 错误: {str(e)[:200]}")

                    # 对超时类错误使用降级处理器的默认响应
                    if error_type in ["ReadTimeout", "TimeoutError"]:
                        print(f"[SiliconFlow] {error_type} 超时，使用降级默认响应")
                        # 使用降级处理器的默认响应
                        if not fallback_handler:
                            fallback_handler = get_fallback_handler()
                        
                        default_response = fallback_handler._get_default_response(
                            agent_role, 
                            f"超时错误: {error_type} (已等待{elapsed:.0f}秒)"
                        )
                        
                        # 返回默认响应而不是抛出异常
                        text = default_response['choices'][0]['message']['content']
                        print(f"[SiliconFlow] 返回默认响应: {text[:100]}...")
                        
                        return {
                            "success": True,
                            "text": text,
                            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                            "fallback_level": 99,  # 标记为默认响应
                            "timeout": True
                        }

                    # 仅对连接类错误保留一次重试
                    if attempt < max_retries - 1:
                        wait_time = 3 + (2 * attempt)  # 3s, 5s
                        print(f"[SiliconFlow] {error_type}，等待{wait_time}秒后重试 (尝试 {attempt + 2}/{max_retries})")

                        # 关闭旧连接
                        if client:
                            try:
                                await client.aclose()
                                print(f"[SiliconFlow] 已关闭旧连接")
                            except:
                                pass
                            client = None

                        await asyncio.sleep(wait_time)
                    else:
                        print(f"[SiliconFlow] 所有重试都失败 ({error_type})，返回降级响应")
                        return {
                            "success": True,
                            "text": f"⚠️ 由于网络波动，本次分析未能完成。建议：\n1. 检查网络连接\n2. 尝试使用其他 AI 模型\n3. 稍后重试",
                            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                            "timeout": True
                        }
                except Exception as e:
                    print(f"[SiliconFlow] 未知错误: {type(e).__name__}: {str(e)}")
                    if attempt < max_retries - 1:
                        wait_time = 3
                        print(f"[SiliconFlow] 等待{wait_time}秒后重试 (尝试 {attempt + 2}/{max_retries})")
                        
                        # 关闭旧连接
                        if client:
                            try:
                                await client.aclose()
                            except:
                                pass
                            client = None
                        
                        await asyncio.sleep(wait_time)
                    else:
                        print(f"[SiliconFlow] 所有重试都失败，返回降级响应")
                        return {
                            "success": True,
                            "text": f"⚠️ 分析过程中出现错误，请稍后重试。",
                            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                            "timeout": True
                        }
            
            # 如果所有重试都失败，返回降级响应
            if response is None:
                retry_summary = f"尝试了{max_retries}次，均失败"
                if hasattr(request, '_start_time'):
                    total_elapsed = time.time() - request._start_time
                    retry_summary += f"，总耗时{total_elapsed:.0f}秒"
                    
                print(f"[SiliconFlow] ❌ 所有重试失败: {retry_summary}")
                return {
                    "success": True,
                    "text": f"⚠️ AI服务暂时响应缓慢（{retry_summary}）。建议：\n1. 减少提示词长度\n2. 避免同时分析多个智能体\n3. 稍后再试",
                    "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                    "timeout": True
                }
            
            if response.status_code != 200:
                error_text = response.text
                print(f"[SiliconFlow] HTTP {response.status_code} 错误")
                print(f"[SiliconFlow] 响应内容: {error_text[:500]}")
                raise HTTPException(status_code=response.status_code, detail=f"SiliconFlow API 错误: {error_text[:200]}")
            
            result = response.json()
            text = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            # 获取token使用信息
            usage = result.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            total_tokens = usage.get("total_tokens", 0)
            
            # 计算总耗时
            import time
            if hasattr(request, '_start_time'):
                total_elapsed = time.time() - request._start_time
                print(f"[SiliconFlow] [{time.strftime('%H:%M:%S')}] 请求总耗时: {total_elapsed:.2f}秒")
            
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
            print(f"[SiliconFlow] ❌ 未知异常: {type(e).__name__}")
            traceback.print_exc()
            # 返回友好的降级响应而不是抛出异常
            return {
                "success": True,
                "text": f"⚠️ 分析服务暂时不可用，请稍后重试。错误类型: {type(e).__name__}",
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                "timeout": True
            }
        finally:
            # 关闭客户端
            if client:
                try:
                    await client.aclose()
                    print(f"[SiliconFlow] 已关闭HTTP客户端")
                except:
                    pass
            
            # 计算并输出总耗时
            if hasattr(request, '_start_time'):
                total_time = time.time() - request._start_time
                print(f"[SiliconFlow] [{time.strftime('%H:%M:%S')}] 🏁 请求结束，总耗时: {total_time:.1f}秒")
                if total_time > 30:
                    print(f"  ⚠️ 耗时过长，建议检查网络或API状态")

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

# ==================== 模型能力画像与静默压测 ====================

def get_calibration_settings() -> Dict[str, Any]:
    """从 agent_configs.json 读取模型能力画像与静默压测配置，并与默认值合并"""
    default_settings = {
        "enabled": False,
        "concurrency": [3, 5],
        "promptLengths": [4000, 6000, 8000],
        "maxTokens": 512,
        "enableThinking": False,
        "timeoutSeconds": 180
    }
    config_file = os.path.join(os.path.dirname(__file__), "agent_configs.json")
    if not os.path.exists(config_file):
        return default_settings
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            config_data = json.load(f)
        custom = config_data.get("calibrationSettings") or {}
        if isinstance(custom, dict):
            merged = default_settings.copy()
            merged.update(custom)
            return merged
    except Exception as e:
        print(f"[Calibration] 读取配置失败: {str(e)}")
    return default_settings


def build_calibration_models(override_models: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """根据 agent_configs.json 中的 selectedModels + summarizerModel 构建仅包含LLM的压测候选模型列表。

    如果传入 override_models，则优先使用与 selectedModels 的交集；若交集为空，则使用 override_models 本身。
    """
    config_file = os.path.join(os.path.dirname(__file__), "agent_configs.json")
    model_names: set[str] = set()
    if os.path.exists(config_file):
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                config_data = json.load(f)
            for name in config_data.get("selectedModels", []):
                if isinstance(name, str) and name.strip():
                    model_names.add(name.strip())
            summarizer = config_data.get("summarizerModel")
            if isinstance(summarizer, str) and summarizer.strip():
                model_names.add(summarizer.strip())
        except Exception as e:
            print(f"[Calibration] 读取 agent_configs 失败: {str(e)}")

    # 如果调用方传入 models，则与现有列表取交集；交集为空时退化为使用传入列表
    if override_models:
        override_set = {m.strip() for m in override_models if isinstance(m, str) and m.strip()}
        if override_set:
            intersection = model_names & override_set
            model_names = intersection or override_set

    if not model_names:
        return []

    vision_keywords = ["stable-diffusion", "sdxl", "flux", "playground", "dall-e", "midjourney"]
    embed_keywords = ["embedding", "bge", "jina-embed", "text-embedding"]
    audio_keywords = ["whisper", "speech", "audio", "voice", "bark"]

    models: List[Dict[str, Any]] = []
    for name in sorted(model_names):
        if not isinstance(name, str) or not name.strip():
            continue
        lower = name.lower()

        # 过滤掉非LLM模型
        model_type = "llm"
        if any(k in lower for k in vision_keywords):
            model_type = "vision"
        elif any(k in lower for k in embed_keywords):
            model_type = "embedding"
        elif any(k in lower for k in audio_keywords):
            model_type = "audio"
        if model_type != "llm":
            continue

        provider = "UNKNOWN"
        channel = None
        if "/" in name:
            # 带斜杠的一律视为硅基流动托管模型
            channel = "硅基流动"
            if "qwen" in lower:
                provider = "QWEN"
            elif "llama" in lower:
                provider = "LLAMA"
            elif "deepseek" in lower:
                provider = "DEEPSEEK"
            elif "mistral" in lower:
                provider = "MISTRAL"
            elif "yi-" in lower or "/yi" in lower:
                provider = "YI"
            elif "glm" in lower or "chatglm" in lower:
                provider = "GLM"
            elif "gemma" in lower:
                provider = "GEMMA"
            elif "baichuan" in lower:
                provider = "BAICHUAN"
            elif "internlm" in lower:
                provider = "INTERNLM"
            elif "phi" in lower:
                provider = "PHI"
        else:
            # 官方直连模型
            if name.startswith("gemini"):
                provider = "GEMINI"
                channel = "Google"
            elif name in ["deepseek-chat", "deepseek-coder", "deepseek-reasoner"]:
                provider = "DEEPSEEK"
                channel = "DeepSeek"
            elif name in [
                "qwen-max",
                "qwen-max-longcontext",
                "qwen-plus",
                "qwen-turbo",
                "qwen-turbo-latest",
                "qwen2.5-72b-instruct",
                "qwen2.5-32b-instruct",
                "qwen2.5-14b-instruct",
                "qwen2.5-7b-instruct",
                "qwen2.5-3b-instruct",
                "qwen2.5-coder-32b-instruct",
                "qwen2.5-coder-7b-instruct",
            ]:
                provider = "QWEN"
                channel = "阿里云"

        models.append({
            "name": name,
            "provider": provider,
            "channel": channel,
            "type": "llm"
        })

    return models


async def _run_single_calibration_test(model: Dict[str, Any], prompt_length: int, settings: Dict[str, Any], timeout_seconds: int, sem: asyncio.Semaphore, concurrency: int):
    """对单个模型和单个prompt长度执行一次静默压测，返回测试结果记录。

    Args:
        model: 模型信息字典
        prompt_length: 提示词长度（字符数）
        settings: 压测配置（包含 maxTokens / enableThinking 等）
        timeout_seconds: 单次调用超时时间
        sem: 控制并发的信号量
        concurrency: 本轮压测目标并发数，用于记录到结果中
    """
    name = model.get("name") or ""
    provider = (model.get("provider") or "").upper() or "UNKNOWN"
    channel = model.get("channel")

    # 构造指定长度的测试提示词
    base = "这是一段用于模型能力画像与静默压测的测试文本。"
    repeat = max(1, int(prompt_length / max(len(base), 1)) + 1)
    user_prompt = (base * repeat)[: max(10, prompt_length)]
    system_prompt = "你是一个中文大语言模型性能测试助手，请针对用户输入给出简短、有意义的回答。"

    max_tokens = int(settings.get("maxTokens", 512) or 512)
    enable_thinking = bool(settings.get("enableThinking", False))

    started_at = datetime.utcnow().isoformat()
    start_time = asyncio.get_event_loop().time()
    success = False
    timeout_flag = False
    error_msg = None
    usage = {}
    conc_value = concurrency if isinstance(concurrency, int) and concurrency > 0 else None

    async with sem:
        try:
            # 根据名称/提供方推断实际调用的provider
            effective_provider = "SILICONFLOW"
            if "/" not in name:
                if name.startswith("gemini"):
                    effective_provider = "GEMINI"
                elif name in ["deepseek-chat", "deepseek-coder", "deepseek-reasoner"]:
                    effective_provider = "DEEPSEEK"
                elif name in [
                    "qwen-max",
                    "qwen-max-longcontext",
                    "qwen-plus",
                    "qwen-turbo",
                    "qwen-turbo-latest",
                    "qwen2.5-72b-instruct",
                    "qwen2.5-32b-instruct",
                    "qwen2.5-14b-instruct",
                    "qwen2.5-7b-instruct",
                    "qwen2.5-3b-instruct",
                    "qwen2.5-coder-32b-instruct",
                    "qwen2.5-coder-7b-instruct",
                ]:
                    effective_provider = "QWEN"

            result: Dict[str, Any] = {"success": False}

            if effective_provider == "GEMINI":
                req = GeminiRequest(
                    model=name,
                    prompt=user_prompt,
                    temperature=0.5
                )
                result = await asyncio.wait_for(gemini_api(req), timeout=timeout_seconds)
            elif effective_provider == "DEEPSEEK":
                req = DeepSeekRequest(
                    model=name,
                    systemPrompt=system_prompt,
                    prompt=user_prompt,
                    temperature=0.5
                )
                result = await asyncio.wait_for(deepseek_api(req), timeout=timeout_seconds)
            elif effective_provider == "QWEN":
                req = QwenRequest(
                    model=name,
                    systemPrompt=system_prompt,
                    prompt=user_prompt,
                    temperature=0.5
                )
                result = await asyncio.wait_for(qwen_api(req), timeout=timeout_seconds)
            else:
                # 默认通过硅基流动调用
                req = SiliconFlowRequest(
                    model=name,
                    systemPrompt=system_prompt,
                    prompt=user_prompt,
                    temperature=0.5,
                    maxTokens=max_tokens,
                    enableThinking=enable_thinking,
                    agentRole="BENCHMARK"  # 压测角色
                )
                result = await asyncio.wait_for(siliconflow_api(req), timeout=timeout_seconds)

            success = bool(result.get("success"))
            usage = result.get("usage") or {}
            timeout_flag = bool(result.get("timeout", False))
        except asyncio.TimeoutError:
            timeout_flag = True
            error_msg = f"Timeout({timeout_seconds}s)"
        except Exception as e:
            error_msg = str(e)

    finished_at = datetime.utcnow().isoformat()
    latency = asyncio.get_event_loop().time() - start_time

    return {
        "modelName": name,
        "provider": provider or "UNKNOWN",
        "channel": channel,
        "promptLength": int(prompt_length),
        "maxTokens": max_tokens,
        "enableThinking": enable_thinking,
        "concurrency": conc_value,
        "startedAt": started_at,
        "finishedAt": finished_at,
        "latencySeconds": round(latency, 2),
        "success": success,
        "timeout": timeout_flag,
        "error": error_msg,
        "usage": usage,
    }


async def run_calibration_once(settings: Dict[str, Any], models: List[Dict[str, Any]]):
    """执行一次完整的模型能力画像与静默压测（仅针对LLM）。"""
    global calibration_state

    prompt_lengths = settings.get("promptLengths") or [4000, 6000, 8000]
    try:
        prompt_lengths = [int(x) for x in prompt_lengths if int(x) > 0]
    except Exception:
        prompt_lengths = [4000, 6000, 8000]

    raw_concurrency = settings.get("concurrency")
    concurrency_list: List[int] = []
    if isinstance(raw_concurrency, list):
        for v in raw_concurrency:
            try:
                iv = int(v)
                if iv > 0:
                    concurrency_list.append(iv)
            except Exception:
                continue
    elif raw_concurrency is not None:
        try:
            iv = int(raw_concurrency)
            if iv > 0:
                concurrency_list.append(iv)
        except Exception:
            pass

    if not concurrency_list:
        concurrency_list = [3]

    # 去重并限制在 1-5 之间
    concurrency_list = sorted({max(1, min(int(v), 5)) for v in concurrency_list})

    timeout_seconds = int(settings.get("timeoutSeconds", 180) or 180)
    if timeout_seconds <= 0:
        timeout_seconds = 180

    print(f"[Calibration] 开始静默压测: 模型数={len(models)}, 并发列表={concurrency_list}, prompt长度={prompt_lengths}, timeout={timeout_seconds}s")

    # 初始化结果结构
    results: Dict[str, Any] = {}
    for m in models:
        name = m.get("name")
        if not name:
            continue
        results[name] = {
            "provider": (m.get("provider") or "UNKNOWN").upper(),
            "channel": m.get("channel"),
            "tests": []
        }

    try:
        # 按不同并发值依次压测，将结果追加到同一 tests 列表中
        for conc in concurrency_list:
            sem = asyncio.Semaphore(conc)
            tasks = []
            for m in models:
                name = m.get("name")
                if not name:
                    continue
                for length in prompt_lengths:
                    tasks.append(
                        _run_single_calibration_test(
                            m,
                            length,
                            settings,
                            timeout_seconds,
                            sem,
                            conc,
                        )
                    )

            test_records = await asyncio.gather(*tasks, return_exceptions=True)
            for record in test_records:
                if isinstance(record, Exception) or not isinstance(record, dict):
                    continue
                model_name = record.get("modelName")
                if not model_name or model_name not in results:
                    continue
                results[model_name]["tests"].append(record)

        calibration_state["status"] = "completed"
        calibration_state["error"] = None
        calibration_state["results"] = results
        save_calibration_state()
        print(f"[Calibration] 静默压测完成，共 {len(results)} 个模型")
    except Exception as e:
        calibration_state["status"] = "error"
        calibration_state["error"] = str(e)
        save_calibration_state()
        print(f"[Calibration] 静默压测失败: {str(e)}")


@app.post("/api/models/calibration/run")
async def start_model_calibration(request: CalibrationRunRequest):
    """触发一次模型能力画像与静默压测（仅针对LLM）。"""
    global calibration_state

    if calibration_state.get("status") == "running":
        return {"success": False, "error": "已有压测任务在运行，请稍后再试"}

    # 合并配置：以 agent_configs.json 为基础，request.calibrationSettings 为覆盖
    base_settings = get_calibration_settings()
    override = request.calibrationSettings or {}
    if isinstance(override, dict):
        base_settings.update(override)

    models = build_calibration_models(request.models)
    if not models:
        calibration_state["status"] = "idle"
        calibration_state["error"] = None
        calibration_state["results"] = {}
        save_calibration_state()
        return {"success": False, "error": "没有可用于压测的模型，请先在模型管理中选择大语言模型"}

    now_iso = datetime.utcnow().isoformat()
    calibration_state["status"] = "running"
    calibration_state["lastRunAt"] = now_iso
    calibration_state["error"] = None
    calibration_state["results"] = {}
    calibration_state["settings"] = base_settings
    save_calibration_state()

    # 异步启动压测任务
    asyncio.create_task(run_calibration_once(base_settings, models))

    return {
        "success": True,
        "message": f"已启动模型能力画像与静默压测，共 {len(models)} 个模型",
        "startedAt": now_iso
    }


@app.get("/api/models/calibration/status")
async def get_model_calibration_status():
    """查询当前模型能力画像与静默压测的状态和最近一次结果。"""
    # 直接返回内存中的状态，前端可根据需要解析 results/tests
    total_models = len(calibration_state.get("results") or {})
    return {
        "success": True,
        "data": {
            **calibration_state,
            "totalModels": total_models
        }
    }


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

"""
修复后的 analyze_stock 函数
请复制此函数替换 server.py 中的 analyze_stock 函数（从第704行开始）
"""

def get_summarizer_settings():
    config_file = os.path.join(os.path.dirname(__file__), "agent_configs.json")
    default_settings = {
        "modelName": "Qwen/Qwen2.5-7B-Instruct",
        "temperature": 0.2
    }
    if not os.path.exists(config_file):
        return default_settings
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        model_name = config_data.get("summarizerModel")
        temperature = config_data.get("summarizerTemperature", 0.2)
        if not model_name:
            return default_settings
        return {
            "modelName": model_name,
            "temperature": temperature
        }
    except Exception:
        return default_settings

async def summarize_previous_outputs(agent_id: str, previous_outputs: Optional[Dict[str, Any]], stock_code: str) -> str:
    texts = []
    if not previous_outputs:
        return ""
    for agent_name, output in previous_outputs.items():
        if output:
            role = get_agent_role(agent_name)
            texts.append(f"{role}（{agent_name}）的结论:\n{output}")
    if not texts:
        return ""
    combined_text = "\n\n".join(texts)
    system_prompt = "你是一个专业的投研团队助理，擅长阅读多位分析师的观点并提炼要点。"
    user_prompt = (
        f"下面是关于股票 {stock_code} 的多位分析师完整分析，请在保留关键信息的前提下进行压缩整理：\n\n"
        "1. 用分点方式归纳出全局核心结论（最多 6 点）。\n"
        "2. 突出重大利好/利空、关键风险和不确定性。\n"
        "3. 输出长度控制在 1200-1500 字以内。\n\n"
        "【分析原文】\n" + combined_text
    )
    settings = get_summarizer_settings()
    model_name = settings.get("modelName", "Qwen/Qwen2.5-7B-Instruct")
    temperature = settings.get("temperature", 0.2)
    provider = "SILICONFLOW"
    # 仅当模型名不包含"/"且明显是官方 DeepSeek 直连型号时，才走 deepseek_api
    # 否则（包括 SiliconFlow deepseek-* 模型）统一通过 SiliconFlow 渠道调用
    if "/" not in model_name:
        lower_name = model_name.lower()
        if model_name.startswith("gemini"):
            provider = "GEMINI"
        elif lower_name.startswith("deepseek-") or lower_name in ["deepseek-chat", "deepseek-coder", "deepseek-reasoner"]:
            provider = "DEEPSEEK"
    try:
        if provider == "GEMINI":
            req = GeminiRequest(
                model=model_name,
                prompt=system_prompt + "\n\n" + user_prompt,
                temperature=temperature
            )
            result = await gemini_api(req)
        elif provider == "DEEPSEEK":
            req = DeepSeekRequest(
                model=model_name,
                systemPrompt=system_prompt,
                prompt=user_prompt,
                temperature=temperature
            )
            result = await deepseek_api(req)
        else:
            req = SiliconFlowRequest(
                model=model_name,
                systemPrompt=system_prompt,
                prompt=user_prompt,
                temperature=temperature,
                agentRole="SUMMARIZER"  # 摘要器角色
            )
            result = await siliconflow_api(req)
    except Exception:
        result = {"success": False}
    if result.get("success"):
        text = result.get("text") or ""
        if text:
            return text
    return combined_text[:2000]

@app.post("/api/analyze")
async def analyze_stock(request: AnalyzeRequest):
    """统一的智能体分析接口"""
    try:
        print(f"[分析] {request.agent_id} 开始分析...")
        agent_id = request.agent_id
        stock_code = request.stock_code
        stock_data = request.stock_data
        previous_outputs = request.previous_outputs
        custom_instruction = request.custom_instruction
        
        # 从缓存获取配置
        agent_config = get_agent_config(agent_id)
        
        # 如果没有找到配置，使用默认值（使用SiliconFlow避免余额问题）
        if not agent_config:
            agent_config = {
                "modelName": "Qwen/Qwen2.5-7B-Instruct",  # 默认使用SiliconFlow的通义千问
                "modelProvider": "SILICONFLOW",
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
        system_prompt = f"你是一个专业的{role_name}，隶属于InvestMindPro顶级投研团队。你的目标是提供深度、犀利且独到的投资见解。"
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
        
        # 重点：前序分析结果（使用完整内容）
        summary_text = None
        if previous_outputs and len(previous_outputs) > 0:
            total_prev_len_for_summary = sum(len(str(output)) for output in previous_outputs.values() if output)
            if total_prev_len_for_summary > 3000:
                summary_text = await summarize_previous_outputs(agent_id, previous_outputs, stock_code)

        if previous_outputs and len(previous_outputs) > 0:
            if summary_text:
                user_prompt += "\n【团队成员已完成的分析摘要】(请基于此进行深化，不要重复)\n"
                user_prompt += summary_text + "\n\n"
            else:
                user_prompt += "\n【团队成员已完成的分析】(请基于此进行深化，不要重复)\n"
                for agent_name, output in previous_outputs.items():
                    if output:
                        user_prompt += f">>> {get_agent_role(agent_name)} 的结论:\n{output}\n\n"
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
            # 获取智能体角色（用于降级策略）
            agent_role_map = {
                'news_analyst': 'NEWS',
                'fundamental': 'FUNDAMENTAL',
                'technical': 'TECHNICAL',
                'bull_researcher': 'BULL',
                'bear_researcher': 'BEAR',
                'risk_manager': 'RISK',
                'risk_aggressive': 'RISK',
                'risk_conservative': 'RISK',
                'risk_neutral': 'RISK',
                'research_manager': 'MANAGER',
                'trader': 'TRADER',
                'macro': 'MACRO',
                'industry': 'INDUSTRY',
                'funds': 'FUNDAMENTAL',
                'manager_fundamental': 'MANAGER',
                'manager_momentum': 'MANAGER',
                'risk_system': 'RISK',
                'risk_portfolio': 'RISK',
                'gm': 'MANAGER',
                'china_market': 'NEWS',
                'social_analyst': 'NEWS'
            }
            
            req = SiliconFlowRequest(
                model=model_name,
                systemPrompt=system_prompt,
                prompt=user_prompt,
                temperature=temperature,
                agentRole=agent_role_map.get(request.agent_id, 'UNKNOWN')  # 添加智能体角色
            )
            # 添加详细日志
            prompt_len = len(system_prompt) + len(user_prompt)
            print(f"[分析] {request.agent_id} 系统提示词: {len(system_prompt)} 字符")
            print(f"[分析] {request.agent_id} 用户提示词: {len(user_prompt)} 字符")
            print(f"[分析] {request.agent_id} 总长度: {prompt_len} 字符 (~{prompt_len//2} tokens)")
            print(f"[分析] {request.agent_id} 降级角色: {req.agentRole}")  # 显示降级角色
            
            # 打印前序输出长度
            if previous_outputs:
                print(f"[分析] {request.agent_id} 前序输出数量: {len(previous_outputs)}")
                total_prev_len = sum(len(output) for output in previous_outputs.values() if output)
                print(f"[分析] {request.agent_id} 前序输出总长度: {total_prev_len} 字符")
                for agent_name, output in list(previous_outputs.items())[:3]:  # 只打印前3个
                    if output:
                        print(f"  - {agent_name}: {len(output)} 字符")
                if len(previous_outputs) > 3:
                    print(f"  ... 还有 {len(previous_outputs)-3} 个")
            
            print(f"[分析] {request.agent_id} 调用SiliconFlow API: {model_name}")
            result = await siliconflow_api(req)
        
        if result.get("success"):
            print(f"[分析] {request.agent_id} 分析完成")
            # 始终返回 fallback_level，默认为 0（原始请求）
            fallback_level = result.get("fallback_level", 0)
            return {
                "success": True,
                "result": result.get("text", ""),
                "fallback_level": fallback_level
            }
        else:
            print(f"[分析] {request.agent_id} 分析失败: {result.get('error')}")
            return {"success": False, "error": result.get("error", "分析失败")}
            
    except Exception as e:
        import traceback
        print(f"[Analyze] {request.agent_id} 错误: {str(e)}")
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
@app.get("/api/stock/{symbol}")
async def stock_data(symbol: str, request: Optional[StockRequest] = None):
    """股票数据API - 优化版AKShare优先"""
    try:
        # 使用优化后的适配器
        from backend.dataflows.stock_data_adapter_optimized import StockDataAdapter
        
        print(f"[Stock API] 开始获取{symbol}的数据...")
        print(f"[Stock API] 使用优化的AKShare接口")
        
        # 使用适配器获取数据
        adapter = StockDataAdapter()
        # 调用异步方法
        result = await adapter.get_stock_data_async(symbol)
        
        print(f"[Stock API] 成功使用数据源: {result.get('data_source')}")
        print(f"[Stock API] 结果: {result.get('name')} 价格=¥{result.get('price')} 涨跌幅={result.get('change')}%")
        
        return result
    
    except Exception as e:
        import traceback
        print(f"[Stock API] ❌ 错误: {str(e)}")
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

    # 添加巨潮API配置（使用官方命名：Access Key, Access Secret, Access Token）
    if API_KEYS.get("cninfo_access_key"):
        config["api_keys"]["cninfo_access_key"] = API_KEYS["cninfo_access_key"]
        config["CNINFO_ACCESS_KEY"] = API_KEYS["cninfo_access_key"]
    if API_KEYS.get("cninfo_access_secret"):
        config["api_keys"]["cninfo_access_secret"] = API_KEYS["cninfo_access_secret"]
        config["CNINFO_ACCESS_SECRET"] = API_KEYS["cninfo_access_secret"]
    if API_KEYS.get("cninfo_access_token"):
        config["api_keys"]["cninfo_access_token"] = API_KEYS["cninfo_access_token"]
        config["CNINFO_ACCESS_TOKEN"] = API_KEYS["cninfo_access_token"]

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
        summarizer = config_data.get('summarizerModel', 'N/A')
        print(f"[配置] 已保存 {agent_count} 个智能体配置和 {model_count} 个模型选择")
        print(f"[配置] 摘要器模型: {summarizer}")
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


async def _check_tushare_points(pro) -> dict:
    """
    检测 Tushare Token 的积分权限

    通过测试各接口来估算账户积分等级

    Returns:
        dict: {'summary': '积分摘要', 'details': '详细信息', 'estimated_points': 积分数}
    """
    from datetime import datetime, timedelta
    import asyncio

    # 定义要检测的接口及其所需积分
    interfaces = {
        'stock_basic': {'points': 0, 'desc': '股票列表', 'group': '基础'},
        'daily': {'points': 0, 'desc': '日线行情', 'group': '基础'},
        'daily_basic': {'points': 120, 'desc': '每日指标', 'group': '进阶'},
        'income': {'points': 500, 'desc': '利润表', 'group': '财务'},
        'fina_indicator': {'points': 500, 'desc': '财务指标', 'group': '财务'},
        'pledge_detail': {'points': 2000, 'desc': '质押明细', 'group': '高级'},
        'stk_holdertrade': {'points': 2000, 'desc': '股东增减持', 'group': '高级'},
        'top_inst': {'points': 2000, 'desc': '机构龙虎榜', 'group': '高级'},
        'stk_rewards': {'points': 5000, 'desc': '管理层薪酬', 'group': 'VIP'},
    }

    results = {}
    today = datetime.now().strftime('%Y%m%d')
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')

    def test_interface(interface):
        """同步测试单个接口"""
        try:
            if interface == 'stock_basic':
                data = pro.stock_basic(list_status='L', limit=1)
            elif interface == 'daily':
                data = pro.daily(ts_code='000001.SZ', start_date=yesterday, end_date=today)
            elif interface == 'daily_basic':
                data = pro.daily_basic(trade_date=yesterday, limit=1)
            elif interface in ['income', 'fina_indicator']:
                data = getattr(pro, interface)(ts_code='000001.SZ', limit=1)
            elif interface == 'pledge_detail':
                data = pro.pledge_detail(ts_code='000001.SZ')
            elif interface == 'stk_holdertrade':
                data = pro.stk_holdertrade(ts_code='000001.SZ', start_date='20240101', end_date=today)
            elif interface == 'top_inst':
                data = pro.top_inst(trade_date=yesterday)
            elif interface == 'stk_rewards':
                data = pro.stk_rewards(ts_code='000001.SZ', end_date='20231231')
            else:
                data = None

            return data is not None and (not hasattr(data, 'empty') or not data.empty)
        except Exception as e:
            error_msg = str(e).lower()
            # 积分不足或权限不足
            if '积分' in error_msg or 'point' in error_msg or '权限' in error_msg:
                return False
            # 其他错误（如网络问题）也视为不可用
            return False

    # 在线程池中并行测试接口
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_interface = {
            executor.submit(test_interface, interface): interface
            for interface in interfaces.keys()
        }
        for future in concurrent.futures.as_completed(future_to_interface):
            interface = future_to_interface[future]
            try:
                results[interface] = future.result()
            except Exception:
                results[interface] = False

    # 统计结果
    available_count = sum(1 for v in results.values() if v)
    total_count = len(results)

    # 估算积分
    estimated_points = 0
    for interface, available in results.items():
        if available:
            estimated_points = max(estimated_points, interfaces[interface]['points'])

    # 生成详细信息
    details_lines = []
    groups = {'基础': [], '进阶': [], '财务': [], '高级': [], 'VIP': []}

    for interface, info in interfaces.items():
        status = '✅' if results.get(interface) else '❌'
        groups[info['group']].append(f"  {status} {info['desc']} ({info['points']}分)")

    for group_name, items in groups.items():
        if items:
            details_lines.append(f"【{group_name}接口】")
            details_lines.extend(items)

    # 生成摘要
    if estimated_points >= 5000:
        level = "VIP会员 (5000+积分)"
        level_emoji = "👑"
    elif estimated_points >= 2000:
        level = "高级会员 (2000+积分)"
        level_emoji = "⭐"
    elif estimated_points >= 500:
        level = "标准会员 (500+积分)"
        level_emoji = "📊"
    elif estimated_points >= 120:
        level = "进阶会员 (120+积分)"
        level_emoji = "📈"
    else:
        level = "基础会员 (0积分)"
        level_emoji = "📋"

    summary = f"{level_emoji} 账户等级: {level}\n📊 接口可用: {available_count}/{total_count}"

    return {
        'summary': summary,
        'details': '\n'.join(details_lines),
        'estimated_points': estimated_points,
        'available_count': available_count,
        'total_count': total_count
    }


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
            # 测试 Tushare API 并检测积分
            try:
                import tushare as ts
                ts.set_token(api_key)
                pro = ts.pro_api()

                # 测试基础接口
                df = pro.trade_cal(exchange='SSE', start_date='20240101', end_date='20240110')
                if df is None or len(df) == 0:
                    return {"success": False, "error": "无法获取数据，Token 可能无效"}

                # 检测各接口权限来估算积分
                points_info = await _check_tushare_points(pro)

                return {
                    "success": True,
                    "message": f"Tushare API 连接成功！",
                    "test_response": f"Token 有效 ✅\n\n{points_info['summary']}\n\n接口权限详情:\n{points_info['details']}"
                }
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
@app.get("/api/health")
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
