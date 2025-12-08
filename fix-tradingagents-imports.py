"""
批量修复 tradingagents 导入
"""
import os
import re

# 需要修复的文件列表
files_to_fix = [
    'backend/dataflows/stock_api_tradingagents.py',
    'backend/dataflows/stock_data_service.py',
    'backend/dataflows/utils/agent_utils.py',
    'backend/dataflows/stock/stock_data_service.py',
]

# 替换规则
replacements = [
    # 日志导入
    (
        r'from tradingagents\.utils\.logging_manager import get_logger',
        'from backend.utils.logging_config import get_logger'
    ),
    # 配置导入
    (
        r'from tradingagents\.config\.config_manager import config_manager',
        '# from tradingagents.config.config_manager import config_manager  # 已移除'
    ),
    (
        r'from tradingagents\.config\.database_manager import get_database_manager',
        '# from tradingagents.config.database_manager import get_database_manager  # 已移除'
    ),
    (
        r'from tradingagents\.default_config import DEFAULT_CONFIG',
        '# from tradingagents.default_config import DEFAULT_CONFIG  # 已移除\nDEFAULT_CONFIG = {}'
    ),
]

def fix_file(filepath):
    """修复单个文件"""
    if not os.path.exists(filepath):
        print(f"⚠️  文件不存在: {filepath}")
        return False
    
    print(f"🔧 修复: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content)
    
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"   ✅ 已修复")
        return True
    else:
        print(f"   ⏭️  无需修复")
        return False

def main():
    print("=" * 60)
    print("批量修复 tradingagents 导入")
    print("=" * 60)
    print()
    
    fixed_count = 0
    for filepath in files_to_fix:
        if fix_file(filepath):
            fixed_count += 1
        print()
    
    print("=" * 60)
    print(f"✅ 完成！修复了 {fixed_count} 个文件")
    print("=" * 60)

if __name__ == '__main__':
    main()
