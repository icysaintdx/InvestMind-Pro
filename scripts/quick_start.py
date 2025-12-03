#!/usr/bin/env python3
"""
TradingAgents 集成快速启动脚本
用于检查环境、修复导入、测试基础功能
"""

import os
import sys
import subprocess
from pathlib import Path
import importlib.util

# 添加项目根目录到Python路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def print_header(title):
    """打印格式化标题"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def check_python_version():
    """检查Python版本"""
    print_header("检查Python版本")
    version = sys.version_info
    print(f"当前Python版本: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python版本过低！需要Python 3.8或更高版本")
        return False
    
    print("✅ Python版本符合要求")
    return True

def check_dependencies():
    """检查核心依赖"""
    print_header("检查核心依赖")
    
    required_packages = {
        'fastapi': 'FastAPI Web框架',
        'uvicorn': 'ASGI服务器',
        'pandas': '数据处理',
        'numpy': '数值计算',
        'httpx': 'HTTP客户端',
        'pydantic': '数据验证',
        'langchain': 'LLM框架',
        'tushare': 'A股数据',
    }
    
    missing_packages = []
    installed_packages = []
    
    for package, description in required_packages.items():
        if importlib.util.find_spec(package):
            installed_packages.append(package)
            print(f"✅ {package:15} - {description}")
        else:
            missing_packages.append(package)
            print(f"❌ {package:15} - {description} (未安装)")
    
    if missing_packages:
        print(f"\n缺少 {len(missing_packages)} 个必要依赖包")
        print("请运行以下命令安装：")
        print(f"  pip install {' '.join(missing_packages)}")
        print("\n或使用完整依赖文件：")
        print("  pip install -r requirements_trading.txt")
        return False
    
    print(f"\n✅ 所有核心依赖已安装")
    return True

def fix_imports():
    """修复导入路径"""
    print_header("修复导入路径")
    
    fix_script = PROJECT_ROOT / "scripts" / "fix_imports.py"
    if not fix_script.exists():
        print("❌ 修复脚本不存在")
        return False
    
    try:
        # 运行修复脚本
        result = subprocess.run(
            [sys.executable, str(fix_script)],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ 导入路径修复成功")
            return True
        else:
            print("❌ 导入路径修复失败")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ 运行修复脚本失败: {e}")
        return False

def test_basic_imports():
    """测试基础导入"""
    print_header("测试基础导入")
    
    test_imports = [
        ("backend.utils.logging_config", "日志系统"),
        ("backend.dataflows.stock_data_service", "股票数据服务"),
        ("agents.analysts.news_analyst", "新闻分析师"),
        ("agents.researchers.bull_researcher", "看涨研究员"),
    ]
    
    success_count = 0
    for module_name, description in test_imports:
        try:
            module = importlib.import_module(module_name)
            print(f"✅ {description:20} - {module_name}")
            success_count += 1
        except ImportError as e:
            print(f"❌ {description:20} - {module_name}")
            print(f"   错误: {e}")
        except Exception as e:
            print(f"⚠️ {description:20} - {module_name}")
            print(f"   警告: {e}")
    
    if success_count == len(test_imports):
        print(f"\n✅ 所有模块导入成功")
        return True
    else:
        print(f"\n⚠️ 部分模块导入失败 ({success_count}/{len(test_imports)})")
        return False

def test_data_sources():
    """测试数据源连接"""
    print_header("测试数据源")
    
    # 测试Tushare
    try:
        import tushare as ts
        token = os.getenv('TUSHARE_TOKEN')
        if token:
            ts.set_token(token)
            pro = ts.pro_api()
            # 测试获取交易日历
            df = pro.trade_cal(exchange='SSE', is_open='1', limit=1)
            if not df.empty:
                print(f"✅ Tushare连接成功")
            else:
                print(f"⚠️ Tushare连接成功但无数据")
        else:
            print("⚠️ 未配置TUSHARE_TOKEN")
    except Exception as e:
        print(f"❌ Tushare连接失败: {e}")
    
    # 测试AkShare
    try:
        import akshare as ak
        # 测试获取股票列表
        df = ak.stock_info_a_code_name()
        if not df.empty:
            print(f"✅ AkShare连接成功 (获取到 {len(df)} 只股票)")
        else:
            print(f"⚠️ AkShare连接成功但无数据")
    except Exception as e:
        print(f"❌ AkShare连接失败: {e}")
    
    return True

def create_directories():
    """创建必要的目录"""
    print_header("创建必要目录")
    
    directories = [
        PROJECT_ROOT / "logs",
        PROJECT_ROOT / "data",
        PROJECT_ROOT / "cache",
        PROJECT_ROOT / "reports",
        PROJECT_ROOT / "backtest",
    ]
    
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            print(f"✅ 创建目录: {directory.relative_to(PROJECT_ROOT)}")
        else:
            print(f"⏭️ 目录已存在: {directory.relative_to(PROJECT_ROOT)}")
    
    return True

def test_news_analyst():
    """测试新闻分析师基础功能"""
    print_header("测试新闻分析师")
    
    try:
        # 初始化日志系统
        from backend.utils.logging_config import init_logging
        init_logging(level="INFO")
        
        # 导入新闻分析相关模块
        from backend.agents.analysts.news_analyst import create_news_analyst
        
        print("✅ 新闻分析师模块加载成功")
        
        # 创建测试状态
        test_state = {
            "company_of_interest": "000001",
            "trade_date": "2024-01-01",
            "session_id": "test-session"
        }
        
        print(f"📊 测试股票: {test_state['company_of_interest']}")
        print(f"📅 测试日期: {test_state['trade_date']}")
        
        # 注意：实际测试需要配置LLM和toolkit
        print("⚠️ 完整测试需要配置LLM和数据工具包")
        
        return True
        
    except Exception as e:
        print(f"❌ 新闻分析师测试失败: {e}")
        return False

def show_next_steps():
    """显示下一步操作建议"""
    print_header("下一步操作")
    
    print("""
