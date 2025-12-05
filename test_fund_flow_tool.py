#!/usr/bin/env python3
"""
测试资金流向工具
验证工具能否正确为分析师提供数据
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from agents.utils.fund_flow_tools import get_fund_flow_tool


def test_fund_flow_tool_without_symbol():
    """测试不带股票代码的资金流向工具"""
    print("\n" + "="*60)
    print("测试1: 获取全市场资金流向数据")
    print("="*60)
    
    tool = get_fund_flow_tool()
    result = tool._run()
    
    print(result)


def test_fund_flow_tool_with_symbol():
    """测试带股票代码的资金流向工具"""
    print("\n" + "="*60)
    print("测试2: 获取贵州茅台(600519)资金流向数据")
    print("="*60)
    
    tool = get_fund_flow_tool()
    result = tool._run("600519")
    
    print(result)


def test_tool_description():
    """测试工具描述"""
    print("\n" + "="*60)
    print("测试3: 工具描述信息")
    print("="*60)
    
    tool = get_fund_flow_tool()
    print(f"工具名称: {tool.name}")
    print(f"\n工具描述:\n{tool.description}")


def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("资金流向工具测试")
    print("为资金流向分析师提供数据支持")
    print("="*60)
    
    try:
        # 测试1: 全市场数据
        test_fund_flow_tool_without_symbol()
        
        # 测试2: 个股数据
        test_fund_flow_tool_with_symbol()
        
        # 测试3: 工具描述
        test_tool_description()
        
        print("\n" + "="*60)
        print("✅ 所有测试完成")
        print("="*60)
        print("\n下一步：将此工具集成到资金流向分析师")
        print("修改文件: backend/agents/analysts/[资金流向分析师文件]")
        print("添加工具: tools = [fund_flow_tool]")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
