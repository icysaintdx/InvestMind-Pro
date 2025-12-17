"""
交易系统LLM配置API
专门用于回测、策略选择、模拟交易等新功能的LLM配置
与智能分析的21个智能体配置完全独立
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import json
from pathlib import Path

from backend.utils.logging_config import get_logger

logger = get_logger("api.trading_llm_config")
router = APIRouter(prefix="/api/trading-llm-config", tags=["Trading LLM Configuration"])


# ==================== 数据模型 ====================

class TradingLLMConfig(BaseModel):
    """交易LLM配置"""
    task_name: str = Field(..., description="任务名称")
    display_name: str = Field(..., description="显示名称")
    description: str = Field(..., description="功能描述")
    provider: str = Field("deepseek", description="LLM提供商")
    model: str = Field("deepseek-chat", description="模型名称")
    temperature: float = Field(0.7, ge=0, le=2, description="温度参数")
    max_tokens: int = Field(2000, gt=0, description="最大tokens")
    timeout: int = Field(60, gt=0, description="超时时间（秒）")
    enabled: bool = Field(True, description="是否启用")


class ConfigUpdateRequest(BaseModel):
    """配置更新请求"""
    provider: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = Field(None, ge=0, le=2)
    max_tokens: Optional[int] = Field(None, gt=0)
    timeout: Optional[int] = Field(None, gt=0)
    enabled: Optional[bool] = None


# ==================== 配置存储 ====================

CONFIG_FILE = Path("backend/data/trading_llm_config.json")

# 默认配置（简化为3个核心任务）
DEFAULT_CONFIGS = {
    "strategy_selector": {
        "task_name": "strategy_selector",
        "display_name": "策略选择器",
        "description": "根据分析结果，LLM推荐最适合的交易策略",
        "provider": "deepseek",
        "model": "deepseek-chat",
        "temperature": 0.7,
        "max_tokens": 2000,
        "timeout": 60,
        "enabled": True
    },
    "trade_decision": {
        "task_name": "trade_decision",
        "display_name": "交易决策器",
        "description": "分析市场情况，LLM决定买入/卖出/持有",
        "provider": "deepseek",
        "model": "deepseek-chat",
        "temperature": 0.6,
        "max_tokens": 1500,
        "timeout": 60,
        "enabled": True
    },
    "market_analyzer": {
        "task_name": "market_analyzer",
        "display_name": "市场分析器",
        "description": "持续跟踪时，分析最新行情和新闻",
        "provider": "deepseek",
        "model": "deepseek-chat",
        "temperature": 0.7,
        "max_tokens": 2000,
        "timeout": 60,
        "enabled": True
    }
}


def load_configs() -> Dict[str, Dict]:
    """加载配置"""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载配置失败: {e}")
            return DEFAULT_CONFIGS.copy()
    else:
        return DEFAULT_CONFIGS.copy()


def save_configs(configs: Dict[str, Dict]):
    """保存配置"""
    try:
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(configs, f, ensure_ascii=False, indent=2)
        logger.info("配置已保存")
    except Exception as e:
        logger.error(f"保存配置失败: {e}")
        raise


# ==================== API端点 ====================

@router.get("/tasks")
async def get_all_tasks():
    """
    获取所有交易LLM任务配置
    
    Returns:
        所有任务的配置信息
    """
    try:
        configs = load_configs()
        
        tasks = []
        for task_name, config in configs.items():
            tasks.append({
                "task_name": config["task_name"],
                "display_name": config["display_name"],
                "description": config["description"],
                "provider": config["provider"],
                "model": config["model"],
                "temperature": config["temperature"],
                "max_tokens": config["max_tokens"],
                "timeout": config["timeout"],
                "enabled": config["enabled"],
                "category": "trading"  # 标记为交易类别
            })
        
        return {
            "success": True,
            "count": len(tasks),
            "tasks": tasks
        }
    except Exception as e:
        logger.error(f"获取任务配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/{task_name}")
async def get_task_config(task_name: str):
    """
    获取特定任务的配置
    
    Args:
        task_name: 任务名称
        
    Returns:
        任务配置详情
    """
    try:
        configs = load_configs()
        
        if task_name not in configs:
            raise HTTPException(status_code=404, detail=f"任务 {task_name} 不存在")
        
        config = configs[task_name]
        
        return {
            "success": True,
            "task_name": task_name,
            "config": config
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取任务配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/tasks/{task_name}")
async def update_task_config(task_name: str, updates: ConfigUpdateRequest):
    """
    更新任务配置
    
    Args:
        task_name: 任务名称
        updates: 要更新的配置项
        
    Returns:
        更新结果
    """
    try:
        configs = load_configs()
        
        if task_name not in configs:
            raise HTTPException(status_code=404, detail=f"任务 {task_name} 不存在")
        
        # 更新配置
        config = configs[task_name]
        
        if updates.provider is not None:
            config["provider"] = updates.provider
        if updates.model is not None:
            config["model"] = updates.model
        if updates.temperature is not None:
            config["temperature"] = updates.temperature
        if updates.max_tokens is not None:
            config["max_tokens"] = updates.max_tokens
        if updates.timeout is not None:
            config["timeout"] = updates.timeout
        if updates.enabled is not None:
            config["enabled"] = updates.enabled
        
        # 保存配置
        save_configs(configs)
        
        logger.info(f"任务 {task_name} 配置已更新")
        
        return {
            "success": True,
            "message": f"任务 {task_name} 配置已更新",
            "config": config
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新任务配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks/{task_name}/reset")
async def reset_task_config(task_name: str):
    """
    重置任务配置为默认值
    
    Args:
        task_name: 任务名称
        
    Returns:
        重置结果
    """
    try:
        if task_name not in DEFAULT_CONFIGS:
            raise HTTPException(status_code=404, detail=f"任务 {task_name} 不存在")
        
        configs = load_configs()
        configs[task_name] = DEFAULT_CONFIGS[task_name].copy()
        save_configs(configs)
        
        logger.info(f"任务 {task_name} 配置已重置")
        
        return {
            "success": True,
            "message": f"任务 {task_name} 配置已重置为默认值",
            "config": configs[task_name]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"重置任务配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/providers")
async def get_providers():
    """
    获取可用的LLM提供商列表
    
    Returns:
        提供商列表
    """
    return {
        "success": True,
        "providers": [
            {
                "id": "deepseek",
                "name": "DeepSeek",
                "models": ["deepseek-chat", "deepseek-coder"]
            },
            {
                "id": "siliconflow",
                "name": "SiliconFlow",
                "models": ["Qwen/Qwen2.5-7B-Instruct", "deepseek-ai/DeepSeek-V2.5"]
            },
            {
                "id": "qwen",
                "name": "通义千问",
                "models": ["qwen-turbo", "qwen-plus", "qwen-max"]
            },
            {
                "id": "gemini",
                "name": "Google Gemini",
                "models": ["gemini-pro", "gemini-1.5-pro"]
            }
        ]
    }


@router.post("/tasks/{task_name}/test")
async def test_task_llm(task_name: str):
    """
    测试任务的LLM配置是否正常工作

    Args:
        task_name: 任务名称

    Returns:
        测试结果
    """
    try:
        configs = load_configs()

        if task_name not in configs:
            raise HTTPException(status_code=404, detail=f"任务 {task_name} 不存在")

        config = configs[task_name]

        if not config.get("enabled", True):
            return {
                "success": False,
                "message": f"任务 {task_name} 已禁用",
                "config": config
            }

        # 真实调用LLM进行测试
        from backend.services.llm_service import get_llm_service

        llm = get_llm_service()

        # 构建测试提示词
        test_prompts = {
            "strategy_selector": "请简单回复：你是策略选择器，已准备就绪。",
            "trade_decision": "请简单回复：你是交易决策器，已准备就绪。",
            "market_analyzer": "请简单回复：你是市场分析器，已准备就绪。"
        }

        prompt = test_prompts.get(task_name, "请简单回复：测试成功。")

        import time
        start_time = time.time()

        result = await llm.call_llm(
            prompt=prompt,
            system_prompt="你是一个测试助手，请简短回复。",
            task_name=task_name,
            max_tokens=100,
            response_format="text"
        )

        elapsed_time = time.time() - start_time

        if result.get("success"):
            return {
                "success": True,
                "message": "LLM测试成功",
                "response": result.get("data", "")[:200],  # 截取前200字符
                "provider": result.get("provider"),
                "model": result.get("model"),
                "elapsed_time": round(elapsed_time, 2),
                "config": config
            }
        else:
            return {
                "success": False,
                "message": "LLM测试失败",
                "error": result.get("error", "未知错误"),
                "config": config
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"测试LLM失败: {e}")
        return {
            "success": False,
            "message": f"测试失败: {str(e)}",
            "error": str(e)
        }


# 获取配置的辅助函数（供其他模块使用）
def get_trading_llm_config(task_name: str) -> Dict[str, Any]:
    """
    获取交易LLM配置（供其他模块调用）

    Args:
        task_name: 任务名称

    Returns:
        配置字典
    """
    configs = load_configs()
    if task_name not in configs:
        logger.warning(f"任务 {task_name} 不存在，使用默认配置")
        return DEFAULT_CONFIGS.get(task_name, DEFAULT_CONFIGS["strategy_selector"])
    return configs[task_name]
