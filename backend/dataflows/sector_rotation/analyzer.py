"""
板块轮动分析器
提供板块轮动、热度、多空分析功能
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import json

from backend.utils.logging_config import get_logger
from .data_fetcher import sector_rotation_fetcher

logger = get_logger("dataflows.sector_rotation.analyzer")


class SectorRotationAnalyzer:
    """板块轮动分析器"""

    def __init__(self):
        self.data_fetcher = sector_rotation_fetcher
        logger.info("[板块轮动分析] 分析器初始化完成")

    def analyze_sector_ranking(self, sector_type: str = "industry", top_n: int = 20) -> Dict[str, Any]:
        """
        分析板块涨跌排名

        Args:
            sector_type: "industry" 或 "concept"
            top_n: 返回前N个

        Returns:
            板块排名分析结果
        """
        try:
            if sector_type == "industry":
                result = self.data_fetcher.get_industry_sectors()
            else:
                result = self.data_fetcher.get_concept_sectors()

            if not result.get("success"):
                return {"success": False, "message": result.get("message", "获取数据失败")}

            sectors = result.get("data", [])

            # 按涨跌幅排序
            sorted_by_change = sorted(sectors, key=lambda x: x.get("change_pct", 0), reverse=True)

            # 涨幅榜
            top_gainers = sorted_by_change[:top_n]
            # 跌幅榜
            top_losers = sorted_by_change[-top_n:][::-1]

            # 按换手率排序
            sorted_by_turnover = sorted(sectors, key=lambda x: x.get("turnover", 0), reverse=True)
            top_active = sorted_by_turnover[:top_n]

            return {
                "success": True,
                "sector_type": sector_type,
                "top_gainers": top_gainers,
                "top_losers": top_losers,
                "top_active": top_active,
                "total_count": len(sectors),
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

        except Exception as e:
            logger.error(f"[板块轮动分析] 排名分析失败: {e}")
            return {"success": False, "message": str(e)}

    def analyze_fund_flow_ranking(self, top_n: int = 20) -> Dict[str, Any]:
        """
        分析资金流向排名

        Args:
            top_n: 返回前N个

        Returns:
            资金流向排名分析结果
        """
        try:
            result = self.data_fetcher.get_sector_fund_flow()

            if not result.get("success"):
                return {"success": False, "message": result.get("message", "获取数据失败")}

            fund_flow = result.get("data", [])

            # 按主力净流入排序
            sorted_by_main = sorted(fund_flow, key=lambda x: x.get("main_net_inflow", 0), reverse=True)

            # 主力流入榜
            top_inflow = sorted_by_main[:top_n]
            # 主力流出榜
            top_outflow = sorted_by_main[-top_n:][::-1]

            # 按超大单净流入排序
            sorted_by_super = sorted(fund_flow, key=lambda x: x.get("super_large_net_inflow", 0), reverse=True)
            top_super_inflow = sorted_by_super[:top_n]

            return {
                "success": True,
                "top_inflow": top_inflow,
                "top_outflow": top_outflow,
                "top_super_inflow": top_super_inflow,
                "total_count": len(fund_flow),
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

        except Exception as e:
            logger.error(f"[板块轮动分析] 资金流向分析失败: {e}")
            return {"success": False, "message": str(e)}

    def analyze_sector_heat(self, top_n: int = 20) -> Dict[str, Any]:
        """
        分析板块热度

        综合考虑涨跌幅、换手率、资金流入计算热度

        Args:
            top_n: 返回前N个

        Returns:
            板块热度分析结果
        """
        try:
            # 获取行业板块数据
            industry_result = self.data_fetcher.get_industry_sectors()
            # 获取资金流向数据
            fund_flow_result = self.data_fetcher.get_sector_fund_flow()

            if not industry_result.get("success"):
                return {"success": False, "message": "获取板块数据失败"}

            sectors = industry_result.get("data", [])
            fund_flow_data = fund_flow_result.get("data", []) if fund_flow_result.get("success") else []

            # 创建资金流向映射
            fund_flow_map = {item.get("sector"): item for item in fund_flow_data}

            # 计算热度分数
            heat_scores = []
            for sector in sectors:
                name = sector.get("name", "")
                change_pct = sector.get("change_pct", 0)
                turnover = sector.get("turnover", 0)
                up_count = sector.get("up_count", 0)
                down_count = sector.get("down_count", 0)

                # 获取资金流向
                fund_info = fund_flow_map.get(name, {})
                main_net_inflow = fund_info.get("main_net_inflow", 0)
                main_net_inflow_pct = fund_info.get("main_net_inflow_pct", 0)

                # 计算热度分数 (0-100)
                # 涨跌幅贡献 (权重30%)
                change_score = min(max((change_pct + 10) / 20 * 100, 0), 100) * 0.3

                # 换手率贡献 (权重20%)
                turnover_score = min(turnover / 10 * 100, 100) * 0.2

                # 资金流入贡献 (权重30%)
                fund_score = min(max((main_net_inflow_pct + 5) / 10 * 100, 0), 100) * 0.3

                # 涨跌家数比贡献 (权重20%)
                total_stocks = up_count + down_count
                if total_stocks > 0:
                    up_ratio = up_count / total_stocks * 100
                else:
                    up_ratio = 50
                ratio_score = up_ratio * 0.2

                heat_score = change_score + turnover_score + fund_score + ratio_score

                # 判断热度趋势
                if main_net_inflow > 0 and change_pct > 0:
                    trend = "升温"
                elif main_net_inflow < 0 and change_pct < 0:
                    trend = "降温"
                else:
                    trend = "稳定"

                # 判断持续性
                if abs(change_pct) > 3 and abs(main_net_inflow_pct) > 2:
                    sustainability = "强"
                elif abs(change_pct) > 1 or abs(main_net_inflow_pct) > 1:
                    sustainability = "中"
                else:
                    sustainability = "弱"

                heat_scores.append({
                    "sector": name,
                    "heat_score": round(heat_score, 2),
                    "change_pct": change_pct,
                    "turnover": turnover,
                    "main_net_inflow": main_net_inflow,
                    "main_net_inflow_pct": main_net_inflow_pct,
                    "up_count": up_count,
                    "down_count": down_count,
                    "trend": trend,
                    "sustainability": sustainability
                })

            # 按热度排序
            sorted_by_heat = sorted(heat_scores, key=lambda x: x.get("heat_score", 0), reverse=True)

            # 最热板块
            hottest = sorted_by_heat[:top_n]

            # 升温板块 (热度高且趋势为升温)
            heating = [s for s in sorted_by_heat if s.get("trend") == "升温"][:top_n]

            # 降温板块 (趋势为降温)
            cooling = [s for s in sorted_by_heat if s.get("trend") == "降温"][:top_n]

            return {
                "success": True,
                "hottest": hottest,
                "heating": heating,
                "cooling": cooling,
                "total_count": len(heat_scores),
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

        except Exception as e:
            logger.error(f"[板块轮动分析] 热度分析失败: {e}")
            return {"success": False, "message": str(e)}

    def analyze_rotation_signal(self) -> Dict[str, Any]:
        """
        分析板块轮动信号

        识别当前强势板块、潜力板块、衰退板块

        Returns:
            轮动信号分析结果
        """
        try:
            # 获取综合数据
            comprehensive = self.data_fetcher.get_comprehensive_data()

            if not comprehensive.get("success"):
                return {"success": False, "message": "获取数据失败"}

            industry_data = comprehensive.get("industry_sectors", {}).get("data", [])
            fund_flow_data = comprehensive.get("fund_flow", {}).get("data", [])
            market_data = comprehensive.get("market_overview", {}).get("data", {})

            # 创建资金流向映射
            fund_flow_map = {item.get("sector"): item for item in fund_flow_data}

            # 分析每个板块的轮动阶段
            rotation_analysis = []
            for sector in industry_data:
                name = sector.get("name", "")
                change_pct = sector.get("change_pct", 0)
                turnover = sector.get("turnover", 0)
                up_count = sector.get("up_count", 0)
                down_count = sector.get("down_count", 0)

                fund_info = fund_flow_map.get(name, {})
                main_net_inflow = fund_info.get("main_net_inflow", 0)
                main_net_inflow_pct = fund_info.get("main_net_inflow_pct", 0)

                # 判断轮动阶段
                # 强势: 涨幅>2%, 资金净流入, 换手率高
                # 潜力: 资金净流入但涨幅不大, 或涨幅开始启动
                # 衰退: 涨幅下跌, 资金流出

                if change_pct > 2 and main_net_inflow > 0 and turnover > 3:
                    stage = "强势"
                    stage_score = 90
                elif change_pct > 1 and main_net_inflow > 0:
                    stage = "强势"
                    stage_score = 80
                elif main_net_inflow > 0 and change_pct > 0:
                    stage = "潜力"
                    stage_score = 70
                elif main_net_inflow > 0 and change_pct <= 0:
                    stage = "潜力"
                    stage_score = 60
                elif change_pct < -1 and main_net_inflow < 0:
                    stage = "衰退"
                    stage_score = 30
                elif change_pct < 0 or main_net_inflow < 0:
                    stage = "衰退"
                    stage_score = 40
                else:
                    stage = "观望"
                    stage_score = 50

                rotation_analysis.append({
                    "sector": name,
                    "stage": stage,
                    "stage_score": stage_score,
                    "change_pct": change_pct,
                    "turnover": turnover,
                    "main_net_inflow": main_net_inflow,
                    "main_net_inflow_pct": main_net_inflow_pct,
                    "up_count": up_count,
                    "down_count": down_count
                })

            # 分类
            current_strong = [s for s in rotation_analysis if s.get("stage") == "强势"]
            current_strong = sorted(current_strong, key=lambda x: x.get("stage_score", 0), reverse=True)[:10]

            potential = [s for s in rotation_analysis if s.get("stage") == "潜力"]
            potential = sorted(potential, key=lambda x: x.get("main_net_inflow", 0), reverse=True)[:10]

            declining = [s for s in rotation_analysis if s.get("stage") == "衰退"]
            declining = sorted(declining, key=lambda x: x.get("change_pct", 0))[:10]

            # 市场整体情况
            market_summary = {
                "total_stocks": market_data.get("total_stocks", 0),
                "up_count": market_data.get("up_count", 0),
                "down_count": market_data.get("down_count", 0),
                "up_ratio": market_data.get("up_ratio", 0),
                "limit_up": market_data.get("limit_up", 0),
                "limit_down": market_data.get("limit_down", 0)
            }

            return {
                "success": True,
                "current_strong": current_strong,
                "potential": potential,
                "declining": declining,
                "market_summary": market_summary,
                "total_sectors": len(rotation_analysis),
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

        except Exception as e:
            logger.error(f"[板块轮动分析] 轮动信号分析失败: {e}")
            return {"success": False, "message": str(e)}

    def get_sector_detail(self, sector_name: str, sector_type: str = "industry") -> Dict[str, Any]:
        """
        获取板块详细信息

        Args:
            sector_name: 板块名称
            sector_type: 板块类型

        Returns:
            板块详细信息
        """
        try:
            # 获取成分股
            stocks_result = self.data_fetcher.get_sector_stocks(sector_name, sector_type)

            # 获取历史行情
            history_result = self.data_fetcher.get_sector_history(sector_name, sector_type)

            # 获取当前板块数据
            if sector_type == "industry":
                sectors_result = self.data_fetcher.get_industry_sectors()
            else:
                sectors_result = self.data_fetcher.get_concept_sectors()

            sector_info = None
            if sectors_result.get("success"):
                for s in sectors_result.get("data", []):
                    if s.get("name") == sector_name:
                        sector_info = s
                        break

            return {
                "success": True,
                "sector_name": sector_name,
                "sector_type": sector_type,
                "sector_info": sector_info,
                "stocks": stocks_result.get("data", []) if stocks_result.get("success") else [],
                "stocks_count": stocks_result.get("count", 0) if stocks_result.get("success") else 0,
                "history": history_result.get("data", [])[-30:] if history_result.get("success") else [],  # 最近30天
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

        except Exception as e:
            logger.error(f"[板块轮动分析] 获取板块详情失败: {e}")
            return {"success": False, "message": str(e)}

    def get_comprehensive_analysis(self) -> Dict[str, Any]:
        """
        获取综合分析报告

        Returns:
            综合分析结果
        """
        try:
            # 获取各项分析
            ranking = self.analyze_sector_ranking("industry", 10)
            fund_flow = self.analyze_fund_flow_ranking(10)
            heat = self.analyze_sector_heat(10)
            rotation = self.analyze_rotation_signal()

            # 获取市场概况
            market = self.data_fetcher.get_market_overview()
            north_flow = self.data_fetcher.get_north_money_flow()

            return {
                "success": True,
                "ranking": ranking if ranking.get("success") else None,
                "fund_flow": fund_flow if fund_flow.get("success") else None,
                "heat": heat if heat.get("success") else None,
                "rotation": rotation if rotation.get("success") else None,
                "market_overview": market.get("data") if market.get("success") else None,
                "north_flow": north_flow.get("data") if north_flow.get("success") else None,
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

        except Exception as e:
            logger.error(f"[板块轮动分析] 综合分析失败: {e}")
            return {"success": False, "message": str(e)}


# 单例实例
sector_rotation_analyzer = SectorRotationAnalyzer()
