"""
回测系统 API 路由
"""

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import pandas as pd
import json
import logging
import uuid

from ..backtest.engine import BacktestEngine, BacktestConfig, BacktestResult
from ..backtest.data_loader import DataLoader, DataSource, load_stock_data
from ..strategies.base import StrategyConfig, get_strategy_registry
# 导入策略模块以触发策略注册
from ..strategies import (
    VegasADXStrategy,
    EMABreakoutStrategy,
    BuffettValueStrategy,
    GrahamMarginStrategy,
    LynchGrowthStrategy,
    MACDCrossoverStrategy,
    BollingerBreakoutStrategy,
    TurtleTradingStrategy,
    DragonLeaderStrategy,
    MartingaleRefinedStrategy,
    ScalpingBladeStrategy,
    TridentStrategy,
    SentimentResonanceStrategy,
    DebateWeightedStrategy,
    LimitUpTradingStrategy,
    VolumePriceSurgeStrategy
)

logger = logging.getLogger(__name__)

# 创建路由
router = APIRouter(prefix="/api/backtest", tags=["backtest"])


class BacktestRequest(BaseModel):
    """回测请求"""
    stock_code: str = Field(..., description="股票代码")
    strategy_name: Optional[str] = Field(None, description="策略名称")  # 兼容strategy_id
    strategy_id: Optional[str] = Field(None, description="策略ID")  # 新增支持
    start_date: str = Field(..., description="开始日期 YYYY-MM-DD")
    end_date: str = Field(..., description="结束日期 YYYY-MM-DD")
    initial_capital: float = Field(100000, description="初始资金")
    strategy_params: Optional[Dict[str, Any]] = Field(None, description="策略参数")
    risk_params: Optional[Dict[str, Any]] = Field(None, description="风险参数")
    use_ai_agents: bool = Field(False, description="是否使用AI智能体")
    ai_agent_names: Optional[List[str]] = Field(None, description="AI智能体列表")


class BacktestResponse(BaseModel):
    """回测响应"""
    task_id: str
    status: str
    message: str
    result: Optional[Dict] = None


class BacktestStatusResponse(BaseModel):
    """回测状态响应"""
    task_id: str
    status: str  # pending, running, completed, failed


class StrategyInfo(BaseModel):
    """策略信息"""
    id: str
    name: str
    category: str
    description: str
    parameters: Dict[str, Any]
    avgWinRate: Optional[float] = None
    icon: str = "📊"


class StrategiesResponse(BaseModel):
    """策略列表响应"""
    success: bool
    strategies: List[StrategyInfo]
    total: int


# 存储回测任务状态（实际应用中应使用 Redis 或数据库）
backtest_tasks: Dict[str, BacktestStatusResponse] = {}


