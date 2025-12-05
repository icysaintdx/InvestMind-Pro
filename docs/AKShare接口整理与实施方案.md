# AKShare接口整理与实施方案

> 创建时间: 2025-12-04 05:04  
> 状态: 🎯 明确方向

---

## 🎯 核心策略

### 决策
1. ✅ **保留**: AKShare的稳定接口
2. ❌ **删除**: 自制的不稳定爬虫
3. ✅ **新增**: 热搜API接口（免费第三方）
4. ✅ **专注**: 法律合规 + 公司公告

---

## 📊 AKShare可用接口分类

### 一、综合财经新闻 ⭐⭐⭐⭐

| 接口名称 | 数据源 | 功能 | 优先级 |
|---------|-------|------|--------|
| `stock_info_cjzc_em` | 东方财富 | 财经早餐资讯 | 高 |
| `stock_info_global_em` | 东方财富 | 全球综合财经新闻 | 高 |
| `stock_info_global_sina` | 新浪财经 | 公开财经新闻 | 高 |
| `stock_info_global_futu` | 富途牛牛 | 全球财经新闻（含港美股） | 中 |
| `stock_info_global_ths` | 同花顺 | 全球财经新闻 | 中 |

### 二、证券专项新闻 ⭐⭐⭐⭐⭐（核心）

| 接口名称 | 数据源 | 功能 | 数据量 | 优先级 |
|---------|-------|------|--------|--------|
| `stock_news_em` | 东方财富 | **个股新闻**（指定股票代码） | 100条/次 | **最高** |
| `stock_info_broker_sina` | 新浪财经 | 证券原创新闻、券商解读 | - | 高 |

**重点**: `stock_news_em` 是个股舆情分析的核心接口！

### 三、快讯类新闻 ⭐⭐⭐⭐

| 接口名称 | 数据源 | 功能 | 数据量 | 优先级 |
|---------|-------|------|--------|--------|
| `stock_info_global_cls` | 财联社 | 电报快讯（突发消息） | 20条/次 | 高 |

**特点**: 时效性强，适合捕捉突发消息

### 四、微博热搜数据 ⭐⭐⭐

| 接口名称 | 数据源 | 功能 | 优先级 |
|---------|-------|------|--------|
| `stock_js_weibo_report` | 微博 | 股票热议排行 | 中 |

---

## 🔥 热搜API接口（第三方免费）

### 推荐使用的热搜API

| API | 数据源 | 费用 | 优先级 |
|-----|-------|------|--------|
| 微博热搜 | https://api.aa1.cn/api/weibo-rs | 免费 | 高 |
| 百度热搜 | https://api.aa1.cn/api/baidu-rs | 免费 | 高 |
| 知乎热搜 | https://api.aa1.cn/api/zhihu-rs | 免费 | 中 |

**用途**: 辅助判断市场关注度和热点题材

---

## 🚀 实施方案

### 阶段1: 清理与重构（今天，2小时）

#### 任务1: 删除不稳定的爬虫
```bash
# 删除或标记为废弃
backend/dataflows/news/china_market_crawler.py  # 删除
backend/dataflows/news/social_media_crawler.py  # 删除
backend/dataflows/news/weibo_hot_search.py      # 保留（使用第三方API）
```

#### 任务2: 创建新的AKShare接口封装
**文件**: `backend/dataflows/news/akshare_news_api.py`

