"""
分析会话管理 API（数据库版本）
支持完整的历史记录查询和统计
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from backend.database.database import get_db, init_database
from backend.database.services import (
    SessionService,
    AgentResultService,
    StockHistoryService,
    StatisticsService
)
from backend.database.models import AnalysisSession, AgentResult

router = APIRouter(prefix="/api/analysis/db", tags=["Analysis Session DB"])

# 确保数据库已初始化
try:
    init_database()
except Exception as e:
    print(f"[数据库] 初始化失败: {e}")


# ==================== Pydantic 模型 ====================

class SessionCreateRequest(BaseModel):
    stock_code: str
    stock_name: Optional[str] = None


class SessionResponse(BaseModel):
    session_id: str
    stock_code: str
    status: str
    message: str


class AgentUpdateRequest(BaseModel):
    agent_id: str
    agent_name: str
    status: str
    output: Optional[str] = None
    tokens: Optional[int] = None
    thoughts: Optional[list] = None
    data_sources: Optional[list] = None
    error_message: Optional[str] = None


# ==================== 会话管理 ====================

@router.post("/session/create", response_model=SessionResponse)
async def create_session(request: SessionCreateRequest, db: Session = Depends(get_db)):
    """创建新的分析会话"""
    import uuid
    import time

    session_id = f"session_{int(time.time())}_{uuid.uuid4().hex[:8]}"

    # 获取股票名称（如果未提供）
    stock_name = request.stock_name
    if not stock_name or stock_name == request.stock_code:
        try:
            from backend.dataflows.data_source_manager import get_data_source_manager
            manager = get_data_source_manager()
            stock_info = manager.get_stock_info(request.stock_code)
            if stock_info and stock_info.get('name'):
                stock_name = stock_info['name']
        except Exception as e:
            print(f"⚠️ 获取股票名称失败: {e}")
            stock_name = request.stock_code

    try:
        # 创建会话
        session = SessionService.create_session(
            db=db,
            session_id=session_id,
            stock_code=request.stock_code,
            stock_name=stock_name
        )

        # 更新股票历史
        StockHistoryService.update_stock_history(
            db=db,
            stock_code=request.stock_code,
            stock_name=stock_name
        )

        return SessionResponse(
            session_id=session_id,
            stock_code=request.stock_code,
            status="created",
            message="会话创建成功"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建会话失败: {str(e)}")


@router.post("/session/{session_id}/start")
async def start_session(session_id: str, db: Session = Depends(get_db)):
    """开始分析"""
    from backend.database.analysis_helper import init_session_timer

    session = SessionService.update_session_status(
        db=db,
        session_id=session_id,
        status="running"
    )

    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    # 初始化会话计时器
    init_session_timer(session_id)

    return {"message": "分析已开始", "session_id": session_id}


@router.get("/session/{session_id}/status")
async def get_session_status(session_id: str, db: Session = Depends(get_db)):
    """查询会话状态"""
    session = SessionService.get_session(db, session_id)

    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    # 检查是否需要标记为中断（如果状态是 running 但长时间无活动）
    if session.status == 'running':
        if session.last_activity_time:
            inactive_seconds = (datetime.utcnow() - session.last_activity_time).total_seconds()
            # 如果超过30秒无活动，标记为中断（缩短超时时间，更快检测到中断）
            if inactive_seconds > 30:
                session = SessionService.update_session_status(
                    db=db,
                    session_id=session_id,
                    status="interrupted",
                    error_message=f"会话中断：服务重启或长时间无响应（无活动时间: {int(inactive_seconds)}秒）"
                )
        else:
            # 没有 last_activity_time 说明从未开始，也标记为中断
            session = SessionService.update_session_status(
                db=db,
                session_id=session_id,
                status="interrupted",
                error_message="会话中断：分析未正常启动"
            )

    # 获取已完成的智能体列表
    completed_agents = AgentResultService.get_completed_agents(db, session_id)

    # 计算运行时间
    elapsed_time = session.actual_elapsed_seconds or 0

    # 如果 actual_elapsed_seconds 为 0 但有 start_time，使用 start_time 计算
    if elapsed_time == 0 and session.start_time:
        # 对于中断的会话，使用 last_activity_time 或 end_time 作为结束点
        end_point = session.end_time or session.last_activity_time or datetime.utcnow()
        elapsed_time = int((end_point - session.start_time).total_seconds())

    # 如果会话正在运行，加上自上次活动以来的时间
    if session.status == 'running' and session.last_activity_time:
        additional_time = (datetime.utcnow() - session.last_activity_time).total_seconds()
        # 加上额外时间（最多300秒，超过说明可能中断了）
        if additional_time < 300:
            elapsed_time += additional_time

    return {
        "session_id": session.session_id,
        "stock_code": session.stock_code,
        "stock_name": session.stock_name,
        "status": session.status,
        "progress": session.progress,
        "current_stage": session.current_stage,
        "completed_agents": completed_agents,
        "total_agents": 21,
        "start_time": session.start_time.timestamp() if session.start_time else None,
        "elapsed_time": int(elapsed_time),
        "actual_elapsed_seconds": session.actual_elapsed_seconds or 0,
        "last_activity_time": session.last_activity_time.timestamp() if session.last_activity_time else None,
        "error_message": session.error_message,
        "can_resume": session.status == 'interrupted' and session.progress < 100  # 是否可以继续
    }


@router.post("/session/{session_id}/update")
async def update_session(
    session_id: str,
    request: AgentUpdateRequest,
    progress: Optional[int] = None,
    current_stage: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """更新会话进度（由后端分析流程调用）"""
    # 保存智能体结果
    AgentResultService.create_or_update_result(
        db=db,
        session_id=session_id,
        agent_id=request.agent_id,
        agent_name=request.agent_name,
        status=request.status,
        output=request.output,
        tokens=request.tokens,
        thoughts=request.thoughts,
        data_sources=request.data_sources,
        error_message=request.error_message
    )
    
    # 更新会话状态
    if progress is not None or current_stage is not None:
        SessionService.update_session_status(
            db=db,
            session_id=session_id,
            status="running",
            progress=progress,
            current_stage=current_stage
        )
    
    return {"message": "更新成功"}


@router.post("/session/{session_id}/complete")
async def complete_session(
    session_id: str,
    success: bool = True,
    error: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """标记会话完成"""
    session = SessionService.update_session_status(
        db=db,
        session_id=session_id,
        status="completed" if success else "error",
        progress=100 if success else None,
        error_message=error
    )
    
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    return {"message": "会话已完成", "status": session.status}


@router.get("/session/{session_id}/agent/{agent_id}")
async def get_agent_result(session_id: str, agent_id: str, db: Session = Depends(get_db)):
    """获取智能体结果"""
    result = AgentResultService.get_result(db, session_id, agent_id)
    
    if not result:
        return {
            "agent_id": agent_id,
            "status": "pending"
        }
    
    return result.to_dict()


# ==================== 历史记录查询 ====================

@router.get("/history/stock/{stock_code}")
async def get_stock_history(
    stock_code: str,
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """查询某股票的历史分析记录"""
    sessions = SessionService.get_sessions_by_stock(db, stock_code, limit)
    
    return {
        "stock_code": stock_code,
        "total": len(sessions),
        "sessions": [s.to_dict() for s in sessions]
    }


@router.get("/history/session/{session_id}/full")
async def get_full_session_history(session_id: str, db: Session = Depends(get_db)):
    """获取完整的会话历史（包括所有智能体结果）"""
    session = SessionService.get_session(db, session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    # 获取所有智能体结果
    agent_results = AgentResultService.get_session_results(db, session_id)
    
    return {
        "session": session.to_dict(),
        "agent_results": [r.to_dict() for r in agent_results]
    }


@router.get("/history/recent")
async def get_recent_sessions(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """获取最近的分析记录"""
    sessions = db.query(AnalysisSession).order_by(
        AnalysisSession.created_at.desc()
    ).limit(limit).all()
    
    return {
        "total": len(sessions),
        "sessions": [s.to_dict() for s in sessions]
    }


@router.get("/history/popular-stocks")
async def get_popular_stocks(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """获取热门股票（分析次数最多）"""
    stocks = StockHistoryService.get_popular_stocks(db, limit)
    
    return {
        "total": len(stocks),
        "stocks": [s.to_dict() for s in stocks]
    }


# ==================== 统计分析 ====================

@router.get("/stats/overview")
async def get_stats_overview(
    days: int = Query(7, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """获取统计概览"""
    analysis_stats = StatisticsService.get_analysis_stats(db, days)
    agent_stats = StatisticsService.get_agent_stats(db, days)
    
    return {
        "analysis": analysis_stats,
        "agents": agent_stats
    }


@router.get("/stats/agents")
async def get_agent_stats(
    days: int = Query(7, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """获取智能体性能统计"""
    stats = StatisticsService.get_agent_stats(db, days)
    
    return {
        "period_days": days,
        "agents": stats
    }


# ==================== 维护 ====================

@router.delete("/session/{session_id}")
async def delete_session(session_id: str, db: Session = Depends(get_db)):
    """删除会话"""
    session = SessionService.get_session(db, session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    db.delete(session)
    db.commit()
    
    return {"message": "会话已删除"}


@router.post("/maintenance/clean-old")
async def clean_old_sessions(
    days: int = Query(7, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """清理旧会话"""
    count = SessionService.clean_old_sessions(db, days)
    
    return {
        "message": f"已清理 {count} 条旧记录",
        "count": count
    }


@router.get("/sessions/active")
async def get_active_sessions(
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """获取所有活跃会话"""
    sessions = SessionService.get_active_sessions(db, limit)
    
    return {
        "total": len(sessions),
        "sessions": [
            {
                "session_id": s.session_id,
                "stock_code": s.stock_code,
                "status": s.status,
                "progress": s.progress,
                "elapsed": int((datetime.utcnow() - s.start_time).total_seconds()) if s.start_time else 0
            }
            for s in sessions
        ]
    }
