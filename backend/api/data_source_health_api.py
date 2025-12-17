#!/usr/bin/env python3
"""
数据源健康检查API
提供数据源状态监控和健康检查功能
"""

import asyncio
import time
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.utils.logging_config import get_logger
from backend.dataflows.utils.circuit_breaker import (
    circuit_breaker_registry,
    get_data_source_breaker,
    CircuitState
)

logger = get_logger("data_source_health")

router = APIRouter(prefix="/api/health", tags=["健康检查"])


class DataSourceStatus(BaseModel):
    """数据源状态模型"""
    name: str
    available: bool
    response_time_ms: float
    last_check: str
    error: str = None


class HealthCheckResponse(BaseModel):
    """健康检查响应模型"""
    status: str  # healthy, degraded, unhealthy
    timestamp: str
    data_sources: Dict[str, Any]
    circuit_breakers: Dict[str, Any]
    summary: Dict[str, int]


async def check_akshare_health() -> Dict[str, Any]:
    """检查AKShare数据源健康状态"""
    start_time = time.time()
    try:
        import akshare as ak
        # 使用简单的API测试连接
        df = ak.stock_zh_index_spot_em()
        elapsed = (time.time() - start_time) * 1000
        return {
            "name": "akshare",
            "available": True,
            "response_time_ms": round(elapsed, 2),
            "records": len(df) if df is not None else 0,
            "error": None
        }
    except Exception as e:
        elapsed = (time.time() - start_time) * 1000
        return {
            "name": "akshare",
            "available": False,
            "response_time_ms": round(elapsed, 2),
            "records": 0,
            "error": str(e)[:200]
        }


async def check_sina_health() -> Dict[str, Any]:
    """检查新浪财经数据源健康状态"""
    start_time = time.time()
    try:
        import httpx
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://hq.sinajs.cn/list=sh000001",
                headers={"Referer": "https://finance.sina.com.cn"}
            )
            elapsed = (time.time() - start_time) * 1000
            return {
                "name": "sina",
                "available": response.status_code == 200,
                "response_time_ms": round(elapsed, 2),
                "status_code": response.status_code,
                "error": None if response.status_code == 200 else f"HTTP {response.status_code}"
            }
    except Exception as e:
        elapsed = (time.time() - start_time) * 1000
        return {
            "name": "sina",
            "available": False,
            "response_time_ms": round(elapsed, 2),
            "status_code": 0,
            "error": str(e)[:200]
        }


async def check_tushare_health() -> Dict[str, Any]:
    """检查Tushare数据源健康状态"""
    import os
    start_time = time.time()

    token = os.environ.get("TUSHARE_TOKEN")
    if not token:
        return {
            "name": "tushare",
            "available": False,
            "response_time_ms": 0,
            "error": "TUSHARE_TOKEN not configured"
        }

    try:
        import tushare as ts
        ts.set_token(token)
        pro = ts.pro_api()
        # 使用简单的API测试
        df = pro.trade_cal(exchange='SSE', start_date='20250101', end_date='20250101')
        elapsed = (time.time() - start_time) * 1000
        return {
            "name": "tushare",
            "available": True,
            "response_time_ms": round(elapsed, 2),
            "records": len(df) if df is not None else 0,
            "error": None
        }
    except Exception as e:
        elapsed = (time.time() - start_time) * 1000
        return {
            "name": "tushare",
            "available": False,
            "response_time_ms": round(elapsed, 2),
            "records": 0,
            "error": str(e)[:200]
        }


async def check_baostock_health() -> Dict[str, Any]:
    """检查BaoStock数据源健康状态"""
    start_time = time.time()
    try:
        import baostock as bs
        lg = bs.login()
        if lg.error_code != '0':
            raise Exception(f"Login failed: {lg.error_msg}")

        # 简单查询测试
        rs = bs.query_trade_dates(start_date="2025-01-01", end_date="2025-01-01")
        bs.logout()

        elapsed = (time.time() - start_time) * 1000
        return {
            "name": "baostock",
            "available": True,
            "response_time_ms": round(elapsed, 2),
            "error": None
        }
    except Exception as e:
        elapsed = (time.time() - start_time) * 1000
        return {
            "name": "baostock",
            "available": False,
            "response_time_ms": round(elapsed, 2),
            "error": str(e)[:200]
        }


