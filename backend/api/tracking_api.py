"""
持续跟踪系统API
定期检查市场情况，LLM决策是否需要调整策略或重新分析
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
from pathlib import Path

from backend.utils.logging_config import get_logger
from backend.api.trading_llm_config_api import get_trading_llm_config

logger = get_logger("api.tracking")
router = APIRouter(prefix="/api/tracking", tags=["Tracking System"])


# ==================== 数据模型 ====================

class TriggerCondition(BaseModel):
    """触发条件"""
    price_change_threshold: float = Field(5.0, description="价格变动阈值（%）")
    volume_change_threshold: float = Field(50.0, description="成交量变动阈值（%）")
    check_news: bool = Field(True, description="是否检查重大新闻")
    check_interval_hours: int = Field(24, description="检查间隔（小时）")


class TrackingTask(BaseModel):
    """跟踪任务"""
    task_id: str
    stock_code: str
    analysis_id: Optional[str] = None
    strategy_id: Optional[str] = None
    auto_trading_task_id: Optional[str] = None
    initial_analysis: Dict[str, Any]
    trigger_condition: TriggerCondition
    status: str = Field(..., description="active/paused/completed")
    created_at: str
    last_check_at: Optional[str] = None
    check_count: int = 0
    trigger_count: int = 0
    decisions: List[Dict] = Field(default_factory=list)


class CreateTaskRequest(BaseModel):
    """创建任务请求"""
    stock_code: str
    analysis_result: Dict[str, Any]
    strategy_id: Optional[str] = None
    auto_trading_task_id: Optional[str] = None
    trigger_condition: Optional[TriggerCondition] = None
    duration_days: int = Field(30, ge=1, le=365, description="跟踪天数")


class CheckResult(BaseModel):
    """检查结果"""
    triggered: bool
    reason: str
    market_change: Dict[str, Any]
    decision: str = Field(..., description="hold/adjust/reanalyze")
    action_details: Optional[Dict[str, Any]] = None


# ==================== 数据存储 ====================

TASKS_FILE = Path("backend/data/tracking_tasks.json")

tracking_tasks: Dict[str, Dict] = {}


def load_tasks():
    """加载任务"""
    global tracking_tasks
    if TASKS_FILE.exists():
        try:
            with open(TASKS_FILE, 'r', encoding='utf-8') as f:
                tracking_tasks = json.load(f)
        except Exception as e:
            logger.error(f"加载跟踪任务失败: {e}")
            tracking_tasks = {}


def save_tasks():
    """保存任务"""
    try:
        TASKS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(TASKS_FILE, 'w', encoding='utf-8') as f:
            json.dump(tracking_tasks, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"保存跟踪任务失败: {e}")


# ==================== LLM决策 ====================

async def call_tracking_decision_llm(
    task: Dict,
    market_data: Dict,
    trigger_reason: str
) -> Dict[str, Any]:
    """
    调用LLM进行跟踪决策
    
    Args:
        task: 跟踪任务
        market_data: 市场数据
        trigger_reason: 触发原因
        
    Returns:
        决策结果
    """
    config = get_trading_llm_config("market_analyzer")
    
    if not config.get("enabled", True):
        raise HTTPException(status_code=503, detail="市场分析LLM未启用")
    
    # 构建提示词
    prompt = f"""你是一个专业的投资跟踪系统。根据以下信息，决定是否需要调整策略或重新分析。

股票代码：{task['stock_code']}

初始分析结果：
{json.dumps(task['initial_analysis'], ensure_ascii=False, indent=2)}

当前市场数据：
- 价格变动：{market_data.get('price_change', 0)}%
- 成交量变动：{market_data.get('volume_change', 0)}%
- 最新新闻：{market_data.get('news_summary', '无')}

触发原因：{trigger_reason}

历史决策记录：
{json.dumps(task.get('decisions', [])[-3:], ensure_ascii=False, indent=2)}

请分析并决定：
1. 决策：hold（继续持有）/ adjust（调整策略）/ reanalyze（重新分析）
2. 理由：详细说明决策理由
3. 行动建议：如果需要调整或重新分析，提供具体建议

