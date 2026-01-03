"""
数据库模型定义
使用 SQLAlchemy ORM
支持 SQLite（开发）和 PostgreSQL（生产）
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class AnalysisSession(Base):
    """分析会话表"""
    __tablename__ = 'analysis_sessions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(100), unique=True, nullable=False, index=True)
    stock_code = Column(String(10), nullable=False, index=True)
    stock_name = Column(String(100))
    status = Column(String(20), nullable=False, index=True)  # created, running, completed, error, interrupted
    progress = Column(Integer, default=0)
    current_stage = Column(Integer, default=0)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    # 新增：实际运行时间（秒），不包含服务中断时间
    actual_elapsed_seconds = Column(Integer, default=0)
    # 新增：最后活动时间，用于检测中断
    last_activity_time = Column(DateTime)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # 关系
    agent_results = relationship("AgentResult", back_populates="session", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<AnalysisSession(session_id='{self.session_id}', stock_code='{self.stock_code}', status='{self.status}')>"
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'stock_code': self.stock_code,
            'stock_name': self.stock_name,
            'status': self.status,
            'progress': self.progress,
            'current_stage': self.current_stage,
            'start_time': self.start_time.timestamp() if self.start_time else None,
            'end_time': self.end_time.timestamp() if self.end_time else None,
            'actual_elapsed_seconds': self.actual_elapsed_seconds or 0,
            'last_activity_time': self.last_activity_time.timestamp() if self.last_activity_time else None,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class AgentResult(Base):
    """智能体结果表"""
    __tablename__ = 'agent_results'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(100), ForeignKey('analysis_sessions.session_id'), nullable=False, index=True)
    agent_id = Column(String(50), nullable=False, index=True)
    agent_name = Column(String(100))
    status = Column(String(20), nullable=False)  # pending, running, completed, error
    output = Column(Text)
    tokens = Column(Integer)
    thoughts = Column(JSON)  # 存储思维链
    data_sources = Column(JSON)  # 存储数据源
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    duration_seconds = Column(Integer)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # 关系
    session = relationship("AnalysisSession", back_populates="agent_results")
    
    # 索引
    __table_args__ = (
        Index('idx_session_agent', 'session_id', 'agent_id'),
    )
    
    def __repr__(self):
        return f"<AgentResult(session_id='{self.session_id}', agent_id='{self.agent_id}', status='{self.status}')>"
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'agent_id': self.agent_id,
            'agent_name': self.agent_name,
            'status': self.status,
            'output': self.output,
            'tokens': self.tokens,
            'thoughts': self.thoughts,
            'data_sources': self.data_sources,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration_seconds': self.duration_seconds,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class StockHistory(Base):
    """股票历史统计表"""
    __tablename__ = 'stock_history'

    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_code = Column(String(10), unique=True, nullable=False, index=True)
    stock_name = Column(String(100))
    analysis_count = Column(Integer, default=0)
    last_analysis_time = Column(DateTime)
    avg_analysis_duration = Column(Integer)  # 平均分析时长（秒）
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<StockHistory(stock_code='{self.stock_code}', analysis_count={self.analysis_count})>"

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'stock_code': self.stock_code,
            'stock_name': self.stock_name,
            'analysis_count': self.analysis_count,
            'last_analysis_time': self.last_analysis_time.isoformat() if self.last_analysis_time else None,
            'avg_analysis_duration': self.avg_analysis_duration,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


# ==================== 数据流监控相关表 ====================

class MonitoredStock(Base):
    """监控股票配置表"""
    __tablename__ = 'monitored_stocks'

    id = Column(Integer, primary_key=True, autoincrement=True)
    ts_code = Column(String(20), unique=True, nullable=False, index=True)  # 股票代码
    name = Column(String(100))  # 股票名称
    frequency = Column(String(10), default='1h')  # 更新频率: 5m/15m/30m/1h/1d
    retention_days = Column(Integer, default=7)  # 数据保留天数

    # 监控项目配置 (JSON)
    items = Column(JSON, default=lambda: {
        'news': True,
        'risk': True,
        'sentiment': True,
        'suspend': False,
        'realtime': True,
        'financial': False,
        'capital': False
    })

    # 状态
    is_active = Column(Integer, default=1)  # 是否启用
    last_update = Column(DateTime)  # 最后更新时间

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    stock_data = relationship("StockDataRecord", back_populates="stock", cascade="all, delete-orphan")
    news_records = relationship("StockNewsRecord", back_populates="stock", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<MonitoredStock(ts_code='{self.ts_code}', name='{self.name}')>"

    def to_dict(self):
        return {
            'id': self.id,
            'ts_code': self.ts_code,
            'name': self.name,
            'frequency': self.frequency,
            'retention_days': self.retention_days,
            'items': self.items,
            'is_active': self.is_active,
            'last_update': self.last_update.isoformat() if self.last_update else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class StockDataRecord(Base):
    """股票数据记录表 - 存储综合数据快照（替换更新）"""
    __tablename__ = 'stock_data_records'

    id = Column(Integer, primary_key=True, autoincrement=True)
    ts_code = Column(String(20), ForeignKey('monitored_stocks.ts_code'), nullable=False, index=True)
    data_type = Column(String(50), nullable=False, index=True)  # realtime/financial/risk/sentiment/comprehensive
    data_date = Column(String(10), nullable=False, index=True)  # YYYY-MM-DD

    # 数据内容 (JSON)
    data = Column(JSON)

    # 元数据
    source = Column(String(50))  # 数据来源: tushare/akshare/eastmoney
    fetch_time = Column(DateTime, default=datetime.utcnow)  # 获取时间

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    stock = relationship("MonitoredStock", back_populates="stock_data")

    # 复合唯一索引：同一股票同一类型同一天只保留一条记录
    __table_args__ = (
        Index('idx_stock_data_unique', 'ts_code', 'data_type', 'data_date', unique=True),
    )

    def __repr__(self):
        return f"<StockDataRecord(ts_code='{self.ts_code}', type='{self.data_type}', date='{self.data_date}')>"

    def to_dict(self):
        return {
            'id': self.id,
            'ts_code': self.ts_code,
            'data_type': self.data_type,
            'data_date': self.data_date,
            'data': self.data,
            'source': self.source,
            'fetch_time': self.fetch_time.isoformat() if self.fetch_time else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class StockNewsRecord(Base):
    """股票新闻记录表 - 增量更新"""
    __tablename__ = 'stock_news_records'

    id = Column(Integer, primary_key=True, autoincrement=True)
    ts_code = Column(String(20), ForeignKey('monitored_stocks.ts_code'), nullable=False, index=True)

    # 新闻内容
    news_id = Column(String(100), unique=True, nullable=False, index=True)  # 新闻唯一ID (hash of title+pub_time)
    title = Column(String(500), nullable=False)
    content = Column(Text)
    summary = Column(String(1000))
    source = Column(String(100))  # 来源
    url = Column(String(500))
    pub_time = Column(DateTime, index=True)  # 发布时间

    # 情绪分析结果
    sentiment = Column(String(20))  # positive/negative/neutral
    sentiment_score = Column(Integer)  # 0-100
    urgency = Column(String(20))  # critical/high/medium/low
    report_type = Column(String(50))  # financial/announcement/news/policy/research
    keywords = Column(JSON)  # 关键词列表

    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # 关系
    stock = relationship("MonitoredStock", back_populates="news_records")

    def __repr__(self):
        return f"<StockNewsRecord(ts_code='{self.ts_code}', title='{self.title[:30]}...')>"

    def to_dict(self):
        return {
            'id': self.id,
            'ts_code': self.ts_code,
            'news_id': self.news_id,
            'title': self.title,
            'content': self.content,
            'summary': self.summary,
            'source': self.source,
            'url': self.url,
            'pub_time': self.pub_time.isoformat() if self.pub_time else None,
            'sentiment': self.sentiment,
            'sentiment_score': self.sentiment_score,
            'urgency': self.urgency,
            'report_type': self.report_type,
            'keywords': self.keywords,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class DataFlowDailyStats(Base):
    """数据流每日统计表"""
    __tablename__ = 'dataflow_daily_stats'

    id = Column(Integer, primary_key=True, autoincrement=True)
    stat_date = Column(String(10), unique=True, nullable=False, index=True)  # YYYY-MM-DD

    # 统计数据
    news_count = Column(Integer, default=0)
    risk_alerts = Column(Integer, default=0)
    analysis_tasks = Column(Integer, default=0)

    # API调用统计 (JSON)
    api_calls = Column(JSON, default=lambda: {
        'tushare': 0,
        'akshare': 0,
        'eastmoney': 0,
        'juhe': 0
    })

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<DataFlowDailyStats(date='{self.stat_date}')>"

    def to_dict(self):
        return {
            'stat_date': self.stat_date,
            'news_count': self.news_count,
            'risk_alerts': self.risk_alerts,
            'analysis_tasks': self.analysis_tasks,
            'api_calls': self.api_calls,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class AlertHistory(Base):
    """预警历史记录表"""
    __tablename__ = 'alert_history'

    id = Column(Integer, primary_key=True, autoincrement=True)
    ts_code = Column(String(20), nullable=False, index=True)  # 股票代码
    stock_name = Column(String(50))  # 股票名称

    # 预警信息
    alert_type = Column(String(50), nullable=False, index=True)  # 预警类型
    alert_level = Column(String(20), nullable=False, index=True)  # critical/high/medium/low
    title = Column(String(200), nullable=False)  # 预警标题
    message = Column(Text)  # 预警详情
    suggestion = Column(Text)  # 建议

    # 状态
    is_read = Column(Integer, default=0)  # 是否已读 0/1
    is_resolved = Column(Integer, default=0)  # 是否已处理 0/1

    # 时间
    alert_time = Column(DateTime, default=datetime.utcnow, index=True)  # 预警时间
    read_time = Column(DateTime)  # 阅读时间
    resolved_time = Column(DateTime)  # 处理时间

    created_at = Column(DateTime, default=datetime.utcnow)

    # 索引
    __table_args__ = (
        Index('idx_alert_stock_time', 'ts_code', 'alert_time'),
        Index('idx_alert_level_time', 'alert_level', 'alert_time'),
    )

    def __repr__(self):
        return f"<AlertHistory(ts_code='{self.ts_code}', type='{self.alert_type}', level='{self.alert_level}')>"

    def to_dict(self):
        return {
            'id': self.id,
            'ts_code': self.ts_code,
            'stock_name': self.stock_name,
            'alert_type': self.alert_type,
            'alert_level': self.alert_level,
            'title': self.title,
            'message': self.message,
            'suggestion': self.suggestion,
            'is_read': bool(self.is_read),
            'is_resolved': bool(self.is_resolved),
            'alert_time': self.alert_time.isoformat() if self.alert_time else None,
            'read_time': self.read_time.isoformat() if self.read_time else None,
            'resolved_time': self.resolved_time.isoformat() if self.resolved_time else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class MarketNews(Base):
    """市场新闻表 - 存储所有新闻数据（不依赖监控股票）"""
    __tablename__ = 'market_news'

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 新闻唯一标识（用标题+来源+发布时间的hash）
    news_id = Column(String(64), unique=True, nullable=False, index=True)

    # 基本信息
    title = Column(String(500), nullable=False)
    content = Column(Text)
    summary = Column(String(1000))

    # 来源信息
    source = Column(String(50), nullable=False, index=True)  # cninfo/eastmoney/sina/cls/ths...
    source_type = Column(String(30), index=True)  # market/stock/announcement/management
    source_url = Column(String(500))

    # 关联股票（可为空，市场新闻不关联具体股票）
    stock_code = Column(String(20), index=True)
    stock_name = Column(String(50))

    # 时间
    pub_time = Column(DateTime, index=True)  # 发布时间
    fetch_time = Column(DateTime, default=datetime.utcnow)  # 抓取时间

    # 情绪分析
    sentiment = Column(String(20), index=True)  # positive/negative/neutral
    sentiment_score = Column(Integer)  # 0-100

    # 分类标签
    category = Column(String(50))  # 新闻分类
    keywords = Column(JSON)  # 关键词列表

    # 额外数据（JSON，存储各数据源特有字段）
    extra_data = Column(JSON)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # 索引
    __table_args__ = (
        Index('idx_market_news_source_time', 'source', 'pub_time'),
        Index('idx_market_news_stock_time', 'stock_code', 'pub_time'),
        Index('idx_market_news_sentiment', 'sentiment', 'pub_time'),
    )

    def __repr__(self):
        return f"<MarketNews(title='{self.title[:30]}...', source='{self.source}')>"

    def to_dict(self):
        return {
            'id': self.id,
            'news_id': self.news_id,
            'title': self.title,
            'content': self.content,
            'summary': self.summary,
            'source': self.source,
            'source_type': self.source_type,
            'source_url': self.source_url,
            'stock_code': self.stock_code,
            'stock_name': self.stock_name,
            'pub_time': self.pub_time.isoformat() if self.pub_time else None,
            'fetch_time': self.fetch_time.isoformat() if self.fetch_time else None,
            'sentiment': self.sentiment,
            'sentiment_score': self.sentiment_score,
            'category': self.category,
            'keywords': self.keywords,
            'extra_data': self.extra_data,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class AlertRule(Base):
    """自定义预警规则表"""
    __tablename__ = 'alert_rules'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)  # 规则名称
    description = Column(Text)  # 规则描述

    # 规则类型
    rule_type = Column(String(50), nullable=False)  # pledge/restricted/holder_sell/limit_down/st/suspend/custom

    # 触发条件 (JSON格式)
    # 例如: {"field": "pledge_ratio", "operator": ">", "value": 50}
    conditions = Column(JSON, nullable=False)

    # 预警级别
    alert_level = Column(String(20), default='medium')  # critical/high/medium/low

    # 适用范围
    apply_to_all = Column(Integer, default=1)  # 1=所有股票, 0=指定股票
    stock_codes = Column(JSON)  # 指定的股票代码列表

    # 通知设置
    notify_email = Column(Integer, default=0)  # 是否邮件通知
    notify_wechat = Column(Integer, default=0)  # 是否微信通知

    # 状态
    is_enabled = Column(Integer, default=1)  # 是否启用

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<AlertRule(name='{self.name}', type='{self.rule_type}')>"

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'rule_type': self.rule_type,
            'conditions': self.conditions,
            'alert_level': self.alert_level,
            'apply_to_all': bool(self.apply_to_all),
            'stock_codes': self.stock_codes,
            'notify_email': bool(self.notify_email),
            'notify_wechat': bool(self.notify_wechat),
            'is_enabled': bool(self.is_enabled),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
