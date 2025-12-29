"""
市场情绪数据获取和计算模块
提供ARBR指标、恐慌贪婪指数、涨跌停统计等市场情绪分析功能
"""

import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import time

from backend.utils.logging_config import get_logger

logger = get_logger("dataflows.sentiment")


class MarketSentimentFetcher:
    """市场情绪数据获取和计算类"""

    def __init__(self):
        self.arbr_period = 26  # ARBR计算周期
        self._cache = {}
        self._cache_time = {}
        self._cache_ttl = 300  # 5分钟缓存
        logger.info("[市场情绪] 数据获取器初始化完成")

    def _get_cached(self, key: str) -> Optional[Any]:
        """获取缓存数据"""
        if key in self._cache:
            cache_time = self._cache_time.get(key, 0)
            if time.time() - cache_time < self._cache_ttl:
                return self._cache[key]
        return None

    def _set_cache(self, key: str, value: Any):
        """设置缓存"""
        self._cache[key] = value
        self._cache_time[key] = time.time()

    def get_market_sentiment(self) -> Dict[str, Any]:
        """
        获取市场整体情绪数据

        Returns:
            包含市场情绪各项指标的字典
        """
        cache_key = "market_sentiment"
        cached = self._get_cached(cache_key)
        if cached:
            return cached

        logger.info("[市场情绪] 开始获取市场情绪数据...")

        sentiment_data = {
            "success": False,
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "market_stats": {},
            "limit_stats": {},
            "fear_greed_index": {},
            "north_flow": {},
            "margin_trading": {}
        }

        try:
            # 1. 获取市场涨跌统计
            logger.info("[市场情绪] 获取市场涨跌统计...")
            market_stats = self._get_market_stats()
            if market_stats:
                sentiment_data["market_stats"] = market_stats

            # 2. 获取涨跌停统计
            logger.info("[市场情绪] 获取涨跌停统计...")
            limit_stats = self._get_limit_stats()
            if limit_stats:
                sentiment_data["limit_stats"] = limit_stats

            # 3. 计算恐慌贪婪指数
            logger.info("[市场情绪] 计算恐慌贪婪指数...")
            fear_greed = self._calculate_fear_greed_index(market_stats, limit_stats)
            if fear_greed:
                sentiment_data["fear_greed_index"] = fear_greed

            # 4. 获取北向资金
            logger.info("[市场情绪] 获取北向资金...")
            north_flow = self._get_north_flow()
            if north_flow:
                sentiment_data["north_flow"] = north_flow

            # 5. 获取融资融券数据
            logger.info("[市场情绪] 获取融资融券数据...")
            margin_data = self._get_margin_trading()
            if margin_data:
                sentiment_data["margin_trading"] = margin_data

            sentiment_data["success"] = True
            self._set_cache(cache_key, sentiment_data)
            logger.info("[市场情绪] 数据获取完成")

        except Exception as e:
            logger.error(f"[市场情绪] 获取数据失败: {e}")
            sentiment_data["error"] = str(e)

        return sentiment_data

    def _get_market_stats(self) -> Dict[str, Any]:
        """获取市场涨跌统计（优先TDX，降级到AKShare）"""
        # 优先使用TDX（快得多，约2-3秒 vs AKShare的1分钟）
        try:
            from backend.dataflows.providers.tdx_native_provider import get_tdx_native_provider
            tdx = get_tdx_native_provider()
            if tdx and tdx.is_available():
                result = self._get_market_stats_from_tdx(tdx)
                if result:
                    logger.info("[市场情绪] TDX获取市场统计成功")
                    return result
        except Exception as e:
            logger.debug(f"[市场情绪] TDX获取市场统计失败: {e}")

        # 降级到AKShare（慢，约1分钟）
        logger.info("[市场情绪] 降级到AKShare获取市场统计...")
        return self._get_market_stats_from_akshare()

    def _get_market_stats_from_tdx(self, tdx) -> Dict[str, Any]:
        """从TDX获取市场涨跌统计"""
        try:
            # 获取所有股票代码
            all_stocks = []

            # 深圳市场
            for start in range(0, 6000, 1000):
                stocks = tdx.get_stock_list(0, start)
                if not stocks:
                    break
                # 只保留A股（00/30开头）
                for s in stocks:
                    code = s.get('code', '')
                    if code.startswith(('00', '30')):
                        all_stocks.append(code)
                if len(stocks) < 1000:
                    break

            # 上海市场
            for start in range(0, 6000, 1000):
                stocks = tdx.get_stock_list(1, start)
                if not stocks:
                    break
                # 只保留A股（60/68开头）
                for s in stocks:
                    code = s.get('code', '')
                    if code.startswith(('60', '68')):
                        all_stocks.append(code)
                if len(stocks) < 1000:
                    break

            if not all_stocks:
                return {}

            logger.info(f"[市场情绪] TDX获取到 {len(all_stocks)} 只A股")

            # 批量获取行情（每次最多80只）
            up_count = 0
            down_count = 0
            flat_count = 0
            up_5_pct = 0
            up_3_pct = 0
            down_3_pct = 0
            down_5_pct = 0
            total_count = 0

            batch_size = 80
            for i in range(0, len(all_stocks), batch_size):
                batch = all_stocks[i:i+batch_size]
                quotes = tdx.get_realtime_quotes(batch)

                for q in quotes:
                    change_pct = q.get('change_pct', 0) or 0
                    total_count += 1

                    if change_pct > 0:
                        up_count += 1
                        if change_pct >= 5:
                            up_5_pct += 1
                        elif change_pct >= 3:
                            up_3_pct += 1
                    elif change_pct < 0:
                        down_count += 1
                        if change_pct <= -5:
                            down_5_pct += 1
                        elif change_pct <= -3:
                            down_3_pct += 1
                    else:
                        flat_count += 1

            if total_count == 0:
                return {}

            # 计算市场情绪得分
            sentiment_score = (up_count - down_count) / total_count * 100

            # 解读市场情绪
            if sentiment_score > 30:
                sentiment_level = "极度乐观"
            elif sentiment_score > 10:
                sentiment_level = "偏多"
            elif sentiment_score > -10:
                sentiment_level = "中性"
            elif sentiment_score > -30:
                sentiment_level = "偏空"
            else:
                sentiment_level = "极度悲观"

            return {
                "total_count": total_count,
                "up_count": up_count,
                "down_count": down_count,
                "flat_count": flat_count,
                "up_ratio": round(up_count / total_count * 100, 2),
                "down_ratio": round(down_count / total_count * 100, 2),
                "up_5_pct": up_5_pct,
                "up_3_pct": up_3_pct,
                "down_3_pct": down_3_pct,
                "down_5_pct": down_5_pct,
                "sentiment_score": round(sentiment_score, 2),
                "sentiment_level": sentiment_level,
                "source": "tdx"
            }

        except Exception as e:
            logger.error(f"[市场情绪] TDX获取市场统计失败: {e}")
            return {}

    def _get_market_stats_from_akshare(self) -> Dict[str, Any]:
        """从AKShare获取市场涨跌统计（慢，约1分钟）"""
        try:
            df = ak.stock_zh_a_spot_em()
            if df is None or df.empty:
                return {}

            total_count = len(df)
            up_count = len(df[df['涨跌幅'] > 0])
            down_count = len(df[df['涨跌幅'] < 0])
            flat_count = total_count - up_count - down_count

            # 计算涨跌幅分布
            up_5_pct = len(df[df['涨跌幅'] >= 5])
            up_3_pct = len(df[(df['涨跌幅'] >= 3) & (df['涨跌幅'] < 5)])
            down_3_pct = len(df[(df['涨跌幅'] <= -3) & (df['涨跌幅'] > -5)])
            down_5_pct = len(df[df['涨跌幅'] <= -5])

            # 计算市场情绪得分
            sentiment_score = (up_count - down_count) / total_count * 100

            # 解读市场情绪
            if sentiment_score > 30:
                sentiment_level = "极度乐观"
            elif sentiment_score > 10:
                sentiment_level = "偏多"
            elif sentiment_score > -10:
                sentiment_level = "中性"
            elif sentiment_score > -30:
                sentiment_level = "偏空"
            else:
                sentiment_level = "极度悲观"

            return {
                "total_count": total_count,
                "up_count": up_count,
                "down_count": down_count,
                "flat_count": flat_count,
                "up_ratio": round(up_count / total_count * 100, 2),
                "down_ratio": round(down_count / total_count * 100, 2),
                "up_5_pct": up_5_pct,
                "up_3_pct": up_3_pct,
                "down_3_pct": down_3_pct,
                "down_5_pct": down_5_pct,
                "sentiment_score": round(sentiment_score, 2),
                "sentiment_level": sentiment_level,
                "source": "akshare"
            }

        except Exception as e:
            logger.error(f"[市场情绪] AKShare获取市场统计失败: {e}")
            return {}

    def _get_limit_stats(self) -> Dict[str, Any]:
        """获取涨跌停统计"""
        try:
            today = datetime.now().strftime('%Y%m%d')

            # 获取涨停股票
            limit_up_count = 0
            limit_up_stocks = []
            try:
                limit_up_df = ak.stock_zt_pool_em(date=today)
                if limit_up_df is not None and not limit_up_df.empty:
                    limit_up_count = len(limit_up_df)
                    # 获取前10只涨停股
                    for idx, row in limit_up_df.head(10).iterrows():
                        limit_up_stocks.append({
                            "code": row.get('代码', ''),
                            "name": row.get('名称', ''),
                            "change_pct": float(row.get('涨跌幅', 0) or 0),
                            "first_time": str(row.get('首次封板时间', ''))
                        })
            except Exception as e:
                logger.warning(f"获取涨停数据失败: {e}")

            # 获取跌停股票
            limit_down_count = 0
            limit_down_stocks = []
            try:
                limit_down_df = ak.stock_zt_pool_dtgc_em(date=today)
                if limit_down_df is not None and not limit_down_df.empty:
                    limit_down_count = len(limit_down_df)
                    # 获取前10只跌停股
                    for idx, row in limit_down_df.head(10).iterrows():
                        limit_down_stocks.append({
                            "code": row.get('代码', ''),
                            "name": row.get('名称', ''),
                            "change_pct": float(row.get('涨跌幅', 0) or 0)
                        })
            except Exception as e:
                logger.warning(f"获取跌停数据失败: {e}")

            # 计算涨跌停比例
            total_limit = limit_up_count + limit_down_count
            if total_limit > 0:
                limit_ratio = limit_up_count / total_limit * 100
            else:
                limit_ratio = 50

            # 解读涨跌停情况
            if limit_ratio > 70:
                interpretation = "涨停股远多于跌停股，市场情绪火热"
            elif limit_ratio > 60:
                interpretation = "涨停股多于跌停股，市场情绪较好"
            elif limit_ratio > 40:
                interpretation = "涨跌停数量相当，市场情绪分化"
            elif limit_ratio > 30:
                interpretation = "跌停股多于涨停股，市场情绪较弱"
            else:
                interpretation = "跌停股远多于涨停股，市场情绪低迷"

            return {
                "limit_up_count": limit_up_count,
                "limit_down_count": limit_down_count,
                "limit_ratio": round(limit_ratio, 2),
                "interpretation": interpretation,
                "limit_up_stocks": limit_up_stocks,
                "limit_down_stocks": limit_down_stocks,
                "date": today
            }

        except Exception as e:
            logger.error(f"[市场情绪] 获取涨跌停统计失败: {e}")
            return {}

    def _calculate_fear_greed_index(self, market_stats: Dict, limit_stats: Dict) -> Dict[str, Any]:
        """
        计算市场恐慌贪婪指数

        综合考虑:
        - 涨跌家数比例 (权重40%)
        - 涨跌停比例 (权重30%)
        - 涨跌幅分布 (权重30%)
        """
        try:
            score = 50  # 基准分数
            factors = []

            # 1. 涨跌家数比例 (权重40%)
            if market_stats:
                up_ratio = market_stats.get("up_ratio", 50)
                # 将涨跌比例转换为0-100分
                up_score = up_ratio
                score += (up_score - 50) * 0.4
                factors.append(f"涨跌家数: 上涨{market_stats.get('up_count', 0)}家, 下跌{market_stats.get('down_count', 0)}家")

            # 2. 涨跌停比例 (权重30%)
            if limit_stats:
                limit_ratio = limit_stats.get("limit_ratio", 50)
                score += (limit_ratio - 50) * 0.3
                factors.append(f"涨跌停: 涨停{limit_stats.get('limit_up_count', 0)}家, 跌停{limit_stats.get('limit_down_count', 0)}家")

            # 3. 涨跌幅分布 (权重30%)
            if market_stats:
                up_5 = market_stats.get("up_5_pct", 0)
                down_5 = market_stats.get("down_5_pct", 0)
                total = market_stats.get("total_count", 1)
                extreme_ratio = (up_5 - down_5) / total * 100
                score += extreme_ratio * 0.3
                factors.append(f"极端涨跌: 涨5%以上{up_5}家, 跌5%以上{down_5}家")

            # 确保分数在0-100之间
            score = max(0, min(100, score))

            # 解读恐慌贪婪指数
            if score >= 75:
                level = "极度贪婪"
                interpretation = "市场情绪极度乐观，投资者贪婪，需警惕回调风险"
                color = "#ff4444"
            elif score >= 60:
                level = "贪婪"
                interpretation = "市场情绪乐观，投资者偏向贪婪"
                color = "#ff8800"
            elif score >= 40:
                level = "中性"
                interpretation = "市场情绪中性，投资者相对理性"
                color = "#888888"
            elif score >= 25:
                level = "恐慌"
                interpretation = "市场情绪悲观，投资者偏向恐慌"
                color = "#4488ff"
            else:
                level = "极度恐慌"
                interpretation = "市场情绪极度悲观，投资者恐慌，可能存在超卖机会"
                color = "#0044ff"

            return {
                "score": round(score, 1),
                "level": level,
                "interpretation": interpretation,
                "color": color,
                "factors": factors
            }

        except Exception as e:
            logger.error(f"[市场情绪] 计算恐慌贪婪指数失败: {e}")
            return {}

    def _get_north_flow(self) -> Dict[str, Any]:
        """获取北向资金流向"""
        try:
            df = ak.stock_hsgt_fund_flow_summary_em()
            if df is None or df.empty:
                return {}

            latest = df.iloc[0]

            north_net = float(latest.get('北向资金-成交净买额', 0) or 0)

            # 解读北向资金
            if north_net > 50:
                interpretation = "北向资金大幅流入，外资看好A股"
            elif north_net > 0:
                interpretation = "北向资金小幅流入，外资偏乐观"
            elif north_net > -50:
                interpretation = "北向资金小幅流出，外资偏谨慎"
            else:
                interpretation = "北向资金大幅流出，外资看空A股"

            return {
                "date": str(latest.get('日期', '')),
                "north_net_inflow": north_net,
                "hgt_net_inflow": float(latest.get('沪股通-成交净买额', 0) or 0),
                "sgt_net_inflow": float(latest.get('深股通-成交净买额', 0) or 0),
                "interpretation": interpretation
            }

        except Exception as e:
            logger.error(f"[市场情绪] 获取北向资金失败: {e}")
            return {}

    def _get_margin_trading(self) -> Dict[str, Any]:
        """获取融资融券数据（沪深两市汇总）"""
        try:
            margin_balance = 0
            short_balance = 0
            margin_buy = 0
            latest_date = ''
            
            # 方案1: 尝试获取上交所融资融券数据
            try:
                df_sse = ak.stock_margin_sse()
                if df_sse is not None and not df_sse.empty:
                    latest_sse = df_sse.iloc[0]
                    # 列名: ['信用交易日期', '融资余额', '融资买入额', '融券余量', '融券余量金额', '融券卖出量', '融资融券余额']
                    margin_balance += float(latest_sse.get('融资余额', 0) or 0)
                    short_balance += float(latest_sse.get('融券余量金额', 0) or 0)
                    margin_buy += float(latest_sse.get('融资买入额', 0) or 0)
                    latest_date = str(latest_sse.get('信用交易日期', ''))
                    logger.info(f"[市场情绪] 上交所融资融券数据获取成功，日期: {latest_date}")
            except Exception as e:
                logger.warning(f"[市场情绪] 获取上交所融资融券数据失败: {e}")
            
            # 方案2: 尝试获取深交所融资融券数据
            try:
                df_szse = ak.stock_margin_szse()
                if df_szse is not None and not df_szse.empty:
                    latest_szse = df_szse.iloc[0]
                    # 列名: ['融资买入额', '融资余额', '融券卖出量', '融券余量', '融券余额', '融资融券余额']
                    # 注意：深交所数据单位可能是亿元，需要转换
                    szse_margin = float(latest_szse.get('融资余额', 0) or 0)
                    szse_short = float(latest_szse.get('融券余额', 0) or 0)
                    szse_buy = float(latest_szse.get('融资买入额', 0) or 0)
                    
                    # 如果数值很小（小于10000），说明单位是亿元，需要转换为元
                    if szse_margin < 10000:
                        szse_margin *= 100000000  # 亿元转元
                        szse_short *= 100000000
                        szse_buy *= 100000000
                    
                    margin_balance += szse_margin
                    short_balance += szse_short
                    margin_buy += szse_buy
                    logger.info(f"[市场情绪] 深交所融资融券数据获取成功")
            except Exception as e:
                logger.warning(f"[市场情绪] 获取深交所融资融券数据失败: {e}")
            
            if margin_balance == 0 and short_balance == 0:
                logger.warning("[市场情绪] 未能获取到融资融券数据")
                return {}

            # 解读融资融券
            if margin_balance > short_balance * 10:
                interpretation = "融资余额远大于融券余额，投资者看多情绪强"
            elif margin_balance > short_balance * 3:
                interpretation = "融资余额大于融券余额，投资者偏看多"
            else:
                interpretation = "融资融券相对平衡"

            return {
                "date": latest_date,
                "margin_balance": margin_balance,
                "short_balance": short_balance,
                "margin_buy": margin_buy,
                "margin_repay": 0,  # 暂无此数据
                "interpretation": interpretation,
                "margin_balance_yi": round(margin_balance / 100000000, 2),  # 转换为亿元便于显示
                "short_balance_yi": round(short_balance / 100000000, 2)
            }

        except Exception as e:
            logger.error(f"[市场情绪] 获取融资融券数据失败: {e}")
            return {}

    def get_stock_sentiment(self, stock_code: str) -> Dict[str, Any]:
        """
        获取个股情绪数据

        Args:
            stock_code: 股票代码

        Returns:
            包含个股情绪指标的字典
        """
        logger.info(f"[市场情绪] 获取个股情绪数据: {stock_code}")

        sentiment_data = {
            "success": False,
            "stock_code": stock_code,
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "arbr_data": {},
            "turnover_data": {},
            "volume_analysis": {}
        }

        try:
            # 1. 计算ARBR指标
            logger.info(f"[市场情绪] 计算ARBR指标: {stock_code}")
            arbr_data = self._calculate_arbr(stock_code)
            if arbr_data:
                sentiment_data["arbr_data"] = arbr_data

            # 2. 获取换手率数据
            logger.info(f"[市场情绪] 获取换手率: {stock_code}")
            turnover_data = self._get_stock_turnover(stock_code)
            if turnover_data:
                sentiment_data["turnover_data"] = turnover_data

            # 3. 成交量分析
            logger.info(f"[市场情绪] 分析成交量: {stock_code}")
            volume_analysis = self._analyze_volume(stock_code)
            if volume_analysis:
                sentiment_data["volume_analysis"] = volume_analysis

            sentiment_data["success"] = True
            logger.info(f"[市场情绪] 个股情绪数据获取完成: {stock_code}")

        except Exception as e:
            logger.error(f"[市场情绪] 获取个股情绪数据失败: {e}")
            sentiment_data["error"] = str(e)

        return sentiment_data

    def _calculate_arbr(self, stock_code: str) -> Dict[str, Any]:
        """
        计算ARBR指标

        AR = (N日内(H-O)之和 / N日内(O-L)之和) × 100
        BR = (N日内(H-CY)之和 / N日内(CY-L)之和) × 100
        """
        try:
            # 获取历史数据
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=150)).strftime('%Y%m%d')

            df = ak.stock_zh_a_hist(
                symbol=stock_code,
                period="daily",
                start_date=start_date,
                end_date=end_date,
                adjust="qfq"
            )

            if df is None or df.empty:
                return {}

            # 重命名列
            df = df.rename(columns={
                '日期': 'date',
                '开盘': 'open',
                '收盘': 'close',
                '最高': 'high',
                '最低': 'low',
                '成交量': 'volume'
            })

            # 计算各项差值
            df['HO'] = df['high'] - df['open']
            df['OL'] = df['open'] - df['low']
            df['HCY'] = df['high'] - df['close'].shift(1)
            df['CYL'] = df['close'].shift(1) - df['low']

            # 计算AR指标
            df['AR'] = (df['HO'].rolling(window=self.arbr_period).sum() /
                       df['OL'].rolling(window=self.arbr_period).sum()) * 100

            # 计算BR指标
            df['BR'] = (df['HCY'].rolling(window=self.arbr_period).sum() /
                       df['CYL'].rolling(window=self.arbr_period).sum()) * 100

            # 处理无穷大和空值
            df['AR'] = df['AR'].replace([np.inf, -np.inf], np.nan)
            df['BR'] = df['BR'].replace([np.inf, -np.inf], np.nan)
            df = df.dropna(subset=['AR', 'BR'])

            if df.empty:
                return {}

            # 获取最新值
            latest = df.iloc[-1]
            ar_value = float(latest['AR'])
            br_value = float(latest['BR'])

            # 解读ARBR
            interpretation = self._interpret_arbr(ar_value, br_value)

            # 生成交易信号
            signals = self._generate_arbr_signals(ar_value, br_value)

            return {
                "latest_ar": round(ar_value, 2),
                "latest_br": round(br_value, 2),
                "interpretation": interpretation,
                "signals": signals,
                "period": self.arbr_period,
                "calculation_date": str(latest['date'])
            }

        except Exception as e:
            logger.error(f"[市场情绪] 计算ARBR失败: {e}")
            return {}

    def _interpret_arbr(self, ar_value: float, br_value: float) -> List[str]:
        """解读ARBR数值"""
        interpretation = []

        # AR指标解读
        if ar_value > 180:
            interpretation.append("AR极度超买（>180），市场过热，风险极高")
        elif ar_value > 150:
            interpretation.append("AR超买（>150），市场情绪过热，注意回调风险")
        elif ar_value < 40:
            interpretation.append("AR极度超卖（<40），市场过冷，可能存在机会")
        elif ar_value < 70:
            interpretation.append("AR超卖（<70），市场情绪低迷，可关注反弹机会")
        else:
            interpretation.append(f"AR处于正常区间（{ar_value:.2f}），市场情绪相对平稳")

        # BR指标解读
        if br_value > 400:
            interpretation.append("BR极度超买（>400），投机情绪过热，警惕泡沫")
        elif br_value > 300:
            interpretation.append("BR超买（>300），投机情绪旺盛，注意风险")
        elif br_value < 30:
            interpretation.append("BR极度超卖（<30），投机情绪冰点，可能触底")
        elif br_value < 50:
            interpretation.append("BR超卖（<50），投机情绪低迷，关注企稳信号")
        else:
            interpretation.append(f"BR处于正常区间（{br_value:.2f}），投机情绪适中")

        return interpretation

    def _generate_arbr_signals(self, ar_value: float, br_value: float) -> Dict[str, Any]:
        """生成ARBR交易信号"""
        signals = []
        signal_strength = 0

        if ar_value > 150:
            signals.append("AR卖出信号")
            signal_strength -= 1
        elif ar_value < 70:
            signals.append("AR买入信号")
            signal_strength += 1

        if br_value > 300:
            signals.append("BR卖出信号")
            signal_strength -= 1
        elif br_value < 50:
            signals.append("BR买入信号")
            signal_strength += 1

        if signal_strength >= 2:
            overall = "强烈买入信号"
        elif signal_strength == 1:
            overall = "买入信号"
        elif signal_strength == -1:
            overall = "卖出信号"
        elif signal_strength <= -2:
            overall = "强烈卖出信号"
        else:
            overall = "中性信号"

        return {
            "individual_signals": signals if signals else ["中性"],
            "overall_signal": overall,
            "signal_strength": signal_strength
        }

    def _get_stock_turnover(self, stock_code: str) -> Dict[str, Any]:
        """获取个股换手率（优先TDX，降级到AKShare单股票API）"""
        try:
            turnover_rate = 0

            # 优先使用TDX（最快最可靠）
            try:
                from backend.dataflows.providers.tdx_native_provider import get_tdx_native_provider
                tdx = get_tdx_native_provider()
                if tdx and tdx.is_available():
                    quote = tdx.get_realtime_quote(stock_code)
                    if quote:
                        # TDX返回的数据中可能包含换手率
                        turnover_rate = float(quote.get('turnover_rate', 0) or 0)
                        if turnover_rate > 0:
                            logger.debug(f"TDX获取换手率成功: {stock_code} = {turnover_rate}%")
            except Exception as e:
                logger.debug(f"TDX获取换手率失败: {e}")

            # 如果TDX没有换手率数据，降级到AKShare
            if turnover_rate == 0:
                df = ak.stock_bid_ask_em(symbol=stock_code)
                if df is not None and not df.empty:
                    # 转换为字典
                    data = {}
                    for _, row in df.iterrows():
                        item = row['item']
                        value = row['value']
                        data[item] = value

                    # 安全转换
                    def safe_float(val, default=0):
                        if val is None:
                            return default
                        if isinstance(val, (int, float)):
                            return float(val)
                        if isinstance(val, str):
                            val = val.strip().replace(',', '')
                            if val == '' or val == '-' or '--' in val:
                                return default
                            try:
                                return float(val)
                            except ValueError:
                                return default
                        return default

                    turnover_rate = safe_float(data.get('换手'))

            # 解读换手率
            if turnover_rate > 20:
                interpretation = "换手率极高（>20%），资金活跃度极高，可能存在炒作"
            elif turnover_rate > 10:
                interpretation = "换手率较高（>10%），交易活跃"
            elif turnover_rate > 5:
                interpretation = "换手率正常（5%-10%），交易适中"
            elif turnover_rate > 2:
                interpretation = "换手率偏低（2%-5%），交易相对清淡"
            else:
                interpretation = "换手率很低（<2%），交易清淡"

            return {
                "turnover_rate": turnover_rate,
                "interpretation": interpretation
            }

        except Exception as e:
            logger.error(f"[市场情绪] 获取换手率失败: {e}")
            return {}

    def _analyze_volume(self, stock_code: str) -> Dict[str, Any]:
        """分析成交量"""
        try:
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')

            df = ak.stock_zh_a_hist(
                symbol=stock_code,
                period="daily",
                start_date=start_date,
                end_date=end_date,
                adjust="qfq"
            )

            if df is None or df.empty:
                return {}

            # 计算成交量统计
            volumes = df['成交量'].values
            avg_volume = np.mean(volumes[:-1]) if len(volumes) > 1 else volumes[0]
            latest_volume = volumes[-1]

            # 计算量比
            volume_ratio = latest_volume / avg_volume if avg_volume > 0 else 1

            # 解读量比
            if volume_ratio > 3:
                interpretation = "量比极高（>3），成交异常放大，关注资金动向"
            elif volume_ratio > 1.5:
                interpretation = "量比较高（>1.5），成交活跃"
            elif volume_ratio > 0.8:
                interpretation = "量比正常，成交平稳"
            elif volume_ratio > 0.5:
                interpretation = "量比偏低，成交萎缩"
            else:
                interpretation = "量比极低（<0.5），成交极度萎缩"

            return {
                "latest_volume": int(latest_volume),
                "avg_volume": int(avg_volume),
                "volume_ratio": round(volume_ratio, 2),
                "interpretation": interpretation
            }

        except Exception as e:
            logger.error(f"[市场情绪] 分析成交量失败: {e}")
            return {}


# 单例实例
market_sentiment_fetcher = MarketSentimentFetcher()
