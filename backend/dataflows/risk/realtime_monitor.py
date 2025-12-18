"""
实时数据监控模块
使用Tushare realtime_quote和realtime_tick接口获取实时行情数据
"""

import os
from datetime import datetime
from typing import Optional, Dict, List
import pandas as pd

from backend.utils.logging_config import get_logger

logger = get_logger("dataflows.realtime_monitor")


class RealtimeMonitor:
    """实时数据监控器"""
    
    def __init__(self):
        self.token = os.getenv('TUSHARE_TOKEN', '')
        if self.token:
            try:
                import tushare as ts
                ts.set_token(self.token)
                logger.info("✅ Tushare实时监控初始化成功")
            except Exception as e:
                logger.error(f"❌ Tushare初始化失败: {e}")
    
    def is_available(self) -> bool:
        """检查是否可用（爬虫接口无需积分）"""
        return bool(self.token)
    
    def get_realtime_quote(
        self, 
        ts_codes: str, 
        src: str = 'sina'
    ) -> Optional[pd.DataFrame]:
        """
        获取实时盘口TICK快照
        
        Args:
            ts_codes: 股票代码，多个用逗号分隔，如'600000.SH,000001.SZ'
            src: 数据源，sina-新浪（默认），dc-东方财富
            
        Returns:
            DataFrame包含实时行情数据
        """
        if not self.is_available():
            logger.warning("⚠️ Tushare Token未配置")
            return None
        
        # 优先使用AKShare获取实时行情（更稳定）
        try:
            import akshare as ak

            # 解析股票代码
            codes = [c.strip().split('.')[0] for c in ts_codes.split(',')]

            df = ak.stock_zh_a_spot_em()
            if df is not None and not df.empty:
                # 筛选目标股票
                result_df = df[df['代码'].isin(codes)]
                if not result_df.empty:
                    # 转换列名以兼容原有格式
                    result_df = result_df.rename(columns={
                        '代码': 'TS_CODE',
                        '名称': 'NAME',
                        '最新价': 'PRICE',
                        '涨跌幅': 'PCT_CHANGE',
                        '涨跌额': 'CHANGE',
                        '成交量': 'VOLUME',
                        '成交额': 'AMOUNT',
                        '最高': 'HIGH',
                        '最低': 'LOW',
                        '今开': 'OPEN',
                        '昨收': 'PRE_CLOSE'
                    })
                    logger.info(f"✅ 获取实时行情(AKShare): {len(result_df)}只股票")
                    return result_df
        except Exception as e:
            logger.debug(f"AKShare实时行情获取失败: {e}")

        # 备选：使用Tushare
        try:
            import tushare as ts

            # 修复: 先设置token
            if self.token:
                ts.set_token(self.token)

            df = ts.realtime_quote(ts_code=ts_codes, src=src)

            if df is not None and not df.empty:
                logger.info(f"✅ 获取实时行情(Tushare): {len(df)}只股票 (来源:{src})")
                return df
            else:
                logger.warning(f"⚠️ 未获取到{ts_codes}的实时行情")
                return None

        except Exception as e:
            logger.error(f"❌ 获取实时行情失败: {str(e)[:100]}")
            return None
    
    def get_realtime_tick(
        self, 
        ts_code: str, 
        src: str = 'sina'
    ) -> Optional[pd.DataFrame]:
        """
        获取实时成交数据（当日所有分笔成交）
        
        Args:
            ts_code: 单个股票代码，如'600000.SH'
            src: 数据源，sina-新浪（默认），dc-东方财富
            
        Returns:
            DataFrame包含分笔成交数据
        """
        if not self.is_available():
            logger.warning("⚠️ Tushare Token未配置")
            return None
        
        try:
            import tushare as ts
            
            logger.info(f"⏳ 正在获取{ts_code}的实时成交数据，请稍等...")
            df = ts.realtime_tick(ts_code=ts_code, src=src)
            
            if df is not None and not df.empty:
                logger.info(f"✅ 获取实时成交数据: {len(df)}条记录")
                return df
            else:
                logger.warning(f"⚠️ 未获取到{ts_code}的成交数据")
                return None
                
        except Exception as e:
            logger.error(f"❌ 获取实时成交数据失败: {e}")
            return None
    
    def analyze_realtime_quote(self, quote_df: pd.DataFrame) -> Dict:
        """
        分析实时行情数据
        
        Args:
            quote_df: realtime_quote返回的DataFrame
            
        Returns:
            分析结果字典
        """
        if quote_df is None or quote_df.empty:
            return {}
        
        try:
            row = quote_df.iloc[0]
            
            price = float(row.get('price', 0))
            pre_close = float(row.get('pre_close', 0))
            change_pct = ((price - pre_close) / pre_close * 100) if pre_close > 0 else 0
            
            volume = int(row.get('volume', 0))
            amount = float(row.get('amount', 0))
            
            # 计算买卖盘力量
            bid = float(row.get('bid', 0))
            ask = float(row.get('ask', 0))
            bid_ask_ratio = (bid / ask) if ask > 0 else 1.0
            
            # 计算委买委卖总量
            total_bid_vol = sum([
                float(row.get(f'b{i}_v', 0)) for i in range(1, 6)
            ])
            total_ask_vol = sum([
                float(row.get(f'a{i}_v', 0)) for i in range(1, 6)
            ])
            
            result = {
                'ts_code': row.get('ts_code'),
                'name': row.get('name'),
                'price': price,
                'pre_close': pre_close,
                'change_pct': round(change_pct, 2),
                'volume': volume,
                'amount': amount,
                'high': float(row.get('high', 0)),
                'low': float(row.get('low', 0)),
                'bid': bid,
                'ask': ask,
                'bid_ask_ratio': round(bid_ask_ratio, 4),
                'total_bid_vol': total_bid_vol,
                'total_ask_vol': total_ask_vol,
                'buy_sell_pressure': round((total_bid_vol / total_ask_vol) if total_ask_vol > 0 else 1.0, 2),
                'timestamp': row.get('time', datetime.now().strftime('%H:%M:%S'))
            }
            
            logger.info(f"📊 {result['name']}({result['ts_code']}) "
                       f"现价:{result['price']} 涨跌:{result['change_pct']}%")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ 分析实时行情失败: {e}")
            return {}
    
    def analyze_tick_data(self, tick_df: pd.DataFrame) -> Dict:
        """
        分析分笔成交数据
        
        Args:
            tick_df: realtime_tick返回的DataFrame
            
        Returns:
            分析结果字典
        """
        if tick_df is None or tick_df.empty:
            return {}
        
        try:
            # 统计买卖盘
            buy_count = len(tick_df[tick_df['type'] == '买盘'])
            sell_count = len(tick_df[tick_df['type'] == '卖盘'])
            neutral_count = len(tick_df[tick_df['type'] == '中性'])
            
            # 计算买卖额
            buy_amount = tick_df[tick_df['type'] == '买盘']['amount'].sum()
            sell_amount = tick_df[tick_df['type'] == '卖盘']['amount'].sum()
            
            # 大单统计（单笔超过50万）
            large_threshold = 500000
            large_buy = len(tick_df[(tick_df['type'] == '买盘') & (tick_df['amount'] >= large_threshold)])
            large_sell = len(tick_df[(tick_df['type'] == '卖盘') & (tick_df['amount'] >= large_threshold)])
            
            result = {
                'total_ticks': len(tick_df),
                'buy_count': buy_count,
                'sell_count': sell_count,
                'neutral_count': neutral_count,
                'buy_sell_ratio': round(buy_count / sell_count, 2) if sell_count > 0 else 0,
                'buy_amount': buy_amount,
                'sell_amount': sell_amount,
                'buy_sell_amount_ratio': round(buy_amount / sell_amount, 2) if sell_amount > 0 else 0,
                'large_buy_count': large_buy,
                'large_sell_count': large_sell,
                'latest_price': float(tick_df.iloc[-1]['price']),
                'price_trend': '上涨' if float(tick_df.iloc[-1]['change']) > 0 else '下跌' if float(tick_df.iloc[-1]['change']) < 0 else '平稳'
            }
            
            logger.info(f"📈 成交分析: 买{buy_count}笔/{sell_count}笔卖, "
                       f"买卖比:{result['buy_sell_ratio']}, 大单买{large_buy}/卖{large_sell}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ 分析分笔数据失败: {e}")
            return {}
    
    def get_market_heat(self, ts_codes: List[str]) -> Dict:
        """
        获取市场热度分析（基于多只股票实时数据）
        
        Args:
            ts_codes: 股票代码列表
            
        Returns:
            市场热度分析结果
        """
        if not ts_codes:
            return {}
        
        try:
            # 批量获取实时数据（新浪支持多股票）
            codes_str = ','.join(ts_codes[:50])  # 限制最多50只
            df = self.get_realtime_quote(codes_str, src='sina')
            
            if df is None or df.empty:
                return {}
            
            # 统计涨跌情况
            df['change_pct'] = ((df['price'] - df['pre_close']) / df['pre_close'] * 100)
            
            up_count = len(df[df['change_pct'] > 0])
            down_count = len(df[df['change_pct'] < 0])
            flat_count = len(df[df['change_pct'] == 0])
            
            avg_change = df['change_pct'].mean()
            total_amount = df['amount'].sum()
            
            result = {
                'total_stocks': len(df),
                'up_count': up_count,
                'down_count': down_count,
                'flat_count': flat_count,
                'up_ratio': round(up_count / len(df) * 100, 2),
                'avg_change_pct': round(avg_change, 2),
                'total_amount': total_amount,
                'market_sentiment': '偏多' if avg_change > 0 else '偏空' if avg_change < 0 else '平衡',
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"🔥 市场热度: {result['up_count']}涨/{result['down_count']}跌, "
                       f"涨跌比:{result['up_ratio']}%, 情绪:{result['market_sentiment']}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ 获取市场热度失败: {e}")
            return {}


# 全局监控器实例
_realtime_monitor = None


def get_realtime_monitor() -> RealtimeMonitor:
    """获取全局实时监控器实例"""
    global _realtime_monitor
    if _realtime_monitor is None:
        _realtime_monitor = RealtimeMonitor()
    return _realtime_monitor


# ==================== 便捷函数 ====================

def get_stock_realtime_quote(ts_code: str, src: str = 'sina') -> Optional[Dict]:
    """获取股票实时行情"""
    monitor = get_realtime_monitor()
    df = monitor.get_realtime_quote(ts_code, src=src)
    if df is not None and not df.empty:
        return monitor.analyze_realtime_quote(df)
    return None


def get_stock_tick_analysis(ts_code: str, src: str = 'sina') -> Optional[Dict]:
    """获取股票分笔成交分析"""
    monitor = get_realtime_monitor()
    df = monitor.get_realtime_tick(ts_code, src=src)
    if df is not None and not df.empty:
        return monitor.analyze_tick_data(df)
    return None
