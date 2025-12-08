"""
分析会话管理 API
支持会话创建、状态查询、结果获取
实现页面刷新恢复和跨设备访问
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import time
import uuid
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/analysis", tags=["Analysis Session"])

# 内存存储（生产环境应使用 Redis）
analysis_sessions: Dict[str, Dict] = {}

# 会话过期时间（1小时）
SESSION_TIMEOUT = 3600


class SessionRequest(BaseModel):
    stock_code: str
    stock_name: Optional[str] = None


class SessionResponse(BaseModel):
    session_id: str
    stock_code: str
    status: str
    message: str


class SessionStatus(BaseModel):
    session_id: str
    stock_code: str
    stock_name: Optional[str]
    status: str  # running, completed, error
    progress: int  # 0-100
    current_stage: int  # 1-4
    completed_agents: List[str]
    total_agents: int
    start_time: float
    elapsed_time: float
    error_message: Optional[str] = None


class AgentResult(BaseModel):
    agent_id: str
    status: str  # pending, running, completed, error
    output: Optional[str] = None
    tokens: Optional[int] = None
    thoughts: Optional[List[Dict]] = None
    data_sources: Optional[List[Dict]] = None
    error: Optional[str] = None


def create_session_id() -> str:
    """生成唯一的会话ID"""
    return f"session_{int(time.time())}_{uuid.uuid4().hex[:8]}"


def clean_expired_sessions():
    """清理过期的会话"""
    current_time = time.time()
    expired = []
    
    for session_id, session in analysis_sessions.items():
        if current_time - session["start_time"] > SESSION_TIMEOUT:
            expired.append(session_id)
    
    for session_id in expired:
        del analysis_sessions[session_id]
        print(f"[会话清理] 删除过期会话: {session_id}")


@router.post("/session/create", response_model=SessionResponse)
async def create_analysis_session(request: SessionRequest):
    """
    创建新的分析会话
    
    返回 session_id，前端用此ID查询进度和结果
    """
    # 清理过期会话
    clean_expired_sessions()
    
    session_id = create_session_id()
    
    # 初始化会话
    analysis_sessions[session_id] = {
        "session_id": session_id,
        "stock_code": request.stock_code,
        "stock_name": request.stock_name,
        "status": "created",  # created -> running -> completed/error
        "progress": 0,
        "current_stage": 0,
        "completed_agents": [],
        "agent_results": {},
        "start_time": time.time(),
        "error_message": None,
        "total_agents": 21  # 21个智能体
    }
    
    print(f"[会话创建] {session_id} - {request.stock_code}")
    
    return SessionResponse(
        session_id=session_id,
        stock_code=request.stock_code,
        status="created",
        message="会话创建成功，请开始分析"
    )


@router.get("/session/{session_id}/status", response_model=SessionStatus)
async def get_session_status(session_id: str):
    """
    查询会话状态
    
    返回当前进度、完成的智能体列表等
    """
    session = analysis_sessions.get(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在或已过期")
    
    elapsed_time = time.time() - session["start_time"]
    
    return SessionStatus(
        session_id=session_id,
        stock_code=session["stock_code"],
        stock_name=session.get("stock_name"),
        status=session["status"],
        progress=session["progress"],
        current_stage=session["current_stage"],
        completed_agents=session["completed_agents"],
        total_agents=session["total_agents"],
        start_time=session["start_time"],
        elapsed_time=elapsed_time,
        error_message=session.get("error_message")
    )


@router.get("/session/{session_id}/agent/{agent_id}", response_model=AgentResult)
async def get_agent_result(session_id: str, agent_id: str):
    """
    获取特定智能体的结果
    
    支持增量获取，前端可以只请求新完成的智能体
    """
    session = analysis_sessions.get(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    agent_result = session["agent_results"].get(agent_id)
    
    if not agent_result:
        return AgentResult(
            agent_id=agent_id,
            status="pending"
        )
    
    return AgentResult(
        agent_id=agent_id,
        status=agent_result.get("status", "completed"),
        output=agent_result.get("output"),
        tokens=agent_result.get("tokens"),
        thoughts=agent_result.get("thoughts"),
        data_sources=agent_result.get("data_sources"),
        error=agent_result.get("error")
    )


@router.post("/session/{session_id}/start")
async def start_analysis(session_id: str):
    """
    开始分析
    
    将会话状态设置为 running
    """
    session = analysis_sessions.get(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    if session["status"] != "created":
        raise HTTPException(status_code=400, detail="会话已经开始或已完成")
    
    session["status"] = "running"
    session["start_time"] = time.time()
    
    print(f"[会话开始] {session_id}")
    
    return {"message": "分析已开始", "session_id": session_id}


@router.post("/session/{session_id}/update")
async def update_session_progress(
    session_id: str,
    agent_id: str,
    status: str,
    output: Optional[str] = None,
    tokens: Optional[int] = None,
    thoughts: Optional[List[Dict]] = None,
    data_sources: Optional[List[Dict]] = None,
    progress: Optional[int] = None,
    current_stage: Optional[int] = None,
    error: Optional[str] = None
):
    """
    更新会话进度
    
    由后端分析流程调用，更新智能体状态
    """
    session = analysis_sessions.get(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    # 更新智能体结果
    session["agent_results"][agent_id] = {
        "status": status,
        "output": output,
        "tokens": tokens,
        "thoughts": thoughts,
        "data_sources": data_sources,
        "error": error,
        "completed_at": time.time()
    }
    
    # 更新完成列表
    if status == "completed" and agent_id not in session["completed_agents"]:
        session["completed_agents"].append(agent_id)
    
    # 更新进度
    if progress is not None:
        session["progress"] = progress
    else:
        # 自动计算进度
        session["progress"] = int(len(session["completed_agents"]) / session["total_agents"] * 100)
    
    # 更新当前阶段
    if current_stage is not None:
        session["current_stage"] = current_stage
    
    print(f"[会话更新] {session_id} - {agent_id}: {status} ({session['progress']}%)")
    
    return {"message": "更新成功", "progress": session["progress"]}


@router.post("/session/{session_id}/complete")
async def complete_session(session_id: str, success: bool = True, error: Optional[str] = None):
    """
    标记会话完成
    """
    session = analysis_sessions.get(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    session["status"] = "completed" if success else "error"
    session["progress"] = 100 if success else session["progress"]
    session["error_message"] = error
    
    print(f"[会话完成] {session_id} - {'成功' if success else '失败'}")
    
    return {"message": "会话已完成", "status": session["status"]}


@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """
    删除会话
    """
    if session_id in analysis_sessions:
        del analysis_sessions[session_id]
        print(f"[会话删除] {session_id}")
        return {"message": "会话已删除"}
    
    raise HTTPException(status_code=404, detail="会话不存在")


@router.get("/sessions/active")
async def get_active_sessions():
    """
    获取所有活跃会话（调试用）
    """
    clean_expired_sessions()
    
    return {
        "total": len(analysis_sessions),
        "sessions": [
            {
                "session_id": sid,
                "stock_code": s["stock_code"],
                "status": s["status"],
                "progress": s["progress"],
                "elapsed": int(time.time() - s["start_time"])
            }
            for sid, s in analysis_sessions.items()
        ]
    }
