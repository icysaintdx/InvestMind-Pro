"""
正确修复 SiliconFlow API 函数的缩进问题
"""

import sys
import os

def fix_siliconflow_api():
    file_path = r"d:\InvestMindPro\backend\server.py"
    
    # 读取文件
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 创建备份
    backup_path = file_path + '.backup_indent'
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print(f"创建备份: {backup_path}")
    
    # 找到需要修正的行
    fixed_lines = []
    in_siliconflow = False
    indent_fixed = False
    
    for i, line in enumerate(lines):
        # 找到 siliconflow_api 函数
        if '@app.post("/api/ai/siliconflow")' in line:
            in_siliconflow = True
            fixed_lines.append(line)
            continue
        
        # 修复第510行附近的缩进问题
        if in_siliconflow and 'if response.status_code != 200:' in line:
            # 确保这行和上面的if response is None在同一缩进级别
            fixed_lines.append('        if response.status_code != 200:\n')
            indent_fixed = True
            print(f"修复第 {i+1} 行的缩进")
            continue
        
        # 修复result = response.json()的缩进
        if in_siliconflow and 'result = response.json()' in line:
            fixed_lines.append('        result = response.json()\n')
            print(f"修复第 {i+1} 行的缩进")
            continue
            
        # 修复text = result.get的缩进
        if in_siliconflow and 'text = result.get(' in line:
            fixed_lines.append('        text = result.get("choices", [{}])[0].get("message", {}).get("content", "")\n')
            print(f"修复第 {i+1} 行的缩进")
            continue
            
        # 修复# 获取token使用信息的缩进
        if in_siliconflow and '# 获取token使用信息' in line:
            fixed_lines.append('        # 获取token使用信息\n')
            print(f"修复第 {i+1} 行的缩进")
            continue
            
        # 修复usage = result.get的缩进
        if in_siliconflow and 'usage = result.get(' in line:
            fixed_lines.append('        usage = result.get("usage", {})\n')
            print(f"修复第 {i+1} 行的缩进")
            continue
            
        # 修复prompt_tokens等的缩进
        if in_siliconflow and 'prompt_tokens = usage.get(' in line:
            fixed_lines.append('        prompt_tokens = usage.get("prompt_tokens", 0)\n')
            print(f"修复第 {i+1} 行的缩进")
            continue
            
        if in_siliconflow and 'completion_tokens = usage.get(' in line:
            fixed_lines.append('        completion_tokens = usage.get("completion_tokens", 0)\n')
            print(f"修复第 {i+1} 行的缩进")
            continue
            
        if in_siliconflow and 'total_tokens = usage.get(' in line:
            fixed_lines.append('        total_tokens = usage.get("total_tokens", 0)\n')
            print(f"修复第 {i+1} 行的缩进")
            continue
            
        # 修复print语句的缩进
        if in_siliconflow and 'print(f"[SiliconFlow] Token使用:' in line:
            fixed_lines.append('        print(f"[SiliconFlow] Token使用: {total_tokens} (输入: {prompt_tokens}, 输出: {completion_tokens})")\n')
            print(f"修复第 {i+1} 行的缩进")
            continue
            
        # 修复return语句的缩进
        if in_siliconflow and 'return {' in line and '"success": True' in lines[i:i+5]:
            # 这是成功返回的部分
            fixed_lines.append('        return {\n')
            print(f"修复第 {i+1} 行的缩进")
            continue
            
        # 检测到下一个函数定义，退出
        if in_siliconflow and line.startswith('@app.') and i > 420:
            in_siliconflow = False
            
        fixed_lines.append(line)
    
    # 写回文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(fixed_lines)
    
    print("修复完成！")
    return indent_fixed

if __name__ == "__main__":
    if fix_siliconflow_api():
        print("缩进问题已修复，请重启后端服务器")
    else:
        print("未发现需要修复的缩进问题")
