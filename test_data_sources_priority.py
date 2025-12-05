"""
测试所有数据源的优先级和可用性
优先级: AKShare > 新浪财经 > 聚合数据 > Tushare > BaoStock
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
import time
from datetime import datetime

test_symbol = "000001"  # 平安银行

print("="*70)
print(" InvestMind Pro - 数据源优先级测试")
print(f" 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*70)
print(f"测试股票: {test_symbol} (平安银行)")
print("优先级: AKShare > 新浪财经 > 聚合数据 > Tushare > BaoStock")
print("-"*70)

# 1. AKShare (第一优先级)
print("\n【优先级1】AKShare")
print("-"*40)
try:
    import akshare as ak
    start = time.time()
    df = ak.stock_zh_a_spot_em()
    elapsed = time.time() - start
    
    if df is not None and not df.empty:
        stock = df[df['代码'] == test_symbol]
        if not stock.empty:
            row = stock.iloc[0]
            print(f"✅ AKShare 可用 (耗时: {elapsed:.2f}秒)")
            print(f"   股票名称: {row.get('名称')}")
            print(f"   当前价: ¥{row.get('最新价')}")
            print(f"   涨跌幅: {row.get('涨跌幅')}%")
            print(f"   成交量: {row.get('成交量')}")
            print(f"   ➡️ 优先使用此数据源")
            akshare_available = True
        else:
            print(f"⚠️ AKShare 可连接但找不到股票 {test_symbol}")
            akshare_available = False
    else:
        print("❌ AKShare 返回空数据")
        akshare_available = False
except Exception as e:
    print(f"❌ AKShare 不可用: {str(e)[:100]}")
    akshare_available = False

# 2. 新浪财经 (第二优先级)
print("\n【优先级2】新浪财经")
print("-"*40)
try:
    sina_code = 'sz' + test_symbol if test_symbol.startswith(('0', '3')) else 'sh' + test_symbol
    url = f"https://hq.sinajs.cn/list={sina_code}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://finance.sina.com.cn'
    }
    
    start = time.time()
    resp = requests.get(url, headers=headers, timeout=5)
    elapsed = time.time() - start
    
    if resp.status_code == 200 and f'hq_str_{sina_code}' in resp.text:
        data = resp.text.split('=')[1].strip('";')
        parts = data.split(',')
        if len(parts) >= 32:
            print(f"✅ 新浪财经 可用 (耗时: {elapsed:.2f}秒)")
            print(f"   股票名称: {parts[0]}")
            print(f"   当前价: ¥{parts[3]}")
            print(f"   涨跌幅: {((float(parts[3])-float(parts[2]))/float(parts[2])*100 if float(parts[2])!=0 else 0):.2f}%")
            print(f"   成交量: {parts[8]}")
            if not akshare_available:
                print(f"   ➡️ AKShare不可用，将使用新浪财经")
            sina_available = True
        else:
            print(f"⚠️ 新浪财经 数据格式不完整 (字段数: {len(parts)})")
            sina_available = False
    else:
        print(f"❌ 新浪财经 HTTP {resp.status_code}")
        sina_available = False
except Exception as e:
    print(f"❌ 新浪财经 不可用: {str(e)[:100]}")
    sina_available = False

# 3. 聚合数据 (第三优先级 - 需要API Key)
print("\n【优先级3】聚合数据")
print("-"*40)
juhe_key = os.getenv('JUHE_API_KEY', '')
if juhe_key:
    print(f"✅ 检测到聚合数据API Key")
    # 可以在这里添加聚合数据的测试
    print("   (需要付费接口，暂不测试)")
else:
    print("⚠️ 未配置聚合数据API Key (JUHE_API_KEY)")
    print("   如需使用，请在.env文件中配置")

# 4. Tushare (第四优先级 - 有积分限制)
print("\n【优先级4】Tushare")
print("-"*40)
try:
    import tushare as ts
    start = time.time()
    df = ts.get_realtime_quotes(test_symbol)
    elapsed = time.time() - start
    
    if df is not None and not df.empty:
        row = df.iloc[0]
        print(f"✅ Tushare 可用 (耗时: {elapsed:.2f}秒)")
        print(f"   股票名称: {row.get('name')}")
        print(f"   当前价: ¥{row.get('price')}")
        print(f"   今开: ¥{row.get('open')}")
        print(f"   昨收: ¥{row.get('pre_close')}")
        print("   ⚠️ 注意: 积分限制，仅作备用")
        tushare_available = True
    else:
        print("❌ Tushare 返回空数据")
        tushare_available = False
except Exception as e:
    print(f"❌ Tushare 不可用: {str(e)[:100]}")
    tushare_available = False

# 检查是否需要配置Token
tushare_token = os.getenv('TUSHARE_TOKEN', '')
if not tushare_token:
    print("   ⚠️ 未配置 TUSHARE_TOKEN，部分功能受限")

# 5. BaoStock (第五优先级)
print("\n【优先级5】BaoStock")
print("-"*40)
try:
    import baostock as bs
    print("✅ BaoStock 模块已安装")
    # 简单测试连接
    lg = bs.login()
    if lg.error_code == '0':
        print("   登录成功，可以获取历史数据")
        bs.logout()
        baostock_available = True
    else:
        print(f"   登录失败: {lg.error_msg}")
        baostock_available = False
except ImportError:
    print("⚠️ BaoStock 未安装")
    print("   安装命令: pip install baostock")
    baostock_available = False
except Exception as e:
    print(f"❌ BaoStock 测试失败: {str(e)[:100]}")
    baostock_available = False

# 总结
print("\n" + "="*70)
print(" 测试结果总结")
print("="*70)

available_sources = []
if akshare_available:
    available_sources.append("AKShare (优先)")
if sina_available:
    available_sources.append("新浪财经")
if tushare_available:
    available_sources.append("Tushare (积分限制)")
if baostock_available:
    available_sources.append("BaoStock (历史数据)")

if available_sources:
    print("✅ 可用数据源:")
    for source in available_sources:
        print(f"   • {source}")
else:
    print("❌ 没有可用的数据源！")
    print("   系统将使用模拟数据")

# 推荐配置
print("\n📌 推荐配置:")
if not akshare_available:
    print("1. 修复AKShare连接问题:")
    print("   - 检查网络连接")
    print("   - 更新AKShare: pip install --upgrade akshare")
    print("   - 可能需要使用代理")

if not sina_available:
    print("2. 新浪财经作为稳定备用源")
    print("   - 通常比较稳定，如果失败请检查网络")

if not tushare_token:
    print("3. 配置Tushare Token获取更多功能:")
    print("   - 注册: https://tushare.pro/register")
    print("   - 在.env文件中添加: TUSHARE_TOKEN=你的token")

print("\n测试完成！")
