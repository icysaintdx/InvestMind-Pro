#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
龙虎榜数据采集模块
支持多数据源获取龙虎榜数据
"""

import logging
import math
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

import pandas as pd
import akshare as ak

logger = logging.getLogger(__name__)


def clean_for_json(value):
    """
    清洗数据以确保可以被JSON序列化
    处理 inf, -inf, nan 等特殊浮点数值
    """
    if value is None:
        return None
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
        return value
    if isinstance(value, dict):
        return {k: clean_for_json(v) for k, v in value.items()}
    if isinstance(value, list):
        return [clean_for_json(item) for item in value]
    return value


def clean_data_list(data_list: List[Dict]) -> List[Dict]:
    """清洗数据列表中的所有值"""
    return [clean_for_json(item) for item in data_list]


def safe_float(value, default=0):
    """安全转换为浮点数"""
    try:
        if pd.isna(value):
            return default
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_int(value, default=0):
    """安全转换为整数"""
    try:
        if pd.isna(value):
            return default
        return int(float(value))
    except (ValueError, TypeError):
        return default


class LonghubangDataFetcher:
    """龙虎榜数据获取类"""

    def __init__(self):
        """初始化数据获取器"""
        logger.info("[龙虎榜] 数据获取器初始化...")

    def _find_latest_trading_day(self, max_days: int = 10) -> Optional[str]:
        """
        查找最近有龙虎榜数据的交易日
        
        Args:
            max_days: 最多往前查找的天数
            
        Returns:
            str: 有数据的日期（格式：YYYYMMDD），如果没找到返回None
        """
        for i in range(max_days):
            check_date = datetime.now() - timedelta(days=i)
            date = check_date.strftime('%Y%m%d')
            # 跳过周末
            weekday = check_date.weekday()
            if weekday >= 5:  # 周六=5, 周日=6
                logger.debug(f"[龙虎榜] {date} 是周末，跳过")
                continue
            try:
                df = ak.stock_lhb_detail_em(start_date=date, end_date=date)
                if df is not None and isinstance(df, pd.DataFrame) and not df.empty:
                    logger.info(f"[龙虎榜] 找到最近有数据的交易日: {date}")
                    return date
                else:
                    logger.debug(f"[龙虎榜] {date} 无数据")
            except TypeError as e:
                # 处理 'NoneType' object is not subscriptable 错误
                logger.debug(f"[龙虎榜] {date} API返回None: {e}")
                continue
            except Exception as e:
                logger.debug(f"[龙虎榜] {date} 查询失败: {e}")
                continue
        return None

    def get_longhubang_data(self, date: str = None) -> Dict[str, Any]:
        """
        获取指定日期的龙虎榜数据

        Args:
            date: 日期，格式为 YYYY-MM-DD 或 YYYYMMDD，默认为最近有数据的交易日

        Returns:
            dict: 龙虎榜数据
        """
        original_date = date
        
        if date is None:
            # 自动查找最近有数据的交易日
            date = self._find_latest_trading_day()
            if date is None:
                logger.warning("[龙虎榜] 未找到最近有数据的交易日")
                return {'success': False, 'data': [], 'message': '未找到最近有数据的交易日，可能是非交易时间'}
        else:
            date = date.replace('-', '')
            # 检查是否是周末
            try:
                check_date = datetime.strptime(date, '%Y%m%d')
                if check_date.weekday() >= 5:
                    logger.info(f"[龙虎榜] {date} 是周末，自动查找最近交易日")
                    date = self._find_latest_trading_day()
                    if date is None:
                        return {'success': False, 'data': [], 'message': f'{original_date} 是周末，未找到最近有数据的交易日'}
            except ValueError:
                pass

        logger.info(f"[龙虎榜] 获取 {date} 的龙虎榜数据...")

        try:
            # 使用akshare获取龙虎榜数据
            # 获取龙虎榜详情
            df = ak.stock_lhb_detail_em(start_date=date, end_date=date)

            if df is None or (isinstance(df, pd.DataFrame) and df.empty):
                logger.warning(f"[龙虎榜] {date} 无数据，尝试查找最近交易日")
                # 如果指定日期无数据，尝试查找最近有数据的交易日
                date = self._find_latest_trading_day()
                if date is None:
                    return {'success': False, 'data': [], 'message': f'无数据，可能是非交易日'}
                # 重新获取
                df = ak.stock_lhb_detail_em(start_date=date, end_date=date)
                if df is None or (isinstance(df, pd.DataFrame) and df.empty):
                    return {'success': False, 'data': [], 'message': f'{date} 无数据'}

            # 转换为标准格式
            data_list = []
            for _, row in df.iterrows():
                data_list.append({
                    'stock_code': str(row.get('代码', '')),
                    'stock_name': str(row.get('名称', '')),
                    'close_price': safe_float(row.get('收盘价', 0)),
                    'change_pct': safe_float(row.get('涨跌幅', 0)),
                    'lhb_net_amount': safe_float(row.get('龙虎榜净买额', 0)),
                    'lhb_buy_amount': safe_float(row.get('龙虎榜买入额', 0)),
                    'lhb_sell_amount': safe_float(row.get('龙虎榜卖出额', 0)),
                    'lhb_turnover_rate': safe_float(row.get('成交额占总成交比', 0)),
                    'turnover_rate': safe_float(row.get('换手率', 0)),
                    'reason': str(row.get('上榜原因', '')),
                    'interpretation': str(row.get('解读', '')),
                    'market_total_amount': safe_float(row.get('市场总成交额', 0)),
                    'circulation_value': safe_float(row.get('流通市值', 0)),
                    'after_1day': safe_float(row.get('上榜后1日', 0)),
                    'after_2day': safe_float(row.get('上榜后2日', 0)),
                    'after_5day': safe_float(row.get('上榜后5日', 0)),
                    'after_10day': safe_float(row.get('上榜后10日', 0)),
                    'date': date
                })

            logger.info(f"[龙虎榜] 成功获取 {len(data_list)} 条记录")
            cleaned_data = clean_data_list(data_list)
            return {
                'success': True,
                'data': cleaned_data,
                'date': date,
                'count': len(cleaned_data)
            }

        except TypeError as e:
            logger.warning(f"[龙虎榜] {date} API返回None，尝试查找最近交易日: {e}")
            latest_date = self._find_latest_trading_day()
            if latest_date and latest_date != date:
                return self.get_longhubang_data(latest_date)
            return {'success': False, 'data': [], 'message': f'{date} 无数据，可能是非交易日'}
        except Exception as e:
            logger.error(f"[龙虎榜] 获取数据失败: {e}", exc_info=True)
            return {'success': False, 'data': [], 'message': str(e)}

    def get_lhb_stock_detail(self, stock_code: str, date: str = None) -> Dict[str, Any]:
        """
        获取单只股票的龙虎榜详情（买卖席位）
        """
        if not stock_code or stock_code == 'undefined':
            logger.warning(f"[龙虎榜] 无效的股票代码: {stock_code}")
            return {'success': False, 'message': '无效的股票代码', 'buy_seats': [], 'sell_seats': []}
        
        if date is None:
            date = self._find_latest_trading_day()
            if date is None:
                return {'success': False, 'message': '未找到最近有数据的交易日', 'buy_seats': [], 'sell_seats': []}
        else:
            date = date.replace('-', '')

        logger.info(f"[龙虎榜] 获取股票 {stock_code} 在 {date} 的席位详情")

        try:
            buy_list = []
            sell_list = []
            
            # 获取买入席位
            try:
                buy_df = ak.stock_lhb_stock_detail_em(symbol=stock_code, date=date, flag="买入")
                if buy_df is not None and isinstance(buy_df, pd.DataFrame) and not buy_df.empty:
                    for _, row in buy_df.iterrows():
                        try:
                            buy_list.append({
                                'rank': safe_int(row.iloc[0]) if len(row) > 0 else 0,
                                'name': str(row.iloc[1]) if len(row) > 1 else '',
                                'trader_name': str(row.iloc[1]) if len(row) > 1 else '',
                                'amount': safe_float(row.iloc[2]) if len(row) > 2 else 0,
                                'buy_amount': safe_float(row.iloc[2]) if len(row) > 2 else 0,
                                'ratio': safe_float(row.iloc[3]) if len(row) > 3 else 0,
                                'buy_pct': safe_float(row.iloc[3]) if len(row) > 3 else 0,
                                'sell_amount': safe_float(row.iloc[4]) if len(row) > 4 else 0,
                                'net_amount': safe_float(row.iloc[5]) if len(row) > 5 else 0
                            })
                        except Exception as e:
                            logger.warning(f"[龙虎榜] 解析买入席位行数据失败: {e}")
                            continue
            except Exception as e:
                logger.warning(f"[龙虎榜] 获取买入席位失败: {e}")

            # 获取卖出席位
            try:
                sell_df = ak.stock_lhb_stock_detail_em(symbol=stock_code, date=date, flag="卖出")
                if sell_df is not None and isinstance(sell_df, pd.DataFrame) and not sell_df.empty:
                    for _, row in sell_df.iterrows():
                        try:
                            sell_list.append({
                                'rank': safe_int(row.iloc[0]) if len(row) > 0 else 0,
                                'name': str(row.iloc[1]) if len(row) > 1 else '',
                                'trader_name': str(row.iloc[1]) if len(row) > 1 else '',
                                'amount': safe_float(row.iloc[4]) if len(row) > 4 else 0,
                                'buy_amount': safe_float(row.iloc[2]) if len(row) > 2 else 0,
                                'sell_amount': safe_float(row.iloc[4]) if len(row) > 4 else 0,
                                'ratio': safe_float(row.iloc[5]) if len(row) > 5 else 0,
                                'sell_pct': safe_float(row.iloc[5]) if len(row) > 5 else 0,
                                'net_amount': safe_float(row.iloc[6]) if len(row) > 6 else 0
                            })
                        except Exception as e:
                            logger.warning(f"[龙虎榜] 解析卖出席位行数据失败: {e}")
                            continue
            except Exception as e:
                logger.warning(f"[龙虎榜] 获取卖出席位失败: {e}")

            logger.info(f"[龙虎榜] 获取到 {len(buy_list)} 个买入席位, {len(sell_list)} 个卖出席位")

            return clean_for_json({
                'success': True,
                'stock_code': stock_code,
                'date': date,
                'buy_seats': buy_list,
                'sell_seats': sell_list
            })

        except Exception as e:
            logger.error(f"[龙虎榜] 获取席位详情失败: {e}", exc_info=True)
            return {'success': False, 'message': str(e), 'buy_seats': [], 'sell_seats': []}

    def get_lhb_institution_stat(self, days: int = 5) -> Dict[str, Any]:
        """获取机构席位统计"""
        try:
            logger.info("[龙虎榜] 正在获取机构席位统计...")
            
            df = None
            try:
                df = ak.stock_lhb_jgstatistic_em(symbol="近一月")
                logger.info("[龙虎榜] 使用机构统计接口成功")
            except Exception as e:
                logger.warning(f"[龙虎榜] 机构统计接口失败: {e}")

            if df is None:
                return {'success': True, 'data': [], 'message': '暂无机构统计数据'}
            
            if isinstance(df, pd.DataFrame) and df.empty:
                return {'success': True, 'data': [], 'message': '暂无机构统计数据'}

            data_list = []
            for _, row in df.head(50).iterrows():
                try:
                    stock_name = str(row.get('名称', ''))
                    buy_count = safe_int(row.get('机构买入次数', 0))
                    sell_count = safe_int(row.get('机构卖出次数', 0))
                    buy_amount = safe_float(row.get('机构买入额', 0))
                    sell_amount = safe_float(row.get('机构卖出额', 0))
                    net_amount = safe_float(row.get('机构净买额', 0))
                    
                    change_1m = safe_float(row.get('近1个月涨跌幅', 0))
                    win_rate = 50 + change_1m / 2 if change_1m else 50
                    win_rate = max(0, min(100, win_rate))
                    
                    data_list.append({
                        'name': stock_name,
                        'stock_code': str(row.get('代码', '')),
                        'stock_name': stock_name,
                        'close_price': safe_float(row.get('收盘价', 0)),
                        'change_pct': safe_float(row.get('涨跌幅', 0)),
                        'buy_count': buy_count,
                        'sell_count': sell_count,
                        'buy_amount': buy_amount,
                        'sell_amount': sell_amount,
                        'net_amount': net_amount,
                        'win_rate': round(win_rate, 1),
                        'lhb_times': safe_int(row.get('上榜次数', 0)),
                        'lhb_amount': safe_float(row.get('龙虎榜成交金额', 0))
                    })
                except Exception as e:
                    logger.warning(f"[龙虎榜] 解析机构统计行数据失败: {e}")
                    continue

            cleaned_data = clean_data_list(data_list)
            logger.info(f"[龙虎榜] 成功获取 {len(cleaned_data)} 条机构统计数据")
            return {
                'success': True,
                'data': cleaned_data,
                'count': len(cleaned_data)
            }

        except Exception as e:
            logger.error(f"[龙虎榜] 获取机构统计失败: {e}", exc_info=True)
            return {'success': True, 'data': [], 'message': f'获取失败: {str(e)}'}

    def get_lhb_trader_stat(self, days: int = 5) -> Dict[str, Any]:
        """获取营业部统计"""
        try:
            logger.info("[龙虎榜] 正在获取营业部统计...")
            
            df = None
            try:
                df = ak.stock_lhb_traderstatistic_em(symbol="近一月")
                logger.info("[龙虎榜] 使用营业部统计接口成功")
            except Exception as e:
                logger.warning(f"[龙虎榜] 营业部统计接口失败: {e}")
                try:
                    df = ak.stock_lhb_yybph_em()
                    logger.info("[龙虎榜] 使用营业部排行接口成功（备用）")
                except Exception as e2:
                    logger.warning(f"[龙虎榜] 营业部排行接口也失败: {e2}")

            if df is None:
                return {'success': True, 'data': [], 'message': '暂无营业部统计数据'}
            
            if isinstance(df, pd.DataFrame) and df.empty:
                return {'success': True, 'data': [], 'message': '暂无营业部统计数据'}

            data_list = []
            for idx, row in df.head(50).iterrows():
                try:
                    trader_name = str(row.get('营业部名称', ''))
                    buy_amount = safe_float(row.get('买入额', 0))
                    sell_amount = safe_float(row.get('卖出额', 0))
                    net_amount = buy_amount - sell_amount
                    count = safe_int(row.get('上榜次数', 0))
                    total_amount = safe_float(row.get('龙虎榜成交金额', 0))
                    
                    data_list.append({
                        'rank': idx + 1,
                        'name': trader_name,
                        'trader_name': trader_name,
                        'count': count,
                        'lhb_times': count,
                        'buy_amount': buy_amount,
                        'sell_amount': sell_amount,
                        'net_amount': net_amount,
                        'total_amount': total_amount,
                        'buy_count': safe_int(row.get('买入次数', 0)),
                        'sell_count': safe_int(row.get('卖出次数', 0)),
                        'stocks': []
                    })
                except Exception as e:
                    logger.warning(f"[龙虎榜] 解析营业部统计行数据失败: {e}")
                    continue

            cleaned_data = clean_data_list(data_list)
            logger.info(f"[龙虎榜] 成功获取 {len(cleaned_data)} 条营业部统计数据")
            return {
                'success': True,
                'data': cleaned_data,
                'count': len(cleaned_data)
            }

        except Exception as e:
            logger.error(f"[龙虎榜] 获取营业部统计失败: {e}", exc_info=True)
            return {'success': True, 'data': [], 'message': f'获取失败: {str(e)}'}

    def get_recent_days_data(self, days: int = 5) -> List[Dict]:
        """获取最近N个交易日的龙虎榜数据"""
        all_data = []
        current_date = datetime.now()

        for i in range(days * 2):
            date = current_date - timedelta(days=i)
            if date.weekday() < 5:
                date_str = date.strftime('%Y%m%d')
                result = self.get_longhubang_data(date_str)
                if result.get('success') and result.get('data'):
                    all_data.extend(result['data'])

            if len(set(d.get('date') for d in all_data)) >= days:
                break

        return all_data

    def analyze_data_summary(self, data_list: List[Dict]) -> Dict[str, Any]:
        """分析龙虎榜数据，生成摘要统计"""
        if not data_list:
            return {}

        df = pd.DataFrame(data_list)
        df = df.fillna(0)

        summary = {
            'total_records': len(df),
            'total_stocks': int(df['stock_code'].nunique()) if 'stock_code' in df.columns else 0,
            'total_buy_amount': float(df['lhb_buy_amount'].sum()) if 'lhb_buy_amount' in df.columns else 0,
            'total_sell_amount': float(df['lhb_sell_amount'].sum()) if 'lhb_sell_amount' in df.columns else 0,
            'total_net_amount': float(df['lhb_net_amount'].sum()) if 'lhb_net_amount' in df.columns else 0,
        }

        if 'lhb_net_amount' in df.columns:
            top_stocks = df.nlargest(20, 'lhb_net_amount')[
                ['stock_code', 'stock_name', 'lhb_net_amount', 'change_pct', 'reason']
            ].to_dict('records')
            summary['top_stocks'] = clean_data_list(top_stocks)

        if 'reason' in df.columns:
            reason_counts = df['reason'].value_counts().head(10).to_dict()
            summary['reason_stats'] = reason_counts

        return clean_for_json(summary)

    def format_data_for_ai(self, data_list: List[Dict], summary: Dict = None) -> str:
        """将龙虎榜数据格式化为适合AI分析的文本格式"""
        if not data_list:
            return "暂无龙虎榜数据"

        if summary is None:
            summary = self.analyze_data_summary(data_list)

        text_parts = []
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M')

        # 总体概况
        text_parts.append(f"""
