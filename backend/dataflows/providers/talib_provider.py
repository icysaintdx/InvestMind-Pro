#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

try:
    import talib
    TALIB_AVAILABLE = True
except ImportError:
    TALIB_AVAILABLE = False

class TALibProvider:
    def __init__(self):
        self.available = TALIB_AVAILABLE

    def is_available(self):
        return self.available

    def calculate_ma(self, close, periods=None):
        if periods is None:
            periods = [5, 10, 20, 60]
        result = {}
        for period in periods:
            if self.available:
                result[f"MA{period}"] = talib.MA(close, timeperiod=period)
            else:
                result[f"MA{period}"] = pd.Series(close).rolling(window=period).mean().values
        return result

    def calculate_macd(self, close, fast=12, slow=26, signal=9):
        if self.available:
            dif, dea, macd = talib.MACD(close, fastperiod=fast, slowperiod=slow, signalperiod=signal)
            return {"DIF": dif, "DEA": dea, "MACD": macd * 2}
        ema_fast = pd.Series(close).ewm(span=fast, adjust=False).mean()
        ema_slow = pd.Series(close).ewm(span=slow, adjust=False).mean()
        dif = ema_fast - ema_slow
        dea = dif.ewm(span=signal, adjust=False).mean()
        macd = (dif - dea) * 2
        return {"DIF": dif.values, "DEA": dea.values, "MACD": macd.values}

    def calculate_rsi(self, close, periods=None):
        if periods is None:
            periods = [6, 12, 24]
        result = {}
        for period in periods:
            if self.available:
                result[f"RSI{period}"] = talib.RSI(close, timeperiod=period)
            else:
                delta = pd.Series(close).diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
                rs = gain / loss
                result[f"RSI{period}"] = (100 - (100 / (1 + rs))).values
        return result

    def calculate_kdj(self, high, low, close, n=9, m1=3, m2=3):
        if self.available:
            k, d = talib.STOCH(high, low, close, fastk_period=n, slowk_period=m1, slowd_period=m2)
            j = 3 * k - 2 * d
            return {"K": k, "D": d, "J": j}
        low_list = pd.Series(low).rolling(window=n).min()
        high_list = pd.Series(high).rolling(window=n).max()
        rsv = (pd.Series(close) - low_list) / (high_list - low_list) * 100
        k = rsv.ewm(com=m1-1, adjust=False).mean()
        d = k.ewm(com=m2-1, adjust=False).mean()
        j = 3 * k - 2 * d
        return {"K": k.values, "D": d.values, "J": j.values}

    def calculate_bollinger(self, close, period=20, nbdev=2):
        if self.available:
            upper, middle, lower = talib.BBANDS(close, timeperiod=period, nbdevup=nbdev, nbdevdn=nbdev)
            return {"upper": upper, "middle": middle, "lower": lower}
        close_s = pd.Series(close)
        middle = close_s.rolling(window=period).mean()
        std = close_s.rolling(window=period).std()
        return {"upper": (middle + nbdev * std).values, "middle": middle.values, "lower": (middle - nbdev * std).values}

    def calculate_all_indicators(self, df):
        result = df.copy()
        close = df["close"].values.astype(float)
        high = df["high"].values.astype(float)
        low = df["low"].values.astype(float)
        for key, value in self.calculate_ma(close).items():
            result[key] = value
        macd_result = self.calculate_macd(close)
        result["MACD_DIF"] = macd_result["DIF"]
        result["MACD_DEA"] = macd_result["DEA"]
        result["MACD"] = macd_result["MACD"]
        for key, value in self.calculate_rsi(close).items():
            result[key] = value
        kdj_result = self.calculate_kdj(high, low, close)
        result["KDJ_K"] = kdj_result["K"]
        result["KDJ_D"] = kdj_result["D"]
        result["KDJ_J"] = kdj_result["J"]
        boll_result = self.calculate_bollinger(close)
        result["BOLL_UPPER"] = boll_result["upper"]
        result["BOLL_MID"] = boll_result["middle"]
        result["BOLL_LOWER"] = boll_result["lower"]
        return result

_talib_provider = None

def get_talib_provider():
    global _talib_provider
    if _talib_provider is None:
        _talib_provider = TALibProvider()
    return _talib_provider
