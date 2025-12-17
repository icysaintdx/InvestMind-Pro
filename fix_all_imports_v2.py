"""
修复所有导入问题：
1. logging_init -> logging_config
2. 移除tradingagents导入
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
        
        # 修复logging导入
        replacements = [
            # 修复logging_init导入
            (r'from backend\.utils\.logging_init import get_logger',
             'from backend.utils.logging_config import get_logger'),
            (r'from backend\.utils\.logging_init import setup_dataflow_logging',
             'from backend.utils.logging_config import get_logger'),
            (r'from backend\.utils\.logging_manager import get_logger',
             'from backend.utils.logging_config import get_logger'),
            (r'logger = setup_dataflow_logging\(\)',
             'logger = get_logger("dataflow")'),
             
            # 移除或注释tradingagents导入
            (r'^from tradingagents\.utils\.logging_init import.*$',
             '# from tradingagents.utils.logging_init import get_logger  # 已移除'),
            (r'^from tradingagents\.utils\.logging_manager import.*$',
             '# from tradingagents.utils.logging_manager import get_logger  # 已移除'),
            (r'^from tradingagents\.config\.database_manager import.*$',
             '# from tradingagents.config.database_manager import get_database_manager  # 已移除'),
            (r'^from tradingagents\.config\.runtime_settings import.*$',
             '# from tradingagents.config.runtime_settings import get_int, get_float  # 已移除'),
            (r'^from tradingagents\.config\.config_manager import.*$',
             '# from tradingagents.config.config_manager import config_manager  # 已移除'),
            (r'^from tradingagents\.dataflows\..*$',
             '# 已移除tradingagents导入'),
            (r'^import tradingagents\..*$',
             '# 已移除tradingagents导入'),
        ]
        
        for pattern, replacement in replacements:
            content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
        
        # 如果内容有改变，写回文件
        if content != original_content:
            # 先创建备份
            backup_path = filepath + '.backup_v2'
            if not os.path.exists(backup_path):
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(original_content)
            
            # 写入修改后的内容
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
    print("修复所有导入问题（logging + tradingagents）")
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
            
        print(f"\n扫描目录: {directory}")
        for root, dirs, files in os.walk(directory):
            # 跳过__pycache__目录
            if '__pycache__' in root:
                continue
                
            for file in files:
                # 只处理.py文件，跳过备份文件
                if file.endswith('.py') and not file.endswith('.backup') and not file.endswith('.backup_v2'):
                    filepath = os.path.join(root, file)
                    if fix_file(filepath):
                        fixed_files.append(filepath)
                        print(f"✅ 修复: {os.path.basename(filepath)}")
    
    print("\n" + "=" * 60)
    print(f"总计修复 {len(fixed_files)} 个文件")
    
    if fixed_files:
        print("\n修复的文件列表:")
        for f in fixed_files:
            print(f"  - {os.path.basename(f)}")
    
    print("\n" + "=" * 60)
    print("修复完成！现在可以运行: start_backend.bat")
    print("=" * 60)

if __name__ == "__main__":
    main()
