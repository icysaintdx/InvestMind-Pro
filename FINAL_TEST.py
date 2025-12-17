#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Final test to verify all imports work
"""

import os
import sys
import traceback

# Add project root to path
project_root = r"D:\InvestMindPro"
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def test_imports():
    """Test all critical imports"""
    errors = []
    
    # Test 1: Tool logging
    try:
        from backend.utils.tool_logging import log_tool_call
        print("✓ tool_logging imported")
    except Exception as e:
        errors.append(f"tool_logging: {str(e)}")
        print(f"✗ tool_logging failed: {e}")
    
    # Test 2: Agent utils
    try:
        from backend.agents.utils.agent_utils import Toolkit, create_msg_delete
        print("✓ agent_utils imported")
    except Exception as e:
        errors.append(f"agent_utils: {str(e)}")
        print(f"✗ agent_utils failed: {e}")
    
    # Test 3: Dataflows config
    try:
        from backend.dataflows.config import get_config
        print("✓ dataflows config imported")
    except Exception as e:
        errors.append(f"dataflows config: {str(e)}")
        print(f"✗ dataflows config failed: {e}")
    
    # Test 4: API routers
    try:
        from backend.api.news_api import router as news_router
        print("✓ news_api imported")
    except Exception as e:
        errors.append(f"news_api: {str(e)}")
        print(f"✗ news_api failed: {e}")
    
    # Summary
    print("\n" + "="*50)
    if errors:
        print("FAILED - There are still import errors:")
        for error in errors:
            print(f"  - {error}")
        return False
    else:
        print("SUCCESS - All imports working!")
        print("\nYou can now run: final_start.bat")
        return True

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
