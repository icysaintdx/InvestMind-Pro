"""
数据库服务层
封装所有数据库操作
"""

import json
import time
from datetime import datetime, timedelta, date
from decimal import Decimal
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from sqlalchemy.exc import OperationalError

from backend.database.models import AnalysisSession, AgentResult, StockHistory, MonitoredStock, StockDataRecord, StockNewsRecord, DataFlowDailyStats, AlertHistory, AlertRule


def json_serializable(obj):
    """
    将对象转换为 JSON 可序列化的格式
    处理 datetime.date, datetime.datetime, Decimal 等类型
    """
    if obj is None:
        return None
    elif isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [json_serializable(item) for item in obj]
    else:
        return obj


def retry_on_db_error(max_retries=3, delay=0.5):
    """数据库操作重试装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except OperationalError as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        time.sleep(delay * (attempt + 1))
                        continue
                    raise
                except Exception as e:
                    # 其他错误直接抛出
                    raise
            raise last_error
        return wrapper
    return decorator


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
        now = datetime.utcnow()
        session = AnalysisSession(
            session_id=session_id,
            stock_code=stock_code,
            stock_name=stock_name,
            status="created",
            progress=0,
            current_stage=0,
            start_time=now,
            actual_elapsed_seconds=0,
            last_activity_time=now
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
        error_message: Optional[str] = None,
        increment_elapsed: Optional[int] = None
    ) -> Optional[AnalysisSession]:
        """更新会话状态"""
        session = SessionService.get_session(db, session_id)
        if not session:
            return None

        now = datetime.utcnow()
        session.status = status
        session.last_activity_time = now

        if progress is not None:
            session.progress = progress
        if current_stage is not None:
            session.current_stage = current_stage
        if error_message is not None:
            session.error_message = error_message

        # 增加实际运行时间
        if increment_elapsed is not None:
            session.actual_elapsed_seconds = (session.actual_elapsed_seconds or 0) + increment_elapsed

        if status in ['completed', 'error', 'interrupted']:
            session.end_time = now

        db.commit()
        db.refresh(session)

        print(f"[数据库] 更新会话: {session_id}, 状态: {status}, 进度: {progress}%")
        return session

    @staticmethod
    def update_activity_time(db: Session, session_id: str, elapsed_increment: int = 0) -> Optional[AnalysisSession]:
        """更新最后活动时间和累计运行时间"""
        session = SessionService.get_session(db, session_id)
        if not session:
            return None

        now = datetime.utcnow()
        session.last_activity_time = now
        if elapsed_increment > 0:
            session.actual_elapsed_seconds = (session.actual_elapsed_seconds or 0) + elapsed_increment

        db.commit()
        db.refresh(session)
        return session

    @staticmethod
    def check_and_mark_interrupted(db: Session, timeout_seconds: int = 120) -> List[AnalysisSession]:
        """
        检查并标记中断的会话
        如果会话状态是 running 但最后活动时间超过 timeout_seconds，标记为 interrupted
        """
        cutoff_time = datetime.utcnow() - timedelta(seconds=timeout_seconds)
        interrupted_sessions = []

        # 查找所有 running 状态但长时间无活动的会话
        sessions = db.query(AnalysisSession).filter(
            AnalysisSession.status == 'running',
            AnalysisSession.last_activity_time < cutoff_time
        ).all()

        for session in sessions:
            session.status = 'interrupted'
            session.error_message = f"会话中断：服务重启或长时间无响应（最后活动时间: {session.last_activity_time}）"
            interrupted_sessions.append(session)
            print(f"[数据库] 标记会话为中断: {session.session_id}")

        if interrupted_sessions:
            db.commit()

        return interrupted_sessions
    
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


# ==================== 数据流监控服务 ====================

class MonitoredStockService:
    """监控股票服务"""
    
    @staticmethod
    def add_stock(
        db: Session,
        ts_code: str,
        name: str,
        frequency: str = '1h',
        retention_days: int = 7,
        items: Optional[Dict] = None
    ) -> MonitoredStock:
        """添加监控股票"""
        # 检查是否已存在
        existing = db.query(MonitoredStock).filter(
            MonitoredStock.ts_code == ts_code
        ).first()
        
        if existing:
            # 更新配置
            existing.name = name
            existing.frequency = frequency
            existing.retention_days = retention_days
            if items:
                existing.items = items
            existing.is_active = 1
            existing.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(existing)
            return existing
        
        # 创建新监控
        stock = MonitoredStock(
            ts_code=ts_code,
            name=name,
            frequency=frequency,
            retention_days=retention_days,
            items=items or {},
            is_active=1
        )
        db.add(stock)
        db.commit()
        db.refresh(stock)
        print(f"[数据库] 添加监控股票: {ts_code} ({name})")
        return stock
    
    @staticmethod
    def get_all_active(db: Session) -> List[MonitoredStock]:
        """获取所有活跃监控股票"""
        return db.query(MonitoredStock).filter(
            MonitoredStock.is_active == 1
        ).all()
    
    @staticmethod
    def get_stock(db: Session, ts_code: str) -> Optional[MonitoredStock]:
        """获取监控股票"""
        return db.query(MonitoredStock).filter(
            MonitoredStock.ts_code == ts_code
        ).first()
    
    @staticmethod
    def update_last_update(db: Session, ts_code: str):
        """更新最后更新时间（使用本地时间）"""
        stock = MonitoredStockService.get_stock(db, ts_code)
        if stock:
            stock.last_update = datetime.now()  # 使用本地时间而非UTC
            db.commit()
    
    @staticmethod
    def remove_stock(db: Session, ts_code: str) -> bool:
        """移除监控股票（软删除）"""
        stock = MonitoredStockService.get_stock(db, ts_code)
        if stock:
            stock.is_active = 0
            stock.updated_at = datetime.utcnow()
            db.commit()
            return True
        return False
    
    @staticmethod
    def delete_stock(db: Session, ts_code: str) -> bool:
        """删除监控股票（硬删除，级联删除所有数据）"""
        count = db.query(MonitoredStock).filter(
            MonitoredStock.ts_code == ts_code
        ).delete()
        db.commit()
        if count > 0:
            print(f"[数据库] 删除监控股票: {ts_code}")
            return True
        return False


class StockDataService:
    """股票数据服务（替换更新）"""

    @staticmethod
    def save_or_update(
        db: Session,
        ts_code: str,
        data_type: str,
        data: Dict,
        source: str = 'tushare',
        data_date: Optional[str] = None,
        max_retries: int = 3
    ) -> Optional[StockDataRecord]:
        """
        保存或更新股票数据（替换更新）
        同一股票同一类型同一天只保留一条记录

        增加重试机制处理 SQLite 并发写入问题
        """
        if not data_date:
            data_date = datetime.utcnow().strftime('%Y-%m-%d')

        # 转换数据为 JSON 可序列化格式（处理 datetime.date, Decimal 等）
        serializable_data = json_serializable(data)

        last_error = None
        for attempt in range(max_retries):
            try:
                # 查找现有记录
                record = db.query(StockDataRecord).filter(
                    StockDataRecord.ts_code == ts_code,
                    StockDataRecord.data_type == data_type,
                    StockDataRecord.data_date == data_date
                ).first()

                if record:
                    # 更新现有记录
                    record.data = serializable_data
                    record.source = source
                    record.fetch_time = datetime.utcnow()
                    record.updated_at = datetime.utcnow()
                else:
                    # 创建新记录
                    record = StockDataRecord(
                        ts_code=ts_code,
                        data_type=data_type,
                        data_date=data_date,
                        data=serializable_data,
                        source=source
                    )
                    db.add(record)

                db.commit()
                db.refresh(record)
                return record

            except OperationalError as e:
                last_error = e
                db.rollback()
                if attempt < max_retries - 1:
                    time.sleep(0.5 * (attempt + 1))  # 递增延迟
                    continue
                print(f"[数据库] 保存失败 {ts_code}/{data_type}: {e}")
                return None
            except Exception as e:
                db.rollback()
                print(f"[数据库] 保存异常 {ts_code}/{data_type}: {e}")
                return None

        return None
    
    @staticmethod
    def get_latest(
        db: Session,
        ts_code: str,
        data_type: str
    ) -> Optional[StockDataRecord]:
        """获取最新数据"""
        return db.query(StockDataRecord).filter(
            StockDataRecord.ts_code == ts_code,
            StockDataRecord.data_type == data_type
        ).order_by(desc(StockDataRecord.data_date)).first()
    
    @staticmethod
    def get_by_date_range(
        db: Session,
        ts_code: str,
        data_type: str,
        start_date: str,
        end_date: str
    ) -> List[StockDataRecord]:
        """获取日期范围内的数据"""
        return db.query(StockDataRecord).filter(
            StockDataRecord.ts_code == ts_code,
            StockDataRecord.data_type == data_type,
            StockDataRecord.data_date >= start_date,
            StockDataRecord.data_date <= end_date
        ).order_by(desc(StockDataRecord.data_date)).all()
    
    @staticmethod
    def clean_old_data(db: Session, ts_code: str, retention_days: int = 7) -> int:
        """清理旧数据"""
        cutoff_date = (datetime.utcnow() - timedelta(days=retention_days)).strftime('%Y-%m-%d')
        count = db.query(StockDataRecord).filter(
            StockDataRecord.ts_code == ts_code,
            StockDataRecord.data_date < cutoff_date
        ).delete()
        db.commit()
        if count > 0:
            print(f"[数据库] 清理旧数据: {ts_code}, 删除{count}条")
        return count

    @staticmethod
    def get_data_types_by_prefix(
        db: Session,
        ts_code: str,
        prefix: str
    ) -> List[str]:
        """获取指定前缀的所有数据类型"""
        records = db.query(StockDataRecord.data_type).filter(
            StockDataRecord.ts_code == ts_code,
            StockDataRecord.data_type.like(f"{prefix}%")
        ).distinct().all()
        return [r[0] for r in records]

    @staticmethod
    def get_all_data_types(db: Session, ts_code: str) -> List[str]:
        """获取股票的所有数据类型"""
        records = db.query(StockDataRecord.data_type).filter(
            StockDataRecord.ts_code == ts_code
        ).distinct().all()
        return [r[0] for r in records]


class StockNewsService:
    """股票新闻服务（增量更新）"""
    
    @staticmethod
    def add_news(
        db: Session,
        ts_code: str,
        news_id: str,
        title: str,
        content: Optional[str] = None,
        summary: Optional[str] = None,
        source: Optional[str] = None,
        url: Optional[str] = None,
        pub_time: Optional[datetime] = None,
        sentiment: Optional[str] = None,
        sentiment_score: Optional[int] = None,
        urgency: Optional[str] = None,
        report_type: Optional[str] = None,
        keywords: Optional[List] = None
    ) -> Optional[StockNewsRecord]:
        """
        添加新闻（增量更新）
        如果news_id已存在则跳过
        """
        # 检查是否已存在
        existing = db.query(StockNewsRecord).filter(
            StockNewsRecord.news_id == news_id
        ).first()
        
        if existing:
            # 已存在，跳过
            return None
        
        # 创建新记录
        news = StockNewsRecord(
            ts_code=ts_code,
            news_id=news_id,
            title=title,
            content=content,
            summary=summary,
            source=source,
            url=url,
            pub_time=pub_time or datetime.utcnow(),
            sentiment=sentiment,
            sentiment_score=sentiment_score,
            urgency=urgency,
            report_type=report_type,
            keywords=keywords
        )
        db.add(news)
        db.commit()
        db.refresh(news)
        return news
    
    @staticmethod
    def batch_add_news(
        db: Session,
        news_list: List[Dict]
    ) -> int:
        """批量添加新闻"""
        added_count = 0
        for news_data in news_list:
            result = StockNewsService.add_news(db, **news_data)
            if result:
                added_count += 1
        
        if added_count > 0:
            print(f"[数据库] 批量添加新闻: {added_count}条")
        return added_count
    
    @staticmethod
    def get_latest_news(
        db: Session,
        ts_code: str,
        limit: int = 20
    ) -> List[StockNewsRecord]:
        """获取最新新闻（只返回有标题的新闻）"""
        return db.query(StockNewsRecord).filter(
            StockNewsRecord.ts_code == ts_code,
            StockNewsRecord.title.isnot(None),
            StockNewsRecord.title != ''
        ).order_by(desc(StockNewsRecord.pub_time)).limit(limit).all()
    
    @staticmethod
    def get_news_by_date_range(
        db: Session,
        ts_code: str,
        start_date: datetime,
        end_date: datetime,
        limit: int = 100
    ) -> List[StockNewsRecord]:
        """获取日期范围内的新闻"""
        return db.query(StockNewsRecord).filter(
            StockNewsRecord.ts_code == ts_code,
            StockNewsRecord.pub_time >= start_date,
            StockNewsRecord.pub_time <= end_date
        ).order_by(desc(StockNewsRecord.pub_time)).limit(limit).all()
    
    @staticmethod
    def clean_old_news(db: Session, ts_code: str, retention_days: int = 7) -> int:
        """清理旧新闻"""
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        count = db.query(StockNewsRecord).filter(
            StockNewsRecord.ts_code == ts_code,
            StockNewsRecord.created_at < cutoff_date
        ).delete()
        db.commit()
        if count > 0:
            print(f"[数据库] 清理旧新闻: {ts_code}, 删除{count}条")
        return count


class DataFlowStatsService:
    """数据流统计服务"""
    
    @staticmethod
    def update_daily_stats(
        db: Session,
        stat_date: Optional[str] = None,
        news_count_inc: int = 0,
        risk_alerts_inc: int = 0,
        analysis_tasks_inc: int = 0,
        api_calls: Optional[Dict[str, int]] = None
    ) -> DataFlowDailyStats:
        """更新每日统计"""
        if not stat_date:
            stat_date = datetime.utcnow().strftime('%Y-%m-%d')
        
        # 查找现有记录
        stats = db.query(DataFlowDailyStats).filter(
            DataFlowDailyStats.stat_date == stat_date
        ).first()
        
        if stats:
            # 更新
            stats.news_count += news_count_inc
            stats.risk_alerts += risk_alerts_inc
            stats.analysis_tasks += analysis_tasks_inc
            if api_calls:
                for key, value in api_calls.items():
                    if key in stats.api_calls:
                        stats.api_calls[key] += value
                    else:
                        stats.api_calls[key] = value
            stats.updated_at = datetime.utcnow()
        else:
            # 创建
            stats = DataFlowDailyStats(
                stat_date=stat_date,
                news_count=news_count_inc,
                risk_alerts=risk_alerts_inc,
                analysis_tasks=analysis_tasks_inc,
                api_calls=api_calls or {}
            )
            db.add(stats)
        
        db.commit()
        db.refresh(stats)
        return stats
    
    @staticmethod
    def get_stats(db: Session, stat_date: str) -> Optional[DataFlowDailyStats]:
        """获取指定日期统计"""
        return db.query(DataFlowDailyStats).filter(
            DataFlowDailyStats.stat_date == stat_date
        ).first()
    
    @staticmethod
    def get_recent_stats(db: Session, days: int = 7) -> List[DataFlowDailyStats]:
        """获取近期统计"""
        cutoff_date = (datetime.utcnow() - timedelta(days=days)).strftime('%Y-%m-%d')
        return db.query(DataFlowDailyStats).filter(
            DataFlowDailyStats.stat_date >= cutoff_date
        ).order_by(desc(DataFlowDailyStats.stat_date)).all()


class AlertHistoryService:
    """预警历史服务"""

    @staticmethod
    def save_alert(
        db: Session,
        ts_code: str,
        alert_type: str,
        alert_level: str,
        title: str,
        message: str = '',
        suggestion: str = '',
        stock_name: str = ''
    ) -> AlertHistory:
        """保存预警记录"""
        # 检查是否已存在相同预警（避免重复）
        existing = db.query(AlertHistory).filter(
            AlertHistory.ts_code == ts_code,
            AlertHistory.alert_type == alert_type,
            AlertHistory.title == title,
            AlertHistory.alert_time >= datetime.utcnow() - timedelta(hours=24)
        ).first()

        if existing:
            # 更新现有记录
            existing.message = message
            existing.suggestion = suggestion
            existing.alert_level = alert_level
            db.commit()
            return existing

        # 创建新记录
        alert = AlertHistory(
            ts_code=ts_code,
            stock_name=stock_name,
            alert_type=alert_type,
            alert_level=alert_level,
            title=title,
            message=message,
            suggestion=suggestion,
            alert_time=datetime.utcnow()
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)
        return alert

    @staticmethod
    def save_alerts_batch(db: Session, ts_code: str, alerts: List[Dict], stock_name: str = '') -> int:
        """批量保存预警记录"""
        saved_count = 0
        for alert in alerts:
            try:
                AlertHistoryService.save_alert(
                    db=db,
                    ts_code=ts_code,
                    alert_type=alert.get('type', 'unknown'),
                    alert_level=alert.get('level', 'medium'),
                    title=alert.get('title', ''),
                    message=alert.get('message', ''),
                    suggestion=alert.get('suggestion', ''),
                    stock_name=stock_name
                )
                saved_count += 1
            except Exception as e:
                print(f"[数据库] 保存预警失败: {e}")
        return saved_count

    @staticmethod
    def get_alerts_by_stock(
        db: Session,
        ts_code: str,
        limit: int = 50,
        include_read: bool = True
    ) -> List[AlertHistory]:
        """获取股票的预警历史"""
        query = db.query(AlertHistory).filter(AlertHistory.ts_code == ts_code)
        if not include_read:
            query = query.filter(AlertHistory.is_read == 0)
        return query.order_by(desc(AlertHistory.alert_time)).limit(limit).all()

    @staticmethod
    def get_recent_alerts(
        db: Session,
        days: int = 7,
        level: Optional[str] = None,
        limit: int = 100
    ) -> List[AlertHistory]:
        """获取近期所有预警"""
        cutoff = datetime.utcnow() - timedelta(days=days)
        query = db.query(AlertHistory).filter(AlertHistory.alert_time >= cutoff)
        if level:
            query = query.filter(AlertHistory.alert_level == level)
        return query.order_by(desc(AlertHistory.alert_time)).limit(limit).all()

    @staticmethod
    def get_unread_count(db: Session, ts_code: Optional[str] = None) -> int:
        """获取未读预警数量"""
        query = db.query(func.count(AlertHistory.id)).filter(AlertHistory.is_read == 0)
        if ts_code:
            query = query.filter(AlertHistory.ts_code == ts_code)
        return query.scalar() or 0

    @staticmethod
    def mark_as_read(db: Session, alert_id: int) -> bool:
        """标记预警为已读"""
        alert = db.query(AlertHistory).filter(AlertHistory.id == alert_id).first()
        if alert:
            alert.is_read = 1
            alert.read_time = datetime.utcnow()
            db.commit()
            return True
        return False

    @staticmethod
    def mark_all_as_read(db: Session, ts_code: Optional[str] = None) -> int:
        """标记所有预警为已读"""
        query = db.query(AlertHistory).filter(AlertHistory.is_read == 0)
        if ts_code:
            query = query.filter(AlertHistory.ts_code == ts_code)
        count = query.update({
            AlertHistory.is_read: 1,
            AlertHistory.read_time: datetime.utcnow()
        })
        db.commit()
        return count

    @staticmethod
    def cleanup_old_alerts(db: Session, days: int = 30) -> int:
        """清理旧预警记录"""
        cutoff = datetime.utcnow() - timedelta(days=days)
        count = db.query(AlertHistory).filter(
            AlertHistory.alert_time < cutoff
        ).delete()
        db.commit()
        return count


class AlertRuleService:
    """预警规则服务"""

    # 预定义的规则类型
    RULE_TYPES = {
        'pledge': '股权质押',
        'restricted': '限售解禁',
        'holder_sell': '股东减持',
        'limit_down': '跌停预警',
        'st': 'ST风险',
        'suspend': '停牌预警',
        'audit': '审计意见',
        'forecast': '业绩预告',
        'custom': '自定义'
    }

    # 支持的操作符
    OPERATORS = ['>', '<', '>=', '<=', '==', '!=', 'contains', 'not_contains']

    @staticmethod
    def create_rule(
        db: Session,
        name: str,
        rule_type: str,
        conditions: Dict,
        alert_level: str = 'medium',
        description: str = '',
        apply_to_all: bool = True,
        stock_codes: List[str] = None,
        notify_email: bool = False,
        notify_wechat: bool = False
    ) -> AlertRule:
        """创建预警规则"""
        rule = AlertRule(
            name=name,
            description=description,
            rule_type=rule_type,
            conditions=conditions,
            alert_level=alert_level,
            apply_to_all=1 if apply_to_all else 0,
            stock_codes=stock_codes,
            notify_email=1 if notify_email else 0,
            notify_wechat=1 if notify_wechat else 0,
            is_enabled=1
        )
        db.add(rule)
        db.commit()
        db.refresh(rule)
        return rule

    @staticmethod
    def get_rule(db: Session, rule_id: int) -> Optional[AlertRule]:
        """获取单个规则"""
        return db.query(AlertRule).filter(AlertRule.id == rule_id).first()

    @staticmethod
    def get_all_rules(db: Session, enabled_only: bool = False) -> List[AlertRule]:
        """获取所有规则"""
        query = db.query(AlertRule)
        if enabled_only:
            query = query.filter(AlertRule.is_enabled == 1)
        return query.order_by(desc(AlertRule.created_at)).all()

    @staticmethod
    def get_rules_for_stock(db: Session, ts_code: str) -> List[AlertRule]:
        """获取适用于指定股票的规则"""
        rules = db.query(AlertRule).filter(AlertRule.is_enabled == 1).all()
        applicable = []
        for rule in rules:
            if rule.apply_to_all:
                applicable.append(rule)
            elif rule.stock_codes and ts_code in rule.stock_codes:
                applicable.append(rule)
        return applicable

    @staticmethod
    def update_rule(
        db: Session,
        rule_id: int,
        **kwargs
    ) -> Optional[AlertRule]:
        """更新规则"""
        rule = db.query(AlertRule).filter(AlertRule.id == rule_id).first()
        if not rule:
            return None

        for key, value in kwargs.items():
            if hasattr(rule, key):
                if key in ['apply_to_all', 'notify_email', 'notify_wechat', 'is_enabled']:
                    value = 1 if value else 0
                setattr(rule, key, value)

        db.commit()
        db.refresh(rule)
        return rule

    @staticmethod
    def delete_rule(db: Session, rule_id: int) -> bool:
        """删除规则"""
        rule = db.query(AlertRule).filter(AlertRule.id == rule_id).first()
        if rule:
            db.delete(rule)
            db.commit()
            return True
        return False

    @staticmethod
    def toggle_rule(db: Session, rule_id: int) -> Optional[AlertRule]:
        """切换规则启用状态"""
        rule = db.query(AlertRule).filter(AlertRule.id == rule_id).first()
        if rule:
            rule.is_enabled = 0 if rule.is_enabled else 1
            db.commit()
            db.refresh(rule)
        return rule

    @staticmethod
    def check_condition(data: Dict, condition: Dict) -> bool:
        """
        检查数据是否满足条件

        Args:
            data: 股票数据字典
            condition: 条件字典 {"field": "pledge_ratio", "operator": ">", "value": 50}
        """
        field = condition.get('field', '')
        operator = condition.get('operator', '==')
        value = condition.get('value')

        # 获取实际值（支持嵌套字段，如 "pledge.pledge_ratio"）
        actual_value = data
        for key in field.split('.'):
            if isinstance(actual_value, dict):
                actual_value = actual_value.get(key)
            else:
                actual_value = None
                break

        if actual_value is None:
            return False

        # 执行比较
        try:
            if operator == '>':
                return float(actual_value) > float(value)
            elif operator == '<':
                return float(actual_value) < float(value)
            elif operator == '>=':
                return float(actual_value) >= float(value)
            elif operator == '<=':
                return float(actual_value) <= float(value)
            elif operator == '==':
                return str(actual_value) == str(value)
            elif operator == '!=':
                return str(actual_value) != str(value)
            elif operator == 'contains':
                return str(value) in str(actual_value)
            elif operator == 'not_contains':
                return str(value) not in str(actual_value)
        except (ValueError, TypeError):
            return False

        return False

    @staticmethod
    def evaluate_rules(db: Session, ts_code: str, data: Dict) -> List[Dict]:
        """
        评估所有适用规则，返回触发的预警

        Args:
            db: 数据库会话
            ts_code: 股票代码
            data: 股票综合数据

        Returns:
            触发的预警列表
        """
        rules = AlertRuleService.get_rules_for_stock(db, ts_code)
        triggered_alerts = []

        for rule in rules:
            conditions = rule.conditions
            if not conditions:
                continue

            # 支持多条件（AND逻辑）
            if isinstance(conditions, list):
                all_match = all(
                    AlertRuleService.check_condition(data, cond)
                    for cond in conditions
                )
            else:
                all_match = AlertRuleService.check_condition(data, conditions)

            if all_match:
                triggered_alerts.append({
                    'rule_id': rule.id,
                    'rule_name': rule.name,
                    'type': rule.rule_type,
                    'level': rule.alert_level,
                    'title': f'[{rule.name}] 触发预警',
                    'message': rule.description or f'规则 "{rule.name}" 的条件已满足',
                    'suggestion': '请关注相关风险',
                    'notify_email': bool(rule.notify_email),
                    'notify_wechat': bool(rule.notify_wechat)
                })

        return triggered_alerts

    @staticmethod
    def get_default_rules() -> List[Dict]:
        """获取默认预警规则模板"""
        return [
            {
                'name': '股权质押过高',
                'rule_type': 'pledge',
                'conditions': {'field': 'pledge.pledge_ratio', 'operator': '>', 'value': 50},
                'alert_level': 'high',
                'description': '股权质押比例超过50%时触发预警'
            },
            {
                'name': '股权质押极高',
                'rule_type': 'pledge',
                'conditions': {'field': 'pledge.pledge_ratio', 'operator': '>', 'value': 70},
                'alert_level': 'critical',
                'description': '股权质押比例超过70%时触发严重预警'
            },
            {
                'name': '近期有限售解禁',
                'rule_type': 'restricted',
                'conditions': {'field': 'restricted.count', 'operator': '>', 'value': 0},
                'alert_level': 'medium',
                'description': '有限售股解禁计划时触发预警'
            },
            {
                'name': 'ST股票',
                'rule_type': 'st',
                'conditions': {'field': 'st_status.is_st', 'operator': '==', 'value': True},
                'alert_level': 'critical',
                'description': '股票被标记为ST时触发严重预警'
            },
            {
                'name': '近期跌停',
                'rule_type': 'limit_down',
                'conditions': {'field': 'limit_list.down_count', 'operator': '>', 'value': 0},
                'alert_level': 'high',
                'description': '近期有跌停记录时触发预警'
            }
        ]
