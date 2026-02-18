"""
策略规则引擎
纯脚本逻辑实现策略条件判断，不依赖LLM
支持：
1. 根据策略条件自动判断买卖点
2. 历史回测 - 在历史K线数据上测试策略
3. 实时信号监控 - 接入实时行情判断交易机会
4. 与虚拟交易系统对接
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class SignalType(Enum):
    """信号类型"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


@dataclass
class TradeSignal:
    """交易信号"""
    signal_type: SignalType
    timestamp: datetime
    price: float
    confidence: float
    conditions_met: List[str]
    indicators: Dict[str, float]
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    reason: str = ""


@dataclass
class BacktestTrade:
    """回测交易记录"""
    entry_date: datetime
    entry_price: float
    entry_signal: TradeSignal
    exit_date: Optional[datetime] = None
    exit_price: Optional[float] = None
    exit_signal: Optional[TradeSignal] = None
    profit_pct: float = 0.0
    status: str = "open"  # open, closed, stopped


@dataclass
class BacktestResult:
    """回测结果"""
    strategy_id: str
    strategy_name: str
    stock_code: str
    start_date: datetime
    end_date: datetime
    trades: List[BacktestTrade] = field(default_factory=list)
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    total_return: float = 0.0
    max_drawdown: float = 0.0
    sharpe_ratio: float = 0.0
    buy_signals: List[Dict] = field(default_factory=list)
    sell_signals: List[Dict] = field(default_factory=list)


