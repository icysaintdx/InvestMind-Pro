"""
修复log_tool_call装饰器的参数问题
移除不支持的log_args参数
"""

import os
import re

def fix_decorator_params(filepath):
    """修复装饰器参数"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 移除log_args参数
        # 匹配 @log_tool_call(..., log_args=True)
        content = re.sub(
            r'@log_tool_call\(([^,)]+),\s*log_args=True\)',
            r'@log_tool_call(\1)',
            content
        )
        
        # 如果只有log_args参数，则移除整个参数
        content = re.sub(
            r'@log_tool_call\(tool_name="([^"]+)",\s*log_args=True\)',
            r'@log_tool_call(tool_name="\1")',
            content
        )
        
        if content != original_content:
            # 备份原文件
            backup_path = filepath + '.decorator_backup'
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
    print("=" * 60)
    print("修复log_tool_call装饰器参数问题")
    print("=" * 60)
    print()
    
    # 需要修复的文件
    files_to_fix = [
        r"d:\InvestMindPro\backend\agents\utils\agent_utils.py",
        r"d:\InvestMindPro\backend\dataflows\agent_utils.py",
    ]
    
    fixed_files = []
    
    for filepath in files_to_fix:
        if not os.path.exists(filepath):
            print(f"文件不存在: {filepath}")
            continue
            
        print(f"检查: {os.path.basename(filepath)}...")
        
        # 先检查是否包含问题
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                if 'log_args=True' in f.read():
                    if fix_decorator_params(filepath):
                        fixed_files.append(filepath)
                        print(f"  ✅ 修复: {os.path.basename(filepath)}")
                    else:
                        print(f"  ⚠️ 未修改: {os.path.basename(filepath)}")
                else:
                    print(f"  ✅ 无需修复")
        except Exception as e:
            print(f"  ❌ 错误: {e}")
    
    # 扫描其他可能的文件
    print("\n扫描其他文件...")
    directories = [
        r"d:\InvestMindPro\backend\agents",
        r"d:\InvestMindPro\backend\dataflows",
    ]
    
    for directory in directories:
        if not os.path.exists(directory):
            continue
            
        for root, dirs, files in os.walk(directory):
            if '__pycache__' in root:
                continue
                
            for file in files:
                if file.endswith('.py') and not file.endswith('.backup'):
                    filepath = os.path.join(root, file)
                    
                    # 检查是否包含log_args=True
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                            if 'log_args=True' in content and filepath not in fixed_files:
                                print(f"发现问题文件: {os.path.basename(filepath)}")
                                if fix_decorator_params(filepath):
                                    fixed_files.append(filepath)
                                    print(f"  ✅ 修复: {os.path.basename(filepath)}")
                    except:
                        pass
    
    print("\n" + "=" * 60)
    print(f"修复了 {len(fixed_files)} 个文件")
    
    if fixed_files:
        print("\n修复的文件:")
        for f in fixed_files:
            print(f"  - {os.path.basename(f)}")
    
    print("\n" + "=" * 60)
    print("修复完成！现在可以运行服务器了。")
    print("运行: final_start.bat")
    print("=" * 60)

if __name__ == "__main__":
    main()
