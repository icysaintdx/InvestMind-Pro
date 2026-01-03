"""
数据源调度器API - 提供前端配置接口

功能：
1. 获取/更新数据源配置
2. 获取健康状态
3. 测试数据源连接
4. 管理缓存设置
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import time
import asyncio
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/datasource", tags=["数据源调度"])


# 延迟导入避免循环依赖
def get_scheduler():
    from backend.services.data_source_scheduler import DataSourceScheduler
    return DataSourceScheduler()


# ============ 请求/响应模型 ============

class SourceConfigUpdate(BaseModel):
    enabled: Optional[bool] = None
    priority: Optional[int] = None
    timeout: Optional[int] = None


class CategoryConfigUpdate(BaseModel):
    primary: Optional[str] = None
    cache_ttl: Optional[int] = None
    cache_level: Optional[str] = None


class TestRequest(BaseModel):
    source: str
    category: Optional[str] = None
    test_params: Optional[Dict] = None


class TestCategoryRequest(BaseModel):
    category: str
    test_params: Optional[Dict] = None


# ============ 配置管理 ============

@router.get("/config")
async def get_config():
    """获取完整配置"""
    try:
        scheduler = get_scheduler()
        return {
            "success": True,
            "data": scheduler.get_config()
        }
    except Exception as e:
        logger.error(f"Failed to get config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/config/source/{source}")
async def update_source_config(source: str, config: SourceConfigUpdate):
    """更新数据源配置"""
    try:
        scheduler = get_scheduler()
        updates = {k: v for k, v in config.dict().items() if v is not None}
        if not updates:
            return {"success": False, "message": "No updates provided"}

        success = scheduler.update_config({
            "data_sources": {source: updates}
        })
        return {"success": success}
    except Exception as e:
        logger.error(f"Failed to update source config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/config/category/{category}")
async def update_category_config(category: str, config: CategoryConfigUpdate):
    """更新数据类别配置"""
    try:
        scheduler = get_scheduler()
        updates = {k: v for k, v in config.dict().items() if v is not None}
        if not updates:
            return {"success": False, "message": "No updates provided"}

        success = scheduler.update_config({
            "data_categories": {category: updates}
        })
        return {"success": success}
    except Exception as e:
        logger.error(f"Failed to update category config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/source/{source}/enable")
async def enable_source(source: str):
    """启用数据源"""
    try:
        scheduler = get_scheduler()
        success = scheduler.set_source_enabled(source, True)
        return {"success": success}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/source/{source}/disable")
async def disable_source(source: str):
    """禁用数据源"""
    try:
        scheduler = get_scheduler()
        success = scheduler.set_source_enabled(source, False)
        return {"success": success}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ 健康状态 ============

@router.get("/health")
async def get_health_status():
    """获取所有数据源健康状态"""
    try:
        scheduler = get_scheduler()
        return {
            "success": True,
            "data": scheduler.get_health_status()
        }
    except Exception as e:
        logger.error(f"Failed to get health status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories")
async def get_category_status():
    """获取所有数据类别状态"""
    try:
        scheduler = get_scheduler()
        return {
            "success": True,
            "data": scheduler.get_category_status()
        }
    except Exception as e:
        logger.error(f"Failed to get category status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/best-source/{category}")
async def get_best_source(category: str):
    """获取指定类别的最优数据源"""
    try:
        scheduler = get_scheduler()
        best = scheduler.get_best_source(category)
        fallbacks = scheduler.get_fallback_sources(category, exclude=best)
        return {
            "success": True,
            "data": {
                "category": category,
                "best_source": best,
                "fallback_sources": fallbacks
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ 测试功能 ============

@router.post("/test")
async def test_source(request: TestRequest):
    """测试单个数据源"""
    try:
        result = await _test_single_source(request.source, request.category, request.test_params)
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        logger.error(f"Test failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@router.post("/test-category")
async def test_category(request: TestCategoryRequest):
    """测试指定类别的所有数据源"""
    try:
        scheduler = get_scheduler()
        config = scheduler.get_config()
        cat_config = config.get("data_categories", {}).get(request.category, {})
        sources = cat_config.get("sources", [])

        if not sources:
            return {
                "success": False,
                "error": f"Category '{request.category}' not found or has no sources"
            }

        # 并行测试所有数据源
        tasks = [
            _test_single_source(source, request.category, request.test_params)
            for source in sources
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 整理结果
        test_results = []
        for source, result in zip(sources, results):
            if isinstance(result, Exception):
                test_results.append({
                    "source": source,
                    "success": False,
                    "error": str(result)
                })
            else:
                test_results.append(result)

        # 按响应时间排序
        test_results.sort(key=lambda x: x.get("response_time_ms", float('inf')))

        return {
            "success": True,
            "category": request.category,
            "results": test_results,
            "recommendation": test_results[0]["source"] if test_results and test_results[0].get("success") else None
        }
    except Exception as e:
        logger.error(f"Category test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test-all")
async def test_all_sources():
    """测试所有数据源的基本连接"""
    try:
        scheduler = get_scheduler()
        config = scheduler.get_config()
        sources = list(config.get("data_sources", {}).keys())

        results = {}
        for source in sources:
            try:
                result = await _test_single_source(source, None, None)
                results[source] = result
            except Exception as e:
                results[source] = {
                    "source": source,
                    "success": False,
                    "error": str(e)
                }

        return {
            "success": True,
            "data": results
        }
    except Exception as e:
        logger.error(f"Test all failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _test_single_source(source: str, category: str = None, params: Dict = None) -> Dict:
    """测试单个数据源"""
    start_time = time.time()
    scheduler = get_scheduler()

    try:
        if source == "tdx":
            result = await _test_tdx()
        elif source == "tushare":
            result = await _test_tushare()
        elif source == "akshare":
            result = await _test_akshare(category)
        elif source == "cninfo":
            result = await _test_cninfo()
        elif source == "eastmoney":
            result = await _test_eastmoney()
        elif source == "sina":
            result = await _test_sina()
        elif source == "juhe":
            result = await _test_juhe()
        else:
            result = {"success": False, "error": f"Unknown source: {source}"}

        response_time = (time.time() - start_time) * 1000

        # 记录测试结果
        scheduler.record_request(
            source=source,
            category=category or "test",
            interface="connection_test",
            response_time_ms=response_time,
            success=result.get("success", False),
            error_message=result.get("error")
        )

        return {
            "source": source,
            "success": result.get("success", False),
            "response_time_ms": round(response_time, 2),
            "data_count": result.get("data_count", 0),
            "message": result.get("message", ""),
            "error": result.get("error")
        }
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        scheduler.record_request(
            source=source,
            category=category or "test",
            interface="connection_test",
            response_time_ms=response_time,
            success=False,
            error_message=str(e)
        )
        return {
            "source": source,
            "success": False,
            "response_time_ms": round(response_time, 2),
            "error": str(e)
        }


async def _test_tdx() -> Dict:
    """测试TDX连接"""
    try:
        # 优先测试 TDX Native Provider（直接连接通达信服务器）
        from backend.dataflows.providers.tdx_native_provider import get_tdx_native_provider
        provider = get_tdx_native_provider()

        if provider.is_available():
            # 尝试获取一只股票的实时行情来测试连接
            quote = provider.get_realtime_quote("600519")  # 贵州茅台

            if quote:
                # 非交易时间 price 可能为 0，但只要有数据返回就说明连接正常
                price = quote.get('price', 0)
                pre_close = quote.get('pre_close', 0)
                name = quote.get('name', '600519')

                # 如果有价格或昨收价，说明连接正常
                if price > 0 or pre_close > 0:
                    display_price = price if price > 0 else pre_close
                    return {
                        "success": True,
                        "data_count": 1,
                        "message": f"TDX连接正常: {name} @ {display_price}" + (" (非交易时间)" if price == 0 else "")
                    }
                else:
                    # 有数据但价格都是0，可能是无效股票代码
                    return {
                        "success": True,
                        "data_count": 1,
                        "message": f"TDX连接正常，但返回数据为空（可能是非交易时间）"
                    }
            else:
                # 尝试获取K线数据作为备选测试
                kline = provider.get_kline("600519", 9, 5)  # 获取5条日K线
                if kline and len(kline) > 0:
                    return {
                        "success": True,
                        "data_count": len(kline),
                        "message": f"TDX连接正常（通过K线验证），获取{len(kline)}条历史数据"
                    }
                else:
                    return {
                        "success": False,
                        "error": "TDX返回数据为空（实时行情和K线都无数据）"
                    }
        else:
            return {
                "success": False,
                "error": "TDX Native Provider不可用（无法连接通达信服务器）"
            }
    except ImportError as e:
        return {"success": False, "error": f"TDX模块未安装: {e}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def _test_tushare() -> Dict:
    """测试Tushare连接"""
    try:
        import tushare as ts
        import os
        token = os.getenv("TUSHARE_TOKEN")
        if not token:
            return {"success": False, "error": "TUSHARE_TOKEN not configured"}

        pro = ts.pro_api(token)
        # 简单测试：获取交易日历
        df = pro.trade_cal(exchange='SSE', start_date='20260101', end_date='20260101')
        return {
            "success": True,
            "data_count": len(df) if df is not None else 0,
            "message": "Tushare connection OK"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


async def _test_akshare(category: str = None) -> Dict:
    """测试AKShare连接"""
    try:
        import akshare as ak
        # 简单测试：获取交易日历
        df = ak.tool_trade_date_hist_sina()
        return {
            "success": True,
            "data_count": len(df) if df is not None else 0,
            "message": "AKShare connection OK"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


async def _test_cninfo() -> Dict:
    """测试巨潮连接"""
    try:
        import requests
        # 测试免费接口
        url = "http://webapi.cninfo.com.cn/api/info/p_info3005"
        response = requests.get(url, params={"format": "json"}, timeout=10)
        if response.status_code == 200:
            data = response.json()
            records = data.get("records", [])
            return {
                "success": True,
                "data_count": len(records),
                "message": "CNInfo connection OK"
            }
        else:
            return {
                "success": False,
                "error": f"HTTP {response.status_code}"
            }
    except Exception as e:
        return {"success": False, "error": str(e)}


async def _test_eastmoney() -> Dict:
    """测试东方财富连接"""
    try:
        import akshare as ak
        # 通过AKShare测试东财接口
        df = ak.stock_info_global_em()
        return {
            "success": True,
            "data_count": len(df) if df is not None else 0,
            "message": "EastMoney (via AKShare) connection OK"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


async def _test_sina() -> Dict:
    """测试新浪财经连接"""
    try:
        import requests

        # 测试获取贵州茅台实时行情
        url = "https://hq.sinajs.cn/list=sh600519"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://finance.sina.com.cn'
        }

        resp = requests.get(url, headers=headers, timeout=5)
        if resp.status_code == 200 and 'hq_str_sh600519' in resp.text:
            return {
                "success": True,
                "data_count": 1,
                "message": "Sina Finance connection OK"
            }
        else:
            return {
                "success": False,
                "error": f"HTTP {resp.status_code} or invalid response"
            }
    except Exception as e:
        return {"success": False, "error": str(e)}


async def _test_juhe() -> Dict:
    """测试聚合数据连接"""
    try:
        import requests
        import os

        api_key = os.getenv("JUHE_API_KEY")
        if not api_key:
            return {"success": False, "error": "JUHE_API_KEY not configured"}

        # 测试获取贵州茅台实时行情
        url = "http://web.juhe.cn/finance/stock/hs"
        params = {
            'key': api_key,
            'gid': 'sh600519',
            'type': ''
        }

        resp = requests.get(url, params=params, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            if data.get('error_code') == 0:
                return {
                    "success": True,
                    "data_count": 1,
                    "message": "Juhe Data connection OK"
                }
            else:
                return {
                    "success": False,
                    "error": data.get('reason', 'Unknown error')
                }
        else:
            return {
                "success": False,
                "error": f"HTTP {resp.status_code}"
            }
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============ 缓存管理 ============

@router.get("/cache/stats")
async def get_cache_stats():
    """获取缓存统计"""
    try:
        # TODO: 实现缓存统计
        return {
            "success": True,
            "data": {
                "memory": {"size_mb": 0, "items": 0},
                "file": {"size_mb": 0, "files": 0},
                "database": {"size_mb": 0, "records": 0}
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cache/clear")
async def clear_cache(category: str = None, level: str = None):
    """清除缓存"""
    try:
        # TODO: 实现缓存清除
        return {
            "success": True,
            "message": f"Cache cleared: category={category}, level={level}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ 指标管理 ============

@router.post("/metrics/reset")
async def reset_metrics(source: str = None):
    """重置指标"""
    try:
        scheduler = get_scheduler()
        scheduler.reset_metrics(source)
        return {
            "success": True,
            "message": f"Metrics reset for: {source or 'all sources'}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
