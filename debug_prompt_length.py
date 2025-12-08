#!/usr/bin/env python3
"""
在后端添加日志，查看实际的Prompt长度
"""

print("""
在 backend/server.py 的 analyze_stock 函数中添加以下日志：

在第813行（调用SiliconFlow API之前）添加：

# 添加详细日志
prompt_len = len(system_prompt) + len(user_prompt)
print(f"[分析] {request.agent_id} 系统提示词: {len(system_prompt)} 字符")
print(f"[分析] {request.agent_id} 用户提示词: {len(user_prompt)} 字符")
print(f"[分析] {request.agent_id} 总长度: {prompt_len} 字符 (~{prompt_len//2} tokens)")

# 如果有前序输出，打印每个的长度
if previous_outputs:
    print(f"[分析] {request.agent_id} 前序输出数量: {len(previous_outputs)}")
    for agent_name, output in previous_outputs.items():
        print(f"  - {agent_name}: {len(output)} 字符")

这样我们就能看到实际的Prompt长度了！
""")
