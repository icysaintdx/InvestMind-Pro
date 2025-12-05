# 爬虫修复与集成 TODO

> 创建时间: 2025-12-04 04:51  
> 状态: 🚀 进行中

---

## 📋 总体规划

### 阶段1: 修复现有爬虫（本周）
### 阶段2: 集成简单API（本周）
### 阶段3: 集成复杂爬虫（下周）

---

## ✅ 阶段1: 修复现有6个爬虫

### 1.1 新浪财经新闻 ✅
- **状态**: 已成功
- **问题**: 时间字段为空
- **优先级**: 低
- **预计时间**: 30分钟

**任务**:
- [ ] 检查时间字段解析
- [ ] 优化数据格式

---

### 1.2 东方财富新闻 ⚠️
- **状态**: 返回0条
- **问题**: API可能变化
- **优先级**: 高
- **预计时间**: 2小时

**任务**:
- [ ] 检查API地址是否变化
- [ ] 测试API参数
- [ ] 更新请求参数
- [ ] 验证数据解析

**技术方案**:
```python
# 当前API
url = "https://emweb.securities.eastmoney.com/PC_HSF10/NewsBulletin/PageAjax"

# 需要检查:
# 1. URL是否正确
# 2. 参数格式是否变化
# 3. 返回数据结构是否变化
```

---

### 1.3 雪球评论 ❌
- **状态**: JSON解析错误
- **问题**: 反爬虫机制
- **优先级**: 中
- **预计时间**: 4小时

**任务**:
- [ ] 安装 curl_cffi
- [ ] 模拟真实浏览器TLS指纹
- [ ] 添加完整请求头
- [ ] 处理Cookie
- [ ] 控制请求频率

**技术方案**:
```python
from curl_cffi import requests

# 使用 curl_cffi 模拟真实浏览器
session = requests.Session(impersonate="chrome110")

headers = {
    'User-Agent': 'Mozilla/5.0 ...',
    'Referer': 'https://xueqiu.com/',
    'Cookie': '...'  # 需要获取真实Cookie
}
```

---

### 1.4 财联社快讯 ⚠️
- **状态**: 返回0条
- **问题**: API可能变化
- **优先级**: 中
- **预计时间**: 2小时

**任务**:
- [ ] 检查API地址
- [ ] 更新请求参数
- [ ] 验证数据解析

---

### 1.5 AKShare新闻 ❌
- **状态**: JSON解析错误
- **问题**: API返回格式问题
- **优先级**: 高
- **预计时间**: 1小时

**任务**:
- [ ] 检查AKShare版本
- [ ] 查看API文档
- [ ] 更新函数调用
- [ ] 测试数据获取

**技术方案**:
```python
import akshare as ak

# 检查可用的新闻接口
# ak.stock_news_em()  # 东方财富新闻
# ak.stock_news_sina() # 新浪新闻
```

---

### 1.6 Tushare新闻 ⚠️
- **状态**: 返回0条
- **问题**: 可能需要更高权限
- **优先级**: 中
- **预计时间**: 1小时

**任务**:
- [ ] 检查Tushare权限
- [ ] 查看API文档
- [ ] 测试不同接口
- [ ] 验证数据获取

**技术方案**:
```python
import tushare as ts

pro = ts.pro_api(token)

# 尝试不同接口
# pro.news()  # 新闻数据
# pro.major_news()  # 重大新闻
```

---

## 🚀 阶段2: 集成简单API（由简到难）

### 2.1 微博热搜API ⭐⭐⭐⭐⭐（最简单）
- **优先级**: 最高
- **难度**: ⭐
- **预计时间**: 1小时

**任务**:
- [ ] 创建 `weibo_hot_search.py`
- [ ] 实现数据获取
- [ ] 股票话题过滤
- [ ] 测试验证

**API地址**: https://api.aa1.cn/doc/weibo-rs.html

**代码示例**:
```python
import requests

class WeiboHotSearchAPI:
    """微博热搜API"""
    
    BASE_URL = "https://api.aa1.cn/api/weibo-rs"
    
    def get_hot_search(self):
        """获取微博热搜榜"""
        response = requests.get(self.BASE_URL)
        return response.json()
    
    def filter_stock_topics(self, hot_list):
        """过滤股票相关话题"""
        stock_keywords = ['股票', '股市', 'A股', '茅台', '比亚迪']
        filtered = []
        for item in hot_list:
            title = item.get('title', '')
            if any(kw in title for kw in stock_keywords):
                filtered.append(item)
        return filtered
```

