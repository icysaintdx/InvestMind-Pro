"""
Test only the critical import issue
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

output = []

try:
    output.append("1. Testing tool_logging import...")
    from backend.utils.tool_logging import log_tool_call
    output.append("   OK - log_tool_call imported")
    
    # Test if it accepts the right parameters
    def dummy_func():
        pass
    
    decorated = log_tool_call(tool_name="test")(dummy_func)
    output.append("   OK - decorator works")
    
except Exception as e:
    output.append(f"   ERROR: {e}")
    import traceback
    output.append(traceback.format_exc())

try:
    output.append("\n2. Testing agent_utils import...")
    from backend.agents.utils.agent_utils import Toolkit, create_msg_delete
    output.append("   OK - agent_utils imported")
    output.append("   OK - Toolkit class loaded")
    
except Exception as e:
    output.append(f"   ERROR: {e}")
    import traceback
    output.append(traceback.format_exc())

# Write output
with open("test_output.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(output))
    
print("Test complete. Results written to test_output.txt")
