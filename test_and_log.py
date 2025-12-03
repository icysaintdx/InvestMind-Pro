"""
测试导入并记录到文件
"""

import os
import sys

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# 打开日志文件
with open("test_result.txt", "w", encoding="utf-8") as f:
    f.write("Testing imports...\n")
    
    try:
        # 测试关键导入
        from backend.api.news_api import router as news_router
        f.write("OK - news_api imported\n")
        
        from backend.agents.utils.agent_utils import Toolkit, create_msg_delete
        f.write("OK - agent_utils imported\n")
        
        from backend.dataflows.config import get_config
        f.write("OK - dataflows config imported\n")
        
        f.write("\nAll imports successful!\n")
        f.write("You can now run: final_start.bat\n")
        
        print("Test successful! Check test_result.txt for details.")
        
    except Exception as e:
        f.write(f"\nERROR: {e}\n")
        import traceback
        f.write(traceback.format_exc())
        
        print(f"Test failed: {e}")
        print("Check test_result.txt for details.")
