"""
智能体配置API
提供智能体启用/禁用配置、验证、保存、加载等功能
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
import json
import os

from backend.utils.logging_config import get_logger
from backend.utils.tool_logging import log_api_call
from backend.agents.agent_registry import get_registry, AgentPriority
from backend.agents.agent_dependency_manager import get_dependency_manager

logger = get_logger("api.agent_config")
router = APIRouter(prefix="/api/agents/config", tags=["Agent Configuration"])

# 配置文件路径
CONFIG_DIR = "backend/data"
CONFIG_FILE = os.path.join(CONFIG_DIR, "agent_config.json")

# 确保配置目录存在
os.makedirs(CONFIG_DIR, exist_ok=True)


class AgentConfigRequest(BaseModel):
    """智能体配置请求"""
    enabled: Dict[str, bool] = Field(..., description="智能体启用状态")
    profile: Optional[str] = Field(None, description="配置方案名称")


class AgentConfigResponse(BaseModel):
    """智能体配置响应"""
    success: bool
    config: Dict[str, bool]
    impact: Optional[Dict] = None
    message: Optional[str] = None


class ValidateConfigRequest(BaseModel):
    """配置验证请求"""
    enabled: Dict[str, bool]


class ValidateConfigResponse(BaseModel):
    """配置验证响应"""
    valid: bool
    checks: List[Dict]
    warnings: List[str]


# 默认配置方案
DEFAULT_PROFILES = {
    "minimal": {
        "name": "最小化配置",
        "description": "仅核心智能体，约45秒，适合快速决策",
        "enabled": {
            "news_analyst": True,
            "fundamental": True,
            "technical": True,
            "bull_researcher": True,
            "bear_researcher": True,
            "research_manager": True,
            "risk_manager": True,
            "gm": True,
            "trader": True
        }
    },
    "balanced": {
        "name": "平衡配置",
        "description": "核心+重要智能体，约75秒，日常分析",
        "enabled": {
            "news_analyst": True,
            "fundamental": True,
            "technical": True,
            "bull_researcher": True,
            "bear_researcher": True,
            "research_manager": True,
            "risk_manager": True,
            "gm": True,
            "trader": True,
            "macro": True,
            "industry": True,
            "funds": True,
            "manager_fundamental": True,
            "risk_aggressive": True,
            "risk_conservative": True,
            "risk_neutral": True
        }
    },
    "complete": {
        "name": "完整配置",
        "description": "全部智能体，约120秒，深度研究",
        "enabled": {}  # 将在运行时填充所有智能体
    }
}


def load_config() -> Dict[str, bool]:
    """加载配置"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载配置失败: {e}")
    
    # 返回默认配置（平衡方案）
    return DEFAULT_PROFILES["balanced"]["enabled"].copy()


