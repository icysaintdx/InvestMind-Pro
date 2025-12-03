"""
一键安装所有项目依赖
"""

import subprocess
import sys

def install_package(package):
    """安装单个包"""
    try:
        print(f"Installing {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ {package} installed successfully")
    except subprocess.CalledProcessError:
        print(f"❌ Failed to install {package}")
        return False
    return True

def main():
    print("="*60)
    print("🚀 Installing AlphaCouncil Dependencies")
    print("="*60)
    print()
    
    # 必要的依赖包列表
    essential_packages = [
        # 日志系统
        "colorlog==6.7.0",
        "colorama==0.4.6",
        "termcolor==2.3.0",
        
        # Web框架
        "fastapi",
        "uvicorn",
        "httpx",
        "python-dotenv",
        "aiofiles",
        
        # 数据处理
        "pandas",
        "numpy",
        "pydantic",
        
        # 市场数据API
        "akshare",
        "tushare",
        "beautifulsoup4",
        "lxml",
        "requests",
        
        # 其他工具
        "python-dateutil",
    ]
    
    failed = []
    
    for package in essential_packages:
        if not install_package(package):
            failed.append(package)
    
    print()
    print("="*60)
    
    if failed:
        print("⚠️ Some packages failed to install:")
        for pkg in failed:
            print(f"  - {pkg}")
        print("\nTry installing them manually:")
        print(f"pip install {' '.join(failed)}")
    else:
        print("✅ All dependencies installed successfully!")
        print("\nYou can now run:")
        print("  python backend/server.py")
        print("  or")
        print("  start_backend.bat")
    
    print("="*60)

if __name__ == "__main__":
    main()
