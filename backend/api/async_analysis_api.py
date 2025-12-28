"""
异步分析会话 API
支持后台执行分析任务，通过 SSE 实时推送进度
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import time
import uuid
import asyncio
import logging

from ..services.async_task.task_manager import task_manager, TaskStatus
from ..services.async_task.log_streamer import log_streamer, LogLevel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/async-analysis", tags=["Async Analysis"])


class AsyncAnalysisRequest(BaseModel):
    """异步分析请求"""
    stock_code: str
    stock_name: Optional[str] = None
    depth: int = 2  # 分析深度 1-4
    agents: Optional[List[str]] = None  # 指定运行的 Agent，None 表示全部


class AsyncAnalysisResponse(BaseModel):
    """异步分析响应"""
    success: bool
    task_id: str
    session_id: str
    message: str
    sse_url: str  # SSE 订阅地址


class TaskStatusResponse(BaseModel):
    """任务状态响应"""
    task_id: str
    status: str
    progress: int
    message: str
    result: Optional[Dict] = None
    error: Optional[str] = None


# 会话存储（用于存储分析结果）
analysis_results: Dict[str, Dict] = {}


def generate_session_id() -> str:
    """生成会话ID"""
    return f"async_{int(time.time())}_{uuid.uuid4().hex[:8]}"


async def run_analysis_task(task_id: str, payload: Dict, manager) -> Dict:
    """
    执行分析任务的处理器

    这个函数会被 TaskManager 的 worker 调用
    """
    session_id = payload["session_id"]
    stock_code = payload["stock_code"]
    stock_name = payload.get("stock_name", stock_code)
    depth = payload.get("depth", 2)

    try:
        await log_streamer.info(session_id, f"开始分析 {stock_name}({stock_code})")

        # 初始化结果存储
        analysis_results[session_id] = {
            "session_id": session_id,
            "stock_code": stock_code,
            "stock_name": stock_name,
            "status": "running",
            "agents": {},
            "stages": {},
            "start_time": time.time()
        }

        # 定义阶段和 Agent
        stages = {
            1: ["macro_analyst", "industry_analyst", "technical_analyst",
                "funds_analyst", "fundamental_analyst"],
            2: ["fundamental_director", "momentum_director"],
            3: ["systemic_risk_director", "portfolio_risk_director"],
            4: ["investment_gm"]
        }

        total_agents = sum(len(agents) for stage, agents in stages.items() if stage <= depth)
        completed = 0

        # 按阶段执行
        for stage_num in range(1, depth + 1):
            stage_agents = stages.get(stage_num, [])

            await log_streamer.publish_stage_event(session_id, stage_num, "start", {
                "agents": stage_agents
            })
            await log_streamer.info(session_id, f"开始第 {stage_num} 阶段分析")

            # 并行执行同阶段的 Agent
            stage_results = await execute_stage_agents(
                session_id, stage_num, stage_agents,
                stock_code, stock_name, manager, task_id
            )

            # 更新进度
            completed += len(stage_agents)
            progress = int(completed / total_agents * 100)
            await manager.update_progress(task_id, progress, f"第 {stage_num} 阶段完成")

            # 保存阶段结果
            analysis_results[session_id]["stages"][stage_num] = stage_results

            await log_streamer.publish_stage_event(session_id, stage_num, "complete", {
                "results": list(stage_results.keys())
            })
            await log_streamer.info(session_id, f"第 {stage_num} 阶段完成")

        # 分析完成
        analysis_results[session_id]["status"] = "completed"
        analysis_results[session_id]["end_time"] = time.time()

        await log_streamer.info(session_id, f"分析完成")
        await log_streamer.publish_event(session_id, "analysis_complete", {
            "session_id": session_id,
            "duration": time.time() - analysis_results[session_id]["start_time"]
        })

        return {
            "session_id": session_id,
            "status": "completed",
            "agents_count": completed
        }

    except Exception as e:
        logger.exception(f"Analysis task failed: {e}")
        analysis_results[session_id]["status"] = "error"
        analysis_results[session_id]["error"] = str(e)
        await log_streamer.error(session_id, f"分析失败: {str(e)}")
        raise


async def execute_stage_agents(
    session_id: str,
    stage: int,
    agents: List[str],
    stock_code: str,
    stock_name: str,
    manager,
    task_id: str
) -> Dict[str, Any]:
    """
    并行执行同一阶段的所有 Agent
    """
    results = {}

    # 创建并行任务
    tasks = []
    for agent_id in agents:
        task = asyncio.create_task(
            execute_single_agent(session_id, agent_id, stock_code, stock_name)
        )
        tasks.append((agent_id, task))

    # 等待所有任务完成
    for agent_id, task in tasks:
        try:
            result = await task
            results[agent_id] = result
            analysis_results[session_id]["agents"][agent_id] = result
        except Exception as e:
            logger.error(f"Agent {agent_id} failed: {e}")
            results[agent_id] = {"status": "error", "error": str(e)}
            analysis_results[session_id]["agents"][agent_id] = results[agent_id]

    return results


async def execute_single_agent(
    session_id: str,
    agent_id: str,
    stock_code: str,
    stock_name: str
) -> Dict[str, Any]:
    """
    执行单个 Agent
    """
    await log_streamer.publish_agent_event(session_id, agent_id, "start")
    await log_streamer.info(session_id, f"Agent {agent_id} 开始执行", agent_id=agent_id)

    try:
        # 这里调用实际的 Agent 分析逻辑
        # 目前使用模拟实现，后续需要集成真实的 Agent
        result = await simulate_agent_analysis(agent_id, stock_code, stock_name, session_id)

        await log_streamer.publish_agent_event(session_id, agent_id, "complete", {
            "has_output": bool(result.get("output"))
        })
        await log_streamer.info(session_id, f"Agent {agent_id} 执行完成", agent_id=agent_id)

        return {
            "status": "completed",
            "output": result.get("output"),
            "tokens": result.get("tokens", 0),
            "data_sources": result.get("data_sources", []),
            "completed_at": time.time()
        }

    except Exception as e:
        await log_streamer.publish_agent_event(session_id, agent_id, "error", {
            "error": str(e)
        })
        await log_streamer.error(session_id, f"Agent {agent_id} 执行失败: {e}", agent_id=agent_id)
        raise


async def simulate_agent_analysis(
    agent_id: str,
    stock_code: str,
    stock_name: str,
    session_id: str
) -> Dict[str, Any]:
    """
    模拟 Agent 分析（用于测试）

    TODO: 替换为真实的 Agent 调用
    """
    # 模拟不同 Agent 的执行时间
    delay_map = {
        "macro_analyst": 2,
        "industry_analyst": 3,
        "technical_analyst": 2,
        "funds_analyst": 2,
        "fundamental_analyst": 4,
        "fundamental_director": 3,
        "momentum_director": 2,
        "systemic_risk_director": 2,
        "portfolio_risk_director": 2,
        "investment_gm": 5
    }

    delay = delay_map.get(agent_id, 2)

    # 模拟进度更新
    for i in range(delay):
        await asyncio.sleep(1)
        progress = int((i + 1) / delay * 100)
        await log_streamer.debug(
            session_id,
            f"Agent {agent_id} 进度: {progress}%",
            agent_id=agent_id,
            extra={"progress": progress}
        )

    return {
        "output": f"[模拟] {agent_id} 对 {stock_name}({stock_code}) 的分析结果",
        "tokens": delay * 100,
        "data_sources": [{"name": "模拟数据源", "status": "success"}]
    }


# ==================== API 端点 ====================

@router.post("/start", response_model=AsyncAnalysisResponse)
async def start_async_analysis(request: AsyncAnalysisRequest, background_tasks: BackgroundTasks):
    """
    启动异步分析任务

    立即返回 task_id 和 session_id，前端通过 SSE 订阅实时进度
    """
    session_id = generate_session_id()

    # 获取股票名称（如果未提供）
    stock_name = request.stock_name
    if not stock_name or stock_name == request.stock_code:
        try:
            from backend.dataflows.data_source_manager import get_data_source_manager
            manager = get_data_source_manager()
            stock_info = manager.get_stock_info(request.stock_code)
            if stock_info and stock_info.get('name'):
                stock_name = stock_info['name']
                logger.info(f"✅ 获取股票名称成功: {request.stock_code} -> {stock_name}")
        except Exception as e:
            logger.warning(f"⚠️ 获取股票名称失败: {e}")
            stock_name = request.stock_code

    # 注册任务处理器（如果还没注册）
    if "analysis" not in task_manager._handlers:
        task_manager.register_handler("analysis", run_analysis_task)

    # 提交任务
    task_id = await task_manager.submit_task("analysis", {
        "session_id": session_id,
        "stock_code": request.stock_code,
        "stock_name": stock_name,
        "depth": request.depth,
        "agents": request.agents
    })

    # 在后台启动 worker（如果还没启动）
    if not task_manager._running:
        background_tasks.add_task(task_manager.start_workers, 2)

    logger.info(f"Started async analysis: task={task_id}, session={session_id}, stock={stock_name}({request.stock_code})")

    return AsyncAnalysisResponse(
        success=True,
        task_id=task_id,
        session_id=session_id,
        message="分析任务已提交",
        sse_url=f"/api/sse/analysis/{session_id}"
    )


@router.get("/task/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """
    查询任务状态
    """
    status = await task_manager.get_task_status(task_id)

    if not status:
        raise HTTPException(status_code=404, detail="任务不存在")

    return TaskStatusResponse(
        task_id=task_id,
        status=status.status.value if isinstance(status.status, TaskStatus) else status.status,
        progress=status.progress,
        message=status.message,
        result=status.result,
        error=status.error
    )


@router.get("/session/{session_id}/results")
async def get_session_results(session_id: str):
    """
    获取分析会话的完整结果
    """
    if session_id not in analysis_results:
        raise HTTPException(status_code=404, detail="会话不存在")

    return {
        "success": True,
        "data": analysis_results[session_id]
    }


@router.get("/session/{session_id}/agent/{agent_id}")
async def get_agent_result(session_id: str, agent_id: str):
    """
    获取特定 Agent 的结果
    """
    if session_id not in analysis_results:
        raise HTTPException(status_code=404, detail="会话不存在")

    agent_result = analysis_results[session_id].get("agents", {}).get(agent_id)

    if not agent_result:
        return {
            "success": True,
            "data": {"status": "pending", "agent_id": agent_id}
        }

    return {
        "success": True,
        "data": {
            "agent_id": agent_id,
            **agent_result
        }
    }


@router.post("/task/{task_id}/cancel")
async def cancel_task(task_id: str):
    """
    取消任务
    """
    status = await task_manager.get_task_status(task_id)

    if not status:
        raise HTTPException(status_code=404, detail="任务不存在")

    if status.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
        raise HTTPException(status_code=400, detail="任务已结束，无法取消")

    await task_manager.cancel_task(task_id)

    return {"success": True, "message": "任务已取消"}


@router.get("/sessions")
async def list_sessions():
    """
    列出所有分析会话
    """
    return {
        "success": True,
        "data": {
            "total": len(analysis_results),
            "sessions": [
                {
                    "session_id": sid,
                    "stock_code": data.get("stock_code"),
                    "stock_name": data.get("stock_name"),
                    "status": data.get("status"),
                    "agents_count": len(data.get("agents", {}))
                }
                for sid, data in analysis_results.items()
            ]
        }
    }
