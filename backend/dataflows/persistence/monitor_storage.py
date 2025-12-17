"""
监控数据持久化存储
使用JSON文件存储监控配置和历史数据
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

from backend.utils.logging_config import get_logger

logger = get_logger("persistence.monitor")


class MonitorStorage:
    """监控数据存储"""
    
    def __init__(self, storage_dir: str = "data/monitor"):
        """
        初始化存储
        
        Args:
            storage_dir: 存储目录
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.config_file = self.storage_dir / "monitor_config.json"
        self.history_dir = self.storage_dir / "history"
        self.history_dir.mkdir(exist_ok=True)
        
        logger.info(f"✅ 监控存储初始化完成: {self.storage_dir}")
    
    def save_monitor_config(self, config: Dict):
        """
        保存监控配置
        
        Args:
            config: 监控配置字典
                {
                    'stocks': {
                        '600519.SH': {
                            'name': '贵州茅台',
                            'frequency': '1h',
                            'items': {...},
                            'created_at': '2024-12-17T...',
                            'updated_at': '2024-12-17T...'
                        }
                    }
                }
        """
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ 保存监控配置成功: {len(config.get('stocks', {}))}只股票")
            
        except Exception as e:
            logger.error(f"❌ 保存监控配置失败: {e}")
            raise
    
    def load_monitor_config(self) -> Dict:
        """
        加载监控配置
        
        Returns:
            监控配置字典
        """
        try:
            if not self.config_file.exists():
                logger.info("ℹ️ 监控配置文件不存在，返回空配置")
                return {'stocks': {}}
            
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            logger.info(f"✅ 加载监控配置成功: {len(config.get('stocks', {}))}只股票")
            return config
            
        except Exception as e:
            logger.error(f"❌ 加载监控配置失败: {e}")
            return {'stocks': {}}
    
    def add_monitored_stock(
        self, 
        ts_code: str, 
        name: str,
        frequency: str = '1h',
        items: Dict = None
    ):
        """
        添加监控股票
        
        Args:
            ts_code: 股票代码
            name: 股票名称
            frequency: 更新频率
            items: 监控项目
        """
        if items is None:
            items = {
                'news': True,
                'risk': True,
                'sentiment': True,
                'suspend': False
            }
        
        config = self.load_monitor_config()
        
        if 'stocks' not in config:
            config['stocks'] = {}
        
        config['stocks'][ts_code] = {
            'name': name,
            'frequency': frequency,
            'items': items,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        self.save_monitor_config(config)
        logger.info(f"➕ 添加监控股票: {name}({ts_code})")
    
    def remove_monitored_stock(self, ts_code: str):
        """移除监控股票"""
        config = self.load_monitor_config()
        
        if ts_code in config.get('stocks', {}):
            stock_name = config['stocks'][ts_code].get('name', ts_code)
            del config['stocks'][ts_code]
            self.save_monitor_config(config)
            logger.info(f"➖ 移除监控股票: {stock_name}({ts_code})")
        else:
            logger.warning(f"⚠️ 股票不在监控列表: {ts_code}")
    
    def get_monitored_stocks(self) -> Dict:
        """获取所有监控股票"""
        config = self.load_monitor_config()
        return config.get('stocks', {})
    
    def save_stock_history(
        self, 
        ts_code: str, 
        data: Dict
    ):
        """
        保存股票历史数据
        
        Args:
            ts_code: 股票代码
            data: 股票数据（包括风险分析、新闻、情绪等）
        """
        try:
            # 按日期组织历史数据
            today = datetime.now().strftime('%Y-%m-%d')
            history_file = self.history_dir / f"{ts_code}_{today}.json"
            
            # 加载当天已有数据
            if history_file.exists():
                with open(history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            else:
                history = {'ts_code': ts_code, 'date': today, 'records': []}
            
            # 添加新记录
            record = {
                'timestamp': datetime.now().isoformat(),
                'data': data
            }
            history['records'].append(record)
            
            # 保存
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
            
            logger.debug(f"✅ 保存{ts_code}历史数据成功")
            
        except Exception as e:
            logger.error(f"❌ 保存历史数据失败 {ts_code}: {e}")
    
    def load_stock_history(
        self, 
        ts_code: str, 
        date: Optional[str] = None
    ) -> List[Dict]:
        """
        加载股票历史数据
        
        Args:
            ts_code: 股票代码
            date: 日期（YYYY-MM-DD），默认今天
            
        Returns:
            历史记录列表
        """
        try:
            if date is None:
                date = datetime.now().strftime('%Y-%m-%d')
            
            history_file = self.history_dir / f"{ts_code}_{date}.json"
            
            if not history_file.exists():
                logger.debug(f"ℹ️ 历史数据文件不存在: {history_file}")
                return []
            
            with open(history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
            
            return history.get('records', [])
            
        except Exception as e:
            logger.error(f"❌ 加载历史数据失败 {ts_code}: {e}")
            return []
    
    def cleanup_old_history(self, days: int = 30):
        """
        清理旧的历史数据
        
        Args:
            days: 保留天数
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            deleted_count = 0
            
            for history_file in self.history_dir.glob("*.json"):
                # 从文件名提取日期
                try:
                    date_str = history_file.stem.split('_')[-1]
                    file_date = datetime.strptime(date_str, '%Y-%m-%d')
                    
                    if file_date < cutoff_date:
                        history_file.unlink()
                        deleted_count += 1
                        
                except Exception:
                    continue
            
            logger.info(f"🗑️ 清理历史数据: 删除{deleted_count}个文件")
            
        except Exception as e:
            logger.error(f"❌ 清理历史数据失败: {e}")


# 全局存储实例
_monitor_storage: Optional[MonitorStorage] = None


def get_monitor_storage() -> MonitorStorage:
    """获取全局监控存储实例"""
    global _monitor_storage
    if _monitor_storage is None:
        _monitor_storage = MonitorStorage()
    return _monitor_storage


# 便捷函数
def save_config(config: Dict):
    """保存监控配置"""
    storage = get_monitor_storage()
    storage.save_monitor_config(config)


def load_config() -> Dict:
    """加载监控配置"""
    storage = get_monitor_storage()
    return storage.load_monitor_config()


def add_stock(ts_code: str, name: str, frequency: str = '1h', items: Dict = None):
    """添加监控股票"""
    storage = get_monitor_storage()
    storage.add_monitored_stock(ts_code, name, frequency, items)


def remove_stock(ts_code: str):
    """移除监控股票"""
    storage = get_monitor_storage()
    storage.remove_monitored_stock(ts_code)
