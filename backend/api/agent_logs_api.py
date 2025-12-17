"""
智能体实时日志流 API
使用 SSE (Server-Sent Events) 推送日志到前端
"""
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import asyncio
import json
from datetime import datetime
from typing import Dict, Optional
import logging

router = APIRouter(prefix="/api/agent-logs", tags=["Agent Logs"])

# 全局日志队列（每个智能体一个队列）
agent_log_queues: Dict[str, asyncio.Queue] = {}

# 日志队列锁
queue_lock = asyncio.Lock()

logger = logging.getLogger(__name__)


async def log_stream(agent_id: str):
    """SSE 日志流生成器"""
    # 创建该智能体的日志队列
    async with queue_lock:
        if agent_id not in agent_log_queues:
            agent_log_queues[agent_id] = asyncio.Queue()
    
    queue = agent_log_queues[agent_id]
    
    try:
        logger.info(f"[SSE] 客户端连接: {agent_id}")
        
        # 发送连接成功消息
        yield f"data: {json.dumps({'type': 'connected', 'message': '日志流已连接'})}\n\n"
        
        while True:
            try:
                # 等待新日志（超时30秒发送心跳）
                log_entry = await asyncio.wait_for(queue.get(), timeout=30.0)
                
                # 如果收到结束信号，退出
                if log_entry == "STREAM_END":
                    logger.info(f"[SSE] 日志流结束: {agent_id}")
                    yield f"data: {json.dumps({'type': 'end', 'message': '日志流已结束'})}\n\n"
                    break
                
                # 发送日志到前端
                yield f"data: {json.dumps(log_entry)}\n\n"
                
            except asyncio.TimeoutError:
                # 发送心跳，保持连接
                yield f": heartbeat\n\n"
                
    except asyncio.CancelledError:
        logger.info(f"[SSE] 客户端断开连接: {agent_id}")
    except Exception as e:
        logger.error(f"[SSE] 日志流错误: {agent_id}, {str(e)}")
    finally:
        # ✅ 修复：不删除队列，只清空它，让后端可以继续执行
        async with queue_lock:
            if agent_id in agent_log_queues:
                # 清空队列但不删除
                while not agent_log_queues[agent_id].empty():
                    try:
                        agent_log_queues[agent_id].get_nowait()
                    except:
                        break
                logger.info(f"[SSE] 清空队列（保留）: {agent_id}")


@router.get("/stream/{agent_id}")
async def stream_agent_logs(agent_id: str):
    """
    SSE 端点：实时推送智能体日志
    
    Args:
        agent_id: 智能体ID（如 news_analyst, fund_flow, etc.）
    
    Returns:
        StreamingResponse: SSE 流
    """
    return StreamingResponse(
        log_stream(agent_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # 禁用 Nginx 缓冲
            "Access-Control-Allow-Origin": "*",  # CORS
        }
    )


def push_agent_log(agent_id: str, log_type: str, message: str, metadata: Optional[Dict] = None):
    """
    推送日志到指定智能体的队列
    
    Args:
        agent_id: 智能体ID
        log_type: 日志类型 ("info", "success", "error", "progress", "warning")
        message: 日志消息
        metadata: 额外元数据（可选）
    """
    # 如果队列不存在，创建它
    if agent_id not in agent_log_queues:
        agent_log_queues[agent_id] = asyncio.Queue(maxsize=100)  # ✅ 限制队列大小
        logger.info(f"[SSE] 创建日志队列: {agent_id}")
    
    log_entry = {
        "type": log_type,
        "message": message,
        "timestamp": datetime.now().isoformat(),
        "metadata": metadata or {}
    }
    try:
        agent_log_queues[agent_id].put_nowait(log_entry)
    except asyncio.QueueFull:
        # ✅ 队列满了，丢弃最旧的日志
        try:
            agent_log_queues[agent_id].get_nowait()
            agent_log_queues[agent_id].put_nowait(log_entry)
        except:
            pass  # 静默失败，不阻塞后端执行
    except Exception as e:
        # ✅ 任何错误都不应该阻塞后端执行
        logger.warning(f"[SSE] 推送日志失败（忽略）: {agent_id}, {str(e)}")


def end_agent_log_stream(agent_id: str):
    """
    结束指定智能体的日志流
    
    Args:
        agent_id: 智能体ID
    """
    if agent_id in agent_log_queues:
        try:
            agent_log_queues[agent_id].put_nowait("STREAM_END")
            logger.info(f"[SSE] 发送结束信号: {agent_id}")
        except Exception as e:
            logger.error(f"[SSE] 发送结束信号失败: {agent_id}, {str(e)}")


@router.post("/test/{agent_id}")
async def test_push_log(agent_id: str, message: str):
    """
    测试端点：手动推送日志
    
    Args:
        agent_id: 智能体ID
        message: 测试消息
    """
    push_agent_log(agent_id, "info", message)
    return {"success": True, "message": f"日志已推送到 {agent_id}"}


@router.get("/status")
async def get_log_stream_status():
    """
    获取当前所有活跃的日志流状态
    
    Returns:
        Dict: 活跃的日志流列表
    """
    async with queue_lock:
        active_streams = list(agent_log_queues.keys())
    
    return {
        "active_streams": active_streams,
        "count": len(active_streams)
    }
