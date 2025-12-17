#!/usr/bin/env python3
"""
测试实际的提示词长度
"""

# 模拟第三阶段的提示词构建
def calculate_prompt_length():
    # 系统提示词
    system_prompt = """你是一个专业的激进风控师，隶属于InvestMindPro顶级投研团队。你的目标是提供深度、犀利且独到的投资见解。

【风格要求】
1. 直接切入主题，严禁废话。
2. 严禁在开头复述股票代码、名称、当前价格等基础信息（除非数据出现重大异常）。
3. 像华尔街资深分析师一样说话，使用专业术语但逻辑清晰。
4. 必须引用前序同事的分析结论作为支撑或反驳的依据。"""
    
    # 自定义指令（风控师）
    custom_instruction = """假设我们必须买入，如何设置止损以最大化赔率？"""
    
    # 基础数据
    basic_data = """【参考数据 - 600547】
价格: 10.50 | 涨跌: 2.5%
成交: 1000000"""
    
    # 前序输出（模拟8个智能体，每个500字符）
    previous_outputs = """【团队成员已完成的分析】(请基于此进行深化，不要重复)
>>> 新闻分析师 的结论:
""" + ("X" * 500) + "...\n\n"
    
    # 假设有8个前序智能体
    previous_outputs = previous_outputs * 8
    
    user_prompt = f"""【当前任务指令】
{custom_instruction}

{basic_data}

{previous_outputs}"""
    
    print("="*60)
    print("提示词长度分析")
    print("="*60)
    print(f"系统提示词: {len(system_prompt)} 字符")
    print(f"用户提示词: {len(user_prompt)} 字符")
    print(f"总长度: {len(system_prompt) + len(user_prompt)} 字符")
    print()
    print(f"估算Token数: {(len(system_prompt) + len(user_prompt)) // 2} tokens")
    print(f"模型上下文: 128K tokens")
    print(f"使用比例: {((len(system_prompt) + len(user_prompt)) // 2) / 128000 * 100:.2f}%")
    print()
    print("结论: 提示词长度完全不是问题！")
    print("="*60)

if __name__ == "__main__":
    calculate_prompt_length()
