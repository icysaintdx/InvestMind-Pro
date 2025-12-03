"""
测试config_utils修复
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("测试配置工具函数修复")
print("=" * 60)
print()

errors = []

# 1. 测试config_utils模块
print("1. 测试config_utils模块...")
try:
    from backend.dataflows.config_utils import get_float, get_int, get_str, get_bool
    print("   ✅ config_utils导入成功")
    
    # 测试函数
    test_float = get_float("TEST_FLOAT", "test_float", 1.5)
    test_int = get_int("TEST_INT", "test_int", 10)
    print(f"   测试值: float={test_float}, int={test_int}")
except Exception as e:
    errors.append(f"config_utils: {e}")
    print(f"   ❌ 失败: {e}")

# 2. 测试google_news模块
print("\n2. 测试google_news模块...")
try:
    from backend.dataflows.news.google_news import SLEEP_MIN, SLEEP_MAX
    print(f"   ✅ google_news导入成功")
    print(f"   SLEEP_MIN={SLEEP_MIN}, SLEEP_MAX={SLEEP_MAX}")
except Exception as e:
    errors.append(f"google_news: {e}")
    print(f"   ❌ 失败: {e}")

# 3. 测试美股数据提供器
print("\n3. 测试美股数据提供器...")
try:
    from backend.dataflows.providers.us.optimized import OptimizedUSDataProvider
    print("   ✅ OptimizedUSDataProvider导入成功")
except Exception as e:
    errors.append(f"US provider: {e}")
    print(f"   ❌ 失败: {e}")

# 4. 测试港股数据提供器
print("\n4. 测试港股数据提供器...")
try:
    from backend.dataflows.providers.hk.improved_hk import ImprovedHKStockProvider
    print("   ✅ ImprovedHKStockProvider导入成功")
except Exception as e:
    errors.append(f"HK improved provider: {e}")
    print(f"   ❌ 失败: {e}")

try:
    from backend.dataflows.providers.hk.hk_stock import HKStockProvider
    print("   ✅ HKStockProvider导入成功")
except Exception as e:
    errors.append(f"HK stock provider: {e}")
    print(f"   ❌ 失败: {e}")

# 5. 测试news模块整体
print("\n5. 测试news模块整体...")
try:
    import backend.dataflows.news
    print("   ✅ news模块初始化成功")
except Exception as e:
    errors.append(f"news module: {e}")
    print(f"   ❌ 失败: {e}")

# 6. 测试news_analyst
print("\n6. 测试news_analyst...")
try:
    from backend.agents.analysts.news_analyst import create_news_analyst
    print("   ✅ news_analyst导入成功")
except Exception as e:
    errors.append(f"news_analyst: {e}")
    print(f"   ❌ 失败: {e}")

# 7. 测试API路由
print("\n7. 测试API路由...")
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
    print("\n现在可以运行: START_SERVER.bat")