---

### 2.2 百度热搜API ⭐⭐⭐⭐⭐
- **优先级**: 高
- **难度**: ⭐
- **预计时间**: 1小时

**任务**:
- [ ] 创建 `baidu_hot_search.py`
- [ ] 实现数据获取
- [ ] 股票关键词过滤
- [ ] 测试验证

**API地址**: https://api.aa1.cn/doc/baidu-rs.html

---

### 2.3 AKShare微博热议 ⭐⭐⭐⭐
- **优先级**: 高
- **难度**: ⭐⭐
- **预计时间**: 1小时

**任务**:
- [ ] 研究AKShare文档
- [ ] 实现 `stock_js_weibo_report()`
- [ ] 数据解析
- [ ] 测试验证

**代码示例**:
```python
import akshare as ak

def get_weibo_stock_report():
    """获取微博股票热议"""
    df = ak.stock_js_weibo_report()
    return df.to_dict('records')
```

---

### 2.4 知乎热搜API ⭐⭐⭐
- **优先级**: 中
- **难度**: ⭐⭐
- **预计时间**: 2小时

**任务**:
- [ ] 确认API地址
- [ ] 实现数据获取
- [ ] 股票话题过滤
- [ ] 测试验证

---

## 📅 时间表

### 第1天（今天）
- [x] 分析测试结果
- [x] 创建TODO文档
- [ ] 集成微博热搜API（1小时）
- [ ] 集成百度热搜API（1小时）
- [ ] 修复AKShare新闻（1小时）

### 第2天
- [ ] 修复东方财富新闻（2小时）
- [ ] 修复财联社快讯（2小时）
- [ ] 集成AKShare微博热议（1小时）
- [ ] 修复Tushare新闻（1小时）

### 第3天
- [ ] 修复雪球评论（4小时）
- [ ] 集成知乎热搜API（2小时）
- [ ] 优化新浪财经（1小时）

### 第4-5天
- [ ] 统一数据接口
- [ ] 前端集成
- [ ] 完整测试

---

## 🎯 成功标准

### 爬虫质量
- ✅ 成功率 > 80%
- ✅ 响应时间 < 5秒
- ✅ 数据完整性 > 90%

### API集成
- ✅ 微博热搜正常工作
- ✅ 百度热搜正常工作
- ✅ AKShare微博热议正常工作
- ✅ 知乎热搜正常工作

---

## 📝 详细任务清单

### 今天立即开始

#### Task 1: 集成微博热搜API ✅
**预计时间**: 1小时  
**文件**: `backend/dataflows/news/weibo_hot_search.py`

- [x] 创建文件
- [x] 实现 `WeiboHotSearchAPI` 类
- [x] 实现 `get_hot_search()` 方法
- [x] 实现 `filter_stock_topics()` 方法
- [x] 创建测试脚本 (`test_hot_search.py`)
- [ ] 测试验证 - 请运行: `python test_hot_search.py`

#### Task 2: 集成百度热搜API ⭐⭐⭐⭐⭐
**预计时间**: 1小时  
**文件**: `backend/dataflows/news/baidu_hot_search.py`

- [ ] 创建文件
- [ ] 实现 `BaiduHotSearchAPI` 类
- [ ] 实现 `get_hot_search()` 方法
- [ ] 实现 `filter_stock_keywords()` 方法
- [ ] 创建测试脚本
- [ ] 测试验证

#### Task 3: 修复AKShare新闻 ⭐⭐⭐⭐
**预计时间**: 1小时  
**文件**: `backend/dataflows/news/china_market_crawler.py`

- [ ] 检查AKShare版本
- [ ] 查看可用接口
- [ ] 更新 `get_akshare_news()` 方法
- [ ] 测试验证

---

### 明天继续

#### Task 4: 修复东方财富新闻 ⭐⭐⭐⭐
**预计时间**: 2小时

- [ ] 检查API地址
- [ ] 测试API参数
- [ ] 更新请求代码
- [ ] 验证数据解析
- [ ] 测试验证

#### Task 5: 修复财联社快讯 ⭐⭐⭐
**预计时间**: 2小时

- [ ] 检查API地址
- [ ] 更新请求参数
- [ ] 验证数据解析
- [ ] 测试验证

