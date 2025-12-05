"""
测试服务器导入是否正常
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("测试 FastAPI 相关导入...")
print("-"*40)

try:
    from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
    print("✅ FastAPI 核心模块")
except ImportError as e:
    print(f"❌ FastAPI 核心模块: {e}")

try:
    from fastapi.middleware.cors import CORSMiddleware
    print("✅ CORS 中间件")
except ImportError as e:
    print(f"❌ CORS 中间件: {e}")

try:
    from fastapi.staticfiles import StaticFiles
    print("✅ StaticFiles")
except ImportError as e:
    print(f"❌ StaticFiles: {e}")

try:
    from fastapi.responses import FileResponse
    print("✅ FileResponse")
except ImportError as e:
    print(f"❌ FileResponse: {e}")

try:
    import httpx
    print("✅ httpx")
except ImportError as e:
    print(f"❌ httpx: {e}")

try:
    import uvicorn
    print("✅ uvicorn")
except ImportError as e:
    print(f"❌ uvicorn: {e}")

print("\n测试后端服务器导入...")
print("-"*40)

try:
    import backend.server
    print("✅ 服务器模块导入成功！")
except Exception as e:
    print(f"❌ 服务器模块导入失败: {e}")
    import traceback
    print(traceback.format_exc())

print("\n测试完成！")
