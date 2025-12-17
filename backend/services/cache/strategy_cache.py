"""
分层缓存系统
L1: 内存缓存（最快，5分钟）
L2: Redis缓存（快，1小时）
L3: 文件缓存（慢，24小时）
"""

import json
import hashlib
import pickle
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class StrategyCache:
    """策略选择缓存"""
    
    def __init__(self):
        # L1: 内存缓存
        self.memory_cache: Dict[str, tuple] = {}  # {key: (value, expire_time)}
        self.l1_ttl = timedelta(minutes=5)
        
        # L2: Redis缓存（可选）
        self.redis_client = None
        self.l2_ttl = timedelta(hours=1)
        self._init_redis()
        
        # L3: 文件缓存
        self.cache_dir = Path(__file__).parent.parent.parent.parent / "cache" / "strategy"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.l3_ttl = timedelta(hours=24)
        
        logger.info("策略缓存系统初始化完成")
    
    def _init_redis(self):
        """初始化Redis客户端"""
        try:
            import redis
            import os
            
            redis_host = os.getenv("REDIS_HOST", "localhost")
            redis_port = int(os.getenv("REDIS_PORT", 6379))
            redis_db = int(os.getenv("REDIS_DB", 0))
            
            self.redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                decode_responses=False  # 使用二进制模式
            )
            
            # 测试连接
            self.redis_client.ping()
            logger.info(f"Redis连接成功: {redis_host}:{redis_port}")
            
        except Exception as e:
            logger.warning(f"Redis初始化失败，将跳过L2缓存: {e}")
            self.redis_client = None
    
    def _generate_cache_key(
        self,
        stock_analysis: Dict[str, Any],
        market_data: Dict[str, Any],
        news_sentiment: float
    ) -> str:
        """生成缓存键"""
        # 提取关键信息
        key_data = {
            "code": stock_analysis.get("code"),
            "risk_level": stock_analysis.get("risk_level"),
            "period": stock_analysis.get("period_suggestion"),
            "trend": market_data.get("trend"),
            "volatility": round(market_data.get("volatility", 0), 3),
            "sentiment": round(news_sentiment, 2)
        }
        
        # 生成MD5哈希
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(
        self,
        stock_analysis: Dict[str, Any],
        market_data: Dict[str, Any],
        news_sentiment: float
    ) -> Optional[Dict[str, Any]]:
        """
        获取缓存的策略选择结果
        
        Returns:
            缓存的结果，如果未命中返回None
        """
        cache_key = self._generate_cache_key(stock_analysis, market_data, news_sentiment)
        
        # L1: 内存缓存
        result = self._get_from_l1(cache_key)
        if result is not None:
            logger.info(f"L1缓存命中: {cache_key[:8]}")
            return result
        
        # L2: Redis缓存
        result = self._get_from_l2(cache_key)
        if result is not None:
            logger.info(f"L2缓存命中: {cache_key[:8]}")
            # 回写到L1
            self._set_to_l1(cache_key, result)
            return result
        
        # L3: 文件缓存
        result = self._get_from_l3(cache_key)
        if result is not None:
            logger.info(f"L3缓存命中: {cache_key[:8]}")
            # 回写到L2和L1
            self._set_to_l2(cache_key, result)
            self._set_to_l1(cache_key, result)
            return result
        
        logger.debug(f"缓存未命中: {cache_key[:8]}")
        return None
    
    def set(
        self,
        stock_analysis: Dict[str, Any],
        market_data: Dict[str, Any],
        news_sentiment: float,
        result: Dict[str, Any]
    ):
        """
        设置缓存
        
        Args:
            stock_analysis: 股票分析
            market_data: 市场数据
            news_sentiment: 新闻情绪
            result: 策略选择结果
        """
        cache_key = self._generate_cache_key(stock_analysis, market_data, news_sentiment)
        
        # 写入所有层级
        self._set_to_l1(cache_key, result)
        self._set_to_l2(cache_key, result)
        self._set_to_l3(cache_key, result)
        
        logger.info(f"缓存已设置: {cache_key[:8]}")
    
    def _get_from_l1(self, key: str) -> Optional[Dict[str, Any]]:
        """从L1内存缓存获取"""
        if key in self.memory_cache:
            value, expire_time = self.memory_cache[key]
            if datetime.now() < expire_time:
                return value
            else:
                # 过期，删除
                del self.memory_cache[key]
        return None
    
    def _set_to_l1(self, key: str, value: Dict[str, Any]):
        """设置到L1内存缓存"""
        expire_time = datetime.now() + self.l1_ttl
        self.memory_cache[key] = (value, expire_time)
        
        # 清理过期缓存
        self._cleanup_l1()
    
    def _cleanup_l1(self):
        """清理L1过期缓存"""
        now = datetime.now()
        expired_keys = [
            k for k, (_, expire_time) in self.memory_cache.items()
            if now >= expire_time
        ]
        for k in expired_keys:
            del self.memory_cache[k]
    
    def _get_from_l2(self, key: str) -> Optional[Dict[str, Any]]:
        """从L2 Redis缓存获取"""
        if self.redis_client is None:
            return None
        
        try:
            data = self.redis_client.get(f"strategy:{key}")
            if data:
                return pickle.loads(data)
        except Exception as e:
            logger.error(f"L2缓存读取失败: {e}")
        
        return None
    
    def _set_to_l2(self, key: str, value: Dict[str, Any]):
        """设置到L2 Redis缓存"""
        if self.redis_client is None:
            return
        
        try:
            data = pickle.dumps(value)
            self.redis_client.setex(
                f"strategy:{key}",
                int(self.l2_ttl.total_seconds()),
                data
            )
        except Exception as e:
            logger.error(f"L2缓存写入失败: {e}")
    
    def _get_from_l3(self, key: str) -> Optional[Dict[str, Any]]:
        """从L3文件缓存获取"""
        cache_file = self.cache_dir / f"{key}.json"
        
        if not cache_file.exists():
            return None
        
        try:
            # 检查文件是否过期
            mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
            if datetime.now() - mtime > self.l3_ttl:
                cache_file.unlink()  # 删除过期文件
                return None
            
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except Exception as e:
            logger.error(f"L3缓存读取失败: {e}")
            return None
    
    def _set_to_l3(self, key: str, value: Dict[str, Any]):
        """设置到L3文件缓存"""
        cache_file = self.cache_dir / f"{key}.json"
        
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(value, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"L3缓存写入失败: {e}")
    
    def clear(self):
        """清空所有缓存"""
        # 清空L1
        self.memory_cache.clear()
        
        # 清空L2
        if self.redis_client:
            try:
                keys = self.redis_client.keys("strategy:*")
                if keys:
                    self.redis_client.delete(*keys)
            except Exception as e:
                logger.error(f"清空L2缓存失败: {e}")
        
        # 清空L3
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
        except Exception as e:
            logger.error(f"清空L3缓存失败: {e}")
        
        logger.info("所有缓存已清空")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        stats = {
            "l1_size": len(self.memory_cache),
            "l1_ttl_minutes": self.l1_ttl.total_seconds() / 60,
            "l2_available": self.redis_client is not None,
            "l2_ttl_hours": self.l2_ttl.total_seconds() / 3600,
            "l3_files": len(list(self.cache_dir.glob("*.json"))),
            "l3_ttl_hours": self.l3_ttl.total_seconds() / 3600
        }
        
        return stats