以JSON格式返回：
{{
  "decision": "hold/adjust/reanalyze",
  "reason": "决策理由",
  "confidence": 0.75,
  "action_details": {{
    "suggested_action": "具体建议",
    "risk_level": "low/medium/high"
  }}
}}
"""
    
    try:
        logger.info(f"调用LLM进行跟踪决策: {task['stock_code']}")

        # 真实调用LLM进行跟踪决策
        from backend.services.llm_service import call_tracking_decision_llm as llm_call

        # 计算距离分析的天数
        created_at = task.get("created_at", "")
        days_since = 0
        if created_at:
            try:
                created_date = datetime.fromisoformat(created_at)
                days_since = (datetime.now() - created_date).days
            except:
                pass

        result = await llm_call(
            stock_code=task["stock_code"],
            original_analysis=task.get("initial_analysis", {}),
            current_market_data=market_data,
            days_since_analysis=days_since
        )

        logger.info(f"LLM跟踪决策完成: {result.get('decision', 'hold')}")

        # 转换为标准格式
        return {
            "decision": result.get("decision", "hold"),
            "reason": result.get("reason", "LLM决策"),
            "confidence": result.get("confidence", 0.5),
            "action_details": {
                "suggested_action": result.get("suggested_action", "继续监控"),
                "risk_level": result.get("urgency", "medium")
            }
        }

    except Exception as e:
        logger.error(f"LLM跟踪决策失败: {e}")
        raise HTTPException(status_code=500, detail=f"决策失败: {str(e)}")


async def check_trigger_conditions(
    task: Dict,
    market_data: Dict
) -> tuple[bool, str]:
    """
    检查触发条件
    
    Args:
        task: 跟踪任务
        market_data: 市场数据
        
    Returns:
        (是否触发, 触发原因)
    """
    condition = task['trigger_condition']
    reasons = []
    
    # 检查价格变动
    price_change = abs(market_data.get('price_change', 0))
    if price_change >= condition['price_change_threshold']:
        reasons.append(f"价格变动{price_change:.2f}%，超过阈值{condition['price_change_threshold']}%")
    
    # 检查成交量变动
    volume_change = abs(market_data.get('volume_change', 0))
    if volume_change >= condition['volume_change_threshold']:
        reasons.append(f"成交量变动{volume_change:.2f}%，超过阈值{condition['volume_change_threshold']}%")
    
    # 检查重大新闻
    if condition['check_news'] and market_data.get('has_major_news', False):
        reasons.append("检测到重大新闻")
    
    triggered = len(reasons) > 0
    reason = "; ".join(reasons) if reasons else "无触发条件"
    
    return triggered, reason


# ==================== API端点 ====================

@router.post("/create")
async def create_tracking_task(request: CreateTaskRequest):
    """
    创建跟踪任务
    
    Args:
        request: 创建请求
        
    Returns:
        任务信息
    """
    try:
        load_tasks()
        
        # 创建任务
        task_id = f"TK{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        task = {
            "task_id": task_id,
            "stock_code": request.stock_code,
            "analysis_id": request.analysis_result.get("analysis_id"),
            "strategy_id": request.strategy_id,
            "auto_trading_task_id": request.auto_trading_task_id,
            "initial_analysis": request.analysis_result,
            "trigger_condition": (request.trigger_condition or TriggerCondition()).dict(),
            "status": "active",
            "created_at": datetime.now().isoformat(),
            "last_check_at": None,
            "check_count": 0,
            "trigger_count": 0,
            "decisions": [],
            "duration_days": request.duration_days,
            "end_date": (datetime.now() + timedelta(days=request.duration_days)).isoformat()
        }
        
        tracking_tasks[task_id] = task
        save_tasks()
        
        logger.info(f"跟踪任务已创建: {task_id}")
        
        return {
            "success": True,
            "task": task,
            "message": "跟踪任务已创建"
        }
        
    except Exception as e:
        logger.error(f"创建任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks")
async def list_tracking_tasks(status: Optional[str] = None):
    """
    获取跟踪任务列表
    
    Args:
        status: 状态筛选
        
    Returns:
        任务列表
    """
    try:
        load_tasks()
        
        tasks = list(tracking_tasks.values())
        
        if status:
            tasks = [t for t in tasks if t['status'] == status]
        
        return {
            "success": True,
            "tasks": tasks,
            "total": len(tasks)
        }
    except Exception as e:
        logger.error(f"获取任务列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/task/{task_id}")
async def get_tracking_task(task_id: str):
    """
    获取跟踪任务详情
    
    Args:
        task_id: 任务ID
        
    Returns:
        任务详情
    """
    try:
        load_tasks()
        
        if task_id not in tracking_tasks:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        return {
            "success": True,
            "task": tracking_tasks[task_id]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取任务详情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/task/{task_id}/check")
async def check_task(task_id: str):
    """
    手动触发任务检查
    
    Args:
        task_id: 任务ID
        
    Returns:
        检查结果
    """
    try:
        load_tasks()
        
        if task_id not in tracking_tasks:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        task = tracking_tasks[task_id]

        # 使用真实的市场数据服务获取行情
        from backend.services.market_data_service import get_realtime_quote, get_market_data_service

        stock_code = task["stock_code"]
        quote = get_realtime_quote(stock_code)

        # 计算价格变化（相对于初始分析时的价格）
        initial_price = task.get("initial_analysis", {}).get("current_price", quote.get("pre_close", 0))
        current_price = quote.get("current_price", 0)
        price_change = ((current_price - initial_price) / initial_price * 100) if initial_price > 0 else 0

        # 获取新闻
        news_summary = "无最新新闻"
        has_major_news = False
        try:
            news_list = get_market_data_service().get_latest_news(stock_code, limit=3)
            if news_list:
                news_summary = "; ".join([n.get("title", "") for n in news_list[:3]])
                # 简单判断是否有重大新闻（包含关键词）
                major_keywords = ["重大", "突发", "暴跌", "暴涨", "停牌", "退市", "收购", "重组"]
                has_major_news = any(kw in news_summary for kw in major_keywords)
        except Exception as e:
            logger.warning(f"获取新闻失败: {e}")

        market_data = {
            "price_change": round(price_change, 2),
            "volume_change": round(quote.get("change_rate", 0), 2),
            "has_major_news": has_major_news,
            "news_summary": news_summary,
            "current_price": current_price
        }
        
        # 检查触发条件
        triggered, reason = await check_trigger_conditions(task, market_data)
        
        # 更新检查次数
        task['check_count'] += 1
        task['last_check_at'] = datetime.now().isoformat()
        
        result = {
            "triggered": triggered,
            "reason": reason,
            "market_change": market_data
        }
        
        if triggered:
            # 调用LLM决策
            llm_decision = await call_tracking_decision_llm(task, market_data, reason)
            
            result.update({
                "decision": llm_decision["decision"],
                "action_details": llm_decision.get("action_details")
            })
            
            # 记录决策
            decision_record = {
                "timestamp": datetime.now().isoformat(),
                "triggered": True,
                "reason": reason,
                "market_data": market_data,
                "decision": llm_decision["decision"],
                "confidence": llm_decision["confidence"],
                "action_details": llm_decision.get("action_details")
            }
            
            task['decisions'].append(decision_record)
            task['trigger_count'] += 1
            
        else:
            result.update({
                "decision": "hold",
                "action_details": None
            })
        
        save_tasks()
        
        logger.info(f"任务检查完成: {task_id} - 触发: {triggered}")
        
        return {
            "success": True,
            "result": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"任务检查失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/task/{task_id}/pause")
async def pause_task(task_id: str):
    """
    暂停跟踪任务
    
    Args:
        task_id: 任务ID
        
    Returns:
        操作结果
    """
    try:
        load_tasks()
        
        if task_id not in tracking_tasks:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        task = tracking_tasks[task_id]
        task['status'] = 'paused'
        task['paused_at'] = datetime.now().isoformat()
        
        save_tasks()
        
        return {
            "success": True,
            "message": "任务已暂停",
            "task": task
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"暂停任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/task/{task_id}/resume")
async def resume_task(task_id: str):
    """
    恢复跟踪任务
    
    Args:
        task_id: 任务ID
        
    Returns:
        操作结果
    """
    try:
        load_tasks()
        
        if task_id not in tracking_tasks:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        task = tracking_tasks[task_id]
        task['status'] = 'active'
        task['resumed_at'] = datetime.now().isoformat()
        
        save_tasks()
        
        return {
            "success": True,
            "message": "任务已恢复",
            "task": task
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"恢复任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test")
async def test_tracking():
    """
    测试跟踪功能
    
    Returns:
        测试结果
    """
    try:
        # 创建测试任务
        test_request = CreateTaskRequest(
            stock_code="600519",
            analysis_result={
                "analysis_id": "test_001",
                "stock_code": "600519",
                "summary": "测试分析"
            },
            duration_days=30
        )
        
        # 创建任务
        create_result = await create_tracking_task(test_request)
        task_id = create_result["task"]["task_id"]
        
        # 执行检查
        check_result = await check_task(task_id)
        
        return {
            "success": True,
            "message": "测试成功",
            "task": create_result["task"],
            "check_result": check_result
        }
    except Exception as e:
        logger.error(f"测试失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 初始化
load_tasks()
