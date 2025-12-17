"""
回测数据加载器
对接 Tushare/AKShare 等数据源
"""

import pandas as pd
import numpy as np
from typing import Optional, Union, List
from enum import Enum
from datetime import datetime, timedelta
import logging
import akshare as ak
import tushare as ts

logger = logging.getLogger(__name__)


class DataSource(str, Enum):
    """数据源类型"""
    AKSHARE = "akshare"
    TUSHARE = "tushare"
    CSV = "csv"
    DATABASE = "database"


class DataLoader:
    """数据加载器"""
    
    def __init__(self, source: DataSource = DataSource.AKSHARE):
        """
        初始化数据加载器
        
        Args:
            source: 数据源类型
        """
        self.source = source
        
        # 初始化 Tushare（需要 token）
        if source == DataSource.TUSHARE:
            # 从配置文件读取 token
            try:
                ts.set_token('your_tushare_token')  # TODO: 从配置文件读取
                self.ts_api = ts.pro_api()
            except Exception as e:
                logger.warning(f"Tushare 初始化失败: {e}，切换到 AKShare")
                self.source = DataSource.AKSHARE
    
    def load_stock_data(
        self,
        symbol: str,
        start_date: Union[str, datetime],
        end_date: Union[str, datetime],
        adjust: str = 'qfq'
    ) -> Optional[pd.DataFrame]:
        """
        加载股票历史数据
        
        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            adjust: 复权类型 ('qfq': 前复权, 'hfq': 后复权, None: 不复权)
        
        Returns:
            包含 OHLCV 的 DataFrame
        """
        # 转换日期格式
        if isinstance(start_date, datetime):
            start_date = start_date.strftime('%Y%m%d')
        else:
            start_date = start_date.replace('-', '')
            
        if isinstance(end_date, datetime):
            end_date = end_date.strftime('%Y%m%d')
        else:
            end_date = end_date.replace('-', '')
        
        if self.source == DataSource.AKSHARE:
            return self._load_from_akshare(symbol, start_date, end_date, adjust)
        elif self.source == DataSource.TUSHARE:
            return self._load_from_tushare(symbol, start_date, end_date, adjust)
        elif self.source == DataSource.CSV:
            return self._load_from_csv(symbol, start_date, end_date)
        else:
            logger.error(f"不支持的数据源: {self.source}")
            return None
    
    def _load_from_akshare(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        adjust: str
    ) -> Optional[pd.DataFrame]:
        """从AKShare加载数据"""
        try:
            # AKShare的stock_zh_a_hist不需要sh/sz前缀，只需要纯数字代码
            # 如果有前缀，去掉它
            if symbol.startswith(('sh', 'sz', 'bj')):
                symbol = symbol[2:]  # 去掉前两个字符
                
            # 确保日期格式为YYYYMMDD（去掉所有连字符）
            start_date = start_date.replace('-', '')
            end_date = end_date.replace('-', '')
                
            logger.info(f"加载AKShare数据: symbol={symbol}, start={start_date}, end={end_date}, adjust={adjust}")
                
            # 获取历史行情数据
            df = ak.stock_zh_a_hist(
                symbol=symbol,
                period="daily",
                start_date=start_date,
                end_date=end_date,
                adjust=adjust
            )
            
            if df is None or df.empty:
                logger.warning(f"AKShare 未获取到数据: {symbol}")
                return None
            
            # 重命名列
            df = df.rename(columns={
                '日期': 'date',
                '开盘': 'open',
                '收盘': 'close',
                '最高': 'high',
                '最低': 'low',
                '成交量': 'volume',
                '成交额': 'amount',
                '涨跌幅': 'pct_change'
            })
            
            # 设置日期索引
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            
            # 确保数据类型正确
            numeric_columns = ['open', 'high', 'low', 'close', 'volume', 'amount']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # 排序
            df.sort_index(inplace=True)
            
            logger.info(f"成功从 AKShare 加载 {symbol} 数据，共 {len(df)} 条")
            return df
            
        except Exception as e:
            logger.error(f"AKShare 加载数据失败 {symbol}: {e}")
            return None
    
    def _load_from_tushare(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        adjust: str
    ) -> Optional[pd.DataFrame]:
        """从 Tushare 加载数据"""
        try:
            # Tushare 股票代码格式：000001.SZ
            if '.' not in symbol:
                if symbol.startswith('6'):
                    symbol = symbol + '.SH'
                else:
                    symbol = symbol + '.SZ'
            
            # 获取日线数据
            df = self.ts_api.daily(
                ts_code=symbol,
                start_date=start_date,
                end_date=end_date
            )
            
            if df is None or df.empty:
                logger.warning(f"Tushare 未获取到数据: {symbol}")
                return None
            
            # 获取复权因子
            if adjust:
                adj_factor = self.ts_api.adj_factor(
                    ts_code=symbol,
                    start_date=start_date,
                    end_date=end_date
                )
                df = pd.merge(df, adj_factor[['trade_date', 'adj_factor']], on='trade_date')
                
                # 复权计算
                if adjust == 'qfq':  # 前复权
                    df['open'] = df['open'] * df['adj_factor']
                    df['high'] = df['high'] * df['adj_factor']
                    df['low'] = df['low'] * df['adj_factor']
                    df['close'] = df['close'] * df['adj_factor']
            
            # 重命名列
            df = df.rename(columns={
                'trade_date': 'date',
                'vol': 'volume'
            })
            
            # 设置日期索引
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            
            # 排序
            df.sort_index(inplace=True)
            
            logger.info(f"成功从 Tushare 加载 {symbol} 数据，共 {len(df)} 条")
            return df[['open', 'high', 'low', 'close', 'volume', 'amount']]
            
        except Exception as e:
            logger.error(f"Tushare 加载数据失败 {symbol}: {e}")
            # 尝试降级到 AKShare
            logger.info("尝试使用 AKShare 加载数据...")
            return self._load_from_akshare(symbol, start_date, end_date, adjust)
    
    def _load_from_csv(
        self,
        symbol: str,
        start_date: str,
        end_date: str
    ) -> Optional[pd.DataFrame]:
        """从 CSV 文件加载数据"""
        try:
            # CSV 文件路径
            file_path = f"data/{symbol}.csv"
            
            # 读取数据
            df = pd.read_csv(file_path)
            
            # 转换日期
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            
            # 日期过滤
            start_dt = pd.to_datetime(start_date)
            end_dt = pd.to_datetime(end_date)
            df = df[(df.index >= start_dt) & (df.index <= end_dt)]
            
            logger.info(f"成功从 CSV 加载 {symbol} 数据，共 {len(df)} 条")
            return df
            
        except Exception as e:
            logger.error(f"CSV 加载数据失败 {symbol}: {e}")
            return None
    
    def load_benchmark_data(
        self,
        benchmark: str,
        start_date: Union[str, datetime],
        end_date: Union[str, datetime]
    ) -> Optional[pd.DataFrame]:
        """
        加载基准指数数据
        
        Args:
            benchmark: 基准代码（如 '000001' 上证指数）
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            基准指数数据
        """
        # 转换日期格式
        if isinstance(start_date, datetime):
            start_date = start_date.strftime('%Y%m%d')
        else:
            start_date = start_date.replace('-', '')
            
        if isinstance(end_date, datetime):
            end_date = end_date.strftime('%Y%m%d')
        else:
            end_date = end_date.replace('-', '')
        
        try:
            if self.source == DataSource.AKSHARE:
                # 获取指数历史数据
                df = ak.stock_zh_index_daily(symbol=f"sh{benchmark}")
                
                if df is None or df.empty:
                    logger.warning(f"未获取到基准数据: {benchmark}")
                    return None
                
                # 重命名列
                df = df.rename(columns={
                    'date': 'date',
                    'open': 'open',
                    'close': 'close',
                    'high': 'high',
                    'low': 'low',
                    'volume': 'volume'
                })
                
                # 设置日期索引
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
                
                # 日期过滤
                start_dt = pd.to_datetime(start_date)
                end_dt = pd.to_datetime(end_date)
                df = df[(df.index >= start_dt) & (df.index <= end_dt)]
                
                logger.info(f"成功加载基准 {benchmark} 数据，共 {len(df)} 条")
                return df
                
        except Exception as e:
            logger.error(f"加载基准数据失败 {benchmark}: {e}")
            return None
    
    def load_multiple_stocks(
        self,
        symbols: List[str],
        start_date: Union[str, datetime],
        end_date: Union[str, datetime],
        adjust: str = 'qfq'
    ) -> dict:
        """
        批量加载多只股票数据
        
        Args:
            symbols: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            adjust: 复权类型
        
        Returns:
            {symbol: DataFrame} 字典
        """
        data = {}
        
        for symbol in symbols:
            df = self.load_stock_data(symbol, start_date, end_date, adjust)
            if df is not None and not df.empty:
                data[symbol] = df
            else:
                logger.warning(f"跳过无数据的股票: {symbol}")
        
        logger.info(f"成功加载 {len(data)}/{len(symbols)} 只股票数据")
        return data
    
    def add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        添加常用技术指标
        
        Args:
            df: OHLCV 数据
        
        Returns:
            包含技术指标的 DataFrame
        """
        # MA 均线
        for period in [5, 10, 20, 30, 60]:
            df[f'ma_{period}'] = df['close'].rolling(window=period).mean()
        
        # EMA 指数均线
        for period in [5, 12, 26]:
            df[f'ema_{period}'] = df['close'].ewm(span=period).mean()
        
        # MACD
        ema_12 = df['close'].ewm(span=12).mean()
        ema_26 = df['close'].ewm(span=26).mean()
        df['macd'] = ema_12 - ema_26
        df['macd_signal'] = df['macd'].ewm(span=9).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # Bollinger Bands
        df['bb_middle'] = df['close'].rolling(window=20).mean()
        bb_std = df['close'].rolling(window=20).std()
        df['bb_upper'] = df['bb_middle'] + 2 * bb_std
        df['bb_lower'] = df['bb_middle'] - 2 * bb_std
        
        # Volume MA
        df['volume_ma'] = df['volume'].rolling(window=20).mean()
        
        # ATR (Average True Range)
        high_low = df['high'] - df['low']
        high_close = abs(df['high'] - df['close'].shift())
        low_close = abs(df['low'] - df['close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['atr'] = tr.rolling(window=14).mean()
        
        return df
    
    def validate_data(self, df: pd.DataFrame) -> bool:
        """
        验证数据完整性
        
        Args:
            df: 数据 DataFrame
        
        Returns:
            是否有效
        """
        # 检查必要列
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        if not all(col in df.columns for col in required_columns):
            logger.error(f"数据缺少必要列: {required_columns}")
            return False
        
        # 检查数据量
        if len(df) < 30:
            logger.error(f"数据量太少: {len(df)} < 30")
            return False
        
        # 检查空值
        if df[required_columns].isnull().any().any():
            logger.warning("数据包含空值，尝试填充...")
            df.fillna(method='ffill', inplace=True)
        
        # 检查数据合理性
        if (df['high'] < df['low']).any():
            logger.error("数据异常: 最高价低于最低价")
            return False
        
        if (df['close'] > df['high']).any() or (df['close'] < df['low']).any():
            logger.error("数据异常: 收盘价超出最高最低价范围")
            return False
        
        return True


# 全局实例
_data_loader_instance = None


def get_data_loader(source: DataSource = DataSource.AKSHARE) -> DataLoader:
    """获取数据加载器实例"""
    global _data_loader_instance
    if _data_loader_instance is None or _data_loader_instance.source != source:
        _data_loader_instance = DataLoader(source)
    return _data_loader_instance


# 便捷函数
def load_stock_data(
    symbol: str,
    start_date: str,
    end_date: str,
    source: DataSource = DataSource.AKSHARE,
    add_indicators: bool = True
) -> Optional[pd.DataFrame]:
    """
    便捷函数：加载股票数据
    
    Args:
        symbol: 股票代码
        start_date: 开始日期
        end_date: 结束日期
        source: 数据源
        add_indicators: 是否添加技术指标
    
    Returns:
        股票数据 DataFrame
    """
    loader = get_data_loader(source)
    df = loader.load_stock_data(symbol, start_date, end_date)
    
    if df is not None and add_indicators:
        df = loader.add_technical_indicators(df)
    
    return df
