"""
策略模块数据库模型
策略定义存储在数据库中，支持动态增删改查
"""

from sqlalchemy import Column, String, Text, Boolean, Integer, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from backend.database.base import Base


class Strategy(Base):
    """策略基本信息表"""
    __tablename__ = "strategies"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False, comment="策略名称")
    description = Column(Text, comment="策略描述")
    category = Column(String(50), comment="策略类别: technical/fundamental/institutional/folk/ai")
    source = Column(String(20), default="user", comment="来源: preset/user/llm_parsed")
    icon = Column(String(10), default="📊", comment="图标")
    is_active = Column(Boolean, default=True, comment="是否启用")
    version = Column(String(10), default="1.0", comment="版本号")
    
    # 元数据
    created_by = Column(String(36), comment="创建者ID")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联
    indicators = relationship("StrategyIndicator", back_populates="strategy", cascade="all, delete-orphan")
    entry_rules = relationship("StrategyRule", back_populates="strategy", 
                               primaryjoin="and_(Strategy.id==StrategyRule.strategy_id, StrategyRule.rule_type=='entry')",
                               cascade="all, delete-orphan")
    exit_rules = relationship("StrategyRule", back_populates="strategy",
                              primaryjoin="and_(Strategy.id==StrategyRule.strategy_id, StrategyRule.rule_type=='exit')",
                              cascade="all, delete-orphan")
    risk_params = relationship("StrategyRiskParams", back_populates="strategy", uselist=False, cascade="all, delete-orphan")
    prompts = relationship("StrategyPrompt", back_populates="strategy", cascade="all, delete-orphan")
    
    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "source": self.source,
            "icon": self.icon,
            "is_active": self.is_active,
            "version": self.version,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "indicators": [ind.to_dict() for ind in self.indicators] if self.indicators else [],
            "entry_conditions": [rule.to_dict() for rule in self.entry_rules] if self.entry_rules else [],
            "exit_conditions": [rule.to_dict() for rule in self.exit_rules] if self.exit_rules else [],
            "risk_params": self.risk_params.to_dict() if self.risk_params else {},
        }


class StrategyIndicator(Base):
    """策略指标配置表"""
    __tablename__ = "strategy_indicators"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    strategy_id = Column(String(36), ForeignKey("strategies.id", ondelete="CASCADE"), nullable=False)
    
    name = Column(String(50), nullable=False, comment="指标名称: MA/MACD/RSI/BOLL/KDJ等")
    type = Column(String(30), comment="指标类型: trend/momentum/oscillator/volatility/volume")
    params = Column(JSON, comment="指标参数")
    weight = Column(Float, default=1.0, comment="权重 0-1")
    description = Column(Text, comment="指标说明")
    sort_order = Column(Integer, default=0, comment="排序")
    
    strategy = relationship("Strategy", back_populates="indicators")
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "params": self.params or {},
            "weight": self.weight,
            "description": self.description
        }


class StrategyRule(Base):
    """策略规则表（入场/出场规则）"""
    __tablename__ = "strategy_rules"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    strategy_id = Column(String(36), ForeignKey("strategies.id", ondelete="CASCADE"), nullable=False)
    
    rule_type = Column(String(20), nullable=False, comment="规则类型: entry/exit")
    name = Column(String(100), comment="规则名称")
    logic = Column(String(10), default="AND", comment="逻辑关系: AND/OR")
    conditions = Column(JSON, comment="条件列表")
    weight = Column(Float, default=1.0, comment="权重")
    priority = Column(Integer, default=0, comment="优先级")
    description = Column(Text, comment="规则描述")
    
    strategy = relationship("Strategy", back_populates="entry_rules", foreign_keys=[strategy_id])
    
    def to_dict(self):
        return {
            "id": self.id,
            "type": self.rule_type,
            "name": self.name,
            "logic": self.logic,
            "conditions": self.conditions or [],
            "weight": self.weight,
            "priority": self.priority,
            "description": self.description
        }