@router.post("/run", response_model=BacktestResponse)
async def run_backtest(
    request: BacktestRequest,
    background_tasks: BackgroundTasks
):
    """
    运行回测
    
    异步执行回测任务，返回任务ID供查询状态
    """
    try:
        # 生成任务ID
        task_id = str(uuid.uuid4())
        
        # 初始化任务状态
        backtest_tasks[task_id] = BacktestStatusResponse(
            task_id=task_id,
            status="pending",
            progress=0.0,
            message="回测任务已创建，等待执行..."
        )
        
        # 添加到后台任务
        background_tasks.add_task(
            execute_backtest,
            task_id,
            request
        )
        
        return BacktestResponse(
            task_id=task_id,
            status="pending",
            message="回测任务已提交，请使用任务ID查询状态"
        )
        
    except Exception as e:
        logger.error(f"创建回测任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_backtest_service_status():
    """获取回测服务整体状态"""
    running = [t for t in backtest_tasks.values() if t.status == "running"]
    pending = [t for t in backtest_tasks.values() if t.status == "pending"]
    return {
        "success": True,
        "service": "running",
        "active_tasks": len(running),
        "pending_tasks": len(pending),
        "total_tasks": len(backtest_tasks)
    }


@router.get("/status/{task_id}", response_model=BacktestStatusResponse)
async def get_backtest_status(task_id: str):
    """获取回测任务状态"""
    if task_id not in backtest_tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return backtest_tasks[task_id]


@router.post("/quick", response_model=Dict)
async def quick_backtest(request: BacktestRequest):
    """
    快速回测（同步）
    
    适用于小数据量的快速回测，直接返回结果
    """
    try:
        # 兼容处理：优先使用strategy_id，其次使用strategy_name
        strategy_name = request.strategy_id or request.strategy_name
        if not strategy_name:
            raise HTTPException(status_code=400, detail="必须提供 strategy_id 或 strategy_name")
        
        # 加载数据
        logger.info(f"加载数据: {request.stock_code}, 日期范围: {request.start_date} - {request.end_date}")
        loader = DataLoader(DataSource.AKSHARE)
        try:
            data = loader.load_stock_data(
                request.stock_code,
                request.start_date,
                request.end_date
            )
            logger.info(f"数据加载结果: data is None={data is None}, empty={data.empty if data is not None else 'N/A'}")
        except Exception as load_error:
            logger.error(f"数据加载异常: {load_error}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"数据加载失败: {str(load_error)}")

        if data is None or data.empty:
            logger.warning(f"无法获取股票数据: {request.stock_code}")
            raise HTTPException(status_code=404, detail=f"无法获取股票数据: {request.stock_code}")
        
        # 添加技术指标
        data = loader.add_technical_indicators(data)
        
        # 创建策略
        strategy_config = StrategyConfig(
            name=strategy_name,
            parameters=request.strategy_params or {},
            risk_params=request.risk_params or {}
        )
        
        strategy = create_strategy(strategy_name, strategy_config)
        if not strategy:
            raise HTTPException(status_code=400, detail=f"未找到策略: {strategy_name}")
        
        # 创建回测引擎
        backtest_config = BacktestConfig(
            initial_capital=request.initial_capital,
            start_date=request.start_date,
            end_date=request.end_date,
            use_ai_agents=request.use_ai_agents,
            ai_agent_names=request.ai_agent_names or []
        )
        
        engine = BacktestEngine(backtest_config)
        
        # 运行回测
        result = engine.run(strategy, data, request.stock_code)
        
        # 返回结果
        return {
            "success": True,
            "summary": {
                "stock_code": request.stock_code,
                "strategy": strategy_name,
                "start_date": request.start_date,
                "end_date": request.end_date,
                "initial_capital": request.initial_capital,
                "final_capital": result.final_capital,
                "total_return": f"{((result.final_capital / request.initial_capital) - 1) * 100:.2f}%"
            },
            "metrics": result.metrics.to_dict(),
            "equity_curve": result.equity_curve.reset_index().to_dict(orient="records")[-100:],  # 最近100个数据点
            "trades": [
                {
                    "timestamp": t.timestamp.isoformat(),
                    "side": t.side,
                    "price": t.price,
                    "quantity": t.quantity,
                    "commission": t.commission
                }
                for t in result.trades[-20:]  # 最近20笔交易
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"快速回测失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# 旧的list_strategies已删除，使用下面的get_strategies替代


@router.get("/debug/akshare")
async def debug_akshare(symbol: str = Query("600519", description="股票代码")):
    """调试AKShare数据加载"""
    import akshare as ak
    import os
    import sys

    result = {
        "cwd": os.getcwd(),
        "python_path": sys.executable,
        "akshare_version": ak.__version__,
    }

    try:
        # 直接调用AKShare
        df = ak.stock_zh_a_hist(
            symbol=symbol,
            period="daily",
            start_date="20241201",
            end_date="20241231",
            adjust="qfq"
        )
        result["direct_akshare"] = {
            "success": True,
            "rows": len(df) if df is not None else 0,
            "columns": list(df.columns) if df is not None else []
        }
    except Exception as e:
        result["direct_akshare"] = {
            "success": False,
            "error": str(e)
        }

    try:
        # 通过DataLoader调用
        loader = DataLoader(DataSource.AKSHARE)
        data = loader.load_stock_data(symbol, "2024-12-01", "2024-12-31")
        result["data_loader"] = {
            "success": data is not None and not data.empty,
            "rows": len(data) if data is not None else 0,
            "columns": list(data.columns) if data is not None else []
        }
    except Exception as e:
        result["data_loader"] = {
            "success": False,
            "error": str(e)
        }

    return result


@router.get("/data/preview")
async def preview_data(
    symbol: str = Query(..., description="股票代码"),
    start_date: str = Query(..., description="开始日期"),
    end_date: str = Query(..., description="结束日期"),
    limit: int = Query(100, description="返回数据条数限制")
):
    """预览历史数据"""
    try:
        loader = DataLoader(DataSource.AKSHARE)
        data = loader.load_stock_data(symbol, start_date, end_date)
        
        if data is None or data.empty:
            raise HTTPException(status_code=404, detail="无法获取股票数据")
        
        # 添加技术指标
        data = loader.add_technical_indicators(data)
        
        # 限制返回数据量
        if len(data) > limit:
            data = data.tail(limit)
        
        # 转换为字典格式
        result = data.reset_index().to_dict(orient="records")
        
        return {
            "success": True,
            "symbol": symbol,
            "total_records": len(data),
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"预览数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compare", response_model=Dict)
async def compare_strategies(
    stock_code: str = Query(..., description="股票代码"),
    strategy_names: List[str] = Query(..., description="策略名称列表"),
    start_date: str = Query(..., description="开始日期"),
    end_date: str = Query(..., description="结束日期"),
    initial_capital: float = Query(100000, description="初始资金")
):
    """
    比较多个策略的回测结果
    """
    try:
        # 加载数据
        loader = DataLoader(DataSource.AKSHARE)
        data = loader.load_stock_data(stock_code, start_date, end_date)
        
        if data is None or data.empty:
            raise HTTPException(status_code=404, detail="无法获取股票数据")
        
        # 添加技术指标
        data = loader.add_technical_indicators(data)
        
        results = {}
        
        for strategy_name in strategy_names:
            try:
                # 创建策略
                strategy_config = StrategyConfig(name=strategy_name)
                strategy = create_strategy(strategy_name, strategy_config)
                
                if not strategy:
                    logger.warning(f"策略不存在: {strategy_name}")
                    continue
                
                # 创建回测引擎
                backtest_config = BacktestConfig(
                    initial_capital=initial_capital,
                    start_date=start_date,
                    end_date=end_date
                )
                
                engine = BacktestEngine(backtest_config)
                
                # 运行回测
                result = engine.run(strategy, data.copy(), stock_code)
                
                # 保存结果
                results[strategy_name] = {
                    "metrics": result.metrics.to_dict(),
                    "final_capital": result.final_capital,
                    "total_return": ((result.final_capital / initial_capital) - 1),
                    "trade_count": len(result.trades)
                }
                
            except Exception as e:
                logger.error(f"策略 {strategy_name} 回测失败: {e}")
                results[strategy_name] = {
                    "error": str(e)
                }
        
        return {
            "success": True,
            "stock_code": stock_code,
            "period": f"{start_date} to {end_date}",
            "comparison": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"策略比较失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def execute_backtest(task_id: str, request: BacktestRequest):
    """后台执行回测任务"""
    try:
        # 兼容处理
        strategy_name = request.strategy_id or request.strategy_name
        if not strategy_name:
            raise ValueError("必须提供 strategy_id 或 strategy_name")
        
        # 更新状态
        backtest_tasks[task_id].status = "running"
        backtest_tasks[task_id].progress = 0.1
        backtest_tasks[task_id].message = "正在加载数据..."
        
        # 加载数据
        loader = DataLoader(DataSource.AKSHARE)
        data = loader.load_stock_data(
            request.stock_code,
            request.start_date,
            request.end_date
        )
        
        if data is None or data.empty:
            raise ValueError("无法获取股票数据")
        
        # 更新进度
        backtest_tasks[task_id].progress = 0.3
        backtest_tasks[task_id].message = "正在计算技术指标..."
        
        # 添加技术指标
        data = loader.add_technical_indicators(data)
        
        # 创建策略
        backtest_tasks[task_id].progress = 0.4
        backtest_tasks[task_id].message = "正在初始化策略..."
        
        strategy_config = StrategyConfig(
            name=strategy_name,
            parameters=request.strategy_params or {},
            risk_params=request.risk_params or {}
        )
        
        strategy = create_strategy(strategy_name, strategy_config)
        if not strategy:
            raise ValueError(f"未找到策略: {strategy_name}")
        
        # 创建回测引擎
        backtest_tasks[task_id].progress = 0.5
        backtest_tasks[task_id].message = "正在运行回测..."
        
        backtest_config = BacktestConfig(
            initial_capital=request.initial_capital,
            start_date=request.start_date,
            end_date=request.end_date,
            use_ai_agents=request.use_ai_agents,
            ai_agent_names=request.ai_agent_names or []
        )
        
        engine = BacktestEngine(backtest_config)
        
        # 运行回测
        result = engine.run(strategy, data, request.stock_code)
        
        # 更新结果
        backtest_tasks[task_id].status = "completed"
        backtest_tasks[task_id].progress = 1.0
        backtest_tasks[task_id].message = "回测完成"
        backtest_tasks[task_id].result = result.to_dict()
        
    except Exception as e:
        logger.error(f"回测任务 {task_id} 失败: {e}", exc_info=True)
        backtest_tasks[task_id].status = "failed"
        backtest_tasks[task_id].progress = 0.0
        backtest_tasks[task_id].message = "回测失败"
        backtest_tasks[task_id].error = str(e)


@router.get("/strategies", response_model=StrategiesResponse)
async def get_strategies():
    """
    获取所有可用策略列表
    
    Returns:
        策略列表，包含：
        - id: 策略ID
        - name: 策略名称
        - category: 类别
        - description: 描述
        - parameters: 参数
        - avgWinRate: 平均胜率
        - icon: 图标
    """
    try:
        from ..services.strategy.selector import StrategySelector
        
        selector = StrategySelector()
        strategies = selector._load_strategies()
        
        # 类别图标映射
        category_icons = {
            "technical": "📊",
            "ai_composite": "🤖",
            "trend_following": "📈",
            "folk_strategy": "🎯",
            "value_investing": "💎"
        }
        
        # 格式化为前端需要的格式
        formatted_strategies = []
        for strategy in strategies:
            formatted_strategies.append(StrategyInfo(
                id=strategy["strategy_id"],
                name=strategy["name"],
                category=strategy["category"],
                description=strategy["description"],
                parameters=strategy["parameters"],
                avgWinRate=0.65,  # 默认值，后续可从历史数据获取
                icon=category_icons.get(strategy["category"], "📋")
            ))
        
        logger.info(f"返回 {len(formatted_strategies)} 个策略")
        
        return StrategiesResponse(
            success=True,
            strategies=formatted_strategies,
            total=len(formatted_strategies)
        )
        
    except Exception as e:
        logger.error(f"获取策略列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取策略列表失败: {str(e)}")


def create_strategy(name: str, config: StrategyConfig):
    """创建策略实例"""
    # 策略映射表 - 直接映射策略ID到策略类
    strategy_map = {
        "vegas_adx": VegasADXStrategy,
        "ema_breakout": EMABreakoutStrategy,
        "buffett_value": BuffettValueStrategy,
        "graham_margin": GrahamMarginStrategy,
        "lynch_growth": LynchGrowthStrategy,
        "macd_crossover": MACDCrossoverStrategy,
        "bollinger_breakout": BollingerBreakoutStrategy,
        "turtle_trading": TurtleTradingStrategy,
        "dragon_leader": DragonLeaderStrategy,
        "martingale_refined": MartingaleRefinedStrategy,
        "scalping_blade": ScalpingBladeStrategy,
        "trident": TridentStrategy,
        "sentiment_resonance": SentimentResonanceStrategy,
        "debate_weighted": DebateWeightedStrategy,
        "limit_up_trading": LimitUpTradingStrategy,
        "volume_price_surge": VolumePriceSurgeStrategy,
    }

    # 先从映射表查找
    if name in strategy_map:
        logger.info(f"从映射表创建策略: {name}")
        return strategy_map[name](config)

    # 再从注册表获取
    registry = get_strategy_registry()
    strategy = registry.create_strategy(name, config)
    if strategy:
        logger.info(f"从注册表创建策略: {name}")
        return strategy

    logger.warning(f"未找到策略: {name}")
    return None
