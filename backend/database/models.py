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
    status = Column(String(20), nullable=False, index=True)  # created, running, completed, error
    progress = Column(Integer, default=0)
    current_stage = Column(Integer, default=0)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
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
