"""
测试AKShare的不同接口方法
找出最稳定快速的方式
"""

import akshare as ak
import time

test_symbol = "000001"

print("="*60)
print("测试 AKShare 不同接口方法")
print("="*60)

# 方法1: stock_zh_a_spot_em() - 获取所有A股数据（可能太重）
print("\n方法1: stock_zh_a_spot_em() - 获取所有A股")
print("-"*40)
try:
    start = time.time()
    df = ak.stock_zh_a_spot_em()
    elapsed = time.time() - start
    if df is not None and not df.empty:
        stock = df[df['代码'] == test_symbol]
        if not stock.empty:
            print(f"✅ 成功 (耗时: {elapsed:.2f}秒)")
            print(f"   数据行数: {len(df)}")
            print(f"   股票名称: {stock.iloc[0]['名称']}")
        else:
            print(f"❌ 找不到股票")
    else:
        print(f"❌ 返回空数据")
except Exception as e:
    print(f"❌ 失败: {str(e)[:100]}")

# 方法2: stock_zh_a_spot() - 获取实时数据（旧版）
print("\n方法2: stock_zh_a_spot() - 实时数据旧版")
print("-"*40)
try:
    start = time.time()
    df = ak.stock_zh_a_spot()
    elapsed = time.time() - start
    if df is not None and not df.empty:
        stock = df[df['symbol'] == 'sz' + test_symbol]
        if not stock.empty:
            print(f"✅ 成功 (耗时: {elapsed:.2f}秒)")
            print(f"   股票名称: {stock.iloc[0]['name']}")
        else:
            print(f"❌ 找不到股票")
    else:
        print(f"❌ 返回空数据")
except Exception as e:
    print(f"❌ 失败: {str(e)[:100]}")

# 方法3: stock_individual_info_em() - 单个股票信息
print("\n方法3: stock_individual_info_em() - 单个股票信息")
print("-"*40)
try:
    start = time.time()
    df = ak.stock_individual_info_em(symbol=test_symbol)
    elapsed = time.time() - start
    if df is not None and not df.empty:
        print(f"✅ 成功 (耗时: {elapsed:.2f}秒)")
        print("   数据预览:")
        print(df.head(10))
    else:
        print(f"❌ 返回空数据")
except Exception as e:
    print(f"❌ 失败: {str(e)[:100]}")

# 方法4: stock_zh_a_hist() - 历史数据（包含今日）
print("\n方法4: stock_zh_a_hist() - 历史数据（包含今日）")
print("-"*40)
try:
    start = time.time()
    df = ak.stock_zh_a_hist(symbol=test_symbol, period="daily", adjust="")
    elapsed = time.time() - start
    if df is not None and not df.empty:
        latest = df.iloc[-1]
        print(f"✅ 成功 (耗时: {elapsed:.2f}秒)")
        print(f"   日期: {latest['日期']}")
        print(f"   收盘: {latest['收盘']}")
        print(f"   涨跌幅: {latest.get('涨跌幅', 'N/A')}")
    else:
        print(f"❌ 返回空数据")
except Exception as e:
    print(f"❌ 失败: {str(e)[:100]}")

# 方法5: stock_bid_ask_em() - 五档买卖盘口数据
print("\n方法5: stock_bid_ask_em() - 买卖盘口数据")
print("-"*40)
try:
    start = time.time()
    df = ak.stock_bid_ask_em(symbol=test_symbol)
    elapsed = time.time() - start
    if df is not None and not df.empty:
        print(f"✅ 成功 (耗时: {elapsed:.2f}秒)")
        print("   数据预览:")
        print(df.head())
    else:
        print(f"❌ 返回空数据")
except Exception as e:
    print(f"❌ 失败: {str(e)[:100]}")

# 方法6: stock_zh_a_hist_min_em() - 分钟数据
print("\n方法6: stock_zh_a_hist_min_em() - 1分钟数据")
print("-"*40)
try:
    start = time.time()
    df = ak.stock_zh_a_hist_min_em(symbol=test_symbol, period='1')
    elapsed = time.time() - start
    if df is not None and not df.empty:
        latest = df.iloc[-1]
        print(f"✅ 成功 (耗时: {elapsed:.2f}秒)")
        print(f"   时间: {latest['时间']}")
        print(f"   收盘: {latest['收盘']}")
    else:
        print(f"❌ 返回空数据")
except Exception as e:
    print(f"❌ 失败: {str(e)[:100]}")

print("\n" + "="*60)
print("测试结果总结")
print("="*60)
print("建议使用最快速稳定的接口获取单个股票数据")
print("避免使用获取全市场数据的接口（太慢）")
