"""
市场数据API
提供盘口信息、热点板块、成交排行、涨跌榜等实时市场数据
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
import akshare as ak

from backend.utils.logging_config import get_logger

logger = get_logger("api.market_data")
router = APIRouter(prefix="/api/market", tags=["Market Data"])


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

        # 整理为结构化格式
        result = {
            "code": code,
            "asks": [
                {"price": data.get('sell_5', 0), "volume": int(data.get('sell_5_vol', 0))},
                {"price": data.get('sell_4', 0), "volume": int(data.get('sell_4_vol', 0))},
                {"price": data.get('sell_3', 0), "volume": int(data.get('sell_3_vol', 0))},
                {"price": data.get('sell_2', 0), "volume": int(data.get('sell_2_vol', 0))},
                {"price": data.get('sell_1', 0), "volume": int(data.get('sell_1_vol', 0))},
            ],
            "bids": [
                {"price": data.get('buy_1', 0), "volume": int(data.get('buy_1_vol', 0))},
                {"price": data.get('buy_2', 0), "volume": int(data.get('buy_2_vol', 0))},
                {"price": data.get('buy_3', 0), "volume": int(data.get('buy_3_vol', 0))},
                {"price": data.get('buy_4', 0), "volume": int(data.get('buy_4_vol', 0))},
                {"price": data.get('buy_5', 0), "volume": int(data.get('buy_5_vol', 0))},
            ],
            "latest": data.get('最新', 0),
            "avg_price": data.get('均价', 0),
            "change_pct": data.get('涨幅', 0),
            "change": data.get('涨跌', 0),
            "volume": int(data.get('总手', 0)),
            "amount": data.get('金额', 0),
            "turnover": data.get('换手', 0),
            "volume_ratio": data.get('量比', 0),
            "high": data.get('最高', 0),
            "low": data.get('最低', 0),
            "open": data.get('今开', 0),
            "pre_close": data.get('昨收', 0),
            "limit_up": data.get('涨停', 0),
            "limit_down": data.get('跌停', 0),
            "outer_vol": int(data.get('外盘', 0)),
            "inner_vol": int(data.get('内盘', 0)),
        }

        logger.info(f"[盘口信息] {code} 获取成功")
        return result

    except Exception as e:
        logger.error(f"[盘口信息] {code} 错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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

        if sector_type == "concept":
            df = ak.stock_board_concept_cons_em(symbol=sector_name)
        else:
            df = ak.stock_board_industry_cons_em(symbol=sector_name)

        if df is None or df.empty:
            return {"stocks": [], "sector_name": sector_name, "message": "暂无数据"}

        # 按涨跌幅排序
        df = df.sort_values(by='涨跌幅', ascending=False)

        # 取前N个
        df = df.head(limit)

        # 转换为列表
        stocks = []
        for _, row in df.iterrows():
            stocks.append({
                "code": row.get('代码', ''),
                "name": row.get('名称', ''),
                "price": row.get('最新价', 0),
                "change_pct": row.get('涨跌幅', 0),
                "change": row.get('涨跌额', 0),
                "volume": row.get('成交量', 0),
                "amount": row.get('成交额', 0),
                "amplitude": row.get('振幅', 0),
                "high": row.get('最高', 0),
                "low": row.get('最低', 0),
                "open": row.get('今开', 0),
                "pre_close": row.get('昨收', 0),
                "turnover": row.get('换手率', 0),
                "pe": row.get('市盈率-动态', 0),
                "pb": row.get('市净率', 0),
            })

        logger.info(f"[板块成分股] {sector_name} 获取到 {len(stocks)} 只股票")
        return {"stocks": stocks, "sector_name": sector_name, "sector_type": sector_type}

    except Exception as e:
        logger.error(f"[板块成分股] {sector_name} 错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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

        # 获取全市场行情
        df = ak.stock_zh_a_spot_em()

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

        # 获取全市场行情
        df = ak.stock_zh_a_spot_em()

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

        # 获取全市场行情
        df = ak.stock_zh_a_spot_em()

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

        # 获取全市场行情
        df = ak.stock_zh_a_spot_em()

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
