"""
策略系统API
提供策略运行、回测、管理等接口
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio

from backend.utils.logging_config import get_logger
from backend.utils.tool_logging import log_api_call
from backend.strategies import StrategyManager

logger = get_logger("api.strategy")
router = APIRouter(prefix="/api/strategy", tags=["Strategy System"])

# 创建全局策略管理器
strategy_manager = StrategyManager()


class StrategyRunRequest(BaseModel):
    """策略运行请求"""
    stock_code: str = Field(..., description="股票代码")
    strategy_ids: Optional[List[str]] = Field(None, description="要运行的策略ID列表")
    include_fundamental: bool = Field(True, description="是否包含基本面数据")
    combine_method: str = Field("weighted_vote", description="信号组合方法")


class StrategyBacktestRequest(BaseModel):
    """策略回测请求"""
    strategy_id: str = Field(..., description="策略ID")
    stock_code: str = Field(..., description="股票代码")
    start_date: str = Field(..., description="开始日期 YYYY-MM-DD")
    end_date: str = Field(..., description="结束日期 YYYY-MM-DD")
    initial_capital: float = Field(100000, description="初始资金")


class StrategyConfigRequest(BaseModel):
    """策略配置请求"""
    strategy_id: str = Field(..., description="策略ID")
    is_active: bool = Field(..., description="是否激活")
    weight: float = Field(1.0, ge=0, le=1, description="策略权重")
    params: Optional[Dict[str, Any]] = Field(None, description="策略参数")


@router.get("/list")
@log_api_call("获取策略列表")
async def list_strategies(
    category: Optional[str] = Query(None, description="策略类别筛选"),
    is_active: Optional[bool] = Query(None, description="是否只显示激活的策略")
):
    """
    获取所有可用策略列表
    
    Returns:
        策略列表及详细信息
    """
    try:
        info = strategy_manager.get_strategy_info()
        
        # 筛选
        strategies = info["strategies"]
        
        if category:
            strategies = {
                k: v for k, v in strategies.items()
                if v["category"] == category
            }
            
        if is_active is not None:
            strategies = {
                k: v for k, v in strategies.items()
                if v["is_active"] == is_active
            }
            
        return {
            "success": True,
            "total": len(strategies),
            "active_count": sum(1 for s in strategies.values() if s["is_active"]),
            "strategies": strategies,
            "categories": [
                {"value": "value_investing", "label": "价值投资", "count": 3},
                {"value": "technical", "label": "技术分析", "count": 5},
                {"value": "quantitative", "label": "量化因子", "count": 4},
                {"value": "folk", "label": "民间策略", "count": 6},
                {"value": "machine_learning", "label": "机器学习", "count": 2}
            ]
        }
        
    except Exception as e:
        logger.error(f"获取策略列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run")
@log_api_call("运行策略")
async def run_strategies(request: StrategyRunRequest):
    """
    运行指定策略并生成交易信号
    
    Args:
        request: 策略运行请求
        
    Returns:
        策略信号和组合决策
    """
    try:
        # 获取市场数据
        # TODO: 从实际数据源获取
        import pandas as pd
        import numpy as np
        
        dates = pd.date_range(end=datetime.now(), periods=100)
        market_data = pd.DataFrame({
            'open': np.random.randn(100) * 2 + 100,
            'high': np.random.randn(100) * 2 + 102,
            'low': np.random.randn(100) * 2 + 98,
            'close': np.random.randn(100) * 2 + 100,
            'volume': np.random.randint(1000000, 10000000, 100)
        }, index=dates)
        
        # 获取基本面数据（如果需要）
        fundamental_data = None
        if request.include_fundamental:
            # TODO: 从实际数据源获取
            fundamental_data = {
                "roe": 18.5,
                "pe_ttm": 22.3,
                "pb": 2.8,
                "revenue_growth": 15.2,
                "profit_growth": 12.8,
                "debt_to_asset": 35.6,
                "current_ratio": 2.1,
                "gross_margin": 42.5,
                "operating_cash_flow": 1000000000,
                "free_cash_flow": 800000000,
                "eps_ttm": 4.5
            }
            
        # 如果指定了策略ID，临时激活这些策略
        original_active = strategy_manager.active_strategies.copy()
        
        if request.strategy_ids:
            strategy_manager.active_strategies = set(request.strategy_ids)
            
        # 运行策略
        signals = await strategy_manager.run_strategies(
            request.stock_code,
            market_data,
            fundamental_data
        )
        
        # 恢复原始激活状态
        if request.strategy_ids:
            strategy_manager.active_strategies = original_active
            
        # 组合信号
        combined_decision = strategy_manager.combine_signals(
            signals,
            method=request.combine_method
        )
        
        # 格式化响应
        return {
            "success": True,
            "stock_code": request.stock_code,
            "timestamp": datetime.now().isoformat(),
            "signals": [
                {
                    "strategy_id": s.strategy_id,
                    "strategy_name": s.strategy_name,
                    "signal_type": s.signal_type.value,
                    "strength": s.strength,
                    "confidence": s.confidence,
                    "target_price": s.target_price,
                    "stop_loss": s.stop_loss,
                    "position_size": s.position_size,
                    "reasons": s.reasons[:3]  # 最多3条理由
                }
                for s in signals
            ],
            "combined_decision": combined_decision,
            "recommendation": _get_recommendation(combined_decision)
        }
        
    except Exception as e:
        logger.error(f"运行策略失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/backtest")
@log_api_call("回测策略")
async def backtest_strategy(request: StrategyBacktestRequest):
    """
    回测单个策略
    
    Args:
        request: 回测请求
        
    Returns:
        回测结果和绩效指标
    """
    try:
        # 获取策略
        if request.strategy_id not in strategy_manager.strategies:
            raise ValueError(f"策略 {request.strategy_id} 不存在")
            
        strategy = strategy_manager.strategies[request.strategy_id]
        
        # 运行回测
        performance = await strategy.backtest(
            request.stock_code,
            request.start_date,
            request.end_date,
            request.initial_capital
        )
        
        # 保存回测结果
        if request.strategy_id not in strategy_manager.performance_history:
            strategy_manager.performance_history[request.strategy_id] = []
            
        strategy_manager.performance_history[request.strategy_id].append(performance)
        
        return {
            "success": True,
            "strategy_id": request.strategy_id,
            "strategy_name": strategy.name,
            "stock_code": request.stock_code,
            "period": f"{request.start_date} 至 {request.end_date}",
            "performance": {
                "total_return": performance.total_return,
                "annual_return": performance.annual_return,
                "sharpe_ratio": performance.sharpe_ratio,
                "max_drawdown": performance.max_drawdown,
                "win_rate": performance.win_rate,
                "total_trades": performance.total_trades,
                "profit_factor": performance.profit_factor
            },
            "details": {
                "win_trades": performance.win_trades,
                "loss_trades": performance.loss_trades,
                "avg_win": performance.avg_win,
                "avg_loss": performance.avg_loss,
                "volatility": performance.volatility
            }
        }
        
    except Exception as e:
        logger.error(f"回测失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/backtest/portfolio")
@log_api_call("回测策略组合")
async def backtest_portfolio(
    stock_codes: List[str] = Query(..., description="股票代码列表"),
    start_date: str = Query(..., description="开始日期"),
    end_date: str = Query(..., description="结束日期"),
    initial_capital: float = Query(1000000, description="初始资金")
):
    """
    回测策略组合在多只股票上的表现
    
    Returns:
        组合回测结果
    """
    try:
        results = await strategy_manager.backtest_portfolio(
            stock_codes,
            start_date,
            end_date,
            initial_capital
        )
        
        return {
            "success": True,
            "portfolio": {
                "stocks": stock_codes,
                "period": f"{start_date} 至 {end_date}",
                "initial_capital": initial_capital
            },
            "performance": results,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"组合回测失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/config")
@log_api_call("配置策略")
async def configure_strategy(request: StrategyConfigRequest):
    """
    配置策略参数和激活状态
    
    Args:
        request: 策略配置请求
        
    Returns:
        配置结果
    """
    try:
        # 检查策略是否存在
        if request.strategy_id not in strategy_manager.strategies:
            raise ValueError(f"策略 {request.strategy_id} 不存在")
            
        # 更新激活状态
        if request.is_active:
            strategy_manager.activate_strategy(request.strategy_id, request.weight)
        else:
            strategy_manager.deactivate_strategy(request.strategy_id)
            
        # 更新参数（如果提供）
        if request.params:
            strategy = strategy_manager.strategies[request.strategy_id]
            strategy.params.update(request.params)
            
        return {
            "success": True,
            "strategy_id": request.strategy_id,
            "is_active": request.is_active,
            "weight": request.weight,
            "message": f"策略 {request.strategy_id} 配置已更新"
        }
        
    except Exception as e:
        logger.error(f"配置策略失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance/{strategy_id}")
@log_api_call("获取策略表现")
async def get_strategy_performance(
    strategy_id: str,
    limit: int = Query(10, description="返回记录数量")
):
    """
    获取策略历史表现
    
    Args:
        strategy_id: 策略ID
        limit: 返回记录数量
        
    Returns:
        策略历史表现数据
    """
    try:
        if strategy_id not in strategy_manager.strategies:
            raise ValueError(f"策略 {strategy_id} 不存在")
            
        history = strategy_manager.performance_history.get(strategy_id, [])
        
        # 获取最近的记录
        recent_history = history[-limit:] if len(history) > limit else history
        
        # 计算统计数据
        if recent_history:
            avg_return = sum(p.total_return for p in recent_history) / len(recent_history)
            avg_sharpe = sum(p.sharpe_ratio for p in recent_history) / len(recent_history)
            avg_win_rate = sum(p.win_rate for p in recent_history) / len(recent_history)
        else:
            avg_return = avg_sharpe = avg_win_rate = 0
            
        return {
            "success": True,
            "strategy_id": strategy_id,
            "strategy_name": strategy_manager.strategies[strategy_id].name,
            "statistics": {
                "avg_return": avg_return,
                "avg_sharpe_ratio": avg_sharpe,
                "avg_win_rate": avg_win_rate,
                "total_backtests": len(history)
            },
            "history": [
                {
                    "total_return": p.total_return,
                    "sharpe_ratio": p.sharpe_ratio,
                    "max_drawdown": p.max_drawdown,
                    "win_rate": p.win_rate,
                    "total_trades": p.total_trades,
                    "start_date": p.start_date.isoformat(),
                    "end_date": p.end_date.isoformat()
                }
                for p in recent_history
            ]
        }
        
    except Exception as e:
        logger.error(f"获取策略表现失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _get_recommendation(decision: Dict[str, Any]) -> str:
    """根据组合决策生成推荐文本"""
    action = decision.get("action", "HOLD")
    confidence = decision.get("confidence", 0)
    
    if action == "BUY":
        if confidence > 0.8:
            return "强烈建议买入"
        elif confidence > 0.6:
            return "建议买入"
        else:
            return "可以考虑买入"
    elif action == "SELL":
        if confidence > 0.8:
            return "强烈建议卖出"
        elif confidence > 0.6:
            return "建议卖出"
        else:
            return "可以考虑卖出"
    else:
        return "建议观望"


# 测试端点
@router.get("/test")
async def test_strategy_api():
    """测试策略API是否正常工作"""
    return {
        "status": "ok",
        "message": "Strategy API is working",
        "features": [
            "Strategy listing",
            "Strategy execution",
            "Backtesting",
            "Portfolio optimization",
            "Performance tracking"
        ],
        "active_strategies": len(strategy_manager.active_strategies),
        "total_strategies": len(strategy_manager.strategies),
        "timestamp": datetime.now().isoformat()
    }
