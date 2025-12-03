"""
多智能体辩论系统API
实现多空辩论和风险评估辩论机制
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
import asyncio

# 导入日志系统
from backend.utils.logging_config import get_logger
from backend.utils.tool_logging import log_api_call, log_debate_round

# 导入研究员和风控智能体
from backend.agents.researchers.bull_researcher import create_bull_researcher
from backend.agents.researchers.bear_researcher import create_bear_researcher
from backend.agents.managers.research_manager import create_research_manager
from backend.agents.risk_mgmt.aggresive_debator import create_risky_debator
from backend.agents.risk_mgmt.conservative_debator import create_safe_debator
from backend.agents.risk_mgmt.neutral_debator import create_neutral_debator
from backend.agents.managers.risk_manager import create_risk_manager
from backend.agents.trader.trader import create_trader

logger = get_logger("api.debate")

# 创建路由器
router = APIRouter(prefix="/api/debate", tags=["Multi-Agent Debate"])


class DebateRequest(BaseModel):
    """辩论请求模型"""
    stock_code: str = Field(..., description="股票代码")
    analysis_data: Dict[str, Any] = Field(..., description="分析数据")
    debate_type: str = Field("research", description="辩论类型: research/risk")
    rounds: int = Field(3, description="辩论轮数", ge=1, le=5)
    
class ResearchDebateResponse(BaseModel):
    """研究辩论响应"""
    success: bool
    stock_code: str
    bull_view: Dict[str, Any]
    bear_view: Dict[str, Any]
    bull_strength: float
    bear_strength: float
    final_decision: Dict[str, Any]
    recommendation: str
    confidence: float
    debate_summary: str
    
class RiskDebateResponse(BaseModel):
    """风险辩论响应"""
    success: bool
    stock_code: str
    aggressive_view: Dict[str, Any]
    conservative_view: Dict[str, Any]
    neutral_view: Dict[str, Any]
    risk_level: str
    risk_score: float
    position_advice: Dict[str, Any]
    risk_factors: List[str]
    mitigation_strategies: List[str]
    
class TradingDecisionRequest(BaseModel):
    """交易决策请求"""
    stock_code: str
    debate_result: Dict[str, Any]
    risk_assessment: Dict[str, Any]
    portfolio: Optional[Dict[str, Any]] = Field(None, description="当前持仓")
    capital: float = Field(100000, description="可用资金")
    
class TradingDecisionResponse(BaseModel):
    """交易决策响应"""
    success: bool
    stock_code: str
    action: str = Field(..., description="BUY/SELL/HOLD")
    quantity: int
    price: float
    stop_loss: float
    take_profit: float
    position_size: float = Field(..., description="仓位比例%")
    risk_reward_ratio: float
    confidence: float = Field(..., description="信心度 0-100")
    reasoning: str
    

@router.post("/research", response_model=ResearchDebateResponse)
@log_api_call("研究辩论")
async def run_research_debate(request: DebateRequest):
    """
    运行多空研究辩论
    
    看涨研究员和看跌研究员进行辩论，
    最终由研究经理做出综合决策
    """
    try:
        logger.info(f"开始 {request.stock_code} 的研究辩论")
        
        # 准备辩论状态
        debate_state = {
            "company_of_interest": request.stock_code,
            "analysis_data": request.analysis_data,
            "rounds": request.rounds,
            "session_id": f"debate-research-{request.stock_code}-{datetime.now().timestamp()}"
        }
        
        # 创建辩论智能体（模拟，实际需要配置LLM）
        bull_researcher = create_bull_researcher(llm=None)
        bear_researcher = create_bear_researcher(llm=None)
        research_manager = create_research_manager(llm=None)
        
        # 进行多轮辩论
        bull_views = []
        bear_views = []
        
        for round_num in range(request.rounds):
            logger.info(f"第 {round_num + 1} 轮辩论")
            
            # 看涨观点
            bull_analysis = await asyncio.to_thread(
                bull_researcher, 
                {**debate_state, "previous_bear_view": bear_views[-1] if bear_views else None}
            )
            bull_views.append(bull_analysis)
            
            # 看跌观点
            bear_analysis = await asyncio.to_thread(
                bear_researcher,
                {**debate_state, "previous_bull_view": bull_analysis}
            )
            bear_views.append(bear_analysis)
            
        # 研究经理综合决策
        manager_decision = await asyncio.to_thread(
            research_manager,
            {
                "stock_code": request.stock_code,
                "bull_views": bull_views,
                "bear_views": bear_views,
                "analysis_data": request.analysis_data
            }
        )
        
        # 计算观点强度
        bull_strength = _calculate_view_strength(bull_views)
        bear_strength = _calculate_view_strength(bear_views)
        
        # 生成辩论总结
        debate_summary = _generate_debate_summary(
            bull_views, bear_views, manager_decision
        )
        
        response = ResearchDebateResponse(
            success=True,
            stock_code=request.stock_code,
            bull_view=bull_views[-1],
            bear_view=bear_views[-1],
            bull_strength=bull_strength,
            bear_strength=bear_strength,
            final_decision=manager_decision,
            recommendation=manager_decision.get("recommendation", "HOLD"),
            confidence=manager_decision.get("confidence", 0.5),
            debate_summary=debate_summary
        )
        
        logger.success(f"研究辩论完成，建议: {response.recommendation}")
        return response
        
    except Exception as e:
        logger.error(f"研究辩论失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"辩论失败: {str(e)}")


@router.post("/risk", response_model=RiskDebateResponse)
@log_api_call("风险辩论")
async def run_risk_debate(request: DebateRequest):
    """
    运行风险评估辩论
    
    激进、保守、中立三方进行风险辩论，
    最终由风险经理做出风控决策
    """
    try:
        logger.info(f"开始 {request.stock_code} 的风险辩论")
        
        # 准备辩论状态
        risk_state = {
            "stock_code": request.stock_code,
            "analysis_data": request.analysis_data,
            "session_id": f"debate-risk-{request.stock_code}-{datetime.now().timestamp()}"
        }
        
        # 创建风控智能体（模拟，实际需要配置LLM）
        aggressive_debator = create_risky_debator(llm=None)
        conservative_debator = create_safe_debator(llm=None)
        neutral_debator = create_neutral_debator(llm=None)
        risk_manager = create_risk_manager(llm=None)
        
        # 三方辩论
        aggressive_view = await asyncio.to_thread(aggressive_debator, risk_state)
        conservative_view = await asyncio.to_thread(conservative_debator, risk_state)
        neutral_view = await asyncio.to_thread(neutral_debator, risk_state)
        
        # 风险经理决策
        risk_decision = await asyncio.to_thread(
            risk_manager,
            {
                "stock_code": request.stock_code,
                "aggressive_view": aggressive_view,
                "conservative_view": conservative_view,
                "neutral_view": neutral_view,
                "analysis_data": request.analysis_data
            }
        )
        
        # 解析风险等级
        risk_score = risk_decision.get("risk_score", 0.5)
        risk_level = _get_risk_level(risk_score)
        
        # 生成仓位建议
        position_advice = _generate_position_advice(
            risk_score, 
            request.analysis_data
        )
        
        response = RiskDebateResponse(
            success=True,
            stock_code=request.stock_code,
            aggressive_view=aggressive_view,
            conservative_view=conservative_view,
            neutral_view=neutral_view,
            risk_level=risk_level,
            risk_score=risk_score,
            position_advice=position_advice,
            risk_factors=risk_decision.get("risk_factors", []),
            mitigation_strategies=risk_decision.get("mitigation_strategies", [])
        )
        
        logger.success(f"风险辩论完成，风险等级: {risk_level}")
        return response
        
    except Exception as e:
        logger.error(f"风险辩论失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"辩论失败: {str(e)}")


@router.post("/trading-decision", response_model=TradingDecisionResponse)
@log_api_call("交易决策")
async def generate_trading_decision(request: TradingDecisionRequest):
    """
    生成结构化交易决策
    
    基于辩论结果和风险评估，生成具体的交易指令
    """
    try:
        logger.info(f"生成 {request.stock_code} 的交易决策")
        
        # 创建交易员智能体（模拟，实际需要配置LLM）
        trader = create_trader(llm=None)
        
        # 准备决策输入
        decision_input = {
            "stock_code": request.stock_code,
            "recommendation": request.debate_result.get("recommendation", "HOLD"),
            "confidence": request.debate_result.get("confidence", 0.5),
            "risk_level": request.risk_assessment.get("risk_level", "MEDIUM"),
            "risk_score": request.risk_assessment.get("risk_score", 0.5),
            "portfolio": request.portfolio or {},
            "capital": request.capital
        }
        
        # 生成交易决策
        trading_order = await asyncio.to_thread(trader, decision_input)
        
        # 计算具体参数
        action = trading_order.get("action", "HOLD")
        current_price = request.debate_result.get("current_price", 100)
        
        # 根据风险调整仓位
        base_position = trading_order.get("position_size", 10)
        risk_adjusted_position = _adjust_position_by_risk(
            base_position,
            request.risk_assessment.get("risk_score", 0.5)
        )
        
        # 计算止损止盈
        stop_loss = current_price * (1 - trading_order.get("stop_loss_pct", 0.05))
        take_profit = current_price * (1 + trading_order.get("take_profit_pct", 0.15))
        
        # 计算风险收益比
        risk_reward_ratio = (take_profit - current_price) / (current_price - stop_loss)
        
        # 计算购买数量
        quantity = int((request.capital * risk_adjusted_position / 100) / current_price / 100) * 100
        
        response = TradingDecisionResponse(
            success=True,
            stock_code=request.stock_code,
            action=action,
            quantity=quantity,
            price=current_price,
            stop_loss=round(stop_loss, 2),
            take_profit=round(take_profit, 2),
            position_size=risk_adjusted_position,
            risk_reward_ratio=round(risk_reward_ratio, 2),
            confidence=trading_order.get("confidence", 50),
            reasoning=trading_order.get("reasoning", "基于综合分析的决策")
        )
        
        logger.success(f"交易决策生成: {action} {quantity}股 @ {current_price}")
        return response
        
    except Exception as e:
        logger.error(f"生成交易决策失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"决策生成失败: {str(e)}")


@router.get("/history/{stock_code}")
async def get_debate_history(stock_code: str, limit: int = 10):
    """
    获取历史辩论记录
    
    Args:
        stock_code: 股票代码
        limit: 记录数量限制
    """
    try:
        # TODO: 从数据库获取历史辩论记录
        # 这里返回模拟数据
        
        history = []
        for i in range(min(limit, 3)):
            history.append({
                "date": (datetime.now()).strftime("%Y-%m-%d"),
                "type": "research" if i % 2 == 0 else "risk",
                "recommendation": ["BUY", "HOLD", "SELL"][i % 3],
                "confidence": 0.7 + i * 0.05,
                "outcome": "pending"
            })
            
        return {
            "success": True,
            "stock_code": stock_code,
            "history": history,
            "total": len(history)
        }
        
    except Exception as e:
        logger.error(f"获取辩论历史失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# 辅助函数
def _calculate_view_strength(views: List[Dict]) -> float:
    """计算观点强度"""
    if not views:
        return 0.5
        
    # 基于信心度和一致性计算
    confidences = [v.get("confidence", 0.5) for v in views]
    avg_confidence = sum(confidences) / len(confidences)
    
    # 计算观点一致性
    recommendations = [v.get("recommendation", "HOLD") for v in views]
    consistency = len(set(recommendations)) / len(recommendations)
    
    # 综合强度
    strength = avg_confidence * (2 - consistency)  # 一致性高则强度高
    
    return min(1.0, max(0.0, strength))


def _generate_debate_summary(
    bull_views: List[Dict],
    bear_views: List[Dict],
    decision: Dict
) -> str:
    """生成辩论总结"""
    
    bull_points = len(bull_views)
    bear_points = len(bear_views)
    recommendation = decision.get("recommendation", "HOLD")
    
    summary = f"经过{max(bull_points, bear_points)}轮激烈辩论，"
    
    if recommendation == "BUY":
        summary += "看涨观点占据上风，建议买入。"
    elif recommendation == "SELL":
        summary += "看跌观点更有说服力，建议卖出。"
    else:
        summary += "多空双方势均力敌，建议持有观望。"
        
    # 添加关键论点
    if bull_views and bull_views[-1].get("key_points"):
        summary += f" 看涨主要理由：{bull_views[-1]['key_points'][0]}"
        
    if bear_views and bear_views[-1].get("key_points"):
        summary += f" 看跌主要理由：{bear_views[-1]['key_points'][0]}"
        
    return summary


def _get_risk_level(risk_score: float) -> str:
    """根据风险分数返回风险等级"""
    if risk_score >= 0.7:
        return "HIGH"
    elif risk_score >= 0.4:
        return "MEDIUM"
    else:
        return "LOW"


def _generate_position_advice(risk_score: float, analysis_data: Dict) -> Dict:
    """生成仓位建议"""
    
    # 基础仓位（反向关系：风险越高，仓位越低）
    base_position = max(5, min(30, int((1 - risk_score) * 40)))
    
    # 根据信心度调整
    confidence = analysis_data.get("confidence", 0.5)
    adjusted_position = base_position * (0.5 + confidence)
    
    return {
        "recommended_position": round(adjusted_position, 1),
        "max_position": round(adjusted_position * 1.5, 1),
        "min_position": round(adjusted_position * 0.5, 1),
        "risk_adjusted": True,
        "notes": f"基于{_get_risk_level(risk_score)}风险等级的仓位建议"
    }


def _adjust_position_by_risk(base_position: float, risk_score: float) -> float:
    """根据风险调整仓位"""
    
    # 风险调整系数（风险越高，系数越低）
    risk_multiplier = 1.5 - risk_score
    
    # 调整后的仓位
    adjusted = base_position * risk_multiplier
    
    # 限制在合理范围内
    return max(2, min(50, adjusted))


# 测试端点
@router.get("/test")
async def test_debate_api():
    """测试辩论API是否正常工作"""
    return {
        "status": "ok",
        "message": "Debate API is working",
        "features": [
            "Research debate (bull vs bear)",
            "Risk debate (aggressive vs conservative vs neutral)",
            "Trading decision generation",
            "Debate history tracking"
        ],
        "timestamp": datetime.now().isoformat()
    }
