"""
市场数据API
提供盘口信息、热点板块、成交排行、涨跌榜等实时市场数据
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from datetime import datetime, timedelta
import threading
import pandas as pd
import akshare as ak

from backend.utils.logging_config import get_logger

logger = get_logger("api.market_data")
router = APIRouter(prefix="/api/market", tags=["Market Data"])

# ==================== 全市场行情缓存 ====================
_market_data_cache = None
_market_data_cache_time = None
_market_data_cache_lock = threading.Lock()
_MARKET_DATA_CACHE_DURATION = 30  # 缓存30秒


def _get_market_data_cached():
    """获取全市场行情数据（优先TDX，降级到AKShare，带缓存）"""
    global _market_data_cache, _market_data_cache_time

    with _market_data_cache_lock:
        now = datetime.now()
        # 检查缓存是否有效
        if (_market_data_cache is not None and
            _market_data_cache_time is not None and
            (now - _market_data_cache_time).total_seconds() < _MARKET_DATA_CACHE_DURATION):
            logger.debug("[市场数据] 使用缓存数据")
            return _market_data_cache

        # 缓存过期或不存在，重新获取
        # 优先使用TDX（快得多，约3-5秒 vs AKShare的1分钟）
        df = _get_market_data_from_tdx()
        if df is not None and not df.empty:
            _market_data_cache = df
            _market_data_cache_time = now
            logger.info(f"[市场数据] TDX获取成功，共 {len(df)} 只股票")
            return df

        # 降级到AKShare
        logger.info("[市场数据] 降级到AKShare获取全市场行情...")
        try:
            df = ak.stock_zh_a_spot_em()
            if df is not None and not df.empty:
                _market_data_cache = df
                _market_data_cache_time = now
                logger.info(f"[市场数据] AKShare获取成功，共 {len(df)} 只股票")
                return df
        except Exception as e:
            logger.error(f"[市场数据] AKShare获取失败: {e}")
            # 如果获取失败但有旧缓存，返回旧缓存
            if _market_data_cache is not None:
                logger.warning("[市场数据] 使用过期缓存")
                return _market_data_cache

        return None


def _get_market_data_from_tdx():
    """从TDX获取全市场行情数据"""
    try:
        from backend.dataflows.providers.tdx_native_provider import get_tdx_native_provider
        tdx = get_tdx_native_provider()
        if not tdx or not tdx.is_available():
            return None

        # 获取所有股票代码
        all_stocks = []

        # 深圳市场（A股在前面，从0开始）
        for start in range(0, 6000, 1000):
            stocks = tdx.get_stock_list(0, start)
            if not stocks:
                break
            # 只保留A股（00/30开头）
            for s in stocks:
                code = s.get('code', '')
                if code.startswith(('00', '30')):
                    all_stocks.append(code)
            if len(stocks) < 1000:
                break

        sz_count = len(all_stocks)
        logger.info(f"[市场数据] TDX深圳市场获取到 {sz_count} 只A股")

        # 上海市场（A股在后面，从20000开始）
        # pytdx的上海市场股票列表中，A股（60/68开头）在较后的位置
        for start in range(20000, 30000, 1000):
            stocks = tdx.get_stock_list(1, start)
            if not stocks:
                continue  # 上海市场可能有空洞，继续尝试
            # 只保留A股（60/68开头）
            for s in stocks:
                code = s.get('code', '')
                if code.startswith(('60', '68')):
                    all_stocks.append(code)

        sh_count = len(all_stocks) - sz_count
        logger.info(f"[市场数据] TDX上海市场获取到 {sh_count} 只A股")

        if not all_stocks:
            return None

        logger.info(f"[市场数据] TDX共获取到 {len(all_stocks)} 只A股代码")

        # 批量获取行情（每次最多80只）
        all_quotes = []
        batch_size = 80
        for i in range(0, len(all_stocks), batch_size):
            batch = all_stocks[i:i+batch_size]
            quotes = tdx.get_realtime_quotes(batch)
            if quotes:
                all_quotes.extend(quotes)

        if not all_quotes:
            return None

        # 转换为DataFrame（与AKShare格式兼容）
        data = []
        for q in all_quotes:
            data.append({
                '代码': q.get('code', ''),
                '名称': q.get('name', ''),
                '最新价': q.get('price', 0) or 0,
                '涨跌幅': q.get('change_pct', 0) or 0,
                '涨跌额': q.get('change', 0) or 0,
                '成交量': q.get('volume', 0) or 0,
                '成交额': q.get('amount', 0) or 0,
                '振幅': 0,  # TDX不直接提供
                '最高': q.get('high', 0) or 0,
                '最低': q.get('low', 0) or 0,
                '今开': q.get('open', 0) or 0,
                '昨收': q.get('pre_close', 0) or 0,
                '换手率': 0,  # TDX不直接提供
            })

        df = pd.DataFrame(data)
        logger.info(f"[市场数据] TDX转换完成，共 {len(df)} 条记录")
        return df

    except Exception as e:
        logger.error(f"[市场数据] TDX获取失败: {e}")
        return None


# ==================== 盘口信息 ====================

@router.get("/bid-ask/{code}")
async def get_bid_ask(code: str):
    """
    获取股票五档盘口数据

    Args:
        code: 股票代码（如 000001）

    Returns:
        五档买卖盘口数据
    """
    try:
        logger.info(f"[盘口信息] 获取 {code} 五档盘口")

        # 使用 AKShare 获取五档盘口
        df = ak.stock_bid_ask_em(symbol=code)

        if df is None or df.empty:
            return {"code": code, "bid_ask": [], "message": "暂无数据"}

        # 转换为字典格式
        data = {}
        for _, row in df.iterrows():
            item = row['item']
            value = row['value']
            data[item] = value

        # 安全转换函数 - 处理异常数据（如停牌股、退市股返回的 '---' 等）
        def safe_float(val, default=0):
            if val is None:
                return default
            if isinstance(val, (int, float)):
                return float(val)
            if isinstance(val, str):
                # 去除可能的空格和特殊字符
                val = val.strip().replace(',', '')
                if val == '' or val == '-' or '--' in val:
                    return default
                try:
                    return float(val)
                except ValueError:
                    return default
            return default

        def safe_int(val, default=0):
            return int(safe_float(val, default))

        # 整理为结构化格式
        result = {
            "code": code,
            "asks": [
                {"price": safe_float(data.get('sell_5')), "volume": safe_int(data.get('sell_5_vol'))},
                {"price": safe_float(data.get('sell_4')), "volume": safe_int(data.get('sell_4_vol'))},
                {"price": safe_float(data.get('sell_3')), "volume": safe_int(data.get('sell_3_vol'))},
                {"price": safe_float(data.get('sell_2')), "volume": safe_int(data.get('sell_2_vol'))},
                {"price": safe_float(data.get('sell_1')), "volume": safe_int(data.get('sell_1_vol'))},
            ],
            "bids": [
                {"price": safe_float(data.get('buy_1')), "volume": safe_int(data.get('buy_1_vol'))},
                {"price": safe_float(data.get('buy_2')), "volume": safe_int(data.get('buy_2_vol'))},
                {"price": safe_float(data.get('buy_3')), "volume": safe_int(data.get('buy_3_vol'))},
                {"price": safe_float(data.get('buy_4')), "volume": safe_int(data.get('buy_4_vol'))},
                {"price": safe_float(data.get('buy_5')), "volume": safe_int(data.get('buy_5_vol'))},
            ],
            "latest": safe_float(data.get('最新')),
            "avg_price": safe_float(data.get('均价')),
            "change_pct": safe_float(data.get('涨幅')),
            "change": safe_float(data.get('涨跌')),
            "volume": safe_int(data.get('总手')),
            "amount": safe_float(data.get('金额')),
            "turnover": safe_float(data.get('换手')),
            "volume_ratio": safe_float(data.get('量比')),
            "high": safe_float(data.get('最高')),
            "low": safe_float(data.get('最低')),
            "open": safe_float(data.get('今开')),
            "pre_close": safe_float(data.get('昨收')),
            "limit_up": safe_float(data.get('涨停')),
            "limit_down": safe_float(data.get('跌停')),
            "outer_vol": safe_int(data.get('外盘')),
            "inner_vol": safe_int(data.get('内盘')),
        }

        logger.info(f"[盘口信息] {code} 获取成功")
        return result

    except Exception as e:
        logger.error(f"[盘口信息] {code} 错误: {e}")
        # 返回空数据而不是抛出异常，避免前端报错
        return {"code": code, "asks": [], "bids": [], "message": f"获取失败: {str(e)}"}


# ==================== 热点板块 ====================

@router.get("/hot-sectors")
async def get_hot_sectors(
    sector_type: str = Query(default="industry", description="板块类型: industry(行业), concept(概念)"),
    limit: int = Query(default=20, description="返回数量")
):
    """
    获取热点板块（按涨跌幅排序）

    Args:
        sector_type: 板块类型 - industry(行业板块) 或 concept(概念板块)
        limit: 返回数量

    Returns:
        热点板块列表
    """
    try:
        logger.info(f"[热点板块] 获取 {sector_type} 板块, limit={limit}")

        if sector_type == "concept":
            df = ak.stock_board_concept_name_em()
        else:
            df = ak.stock_board_industry_name_em()

        if df is None or df.empty:
            return {"sectors": [], "message": "暂无数据"}

        # 按涨跌幅排序
        df = df.sort_values(by='涨跌幅', ascending=False)

        # 取前N个
        df = df.head(limit)

        # 转换为列表
        sectors = []
        for _, row in df.iterrows():
            sectors.append({
                "rank": int(row.get('排名', 0)),
                "name": row.get('板块名称', ''),
                "code": row.get('板块代码', ''),
                "price": row.get('最新价', 0),
                "change": row.get('涨跌额', 0),
                "change_pct": row.get('涨跌幅', 0),
                "market_cap": row.get('总市值', 0),
                "turnover": row.get('换手率', 0),
                "rise_count": int(row.get('上涨家数', 0)),
                "fall_count": int(row.get('下跌家数', 0)),
                "leader_stock": row.get('领涨股票', ''),
                "leader_change_pct": row.get('领涨股票-涨跌幅', 0),
            })

        logger.info(f"[热点板块] 获取到 {len(sectors)} 个板块")
        return {"sectors": sectors, "type": sector_type}

    except Exception as e:
        logger.error(f"[热点板块] 错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 板块成分股 ====================

@router.get("/sector-stocks/{sector_name}")
async def get_sector_stocks(
    sector_name: str,
    sector_type: str = Query(default="industry", description="板块类型: industry, concept"),
    limit: int = Query(default=50, description="返回数量")
):
    """
    获取板块成分股

    Args:
        sector_name: 板块名称
        sector_type: 板块类型
        limit: 返回数量

    Returns:
        成分股列表
    """
    try:
        logger.info(f"[板块成分股] 获取 {sector_name} ({sector_type}) 成分股")

        df = None
        try:
            if sector_type == "concept":
                df = ak.stock_board_concept_cons_em(symbol=sector_name)
            else:
                df = ak.stock_board_industry_cons_em(symbol=sector_name)
        except Exception as api_error:
            logger.warning(f"[板块成分股] API调用失败: {api_error}")
            # 尝试另一种板块类型
            try:
                if sector_type == "concept":
                    df = ak.stock_board_industry_cons_em(symbol=sector_name)
                else:
                    df = ak.stock_board_concept_cons_em(symbol=sector_name)
            except Exception:
                pass

        if df is None or df.empty:
            return {"stocks": [], "sector_name": sector_name, "message": "暂无数据或板块不存在"}

        # 按涨跌幅排序
        if '涨跌幅' in df.columns:
            df = df.sort_values(by='涨跌幅', ascending=False)

        # 取前N个
        df = df.head(limit)

        # 转换为列表
        stocks = []
        for _, row in df.iterrows():
            stocks.append({
                "code": str(row.get('代码', '')),
                "name": str(row.get('名称', '')),
                "price": float(row.get('最新价', 0) or 0),
                "change_pct": float(row.get('涨跌幅', 0) or 0),
                "change": float(row.get('涨跌额', 0) or 0),
                "volume": float(row.get('成交量', 0) or 0),
                "amount": float(row.get('成交额', 0) or 0),
                "amplitude": float(row.get('振幅', 0) or 0),
                "high": float(row.get('最高', 0) or 0),
                "low": float(row.get('最低', 0) or 0),
                "open": float(row.get('今开', 0) or 0),
                "pre_close": float(row.get('昨收', 0) or 0),
                "turnover": float(row.get('换手率', 0) or 0),
                "pe": float(row.get('市盈率-动态', 0) or 0),
                "pb": float(row.get('市净率', 0) or 0),
            })

        logger.info(f"[板块成分股] {sector_name} 获取到 {len(stocks)} 只股票")
        return {"stocks": stocks, "sector_name": sector_name, "sector_type": sector_type}

    except Exception as e:
        logger.error(f"[板块成分股] {sector_name} 错误: {e}")
        # 返回空数据而不是抛出异常
        return {"stocks": [], "sector_name": sector_name, "message": f"获取失败: {str(e)}"}


# ==================== 成交额排行 ====================

@router.get("/top-amount")
async def get_top_amount(
    limit: int = Query(default=20, description="返回数量")
):
    """
    获取成交额排行榜

    Args:
        limit: 返回数量

    Returns:
        成交额排行列表
    """
    try:
        logger.info(f"[成交额排行] 获取前 {limit} 名")

        # 使用缓存获取全市场行情
        df = _get_market_data_cached()

        if df is None or df.empty:
            return {"stocks": [], "message": "暂无数据"}

        # 按成交额排序
        df = df.sort_values(by='成交额', ascending=False)

        # 取前N个
        df = df.head(limit)

        # 转换为列表
        stocks = []
        rank = 1
        for _, row in df.iterrows():
            stocks.append({
                "rank": rank,
                "code": row.get('代码', ''),
                "name": row.get('名称', ''),
                "price": row.get('最新价', 0),
                "change_pct": row.get('涨跌幅', 0),
                "amount": row.get('成交额', 0),
                "volume": row.get('成交量', 0),
                "turnover": row.get('换手率', 0),
            })
            rank += 1

        logger.info(f"[成交额排行] 获取到 {len(stocks)} 只股票")
        return {"stocks": stocks}

    except Exception as e:
        logger.error(f"[成交额排行] 错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 成交明细 ====================

@router.get("/transactions/{code}")
async def get_transactions(
    code: str,
    count: int = Query(default=100, description="获取数量")
):
    """
    获取股票成交明细（逐笔成交）

    Args:
        code: 股票代码
        count: 获取数量

    Returns:
        成交明细列表
    """
    try:
        logger.info(f"[成交明细] 获取 {code} 最近 {count} 笔成交")

        # 优先使用 TDX
        try:
            from backend.dataflows.providers.tdx_native_provider import get_tdx_native_provider
            tdx = get_tdx_native_provider()

            if tdx and tdx.is_available():
                data = tdx.get_transaction_data(code, 0, count)
                if data:
                    transactions = []
                    for item in data:
                        # buyorsell: 0=买入 1=卖出 2=中性
                        direction = "买入" if item.get('buyorsell') == 0 else ("卖出" if item.get('buyorsell') == 1 else "中性")
                        transactions.append({
                            "time": item.get('time', ''),
                            "price": item.get('price', 0),
                            "volume": item.get('volume', 0),
                            "amount": item.get('price', 0) * item.get('volume', 0) * 100,  # 金额 = 价格 * 手数 * 100
                            "direction": direction,
                            "direction_code": item.get('buyorsell', 2),
                        })

                    logger.info(f"[成交明细] {code} 获取到 {len(transactions)} 笔成交 (TDX)")
                    return {"code": code, "transactions": transactions, "source": "TDX"}
        except Exception as e:
            logger.warning(f"[成交明细] TDX 获取失败: {e}")

        # TDX 不可用时返回空
        return {"code": code, "transactions": [], "message": "TDX不可用，暂无成交明细数据"}

    except Exception as e:
        logger.error(f"[成交明细] {code} 错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 涨幅排名 ====================

@router.get("/top-gainers")
async def get_top_gainers(
    limit: int = Query(default=20, description="返回数量")
):
    """
    获取今日涨幅排名

    Args:
        limit: 返回数量

    Returns:
        涨幅排名列表
    """
    try:
        logger.info(f"[涨幅排名] 获取前 {limit} 名")

        # 使用缓存获取全市场行情
        df = _get_market_data_cached()

        if df is None or df.empty:
            return {"stocks": [], "message": "暂无数据"}

        # 过滤掉停牌股票（成交量为0）
        df = df[df['成交量'] > 0]

        # 按涨跌幅排序
        df = df.sort_values(by='涨跌幅', ascending=False)

        # 取前N个
        df = df.head(limit)

        # 转换为列表
        stocks = []
        rank = 1
        for _, row in df.iterrows():
            stocks.append({
                "rank": rank,
                "code": row.get('代码', ''),
                "name": row.get('名称', ''),
                "price": row.get('最新价', 0),
                "change_pct": row.get('涨跌幅', 0),
                "change": row.get('涨跌额', 0),
                "amount": row.get('成交额', 0),
                "volume": row.get('成交量', 0),
                "turnover": row.get('换手率', 0),
                "amplitude": row.get('振幅', 0),
            })
            rank += 1

        logger.info(f"[涨幅排名] 获取到 {len(stocks)} 只股票")
        return {"stocks": stocks}

    except Exception as e:
        logger.error(f"[涨幅排名] 错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 跌幅排名 ====================

@router.get("/top-losers")
async def get_top_losers(
    limit: int = Query(default=20, description="返回数量")
):
    """
    获取今日跌幅排名

    Args:
        limit: 返回数量

    Returns:
        跌幅排名列表
    """
    try:
        logger.info(f"[跌幅排名] 获取前 {limit} 名")

        # 使用缓存获取全市场行情
        df = _get_market_data_cached()

        if df is None or df.empty:
            return {"stocks": [], "message": "暂无数据"}

        # 过滤掉停牌股票（成交量为0）
        df = df[df['成交量'] > 0]

        # 按涨跌幅排序（升序，跌幅最大的在前）
        df = df.sort_values(by='涨跌幅', ascending=True)

        # 取前N个
        df = df.head(limit)

        # 转换为列表
        stocks = []
        rank = 1
        for _, row in df.iterrows():
            stocks.append({
                "rank": rank,
                "code": row.get('代码', ''),
                "name": row.get('名称', ''),
                "price": row.get('最新价', 0),
                "change_pct": row.get('涨跌幅', 0),
                "change": row.get('涨跌额', 0),
                "amount": row.get('成交额', 0),
                "volume": row.get('成交量', 0),
                "turnover": row.get('换手率', 0),
                "amplitude": row.get('振幅', 0),
            })
            rank += 1

        logger.info(f"[跌幅排名] 获取到 {len(stocks)} 只股票")
        return {"stocks": stocks}

    except Exception as e:
        logger.error(f"[跌幅排名] 错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 综合市场数据 ====================

@router.get("/overview")
async def get_market_overview():
    """
    获取市场概览数据（一次性获取多个排行榜）

    Returns:
        包含涨幅榜、跌幅榜、成交额榜的综合数据
    """
    try:
        logger.info("[市场概览] 获取综合数据")

        # 使用缓存获取全市场行情
        df = _get_market_data_cached()

        if df is None or df.empty:
            return {"message": "暂无数据"}

        # 过滤掉停牌股票
        df_active = df[df['成交量'] > 0]

        # 涨幅榜
        top_gainers = df_active.nlargest(10, '涨跌幅')
        gainers = []
        for i, (_, row) in enumerate(top_gainers.iterrows(), 1):
            gainers.append({
                "rank": i,
                "code": row.get('代码', ''),
                "name": row.get('名称', ''),
                "price": row.get('最新价', 0),
                "change_pct": row.get('涨跌幅', 0),
            })

        # 跌幅榜
        top_losers = df_active.nsmallest(10, '涨跌幅')
        losers = []
        for i, (_, row) in enumerate(top_losers.iterrows(), 1):
            losers.append({
                "rank": i,
                "code": row.get('代码', ''),
                "name": row.get('名称', ''),
                "price": row.get('最新价', 0),
                "change_pct": row.get('涨跌幅', 0),
            })

        # 成交额榜
        top_amount = df.nlargest(10, '成交额')
        amount_list = []
        for i, (_, row) in enumerate(top_amount.iterrows(), 1):
            amount_list.append({
                "rank": i,
                "code": row.get('代码', ''),
                "name": row.get('名称', ''),
                "price": row.get('最新价', 0),
                "amount": row.get('成交额', 0),
                "change_pct": row.get('涨跌幅', 0),
            })

        # 市场统计
        total_stocks = len(df)
        rise_count = len(df_active[df_active['涨跌幅'] > 0])
        fall_count = len(df_active[df_active['涨跌幅'] < 0])
        flat_count = len(df_active[df_active['涨跌幅'] == 0])
        limit_up = len(df_active[df_active['涨跌幅'] >= 9.9])
        limit_down = len(df_active[df_active['涨跌幅'] <= -9.9])

        result = {
            "top_gainers": gainers,
            "top_losers": losers,
            "top_amount": amount_list,
            "statistics": {
                "total": total_stocks,
                "rise": rise_count,
                "fall": fall_count,
                "flat": flat_count,
                "limit_up": limit_up,
                "limit_down": limit_down,
            }
        }

        logger.info("[市场概览] 获取成功")
        return result

    except Exception as e:
        logger.error(f"[市场概览] 错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))
