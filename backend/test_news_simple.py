#!/usr/bin/env python3
"""
简化的新闻测试脚本（不使用 async）
"""

import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

# 加载环境变量
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

print("=" * 80)
print("📰 新闻接口简单测试")
print("=" * 80)
print()

# 测试1: 中国财经新闻
print("🇨🇳 测试: 中国财经新闻")
print("-" * 80)

try:
    from backend.dataflows.news.chinese_finance import get_chinese_finance_news
    
    test_symbol = "600519"
    curr_date = datetime.now().strftime('%Y-%m-%d')
    
    print(f"正在获取 {test_symbol} 的新闻 (日期: {curr_date})...")
    
    # 直接调用，不用 await
    result = get_chinese_finance_news(test_symbol, curr_date)
    
    if result:
        print("✅ 获取成功!")
        print(f"结果类型: {type(result)}")
        print(f"结果长度: {len(str(result))}")
        print(f"前500字符:\n{str(result)[:500]}")
    else:
        print("⚠️ 返回空结果")
        
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()

print()
print()

# 测试2: 检查实时新闻的依赖
print("⚡ 测试: 实时新闻依赖检查")
print("-" * 80)

try:
    from backend.dataflows.news import realtime_news
    
    # 检查缺失的函数
    if hasattr(realtime_news, 'get_timezone_name'):
        print("✅ get_timezone_name 函数存在")
    else:
        print("❌ get_timezone_name 函数缺失")
        print("   需要从 TradingAgents-CN-main 复制")
    
    if hasattr(realtime_news, 'get_realtime_stock_news'):
        print("✅ get_realtime_stock_news 函数存在")
    else:
        print("❌ get_realtime_stock_news 函数缺失")
        
except Exception as e:
    print(f"❌ 导入失败: {e}")

print()
print()

# 测试3: 检查需要的文件
print("📁 测试: 检查缺失的文件")
print("-" * 80)

missing_files = []
dataflows_dir = Path(__file__).parent / 'dataflows'

files_to_check = [
    'akshare_utils.py',
    'finnhub_utils.py',
    'googlenews_utils.py',
    'reddit_utils.py',
    'stockstats_utils.py',
    'interface.py',
]

for filename in files_to_check:
    filepath = dataflows_dir / filename
    if filepath.exists():
        print(f"✅ {filename} 存在")
    else:
        print(f"❌ {filename} 缺失")
        missing_files.append(filename)

print()
if missing_files:
    print("需要从 TradingAgents-CN-main 复制的文件:")
    for f in missing_files:
        print(f"  - {f}")
else:
    print("✅ 所有文件都存在")

print()
print("=" * 80)
print("测试完成")
print("=" * 80)
