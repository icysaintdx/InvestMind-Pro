#!/usr/bin/env python3
"""
AKShare资金流向数据模块
为资金流向分析师(Fund Flow Analyst)提供数据支持

数据来源：
1. 北向资金（沪深港通）- 东方财富
2. 个股资金流 - 同花顺
3. 行业资金流 - 同花顺
4. 概念资金流 - 同花顺
5. 融资融券 - 东方财富

使用场景：
- 资金流向分析师：监控主力资金动向、北向资金、机构持仓变化
- 中国市场分析师：分析北向资金、融资融券、大宗交易等资金流向
- 动量投资经理：整合技术面和资金面分析，判断短期动能
"""

import akshare as ak
from typing import List, Dict, Any, Optional
from .base import AKShareBase


class AKShareFundFlowData(AKShareBase):
    """AKShare资金流向数据"""
    
    def __init__(self):
        """初始化"""
        super().__init__()
    
    # ========== 北向资金（沪深港通）==========
    
    def get_hsgt_realtime(self, symbol: str = "北向资金") -> List[Dict[str, Any]]:
        """
        获取沪深港通实时资金流向（分钟级）
        
        Args:
            symbol: 北向资金/沪股通/深股通/南向资金/港股通沪/港股通深
            
        Returns:
            分钟级资金流向列表
            
        应用场景：
            - 资金流向分析师：实时监控北向资金动向
            - 判断当日资金流入流出趋势
        """
        self.logger.info(f"获取{symbol}实时资金流向...")
        
        df = self.safe_call(ak.stock_hsgt_fund_min_em, symbol=symbol)
        
        if df is None:
            return []
        
        flow_list = self.df_to_dict(df)
        self.logger.info(f"✅ 获取到{len(flow_list)}条{symbol}实时数据")
        
        return flow_list
    
    def get_hsgt_history(self, symbol: str = "北向资金") -> List[Dict[str, Any]]:
        """
        获取沪深港通历史资金流向
        
        Args:
            symbol: 北向资金/沪股通/深股通/南向资金/港股通沪/港股通深
            
        Returns:
            历史资金流向列表
            
        应用场景：
            - 分析北向资金长期趋势
            - 判断外资对A股的态度变化
        """
        self.logger.info(f"获取{symbol}历史资金流向...")
        
        df = self.safe_call(ak.stock_hsgt_hist_em, symbol=symbol)
        
        if df is None:
            return []
        
        flow_list = self.df_to_dict(df)
        self.logger.info(f"✅ 获取到{len(flow_list)}条{symbol}历史数据")
        
        return flow_list
    
    def get_hsgt_top10(self, market: str = "北向", indicator: str = "今日排行") -> List[Dict[str, Any]]:
        """
        获取沪深港通持股排名
        
        Args:
            market: 北向/沪股通/深股通
            indicator: 今日排行/3日排行/5日排行/10日排行/月排行/季排行/年排行
            
        Returns:
            持股排名列表
            
        应用场景：
            - 发现北向资金重仓股
            - 分析外资偏好的个股
        """
        self.logger.info(f"获取{market}持股排名({indicator})...")
        
        df = self.safe_call(ak.stock_hsgt_hold_stock_em, market=market, indicator=indicator)
        
        if df is None:
            return []
        
        rank_list = self.df_to_dict(df)
        self.logger.info(f"✅ 获取到{len(rank_list)}条持股排名")
        
        return rank_list
    
    def get_hsgt_board_rank(
        self, 
        symbol: str = "北向资金增持行业板块排行", 
        indicator: str = "今日"
    ) -> List[Dict[str, Any]]:
        """
        获取北向资金增持板块排行
        
        Args:
            symbol: 北向资金增持行业板块排行/北向资金增持概念板块排行/北向资金增持地域板块排行
            indicator: 今日/3日/5日/10日/1月/1季/1年
            
        Returns:
            板块排行列表
            
        应用场景：
            - 发现北向资金青睐的行业/概念
            - 判断外资配置方向
        """
        self.logger.info(f"获取{symbol}({indicator})...")
        
        df = self.safe_call(ak.stock_hsgt_board_rank_em, symbol=symbol, indicator=indicator)
        
        if df is None:
            return []
        
        rank_list = self.df_to_dict(df)
        self.logger.info(f"✅ 获取到{len(rank_list)}条板块排行")
        
        return rank_list
    
    # ========== 个股资金流（同花顺）==========
    
    def get_individual_fund_flow(self, symbol: str = "即时") -> List[Dict[str, Any]]:
        """
        获取个股资金流向
        
        Args:
            symbol: 即时/3日排行/5日排行/10日排行/20日排行
            
        Returns:
            个股资金流向列表
            
        应用场景：
            - 资金流向分析师：监控主力资金流入流出
            - 发现资金集中流入的个股
            - 判断主力是否在吸筹或出货
        """
        self.logger.info(f"获取个股资金流向({symbol})...")
        
        df = self.safe_call(ak.stock_fund_flow_individual, symbol=symbol)
        
        if df is None:
            return []
        
        flow_list = self.df_to_dict(df)
        self.logger.info(f"✅ 获取到{len(flow_list)}条个股资金流向")
        
        return flow_list
    
    def get_stock_fund_flow(self, symbol: str) -> Dict[str, Any]:
        """
        获取单个股票的资金流向详情
        
        Args:
            symbol: 股票代码（如：600519）
            
        Returns:
            资金流向详情
            
        应用场景：
            - 分析特定个股的资金流入流出情况
            - 判断主力资金动向
        """
        clean_symbol = symbol.replace('.SH', '').replace('.SZ', '')
        self.logger.info(f"获取{clean_symbol}的资金流向详情...")
        
        # 从即时数据中筛选
        all_flow = self.get_individual_fund_flow("即时")
        
        if not all_flow:
            return {}
        
        # 查找目标股票
        for item in all_flow:
            stock_code = str(item.get('股票代码', ''))
            if stock_code == clean_symbol or stock_code.zfill(6) == clean_symbol:
                self.logger.info(f"✅ 找到{clean_symbol}的资金流向")
                return item
        
        self.logger.warning(f"⚠️ 未找到{clean_symbol}的资金流向")
        return {}
    
    # ========== 行业资金流（同花顺）==========
    
    def get_industry_fund_flow(self, symbol: str = "即时") -> List[Dict[str, Any]]:
        """
        获取行业资金流向
        
        Args:
            symbol: 即时/3日排行/5日排行/10日排行/20日排行
            
        Returns:
            行业资金流向列表
            
        应用场景：
            - 发现资金流入的热门行业
            - 判断行业轮动方向
            - 中国市场分析师：分析行业资金流向
        """
        self.logger.info(f"获取行业资金流向({symbol})...")
        
        df = self.safe_call(ak.stock_fund_flow_industry, symbol=symbol)
        
        if df is None:
            return []
        
        flow_list = self.df_to_dict(df)
        self.logger.info(f"✅ 获取到{len(flow_list)}条行业资金流向")
        
        return flow_list
    
    # ========== 概念资金流（同花顺）==========
    
    def get_concept_fund_flow(self, symbol: str = "即时") -> List[Dict[str, Any]]:
        """
        获取概念资金流向
        
        Args:
            symbol: 即时/3日排行/5日排行/10日排行/20日排行
            
        Returns:
            概念资金流向列表
            
        应用场景：
            - 发现热门概念题材
            - 判断市场炒作方向
            - 追踪主题投资机会
        """
        self.logger.info(f"获取概念资金流向({symbol})...")
        
        df = self.safe_call(ak.stock_fund_flow_concept, symbol=symbol)
        
        if df is None:
            return []
        
        flow_list = self.df_to_dict(df)
        self.logger.info(f"✅ 获取到{len(flow_list)}条概念资金流向")
        
        return flow_list
    
    # ========== 融资融券 ==========
    
    def get_margin_trading_detail(self, date: str) -> List[Dict[str, Any]]:
        """
        获取上交所融资融券明细
        
        Args:
            date: 日期（如：20240101）
            
        Returns:
            融资融券明细列表
            
        应用场景：
            - 分析融资买入和融券卖出情况
            - 判断市场情绪和杠杆水平
        """
        self.logger.info(f"获取{date}的融资融券明细...")
        
        df = self.safe_call(ak.stock_margin_detail_sse, date=date)
        
        if df is None:
            return []
        
        margin_list = self.df_to_dict(df)
        self.logger.info(f"✅ 获取到{len(margin_list)}条融资融券明细")
        
        return margin_list
    
    def get_margin_trading_summary(self, start_date: str = None, end_date: str = None) -> List[Dict[str, Any]]:
        """
        获取上交所融资融券汇总数据
        
        Args:
            start_date: 开始日期（如：20240101）
            end_date: 结束日期（如：20241231）
            
        Returns:
            融资融券汇总列表
            
        应用场景：
            - 分析市场整体杠杆水平
            - 判断市场情绪变化
        """
        from datetime import datetime, timedelta
        
        if not end_date:
            end_date = datetime.now().strftime("%Y%m%d")
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")
        
        self.logger.info(f"获取融资融券汇总({start_date}~{end_date})...")
        
        df = self.safe_call(ak.stock_margin_sse, start_date=start_date, end_date=end_date)
        
        if df is None:
            return []
        
        summary_list = self.df_to_dict(df)
        self.logger.info(f"✅ 获取到{len(summary_list)}条融资融券汇总")
        
        return summary_list
    
    # ========== 综合分析 ==========
    
    def get_comprehensive_fund_flow(
        self, 
        symbol: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取综合资金流向分析（为资金流向分析师提供完整数据）
        
        Args:
            symbol: 股票代码（可选）
            
        Returns:
            包含多维度资金流向的字典
            
        应用场景：
            - 资金流向分析师：一次性获取所有需要的数据
            - 动量投资经理：综合判断资金面
        """
        result = {
            'north_bound_realtime': [],
            'north_bound_history': [],
            'north_bound_top10': [],
            'industry_flow': [],
            'concept_flow': [],
            'individual_flow_top': [],
            'margin_summary': []
        }
        
        # 1. 北向资金实时
        try:
            result['north_bound_realtime'] = self.get_hsgt_realtime("北向资金")
        except Exception as e:
            self.logger.error(f"❌ 获取北向资金实时数据失败: {e}")
        
        # 2. 北向资金历史（最近30天）
        try:
            history = self.get_hsgt_history("北向资金")
            result['north_bound_history'] = history[:30] if history else []
        except Exception as e:
            self.logger.error(f"❌ 获取北向资金历史数据失败: {e}")
        
        # 3. 北向资金持股TOP10
        try:
            result['north_bound_top10'] = self.get_hsgt_top10("北向", "今日排行")
        except Exception as e:
            self.logger.error(f"❌ 获取北向资金持股排名失败: {e}")
        
        # 4. 行业资金流（即时）
        try:
            result['industry_flow'] = self.get_industry_fund_flow("即时")
        except Exception as e:
            self.logger.error(f"❌ 获取行业资金流失败: {e}")
        
        # 5. 概念资金流（即时，TOP20）
        try:
            concept_flow = self.get_concept_fund_flow("即时")
            result['concept_flow'] = concept_flow[:20] if concept_flow else []
        except Exception as e:
            self.logger.error(f"❌ 获取概念资金流失败: {e}")
        
        # 6. 个股资金流TOP50
        try:
            individual_flow = self.get_individual_fund_flow("即时")
            result['individual_flow_top'] = individual_flow[:50] if individual_flow else []
        except Exception as e:
            self.logger.error(f"❌ 获取个股资金流失败: {e}")
        
        # 7. 融资融券汇总（最近30天）
        try:
            result['margin_summary'] = self.get_margin_trading_summary()
        except Exception as e:
            self.logger.error(f"❌ 获取融资融券汇总失败: {e}")
        
        # 8. 如果指定了股票代码，获取个股详情
        if symbol:
            result['stock_detail'] = {}
            try:
                result['stock_detail']['fund_flow'] = self.get_stock_fund_flow(symbol)
            except Exception as e:
                self.logger.error(f"❌ 获取个股资金流失败: {e}")
            
            # 融资融券明细需要日期参数，暂时跳过
            # try:
            #     from datetime import datetime
            #     today = datetime.now().strftime("%Y%m%d")
            #     result['stock_detail']['margin'] = self.get_margin_trading_detail(today)
            # except Exception as e:
            #     self.logger.error(f"❌ 获取融资融券明细失败: {e}")
        
        return result


# 全局实例
_fund_flow_data = None

def get_fund_flow_data():
    """获取资金流向数据实例（单例）"""
    global _fund_flow_data
    if _fund_flow_data is None:
        _fund_flow_data = AKShareFundFlowData()
    return _fund_flow_data
