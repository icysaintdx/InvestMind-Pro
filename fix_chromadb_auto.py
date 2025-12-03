"""
自动修复NumPy和ChromaDB兼容性问题
"""

import subprocess
import sys
import os

print("=" * 60)
print("自动修复NumPy和ChromaDB兼容性")
print("=" * 60)
print()

# 检查NumPy版本
try:
    import numpy as np
    numpy_version = np.__version__
    print(f"当前NumPy版本: {numpy_version}")
    
    if numpy_version.startswith("2."):
        print("⚠️ 检测到NumPy 2.0，与ChromaDB不兼容")
        print("正在降级NumPy到1.26.4...")
        
        # 降级NumPy
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "numpy==1.26.4", "--force-reinstall"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ NumPy已成功降级到1.26.4")
        else:
            print("❌ NumPy降级失败")
            print("错误信息:", result.stderr)
    else:
        print("✅ NumPy版本兼容")
        
except ImportError:
    print("❌ NumPy未安装")
    print("正在安装NumPy 1.26.4...")
    subprocess.run([sys.executable, "-m", "pip", "install", "numpy==1.26.4"])

# 测试ChromaDB
print("\n测试ChromaDB...")
try:
    import chromadb
    print("✅ ChromaDB可以正常导入")
except ImportError as e:
    if "np.float_" in str(e):
        print("❌ ChromaDB与NumPy不兼容")
        print("正在重新安装NumPy 1.26.4...")
        subprocess.run([sys.executable, "-m", "pip", "install", "numpy==1.26.4", "--force-reinstall"])
        print("✅ 已尝试修复")
    else:
        print(f"⚠️ ChromaDB不可用: {e}")
        print("Memory功能将被禁用，但不影响其他功能")

print("\n" + "=" * 60)
print("修复完成！")
print("请运行: READY_TO_START.bat")
print("=" * 60)
