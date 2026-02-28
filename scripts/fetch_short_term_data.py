#!/usr/bin/env python3
"""
短线数据获取脚本 - 获取最近3-6个月行情数据
用于EMA短线策略回测
"""

import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
import json
import os
import time

# 股票池
STOCK_POOL = [
    "600519", "000858", "601318", "000333", "600036",
    "002594", "601899", "600900", "000001", "002475",
    "601012", "600276", "000568", "002714", "600809",
    "601888", "300750", "002460", "000651", "688981",
    "002415", "603259", "601012", "000725", "300760",
    "600438", "300274", "300033", "603288", "002230",
    "600030", "601628", "601166", "601398", "601939"
]

def get_short_term_data(stock_code, months=3):
    """获取最近N个月数据"""
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30*months)
        
        # 使用akshare获取历史数据
        df = ak.stock_zh_a_hist(
            symbol=stock_code,
            period="daily",
            start_date=start_date.strftime("%Y%m%d"),
            end_date=end_date.strftime("%Y%m%d"),
            adjust="qfq"
        )
        
        if df is not None and not df.empty:
            return df
        return None
    except Exception as e:
        print(f"❌ 获取{stock_code}数据失败: {e}")
        return None

def main():
    print("="*60)
    print("📊 短线数据获取 - EMA V2.1策略")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"数据范围: 最近3个月")
    print("="*60)
    
    data_dir = "data/short_term"
    os.makedirs(data_dir, exist_ok=True)
    
    success_count = 0
    for i, code in enumerate(STOCK_POOL, 1):
        print(f"\n[{i}/{len(STOCK_POOL)}] 获取 {code} ...", end=" ")
        
        df = get_short_term_data(code, months=3)
        if df is not None:
            file_path = f"{data_dir}/{code}_short.csv"
            df.to_csv(file_path, index=False)
            print(f"✅ {len(df)}条记录")
            success_count += 1
        else:
            print("❌ 失败")
        
        time.sleep(0.5)  # 避免限流
    
    print("\n" + "="*60)
    print(f"✅ 完成: {success_count}/{len(STOCK_POOL)} 只股票")
    print(f"📁 数据保存: {data_dir}/")
    print("="*60)
    
    # 保存元数据
    meta = {
        "created_at": datetime.now().isoformat(),
        "data_range": "3_months",
        "stock_count": success_count,
        "stocks": STOCK_POOL[:success_count]
    }
    with open(f"{data_dir}/meta.json", "w") as f:
        json.dump(meta, f, indent=2)

if __name__ == "__main__":
    main()
