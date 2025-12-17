"""
修复所有LangChain导入，使用兼容层
"""

import os
import re

def fix_file(filepath):
    """修复单个文件的LangChain导入"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 记录原始内容用于比较
        original_content = content
        
        # 替换LangChain导入为兼容层导入
        replacements = [
            # 消息类
            (r'from langchain_core\.messages import ([^;\n]+)',
             r'from backend.agents.utils.langchain_compat import \1'),
             
            # Prompt模板
            (r'from langchain_core\.prompts import ([^;\n]+)',
             r'from backend.agents.utils.langchain_compat import \1'),
             
            # 工具
            (r'from langchain_core\.tools import ([^;\n]+)',
             r'from backend.agents.utils.langchain_compat import \1'),
             
            # ChatOpenAI
            (r'from langchain_openai import ChatOpenAI',
             'from backend.agents.utils.langchain_compat import ChatOpenAI'),
             
            # Agent相关
            (r'from langchain\.agents import ([^;\n]+)',
             r'from backend.agents.utils.langchain_compat import \1'),
             
            # Hub
            (r'from langchain import hub',
             'from backend.agents.utils.langchain_compat import hub'),
             
            # LangGraph
            (r'from langgraph\.graph import ([^;\n]+)',
             r'from backend.agents.utils.langchain_compat import \1'),
            (r'from langgraph\.prebuilt import ([^;\n]+)',
             r'from backend.agents.utils.langchain_compat import \1'),
        ]
        
        for pattern, replacement in replacements:
            content = re.sub(pattern, replacement, content)
        
        # 如果内容有改变，写回文件
        if content != original_content:
            # 先创建备份
            backup_path = filepath + '.langchain_backup'
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
    print("修复所有LangChain导入问题")
    print("=" * 60)
    
    # 需要修复的目录
    directories = [
        r"d:\InvestMindPro\backend\agents",
    ]
    
    fixed_files = []
    skipped_files = [
        'langchain_compat.py',
        'agent_utils_simple.py'
    ]
    
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
                # 只处理.py文件，跳过备份文件和兼容层文件
                if (file.endswith('.py') and 
                    not file.endswith('.backup') and 
                    not file.endswith('.backup_v2') and
                    not file.endswith('.langchain_backup') and
                    file not in skipped_files):
                    
                    filepath = os.path.join(root, file)
                    
                    # 检查文件是否包含langchain导入
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                            if 'langchain' in content or 'langgraph' in content:
                                if fix_file(filepath):
                                    fixed_files.append(filepath)
                                    print(f"✅ 修复: {os.path.basename(filepath)}")
                    except:
                        pass
    
    print("\n" + "=" * 60)
    print(f"总计修复 {len(fixed_files)} 个文件")
    
    if fixed_files:
        print("\n修复的文件列表:")
        for f in fixed_files:
            print(f"  - {os.path.basename(f)}")
    
    print("\n" + "=" * 60)
    print("LangChain导入修复完成！")
    print("现在可以运行: start_backend.bat")
    print("=" * 60)

if __name__ == "__main__":
    main()
