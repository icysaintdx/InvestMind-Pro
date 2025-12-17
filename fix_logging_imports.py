"""
修复所有logging_init导入为logging_config
"""

import os
import re

def fix_file(filepath):
    """修复单个文件的导入"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 记录原始内容用于比较
        original_content = content
        
        # 替换导入语句
        replacements = [
            (r'from backend\.utils\.logging_init import get_logger',
             'from backend.utils.logging_config import get_logger'),
            (r'from backend\.utils\.logging_init import setup_dataflow_logging',
             'from backend.utils.logging_config import get_logger'),
            (r'from backend\.utils\.logging_manager import get_logger',
             'from backend.utils.logging_config import get_logger'),
            (r'logger = setup_dataflow_logging\(\)',
             'logger = get_logger("dataflow")'),
        ]
        
        for pattern, replacement in replacements:
            content = re.sub(pattern, replacement, content)
        
        # 如果内容有改变，写回文件
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("修复所有 logging_init 导入问题")
    print("=" * 60)
    
    # 需要修复的目录
    directories = [
        r"d:\InvestMindPro\backend\agents",
        r"d:\InvestMindPro\backend\api",
        r"d:\InvestMindPro\backend\dataflows",
    ]
    
    fixed_files = []
    
    for directory in directories:
        if not os.path.exists(directory):
            print(f"目录不存在: {directory}")
            continue
            
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    if fix_file(filepath):
                        fixed_files.append(filepath)
                        print(f"✅ 修复: {filepath}")
    
    print("\n" + "=" * 60)
    print(f"总计修复 {len(fixed_files)} 个文件")
    
    if fixed_files:
        print("\n修复的文件列表:")
        for f in fixed_files:
            print(f"  - {f}")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
