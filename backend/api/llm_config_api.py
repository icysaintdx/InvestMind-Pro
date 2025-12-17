"""
LLM配置管理API
提供LLM配置的查询和更新接口
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional

from backend.utils.logging_config import get_logger
from backend.utils.tool_logging import log_api_call

logger = get_logger("api.llm_config")
router = APIRouter(prefix="/api/llm-config", tags=["LLM Configuration"])


class TaskConfigUpdate(BaseModel):
    """任务配置更新请求"""
    provider: Optional[str] = Field(None, description="LLM提供商")
    model: Optional[str] = Field(None, description="模型名称")
    temperature: Optional[float] = Field(None, ge=0, le=2, description="温度参数")
    max_tokens: Optional[int] = Field(None, gt=0, description="最大tokens")
    timeout: Optional[int] = Field(None, gt=0, description="超时时间（秒）")
    enabled: Optional[bool] = Field(None, description="是否启用")


@router.get("/tasks")
@log_api_call("获取所有LLM任务配置")
async def get_all_tasks():
    """
    获取所有LLM任务配置
    
    Returns:
        所有任务的配置信息
    """
    try:
        from backend.services.llm.llm_config_manager import get_llm_config_manager
        
        manager = get_llm_config_manager()
        tasks = manager.get_all_tasks()
        
        return {
            "success": True,
            "count": len(tasks),
            "tasks": tasks
        }
    except Exception as e:
        logger.error(f"获取LLM任务配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/{task_name}")
@log_api_call("获取特定LLM任务配置")
async def get_task_config(task_name: str):
    """
    获取特定任务的配置
    
    Args:
        task_name: 任务名称
        
    Returns:
        任务配置详情
    """
    try:
        from backend.services.llm.llm_config_manager import get_llm_config_manager
        
        manager = get_llm_config_manager()
        task_config = manager.get_task_config(task_name)
        
        if task_config is None:
            raise HTTPException(status_code=404, detail=f"任务 {task_name} 不存在或已禁用")
        
        # 获取完整参数
        params = manager.get_llm_client_params(task_name)
        
        return {
            "success": True,
            "task_name": task_name,
            "config": task_config,
            "runtime_params": params
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取任务配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/tasks/{task_name}")
@log_api_call("更新LLM任务配置")
async def update_task_config(
    task_name: str,
    updates: TaskConfigUpdate
):
    """
    更新任务配置
    
    Args:
        task_name: 任务名称
        updates: 要更新的配置项
        
    Returns:
        更新结果
    """
    try:
        from backend.services.llm.llm_config_manager import get_llm_config_manager
        
        manager = get_llm_config_manager()
        
        # 构建更新字典（只包含非None的值）
        update_dict = {}
        if updates.provider is not None:
            update_dict["provider"] = updates.provider
        if updates.model is not None:
            update_dict["model"] = updates.model
        if updates.temperature is not None:
            update_dict["temperature"] = updates.temperature
        if updates.max_tokens is not None:
            update_dict["max_tokens"] = updates.max_tokens
        if updates.timeout is not None:
            update_dict["timeout"] = updates.timeout
        if updates.enabled is not None:
            update_dict["enabled"] = updates.enabled
        
        if not update_dict:
            raise HTTPException(status_code=400, detail="没有提供要更新的配置项")
        
        # 更新配置
        manager.update_task_config(task_name, update_dict, save=True)
        
        # 获取更新后的配置
        new_config = manager.get_task_config(task_name)
        
        return {
            "success": True,
            "message": f"任务 {task_name} 配置已更新",
            "task_name": task_name,
            "updated_fields": list(update_dict.keys()),
            "new_config": new_config
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新任务配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/providers")
@log_api_call("获取所有LLM提供商")
async def get_all_providers():
    """
    获取所有LLM提供商配置
    
    Returns:
        所有提供商的配置信息
    """
    try:
        from backend.services.llm.llm_config_manager import get_llm_config_manager
        
        manager = get_llm_config_manager()
        providers = manager.get_all_providers()
        
        return {
            "success": True,
            "count": len(providers),
            "providers": providers
        }
    except Exception as e:
        logger.error(f"获取LLM提供商配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/providers/{provider_name}")
@log_api_call("获取特定LLM提供商配置")
async def get_provider_config(provider_name: str):
    """
    获取特定提供商的配置
    
    Args:
        provider_name: 提供商名称
        
    Returns:
        提供商配置详情
    """
    try:
        from backend.services.llm.llm_config_manager import get_llm_config_manager
        
        manager = get_llm_config_manager()
        provider_config = manager.get_provider_config(provider_name)
        
        if provider_config is None:
            raise HTTPException(status_code=404, detail=f"提供商 {provider_name} 不存在")
        
        return {
            "success": True,
            "provider_name": provider_name,
            "config": provider_config
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取提供商配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reload")
@log_api_call("重新加载LLM配置")
async def reload_config():
    """
    重新加载LLM配置文件
    
    Returns:
        重新加载结果
    """
    try:
        from backend.services.llm.llm_config_manager import get_llm_config_manager
        
        manager = get_llm_config_manager()
        manager.reload_config()
        
        return {
            "success": True,
            "message": "LLM配置已重新加载",
            "version": manager.config.get("version"),
            "updated_at": manager.config.get("updated_at")
        }
    except Exception as e:
        logger.error(f"重新加载配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
@log_api_call("获取LLM配置状态")
async def get_config_status():
    """
    获取LLM配置系统状态
    
    Returns:
        配置系统状态信息
    """
    try:
        from backend.services.llm.llm_config_manager import get_llm_config_manager
        
        manager = get_llm_config_manager()
        
        tasks = manager.get_all_tasks()
        enabled_tasks = [name for name, config in tasks.items() if config.get("enabled", True)]
        disabled_tasks = [name for name, config in tasks.items() if not config.get("enabled", True)]
        
        providers = manager.get_all_providers()
        
        return {
            "success": True,
            "version": manager.config.get("version"),
            "updated_at": manager.config.get("updated_at"),
            "default_provider": manager.config.get("default_provider"),
            "default_model": manager.config.get("default_model"),
            "statistics": {
                "total_tasks": len(tasks),
                "enabled_tasks": len(enabled_tasks),
                "disabled_tasks": len(disabled_tasks),
                "total_providers": len(providers)
            },
            "enabled_tasks": enabled_tasks,
            "disabled_tasks": disabled_tasks
        }
    except Exception as e:
        logger.error(f"获取配置状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