def save_config(config: Dict[str, bool]) -> bool:
    """保存配置"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        logger.info(f"配置已保存: {len([v for v in config.values() if v])} 个智能体启用")
        return True
    except Exception as e:
        logger.error(f"保存配置失败: {e}")
        return False


@router.get("/profiles", response_model=Dict)
@log_api_call("获取配置方案列表")
async def get_profiles():
    """获取所有预设配置方案"""
    registry = get_registry()
    
    # 填充完整配置的所有智能体
    complete_enabled = {}
    for agent_id in registry.get_all_agents().keys():
        complete_enabled[agent_id] = True
    DEFAULT_PROFILES["complete"]["enabled"] = complete_enabled
    
    return {
        "success": True,
        "profiles": DEFAULT_PROFILES
    }


@router.get("/current", response_model=AgentConfigResponse)
@log_api_call("获取当前配置")
async def get_current_config():
    """获取当前配置"""
    config = load_config()
    dep_manager = get_dependency_manager()
    impact = dep_manager.get_config_impact(config)
    
    return AgentConfigResponse(
        success=True,
        config=config,
        impact=impact
    )


@router.post("/validate", response_model=ValidateConfigResponse)
@log_api_call("验证配置")
async def validate_config(request: ValidateConfigRequest):
    """
    验证配置的合法性
    检查依赖关系、核心智能体等
    """
    dep_manager = get_dependency_manager()
    is_valid, check_results = dep_manager.validate_config(request.enabled)
    
    # 收集所有警告
    all_warnings = []
    checks_data = []
    
    for result in check_results:
        result_dict = result.to_dict()
        checks_data.append(result_dict)
        all_warnings.extend(result_dict["warnings"])
    
    return ValidateConfigResponse(
        valid=is_valid,
        checks=checks_data,
        warnings=all_warnings
    )


@router.post("/apply", response_model=AgentConfigResponse)
@log_api_call("应用配置")
async def apply_config(request: AgentConfigRequest):
    """
    应用智能体配置
    先验证，再保存
    """
    dep_manager = get_dependency_manager()
    
    # 验证配置
    is_valid, check_results = dep_manager.validate_config(request.enabled)
    
    if not is_valid:
        warnings = []
        for result in check_results:
            warnings.extend(result.warnings)
        raise HTTPException(
            status_code=400,
            detail={
                "message": "配置验证失败",
                "warnings": warnings
            }
        )
    
    # 保存配置
    if not save_config(request.enabled):
        raise HTTPException(status_code=500, detail="保存配置失败")
    
    # 计算影响
    impact = dep_manager.get_config_impact(request.enabled)
    
    return AgentConfigResponse(
        success=True,
        config=request.enabled,
        impact=impact,
        message=f"配置已保存，启用 {impact['enabled_count']} 个智能体"
    )


@router.post("/profile/{profile_name}", response_model=AgentConfigResponse)
@log_api_call("应用预设方案")
async def apply_profile(profile_name: str):
    """应用预设配置方案"""
    if profile_name not in DEFAULT_PROFILES:
        raise HTTPException(status_code=404, detail=f"方案不存在: {profile_name}")
    
    profile = DEFAULT_PROFILES[profile_name]
    
    # 如果是完整配置，填充所有智能体
    if profile_name == "complete":
        registry = get_registry()
        enabled = {agent_id: True for agent_id in registry.get_all_agents().keys()}
    else:
        enabled = profile["enabled"].copy()
    
    # 保存配置
    if not save_config(enabled):
        raise HTTPException(status_code=500, detail="保存配置失败")
    
    # 计算影响
    dep_manager = get_dependency_manager()
    impact = dep_manager.get_config_impact(enabled)
    
    return AgentConfigResponse(
        success=True,
        config=enabled,
        impact=impact,
        message=f"已应用 {profile['name']}"
    )


@router.post("/enable/{agent_id}", response_model=AgentConfigResponse)
@log_api_call("启用智能体")
async def enable_agent(agent_id: str, auto_deps: bool = True):
    """
    启用单个智能体
    
    Args:
        agent_id: 智能体ID
        auto_deps: 是否自动启用依赖
    """
    registry = get_registry()
    agent = registry.get_agent(agent_id)
    
    if not agent:
        raise HTTPException(status_code=404, detail=f"智能体不存在: {agent_id}")
    
    # 加载当前配置
    config = load_config()
    dep_manager = get_dependency_manager()
    
    # 检查是否可以启用
    check_result = dep_manager.check_enable(agent_id, config)
    
    if not check_result.can_enable:
        raise HTTPException(
            status_code=400,
            detail={
                "message": f"无法启用 {agent.name}",
                "warnings": check_result.warnings
            }
        )
    
    # 启用智能体
    if auto_deps:
        config = dep_manager.auto_enable_dependencies(agent_id, config)
    else:
        config[agent_id] = True
    
    # 保存配置
    if not save_config(config):
        raise HTTPException(status_code=500, detail="保存配置失败")
    
    # 计算影响
    impact = dep_manager.get_config_impact(config)
    
    return AgentConfigResponse(
        success=True,
        config=config,
        impact=impact,
        message=f"已启用 {agent.name}" + (
            f"，并自动启用 {len(check_result.missing_deps)} 个依赖" 
            if auto_deps and check_result.missing_deps else ""
        )
    )


@router.post("/disable/{agent_id}", response_model=AgentConfigResponse)
@log_api_call("禁用智能体")
async def disable_agent(agent_id: str):
    """禁用单个智能体"""
    registry = get_registry()
    agent = registry.get_agent(agent_id)
    
    if not agent:
        raise HTTPException(status_code=404, detail=f"智能体不存在: {agent_id}")
    
    # 加载当前配置
    config = load_config()
    dep_manager = get_dependency_manager()
    
    # 检查是否可以禁用
    check_result = dep_manager.check_disable(agent_id, config)
    
    if not check_result.can_disable:
        raise HTTPException(
            status_code=400,
            detail={
                "message": f"无法禁用 {agent.name}",
                "warnings": check_result.warnings
            }
        )
    
    # 禁用智能体
    config[agent_id] = False
    
    # 保存配置
    if not save_config(config):
        raise HTTPException(status_code=500, detail="保存配置失败")
    
    # 计算影响
    impact = dep_manager.get_config_impact(config)
    
    warnings = check_result.warnings if check_result.warnings else []
    
    return AgentConfigResponse(
        success=True,
        config=config,
        impact=impact,
        message=f"已禁用 {agent.name}" + (
            f"。{check_result.degradation_message}" 
            if check_result.degradation_message else ""
        )
    )


@router.get("/priority/{priority}", response_model=Dict)
@log_api_call("按优先级获取智能体")
async def get_agents_by_priority(priority: str):
    """按优先级获取智能体列表"""
    try:
        agent_priority = AgentPriority(priority)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"无效的优先级: {priority}")
    
    registry = get_registry()
    agents = []
    
    for agent in registry.get_all_agents().values():
        if agent.priority == agent_priority:
            agents.append({
                "id": agent.id,
                "name": agent.name,
                "icon": agent.icon,
                "description": agent.description,
                "stage": agent.stage.value,
                "dependencies": agent.dependencies or []
            })
    
    return {
        "success": True,
        "priority": priority,
        "count": len(agents),
        "agents": agents
    }


@router.get("/impact", response_model=Dict)
@log_api_call("获取配置影响")
async def get_config_impact():
    """获取当前配置的影响分析"""
    config = load_config()
    dep_manager = get_dependency_manager()
    impact = dep_manager.get_config_impact(config)
    
    return {
        "success": True,
        "impact": impact
    }
