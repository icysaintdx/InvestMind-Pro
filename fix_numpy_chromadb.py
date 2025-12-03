"""
修复NumPy 2.0与ChromaDB的兼容性问题
"""

import subprocess
import sys

print("=" * 60)
print("修复NumPy和ChromaDB兼容性问题")
print("=" * 60)
print()

# 方案1：降级NumPy到兼容版本
print("方案1：降级NumPy到1.26.4（推荐）")
print("执行命令：pip install numpy==1.26.4")
response1 = input("是否执行？(y/n): ")
if response1.lower() == 'y':
    subprocess.run([sys.executable, "-m", "pip", "install", "numpy==1.26.4", "--force-reinstall"])
    print("✅ NumPy已降级到1.26.4")
    print("\n请运行: READY_TO_START.bat")
    sys.exit(0)

# 方案2：升级ChromaDB
print("\n方案2：升级ChromaDB到最新版本")
print("执行命令：pip install chromadb --upgrade")
response2 = input("是否执行？(y/n): ")
if response2.lower() == 'y':
    subprocess.run([sys.executable, "-m", "pip", "install", "chromadb", "--upgrade"])
    print("✅ ChromaDB已升级")
    print("\n请运行: READY_TO_START.bat")
    sys.exit(0)

# 方案3：卸载ChromaDB（会影响memory功能）
print("\n方案3：卸载ChromaDB（会禁用memory功能）")
print("执行命令：pip uninstall chromadb")
response3 = input("是否执行？(y/n): ")
if response3.lower() == 'y':
    subprocess.run([sys.executable, "-m", "pip", "uninstall", "chromadb", "-y"])
    print("✅ ChromaDB已卸载")
    print("⚠️ 注意：memory功能将被禁用")
    print("\n请运行: READY_TO_START.bat")
    sys.exit(0)

print("\n未选择任何方案。")
print("建议执行：pip install numpy==1.26.4")
