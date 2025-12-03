#!/usr/bin/env python3
"""
环境检查工具
检查所有依赖是否安装，配置是否正确
"""

import sys
import os
from pathlib import Path

def check_python_version():
    """检查Python版本"""
    print("🐍 Python版本检查...")
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print(f"  ✅ Python {version.major}.{version.minor}.{version.micro}")
    else:
        print(f"  ❌ Python版本过低: {sys.version}")
        print("     需要Python 3.8或更高版本")
    print()

def check_packages():
    """检查必要的包"""
    print("📦 依赖包检查...")
    
    required_packages = [
        # Web框架
        ("fastapi", "FastAPI框架"),
        ("uvicorn", "ASGI服务器"),
        ("httpx", "HTTP客户端"),
        
        # 数据处理
        ("pandas", "数据分析"),
        ("numpy", "数值计算"),
        
        # 数据源
        ("akshare", "AkShare数据接口"),
        ("tushare", "Tushare数据接口"),
        ("beautifulsoup4", "网页解析"),
        ("lxml", "XML处理"),
        
        # 工具
        ("pydantic", "数据验证"),
        ("python-dotenv", "环境变量"),
        ("colorlog", "彩色日志"),
    ]
    
    missing = []
    
    for package, description in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"  ✅ {package} - {description}")
        except ImportError:
            print(f"  ❌ {package} - {description} (未安装)")
            missing.append(package)
            
    if missing:
        print(f"\n  ⚠️ 缺少 {len(missing)} 个包")
        print(f"  运行: pip install {' '.join(missing)}")
    else:
        print(f"\n  ✨ 所有依赖包已安装")
    print()
    
    return len(missing) == 0

def check_directories():
    """检查目录结构"""
    print("📁 目录结构检查...")
    
    required_dirs = [
        "backend/agents",
        "backend/api",
        "backend/dataflows",
        "backend/utils",
        "backend/data",
        "scripts",
        "docs",
        "alpha-council-vue"
    ]
    
    project_root = Path(__file__).parent.parent
    missing = []
    
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if full_path.exists():
            # 计算文件数量
            if full_path.is_dir():
                file_count = len(list(full_path.rglob("*.py"))) if "backend" in dir_path else len(list(full_path.iterdir()))
                print(f"  ✅ {dir_path}/ ({file_count} files)")
            else:
                print(f"  ✅ {dir_path}")
        else:
            print(f"  ❌ {dir_path} (不存在)")
            missing.append(dir_path)
            
    if missing:
        print(f"\n  ⚠️ 缺少 {len(missing)} 个目录")
        for dir_path in missing:
            print(f"     mkdir {dir_path}")
    else:
        print(f"\n  ✨ 目录结构完整")
    print()
    
    return len(missing) == 0

def check_env_file():
    """检查环境变量配置"""
    print("🔐 环境变量检查...")
    
    project_root = Path(__file__).parent.parent
    env_file = project_root / ".env"
    
    if env_file.exists():
        print(f"  ✅ .env文件存在")
        
        # 读取并检查关键配置
        from dotenv import dotenv_values
        config = dotenv_values(env_file)
        
        required_keys = [
            ("DEEPSEEK_API_KEY", "DeepSeek API密钥"),
            ("QWEN_API_KEY", "Qwen API密钥"),
            ("DASHSCOPE_API_KEY", "DashScope API密钥"),
            ("TUSHARE_TOKEN", "Tushare数据令牌"),
            ("JUHE_API_KEY", "聚合数据API密钥"),
        ]
        
        missing = []
        for key, description in required_keys:
            if key in config and config[key] and config[key] != "your_key_here":
                print(f"  ✅ {key} - {description}")
            else:
                print(f"  ⚠️ {key} - {description} (未配置)")
                missing.append(key)
                
        if missing:
            print(f"\n  ⚠️ 有 {len(missing)} 个API密钥未配置")
            print("     请在.env文件中配置这些密钥")
        else:
            print(f"\n  ✨ 所有API密钥已配置")
    else:
        print(f"  ❌ .env文件不存在")
        print(f"     请创建.env文件并配置API密钥")
        
        # 创建示例文件
        env_example = project_root / ".env.example"
        if env_example.exists():
            print(f"     可以参考 .env.example 文件")
    print()

def check_api_files():
    """检查API文件是否存在"""
    print("🔌 API模块检查...")
    
    api_files = [
        ("backend/api/news_api.py", "新闻分析API"),
        ("backend/api/debate_api.py", "智能体辩论API"),
        ("backend/api/trading_api.py", "模拟交易API"),
        ("backend/api/verification_api.py", "闭环验证API"),
        ("backend/dataflows/china_market_crawler.py", "中国市场爬虫"),
    ]
    
    project_root = Path(__file__).parent.parent
    missing = []
    
    for file_path, description in api_files:
        full_path = project_root / file_path
        if full_path.exists():
            size = full_path.stat().st_size
            print(f"  ✅ {file_path} ({size:,} bytes) - {description}")
        else:
            print(f"  ❌ {file_path} - {description} (不存在)")
            missing.append(file_path)
            
    if missing:
        print(f"\n  ⚠️ 缺少 {len(missing)} 个文件")
    else:
        print(f"\n  ✨ 所有API模块已就绪")
    print()
    
    return len(missing) == 0

def main():
    """主函数"""
    print("=" * 60)
    print("AlphaCouncil 环境检查工具")
    print("=" * 60)
    print()
    
    # 运行各项检查
    results = []
    results.append(("Python版本", check_python_version()))
    results.append(("依赖包", check_packages()))
    results.append(("目录结构", check_directories()))
    results.append(("环境变量", check_env_file()))
    results.append(("API模块", check_api_files()))
    
    # 总结
    print("=" * 60)
    print("检查结果总结")
    print("=" * 60)
    
    all_pass = all(r if r is not None else True for _, r in results)
    
    if all_pass:
        print("✅ 环境检查通过！")
        print("\n可以运行以下命令启动项目：")
        print("  1. python backend/server.py  # 启动后端")
        print("  2. cd alpha-council-vue && npm run serve  # 启动前端")
        print("\n或使用快速启动：")
        print("  quick_start.bat")
    else:
        print("❌ 环境检查发现问题")
        print("\n请按照上述提示解决问题后再启动项目")
        
    print("\n💡 提示：")
    print("  - 使用 pip install -r requirements_trading.txt 安装依赖")
    print("  - 使用 python scripts/fix_imports.py 修复导入路径")
    print("  - 使用 python scripts/test_all_apis.py 测试API")
    
if __name__ == "__main__":
    main()
