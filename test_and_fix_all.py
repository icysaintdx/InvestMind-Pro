"""
完整测试和修复所有数据源问题
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import asyncio
import json
import akshare as ak
import requests
from datetime import datetime
from backend.dataflows.stock_data_adapter import StockDataAdapter

print("="*70)
print(" InvestMind Pro - 数据源测试与修复")
print("="*70)

# 测试配置
test_symbol = "000001"  # 平安银行

print(f"\n测试股票: {test_symbol} (平安银行)")
print("-"*70)

# 1. 测试 AKShare 直接调用
print("\n【1】AKShare 直接调用测试")
print("-"*40)
try:
    # 测试实时行情
    print("1.1 测试实时行情接口...")
    df = ak.stock_zh_a_spot_em()
    if not df.empty:
        stock = df[df['代码'] == test_symbol]
        if not stock.empty:
            row = stock.iloc[0]
            print(f"✅ AKShare 实时行情正常")
            print(f"   股票名称: {row.get('名称', 'N/A')}")
            print(f"   最新价: {row.get('最新价', 'N/A')}")
            print(f"   涨跌幅: {row.get('涨跌幅', 'N/A')}%")
            print(f"   成交量: {row.get('成交量', 'N/A')}")
            akshare_works = True
        else:
            print(f"⚠️ 找不到股票 {test_symbol}")
            akshare_works = False
    else:
        print("❌ AKShare 返回空数据")
        akshare_works = False
except Exception as e:
    print(f"❌ AKShare 失败: {str(e)}")
    akshare_works = False

# 2. 测试 Sina Finance
print("\n【2】新浪财经接口测试")
print("-"*40)
try:
    url = f"https://hq.sinajs.cn/list=sz{test_symbol}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://finance.sina.com.cn'
    }
    resp = requests.get(url, headers=headers, timeout=5)
    if resp.status_code == 200 and f'hq_str_sz{test_symbol}' in resp.text:
        data = resp.text.split('=')[1].strip('";')
        parts = data.split(',')
        if len(parts) > 3:
            print(f"✅ 新浪财经正常")
            print(f"   股票名称: {parts[0]}")
            print(f"   当前价: {parts[3]}")
            print(f"   涨跌额: {parts[4]}")
            print(f"   涨跌幅: {parts[5]}%")
            sina_works = True
        else:
            print("⚠️ 新浪数据格式不完整")
            sina_works = False
    else:
        print(f"❌ 新浪财经返回异常: HTTP {resp.status_code}")
        sina_works = False
except Exception as e:
    print(f"❌ 新浪财经失败: {str(e)}")
    sina_works = False

# 3. 测试 Tushare
print("\n【3】Tushare 接口测试")
print("-"*40)
try:
    import tushare as ts
    # 免费接口测试
    df = ts.get_realtime_quotes(test_symbol)
    if df is not None and not df.empty:
        row = df.iloc[0]
        print(f"✅ Tushare 基础接口正常")
        print(f"   股票名称: {row.get('name', 'N/A')}")
        print(f"   当前价: {row.get('price', 'N/A')}")
        print(f"   涨跌幅: {row.get('changepercent', 'N/A')}%")
        tushare_works = True
    else:
        print("⚠️ Tushare 需要配置 Token")
        tushare_works = False
except Exception as e:
    print(f"⚠️ Tushare 失败(可能需要Token): {str(e)}")
    tushare_works = False

# 4. 测试股票数据适配器
print("\n【4】股票数据适配器测试")
print("-"*40)

async def test_adapter():
    adapter = StockDataAdapter()
    result = await adapter.get_stock_data(test_symbol)
    
    if result.get('success'):
        data = result.get('data', {})
        print(f"✅ 股票适配器正常")
        print(f"   数据源: {data.get('data_source', 'Unknown')}")
        print(f"   股票名: {data.get('name', 'N/A')}")
        print(f"   当前价: ¥{data.get('price', 0)}")
        print(f"   涨跌幅: {data.get('change', 0)}%")
        
        # 显示原始文本预览
        if 'raw_text' in data:
            raw = data['raw_text']
            print(f"   原始数据长度: {len(raw)} 字符")
        return True
    else:
        print(f"❌ 适配器失败: {result.get('error', 'Unknown error')}")
        return False

adapter_works = asyncio.run(test_adapter())

# 5. 测试新闻API
print("\n【5】新闻API测试")
print("-"*40)
try:
    # 测试统一新闻接口
    response = requests.post('http://localhost:8000/api/unified-news/stock', 
                           json={"ticker": test_symbol}, 
                           timeout=10)
    
    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            news_data = result.get('data', {})
            sources = news_data.get('sources', {})
            
            print(f"✅ 新闻API正常")
            
            # 统计各数据源状态
            success_count = 0
            total_news = 0
            for source_name, source_data in sources.items():
                if source_data.get('status') == 'success':
                    count = source_data.get('count', 0)
                    success_count += 1
                    total_news += count
                    print(f"   ✅ {source_name}: {count}条")
                else:
                    print(f"   ❌ {source_name}: {source_data.get('status', 'error')}")
            
            print(f"\n   成功数据源: {success_count}/{len(sources)}")
            print(f"   总新闻数: {total_news}条")
            news_works = total_news > 0
        else:
            print(f"❌ 新闻API返回失败: {result.get('message')}")
            news_works = False
    else:
        print(f"❌ 新闻API HTTP错误: {response.status_code}")
        news_works = False
except Exception as e:
    print(f"❌ 新闻API失败: {str(e)}")
    news_works = False

# 6. 直接测试各个新闻数据源
print("\n【6】各新闻数据源直接测试")
print("-"*40)

# 6.1 测试个股新闻
try:
    news_em = ak.stock_news_em(symbol=test_symbol)
    print(f"✅ 个股新闻: {len(news_em)}条")
    if not news_em.empty and len(news_em) > 0:
        print(f"   最新: {news_em.iloc[0].get('新闻标题', 'N/A')[:40]}...")
except Exception as e:
    print(f"❌ 个股新闻失败: {str(e)}")

# 6.2 测试财经早餐
try:
    cjzc = ak.stock_info_cjzc_em()
    print(f"✅ 财经早餐: {len(cjzc)}条")
except Exception as e:
    print(f"❌ 财经早餐失败: {str(e)}")

# 6.3 测试全球财经新闻
try:
    global_news = ak.stock_info_global_em()
    print(f"✅ 全球财经: {len(global_news)}条")
except Exception as e:
    print(f"❌ 全球财经失败: {str(e)}")

# 6.4 测试财联社快讯
try:
    cls_news = ak.stock_info_global_cls()
    print(f"✅ 财联社快讯: {len(cls_news)}条")
except Exception as e:
    print(f"❌ 财联社快讯失败: {str(e)}")

# 6.5 测试微博热议
try:
    weibo = ak.stock_js_weibo_report(num=10)
    print(f"✅ 微博热议: {len(weibo)}条")
except Exception as e:
    print(f"❌ 微博热议失败: {str(e)}")

# 7. 总结和建议
print("\n" + "="*70)
print(" 测试结果总结")
print("="*70)

print("\n✅ 可用的数据源:")
if akshare_works:
    print("  • AKShare 实时行情")
if sina_works:
    print("  • 新浪财经")
if tushare_works:
    print("  • Tushare 基础接口")
if adapter_works:
    print("  • 股票数据适配器")
if news_works:
    print("  • 新闻API")

print("\n⚠️ 问题和建议:")
if not akshare_works:
    print("  1. AKShare 有问题:")
    print("     - 更新: pip install --upgrade akshare")
    print("     - 检查网络连接")
    
if not news_works:
    print("  2. 新闻API 问题:")
    print("     - 确保后端服务运行: python backend/server.py")
    print("     - 检查端口8000是否被占用")

print("\n📊 数据源优先级建议:")
print("  1. 使用 AKShare 作为主数据源（免费、稳定）")
print("  2. 新浪财经作为备用数据源")
print("  3. Tushare 需要配置Token才能使用完整功能")

# 8. 修复股票适配器优先级
print("\n" + "="*70)
print(" 自动修复建议")
print("="*70)

if akshare_works and not adapter_works:
    print("\n需要修改 backend/dataflows/stock_data_adapter.py:")
    print("确保 AKShare 是第一优先级数据源")
    
print("\n前端修复:")
print("1. 清理浏览器缓存: Ctrl+Shift+Delete")
print("2. 重启前端: cd alpha-council-vue && npm run serve")
print("3. 确保后端运行: python backend/server.py")

print("\n测试完成！")
