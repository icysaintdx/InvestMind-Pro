#!/usr/bin/env python3
"""
修复TradingAgents导入路径问题的脚本
将所有 tradingagents.xxx 导入替换为正确的相对路径
"""

import os
import re
from pathlib import Path

def fix_import_in_file(file_path):
    """修复单个文件中的导入路径"""
    
    # 读取文件内容
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 记录是否有修改
    modified = False
    original_content = content
    
    # 定义替换规则
    replacements = [
        # agents相关导入
        (r'from tradingagents\.agents\.', 'from agents.'),
        (r'from tradingagents\.tools\.', 'from backend.dataflows.'),
        (r'from tradingagents\.dataflows\.', 'from backend.dataflows.'),
        (r'from tradingagents\.utils\.', 'from backend.utils.'),
        (r'import tradingagents\.', 'import '),
        
        # 修复日志导入
        (r'from tradingagents\.utils\.logging_init import get_logger', 
         'from backend.utils.logging_config import get_logger'),
        (r'from tradingagents\.utils\.logging_manager import get_logger',
         'from backend.utils.logging_config import get_logger'),
        (r'from tradingagents\.utils\.tool_logging import',
         'from backend.utils.tool_logging import'),
        
        # 修复dataflows内部导入
        (r'from dataflows\.', 'from backend.dataflows.'),
        (r'import dataflows\.', 'import backend.dataflows.'),
        
        # 修复agents内部导入
        (r'from agents\.utils\.', 'from agents.utils.'),
        (r'from agents\.analysts\.', 'from agents.analysts.'),
        (r'from agents\.researchers\.', 'from agents.researchers.'),
        (r'from agents\.managers\.', 'from agents.managers.'),
        (r'from agents\.trader\.', 'from agents.trader.'),
        (r'from agents\.risk_mgmt\.', 'from agents.risk_mgmt.'),
    ]
    
    # 应用替换规则
    for pattern, replacement in replacements:
        new_content = re.sub(pattern, replacement, content)
        if new_content != content:
            modified = True
            content = new_content
    
    # 如果有修改，写回文件
    if modified:
        # 备份原文件
        backup_path = f"{file_path}.backup"
        if not os.path.exists(backup_path):
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(original_content)
        
        # 写入修改后的内容
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return True, file_path
    
    return False, file_path

def fix_imports_in_directory(directory):
    """递归修复目录中所有Python文件的导入"""
    
    fixed_files = []
    skipped_files = []
    error_files = []
    
    # 遍历所有Python文件
    for root, dirs, files in os.walk(directory):
        # 跳过__pycache__目录
        if '__pycache__' in root:
            continue
            
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    fixed, path = fix_import_in_file(file_path)
                    if fixed:
                        fixed_files.append(path)
                    else:
                        skipped_files.append(path)
                except Exception as e:
                    error_files.append((file_path, str(e)))
    
    return fixed_files, skipped_files, error_files

def main():
    """主函数"""
    print("=" * 60)
    print("TradingAgents 导入路径修复工具")
    print("=" * 60)
    
    # 获取项目根目录
    project_root = Path(__file__).parent.parent
    
    # 需要修复的目录
    directories_to_fix = [
        project_root / 'agents',
        project_root / 'backend' / 'dataflows',
        project_root / 'backend' / 'api',
    ]
    
    total_fixed = []
    total_skipped = []
    total_errors = []
    
    for directory in directories_to_fix:
        if directory.exists():
            print(f"\n处理目录: {directory}")
            fixed, skipped, errors = fix_imports_in_directory(directory)
            
            total_fixed.extend(fixed)
            total_skipped.extend(skipped)
            total_errors.extend(errors)
            
            print(f"  ✅ 修复文件: {len(fixed)}")
            print(f"  ⏭️ 跳过文件: {len(skipped)}")
            print(f"  ❌ 错误文件: {len(errors)}")
    
    # 打印总结
    print("\n" + "=" * 60)
    print("修复完成！")
    print(f"总计修复文件: {len(total_fixed)}")
    print(f"总计跳过文件: {len(total_skipped)}")
    print(f"总计错误文件: {len(total_errors)}")
    
    # 显示修复的文件列表
    if total_fixed:
        print("\n修复的文件:")
        for file in total_fixed[:10]:  # 只显示前10个
            rel_path = Path(file).relative_to(project_root)
            print(f"  • {rel_path}")
        if len(total_fixed) > 10:
            print(f"  ... 还有 {len(total_fixed) - 10} 个文件")
    
    # 显示错误信息
    if total_errors:
        print("\n❌ 错误文件:")
        for file, error in total_errors:
            rel_path = Path(file).relative_to(project_root)
            print(f"  • {rel_path}: {error}")
    
    print("\n💡 提示:")
    print("1. 原始文件已备份为 .backup 文件")
    print("2. 如需恢复，删除修改的文件并重命名 .backup 文件")
    print("3. 建议手动检查修复后的导入是否正确")

if __name__ == "__main__":
    main()
