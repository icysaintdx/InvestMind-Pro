"""
自动交易系统数据模型
包含：交易计划、监控任务、执行日志
"""

from sqlalchemy import Column, String, Text, Boolean, Integer, Float, DateTime, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from backend.database.base import Base


class PlanStatus(enum.Enum):
    """计划状态"""
    PENDING = "pending"          # 待启动
    RUNNING = "running"          # 运行中
    PAUSED = "paused"            # 已暂停
    COMPLETED = "completed"      # 已完成
    STOPPED = "stopped"          # 已停止
    ERROR = "error"              # 异常


class EntryMode(enum.Enum):
    """入场模式"""
    RULE_ONLY = "rule_only"      # 仅规则引擎
    RULE_LLM = "rule_llm"        # 规则+LLM确认
    LLM_ONLY = "llm_only"        # 仅LLM判断


class ExitMode(enum.Enum):
    """出场模式"""
    RULE_ONLY = "rule_only"      # 仅规则引擎
    RULE_LLM = "rule_llm"        # 规则+LLM确认
    LLM_ONLY = "llm_only"        # 仅LLM判断


class SignalAction(enum.Enum):
    """信号动作"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class ExecutionStatus(enum.Enum):
    """执行状态"""
    PENDING = "pending"          # 待执行
    EXECUTING = "executing"      # 执行中
    SUCCESS = "success"          # 执行成功
    FAILED = "failed"            # 执行失败
    CANCELLED = "cancelled"      # 已取消


class TradingPlan(Base):
    """交易计划表"""
    __tablename__ = "trading_plans"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # 基本信息
    name = Column(String(100), comment="计划名称")
    strategy_id = Column(String(36), nullable=False, comment="策略ID")
    strategy_name = Column(String(100), comment="策略名称")
    stock_code = Column(String(20), nullable=False, comment="股票代码")
    stock_name = Column(String(50), comment="股票名称")

    # 计划参数
    initial_capital = Column(Float, default=100000, comment="计划资金")
    max_position_ratio = Column(Float, default=0.3, comment="最大仓位比例")
    entry_mode = Column(String(20), default="rule_only", comment="入场模式")
    exit_mode = Column(String(20), default="rule_only", comment="出场模式")
    check_interval = Column(Integer, default=30, comment="检查间隔(秒)")

    # 策略配置（JSON存储完整策略定义）
    strategy_config = Column(JSON, comment="策略配置")

    # 风控参数
    stop_loss_pct = Column(Float, default=0.05, comment="止损比例")
    take_profit_pct = Column(Float, default=0.15, comment="止盈比例")
    max_daily_trades = Column(Integer, default=3, comment="每日最大交易次数")

    # 状态
    status = Column(String(20), default="pending", comment="计划状态")
    error_message = Column(Text, comment="错误信息")

    # 持仓状态
    current_position = Column(Integer, default=0, comment="当前持仓数量")
    avg_cost = Column(Float, default=0, comment="持仓成本")
    current_price = Column(Float, default=0, comment="当前价格")
    unrealized_pnl = Column(Float, default=0, comment="未实现盈亏")
    unrealized_pnl_pct = Column(Float, default=0, comment="未实现盈亏比例")

    # 统计
    signals_generated = Column(Integer, default=0, comment="生成信号数")
    trades_executed = Column(Integer, default=0, comment="执行交易数")
    winning_trades = Column(Integer, default=0, comment="盈利交易数")
    losing_trades = Column(Integer, default=0, comment="亏损交易数")
    total_profit_loss = Column(Float, default=0, comment="累计盈亏")

    # 时间
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at = Column(DateTime, comment="启动时间")
    stopped_at = Column(DateTime, comment="停止时间")
    last_check_at = Column(DateTime, comment="最后检查时间")

    # 关联
    monitor_tasks = relationship("MonitorTask", back_populates="plan", cascade="all, delete-orphan")
    execution_logs = relationship("ExecutionLog", back_populates="plan", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "strategy_id": self.strategy_id,
            "strategy_name": self.strategy_name,
            "stock_code": self.stock_code,
            "stock_name": self.stock_name,
            "initial_capital": self.initial_capital,
            "max_position_ratio": self.max_position_ratio,
            "entry_mode": self.entry_mode,
            "exit_mode": self.exit_mode,
            "check_interval": self.check_interval,
            "stop_loss_pct": self.stop_loss_pct,
            "take_profit_pct": self.take_profit_pct,
            "max_daily_trades": self.max_daily_trades,
            "status": self.status,
            "error_message": self.error_message,
            "current_position": self.current_position,
            "avg_cost": self.avg_cost,
            "current_price": self.current_price,
            "unrealized_pnl": round(self.unrealized_pnl, 2) if self.unrealized_pnl else 0,
            "unrealized_pnl_pct": round(self.unrealized_pnl_pct * 100, 2) if self.unrealized_pnl_pct else 0,
            "signals_generated": self.signals_generated,
            "trades_executed": self.trades_executed,
            "winning_trades": self.winning_trades,
            "losing_trades": self.losing_trades,
            "total_profit_loss": round(self.total_profit_loss, 2) if self.total_profit_loss else 0,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "stopped_at": self.stopped_at.isoformat() if self.stopped_at else None,
            "last_check_at": self.last_check_at.isoformat() if self.last_check_at else None,
        }


class MonitorTask(Base):
    """监控任务表"""
    __tablename__ = "monitor_tasks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    plan_id = Column(String(36), ForeignKey("trading_plans.id", ondelete="CASCADE"), nullable=False)

    # 监控目标
    stock_code = Column(String(20), nullable=False)
    stock_name = Column(String(50))

    # 监控状态
    is_active = Column(Boolean, default=True, comment="是否激活")
    last_check_time = Column(DateTime, comment="最后检查时间")
    last_price = Column(Float, comment="最新价格")
    last_indicators = Column(JSON, comment="最新指标值")

    # 入场状态
    entry_conditions_status = Column(JSON, comment="入场条件状态")
    entry_ready = Column(Boolean, default=False, comment="是否满足入场")
    entry_confidence = Column(Float, default=0, comment="入场置信度")

    # 出场状态（持仓时）
    exit_conditions_status = Column(JSON, comment="出场条件状态")
    exit_ready = Column(Boolean, default=False, comment="是否满足出场")
    exit_confidence = Column(Float, default=0, comment="出场置信度")

    # 止损止盈状态
    stop_loss_price = Column(Float, comment="止损价")
    take_profit_price = Column(Float, comment="止盈价")
    stop_loss_triggered = Column(Boolean, default=False)
    take_profit_triggered = Column(Boolean, default=False)

    # 统计
    check_count = Column(Integer, default=0, comment="检查次数")
    signal_count = Column(Integer, default=0, comment="信号次数")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联
    plan = relationship("TradingPlan", back_populates="monitor_tasks")

    def to_dict(self):
        return {
            "id": self.id,
            "plan_id": self.plan_id,
            "stock_code": self.stock_code,
            "stock_name": self.stock_name,
            "is_active": self.is_active,
            "last_check_time": self.last_check_time.isoformat() if self.last_check_time else None,
            "last_price": self.last_price,
            "last_indicators": self.last_indicators,
            "entry_conditions_status": self.entry_conditions_status,
            "entry_ready": self.entry_ready,
            "entry_confidence": self.entry_confidence,
            "exit_conditions_status": self.exit_conditions_status,
            "exit_ready": self.exit_ready,
            "exit_confidence": self.exit_confidence,
            "stop_loss_price": self.stop_loss_price,
            "take_profit_price": self.take_profit_price,
            "stop_loss_triggered": self.stop_loss_triggered,
            "take_profit_triggered": self.take_profit_triggered,
            "check_count": self.check_count,
            "signal_count": self.signal_count,
        }


class ExecutionLog(Base):
    """执行日志表"""
    __tablename__ = "execution_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    plan_id = Column(String(36), ForeignKey("trading_plans.id", ondelete="CASCADE"), nullable=False)

    # 执行信息
    action = Column(String(10), nullable=False, comment="动作: BUY/SELL/HOLD")
    status = Column(String(20), default="pending", comment="执行状态")

    # 信号信息
    signal_source = Column(String(20), comment="信号来源: rule_engine/llm/manual")
    signal_confidence = Column(Float, comment="信号置信度")
    conditions_met = Column(JSON, comment="满足的条件")

    # 交易信息
    stock_code = Column(String(20), nullable=False)
    stock_name = Column(String(50))
    price = Column(Float, comment="执行价格")
    quantity = Column(Integer, comment="执行数量")
    amount = Column(Float, comment="交易金额")

    # 止损止盈
    stop_loss = Column(Float, comment="止损价")
    take_profit = Column(Float, comment="止盈价")

    # 盈亏（卖出时）
    profit_loss = Column(Float, comment="盈亏金额")
    profit_loss_pct = Column(Float, comment="盈亏比例")

    # 分析数据
    indicators_snapshot = Column(JSON, comment="指标快照")
    rule_engine_result = Column(JSON, comment="规则引擎结果")
    llm_analysis = Column(Text, comment="LLM分析结果")

    # 执行结果
    order_id = Column(String(36), comment="订单ID")
    error_message = Column(Text, comment="错误信息")

    # 时间
    created_at = Column(DateTime, default=datetime.utcnow)
    executed_at = Column(DateTime, comment="执行时间")

    # 关联
    plan = relationship("TradingPlan", back_populates="execution_logs")

    def to_dict(self):
        return {
            "id": self.id,
            "plan_id": self.plan_id,
            "action": self.action,
            "status": self.status,
            "signal_source": self.signal_source,
            "signal_confidence": self.signal_confidence,
            "conditions_met": self.conditions_met,
            "stock_code": self.stock_code,
            "stock_name": self.stock_name,
            "price": self.price,
            "quantity": self.quantity,
            "amount": self.amount,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "profit_loss": round(self.profit_loss, 2) if self.profit_loss else None,
            "profit_loss_pct": round(self.profit_loss_pct * 100, 2) if self.profit_loss_pct else None,
            "indicators_snapshot": self.indicators_snapshot,
            "rule_engine_result": self.rule_engine_result,
            "llm_analysis": self.llm_analysis,
            "order_id": self.order_id,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "executed_at": self.executed_at.isoformat() if self.executed_at else None,
        }


class AutoTradeConfig(Base):
    """自动交易全局配置表"""
    __tablename__ = "auto_trade_config"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # 全局开关
    is_enabled = Column(Boolean, default=True, comment="是否启用自动交易")

    # 交易时间设置
    trading_start_time = Column(String(10), default="09:30", comment="交易开始时间")
    trading_end_time = Column(String(10), default="15:00", comment="交易结束时间")
    lunch_break_start = Column(String(10), default="11:30", comment="午休开始")
    lunch_break_end = Column(String(10), default="13:00", comment="午休结束")

    # 监控设置
    default_check_interval = Column(Integer, default=30, comment="默认检查间隔(秒)")
    max_concurrent_plans = Column(Integer, default=10, comment="最大并发计划数")

    # 风控设置
    global_max_daily_loss = Column(Float, default=0.05, comment="全局单日最大亏损")
    global_max_position = Column(Float, default=0.8, comment="全局最大仓位")

    # LLM设置
    llm_enabled = Column(Boolean, default=True, comment="是否启用LLM")
    llm_model = Column(String(50), default="deepseek", comment="LLM模型")
    llm_timeout = Column(Integer, default=30, comment="LLM超时(秒)")

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "is_enabled": self.is_enabled,
            "trading_start_time": self.trading_start_time,
            "trading_end_time": self.trading_end_time,
            "lunch_break_start": self.lunch_break_start,
            "lunch_break_end": self.lunch_break_end,
            "default_check_interval": self.default_check_interval,
            "max_concurrent_plans": self.max_concurrent_plans,
            "global_max_daily_loss": self.global_max_daily_loss,
            "global_max_position": self.global_max_position,
            "llm_enabled": self.llm_enabled,
            "llm_model": self.llm_model,
            "llm_timeout": self.llm_timeout,
        }
