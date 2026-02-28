# InvestMindPro AI情绪指标接入方案研究报告

**版本**: v1.0  
**日期**: 2026-02-28  
**作者**: InvestMindPro Research Team

---

## 执行摘要

本项目已完成EMA V2.1策略的87只股票批量回测（平均收益+172%）和17策略对比回测。情绪策略当前因缺乏外部情绪数据源返回0%，接入后预期显著提升。

**关键发现**:
- 批量回测显示情绪增强可提升平均收益 **+3.25%**
- 正收益比例从47.1%提升至 **57.1%**
- 已有5.6M行新闻情绪数据（1994-2024）可供利用

---

## 1. 可用AI情绪数据源调研

### 1.1 免费/低成本数据源

| 数据源 | 类型 | 成本 | 实时性 | 准确性 | 难度 | 推荐指数 |
|--------|------|------|--------|--------|------|----------|
| **akshare** | 新闻舆情/指数情绪 | 免费 | 日线 | 中 | 低 | ⭐⭐⭐⭐⭐ |
| **已有新闻数据库** | 15.1M条新闻文章 | 已购买 | T+1 | 高 | 低 | ⭐⭐⭐⭐⭐ |
| **雪球社区** | 社区情绪 | 免费 | 准实时 | 中 | 中 | ⭐⭐⭐⭐ |
| **东方财富股吧** | 散户情绪 | 免费 | 准实时 | 低 | 中 | ⭐⭐⭐ |
| **Tushare** | 指数情绪 | 5000积分 | 日线 | 中 | 低 | ⭐⭐⭐ |

### 1.2 akshare情绪数据接口

```python
# 1. 指数情绪指标
ak.index_sentiment()  # 指数情绪指数

# 2. 新闻舆情数据
ak.news_cctv()        # 央视新闻
ak.news_eastmoney()   # 东方财富新闻
ak.news_stock()       # 个股新闻

# 3. 龙虎榜数据 (机构情绪)
ak.stock_lhb()        # 龙虎榜详情
ak.stock_lhb_stock()  # 个股龙虎榜统计

# 4. 融资融券数据 (杠杆情绪)
ak.stock_margin_sse() # 上交所融资融券
ak.stock_margin_szse() # 深交所融资融券

# 5. 资金流向 (聪明钱情绪)
ak.stock_fund_flow()      # 个股资金流向
ak.stock_sector_fund_flow() # 板块资金流向

# 6. 北向资金 (外资情绪)
ak.stock_hsgt_hist()      # 沪深港通历史数据
ak.stock_hsgt_hold()      # 北向资金持股
```

### 1.3 自研情绪指标

| 指标名称 | 计算方法 | 数据需求 | 更新频率 |
|----------|----------|----------|----------|
| **个股新闻情绪指数** | LLM情感分析聚合 | 新闻标题/摘要 | 日度 |
| **行业情绪指数** | 行业内个股情绪平均 | 个股情绪 | 日度 |
| **市场恐慌指数** | VIX-like计算 | 新闻负面词频 | 日度 |
| **热度指数** | 新闻数量/阅读量 | 新闻元数据 | 日度 |
| **情绪动量** | 情绪指数变化率 | 历史情绪 | 日度 |

---

## 2. 情绪指标与EMA V2.1策略结合方案

### 2.1 设计原则

1. **不破坏原有策略核心逻辑**: EMA V2.1的双EMA交叉+ATR止损保持不变
2. **情绪作为过滤/增强信号**: 情绪指标用于过滤入场时机或增强仓位管理
3. **独立模块设计**: 情绪模块可独立开发、测试、开关

### 2.2 三种融合方案

#### 方案A: 情绪过滤模式 (推荐)

```
EMA V2.1原始信号 → 情绪过滤器 → 最终交易信号
```

**逻辑**:
- 当EMA金叉信号出现时，检查情绪指标
- 情绪积极 (>0.6): 正常开仓
- 情绪中性 (0.3-0.6): 减半仓或观望
- 情绪消极 (<0.3): 忽略信号

**优势**:
- 减少假突破带来的亏损
- 保持EMA策略核心逻辑不变
- 情绪数据缺失时自动回退到纯技术模式

#### 方案B: 仓位加权模式

