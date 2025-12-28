#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
问财智能选股服务
使用pywencai进行自然语言股票筛选
整合了 aiagents-stock 中的选股策略
"""

import logging
import math
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


def clean_for_json(obj: Any) -> Any:
    """
    清理数据使其可以被JSON序列化
    
    处理:
    - inf -> None
    - -inf -> None
    - nan -> None
    - numpy类型 -> Python原生类型
    """
    if obj is None:
        return None
    
    # 处理numpy类型
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        if np.isnan(obj) or np.isinf(obj):
            return None
        return float(obj)
    if isinstance(obj, np.ndarray):
        return [clean_for_json(item) for item in obj.tolist()]
    
    # 处理Python float
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    
    # 处理字典
    if isinstance(obj, dict):
        return {k: clean_for_json(v) for k, v in obj.items()}
    
    # 处理列表
    if isinstance(obj, list):
        return [clean_for_json(item) for item in obj]
    
    # 处理pandas Timestamp
    if isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    
    # 处理datetime
    if isinstance(obj, datetime):
        return obj.isoformat()
    
    return obj


class WencaiStockSelector:
    """问财智能选股器"""

    def __init__(self):
        self._pywencai = None
        self._available = None

    @property
    def is_available(self) -> bool:
        """检查pywencai是否可用"""
        if self._available is None:
            try:
                import pywencai
                self._pywencai = pywencai
                self._available = True
                logger.info("pywencai 模块加载成功")
            except ImportError:
                self._available = False
                logger.warning("pywencai 模块未安装，智能选股功能不可用")
        return self._available

    def query(self, query_text: str, top_n: int = 50) -> Dict[str, Any]:
        """
        执行问财查询

        Args:
            query_text: 自然语言查询条件
            top_n: 返回前N条结果

        Returns:
            查询结果
        """
        if not self.is_available:
            return {
                'success': False,
                'message': 'pywencai模块未安装，请执行: pip install pywencai',
                'data': []
            }

        try:
            logger.info(f"[问财选股] 执行查询: {query_text}")

            result = self._pywencai.get(query=query_text, loop=True)

            if result is None or (hasattr(result, 'empty') and result.empty):
                return {
                    'success': True,
                    'message': '未找到符合条件的股票',
                    'data': [],
                    'count': 0
                }

            # 转换为列表格式
            if isinstance(result, pd.DataFrame):
                if len(result) > top_n:
                    result = result.head(top_n)
                
                # 替换inf和nan值为None
                result = result.replace([np.inf, -np.inf], np.nan)
                
                # 转换为字典列表
                data_list = result.to_dict('records')
                
                # 清理数据使其可以被JSON序列化
                data_list = clean_for_json(data_list)
                
                columns = list(result.columns)
            else:
                data_list = result if isinstance(result, list) else [result]
                data_list = clean_for_json(data_list)
                columns = []

            logger.info(f"[问财选股] 获取到 {len(data_list)} 条结果")

            return {
                'success': True,
                'message': f'成功获取 {len(data_list)} 只股票',
                'data': data_list,
                'count': len(data_list),
                'columns': columns
            }

        except Exception as e:
            logger.error(f"[问财选股] 查询失败: {e}")
            return {
                'success': False,
                'message': f'查询失败: {str(e)}',
                'data': []
            }

    # ==================== aiagents-stock 精选策略 ====================
    # 以下策略来自 aiagents-stock 项目，经过优化筛选，返回精选股票

    def get_main_force_stocks_v2(self, top_n: int = 5, days_ago: int = 90,
                                  min_market_cap: float = 50, max_market_cap: float = 5000,
                                  max_range_change: float = 30) -> Dict[str, Any]:
        """
        主力选股 (aiagents-stock 版本)
        
        获取主力资金净流入排名靠前的股票，并进行智能筛选
        
        筛选条件：
        - 指定日期以来主力资金净流入排名
        - 区间涨跌幅 < max_range_change% (避免追高)
        - 市值范围: min_market_cap - max_market_cap 亿
        - 非ST、非科创板
        
        Args:
            top_n: 返回前N只股票 (默认5只)
            days_ago: 距今多少天 (默认90天，即3个月)
            min_market_cap: 最小市值(亿) (默认50亿)
            max_market_cap: 最大市值(亿) (默认5000亿)
            max_range_change: 最大涨跌幅(%) (默认30%)
            
        Returns:
            筛选后的股票数据
        """
        if not self.is_available:
            return {
                'success': False,
                'message': 'pywencai模块未安装',
                'data': []
            }
        
        try:
            # 计算开始日期
            date_obj = datetime.now() - timedelta(days=days_ago)
            start_date = f"{date_obj.year}年{date_obj.month}月{date_obj.day}日"
            
            logger.info(f"[主力选股V2] 开始日期: {start_date}, 市值范围: {min_market_cap}-{max_market_cap}亿")
            
            # 构建查询语句 - 使用多个备选方案
            queries = [
                # 方案1: 完整查询
                f"{start_date}以来主力资金净流入排名，并计算区间涨跌幅，市值{min_market_cap}-{max_market_cap}亿之间，非科创非st，"
                f"所属同花顺行业，总市值，净利润，营收，市盈率，市净率",
                
                # 方案2: 简化查询
                f"{start_date}以来主力资金净流入，并计算区间涨跌幅，市值{min_market_cap}-{max_market_cap}亿，非科创非st，"
                f"所属同花顺行业，总市值",
                
                # 方案3: 基础查询
                f"{start_date}以来主力资金净流入排名，并计算区间涨跌幅，市值{min_market_cap}-{max_market_cap}亿，非科创非st，"
                f"所属行业，总市值",
                
                # 方案4: 最简查询
                f"{start_date}以来主力资金净流入前100名，并计算区间涨跌幅，市值{min_market_cap}-{max_market_cap}亿，非st非科创板，所属行业，总市值",
            ]
            
            df_result = None
            
            # 尝试不同的查询方案
            for i, query in enumerate(queries, 1):
                logger.info(f"[主力选股V2] 尝试方案 {i}/{len(queries)}")
                
                try:
                    result = self._pywencai.get(query=query, loop=True)
                    
                    if result is None:
                        continue
                    
                    if isinstance(result, pd.DataFrame) and not result.empty:
                        df_result = result
                        logger.info(f"[主力选股V2] 方案{i}成功，获取到 {len(df_result)} 只股票")
                        break
                    
                except Exception as e:
                    logger.warning(f"[主力选股V2] 方案{i}失败: {e}")
                    continue
            
            if df_result is None or df_result.empty:
                return {
                    'success': False,
                    'message': '未获取到符合条件的股票',
                    'data': []
                }
            
            # 智能筛选 - 过滤区间涨跌幅
            filtered_df = df_result.copy()
            
            # 查找区间涨跌幅列
            interval_pct_col = None
            possible_names = [
                '区间涨跌幅:前复权', '区间涨跌幅:前复权(%)', '区间涨跌幅(%)', 
                '区间涨跌幅', '涨跌幅:前复权', '涨跌幅:前复权(%)', '涨跌幅(%)', '涨跌幅'
            ]
            for name in possible_names:
                for col in df_result.columns:
                    if name in col:
                        interval_pct_col = col
                        break
                if interval_pct_col:
                    break
            
            if interval_pct_col:
                filtered_df[interval_pct_col] = pd.to_numeric(filtered_df[interval_pct_col], errors='coerce')
                filtered_df = filtered_df[
                    (filtered_df[interval_pct_col].notna()) & 
                    (filtered_df[interval_pct_col] < max_range_change)
                ]
                logger.info(f"[主力选股V2] 涨跌幅筛选后: {len(filtered_df)} 只")
            
            # 去除ST股票
            if '股票简称' in filtered_df.columns:
                filtered_df = filtered_df[~filtered_df['股票简称'].str.contains('ST', na=False)]
            
            # 按主力资金净流入排序并取前N名
            main_fund_col = None
            main_fund_patterns = ['区间主力资金流向', '区间主力资金净流入', '主力资金流向', '主力资金净流入', '主力净流入']
            for pattern in main_fund_patterns:
                matching = [col for col in filtered_df.columns if pattern in col]
                if matching:
                    main_fund_col = matching[0]
                    break
            
            if main_fund_col:
                filtered_df[main_fund_col] = pd.to_numeric(filtered_df[main_fund_col], errors='coerce')
                filtered_df = filtered_df.nlargest(top_n, main_fund_col)
            else:
                filtered_df = filtered_df.head(top_n)
            
            # 替换inf和nan值
            filtered_df = filtered_df.replace([np.inf, -np.inf], np.nan)
            
            # 转换为字典列表
            data_list = filtered_df.to_dict('records')
            data_list = clean_for_json(data_list)
            
            return {
                'success': True,
                'message': f'成功筛选出 {len(data_list)} 只主力资金流入股票',
                'data': data_list,
                'count': len(data_list),
                'columns': list(filtered_df.columns),
                'params': {
                    'days_ago': days_ago,
                    'min_market_cap': min_market_cap,
                    'max_market_cap': max_market_cap,
                    'max_range_change': max_range_change
                }
            }
            
        except Exception as e:
            logger.error(f"[主力选股V2] 失败: {e}")
            return {
                'success': False,
                'message': f'主力选股失败: {str(e)}',
                'data': []
            }

    def get_low_price_bull_stocks(self, top_n: int = 5) -> Dict[str, Any]:
        """
        低价擒牛选股 (aiagents-stock 版本)
        
        筛选条件：
        - 股价 < 10元
        - 净利润增长率 ≥ 100%
        - 非ST
        - 非科创板
        - 非创业板
        - 沪深A股
        - 按成交额由小至大排名 (寻找低关注度的潜力股)
        
        Args:
            top_n: 返回前N只股票 (默认5只)
            
        Returns:
            筛选后的股票数据
        """
        if not self.is_available:
            return {
                'success': False,
                'message': 'pywencai模块未安装',
                'data': []
            }
        
        try:
            logger.info(f"[低价擒牛] 开始选股，目标: {top_n} 只")
            
            # 构建查询语句（按成交额由小至大排名）
            query = (
                "股价<10元，"
                "净利润增长率(净利润同比增长率)≥100%，"
                "非st，"
                "非科创板，"
                "非创业板，"
                "沪深A股，"
                "成交额由小至大排名"
            )
            
            result = self._pywencai.get(query=query, loop=True)
            
            if result is None or (hasattr(result, 'empty') and result.empty):
                return {
                    'success': False,
                    'message': '未找到符合条件的股票',
                    'data': []
                }
            
            if isinstance(result, pd.DataFrame):
                logger.info(f"[低价擒牛] 获取到 {len(result)} 只股票")
                
                # 取前N只
                if len(result) > top_n:
                    result = result.head(top_n)
                
                # 替换inf和nan值
                result = result.replace([np.inf, -np.inf], np.nan)
                
                # 转换为字典列表
                data_list = result.to_dict('records')
                data_list = clean_for_json(data_list)
                
                return {
                    'success': True,
                    'message': f'成功筛选出 {len(data_list)} 只低价高成长股票',
                    'data': data_list,
                    'count': len(data_list),
                    'columns': list(result.columns)
                }
            
            return {
                'success': False,
                'message': '数据格式异常',
                'data': []
            }
            
        except Exception as e:
            logger.error(f"[低价擒牛] 失败: {e}")
            return {
                'success': False,
                'message': f'低价擒牛选股失败: {str(e)}',
                'data': []
            }

    def get_small_cap_stocks_v2(self, top_n: int = 5) -> Dict[str, Any]:
        """
        小市值策略选股 (aiagents-stock 版本)
        
        筛选条件：
        - 总市值 ≤ 50亿
        - 营收增长率 ≥ 10%
        - 净利润增长率 ≥ 100%
        - 沪深A股
        - 非ST
        - 非创业板
        - 非科创板
        - 按总市值由小到大排名
        
        Args:
            top_n: 返回前N只股票 (默认5只)
            
        Returns:
            筛选后的股票数据
        """
        if not self.is_available:
            return {
                'success': False,
                'message': 'pywencai模块未安装',
                'data': []
            }
        
        try:
            logger.info(f"[小市值策略V2] 开始选股，目标: {top_n} 只")
            
            # 构建查询语句（按总市值由小至大排名）
            query = (
                "总市值≤50亿，"
                "营收增长率≥10%，"
                "净利润增长率(净利润同比增长率)≥100%，"
                "沪深A股，"
                "非ST，"
                "非创业板，"
                "非科创板，"
                "总市值由小至大排名"
            )
            
            result = self._pywencai.get(query=query, loop=True)
            
            if result is None or (hasattr(result, 'empty') and result.empty):
                return {
                    'success': False,
                    'message': '未找到符合条件的股票',
                    'data': []
                }
            
            if isinstance(result, pd.DataFrame):
                logger.info(f"[小市值策略V2] 获取到 {len(result)} 只股票")
                
                # 取前N只
                if len(result) > top_n:
                    result = result.head(top_n)
                
                # 替换inf和nan值
                result = result.replace([np.inf, -np.inf], np.nan)
                
                # 转换为字典列表
                data_list = result.to_dict('records')
                data_list = clean_for_json(data_list)
                
                return {
                    'success': True,
                    'message': f'成功筛选出 {len(data_list)} 只小市值高成长股票',
                    'data': data_list,
                    'count': len(data_list),
                    'columns': list(result.columns)
                }
            
            return {
                'success': False,
                'message': '数据格式异常',
                'data': []
            }
            
        except Exception as e:
            logger.error(f"[小市值策略V2] 失败: {e}")
            return {
                'success': False,
                'message': f'小市值策略选股失败: {str(e)}',
                'data': []
            }

    def get_profit_growth_stocks_v2(self, top_n: int = 5) -> Dict[str, Any]:
        """
        净利增长选股 (aiagents-stock 版本)
        
        筛选条件：
        - 净利润增长率 ≥ 10%（净利润同比增长率）
        - 深圳A股
        - 非科创板
        - 非创业板
        - 非ST
        - 按成交额由小到大排名 (寻找低关注度的潜力股)
        
        Args:
            top_n: 返回前N只股票 (默认5只)
            
        Returns:
            筛选后的股票数据
        """
        if not self.is_available:
            return {
                'success': False,
                'message': 'pywencai模块未安装',
                'data': []
            }
        
        try:
            logger.info(f"[净利增长V2] 开始选股，目标: {top_n} 只")
            
            # 构建查询语句（按成交额由小至大排名）
            query = (
                "净利润增长率(净利润同比增长率)≥10%，"
                "非科创板，"
                "非创业板，"
                "非ST，"
                "深圳A股，"
                "成交额由小至大排名"
            )
            
            result = self._pywencai.get(query=query, loop=True)
            
            if result is None or (hasattr(result, 'empty') and result.empty):
                return {
                    'success': False,
                    'message': '未找到符合条件的股票',
                    'data': []
                }
            
            if isinstance(result, pd.DataFrame):
                logger.info(f"[净利增长V2] 获取到 {len(result)} 只股票")
                
                # 取前N只
                if len(result) > top_n:
                    result = result.head(top_n)
                
                # 替换inf和nan值
                result = result.replace([np.inf, -np.inf], np.nan)
                
                # 转换为字典列表
                data_list = result.to_dict('records')
                data_list = clean_for_json(data_list)
                
                return {
                    'success': True,
                    'message': f'成功筛选出 {len(data_list)} 只净利增长股票',
                    'data': data_list,
                    'count': len(data_list),
                    'columns': list(result.columns)
                }
            
            return {
                'success': False,
                'message': '数据格式异常',
                'data': []
            }
            
        except Exception as e:
            logger.error(f"[净利增长V2] 失败: {e}")
            return {
                'success': False,
                'message': f'净利增长选股失败: {str(e)}',
                'data': []
            }

    def get_volume_breakout_stocks(self, top_n: int = 5) -> Dict[str, Any]:
        """
        放量突破选股 (aiagents-stock 风格)
        
        筛选条件：
        - 创20日新高
        - 量比 > 2 (放量)
        - 换手率 > 3%
        - 非ST
        - 沪深A股
        - 按涨跌幅由大至小排名
        
        Args:
            top_n: 返回前N只股票 (默认5只)
            
        Returns:
            筛选后的股票数据
        """
        if not self.is_available:
            return {
                'success': False,
                'message': 'pywencai模块未安装',
                'data': []
            }
        
        try:
            logger.info(f"[放量突破] 开始选股，目标: {top_n} 只")
            
            # 构建查询语句
            query = (
                "创20日新高，"
                "量比>2，"
                "换手率>3%，"
                "非ST，"
                "沪深A股，"
                "涨跌幅由大至小排名"
            )
            
            result = self._pywencai.get(query=query, loop=True)
            
            if result is None or (hasattr(result, 'empty') and result.empty):
                return {
                    'success': False,
                    'message': '未找到符合条件的股票',
                    'data': []
                }
            
            if isinstance(result, pd.DataFrame):
                logger.info(f"[放量突破] 获取到 {len(result)} 只股票")
                
                # 取前N只
                if len(result) > top_n:
                    result = result.head(top_n)
                
                # 替换inf和nan值
                result = result.replace([np.inf, -np.inf], np.nan)
                
                # 转换为字典列表
                data_list = result.to_dict('records')
                data_list = clean_for_json(data_list)
                
                return {
                    'success': True,
                    'message': f'成功筛选出 {len(data_list)} 只放量突破股票',
                    'data': data_list,
                    'count': len(data_list),
                    'columns': list(result.columns)
                }
            
            return {
                'success': False,
                'message': '数据格式异常',
                'data': []
            }
            
        except Exception as e:
            logger.error(f"[放量突破] 失败: {e}")
            return {
                'success': False,
                'message': f'放量突破选股失败: {str(e)}',
                'data': []
            }

    # ==================== 原有预设选股策略 ====================

    def get_profit_growth_stocks(self, top_n: int = 20) -> Dict[str, Any]:
        """
        净利增长选股 (原版本 - 返回较多股票)

        筛选条件：
        - 净利润增长率 ≥ 10%
        - 非ST
        - 非科创板
        - 非创业板
        """
        query = (
            "净利润增长率(净利润同比增长率)≥10%，"
            "非科创板，非创业板，非ST，"
            "沪深A股，成交额由大至小排名"
        )
        return self.query(query, top_n)

    def get_small_cap_growth_stocks(self, top_n: int = 20) -> Dict[str, Any]:
        """
        小市值高增长选股 (原版本 - 返回较多股票)

        筛选条件：
        - 总市值 ≤ 50亿
        - 营收增长率 ≥ 10%
        - 净利润增长率 ≥ 50%
        - 非ST
        """
        query = (
            "总市值≤50亿，"
            "营收增长率≥10%，"
            "净利润增长率(净利润同比增长率)≥50%，"
            "沪深A股，非ST，非创业板，非科创板，"
            "总市值由小至大排名"
        )
        return self.query(query, top_n)

    def get_main_force_inflow_stocks(self, top_n: int = 20) -> Dict[str, Any]:
        """
        主力资金净流入选股 (原版本 - 返回较多股票)

        筛选条件：
        - 主力资金净流入 > 0
        - 涨跌幅 > 0
        - 非ST
        """
        query = (
            "主力资金净流入>0，"
            "涨跌幅>0，"
            "沪深A股，非ST，"
            "主力资金净流入由大至小排名"
        )
        return self.query(query, top_n)

    def get_limit_up_stocks(self, top_n: int = 50) -> Dict[str, Any]:
        """
        涨停股票

        获取今日涨停的股票
        """
        query = "涨停，沪深A股，非ST"
        return self.query(query, top_n)

    def get_breakout_stocks(self, top_n: int = 20) -> Dict[str, Any]:
        """
        突破新高选股

        筛选条件：
        - 创60日新高
        - 成交量放大
        - 非ST
        """
        query = (
            "创60日新高，"
            "量比>1.5，"
            "沪深A股，非ST，"
            "涨跌幅由大至小排名"
        )
        return self.query(query, top_n)

    def get_low_pe_value_stocks(self, top_n: int = 20) -> Dict[str, Any]:
        """
        低估值价值股

        筛选条件：
        - 市盈率 < 20
        - 市净率 < 2
        - ROE > 10%
        - 非ST
        """
        query = (
            "市盈率<20，市盈率>0，"
            "市净率<2，市净率>0，"
            "ROE>10%，"
            "沪深A股，非ST，"
            "市盈率由小至大排名"
        )
        return self.query(query, top_n)

    def get_dividend_stocks(self, top_n: int = 20) -> Dict[str, Any]:
        """
        高股息股票

        筛选条件：
        - 股息率 > 3%
        - 连续3年分红
        - 非ST
        """
        query = (
            "股息率>3%，"
            "连续3年分红，"
            "沪深A股，非ST，"
            "股息率由大至小排名"
        )
        return self.query(query, top_n)

    def get_sector_hot_stocks(self, sector: str, top_n: int = 20) -> Dict[str, Any]:
        """
        板块热门股票

        Args:
            sector: 板块名称（如"人工智能"、"新能源"等）
            top_n: 返回数量
        """
        query = f"{sector}概念，涨跌幅由大至小排名，沪深A股，非ST"
        return self.query(query, top_n)

    def get_institution_holding_stocks(self, top_n: int = 20) -> Dict[str, Any]:
        """
        机构重仓股

        筛选条件：
        - 机构持股比例 > 20%
        - 非ST
        """
        query = (
            "机构持股比例>20%，"
            "沪深A股，非ST，"
            "机构持股比例由大至小排名"
        )
        return self.query(query, top_n)

    def get_northbound_inflow_stocks(self, top_n: int = 20) -> Dict[str, Any]:
        """
        北向资金流入股

        筛选条件：
        - 北向资金持股
        - 近期增持
        """
        query = (
            "北向资金持股，"
            "沪深A股，非ST，"
            "北向资金持股市值由大至小排名"
        )
        return self.query(query, top_n)

    # ==================== 风险数据查询 ====================

    def get_stock_risk_data(self, stock_code: str) -> Dict[str, Any]:
        """
        获取股票风险数据

        Args:
            stock_code: 股票代码

        Returns:
            风险数据（限售解禁、大股东减持、重要事件等）
        """
        result = {
            'success': True,
            'stock_code': stock_code,
            'lifting_ban': None,
            'shareholder_reduction': None,
            'important_events': None
        }

        try:
            # 限售解禁
            lifting_query = f"{stock_code}限售解禁"
            lifting_result = self.query(lifting_query, 10)
            if lifting_result.get('success') and lifting_result.get('data'):
                result['lifting_ban'] = lifting_result['data']

            # 大股东减持
            reduction_query = f"{stock_code}大股东减持公告"
            reduction_result = self.query(reduction_query, 10)
            if reduction_result.get('success') and reduction_result.get('data'):
                result['shareholder_reduction'] = reduction_result['data']

            # 重要事件
            events_query = f"{stock_code}近期重要事件"
            events_result = self.query(events_query, 10)
            if events_result.get('success') and events_result.get('data'):
                result['important_events'] = events_result['data']

        except Exception as e:
            logger.error(f"获取风险数据失败: {e}")
            result['success'] = False
            result['message'] = str(e)

        return result

    def format_result(self, result: Dict[str, Any]) -> str:
        """
        格式化查询结果为文本

        Args:
            result: 查询结果

        Returns:
            格式化的文本
        """
        if not result.get('success'):
            return f"查询失败: {result.get('message', '未知错误')}"

        data = result.get('data', [])
        if not data:
            return "未找到符合条件的股票"

        lines = [f"共找到 {len(data)} 只股票:\n"]

        for idx, item in enumerate(data[:20], 1):
            code = item.get('股票代码', item.get('code', 'N/A'))
            name = item.get('股票简称', item.get('name', 'N/A'))
            line = f"{idx}. {code} {name}"

            # 添加关键指标
            details = []
            for key in ['涨跌幅', '市盈率', '市净率', '净利润增长率', '主力资金净流入', '成交额']:
                if key in item:
                    val = item[key]
                    if val is not None and isinstance(val, (int, float)):
                        if '金额' in key or '成交额' in key:
                            if abs(val) >= 100000000:
                                details.append(f"{key}:{val/100000000:.2f}亿")
                            else:
                                details.append(f"{key}:{val/10000:.2f}万")
                        else:
                            details.append(f"{key}:{val:.2f}")

            if details:
                line += f" ({', '.join(details[:3])})"

            lines.append(line)

        return '\n'.join(lines)


# 单例实例
wencai_selector = WencaiStockSelector()
