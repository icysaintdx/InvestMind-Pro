"""
行业板块数据模块
为行业轮动分析师提供数据支持
"""

import akshare as ak
from typing import List, Dict, Any
from .base import AKShareBase


class AKShareSectorData(AKShareBase):
    """行业板块数据"""
    
    def __init__(self):
        super().__init__()
    
    def get_industry_list(self) -> List[Dict[str, Any]]:
        """获取行业板块列表"""
        self.logger.info("获取行业板块列表...")
        df = self.safe_call(ak.stock_board_industry_name_em)
        if df is None:
            return []
        data_list = self.df_to_dict(df)
        self.logger.info(f"✅ 获取到{len(data_list)}个行业板块")
        return data_list
    
    def get_industry_cons(self, symbol: str) -> List[Dict[str, Any]]:
        """获取行业成分股"""
        self.logger.info(f"获取{symbol}成分股...")
        df = self.safe_call(ak.stock_board_industry_cons_em, symbol=symbol)
        if df is None:
            return []
        data_list = self.df_to_dict(df)
        self.logger.info(f"✅ 获取到{len(data_list)}只成分股")
        return data_list
    
    def get_comprehensive_sector_data(self) -> Dict[str, Any]:
        """获取综合板块数据"""
        result = {
            'industry_list': [],
            'industry_flow': []
        }
        
        try:
            result['industry_list'] = self.get_industry_list()
        except Exception as e:
            self.logger.error(f"❌ 获取行业列表失败: {e}")
        
        # 获取行业资金流向
        try:
            from .fund_flow_data import get_fund_flow_data
            fund_flow = get_fund_flow_data()
            result['industry_flow'] = fund_flow.get_industry_fund_flow("即时")
        except Exception as e:
            self.logger.error(f"❌ 获取行业资金流失败: {e}")
        
        return result


# 全局实例
_sector_data = None

def get_sector_data():
    """获取板块数据实例（单例）"""
    global _sector_data
    if _sector_data is None:
        _sector_data = AKShareSectorData()
    return _sector_data
