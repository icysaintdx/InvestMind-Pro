"""
测试google_news模块修复
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("测试google_news模块...")

try:
    from backend.dataflows.news.google_news import get_float, get_int, SLEEP_MIN, SLEEP_MAX
    print(f"✅ google_news模块导入成功")
    print(f"   SLEEP_MIN: {SLEEP_MIN}")
    print(f"   SLEEP_MAX: {SLEEP_MAX}")
    
    # 测试函数
    test_val = get_float("TEST_VAR", "test_var", 1.5)
    print(f"   get_float测试: {test_val}")
    
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    import traceback
    traceback.print_exc()

print("\n测试news模块初始化...")
try:
    import backend.dataflows.news
    print("✅ news模块初始化成功")
except Exception as e:
    print(f"❌ news模块初始化失败: {e}")

print("\n测试news_analyst导入...")
try:
    from backend.agents.analysts.news_analyst import create_news_analyst
    print("✅ news_analyst导入成功")
except Exception as e:
    print(f"❌ news_analyst导入失败: {e}")
    
print("\n测试完成！")
