#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
问财(pywencai)数据源 Provider
提供主力资金、季报数据、智能选股等功能

功能：
1. 主力资金净流入排名
2. 季报财务数据
3. 自然语言智能选股
4. 行业板块分析

依赖：pip install pywencai
"""

import logging
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# 尝试导入pywencai
try:
    import pywencai
    PYWENCAI_AVAILABLE = True
except ImportError:
    PYWENCAI_AVAILABLE = False
    logger.warning("pywencai未安装，问财数据源不可用。请运行: pip install pywencai")


class WencaiProvider:
    """问财数据源Provider"""

    def __init__(self):
        """初始化问财数据源"""
        self.available = PYWENCAI_AVAILABLE
        if not self.available:
            logger.warning("pywencai未安装，问财功能不可用")

    def is_available(self) -> bool:
        """检查问财服务是否可用"""
        return self.available

    def query(self, query_text: str, loop: bool = True) -> Optional[pd.DataFrame]:
        """
        执行问财自然语言查询

        Args:
            query_text: 自然语言查询语句
            loop: 是否循环获取所有数据

        Returns:
            查询结果DataFrame
        """
        if not self.available:
            logger.error("pywencai未安装")
            return None

        try:
            logger.info(f"问财查询: {query_text[:50]}...")
            result = pywencai.get(query=query_text, loop=loop)

            if result is None:
                logger.warning("问财查询返回None")
                return None

            # 转换为DataFrame
            df = self._convert_to_dataframe(result)
            if df is not None and not df.empty:
                logger.info(f"问财查询成功，返回{len(df)}条数据")
            return df

        except Exception as e:
            logger.error(f"问财查询失败: {e}")
            return None

    def get_main_force_stocks(self, start_date: str = None, days_ago: int = 30,
                              min_market_cap: float = 50, max_market_cap: float = 2000,
                              top_n: int = 100) -> Tuple[bool, Optional[pd.DataFrame], str]:
        """
        获取主力资金净流入排名股票

        Args:
            start_date: 开始日期，格式如"2025年1月1日"
            days_ago: 距今多少天（如果start_date为空则使用）
            min_market_cap: 最小市值（亿）
            max_market_cap: 最大市值（亿）
            top_n: 返回前N名

        Returns:
            (success, dataframe, message)
        """
        if not self.available:
            return False, None, "pywencai未安装"

        try:
            # 计算开始日期
            if not start_date:
                date_obj = datetime.now() - timedelta(days=days_ago)
                start_date = f"{date_obj.year}年{date_obj.month}月{date_obj.day}日"

            logger.info(f"获取主力资金数据，开始日期: {start_date}")

            # 构建查询语句（多个备选方案）
            queries = [
                # 方案1: 完整查询
                f"{start_date}以来主力资金净流入排名前{top_n}名，并计算区间涨跌幅，"
                f"市值{min_market_cap}-{max_market_cap}亿之间，非科创非st，"
                f"所属同花顺行业，总市值，净利润，营收，市盈率，市净率，"
                f"盈利能力评分，成长能力评分",

                # 方案2: 简化查询
                f"{start_date}以来主力资金净流入，并计算区间涨跌幅，"
                f"市值{min_market_cap}-{max_market_cap}亿，非科创非st，"
                f"所属同花顺行业，总市值，净利润，营收，市盈率，市净率",

                # 方案3: 基础查询
                f"{start_date}以来主力资金净流入排名前{top_n}名，并计算区间涨跌幅，"
                f"市值{min_market_cap}-{max_market_cap}亿，非st非科创板，所属行业，总市值",
            ]

            # 尝试不同的查询方案
            for i, query in enumerate(queries, 1):
                logger.info(f"尝试查询方案 {i}/{len(queries)}")
                try:
                    result = pywencai.get(query=query, loop=True)
                    df = self._convert_to_dataframe(result)

                    if df is not None and not df.empty:
                        logger.info(f"方案{i}成功，获取{len(df)}只股票")
                        return True, df, f"成功获取{len(df)}只股票数据"

                except Exception as e:
                    logger.warning(f"方案{i}失败: {e}")
                    continue

            return False, None, "所有查询方案都失败"

        except Exception as e:
            error_msg = f"获取主力资金数据失败: {e}"
            logger.error(error_msg)
            return False, None, error_msg

    def get_quarterly_report(self, symbol: str) -> Optional[Dict]:
        """
        获取股票季报数据

        Args:
            symbol: 股票代码

        Returns:
            季报数据字典
        """
        if not self.available:
            return None

        try:
            # 查询最新季报数据
            query = f"{symbol}最新季报，营业收入，净利润，毛利率，净利率，ROE，资产负债率"
            result = pywencai.get(query=query, loop=False)
            df = self._convert_to_dataframe(result)

            if df is None or df.empty:
                return None

            # 转换为字典
            row = df.iloc[0]
            return {
                'symbol': symbol,
                'revenue': self._safe_get(row, '营业收入', '营收'),
                'net_profit': self._safe_get(row, '净利润'),
                'gross_margin': self._safe_get(row, '毛利率'),
                'net_margin': self._safe_get(row, '净利率'),
                'roe': self._safe_get(row, 'ROE', '净资产收益率'),
                'debt_ratio': self._safe_get(row, '资产负债率'),
                'report_date': self._safe_get(row, '报告期'),
                'data_source': 'wencai'
            }

        except Exception as e:
            logger.error(f"获取季报数据失败: {e}")
            return None

    def get_financial_scores(self, symbol: str) -> Optional[Dict]:
        """
        获取股票财务评分

        Args:
            symbol: 股票代码

        Returns:
            财务评分字典
        """
        if not self.available:
            return None

        try:
            query = f"{symbol}盈利能力评分，成长能力评分，营运能力评分，偿债能力评分，现金流评分"
            result = pywencai.get(query=query, loop=False)
            df = self._convert_to_dataframe(result)

            if df is None or df.empty:
                return None

            row = df.iloc[0]
            return {
                'symbol': symbol,
                'profitability_score': self._safe_get(row, '盈利能力评分'),
                'growth_score': self._safe_get(row, '成长能力评分'),
                'operation_score': self._safe_get(row, '营运能力评分'),
                'solvency_score': self._safe_get(row, '偿债能力评分'),
                'cashflow_score': self._safe_get(row, '现金流评分'),
                'data_source': 'wencai'
            }

        except Exception as e:
            logger.error(f"获取财务评分失败: {e}")
            return None

    def get_industry_stocks(self, industry: str, top_n: int = 20) -> Optional[pd.DataFrame]:
        """
        获取行业内股票

        Args:
            industry: 行业名称
            top_n: 返回数量

        Returns:
            行业股票DataFrame
        """
        if not self.available:
            return None

        try:
            query = f"{industry}行业股票，市值排名前{top_n}，总市值，市盈率，涨跌幅"
            result = pywencai.get(query=query, loop=False)
            return self._convert_to_dataframe(result)

        except Exception as e:
            logger.error(f"获取行业股票失败: {e}")
            return None

    def get_hot_sectors(self, days: int = 5) -> Optional[pd.DataFrame]:
        """
        获取热门板块

        Args:
            days: 统计天数

        Returns:
            热门板块DataFrame
        """
        if not self.available:
            return None

        try:
            query = f"最近{days}日涨幅最大的行业板块，板块涨跌幅，成交额，主力资金净流入"
            result = pywencai.get(query=query, loop=False)
            return self._convert_to_dataframe(result)

        except Exception as e:
            logger.error(f"获取热门板块失败: {e}")
            return None

    def get_fund_flow_ranking(self, days: int = 5, top_n: int = 50) -> Optional[pd.DataFrame]:
        """
        获取资金流向排名

        Args:
            days: 统计天数
            top_n: 返回数量

        Returns:
            资金流向排名DataFrame
        """
        if not self.available:
            return None

        try:
            query = f"最近{days}日主力资金净流入排名前{top_n}，主力资金净流入，涨跌幅，所属行业"
            result = pywencai.get(query=query, loop=False)
            return self._convert_to_dataframe(result)

        except Exception as e:
            logger.error(f"获取资金流向排名失败: {e}")
            return None

    def smart_stock_selection(self, conditions: str) -> Optional[pd.DataFrame]:
        """
        智能选股

        Args:
            conditions: 选股条件（自然语言）

        Returns:
            选股结果DataFrame

        示例:
            conditions = "市盈率小于20，ROE大于15%，近5日涨幅小于10%"
        """
        if not self.available:
            return None

        try:
            query = f"{conditions}，股票代码，股票简称，所属行业，总市值，市盈率"
            result = pywencai.get(query=query, loop=True)
            return self._convert_to_dataframe(result)

        except Exception as e:
            logger.error(f"智能选股失败: {e}")
            return None

    def filter_stocks(self, df: pd.DataFrame,
                      max_change_pct: float = None,
                      min_market_cap: float = None,
                      max_market_cap: float = None,
                      exclude_st: bool = True) -> pd.DataFrame:
        """
        筛选股票

        Args:
            df: 原始数据
            max_change_pct: 最大涨跌幅
            min_market_cap: 最小市值（亿）
            max_market_cap: 最大市值（亿）
            exclude_st: 是否排除ST股票

        Returns:
            筛选后的DataFrame
        """
        if df is None or df.empty:
            return df

        filtered = df.copy()

        # 筛选涨跌幅
        if max_change_pct is not None:
            change_col = self._find_column(filtered, ['区间涨跌幅', '涨跌幅'])
            if change_col:
                filtered[change_col] = pd.to_numeric(filtered[change_col], errors='coerce')
                filtered = filtered[filtered[change_col] < max_change_pct]

        # 筛选市值
        market_cap_col = self._find_column(filtered, ['总市值', '市值'])
        if market_cap_col:
            filtered[market_cap_col] = pd.to_numeric(filtered[market_cap_col], errors='coerce')

            # 判断单位（如果值很大，可能是元）
            max_val = filtered[market_cap_col].max()
            if max_val > 100000:  # 大于10万，认为是元
                filtered[market_cap_col] = filtered[market_cap_col] / 100000000

            if min_market_cap is not None:
                filtered = filtered[filtered[market_cap_col] >= min_market_cap]
            if max_market_cap is not None:
                filtered = filtered[filtered[market_cap_col] <= max_market_cap]

        # 排除ST股票
        if exclude_st:
            name_col = self._find_column(filtered, ['股票简称', '名称'])
            if name_col:
                filtered = filtered[~filtered[name_col].str.contains('ST', na=False)]

        return filtered

    # ========== 私有方法 ==========

    def _convert_to_dataframe(self, result) -> Optional[pd.DataFrame]:
        """转换问财返回结果为DataFrame"""
        try:
            if isinstance(result, pd.DataFrame):
                return result
            elif isinstance(result, dict):
                if 'tableV1' in result:
                    table_data = result['tableV1']
                    if isinstance(table_data, pd.DataFrame):
                        return table_data
                    elif isinstance(table_data, list):
                        return pd.DataFrame(table_data)
                return pd.DataFrame([result])
            elif isinstance(result, list):
                return pd.DataFrame(result)
            else:
                return None
        except Exception as e:
            logger.error(f"转换DataFrame失败: {e}")
            return None

    def _safe_get(self, row, *keys):
        """安全获取行数据"""
        for key in keys:
            # 精确匹配
            if key in row.index:
                return row[key]
            # 模糊匹配
            for col in row.index:
                if key in col:
                    return row[col]
        return None

    def _find_column(self, df: pd.DataFrame, patterns: List[str]) -> Optional[str]:
        """查找匹配的列名"""
        for pattern in patterns:
            for col in df.columns:
                if pattern in col:
                    return col
        return None


# 全局单例
_wencai_provider = None

def get_wencai_provider() -> WencaiProvider:
    """获取问财Provider单例"""
    global _wencai_provider
    if _wencai_provider is None:
        _wencai_provider = WencaiProvider()
    return _wencai_provider


if __name__ == '__main__':
    # 测试代码
    logging.basicConfig(level=logging.INFO)

    provider = get_wencai_provider()

    if provider.is_available():
        print("问财服务可用")

        # 测试主力资金查询
        success, df, msg = provider.get_main_force_stocks(days_ago=10, top_n=20)
        if success:
            print(f"主力资金数据: {len(df)}条")
            print(df.head())

        # 测试智能选股
        result = provider.smart_stock_selection("市盈率小于30，ROE大于10%")
        if result is not None:
            print(f"智能选股结果: {len(result)}条")
    else:
        print("问财服务不可用，请安装pywencai: pip install pywencai")
