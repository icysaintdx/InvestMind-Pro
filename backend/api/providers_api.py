"""
数据源Provider API
提供TDX通达信、问财(Wencai)、TA-Lib技术指标等数据源的API端点
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from datetime import datetime
import pandas as pd

from backend.utils.logging_config import get_logger

logger = get_logger("api.providers")
router = APIRouter(prefix="/api/providers", tags=["Data Providers"])


# ==================== TDX Provider 辅助函数 ====================

def get_best_tdx_provider():
    """
    获取最佳可用的 TDX Provider
    优先级: TDX Native (纯Python) > TDX HTTP (需要Docker服务)

    Returns:
        (provider, provider_type) 或 (None, None)
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


# ==================== TDX 通达信数据源 ====================

@router.get("/tdx/status")
async def get_tdx_status():
    """
    获取TDX服务状态（优先检查Native Provider）

    Returns:
        TDX服务可用性状态
    """
    try:
        # 检查 Native Provider
        native_available = False
        native_info = None
        try:
            from backend.dataflows.providers.tdx_native_provider import get_tdx_native_provider
            native_provider = get_tdx_native_provider()
            native_available = native_provider.is_available()
            if native_available:
                native_info = "TDX Native Provider (纯Python，无需Docker)"
        except Exception as e:
            logger.debug(f"Native Provider检查失败: {e}")

        # 检查 HTTP Provider
        http_available = False
        http_info = None
        try:
            from backend.dataflows.providers.tdx_provider import get_tdx_provider
            http_provider = get_tdx_provider()
            http_available = http_provider.is_available()
            if http_available:
                http_info = f"TDX HTTP Provider ({http_provider.base_url})"
        except Exception as e:
            logger.debug(f"HTTP Provider检查失败: {e}")

        available = native_available or http_available
        provider_type = 'native' if native_available else ('http' if http_available else None)

        return {
            "success": True,
            "available": available,
            "provider_type": provider_type,
            "native_available": native_available,
            "http_available": http_available,
            "native_info": native_info,
            "http_info": http_info,
            "message": f"TDX服务可用 ({provider_type})" if available else "TDX服务不可用"
        }
    except Exception as e:
        logger.error(f"获取TDX状态失败: {e}")
        return {
            "success": False,
            "available": False,
            "message": f"获取TDX状态失败: {str(e)}"
        }


@router.get("/tdx/quote")
async def get_tdx_quote(
    codes: str = Query(..., description="股票代码，多个用逗号分隔，如：000001,600519")
):
    """
    通过TDX获取实时行情（优先使用Native Provider）

    Args:
        codes: 股票代码列表

    Returns:
        实时行情数据
    """
    try:
        provider, provider_type = get_best_tdx_provider()

        if not provider:
            raise HTTPException(status_code=503, detail="TDX服务不可用")

        code_list = [c.strip() for c in codes.split(',')]

        # Native Provider 使用 get_realtime_quotes
        if provider_type == 'native':
            quotes = provider.get_realtime_quotes(code_list)
        else:
            # HTTP Provider 使用 get_realtime_quote
            quotes = provider.get_realtime_quote(code_list)

        return {
            "success": True,
            "count": len(quotes) if quotes else 0,
            "data": quotes,
            "source": f"tdx_{provider_type}"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"TDX获取行情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tdx/kline")
async def get_tdx_kline(
    code: str = Query(..., description="股票代码，如：000001"),
    kline_type: str = Query("day", description="K线类型：1m/5m/15m/30m/60m/day/week/month"),
    limit: int = Query(200, description="返回条数")
):
    """
    通过TDX获取K线数据（优先使用Native Provider）

    Args:
        code: 股票代码
        kline_type: K线类型
        limit: 返回条数

    Returns:
        K线数据
    """
    try:
        provider, provider_type = get_best_tdx_provider()

        if not provider:
            raise HTTPException(status_code=503, detail="TDX服务不可用")

        # Native Provider 使用 kline_type 数字
        if provider_type == 'native':
            kline_type_mapping = {
                '1m': 8, '5m': 0, '15m': 1, '30m': 2, '60m': 3,
                'day': 9, 'week': 5, 'month': 6
            }
            ktype = kline_type_mapping.get(kline_type, 9)
            kline_data = provider.get_kline(code, ktype, limit)
            if kline_data:
                import pandas as pd
                df = pd.DataFrame(kline_data)
            else:
                df = None
        else:
            df = provider.get_kline(code, kline_type, limit)

        if df is None or (hasattr(df, 'empty') and df.empty):
            raise HTTPException(status_code=404, detail="未获取到K线数据")

        # 转换为JSON格式
        data = df.to_dict(orient='records') if hasattr(df, 'to_dict') else df

        return {
            "success": True,
            "code": code,
            "kline_type": kline_type,
            "count": len(data),
            "data": data,
            "source": f"tdx_{provider_type}"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"TDX获取K线失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tdx/minute")
