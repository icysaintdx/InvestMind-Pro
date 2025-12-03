"""
测试所有关键导入是否正常
模拟server.py的导入过程
"""

import os
import sys

# 添加项目根目录到Python路径（模拟server.py的做法）
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

print("=" * 60)
print("测试AlphaCouncil导入链")
print("=" * 60)
print()

success = True

# 1. 测试环境变量加载
print("1. 加载环境变量...")
try:
    from pathlib import Path
    from dotenv import load_dotenv
    env_file = Path(__file__).parent / '.env'
    if env_file.exists():
        load_dotenv(env_file)
        print(f"  ✅ 加载环境变量文件: {env_file}")
    else:
        print("  ⚠️ 未找到.env文件（可选）")
except Exception as e:
    print(f"  ❌ 错误: {e}")
    success = False

# 2. 测试API路由导入（这是server.py的关键导入）
print("\n2. 导入API路由...")
try:
    print("  导入news_api...")
    from backend.api.news_api import router as news_router
    print("    ✅ news_api")
except ImportError as e:
    print(f"    ❌ news_api: {e}")
    success = False

try:
    print("  导入debate_api...")
    from backend.api.debate_api import router as debate_router
    print("    ✅ debate_api")
except ImportError as e:
    print(f"    ❌ debate_api: {e}")
    success = False

try:
    print("  导入trading_api...")
    from backend.api.trading_api import router as trading_router
    print("    ✅ trading_api")
except ImportError as e:
    print(f"    ❌ trading_api: {e}")
    success = False

try:
    print("  导入verification_api...")
    from backend.api.verification_api import router as verification_router
    print("    ✅ verification_api")
except ImportError as e:
    print(f"    ❌ verification_api: {e}")
    success = False

try:
    print("  导入agents_api...")
    from backend.api.agents_api import router as agents_router
    print("    ✅ agents_api")
except ImportError as e:
    print(f"    ❌ agents_api: {e}")
    success = False

# 3. 测试FastAPI应用创建
print("\n3. 创建FastAPI应用...")
try:
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    app = FastAPI(title="Test")
    print("  ✅ FastAPI应用创建成功")
except ImportError as e:
    print(f"  ❌ FastAPI: {e}")
    success = False

print("\n" + "=" * 60)
print("测试结果")
print("=" * 60)

if success:
    print("\n✅ 所有导入测试通过！")
    print("\n服务器应该可以正常启动。")
    print("运行: final_start.bat")
else:
    print("\n❌ 有导入错误需要修复。")
    print("\n建议：")
    print("1. 运行: python comprehensive_fix.py")
    print("2. 再次运行此测试")

print("=" * 60)
