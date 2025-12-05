"""
宏观经济数据模块
为宏观政策分析师提供数据支持
"""

import akshare as ak
from typing import List, Dict, Any
from .base import AKShareBase


class AKShareMacroData(AKShareBase):
    """宏观经济数据"""
    
    def __init__(self):
        super().__init__()
    
    def get_gdp_data(self) -> List[Dict[str, Any]]:
        """获取GDP数据"""
        self.logger.info("获取GDP数据...")
        df = self.safe_call(ak.macro_china_gdp)
        if df is None:
            return []
        data_list = self.df_to_dict(df)
        self.logger.info(f"✅ 获取到{len(data_list)}条GDP数据")
        return data_list
    
    def get_cpi_data(self) -> List[Dict[str, Any]]:
        """获取CPI数据"""
        self.logger.info("获取CPI数据...")
        df = self.safe_call(ak.macro_china_cpi)
        if df is None:
            return []
        data_list = self.df_to_dict(df)
        self.logger.info(f"✅ 获取到{len(data_list)}条CPI数据")
        return data_list
    
    def get_pmi_data(self) -> List[Dict[str, Any]]:
        """获取PMI数据"""
        self.logger.info("获取PMI数据...")
        df = self.safe_call(ak.macro_china_pmi)
        if df is None:
            return []
        data_list = self.df_to_dict(df)
        self.logger.info(f"✅ 获取到{len(data_list)}条PMI数据")
        return data_list
    
    def get_money_supply(self) -> List[Dict[str, Any]]:
        """获取货币供应量数据"""
        self.logger.info("获取货币供应量数据...")
        df = self.safe_call(ak.macro_china_money_supply)
        if df is None:
            return []
        data_list = self.df_to_dict(df)
        self.logger.info(f"✅ 获取到{len(data_list)}条货币供应量数据")
        return data_list
    
    def get_comprehensive_macro_data(self) -> Dict[str, Any]:
        """获取综合宏观数据"""
        result = {
            'gdp': [],
            'cpi': [],
            'pmi': [],
            'money_supply': []
        }
        
        try:
            gdp = self.get_gdp_data()
            result['gdp'] = gdp[:12] if gdp else []  # 最近12个月
        except Exception as e:
            self.logger.error(f"❌ 获取GDP数据失败: {e}")
        
        try:
            cpi = self.get_cpi_data()
            result['cpi'] = cpi[:12] if cpi else []
        except Exception as e:
            self.logger.error(f"❌ 获取CPI数据失败: {e}")
        
        try:
            pmi = self.get_pmi_data()
            result['pmi'] = pmi[:12] if pmi else []
        except Exception as e:
            self.logger.error(f"❌ 获取PMI数据失败: {e}")
        
        try:
            money = self.get_money_supply()
            result['money_supply'] = money[:12] if money else []
        except Exception as e:
            self.logger.error(f"❌ 获取货币供应量失败: {e}")
        
        return result


# 全局实例
_macro_data = None

def get_macro_data():
    """获取宏观数据实例（单例）"""
    global _macro_data
    if _macro_data is None:
        _macro_data = AKShareMacroData()
    return _macro_data