async def check_juhe_health() -> Dict[str, Any]:
    """检查聚合数据源健康状态"""
    import os
    start_time = time.time()

    api_key = os.environ.get("JUHE_API_KEY")
    if not api_key:
        return {
            "name": "juhe",
            "available": False,
            "response_time_ms": 0,
            "error": "JUHE_API_KEY not configured"
        }

    try:
        import httpx
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"http://web.juhe.cn/finance/stock/hs?gid=sh601006&key={api_key}"
            )
            elapsed = (time.time() - start_time) * 1000
            data = response.json()
            return {
                "name": "juhe",
                "available": data.get("error_code") == 0,
                "response_time_ms": round(elapsed, 2),
                "error": data.get("reason") if data.get("error_code") != 0 else None
            }
    except Exception as e:
        elapsed = (time.time() - start_time) * 1000
        return {
            "name": "juhe",
            "available": False,
            "response_time_ms": round(elapsed, 2),
            "error": str(e)[:200]
        }


@router.get("/data-sources", response_model=HealthCheckResponse)
async def check_data_sources_health():
    """
    检查所有数据源的健康状态

    返回:
    - 各数据源的可用性
    - 响应时间
    - 断路器状态
    - 整体健康状态
    """
    from datetime import datetime

    # 并行检查所有数据源
    results = await asyncio.gather(
        check_akshare_health(),
        check_sina_health(),
        check_tushare_health(),
        check_baostock_health(),
        check_juhe_health(),
        return_exceptions=True
    )

    data_sources = {}
    for result in results:
        if isinstance(result, Exception):
            continue
        if isinstance(result, dict):
            data_sources[result["name"]] = result

    # 获取断路器状态
    circuit_breakers = circuit_breaker_registry.get_all_status()

    # 计算摘要
    available_count = sum(1 for ds in data_sources.values() if ds.get("available"))
    total_count = len(data_sources)

    # 确定整体状态
    if available_count == total_count:
        status = "healthy"
    elif available_count >= total_count // 2:
        status = "degraded"
    else:
        status = "unhealthy"

    return HealthCheckResponse(
        status=status,
        timestamp=datetime.now().isoformat(),
        data_sources=data_sources,
        circuit_breakers=circuit_breakers,
        summary={
            "total": total_count,
            "available": available_count,
            "unavailable": total_count - available_count
        }
    )


@router.get("/data-sources/{source_name}")
async def check_single_data_source(source_name: str):
    """检查单个数据源的健康状态"""
    check_functions = {
        "akshare": check_akshare_health,
        "sina": check_sina_health,
        "tushare": check_tushare_health,
        "baostock": check_baostock_health,
        "juhe": check_juhe_health
    }

    if source_name.lower() not in check_functions:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown data source: {source_name}. Available: {list(check_functions.keys())}"
        )

    result = await check_functions[source_name.lower()]()

    # 更新断路器状态
    breaker = get_data_source_breaker(source_name)
    if result.get("available"):
        breaker.record_success()
    else:
        breaker.record_failure()

    return {
        "data_source": result,
        "circuit_breaker": breaker.get_status()
    }


@router.get("/circuit-breakers")
async def get_circuit_breakers_status():
    """获取所有断路器状态"""
    return {
        "circuit_breakers": circuit_breaker_registry.get_all_status(),
        "summary": {
            "total": len(circuit_breaker_registry._breakers),
            "open": sum(
                1 for b in circuit_breaker_registry._breakers.values()
                if b.state == CircuitState.OPEN
            ),
            "half_open": sum(
                1 for b in circuit_breaker_registry._breakers.values()
                if b.state == CircuitState.HALF_OPEN
            ),
            "closed": sum(
                1 for b in circuit_breaker_registry._breakers.values()
                if b.state == CircuitState.CLOSED
            )
        }
    }


@router.post("/circuit-breakers/reset")
async def reset_circuit_breakers():
    """重置所有断路器"""
    circuit_breaker_registry.reset_all()
    return {"message": "All circuit breakers have been reset", "status": "success"}


@router.post("/circuit-breakers/{source_name}/reset")
async def reset_single_circuit_breaker(source_name: str):
    """重置单个断路器"""
    breaker = get_data_source_breaker(source_name)
    breaker.reset()
    return {
        "message": f"Circuit breaker for {source_name} has been reset",
        "status": breaker.get_status()
    }
