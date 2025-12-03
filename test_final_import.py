"""
最终导入测试 - 验证所有修复
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("最终导入测试")
print("=" * 60)
print()

errors = []

# 1. 测试tool_logging
print("1. 测试tool_logging模块...")
try:
    from backend.utils.tool_logging import log_tool_call, log_api_call
    print("   ✅ tool_logging导入成功")
except Exception as e:
    errors.append(f"tool_logging: {e}")
    print(f"   ❌ 失败: {e}")

# 2. 测试news_api
print("\n2. 测试news_api路由...")
try:
    from backend.api.news_api import router as news_router
    print("   ✅ news_api路由导入成功")
except Exception as e:
    errors.append(f"news_api: {e}")
    print(f"   ❌ 失败: {e}")

# 3. 测试所有API路由
print("\n3. 测试所有API路由...")
api_modules = [
    ("debate_api", "backend.api.debate_api"),
    ("trading_api", "backend.api.trading_api"),
    ("verification_api", "backend.api.verification_api"),
    ("agents_api", "backend.api.agents_api"),
]

for name, module_path in api_modules:
    try:
        __import__(module_path)
        print(f"   ✅ {name}导入成功")
    except Exception as e:
        errors.append(f"{name}: {e}")
        print(f"   ❌ {name}失败: {e}")

# 4. 测试server.py
print("\n4. 测试server.py...")
try:
    # 只测试导入，不实际运行服务器
    import backend.server
    print("   ✅ server.py导入成功")
except Exception as e:
    errors.append(f"server: {e}")
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
    print("\n🚀 服务器可以启动了！")
    print("   运行: python backend/server.py")
