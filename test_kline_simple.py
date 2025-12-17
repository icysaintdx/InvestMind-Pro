"""简单测试K线API"""
import akshare as ak
from datetime import datetime, timedelta

try:
    print("测试AKShare...")
    
    # 测试日线数据
    print("\n1. 测试日线数据...")
    df = ak.stock_zh_a_hist(
        symbol="600519",
        period="daily",
        start_date=(datetime.now() - timedelta(days=30)).strftime('%Y%m%d'),
        end_date=datetime.now().strftime('%Y%m%d'),
        adjust="qfq"
    )
    
    print(f"获取到 {len(df)} 条数据")
    print(f"列名: {df.columns.tolist()}")
    if len(df) > 0:
        print(f"第一条: {df.iloc[0].to_dict()}")
    
    # 测试5分钟数据
    print("\n2. 测试5分钟数据...")
    df2 = ak.stock_zh_a_hist_min_em(
        symbol="600519",
        period="5",
        adjust="qfq"
    )
    
    print(f"获取到 {len(df2)} 条数据")
    print(f"列名: {df2.columns.tolist()}")
    if len(df2) > 0:
        print(f"第一条: {df2.iloc[0].to_dict()}")
    
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()