```python
#!/usr/bin/env python3
"""
AKShare新闻接口封装
使用稳定的AKShare接口
"""

import akshare as ak
from typing import List, Dict, Any
from backend.utils.logging_config import get_logger

logger = get_logger("akshare_news")


class AKShareNewsAPI:
    """AKShare新闻API封装"""
    
    def __init__(self):
        logger.info(f"初始化AKShare新闻API，版本: {ak.__version__}")
    
    # ========== 核心接口 ==========
    
    def get_stock_news(self, symbol: str) -> List[Dict[str, Any]]:
        """
        获取个股新闻（最重要）
        接口: stock_news_em
        数据量: 100条/次
        """
        try:
            logger.info(f"获取{symbol}的个股新闻...")
            clean_symbol = symbol.replace('.SH', '').replace('.SZ', '')
            
            df = ak.stock_news_em(symbol=clean_symbol)
            
            if df is None or len(df) == 0:
                return []
            
            # 转换为标准格式
            news_list = []
            for _, row in df.iterrows():
                news_list.append({
                    'title': str(row.get('新闻标题', '')),
                    'content': str(row.get('新闻内容', '')),
                    'publish_time': str(row.get('发布时间', '')),
                    'source': str(row.get('文章来源', '东方财富')),
                    'url': str(row.get('新闻链接', ''))
                })
            
            logger.info(f"✅ 获取{symbol}新闻 {len(news_list)} 条")
            return news_list
            
        except Exception as e:
            logger.error(f"❌ 获取个股新闻失败: {e}")
            return []
    
    # ========== 综合新闻 ==========
    
    def get_morning_news(self) -> List[Dict[str, Any]]:
        """
        获取财经早餐
        接口: stock_info_cjzc_em
        """
        try:
            logger.info("获取财经早餐...")
            df = ak.stock_info_cjzc_em()
            
            if df is None or len(df) == 0:
                return []
            
            news_list = []
            for _, row in df.iterrows():
                news_list.append({
                    'title': str(row.get('标题', '')),
                    'content': str(row.get('内容', '')),
                    'publish_time': str(row.get('发布时间', '')),
                    'source': '东方财富',
                    'url': ''
                })
            
            logger.info(f"✅ 获取财经早餐 {len(news_list)} 条")
            return news_list
            
        except Exception as e:
            logger.error(f"❌ 获取财经早餐失败: {e}")
            return []
    
    def get_global_news_em(self) -> List[Dict[str, Any]]:
        """
        获取全球财经新闻（东方财富）
        接口: stock_info_global_em
        """
        try:
            logger.info("获取全球财经新闻（东方财富）...")
            df = ak.stock_info_global_em()
            
            if df is None or len(df) == 0:
                return []
            
            news_list = []
            for _, row in df.iterrows():
                news_list.append({
                    'title': str(row.get('标题', '')),
                    'content': str(row.get('内容', '')),
                    'publish_time': str(row.get('发布时间', '')),
                    'source': '东方财富',
                    'url': str(row.get('链接', ''))
                })
            
            logger.info(f"✅ 获取全球财经新闻 {len(news_list)} 条")
            return news_list
            
        except Exception as e:
            logger.error(f"❌ 获取全球财经新闻失败: {e}")
            return []
    
    def get_global_news_sina(self) -> List[Dict[str, Any]]:
        """
        获取全球财经新闻（新浪）
        接口: stock_info_global_sina
        """
        try:
            logger.info("获取全球财经新闻（新浪）...")
            df = ak.stock_info_global_sina()
            
            if df is None or len(df) == 0:
                return []
            
            news_list = []
            for _, row in df.iterrows():
                news_list.append({
                    'title': str(row.get('标题', '')),
                    'content': str(row.get('内容', '')),
                    'publish_time': str(row.get('发布时间', '')),
                    'source': '新浪财经',
                    'url': str(row.get('链接', ''))
                })
            
            logger.info(f"✅ 获取全球财经新闻（新浪） {len(news_list)} 条")
            return news_list
            
        except Exception as e:
            logger.error(f"❌ 获取全球财经新闻（新浪）失败: {e}")
            return []
    
    # ========== 快讯 ==========
    
    def get_cls_telegraph(self) -> List[Dict[str, Any]]:
        """
        获取财联社电报快讯
        接口: stock_info_global_cls
        数据量: 20条/次
        """
        try:
            logger.info("获取财联社电报快讯...")
            df = ak.stock_info_global_cls()
            
            if df is None or len(df) == 0:
                return []
            
            news_list = []
            for _, row in df.iterrows():
                news_list.append({
                    'title': str(row.get('标题', '')),
                    'content': str(row.get('内容', '')),
                    'publish_time': str(row.get('发布时间', '')),
                    'source': '财联社',
                    'url': ''
                })
            
            logger.info(f"✅ 获取财联社快讯 {len(news_list)} 条")
            return news_list
            
        except Exception as e:
            logger.error(f"❌ 获取财联社快讯失败: {e}")
            return []
    
    # ========== 微博热议 ==========
    
    def get_weibo_stock_hot(self) -> List[Dict[str, Any]]:
        """
        获取微博股票热议
        接口: stock_js_weibo_report
        """
        try:
            logger.info("获取微博股票热议...")
            df = ak.stock_js_weibo_report()
            
            if df is None or len(df) == 0:
                return []
            
            # 打印列名用于调试
            logger.info(f"微博热议数据列: {list(df.columns)}")
            
            hot_list = df.to_dict('records')
            
            logger.info(f"✅ 获取微博热议 {len(hot_list)} 条")
            return hot_list
            
        except Exception as e:
            logger.error(f"❌ 获取微博热议失败: {e}")
            return []


# 全局实例
_akshare_news_api = None

def get_akshare_news_api():
    """获取AKShare新闻API实例（单例）"""
    global _akshare_news_api
    if _akshare_news_api is None:
        _akshare_news_api = AKShareNewsAPI()
    return _akshare_news_api
```

#### 任务3: 创建热搜API接口
**文件**: `backend/dataflows/news/hot_search_api.py`

