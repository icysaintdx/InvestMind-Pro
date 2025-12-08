"""
多智能体辩论系统API
实现多空辩论和风险评估辩论机制
"""

import os
import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
import asyncio

# 导入日志系统
from backend.utils.logging_config import get_logger
from backend.utils.tool_logging import log_api_call, log_debate_round
from backend.utils.llm_client import create_agent_llm

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

# ========== LLM 与配置工具函数 ==========

AGENT_CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "agent_configs.json")
_AGENT_CONFIG_CACHE: Optional[Dict[str, Any]] = None


def _load_agent_configs() -> Dict[str, Any]:
    """加载智能体模型配置（带简单缓存）"""
    global _AGENT_CONFIG_CACHE
    if _AGENT_CONFIG_CACHE is not None:
        return _AGENT_CONFIG_CACHE

    if not os.path.exists(AGENT_CONFIG_FILE):
        logger.warning(f"agent_configs.json 不存在: {AGENT_CONFIG_FILE}")
        _AGENT_CONFIG_CACHE = {"agents": []}
        return _AGENT_CONFIG_CACHE

    try:
        with open(AGENT_CONFIG_FILE, "r", encoding="utf-8") as f:
            _AGENT_CONFIG_CACHE = json.load(f)
    except Exception as e:
        logger.error(f"加载 agent_configs.json 失败: {str(e)}")
        _AGENT_CONFIG_CACHE = {"agents": []}
    return _AGENT_CONFIG_CACHE


def _get_agent_config(agent_id: str) -> Dict[str, Any]:
    """根据 ID 获取单个智能体的模型配置"""
    configs = _load_agent_configs()
    for agent in configs.get("agents", []):
        if agent.get("id") == agent_id:
            return agent
    return {}


def _resolve_provider(model_name: str, model_provider: Optional[str]) -> str:
    """根据模型名和配置解析实际使用的 provider 字符串"""
    if model_provider and model_provider.upper() != "AUTO":
        return model_provider.lower()

    name = (model_name or "").lower()

    # 带 / 的通常是平台模型，默认通过 SiliconFlow 统一访问
    if "/" in (model_name or ""):
        return "siliconflow"

    if name.startswith("gemini"):
        return "gemini"
    if name.startswith("deepseek"):
        return "deepseek"
    if name.startswith("qwen"):
        # 官方通义千问兼容接口
        return "qwen"

    # 兜底交给 SiliconFlow 统一转发
    return "siliconflow"


def _create_llm_for_agent(agent_id: str, default_model: str = "Qwen/Qwen2.5-7B-Instruct", default_temp: float = 0.3):
    """为指定智能体创建 LLM 适配器，使用 agent_configs.json 中的配置"""
    cfg = _get_agent_config(agent_id) or {}
    model_name = cfg.get("modelName", default_model)
    temperature = cfg.get("temperature", default_temp)
    provider = _resolve_provider(model_name, cfg.get("modelProvider"))

    logger.debug(
        f"[Debate] 创建智能体 LLM: id={agent_id}, provider={provider}, model={model_name}, temp={temperature}"
    )

    return create_agent_llm(
        provider=provider,
        model=model_name,
        temperature=temperature,
    )