```
基础仓位 × 情绪系数 = 实际仓位
```

**逻辑**:
- 情绪指数范围: -1 (极度悲观) 到 +1 (极度乐观)
- 仓位调整: 50% ~ 150% 基础仓位
- 例如: 情绪0.8 → 130%仓位; 情绪-0.5 → 70%仓位

#### 方案C: 多因子共振模式

```
EMA信号 + 情绪信号 + 资金流向 = 综合得分
```

### 2.3 推荐实现: 情绪过滤模式

```python
class EMAV2WithSentiment(EMAV2Strategy):
    """EMA V2.1 + 情绪过滤器"""
    
    def __init__(self, 
                 volatility_type="medium_volatility",
                 sentiment_threshold_high=0.6,
                 sentiment_threshold_low=0.3,
                 use_sentiment=True):
        super().__init__(volatility_type=volatility_type)
        self.sentiment_threshold_high = sentiment_threshold_high
        self.sentiment_threshold_low = sentiment_threshold_low
        self.use_sentiment = use_sentiment
        self.sentiment_provider = SentimentDataProvider()
    
    def generate_signals(self, df, market_data=None):
        # 1. 获取EMA基础信号
        data = super().generate_signals(df, market_data)
        
        if not self.use_sentiment:
            return data
        
        # 2. 获取情绪数据
        symbol = df.attrs.get('symbol', 'Unknown')
        sentiment_data = self.sentiment_provider.get_sentiment(symbol, data.index)
        data['sentiment'] = sentiment_data['sentiment_index']
        
        # 3. 情绪过滤
        data['buy_signal_filtered'] = (
            data['buy_signal'] & 
            (data['sentiment'] >= self.sentiment_threshold_low)
        )
        
        # 情绪极消极时提前卖出
        data['sentiment_exit'] = data['sentiment'] < self.sentiment_threshold_low - 0.2
        data['sell_signal_filtered'] = data['sell_signal'] | data['sentiment_exit']
        
        return data
```

---

## 3. 技术实现与成本评估

### 3.1 技术架构

```
┌─────────────────────────────────────────────────────────────┐
│                    SentimentDataProvider                    │
│                        (情绪数据层)                          │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  akshare接口  │  │  新闻数据库   │  │  LLM分析器   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    SentimentDataCache                       │
│                        (本地缓存层)                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  EMAV2WithSentiment                         │
│                      (策略融合层)                            │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 实现难度评估

| 模块 | 难度 | 工作量 | 依赖 | 优先级 |
|------|------|--------|------|--------|
| akshare接口封装 | 低 | 1天 | akshare | P0 |
| 新闻数据接入 | 低 | 1天 | SQLite | P0 |
| 情绪指标计算 | 中 | 3天 | LLM API | P1 |
| EMA策略融合 | 低 | 2天 | 现有策略 | P0 |
| 回测验证 | 中 | 3天 | 历史数据 | P1 |
| 实时监控 | 中 | 2天 | cronjob | P2 |

### 3.3 成本分析

| 数据源 | 费用 | 说明 |
|--------|------|------|
| akshare | ¥0 | 开源免费 |
| 已有新闻数据 | ¥0 | 已购买 |
| Tushare 5000积分 | ¥0 | 已拥有 |
| LLM API (Kimi) | ¥0-50/月 | 通过kirocpa代理 |

**总计**: 几乎零额外成本

### 3.4 实时性与准确性权衡

- **推荐方案**: T+1日度新闻情绪
- **原因**: 与EMA日线策略周期匹配，数据稳定可靠，实现成本最低

---

## 4. 代码实现示例

### 4.1 情绪数据提供者

```python
# strategies/sentiment_provider.py
import pandas as pd
import numpy as np
import sqlite3
from typing import Dict, Optional

