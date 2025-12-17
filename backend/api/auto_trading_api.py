"""
自动模拟交易API
使用LLM进行智能交易决策，自动执行买入/卖出操作
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
from pathlib import Path

from backend.utils.logging_config import get_logger
from backend.api.trading_llm_config_api import get_trading_llm_config

logger = get_logger("api.auto_trading")
router = APIRouter(prefix="/api/auto-trading", tags=["Auto Trading"])


# ==================== 数据模型 ====================

class MarketData(BaseModel):
    """市场数据"""
    stock_code: str
    current_price: float
    change_rate: float
    volume: float
    news_summary: Optional[str] = None


class TradingDecision(BaseModel):
    """交易决策"""
    action: str = Field(..., description="buy/sell/hold")
    quantity: int = Field(0, ge=0, description="交易数量")
    reason: str = Field(..., description="决策理由")
    confidence: float = Field(..., ge=0, le=1, description="决策置信度")
    risk_level: str = Field(..., description="风险等级")
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None


class AutoTradingTask(BaseModel):
    """自动交易任务"""
    task_id: str
    stock_code: str
    strategy_id: Optional[str] = None
    initial_capital: float
    current_capital: float
    status: str = Field(..., description="running/stopped/completed")
    created_at: str
    last_decision_at: Optional[str] = None
    total_trades: int = 0
    total_profit: float = 0


class StartTaskRequest(BaseModel):
    """启动任务请求"""
    stock_code: str
    analysis_result: Optional[Dict[str, Any]] = None
    strategy_id: Optional[str] = None
    initial_capital: float = Field(100000, gt=0)
    auto_select_strategy: bool = Field(True, description="是否自动选择策略")
    risk_preference: str = Field("moderate", description="风险偏好")


class DecisionRecord(BaseModel):
    """决策记录"""
    record_id: str
    task_id: str
    timestamp: str
    market_data: MarketData
    decision: TradingDecision
    executed: bool
    execution_result: Optional[Dict[str, Any]] = None


# ==================== 数据存储 ====================

TASKS_FILE = Path("backend/data/auto_trading_tasks.json")
DECISIONS_FILE = Path("backend/data/trading_decisions.json")

# 内存存储（实际应该用数据库）
active_tasks: Dict[str, Dict] = {}
decision_records: List[Dict] = []


def load_tasks():
    """加载任务"""
    global active_tasks
    if TASKS_FILE.exists():
        try:
            with open(TASKS_FILE, 'r', encoding='utf-8') as f:
                active_tasks = json.load(f)
        except Exception as e:
            logger.error(f"加载任务失败: {e}")
            active_tasks = {}


def save_tasks():
    """保存任务"""
    try:
        TASKS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(TASKS_FILE, 'w', encoding='utf-8') as f:
            json.dump(active_tasks, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"保存任务失败: {e}")


def load_decisions():
    """加载决策记录"""
    global decision_records
    if DECISIONS_FILE.exists():
        try:
            with open(DECISIONS_FILE, 'r', encoding='utf-8') as f:
                decision_records = json.load(f)
        except Exception as e:
            logger.error(f"加载决策记录失败: {e}")
            decision_records = []


def save_decisions():
    """保存决策记录"""
    try:
        DECISIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(DECISIONS_FILE, 'w', encoding='utf-8') as f:
            json.dump(decision_records, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"保存决策记录失败: {e}")


# ==================== LLM决策 ====================

async def call_trading_decision_llm(
    stock_code: str,
    market_data: MarketData,
    analysis_result: Optional[Dict],
    current_position: Optional[Dict],
    strategy_id: Optional[str]
) -> TradingDecision:
    """
    调用LLM进行交易决策

    Args:
        stock_code: 股票代码
        market_data: 市场数据
        analysis_result: 分析结果
        current_position: 当前持仓
        strategy_id: 策略ID

    Returns:
        交易决策
    """
    # 获取LLM配置
    config = get_trading_llm_config("trade_decision")

    if not config.get("enabled", True):
        raise HTTPException(status_code=503, detail="交易决策LLM未启用")

    try:
        logger.info(f"调用LLM进行交易决策: {stock_code}")

        # 真实调用LLM进行交易决策
        from backend.services.llm_service import call_trading_decision_llm as llm_call

        decision = await llm_call(
            stock_code=stock_code,
            current_price=market_data.current_price,
            change_rate=market_data.change_rate,
            volume=market_data.volume,
            analysis_result=analysis_result,
            current_position=current_position,
            strategy_id=strategy_id,
            news_summary=market_data.news_summary
        )

        logger.info(f"LLM交易决策完成: {decision.get('action', 'hold')}")

        return TradingDecision(
            action=decision.get("action", "hold"),
            quantity=decision.get("quantity", 0),
            reason=decision.get("reason", "LLM决策"),
            confidence=decision.get("confidence", 0.5),
            risk_level=decision.get("risk_level", "medium"),
            stop_loss=decision.get("stop_loss"),
            take_profit=decision.get("take_profit")
        )

    except Exception as e:
        logger.error(f"LLM交易决策失败: {e}")
        raise HTTPException(status_code=500, detail=f"决策失败: {str(e)}")


async def execute_trade(
    task_id: str,
    decision: TradingDecision,
    market_data: MarketData
) -> Dict[str, Any]:
    """
    执行交易 - 调用trading_api的模拟交易引擎，确保数据同步

    Args:
        task_id: 任务ID
        decision: 交易决策
        market_data: 市场数据

    Returns:
        执行结果
    """
    try:
        if decision.action == "hold":
            return {
                "success": True,
                "action": "hold",
                "message": "持有观望"
            }

        # 调用trading_api的模拟交易引擎，确保数据同步到模拟交易页面
        from backend.api.trading_api import simulator, TradeOrder

        # 构建交易订单
        order = TradeOrder(
            stock_code=market_data.stock_code,
            action=decision.action.upper(),  # BUY/SELL
            quantity=decision.quantity,
            price=market_data.current_price,
            order_type="MARKET",
            stop_loss=decision.stop_loss,
            take_profit=decision.take_profit
        )

        # 执行交易
        result = await simulator.execute_trade(order)

        if result.get("success"):
            logger.info(f"交易执行成功: {task_id} - {decision.action} {decision.quantity}股 @ {market_data.current_price}")
        else:
            logger.warning(f"交易执行失败: {task_id} - {result.get('error', '未知错误')}")

        return result

    except Exception as e:
        logger.error(f"交易执行失败: {e}")
        return {
            "success": False,
            "error": str(e)
        }


# ==================== API端点 ====================

@router.post("/start")
async def start_auto_trading(request: StartTaskRequest, background_tasks: BackgroundTasks):
    """
    启动自动交易任务
    
    Args:
        request: 启动请求
        background_tasks: 后台任务
        
    Returns:
        任务信息
    """
    try:
        load_tasks()
        
        # 创建任务
        task_id = f"AT{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        task = {
            "task_id": task_id,
            "stock_code": request.stock_code,
            "strategy_id": request.strategy_id,
            "initial_capital": request.initial_capital,
            "current_capital": request.initial_capital,
            "status": "running",
            "created_at": datetime.now().isoformat(),
            "last_decision_at": None,
            "total_trades": 0,
            "total_profit": 0,
            "auto_select_strategy": request.auto_select_strategy,
            "risk_preference": request.risk_preference,
            "analysis_result": request.analysis_result
        }
        
        active_tasks[task_id] = task
        save_tasks()

        logger.info(f"自动交易任务已启动: {task_id}")

        # 立即执行第一次决策
        first_decision = None
        try:
            first_decision = await make_decision(task_id)
            # decision 是 TradingDecision 对象，需要用 .action 而不是 .get()
            decision_obj = first_decision.get('decision')
            action = decision_obj.action if hasattr(decision_obj, 'action') else decision_obj.get('action', 'unknown') if isinstance(decision_obj, dict) else 'unknown'
            logger.info(f"首次决策完成: {task_id} - {action}")
        except Exception as e:
            logger.warning(f"首次决策失败: {e}")

        return {
            "success": True,
            "task": active_tasks.get(task_id, task),  # 返回更新后的任务
            "first_decision": first_decision,
            "message": "自动交易任务已启动并执行首次决策"
        }
        
    except Exception as e:
        logger.error(f"启动任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop/{task_id}")
async def stop_auto_trading(task_id: str):
    """
    停止自动交易任务
    
    Args:
        task_id: 任务ID
        
    Returns:
        停止结果
    """
    try:
        load_tasks()
        
        if task_id not in active_tasks:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        task = active_tasks[task_id]
        task["status"] = "stopped"
        task["stopped_at"] = datetime.now().isoformat()
        
        save_tasks()
        
        logger.info(f"自动交易任务已停止: {task_id}")
        
        return {
            "success": True,
            "task": task,
            "message": "任务已停止"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"停止任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks")
async def list_tasks():
    """
    获取所有任务列表
    
    Returns:
        任务列表
    """
    try:
        load_tasks()
        
        return {
            "success": True,
            "tasks": list(active_tasks.values()),
            "total": len(active_tasks)
        }
    except Exception as e:
        logger.error(f"获取任务列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/task/{task_id}")
async def get_task(task_id: str):
    """
    获取任务详情
    
    Args:
        task_id: 任务ID
        
    Returns:
        任务详情
    """
    try:
        load_tasks()
        
        if task_id not in active_tasks:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        return {
            "success": True,
            "task": active_tasks[task_id]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取任务详情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/task/{task_id}/decisions")
async def get_task_decisions(task_id: str, limit: int = 50):
    """
    获取任务的决策记录
    
    Args:
        task_id: 任务ID
        limit: 返回数量限制
        
    Returns:
        决策记录列表
    """
    try:
        load_decisions()
        
        task_decisions = [
            d for d in decision_records
            if d.get("task_id") == task_id
        ]
        
        # 按时间倒序
        task_decisions.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        return {
            "success": True,
            "decisions": task_decisions[:limit],
            "total": len(task_decisions)
        }
    except Exception as e:
        logger.error(f"获取决策记录失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/task/{task_id}/decide")
async def make_decision(task_id: str):
    """
    手动触发一次决策
    
    Args:
        task_id: 任务ID
        
    Returns:
        决策结果
    """
    try:
        load_tasks()
        load_decisions()
        
        if task_id not in active_tasks:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        task = active_tasks[task_id]

        # 使用真实的市场数据服务获取行情
        from backend.services.market_data_service import get_realtime_quote, get_market_data_service

        quote = get_realtime_quote(task["stock_code"])

        # 获取新闻摘要
        news_summary = "无最新新闻"
        try:
            news_list = get_market_data_service().get_latest_news(task["stock_code"], limit=3)
            if news_list:
                news_summary = "; ".join([n.get("title", "") for n in news_list[:3]])
        except Exception as e:
            logger.warning(f"获取新闻失败: {e}")

        market_data = MarketData(
            stock_code=task["stock_code"],
            current_price=quote.get("current_price", 0),
            change_rate=quote.get("change_rate", 0),
            volume=quote.get("volume", 0),
            news_summary=news_summary
        )

        # 获取当前持仓
        from backend.api.trading_api import simulator
        current_position = simulator.positions.get(task["stock_code"])

        # 调用LLM决策
        decision = await call_trading_decision_llm(
            task["stock_code"],
            market_data,
            task.get("analysis_result"),
            current_position,
            task.get("strategy_id")
        )
        
        # 执行交易
        execution_result = await execute_trade(task_id, decision, market_data)
        
        # 记录决策
        record = {
            "record_id": f"DR{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "task_id": task_id,
            "timestamp": datetime.now().isoformat(),
            "market_data": market_data.dict(),
            "decision": decision.dict(),
            "executed": execution_result.get("success", False),
            "execution_result": execution_result
        }
        
        decision_records.append(record)
        save_decisions()
        
        # 更新任务
        task["last_decision_at"] = datetime.now().isoformat()
        task["total_trades"] += 1 if decision.action != "hold" else 0
        save_tasks()
        
        logger.info(f"决策完成: {task_id} - {decision.action}")
        
        return {
            "success": True,
            "decision": decision,
            "execution": execution_result,
            "record": record
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"决策失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test")
async def test_auto_trading():
    """
    测试自动交易功能
    
    Returns:
        测试结果
    """
    try:
        # 创建测试任务
        test_request = StartTaskRequest(
            stock_code="600519",
            initial_capital=100000,
            auto_select_strategy=True,
            risk_preference="moderate"
        )
        
        # 启动任务
        result = await start_auto_trading(test_request, BackgroundTasks())
        task_id = result["task"]["task_id"]
        
        # 执行一次决策
        decision_result = await make_decision(task_id)
        
        return {
            "success": True,
            "message": "测试成功",
            "task": result["task"],
            "decision": decision_result
        }
    except Exception as e:
        logger.error(f"测试失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 初始化
load_tasks()
load_decisions()
