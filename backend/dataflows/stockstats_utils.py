#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stockstats 技术指标计算模块

用于计算各种技术指标（SMA, EMA, MACD, RSI, 布林带等）
需要安装 stockstats 和 yfinance 库

配置说明：
- 数据缓存目录：DATA_CACHE_DIR 环境变量
"""

import os
from datetime import datetime
from typing import Any, Optional

# 导入日志模块
from backend.utils.logging_config import get_logger
logger = get_logger('dataflow')

# 尝试导入必要的库
try:
    import pandas as pd
    from stockstats import wrap
    STOCKSTATS_AVAILABLE = True
except ImportError:
    STOCKSTATS_AVAILABLE = False
    logger.warning("[Stockstats] stockstats 未安装，技术指标功能不可用")
    pd = None
    wrap = None

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    logger.warning("[Stockstats] yfinance 未安装，在线数据获取不可用")
    yf = None

# 默认缓存目录
DEFAULT_CACHE_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'cache')

# 支持的技术指标及其说明
INDICATOR_DESCRIPTIONS = {
    "close_50_sma": (
        "50 SMA: 中期趋势指标。"
        "用途：识别趋势方向，作为动态支撑/阻力位。"
        "提示：滞后于价格，建议结合快速指标使用。"
    ),
    "close_200_sma": (
        "200 SMA: 长期趋势基准。"
        "用途：确认整体市场趋势，识别金叉/死叉。"
        "提示：反应缓慢，适合战略性趋势确认。"
    ),
    "close_10_ema": (
        "10 EMA: 短期响应平均线。"
        "用途：捕捉快速动量变化和潜在入场点。"
        "提示：在震荡市场中容易产生噪音。"
    ),
    "macd": (
        "MACD: 通过EMA差值计算动量。"
        "用途：寻找交叉和背离作为趋势变化信号。"
        "提示：在低波动或横盘市场中需要其他指标确认。"
    ),
    "macds": (
        "MACD信号线: MACD线的EMA平滑。"
        "用途：与MACD线交叉触发交易信号。"
        "提示：应作为更广泛策略的一部分。"
    ),
    "macdh": (
        "MACD柱状图: MACD线与信号线的差值。"
        "用途：可视化动量强度，早期发现背离。"
        "提示：可能波动较大，在快速市场中需要额外过滤。"
    ),
    "rsi_14": (
        "RSI: 测量动量以标记超买/超卖状态。"
        "用途：应用70/30阈值，观察背离以信号反转。"
        "提示：在强趋势中RSI可能保持极端值，需结合趋势分析。"
    ),
    "boll": (
        "布林带中轨: 20日SMA作为布林带基准。"
        "用途：作为价格运动的动态基准。"
        "提示：结合上下轨有效发现突破或反转。"
    ),
    "boll_ub": (
        "布林带上轨: 通常为中轨上方2个标准差。"
        "用途：信号潜在超买状态和突破区域。"
        "提示：需其他工具确认，强趋势中价格可能沿轨道运行。"
    ),
    "boll_lb": (
        "布林带下轨: 通常为中轨下方2个标准差。"
        "用途：指示潜在超卖状态。"
        "提示：使用额外分析避免虚假反转信号。"
    ),
    "atr": (
        "ATR: 平均真实波幅测量波动性。"
        "用途：设置止损位，根据当前市场波动调整仓位大小。"
        "提示：这是反应性指标，应作为更广泛风险管理策略的一部分。"
    ),
    "vwma": (
        "VWMA: 成交量加权移动平均。"
        "用途：通过整合价格和成交量数据确认趋势。"
        "提示：注意成交量激增导致的偏差，结合其他成交量分析使用。"
    ),
    "mfi": (
        "MFI: 资金流量指标，使用价格和成交量测量买卖压力。"
        "用途：识别超买(>80)或超卖(<20)状态，确认趋势或反转强度。"
        "提示：与RSI或MACD结合使用确认信号，价格与MFI背离可能预示反转。"
    ),
}


class StockstatsUtils:
    """技术指标计算工具类"""
    
    @staticmethod
    def get_stock_stats(
        symbol: str,
        indicator: str,
        curr_date: str,
        data_dir: str = None,
        online: bool = True
    ) -> Any:
        """
        获取股票技术指标
        
        Args:
            symbol: 股票代码
            indicator: 技术指标名称
            curr_date: 当前日期，格式 YYYY-MM-DD
            data_dir: 数据目录
            online: 是否在线获取数据
            
        Returns:
            指标值或 "N/A"
        """
        if not STOCKSTATS_AVAILABLE:
            logger.warning("[Stockstats] stockstats 未安装")
            return "N/A: stockstats not installed"
        
        if data_dir is None:
            data_dir = os.environ.get('DATA_CACHE_DIR', DEFAULT_CACHE_DIR)
        
        df = None
        data = None
        
        if not online:
            # 离线模式：从本地文件读取
            try:
                data_file = os.path.join(
                    data_dir,
                    f"{symbol}-YFin-data-2015-01-01-2025-03-25.csv",
                )
                data = pd.read_csv(data_file)
                df = wrap(data)
            except FileNotFoundError:
                logger.warning(f"[Stockstats] 本地数据文件不存在: {data_file}")
                return "N/A: Data file not found"
        else:
            # 在线模式：从 Yahoo Finance 获取
            if not YFINANCE_AVAILABLE:
                return "N/A: yfinance not installed"
            
            try:
                today_date = pd.Timestamp.today()
                curr_date_dt = pd.to_datetime(curr_date)
                
                end_date = today_date
                start_date = today_date - pd.DateOffset(years=15)
                start_date_str = start_date.strftime("%Y-%m-%d")
                end_date_str = end_date.strftime("%Y-%m-%d")
                
                # 确保缓存目录存在
                os.makedirs(data_dir, exist_ok=True)
                
                data_file = os.path.join(
                    data_dir,
                    f"{symbol}-YFin-data-{start_date_str}-{end_date_str}.csv",
                )
                
                if os.path.exists(data_file):
                    data = pd.read_csv(data_file)
                    data["Date"] = pd.to_datetime(data["Date"])
                else:
                    data = yf.download(
                        symbol,
                        start=start_date_str,
                        end=end_date_str,
                        multi_level_index=False,
                        progress=False,
                        auto_adjust=True,
                    )
                    data = data.reset_index()
                    data.to_csv(data_file, index=False)
                
                df = wrap(data)
                df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")
                curr_date = curr_date_dt.strftime("%Y-%m-%d")
                
            except Exception as e:
                logger.error(f"[Stockstats] 获取数据失败: {e}")
                return f"N/A: {str(e)}"
        
        try:
            # 触发 stockstats 计算指标
            df[indicator]
            matching_rows = df[df["Date"].str.startswith(curr_date)]
            
            if not matching_rows.empty:
                indicator_value = matching_rows[indicator].values[0]
                return indicator_value
            else:
                return "N/A: Not a trading day (weekend or holiday)"
                
        except Exception as e:
            logger.error(f"[Stockstats] 计算指标失败: {e}")
            return f"N/A: {str(e)}"
    
    @staticmethod
    def get_supported_indicators() -> dict:
        """获取支持的技术指标列表"""
        return INDICATOR_DESCRIPTIONS


def get_technical_indicator(
    symbol: str,
    indicator: str,
    curr_date: str,
    look_back_days: int = 60
) -> str:
    """
    获取技术指标数据（使用 stockstats 库计算）
    
    Args:
        symbol: 股票代码
        indicator: 技术指标名称
        curr_date: 当前日期，格式 YYYY-MM-DD
        look_back_days: 回看天数
        
    Returns:
        str: 格式化的指标数据
    """
    if not STOCKSTATS_AVAILABLE:
        return "Error: stockstats not installed. Please run: pip install stockstats"
    
    if not YFINANCE_AVAILABLE:
        return "Error: yfinance not installed. Please run: pip install yfinance"
    
    if indicator not in INDICATOR_DESCRIPTIONS:
        supported = ", ".join(INDICATOR_DESCRIPTIONS.keys())
        return f"Error: Unsupported indicator '{indicator}'. Supported: {supported}"
    
    try:
        from dateutil.relativedelta import relativedelta
        
        # 计算日期范围
        curr_date_dt = datetime.strptime(curr_date, "%Y-%m-%d")
        start_date_dt = curr_date_dt - relativedelta(days=look_back_days + 365)
        start_date = start_date_dt.strftime("%Y-%m-%d")
        
        # 获取股票数据
        logger.info(f"[Stockstats] 获取 {symbol} 技术指标 {indicator}")
        ticker = yf.Ticker(symbol.upper())
        data = ticker.history(start=start_date, end=curr_date)
        
        if data.empty:
            return f"Error: No data found for {symbol}"
        
        # 重置索引
        data = data.reset_index()
        data['Date'] = pd.to_datetime(data['Date']).dt.strftime('%Y-%m-%d')
        
        # 使用 stockstats 计算指标
        df = wrap(data)
        df[indicator]  # 触发计算
        
        # 生成结果
        result_lines = []
        check_date = curr_date_dt
        end_date = curr_date_dt - relativedelta(days=look_back_days)
        
        while check_date >= end_date:
            date_str = check_date.strftime('%Y-%m-%d')
            matching_rows = df[df['Date'] == date_str]
            
            if not matching_rows.empty:
                value = matching_rows.iloc[0][indicator]
                if pd.isna(value):
                    result_lines.append(f"{date_str}: N/A")
                else:
                    result_lines.append(f"{date_str}: {value:.4f}")
            else:
                result_lines.append(f"{date_str}: N/A (not a trading day)")
            
            check_date = check_date - relativedelta(days=1)
        
        # 构建结果字符串
        result = f"## {indicator} values from {end_date.strftime('%Y-%m-%d')} to {curr_date}:\n\n"
        result += "\n".join(result_lines)
        result += "\n\n" + INDICATOR_DESCRIPTIONS[indicator]
        
        return result
        
    except ImportError:
        return "Error: dateutil not installed. Please run: pip install python-dateutil"
    except Exception as e:
        logger.error(f"[Stockstats] 计算技术指标失败: {e}")
        return f"Error calculating indicator {indicator} for {symbol}: {str(e)}"


# 检查模块是否可用
def is_available() -> bool:
    """检查技术指标功能是否可用"""
    return STOCKSTATS_AVAILABLE and YFINANCE_AVAILABLE