"""
快速测试导入是否正常
"""

import os
import sys

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

print("Testing imports...")

try:
    # 测试关键导入
    from backend.api.news_api import router as news_router
    print("OK - news_api imported")
    
    from backend.agents.utils.agent_utils import Toolkit, create_msg_delete
    print("OK - agent_utils imported")
    
    from backend.dataflows.config import get_config
    print("OK - dataflows config imported")
    
    print("\nAll imports successful!")
    print("You can now run: final_start.bat")
    
except Exception as e:
    print(f"\nERROR: {e}")
    import traceback
    traceback.print_exc()
