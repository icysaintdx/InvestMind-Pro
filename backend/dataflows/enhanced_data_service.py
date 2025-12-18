"""
增强版综合数据服务
整合所有57个接口：Tushare 40个 + AKShare 17个
包含情绪分析、风险评估、紧急程度分类
"""

import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pandas as pd

from backend.utils.logging_config import get_logger

logger = get_logger("dataflows.enhanced_service")


# ==================== 分类常量 ====================

class RiskLevel:
    """风险等级"""
    CRITICAL = "critical"  # 严重风险
    HIGH = "high"          # 高风险
    MEDIUM = "medium"      # 中等风险
    LOW = "low"            # 低风险
    NONE = "none"          # 无风险


class SentimentLevel:
    """情绪等级"""
    VERY_POSITIVE = "very_positive"  # 非常正面
    POSITIVE = "positive"            # 正面
    NEUTRAL = "neutral"              # 中性
    NEGATIVE = "negative"            # 负面
    VERY_NEGATIVE = "very_negative"  # 非常负面


class UrgencyLevel:
    """紧急程度"""
    IMMEDIATE = "immediate"  # 立即处理
    HIGH = "high"            # 高优先级
    MEDIUM = "medium"        # 中等优先级
    LOW = "low"              # 低优先级
    INFO = "info"            # 仅供参考


class DataCategory:
    """数据分类"""
    NEWS = "news"                    # 新闻舆情
    RISK = "risk"                    # 风险预警
    POSITIVE = "positive"            # 利好信号
    FUNDAMENTAL = "fundamental"      # 基本面数据
    MARKET = "market"                # 市场数据
    CAPITAL_FLOW = "capital_flow"    # 资金流向


# ==================== 接口状态追踪 ====================

INTERFACE_STATUS = {
    # Tushare接口 (40个)
    "tushare": {
        "realtime_quote": {"status": "integrated", "method": "_get_realtime_quote"},
        "realtime_tick": {"status": "partial", "method": "_get_realtime_tick", "note": "使用stk_mins替代"},
        "realtime_list": {"status": "missing", "method": None},
        "suspend_d": {"status": "integrated", "method": "_get_suspend_info"},
        "stock_st": {"status": "integrated", "method": "_check_st_status", "note": "使用AKShare"},
        "income": {"status": "integrated", "method": "_get_financial_data"},
        "balancesheet": {"status": "integrated", "method": "_get_financial_data"},
        "cashflow": {"status": "integrated", "method": "_get_financial_data"},
        "fina_audit": {"status": "integrated", "method": "_get_audit_opinion"},
        "forecast": {"status": "integrated", "method": "_get_performance_forecast"},
        "express": {"status": "integrated", "method": "_get_performance_forecast"},
        "dividend": {"status": "integrated", "method": "_get_dividend_data"},
        "share_float": {"status": "integrated", "method": "_get_restricted_release"},
        "pledge_stat": {"status": "integrated", "method": "_get_pledge_data"},
        "pledge_detail": {"status": "missing", "method": None},
        "stk_holdertrade": {"status": "integrated", "method": "_get_holder_trade"},
        "top_list": {"status": "integrated", "method": "_get_dragon_tiger"},
        "top_inst": {"status": "integrated", "method": "_get_top_inst"},
        "limit_list_d": {"status": "integrated", "method": "_get_limit_list"},
        "limit_list_ths": {"status": "missing", "method": None},
        "margin": {"status": "integrated", "method": "_get_margin_data"},
        "margin_detail": {"status": "missing", "method": None},
        "stock_company": {"status": "integrated", "method": "_get_company_info"},
        "stk_managers": {"status": "integrated", "method": "_get_managers"},
        "stk_rewards": {"status": "integrated", "method": "_get_manager_rewards"},
        "fina_mainbz": {"status": "integrated", "method": "_get_main_business"},
        "hsgt_top10": {"status": "integrated", "method": "_get_hsgt_holding"},
        "ggt_top10": {"status": "missing", "method": None},
        "hk_hold": {"status": "missing", "method": None},
        "moneyflow_hsgt": {"status": "missing", "method": None},
    },
    # AKShare接口 (17个)
    "akshare": {
        "stock_announcement": {"status": "integrated", "method": "_get_announcements_akshare"},
        "stock_news_em": {"status": "integrated", "method": "_get_news_em"},
        "stock_news_sina": {"status": "partial", "method": "_get_news_sina", "note": "使用替代接口"},
        "stock_market_news_cninfo": {"status": "integrated", "method": "_get_market_news_cninfo"},
        "stock_st_info": {"status": "integrated", "method": "_get_stock_st_info_ak"},
        "stock_suspension_info": {"status": "integrated", "method": "_get_suspension_info_ak"},
        "stock_equity_pledge_detail": {"status": "integrated", "method": "_get_pledge_detail_ak"},
        "stock_restricted_shares": {"status": "integrated", "method": "_get_restricted_shares_ak"},
        "stock_shareholder_change": {"status": "partial", "method": "_get_shareholder_change_ak", "note": "使用股东户数"},
        "stock_dragon_tiger_list": {"status": "integrated", "method": "_get_dragon_tiger_ak"},
        "stock_zh_a_st_em": {"status": "integrated", "method": "_check_st_status"},
        "stock_performance_forecast": {"status": "integrated", "method": "_get_performance_forecast_ak"},
        "stock_audit_opinion": {"status": "integrated", "method": "_get_audit_opinion_ak"},
        "stock_margin_trading": {"status": "integrated", "method": "_get_margin_trading_ak"},
        "stock_block_trade": {"status": "integrated", "method": "_get_block_trade"},
        "stock_industry_policy": {"status": "stub", "method": "_get_industry_policy"},
        "stock_yjyg_em": {"status": "integrated", "method": "_get_performance_forecast_ak"},
    }
}


