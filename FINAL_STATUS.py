#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
最终状态检查 - 显示所有模块的状态
"""

import os
import sys

# Add project root to path
project_root = r"D:\AlphaCouncil"
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def check_module(module_path, name):
    """检查模块是否可以导入"""
    try:
        exec(f"import {module_path}")
        return True, "✅ 正常"
    except ImportError as e:
        return False, f"❌ {str(e)}"
    except Exception as e:
        return False, f"⚠️ {str(e)}"

print("=" * 60)
print("AlphaCouncil 最终状态检查")
print("=" * 60)
print()

# 检查关键依赖
print("📦 核心依赖检查:")
print("-" * 40)

modules_to_check = [
    ("numpy", "NumPy"),
    ("pandas", "Pandas"),
    ("fastapi", "FastAPI"),
    ("uvicorn", "Uvicorn"),
    ("colorlog", "ColorLog"),
]

for module, name in modules_to_check:
    success, msg = check_module(module, name)
    print(f"{name:20} {msg}")

# 检查可选依赖
print()
print("📦 可选依赖检查:")
print("-" * 40)

optional_modules = [
    ("chromadb", "ChromaDB (Memory)"),
    ("yfinance", "YFinance"),
    ("stockstats", "StockStats"),
    ("akshare", "AkShare"),
    ("tushare", "Tushare"),
]

optional_status = {}
for module, name in optional_modules:
    success, msg = check_module(module, name)
    optional_status[module] = success
    print(f"{name:20} {msg}")

# 检查项目模块
print()
print("🔧 项目模块检查:")
print("-" * 40)

# 核心模块
print("核心模块:")
core_modules = [
    ("backend.utils.logging_config", "日志系统"),
    ("backend.dataflows.config", "配置系统"),
    ("backend.agents.utils.agent_utils", "智能体工具"),
    ("backend.agents.utils.langchain_compat", "LangChain兼容层"),
]

all_core_ok = True
for module, name in core_modules:
    success, msg = check_module(module, name)
    if not success:
        all_core_ok = False
    print(f"  {name:18} {msg}")

# API模块
print()
print("API模块:")
api_modules = [
    ("backend.api.news_api", "新闻API"),
    ("backend.api.debate_api", "辩论API"),
    ("backend.api.trading_api", "交易API"),
    ("backend.api.verification_api", "验证API"),
    ("backend.api.agents_api", "智能体API"),
]

all_api_ok = True
for module, name in api_modules:
    success, msg = check_module(module, name)
    if not success:
        all_api_ok = False
    print(f"  {name:18} {msg}")

# Memory功能检查
print()
print("💾 Memory功能检查:")
print("-" * 40)
try:
    from backend.agents import MEMORY_AVAILABLE, FinancialSituationMemory
    if MEMORY_AVAILABLE:
        print("  Memory功能: ✅ 可用")
        print(f"  FinancialSituationMemory: {'✅ 已加载' if FinancialSituationMemory else '❌ 未加载'}")
    else:
        print("  Memory功能: ⚠️ 已禁用（ChromaDB不可用）")
        print("  注意：这不会影响其他功能")
except:
    print("  Memory功能: ❌ 检查失败")

# NumPy版本检查
print()
print("🔍 版本检查:")
print("-" * 40)
try:
    import numpy as np
    numpy_version = np.__version__
    if numpy_version.startswith("2."):
        print(f"  NumPy版本: {numpy_version} ⚠️ (与ChromaDB不兼容)")
        print("  建议：运行 python fix_chromadb_auto.py 降级到1.26.4")
    else:
        print(f"  NumPy版本: {numpy_version} ✅")
except:
    print("  NumPy: 未安装")

# 总结
print()
print("=" * 60)
print("📊 总结")
print("=" * 60)

if all_core_ok and all_api_ok:
    print()
    print("✅ 所有核心模块正常！")
    print()
    print("🚀 可以启动服务器：")
    print("   运行: START_SERVER.bat")
    print()
    if not optional_status.get("chromadb", False):
        print("⚠️ 注意：ChromaDB不可用，Memory功能将被禁用")
        print("   这不会影响其他功能的正常运行")
else:
    print()
    print("❌ 有核心模块存在问题")
    print()
    print("建议：")
    print("1. 运行: python fix_chromadb_auto.py")
    print("2. 运行: python install_dependencies.bat")
    print("3. 重新运行此脚本")

print()
print("=" * 60)
