"""
闭环验证系统API
实现决策验证、效果跟踪、策略优化
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import asyncio
import json
from pathlib import Path
import numpy as np

# 导入日志系统
from backend.utils.logging_config import get_logger
from backend.utils.tool_logging import log_api_call

logger = get_logger("api.verification")

# 创建路由器
router = APIRouter(prefix="/api/verification", tags=["Verification System"])


class Decision(BaseModel):
    """投资决策"""
    decision_id: str
    stock_code: str
    stock_name: str
    timestamp: datetime
    recommendation: str = Field(..., description="BUY/SELL/HOLD")
    confidence: float = Field(..., ge=0, le=1)
    target_price: float
    stop_loss: float
    reasons: List[str]
    source: str = Field(..., description="决策来源: DEBATE/ANALYST/MANUAL")
    
class Verification(BaseModel):
    """验证记录"""
    verification_id: str
    decision_id: str
    timestamp: datetime
    actual_price: float
    predicted_price: float
    accuracy_rate: float
    profit_loss: float
    is_success: bool
    notes: str
    
class Strategy(BaseModel):
    """策略配置"""
    strategy_id: str
    name: str
    description: str
    parameters: Dict[str, Any]
    performance_metrics: Dict[str, float]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
class OptimizationResult(BaseModel):
    """优化结果"""
    original_performance: Dict[str, float]
    optimized_performance: Dict[str, float]
    improvements: Dict[str, float]
    recommendations: List[str]


class VerificationEngine:
    """闭环验证引擎"""
    
    def __init__(self):
        self.data_file = Path("backend/data/verification_data.json")
        self.load_data()
        
    def load_data(self):
        """加载验证数据"""
        if self.data_file.exists():
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.decisions = data.get("decisions", [])
                self.verifications = data.get("verifications", [])
                self.strategies = data.get("strategies", [])
                self.performance_history = data.get("performance_history", [])
        else:
            self.decisions = []
            self.verifications = []
            self.strategies = self._default_strategies()
            self.performance_history = []
            self.save_data()
            
    def save_data(self):
        """保存验证数据"""
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "decisions": self.decisions,
            "verifications": self.verifications,
            "strategies": self.strategies,
            "performance_history": self.performance_history,
            "last_update": datetime.now().isoformat()
        }
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            
    def _default_strategies(self):
        """默认策略配置"""
        return [
            {
                "strategy_id": "S001",
                "name": "保守型策略",
                "description": "低风险，稳健收益",
                "parameters": {
                    "max_position": 0.3,
                    "stop_loss": 0.05,
                    "take_profit": 0.15,
                    "confidence_threshold": 0.7
                },
                "performance_metrics": {},
                "is_active": True,
                "created_at": datetime.now().isoformat()
            },
            {
                "strategy_id": "S002",
                "name": "平衡型策略",
                "description": "风险收益平衡",
                "parameters": {
                    "max_position": 0.5,
                    "stop_loss": 0.08,
                    "take_profit": 0.25,
                    "confidence_threshold": 0.6
                },
                "performance_metrics": {},
                "is_active": True,
                "created_at": datetime.now().isoformat()
            },
            {
                "strategy_id": "S003",
                "name": "激进型策略",
                "description": "高风险，高收益",
                "parameters": {
                    "max_position": 0.7,
                    "stop_loss": 0.12,
                    "take_profit": 0.40,
                    "confidence_threshold": 0.5
                },
                "performance_metrics": {},
                "is_active": False,
                "created_at": datetime.now().isoformat()
            }
        ]
        
    async def record_decision(self, decision: Dict[str, Any]) -> str:
        """记录投资决策"""
        decision_id = f"D{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        decision_record = {
            "decision_id": decision_id,
            "timestamp": datetime.now().isoformat(),
            **decision
        }
        
        self.decisions.append(decision_record)
        self.save_data()
        
        # 启动后台验证任务
        asyncio.create_task(self._schedule_verification(decision_id))
        
        return decision_id
        
    async def _schedule_verification(self, decision_id: str):
        """安排验证任务"""
        # 等待一段时间后进行验证（实际应用中可能是几天后）
        await asyncio.sleep(60)  # 模拟等待60秒
        await self.verify_decision(decision_id)
        
    async def verify_decision(self, decision_id: str) -> Dict[str, Any]:
        """验证决策效果"""
        # 找到对应决策
        decision = next((d for d in self.decisions if d["decision_id"] == decision_id), None)
        if not decision:
            raise ValueError(f"决策不存在: {decision_id}")
            
        # 获取实际价格（模拟）
        actual_price = await self._get_actual_price(decision["stock_code"])
        predicted_price = decision.get("target_price", 100)
        
        # 计算准确率
        accuracy_rate = 1 - abs(actual_price - predicted_price) / predicted_price
        
        # 计算盈亏
        entry_price = decision.get("entry_price", 100)
        if decision["recommendation"] == "BUY":
            profit_loss = (actual_price - entry_price) / entry_price * 100
        elif decision["recommendation"] == "SELL":
            profit_loss = (entry_price - actual_price) / entry_price * 100
        else:  # HOLD
            profit_loss = 0
            
        # 判断是否成功
        is_success = profit_loss > 0 and accuracy_rate > 0.8
        
        # 创建验证记录
        verification = {
            "verification_id": f"V{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "decision_id": decision_id,
            "timestamp": datetime.now().isoformat(),
            "actual_price": actual_price,
            "predicted_price": predicted_price,
            "accuracy_rate": accuracy_rate,
            "profit_loss": profit_loss,
            "is_success": is_success,
            "notes": f"准确率{accuracy_rate:.2%}, 收益率{profit_loss:.2f}%"
        }
        
        self.verifications.append(verification)
        
        # 更新策略表现
        await self._update_strategy_performance(decision, verification)
        
        self.save_data()
        
        return verification
        
    async def _get_actual_price(self, stock_code: str) -> float:
        """获取实际价格（模拟）"""
        import random
        base_price = 100
        return base_price * (1 + random.uniform(-0.1, 0.1))
        
    async def _update_strategy_performance(self, decision: Dict, verification: Dict):
        """更新策略表现"""
        # 找到对应策略
        strategy_name = decision.get("strategy", "平衡型策略")
        strategy = next((s for s in self.strategies if s["name"] == strategy_name), None)
        
        if strategy:
            metrics = strategy.get("performance_metrics", {})
            
            # 更新统计
            total_trades = metrics.get("total_trades", 0) + 1
            success_trades = metrics.get("success_trades", 0) + (1 if verification["is_success"] else 0)
            total_profit = metrics.get("total_profit", 0) + verification["profit_loss"]
            
            metrics.update({
                "total_trades": total_trades,
                "success_trades": success_trades,
                "win_rate": success_trades / total_trades if total_trades > 0 else 0,
                "total_profit": total_profit,
                "avg_profit": total_profit / total_trades if total_trades > 0 else 0,
                "last_update": datetime.now().isoformat()
            })
            
            strategy["performance_metrics"] = metrics
            strategy["updated_at"] = datetime.now().isoformat()
            
    async def optimize_strategy(self, strategy_id: str) -> Dict[str, Any]:
        """优化策略参数"""
        strategy = next((s for s in self.strategies if s["strategy_id"] == strategy_id), None)
        if not strategy:
            raise ValueError(f"策略不存在: {strategy_id}")
            
        # 获取当前表现
        original_metrics = strategy.get("performance_metrics", {})
        
        # 模拟优化过程（实际应用中使用机器学习）
        optimized_params = self._run_optimization(strategy["parameters"], original_metrics)
        
        # 创建优化后的策略
        optimized_strategy = {
            **strategy,
            "strategy_id": f"S{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "name": f"{strategy['name']}_优化版",
            "parameters": optimized_params,
            "created_at": datetime.now().isoformat()
        }
        
        # 模拟优化后的表现
        optimized_metrics = {
            "win_rate": min(0.95, original_metrics.get("win_rate", 0.5) * 1.2),
            "avg_profit": original_metrics.get("avg_profit", 0) * 1.3,
            "max_drawdown": original_metrics.get("max_drawdown", 0.2) * 0.8
        }
        
        # 计算改进
        improvements = {}
        for key in optimized_metrics:
            if key in original_metrics:
                improvements[key] = (
                    (optimized_metrics[key] - original_metrics[key]) / 
                    original_metrics[key] * 100 if original_metrics[key] != 0 else 0
                )
                
        return {
            "original_performance": original_metrics,
            "optimized_performance": optimized_metrics,
            "improvements": improvements,
            "optimized_strategy": optimized_strategy,
            "recommendations": [
                f"建议将止损调整为{optimized_params.get('stop_loss', 0.08):.1%}",
                f"建议将仓位上限调整为{optimized_params.get('max_position', 0.5):.1%}",
                f"建议将信心阈值调整为{optimized_params.get('confidence_threshold', 0.6):.1f}"
            ]
        }
        
    def _run_optimization(self, params: Dict, metrics: Dict) -> Dict:
        """运行优化算法（简化版）"""
        import random
        
        # 基于当前表现调整参数
        win_rate = metrics.get("win_rate", 0.5)
        
        optimized = dict(params)
        
        # 如果胜率低，提高信心阈值
        if win_rate < 0.5:
            optimized["confidence_threshold"] = min(0.9, params.get("confidence_threshold", 0.6) * 1.2)
            optimized["stop_loss"] = max(0.03, params.get("stop_loss", 0.08) * 0.8)
            
        # 如果胜率高，可以适当放宽
        elif win_rate > 0.7:
            optimized["max_position"] = min(0.8, params.get("max_position", 0.5) * 1.2)
            optimized["take_profit"] = params.get("take_profit", 0.25) * 1.3
            
        return optimized


# 创建全局验证引擎实例
engine = VerificationEngine()


@router.post("/decision", response_model=Dict[str, Any])
@log_api_call("记录决策")
async def record_decision(
    stock_code: str,
    recommendation: str,
    confidence: float,
    target_price: float,
    stop_loss: float,
    reasons: List[str],
    source: str = "MANUAL",
    strategy: str = "平衡型策略"
):
    """
    记录投资决策
    
    Args:
        stock_code: 股票代码
        recommendation: 建议(BUY/SELL/HOLD)
        confidence: 信心度
        target_price: 目标价
        stop_loss: 止损价
        reasons: 决策理由
        source: 决策来源
        strategy: 使用的策略
        
    Returns:
        决策记录结果
    """
    try:
        decision = {
            "stock_code": stock_code,
            "stock_name": await _get_stock_name(stock_code),
            "recommendation": recommendation,
            "confidence": confidence,
            "target_price": target_price,
            "stop_loss": stop_loss,
            "reasons": reasons,
            "source": source,
            "strategy": strategy,
            "entry_price": await _get_current_price(stock_code)
        }
        
        decision_id = await engine.record_decision(decision)
        
        logger.success(f"决策已记录: {decision_id}")
        
        return {
            "success": True,
            "decision_id": decision_id,
            "message": "决策已记录，将自动进行后续验证",
            "decision": decision
        }
        
    except Exception as e:
        logger.error(f"记录决策失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/verify/{decision_id}", response_model=Dict[str, Any])
@log_api_call("验证决策")
async def verify_decision(decision_id: str):
    """
    手动触发决策验证
    
    Args:
        decision_id: 决策ID
        
    Returns:
        验证结果
    """
    try:
        verification = await engine.verify_decision(decision_id)
        
        logger.info(f"决策验证完成: {decision_id}")
        
        return {
            "success": True,
            "verification": verification,
            "message": f"验证完成，准确率{verification['accuracy_rate']:.2%}"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"验证失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/decisions", response_model=Dict[str, Any])
async def get_decisions(
    limit: int = 50,
    offset: int = 0,
    stock_code: Optional[str] = None,
    recommendation: Optional[str] = None
):
    """
    获取决策列表
    
    Args:
        limit: 返回数量
        offset: 偏移量
        stock_code: 股票代码筛选
        recommendation: 建议类型筛选
        
    Returns:
        决策列表
    """
    try:
        decisions = engine.decisions
        
        # 筛选
        if stock_code:
            decisions = [d for d in decisions if d.get("stock_code") == stock_code]
        if recommendation:
            decisions = [d for d in decisions if d.get("recommendation") == recommendation]
            
        # 排序（最新的在前）
        decisions = sorted(decisions, key=lambda x: x.get("timestamp", ""), reverse=True)
        
        # 分页
        total = len(decisions)
        decisions = decisions[offset:offset + limit]
        
        return {
            "success": True,
            "total": total,
            "offset": offset,
            "limit": limit,
            "decisions": decisions
        }
        
    except Exception as e:
        logger.error(f"获取决策列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/verifications", response_model=Dict[str, Any])
async def get_verifications(limit: int = 50):
    """
    获取验证记录
    
    Args:
        limit: 返回数量
        
    Returns:
        验证记录列表
    """
    try:
        verifications = sorted(
            engine.verifications,
            key=lambda x: x.get("timestamp", ""),
            reverse=True
        )[:limit]
        
        # 计算统计
        total = len(engine.verifications)
        success_count = len([v for v in engine.verifications if v.get("is_success")])
        
        stats = {
            "total_verifications": total,
            "success_count": success_count,
            "success_rate": success_count / total if total > 0 else 0,
            "avg_accuracy": np.mean([v.get("accuracy_rate", 0) for v in engine.verifications]) if engine.verifications else 0,
            "avg_profit_loss": np.mean([v.get("profit_loss", 0) for v in engine.verifications]) if engine.verifications else 0
        }
        
        return {
            "success": True,
            "stats": stats,
            "verifications": verifications
        }
        
    except Exception as e:
        logger.error(f"获取验证记录失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/strategies", response_model=Dict[str, Any])
async def get_strategies():
    """
    获取策略列表
    
    Returns:
        策略列表及其表现
    """
    try:
        # 按表现排序
        strategies = sorted(
            engine.strategies,
            key=lambda x: x.get("performance_metrics", {}).get("win_rate", 0),
            reverse=True
        )
        
        return {
            "success": True,
            "strategies": strategies,
            "active_count": len([s for s in strategies if s.get("is_active")])
        }
        
    except Exception as e:
        logger.error(f"获取策略列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/optimize/{strategy_id}", response_model=Dict[str, Any])
@log_api_call("优化策略")
async def optimize_strategy(strategy_id: str):
    """
    优化策略参数
    
    Args:
        strategy_id: 策略ID
        
    Returns:
        优化结果和建议
    """
    try:
        result = await engine.optimize_strategy(strategy_id)
        
        logger.success(f"策略优化完成: {strategy_id}")
        
        return {
            "success": True,
            **result
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"优化失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# 辅助函数
async def _get_stock_name(stock_code: str) -> str:
    """获取股票名称"""
    stock_names = {
        "600519": "贵州茅台",
        "000858": "五粮液",
        "000333": "美的集团",
    }
    code = stock_code.replace(".SH", "").replace(".SZ", "")
    return stock_names.get(code, stock_code)

async def _get_current_price(stock_code: str) -> float:
    """获取当前价格（模拟）"""
    import random
    return 100 * (1 + random.uniform(-0.05, 0.05))


# 测试端点
@router.get("/test")
async def test_verification_api():
    """测试验证API是否正常工作"""
    return {
        "status": "ok",
        "message": "Verification API is working",
        "features": [
            "Decision recording",
            "Automatic verification",
            "Strategy optimization",
            "Performance tracking",
            "Closed-loop feedback"
        ],
        "timestamp": datetime.now().isoformat()
    }
