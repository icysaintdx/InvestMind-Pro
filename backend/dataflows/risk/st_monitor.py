"""
ST股票监控模块
使用Tushare stock_st接口获取ST股票列表
ST股票通常存在财务亏损、违规等风险，是风险评估的关键标的池
"""

import os
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import pandas as pd

from backend.utils.logging_config import get_logger

logger = get_logger("dataflows.st_monitor")


def get_tushare_api():
    """获取Tushare API实例"""
    try:
        import tushare as ts
        
        token = os.getenv('TUSHARE_TOKEN', '')
        if not token:
            logger.error("❌ TUSHARE_TOKEN未配置")
            return None
        
        ts.set_token(token)
        api = ts.pro_api()
        return api
        
    except ImportError:
        logger.error("❌ Tushare库未安装")
        return None
    except Exception as e:
        logger.error(f"❌ Tushare API初始化失败: {e}")
        return None


class STStockMonitor:
    """ST股票监控器"""
    
    def __init__(self):
        self.api = get_tushare_api()
    
    def is_available(self) -> bool:
        """检查是否可用（需要3000积分）"""
        return self.api is not None
    
    def get_st_stocks_today(self) -> Optional[pd.DataFrame]:
        """
        获取今日ST股票列表
        
        Returns:
            DataFrame包含: ts_code, name, trade_date, type, type_name
        """
        if not self.is_available():
            logger.warning("⚠️ Tushare API不可用或积分不足（需要3000积分）")
            return None
        
        try:
            today = datetime.now().strftime('%Y%m%d')
            
            df = self.api.stock_st(trade_date=today)
            
            if df is not None and not df.empty:
                logger.info(f"✅ 获取今日ST股票: {len(df)}只")
                return df
            else:
                logger.info("ℹ️ 今日无ST股票数据")
                return pd.DataFrame()
                
        except Exception as e:
            error_msg = str(e)
            if '权限' in error_msg or 'permission' in error_msg.lower():
                logger.error("❌ Tushare积分不足，需要3000积分才能访问ST股票接口")
            else:
                logger.error(f"❌ 获取ST股票列表失败: {e}")
            return None
    
    def check_if_st(self, ts_code: str, trade_date: Optional[str] = None) -> Dict:
        """
        检查指定股票是否为ST股票
        
        Args:
            ts_code: 股票代码，如 600519.SH
            trade_date: 交易日期，格式YYYYMMDD，默认为今天
            
        Returns:
            {
                'is_st': bool,        # 是否是ST股票
                'st_type': str,       # ST类型
                'st_type_name': str,  # ST类型名称
                'trade_date': str     # 查询日期
            }
        """
        if not self.is_available():
            logger.warning("⚠️ Tushare API不可用")
            return {
                'is_st': False,
                'st_type': None,
                'st_type_name': None,
                'trade_date': None,
                'error': 'API不可用'
            }
        
        try:
            if not trade_date:
                trade_date = datetime.now().strftime('%Y%m%d')
            
            # 查询指定股票的ST状态
            df = self.api.stock_st(ts_code=ts_code, trade_date=trade_date)
            
            if df is not None and not df.empty:
                row = df.iloc[0]
                result = {
                    'is_st': True,
                    'st_type': row.get('type', 'ST'),
                    'st_type_name': row.get('type_name', '风险警示板'),
                    'trade_date': trade_date,
                    'stock_name': row.get('name', '')
                }
                logger.info(f"⚠️ {ts_code} 是ST股票: {result['st_type_name']}")
                return result
            else:
                logger.info(f"✅ {ts_code} 非ST股票")
                return {
                    'is_st': False,
                    'st_type': None,
                    'st_type_name': None,
                    'trade_date': trade_date
                }
                
        except Exception as e:
            logger.error(f"❌ 查询{ts_code}的ST状态失败: {e}")
            return {
                'is_st': False,
                'st_type': None,
                'st_type_name': None,
                'trade_date': None,
                'error': str(e)
            }
    
    def get_st_history(
        self, 
        ts_code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Optional[pd.DataFrame]:
        """
        获取股票的ST历史记录
        
        Args:
            ts_code: 股票代码
            start_date: 开始日期，格式YYYYMMDD
            end_date: 结束日期，格式YYYYMMDD
            
        Returns:
            DataFrame包含ST历史记录
        """
        if not self.is_available():
            logger.warning("⚠️ Tushare API不可用")
            return None
        
        try:
            if not end_date:
                end_date = datetime.now().strftime('%Y%m%d')
            if not start_date:
                # 默认查询最近1年
                start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
            
            df = self.api.stock_st(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date
            )
            
            if df is not None and not df.empty:
                logger.info(f"✅ 获取{ts_code}的ST历史: {len(df)}条记录")
                return df
            else:
                logger.info(f"ℹ️ {ts_code}在{start_date}至{end_date}期间无ST记录")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"❌ 获取ST历史失败: {e}")
            return None
    
    def get_st_risk_level(self, st_status: Dict) -> str:
        """
        根据ST状态评估风险等级
        
        Args:
            st_status: check_if_st返回的结果
            
        Returns:
            'high'/'medium'/'low'
        """
        if not st_status.get('is_st'):
            return 'low'
        
        st_type = st_status.get('st_type', 'ST')
        
        # *ST（连续亏损）风险最高
        if st_type.startswith('*ST'):
            return 'high'
        # ST（其他风险警示）中等风险
        elif st_type == 'ST':
            return 'medium'
        else:
            return 'medium'
    
    def get_st_statistics(self, st_df: pd.DataFrame) -> Dict:
        """
        统计ST股票信息
        
        Args:
            st_df: ST股票DataFrame
            
        Returns:
            统计信息字典
        """
        if st_df is None or st_df.empty:
            return {
                'total_count': 0,
                'st_count': 0,
                'sst_count': 0,
                'by_type': {}
            }
        
        try:
            total = len(st_df)
            
            # 统计*ST和ST
            sst_count = len(st_df[st_df['type'].str.startswith('*ST', na=False)])
            st_count = len(st_df[st_df['type'] == 'ST'])
            
            # 按类型统计
            type_counts = st_df['type_name'].value_counts().to_dict()
            
            result = {
                'total_count': total,
                'st_count': st_count,
                'sst_count': sst_count,
                'by_type': type_counts,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"📊 ST股票统计: 总计{total}只, *ST:{sst_count}只, ST:{st_count}只")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ ST统计失败: {e}")
            return {}


# 全局监控器实例
_st_monitor = None


def get_st_monitor() -> STStockMonitor:
    """获取全局ST监控器实例"""
    global _st_monitor
    if _st_monitor is None:
        _st_monitor = STStockMonitor()
    return _st_monitor


# ==================== 便捷函数 ====================

def is_st_stock(ts_code: str) -> bool:
    """判断是否为ST股票"""
    monitor = get_st_monitor()
    status = monitor.check_if_st(ts_code)
    return status.get('is_st', False)


def get_today_st_stocks() -> Optional[List[str]]:
    """获取今日ST股票代码列表"""
    monitor = get_st_monitor()
    df = monitor.get_st_stocks_today()
    
    if df is not None and not df.empty:
        return df['ts_code'].tolist()
    return []


def check_st_risk(ts_code: str) -> str:
    """检查ST风险等级"""
    monitor = get_st_monitor()
    status = monitor.check_if_st(ts_code)
    return monitor.get_st_risk_level(status)
