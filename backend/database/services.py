"""
数据库服务层
封装所有数据库操作
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from backend.database.models import AnalysisSession, AgentResult, StockHistory


class SessionService:
    """分析会话服务"""
    
    @staticmethod
    def create_session(
        db: Session,
        session_id: str,
        stock_code: str,
        stock_name: Optional[str] = None
    ) -> AnalysisSession:
        """创建新会话"""
        session = AnalysisSession(
            session_id=session_id,
            stock_code=stock_code,
            stock_name=stock_name,
            status="created",
            progress=0,
            current_stage=0,
            start_time=datetime.utcnow()
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        
        print(f"[数据库] 创建会话: {session_id}")
        return session
    
    @staticmethod
    def get_session(db: Session, session_id: str) -> Optional[AnalysisSession]:
        """获取会话"""
        return db.query(AnalysisSession).filter(
            AnalysisSession.session_id == session_id
        ).first()
    
    @staticmethod
    def update_session_status(
        db: Session,
        session_id: str,
        status: str,
        progress: Optional[int] = None,
        current_stage: Optional[int] = None,
        error_message: Optional[str] = None
    ) -> Optional[AnalysisSession]:
        """更新会话状态"""
        session = SessionService.get_session(db, session_id)
        if not session:
            return None
        
        session.status = status
        if progress is not None:
            session.progress = progress
        if current_stage is not None:
            session.current_stage = current_stage
        if error_message is not None:
            session.error_message = error_message
        
        if status in ['completed', 'error']:
            session.end_time = datetime.utcnow()
        
        db.commit()
        db.refresh(session)
        
        print(f"[数据库] 更新会话: {session_id}, 状态: {status}, 进度: {progress}%")
        return session
    
    @staticmethod
    def get_active_sessions(db: Session, limit: int = 100) -> List[AnalysisSession]:
        """获取活跃会话"""
        return db.query(AnalysisSession).filter(
            AnalysisSession.status.in_(['created', 'running'])
        ).order_by(desc(AnalysisSession.created_at)).limit(limit).all()
    
    @staticmethod
    def get_sessions_by_stock(
        db: Session,
        stock_code: str,
        limit: int = 10
    ) -> List[AnalysisSession]:
        """获取某股票的历史会话"""
        return db.query(AnalysisSession).filter(
            AnalysisSession.stock_code == stock_code
        ).order_by(desc(AnalysisSession.created_at)).limit(limit).all()
    
    @staticmethod
    def clean_old_sessions(db: Session, days: int = 7) -> int:
        """清理旧会话"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        count = db.query(AnalysisSession).filter(
            AnalysisSession.created_at < cutoff_date,
            AnalysisSession.status.in_(['completed', 'error'])
        ).delete()
        db.commit()
        
        print(f"[数据库] 清理旧会话: {count} 条")
        return count


class AgentResultService:
    """智能体结果服务"""
    
    @staticmethod
    def create_or_update_result(
        db: Session,
        session_id: str,
        agent_id: str,
        agent_name: str,
        status: str,
        output: Optional[str] = None,
        tokens: Optional[int] = None,
        thoughts: Optional[List[Dict]] = None,
        data_sources: Optional[List[Dict]] = None,
        error_message: Optional[str] = None
    ) -> AgentResult:
        """创建或更新智能体结果"""
        # 查找现有记录
        result = db.query(AgentResult).filter(
            AgentResult.session_id == session_id,
            AgentResult.agent_id == agent_id
        ).first()
        
        now = datetime.utcnow()
        
        if result:
            # 更新现有记录
            result.status = status
            if output is not None:
                result.output = output
            if tokens is not None:
                result.tokens = tokens
            if thoughts is not None:
                result.thoughts = thoughts
            if data_sources is not None:
                result.data_sources = data_sources
            if error_message is not None:
                result.error_message = error_message
            
            if status == 'running' and not result.start_time:
                result.start_time = now
            elif status in ['completed', 'error']:
                result.end_time = now
                if result.start_time:
                    result.duration_seconds = int((now - result.start_time).total_seconds())
        else:
            # 创建新记录
            result = AgentResult(
                session_id=session_id,
                agent_id=agent_id,
                agent_name=agent_name,
                status=status,
                output=output,
                tokens=tokens,
                thoughts=thoughts,
                data_sources=data_sources,
                error_message=error_message,
                start_time=now if status == 'running' else None
            )
            db.add(result)
        
        db.commit()
        db.refresh(result)
        
        print(f"[数据库] 保存智能体结果: {agent_id}, 状态: {status}")
        return result
    
    @staticmethod
    def get_result(db: Session, session_id: str, agent_id: str) -> Optional[AgentResult]:
        """获取智能体结果"""
        return db.query(AgentResult).filter(
            AgentResult.session_id == session_id,
            AgentResult.agent_id == agent_id
        ).first()
    
    @staticmethod
    def get_session_results(db: Session, session_id: str) -> List[AgentResult]:
        """获取会话的所有智能体结果"""
        return db.query(AgentResult).filter(
            AgentResult.session_id == session_id
        ).order_by(AgentResult.created_at).all()
    
    @staticmethod
    def get_completed_agents(db: Session, session_id: str) -> List[str]:
        """获取已完成的智能体ID列表"""
        results = db.query(AgentResult.agent_id).filter(
            AgentResult.session_id == session_id,
            AgentResult.status == 'completed'
        ).all()
        return [r[0] for r in results]


