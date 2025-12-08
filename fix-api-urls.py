"""
批量替换前端 API URL
"""
import os
import re

# 需要修复的文件
files_to_fix = [
    'alpha-council-vue/src/views/AnalysisView.vue',
    'alpha-council-vue/src/views/HistoryView.vue',
    'alpha-council-vue/src/views/DocumentView.vue',
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
    
    # 替换所有 http://localhost:8000 为空字符串（使用相对路径）
    content = content.replace('http://localhost:8000', '')
    
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
    print("批量修复前端 API URL")
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
    print()
    print("现在运行: docker-build-all-in-one.bat")

if __name__ == '__main__':
    main()
