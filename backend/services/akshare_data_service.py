"""
AKShare历史数据服务
封装个股资金流向、龙虎榜、大宗交易、融资融券、涨停/跌停/炸板池等接口
缓存策略：交易时段60s，非交易时段3600s
"""

import asyncio
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd

from utils.logging_config import get_logger

logger = get_logger("services.akshare_data")

# ==================== 线程池 & 缓存 ====================
_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="akdata")

_cache: Dict[str, Dict[str, Any]] = {}
_cache_lock = threading.Lock()

TRADING_TTL = 60       # 交易时段缓存60秒
OFF_HOURS_TTL = 3600   # 非交易时段缓存1小时


def _is_trading_time() -> bool:
    """判断当前是否为A股交易时段"""
    now = datetime.now()
    if now.weekday() >= 5:
        return False
    hm = now.hour * 100 + now.minute
    return 915 <= hm <= 1530


def _get_ttl() -> int:
    return TRADING_TTL if _is_trading_time() else OFF_HOURS_TTL


def _cache_get(key: str) -> Optional[Any]:
    with _cache_lock:
        entry = _cache.get(key)
        if entry and (time.time() - entry["ts"]) < _get_ttl():
            return entry["data"]
        if entry:
            del _cache[key]
    return None


def _cache_set(key: str, data: Any):
    with _cache_lock:
        _cache[key] = {"data": data, "ts": time.time()}


def _df_to_records(df: Optional[pd.DataFrame]) -> List[Dict[str, Any]]:
    """DataFrame转dict列表，处理NaN"""
    if df is None or df.empty:
        return []
    return df.where(df.notna(), None).to_dict(orient="records")


async def _run_ak(func, *args, timeout: int = 15, **kwargs) -> Optional[pd.DataFrame]:
    """在线程池中运行同步akshare调用"""
    loop = asyncio.get_event_loop()
    try:
        return await asyncio.wait_for(
            loop.run_in_executor(_executor, lambda: func(*args, **kwargs)),
            timeout=timeout,
        )
    except asyncio.TimeoutError:
        logger.warning(f"[akshare] {func.__name__} 超时({timeout}s)")
        return None
    except Exception as e:
        logger.warning(f"[akshare] {func.__name__} 失败: {e}")
        return None


def _detect_market(stock_code: str) -> str:
    """根据股票代码判断市场: sh/sz/bj"""
    if stock_code.startswith(("6", "9")):
        return "sh"
    elif stock_code.startswith(("0", "2", "3")):
        return "sz"
    elif stock_code.startswith(("4", "8")):
        return "bj"
    return "sh"


# ==================== 个股资金流向 ====================

async def get_individual_fund_flow(stock_code: str) -> Dict[str, Any]:
    """
    获取个股历史资金流向
    Returns: {"flow": [...], "rank": [...]}
    """
    cache_key = f"fund_flow:{stock_code}"
    cached = _cache_get(cache_key)
    if cached:
        return cached

    import akshare as ak
    market = _detect_market(stock_code)

    flow_df, rank_df = await asyncio.gather(
        _run_ak(ak.stock_individual_fund_flow, stock=stock_code, market=market, timeout=20),
        _run_ak(ak.stock_individual_fund_flow_rank, indicator="今日", timeout=15),
    )

    result = {
        "flow": _df_to_records(flow_df),
        "rank": _df_to_records(rank_df),
    }
    _cache_set(cache_key, result)
    logger.info(f"[资金流向] {stock_code}: flow={len(result['flow'])}条, rank={len(result['rank'])}条")
    return result


# ==================== 龙虎榜历史 ====================

async def get_lhb_history(date: Optional[str] = None, jgzz_period: str = "5") -> Dict[str, Any]:
    """
    获取龙虎榜历史明细
    Args:
        date: 日期 YYYYMMDD，默认最近交易日
        jgzz_period: 机构驻扎周期 "5"/"10"/"30"/"60"
    Returns: {"detail": [...], "jgzz": [...]}
    """
    if not date:
        date = datetime.now().strftime("%Y%m%d")

    cache_key = f"lhb:{date}:{jgzz_period}"
    cached = _cache_get(cache_key)
    if cached:
        return cached

    import akshare as ak

    detail_df, jgzz_df = await asyncio.gather(
        _run_ak(ak.stock_lhb_detail_daily_sina, date=date, timeout=20),
        _run_ak(ak.stock_lhb_jgzz_sina, symbol=jgzz_period, timeout=20),
    )

    result = {
        "detail": _df_to_records(detail_df),
        "jgzz": _df_to_records(jgzz_df),
        "date": date,
    }
    _cache_set(cache_key, result)
    logger.info(f"[龙虎榜] {date}: detail={len(result['detail'])}条, jgzz={len(result['jgzz'])}条")
    return result


# ==================== 大宗交易 ====================

