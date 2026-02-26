# InvestMindPro 新闻数据源优化总结

## 优化完成时间
2026-02-20 21:20

## 优化内容

### 1. Tushare 接口调用策略优化

**问题**: Tushare major_news 接口每日限制40次，之前无策略导致额度快速耗尽

**解决方案**:
- 新建 `tushare_quota_manager.py` - 智能配额管理器
- 实现优先级队列：雪球(8) > 华尔街见闻(6) > 财联社(5) > 第一财经(4) > 东方财富(3) > ...
- 缓存机制：记录每日调用次数，自动重置
- 智能分配：优先确保高价值源有数据

**优化策略**:
```python
优先级排序:
1. 雪球 (priority=1, must_fetch=True)     - 社区讨论价值高
2. 华尔街见闻 (priority=2)               - 专业财经
3. 财联社 (priority=3)                   - 快速资讯
4. 第一财经 (priority=4)
5. 东方财富 (priority=5)
6. 新浪财经 (priority=6)
...

分配逻辑:
- 高优先级(priority<=3): 必须获取，使用默认条数
- 中优先级(priority<=5): 有余量时获取，限制10条
- 低优先级: 最后获取，限制5条
```

### 2. 新增备用新闻数据源

**问题**: Tushare 额度用完后，部分数据源为0

**解决方案**:
- 新建 `alternative_news_api.py` - 备用免费API聚合器
- 包含以下免费数据源:
  - 网易财经
  - 腾讯财经
  - 搜狐财经
  - 和讯网
  - 中证网

**特点**:
- 异步并发获取，速度快
- 自动去重（按标题）
- 失败自动降级，不影响其他源

### 3. 配置调整

**修改文件**: `news_config.py`
- 禁用 Tushare 付费接口（与免费接口共享40次额度）
- 保留免费聚合接口（使用优化策略）

### 4. 监控中心更新

**修改文件**: `news_monitor_center.py`
- 集成新的配额管理器
- 添加备用数据源调用
- 优化错误处理逻辑

## 当前数据源状态

### 正常工作（AKShare）
| 数据源 | 数量 | 来源 |
|--------|------|------|
| 东财公告 | 2057 | AKShare |
| 微博热议 | 1051 | AKShare |
| 巨潮资讯 | 1027 | AKShare + CNInfo API |
| 新浪财经 | 729 | AKShare |
| 东方财富 | 248 | AKShare |
| 百度财经 | 99 | AKShare |
| 同花顺 | 96 | AKShare |
| 富途牛牛 | 76 | AKShare |
| 财联社 | 116 | AKShare |
| 新闻联播 | 12 | AKShare |
| 财经早餐 | 10 | AKShare |
| 巨潮高管变动 | 85 | 巨潮API |

### Tushare 源（明日恢复）
- 雪球、华尔街见闻、第一财经、东方财富等
- 受40次/日限制，优化后优先获取高价值源

### 备用源（新增）
- 网易财经、腾讯财经、搜狐财经、和讯网、中证网
- 当 Tushare 额度用完时自动启用

## 效果预期

1. **今日**: 已有3100+条新闻，备用源补充
2. **明日**: Tushare 额度重置，优先获取雪球+华尔街见闻+财联社
3. **长期**: 智能分配40次额度，确保最重要的源有数据

## 文件变更

```
backend/dataflows/news/
├── tushare_quota_manager.py      # 新增: 配额管理器
└── alternative_news_api.py       # 新增: 备用API

backend/services/news_center/
├── news_monitor_center.py        # 修改: 集成优化策略
└── news_config.py                # 修改: 禁用付费接口
```

## 后续建议

1. **监控额度使用**: 查看 `data/news_storage/tushare_call_stats.json`
2. **调整优先级**: 如需调整，修改 `tushare_quota_manager.py` 的 `SOURCE_PRIORITY`
3. **添加更多备用源**: 可在 `alternative_news_api.py` 中添加其他免费API
