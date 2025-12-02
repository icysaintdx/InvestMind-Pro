#!/usr/bin/env python3
"""
测试Node.js和npm环境
"""
import subprocess
import sys
import platform

def test_node_npm():
    """测试Node.js和npm"""
    print("=" * 60)
    print("环境检测")
    print("=" * 60)
    print(f"操作系统: {platform.system()}")
    print(f"Python版本: {sys.version}")
    print("-" * 60)
    
    # 测试Node.js
    print("\n1. 测试Node.js:")
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            print(f"   ✅ Node.js版本: {result.stdout.strip()}")
        else:
            print(f"   ❌ Node.js错误: {result.stderr}")
    except Exception as e:
        print(f"   ❌ 无法运行node: {e}")
    
    # 测试npm - 方法1
    print("\n2. 测试npm (直接调用):")
    try:
        result = subprocess.run(['npm', '--version'], capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            print(f"   ✅ npm版本: {result.stdout.strip()}")
        else:
            print(f"   ❌ npm错误: {result.stderr}")
    except Exception as e:
        print(f"   ❌ 无法运行npm: {e}")
    
    # 测试npm - 方法2 (Windows专用)
    if platform.system() == 'Windows':
        print("\n3. 测试npm.cmd (Windows):")
        try:
            result = subprocess.run(['npm.cmd', '--version'], capture_output=True, text=True, shell=True)
            if result.returncode == 0:
                print(f"   ✅ npm.cmd版本: {result.stdout.strip()}")
            else:
                print(f"   ❌ npm.cmd错误: {result.stderr}")
        except Exception as e:
            print(f"   ❌ 无法运行npm.cmd: {e}")
    
    # 测试where/which命令
    print("\n4. 查找命令位置:")
    locate_cmd = 'where' if platform.system() == 'Windows' else 'which'
    
    for cmd in ['node', 'npm']:
        try:
            result = subprocess.run([locate_cmd, cmd], capture_output=True, text=True, shell=True)
            if result.returncode == 0:
                print(f"   {cmd}: {result.stdout.strip()}")
            else:
                print(f"   {cmd}: 未找到")
        except Exception as e:
            print(f"   {cmd}: 查找失败 - {e}")
    
    # 测试PATH环境变量
    print("\n5. PATH环境变量中的Node相关路径:")
    import os
    path_dirs = os.environ.get('PATH', '').split(os.pathsep)
    node_paths = [d for d in path_dirs if 'node' in d.lower() or 'npm' in d.lower()]
    if node_paths:
        for p in node_paths:
            print(f"   - {p}")
    else:
        print("   未找到Node相关路径")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)

if __name__ == "__main__":
    test_node_npm()