#### Task 6: 集成AKShare微博热议 ⭐⭐⭐⭐
**预计时间**: 1小时

- [ ] 研究AKShare文档
- [ ] 实现数据获取
- [ ] 数据解析
- [ ] 测试验证

---

## 🔧 技术准备

### 需要安装的库
```bash
# curl_cffi - 用于雪球反爬虫
pip install curl_cffi

# 确保AKShare和Tushare是最新版本
pip install --upgrade akshare
pip install --upgrade tushare
```

### 测试脚本模板
```python
#!/usr/bin/env python3
"""
测试热搜API
"""

def test_weibo_hot_search():
    """测试微博热搜"""
    from backend.dataflows.news.weibo_hot_search import WeiboHotSearchAPI
    
    api = WeiboHotSearchAPI()
    hot_list = api.get_hot_search()
    
    print(f"获取到 {len(hot_list)} 条热搜")
    
    # 过滤股票相关
    stock_topics = api.filter_stock_topics(hot_list)
    print(f"股票相关: {len(stock_topics)} 条")
    
    for topic in stock_topics[:5]:
        print(f"- {topic}")

if __name__ == '__main__':
    test_weibo_hot_search()
```

---

## 📊 进度跟踪

### 整体进度: 20%

- [x] 测试现有爬虫 - 100%
- [x] 分析问题 - 100%
- [x] 创建TODO - 100%
- [x] 集成微博热搜 - 100% ✅
- [ ] 集成百度热搜 - 0%
- [ ] 修复AKShare - 0%
- [ ] 修复东方财富 - 0%
- [ ] 修复财联社 - 0%
- [ ] 修复雪球 - 0%
- [ ] 修复Tushare - 0%
- [ ] 集成AKShare微博热议 - 0%
- [ ] 集成知乎热搜 - 0%

---

## 🎉 里程碑

### 里程碑1: 简单API集成（今天）
- [ ] 微博热搜API工作
- [ ] 百度热搜API工作
- [ ] 能过滤股票相关话题

### 里程碑2: 修复现有爬虫（明后天）
- [ ] 6个爬虫都能正常工作
- [ ] 成功率 > 80%

### 里程碑3: 完整集成（本周末）
- [ ] 所有数据源集成完成
- [ ] 统一数据接口
- [ ] 前端能展示

---

**现在立即开始：集成微博热搜API！** 🚀



一、核心数据源（风险合规 + 新闻舆情）⭐⭐⭐⭐⭐
1. 法律合规类
中国裁判文书网 - 诉讼、判决
证监会/交易所 - 监管处罚、立案调查
国家企业信用信息公示系统 - 行政处罚
企查查/天眼查API - 法律风险数据（付费）
2. 公司公告类
巨潮资讯网 - 官方公告、财报（最重要）
上交所/深交所 - 公告披露
3. 权威财经新闻
证券时报 - 权威财经新闻
中国证券报 - 权威财经新闻
财新网 - 深度报道
财联社 - 快讯（已有，需修复）
东方财富新闻 - 已有，需修复
4. 专业数据接口
Tushare - 新闻事件、公告（已有，需修复参数）
AKShare - 新闻数据（已有，需修复参数）
二、辅助数据源（社交媒体情绪）⭐⭐⭐
1. 投资者讨论
东方财富股吧 - 散户讨论
雪球 - 投资者社区（已有，需修复反爬虫）
同花顺股吧 - 散户讨论
2. 社交媒体热度
微博热搜API - 话题热度
百度热搜API - 搜索热度
知乎热搜 - 专业讨论
AKShare微博热议 - 股票热度排行
🎯 重新调整优先级
第一优先级：修复现有爬虫 ⭐⭐⭐⭐⭐
理由: 已经有代码，修复比新建快

修复测试脚本 - 移除 limit 参数
修复东方财富新闻 - API变化
修复财联社快讯 - API变化
修复雪球评论 - 反爬虫
第二优先级：核心风险合规数据 ⭐⭐⭐⭐⭐
理由: 这才是多维度风险分析的核心

巨潮资讯网爬虫 - 公司公告（最重要）
证券时报爬虫 - 权威新闻
中国裁判文书网 - 法律风险
证监会处罚公告 - 合规风险
第三优先级：社交媒体情绪 ⭐⭐⭐
理由: 辅助分析，不是核心

东方财富股吧 - 散户情绪
微博热搜API - 话题热度
百度热搜API - 搜索热度