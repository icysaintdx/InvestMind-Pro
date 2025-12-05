"""
快速测试数据源状态
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 测试基础数据源
print("="*60)
print("1. 测试 AKShare")
print("="*60)
try:
    import akshare as ak
    # 测试最简单的接口
    df = ak.stock_zh_a_spot_em()
    print(f"✓ AKShare可用 - 获取到 {len(df)} 支股票")
    # 获取平安银行数据测试
    stock = df[df['代码'] == '000001']
    if not stock.empty:
        print(f"  平安银行最新价: {stock.iloc[0]['最新价']}")
        print(f"  涨跌幅: {stock.iloc[0]['涨跌幅']}%")
except Exception as e:
    print(f"✗ AKShare失败: {str(e)}")

print("\n" + "="*60)
print("2. 测试 Tushare")
print("="*60)
try:
    import tushare as ts
    # Tushare大部分接口需要token，测试免费接口
    df = ts.get_realtime_quotes('000001')
    if df is not None and not df.empty:
        print(f"✓ Tushare可用")
        print(f"  平安银行: {df.iloc[0]['name']}")
        print(f"  当前价: {df.iloc[0]['price']}")
    else:
        print("⚠ Tushare需要token或数据为空")
except Exception as e:
    print(f"⚠ Tushare需要配置: {str(e)}")

print("\n" + "="*60)
print("3. 测试新浪财经")
print("="*60)
try:
    import requests
    url = "https://hq.sinajs.cn/list=sz000001"
    headers = {'User-Agent': 'Mozilla/5.0'}
    resp = requests.get(url, headers=headers, timeout=5)
    if resp.status_code == 200 and 'hq_str_sz000001' in resp.text:
        data = resp.text.split('=')[1].strip('";')
        parts = data.split(',')
        if len(parts) > 3:
            print(f"✓ 新浪财经可用")
            print(f"  平安银行: {parts[0]}")
            print(f"  当前价: {parts[3]}")
    else:
        print(f"✗ 新浪财经失败: 响应异常")
except Exception as e:
    print(f"✗ 新浪财经失败: {str(e)}")

print("\n" + "="*60)
print("4. 测试新闻API")
print("="*60)
try:
    # 测试AKShare新闻接口
    import akshare as ak
    # 个股新闻
    news = ak.stock_news_em(symbol="000001")
    print(f"✓ 东方财富个股新闻: {len(news)} 条")
    
    # 财经早餐
    cjzc = ak.stock_info_cjzc_em()
    print(f"✓ 财经早餐: {len(cjzc)} 条")
    
    # 全球财经
    global_news = ak.stock_info_global_em()
    print(f"✓ 全球财经新闻: {len(global_news)} 条")
except Exception as e:
    print(f"✗ 新闻API失败: {str(e)}")

print("\n" + "="*60)
print("5. 测试股票数据适配器")
print("="*60)
try:
    from backend.dataflows.stock_data_adapter import StockDataAdapter
    import asyncio
    
    async def test():
        adapter = StockDataAdapter()
        result = await adapter.get_stock_data("000001")
        if result.get('success'):
            data = result['data']
            print(f"✓ 适配器正常")
            print(f"  数据源: {data.get('data_source')}")
            print(f"  股票: {data.get('name')}")
            print(f"  价格: {data.get('price')}")
            return True
        else:
            print(f"✗ 适配器失败: {result.get('error')}")
            return False
    
    asyncio.run(test())
except Exception as e:
    print(f"✗ 适配器失败: {str(e)}")

print("\n" + "="*60)
print("测试完成")
print("="*60)