class StockHistoryService:
    """股票历史服务"""
    
    @staticmethod
    def update_stock_history(
        db: Session,
        stock_code: str,
        stock_name: Optional[str] = None
    ) -> StockHistory:
        """更新股票历史统计"""
        history = db.query(StockHistory).filter(
            StockHistory.stock_code == stock_code
        ).first()
        
        if history:
            history.analysis_count += 1
            history.last_analysis_time = datetime.utcnow()
            if stock_name:
                history.stock_name = stock_name
            history.updated_at = datetime.utcnow()
        else:
            history = StockHistory(
                stock_code=stock_code,
                stock_name=stock_name,
                analysis_count=1,
                last_analysis_time=datetime.utcnow()
            )
            db.add(history)
        
        db.commit()
        db.refresh(history)
        return history
    
    @staticmethod
    def get_popular_stocks(db: Session, limit: int = 10) -> List[StockHistory]:
        """获取热门股票"""
        return db.query(StockHistory).order_by(
            desc(StockHistory.analysis_count)
        ).limit(limit).all()
    
    @staticmethod
    def get_recent_stocks(db: Session, limit: int = 10) -> List[StockHistory]:
        """获取最近分析的股票"""
        return db.query(StockHistory).order_by(
            desc(StockHistory.last_analysis_time)
        ).limit(limit).all()


class StatisticsService:
    """统计服务"""
    
    @staticmethod
    def get_analysis_stats(db: Session, days: int = 7) -> Dict[str, Any]:
        """获取分析统计"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # 总分析次数
        total_count = db.query(func.count(AnalysisSession.id)).filter(
            AnalysisSession.created_at >= cutoff_date
        ).scalar()
        
        # 成功/失败统计
        status_stats = db.query(
            AnalysisSession.status,
            func.count(AnalysisSession.id)
        ).filter(
            AnalysisSession.created_at >= cutoff_date
        ).group_by(AnalysisSession.status).all()
        
        # 平均分析时长 - 使用Python计算而不SQL（SQLite不支持extract）
        completed_sessions = db.query(AnalysisSession).filter(
            AnalysisSession.created_at >= cutoff_date,
            AnalysisSession.status == 'completed',
            AnalysisSession.end_time.isnot(None),
            AnalysisSession.start_time.isnot(None)
        ).all()
        
        if completed_sessions:
            durations = []
            for session in completed_sessions:
                duration = (session.end_time - session.start_time).total_seconds()
                # 过滤异常值
                if 0 <= duration <= 86400:  # 0到1天
                    durations.append(duration)
            
            avg_duration = int(sum(durations) / len(durations)) if durations else 0
        else:
            avg_duration = 0
        
        return {
            'total_count': total_count or 0,
            'status_distribution': {status: count for status, count in status_stats},
            'avg_duration_seconds': avg_duration,
            'period_days': days
        }
    
    @staticmethod
    def get_agent_stats(db: Session, days: int = 7) -> List[Dict[str, Any]]:
        """获取智能体统计"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        stats = db.query(
            AgentResult.agent_id,
            AgentResult.agent_name,
            func.count(AgentResult.id).label('total_runs'),
            func.avg(AgentResult.duration_seconds).label('avg_duration'),
            func.max(AgentResult.duration_seconds).label('max_duration'),
            func.sum(AgentResult.tokens).label('total_tokens')
        ).filter(
            AgentResult.created_at >= cutoff_date,
            AgentResult.status == 'completed'
        ).group_by(
            AgentResult.agent_id,
            AgentResult.agent_name
        ).all()
        
        return [
            {
                'agent_id': s.agent_id,
                'agent_name': s.agent_name,
                'total_runs': s.total_runs,
                'avg_duration': int(s.avg_duration) if s.avg_duration else 0,
                'max_duration': s.max_duration or 0,
                'total_tokens': s.total_tokens or 0
            }
            for s in stats
        ]
