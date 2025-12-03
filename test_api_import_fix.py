"""
测试API导入修复
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("测试API导入修复")
print("=" * 60)
print()

errors = []

# 1. 测试get_realtime_news
print("1. 测试get_realtime_news导入...")
try:
    from backend.dataflows.news.realtime_news import get_realtime_news
    print("   ✅ get_realtime_news导入成功")
except Exception as e:
    errors.append(f"get_realtime_news: {e}")
    print(f"   ❌ 失败: {e}")

# 2. 测试get_chinese_finance_news
print("\n2. 测试get_chinese_finance_news导入...")
try:
    from backend.dataflows.news.chinese_finance import get_chinese_finance_news
    print("   ✅ get_chinese_finance_news导入成功")
except Exception as e:
    errors.append(f"get_chinese_finance_news: {e}")
    print(f"   ❌ 失败: {e}")

# 3. 测试API路由
print("\n3. 测试API路由...")
try:
    from backend.api.news_api import router as news_router
    print("   ✅ news_api路由导入成功")
except Exception as e:
    errors.append(f"news_api: {e}")
    print(f"   ❌ 失败: {e}")

# 总结
print("\n" + "=" * 60)
print("测试结果")
print("=" * 60)

if errors:
    print("\n❌ 发现错误:")
    for error in errors:
        print(f"   - {error}")
    print("\n需要进一步修复。")
else:
    print("\n✅ 所有测试通过！")
    print("\n现在可以运行: LAUNCH_SERVER.bat")
