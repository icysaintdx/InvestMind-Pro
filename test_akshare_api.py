import requests
import json

print("="*100)
print("Testing all 17 AKShare interfaces via API")
print("="*100)

r = requests.get('http://localhost:8000/api/dataflow/stock/comprehensive/600519.SH')
data = r.json()

print(f"\nAPI Status: {data.get('success')}")

# AKShare扩展接口
print("\n" + "="*100)
print("AKShare Extension Interfaces (akshare_ext):")
print("="*100)

ext = data.get('data', {}).get('akshare_ext', {})
count = 1
for k, v in ext.items():
    if isinstance(v, dict):
        status = v.get('status')
        detail = v.get('count', v.get('message', ''))
        emoji = '✅' if status == 'success' else ('⚠️' if status == 'no_data' else '❌')
        print(f"{count:2d}. {k:30s} {emoji} {status:12s} - {detail}")
        count += 1

# 其他AKShare接口
print("\n" + "="*100)
print("Other AKShare Interfaces:")
print("="*100)

for k in ['news_sina', 'market_news', 'cninfo_news', 'industry_policy']:
    v = data.get('data', {}).get(k, {})
    status = v.get('status')
    detail = v.get('count', v.get('message', ''))
    emoji = '✅' if status == 'success' else ('⚠️' if status == 'no_data' else '❌')
    print(f"{count:2d}. {k:30s} {emoji} {status:12s} - {detail}")
    count += 1

# 基础接口
print("\n" + "="*100)
print("Base AKShare Interfaces:")
print("="*100)

for k in ['st_status', 'announcements', 'block_trade', 'news']:
    v = data.get('data', {}).get(k, {})
    status = v.get('status') if isinstance(v, dict) else ('success' if v else 'no_data')
    if isinstance(v, dict):
        detail = v.get('count', v.get('message', ''))
    else:
        detail = len(v) if isinstance(v, list) else ''
    emoji = '✅' if status == 'success' else ('⚠️' if status == 'no_data' else '❌')
    print(f"{count:2d}. {k:30s} {emoji} {status:12s} - {detail}")
    count += 1

print("\n" + "="*100)
print(f"Total AKShare interfaces tested: {count-1}")
print("="*100)