class IndicatorCalculator:
    """技术指标计算器 - 完整版"""
    
    @staticmethod
    def calculate_ma(df: pd.DataFrame, period: int, column: str = 'close') -> pd.Series:
        """计算简单移动平均线 (SMA)"""
        return df[column].rolling(window=period).mean()
    
    @staticmethod
    def calculate_ema(df: pd.DataFrame, period: int, column: str = 'close') -> pd.Series:
        """计算指数移动平均线 (EMA)"""
        return df[column].ewm(span=period, adjust=False).mean()
    
    @staticmethod
    def calculate_wma(df: pd.DataFrame, period: int, column: str = 'close') -> pd.Series:
        """计算加权移动平均线 (WMA)"""
        weights = np.arange(1, period + 1)
        return df[column].rolling(window=period).apply(
            lambda x: np.dot(x, weights) / weights.sum(), raw=True
        )
    
    @staticmethod
    def calculate_rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """计算相对强弱指数 (RSI)"""
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.fillna(50)  # 填充NaN为中性值
    
    @staticmethod
    def calculate_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """计算MACD指标"""
        exp1 = df['close'].ewm(span=fast, adjust=False).mean()
        exp2 = df['close'].ewm(span=slow, adjust=False).mean()
        macd = exp1 - exp2
        signal_line = macd.ewm(span=signal, adjust=False).mean()
        histogram = macd - signal_line
        return macd, signal_line, histogram
    
    @staticmethod
    def calculate_bollinger(df: pd.DataFrame, period: int = 20, std: float = 2) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """计算布林带 (Bollinger Bands)"""
        middle = df['close'].rolling(window=period).mean()
        std_dev = df['close'].rolling(window=period).std()
        upper = middle + (std_dev * std)
        lower = middle - (std_dev * std)
        return upper, middle, lower
    
    @staticmethod
    def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """计算真实波幅 (ATR)"""
        high = df['high']
        low = df['low']
        close = df['close']
        
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        return atr
    
    @staticmethod
    def calculate_adx(df: pd.DataFrame, period: int = 14) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """计算平均趋向指数 (ADX) 及 +DI/-DI"""
        high = df['high']
        low = df['low']
        close = df['close']
        
        # 计算方向移动
        plus_dm = high.diff()
        minus_dm = -low.diff()
        
        plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0)
        minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0)
        
        # 计算真实波幅
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # 平滑处理
        atr = tr.rolling(window=period).mean()
        plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)
        
        # 计算DX和ADX
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(window=period).mean()
        
        return adx, plus_di, minus_di
    
    @staticmethod
    def calculate_kdj(df: pd.DataFrame, k_period: int = 9, d_period: int = 3, j_period: int = 3) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """计算KDJ随机指标"""
        low_min = df['low'].rolling(window=k_period).min()
        high_max = df['high'].rolling(window=k_period).max()
        
        rsv = (df['close'] - low_min) / (high_max - low_min) * 100
        rsv = rsv.fillna(50)  # 填充NaN
        
        k = rsv.ewm(com=d_period-1, adjust=False).mean()
        d = k.ewm(com=j_period-1, adjust=False).mean()
        j = 3 * k - 2 * d
        
        return k, d, j
    
    @staticmethod
    def calculate_cci(df: pd.DataFrame, period: int = 20) -> pd.Series:
        """计算商品通道指数 (CCI)"""
        tp = (df['high'] + df['low'] + df['close']) / 3
        ma = tp.rolling(window=period).mean()
        md = tp.rolling(window=period).apply(lambda x: np.abs(x - x.mean()).mean(), raw=True)
        cci = (tp - ma) / (0.015 * md)
        return cci
    
    @staticmethod
    def calculate_williams_r(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """计算威廉指标 (Williams %R)"""
        high_max = df['high'].rolling(window=period).max()
        low_min = df['low'].rolling(window=period).min()
        wr = -100 * (high_max - df['close']) / (high_max - low_min)
        return wr
    
    @staticmethod
    def calculate_obv(df: pd.DataFrame) -> pd.Series:
        """计算能量潮指标 (OBV)"""
        obv = (np.sign(df['close'].diff()) * df['volume']).fillna(0).cumsum()
        return obv
    
    @staticmethod
    def calculate_volume_ma(df: pd.DataFrame, period: int = 5) -> pd.Series:
        """计算成交量均线"""
        return df['volume'].rolling(window=period).mean()
    
    @staticmethod
    def calculate_volume_ratio(df: pd.DataFrame, period: int = 5) -> pd.Series:
        """计算量比"""
        vol_ma = df['volume'].rolling(window=period).mean()
        return df['volume'] / vol_ma
    
    @staticmethod
    def calculate_donchian(df: pd.DataFrame, period: int = 20) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """计算唐奇安通道 (Donchian Channel)"""
        upper = df['high'].rolling(window=period).max()
        lower = df['low'].rolling(window=period).min()
        middle = (upper + lower) / 2
        return upper, middle, lower
    
    @staticmethod
    def calculate_sar(df: pd.DataFrame, af_start: float = 0.02, af_step: float = 0.02, af_max: float = 0.2) -> pd.Series:
        """计算抛物线转向指标 (SAR) - 简化版"""
        high = df['high'].values
        low = df['low'].values
        close = df['close'].values
        n = len(close)
        
        sar = np.zeros(n)
        trend = np.ones(n)  # 1 = 上升趋势, -1 = 下降趋势
        ep = np.zeros(n)  # 极值点
        af = np.zeros(n)  # 加速因子
        
        # 初始化
        sar[0] = low[0]
        ep[0] = high[0]
        af[0] = af_start
        
        for i in range(1, n):
            if trend[i-1] == 1:  # 上升趋势
                sar[i] = sar[i-1] + af[i-1] * (ep[i-1] - sar[i-1])
                sar[i] = min(sar[i], low[i-1], low[i-2] if i > 1 else low[i-1])
                
                if low[i] < sar[i]:  # 趋势反转
                    trend[i] = -1
                    sar[i] = ep[i-1]
                    ep[i] = low[i]
                    af[i] = af_start
                else:
                    trend[i] = 1
                    if high[i] > ep[i-1]:
                        ep[i] = high[i]
                        af[i] = min(af[i-1] + af_step, af_max)
                    else:
                        ep[i] = ep[i-1]
                        af[i] = af[i-1]
            else:  # 下降趋势
                sar[i] = sar[i-1] + af[i-1] * (ep[i-1] - sar[i-1])
                sar[i] = max(sar[i], high[i-1], high[i-2] if i > 1 else high[i-1])
                
                if high[i] > sar[i]:  # 趋势反转
                    trend[i] = 1
                    sar[i] = ep[i-1]
                    ep[i] = high[i]
                    af[i] = af_start
                else:
                    trend[i] = -1
                    if low[i] < ep[i-1]:
                        ep[i] = low[i]
                        af[i] = min(af[i-1] + af_step, af_max)
                    else:
                        ep[i] = ep[i-1]
                        af[i] = af[i-1]
        
        return pd.Series(sar, index=df.index)
    
    @staticmethod
    def calculate_momentum(df: pd.DataFrame, period: int = 10) -> pd.Series:
        """计算动量指标 (Momentum)"""
        return df['close'] - df['close'].shift(period)
    
    @staticmethod
    def calculate_roc(df: pd.DataFrame, period: int = 10) -> pd.Series:
        """计算变动率指标 (ROC)"""
        return (df['close'] - df['close'].shift(period)) / df['close'].shift(period) * 100
    
    @staticmethod
    def calculate_bias(df: pd.DataFrame, period: int = 6) -> pd.Series:
        """计算乖离率 (BIAS)"""
        ma = df['close'].rolling(window=period).mean()
        return (df['close'] - ma) / ma * 100
    
    @staticmethod
    def calculate_dmi(df: pd.DataFrame, period: int = 14) -> Dict[str, pd.Series]:
        """计算趋向指标 (DMI) - 返回完整的DMI指标组"""
        adx, plus_di, minus_di = IndicatorCalculator.calculate_adx(df, period)
        return {
            'ADX': adx,
            'PDI': plus_di,
            'MDI': minus_di
        }
    
    @staticmethod
    def calculate_trix(df: pd.DataFrame, period: int = 12) -> pd.Series:
        """计算三重指数平滑移动平均 (TRIX)"""
        ema1 = df['close'].ewm(span=period, adjust=False).mean()
        ema2 = ema1.ewm(span=period, adjust=False).mean()
        ema3 = ema2.ewm(span=period, adjust=False).mean()
        trix = (ema3 - ema3.shift(1)) / ema3.shift(1) * 100
        return trix


class StrategyRuleEngine:
    """策略规则引擎"""
    
    def __init__(self):
        self.indicator_calculator = IndicatorCalculator()
        
    def prepare_dataframe(self, kline_data: List[Dict]) -> pd.DataFrame:
        """准备数据框架"""
        df = pd.DataFrame(kline_data)
        
        # 列名映射
        column_mapping = {
            '日期': 'date', '开盘': 'open', '收盘': 'close',
            '最高': 'high', '最低': 'low', '成交量': 'volume',
            '成交额': 'amount', '涨跌幅': 'change_pct'
        }
        
        for cn, en in column_mapping.items():
            if cn in df.columns:
                df[en] = df[cn]
        
        # 确保数值类型
        for col in ['open', 'close', 'high', 'low', 'volume']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # 确保日期类型
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date').reset_index(drop=True)
        
        return df
    
    def calculate_all_indicators(self, df: pd.DataFrame, strategy: Dict) -> pd.DataFrame:
        """根据策略计算所有需要的指标 - 完整版"""
        indicators = strategy.get('indicators', [])
        
        for ind in indicators:
            name = ind.get('name', '').upper()
            params = ind.get('params', {})
            
            try:
                if name == 'MA' or name == 'SMA':
                    period = params.get('period', 20)
                    df[f'MA{period}'] = self.indicator_calculator.calculate_ma(df, period)
                    
                elif name == 'EMA':
                    period = params.get('period', 20)
                    df[f'EMA{period}'] = self.indicator_calculator.calculate_ema(df, period)
                    
                elif name == 'WMA':
                    period = params.get('period', 20)
                    df[f'WMA{period}'] = self.indicator_calculator.calculate_wma(df, period)
                    
                elif name == 'RSI':
                    period = params.get('period', 14)
                    df[f'RSI{period}'] = self.indicator_calculator.calculate_rsi(df, period)
                    df['RSI'] = df[f'RSI{period}']  # 别名
                    
                elif name == 'MACD':
                    fast = params.get('fast', 12)
                    slow = params.get('slow', 26)
                    signal = params.get('signal', 9)
                    macd, signal_line, histogram = self.indicator_calculator.calculate_macd(df, fast, slow, signal)
                    df['MACD'] = macd
                    df['MACD_DIF'] = macd  # 别名
                    df['MACD_Signal'] = signal_line
                    df['MACD_DEA'] = signal_line  # 别名
                    df['MACD_Histogram'] = histogram
                    df['MACD_HIST'] = histogram  # 别名
                    
                elif name == 'BOLL' or name == 'BOLLINGER':
                    period = params.get('period', 20)
                    std = params.get('std', 2)
                    upper, middle, lower = self.indicator_calculator.calculate_bollinger(df, period, std)
                    df['BOLL_upper'] = upper
                    df['BOLL_middle'] = middle
                    df['BOLL_lower'] = lower
                    df['BOLL_UP'] = upper  # 别名
                    df['BOLL_MID'] = middle  # 别名
                    df['BOLL_DOWN'] = lower  # 别名
                    
                elif name == 'ATR':
                    period = params.get('period', 14)
                    df['ATR'] = self.indicator_calculator.calculate_atr(df, period)
                    df[f'ATR{period}'] = df['ATR']
                    
                elif name == 'ADX' or name == 'DMI':
                    period = params.get('period', 14)
                    adx, plus_di, minus_di = self.indicator_calculator.calculate_adx(df, period)
                    df['ADX'] = adx
                    df['PDI'] = plus_di
                    df['MDI'] = minus_di
                    df['+DI'] = plus_di  # 别名
                    df['-DI'] = minus_di  # 别名
                    
                elif name == 'KDJ':
                    k_period = params.get('k_period', 9)
                    d_period = params.get('d_period', 3)
                    j_period = params.get('j_period', 3)
                    k, d, j = self.indicator_calculator.calculate_kdj(df, k_period, d_period, j_period)
                    df['KDJ_K'] = k
                    df['KDJ_D'] = d
                    df['KDJ_J'] = j
                    df['K'] = k  # 别名
                    df['D'] = d  # 别名
                    df['J'] = j  # 别名
                    
                elif name == 'CCI':
                    period = params.get('period', 20)
                    df['CCI'] = self.indicator_calculator.calculate_cci(df, period)
                    df[f'CCI{period}'] = df['CCI']
                    
                elif name == 'WR' or name == 'WILLIAMS':
                    period = params.get('period', 14)
                    df['WR'] = self.indicator_calculator.calculate_williams_r(df, period)
                    df[f'WR{period}'] = df['WR']
                    
                elif name == 'OBV':
                    df['OBV'] = self.indicator_calculator.calculate_obv(df)
                    
                elif name == 'VOLUME' or name == 'VOL':
                    ma_period = params.get('ma_period', 5)
                    df['Volume_MA'] = self.indicator_calculator.calculate_volume_ma(df, ma_period)
                    df[f'VOL_MA{ma_period}'] = df['Volume_MA']
                    # 量比
                    df['Volume_Ratio'] = self.indicator_calculator.calculate_volume_ratio(df, ma_period)
                    
                elif name == 'DONCHIAN':
                    period = params.get('period', 20)
                    upper, middle, lower = self.indicator_calculator.calculate_donchian(df, period)
                    df['DC_upper'] = upper
                    df['DC_middle'] = middle
                    df['DC_lower'] = lower
                    
                elif name == 'SAR' or name == 'PSAR':
                    af_start = params.get('af_start', 0.02)
                    af_step = params.get('af_step', 0.02)
                    af_max = params.get('af_max', 0.2)
                    df['SAR'] = self.indicator_calculator.calculate_sar(df, af_start, af_step, af_max)
                    
                elif name == 'MOM' or name == 'MOMENTUM':
                    period = params.get('period', 10)
                    df['MOM'] = self.indicator_calculator.calculate_momentum(df, period)
                    df[f'MOM{period}'] = df['MOM']
                    
                elif name == 'ROC':
                    period = params.get('period', 10)
                    df['ROC'] = self.indicator_calculator.calculate_roc(df, period)
                    df[f'ROC{period}'] = df['ROC']
                    
                elif name == 'BIAS':
                    period = params.get('period', 6)
                    df['BIAS'] = self.indicator_calculator.calculate_bias(df, period)
                    df[f'BIAS{period}'] = df['BIAS']
                    
                elif name == 'TRIX':
                    period = params.get('period', 12)
                    df['TRIX'] = self.indicator_calculator.calculate_trix(df, period)
                    df[f'TRIX{period}'] = df['TRIX']
                    
            except Exception as e:
                logger.warning(f"计算指标 {name} 失败: {e}")
        
        # 添加常用指标（如果策略中没有明确指定）
        if 'MA5' not in df.columns:
            df['MA5'] = self.indicator_calculator.calculate_ma(df, 5)
        if 'MA10' not in df.columns:
            df['MA10'] = self.indicator_calculator.calculate_ma(df, 10)
        if 'MA20' not in df.columns:
            df['MA20'] = self.indicator_calculator.calculate_ma(df, 20)
        if 'MA60' not in df.columns:
            df['MA60'] = self.indicator_calculator.calculate_ma(df, 60)
        
        # 添加RSI（常用）
        if 'RSI14' not in df.columns and 'RSI' not in df.columns:
            df['RSI14'] = self.indicator_calculator.calculate_rsi(df, 14)
            df['RSI'] = df['RSI14']
        
        # 添加MACD（常用）
        if 'MACD' not in df.columns:
            macd, signal_line, histogram = self.indicator_calculator.calculate_macd(df)
            df['MACD'] = macd
            df['MACD_Signal'] = signal_line
            df['MACD_Histogram'] = histogram
        
        return df
    
    def get_indicator_value(self, df: pd.DataFrame, idx: int, indicator: str) -> Optional[float]:
        """获取指标值"""
        if indicator == 'price':
            return df.loc[idx, 'close'] if 'close' in df.columns else None
        elif indicator == 'Signal':
            return df.loc[idx, 'MACD_Signal'] if 'MACD_Signal' in df.columns else None
        elif indicator in df.columns:
            return df.loc[idx, indicator]
        return None
    
    def check_cross_above(self, df: pd.DataFrame, idx: int, indicator1: str, indicator2: str) -> bool:
        """检查上穿条件"""
        if idx < 1:
            return False
        
        val1_curr = self.get_indicator_value(df, idx, indicator1)
        val2_curr = self.get_indicator_value(df, idx, indicator2)
        val1_prev = self.get_indicator_value(df, idx - 1, indicator1)
        val2_prev = self.get_indicator_value(df, idx - 1, indicator2)
        
        if None in [val1_curr, val2_curr, val1_prev, val2_prev]:
            return False
        
        return val1_prev <= val2_prev and val1_curr > val2_curr
    
    def check_cross_below(self, df: pd.DataFrame, idx: int, indicator1: str, indicator2: str) -> bool:
        """检查下穿条件"""
        if idx < 1:
            return False
        
        val1_curr = self.get_indicator_value(df, idx, indicator1)
        val2_curr = self.get_indicator_value(df, idx, indicator2)
        val1_prev = self.get_indicator_value(df, idx - 1, indicator1)
        val2_prev = self.get_indicator_value(df, idx - 1, indicator2)
        
        if None in [val1_curr, val2_curr, val1_prev, val2_prev]:
            return False
        
        return val1_prev >= val2_prev and val1_curr < val2_curr
    
    def evaluate_condition(self, df: pd.DataFrame, idx: int, condition: Dict) -> Tuple[bool, str]:
        """评估单个条件"""
        indicator = condition.get('indicator', '')
        operator = condition.get('operator', '')
        value = condition.get('value')
        description = condition.get('description', '')
        
        # 获取指标值
        ind_value = self.get_indicator_value(df, idx, indicator)
        
        if ind_value is None:
            return False, f"指标 {indicator} 无数据"
        
        # 处理比较值
        if isinstance(value, str):
            compare_value = self.get_indicator_value(df, idx, value)
            if compare_value is None:
                return False, f"比较指标 {value} 无数据"
        else:
            compare_value = float(value) if value is not None else 0
        
        # 评估条件
        result = False
        
        if operator == '>':
            result = ind_value > compare_value
        elif operator == '<':
            result = ind_value < compare_value
        elif operator == '>=':
            result = ind_value >= compare_value
        elif operator == '<=':
            result = ind_value <= compare_value
        elif operator == '==':
            result = abs(ind_value - compare_value) < 0.0001
        elif operator == 'cross_above':
            result = self.check_cross_above(df, idx, indicator, value)
        elif operator == 'cross_below':
            result = self.check_cross_below(df, idx, indicator, value)
        
        return result, description if result else ""
    
    def evaluate_entry_conditions(self, df: pd.DataFrame, idx: int, strategy: Dict) -> Tuple[bool, List[str], float]:
        """评估入场条件"""
        entry_conditions = strategy.get('entry_conditions', [])
        
        if not entry_conditions:
            return False, [], 0.0
        
        met_conditions = []
        total_weight = 0
        weighted_score = 0
        
        for cond in entry_conditions:
            weight = cond.get('weight', 1.0)
            total_weight += weight
            
            result, desc = self.evaluate_condition(df, idx, cond)
            if result:
                met_conditions.append(desc)
                weighted_score += weight
        
        # 计算置信度
        confidence = weighted_score / total_weight if total_weight > 0 else 0
        
        # 所有条件都满足才触发信号
        all_met = len(met_conditions) == len(entry_conditions)
        
        return all_met, met_conditions, confidence
    
    def evaluate_exit_conditions(self, df: pd.DataFrame, idx: int, strategy: Dict) -> Tuple[bool, List[str], float]:
        """评估出场条件"""
        exit_conditions = strategy.get('exit_conditions', [])
        
        if not exit_conditions:
            return False, [], 0.0
        
        met_conditions = []
        
        for cond in exit_conditions:
            result, desc = self.evaluate_condition(df, idx, cond)
            if result:
                met_conditions.append(desc)
        
        # 任一出场条件满足即触发
        any_met = len(met_conditions) > 0
        confidence = len(met_conditions) / len(exit_conditions)
        
        return any_met, met_conditions, confidence
    
    def generate_signal_at_point(self, df: pd.DataFrame, idx: int, strategy: Dict, current_position: str = "none") -> Optional[TradeSignal]:
        """在指定点位生成信号"""
        if idx < 60:  # 需要足够的历史数据计算指标
            return None
        
        current_price = df.loc[idx, 'close']
        current_date = df.loc[idx, 'date'] if 'date' in df.columns else datetime.now()
        
        # 收集当前指标值
        indicators = {}
        for col in df.columns:
            if col not in ['date', 'open', 'close', 'high', 'low', 'volume', 'amount', 'change_pct']:
                val = df.loc[idx, col]
                if pd.notna(val):
                    indicators[col] = round(float(val), 4)
        
        risk_params = strategy.get('risk_params', {})
        
        # 如果没有持仓，检查入场条件
        if current_position == "none":
            entry_met, entry_conditions, entry_confidence = self.evaluate_entry_conditions(df, idx, strategy)
            
            if entry_met:
                stop_loss = current_price * (1 - risk_params.get('stop_loss', 0.05))
                take_profit = current_price * (1 + risk_params.get('take_profit', 0.15))
                
                return TradeSignal(
                    signal_type=SignalType.BUY,
                    timestamp=current_date,
                    price=current_price,
                    confidence=entry_confidence,
                    conditions_met=entry_conditions,
                    indicators=indicators,
                    stop_loss=round(stop_loss, 2),
                    take_profit=round(take_profit, 2),
                    reason=f"满足入场条件: {', '.join(entry_conditions)}"
                )
        
        # 如果有持仓，检查出场条件
        elif current_position == "long":
            exit_met, exit_conditions, exit_confidence = self.evaluate_exit_conditions(df, idx, strategy)
            
            if exit_met:
                return TradeSignal(
                    signal_type=SignalType.SELL,
                    timestamp=current_date,
                    price=current_price,
                    confidence=exit_confidence,
                    conditions_met=exit_conditions,
                    indicators=indicators,
                    reason=f"满足出场条件: {', '.join(exit_conditions)}"
                )
        
        return None
    
    def find_all_signals(self, df: pd.DataFrame, strategy: Dict) -> List[TradeSignal]:
        """在整个数据集中找出所有信号点"""
        signals = []
        current_position = "none"
        
        for idx in range(60, len(df)):
            signal = self.generate_signal_at_point(df, idx, strategy, current_position)
            
            if signal:
                signals.append(signal)
                
                if signal.signal_type == SignalType.BUY:
                    current_position = "long"
                elif signal.signal_type == SignalType.SELL:
                    current_position = "none"
        
        return signals
    
    def backtest(self, kline_data: List[Dict], strategy: Dict, initial_capital: float = 100000) -> BacktestResult:
        """执行回测"""
        # 准备数据
        df = self.prepare_dataframe(kline_data)
        df = self.calculate_all_indicators(df, strategy)
        
        # 找出所有信号
        signals = self.find_all_signals(df, strategy)
        
        # 构建交易记录
        trades = []
        current_trade = None
        capital = initial_capital
        peak_capital = initial_capital
        max_drawdown = 0
        
        for signal in signals:
            if signal.signal_type == SignalType.BUY and current_trade is None:
                current_trade = BacktestTrade(
                    entry_date=signal.timestamp,
                    entry_price=signal.price,
                    entry_signal=signal
                )
            elif signal.signal_type == SignalType.SELL and current_trade is not None:
                current_trade.exit_date = signal.timestamp
                current_trade.exit_price = signal.price
                current_trade.exit_signal = signal
                current_trade.profit_pct = (signal.price - current_trade.entry_price) / current_trade.entry_price
                current_trade.status = "closed"
                
                # 更新资金
                capital *= (1 + current_trade.profit_pct)
                peak_capital = max(peak_capital, capital)
                drawdown = (peak_capital - capital) / peak_capital
                max_drawdown = max(max_drawdown, drawdown)
                
                trades.append(current_trade)
                current_trade = None
        
        # 如果还有未平仓的交易
        if current_trade is not None:
            current_trade.status = "open"
            trades.append(current_trade)
        
        # 计算统计数据
        closed_trades = [t for t in trades if t.status == "closed"]
        winning_trades = [t for t in closed_trades if t.profit_pct > 0]
        losing_trades = [t for t in closed_trades if t.profit_pct <= 0]
        
        total_return = (capital - initial_capital) / initial_capital if closed_trades else 0
        win_rate = len(winning_trades) / len(closed_trades) if closed_trades else 0
        
        # 构建买卖信号列表
        buy_signals = []
        sell_signals = []
        
        for signal in signals:
            signal_dict = {
                "date": signal.timestamp.strftime("%Y-%m-%d") if isinstance(signal.timestamp, datetime) else str(signal.timestamp),
                "price": signal.price,
                "confidence": signal.confidence,
                "conditions": signal.conditions_met,
                "reason": signal.reason
            }
            
            if signal.signal_type == SignalType.BUY:
                signal_dict["stop_loss"] = signal.stop_loss
                signal_dict["take_profit"] = signal.take_profit
                buy_signals.append(signal_dict)
            else:
                sell_signals.append(signal_dict)
        
        return BacktestResult(
            strategy_id=strategy.get('id', ''),
            strategy_name=strategy.get('name', ''),
            stock_code=strategy.get('stock_code', ''),
            start_date=df['date'].iloc[0] if 'date' in df.columns else datetime.now(),
            end_date=df['date'].iloc[-1] if 'date' in df.columns else datetime.now(),
            trades=trades,
            total_trades=len(closed_trades),
            winning_trades=len(winning_trades),
            losing_trades=len(losing_trades),
            win_rate=win_rate,
            total_return=total_return,
            max_drawdown=max_drawdown,
            buy_signals=buy_signals,
            sell_signals=sell_signals
        )
    
    def analyze_current_state(self, kline_data: List[Dict], strategy: Dict) -> Dict[str, Any]:
        """分析当前状态，判断是否有交易机会"""
        df = self.prepare_dataframe(kline_data)
        df = self.calculate_all_indicators(df, strategy)
        
        if len(df) < 60:
            return {
                "has_signal": False,
                "signal_type": "HOLD",
                "reason": "数据不足，需要至少60根K线"
            }
        
        idx = len(df) - 1
        current_price = df.loc[idx, 'close']
        
        # 收集当前指标值
        indicators = {}
        for col in df.columns:
            if col not in ['date', 'open', 'close', 'high', 'low', 'volume', 'amount', 'change_pct']:
                val = df.loc[idx, col]
                if pd.notna(val):
                    indicators[col] = round(float(val), 4)
        
        # 检查入场条件
        entry_met, entry_conditions, entry_confidence = self.evaluate_entry_conditions(df, idx, strategy)
        
        # 检查出场条件
        exit_met, exit_conditions, exit_confidence = self.evaluate_exit_conditions(df, idx, strategy)
        
        # 检查各个条件的状态
        entry_condition_status = []
        for cond in strategy.get('entry_conditions', []):
            result, desc = self.evaluate_condition(df, idx, cond)
            entry_condition_status.append({
                "description": cond.get('description', ''),
                "indicator": cond.get('indicator', ''),
                "operator": cond.get('operator', ''),
                "value": cond.get('value'),
                "met": result
            })
        
        exit_condition_status = []
        for cond in strategy.get('exit_conditions', []):
            result, desc = self.evaluate_condition(df, idx, cond)
            exit_condition_status.append({
                "description": cond.get('description', ''),
                "indicator": cond.get('indicator', ''),
                "operator": cond.get('operator', ''),
                "value": cond.get('value'),
                "met": result
            })
        
        risk_params = strategy.get('risk_params', {})
        
        result = {
            "has_signal": entry_met or exit_met,
            "signal_type": "BUY" if entry_met else ("SELL" if exit_met else "HOLD"),
            "current_price": current_price,
            "indicators": indicators,
            "entry_analysis": {
                "all_conditions_met": entry_met,
                "conditions_met": entry_conditions,
                "confidence": entry_confidence,
                "condition_status": entry_condition_status
            },
            "exit_analysis": {
                "any_condition_met": exit_met,
                "conditions_met": exit_conditions,
                "confidence": exit_confidence,
                "condition_status": exit_condition_status
            },
            "trade_suggestion": None
        }
        
        if entry_met:
            stop_loss = current_price * (1 - risk_params.get('stop_loss', 0.05))
            take_profit = current_price * (1 + risk_params.get('take_profit', 0.15))
            
            result["trade_suggestion"] = {
                "action": "BUY",
                "price": current_price,
                "stop_loss": round(stop_loss, 2),
                "take_profit": round(take_profit, 2),
                "position_size": risk_params.get('max_position', 0.30),
                "reason": f"满足入场条件: {', '.join(entry_conditions)}"
            }
        elif exit_met:
            result["trade_suggestion"] = {
                "action": "SELL",
                "price": current_price,
                "reason": f"满足出场条件: {', '.join(exit_conditions)}"
            }
        
        return result


# 创建全局实例
strategy_rule_engine = StrategyRuleEngine()


def get_strategy_rule_engine() -> StrategyRuleEngine:
    """获取策略规则引擎实例"""
    return strategy_rule_engine