class EnhancedDataService:
    """增强版综合数据服务"""

    def __init__(self):
        self.tushare_token = os.getenv('TUSHARE_TOKEN', '')
        self.tushare_api = None

        # 初始化Tushare
        if self.tushare_token:
            try:
                import tushare as ts
                ts.set_token(self.tushare_token)
                self.tushare_api = ts.pro_api()
                logger.info("✅ Tushare API初始化成功")
            except Exception as e:
                logger.error(f"❌ Tushare初始化失败: {e}")

    # ==================== 新增缺失接口 ====================

    def _get_realtime_list(self, src: str = 'dc') -> Dict:
        """获取实时涨跌幅排名 (Tushare realtime_list)"""
        try:
            import tushare as ts
            df = ts.realtime_list(src=src)

            if df is None or df.empty:
                return {'status': 'no_data', 'message': '无实时排名数据'}

            records = df.head(50).to_dict('records')
            return {
                'status': 'success',
                'count': len(records),
                'data': records,
                'source': src
            }
        except Exception as e:
            logger.warning(f"⚠️ 实时排名获取失败: {e}")
            return {'status': 'error', 'message': str(e)}

    def _get_pledge_detail_tushare(self, ts_code: str) -> Dict:
        """获取股权质押明细 (Tushare pledge_detail)"""
        if not self.tushare_api:
            return {'status': 'api_unavailable'}

        try:
            df = self.tushare_api.pledge_detail(ts_code=ts_code)

            if df is None or df.empty:
                return {'status': 'no_data', 'message': '无质押明细'}

            records = df.head(20).to_dict('records')
            return {
                'status': 'success',
                'count': len(records),
                'data': records
            }
        except Exception as e:
            logger.warning(f"⚠️ 质押明细获取失败: {e}")
            return {'status': 'error', 'message': str(e)}

    def _get_margin_detail(self, ts_code: str) -> Dict:
        """获取融资融券明细 (Tushare margin_detail)"""
        if not self.tushare_api:
            return {'status': 'api_unavailable'}

        try:
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')

            df = self.tushare_api.margin_detail(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date
            )

            if df is None or df.empty:
                return {'status': 'no_data', 'message': '无融资融券明细'}

            records = df.head(20).to_dict('records')
            return {
                'status': 'success',
                'count': len(records),
                'data': records
            }
        except Exception as e:
            logger.warning(f"⚠️ 融资融券明细获取失败: {e}")
            return {'status': 'error', 'message': str(e)}

    def _get_ggt_top10(self, trade_date: str = None) -> Dict:
        """获取港股通十大成交股 (Tushare ggt_top10)"""
        if not self.tushare_api:
            return {'status': 'api_unavailable'}

        try:
            if not trade_date:
                trade_date = datetime.now().strftime('%Y%m%d')

            df = self.tushare_api.ggt_top10(trade_date=trade_date)

            if df is None or df.empty:
                return {'status': 'no_data', 'message': '无港股通数据'}

            records = df.to_dict('records')
            return {
                'status': 'success',
                'count': len(records),
                'data': records,
                'trade_date': trade_date
            }
        except Exception as e:
            logger.warning(f"⚠️ 港股通十大成交获取失败: {e}")
            return {'status': 'error', 'message': str(e)}

    def _get_hk_hold(self, ts_code: str = None, trade_date: str = None) -> Dict:
        """获取沪深港通持股明细 (Tushare hk_hold)"""
        if not self.tushare_api:
            return {'status': 'api_unavailable'}

        try:
            if not trade_date:
                trade_date = datetime.now().strftime('%Y%m%d')

            df = self.tushare_api.hk_hold(
                ts_code=ts_code,
                trade_date=trade_date
            )

            if df is None or df.empty:
                return {'status': 'no_data', 'message': '无港股通持股数据'}

            records = df.head(50).to_dict('records')
            return {
                'status': 'success',
                'count': len(records),
                'data': records
            }
        except Exception as e:
            logger.warning(f"⚠️ 港股通持股获取失败: {e}")
            return {'status': 'error', 'message': str(e)}

    def _get_moneyflow_hsgt(self, start_date: str = None, end_date: str = None) -> Dict:
        """获取沪深港通资金流向 (Tushare moneyflow_hsgt)"""
        if not self.tushare_api:
            return {'status': 'api_unavailable'}

        try:
            if not end_date:
                end_date = datetime.now().strftime('%Y%m%d')
            if not start_date:
                start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')

            df = self.tushare_api.moneyflow_hsgt(
                start_date=start_date,
                end_date=end_date
            )

            if df is None or df.empty:
                return {'status': 'no_data', 'message': '无资金流向数据'}

            records = df.to_dict('records')
            return {
                'status': 'success',
                'count': len(records),
                'data': records,
                'latest': records[0] if records else None
            }
        except Exception as e:
            logger.warning(f"⚠️ 资金流向获取失败: {e}")
            return {'status': 'error', 'message': str(e)}

    def _get_news_em(self, symbol: str) -> Dict:
        """获取东方财富个股新闻 (AKShare stock_news_em)"""
        try:
            import akshare as ak

            if '.' in symbol:
                symbol = symbol.split('.')[0]

            df = ak.stock_news_em(symbol=symbol)

            if df is None or df.empty:
                return {'status': 'no_data', 'message': '无新闻数据'}

            records = []
            for _, row in df.head(30).iterrows():
                records.append({
                    'title': str(row.get('新闻标题', '')),
                    'content': str(row.get('新闻内容', ''))[:500],
                    'pub_time': str(row.get('发布时间', '')),
                    'source': '东方财富',
                    'url': str(row.get('新闻链接', ''))
                })

            return {
                'status': 'success',
                'count': len(records),
                'data': records
            }
        except Exception as e:
            logger.warning(f"⚠️ 东方财富新闻获取失败: {e}")
            return {'status': 'error', 'message': str(e)}

    def _get_industry_policy_real(self) -> Dict:
        """获取行业政策动态 (AKShare)"""
        try:
            import akshare as ak

            # 尝试获取财经新闻作为政策信息来源
            df = ak.news_cctv()

            if df is None or df.empty:
                return {'status': 'no_data', 'message': '无政策新闻'}

            records = []
            for _, row in df.head(20).iterrows():
                records.append({
                    'title': str(row.get('title', '')),
                    'content': str(row.get('content', ''))[:300],
                    'pub_time': str(row.get('date', '')),
                    'source': 'CCTV财经'
                })

            return {
                'status': 'success',
                'count': len(records),
                'data': records
            }
        except Exception as e:
            logger.warning(f"⚠️ 行业政策获取失败: {e}")
            return {'status': 'no_data', 'message': str(e)}

    # ==================== 分类与评级系统 ====================

    def classify_data(self, data: Dict, ts_code: str) -> Dict:
        """
        对获取的数据进行分类和评级

        Returns:
            {
                'news_items': [...],      # 新闻舆情
                'risk_items': [...],      # 风险预警
                'positive_items': [...],  # 利好信号
                'overall_sentiment': str,
                'overall_risk': str,
                'urgency': str,
                'summary': str
            }
        """
        news_items = []
        risk_items = []
        positive_items = []

        # 1. 分析ST状态
        st_status = data.get('st_status', {})
        if st_status.get('is_st'):
            risk_items.append({
                'type': 'ST风险',
                'level': RiskLevel.CRITICAL,
                'urgency': UrgencyLevel.IMMEDIATE,
                'message': f"股票为{st_status.get('name', 'ST')}股票",
                'category': DataCategory.RISK
            })

        # 2. 分析停复牌
        suspend = data.get('suspend', {})
        if suspend.get('status') == 'has_suspend':
            risk_items.append({
                'type': '停复牌风险',
                'level': RiskLevel.HIGH,
                'urgency': UrgencyLevel.HIGH,
                'message': suspend.get('message', '近期有停复牌记录'),
                'category': DataCategory.RISK
            })

        # 3. 分析股权质押
        pledge = data.get('pledge', {})
        if pledge.get('status') == 'success':
            pledge_ratio = pledge.get('pledge_ratio', 0)
            if pledge_ratio > 50:
                risk_items.append({
                    'type': '高质押风险',
                    'level': RiskLevel.CRITICAL,
                    'urgency': UrgencyLevel.IMMEDIATE,
                    'message': f"质押比例{pledge_ratio}%，存在平仓风险",
                    'category': DataCategory.RISK
                })
            elif pledge_ratio > 30:
                risk_items.append({
                    'type': '质押风险',
                    'level': RiskLevel.MEDIUM,
                    'urgency': UrgencyLevel.MEDIUM,
                    'message': f"质押比例{pledge_ratio}%",
                    'category': DataCategory.RISK
                })

        # 4. 分析限售解禁
        restricted = data.get('restricted', {})
        if restricted.get('status') == 'success' and restricted.get('count', 0) > 0:
            risk_items.append({
                'type': '解禁风险',
                'level': RiskLevel.MEDIUM,
                'urgency': UrgencyLevel.MEDIUM,
                'message': f"近期有{restricted['count']}笔限售股解禁",
                'category': DataCategory.RISK
            })

        # 5. 分析股东增减持
        holder_trade = data.get('holder_trade', {})
        if holder_trade.get('status') == 'success':
            records = holder_trade.get('records', [])
            increase_count = sum(1 for r in records if r.get('type') == 'IN')
            decrease_count = sum(1 for r in records if r.get('type') == 'DE')

            if decrease_count > increase_count:
                risk_items.append({
                    'type': '股东减持',
                    'level': RiskLevel.MEDIUM,
                    'urgency': UrgencyLevel.MEDIUM,
                    'message': f"近期减持{decrease_count}次，增持{increase_count}次",
                    'category': DataCategory.RISK
                })
            elif increase_count > decrease_count:
                positive_items.append({
                    'type': '股东增持',
                    'level': 'positive',
                    'urgency': UrgencyLevel.INFO,
                    'message': f"近期增持{increase_count}次",
                    'category': DataCategory.POSITIVE
                })

        # 6. 分析业绩预告
        forecast = data.get('forecast', {})
        if forecast.get('status') == 'success':
            forecasts = forecast.get('forecast', [])
            for f in forecasts[:3]:
                f_type = f.get('type', '')
                if f_type in ['预增', '扭亏']:
                    positive_items.append({
                        'type': '业绩预增',
                        'level': 'positive',
                        'urgency': UrgencyLevel.INFO,
                        'message': f"业绩{f_type}，预计变动{f.get('profit_min', 0)}%~{f.get('profit_max', 0)}%",
                        'category': DataCategory.POSITIVE
                    })
                elif f_type in ['预减', '首亏', '续亏']:
                    risk_items.append({
                        'type': '业绩风险',
                        'level': RiskLevel.HIGH,
                        'urgency': UrgencyLevel.HIGH,
                        'message': f"业绩{f_type}",
                        'category': DataCategory.RISK
                    })

        # 7. 分析审计意见
        audit = data.get('audit', {})
        if audit.get('status') == 'success':
            opinion = audit.get('opinion', '')
            if '保留' in opinion or '无法表示' in opinion or '否定' in opinion:
                risk_items.append({
                    'type': '审计风险',
                    'level': RiskLevel.CRITICAL,
                    'urgency': UrgencyLevel.IMMEDIATE,
                    'message': f"审计意见：{opinion}",
                    'category': DataCategory.RISK
                })

        # 8. 分析龙虎榜
        dragon_tiger = data.get('dragon_tiger', {})
        if dragon_tiger.get('status') == 'success':
            records = dragon_tiger.get('records', [])
            if records:
                total_net = sum(r.get('net', 0) for r in records)
                if total_net > 0:
                    positive_items.append({
                        'type': '龙虎榜净买入',
                        'level': 'positive',
                        'urgency': UrgencyLevel.INFO,
                        'message': f"近期龙虎榜净买入{total_net/10000:.2f}万",
                        'category': DataCategory.CAPITAL_FLOW
                    })
                else:
                    risk_items.append({
                        'type': '龙虎榜净卖出',
                        'level': RiskLevel.LOW,
                        'urgency': UrgencyLevel.LOW,
                        'message': f"近期龙虎榜净卖出{abs(total_net)/10000:.2f}万",
                        'category': DataCategory.CAPITAL_FLOW
                    })

        # 9. 分析分红
        dividend = data.get('dividend', {})
        if dividend.get('status') == 'success' and dividend.get('count', 0) > 0:
            positive_items.append({
                'type': '分红记录',
                'level': 'positive',
                'urgency': UrgencyLevel.INFO,
                'message': f"有{dividend['count']}次分红记录",
                'category': DataCategory.POSITIVE
            })

        # 10. 处理新闻
        news = data.get('news', [])
        for n in news[:10]:
            news_items.append({
                'title': n.get('title', ''),
                'content': n.get('content', '')[:200],
                'pub_time': n.get('pub_time', ''),
                'source': n.get('source', ''),
                'category': DataCategory.NEWS
            })

        # 计算综合评级
        overall_risk = self._calculate_overall_risk(risk_items)
        overall_sentiment = self._calculate_overall_sentiment(risk_items, positive_items)
        urgency = self._calculate_urgency(risk_items)

        return {
            'ts_code': ts_code,
            'news_items': news_items,
            'risk_items': risk_items,
            'positive_items': positive_items,
            'overall_risk': overall_risk,
            'overall_sentiment': overall_sentiment,
            'urgency': urgency,
            'risk_count': len(risk_items),
            'positive_count': len(positive_items),
            'news_count': len(news_items),
            'summary': self._generate_summary(ts_code, risk_items, positive_items, overall_risk),
            'timestamp': datetime.now().isoformat()
        }

    def _calculate_overall_risk(self, risk_items: List[Dict]) -> str:
        """计算综合风险等级"""
        if not risk_items:
            return RiskLevel.NONE

        critical_count = sum(1 for r in risk_items if r.get('level') == RiskLevel.CRITICAL)
        high_count = sum(1 for r in risk_items if r.get('level') == RiskLevel.HIGH)

        if critical_count > 0:
            return RiskLevel.CRITICAL
        elif high_count >= 2:
            return RiskLevel.HIGH
        elif high_count == 1 or len(risk_items) >= 3:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

    def _calculate_overall_sentiment(self, risk_items: List, positive_items: List) -> str:
        """计算综合情绪"""
        risk_score = len(risk_items) * -10
        positive_score = len(positive_items) * 10

        # 严重风险额外扣分
        for r in risk_items:
            if r.get('level') == RiskLevel.CRITICAL:
                risk_score -= 20
            elif r.get('level') == RiskLevel.HIGH:
                risk_score -= 10

        total_score = 50 + risk_score + positive_score

        if total_score >= 70:
            return SentimentLevel.VERY_POSITIVE
        elif total_score >= 55:
            return SentimentLevel.POSITIVE
        elif total_score >= 45:
            return SentimentLevel.NEUTRAL
        elif total_score >= 30:
            return SentimentLevel.NEGATIVE
        else:
            return SentimentLevel.VERY_NEGATIVE

    def _calculate_urgency(self, risk_items: List[Dict]) -> str:
        """计算紧急程度"""
        if not risk_items:
            return UrgencyLevel.INFO

        for r in risk_items:
            if r.get('urgency') == UrgencyLevel.IMMEDIATE:
                return UrgencyLevel.IMMEDIATE

        high_count = sum(1 for r in risk_items if r.get('urgency') == UrgencyLevel.HIGH)
        if high_count > 0:
            return UrgencyLevel.HIGH

        medium_count = sum(1 for r in risk_items if r.get('urgency') == UrgencyLevel.MEDIUM)
        if medium_count > 0:
            return UrgencyLevel.MEDIUM

        return UrgencyLevel.LOW

    def _generate_summary(self, ts_code: str, risk_items: List, positive_items: List, overall_risk: str) -> str:
        """生成摘要"""
        summary_parts = [f"{ts_code} 数据分析摘要："]

        if overall_risk == RiskLevel.CRITICAL:
            summary_parts.append("⚠️ 存在严重风险，需立即关注！")
        elif overall_risk == RiskLevel.HIGH:
            summary_parts.append("⚠️ 存在较高风险，建议谨慎。")
        elif overall_risk == RiskLevel.MEDIUM:
            summary_parts.append("存在一定风险，需持续关注。")
        else:
            summary_parts.append("风险较低。")

        if risk_items:
            risk_types = list(set(r.get('type', '') for r in risk_items))
            summary_parts.append(f"风险点：{', '.join(risk_types[:3])}")

        if positive_items:
            positive_types = list(set(p.get('type', '') for p in positive_items))
            summary_parts.append(f"利好：{', '.join(positive_types[:3])}")

        return ' '.join(summary_parts)

    def get_interface_status(self) -> Dict:
        """获取所有接口的集成状态"""
        total = 0
        integrated = 0
        partial = 0
        missing = 0

        for source, interfaces in INTERFACE_STATUS.items():
            for name, info in interfaces.items():
                total += 1
                status = info.get('status', 'missing')
                if status == 'integrated':
                    integrated += 1
                elif status == 'partial':
                    partial += 1
                else:
                    missing += 1

        return {
            'total': total,
            'integrated': integrated,
            'partial': partial,
            'missing': missing,
            'coverage': f"{(integrated + partial) / total * 100:.1f}%",
            'details': INTERFACE_STATUS
        }


# 全局实例
_enhanced_service = None


def get_enhanced_service() -> EnhancedDataService:
    """获取增强数据服务实例"""
    global _enhanced_service
    if _enhanced_service is None:
        _enhanced_service = EnhancedDataService()
    return _enhanced_service