```python
#!/usr/bin/env python3
"""
热搜API接口
使用第三方免费API
"""

import requests
from typing import List, Dict, Any
from backend.utils.logging_config import get_logger

logger = get_logger("hot_search")


class HotSearchAPI:
    """热搜API"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # 股票关键词
        self.stock_keywords = [
            '股票', '股市', 'A股', '港股', '美股',
            '茅台', '比亚迪', '宁德时代', '腾讯', '阿里',
            '涨停', '跌停', '牛市', '熊市',
            '新能源', '芯片', '半导体', '医药', '白酒'
        ]
    
    def get_weibo_hot(self) -> List[Dict[str, Any]]:
        """获取微博热搜"""
        try:
            url = "https://api.aa1.cn/api/weibo-rs"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ 获取微博热搜成功")
                return data if isinstance(data, list) else data.get('data', [])
            else:
                logger.error(f"❌ 获取微博热搜失败: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"❌ 获取微博热搜失败: {e}")
            return []
    
    def get_baidu_hot(self) -> List[Dict[str, Any]]:
        """获取百度热搜"""
        try:
            url = "https://api.aa1.cn/api/baidu-rs"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ 获取百度热搜成功")
                return data if isinstance(data, list) else data.get('data', [])
            else:
                logger.error(f"❌ 获取百度热搜失败: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"❌ 获取百度热搜失败: {e}")
            return []
    
    def filter_stock_topics(self, hot_list: List[Dict]) -> List[Dict]:
        """过滤股票相关话题"""
        filtered = []
        for item in hot_list:
            title = str(item.get('title', '') or item.get('word', '') or item.get('query', ''))
            if any(kw in title for kw in self.stock_keywords):
                filtered.append(item)
        return filtered


# 全局实例
_hot_search_api = None

def get_hot_search_api():
    """获取热搜API实例（单例）"""
    global _hot_search_api
    if _hot_search_api is None:
        _hot_search_api = HotSearchAPI()
    return _hot_search_api
```

---

### 阶段2: 测试验证（今天，1小时）

创建测试脚本 `test_final_news_api.py`:

```python
#!/usr/bin/env python3
"""
测试最终的新闻API
"""

from backend.dataflows.news.akshare_news_api import get_akshare_news_api
from backend.dataflows.news.hot_search_api import get_hot_search_api

print("=" * 80)
print("🧪 测试AKShare新闻API")
print("=" * 80)

api = get_akshare_news_api()

# 测试1: 个股新闻（核心）
print("\n📰 测试1: 个股新闻")
news = api.get_stock_news("600519")
print(f"结果: {len(news)} 条")

# 测试2: 财经早餐
print("\n☕ 测试2: 财经早餐")
morning = api.get_morning_news()
print(f"结果: {len(morning)} 条")

# 测试3: 财联社快讯
print("\n⚡ 测试3: 财联社快讯")
cls = api.get_cls_telegraph()
print(f"结果: {len(cls)} 条")

# 测试4: 微博热议
print("\n🔥 测试4: 微博热议")
weibo = api.get_weibo_stock_hot()
print(f"结果: {len(weibo)} 条")

print("\n" + "=" * 80)
print("🧪 测试热搜API")
print("=" * 80)

hot_api = get_hot_search_api()

# 测试5: 微博热搜
print("\n📱 测试5: 微博热搜")
weibo_hot = hot_api.get_weibo_hot()
print(f"结果: {len(weibo_hot)} 条")
stock_topics = hot_api.filter_stock_topics(weibo_hot)
print(f"股票相关: {len(stock_topics)} 条")

# 测试6: 百度热搜
print("\n🔍 测试6: 百度热搜")
baidu_hot = hot_api.get_baidu_hot()
print(f"结果: {len(baidu_hot)} 条")
```

---

### 阶段3: 集成到统一API（明天，2小时）

创建统一的新闻数据接口，供前端调用。

---

## 📋 待删除的文件

```bash
# 不稳定的爬虫（删除）
backend/dataflows/news/china_market_crawler.py
backend/dataflows/news/social_media_crawler.py

# 测试失败的文件（删除）
backend/dataflows/news/akshare_provider.py
test_akshare.py
test_akshare_simple.py
check_akshare_api.py
diagnose_api.py
simple_test.py
fix_crawlers.py
```

---

## 📋 保留的文件

```bash
# 已验证可用（保留）
backend/dataflows/news/realtime_news.py
backend/dataflows/news/improved_sentiment_analysis.py

# 新创建（保留）
backend/dataflows/news/akshare_news_api.py
backend/dataflows/news/hot_search_api.py
backend/dataflows/news/weibo_hot_search.py  # 使用第三方API
```

---

## 🎯 最终目标

### 数据源架构
```
核心数据（AKShare）
├── 个股新闻（stock_news_em）⭐⭐⭐⭐⭐
├── 财经早餐（stock_info_cjzc_em）
├── 全球新闻（stock_info_global_em/sina）
├── 财联社快讯（stock_info_global_cls）
└── 微博热议（stock_js_weibo_report）

辅助数据（第三方API）
├── 微博热搜（api.aa1.cn）
├── 百度热搜（api.aa1.cn）
└── 知乎热搜（api.aa1.cn）

未来扩展（核心）
├── 中国裁判文书网（法律风险）
├── 巨潮资讯网（公司公告）
└── 证券时报（权威新闻）
```

---

**现在开始实施：创建新的AKShare接口封装！** 🚀
