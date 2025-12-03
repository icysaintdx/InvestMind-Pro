"""
综合修复脚本 - 确保所有问题都被修复
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("AlphaCouncil 综合修复脚本")
print("=" * 60)
print()

fixes_applied = 0

# 1. 确保tool_logging.py有log_analysis_step别名
print("1. 检查tool_logging别名...")
try:
    with open(r"d:\AlphaCouncil\backend\utils\tool_logging.py", 'r', encoding='utf-8') as f:
        content = f.read()
    
    if "log_analysis_step = log_analyst_module" not in content:
        # 添加别名
        if content.strip().endswith('print("测试完成！")'):
            content += '\n\n# 创建别名以保持向后兼容性\nlog_analysis_step = log_analyst_module\n'
        else:
            content += '\n\n# 创建别名以保持向后兼容性\nlog_analysis_step = log_analyst_module\n'
        
        with open(r"d:\AlphaCouncil\backend\utils\tool_logging.py", 'w', encoding='utf-8') as f:
            f.write(content)
        print("  ✅ 添加了log_analysis_step别名")
        fixes_applied += 1
    else:
        print("  ✅ 别名已存在")
except Exception as e:
    print(f"  ❌ 错误: {e}")

# 2. 确保config.py正确
print("\n2. 检查dataflows/config.py...")
try:
    from backend.dataflows.config import get_config, DEFAULT_CONFIG
    config = get_config()
    print("  ✅ config.py正常")
except Exception as e:
    print(f"  ❌ config.py有问题: {e}")
    # 尝试修复
    try:
        config_path = r"d:\AlphaCouncil\backend\dataflows\config.py"
        with open(config_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 查找并修复重复或错误的代码
        fixed_lines = []
        skip_next = False
        for i, line in enumerate(lines):
            if skip_next:
                skip_next = False
                continue
            # 跳过可能的重复代码
            if i < len(lines) - 1 and line.strip() == "return _config.copy()" and lines[i+1].strip().startswith("global"):
                fixed_lines.append(line)
                skip_next = True
            else:
                fixed_lines.append(line)
        
        with open(config_path, 'w', encoding='utf-8') as f:
            f.writelines(fixed_lines)
        
        print("  ✅ 已尝试修复config.py")
        fixes_applied += 1
    except Exception as fix_e:
        print(f"  ❌ 修复失败: {fix_e}")

# 3. 检查agent_utils.py
print("\n3. 检查agent_utils.py...")
agent_utils_path = r"d:\AlphaCouncil\backend\agents\utils\agent_utils.py"
try:
    with open(agent_utils_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否有log_analysis_step导入
    if "from backend.utils.tool_logging import log_tool_call, log_analysis_step" in content:
        # 移除log_analysis_step
        content = content.replace(
            "from backend.utils.tool_logging import log_tool_call, log_analysis_step",
            "from backend.utils.tool_logging import log_tool_call"
        )
        with open(agent_utils_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("  ✅ 移除了不必要的log_analysis_step导入")
        fixes_applied += 1
    else:
        print("  ✅ 导入正确")
except Exception as e:
    print(f"  ❌ 错误: {e}")

# 4. 创建必要目录
print("\n4. 创建必要目录...")
dirs_to_create = [
    r"d:\AlphaCouncil\backend\data",
    r"d:\AlphaCouncil\backend\dataflows\data",
    r"d:\AlphaCouncil\backend\dataflows\cache",
    r"d:\AlphaCouncil\logs"
]

for dir_path in dirs_to_create:
    try:
        os.makedirs(dir_path, exist_ok=True)
        print(f"  ✅ {os.path.basename(dir_path)}/")
    except:
        pass

# 5. 最终验证
print("\n5. 最终验证...")
errors = []

try:
    from backend.utils.logging_config import get_logger
    print("  ✅ 日志系统")
except ImportError as e:
    errors.append(f"日志系统: {e}")

try:
    from backend.agents.utils.agent_utils import Toolkit, create_msg_delete
    print("  ✅ agent_utils")
except ImportError as e:
    errors.append(f"agent_utils: {e}")

try:
    from backend.dataflows.config import get_config
    print("  ✅ dataflows config")
except ImportError as e:
    errors.append(f"dataflows config: {e}")

try:
    from backend.agents.utils.langchain_compat import ChatOpenAI
    print("  ✅ LangChain兼容层")
except ImportError as e:
    errors.append(f"LangChain兼容层: {e}")

print("\n" + "=" * 60)
print("修复结果")
print("=" * 60)

if errors:
    print("\n❌ 仍有错误:")
    for error in errors:
        print(f"  - {error}")
    print("\n请手动检查这些错误。")
else:
    print(f"\n✅ 所有检查通过！")
    print(f"✅ 应用了 {fixes_applied} 个修复")
    print("\n现在可以运行: final_start.bat")

print("=" * 60)
