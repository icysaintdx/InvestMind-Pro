"""
停复牌监控模块
使用Tushare suspend_d接口获取股票停复牌信息
"""

import os
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import pandas as pd

from backend.utils.logging_config import get_logger

logger = get_logger("dataflows.suspend_monitor")

# 全局Tushare API实例
_tushare_api = None


def get_tushare_api():
    """获取Tushare API实例"""
    global _tushare_api
    
    if _tushare_api is not None:
        return _tushare_api
    
    try:
        import tushare as ts
        
        # 从环境变量获取token
        token = os.getenv('TUSHARE_TOKEN', '')
        if not token:
            logger.error("❌ TUSHARE_TOKEN未配置")
            return None
        
        ts.set_token(token)
        _tushare_api = ts.pro_api()
        logger.info("✅ Tushare API初始化成功")
        return _tushare_api
        
    except ImportError:
        logger.error("❌ Tushare库未安装，请运行: pip install tushare")
        return None
    except Exception as e:
        logger.error(f"❌ Tushare API初始化失败: {e}")
        return None


class SuspendMonitor:
    """停复牌监控器"""
    
    def __init__(self):
        self.api = get_tushare_api()
    
    def is_available(self) -> bool:
        """检查是否可用"""
        return self.api is not None
    
    def get_suspend_stocks_today(self) -> Optional[pd.DataFrame]:
        """
        获取今日停牌股票列表
        
        Returns:
            DataFrame包含: ts_code, trade_date, suspend_timing, suspend_type
        """
        if not self.is_available():
            logger.warning("⚠️ Tushare API不可用")
            return None
        
        try:
            today = datetime.now().strftime('%Y%m%d')
            
            df = self.api.suspend_d(
                suspend_type='S',  # S-停牌
                trade_date=today
            )
            
            if df is not None and not df.empty:
                logger.info(f"✅ 获取今日停牌股票: {len(df)}只")
                return df
            else:
                logger.info("ℹ️ 今日无停牌股票")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"❌ 获取今日停牌股票失败: {e}")
            return None
    
    def get_resume_stocks_today(self) -> Optional[pd.DataFrame]:
        """
        获取今日复牌股票列表
        
        Returns:
            DataFrame包含: ts_code, trade_date, suspend_timing, suspend_type
        """
        if not self.is_available():
            logger.warning("⚠️ Tushare API不可用")
            return None
        
        try:
            today = datetime.now().strftime('%Y%m%d')
            
            df = self.api.suspend_d(
                suspend_type='R',  # R-复牌
                trade_date=today
            )
            
            if df is not None and not df.empty:
                logger.info(f"✅ 获取今日复牌股票: {len(df)}只")
                return df
            else:
                logger.info("ℹ️ 今日无复牌股票")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"❌ 获取今日复牌股票失败: {e}")
            return None
    
    def check_stock_suspend_status(
        self, 
        ts_code: str, 
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, any]:
        """
        检查指定股票的停复牌状态
        
        Args:
            ts_code: 股票代码，如 600519.SH
            start_date: 开始日期，格式YYYYMMDD
            end_date: 结束日期，格式YYYYMMDD
            
        Returns:
            {
                'is_suspended': bool,  # 当前是否停牌
                'suspend_count': int,  # 停牌次数
                'resume_count': int,   # 复牌次数
                'latest_status': str,  # 最新状态: 'suspended'/'trading'
                'latest_date': str,    # 最新状态日期
                'suspend_records': []  # 停复牌记录
            }
        """
        if not self.is_available():
            logger.warning("⚠️ Tushare API不可用")
            return {
                'is_suspended': False,
                'suspend_count': 0,
                'resume_count': 0,
                'latest_status': 'unknown',
                'latest_date': None,
                'suspend_records': []
            }
        
        try:
            # 默认查询最近30天
            if not end_date:
                end_date = datetime.now().strftime('%Y%m%d')
            if not start_date:
                start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
            
            # 查询停复牌记录
            df = self.api.suspend_d(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date
            )
            
            result = {
                'is_suspended': False,
                'suspend_count': 0,
                'resume_count': 0,
                'latest_status': 'trading',
                'latest_date': None,
                'suspend_records': []
            }
            
            if df is None or df.empty:
                logger.info(f"ℹ️ {ts_code} 近期无停复牌记录")
                return result
            
            # 统计停复牌次数
            suspend_records = []
            for _, row in df.iterrows():
                record = {
                    'date': row['trade_date'],
                    'type': '停牌' if row['suspend_type'] == 'S' else '复牌',
                    'timing': row.get('suspend_timing', '全天')
                }
                suspend_records.append(record)
                
                if row['suspend_type'] == 'S':
                    result['suspend_count'] += 1
                else:
                    result['resume_count'] += 1
            
            result['suspend_records'] = suspend_records
            
            # 确定最新状态
            if not df.empty:
                latest_row = df.iloc[0]  # Tushare数据通常按日期倒序
                result['latest_date'] = latest_row['trade_date']
                result['latest_status'] = 'suspended' if latest_row['suspend_type'] == 'S' else 'trading'
                result['is_suspended'] = (latest_row['suspend_type'] == 'S')
            
            logger.info(f"✅ {ts_code} 停复牌状态: {result['latest_status']}, "
                       f"停牌{result['suspend_count']}次, 复牌{result['resume_count']}次")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ 查询{ts_code}停复牌状态失败: {e}")
            return {
                'is_suspended': False,
                'suspend_count': 0,
                'resume_count': 0,
                'latest_status': 'error',
                'latest_date': None,
                'suspend_records': [],
                'error': str(e)
            }
    
    def get_suspend_risk_level(self, suspend_status: Dict) -> str:
        """
        根据停复牌状态评估风险等级
        
        Args:
            suspend_status: check_stock_suspend_status返回的结果
            
        Returns:
            'high'/'medium'/'low'
        """
        if suspend_status.get('is_suspended'):
            # 当前停牌 - 高风险
            return 'high'
        
        suspend_count = suspend_status.get('suspend_count', 0)
        
        if suspend_count >= 3:
            # 频繁停牌 - 中等风险
            return 'medium'
        elif suspend_count > 0:
            # 有停牌记录 - 低风险
            return 'low'
        else:
            # 无停牌记录 - 低风险
            return 'low'


# 全局监控器实例
_suspend_monitor = None


def get_suspend_monitor() -> SuspendMonitor:
    """获取全局停复牌监控器实例"""
    global _suspend_monitor
    if _suspend_monitor is None:
        _suspend_monitor = SuspendMonitor()
    return _suspend_monitor


# ==================== 便捷函数 ====================

def check_suspend_status(ts_code: str) -> Dict:
    """检查股票停复牌状态"""
    monitor = get_suspend_monitor()
    return monitor.check_stock_suspend_status(ts_code)


def get_today_suspended_stocks() -> Optional[List[str]]:
    """获取今日停牌股票代码列表"""
    monitor = get_suspend_monitor()
    df = monitor.get_suspend_stocks_today()
    
    if df is not None and not df.empty:
        return df['ts_code'].tolist()
    return []


def is_stock_suspended(ts_code: str) -> bool:
    """判断股票是否停牌"""
    status = check_suspend_status(ts_code)
    return status.get('is_suspended', False)