📋 建议的下一步操作：

1. 📝 配置环境变量
   - 创建或编辑 .env 文件
   - 添加必要的API密钥：
     TUSHARE_TOKEN=your_token
     JUHE_API_KEY=your_key
     GEMINI_API_KEY=your_key (如使用)
     DEEPSEEK_API_KEY=your_key (如使用)

2. 📦 安装完整依赖
   pip install -r requirements_trading.txt

3. 🔧 运行导入修复
   python scripts/fix_imports.py

4. 🚀 启动后端服务
   cd backend
   python server.py

5. 📊 测试新闻分析API
   访问: http://localhost:8000/docs
   测试: POST /api/news/analyze

6. 🎯 集成到前端
   - 修改 backend/static/app.js
   - 添加新闻分析调用
   - 更新UI显示

7. 📈 测试完整流程
   - 输入股票代码
   - 触发多智能体分析
   - 查看结构化决策
   - 执行模拟交易

详细文档请查看：
- TRADINGAGENTS_INTEGRATION_PLAN.md
- docs/设计原型.md
""")

def main():
    """主函数"""
    print("=" * 60)
    print("  TradingAgents 集成环境检查与快速启动")
    print("=" * 60)
    
    # 执行检查步骤
    steps = [
        ("Python版本", check_python_version),
        ("创建目录", create_directories),
        ("核心依赖", check_dependencies),
        # ("修复导入", fix_imports),  # 暂时跳过，避免破坏现有代码
        ("基础导入", test_basic_imports),
        ("数据源", test_data_sources),
        ("新闻分析师", test_news_analyst),
    ]
    
    results = []
    for step_name, step_func in steps:
        try:
            success = step_func()
            results.append((step_name, success))
        except Exception as e:
            print(f"\n❌ 步骤 '{step_name}' 执行失败: {e}")
            results.append((step_name, False))
    
    # 显示总结
    print_header("检查总结")
    success_count = sum(1 for _, success in results if success)
    total_count = len(results)
    
    for step_name, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {step_name}")
    
    print(f"\n完成度: {success_count}/{total_count}")
    
    if success_count == total_count:
        print("\n🎉 所有检查通过！系统已准备就绪")
    elif success_count >= total_count * 0.7:
        print("\n⚠️ 大部分检查通过，但仍有一些问题需要解决")
    else:
        print("\n❌ 多项检查未通过，请先解决上述问题")
    
    # 显示下一步建议
    show_next_steps()

if __name__ == "__main__":
    main()
