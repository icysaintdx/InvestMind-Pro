"""
综合股票数据获取服务
整合所有数据接口：财务、风险、新闻、股权等
"""

import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd

from backend.utils.logging_config import get_logger

logger = get_logger("dataflows.comprehensive")


class ComprehensiveStockDataService:
    """综合股票数据服务 - 整合所有接口"""
    
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
    
    def get_all_stock_data(self, ts_code: str) -> Dict:
        """
        获取股票的所有数据
        
        Returns:
            {
                'basic_info': {},  # 基础信息
                'realtime': {},  # 实时行情
                'realtime_tick': {},  # 实时成交
                'suspend': {},  # 停复牌
                'st_status': {},  # ST状态
                'financial': {},  # 财务数据
                'audit': {},  # 审计意见
                'forecast': {},  # 业绩预告
                'dividend': {},  # 分红送股
                'restricted': {},  # 限售解禁
                'pledge': {},  # 股权质押
                'holder_trade': {},  # 股东增减持
                'dragon_tiger': {},  # 龙虎榜
                'top_inst': {},  # 龙虎榜机构明细
                'block_trade': {},  # 大宗交易
                'limit_list': {},  # 涨跌停数据
                'margin': {},  # 融资融券
                'company_info': {},  # 公司基本信息
                'managers': {},  # 管理层
                'manager_rewards': {},  # 管理层薪酬
                'main_business': {},  # 主营业务
                'hsgt_holding': {},  # 沪深港通持股
                'announcements': {},  # 公告  
                'news_sina': {},  # 新浪新闻
                'market_news': {},  # 市场快讯
                'cninfo_news': {},  # 巨潮资讯
                'industry_policy': {},  # 行业政策
                'akshare_ext': {},  # AKShare扩展数据
                'news': {},  # 多源新闻聚合

            }
        """
        logger.info(f"📊 开始获取 {ts_code} 的全面数据...")
        
        result = {
            'ts_code': ts_code,
            'timestamp': datetime.now().isoformat(),
            'data_summary': {},
            'basic_info': {},
            'realtime': {},
            'realtime_tick': {},
            'realtime_list': {},  # 新增：全市场实时行情
            'suspend': {},
            'st_status': {},
            'financial': {},
            'audit': {},
            'forecast': {},
            'dividend': {},
            'restricted': {},
            'pledge': {},
            'pledge_detail': {},  # 新增：质押明细
            'holder_trade': {},
            'dragon_tiger': {},
            'top_inst': {},
            'block_trade': {},
            'limit_list': {},
            'limit_list_ths': {},  # 新增：同花顺涨跌停
            'margin': {},
            'margin_detail': {},  # 新增：融资融券明细
            'company_info': {},
            'managers': {},
            'manager_rewards': {},
            'main_business': {},
            'hsgt_holding': {},
            'ggt_top10': {},  # 新增：港股通十大成交
            'hk_hold': {},  # 新增：沪深港通持股明细
            'moneyflow_hsgt': {},  # 新增：沪深港通资金流向
            'announcements': {},
            'news_sina': {},
            'news_em': {},  # 新增：东方财富个股新闻
            'market_news': {},
            'industry_policy': {},
            'news': {},  # 多源新闻聚合
        }
        
        # 1. 实时行情
        result['realtime'] = self._get_realtime_quote(ts_code)
        
        # 2. 实时成交数据
        result['realtime_tick'] = self._get_realtime_tick(ts_code)
        
        # 3. 停复牌信息
        result['suspend'] = self._get_suspend_info(ts_code)
        
        # 4. ST状态检查
        result['st_status'] = self._check_st_status(ts_code)
        
        # 5. 财务数据（最新3期）
        result['financial'] = self._get_financial_data(ts_code)
        
        # 6. 财务审计意见
        result['audit'] = self._get_audit_opinion(ts_code)
        
        # 7. 业绩预告/快报
        result['forecast'] = self._get_performance_forecast(ts_code)
        
        # 8. 分红送股
        result['dividend'] = self._get_dividend_data(ts_code)
        
        # 9. 限售股解禁
        result['restricted'] = self._get_restricted_release(ts_code)
        
        # 10. 股权质押
        result['pledge'] = self._get_pledge_data(ts_code)
        
        # 11. 股东增减持
        result['holder_trade'] = self._get_holder_trade(ts_code)
        
        # 12. 龙虎榜
        result['dragon_tiger'] = self._get_dragon_tiger(ts_code)
        
        # 12.5 龙虎榜机构明细
        result['top_inst'] = self._get_top_inst(ts_code)
        
        # 12.6 大宗交易
        result['block_trade'] = self._get_block_trade(ts_code)
        
        # 13. 涨跌停数据
        result['limit_list'] = self._get_limit_list(ts_code)
        
        # 14. 融资融券
        result['margin'] = self._get_margin_data(ts_code)
        
        # 15. 公司基本信息
        result['company_info'] = self._get_company_info(ts_code)
        
        # 16. 管理层信息
        result['managers'] = self._get_managers(ts_code)
        
        # 17. 管理层薪酬
        result['manager_rewards'] = self._get_manager_rewards(ts_code)
        
        # 18. 主营业务构成
        result['main_business'] = self._get_main_business(ts_code)
        
        # 19. 沪深港通持股
        result['hsgt_holding'] = self._get_hsgt_holding(ts_code)
        
        # 20. 上市公司公告（优先使用AKShare）
        announcements_ak = self._get_announcements_akshare(ts_code)
        if announcements_ak.get('status') == 'success':
            result['announcements'] = announcements_ak
        else:
            result['announcements'] = self._get_announcements(ts_code)
        
        # 20.5 新浪财经新闻
        result['news_sina'] = self._get_news_sina(ts_code)
        
        # 20.6 市场快讯（百度财经）
        result['market_news'] = self._get_market_news_cninfo()
        
        # 20.7 巨潮资讯公告
        result['cninfo_news'] = self._get_cninfo_news()
        
        # 20.8 行业政策
        result['industry_policy'] = self._get_industry_policy()
        
        # 21. AKShare扩展数据
        result['akshare_ext'] = {
            'st_info': self._get_stock_st_info_ak(ts_code),
            'suspension_info': self._get_suspension_info_ak(ts_code),
            'pledge_detail_ak': self._get_pledge_detail_ak(ts_code),
            'restricted_ak': self._get_restricted_shares_ak(ts_code),
            'shareholder_change_ak': self._get_shareholder_change_ak(ts_code),
            'dragon_tiger_ak': self._get_dragon_tiger_ak(ts_code),
            'performance_forecast_ak': self._get_performance_forecast_ak(ts_code),
            'audit_opinion_ak': self._get_audit_opinion_ak(ts_code),
            'margin_trading_ak': self._get_margin_trading_ak(ts_code)
        }

        # 22. 新增Tushare接口
        result['realtime_list'] = self._get_realtime_list()
        result['pledge_detail'] = self._get_pledge_detail(ts_code)
        result['margin_detail'] = self._get_margin_detail(ts_code)
        result['ggt_top10'] = self._get_ggt_top10(ts_code)
        result['hk_hold'] = self._get_hk_hold(ts_code)
        result['moneyflow_hsgt'] = self._get_moneyflow_hsgt()
        result['limit_list_ths'] = self._get_limit_list_ths(ts_code)

        # 23. 新增AKShare接口
        result['news_em'] = self._get_stock_news_em(ts_code)

        # 24. 新闻数据（从多源新闻聚合器获取）
        result['news'] = self._get_news_data(ts_code)
        
        # 生成数据摘要
        result['data_summary'] = self._generate_summary(result)
        
        logger.info(f"✅ 数据获取完成，共 {len(result['data_summary'])} 个类别")
        
        return result
    
    def _get_realtime_quote(self, ts_code: str) -> Dict:
        """获取实时行情（优先使用AKShare，备选Tushare）"""
        # 优先使用AKShare获取实时行情
        try:
            import akshare as ak
            symbol = ts_code.split('.')[0]

            # 使用东方财富实时行情
            df = ak.stock_zh_a_spot_em()
            if df is not None and not df.empty:
                stock_data = df[df['代码'] == symbol]
                if not stock_data.empty:
                    row = stock_data.iloc[0]
                    return {
                        'status': 'success',
                        'source': 'akshare',
                        'data': {
                            'name': str(row.get('名称', '')),
                            'price': float(row.get('最新价', 0) or 0),
                            'change': float(row.get('涨跌额', 0) or 0),
                            'change_pct': float(row.get('涨跌幅', 0) or 0),
                            'volume': int(row.get('成交量', 0) or 0),
                            'amount': float(row.get('成交额', 0) or 0),
                            'high': float(row.get('最高', 0) or 0),
                            'low': float(row.get('最低', 0) or 0),
                            'open': float(row.get('今开', 0) or 0),
                            'pre_close': float(row.get('昨收', 0) or 0),
                            'date': datetime.now().strftime('%Y-%m-%d'),
                            'time': datetime.now().strftime('%H:%M:%S')
                        }
                    }
        except Exception as e:
            logger.debug(f"AKShare实时行情获取失败: {e}")

        # 备选：使用Tushare
        try:
            import tushare as ts
            df = ts.realtime_quote(ts_code=ts_code)

            if df is None or df.empty:
                return {'status': 'no_data', 'message': '无实时行情数据'}

            data = df.iloc[0].to_dict()
            return {
                'status': 'success',
                'source': 'tushare',
                'data': {
                    'name': data.get('NAME', ''),
                    'price': float(data.get('PRICE', 0) or 0),
                    'change': float(data.get('PRICE', 0) or 0) - float(data.get('PRE_CLOSE', 0) or 0),
                    'change_pct': ((float(data.get('PRICE', 0) or 0) - float(data.get('PRE_CLOSE', 0) or 0)) / float(data.get('PRE_CLOSE', 1) or 1) * 100) if data.get('PRE_CLOSE') else 0,
                    'volume': int(data.get('VOLUME', 0) or 0),
                    'amount': float(data.get('AMOUNT', 0) or 0),
                    'high': float(data.get('HIGH', 0) or 0),
                    'low': float(data.get('LOW', 0) or 0),
                    'open': float(data.get('OPEN', 0) or 0),
                    'pre_close': float(data.get('PRE_CLOSE', 0) or 0),
                    'date': data.get('DATE', ''),
                    'time': data.get('TIME', '')
                }
            }
        except Exception as e:
            logger.warning(f"⚠️ 实时行情获取失败: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _get_suspend_info(self, ts_code: str) -> Dict:
        """获取停复牌信息"""
        if not self.tushare_api:
            return {'status': 'api_unavailable'}
        
        try:
            # 获取最近30天的停复牌记录
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
            
            df = self.tushare_api.suspend_d(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date
            )
            
            if df is None or df.empty:
                return {
                    'status': 'normal',
                    'message': '近期无停复牌记录',
                    'records': []
                }
            
            records = []
            for _, row in df.iterrows():
                records.append({
                    'suspend_date': row.get('suspend_date', ''),
                    'resume_date': row.get('resume_date', ''),
                    'suspend_reason': row.get('suspend_reason', ''),
                    'suspend_type': row.get('suspend_type', '')
                })
            
            return {
                'status': 'has_suspend',
                'message': f'近期有{len(records)}条停复牌记录',
                'count': len(records),
                'records': records
            }
            
        except Exception as e:
            logger.warning(f"⚠️ 停复牌信息获取失败: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _check_st_status(self, ts_code: str) -> Dict:
        """检查ST状态"""
        try:
            import akshare as ak
            
            # 使用AKShare的ST风险警示板接口
            df = ak.stock_zh_a_st_em()
            
            if df is None or df.empty:
                return {'status': 'normal', 'is_st': False, 'message': '非ST股票'}
            
            # 检查是否在ST列表中
            stock_code = ts_code.split('.')[0]
            is_st = stock_code in df['代码'].values
            
            if is_st:
                st_info = df[df['代码'] == stock_code].iloc[0]
                return {
                    'status': 'st_stock',
                    'is_st': True,
                    'name': st_info.get('名称', ''),
                    'message': f'{stock_code} 为ST股票'
                }
            else:
                return {
                    'status': 'normal',
                    'is_st': False,
                    'message': '非ST股票'
                }
                
        except Exception as e:
            logger.warning(f"⚠️ ST状态检查失败: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _get_financial_data(self, ts_code: str) -> Dict:
        """获取财务数据（利润表、资产负债表、现金流量表）"""
        if not self.tushare_api:
            return {'status': 'api_unavailable'}
        
        try:
            result = {
                'status': 'success',
                'income': [],  # 利润表
                'balance': [],  # 资产负债表
                'cashflow': []  # 现金流量表
            }
            
            # 1. 利润表（最近3期）
            try:
                income_df = self.tushare_api.income(ts_code=ts_code, fields=[
                    'ts_code', 'end_date', 'total_revenue', 'revenue', 'operate_profit',
                    'total_profit', 'n_income', 'n_income_attr_p'
                ])
                
                if income_df is not None and not income_df.empty:
                    for _, row in income_df.head(3).iterrows():
                        result['income'].append({
                            'period': row.get('end_date', ''),
                            'total_revenue': float(row.get('total_revenue', 0) or 0),
                            'operate_profit': float(row.get('operate_profit', 0) or 0),
                            'net_profit': float(row.get('n_income_attr_p', 0) or 0)
                        })
            except Exception as e:
                logger.debug(f"利润表获取失败: {e}")
            
            # 2. 资产负债表（最近3期）
            try:
                balance_df = self.tushare_api.balancesheet(ts_code=ts_code, fields=[
                    'ts_code', 'end_date', 'total_assets', 'total_liab', 'total_hldr_eqy_exc_min_int'
                ])
                
                if balance_df is not None and not balance_df.empty:
                    for _, row in balance_df.head(3).iterrows():
                        result['balance'].append({
                            'period': row.get('end_date', ''),
                            'total_assets': float(row.get('total_assets', 0) or 0),
                            'total_liab': float(row.get('total_liab', 0) or 0),
                            'equity': float(row.get('total_hldr_eqy_exc_min_int', 0) or 0)
                        })
            except Exception as e:
                logger.debug(f"资产负债表获取失败: {e}")
            
            # 3. 现金流量表（最近3期）
            try:
                cashflow_df = self.tushare_api.cashflow(ts_code=ts_code, fields=[
                    'ts_code', 'end_date', 'n_cashflow_act', 'n_cashflow_inv_act', 'n_cash_flows_fnc_act'
                ])
                
                if cashflow_df is not None and not cashflow_df.empty:
                    for _, row in cashflow_df.head(3).iterrows():
                        result['cashflow'].append({
                            'period': row.get('end_date', ''),
                            'operating_cash': float(row.get('n_cashflow_act', 0) or 0),
                            'investing_cash': float(row.get('n_cashflow_inv_act', 0) or 0),
                            'financing_cash': float(row.get('n_cash_flows_fnc_act', 0) or 0)
                        })
            except Exception as e:
                logger.debug(f"现金流量表获取失败: {e}")
            
            return result
            
        except Exception as e:
            logger.warning(f"⚠️ 财务数据获取失败: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _get_audit_opinion(self, ts_code: str) -> Dict:
        """获取财务审计意见"""
        if not self.tushare_api:
            return {'status': 'api_unavailable'}
        
        try:
            df = self.tushare_api.fina_audit(ts_code=ts_code)
            
            if df is None or df.empty:
                return {'status': 'no_data', 'message': '无审计意见数据'}
            
            latest = df.iloc[0]
            return {
                'status': 'success',
                'period': latest.get('end_date', ''),
                'opinion': latest.get('audit_result', ''),
                'agency': latest.get('audit_agency', ''),
                'is_standard': latest.get('audit_result', '') == '标准无保留意见'
            }
            
        except Exception as e:
            logger.warning(f"⚠️ 审计意见获取失败: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _get_performance_forecast(self, ts_code: str) -> Dict:
        """获取业绩预告/快报"""
        if not self.tushare_api:
            return {'status': 'api_unavailable'}
        
        try:
            # 获取业绩预告
            forecast_df = self.tushare_api.forecast(ts_code=ts_code)
            
            # 获取业绩快报
            express_df = self.tushare_api.express(ts_code=ts_code)
            
            result = {
                'status': 'success',
                'forecast': [],
                'express': []
            }
            
            if forecast_df is not None and not forecast_df.empty:
                for _, row in forecast_df.head(3).iterrows():
                    result['forecast'].append({
                        'period': row.get('end_date', ''),
                        'type': row.get('type', ''),
                        'profit_min': float(row.get('p_change_min', 0) or 0),
                        'profit_max': float(row.get('p_change_max', 0) or 0),
                        'summary': row.get('summary', '')
                    })
            
            if express_df is not None and not express_df.empty:
                for _, row in express_df.head(3).iterrows():
                    result['express'].append({
                        'period': row.get('end_date', ''),
                        'revenue': float(row.get('revenue', 0) or 0),
                        'profit': float(row.get('operate_profit', 0) or 0),
                        'eps': float(row.get('eps', 0) or 0)
                    })
            
            return result
            
        except Exception as e:
            logger.warning(f"⚠️ 业绩预告获取失败: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _get_dividend_data(self, ts_code: str) -> Dict:
        """获取分红送股数据"""
        if not self.tushare_api:
            return {'status': 'api_unavailable'}
        
        try:
            df = self.tushare_api.dividend(ts_code=ts_code)
            
            if df is None or df.empty:
                return {'status': 'no_data', 'message': '无分红数据'}
            
            records = []
            for _, row in df.head(5).iterrows():
                records.append({
                    'year': row.get('end_date', ''),
                    'cash_div': float(row.get('cash_div', 0) or 0),
                    'bonus_share': float(row.get('stk_bo_rate', 0) or 0),
                    'record_date': row.get('record_date', ''),
                    'ex_date': row.get('ex_date', '')
                })
            
            return {
                'status': 'success',
                'count': len(records),
                'records': records
            }
            
        except Exception as e:
            logger.warning(f"⚠️ 分红数据获取失败: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _get_restricted_release(self, ts_code: str) -> Dict:
        """获取限售股解禁数据"""
        if not self.tushare_api:
            return {'status': 'api_unavailable'}
        
        try:
            # 获取未来6个月的解禁数据
            df = self.tushare_api.share_float(ts_code=ts_code)
            
            if df is None or df.empty:
                return {'status': 'no_data', 'message': '无解禁数据'}
            
            records = []
            for _, row in df.head(5).iterrows():
                records.append({
                    'release_date': row.get('float_date', ''),
                    'float_share': float(row.get('float_share', 0) or 0),
                    'float_ratio': float(row.get('float_ratio', 0) or 0),
                    'holder_name': row.get('holder_name', '')
                })
            
            return {
                'status': 'success',
                'count': len(records),
                'records': records
            }
            
        except Exception as e:
            logger.warning(f"⚠️ 解禁数据获取失败: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _get_pledge_data(self, ts_code: str) -> Dict:
        """获取股权质押数据"""
        if not self.tushare_api:
            return {'status': 'api_unavailable'}
        
        try:
            # 获取股权质押统计
            df = self.tushare_api.pledge_stat(ts_code=ts_code)
            
            if df is None or df.empty:
                return {'status': 'no_data', 'message': '无质押数据'}
            
            latest = df.iloc[0]
            return {
                'status': 'success',
                'end_date': latest.get('end_date', ''),
                'pledge_count': int(latest.get('pledge_count', 0) or 0),
                'pledge_ratio': float(latest.get('pledge_ratio', 0) or 0),
                'un_pledge_ratio': float(latest.get('unrest_pledge', 0) or 0)
            }
            
        except Exception as e:
            logger.warning(f"⚠️ 质押数据获取失败: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _get_holder_trade(self, ts_code: str) -> Dict:
        """获取股东增减持数据"""
        if not self.tushare_api:
            return {'status': 'api_unavailable'}
        
        try:
            # 获取最近6个月的增减持
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=180)).strftime('%Y%m%d')
            
            df = self.tushare_api.stk_holdertrade(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date
            )
            
            if df is None or df.empty:
                return {'status': 'no_data', 'message': '无增减持数据'}
            
            records = []
            for _, row in df.head(10).iterrows():
                records.append({
                    'date': row.get('ann_date', ''),
                    'holder': row.get('holder_name', ''),
                    'type': row.get('holder_type', ''),
                    'volume': float(row.get('vol', 0) or 0),
                    'total_share': float(row.get('total_share', 0) or 0)
                })
            
            return {
                'status': 'success',
                'count': len(records),
                'records': records
            }
            
        except Exception as e:
            logger.warning(f"⚠️ 增减持数据获取失败: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _get_dragon_tiger(self, ts_code: str) -> Dict:
        """获取龙虎榜数据"""
        if not self.tushare_api:
            return {'status': 'api_unavailable'}
        
        try:
            # 获取最近30天的龙虎榜，逐天查询
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            all_records = []
            current_date = end_date
            days_checked = 0
            
            # 最多查询30个交易日，或者找到10条记录
            while current_date >= start_date and len(all_records) < 10 and days_checked < 45:
                # 跳过周末
                if current_date.weekday() < 5:  # 0-4为周一到周五
                    try:
                        trade_date_str = current_date.strftime('%Y%m%d')
                        df = self.tushare_api.top_list(
                            trade_date=trade_date_str
                        )
                        
                        if df is not None and not df.empty:
                            # 筛选出当前股票的记录
                            stock_df = df[df['ts_code'] == ts_code]
                            if not stock_df.empty:
                                for _, row in stock_df.iterrows():
                                    all_records.append({
                                        'date': row.get('trade_date', ''),
                                        'reason': row.get('reason', ''),
                                        'buy': float(row.get('buy', 0) or 0),
                                        'sell': float(row.get('sell', 0) or 0),
                                        'net': float(row.get('net', 0) or 0)
                                    })
                    except Exception as day_error:
                        # 单日查询失败，继续下一天
                        pass
                
                current_date -= timedelta(days=1)
                days_checked += 1
            
            if all_records:
                return {
                    'status': 'success',
                    'count': len(all_records),
                    'records': all_records
                }
            else:
                return {'status': 'no_data', 'message': '近30天无龙虎榜数据'}
            
        except Exception as e:
            logger.warning(f"⚠️ 龙虎榜数据获取失败: {e}")
            return {'status': 'no_data', 'message': f'龙虎榜查询失败'}
    
    def _get_top_inst(self, ts_code: str) -> Dict:
        """获取龙虎榜机构明细"""
        try:
            if not self.tushare_api:
                return {'status': 'error', 'message': 'Tushare API未初始化'}
            
            # 获取最近30天的机构明细
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            all_records = []
            current_date = end_date
            days_checked = 0
            
            while current_date >= start_date and len(all_records) < 10 and days_checked < 45:
                if current_date.weekday() < 5:
                    try:
                        trade_date_str = current_date.strftime('%Y%m%d')
                        df = self.tushare_api.top_inst(
                            trade_date=trade_date_str
                        )
                        
                        if df is not None and not df.empty:
                            stock_df = df[df['ts_code'] == ts_code]
                            if not stock_df.empty:
                                for _, row in stock_df.iterrows():
                                    all_records.append({
                                        'trade_date': row.get('trade_date', ''),
                                        'exalter': row.get('exalter', ''),
                                        'buy': float(row.get('buy', 0) or 0),
                                        'buy_rate': float(row.get('buy_rate', 0) or 0),
                                        'sell': float(row.get('sell', 0) or 0),
                                        'sell_rate': float(row.get('sell_rate', 0) or 0),
                                        'net_buy': float(row.get('net_buy', 0) or 0)
                                    })
                    except:
                        pass
                
                current_date -= timedelta(days=1)
                days_checked += 1
            
            if all_records:
                return {
                    'status': 'success',
                    'count': len(all_records),
                    'records': all_records
                }
            else:
                return {'status': 'no_data', 'message': '近30天无机构龙虎榜'}
                
        except Exception as e:
            logger.warning(f"⚠️ 龙虎榜机构明细获取失败: {e}")
            return {'status': 'no_data', 'message': '机构明细查询失败'}
    
    def _get_block_trade(self, ts_code: str) -> Dict:
        """获取大宗交易数据（AKShare）"""
        try:
            import akshare as ak

            # 获取全市场大宗交易数据，然后筛选
            symbol = ts_code.split('.')[0]

            # 使用stock_dzjy_sctj获取大宗交易统计
            try:
                df = ak.stock_dzjy_sctj()
                if df is not None and not df.empty:
                    # 筛选当前股票
                    stock_data = df[df['证券代码'].astype(str) == symbol]
                    if not stock_data.empty:
                        records = stock_data.head(20).to_dict('records')
                        return {
                            'status': 'success',
                            'count': len(records),
                            'data': records,
                            'description': '大宗交易统计'
                        }
            except Exception as e1:
                logger.debug(f"stock_dzjy_sctj失败: {e1}")

            # 备选：获取每日明细
            try:
                df = ak.stock_dzjy_mrtj()
                if df is not None and not df.empty:
                    stock_data = df[df['证券代码'].astype(str) == symbol]
                    if not stock_data.empty:
                        records = stock_data.head(20).to_dict('records')
                        return {
                            'status': 'success',
                            'count': len(records),
                            'data': records,
                            'description': '大宗交易每日统计'
                        }
            except Exception as e2:
                logger.debug(f"stock_dzjy_mrtj失败: {e2}")

            return {
                'status': 'no_data',
                'message': '近期无大宗交易'
            }

        except Exception as e:
            logger.warning(f"⚠️ 大宗交易数据获取失败: {e}")
            return {'status': 'no_data', 'message': '大宗交易查询暂不可用'}
    
    def _get_announcements_akshare(self, ts_code: str) -> Dict:
        """获取上市公司公告（AKShare）"""
        try:
            import akshare as ak

            symbol = ts_code.split('.')[0]

            # 方法1: 使用巨潮资讯公告查询
            try:
                end_date = datetime.now().strftime('%Y-%m-%d')
                start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')

                df = ak.stock_notice_report(symbol=symbol, date=start_date)
                if df is not None and not df.empty:
                    records = []
                    for _, row in df.head(20).iterrows():
                        records.append({
                            'date': str(row.get('公告日期', row.get('日期', ''))),
                            'title': str(row.get('公告标题', row.get('标题', ''))),
                            'type': str(row.get('公告类型', '')),
                            'url': str(row.get('公告链接', row.get('链接', '')))
                        })
                    return {
                        'status': 'success',
                        'count': len(records),
                        'data': records
                    }
            except Exception as e1:
                logger.debug(f"stock_notice_report失败: {e1}")

            # 方法2: 使用东方财富公告
            try:
                df = ak.stock_ggcg_em(symbol=symbol)
                if df is not None and not df.empty:
                    records = []
                    for _, row in df.head(20).iterrows():
                        records.append({
                            'date': str(row.get('公告日期', '')),
                            'title': str(row.get('公告标题', '')),
                            'type': '公告',
                            'url': ''
                        })
                    return {
                        'status': 'success',
                        'count': len(records),
                        'data': records
                    }
            except Exception as e2:
                logger.debug(f"stock_ggcg_em失败: {e2}")

            return {
                'status': 'no_data',
                'message': '近期无公告'
            }

        except Exception as e:
            logger.warning(f"⚠️ 公告数据获取失败: {e}")
            return {'status': 'no_data', 'message': '公告查询暂不可用'}
    
    def _get_news_sina(self, ts_code: str) -> Dict:
        """获取个股新闻（使用东方财富）"""
        try:
            import akshare as ak

            symbol = ts_code.split('.')[0]

            # 方法1: 使用东方财富个股新闻
            try:
                df = ak.stock_news_em(symbol=symbol)
                if df is not None and not df.empty:
                    records = []
                    for _, row in df.head(20).iterrows():
                        records.append({
                            'title': str(row.get('新闻标题', '')),
                            'content': str(row.get('新闻内容', ''))[:200],
                            'time': str(row.get('发布时间', '')),
                            'source': str(row.get('文章来源', '东方财富')),
                            'url': str(row.get('新闻链接', ''))
                        })
                    return {
                        'status': 'success',
                        'count': len(records),
                        'data': records
                    }
            except Exception as e1:
                logger.debug(f"stock_news_em失败: {e1}")

            # 方法2: 使用财联社电报
            try:
                df = ak.stock_telegraph_cls()
                if df is not None and not df.empty:
                    records = []
                    for _, row in df.head(20).iterrows():
                        records.append({
                            'title': str(row.get('标题', '')),
                            'content': str(row.get('内容', ''))[:200],
                            'time': str(row.get('发布时间', '')),
                            'source': '财联社',
                            'url': ''
                        })
                    return {
                        'status': 'success',
                        'count': len(records),
                        'data': records
                    }
            except Exception as e2:
                logger.debug(f"stock_telegraph_cls失败: {e2}")

            return {'status': 'no_data', 'message': '无新闻数据'}

        except Exception as e:
            logger.warning(f"⚠️ 新闻数据获取失败: {e}")
            return {'status': 'no_data', 'message': '新闻暂不可用'}
    
    def _get_market_news_cninfo(self) -> Dict:
        """获取市场快讯（百度财经）"""
        try:
            import akshare as ak
            
            # 百度财经新闻
            df = ak.news_economic_baidu()
            
            if df is not None and not df.empty:
                records = []
                for _, row in df.head(30).iterrows():
                    records.append({
                        'time': str(row.get('发布时间', '')),
                        'title': str(row.get('标题', '')),
                        'content': str(row.get('内容', '')),
                        'source': '百度财经'
                    })
                
                return {
                    'status': 'success',
                    'count': len(records),
                    'data': records
                }
            else:
                return {'status': 'no_data', 'message': '无市场快讯'}
                
        except Exception as e:
            logger.warning(f"⚠️ 市场快讯获取失败: {e}")
            return {'status': 'no_data', 'message': '市场快讯暂不可用'}
    
    def _get_cninfo_news(self) -> Dict:
        """获取巨潮资讯公告快讯（AKShare）"""
        try:
            import akshare as ak

            # 方法1: 使用东方财富公告
            try:
                df = ak.stock_gsgg_em()
                if df is not None and not df.empty:
                    records = []
                    for _, row in df.head(50).iterrows():
                        records.append({
                            'time': str(row.get('公告日期', '')),
                            'code': str(row.get('代码', '')),
                            'name': str(row.get('名称', '')),
                            'title': str(row.get('公告标题', '')),
                            'category': str(row.get('公告类型', '')),
                            'source': '东方财富'
                        })
                    return {
                        'status': 'success',
                        'count': len(records),
                        'data': records
                    }
            except Exception as e1:
                logger.debug(f"stock_gsgg_em失败: {e1}")

            # 方法2: 使用财联社电报作为替代
            try:
                df = ak.stock_telegraph_cls()
                if df is not None and not df.empty:
                    records = []
                    for _, row in df.head(50).iterrows():
                        records.append({
                            'time': str(row.get('发布时间', '')),
                            'code': '',
                            'name': '',
                            'title': str(row.get('标题', '')),
                            'category': '快讯',
                            'source': '财联社'
                        })
                    return {
                        'status': 'success',
                        'count': len(records),
                        'data': records
                    }
            except Exception as e2:
                logger.debug(f"stock_telegraph_cls失败: {e2}")

            return {'status': 'no_data', 'message': '无公告快讯'}

        except Exception as e:
            logger.warning(f"⚠️ 公告快讯获取失败: {e}")
            return {'status': 'no_data', 'message': '公告快讯暂不可用'}
    
    def _get_industry_policy(self) -> Dict:
        """获取行业政策动态（AKShare）- 使用财经新闻作为政策信息源"""
        try:
            import akshare as ak

            all_news = []

            # 1. 尝试获取财联社电报（实时财经新闻，包含政策信息）
            try:
                df_cls = ak.stock_telegraph_cls()
                if df_cls is not None and not df_cls.empty:
                    for _, row in df_cls.head(30).iterrows():
                        title = str(row.get('标题', ''))
                        content = str(row.get('内容', ''))
                        # 筛选政策相关新闻
                        policy_keywords = ['政策', '监管', '央行', '证监会', '发改委', '国务院',
                                         '部委', '法规', '条例', '意见', '通知', '规定']
                        if any(kw in title or kw in content for kw in policy_keywords):
                            all_news.append({
                                'time': str(row.get('发布时间', '')),
                                'title': title,
                                'content': content[:200] if len(content) > 200 else content,
                                'source': '财联社',
                                'type': 'policy'
                            })
            except Exception as e:
                logger.debug(f"财联社电报获取失败: {e}")

            # 2. 尝试获取东方财富财经新闻
            try:
                df_em = ak.stock_news_em(symbol="财经")
                if df_em is not None and not df_em.empty:
                    for _, row in df_em.head(20).iterrows():
                        title = str(row.get('新闻标题', ''))
                        all_news.append({
                            'time': str(row.get('发布时间', '')),
                            'title': title,
                            'content': str(row.get('新闻内容', ''))[:200],
                            'source': '东方财富',
                            'url': str(row.get('新闻链接', '')),
                            'type': 'financial_news'
                        })
            except Exception as e:
                logger.debug(f"东方财富新闻获取失败: {e}")

            if all_news:
                return {
                    'status': 'success',
                    'count': len(all_news),
                    'data': all_news,
                    'description': '财经政策新闻'
                }
            else:
                return {'status': 'no_data', 'message': '暂无政策新闻'}

        except Exception as e:
            logger.warning(f"⚠️ 行业政策获取失败: {e}")
            return {'status': 'no_data', 'message': '行业政策暂不可用'}
    
    def _get_stock_st_info_ak(self, ts_code: str) -> Dict:
        """获取ST股票详细信息（AKShare）"""
        try:
            import akshare as ak
            symbol = ts_code.split('.')[0]
            
            # ST股票统计
            df = ak.stock_zh_a_st_em()
            if df is not None and not df.empty:
                stock_data = df[df['代码'] == symbol]
                if not stock_data.empty:
                    return {
                        'status': 'success',
                        'data': stock_data.iloc[0].to_dict()
                    }
            return {'status': 'no_data', 'message': '非ST股票'}
        except Exception as e:
            logger.warning(f"⚠️ ST信息获取失败: {e}")
            return {'status': 'no_data', 'message': 'ST信息暂不可用'}
    
    def _get_suspension_info_ak(self, ts_code: str) -> Dict:
        """获取停复牌信息（AKShare）"""
        try:
            import akshare as ak
            symbol = ts_code.split('.')[0]
            
            # 停复牌信息
            df = ak.stock_zh_a_stop_em()
            if df is not None and not df.empty:
                stock_data = df[df['代码'] == symbol]
                if not stock_data.empty:
                    return {
                        'status': 'success',
                        'count': len(stock_data),
                        'data': stock_data.to_dict('records')
                    }
            return {'status': 'no_data', 'message': '无停复牌记录'}
        except Exception as e:
            logger.warning(f"⚠️ 停复牌信息获取失败: {e}")
            return {'status': 'no_data', 'message': '停复牌信息暂不可用'}
    
    def _get_pledge_detail_ak(self, ts_code: str) -> Dict:
        """获取股权质押详情（AKShare）"""
        try:
            import akshare as ak
            symbol = ts_code.split('.')[0]

            # 方法1: 使用股权质押市场概况
            try:
                df = ak.stock_gpzy_pledge_ratio_em()
                if df is not None and not df.empty:
                    stock_data = df[df['股票代码'].astype(str) == symbol]
                    if not stock_data.empty:
                        return {
                            'status': 'success',
                            'count': len(stock_data),
                            'data': stock_data.to_dict('records')
                        }
            except Exception as e1:
                logger.debug(f"stock_gpzy_pledge_ratio_em失败: {e1}")

            # 方法2: 使用质押统计
            try:
                df = ak.stock_gpzy_profile_em()
                if df is not None and not df.empty:
                    stock_data = df[df['股票代码'].astype(str) == symbol]
                    if not stock_data.empty:
                        return {
                            'status': 'success',
                            'count': len(stock_data),
                            'data': stock_data.to_dict('records')
                        }
            except Exception as e2:
                logger.debug(f"stock_gpzy_profile_em失败: {e2}")

            return {'status': 'no_data', 'message': '无质押记录'}
        except Exception as e:
            logger.warning(f"⚠️ 质押详情获取失败: {e}")
            return {'status': 'no_data', 'message': '质押详情暂不可用'}
    
    def _get_restricted_shares_ak(self, ts_code: str) -> Dict:
        """获取限售股解禁（AKShare）"""
        try:
            import akshare as ak
            symbol = ts_code.split('.')[0]
            
            # 限售股解禁
            df = ak.stock_restricted_release_queue_sina(symbol=symbol)
            if df is not None and not df.empty:
                return {
                    'status': 'success',
                    'count': len(df),
                    'data': df.to_dict('records')
                }
            return {'status': 'no_data', 'message': '无解禁数据'}
        except Exception as e:
            logger.warning(f"⚠️ 限售股获取失败: {e}")
            return {'status': 'no_data', 'message': '限售股暂不可用'}
    
    def _get_shareholder_change_ak(self, ts_code: str) -> Dict:
        """获取股东增减持（AKShare）- 使用股东人数变化数据"""
        try:
            import akshare as ak
            symbol = ts_code.split('.')[0]

            # 使用stock_zh_a_gdhs获取股东户数变化（这是正确的接口）
            # 股东户数变化可以反映筹码集中度
            df = ak.stock_zh_a_gdhs(symbol=symbol)
            if df is not None and not df.empty:
                records = []
                for _, row in df.head(20).iterrows():
                    records.append({
                        '截止日期': str(row.get('截止日期', '')),
                        '股东户数': int(row.get('股东户数', 0)) if pd.notna(row.get('股东户数')) else 0,
                        '较上期变化': float(row.get('较上期变化', 0)) if pd.notna(row.get('较上期变化')) else 0,
                        '人均流通股': float(row.get('人均流通股', 0)) if pd.notna(row.get('人均流通股')) else 0,
                        '股价': float(row.get('股价', 0)) if pd.notna(row.get('股价')) else 0,
                        '人均持股金额': float(row.get('人均持股金额', 0)) if pd.notna(row.get('人均持股金额')) else 0
                    })
                return {
                    'status': 'success',
                    'count': len(records),
                    'data': records,
                    'description': '股东户数变化（筹码集中度指标）'
                }
            return {'status': 'no_data', 'message': '无股东户数数据'}
        except Exception as e:
            logger.warning(f"⚠️ 股东户数获取失败: {e}")
            return {'status': 'no_data', 'message': '股东户数暂不可用'}
    
    def _get_dragon_tiger_ak(self, ts_code: str) -> Dict:
        """获取龙虎榜（AKShare）"""
        try:
            import akshare as ak
            symbol = ts_code.split('.')[0]

            # 方法1: 获取龙虎榜每日详情（不需要symbol参数）
            try:
                # 获取最近的龙虎榜数据
                end_date = datetime.now().strftime('%Y%m%d')
                start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')

                df = ak.stock_lhb_detail_em(start_date=start_date, end_date=end_date)
                if df is not None and not df.empty:
                    # 筛选当前股票
                    stock_data = df[df['代码'].astype(str) == symbol]
                    if not stock_data.empty:
                        return {
                            'status': 'success',
                            'count': len(stock_data),
                            'data': stock_data.head(10).to_dict('records')
                        }
            except Exception as e1:
                logger.debug(f"stock_lhb_detail_em失败: {e1}")

            # 方法2: 使用龙虎榜营业部统计
            try:
                df = ak.stock_lhb_stock_statistic_em(symbol="近一月")
                if df is not None and not df.empty:
                    stock_data = df[df['代码'].astype(str) == symbol]
                    if not stock_data.empty:
                        return {
                            'status': 'success',
                            'count': len(stock_data),
                            'data': stock_data.to_dict('records')
                        }
            except Exception as e2:
                logger.debug(f"stock_lhb_stock_statistic_em失败: {e2}")

            return {'status': 'no_data', 'message': '无龙虎榜数据'}
        except Exception as e:
            logger.warning(f"⚠️ 龙虎榜获取失败: {e}")
            return {'status': 'no_data', 'message': '龙虎榜暂不可用'}
    
    def _get_performance_forecast_ak(self, ts_code: str) -> Dict:
        """获取业绩预告（AKShare）"""
        try:
            import akshare as ak
            symbol = ts_code.split('.')[0]

            # 方法1: 获取业绩预告汇总
            try:
                # 获取最新一期业绩预告
                df = ak.stock_yjyg_em(date="")  # 空字符串获取最新
                if df is not None and not df.empty:
                    stock_data = df[df['股票代码'].astype(str) == symbol]
                    if not stock_data.empty:
                        return {
                            'status': 'success',
                            'count': len(stock_data),
                            'data': stock_data.to_dict('records')
                        }
            except Exception as e1:
                logger.debug(f"stock_yjyg_em失败: {e1}")

            # 方法2: 使用业绩快报
            try:
                df = ak.stock_yjkb_em(date="")
                if df is not None and not df.empty:
                    stock_data = df[df['股票代码'].astype(str) == symbol]
                    if not stock_data.empty:
                        return {
                            'status': 'success',
                            'count': len(stock_data),
                            'data': stock_data.to_dict('records'),
                            'description': '业绩快报'
                        }
            except Exception as e2:
                logger.debug(f"stock_yjkb_em失败: {e2}")

            return {'status': 'no_data', 'message': '无业绩预告'}
        except Exception as e:
            logger.warning(f"⚠️ 业绩预告获取失败: {e}")
            return {'status': 'no_data', 'message': '业绩预告暂不可用'}
    
    def _get_audit_opinion_ak(self, ts_code: str) -> Dict:
        """获取审计意见（AKShare）"""
        try:
            import akshare as ak
            symbol = ts_code.split('.')[0]

            # 方法1: 使用财务审计意见汇总
            try:
                df = ak.stock_fhps_detail_em()
                if df is not None and not df.empty:
                    stock_data = df[df['代码'].astype(str) == symbol]
                    if not stock_data.empty:
                        return {
                            'status': 'success',
                            'count': len(stock_data),
                            'data': stock_data.to_dict('records')
                        }
            except Exception as e1:
                logger.debug(f"stock_fhps_detail_em失败: {e1}")

            # 方法2: 使用Tushare的审计意见（如果可用）
            if self.tushare_api:
                try:
                    df = self.tushare_api.fina_audit(ts_code=ts_code)
                    if df is not None and not df.empty:
                        return {
                            'status': 'success',
                            'count': len(df),
                            'data': df.to_dict('records'),
                            'source': 'tushare'
                        }
                except Exception as e2:
                    logger.debug(f"tushare fina_audit失败: {e2}")

            return {'status': 'no_data', 'message': '无审计意见'}
        except Exception as e:
            logger.warning(f"⚠️ 审计意见获取失败: {e}")
            return {'status': 'no_data', 'message': '审计意见暂不可用'}

    def _get_margin_trading_ak(self, ts_code: str) -> Dict:
        """获取融资融券（AKShare）"""
        try:
            import akshare as ak
            symbol = ts_code.split('.')[0]

            # 方法1: 使用融资融券明细
            try:
                df = ak.stock_margin_detail_szse(date="")  # 最新日期
                if df is not None and not df.empty:
                    stock_data = df[df['证券代码'].astype(str) == symbol]
                    if not stock_data.empty:
                        return {
                            'status': 'success',
                            'count': len(stock_data),
                            'data': stock_data.head(20).to_dict('records')
                        }
            except Exception as e1:
                logger.debug(f"stock_margin_detail_szse失败: {e1}")

            # 方法2: 使用上交所融资融券
            try:
                df = ak.stock_margin_detail_sse(date="")
                if df is not None and not df.empty:
                    stock_data = df[df['标的证券代码'].astype(str) == symbol]
                    if not stock_data.empty:
                        return {
                            'status': 'success',
                            'count': len(stock_data),
                            'data': stock_data.head(20).to_dict('records')
                        }
            except Exception as e2:
                logger.debug(f"stock_margin_detail_sse失败: {e2}")

            # 方法3: 使用东方财富融资融券汇总
            try:
                df = ak.stock_margin_sse(start_date=(datetime.now() - timedelta(days=30)).strftime('%Y%m%d'))
                if df is not None and not df.empty:
                    return {
                        'status': 'success',
                        'count': len(df),
                        'data': df.head(20).to_dict('records'),
                        'description': '市场融资融券汇总'
                    }
            except Exception as e3:
                logger.debug(f"stock_margin_sse失败: {e3}")

            return {'status': 'no_data', 'message': '无融资融券数据'}
        except Exception as e:
            logger.warning(f"⚠️ 融资融券获取失败: {e}")
            return {'status': 'no_data', 'message': '融资融券暂不可用'}
    
    def _get_realtime_tick(self, ts_code: str) -> Dict:
        """获取实时成交数据（使用tick_5min）"""
        try:
            if not self.tushare_api:
                return {'status': 'error', 'error': 'Tushare API未初始化'}
            
            # 使用5分钟tick数据代替（Tushare没有realtime_tick接口）
            # 获取当天数据
            trade_date = datetime.now().strftime('%Y%m%d')
            
            df = self.tushare_api.stk_mins(
                ts_code=ts_code,
                freq='5min'  # 5分钟频度
            )
            
            if df is not None and not df.empty:
                # 只返回最新20条
                records = df.head(20).to_dict('records')
                return {
                    'status': 'success',
                    'count': len(records),
                    'data': records,
                    'message': '5分钟tick数据'
                }
            else:
                return {
                    'status': 'no_data',
                    'message': '无分钟级数据（可能需要更高权限）'
                }
                
        except Exception as e:
            logger.warning(f"⚠️ 分钟级数据获取失败: {e}")
            # 降级：返回无数据而不是错误
            return {
                'status': 'no_data',
                'message': f'暂不支持实时成交（{str(e)[:50]}）'
            }
    
    def _get_limit_list(self, ts_code: str) -> Dict:
        """获取涨跌停数据"""
        try:
            if not self.tushare_api:
                return {'status': 'error', 'error': 'Tushare API未初始化'}
            
            # 获取最近30天的数据
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            df = self.tushare_api.limit_list_d(
                ts_code=ts_code,
                start_date=start_date.strftime('%Y%m%d'),
                end_date=end_date.strftime('%Y%m%d')
            )
            
            if df is not None and not df.empty:
                records = df.to_dict('records')
                return {
                    'status': 'success',
                    'count': len(records),
                    'data': records
                }
            else:
                return {
                    'status': 'no_data',
                    'message': '近30天无涨跌停记录'
                }
                
        except Exception as e:
            logger.warning(f"⚠️ 涨跌停数据获取失败: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _get_margin_data(self, ts_code: str) -> Dict:
        """获取融资融券数据"""
        try:
            if not self.tushare_api:
                return {'status': 'error', 'error': 'Tushare API未初始化'}
            
            # 获取最近10条记录
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
            
            df = self.tushare_api.margin(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date
            )
            
            if df is not None and not df.empty:
                records = df.head(10).to_dict('records')
                return {
                    'status': 'success',
                    'count': len(records),
                    'data': records,
                    'latest': records[0] if records else None
                }
            else:
                return {
                    'status': 'no_data',
                    'message': '无融资融券数据'
                }
                
        except Exception as e:
            logger.warning(f"⚠️ 融资融券数据获取失败: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _get_company_info(self, ts_code: str) -> Dict:
        """获取上市公司基本信息"""
        try:
            if not self.tushare_api:
                return {'status': 'error', 'error': 'Tushare API未初始化'}
            
            df = self.tushare_api.stock_company(
                ts_code=ts_code,
                fields='ts_code,chairman,manager,secretary,reg_capital,setup_date,province,city,introduction,website,email,office,employees,main_business,business_scope'
            )
            
            if df is not None and not df.empty:
                info = df.iloc[0].to_dict()
                return {
                    'status': 'success',
                    'data': info
                }
            else:
                return {
                    'status': 'no_data',
                    'message': '无公司基本信息'
                }
                
        except Exception as e:
            logger.warning(f"⚠️ 公司基本信息获取失败: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _get_managers(self, ts_code: str) -> Dict:
        """获取管理层信息"""
        try:
            if not self.tushare_api:
                return {'status': 'error', 'error': 'Tushare API未初始化'}
            
            df = self.tushare_api.stk_managers(
                ts_code=ts_code
            )
            
            if df is not None and not df.empty:
                records = df.to_dict('records')
                return {
                    'status': 'success',
                    'count': len(records),
                    'data': records
                }
            else:
                return {
                    'status': 'no_data',
                    'message': '无管理层信息'
                }
                
        except Exception as e:
            logger.warning(f"⚠️ 管理层信息获取失败: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _get_manager_rewards(self, ts_code: str) -> Dict:
        """获取管理层薪酬和持股"""
        try:
            if not self.tushare_api:
                return {'status': 'error', 'error': 'Tushare API未初始化'}
            
            # 获取最近3年的薪酬数据
            end_year = datetime.now().year
            
            df = self.tushare_api.stk_rewards(
                ts_code=ts_code,
                end_date=f'{end_year}1231'
            )
            
            if df is not None and not df.empty:
                records = df.to_dict('records')
                return {
                    'status': 'success',
                    'count': len(records),
                    'data': records
                }
            else:
                return {
                    'status': 'no_data',
                    'message': '无薪酬数据'
                }
                
        except Exception as e:
            logger.warning(f"⚠️ 管理层薪酬获取失败: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _get_main_business(self, ts_code: str) -> Dict:
        """获取主营业务构成"""
        try:
            if not self.tushare_api:
                return {'status': 'error', 'error': 'Tushare API未初始化'}
            
            # 获取最近3期数据
            df = self.tushare_api.fina_mainbz(
                ts_code=ts_code,
                period=(datetime.now() - timedelta(days=365)).strftime('%Y%m%d'),
                type='P'  # P按产品 D按地区
            )
            
            if df is not None and not df.empty:
                records = df.to_dict('records')
                return {
                    'status': 'success',
                    'count': len(records),
                    'data': records
                }
            else:
                return {
                    'status': 'no_data',
                    'message': '无主营业务数据'
                }
                
        except Exception as e:
            logger.warning(f"⚠️ 主营业务数据获取失败: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _get_hsgt_holding(self, ts_code: str) -> Dict:
        """获取沪深港通持股数据"""
        try:
            if not self.tushare_api:
                return {'status': 'error', 'error': 'Tushare API未初始化'}
            
            # 获取最近30天的数据
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
            
            df = self.tushare_api.hsgt_top10(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date
            )
            
            if df is not None and not df.empty:
                records = df.to_dict('records')
                return {
                    'status': 'success',
                    'count': len(records),
                    'data': records,
                    'latest': records[0] if records else None
                }
            else:
                return {
                    'status': 'no_data',
                    'message': '无港股通持股数据'
                }
                
        except Exception as e:
            logger.warning(f"⚠️ 港股通持股数据获取失败: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _get_announcements(self, ts_code: str) -> Dict:
        """获取上市公司公告（暂无可用接口）"""
        # Tushare的公告接口需要高积分权限，AKShare的stock_notice_report也不稳定
        # 作为替代，我们使用业绩预告和快报作为“重要公告”
        try:
            if not self.tushare_api:
                return {'status': 'no_data', 'message': '公告查询暂不可用'}
            
            # 使用业绩预告作为重要公告的替代
            announcements = []
            
            # 1. 业绩预告
            try:
                forecast_df = self.tushare_api.forecast(
                    ts_code=ts_code,
                    start_date=(datetime.now() - timedelta(days=365)).strftime('%Y%m%d'),
                    end_date=datetime.now().strftime('%Y%m%d')
                )
                if forecast_df is not None and not forecast_df.empty:
                    for _, row in forecast_df.head(5).iterrows():
                        announcements.append({
                            'type': '业绩预告',
                            'ann_date': row.get('ann_date', ''),
                            'end_date': row.get('end_date', ''),
                            'summary': row.get('summary', ''),
                            'change_reason': row.get('change_reason', '')
                        })
            except:
                pass
            
            # 2. 业绩快报
            try:
                express_df = self.tushare_api.express(
                    ts_code=ts_code,
                    start_date=(datetime.now() - timedelta(days=365)).strftime('%Y%m%d'),
                    end_date=datetime.now().strftime('%Y%m%d')
                )
                if express_df is not None and not express_df.empty:
                    for _, row in express_df.head(5).iterrows():
                        announcements.append({
                            'type': '业绩快报',
                            'ann_date': row.get('ann_date', ''),
                            'end_date': row.get('end_date', ''),
                            'revenue': row.get('revenue', 0),
                            'profit': row.get('operate_profit', 0)
                        })
            except:
                pass
            
            if announcements:
                return {
                    'status': 'success',
                    'count': len(announcements),
                    'data': announcements,
                    'message': '重要公告（业绩预告/快报）'
                }
            else:
                return {
                    'status': 'no_data',
                    'message': '近一年无重要公告'
                }
                
        except Exception as e:
            logger.warning(f"⚠️ 公告数据获取失败: {e}")
            return {
                'status': 'no_data',
                'message': '公告查询暂不可用'
            }
    
    def _get_news_data(self, ts_code: str) -> List[Dict]:
        """获取新闻数据（调用现有的新闻聚合器）"""
        try:
            from backend.dataflows.news.multi_source_news_aggregator import get_news_aggregator

            aggregator = get_news_aggregator()
            result = aggregator.aggregate_news(
                ts_code=ts_code,
                limit_per_source=50,  # 每个源50条
                include_tushare=False,
                include_akshare=True,
                include_market_news=True
            )

            return result.get('merged_news', [])

        except Exception as e:
            logger.warning(f"⚠️ 新闻数据获取失败: {e}")
            return []

    # ==================== 缺失的Tushare接口补充 ====================

    def _get_realtime_list(self) -> Dict:
        """获取实时行情列表（Tushare realtime_list）- 全市场实时行情"""
        try:
            import tushare as ts
            # 使用爬虫接口获取全市场实时行情
            df = ts.realtime_list(src='dc')  # dc=东财

            if df is not None and not df.empty:
                records = df.head(100).to_dict('records')
                return {
                    'status': 'success',
                    'count': len(records),
                    'data': records,
                    'description': '全市场实时行情TOP100'
                }
            return {'status': 'no_data', 'message': '无实时行情数据'}
        except Exception as e:
            logger.warning(f"⚠️ 实时行情列表获取失败: {e}")
            return {'status': 'no_data', 'message': '实时行情列表暂不可用'}

    def _get_pledge_detail(self, ts_code: str) -> Dict:
        """获取股权质押明细（Tushare pledge_detail）"""
        try:
            if not self.tushare_api:
                return {'status': 'error', 'message': 'Tushare API未初始化'}

            df = self.tushare_api.pledge_detail(ts_code=ts_code)

            if df is not None and not df.empty:
                records = df.head(20).to_dict('records')
                return {
                    'status': 'success',
                    'count': len(records),
                    'data': records,
                    'description': '股权质押明细'
                }
            return {'status': 'no_data', 'message': '无质押明细数据'}
        except Exception as e:
            logger.warning(f"⚠️ 质押明细获取失败: {e}")
            return {'status': 'no_data', 'message': '质押明细暂不可用'}

    def _get_margin_detail(self, ts_code: str) -> Dict:
        """获取融资融券明细（Tushare margin_detail）"""
        try:
            if not self.tushare_api:
                return {'status': 'error', 'message': 'Tushare API未初始化'}

            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')

            df = self.tushare_api.margin_detail(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date
            )

            if df is not None and not df.empty:
                records = df.head(30).to_dict('records')
                return {
                    'status': 'success',
                    'count': len(records),
                    'data': records,
                    'description': '融资融券明细'
                }
            return {'status': 'no_data', 'message': '无融资融券明细'}
        except Exception as e:
            logger.warning(f"⚠️ 融资融券明细获取失败: {e}")
            return {'status': 'no_data', 'message': '融资融券明细暂不可用'}

    def _get_ggt_top10(self, ts_code: str = None) -> Dict:
        """获取港股通十大成交股（Tushare ggt_top10）"""
        try:
            if not self.tushare_api:
                return {'status': 'error', 'message': 'Tushare API未初始化'}

            trade_date = datetime.now().strftime('%Y%m%d')

            # 尝试获取最近5个交易日的数据
            for i in range(5):
                try:
                    check_date = (datetime.now() - timedelta(days=i)).strftime('%Y%m%d')
                    df = self.tushare_api.ggt_top10(trade_date=check_date)
                    if df is not None and not df.empty:
                        if ts_code:
                            df = df[df['ts_code'] == ts_code]
                        if not df.empty:
                            records = df.to_dict('records')
                            return {
                                'status': 'success',
                                'count': len(records),
                                'data': records,
                                'trade_date': check_date,
                                'description': '港股通十大成交股'
                            }
                except:
                    continue

            return {'status': 'no_data', 'message': '无港股通十大成交数据'}
        except Exception as e:
            logger.warning(f"⚠️ 港股通十大成交获取失败: {e}")
            return {'status': 'no_data', 'message': '港股通十大成交暂不可用'}

    def _get_hk_hold(self, ts_code: str) -> Dict:
        """获取沪深港通持股明细（Tushare hk_hold）"""
        try:
            if not self.tushare_api:
                return {'status': 'error', 'message': 'Tushare API未初始化'}

            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')

            df = self.tushare_api.hk_hold(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date
            )

            if df is not None and not df.empty:
                records = df.head(30).to_dict('records')
                return {
                    'status': 'success',
                    'count': len(records),
                    'data': records,
                    'description': '沪深港通持股明细'
                }
            return {'status': 'no_data', 'message': '无沪深港通持股明细'}
        except Exception as e:
            logger.warning(f"⚠️ 沪深港通持股明细获取失败: {e}")
            return {'status': 'no_data', 'message': '沪深港通持股明细暂不可用'}

    def _get_moneyflow_hsgt(self) -> Dict:
        """获取沪深港通资金流向（Tushare moneyflow_hsgt）"""
        try:
            if not self.tushare_api:
                return {'status': 'error', 'message': 'Tushare API未初始化'}

            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')

            df = self.tushare_api.moneyflow_hsgt(
                start_date=start_date,
                end_date=end_date
            )

            if df is not None and not df.empty:
                records = df.to_dict('records')
                return {
                    'status': 'success',
                    'count': len(records),
                    'data': records,
                    'description': '沪深港通资金流向'
                }
            return {'status': 'no_data', 'message': '无沪深港通资金流向数据'}
        except Exception as e:
            logger.warning(f"⚠️ 沪深港通资金流向获取失败: {e}")
            return {'status': 'no_data', 'message': '沪深港通资金流向暂不可用'}

    def _get_limit_list_ths(self, ts_code: str = None) -> Dict:
        """获取同花顺涨跌停数据（Tushare limit_list_ths）- 备用接口"""
        try:
            if not self.tushare_api:
                return {'status': 'error', 'message': 'Tushare API未初始化'}

            trade_date = datetime.now().strftime('%Y%m%d')

            # 尝试获取最近5个交易日的数据
            for i in range(5):
                try:
                    check_date = (datetime.now() - timedelta(days=i)).strftime('%Y%m%d')
                    df = self.tushare_api.limit_list_d(trade_date=check_date)
                    if df is not None and not df.empty:
                        if ts_code:
                            df = df[df['ts_code'] == ts_code]
                        if not df.empty:
                            records = df.to_dict('records')
                            return {
                                'status': 'success',
                                'count': len(records),
                                'data': records,
                                'trade_date': check_date,
                                'description': '涨跌停数据'
                            }
                except:
                    continue

            return {'status': 'no_data', 'message': '无涨跌停数据'}
        except Exception as e:
            logger.warning(f"⚠️ 涨跌停数据获取失败: {e}")
            return {'status': 'no_data', 'message': '涨跌停数据暂不可用'}

    # ==================== 缺失的AKShare接口补充 ====================

    def _get_stock_news_em(self, ts_code: str) -> Dict:
        """获取东方财富个股新闻（AKShare stock_news_em）"""
        try:
            import akshare as ak
            symbol = ts_code.split('.')[0]

            df = ak.stock_news_em(symbol=symbol)

            if df is not None and not df.empty:
                records = []
                for _, row in df.head(30).iterrows():
                    records.append({
                        'title': str(row.get('新闻标题', '')),
                        'content': str(row.get('新闻内容', ''))[:300],
                        'time': str(row.get('发布时间', '')),
                        'source': str(row.get('文章来源', '东方财富')),
                        'url': str(row.get('新闻链接', ''))
                    })
                return {
                    'status': 'success',
                    'count': len(records),
                    'data': records,
                    'description': '东方财富个股新闻'
                }
            return {'status': 'no_data', 'message': '无个股新闻'}
        except Exception as e:
            logger.warning(f"⚠️ 东方财富新闻获取失败: {e}")
            return {'status': 'no_data', 'message': '东方财富新闻暂不可用'}

    def _generate_summary(self, data: Dict) -> Dict:
        """生成数据摘要"""
        summary = {}
        
        # 1. 实时行情
        if data['realtime'].get('status') == 'success':
            summary['realtime'] = '✅ 已获取'
        
        # 2. 实时成交
        if data['realtime_tick'].get('status') == 'success':
            summary['realtime_tick'] = f"✅ 成交{data['realtime_tick']['count']}条"
        elif data['realtime_tick'].get('status') == 'no_data':
            summary['realtime_tick'] = '🔴 无成交数据'
        
        # 3. 停复牌
        if data['suspend'].get('status') in ['normal', 'has_suspend']:
            summary['suspend'] = f"✅ {data['suspend']['message']}"
        
        # 4. ST状态
        if data['st_status'].get('status') in ['normal', 'st_stock']:
            summary['st_status'] = f"✅ {data['st_status']['message']}"
        
        # 5. 财务数据
        if data['financial'].get('status') == 'success':
            summary['financial'] = f"✅ 利润表{len(data['financial']['income'])}期 资产负债表{len(data['financial']['balance'])}期 现金流{len(data['financial']['cashflow'])}期"
        
        # 6. 审计意见
        if data.get('audit', {}).get('status') == 'success':
            count = data['audit'].get('count', len(data['audit'].get('data', [])))
            summary['audit'] = f"✅ 审计意见{count}条"
        elif data.get('audit', {}).get('status') == 'no_data':
            summary['audit'] = '🔴 无审计数据'
        
        # 7. 业绩预告
        if data['forecast'].get('status') == 'success':
            summary['forecast'] = f"✅ 业绩预告{len(data['forecast']['forecast'])}条 快报{len(data['forecast']['express'])}条"
        elif data['forecast'].get('status') == 'no_data':
            summary['forecast'] = '🔴 无业绩预告'
        
        # 8. 分红送股
        if data['dividend'].get('status') == 'success':
            summary['dividend'] = f"✅ 分红记录{data['dividend']['count']}条"
        elif data['dividend'].get('status') == 'no_data':
            summary['dividend'] = '🔴 无分红记录'
        
        # 9. 限售解禁
        if data['restricted'].get('status') == 'success':
            summary['restricted'] = f"✅ 解禁数据{data['restricted']['count']}条"
        elif data['restricted'].get('status') == 'no_data':
            summary['restricted'] = '🔴 无解禁数据'
        
        # 10. 股权质押
        if data['pledge'].get('status') == 'success':
            summary['pledge'] = f"✅ 质押比例{data['pledge']['pledge_ratio']}%"
        elif data['pledge'].get('status') == 'no_data':
            summary['pledge'] = '🔴 无质押数据'
        
        # 11. 股东增减持
        if data['holder_trade'].get('status') == 'success':
            summary['holder_trade'] = f"✅ 增减持{data['holder_trade']['count']}条"
        elif data['holder_trade'].get('status') == 'no_data':
            summary['holder_trade'] = '🔴 无增减持记录'
        
        # 12. 龙虎榜
        if data['dragon_tiger'].get('status') == 'success':
            summary['dragon_tiger'] = f"✅ 龙虎榜{data['dragon_tiger']['count']}次"
        elif data['dragon_tiger'].get('status') == 'no_data':
            summary['dragon_tiger'] = '🔴 无龙虎榜数据'
        
        # 12.5 机构龙虎榜
        if data.get('top_inst', {}).get('status') == 'success':
            summary['top_inst'] = f"✅ 机构龙虎榜{data['top_inst']['count']}条"
        
        # 12.6 大宗交易
        if data.get('block_trade', {}).get('status') == 'success':
            summary['block_trade'] = f"✅ 大宗交易{data['block_trade']['count']}条"
        
        # 13. 涨跌停
        if data['limit_list'].get('status') == 'success':
            summary['limit_list'] = f"✅ 涨跌停{data['limit_list']['count']}次"
        elif data['limit_list'].get('status') == 'no_data':
            summary['limit_list'] = '🔴 近30天无涨跌停'
        
        # 14. 融资融券
        if data['margin'].get('status') == 'success':
            summary['margin'] = f"✅ 融资融券{data['margin']['count']}条"
        elif data['margin'].get('status') == 'no_data':
            summary['margin'] = '🔴 无融资融券数据'
        
        # 15. 公司信息
        if data['company_info'].get('status') == 'success':
            summary['company_info'] = '✅ 已获取公司信息'
        elif data['company_info'].get('status') == 'no_data':
            summary['company_info'] = '🔴 无公司信息'
        
        # 16. 管理层
        if data['managers'].get('status') == 'success':
            summary['managers'] = f"✅ 管理层{data['managers']['count']}人"
        elif data['managers'].get('status') == 'no_data':
            summary['managers'] = '🔴 无管理层信息'
        
        # 17. 管理层薪酬
        if data['manager_rewards'].get('status') == 'success':
            summary['manager_rewards'] = f"✅ 薪酬记录{data['manager_rewards']['count']}条"
        elif data['manager_rewards'].get('status') == 'no_data':
            summary['manager_rewards'] = '🔴 无薪酬记录'
        
        # 18. 主营业务
        if data['main_business'].get('status') == 'success':
            summary['main_business'] = f"✅ 主营构成{data['main_business']['count']}条"
        elif data['main_business'].get('status') == 'no_data':
            summary['main_business'] = '🔴 无主营业务数据'
        
        # 19. 港股通
        if data['hsgt_holding'].get('status') == 'success':
            summary['hsgt_holding'] = f"✅ 港股通{data['hsgt_holding']['count']}条"
        elif data['hsgt_holding'].get('status') == 'no_data':
            summary['hsgt_holding'] = '🔴 无港股通数据'
        
        # 20. 公告
        if data['announcements'].get('status') == 'success':
            summary['announcements'] = f"✅ 公告{data['announcements']['count']}条"
        elif data['announcements'].get('status') == 'no_data':
            summary['announcements'] = '🔴 无公告数据'

        # 20.5 新浪新闻
        if data.get('news_sina', {}).get('status') == 'success':
            summary['news_sina'] = f"✅ 新浪新闻{data['news_sina']['count']}条"

        # 20.6 市场快讯
        if data.get('market_news', {}).get('status') == 'success':
            summary['market_news'] = f"✅ 市场快讯{data['market_news']['count']}条"

        # 20.7 行业政策
        if data.get('industry_policy', {}).get('status') == 'success':
            summary['industry_policy'] = f"✅ 行业政策{data['industry_policy']['count']}条"

        # 21. 新闻
        if data['news']:
            summary['news'] = f"✅ 新闻{len(data['news'])}条"
        else:
            summary['news'] = '🔴 无新闻数据'

        # ==================== 新增接口摘要 ====================

        # 22. 全市场实时行情
        if data.get('realtime_list', {}).get('status') == 'success':
            summary['realtime_list'] = f"✅ 全市场行情{data['realtime_list']['count']}条"

        # 23. 质押明细
        if data.get('pledge_detail', {}).get('status') == 'success':
            summary['pledge_detail'] = f"✅ 质押明细{data['pledge_detail']['count']}条"

        # 24. 融资融券明细
        if data.get('margin_detail', {}).get('status') == 'success':
            summary['margin_detail'] = f"✅ 融资融券明细{data['margin_detail']['count']}条"

        # 25. 港股通十大成交
        if data.get('ggt_top10', {}).get('status') == 'success':
            summary['ggt_top10'] = f"✅ 港股通十大{data['ggt_top10']['count']}条"

        # 26. 沪深港通持股明细
        if data.get('hk_hold', {}).get('status') == 'success':
            summary['hk_hold'] = f"✅ 沪深港通持股{data['hk_hold']['count']}条"

        # 27. 沪深港通资金流向
        if data.get('moneyflow_hsgt', {}).get('status') == 'success':
            summary['moneyflow_hsgt'] = f"✅ 资金流向{data['moneyflow_hsgt']['count']}条"

        # 28. 涨跌停数据（同花顺）
        if data.get('limit_list_ths', {}).get('status') == 'success':
            summary['limit_list_ths'] = f"✅ 涨跌停THS{data['limit_list_ths']['count']}条"

        # 29. 东方财富个股新闻
        if data.get('news_em', {}).get('status') == 'success':
            summary['news_em'] = f"✅ 东财新闻{data['news_em']['count']}条"

        return summary


# 全局实例
_comprehensive_service = None

def get_comprehensive_service():
    """获取综合数据服务实例"""
    global _comprehensive_service
    if _comprehensive_service is None:
        _comprehensive_service = ComprehensiveStockDataService()
    return _comprehensive_service
