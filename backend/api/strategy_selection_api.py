"""
智能策略选择API
根据智能分析结果，使用LLM推荐最适合的交易策略
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import json

from backend.utils.logging_config import get_logger
from backend.api.trading_llm_config_api import get_trading_llm_config
from backend.services.strategy.selector import StrategySelector

logger = get_logger("api.strategy_selection")
router = APIRouter(prefix="/api/strategy-selection", tags=["Strategy Selection"])


# ==================== 数据模型 ====================

class AnalysisResult(BaseModel):
    """分析结果"""
    stock_code: str
    stock_name: Optional[str] = None
    analysis_summary: str = Field(..., description="分析摘要")
    technical_score: Optional[float] = Field(None, description="技术面评分")
    fundamental_score: Optional[float] = Field(None, description="基本面评分")
    sentiment_score: Optional[float] = Field(None, description="情绪评分")
    risk_level: Optional[str] = Field(None, description="风险等级")
    investment_advice: Optional[str] = Field(None, description="投资建议")


class StrategyRecommendation(BaseModel):
    """策略推荐"""
    strategy_id: str
    strategy_name: str
    confidence: float = Field(..., ge=0, le=1, description="推荐置信度")
    reason: str = Field(..., description="推荐理由")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="建议参数")


class SelectionRequest(BaseModel):
    """策略选择请求"""
    analysis_result: AnalysisResult
    risk_preference: str = Field("moderate", description="风险偏好: conservative/moderate/aggressive")
    max_recommendations: int = Field(3, ge=1, le=5, description="最多推荐数量")


class SelectionResponse(BaseModel):
    """策略选择响应"""
    success: bool
    recommendations: List[StrategyRecommendation]
    reasoning: str = Field(..., description="整体推荐逻辑")


# ==================== LLM调用 ====================

async def call_strategy_selector_llm(
    analysis_result: AnalysisResult,
    available_strategies: List[Dict],
    risk_preference: str
) -> Dict[str, Any]:
    """
    调用LLM进行策略选择
    
    Args:
        analysis_result: 分析结果
        available_strategies: 可用策略列表
        risk_preference: 风险偏好
        
    Returns:
        LLM推荐结果
    """
    # 获取LLM配置
    config = get_trading_llm_config("strategy_selector")
    
    if not config.get("enabled", True):
        raise HTTPException(status_code=503, detail="策略选择LLM未启用")
    
    # 构建提示词
    prompt = f"""你是一个专业的量化交易策略顾问。根据以下股票分析结果，从可用策略中推荐最适合的交易策略。

股票信息：
- 代码：{analysis_result.stock_code}
- 名称：{analysis_result.stock_name or '未知'}

分析结果：
{analysis_result.analysis_summary}

技术面评分：{analysis_result.technical_score or '未评分'}
基本面评分：{analysis_result.fundamental_score or '未评分'}
情绪评分：{analysis_result.sentiment_score or '未评分'}
风险等级：{analysis_result.risk_level or '未评估'}
投资建议：{analysis_result.investment_advice or '无'}

用户风险偏好：{risk_preference}
- conservative: 保守型，偏好低风险策略
- moderate: 稳健型，平衡风险和收益
- aggressive: 激进型，追求高收益

可用策略列表：
{json.dumps([{
    'id': s['strategy_id'],
    'name': s['name'],
    'category': s['category'],
    'description': s['description']
} for s in available_strategies], ensure_ascii=False, indent=2)}

请分析并推荐1-3个最适合的策略，对每个策略说明：
1. 推荐理由（结合分析结果）
2. 置信度（0-1之间的数值）
3. 建议的参数设置

以JSON格式返回，格式如下：
{{
  "recommendations": [
    {{
      "strategy_id": "策略ID",
      "confidence": 0.85,
      "reason": "推荐理由",
      "parameters": {{"param1": value1}}
    }}
  ],
  "reasoning": "整体推荐逻辑说明"
}}
"""
    
    try:
        logger.info(f"调用LLM进行策略选择: {analysis_result.stock_code}")

        # 真实调用LLM进行策略选择
        from backend.services.llm_service import call_strategy_selector_llm as llm_call

        result = await llm_call(
            stock_code=analysis_result.stock_code,
            stock_name=analysis_result.stock_name or "未知",
            analysis_summary=analysis_result.analysis_summary,
            technical_score=analysis_result.technical_score or 0.5,
            fundamental_score=analysis_result.fundamental_score or 0.5,
            sentiment_score=analysis_result.sentiment_score or 0.5,
            risk_level=analysis_result.risk_level or "中",
            risk_preference=risk_preference,
            available_strategies=available_strategies
        )

        logger.info(f"LLM策略选择完成: {len(result.get('recommendations', []))}个推荐")
        return result
        
    except Exception as e:
        logger.error(f"LLM策略选择失败: {e}")
        raise HTTPException(status_code=500, detail=f"策略选择失败: {str(e)}")


# ==================== API端点 ====================

@router.post("/select", response_model=SelectionResponse)
async def select_strategies(request: SelectionRequest):
    """
    智能选择交易策略
    
    Args:
        request: 选择请求
        
    Returns:
        策略推荐结果
    """
    try:
        logger.info(f"开始策略选择: {request.analysis_result.stock_code}")
        
        # 获取可用策略列表
        selector = StrategySelector()
        available_strategies = selector._load_strategies()
        
        logger.info(f"可用策略数量: {len(available_strategies)}")
        
        # 调用LLM进行策略选择
        llm_result = await call_strategy_selector_llm(
            request.analysis_result,
            available_strategies,
            request.risk_preference
        )
        
        # 构建响应
        recommendations = []
        for rec in llm_result["recommendations"][:request.max_recommendations]:
            # 查找策略详情
            strategy = next(
                (s for s in available_strategies if s["strategy_id"] == rec["strategy_id"]),
                None
            )
            
            if strategy:
                recommendations.append(StrategyRecommendation(
                    strategy_id=rec["strategy_id"],
                    strategy_name=strategy["name"],
                    confidence=rec["confidence"],
                    reason=rec["reason"],
                    parameters=rec.get("parameters", {})
                ))
        
        logger.info(f"推荐策略数量: {len(recommendations)}")
        
        return SelectionResponse(
            success=True,
            recommendations=recommendations,
            reasoning=llm_result["reasoning"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"策略选择失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"策略选择失败: {str(e)}")


@router.get("/strategies")
async def list_available_strategies():
    """
    获取所有可用策略列表
    
    Returns:
        策略列表
    """
    try:
        selector = StrategySelector()
        strategies = selector._load_strategies()
        
        return {
            "success": True,
            "strategies": strategies,
            "total": len(strategies)
        }
    except Exception as e:
        logger.error(f"获取策略列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test")
async def test_strategy_selection():
    """
    测试策略选择功能
    
    Returns:
        测试结果
    """
    # 构建测试数据
    test_request = SelectionRequest(
        analysis_result=AnalysisResult(
            stock_code="600519",
            stock_name="贵州茅台",
            analysis_summary="该股票基本面优秀，财务稳健，行业地位突出。技术面显示上升趋势，市场情绪积极。",
            technical_score=0.85,
            fundamental_score=0.90,
            sentiment_score=0.75,
            risk_level="低",
            investment_advice="建议长期持有"
        ),
        risk_preference="moderate",
        max_recommendations=3
    )
    
    # 调用选择API
    result = await select_strategies(test_request)
    
    return {
        "success": True,
        "message": "测试成功",
        "result": result
    }