async def get_block_trade(stock_code: Optional[str] = None,
                          start_date: Optional[str] = None,
                          end_date: Optional[str] = None) -> Dict[str, Any]:
    """
    获取大宗交易数据
    Args:
        stock_code: 股票代码（可选，用于过滤明细）
        start_date/end_date: YYYYMMDD
    Returns: {"stats": [...], "detail": [...]}
    """
    if not end_date:
        end_date = datetime.now().strftime("%Y%m%d")
    if not start_date:
        start_date = end_date

    cache_key = f"dzjy:{stock_code or 'all'}:{start_date}:{end_date}"
    cached = _cache_get(cache_key)
    if cached:
        return cached

    import akshare as ak

    stats_df, detail_df = await asyncio.gather(
        _run_ak(ak.stock_dzjy_sctj, timeout=20),
        _run_ak(ak.stock_dzjy_mrmx, symbol="A股", start_date=start_date, end_date=end_date, timeout=20),
    )

    detail_records = _df_to_records(detail_df)

    # 按股票代码过滤
    if stock_code and detail_records:
        detail_records = [r for r in detail_records if str(r.get("证券代码", "")).endswith(stock_code)]

    result = {
        "stats": _df_to_records(stats_df),
        "detail": detail_records,
    }
    _cache_set(cache_key, result)
    logger.info(f"[大宗交易] {stock_code or 'all'}: stats={len(result['stats'])}条, detail={len(result['detail'])}条")
    return result


# ==================== 融资融券 ====================

async def get_margin_detail(stock_code: Optional[str] = None,
                            date: Optional[str] = None) -> Dict[str, Any]:
    """
    获取融资融券明细（合并深交所+上交所）
    Args:
        stock_code: 股票代码（可选，用于过滤）
        date: YYYYMMDD
    Returns: {"szse": [...], "sse": [...], "combined": [...]}
    """
    if not date:
        date = datetime.now().strftime("%Y%m%d")

    cache_key = f"margin:{stock_code or 'all'}:{date}"
    cached = _cache_get(cache_key)
    if cached:
        return cached

    import akshare as ak

    szse_df, sse_df = await asyncio.gather(
        _run_ak(ak.stock_margin_detail_szse, date=date, timeout=20),
        _run_ak(ak.stock_margin_detail_sse, date=date, timeout=20),
    )

    szse_records = _df_to_records(szse_df)
    sse_records = _df_to_records(sse_df)

    # 按股票代码过滤
    if stock_code:
        szse_records = [r for r in szse_records if str(r.get("证券代码", "")).endswith(stock_code)]
        sse_records = [r for r in sse_records
                       if str(r.get("标的证券代码", "")).endswith(stock_code)]

    result = {
        "szse": szse_records,
        "sse": sse_records,
        "combined": szse_records + sse_records,
        "date": date,
    }
    _cache_set(cache_key, result)
    logger.info(f"[融资融券] {stock_code or 'all'} {date}: szse={len(szse_records)}条, sse={len(sse_records)}条")
    return result


# ==================== 涨停板池 ====================

async def get_zt_pool(date: Optional[str] = None) -> Dict[str, Any]:
    """
    获取涨停板池（涨停+强势）
    Returns: {"zt_pool": [...], "strong_pool": [...]}
    """
    if not date:
        date = datetime.now().strftime("%Y%m%d")

    cache_key = f"zt_pool:{date}"
    cached = _cache_get(cache_key)
    if cached:
        return cached

    import akshare as ak

    zt_df, strong_df = await asyncio.gather(
        _run_ak(ak.stock_zt_pool_em, date=date, timeout=20),
        _run_ak(ak.stock_zt_pool_strong_em, date=date, timeout=20),
    )

    result = {
        "zt_pool": _df_to_records(zt_df),
        "strong_pool": _df_to_records(strong_df),
        "date": date,
    }
    _cache_set(cache_key, result)
    logger.info(f"[涨停池] {date}: zt={len(result['zt_pool'])}条, strong={len(result['strong_pool'])}条")
    return result


# ==================== 跌停板池 ====================

async def get_dt_pool(date: Optional[str] = None) -> Dict[str, Any]:
    """
    获取跌停板池
    Returns: {"dt_pool": [...]}
    """
    if not date:
        date = datetime.now().strftime("%Y%m%d")

    cache_key = f"dt_pool:{date}"
    cached = _cache_get(cache_key)
    if cached:
        return cached

    import akshare as ak

    dt_df = await _run_ak(ak.stock_zt_pool_dtgc_em, date=date, timeout=20)

    result = {
        "dt_pool": _df_to_records(dt_df),
        "date": date,
    }
    _cache_set(cache_key, result)
    logger.info(f"[跌停池] {date}: {len(result['dt_pool'])}条")
    return result


# ==================== 炸板池 ====================

async def get_zb_pool(date: Optional[str] = None) -> Dict[str, Any]:
    """
    获取炸板池
    Returns: {"zb_pool": [...]}
    """
    if not date:
        date = datetime.now().strftime("%Y%m%d")

    cache_key = f"zb_pool:{date}"
    cached = _cache_get(cache_key)
    if cached:
        return cached

    import akshare as ak

    zb_df = await _run_ak(ak.stock_zt_pool_zbgc_em, date=date, timeout=20)

    result = {
        "zb_pool": _df_to_records(zb_df),
        "date": date,
    }
    _cache_set(cache_key, result)
    logger.info(f"[炸板池] {date}: {len(result['zb_pool'])}条")
    return result


# ==================== 缓存管理 ====================

def get_cache_stats() -> Dict[str, Any]:
    """获取缓存统计"""
    with _cache_lock:
        now = time.time()
        ttl = _get_ttl()
        active = {k: v for k, v in _cache.items() if (now - v["ts"]) < ttl}
        return {
            "total_entries": len(_cache),
            "active_entries": len(active),
            "ttl_seconds": ttl,
            "is_trading_time": _is_trading_time(),
        }


def clear_cache():
    """清空缓存"""
    with _cache_lock:
        _cache.clear()
    logger.info("[缓存] 已清空所有缓存")
