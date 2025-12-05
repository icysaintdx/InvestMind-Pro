#!/usr/bin/env python3
"""
资金流向数据工具
为资金流向分析师提供数据支持
"""

from backend.dataflows.akshare.fund_flow_data import get_fund_flow_data
from backend.agents.utils.langchain_compat import BaseTool
from typing import Optional
import json


class FundFlowTool(BaseTool):
    """资金流向数据工具"""
    name: str = "get_fund_flow_data"
    description: str = """
    获取资金流向数据，包括：
    1. 北向资金实时流入流出（分钟级数据）
    2. 个股主力资金动向（5000+个股）
    3. 行业和概念资金流向（90行业+400概念）
    4. 融资融券数据（市场杠杆水平）
    
    参数：
    - symbol: 股票代码（可选，如：600519）
    
    返回：包含所有资金流向数据的字典
    
    使用场景：
    - 监控北向资金流入流出
    - 发现主力资金集中流入的个股
    - 判断行业轮动方向
    - 分析市场情绪和杠杆水平
    """
    
    def _run(self, symbol: Optional[str] = None) -> str:
        """执行工具"""
        try:
            fund_flow = get_fund_flow_data()
            result = fund_flow.get_comprehensive_fund_flow(symbol)
            
            # 格式化输出，便于LLM理解
            output = self._format_output(result, symbol)
            return output
        except Exception as e:
            return f"获取资金流向数据失败: {str(e)}"
    
    def _format_output(self, data: dict, symbol: Optional[str] = None) -> str:
        """格式化输出"""
        lines = []
        lines.append("=" * 60)
        lines.append("📊 资金流向数据汇总")
        lines.append("=" * 60)
        
        # 1. 北向资金实时
        if data.get('north_bound_realtime'):
            realtime = data['north_bound_realtime']
            if realtime:
                latest = realtime[0]
                lines.append(f"\n🌏 北向资金实时（{latest.get('日期')} {latest.get('时间')}）:")
                lines.append(f"  - 北向资金: {latest.get('北向资金')}万元")
                lines.append(f"  - 沪股通: {latest.get('沪股通')}万元")
                lines.append(f"  - 深股通: {latest.get('深股通')}万元")
        
        # 2. 北向资金历史趋势
        if data.get('north_bound_history'):
            history = data['north_bound_history'][:5]
            lines.append(f"\n📈 北向资金历史趋势（最近5日）:")
            for item in history:
                lines.append(f"  - {item.get('日期')}: 净买额{item.get('当日成交净买额')}亿元")
        
        # 3. 北向资金TOP10
        if data.get('north_bound_top10'):
            top10 = data['north_bound_top10'][:10]
            lines.append(f"\n🏆 北向资金持股TOP10:")
            for i, item in enumerate(top10, 1):
                lines.append(f"  {i}. {item.get('名称')}({item.get('代码')}): 持股市值{item.get('今日持股-市值')}万元")
        
        # 4. 行业资金流TOP5
        if data.get('industry_flow'):
            industries = sorted(data['industry_flow'], key=lambda x: float(x.get('净额', 0)), reverse=True)[:5]
            lines.append(f"\n🏭 行业资金流TOP5:")
            for item in industries:
                lines.append(f"  - {item.get('行业')}: 净额{item.get('净额')}亿, 涨跌幅{item.get('行业-涨跌幅')}")
        
        # 5. 概念资金流TOP5
        if data.get('concept_flow'):
            concepts = sorted(data['concept_flow'], key=lambda x: float(x.get('净额', 0)), reverse=True)[:5]
            lines.append(f"\n💡 概念资金流TOP5:")
            for item in concepts:
                lines.append(f"  - {item.get('行业')}: 净额{item.get('净额')}亿, 涨跌幅{item.get('行业-涨跌幅')}")
        
        # 6. 个股资金流TOP10
        if data.get('individual_flow_top'):
            stocks = sorted(data['individual_flow_top'], 
                          key=lambda x: float(str(x.get('净额', '0')).replace('亿', '').replace('万', '').replace(',', '') or 0), 
                          reverse=True)[:10]
            lines.append(f"\n📊 个股资金流TOP10:")
            for i, item in enumerate(stocks, 1):
                lines.append(f"  {i}. {item.get('股票简称')}({item.get('股票代码')}): 净额{item.get('净额')}, 涨跌幅{item.get('涨跌幅')}")
        
        # 7. 融资融券
        if data.get('margin_summary'):
            margin = data['margin_summary'][:3]
            lines.append(f"\n💰 融资融券（最近3日）:")
            for item in margin:
                lines.append(f"  - {item.get('信用交易日期')}: 融资余额{item.get('融资余额')}")
        
        # 8. 个股详情
        if symbol and data.get('stock_detail'):
            detail = data['stock_detail']
            if detail.get('fund_flow'):
                flow = detail['fund_flow']
                lines.append(f"\n🎯 {symbol} 资金流向:")
                lines.append(f"  - 股票名称: {flow.get('股票简称')}")
                lines.append(f"  - 最新价: {flow.get('最新价')}")
                lines.append(f"  - 涨跌幅: {flow.get('涨跌幅')}")
                lines.append(f"  - 流入资金: {flow.get('流入资金')}")
                lines.append(f"  - 流出资金: {flow.get('流出资金')}")
                lines.append(f"  - 净额: {flow.get('净额')}")
        
        lines.append("\n" + "=" * 60)
        return "\n".join(lines)


# 创建全局实例
fund_flow_tool = FundFlowTool()


def get_fund_flow_tool():
    """获取资金流向工具实例"""
    return fund_flow_tool
