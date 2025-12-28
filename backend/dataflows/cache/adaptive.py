#!/usr/bin/env python3
"""
自适应缓存系统
根据数据库可用性自动选择最佳缓存策略
"""

import os
import json
import pickle
import hashlib
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional, Union
import pandas as pd

class AdaptiveCacheSystem:
    """自适应缓存系统"""
    
    def __init__(self, cache_dir: str = None):
        self.logger = logging.getLogger(__name__)

        # 数据库管理器已移除，使用环境变量配置
        self.db_manager = None

        # 设置缓存目录
        if cache_dir is None:
            # 默认使用 data/cache 目录
            cache_dir = "data/cache"
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # 获取配置（使用默认配置，因为数据库管理器已移除）
        self.config = {
            "cache": {
                "primary_backend": "file",
                "fallback_enabled": True,
                "ttl_settings": {
                    "china_stock_data": 7200,
                    "us_stock_data": 7200,
                    "china_news_data": 3600,
                    "us_news_data": 3600
                }
            }
        }
        self.cache_config = self.config["cache"]
        
        # 初始化缓存后端
        self.primary_backend = self.cache_config["primary_backend"]
        self.fallback_enabled = self.cache_config["fallback_enabled"]
        
        self.logger.info(f"自适应缓存系统初始化 - 主要后端: {self.primary_backend}")
    
    def _get_cache_key(self, symbol: str, start_date: str = "", end_date: str = "", 
                      data_source: str = "default", data_type: str = "stock_data") -> str:
        """生成缓存键"""
        key_data = f"{symbol}_{start_date}_{end_date}_{data_source}_{data_type}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _get_ttl_seconds(self, symbol: str, data_type: str = "stock_data") -> int:
        """获取TTL秒数"""
        # 判断市场类型
        if len(symbol) == 6 and symbol.isdigit():
            market = "china"
        else:
            market = "us"
        
        # 获取TTL配置
        ttl_key = f"{market}_{data_type}"
        ttl_seconds = self.cache_config["ttl_settings"].get(ttl_key, 7200)
        return ttl_seconds
    
    def _is_cache_valid(self, cache_time: datetime, ttl_seconds: int) -> bool:
        """检查缓存是否有效"""
        if cache_time is None:
            return False
        
        expiry_time = cache_time + timedelta(seconds=ttl_seconds)
        return datetime.now() < expiry_time
    
    def _save_to_file(self, cache_key: str, data: Any, metadata: Dict) -> bool:
        """保存到文件缓存"""
        try:
            cache_file = self.cache_dir / f"{cache_key}.pkl"
            cache_data = {
                'data': data,
                'metadata': metadata,
                'timestamp': datetime.now(),
                'backend': 'file'
            }
            
            with open(cache_file, 'wb') as f:
                pickle.dump(cache_data, f)
            
            self.logger.debug(f"文件缓存保存成功: {cache_key}")
            return True
            
        except Exception as e:
            self.logger.error(f"文件缓存保存失败: {e}")
            return False
    
    def _load_from_file(self, cache_key: str) -> Optional[Dict]:
        """从文件缓存加载"""
        try:
            cache_file = self.cache_dir / f"{cache_key}.pkl"
            if not cache_file.exists():
                return None
            
            with open(cache_file, 'rb') as f:
                cache_data = pickle.load(f)
            
            self.logger.debug(f"文件缓存加载成功: {cache_key}")
            return cache_data
            
        except Exception as e:
            self.logger.error(f"文件缓存加载失败: {e}")
            return None
    
    def _save_to_redis(self, cache_key: str, data: Any, metadata: Dict, ttl_seconds: int) -> bool:
        """保存到Redis缓存"""
        # Redis 功能已移除
        return False
    
    def _load_from_redis(self, cache_key: str) -> Optional[Dict]:
        """从Redis缓存加载"""
        # Redis 功能已移除
        return None
    
    def _save_to_mongodb(self, cache_key: str, data: Any, metadata: Dict, ttl_seconds: int) -> bool:
        """保存到MongoDB缓存"""
        # MongoDB 功能已移除
        return False
    
    def _load_from_mongodb(self, cache_key: str) -> Optional[Dict]:
        """从MongoDB缓存加载"""
        # MongoDB 功能已移除
        return None
    
    def save_data(self, symbol: str, data: Any, start_date: str = "", end_date: str = "", 
                  data_source: str = "default", data_type: str = "stock_data") -> str:
        """保存数据到缓存"""
        # 生成缓存键
        cache_key = self._get_cache_key(symbol, start_date, end_date, data_source, data_type)
        
        # 准备元数据
        metadata = {
            'symbol': symbol,
            'start_date': start_date,
            'end_date': end_date,
            'data_source': data_source,
            'data_type': data_type
        }
        
        # 获取TTL
        ttl_seconds = self._get_ttl_seconds(symbol, data_type)
        
        # 根据主要后端保存
        success = False
        
        if self.primary_backend == "redis":
            success = self._save_to_redis(cache_key, data, metadata, ttl_seconds)
        elif self.primary_backend == "mongodb":
            success = self._save_to_mongodb(cache_key, data, metadata, ttl_seconds)
        elif self.primary_backend == "file":
            success = self._save_to_file(cache_key, data, metadata)
        
        # 如果主要后端失败，使用降级策略
        if not success and self.fallback_enabled:
            self.logger.warning(f"主要后端({self.primary_backend})保存失败，使用文件缓存降级")
            success = self._save_to_file(cache_key, data, metadata)
        
        if success:
            self.logger.info(f"数据缓存成功: {symbol} -> {cache_key} (后端: {self.primary_backend})")
        else:
            self.logger.error(f"数据缓存失败: {symbol}")
        
        return cache_key
    
    def load_data(self, cache_key: str) -> Optional[Any]:
        """从缓存加载数据"""
        cache_data = None
        
        # 根据主要后端加载
        if self.primary_backend == "redis":
            cache_data = self._load_from_redis(cache_key)
        elif self.primary_backend == "mongodb":
            cache_data = self._load_from_mongodb(cache_key)
        elif self.primary_backend == "file":
            cache_data = self._load_from_file(cache_key)
        
        # 如果主要后端失败，尝试降级
        if not cache_data and self.fallback_enabled:
            self.logger.debug(f"主要后端({self.primary_backend})加载失败，尝试文件缓存")
            cache_data = self._load_from_file(cache_key)
        
        if not cache_data:
            return None
        
        # 检查缓存是否有效（仅对文件缓存，数据库缓存有自己的TTL机制）
        if cache_data.get('backend') == 'file':
            symbol = cache_data['metadata'].get('symbol', '')
            data_type = cache_data['metadata'].get('data_type', 'stock_data')
            ttl_seconds = self._get_ttl_seconds(symbol, data_type)
            
            if not self._is_cache_valid(cache_data['timestamp'], ttl_seconds):
                self.logger.debug(f"文件缓存已过期: {cache_key}")
                return None
        
        return cache_data['data']
    
    def find_cached_data(self, symbol: str, start_date: str = "", end_date: str = "", 
                        data_source: str = "default", data_type: str = "stock_data") -> Optional[str]:
        """查找缓存的数据"""
        cache_key = self._get_cache_key(symbol, start_date, end_date, data_source, data_type)
        
        # 检查缓存是否存在且有效
        if self.load_data(cache_key) is not None:
            return cache_key
        
        return None
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        # 标准统计格式
        stats = {
            'total_files': 0,
            'stock_data_count': 0,
            'news_count': 0,
            'fundamentals_count': 0,
            'total_size': 0,  # 字节
            'total_size_mb': 0,  # MB
            'skipped_count': 0
        }

        # 后端信息
        backend_info = {
            'primary_backend': self.primary_backend,
            'fallback_enabled': self.fallback_enabled,
            'database_available': False,
            'mongodb_available': False,
            'redis_available': False,
            'file_cache_directory': str(self.cache_dir),
            'file_cache_count': len(list(self.cache_dir.glob("*.pkl"))),
        }

        total_size_bytes = 0

        # 文件缓存统计
        if self.primary_backend == 'file' or self.fallback_enabled:
            for pkl_file in self.cache_dir.glob("*.pkl"):
                try:
                    total_size_bytes += pkl_file.stat().st_size
                except:
                    pass

        # 设置总大小
        stats['total_size'] = total_size_bytes
        stats['total_size_mb'] = round(total_size_bytes / (1024 * 1024), 2)

        # 添加后端详细信息
        stats['backend_info'] = backend_info

        return stats
    
    def clear_expired_cache(self):
        """清理过期缓存"""
        self.logger.info("开始清理过期缓存...")
        
        # 清理文件缓存
        cleared_files = 0
        for cache_file in self.cache_dir.glob("*.pkl"):
            try:
                with open(cache_file, 'rb') as f:
                    cache_data = pickle.load(f)
                
                symbol = cache_data['metadata'].get('symbol', '')
                data_type = cache_data['metadata'].get('data_type', 'stock_data')
                ttl_seconds = self._get_ttl_seconds(symbol, data_type)
                
                if not self._is_cache_valid(cache_data['timestamp'], ttl_seconds):
                    cache_file.unlink()
                    cleared_files += 1
                    
            except Exception as e:
                self.logger.error(f"清理缓存文件失败 {cache_file}: {e}")
        
        self.logger.info(f"文件缓存清理完成，删除 {cleared_files} 个过期文件")
        
        # MongoDB会自动清理过期文档（通过expires_at字段）
        # Redis会自动清理过期键


# 全局缓存系统实例
_cache_system = None

def get_cache_system() -> AdaptiveCacheSystem:
    """获取全局自适应缓存系统实例"""
    global _cache_system
    if _cache_system is None:
        _cache_system = AdaptiveCacheSystem()
    return _cache_system
