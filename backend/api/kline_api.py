"""
K线数据API
提供多种周期的K线数据，支持AKShare、Tushare、新浪、TDX等数据源
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime, timedelta
import pandas as pd

from backend.utils.logging_config import get_logger

logger = get_logger("api.kline")
router = APIRouter(prefix="/api/kline", tags=["K-Line Data"])


# ==================== TDX Provider 辅助函数 ====================

def get_best_tdx_provider():
    """
    获取最佳可用的 TDX Provider
    优先级: TDX Native (纯Python) > TDX HTTP (需要Docker服务)
    """
    # 1. 优先使用 Native Provider
    try:
        from backend.dataflows.providers.tdx_native_provider import get_tdx_native_provider
        provider = get_tdx_native_provider()
        if provider.is_available():
            return provider, 'native'
    except Exception:
        pass

    # 2. 降级到 HTTP Provider
    try:
        from backend.dataflows.providers.tdx_provider import get_tdx_provider
        provider = get_tdx_provider()
        if provider.is_available():
            return provider, 'http'
    except Exception:
        pass

    return None, None


# ==================== 数据获取函数 ====================

def get_kline_from_akshare(symbol: str, period: str, adjust: str = "qfq") -> pd.DataFrame:
    """
    从 AKShare获取K线数据
    
    Args:
        symbol: 股票代码（如：600519）
        period: 周期（1/5/15/30/60/daily）
        adjust: 复权类型（qfq前复权/hfq后复权/空不复权）
    
    Returns:
        K线数据DataFrame
    """
    try:
        import akshare as ak
        
        # 移除前缀，只保留数字
        clean_symbol = symbol.replace('sh', '').replace('sz', '')
        
        # 根据周期选择不同的接口
        if period == 'daily':
            # 日线数据 - 使用东方财富接口
            df = ak.stock_zh_a_hist(
                symbol=clean_symbol,
                period="daily",
                start_date=(datetime.now() - timedelta(days=365)).strftime('%Y%m%d'),
                end_date=datetime.now().strftime('%Y%m%d'),
                adjust=adjust
            )
        elif period in ['1', '5', '15', '30', '60']:
            # 分钟数据 - 使用东方财富接口
            df = ak.stock_zh_a_hist_min_em(
                symbol=clean_symbol,
                period=period,
                adjust=adjust
            )
        else:
            raise ValueError(f"不支持的周期: {period}")
        
        if df is None or df.empty:
            raise ValueError(f"未获取到数据: {symbol}")
        
        # 统一列名
        column_mapping = {
            '日期': 'time',
            '时间': 'time',
            '开盘': 'open',
            '收盘': 'close',
            '最高': 'high',
            '最低': 'low',
            '成交量': 'volume',
            '成交额': 'amount',
            '振幅': 'amplitude',
            '涨跌幅': 'change_pct',
            '涨跌额': 'change',
            '换手率': 'turnover'
        }
        
        # 只重命名存在的列
        rename_dict = {k: v for k, v in column_mapping.items() if k in df.columns}
        df = df.rename(columns=rename_dict)
        
        # 确保必须的列存在
        required_columns = ['time', 'open', 'close', 'high', 'low', 'volume']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"缺少必须的列: {missing_columns}")
        
        return df
        
    except Exception as e:
        logger.error(f"AKShare获取K线失败: {e}", exc_info=True)
        raise


def get_kline_from_sina(symbol: str, period: str) -> pd.DataFrame:
    """
    从新浪获取K线数据
    
    Args:
        symbol: 股票代码
        period: 周期
    
    Returns:
        K线数据DataFrame
    """
    try:
        import akshare as ak
        
        # 新浪接口通过AKShare调用
        if period in ['1', '5', '15', '30', '60']:
            df = ak.stock_zh_a_minute(
                symbol=symbol,
                period=period,
                adjust="qfq"
            )
        else:
            df = ak.stock_zh_a_daily(
                symbol=symbol,
                adjust="qfq"
            )
        
        return df

    except Exception as e:
        logger.error(f"新浪获取K线失败: {e}")
        raise


def get_kline_from_tdx(symbol: str, period: str, limit: int = 200) -> pd.DataFrame:
    """
    从TDX通达信获取K线数据（优先使用Native Provider）

    Args:
        symbol: 股票代码
        period: 周期 (1/5/15/30/60/daily/weekly/monthly)
        limit: 返回条数

    Returns:
        K线数据DataFrame
    """
    # 1. 优先使用 TDX Native Provider
    try:
        from backend.dataflows.providers.tdx_native_provider import get_tdx_native_provider
        provider = get_tdx_native_provider()

        if provider.is_available():
            # 转换周期格式为 pytdx 的 kline_type
            kline_type_mapping = {
                '1': 8,      # 1分钟K线
                '5': 0,      # 5分钟K线
                '15': 1,     # 15分钟K线
                '30': 2,     # 30分钟K线
                '60': 3,     # 60分钟K线
                'daily': 9,  # 日K线
                'weekly': 5, # 周K线
                'monthly': 6 # 月K线
            }
            kline_type = kline_type_mapping.get(period, 9)

            # 获取K线数据
            kline_data = provider.get_kline(symbol, kline_type, limit)

            if kline_data:
                df = pd.DataFrame(kline_data)
                # 统一列名格式
                df = df.rename(columns={
                    'date': 'time',
                    'pre_close': 'preclose'
                })
                logger.info(f"✅ TDX Native获取K线成功: {symbol} {period} {len(df)}条")
                return df
    except Exception as e:
        logger.debug(f"TDX Native获取K线失败: {e}，降级到TDX HTTP")

    # 2. 降级到 TDX HTTP Provider
    try:
        from backend.dataflows.providers.tdx_provider import get_tdx_provider
        provider = get_tdx_provider()

        if not provider.is_available():
            raise ValueError("TDX服务不可用")

        # 转换周期格式
        period_mapping = {
            '1': '1m',
            '5': '5m',
            '15': '15m',
            '30': '30m',
            '60': '60m',
            'daily': 'day',
            'weekly': 'week',
            'monthly': 'month'
        }
        tdx_period = period_mapping.get(period, 'day')

        # 获取K线数据
        df = provider.get_kline(symbol, tdx_period, limit)

        if df is None or df.empty:
            raise ValueError(f"TDX未返回数据: {symbol}")

        # 统一列名格式
        df = df.rename(columns={
            'date': 'time',
            'pre_close': 'preclose'
        })

        return df

    except Exception as e:
        logger.error(f"TDX获取K线失败: {e}")
        raise


# ==================== API端点 ====================

@router.get("/data")
async def get_kline_data(
    symbol: str = Query(..., description="股票代码，如：600519"),
    period: str = Query("daily", description="周期：1/5/15/30/60/daily/weekly/monthly"),
    adjust: str = Query("qfq", description="复权类型：qfq前复权/hfq后复权/空不复权"),
    source: str = Query("auto", description="数据源：auto/tdx/akshare/sina（auto自动选择最优数据源）"),
    limit: int = Query(500, description="返回数据条数")
):
    """
    获取K线数据（支持多数据源自动降级）

    Args:
        symbol: 股票代码
        period: 周期
        adjust: 复权类型
        source: 数据源 (auto/tdx/akshare/sina)，auto模式按优先级自动选择
        limit: 返回条数

    Returns:
        K线数据
    """
    try:
        logger.info(f"获取K线数据: {symbol} {period} {adjust} {source}")

        df = None
        used_source = source

        # 数据源优先级: TDX > AKShare > Sina
        if source == "auto":
            # 自动模式：按优先级尝试各数据源
            data_sources = [
                ("tdx", lambda: get_kline_from_tdx(symbol, period, limit)),
                ("akshare", lambda: get_kline_from_akshare(symbol, period, adjust)),
                ("sina", lambda: get_kline_from_sina(symbol, period))
            ]

            for src_name, src_func in data_sources:
                try:
                    logger.info(f"尝试数据源: {src_name}")
                    df = src_func()
                    if df is not None and not df.empty:
                        used_source = src_name
                        logger.info(f"✅ 数据源 {src_name} 获取成功")
                        break
                except Exception as e:
                    logger.warning(f"⚠️ 数据源 {src_name} 失败: {e}，尝试下一个")
                    continue

            if df is None or df.empty:
                raise ValueError(f"所有数据源都无法获取 {symbol} 的K线数据")
        else:
            # 指定数据源模式
            if source == "tdx":
                df = get_kline_from_tdx(symbol, period, limit)
            elif source == "akshare":
                df = get_kline_from_akshare(symbol, period, adjust)
            elif source == "sina":
                df = get_kline_from_sina(symbol, period)
            else:
                raise ValueError(f"不支持的数据源: {source}")

        # 限制返回数量
        if len(df) > limit:
            df = df.tail(limit)
        
        # 移除不需要的列
        columns_to_drop = ['股票代码', 'stock_code']
        for col in columns_to_drop:
            if col in df.columns:
                df = df.drop(columns=[col])
        
        # 转换为JSON格式
        data = df.to_dict(orient='records')
        
        logger.info(f"成功获取{len(data)}条K线数据")
        
        return {
            "success": True,
            "symbol": symbol,
            "period": period,
            "adjust": adjust,
            "source": used_source,
            "count": len(data),
            "data": data
        }
        
    except Exception as e:
        logger.error(f"获取K线数据失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取K线数据失败: {str(e)}")


@router.get("/realtime")
async def get_realtime_data(
    symbol: str = Query(..., description="股票代码，如：600519"),
    source: str = Query("auto", description="数据源：auto/tdx/akshare（auto自动选择）")
):
    """
    获取实时行情数据（支持多数据源自动降级）

    Args:
        symbol: 股票代码
        source: 数据源 (auto/tdx/akshare)

    Returns:
        实时行情
    """
    try:
        # 处理股票代码格式
        clean_symbol = symbol.replace('sh', '').replace('sz', '')

        data = None
        used_source = source

        if source == "auto":
            # 优先尝试TDX Native Provider
            try:
                from backend.dataflows.providers.tdx_native_provider import get_tdx_native_provider
                provider = get_tdx_native_provider()
                if provider.is_available():
                    quote = provider.get_realtime_quote(clean_symbol)
                    if quote:
                        data = {
                            "symbol": clean_symbol,
                            "name": quote.get('name', ''),
                            "price": quote.get('price', 0),
                            "change": quote.get('change', 0),
                            "change_pct": quote.get('change_pct', 0),
                            "open": quote.get('open', 0),
                            "high": quote.get('high', 0),
                            "low": quote.get('low', 0),
                            "volume": quote.get('volume', 0),
                            "amount": quote.get('amount', 0),
                            "turnover": 0,
                            "pre_close": quote.get('pre_close', 0)
                        }
                        used_source = "tdx_native"
                        logger.info(f"✅ TDX Native实时行情获取成功: {clean_symbol}")
            except Exception as e:
                logger.debug(f"TDX Native实时行情失败: {e}")

            # TDX Native失败，尝试TDX HTTP
            if data is None:
                try:
                    from backend.dataflows.providers.tdx_provider import get_tdx_provider
                    provider = get_tdx_provider()
                    if provider.is_available():
                        quote = provider.get_quote(clean_symbol)
                        if quote:
                            data = {
                                "symbol": clean_symbol,
                                "name": quote.get('name', ''),
                                "price": quote.get('price', 0),
                                "change": quote.get('change', 0),
                                "change_pct": quote.get('change_pct', 0),
                                "open": quote.get('open', 0),
                                "high": quote.get('high', 0),
                                "low": quote.get('low', 0),
                                "volume": quote.get('volume', 0),
                                "amount": quote.get('amount', 0),
                                "turnover": quote.get('turnover', 0),
                                "pre_close": quote.get('pre_close', 0)
                            }
                            used_source = "tdx"
                            logger.info(f"✅ TDX HTTP实时行情获取成功: {clean_symbol}")
                except Exception as e:
                    logger.warning(f"⚠️ TDX HTTP实时行情失败: {e}，降级到AKShare")

            # TDX失败，降级到AKShare
            if data is None:
                data = await _get_realtime_from_akshare(clean_symbol)
                used_source = "akshare"
        elif source == "tdx":
            from backend.dataflows.providers.tdx_provider import get_tdx_provider
            provider = get_tdx_provider()
            if not provider.is_available():
                raise ValueError("TDX服务不可用")
            quote = provider.get_quote(clean_symbol)
            if not quote:
                raise ValueError(f"TDX未返回数据: {clean_symbol}")
            data = {
                "symbol": clean_symbol,
                "name": quote.get('name', ''),
                "price": quote.get('price', 0),
                "change": quote.get('change', 0),
                "change_pct": quote.get('change_pct', 0),
                "open": quote.get('open', 0),
                "high": quote.get('high', 0),
                "low": quote.get('low', 0),
                "volume": quote.get('volume', 0),
                "amount": quote.get('amount', 0),
                "turnover": quote.get('turnover', 0),
                "pre_close": quote.get('pre_close', 0)
            }
        else:
            data = await _get_realtime_from_akshare(clean_symbol)
            used_source = "akshare"

        return {
            "success": True,
            "source": used_source,
            "data": data
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取实时行情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _get_realtime_from_akshare(symbol: str) -> dict:
    """从AKShare获取实时行情（使用单股票API，避免获取全市场数据）"""
    import akshare as ak

    # 使用 stock_bid_ask_em 获取单只股票实时行情（比 stock_zh_a_spot_em 快得多）
    try:
        df = ak.stock_bid_ask_em(symbol=symbol)
        if df is None or df.empty:
            raise HTTPException(status_code=404, detail="股票不存在")

        # 转换为字典
        data = {}
        for _, row in df.iterrows():
            item = row['item']
            value = row['value']
            data[item] = value

        # 安全转换函数
        def safe_float(val, default=0):
            if val is None:
                return default
            if isinstance(val, (int, float)):
                return float(val)
            if isinstance(val, str):
                val = val.strip().replace(',', '')
                if val == '' or val == '-' or '--' in val:
                    return default
                try:
                    return float(val)
                except ValueError:
                    return default
            return default

        return {
            "symbol": symbol,
            "name": "",  # bid_ask_em 不返回名称
            "price": safe_float(data.get('最新')),
            "change": safe_float(data.get('涨跌')),
            "change_pct": safe_float(data.get('涨幅')),
            "open": safe_float(data.get('今开')),
            "high": safe_float(data.get('最高')),
            "low": safe_float(data.get('最低')),
            "volume": safe_float(data.get('总手')),
            "amount": safe_float(data.get('金额')),
            "turnover": safe_float(data.get('换手'))
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取行情失败: {str(e)}")


@router.get("/periods")
async def get_available_periods():
    """
    获取可用的K线周期列表
    
    Returns:
        周期列表
    """
    return {
        "success": True,
        "periods": [
            {"value": "1", "label": "1分钟"},
            {"value": "5", "label": "5分钟"},
            {"value": "15", "label": "15分钟"},
            {"value": "30", "label": "30分钟"},
            {"value": "60", "label": "60分钟"},
            {"value": "daily", "label": "日线"},
            {"value": "weekly", "label": "周线"},
            {"value": "monthly", "label": "月线"}
        ]
    }


@router.get("/test")
async def test_kline_api(symbol: str = "600519"):
    """
    测试K线API
    
    Args:
        symbol: 测试股票代码
    
    Returns:
        测试结果
    """
    try:
        # 测试日线数据
        daily_result = await get_kline_data(
            symbol=symbol,
            period="daily",
            adjust="qfq",
            source="akshare",
            limit=10
        )
        
        # 测试分钟数据
        minute_result = await get_kline_data(
            symbol=symbol,
            period="5",
            adjust="qfq",
            source="akshare",
            limit=10
        )
        
        # 测试实时数据
        realtime_result = await get_realtime_data(symbol=symbol)
        
        return {
            "success": True,
            "message": "测试成功",
            "daily_count": daily_result["count"],
            "minute_count": minute_result["count"],
            "realtime": realtime_result["data"]
        }
        
    except Exception as e:
        logger.error(f"测试失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 分时数据接口 ====================

@router.get("/minute")
async def get_minute_data(
    symbol: str = Query(..., description="股票代码，如：600519"),
    source: str = Query("auto", description="数据源：auto/tdx/akshare（auto自动选择）")
):
    """
    获取分时数据（当日分时走势）

    Args:
        symbol: 股票代码
        source: 数据源 (auto/tdx/akshare)

    Returns:
        分时数据
    """
    try:
        clean_symbol = symbol.replace('sh', '').replace('sz', '')
        data = None
        used_source = source

        if source == "auto":
            # 优先尝试TDX
            try:
                from backend.dataflows.providers.tdx_provider import get_tdx_provider
                provider = get_tdx_provider()
                if provider.is_available():
                    minute_data = provider.get_minute(clean_symbol)
                    if minute_data:
                        data = minute_data
                        used_source = "tdx"
                        logger.info(f"✅ TDX分时数据获取成功: {clean_symbol}")
            except Exception as e:
                logger.warning(f"⚠️ TDX分时数据失败: {e}，降级到AKShare")

            # TDX失败，降级到AKShare
            if data is None:
                data = await _get_minute_from_akshare(clean_symbol)
                used_source = "akshare"
        elif source == "tdx":
            from backend.dataflows.providers.tdx_provider import get_tdx_provider
            provider = get_tdx_provider()
            if not provider.is_available():
                raise ValueError("TDX服务不可用")
            data = provider.get_minute(clean_symbol)
            if not data:
                raise ValueError(f"TDX未返回分时数据: {clean_symbol}")
        else:
            data = await _get_minute_from_akshare(clean_symbol)
            used_source = "akshare"

        return {
            "success": True,
            "symbol": clean_symbol,
            "source": used_source,
            "count": len(data) if isinstance(data, list) else 0,
            "data": data
        }

    except Exception as e:
        logger.error(f"获取分时数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _get_minute_from_akshare(symbol: str) -> list:
    """从AKShare获取分时数据"""
    import akshare as ak

    try:
        df = ak.stock_zh_a_hist_min_em(symbol=symbol, period="1", adjust="")
        if df is None or df.empty:
            return []

        # 转换为列表格式
        result = []
        for _, row in df.iterrows():
            result.append({
                "time": str(row.get('时间', '')),
                "price": row.get('收盘', 0),
                "volume": row.get('成交量', 0),
                "amount": row.get('成交额', 0)
            })
        return result
    except Exception as e:
        logger.error(f"AKShare分时数据获取失败: {e}")
        return []


@router.get("/trade")
async def get_trade_data(
    symbol: str = Query(..., description="股票代码，如：600519"),
    limit: int = Query(100, description="返回条数"),
    source: str = Query("auto", description="数据源：auto/tdx/akshare")
):
    """
    获取逐笔成交数据

    Args:
        symbol: 股票代码
        limit: 返回条数
        source: 数据源

    Returns:
        逐笔成交数据
    """
    try:
        clean_symbol = symbol.replace('sh', '').replace('sz', '')
        data = None
        used_source = source

        if source == "auto" or source == "tdx":
            try:
                from backend.dataflows.providers.tdx_provider import get_tdx_provider
                provider = get_tdx_provider()
                if provider.is_available():
                    trade_data = provider.get_trade(clean_symbol, limit)
                    if trade_data:
                        data = trade_data
                        used_source = "tdx"
                        logger.info(f"✅ TDX逐笔成交获取成功: {clean_symbol}")
            except Exception as e:
                logger.warning(f"⚠️ TDX逐笔成交失败: {e}")

        if data is None:
            # TDX不支持或失败，返回空数据（AKShare没有逐笔成交接口）
            data = []
            used_source = "none"
            logger.warning(f"⚠️ 无可用数据源获取逐笔成交: {clean_symbol}")

        return {
            "success": True,
            "symbol": clean_symbol,
            "source": used_source,
            "count": len(data) if isinstance(data, list) else 0,
            "data": data
        }

    except Exception as e:
        logger.error(f"获取逐笔成交失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 数据源状态接口 ====================

@router.get("/sources")
async def get_data_sources_status():
    """
    获取所有数据源状态

    Returns:
        数据源状态列表
    """
    sources = []

    # 检查TDX
    try:
        from backend.dataflows.providers.tdx_provider import get_tdx_provider
        provider = get_tdx_provider()
        tdx_available = provider.is_available()
        sources.append({
            "name": "tdx",
            "label": "通达信(TDX)",
            "available": tdx_available,
            "priority": 1,
            "description": "本地通达信数据服务，速度最快"
        })
    except Exception as e:
        sources.append({
            "name": "tdx",
            "label": "通达信(TDX)",
            "available": False,
            "priority": 1,
            "error": str(e)
        })

    # 检查AKShare
    try:
        import akshare
        sources.append({
            "name": "akshare",
            "label": "AKShare",
            "available": True,
            "priority": 2,
            "description": "开源金融数据接口，数据全面"
        })
    except ImportError:
        sources.append({
            "name": "akshare",
            "label": "AKShare",
            "available": False,
            "priority": 2,
            "error": "akshare库未安装"
        })

    # 检查新浪
    sources.append({
        "name": "sina",
        "label": "新浪财经",
        "available": True,
        "priority": 3,
        "description": "新浪财经数据接口"
    })

    return {
        "success": True,
        "sources": sources
    }


# ==================== ETF数据接口 ====================

@router.get("/etf/list")
async def get_etf_list(
    source: str = Query("auto", description="数据源：auto/tdx/akshare")
):
    """
    获取ETF列表

    Args:
        source: 数据源

    Returns:
        ETF列表
    """
    try:
        data = None
        used_source = source

        if source == "auto" or source == "tdx":
            try:
                from backend.dataflows.providers.tdx_provider import get_tdx_provider
                provider = get_tdx_provider()
                if provider.is_available():
                    etf_list = provider.get_etf_list()
                    if etf_list:
                        data = etf_list
                        used_source = "tdx"
                        logger.info(f"✅ TDX ETF列表获取成功: {len(etf_list)}只")
            except Exception as e:
                logger.warning(f"⚠️ TDX ETF列表失败: {e}，降级到AKShare")

        if data is None:
            # 降级到AKShare
            data = await _get_etf_list_from_akshare()
            used_source = "akshare"

        return {
            "success": True,
            "source": used_source,
            "count": len(data) if data else 0,
            "data": data
        }

    except Exception as e:
        logger.error(f"获取ETF列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _get_etf_list_from_akshare() -> list:
    """从AKShare获取ETF列表"""
    try:
        import akshare as ak
        df = ak.fund_etf_spot_em()
        if df is None or df.empty:
            return []

        result = []
        for _, row in df.iterrows():
            result.append({
                "code": row.get('代码', ''),
                "name": row.get('名称', ''),
                "price": row.get('最新价', 0),
                "change_pct": row.get('涨跌幅', 0)
            })
        return result
    except Exception as e:
        logger.error(f"AKShare ETF列表获取失败: {e}")
        return []


@router.get("/etf/codes")
async def get_etf_codes(
    source: str = Query("auto", description="数据源：auto/tdx/akshare")
):
    """
    获取ETF代码列表

    Args:
        source: 数据源

    Returns:
        ETF代码列表
    """
    try:
        data = None
        used_source = source

        if source == "auto" or source == "tdx":
            try:
                from backend.dataflows.providers.tdx_provider import get_tdx_provider
                provider = get_tdx_provider()
                if provider.is_available():
                    codes = provider.get_etf_codes()
                    if codes:
                        data = codes
                        used_source = "tdx"
                        logger.info(f"✅ TDX ETF代码获取成功: {len(codes)}个")
            except Exception as e:
                logger.warning(f"⚠️ TDX ETF代码失败: {e}")

        if data is None:
            # 从ETF列表中提取代码
            etf_list = await _get_etf_list_from_akshare()
            data = [item.get('code', '') for item in etf_list if item.get('code')]
            used_source = "akshare"

        return {
            "success": True,
            "source": used_source,
            "count": len(data) if data else 0,
            "data": data
        }

    except Exception as e:
        logger.error(f"获取ETF代码失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 指数数据接口 ====================

@router.get("/index/data")
async def get_index_data(
    symbol: str = Query(..., description="指数代码，如：000001（上证指数）"),
    limit: int = Query(100, description="返回条数"),
    source: str = Query("auto", description="数据源：auto/tdx/akshare")
):
    """
    获取指数数据

    Args:
        symbol: 指数代码
        limit: 返回条数
        source: 数据源

    Returns:
        指数数据
    """
    try:
        data = None
        used_source = source

        if source == "auto" or source == "tdx":
            try:
                from backend.dataflows.providers.tdx_provider import get_tdx_provider
                provider = get_tdx_provider()
                if provider.is_available():
                    index_data = provider.get_index(symbol, limit)
                    if index_data:
                        data = index_data
                        used_source = "tdx"
                        logger.info(f"✅ TDX指数数据获取成功: {symbol}")
            except Exception as e:
                logger.warning(f"⚠️ TDX指数数据失败: {e}，降级到AKShare")

        if data is None:
            # 降级到AKShare
            data = await _get_index_from_akshare(symbol, limit)
            used_source = "akshare"

        return {
            "success": True,
            "symbol": symbol,
            "source": used_source,
            "count": len(data) if isinstance(data, list) else 0,
            "data": data
        }

    except Exception as e:
        logger.error(f"获取指数数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _get_index_from_akshare(symbol: str, limit: int) -> list:
    """从AKShare获取指数数据"""
    try:
        import akshare as ak

        # 获取指数日线数据
        df = ak.stock_zh_index_daily(symbol=f"sh{symbol}")
        if df is None or df.empty:
            return []

        # 限制返回条数
        if len(df) > limit:
            df = df.tail(limit)

        result = []
        for _, row in df.iterrows():
            result.append({
                "date": str(row.get('date', '')),
                "open": row.get('open', 0),
                "high": row.get('high', 0),
                "low": row.get('low', 0),
                "close": row.get('close', 0),
                "volume": row.get('volume', 0)
            })
        return result
    except Exception as e:
        logger.error(f"AKShare指数数据获取失败: {e}")
        return []


# ==================== 交易日查询接口 ====================

@router.get("/workday/check")
async def check_workday(
    date: str = Query(None, description="日期，格式：YYYY-MM-DD，默认今天"),
    source: str = Query("auto", description="数据源：auto/tdx/akshare")
):
    """
    检查指定日期是否为交易日

    Args:
        date: 日期
        source: 数据源

    Returns:
        是否为交易日
    """
    try:
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')

        is_trading_day = None
        used_source = source

        if source == "auto" or source == "tdx":
            try:
                from backend.dataflows.providers.tdx_provider import get_tdx_provider
                provider = get_tdx_provider()
                if provider.is_available():
                    is_trading_day = provider.is_trading_day(date)
                    used_source = "tdx"
                    logger.info(f"✅ TDX交易日检查成功: {date} -> {is_trading_day}")
            except Exception as e:
                logger.warning(f"⚠️ TDX交易日检查失败: {e}")

        if is_trading_day is None:
            # 降级到AKShare
            is_trading_day = await _check_workday_akshare(date)
            used_source = "akshare"

        return {
            "success": True,
            "date": date,
            "is_trading_day": is_trading_day,
            "source": used_source
        }

    except Exception as e:
        logger.error(f"检查交易日失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _check_workday_akshare(date: str) -> bool:
    """使用AKShare检查交易日"""
    try:
        import akshare as ak
        from datetime import datetime

        # 获取交易日历
        df = ak.tool_trade_date_hist_sina()
        if df is None or df.empty:
            return False

        # 转换日期格式
        check_date = datetime.strptime(date, '%Y-%m-%d').strftime('%Y-%m-%d')
        trade_dates = df['trade_date'].astype(str).tolist()

        return check_date in trade_dates
    except Exception as e:
        logger.error(f"AKShare交易日检查失败: {e}")
        return False


@router.get("/workday/range")
async def get_workday_range(
    start_date: str = Query(..., description="开始日期，格式：YYYY-MM-DD"),
    end_date: str = Query(..., description="结束日期，格式：YYYY-MM-DD"),
    source: str = Query("auto", description="数据源：auto/tdx/akshare")
):
    """
    获取日期范围内的交易日列表

    Args:
        start_date: 开始日期
        end_date: 结束日期
        source: 数据源

    Returns:
        交易日列表
    """
    try:
        data = None
        used_source = source

        if source == "auto" or source == "tdx":
            try:
                from backend.dataflows.providers.tdx_provider import get_tdx_provider
                provider = get_tdx_provider()
                if provider.is_available():
                    workdays = provider.get_workday_range(start_date, end_date)
                    if workdays:
                        data = workdays
                        used_source = "tdx"
                        logger.info(f"✅ TDX交易日范围获取成功: {len(workdays)}天")
            except Exception as e:
                logger.warning(f"⚠️ TDX交易日范围失败: {e}")

        if data is None:
            # 降级到AKShare
            data = await _get_workday_range_akshare(start_date, end_date)
            used_source = "akshare"

        return {
            "success": True,
            "start_date": start_date,
            "end_date": end_date,
            "source": used_source,
            "count": len(data) if data else 0,
            "data": data
        }

    except Exception as e:
        logger.error(f"获取交易日范围失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _get_workday_range_akshare(start_date: str, end_date: str) -> list:
    """使用AKShare获取交易日范围"""
    try:
        import akshare as ak
        from datetime import datetime

        # 获取交易日历
        df = ak.tool_trade_date_hist_sina()
        if df is None or df.empty:
            return []

        # 过滤日期范围
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')

        result = []
        for _, row in df.iterrows():
            trade_date = str(row['trade_date'])
            try:
                dt = datetime.strptime(trade_date, '%Y-%m-%d')
                if start_dt <= dt <= end_dt:
                    result.append(trade_date)
            except:
                continue

        return sorted(result)
    except Exception as e:
        logger.error(f"AKShare交易日范围获取失败: {e}")
        return []


@router.get("/workday/next")
async def get_next_workday(
    date: str = Query(None, description="日期，格式：YYYY-MM-DD，默认今天"),
    source: str = Query("auto", description="数据源：auto/tdx")
):
    """
    获取下一个交易日

    Args:
        date: 日期
        source: 数据源

    Returns:
        下一个交易日
    """
    try:
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')

        next_day = None
        used_source = source

        if source == "auto" or source == "tdx":
            try:
                from backend.dataflows.providers.tdx_provider import get_tdx_provider
                provider = get_tdx_provider()
                if provider.is_available():
                    next_day = provider.get_next_trading_day(date)
                    used_source = "tdx"
                    logger.info(f"✅ TDX下一交易日获取成功: {date} -> {next_day}")
            except Exception as e:
                logger.warning(f"⚠️ TDX下一交易日失败: {e}")

        return {
            "success": True,
            "date": date,
            "next_trading_day": next_day,
            "source": used_source
        }

    except Exception as e:
        logger.error(f"获取下一交易日失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workday/prev")
async def get_prev_workday(
    date: str = Query(None, description="日期，格式：YYYY-MM-DD，默认今天"),
    source: str = Query("auto", description="数据源：auto/tdx")
):
    """
    获取上一个交易日

    Args:
        date: 日期
        source: 数据源

    Returns:
        上一个交易日
    """
    try:
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')

        prev_day = None
        used_source = source

        if source == "auto" or source == "tdx":
            try:
                from backend.dataflows.providers.tdx_provider import get_tdx_provider
                provider = get_tdx_provider()
                if provider.is_available():
                    prev_day = provider.get_prev_trading_day(date)
                    used_source = "tdx"
                    logger.info(f"✅ TDX上一交易日获取成功: {date} -> {prev_day}")
            except Exception as e:
                logger.warning(f"⚠️ TDX上一交易日失败: {e}")

        return {
            "success": True,
            "date": date,
            "prev_trading_day": prev_day,
            "source": used_source
        }

    except Exception as e:
        logger.error(f"获取上一交易日失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

