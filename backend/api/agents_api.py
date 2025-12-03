"""
智能体管理API
提供智能体注册、查询、调用等功能
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

# 导入日志系统
from backend.utils.logging_config import get_logger
from backend.utils.tool_logging import log_api_call

# 导入智能体注册表
from backend.agents.agent_registry import get_registry, AgentType, AgentStage

# 导入LLM客户端
from backend.utils.llm_client import create_agent_llm, LLMProvider

logger = get_logger("api.agents")

# 创建路由器
router = APIRouter(prefix="/api/agents", tags=["Agent Management"])


class AgentListRequest(BaseModel):
    """智能体列表请求"""
    type: Optional[str] = Field(None, description="按类型筛选")
    stage: Optional[int] = Field(None, description="按阶段筛选")
    is_legacy: Optional[bool] = Field(None, description="是否旧系统")
    is_active: Optional[bool] = Field(True, description="是否激活")


class AgentCallRequest(BaseModel):
    """智能体调用请求"""
    agent_id: str = Field(..., description="智能体ID")
    stock_code: str = Field(..., description="股票代码")
    params: Dict[str, Any] = Field(default_factory=dict, description="调用参数")
    context: Dict[str, Any] = Field(default_factory=dict, description="上下文信息")


@router.get("/registry", response_model=Dict[str, Any])
@log_api_call("获取智能体注册表")
async def get_agent_registry():
    """
    获取完整的智能体注册表
    
    Returns:
        智能体注册表信息
    """
    try:
        registry = get_registry()
        return {
            "success": True,
            "data": registry.to_dict()
        }
    except Exception as e:
        logger.error(f"获取注册表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list", response_model=Dict[str, Any])
@log_api_call("获取智能体列表")
async def get_agents_list(
    type: Optional[str] = None,
    stage: Optional[int] = None,
    is_legacy: Optional[bool] = None,
    is_active: bool = True
):
    """
    获取智能体列表
    
    Args:
        type: 按类型筛选
        stage: 按阶段筛选
        is_legacy: 是否旧系统
        is_active: 是否激活
        
    Returns:
        符合条件的智能体列表
    """
    try:
        registry = get_registry()
        agents = registry.get_active_agents() if is_active else list(registry.get_all_agents().values())
        
        # 筛选
        if type:
            try:
                agent_type = AgentType(type)
                agents = [a for a in agents if a.type == agent_type]
            except ValueError:
                raise HTTPException(status_code=400, detail=f"无效的类型: {type}")
                
        if stage:
            try:
                agent_stage = AgentStage(stage)
                agents = [a for a in agents if a.stage == agent_stage]
            except ValueError:
                raise HTTPException(status_code=400, detail=f"无效的阶段: {stage}")
                
        if is_legacy is not None:
            agents = [a for a in agents if a.is_legacy == is_legacy]
            
        # 转换为字典
        result = []
        for agent in agents:
            result.append({
                "id": agent.id,
                "name": agent.name,
                "english_name": agent.english_name,
                "type": agent.type.value,
                "stage": agent.stage.value,
                "icon": agent.icon,
                "color": agent.color,
                "description": agent.description,
                "is_legacy": agent.is_legacy,
                "is_active": agent.is_active
            })
            
        return {
            "success": True,
            "count": len(result),
            "agents": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取智能体列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_id}", response_model=Dict[str, Any])
@log_api_call("获取智能体详情")
async def get_agent_detail(agent_id: str):
    """
    获取智能体详细信息
    
    Args:
        agent_id: 智能体ID
        
    Returns:
        智能体详细信息
    """
    try:
        registry = get_registry()
        agent = registry.get_agent(agent_id)
        
        if not agent:
            raise HTTPException(status_code=404, detail=f"智能体不存在: {agent_id}")
            
        # 获取依赖信息
        dependencies = registry.get_agent_dependencies(agent_id)
        
        return {
            "success": True,
            "agent": {
                "id": agent.id,
                "name": agent.name,
                "english_name": agent.english_name,
                "type": agent.type.value,
                "stage": agent.stage.value,
                "icon": agent.icon,
                "color": agent.color,
                "description": agent.description,
                "module_path": agent.module_path,
                "api_endpoint": agent.api_endpoint,
                "is_legacy": agent.is_legacy,
                "is_active": agent.is_active,
                "dependencies": [
                    {
                        "id": dep.id,
                        "name": dep.name,
                        "type": dep.type.value
                    } for dep in dependencies
                ]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取智能体详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/call", response_model=Dict[str, Any])
@log_api_call("调用智能体")
async def call_agent(request: AgentCallRequest):
    """
    统一的智能体调用接口
    
    Args:
        request: 调用请求
        
    Returns:
        调用结果
    """
    try:
        registry = get_registry()
        agent = registry.get_agent(request.agent_id)
        
        if not agent:
            raise HTTPException(status_code=404, detail=f"智能体不存在: {request.agent_id}")
            
        if not agent.is_active:
            raise HTTPException(status_code=400, detail=f"智能体未激活: {request.agent_id}")
            
        # 根据智能体类型路由到不同的处理逻辑
        if agent.is_legacy:
            # 旧系统智能体，使用原有的/api/analyze接口逻辑
            from backend.server import analyze_stock, AnalyzeRequest
            analyze_req = AnalyzeRequest(
                agent_id=request.agent_id,
                stock_code=request.stock_code,
                stock_data=request.params.get("stock_data", {}),
                previous_outputs=request.context.get("previous_outputs", {})
            )
            result = await analyze_stock(analyze_req)
            
        elif agent.module_path:
            # 新系统智能体，动态加载模块
            try:
                # 动态导入模块
                import importlib
                module = importlib.import_module(agent.module_path)
                
                # 查找创建函数（约定：create_<agent_id>）
                create_func_name = f"create_{request.agent_id}"
                if hasattr(module, create_func_name):
                    create_func = getattr(module, create_func_name)
                    
                    # 创建LLM客户端
                    # 根据智能体类型选择合适的模型和参数
                    if agent.type == AgentType.ANALYST:
                        # 分析师使用较精确的模型
                        llm = create_agent_llm(
                            provider=request.params.get("provider", "deepseek"),
                            model=request.params.get("model", "deepseek-chat"),
                            temperature=0.3
                        )
                    elif agent.type in [AgentType.RESEARCHER, AgentType.DEBATOR]:
                        # 研究员和辩论员使用稍高的创造性
                        llm = create_agent_llm(
                            provider=request.params.get("provider", "qwen"),
                            model=request.params.get("model", "qwen-plus"),
                            temperature=0.5
                        )
                    elif agent.type == AgentType.MANAGER:
                        # 管理者使用平衡的参数
                        llm = create_agent_llm(
                            provider=request.params.get("provider", "deepseek"),
                            model=request.params.get("model", "deepseek-chat"),
                            temperature=0.4
                        )
                    else:
                        # 默认配置
                        llm = create_agent_llm()
                    
                    # 创建智能体实例
                    # 注意：有些智能体可能需要toolkit参数
                    try:
                        agent_instance = create_func(llm=llm, toolkit=None)
                    except TypeError:
                        # 如果不需要toolkit参数，只传llm
                        try:
                            agent_instance = create_func(llm=llm)
                        except TypeError:
                            # 如果连llm都不需要，直接创建
                            agent_instance = create_func()
                    
                    # 准备状态
                    state = {
                        "company_of_interest": request.stock_code,
                        "trade_date": request.params.get("trade_date"),
                        "session_id": request.context.get("session_id", "api_call"),
                        **request.context
                    }
                    
                    # 调用智能体
                    # 判断是同步还是异步函数
                    import inspect
                    if inspect.iscoroutinefunction(agent_instance):
                        result = await agent_instance(state)
                    else:
                        result = agent_instance(state)
                        
                    # 处理结果格式
                    if isinstance(result, dict):
                        # 如果返回的是状态字典，提取相关信息
                        agent_output_key = f"{request.agent_id}_output"
                        if agent_output_key in result:
                            result = result[agent_output_key]
                        elif "output" in result:
                            result = result["output"]
                            
                else:
                    raise HTTPException(
                        status_code=500, 
                        detail=f"模块 {agent.module_path} 中未找到 {create_func_name} 函数"
                    )
                    
            except ImportError as e:
                logger.error(f"导入模块失败: {agent.module_path}", exc_info=True)
                raise HTTPException(
                    status_code=500,
                    detail=f"无法导入模块 {agent.module_path}: {str(e)}"
                )
        else:
            # 没有实现的智能体
            raise HTTPException(
                status_code=501,
                detail=f"智能体 {request.agent_id} 尚未实现"
            )
            
        return {
            "success": True,
            "agent_id": request.agent_id,
            "result": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"调用智能体失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workflow/stages", response_model=Dict[str, Any])
@log_api_call("获取工作流阶段")
async def get_workflow_stages():
    """
    获取智能体工作流的阶段信息
    
    Returns:
        工作流阶段信息
    """
    try:
        registry = get_registry()
        
        stages = {}
        for stage in AgentStage:
            agents = registry.get_agents_by_stage(stage)
            stages[f"stage_{stage.value}"] = {
                "name": {
                    1: "数据分析阶段",
                    2: "研究整合阶段", 
                    3: "风险评估阶段",
                    4: "决策执行阶段"
                }.get(stage.value, f"阶段{stage.value}"),
                "agents": [
                    {
                        "id": a.id,
                        "name": a.name,
                        "type": a.type.value,
                        "is_legacy": a.is_legacy
                    } for a in agents
                ]
            }
            
        return {
            "success": True,
            "stages": stages,
            "total_agents": len(registry.get_all_agents()),
            "flow": [
                "stage_1 -> stage_2",
                "stage_2 -> stage_3",  
                "stage_3 -> stage_4"
            ]
        }
        
    except Exception as e:
        logger.error(f"获取工作流阶段失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics", response_model=Dict[str, Any])
@log_api_call("获取智能体统计")
async def get_agent_statistics():
    """
    获取智能体统计信息
    
    Returns:
        统计信息
    """
    try:
        registry = get_registry()
        
        all_agents = registry.get_all_agents()
        legacy_agents = registry.get_legacy_agents()
        new_agents = registry.get_new_agents()
        active_agents = registry.get_active_agents()
        
        # 按类型统计
        type_stats = {}
        for agent_type in AgentType:
            agents = registry.get_agents_by_type(agent_type)
            type_stats[agent_type.value] = {
                "count": len(agents),
                "percentage": len(agents) / len(all_agents) * 100 if all_agents else 0
            }
            
        # 按阶段统计
        stage_stats = {}
        for stage in AgentStage:
            agents = registry.get_agents_by_stage(stage)
            stage_stats[stage.value] = {
                "count": len(agents),
                "percentage": len(agents) / len(all_agents) * 100 if all_agents else 0
            }
            
        return {
            "success": True,
            "statistics": {
                "total": len(all_agents),
                "active": len(active_agents),
                "legacy": len(legacy_agents),
                "new": len(new_agents),
                "by_type": type_stats,
                "by_stage": stage_stats,
                "integration_rate": len(new_agents) / len(all_agents) * 100 if all_agents else 0
            }
        }
        
    except Exception as e:
        logger.error(f"获取统计信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# 测试端点
@router.get("/test")
async def test_agents_api():
    """测试智能体API是否正常工作"""
    return {
        "status": "ok",
        "message": "Agents API is working",
        "features": [
            "Agent registry",
            "Agent listing",
            "Agent details",
            "Unified calling",
            "Workflow stages",
            "Statistics"
        ],
        "total_agents": len(get_registry().get_all_agents())
    }
