#!/usr/bin/env python3
"""
AKShare财务数据模块
提供资产负债表、利润表、现金流量表等财务数据

数据来源：东方财富
使用场景：
- 基本面估值分析师：分析财务报表、估值模型、公司基本面
- 基本面研究总监：整合基本面相关分析
"""

import akshare as ak
from typing import List, Dict, Any, Optional
from .base import AKShareBase


class AKShareFinancialData(AKShareBase):
    """AKShare财务数据"""
    
    def __init__(self):
        """初始化"""
        super().__init__()
    
    # ========== 资产负债表 ==========
    
    def get_balance_sheet_by_report(self, symbol: str) -> List[Dict[str, Any]]:
        """
        获取资产负债表（按报告期）
        
        Args:
            symbol: 股票代码（如：600519）
            
        Returns:
            资产负债表列表（按报告期）
            
        应用场景：
            - 分析公司资产结构
            - 评估负债水平
            - 计算财务比率
        """
        # 转换为AKShare需要的格式：SH600519 或 SZ000001
        clean_symbol = symbol.replace('.SH', '').replace('.SZ', '')
        if clean_symbol.startswith('6'):
            akshare_symbol = f"SH{clean_symbol}"
        elif clean_symbol.startswith(('0', '3')):
            akshare_symbol = f"SZ{clean_symbol}"
        else:
            akshare_symbol = f"SH{clean_symbol}"  # 默认上交所
        
        self.logger.info(f"获取{akshare_symbol}的资产负债表（按报告期）...")
        
        df = self.safe_call(ak.stock_balance_sheet_by_report_em, symbol=akshare_symbol)
        
        if df is None:
            return []
        
        balance_list = self.df_to_dict(df)
        self.logger.info(f"✅ 获取到{len(balance_list)}期资产负债表")
        
        return balance_list
    
    def get_balance_sheet_by_yearly(self, symbol: str) -> List[Dict[str, Any]]:
        """
        获取资产负债表（按年度）
        
        Args:
            symbol: 股票代码（如：600519）
            
        Returns:
            资产负债表列表（按年度）
            
        应用场景：
            - 长期财务趋势分析
            - 年度对比
        """
        clean_symbol = symbol.replace('.SH', '').replace('.SZ', '')
        if clean_symbol.startswith('6'):
            akshare_symbol = f"SH{clean_symbol}"
        elif clean_symbol.startswith(('0', '3')):
            akshare_symbol = f"SZ{clean_symbol}"
        else:
            akshare_symbol = f"SH{clean_symbol}"
        
        self.logger.info(f"获取{akshare_symbol}的资产负债表（按年度）...")
        
        df = self.safe_call(ak.stock_balance_sheet_by_yearly_em, symbol=akshare_symbol)
        
        if df is None:
            return []
        
        balance_list = self.df_to_dict(df)
        self.logger.info(f"✅ 获取到{len(balance_list)}年资产负债表")
        
        return balance_list
    
    # ========== 利润表 ==========
    
    def get_profit_sheet_by_report(self, symbol: str) -> List[Dict[str, Any]]:
        """
        获取利润表（按报告期）
        
        Args:
            symbol: 股票代码（如：600519）
            
        Returns:
            利润表列表（按报告期）
            
        应用场景：
            - 分析盈利能力
            - 评估营收增长
            - 计算利润率
        """
        clean_symbol = symbol.replace('.SH', '').replace('.SZ', '')
        if clean_symbol.startswith('6'):
            akshare_symbol = f"SH{clean_symbol}"
        elif clean_symbol.startswith(('0', '3')):
            akshare_symbol = f"SZ{clean_symbol}"
        else:
            akshare_symbol = f"SH{clean_symbol}"
        
        self.logger.info(f"获取{akshare_symbol}的利润表（按报告期）...")
        
        df = self.safe_call(ak.stock_profit_sheet_by_report_em, symbol=akshare_symbol)
        
        if df is None:
            return []
        
        profit_list = self.df_to_dict(df)
        self.logger.info(f"✅ 获取到{len(profit_list)}期利润表")
        
        return profit_list
    
    def get_profit_sheet_by_yearly(self, symbol: str) -> List[Dict[str, Any]]:
        """
        获取利润表（按年度）
        
        Args:
            symbol: 股票代码（如：600519）
            
        Returns:
            利润表列表（按年度）
            
        应用场景：
            - 长期盈利趋势分析
            - 年度对比
        """
        clean_symbol = symbol.replace('.SH', '').replace('.SZ', '')
        if clean_symbol.startswith('6'):
            akshare_symbol = f"SH{clean_symbol}"
        elif clean_symbol.startswith(('0', '3')):
            akshare_symbol = f"SZ{clean_symbol}"
        else:
            akshare_symbol = f"SH{clean_symbol}"
        
        self.logger.info(f"获取{akshare_symbol}的利润表（按年度）...")
        
        df = self.safe_call(ak.stock_profit_sheet_by_yearly_em, symbol=akshare_symbol)
        
        if df is None:
            return []
        
        profit_list = self.df_to_dict(df)
        self.logger.info(f"✅ 获取到{len(profit_list)}年利润表")
        
        return profit_list
    
    def get_profit_sheet_by_quarterly(self, symbol: str) -> List[Dict[str, Any]]:
        """
        获取利润表（按单季度）
        
        Args:
            symbol: 股票代码（如：600519）
            
        Returns:
            利润表列表（按单季度）
            
        应用场景：
            - 季度盈利分析
            - 环比增长分析
        """
        clean_symbol = symbol.replace('.SH', '').replace('.SZ', '')
        if clean_symbol.startswith('6'):
            akshare_symbol = f"SH{clean_symbol}"
        elif clean_symbol.startswith(('0', '3')):
            akshare_symbol = f"SZ{clean_symbol}"
        else:
            akshare_symbol = f"SH{clean_symbol}"
        
        self.logger.info(f"获取{akshare_symbol}的利润表（按单季度）...")
        
        df = self.safe_call(ak.stock_profit_sheet_by_quarterly_em, symbol=akshare_symbol)
        
        if df is None:
            return []
        
        profit_list = self.df_to_dict(df)
        self.logger.info(f"✅ 获取到{len(profit_list)}季利润表")
        
        return profit_list
    
    # ========== 现金流量表 ==========
    
    def get_cash_flow_sheet_by_report(self, symbol: str) -> List[Dict[str, Any]]:
        """
        获取现金流量表（按报告期）
        
        Args:
            symbol: 股票代码（如：600519）
            
        Returns:
            现金流量表列表（按报告期）
            
        应用场景：
            - 分析现金流健康度
            - 评估经营活动现金流
            - 判断公司造血能力
        """
        clean_symbol = symbol.replace('.SH', '').replace('.SZ', '')
        if clean_symbol.startswith('6'):
            akshare_symbol = f"SH{clean_symbol}"
        elif clean_symbol.startswith(('0', '3')):
            akshare_symbol = f"SZ{clean_symbol}"
        else:
            akshare_symbol = f"SH{clean_symbol}"
        
        self.logger.info(f"获取{akshare_symbol}的现金流量表（按报告期）...")
        
        df = self.safe_call(ak.stock_cash_flow_sheet_by_report_em, symbol=akshare_symbol)
        
        if df is None:
            return []
        
        cash_flow_list = self.df_to_dict(df)
        self.logger.info(f"✅ 获取到{len(cash_flow_list)}期现金流量表")
        
        return cash_flow_list
    
    def get_cash_flow_sheet_by_yearly(self, symbol: str) -> List[Dict[str, Any]]:
        """
        获取现金流量表（按年度）
        
        Args:
            symbol: 股票代码（如：600519）
            
        Returns:
            现金流量表列表（按年度）
            
        应用场景：
            - 长期现金流趋势分析
            - 年度对比
        """
        clean_symbol = symbol.replace('.SH', '').replace('.SZ', '')
        if clean_symbol.startswith('6'):
            akshare_symbol = f"SH{clean_symbol}"
        elif clean_symbol.startswith(('0', '3')):
            akshare_symbol = f"SZ{clean_symbol}"
        else:
            akshare_symbol = f"SH{clean_symbol}"
        
        self.logger.info(f"获取{akshare_symbol}的现金流量表（按年度）...")
        
        df = self.safe_call(ak.stock_cash_flow_sheet_by_yearly_em, symbol=akshare_symbol)
        
        if df is None:
            return []
        
        cash_flow_list = self.df_to_dict(df)
        self.logger.info(f"✅ 获取到{len(cash_flow_list)}年现金流量表")
        
        return cash_flow_list
    
    def get_cash_flow_sheet_by_quarterly(self, symbol: str) -> List[Dict[str, Any]]:
        """
        获取现金流量表（按单季度）
        
        Args:
            symbol: 股票代码（如：600519）
            
        Returns:
            现金流量表列表（按单季度）
            
        应用场景：
            - 季度现金流分析
            - 环比增长分析
        """
        clean_symbol = symbol.replace('.SH', '').replace('.SZ', '')
        if clean_symbol.startswith('6'):
            akshare_symbol = f"SH{clean_symbol}"
        elif clean_symbol.startswith(('0', '3')):
            akshare_symbol = f"SZ{clean_symbol}"
        else:
            akshare_symbol = f"SH{clean_symbol}"
        
        self.logger.info(f"获取{akshare_symbol}的现金流量表（按单季度）...")
        
        df = self.safe_call(ak.stock_cash_flow_sheet_by_quarterly_em, symbol=akshare_symbol)
        
        if df is None:
            return []
        
        cash_flow_list = self.df_to_dict(df)
        self.logger.info(f"✅ 获取到{len(cash_flow_list)}季现金流量表")
        
        return cash_flow_list
    
    # ========== 综合财务数据 ==========
    
    def get_comprehensive_financial_data(
        self, 
        symbol: str,
        period: str = "report"  # report/yearly/quarterly
    ) -> Dict[str, Any]:
        """
        获取综合财务数据（为基本面分析师提供完整数据）
        
        Args:
            symbol: 股票代码（如：600519）
            period: 报告期类型（report/yearly/quarterly）
            
        Returns:
            包含三大财务报表的字典
            
        应用场景：
            - 基本面估值分析师：一次性获取所有财务数据
            - 全面的财务分析
        """
        result = {
            'balance_sheet': [],
            'profit_sheet': [],
            'cash_flow_sheet': []
        }
        
        # 1. 资产负债表
        try:
            if period == "report":
                result['balance_sheet'] = self.get_balance_sheet_by_report(symbol)
            elif period == "yearly":
                result['balance_sheet'] = self.get_balance_sheet_by_yearly(symbol)
        except Exception as e:
            self.logger.error(f"❌ 获取资产负债表失败: {e}")
        
        # 2. 利润表
        try:
            if period == "report":
                result['profit_sheet'] = self.get_profit_sheet_by_report(symbol)
            elif period == "yearly":
                result['profit_sheet'] = self.get_profit_sheet_by_yearly(symbol)
            elif period == "quarterly":
                result['profit_sheet'] = self.get_profit_sheet_by_quarterly(symbol)
        except Exception as e:
            self.logger.error(f"❌ 获取利润表失败: {e}")
        
        # 3. 现金流量表
        try:
            if period == "report":
                result['cash_flow_sheet'] = self.get_cash_flow_sheet_by_report(symbol)
            elif period == "yearly":
                result['cash_flow_sheet'] = self.get_cash_flow_sheet_by_yearly(symbol)
            elif period == "quarterly":
                result['cash_flow_sheet'] = self.get_cash_flow_sheet_by_quarterly(symbol)
        except Exception as e:
            self.logger.error(f"❌ 获取现金流量表失败: {e}")
        
        return result
    
    def get_latest_financial_summary(self, symbol: str) -> Dict[str, Any]:
        """
        获取最新财务摘要（关键指标）
        
        Args:
            symbol: 股票代码（如：600519）
            
        Returns:
            最新财务摘要
            
        应用场景：
            - 快速了解公司最新财务状况
            - 关键指标一览
        """
        result = {}
        
        try:
            # 获取最新一期的三大报表
            balance = self.get_balance_sheet_by_report(symbol)
            profit = self.get_profit_sheet_by_report(symbol)
            cash_flow = self.get_cash_flow_sheet_by_report(symbol)
            
            # 资产负债表
            if balance:
                latest_balance = balance[0]
                result['报告期'] = latest_balance.get('REPORT_DATE')
                total_assets = latest_balance.get('TOTAL_ASSETS')
                total_liab = latest_balance.get('TOTAL_LIABILITIES')
                total_equity = latest_balance.get('TOTAL_EQUITY')
                
                result['总资产'] = total_assets
                result['总负债'] = total_liab
                result['净资产'] = total_equity
                
                # 计算资产负债率（如果原始数据没有）
                asset_liab_ratio = latest_balance.get('ASSET_LIAB_RATIO')
                if asset_liab_ratio is None and total_assets and total_liab:
                    try:
                        asset_liab_ratio = round(total_liab / total_assets, 4)
                    except:
                        pass
                result['资产负债率'] = asset_liab_ratio
            
            # 利润表
            if profit:
                latest_profit = profit[0]
                revenue = latest_profit.get('TOTAL_OPERATE_INCOME')
                net_profit = latest_profit.get('NETPROFIT')
                
                result['营业收入'] = revenue
                result['净利润'] = net_profit
                
                # 毛利率（尝试多个字段名）
                gross_profit_ratio = latest_profit.get('GROSS_PROFIT_RATIO') or \
                                   latest_profit.get('GROSS_MARGIN') or \
                                   latest_profit.get('XSMLL')  # 销售毛利率
                result['毛利率'] = gross_profit_ratio
                
                # 净利率（计算）
                net_profit_ratio = latest_profit.get('NETPROFIT_RATIO') or \
                                 latest_profit.get('XSJLL')  # 销售净利率
                if net_profit_ratio is None and revenue and net_profit:
                    try:
                        net_profit_ratio = round(net_profit / revenue, 4)
                    except:
                        pass
                result['净利率'] = net_profit_ratio
            
            # 现金流量表
            if cash_flow:
                latest_cash = cash_flow[0]
                # 尝试多个字段名
                operate_cash = latest_cash.get('OPERATE_CASH_FLOW_NET') or \
                             latest_cash.get('NCF_OPERATE_A') or \
                             latest_cash.get('OPERATE_NET_CASH_FLOW')
                invest_cash = latest_cash.get('INVEST_CASH_FLOW_NET') or \
                            latest_cash.get('NCF_INV_A') or \
                            latest_cash.get('INVEST_NET_CASH_FLOW')
                finance_cash = latest_cash.get('FINANCE_CASH_FLOW_NET') or \
                             latest_cash.get('NCF_FIN_A') or \
                             latest_cash.get('FINANCE_NET_CASH_FLOW')
                
                result['经营活动现金流'] = operate_cash
                result['投资活动现金流'] = invest_cash
                result['筹资活动现金流'] = finance_cash
            
            self.logger.info(f"✅ 获取{symbol}最新财务摘要")
            
        except Exception as e:
            self.logger.error(f"❌ 获取财务摘要失败: {e}")
            import traceback
            traceback.print_exc()
        
        return result


# 全局实例
_financial_data = None

def get_financial_data():
    """获取财务数据实例（单例）"""
    global _financial_data
    if _financial_data is None:
        _financial_data = AKShareFinancialData()
    return _financial_data
