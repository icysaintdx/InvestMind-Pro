#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tushare 新闻接口优化调用策略
解决每日40次 major_news 接口限制问题

策略:
1. 优先级队列 - 按重要性分配调用次数
2. 智能缓存 - 避免重复调用
3. 错峰调用 - 分散到不同时间段
4. 降级方案 - 额度用完时使用备用源
"""

import os
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# 缓存文件路径
CACHE_DIR = Path(__file__).parent / ".." / ".." / ".." / "data" / "news_storage"
CACHE_FILE = CACHE_DIR / "tushare_call_stats.json"

# 数据源优先级配置 (按重要性排序)
SOURCE_PRIORITY = {
    # source_id: (优先级, 单次获取条数, 权重)
    6: (1, 20, 8),   # 雪球 - 最重要，社区讨论价值高
    10: (2, 15, 6),  # 华尔街见闻 - 专业财经
    2: (3, 15, 5),   # 财联社 - 快速资讯
    7: (4, 10, 4),   # 第一财经
    1: (5, 10, 3),   # 东方财富
    4: (6, 8, 3),    # 新浪财经
    3: (7, 8, 2),    # 同花顺
    5: (8, 5, 1),    # 金融界
}

# 平台名称映射
SOURCE_NAMES = {
    0: "全平台聚合",
    1: "东方财富",
    2: "财联社",
    3: "同花顺",
    4: "新浪财经",
    5: "金融界",
    6: "雪球",
    7: "第一财经",
    8: "凤凰财经",
    9: "云财经",
    10: "华尔街见闻",
    11: "每日经济新闻",
    12: "证券时报",
    13: "中证网",
}


class TushareQuotaManager:
    """Tushare 调用额度管理器"""
    
    DAILY_LIMIT = 40  # 每日限制
    
    def __init__(self):
        self.cache_dir = CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.stats_file = CACHE_FILE
        self.stats = self._load_stats()
        
    def _load_stats(self) -> Dict:
        """加载调用统计"""
        if self.stats_file.exists():
            try:
                with open(self.stats_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"加载Tushare统计失败: {e}")
        
        return {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "calls": {},  # source_id -> call_count
            "total_calls": 0,
            "last_reset": datetime.now().isoformat()
        }
    
    def _save_stats(self):
        """保存调用统计"""
        try:
            with open(self.stats_file, 'w') as f:
                json.dump(self.stats, f, indent=2)
        except Exception as e:
            logger.warning(f"保存Tushare统计失败: {e}")
    
    def _check_and_reset(self):
        """检查是否需要重置每日统计"""
        today = datetime.now().strftime("%Y-%m-%d")
        if self.stats.get("date") != today:
            logger.info("Tushare调用额度已重置（新的一天）")
            self.stats = {
                "date": today,
                "calls": {},
                "total_calls": 0,
                "last_reset": datetime.now().isoformat()
            }
            self._save_stats()
    
    def get_remaining_quota(self) -> int:
        """获取剩余调用额度"""
        self._check_and_reset()
        return max(0, self.DAILY_LIMIT - self.stats.get("total_calls", 0))
    
    def get_source_call_count(self, source_id: int) -> int:
        """获取指定源的调用次数"""
        self._check_and_reset()
        return self.stats.get("calls", {}).get(str(source_id), 0)
    
    def record_call(self, source_id: int):
        """记录一次调用"""
        self._check_and_reset()
        calls = self.stats.get("calls", {})
        calls[str(source_id)] = calls.get(str(source_id), 0) + 1
        self.stats["calls"] = calls
        self.stats["total_calls"] = self.stats.get("total_calls", 0) + 1
        self._save_stats()
        logger.debug(f"Tushare调用记录: source_id={source_id}, 今日已用{self.stats['total_calls']}/{self.DAILY_LIMIT}")
    
    def get_optimized_sources(self, max_calls: int = None) -> List[Dict]:
        """
        获取优化后的数据源列表
        
        策略:
        1. 优先获取高优先级源
        2. 根据剩余额度动态分配
        3. 确保最重要的源至少有数据
        
        Returns:
            List[{"source_id": int, "limit": int, "name": str, "priority": int}]
        """
        self._check_and_reset()
        remaining = self.get_remaining_quota()
        
        if max_calls:
            remaining = min(remaining, max_calls)
        
        if remaining <= 0:
            logger.warning("Tushare今日额度已用完")
            return []
        
        # 按优先级排序
        sorted_sources = sorted(
            SOURCE_PRIORITY.items(),
            key=lambda x: (x[1][0], -x[1][2])  # 按优先级排序，相同优先级按权重
        )
        
        result = []
        calls_allocated = 0
        
        for source_id, (priority, default_limit, weight) in sorted_sources:
            if calls_allocated >= remaining:
                break
            
            # 检查今天是否已经调用过
            already_called = self.get_source_call_count(source_id)
            
            # 优先确保高优先级源至少有数据
            if priority <= 3 and already_called == 0:
                # 高优先级源，必须获取
                limit = default_limit
                result.append({
                    "source_id": source_id,
                    "limit": limit,
                    "name": SOURCE_NAMES.get(source_id, f"平台{source_id}"),
                    "priority": priority,
                    "must_fetch": True
                })
                calls_allocated += 1
            elif priority <= 5 and calls_allocated < remaining - 2:
                # 中等优先级，如果有余量就获取
                limit = min(default_limit, 10)
                result.append({
                    "source_id": source_id,
                    "limit": limit,
                    "name": SOURCE_NAMES.get(source_id, f"平台{source_id}"),
                    "priority": priority,
                    "must_fetch": False
                })
                calls_allocated += 1
            elif calls_allocated < remaining:
                # 低优先级，最后获取
                limit = min(default_limit, 5)
                result.append({
                    "source_id": source_id,
                    "limit": limit,
                    "name": SOURCE_NAMES.get(source_id, f"平台{source_id}"),
                    "priority": priority,
                    "must_fetch": False
                })
                calls_allocated += 1
        
        logger.info(f"Tushare优化策略: 剩余额度{remaining}, 计划获取{len(result)}个源")
        return result


# 全局配额管理器实例
_quota_manager = None

def get_quota_manager() -> TushareQuotaManager:
    """获取全局配额管理器"""
    global _quota_manager
    if _quota_manager is None:
        _quota_manager = TushareQuotaManager()
    return _quota_manager