# 全局缓存实例
_cache_instance = None


def get_strategy_cache() -> StrategyCache:
    """获取策略缓存单例"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = StrategyCache()
    return _cache_instance


# 测试函数
def test_cache():
    """测试缓存系统"""
    print("=" * 60)
    print("策略缓存系统测试")
    print("=" * 60)
    
    cache = get_strategy_cache()
    
    # 测试数据
    stock_analysis = {
        "code": "600519",
        "risk_level": "medium",
        "period_suggestion": 15
    }
    
    market_data = {
        "trend": "up",
        "volatility": 0.05
    }
    
    news_sentiment = 0.6
    
    result = {
        "selected_strategy_id": "vegas_adx",
        "selected_strategy_name": "Vegas+ADX策略",
        "score": 85.0
    }
    
    # 测试1：设置缓存
    print("\n【测试1】设置缓存")
    cache.set(stock_analysis, market_data, news_sentiment, result)
    print("✅ 缓存已设置")
    
    # 测试2：获取缓存（L1命中）
    print("\n【测试2】获取缓存（应该L1命中）")
    cached_result = cache.get(stock_analysis, market_data, news_sentiment)
    if cached_result:
        print(f"✅ 缓存命中: {cached_result['selected_strategy_name']}")
    else:
        print("❌ 缓存未命中")
    
    # 测试3：清空L1，测试L3
    print("\n【测试3】清空L1，测试L3回写")
    cache.memory_cache.clear()
    cached_result = cache.get(stock_analysis, market_data, news_sentiment)
    if cached_result:
        print(f"✅ L3缓存命中并回写: {cached_result['selected_strategy_name']}")
    else:
        print("❌ L3缓存未命中")
    
    # 测试4：统计信息
    print("\n【测试4】缓存统计")
    stats = cache.get_stats()
    print(f"L1大小: {stats['l1_size']}")
    print(f"L1 TTL: {stats['l1_ttl_minutes']}分钟")
    print(f"L2可用: {stats['l2_available']}")
    print(f"L3文件数: {stats['l3_files']}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    test_cache()
