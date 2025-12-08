#!/usr/bin/env python3
"""
修复server.py中analyze_stock函数的缩进问题
"""

def fix_indentation():
    file_path = r'd:\AlphaCouncil\backend\server.py'
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 从第716行开始到第813行，减少4个空格缩进
    for i in range(715, 813):  # 0-indexed, so 715 = line 716
        if lines[i].startswith('            '):  # 12个空格
            lines[i] = lines[i][4:]  # 移除4个空格，变成8个
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print("✅ 缩进修复完成！")
    print("修复范围: 第716-813行")
    print("请重启后端测试")

if __name__ == "__main__":
    fix_indentation()