class DebateRequest(BaseModel):
    """辩论请求模型"""
    stock_code: str = Field(..., description="股票代码")
    analysis_data: Dict[str, Any] = Field(..., description="分析数据")
    debate_type: str = Field("research", description="辩论类型: research/risk")
    rounds: int = Field(1, description="辩论轮数", ge=1, le=5)
    
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

        analysis_data = request.analysis_data or {}

        # 构建智能体期望的状态结构
        state = _build_research_state(request.stock_code, analysis_data)

        # 为三个智能体创建独立 LLM（均从 agent_configs.json 读取配置）
        bull_llm = _create_llm_for_agent("bull_researcher")
        bear_llm = _create_llm_for_agent("bear_researcher")
        manager_llm = _create_llm_for_agent("research_manager")

        bull_agent = create_bull_researcher(llm=bull_llm, memory=None)
        bear_agent = create_bear_researcher(llm=bear_llm, memory=None)
        manager_agent = create_research_manager(llm=manager_llm, memory=None)

        bull_rounds: List[Dict[str, Any]] = []
        bear_rounds: List[Dict[str, Any]] = []

        # 多轮交替辩论：Bull -> Bear
        for round_num in range(request.rounds):
            logger.info(f"第 {round_num + 1} 轮辩论")

            # 看涨观点
            bull_result = await asyncio.to_thread(bull_agent, state)
            state.update(bull_result)
            invest_state = state.get("investment_debate_state", {})
            bull_content = invest_state.get("current_response", "")
            bull_rounds.append({
                "round": round_num + 1,
                "content": bull_content,
            })
            log_debate_round("bull", round_num + 1, bull_content)

            # 看跌观点
            bear_result = await asyncio.to_thread(bear_agent, state)
            state.update(bear_result)
            invest_state = state.get("investment_debate_state", {})
            bear_content = invest_state.get("current_response", "")
            bear_rounds.append({
                "round": round_num + 1,
                "content": bear_content,
            })
            log_debate_round("bear", round_num + 1, bear_content)

        # 研究经理综合决策
        manager_result = await asyncio.to_thread(manager_agent, state)
        state.update(manager_result)
        invest_state = state.get("investment_debate_state", {})
        decision_text = manager_result.get("investment_plan", invest_state.get("judge_decision", ""))

        # 基于文本推断推荐方向与置信度
        recommendation = _infer_recommendation_from_text(decision_text)
        confidence = _infer_confidence_from_text(decision_text)

        bull_view_state = state.get("investment_debate_state", {})
        bull_view = {
            "content": bull_rounds[-1]["content"] if bull_rounds else "",
            "history": bull_view_state.get("bull_history", ""),
        }
        bear_view = {
            "content": bear_rounds[-1]["content"] if bear_rounds else "",
            "history": bull_view_state.get("bear_history", ""),
        }

        # 使用已有强度计算函数做一个简单评分（传入抽象化视图结构）
        bull_strength = _calculate_view_strength([
            {"recommendation": recommendation, "confidence": confidence}
        ])
        bear_strength = _calculate_view_strength([
            {"recommendation": recommendation, "confidence": 1 - confidence}
        ])

        # 生成辩论总结（只用最后一轮的精简句子作为 key_points）
        debate_summary = _generate_debate_summary(
            [
                {
                    "recommendation": recommendation,
                    "key_points": [bull_view["content"][:120]],
                }
            ],
            [
                {
                    "recommendation": recommendation,
                    "key_points": [bear_view["content"][:120]],
                }
            ],
            {"recommendation": recommendation},
        )

        response = ResearchDebateResponse(
            success=True,
            stock_code=request.stock_code,
            bull_view=bull_view,
            bear_view=bear_view,
            bull_strength=bull_strength,
            bear_strength=bear_strength,
            final_decision={
                "content": decision_text,
                "state": invest_state,
            },
            recommendation=recommendation,
            confidence=confidence,
            debate_summary=debate_summary,
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

        analysis_data = request.analysis_data or {}

        # 构建风险团队需要的状态结构
        state = _build_risk_state(request.stock_code, analysis_data)

        # 为四个风险相关智能体创建 LLM
        aggressive_llm = _create_llm_for_agent("risk_aggressive")
        conservative_llm = _create_llm_for_agent("risk_conservative")
        neutral_llm = _create_llm_for_agent("risk_neutral")
        manager_llm = _create_llm_for_agent("risk_manager")

        aggressive_agent = create_risky_debator(llm=aggressive_llm)
        conservative_agent = create_safe_debator(llm=conservative_llm)
        neutral_agent = create_neutral_debator(llm=neutral_llm)
        risk_manager_agent = create_risk_manager(llm=manager_llm, memory=None)

        aggressive_last: str = ""
        conservative_last: str = ""
        neutral_last: str = ""

        # 默认一轮即可，可根据 request.rounds 控制多轮交替
        for round_num in range(request.rounds):
            logger.info(f"风险辩论 第 {round_num + 1} 轮")

            # 激进视角
            ag_result = await asyncio.to_thread(aggressive_agent, state)
            state.update(ag_result)
            risk_state = state.get("risk_debate_state", {})
            aggressive_last = risk_state.get("current_risky_response", "")
            log_debate_round("risk_aggressive", round_num + 1, aggressive_last)

            # 保守视角
            safe_result = await asyncio.to_thread(conservative_agent, state)
            state.update(safe_result)
            risk_state = state.get("risk_debate_state", {})
            conservative_last = risk_state.get("current_safe_response", "")
            log_debate_round("risk_conservative", round_num + 1, conservative_last)

            # 中立视角
            neutral_result = await asyncio.to_thread(neutral_agent, state)
            state.update(neutral_result)
            risk_state = state.get("risk_debate_state", {})
            neutral_last = risk_state.get("current_neutral_response", "")
            log_debate_round("risk_neutral", round_num + 1, neutral_last)

        # 风险经理综合决策
        risk_manager_result = await asyncio.to_thread(risk_manager_agent, state)
        state.update(risk_manager_result)
        risk_state = state.get("risk_debate_state", {})
        risk_decision_text = risk_manager_result.get("final_trade_decision", risk_state.get("judge_decision", ""))

        # 基于文本推断风险分数与等级
        risk_score = _infer_risk_score_from_text(risk_decision_text)
        risk_level = _get_risk_level(risk_score)

        # 生成仓位建议（使用简单置信度 0.6 作为输入）
        position_advice = _generate_position_advice(
            risk_score,
            {"confidence": 0.6},
        )

        aggressive_view = {
            "content": aggressive_last,
            "history": risk_state.get("risky_history", ""),
        }
        conservative_view = {
            "content": conservative_last,
            "history": risk_state.get("safe_history", ""),
        }
        neutral_view = {
            "content": neutral_last,
            "history": risk_state.get("neutral_history", ""),
        }

        response = RiskDebateResponse(
            success=True,
            stock_code=request.stock_code,
            aggressive_view=aggressive_view,
            conservative_view=conservative_view,
            neutral_view=neutral_view,
            risk_level=risk_level,
            risk_score=risk_score,
            position_advice={
                "summary": risk_decision_text,
                **position_advice,
            },
            risk_factors=["详见风控经理详细分析文本"],
            mitigation_strategies=["根据风控建议控制仓位、设置止损并关注系统性风险。"],
        )

        logger.success(f"风险辩论完成，风险等级: {risk_level}")
        return response

    except Exception as e:
        logger.error(f"风险辩论失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"辩论失败: {str(e)}")


def _build_research_state(stock_code: str, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
    """将前端分析结果转换为研究辩论智能体需要的状态结构"""

    def _get(agent_id: str) -> str:
        val = analysis_data.get(agent_id)
        if isinstance(val, str):
            return val
        if val is None:
            return ""
        return str(val)

    # 市场研究 = 中国市场 + 宏观 + 技术 + 资金的综合
    market_parts: List[str] = []
    for key in ["china_market", "macro", "technical", "funds"]:
        content = _get(key)
        if content:
            market_parts.append(f"[{key}]\n{content}")
    market_report = "\n\n".join(market_parts)

    sentiment_report = _get("social_analyst")
    news_report = _get("news_analyst")
    fundamentals_report = _get("fundamental")

    return {
        "company_of_interest": stock_code,
        "trade_date": datetime.now().strftime("%Y-%m-%d"),
        "analysis_data": analysis_data,
        "market_report": market_report,
        "sentiment_report": sentiment_report,
        "news_report": news_report,
        "fundamentals_report": fundamentals_report,
        # 辩论状态初始化
        "investment_debate_state": {
            "bull_history": "",
            "bear_history": "",
            "history": "",
            "current_response": "",
            "judge_decision": "",
            "count": 0,
        },
        "investment_plan": "",
    }


def _build_risk_state(stock_code: str, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
    """基于研究状态扩展出风险团队需要的状态结构"""
    state = _build_research_state(stock_code, analysis_data)

    # 交易员/策略计划：优先使用 trader，其次 gm，再次 research_manager
    trader_plan = analysis_data.get("trader") or analysis_data.get("gm") or analysis_data.get("research_manager") or ""
    if not isinstance(trader_plan, str):
        trader_plan = str(trader_plan)

    state.update(
        {
            "investment_plan": trader_plan or state.get("investment_plan", ""),
            "trader_investment_plan": trader_plan,
            "risk_debate_state": {
                "risky_history": "",
                "safe_history": "",
                "neutral_history": "",
                "history": "",
                "latest_speaker": "",
                "current_risky_response": "",
                "current_safe_response": "",
                "current_neutral_response": "",
                "judge_decision": "",
                "count": 0,
            },
        }
    )

    return state


def _infer_recommendation_from_text(text: str) -> str:
    """从研究经理输出文本中粗略推断 BUY/SELL/HOLD"""
    if not text:
        return "HOLD"
    t = text.upper()
    t_cn = text

    if any(kw in t_cn for kw in ["强烈买入", "积极买入", "建议买入", "加仓", "看多"]):
        return "BUY"
    if any(kw in t_cn for kw in ["建议卖出", "清仓", "减仓", "止损", "看空"]):
        return "SELL"
    if any(kw in t_cn for kw in ["持有", "观望", "中性"]):
        return "HOLD"

    if "BUY" in t:
        return "BUY"
    if "SELL" in t:
        return "SELL"
    if "HOLD" in t:
        return "HOLD"
    return "HOLD"


def _infer_confidence_from_text(text: str) -> float:
    """从措辞强弱大致估计一个 0-1 的置信度"""
    if not text:
        return 0.5
    t = text
    if any(kw in t for kw in ["强烈", "极高把握", "非常确定", "极大概率"]):
        return 0.85
    if any(kw in t for kw in ["相对乐观", "倾向于", "更支持"]):
        return 0.7
    if any(kw in t for kw in ["谨慎", "不确定", "存在较大不确定性"]):
        return 0.55
    return 0.6


def _infer_risk_score_from_text(text: str) -> float:
    """从风控经理文本中粗略推断风险分数 0-1"""
    if not text:
        return 0.5
    t = text
    if any(kw in t for kw in ["高风险", "中高风险", "波动较大", "剧烈波动"]):
        return 0.8
    if any(kw in t for kw in ["低风险", "风险较低", "稳健", "防御"]):
        return 0.25
    if any(kw in t for kw in ["中等风险", "风险可控", "中风险"]):
        return 0.5
    return 0.5


def _get_risk_level(risk_score: float) -> str:
    """根据风险分数返回风险等级"""
    if risk_score >= 0.7:
        return "HIGH"
    elif risk_score >= 0.4:
        return "MEDIUM"
    else:
        return "LOW"


def _calculate_view_strength(views: List[Dict]) -> float:
    """根据多轮观点的置信度与一致性，计算观点强度（0-1）"""
    if not views:
        return 0.0

    confidences = [v.get("confidence", 0.5) for v in views]
    avg_confidence = sum(confidences) / len(confidences)

    recommendations = [v.get("recommendation", "HOLD") for v in views]
    consistency = len(set(recommendations)) / len(recommendations)

    strength = avg_confidence * (2 - consistency)
    return min(1.0, max(0.0, strength))


def _generate_debate_summary(
    bull_views: List[Dict],
    bear_views: List[Dict],
    decision: Dict,
) -> str:
    """根据多空观点与最终决策生成简要辩论总结"""
    bull_points = len(bull_views or [])
    bear_points = len(bear_views or [])
    recommendation = (decision or {}).get("recommendation", "HOLD")

    rounds = max(bull_points, bear_points) or 1
    summary = f"经过{rounds}轮激烈辩论，"

    if recommendation == "BUY":
        summary += "看涨观点占据上风，建议买入。"
    elif recommendation == "SELL":
        summary += "看跌观点更有说服力，建议卖出。"
    else:
        summary += "多空双方势均力敌，建议持有观望。"

    return summary


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
