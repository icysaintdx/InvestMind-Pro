"""
K线数据API
提供多种周期的K线数据，支持AKShare、Tushare、新浪等数据源
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime, timedelta
import pandas as pd

from backend.utils.logging_config import get_logger

logger = get_logger("api.kline")
router = APIRouter(prefix="/api/kline", tags=["K-Line Data"])


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


# ==================== API端点 ====================

@router.get("/data")
async def get_kline_data(
    symbol: str = Query(..., description="股票代码，如：600519"),
    period: str = Query("daily", description="周期：1/5/15/30/60/daily"),
    adjust: str = Query("qfq", description="复权类型：qfq前复权/hfq后复权/空不复权"),
    source: str = Query("akshare", description="数据源：akshare/sina"),
    limit: int = Query(500, description="返回数据条数")
):
    """
    获取K线数据
    
    Args:
        symbol: 股票代码
        period: 周期
        adjust: 复权类型
        source: 数据源
        limit: 返回条数
    
    Returns:
        K线数据
    """
    try:
        logger.info(f"获取K线数据: {symbol} {period} {adjust} {source}")
        
        # 根据数据源获取数据
        if source == "akshare":
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
            "count": len(data),
            "data": data
        }
        
    except Exception as e:
        logger.error(f"获取K线数据失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取K线数据失败: {str(e)}")


@router.get("/realtime")
async def get_realtime_data(
    symbol: str = Query(..., description="股票代码，如：600519")
):
    """
    获取实时行情数据
    
    Args:
        symbol: 股票代码
    
    Returns:
        实时行情
    """
    try:
        import akshare as ak
        
        # 处理股票代码格式
        if not symbol.startswith(('sh', 'sz')):
            if symbol.startswith('6'):
                symbol = f'sh{symbol}'
            else:
                symbol = f'sz{symbol}'
        
        # 获取实时行情
        df = ak.stock_zh_a_spot_em()
        stock_data = df[df['代码'] == symbol.replace('sh', '').replace('sz', '')]
        
        if stock_data.empty:
            raise HTTPException(status_code=404, detail="股票不存在")
        
        data = stock_data.iloc[0].to_dict()
        
        return {
            "success": True,
            "data": {
                "symbol": symbol,
                "name": data.get('名称', ''),
                "price": data.get('最新价', 0),
                "change": data.get('涨跌额', 0),
                "change_pct": data.get('涨跌幅', 0),
                "open": data.get('今开', 0),
                "high": data.get('最高', 0),
                "low": data.get('最低', 0),
                "volume": data.get('成交量', 0),
                "amount": data.get('成交额', 0),
                "turnover": data.get('换手率', 0)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取实时行情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