async def get_tdx_minute(
    code: str = Query(..., description="股票代码"),
    date: Optional[str] = Query(None, description="日期，格式YYYYMMDD，默认今天")
):
    """
    通过TDX获取分时数据（优先使用Native Provider）

    Args:
        code: 股票代码
        date: 日期

    Returns:
        分时数据
    """
    try:
        provider, provider_type = get_best_tdx_provider()

        if not provider:
            raise HTTPException(status_code=503, detail="TDX服务不可用")

        # Native Provider
        if provider_type == 'native':
            if date:
                minute_data = provider.get_history_minute_data(code, date)
            else:
                minute_data = provider.get_minute_data(code)
            data = minute_data if minute_data else []
        else:
            df = provider.get_minute_data(code, date)
            if df is None or df.empty:
                raise HTTPException(status_code=404, detail="未获取到分时数据")
            data = df.to_dict(orient='records')

        return {
            "success": True,
            "code": code,
            "count": len(data),
            "data": data,
            "source": f"tdx_{provider_type}"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"TDX获取分时数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tdx/indicators")
async def get_tdx_indicators(
    code: str = Query(..., description="股票代码"),
    kline_type: str = Query("day", description="K线类型")
):
    """
    通过TDX获取技术指标

    Args:
        code: 股票代码
        kline_type: K线类型

    Returns:
        技术指标数据
    """
    try:
        # 技术指标计算目前只有HTTP Provider支持
        # Native Provider可以获取K线数据，但技术指标需要额外计算
        from backend.dataflows.providers.tdx_provider import get_tdx_provider
        provider = get_tdx_provider()

        if not provider.is_available():
            raise HTTPException(status_code=503, detail="TDX服务不可用（技术指标需要TDX HTTP服务）")

        indicators = provider.calculate_technical_indicators(code, kline_type)

        if indicators is None:
            raise HTTPException(status_code=404, detail="未能计算技术指标")

        return {
            "success": True,
            "data": indicators,
            "source": "tdx_http"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"TDX计算技术指标失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 问财(Wencai)数据源 ====================

@router.get("/wencai/status")
async def get_wencai_status():
    """
    获取问财服务状态

    Returns:
        问财服务可用性状态
    """
    try:
        from backend.dataflows.providers.wencai_provider import get_wencai_provider
        provider = get_wencai_provider()

        return {
            "success": True,
            "available": provider.is_available(),
            "message": "问财服务可用" if provider.is_available() else "问财服务不可用，请安装pywencai: pip install pywencai"
        }
    except Exception as e:
        logger.error(f"获取问财状态失败: {e}")
        return {
            "success": False,
            "available": False,
            "message": f"获取问财状态失败: {str(e)}"
        }


@router.get("/wencai/query")
async def wencai_query(
    query: str = Query(..., description="自然语言查询语句"),
    loop: bool = Query(True, description="是否循环获取所有数据")
):
    """
    执行问财自然语言查询

    Args:
        query: 自然语言查询语句
        loop: 是否循环获取所有数据

    Returns:
        查询结果
    """
    try:
        from backend.dataflows.providers.wencai_provider import get_wencai_provider
        provider = get_wencai_provider()

        if not provider.is_available():
            raise HTTPException(status_code=503, detail="问财服务不可用，请安装pywencai")

        df = provider.query(query, loop)

        if df is None or df.empty:
            return {
                "success": True,
                "count": 0,
                "data": [],
                "message": "查询无结果"
            }

        data = df.to_dict(orient='records')

        return {
            "success": True,
            "count": len(data),
            "data": data
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"问财查询失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/wencai/main-force")
async def get_main_force_stocks(
    days_ago: int = Query(30, description="距今多少天"),
    min_market_cap: float = Query(50, description="最小市值（亿）"),
    max_market_cap: float = Query(2000, description="最大市值（亿）"),
    top_n: int = Query(100, description="返回前N名")
):
    """
    获取主力资金净流入排名股票

    Args:
        days_ago: 距今多少天
        min_market_cap: 最小市值
        max_market_cap: 最大市值
        top_n: 返回数量

    Returns:
        主力资金数据
    """
    try:
        from backend.dataflows.providers.wencai_provider import get_wencai_provider
        provider = get_wencai_provider()

        if not provider.is_available():
            raise HTTPException(status_code=503, detail="问财服务不可用")

        success, df, message = provider.get_main_force_stocks(
            days_ago=days_ago,
            min_market_cap=min_market_cap,
            max_market_cap=max_market_cap,
            top_n=top_n
        )

        if not success or df is None:
            return {
                "success": False,
                "message": message,
                "data": []
            }

        data = df.to_dict(orient='records')

        return {
            "success": True,
            "count": len(data),
            "message": message,
            "data": data
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取主力资金数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/wencai/quarterly-report")
async def get_quarterly_report(
    symbol: str = Query(..., description="股票代码")
):
    """
    获取股票季报数据

    Args:
        symbol: 股票代码

    Returns:
        季报数据
    """
    try:
        from backend.dataflows.providers.wencai_provider import get_wencai_provider
        provider = get_wencai_provider()

        if not provider.is_available():
            raise HTTPException(status_code=503, detail="问财服务不可用")

        data = provider.get_quarterly_report(symbol)

        if data is None:
            return {
                "success": False,
                "message": "未获取到季报数据",
                "data": None
            }

        return {
            "success": True,
            "data": data
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取季报数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/wencai/financial-scores")
async def get_financial_scores(
    symbol: str = Query(..., description="股票代码")
):
    """
    获取股票财务评分

    Args:
        symbol: 股票代码

    Returns:
        财务评分数据
    """
    try:
        from backend.dataflows.providers.wencai_provider import get_wencai_provider
        provider = get_wencai_provider()

        if not provider.is_available():
            raise HTTPException(status_code=503, detail="问财服务不可用")

        data = provider.get_financial_scores(symbol)

        if data is None:
            return {
                "success": False,
                "message": "未获取到财务评分",
                "data": None
            }

        return {
            "success": True,
            "data": data
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取财务评分失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/wencai/hot-sectors")
async def get_hot_sectors(
    days: int = Query(5, description="统计天数")
):
    """
    获取热门板块

    Args:
        days: 统计天数

    Returns:
        热门板块数据
    """
    try:
        from backend.dataflows.providers.wencai_provider import get_wencai_provider
        provider = get_wencai_provider()

        if not provider.is_available():
            raise HTTPException(status_code=503, detail="问财服务不可用")

        df = provider.get_hot_sectors(days)

        if df is None or df.empty:
            return {
                "success": True,
                "count": 0,
                "data": []
            }

        data = df.to_dict(orient='records')

        return {
            "success": True,
            "count": len(data),
            "data": data
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取热门板块失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/wencai/smart-selection")
async def smart_stock_selection(
    conditions: str = Query(..., description="选股条件（自然语言），如：市盈率小于20，ROE大于15%")
):
    """
    智能选股

    Args:
        conditions: 选股条件

    Returns:
        选股结果
    """
    try:
        from backend.dataflows.providers.wencai_provider import get_wencai_provider
        provider = get_wencai_provider()

        if not provider.is_available():
            raise HTTPException(status_code=503, detail="问财服务不可用")

        df = provider.smart_stock_selection(conditions)

        if df is None or df.empty:
            return {
                "success": True,
                "count": 0,
                "data": [],
                "message": "未找到符合条件的股票"
            }

        data = df.to_dict(orient='records')

        return {
            "success": True,
            "count": len(data),
            "data": data
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"智能选股失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== TA-Lib 技术指标 ====================

@router.get("/talib/status")
async def get_talib_status():
    """
    获取TA-Lib状态

    Returns:
        TA-Lib可用性状态
    """
    try:
        from backend.dataflows.providers.talib_provider import get_talib_provider
        provider = get_talib_provider()

        return {
            "success": True,
            "available": provider.is_available(),
            "message": "TA-Lib可用" if provider.is_available() else "TA-Lib未安装，使用纯Python实现作为备选"
        }
    except Exception as e:
        logger.error(f"获取TA-Lib状态失败: {e}")
        return {
            "success": False,
            "available": False,
            "message": f"获取TA-Lib状态失败: {str(e)}"
        }


@router.post("/talib/indicators")
async def calculate_talib_indicators(
    symbol: str = Query(..., description="股票代码"),
    period: str = Query("daily", description="K线周期"),
    limit: int = Query(200, description="数据条数")
):
    """
    使用TA-Lib计算技术指标

    Args:
        symbol: 股票代码
        period: K线周期
        limit: 数据条数

    Returns:
        技术指标数据
    """
    try:
        from backend.dataflows.providers.talib_provider import get_talib_provider
        import akshare as ak

        provider = get_talib_provider()

        # 获取K线数据
        clean_symbol = symbol.replace('sh', '').replace('sz', '')

        if period == 'daily':
            from datetime import timedelta
            df = ak.stock_zh_a_hist(
                symbol=clean_symbol,
                period="daily",
                start_date=(datetime.now() - timedelta(days=365)).strftime('%Y%m%d'),
                end_date=datetime.now().strftime('%Y%m%d'),
                adjust="qfq"
            )
        else:
            df = ak.stock_zh_a_hist_min_em(
                symbol=clean_symbol,
                period=period,
                adjust="qfq"
            )

        if df is None or df.empty:
            raise HTTPException(status_code=404, detail="未获取到K线数据")

        # 统一列名
        column_mapping = {
            '日期': 'date',
            '时间': 'date',
            '开盘': 'open',
            '收盘': 'close',
            '最高': 'high',
            '最低': 'low',
            '成交量': 'volume'
        }
        rename_dict = {k: v for k, v in column_mapping.items() if k in df.columns}
        df = df.rename(columns=rename_dict)

        # 限制数据量
        if len(df) > limit:
            df = df.tail(limit).reset_index(drop=True)

        # 计算所有技术指标
        result_df = provider.calculate_all_indicators(df)

        # 取最新数据
        latest = result_df.iloc[-1].to_dict()

        # 清理NaN值
        for key, value in latest.items():
            if pd.isna(value):
                latest[key] = None

        return {
            "success": True,
            "symbol": symbol,
            "talib_available": provider.is_available(),
            "latest_indicators": latest,
            "data_count": len(result_df)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"计算技术指标失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 综合数据源状态 ====================

@router.get("/status")
async def get_all_providers_status():
    """
    获取所有数据源Provider的状态

    Returns:
        所有Provider的状态汇总
    """
    status = {
        "success": True,
        "timestamp": datetime.now().isoformat(),
        "providers": {}
    }

    # TDX状态
    try:
        from backend.dataflows.providers.tdx_provider import get_tdx_provider
        tdx = get_tdx_provider()
        status["providers"]["tdx"] = {
            "name": "通达信TDX",
            "available": tdx.is_available(),
            "base_url": tdx.base_url,
            "features": ["实时行情", "K线数据", "分时数据", "技术指标"]
        }
    except Exception as e:
        status["providers"]["tdx"] = {
            "name": "通达信TDX",
            "available": False,
            "error": str(e)
        }

    # Wencai状态
    try:
        from backend.dataflows.providers.wencai_provider import get_wencai_provider
        wencai = get_wencai_provider()
        status["providers"]["wencai"] = {
            "name": "问财(pywencai)",
            "available": wencai.is_available(),
            "features": ["主力资金", "季报数据", "智能选股", "热门板块"]
        }
    except Exception as e:
        status["providers"]["wencai"] = {
            "name": "问财(pywencai)",
            "available": False,
            "error": str(e)
        }

    # TA-Lib状态
    try:
        from backend.dataflows.providers.talib_provider import get_talib_provider
        talib = get_talib_provider()
        status["providers"]["talib"] = {
            "name": "TA-Lib技术指标",
            "available": talib.is_available(),
            "fallback": "纯Python实现" if not talib.is_available() else None,
            "features": ["MA均线", "MACD", "RSI", "KDJ", "布林带"]
        }
    except Exception as e:
        status["providers"]["talib"] = {
            "name": "TA-Lib技术指标",
            "available": False,
            "error": str(e)
        }

    # AKShare状态
    try:
        import akshare as ak
        status["providers"]["akshare"] = {
            "name": "AKShare",
            "available": True,
            "version": ak.__version__,
            "features": ["A股数据", "港股数据", "新闻数据", "指数数据"]
        }
    except Exception as e:
        status["providers"]["akshare"] = {
            "name": "AKShare",
            "available": False,
            "error": str(e)
        }

    return status
