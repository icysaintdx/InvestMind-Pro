"""
SSE (Server-Sent Events) API 端点
提供实时事件推送功能
"""
import json
import asyncio
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from ..services.async_task.redis_client import redis_client
from ..services.async_task.task_manager import task_manager
from ..services.async_task.log_streamer import log_streamer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sse", tags=["SSE"])


async def event_generator(channel: str, timeout: int = 30):
    """
    SSE 事件生成器

    Args:
        channel: Redis 频道名称
        timeout: 心跳超时时间（秒）
    """
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(channel)

    try:
        # 发送连接成功事件
        yield f"event: connected\ndata: {json.dumps({'channel': channel})}\n\n"

        async for message in pubsub.listen():
            if message["type"] == "message":
                data = message["data"]
                if isinstance(data, bytes):
                    data = data.decode("utf-8")

                try:
                    parsed = json.loads(data)
                    event_type = parsed.get("event", "message")
                    yield f"event: {event_type}\ndata: {data}\n\n"
                except json.JSONDecodeError:
                    yield f"event: message\ndata: {data}\n\n"

            elif message["type"] == "ping":
                # 发送心跳
                yield f"event: ping\ndata: {json.dumps({'timestamp': asyncio.get_event_loop().time()})}\n\n"

    except asyncio.CancelledError:
        logger.info(f"SSE connection cancelled for channel: {channel}")
    except Exception as e:
        logger.error(f"SSE error for channel {channel}: {e}")
        yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
    finally:
        await pubsub.unsubscribe(channel)


@router.get("/task/{task_id}")
async def task_stream(task_id: str):
    """
    任务进度 SSE 流

    订阅指定任务的实时进度更新

    Args:
        task_id: 任务ID

    Returns:
        SSE 事件流
    """
    # 检查任务是否存在
    task_info = await task_manager.get_task_status(task_id)
    if not task_info:
        raise HTTPException(status_code=404, detail="Task not found")

    channel = f"task:{task_id}"

    return StreamingResponse(
        event_generator(channel),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # 禁用 nginx 缓冲
        }
    )


@router.get("/analysis/{session_id}")
async def analysis_stream(session_id: str):
    """
    分析会话 SSE 流

    订阅指定分析会话的实时更新，包括:
    - Agent 状态变化
    - 阶段进度
    - 实时日志

    Args:
        session_id: 分析会话ID

    Returns:
        SSE 事件流
    """
    channel = f"log_stream:{session_id}"

    return StreamingResponse(
        event_generator(channel),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.get("/logs/{session_id}")
async def logs_stream(
    session_id: str,
    level: Optional[str] = Query(None, description="过滤日志级别")
):
    """
    日志 SSE 流

    订阅指定会话的实时日志

    Args:
        session_id: 会话ID
        level: 日志级别过滤（可选）

    Returns:
        SSE 事件流
    """
    channel = f"log_stream:{session_id}"

    async def filtered_generator():
        pubsub = redis_client.pubsub()
        await pubsub.subscribe(channel)

        try:
            yield f"event: connected\ndata: {json.dumps({'session_id': session_id})}\n\n"

            async for message in pubsub.listen():
                if message["type"] == "message":
                    data = message["data"]
                    if isinstance(data, bytes):
                        data = data.decode("utf-8")

                    try:
                        parsed = json.loads(data)
                        # 只推送日志事件
                        if parsed.get("event") == "log":
                            log_data = parsed.get("data", {})
                            # 级别过滤
                            if level is None or log_data.get("level") == level:
                                yield f"event: log\ndata: {json.dumps(log_data)}\n\n"
                    except json.JSONDecodeError:
                        pass

                elif message["type"] == "ping":
                    yield f"event: ping\ndata: {{}}\n\n"

        except asyncio.CancelledError:
            pass
        finally:
            await pubsub.unsubscribe(channel)

    return StreamingResponse(
        filtered_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.get("/multi")
async def multi_stream(
    channels: str = Query(..., description="逗号分隔的频道列表")
):
    """
    多频道 SSE 流

    同时订阅多个频道的事件

    Args:
        channels: 逗号分隔的频道列表

    Returns:
        SSE 事件流
    """
    channel_list = [c.strip() for c in channels.split(",") if c.strip()]

    if not channel_list:
        raise HTTPException(status_code=400, detail="No channels specified")

    async def multi_generator():
        pubsub = redis_client.pubsub()

        for channel in channel_list:
            await pubsub.subscribe(channel)

        try:
            yield f"event: connected\ndata: {json.dumps({'channels': channel_list})}\n\n"

            async for message in pubsub.listen():
                if message["type"] == "message":
                    channel = message.get("channel", "")
                    if isinstance(channel, bytes):
                        channel = channel.decode("utf-8")

                    data = message["data"]
                    if isinstance(data, bytes):
                        data = data.decode("utf-8")

                    yield f"event: message\ndata: {json.dumps({'channel': channel, 'data': data})}\n\n"

                elif message["type"] == "ping":
                    yield f"event: ping\ndata: {{}}\n\n"

        except asyncio.CancelledError:
            pass
        finally:
            for channel in channel_list:
                await pubsub.unsubscribe(channel)

    return StreamingResponse(
        multi_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


# 历史日志查询端点（非 SSE）
@router.get("/logs/{session_id}/history")
async def get_log_history(
    session_id: str,
    start: int = Query(0, ge=0, description="起始位置"),
    count: int = Query(100, ge=1, le=500, description="获取数量"),
    level: Optional[str] = Query(None, description="日志级别过滤")
):
    """
    获取历史日志

    Args:
        session_id: 会话ID
        start: 起始位置
        count: 获取数量
        level: 日志级别过滤

    Returns:
        日志列表
    """
    from ..services.async_task.log_streamer import LogLevel

    level_enum = LogLevel(level) if level else None
    logs = await log_streamer.get_logs(session_id, start, count, level_enum)
    total = await log_streamer.get_log_count(session_id)

    return {
        "success": True,
        "data": {
            "logs": logs,
            "total": total,
            "start": start,
            "count": len(logs)
        }
    }