class StrategyRiskParams(Base):
    """策略风险参数表"""
    __tablename__ = "strategy_risk_params"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    strategy_id = Column(String(36), ForeignKey("strategies.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    # 止损设置
    stop_loss_type = Column(String(20), default="percentage", comment="止损类型: percentage/atr/support")
    stop_loss_value = Column(Float, default=0.05, comment="止损值")
    trailing_stop = Column(Boolean, default=False, comment="是否浮动止损")
    trailing_step = Column(Float, default=0.01, comment="浮动止损步进")
    
    # 止盈设置
    take_profit_type = Column(String(20), default="percentage", comment="止盈类型: percentage/resistance/ratio")
    take_profit_value = Column(Float, default=0.15, comment="止盈值")
    partial_exits = Column(JSON, comment="分批止盈设置")
    
    # 仓位管理
    position_type = Column(String(20), default="fixed", comment="仓位类型: fixed/kelly/volatility")
    max_position = Column(Float, default=0.3, comment="最大仓位比例")
    risk_per_trade = Column(Float, default=0.02, comment="单笔风险比例")
    
    strategy = relationship("Strategy", back_populates="risk_params")
    
    def to_dict(self):
        return {
            "stop_loss": self.stop_loss_value,
            "stop_loss_type": self.stop_loss_type,
            "trailing_stop": self.trailing_stop,
            "trailing_step": self.trailing_step,
            "take_profit": self.take_profit_value,
            "take_profit_type": self.take_profit_type,
            "partial_exits": self.partial_exits or [],
            "max_position": self.max_position,
            "position_type": self.position_type,
            "risk_per_trade": self.risk_per_trade
        }


class StrategyPrompt(Base):
    """策略LLM提示词模板表"""
    __tablename__ = "strategy_prompts"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    strategy_id = Column(String(36), ForeignKey("strategies.id", ondelete="CASCADE"), nullable=False)
    
    prompt_type = Column(String(30), nullable=False, comment="提示词类型: analysis/image_analysis/parse")
    prompt_template = Column(Text, comment="提示词模板")
    variables = Column(JSON, comment="变量定义")
    
    strategy = relationship("Strategy", back_populates="prompts")
    
    def to_dict(self):
        return {
            "id": self.id,
            "type": self.prompt_type,
            "template": self.prompt_template,
            "variables": self.variables or []
        }


class TradeSignal(Base):
    """交易信号记录表"""
    __tablename__ = "trade_signals"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    strategy_id = Column(String(36), ForeignKey("strategies.id"), nullable=False)
    stock_code = Column(String(20), nullable=False, comment="股票代码")
    
    signal_type = Column(String(10), nullable=False, comment="信号类型: BUY/SELL/HOLD")
    signal_strength = Column(Float, comment="信号强度 0-1")
    confidence = Column(Float, comment="置信度 0-1")
    
    entry_price = Column(Float, comment="建议入场价")
    stop_loss = Column(Float, comment="止损价")
    take_profit = Column(Float, comment="止盈价")
    position_size = Column(Float, comment="建议仓位")
    
    analysis_data = Column(JSON, comment="分析数据")
    llm_response = Column(Text, comment="LLM分析结果")
    image_analysis = Column(Text, comment="图像分析结果")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id,
            "strategy_id": self.strategy_id,
            "stock_code": self.stock_code,
            "signal_type": self.signal_type,
            "signal_strength": self.signal_strength,
            "confidence": self.confidence,
            "entry_price": self.entry_price,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "position_size": self.position_size,
            "analysis_data": self.analysis_data,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class ChartAnnotation(Base):
    """K线图标注表"""
    __tablename__ = "chart_annotations"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    stock_code = Column(String(20), nullable=False)
    
    annotation_type = Column(String(30), nullable=False, comment="标注类型: entry/exit/stop_loss/take_profit/support/resistance/trendline")
    price = Column(Float, comment="价格")
    price_end = Column(Float, comment="结束价格（用于趋势线）")
    time_start = Column(DateTime, comment="开始时间")
    time_end = Column(DateTime, comment="结束时间")
    
    label = Column(String(100), comment="标签")
    color = Column(String(20), comment="颜色")
    style = Column(JSON, comment="样式配置")
    note = Column(Text, comment="备注")
    
    created_by = Column(String(36))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id,
            "stock_code": self.stock_code,
            "type": self.annotation_type,
            "price": self.price,
            "price_end": self.price_end,
            "time_start": self.time_start.isoformat() if self.time_start else None,
            "time_end": self.time_end.isoformat() if self.time_end else None,
            "label": self.label,
            "color": self.color,
            "style": self.style,
            "note": self.note
        }