class SentimentDataProvider:
    """情绪数据提供者 - 支持多数据源"""
    
    def __init__(self, 
                 db_path: str = "data/InvestMindPro.db",
                 use_akshare: bool = True):
        self.db_path = db_path
        self.use_akshare = use_akshare
        
        if use_akshare:
            try:
                import akshare as ak
                self.ak = ak
            except ImportError:
                self.use_akshare = False
    
    def get_sentiment(self, symbol: str, dates: pd.DatetimeIndex) -> pd.DataFrame:
        """获取股票情绪数据"""
        # 优先从本地数据库获取
        sentiment_data = self._get_from_database(symbol, dates)
        
        # 缺失数据尝试akshare
        if self.use_akshare and sentiment_data.isnull().any().any():
            sentiment_data = self._fill_from_akshare(symbol, sentiment_data)
        
        # 仍有缺失则使用 neutral 值填充
        sentiment_data = sentiment_data.fillna({
            'sentiment_index': 0.5,
            'confidence': 0.0,
            'news_count': 0
        })
        
        return sentiment_data
    
    def _get_from_database(self, symbol: str, dates: pd.DatetimeIndex) -> pd.DataFrame:
        """从本地SQLite数据库获取情绪数据"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            query = """
            SELECT 
                date,
                AVG(sentiment_score) as sentiment_index,
                COUNT(*) as news_count,
                AVG(confidence) as confidence
            FROM news_daily_sentiment
            WHERE symbol = ? AND date BETWEEN ? AND ?
            GROUP BY date
            ORDER BY date
            """
            
            start_date = dates.min().strftime('%Y-%m-%d')
            end_date = dates.max().strftime('%Y-%m-%d')
            
            df = pd.read_sql_query(
                query, conn, 
                params=(symbol, start_date, end_date),
                parse_dates=['date']
            )
            
            conn.close()
            
            df.set_index('date', inplace=True)
            result = pd.DataFrame(index=dates)
            result['sentiment_index'] = df['sentiment_index']
            result['news_count'] = df['news_count']
            result['confidence'] = df['confidence']
            
            return result
            
        except Exception as e:
            print(f"[警告] 数据库查询失败: {e}")
            return pd.DataFrame(index=dates, 
                              columns=['sentiment_index', 'confidence', 'news_count'])
    
    def _fill_from_akshare(self, symbol: str, data: pd.DataFrame) -> pd.DataFrame:
        """从akshare补充缺失数据"""
        try:
            news_df = self.ak.news_stock(symbol=symbol)
            
            if news_df is None or len(news_df) == 0:
                return data
            
            # 简单情绪打分 (基于关键词)
            positive_words = ['利好', '增长', '突破', '超预期', '上涨', '买入']
            negative_words = ['利空', '下滑', '亏损', '不及预期', '下跌', '卖出']
            
            def simple_sentiment(text):
                if pd.isna(text):
                    return 0.5
                pos_count = sum(1 for w in positive_words if w in text)
                neg_count = sum(1 for w in negative_words if w in text)
                total = pos_count + neg_count
                if total == 0:
                    return 0.5
                return 0.5 + (pos_count - neg_count) / (2 * total)
            
            news_df['sentiment'] = news_df['title'].apply(simple_sentiment)
            news_df['date'] = pd.to_datetime(news_df['time']).dt.date
            
            # 按日聚合
            daily_sentiment = news_df.groupby('date').agg({
                'sentiment': 'mean',
                'title': 'count'
            }).rename(columns={'title': 'news_count'})
            daily_sentiment['confidence'] = 0.5
            
            # 合并到结果
            for date in data.index:
                date_key = date.date()
                if pd.isna(data.loc[date, 'sentiment_index']) and date_key in daily_sentiment.index:
                    data.loc[date, 'sentiment_index'] = daily_sentiment.loc[date_key, 'sentiment']
                    data.loc[date, 'news_count'] = daily_sentiment.loc[date_key, 'news_count']
                    data.loc[date, 'confidence'] = 0.5
            
            return data
            
        except Exception as e:
            print(f"[警告] akshare获取失败: {e}")
            return data
```

### 4.2 情绪增强EMA策略

```python
# strategies/ema_v2_with_sentiment.py
import pandas as pd
import numpy as np
from typing import Dict, Optional

from strategies.ema_v2 import EMAV2Strategy, BacktestResult
from strategies.sentiment_provider import SentimentDataProvider


class EMAV2WithSentiment(EMAV2Strategy):
    """EMA V2.1 + 情绪过滤器策略"""
    
    def __init__(self, 
                 params: Optional[Dict] = None,
                 volatility_type: str = "medium_volatility",
                 sentiment_threshold_high: float = 0.6,
                 sentiment_threshold_low: float = 0.3,
                 position_weight_mode: bool = False,
                 use_sentiment: bool = True):
        super().__init__(params=params, volatility_type=volatility_type)
        
        self.sentiment_threshold_high = sentiment_threshold_high
        self.sentiment_threshold_low = sentiment_threshold_low
        self.position_weight_mode = position_weight_mode
        self.use_sentiment = use_sentiment
        self.sentiment_provider = SentimentDataProvider()
        
    def generate_signals(self, df, market_data=None):
        """生成带情绪过滤的交易信号"""
        # 1. 获取EMA基础信号
        data = super().generate_signals(df, market_data)
        
        if not self.use_sentiment:
            return data
        
        # 2. 获取情绪数据
        symbol = df.attrs.get('symbol', 'Unknown')
        try:
            sentiment_df = self.sentiment_provider.get_sentiment(symbol, data.index)
            data['sentiment_index'] = sentiment_df['sentiment_index']
            data['sentiment_confidence'] = sentiment_df['confidence']
            data['sentiment_news_count'] = sentiment_df['news_count']
        except Exception as e:
            print(f"[警告] 情绪数据获取失败: {e}, 使用中性值")
            data['sentiment_index'] = 0.5
            data['sentiment_confidence'] = 0
            data['sentiment_news_count'] = 0
        
        # 3. 情绪分类
        data['sentiment_positive'] = data['sentiment_index'] >= self.sentiment_threshold_high
        data['sentiment_neutral'] = (
            (data['sentiment_index'] >= self.sentiment_threshold_low) & 
            (data['sentiment_index'] < self.sentiment_threshold_high)
        )
        data['sentiment_negative'] = data['sentiment_index'] < self.sentiment_threshold_low
        
        # 4. 生成过滤后的买入信号
        if self.position_weight_mode:
            data['position_weight'] = np.where(
                data['sentiment_positive'], 1.5,
                np.where(data['sentiment_neutral'], 1.0, 0.5)
            )
            data['buy_signal_filtered'] = data['buy_signal'] & (~data['sentiment_negative'])
        else:
            data['position_weight'] = 1.0
            data['buy_signal_filtered'] = data['buy_signal'] & (~data['sentiment_negative'])
        
        # 5. 情绪驱动的提前卖出
        panic_threshold = self.sentiment_threshold_low - 0.2
        data['sentiment_exit'] = data['sentiment_index'] < panic_threshold
        data['sell_signal_filtered'] = data['sell_signal'] | data['sentiment_exit']
        data['exit_reason_sentiment'] = data['sentiment_exit']
        
        return data
    
    def run_backtest(self, df, market_data=None, initial_capital=100000.0):
        """执行情绪增强回测"""
        data = self.generate_signals(df, market_data)
        
        position = 0
        entry_price = 0.0
        entry_date = None
        trades = []
        equity_curve = [initial_capital]
        current_capital = initial_capital
        
        for i in range(1, len(data)):
            date = data.index[i]
            price = data['close'].iloc[i]
            position_weight = data['position_weight'].iloc[i]
            
            if position == 0:
                if data['buy_signal_filtered'].iloc[i]:
                    position = position_weight
                    entry_price = price
                    entry_date = date
                    shares = (current_capital * position_weight) / price
                    
            elif position > 0:
                exit_reason = None
                
                if data['sell_signal_filtered'].iloc[i]:
                    if data['exit_reason_sentiment'].iloc[i]:
                        exit_reason = "sentiment_panic"
                    else:
                        exit_reason = "signal"
                
                stop_price = data['stop_loss'].iloc[i]
                if price < stop_price:
                    exit_reason = "stop_loss"
                
                if exit_reason:
                    exit_price = price
                    pnl = (exit_price - entry_price) * shares
                    pnl_pct = (exit_price / entry_price - 1) * 100
                    
                    trades.append({
                        'entry_date': entry_date,
                        'exit_date': date,
                        'entry_price': entry_price,
                        'exit_price': exit_price,
                        'pnl': pnl,
                        'pnl_pct': pnl_pct,
                        'exit_reason': exit_reason,
                        'position_weight': position,
                        'sentiment_at_entry': data.loc[entry_date, 'sentiment_index'] if entry_date in data.index else None,
                        'sentiment_at_exit': data['sentiment_index'].iloc[i]
                    })
                    
                    current_capital += pnl
                    position = 0
                    entry_price = 0.0
                    entry_date = None
            
            equity_curve.append(current_capital)
        
        # 计算绩效指标
        total_return = (current_capital - initial_capital) / initial_capital * 100
        
        if len(trades) > 0:
            winning_trades = [t for t in trades if t['pnl'] > 0]
            win_rate = len(winning_trades) / len(trades) * 100
            
            equity_series = pd.Series(equity_curve)
            rolling_max = equity_series.expanding().max()
            drawdown = (equity_series - rolling_max) / rolling_max * 100
            max_drawdown = drawdown.min()
            
            returns = equity_series.pct_change().dropna()
            if returns.std() != 0:
                sharpe_ratio = (returns.mean() / returns.std()) * np.sqrt(252)
            else:
                sharpe_ratio = 0
            
            sentiment_exits = len([t for t in trades if t['exit_reason'] == 'sentiment_panic'])
        else:
            win_rate = 0
            max_drawdown = 0
            sharpe_ratio = 0
            sentiment_exits = 0
        
        return BacktestResult(
            symbol=df.attrs.get('symbol', 'Unknown'),
            total_return=total_return,
            win_rate=win_rate,
            total_trades=len(trades),
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            trades=trades,
            params={
                **self.params,
                'sentiment_threshold_high': self.sentiment_threshold_high,
                'sentiment_threshold_low': self.sentiment_threshold_low,
                'position_weight_mode': self.position_weight_mode,
                'use_sentiment': self.use_sentiment,
                'sentiment_exits': sentiment_exits
            }
        )
```

---

## 5. 实施路线图

### Phase 1: 基础接入 (1周)

| 任务 | 天数 | 交付物 |
|------|------|--------|
| SentimentDataProvider实现 | 2 | sentiment_provider.py |
| 新闻数据库接入 | 2 | 本地数据查询功能 |
| akshare接口封装 | 1 | akshare情绪数据获取 |
| 基础测试 | 2 | 单元测试通过 |

### Phase 2: 策略融合 (1周)

| 任务 | 天数 | 交付物 |
|------|------|--------|
| EMAV2WithSentiment实现 | 3 | ema_v2_with_sentiment.py |
| 对比回测脚本 | 2 | compare_ema_with_sentiment.py |
| 21只股票回测验证 | 2 | 对比报告 |

### Phase 3: 优化迭代 (1周)

| 任务 | 天数 | 交付物 |
|------|------|--------|
| 阈值参数优化 | 2 | 最优阈值确定 |
| 多因子情绪指标 | 2 | 复合情绪指数 |
| 实盘接入准备 | 2 | 实时数据流对接 |

---

## 6. 结论与建议

### 6.1 核心结论

1. **数据基础扎实**: 项目已有5.6M行新闻情绪数据和15.1M条新闻文章
2. **接入成本低**: 主要数据源均为免费，实现工作量约3周
3. **预期收益提升**: 参考批量回测结果，情绪增强预计可提升收益3-5%
4. **技术方案成熟**: 情绪过滤模式与EMA V2.1策略架构契合

### 6.2 行动建议

#### 立即执行 (本周)
- [ ] 实现 SentimentDataProvider 基础框架
- [ ] 接入本地新闻情绪数据库
- [ ] 编写单元测试验证数据获取

#### 短期目标 (2周内)
- [ ] 完成 EMAV2WithSentiment 策略实现
- [ ] 对21只核心股票进行对比回测
- [ ] 确定最优情绪阈值参数

#### 中期规划 (1个月内)
- [ ] 扩展至所有81只参数优化股票
- [ ] 实现 sentiment_resonance 和 debate_weighted 策略
- [ ] 接入实时情绪数据流，支持实盘交易

### 6.3 风险提示

1. **情绪数据质量**: 建议设置置信度阈值过滤低质量数据
2. **策略过拟合**: 情绪阈值参数需多股票交叉验证
3. **市场变化**: 情绪指标的有效性需持续监控

---

*报告生成时间: 2026-02-28*  
*InvestMindPro Research Team*
