"""
市场数据 API 适配器（统一数据中心版）
替换原有的 /api/market/* 接口
非交易时段返回最后一个交易日缓存数据
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import asyncio
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
import akshare as ak

from backend.utils.logging_config import get_logger
from backend.dataflows.unified import (
    Symbol, MarketType, unified_data_service, DataPriority
)

logger = get_logger("api.market_adapter")
router = APIRouter(prefix="/api/market", tags=["市场数据-统一数据中心"])

# ==================== 通用工具 ====================
_executor = ThreadPoolExecutor(max_workers=3, thread_name_prefix="market-ak")
_TRADE_TIMEOUT = 5
_COLD_START_TIMEOUT = 15


def _is_trading_time():
    now = datetime.now()
    if now.weekday() >= 5:
        return False
    hm = now.hour * 100 + now.minute
    return 915 <= hm <= 1530


async def _run_ak(func, *args, timeout=10, **kwargs):
    """在线程池中运行同步akshare调用，带超时"""
    loop = asyncio.get_event_loop()
    try:
        return await asyncio.wait_for(
            loop.run_in_executor(_executor, lambda: func(*args, **kwargs)),
            timeout=timeout
        )
    except asyncio.TimeoutError:
        logger.warning(f"[akshare] {func.__name__} 超时({timeout}s)")
        return None
    except Exception as e:
        logger.warning(f"[akshare] {func.__name__} 失败: {e}")
        return None


# ==================== 缓存 ====================
_overview_cache = None
_sectors_cache = {}
_spot_cache = None          # 全市场行情 DataFrame
_spot_cache_time = None
_bid_ask_cache = {}         # key=code, value=result dict
_tx_cache = {}              # key=code, value=result dict
_spot_prefetch_done = False


def _prefetch_spot_data():
    """服务器启动时后台预加载全市场行情（akshare周末需60-70秒）"""
    import threading
    global _spot_cache, _spot_cache_time, _spot_prefetch_done
    try:
        logger.info("[市场数据] 🚀 后台预加载全市场行情...")
        df = ak.stock_zh_a_spot_em()
        if df is not None and not df.empty:
            _spot_cache = df
            _spot_cache_time = datetime.now()
            logger.info(f"[市场数据] ✅ 预加载完成，{len(df)} 只股票")
        else:
            logger.warning("[市场数据] ⚠️ 预加载返回空数据")
    except Exception as e:
        logger.error(f"[市场数据] ❌ 预加载失败: {e}")
    finally:
        _spot_prefetch_done = True


# 服务器启动时立即开始后台预加载
import threading as _threading
_threading.Thread(target=_prefetch_spot_data, daemon=True, name="spot-prefetch").start()


async def _get_spot_data():
    """获取全市场行情（带缓存，非交易时段复用）"""
    global _spot_cache, _spot_cache_time
    trading = _is_trading_time()

    if _spot_cache is not None:
        if not trading:
            return _spot_cache
        if _spot_cache_time and (datetime.now() - _spot_cache_time).total_seconds() < 30:
            return _spot_cache

    timeout = _TRADE_TIMEOUT if trading else _COLD_START_TIMEOUT
    df = await _run_ak(ak.stock_zh_a_spot_em, timeout=timeout)
    if df is not None and not df.empty:
        _spot_cache = df
        _spot_cache_time = datetime.now()
        return df

    return _spot_cache  # 降级到旧缓存


def _get_price_from_spot(code):
    """从全市场缓存获取个股价格信息"""
    if _spot_cache is not None:
        try:
            row = _spot_cache[_spot_cache['代码'] == code]
            if not row.empty:
                r = row.iloc[0]
                return (float(r.get('最新价', 0) or 0),
                        float(r.get('涨跌额', 0) or 0),
                        float(r.get('涨跌幅', 0) or 0))
        except Exception:
            pass
    return 0, 0, 0


# ==================== 市场概览 ====================
async def _fetch_overview():
    indices = ['000001', '399001', '399006', '000688']
    index_names = {'000001': '上证指数', '399001': '深证成指',
                   '399006': '创业板指', '000688': '科创50'}
    tasks = [unified_data_service.get_tick(Symbol(code=c, market=MarketType.A_SHARE)) for c in indices]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    data = {}
    for i, code in enumerate(indices):
        if isinstance(results[i], Exception) or results[i] is None:
            continue
        tick = results[i]
        data[index_names[code]] = {
            'code': code, 'price': tick.price if tick else 0,
            'change_pct': tick.change_pct if tick else 0, 'volume': tick.volume if tick else 0,
        }
    return data


async def _fetch_overview_akshare():
    """akshare降级：从全市场行情缓存中提取指数数据"""
    index_map = {
        '000001': '上证指数', '399001': '深证成指',
        '399006': '创业板指', '000688': '科创50',
    }
    try:
        df = await _run_ak(ak.stock_zh_index_spot_em, timeout=_COLD_START_TIMEOUT)
        if df is None or df.empty:
            return {}
        data = {}
        for code, name in index_map.items():
            row = df[df['代码'] == code]
            if not row.empty:
                r = row.iloc[0]
                data[name] = {
                    'code': code,
                    'price': float(r.get('最新价', 0) or 0),
                    'change_pct': float(r.get('涨跌幅', 0) or 0),
                    'volume': float(r.get('成交量', 0) or 0),
                }
        return data
    except Exception as e:
        logger.warning(f"[市场概览] akshare降级失败: {e}")
        return {}


@router.get("/overview")
async def get_market_overview():
    global _overview_cache
    trading = _is_trading_time()
    if not trading and _overview_cache is not None:
        return {"success": True, "data": _overview_cache, "source": "cache", "message": "最后交易日数据"}
    timeout = _TRADE_TIMEOUT if trading else _COLD_START_TIMEOUT
    try:
        data = await asyncio.wait_for(_fetch_overview(), timeout=timeout)
        if data:
            _overview_cache = data
            return {"success": True, "data": data, "source": "unified_data_center"}
    except (asyncio.TimeoutError, Exception) as e:
        logger.warning(f"[市场概览] unified异常: {e}")

    # 降级到akshare
    if not _overview_cache:
        try:
            data = await _fetch_overview_akshare()
            if data:
                _overview_cache = data
        except Exception as e:
            logger.warning(f"[市场概览] akshare降级也失败: {e}")

    if _overview_cache:
        return {"success": True, "data": _overview_cache, "source": "cache"}
    return {"success": False, "data": {}, "message": "市场概览数据暂不可用"}


# ==================== 热门板块 ====================
@router.get("/hot-sectors")
async def get_hot_sectors(type: str = Query("industry")):
    global _sectors_cache
    trading = _is_trading_time()
    if not trading and type in _sectors_cache:
        return _sectors_cache[type]
    timeout = _TRADE_TIMEOUT if trading else _COLD_START_TIMEOUT
    try:
        sectors = await asyncio.wait_for(unified_data_service.get_sectors(
            market=MarketType.A_SHARE, sector_type=type, priority=DataPriority.FAST
        ), timeout=timeout)
        sorted_sectors = sorted(sectors, key=lambda x: abs(x.change_pct), reverse=True)
        data = [{'name': s.name, 'code': s.code, 'change_pct': s.change_pct, 'turnover': s.turnover}
                for s in sorted_sectors[:20]]
        result = {"success": True, "sectors": data, "count": len(data), "source": "unified_data_center"}
        _sectors_cache[type] = result
        return result
    except (asyncio.TimeoutError, Exception) as e:
        logger.warning(f"[热门板块] {type} 异常: {e}")
        if type in _sectors_cache:
            return _sectors_cache[type]
        return {"success": False, "sectors": [], "message": str(e)}


# ==================== 排行榜（涨幅/跌幅/成交额）====================
def _build_ranking(df, sort_col, ascending, limit):
    """从全市场行情构建排行榜"""
    if df is None or df.empty:
        return []
    try:
        active = df[df['成交量'] > 0] if '成交量' in df.columns else df
        sorted_df = active.sort_values(by=sort_col, ascending=ascending).head(limit)
        result = []
        for i, (_, row) in enumerate(sorted_df.iterrows(), 1):
            result.append({
                "rank": i,
                "code": str(row.get('代码', '')),
                "name": str(row.get('名称', '')),
                "price": float(row.get('最新价', 0) or 0),
                "change_pct": float(row.get('涨跌幅', 0) or 0),
                "amount": float(row.get('成交额', 0) or 0),
                "volume": float(row.get('成交量', 0) or 0),
            })
        return result
    except Exception as e:
        logger.error(f"[排行榜] 构建失败: {e}")
        return []


@router.get("/top-gainers")
async def get_top_gainers(limit: int = Query(20)):
    df = await _get_spot_data()
    data = _build_ranking(df, '涨跌幅', False, limit)
    return {"success": True, "data": data, "count": len(data), "source": "akshare" if data else "empty"}


@router.get("/top-losers")
async def get_top_losers(limit: int = Query(20)):
    df = await _get_spot_data()
    data = _build_ranking(df, '涨跌幅', True, limit)
    return {"success": True, "data": data, "count": len(data), "source": "akshare" if data else "empty"}


@router.get("/top-amount")
async def get_top_amount(limit: int = Query(20)):
    df = await _get_spot_data()
    data = _build_ranking(df, '成交额', False, limit)
    return {"success": True, "data": data, "count": len(data), "source": "akshare" if data else "empty"}


# ==================== 板块个股 ====================
@router.get("/sector-stocks/{sector_name}")
async def get_sector_stocks(sector_name: str, sector_type: str = Query("industry")):
    """板块成分股 - 使用统一数据中心"""
    cache_key = f"sector_stocks_{sector_name}_{sector_type}"
    cached = _bid_ask_cache.get(cache_key)
    if cached and not _is_trading_time():
        return cached

    try:
        stocks = await asyncio.wait_for(
            unified_data_service.get_sector_stocks(
                sector_name=sector_name,
                sector_type=sector_type,
                priority=DataPriority.FAST
            ),
            timeout=15
        )

        data = []
        for s in stocks:
            data.append({
                "code": s.symbol.code,
                "name": s.name,
                "price": s.price,
                "change_pct": s.change_pct,
                "volume": s.volume,
            })

        result = {
            "success": True,
            "sector": sector_name,
            "data": data,
            "count": len(data),
            "source": "unified_data_center"
        }
        _bid_ask_cache[cache_key] = result
        return result

    except (asyncio.TimeoutError, Exception) as e:
        logger.warning(f"[板块个股] {sector_name} 失败: {e}")
        if cache_key in _bid_ask_cache:
            return _bid_ask_cache[cache_key]
        return {"success": True, "sector": sector_name, "data": [], "count": 0}


# ==================== 盘口数据 ====================
@router.get("/bid-ask/{code}")
async def get_bid_ask(code: str):
    global _bid_ask_cache
    trading = _is_trading_time()

    # 非交易时段有缓存 → 秒回
    if not trading and code in _bid_ask_cache:
        return _bid_ask_cache[code]

    # 先尝试 unified_data_service
    try:
        symbol = Symbol(code=code, market=MarketType.A_SHARE)
        depth = await asyncio.wait_for(unified_data_service.get_depth(symbol), timeout=3)
        if depth and (depth.bids or depth.asks):
            latest, change, change_pct = _get_price_from_spot(code)
            result = {
                "code": code, "latest": latest, "change": change, "change_pct": change_pct,
                "bids": depth.bids[:5] if depth.bids else [],
                "asks": depth.asks[:5] if depth.asks else [],
                "source": "unified_data_center"
            }
            _bid_ask_cache[code] = result
            return result
    except Exception:
        pass

    # 降级到 akshare
    try:
        df = await _run_ak(ak.stock_bid_ask_em, symbol=code, timeout=5)
        if df is not None and not df.empty:
            asks, bids = [], []
            cols = list(df.columns)
            for _, row in df.iterrows():
                try:
                    label = str(row.iloc[0]) if len(cols) > 0 else ''
                    price = float(row.iloc[1]) if len(cols) > 1 and pd.notna(row.iloc[1]) else 0
                    vol = int(row.iloc[2]) if len(cols) > 2 and pd.notna(row.iloc[2]) else 0
                    item = {"price": price, "volume": vol}
                    if '卖' in label:
                        asks.append(item)
                    elif '买' in label:
                        bids.append(item)
                except (IndexError, ValueError, TypeError):
                    continue
            asks.reverse()

            if asks or bids:
                latest, change, change_pct = _get_price_from_spot(code)
                result = {
                    "code": code, "latest": latest, "change": change, "change_pct": change_pct,
                    "asks": asks, "bids": bids, "source": "akshare"
                }
                _bid_ask_cache[code] = result
                return result
    except Exception as e:
        logger.warning(f"[盘口] akshare降级失败 {code}: {e}")

    # 返回缓存
    if code in _bid_ask_cache:
        return _bid_ask_cache[code]

    # 最终降级：从全市场缓存返回基本价格信息（无盘口但有价格）
    latest, change, change_pct = _get_price_from_spot(code)
    if latest > 0:
        return {"code": code, "latest": latest, "change": change, "change_pct": change_pct,
                "asks": [], "bids": [], "source": "spot_cache", "message": "非交易时段，仅显示收盘价"}
    return {"success": False, "data": None, "message": "盘口数据暂不可用（非交易时段）"}


# ==================== 成交明细 ====================
@router.get("/transactions/{code}")
async def get_transactions(code: str, limit: int = Query(50)):
    global _tx_cache
    trading = _is_trading_time()

    if not trading and code in _tx_cache:
        return _tx_cache[code]

    try:
        df = await _run_ak(ak.stock_intraday_em, symbol=code, timeout=15)
        if df is not None and not df.empty:
            records = []
            for _, row in df.tail(limit).iterrows():
                direction_str = str(row.get('买卖盘性质', ''))
                direction_code = 0 if '买' in direction_str else 1  # 0=买 1=卖
                records.append({
                    "time": str(row.get('时间', '')),
                    "price": float(row.get('成交价', 0) or 0),
                    "volume": int(row.get('手数', 0) or 0),
                    "direction_code": direction_code,
                })
            records.reverse()
            # 前端期望 result.transactions
            result = {"transactions": records, "count": len(records), "source": "akshare"}
            _tx_cache[code] = result
            return result
    except Exception as e:
        logger.warning(f"[成交明细] {code} 失败: {e}")

    if code in _tx_cache:
        return _tx_cache[code]
    return {"transactions": [], "message": "成交明细暂不可用（非交易时段）"}