【龙虎榜总体概况】
数据时间: {now_str}
上榜股票数: {summary.get('total_stocks', 0)}
总买入额: {summary.get('total_buy_amount', 0) / 100000000:.2f}亿
总卖出额: {summary.get('total_sell_amount', 0) / 100000000:.2f}亿
净买入额: {summary.get('total_net_amount', 0) / 100000000:.2f}亿
""")

        # Top股票
        top_stocks = summary.get('top_stocks', [])
        if top_stocks:
            text_parts.append("\n【净买入TOP10】")
            for i, stock in enumerate(top_stocks[:10], 1):
                text_parts.append(
                    f"{i}. {stock.get('stock_name', '')}({stock.get('stock_code', '')}) "
                    f"净买入: {stock.get('lhb_net_amount', 0) / 10000:.0f}万 "
                    f"涨跌幅: {stock.get('change_pct', 0):.2f}% "
                    f"原因: {stock.get('reason', '')}"
                )

        # 上榜原因统计
        reason_stats = summary.get('reason_stats', {})
        if reason_stats:
            text_parts.append("\n【上榜原因分布】")
            for reason, count in list(reason_stats.items())[:5]:
                text_parts.append(f"- {reason}: {count}次")

        return "\n".join(text_parts)


# 创建全局实例
longhubang_data_fetcher = LonghubangDataFetcher()
