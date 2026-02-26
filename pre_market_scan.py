#!/usr/bin/env python3
"""
开盘前紧急分析脚本
不依赖服务器，直接生成今日关注清单
"""

import akshare as ak
import pandas as pd
from datetime import datetime

print(f"=== 早盘扫描 {datetime.now().strftime('%Y-%m-%d %H:%M')} ===\n")

# 1. 获取涨停池
try:
    zt_df = ak.stock_zt_pool_em(date=datetime.now().strftime('%Y%m%d'))
    print(f"【涨停池】{len(zt_df)} 只")
    if len(zt_df) > 0:
        print(zt_df[['代码', '名称', '涨跌幅', '首次封板时间']].head(5).to_string(index=False))
        print()
except Exception as e:
    print(f"涨停池获取失败: {e}\n")

# 2. 获取热点板块
try:
    sector_df = ak.stock_sector_fund_flow_rank(indicator="5日排行")
    print(f"【5日热点板块】Top 5:")
    print(sector_df[['名称', '涨跌幅']].head(5).to_string(index=False))
    print()
except Exception as e:
    print(f"板块数据获取失败: {e}\n")

# 3. 获取龙虎榜
try:
    lhb_df = ak.stock_lhb_detail_daily_sina()
    print(f"【今日龙虎榜】{len(lhb_df)} 条数据")
    print(lhb_df[['代码', '名称', '营业部名称', '买入金额']].head(5).to_string(index=False))
    print()
except Exception as e:
    print(f"龙虎榜获取失败: {e}\n")

# 4. 成交额排行
try:
    amount_df = ak.stock_zh_a_spot_em()
    amount_df = amount_df.sort_values('成交额', ascending=False)
    print(f"【成交额Top 5】:")
    print(amount_df[['代码', '名称', '最新价', '涨跌幅', '成交额']].head(5).to_string(index=False))
    print()
except Exception as e:
    print(f"成交额数据获取失败: {e}\n")

print("=== 扫描完成 ===")
