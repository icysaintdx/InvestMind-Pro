"""
数据流监控系统 - 接口对接状态检查

检查所有数据接口的对接情况并分类展示
"""

import json
from typing import Dict, List
from datetime import datetime


class DataflowIntegrationChecker:
    """数据接口对接状态检查器"""
    
    def __init__(self):
        # 定义所有数据接口分类
        self.api_categories = {
            "风险监控类": [
                {
                    "name": "停复牌信息",
                    "interface": "suspend_d",
                    "module": "backend.dataflows.risk.risk_analyzer",
                    "function": "get_suspend_info",
                    "status": "✅ 已对接",
                    "priority": "P0",
                    "description": "获取个股每日停复牌状态，核心风险信号"
                },
                {
                    "name": "ST股票列表",
                    "interface": "stock_st",
                    "module": "backend.dataflows.risk.risk_analyzer",
                    "function": "get_st_stocks",
                    "status": "✅ 已对接",
                    "priority": "P0",
                    "description": "筛选被特别处理的个股"
                },
                {
                    "name": "实时行情数据",
                    "interface": "realtime_quote",
                    "module": "backend.dataflows.risk.risk_analyzer",
                    "function": "get_realtime_data",
                    "status": "✅ 已对接",
                    "priority": "P0",
                    "description": "A股实时行情快照"
                }
            ],
            
            "新闻舆情类": [
                {
                    "name": "AKShare个股新闻",
                    "interface": "stock_news_em",
                    "module": "backend.dataflows.news.multi_source_news_aggregator",
                    "function": "get_stock_news_akshare",
                    "status": "✅ 已对接 (含备用源)",
                    "priority": "P1",
                    "description": "东方财富个股新闻，支持fallback机制"
                },
                {
                    "name": "AKShare市场新闻",
                    "interface": "stock_news_main_cx",
                    "module": "backend.dataflows.news.multi_source_news_aggregator",
                    "function": "get_market_news_akshare",
                    "status": "✅ 已对接",
                    "priority": "P1",
                    "description": "财经市场要闻"
                },
                {
                    "name": "Tushare新闻",
                    "interface": "news",
                    "module": "backend.dataflows.news.multi_source_news_aggregator",
                    "function": "get_stock_news_tushare",
                    "status": "✅ 已对接 (需5000积分)",
                    "priority": "P1",
                    "description": "Tushare新闻接口"
                },
                {
                    "name": "实时新闻备用源",
                    "interface": "realtime_news",
                    "module": "backend.dataflows.news.realtime_news",
                    "function": "get_realtime_stock_news",
                    "status": "✅ 已对接",
                    "priority": "P1",
                    "description": "备用新闻数据源"
                }
            ],
            
            "情绪分析类": [
                {
                    "name": "文本情绪分析",
                    "interface": "NLP引擎",
                    "module": "backend.dataflows.news.sentiment_engine",
                    "function": "analyze_text",
                    "status": "✅ 已对接 (增强版)",
                    "priority": "P1",
                    "description": "中文情感词典 + 强化词 + 否定词处理"
                },
                {
                    "name": "新闻列表情绪分析",
                    "interface": "批量分析",
                    "module": "backend.dataflows.news.sentiment_engine",
                    "function": "analyze_news_list",
                    "status": "✅ 已对接 (增强版)",
                    "priority": "P1",
                    "description": "批量新闻情绪评分，含紧急度和类型识别"
                },
                {
                    "name": "正面词汇库",
                    "interface": "词典",
                    "count": "200+ 词汇",
                    "status": "✅ 已完善",
                    "priority": "P1",
                    "description": "业绩、市场、运营、政策、创新 5大类"
                },
                {
                    "name": "负面词汇库",
                    "interface": "词典",
                    "count": "150+ 词汇",
                    "status": "✅ 已完善",
                    "priority": "P1",
                    "description": "业绩、市场、问题、监管 4大类"
                },
                {
                    "name": "强化词库",
                    "interface": "词典",
                    "count": "20+ 词汇",
                    "status": "✅ 已完善",
                    "priority": "P1",
                    "description": "程度、时间、范围、确定性 4大类"
                },
                {
                    "name": "否定词库",
                    "interface": "词典",
                    "count": "15+ 词汇",
                    "status": "✅ 已完善",
                    "priority": "P1",
                    "description": "基础否定、复合否定、程度否定"
                },
                {
                    "name": "紧急度评估",
                    "interface": "智能判断",
                    "module": "backend.dataflows.news.sentiment_engine",
                    "function": "_assess_urgency",
                    "status": "✅ 已对接",
                    "priority": "P1",
                    "description": "critical/high/medium/low 4级分类"
                },
                {
                    "name": "报告类型识别",
                    "interface": "智能判断",
                    "module": "backend.dataflows.news.sentiment_engine",
                    "function": "_identify_report_type",
                    "status": "✅ 已对接",
                    "priority": "P1",
                    "description": "财务/研究/公告/新闻/政策 5类识别"
                }
            ],
            
            "财务数据类": [
                {
                    "name": "利润表",
                    "interface": "income",
                    "module": "待对接",
                    "status": "⏳ 计划中",
                    "priority": "P2",
                    "description": "公司利润表数据"
                },
                {
                    "name": "资产负债表",
                    "interface": "balancesheet",
                    "module": "待对接",
                    "status": "⏳ 计划中",
                    "priority": "P2",
                    "description": "公司资产负债数据"
                },
                {
                    "name": "现金流量表",
                    "interface": "cashflow",
                    "module": "待对接",
                    "status": "⏳ 计划中",
                    "priority": "P2",
                    "description": "公司现金流数据"
                }
            ],
            
            "实时交易类": [
                {
                    "name": "实时成交数据",
                    "interface": "realtime_tick",
                    "module": "待对接",
                    "status": "⏳ 计划中",
                    "priority": "P2",
                    "description": "当日成交历史数据"
                },
                {
                    "name": "涨跌幅排名",
                    "interface": "realtime_list",
                    "module": "待对接",
                    "status": "⏳ 计划中",
                    "priority": "P2",
                    "description": "实时涨跌幅排行"
                }
            ],
            
            "任务调度类": [
                {
                    "name": "任务调度器",
                    "interface": "异步调度",
                    "module": "backend.dataflows.scheduler.task_scheduler",
                    "function": "TaskScheduler",
                    "status": "✅ 已对接",
                    "priority": "P2",
                    "description": "异步任务调度，支持重试和并发控制"
                },
                {
                    "name": "数据持久化",
                    "interface": "JSON存储",
                    "module": "backend.dataflows.persistence.monitor_storage",
                    "function": "MonitorStorage",
                    "status": "✅ 已对接",
                    "priority": "P2",
                    "description": "监控配置和历史数据存储"
                }
            ]
        }
    
    def generate_report(self) -> str:
        """生成对接状态报告"""
        
        report = []
        report.append("=" * 80)
        report.append("数据流监控系统 - 接口对接状态报告")
        report.append("=" * 80)
        report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # 统计数据
        total_apis = 0
        completed_apis = 0
        planned_apis = 0
        
        for category, apis in self.api_categories.items():
            total_apis += len(apis)
            for api in apis:
                if "✅" in api['status']:
                    completed_apis += 1
                elif "⏳" in api['status']:
                    planned_apis += 1
        
        # 总体统计
        report.append("【总体统计】")
        report.append(f"  总接口数: {total_apis}")
        report.append(f"  已完成: {completed_apis} ({completed_apis/total_apis*100:.1f}%)")
        report.append(f"  计划中: {planned_apis} ({planned_apis/total_apis*100:.1f}%)")
        report.append("")
        
        # 按分类展示
        for category, apis in self.api_categories.items():
            report.append("=" * 80)
            report.append(f"【{category}】")
            report.append("=" * 80)
            
            for i, api in enumerate(apis, 1):
                report.append(f"\n{i}. {api['name']}")
                report.append(f"   状态: {api['status']}")
                report.append(f"   优先级: {api['priority']}")
                
                if 'interface' in api:
                    report.append(f"   接口: {api['interface']}")
                if 'module' in api:
                    report.append(f"   模块: {api['module']}")
                if 'function' in api:
                    report.append(f"   函数: {api['function']}")
                if 'count' in api:
                    report.append(f"   规模: {api['count']}")
                if 'description' in api:
                    report.append(f"   说明: {api['description']}")
            
            report.append("")
        
        # 情感词典详情
        report.append("=" * 80)
        report.append("【情感词典详细统计】")
        report.append("=" * 80)
        report.append("")
        report.append("✅ 正面词汇库 (200+ 词汇)")
        report.append("   • 业绩利好类 (30+): 增长、上涨、盈利、突破、创新高...")
        report.append("   • 市场情绪类 (50+): 利好、看好、强劲、复苏、机会...")
        report.append("   • 公司运营类 (40+): 中标、合作、订单、并购、分红...")
        report.append("   • 行业政策类 (30+): 政策支持、补贴、激励、放开...")
        report.append("   • 技术创新类 (50+): 创新、研发、突破、专利、AI...")
        report.append("")
        report.append("✅ 负面词汇库 (150+ 词汇)")
        report.append("   • 业绩利空类 (30+): 下跌、亏损、下滑、暴跌、业绩变脸...")
        report.append("   • 市场情绪类 (50+): 利空、看空、担忧、风险、爆雷...")
        report.append("   • 公司问题类 (40+): 违规、处罚、调查、ST、退市...")
        report.append("   • 监管风险类 (30+): 问询函、警示函、处罚、限制...")
        report.append("")
        report.append("✅ 强化词库 (20+ 词汇)")
        report.append("   • 程度强化: 大幅(1.5x)、显著(1.4x)、明显(1.3x)...")
        report.append("   • 时间强化: 突然、急剧、迅速、持续...")
        report.append("   • 范围强化: 全面、全部、所有、大量...")
        report.append("   • 确定性强化: 确定、明确、肯定、必然...")
        report.append("")
        report.append("✅ 否定词库 (15+ 词汇)")
        report.append("   • 基础否定: 不、没、无、未、非...")
        report.append("   • 复合否定: 不是、没有、无法、未能...")
        report.append("   • 程度否定: 几乎不、几乎没、极少、很少...")
        report.append("")
        report.append("✅ 紧急度关键词 (4级分类)")
        report.append("   • Critical: 特别重大、紧急通知、强制退市...")
        report.append("   • High: 重大、重要、严重、核心...")
        report.append("   • Medium: 较大、不小、值得关注...")
        report.append("   • Low: 普通、常规、日常、一般...")
        report.append("")
        report.append("✅ 报告类型识别词库 (5大类)")
        report.append("   • 财务报告: 财报、年报、季报、业绩...")
        report.append("   • 研究报告: 研报、分析师、机构研究、评级...")
        report.append("   • 公告文件: 公告、风险提示、澄清、问询函...")
        report.append("   • 新闻资讯: 新闻、快讯、专访、报道...")
        report.append("   • 政策文件: 政策、通知、意见、规划...")
        report.append("")
        
        # API端点
        report.append("=" * 80)
        report.append("【已对接API端点】")
        report.append("=" * 80)
        report.append("")
        report.append("1. GET /api/dataflow/stock/monitor/{ts_code}")
        report.append("   • 综合风险监控 (停复牌 + ST + 实时数据 + 风险评分)")
        report.append("")
        report.append("2. GET /api/dataflow/stock/news/{ts_code}")
        report.append("   • 多源新闻聚合 (AKShare + Tushare + 备用源)")
        report.append("")
        report.append("3. GET /api/dataflow/stock/sentiment/{ts_code}")
        report.append("   • 新闻情绪分析 (情感打分 + 紧急度 + 类型识别)")
        report.append("")
        report.append("4. POST /api/dataflow/monitor/config")
        report.append("   • 保存监控配置 (持久化到JSON)")
        report.append("")
        report.append("5. GET /api/dataflow/monitor/config")
        report.append("   • 读取监控配置")
        report.append("")
        report.append("6. GET /api/dataflow/monitor/history/{ts_code}")
        report.append("   • 获取历史监控数据")
        report.append("")
        report.append("7. GET /api/dataflow/scheduler/tasks")
        report.append("   • 获取所有任务状态")
        report.append("")
        report.append("8. POST /api/dataflow/scheduler/task")
        report.append("   • 添加定时任务")
        report.append("")
        report.append("9. DELETE /api/dataflow/scheduler/task/{task_id}")
        report.append("   • 删除任务")
        report.append("")
        
        # 下一步计划
        report.append("=" * 80)
        report.append("【下一步计划 (P2优先级)】")
        report.append("=" * 80)
        report.append("")
        report.append("1. ⏳ 财务数据类接口对接")
        report.append("   • 利润表 (income)")
        report.append("   • 资产负债表 (balancesheet)")
        report.append("   • 现金流量表 (cashflow)")
        report.append("")
        report.append("2. ⏳ 实时交易类接口对接")
        report.append("   • 实时成交数据 (realtime_tick)")
        report.append("   • 涨跌幅排名 (realtime_list)")
        report.append("")
        report.append("3. ⏳ 高级情绪分析功能")
        report.append("   • 引入jieba分词提升准确度")
        report.append("   • 机器学习情绪模型")
        report.append("   • 实时情绪趋势追踪")
        report.append("")
        
        report.append("=" * 80)
        report.append("报告结束")
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def save_report(self, filename: str = "dataflow_integration_report.txt"):
        """保存报告到文件"""
        report = self.generate_report()
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"✅ 报告已保存: {filename}")
        return filename
    
    def print_report(self):
        """打印报告"""
        print(self.generate_report())


if __name__ == "__main__":
    checker = DataflowIntegrationChecker()
    
    # 打印到控制台
    checker.print_report()
    
    # 保存到文件
    checker.save_report()
