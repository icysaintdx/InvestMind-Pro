"""
验证所有修复是否成功
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("验证AlphaCouncil修复状态")
print("=" * 60)

errors = []
warnings = []

# 1. 检查config.py是否正确
try:
    from backend.dataflows.config import get_config, DEFAULT_CONFIG
    config = get_config()
    print("✅ config.py 正常工作")
except ImportError as e:
    errors.append(f"config.py 导入错误: {e}")
except Exception as e:
    errors.append(f"config.py 错误: {e}")

# 2. 检查LangChain兼容层
try:
    from backend.agents.utils.langchain_compat import (
        BaseMessage, HumanMessage, AIMessage, ChatOpenAI
    )
    print("✅ LangChain兼容层正常")
except ImportError as e:
    errors.append(f"LangChain兼容层导入错误: {e}")

# 3. 检查agent_utils
try:
    from backend.agents.utils.agent_utils import Toolkit, create_msg_delete
    print("✅ agent_utils 正常")
except ImportError as e:
    errors.append(f"agent_utils 导入错误: {e}")
    
# 3.1 检查tool_logging的log_analysis_step
try:
    from backend.utils.tool_logging import log_tool_call, log_analyst_module
    # 检查别名
    from backend.utils.tool_logging import log_analysis_step
    print("✅ tool_logging 别名正常")
except ImportError as e:
    warnings.append(f"tool_logging 别名警告: {e}")

# 4. 检查日志系统
try:
    from backend.utils.logging_config import get_logger
    logger = get_logger("test")
    print("✅ 日志系统正常")
except ImportError as e:
    errors.append(f"日志系统导入错误: {e}")

# 5. 检查LLM客户端
try:
    from backend.utils.llm_client import create_llm_client
    print("✅ LLM客户端正常")
except ImportError as e:
    errors.append(f"LLM客户端导入错误: {e}")

# 6. 检查数据流初始化
try:
    import backend.dataflows
    print("✅ 数据流模块正常")
    # 检查可选模块
    if not backend.dataflows.YFINANCE_AVAILABLE:
        warnings.append("yfinance未安装（可选）")
    if not backend.dataflows.STOCKSTATS_AVAILABLE:
        warnings.append("stockstats未安装（可选）")
except ImportError as e:
    errors.append(f"数据流模块导入错误: {e}")

# 7. 检查智能体模块
try:
    import backend.agents
    print("✅ 智能体模块正常")
except ImportError as e:
    errors.append(f"智能体模块导入错误: {e}")

# 8. 检查API路由
try:
    from backend.api.news_api import router as news_router
    from backend.api.debate_api import router as debate_router
    from backend.api.trading_api import router as trading_router
    from backend.api.verification_api import router as verification_router
    from backend.api.agents_api import router as agents_router
    print("✅ 所有API路由正常")
except ImportError as e:
    errors.append(f"API路由导入错误: {e}")

print("\n" + "=" * 60)
print("验证结果")
print("=" * 60)

if errors:
    print("\n❌ 发现错误：")
    for error in errors:
        print(f"  - {error}")
else:
    print("\n✅ 所有核心模块正常！")

if warnings:
    print("\n⚠️ 警告（可选模块）：")
    for warning in warnings:
        print(f"  - {warning}")
    print("\n这些是可选模块，不影响核心功能。")

if not errors:
    print("\n" + "=" * 60)
    print("✅ 系统已准备就绪！")
    print("现在可以运行: start_now.bat")
    print("=" * 60)
else:
    print("\n" + "=" * 60)
    print("❌ 请先修复上述错误")
    print("=" * 60)
