#!/usr/bin/env python3
"""
诊断API问题
检查各个API的返回数据
"""

import requests
import json

print("=" * 80)
print("🔍 诊断API问题")
print("=" * 80)
print()

# 测试1: 微博热搜API
print("📱 测试1: 微博热搜API")
print("-" * 80)
print("URL: https://api.aa1.cn/api/weibo-rs")
print()

try:
    response = requests.get("https://api.aa1.cn/api/weibo-rs", timeout=10)
    print(f"状态码: {response.status_code}")
    print(f"响应头: {dict(response.headers)}")
    print(f"响应内容类型: {response.headers.get('Content-Type')}")
    print(f"响应长度: {len(response.text)} 字符")
    print()
    print("前500字符:")
    print(response.text[:500])
    print()
    
    # 尝试解析JSON
    try:
        data = response.json()
        print(f"✅ JSON解析成功")
        print(f"数据类型: {type(data)}")
        if isinstance(data, dict):
            print(f"字典键: {list(data.keys())}")
        elif isinstance(data, list):
            print(f"列表长度: {len(data)}")
            if data:
                print(f"第一项: {data[0]}")
    except Exception as e:
        print(f"❌ JSON解析失败: {e}")
        
except Exception as e:
    print(f"❌ 请求失败: {e}")

print("\n")

# 测试2: 东方财富新闻API
print("📰 测试2: 东方财富新闻API")
print("-" * 80)

stock_code = "600519"
market = "1"  # 上证
url = f"https://emweb.securities.eastmoney.com/PC_HSF10/NewsBulletin/PageAjax"
params = {
    'code': f"{stock_code}{market}",
    'pageSize': 5,
    'pageIndex': 1,
    'type': '0'
}

print(f"URL: {url}")
print(f"参数: {params}")
print()

try:
    response = requests.get(url, params=params, timeout=10)
    print(f"状态码: {response.status_code}")
    print(f"响应长度: {len(response.text)} 字符")
    print()
    print("前500字符:")
    print(response.text[:500])
    print()
    
    # 尝试解析JSON
    try:
        data = response.json()
        print(f"✅ JSON解析成功")
        print(f"数据类型: {type(data)}")
        print(f"数据内容: {json.dumps(data, ensure_ascii=False, indent=2)[:500]}")
    except Exception as e:
        print(f"❌ JSON解析失败: {e}")
        
except Exception as e:
    print(f"❌ 请求失败: {e}")

print("\n")

# 测试3: 雪球API
print("💬 测试3: 雪球API")
print("-" * 80)

url = f"https://xueqiu.com/statuses/stock_timeline.json"
params = {
    'symbol': f'SH{stock_code}',
    'count': 5
}

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://xueqiu.com/'
}

print(f"URL: {url}")
print(f"参数: {params}")
print()

try:
    response = requests.get(url, params=params, headers=headers, timeout=10)
    print(f"状态码: {response.status_code}")
    print(f"响应长度: {len(response.text)} 字符")
    print()
    print("前500字符:")
    print(response.text[:500])
    print()
    
    # 尝试解析JSON
    try:
        data = response.json()
        print(f"✅ JSON解析成功")
        print(f"数据类型: {type(data)}")
    except Exception as e:
        print(f"❌ JSON解析失败: {e}")
        
except Exception as e:
    print(f"❌ 请求失败: {e}")

print("\n")

# 测试4: AKShare
print("📊 测试4: AKShare")
print("-" * 80)

try:
    import akshare as ak
    print(f"AKShare版本: {ak.__version__}")
    print()
    
    # 测试可用的新闻接口
    print("测试 stock_news_em()...")
    try:
        df = ak.stock_news_em(symbol=stock_code)
        print(f"✅ 成功获取 {len(df)} 条新闻")
        if len(df) > 0:
            print(f"列: {list(df.columns)}")
            print(f"第一条: {df.iloc[0].to_dict()}")
    except Exception as e:
        print(f"❌ 失败: {e}")
    
except ImportError:
    print("❌ AKShare未安装")
except Exception as e:
    print(f"❌ 测试失败: {e}")

print("\n")

# 测试5: Tushare
print("📈 测试5: Tushare")
print("-" * 80)

try:
    import tushare as ts
    import os
    
    token = os.getenv('TUSHARE_TOKEN')
    if token:
        print(f"Token已配置: {token[:10]}...")
        ts.set_token(token)
        pro = ts.pro_api()
        
        # 测试新闻接口
        print("测试 news()...")
        try:
            df = pro.news(src='sina', start_date='20251201', end_date='20251204')
            print(f"✅ 成功获取 {len(df)} 条新闻")
            if len(df) > 0:
                print(f"列: {list(df.columns)}")
        except Exception as e:
            print(f"❌ 失败: {e}")
    else:
        print("⚠️ 未配置TUSHARE_TOKEN")
        
except ImportError:
    print("❌ Tushare未安装")
except Exception as e:
    print(f"❌ 测试失败: {e}")

print("\n")
print("=" * 80)
print("📋 诊断完成")
print("=" * 80)
