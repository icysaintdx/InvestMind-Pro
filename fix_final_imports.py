"""
最终的导入修复脚本
修复所有剩余的导入问题
"""

import os
import re

def fix_log_analysis_step(filepath):
    """修复log_analysis_step导入"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 移除log_analysis_step导入
        content = re.sub(
            r'from backend\.utils\.tool_logging import ([^,\n]*),\s*log_analysis_step',
            r'from backend.utils.tool_logging import \1',
            content
        )
        
        # 如果只导入log_analysis_step，则改为log_analyst_module
        content = re.sub(
            r'from backend\.utils\.tool_logging import log_analysis_step',
            'from backend.utils.tool_logging import log_analyst_module as log_analysis_step',
            content
        )
        
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False

def main():
    print("=" * 60)
    print("修复最终的导入问题")
    print("=" * 60)
    
    # 需要扫描的目录
    directories = [
        r"d:\AlphaCouncil\backend\agents",
        r"d:\AlphaCouncil\backend\dataflows",
    ]
    
    fixed_files = []
    
    for directory in directories:
        if not os.path.exists(directory):
            continue
            
        for root, dirs, files in os.walk(directory):
            if '__pycache__' in root:
                continue
                
            for file in files:
                if file.endswith('.py') and not file.endswith('.backup'):
                    filepath = os.path.join(root, file)
                    
                    # 检查是否包含log_analysis_step
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            if 'log_analysis_step' in f.read():
                                if fix_log_analysis_step(filepath):
                                    fixed_files.append(filepath)
                                    print(f"✅ 修复: {os.path.basename(filepath)}")
                    except:
                        pass
    
    print("\n" + "=" * 60)
    print(f"修复了 {len(fixed_files)} 个文件")
    
    if fixed_files:
        print("\n修复的文件:")
        for f in fixed_files:
            print(f"  - {os.path.basename(f)}")
    
    print("\n" + "=" * 60)
    print("修复完成！")

if __name__ == "__main__":
    main()
