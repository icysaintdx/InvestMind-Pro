"""
板块轮动数据获取模块
使用AKShare获取行业板块和概念板块数据
"""

import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import time

from backend.utils.logging_config import get_logger

logger = get_logger("dataflows.sector_rotation")


class SectorRotationDataFetcher:
    """板块轮动数据获取器"""

    def __init__(self):
        self.max_retries = 3
        self.retry_delay = 2
        self.request_delay = 0.5
        self._cache = {}
        self._cache_time = {}
        self._cache_ttl = 300  # 5分钟缓存
        logger.info("[板块轮动] 数据获取器初始化完成")

    def _safe_request(self, func, *args, **kwargs):
        """安全的请求函数，包含重试机制"""
        for attempt in range(self.max_retries):
            try:
                result = func(*args, **kwargs)
                time.sleep(self.request_delay)
                return result
            except Exception as e:
                if attempt < self.max_retries - 1:
                    logger.warning(f"请求失败，{self.retry_delay}秒后重试... (尝试 {attempt + 1}/{self.max_retries})")
                    time.sleep(self.retry_delay)
                else:
                    logger.error(f"请求失败，已达最大重试次数: {e}")
                    raise e

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

    def get_industry_sectors(self) -> Dict[str, Any]:
        """
        获取行业板块实时行情

        Returns:
            包含行业板块数据的字典
        """
        cache_key = "industry_sectors"
        cached = self._get_cached(cache_key)
        if cached:
            return cached

        try:
            logger.info("[板块轮动] 获取行业板块行情...")
            df = self._safe_request(ak.stock_board_industry_name_em)

            if df is None or df.empty:
                return {"success": False, "data": [], "message": "无数据"}

            sectors = []
            for idx, row in df.iterrows():
                sector_name = row.get('板块名称', '')
                if sector_name:
                    sectors.append({
                        "name": sector_name,
                        "code": row.get('板块代码', ''),
                        "change_pct": float(row.get('涨跌幅', 0) or 0),
                        "turnover": float(row.get('换手率', 0) or 0),
                        "total_market_cap": float(row.get('总市值', 0) or 0),
                        "top_stock": row.get('领涨股票', ''),
                        "top_stock_change": float(row.get('领涨股票-涨跌幅', 0) or 0),
                        "up_count": int(row.get('上涨家数', 0) or 0),
                        "down_count": int(row.get('下跌家数', 0) or 0),
                        "latest_price": float(row.get('最新价', 0) or 0),
                        "volume": float(row.get('成交量', 0) or 0),
                        "amount": float(row.get('成交额', 0) or 0)
                    })

            result = {
                "success": True,
                "data": sectors,
                "count": len(sectors),
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

            self._set_cache(cache_key, result)
            logger.info(f"[板块轮动] 获取到 {len(sectors)} 个行业板块")
            return result

        except Exception as e:
            logger.error(f"[板块轮动] 获取行业板块失败: {e}")
            return {"success": False, "data": [], "message": str(e)}

    def get_concept_sectors(self) -> Dict[str, Any]:
        """
        获取概念板块实时行情

        Returns:
            包含概念板块数据的字典
        """
        cache_key = "concept_sectors"
        cached = self._get_cached(cache_key)
        if cached:
            return cached

        try:
            logger.info("[板块轮动] 获取概念板块行情...")
            df = self._safe_request(ak.stock_board_concept_name_em)

            if df is None or df.empty:
                return {"success": False, "data": [], "message": "无数据"}

            concepts = []
            for idx, row in df.iterrows():
                concept_name = row.get('板块名称', '')
                if concept_name:
                    concepts.append({
                        "name": concept_name,
                        "code": row.get('板块代码', ''),
                        "change_pct": float(row.get('涨跌幅', 0) or 0),
                        "turnover": float(row.get('换手率', 0) or 0),
                        "total_market_cap": float(row.get('总市值', 0) or 0),
                        "top_stock": row.get('领涨股票', ''),
                        "top_stock_change": float(row.get('领涨股票-涨跌幅', 0) or 0),
                        "up_count": int(row.get('上涨家数', 0) or 0),
                        "down_count": int(row.get('下跌家数', 0) or 0),
                        "latest_price": float(row.get('最新价', 0) or 0),
                        "volume": float(row.get('成交量', 0) or 0),
                        "amount": float(row.get('成交额', 0) or 0)
                    })

            result = {
                "success": True,
                "data": concepts,
                "count": len(concepts),
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

            self._set_cache(cache_key, result)
            logger.info(f"[板块轮动] 获取到 {len(concepts)} 个概念板块")
            return result

        except Exception as e:
            logger.error(f"[板块轮动] 获取概念板块失败: {e}")
            return {"success": False, "data": [], "message": str(e)}

    def get_sector_fund_flow(self, indicator: str = "今日") -> Dict[str, Any]:
        """
        获取行业资金流向

        Args:
            indicator: 时间周期，可选 "今日", "5日", "10日"

        Returns:
            包含资金流向数据的字典
        """
        cache_key = f"sector_fund_flow_{indicator}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached

        try:
            logger.info(f"[板块轮动] 获取行业资金流向 ({indicator})...")
            df = self._safe_request(ak.stock_sector_fund_flow_rank, indicator=indicator)

            if df is None or df.empty:
                return {"success": False, "data": [], "message": "无数据"}

            fund_flow = []
            for idx, row in df.iterrows():
                fund_flow.append({
                    "sector": row.get('名称', ''),
                    "change_pct": float(row.get('今日涨跌幅', 0) or 0),
                    "main_net_inflow": float(row.get('今日主力净流入-净额', 0) or 0),
                    "main_net_inflow_pct": float(row.get('今日主力净流入-净占比', 0) or 0),
                    "super_large_net_inflow": float(row.get('今日超大单净流入-净额', 0) or 0),
                    "super_large_net_inflow_pct": float(row.get('今日超大单净流入-净占比', 0) or 0),
                    "large_net_inflow": float(row.get('今日大单净流入-净额', 0) or 0),
                    "large_net_inflow_pct": float(row.get('今日大单净流入-净占比', 0) or 0),
                    "medium_net_inflow": float(row.get('今日中单净流入-净额', 0) or 0),
                    "small_net_inflow": float(row.get('今日小单净流入-净额', 0) or 0)
                })

            result = {
                "success": True,
                "data": fund_flow,
                "count": len(fund_flow),
                "indicator": indicator,
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

            self._set_cache(cache_key, result)
            logger.info(f"[板块轮动] 获取到 {len(fund_flow)} 条资金流向数据")
            return result

        except Exception as e:
            logger.error(f"[板块轮动] 获取资金流向失败: {e}")
            return {"success": False, "data": [], "message": str(e)}

    def get_sector_stocks(self, sector_name: str, sector_type: str = "industry") -> Dict[str, Any]:
        """
        获取板块成分股

        Args:
            sector_name: 板块名称
            sector_type: 板块类型，"industry" 或 "concept"

        Returns:
            包含成分股数据的字典
        """
        try:
            logger.info(f"[板块轮动] 获取板块成分股: {sector_name} ({sector_type})...")

            if sector_type == "industry":
                df = self._safe_request(ak.stock_board_industry_cons_em, symbol=sector_name)
            else:
                df = self._safe_request(ak.stock_board_concept_cons_em, symbol=sector_name)

            if df is None or df.empty:
                return {"success": False, "data": [], "message": "无数据"}

            stocks = []
            for idx, row in df.iterrows():
                stocks.append({
                    "code": row.get('代码', ''),
                    "name": row.get('名称', ''),
                    "latest_price": float(row.get('最新价', 0) or 0),
                    "change_pct": float(row.get('涨跌幅', 0) or 0),
                    "change_amount": float(row.get('涨跌额', 0) or 0),
                    "volume": float(row.get('成交量', 0) or 0),
                    "amount": float(row.get('成交额', 0) or 0),
                    "amplitude": float(row.get('振幅', 0) or 0),
                    "high": float(row.get('最高', 0) or 0),
                    "low": float(row.get('最低', 0) or 0),
                    "open": float(row.get('今开', 0) or 0),
                    "prev_close": float(row.get('昨收', 0) or 0),
                    "turnover": float(row.get('换手率', 0) or 0),
                    "pe_ratio": float(row.get('市盈率-动态', 0) or 0),
                    "pb_ratio": float(row.get('市净率', 0) or 0)
                })

            result = {
                "success": True,
                "data": stocks,
                "count": len(stocks),
                "sector_name": sector_name,
                "sector_type": sector_type,
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

            logger.info(f"[板块轮动] 获取到 {len(stocks)} 只成分股")
            return result

        except Exception as e:
            logger.error(f"[板块轮动] 获取成分股失败: {e}")
            return {"success": False, "data": [], "message": str(e)}

    def get_sector_history(self, sector_name: str, sector_type: str = "industry",
                          period: str = "日k", adjust: str = "qfq") -> Dict[str, Any]:
        """
        获取板块历史行情

        Args:
            sector_name: 板块名称
            sector_type: 板块类型
            period: K线周期
            adjust: 复权类型

        Returns:
            包含历史行情的字典
        """
        try:
            logger.info(f"[板块轮动] 获取板块历史行情: {sector_name}...")

            if sector_type == "industry":
                df = self._safe_request(
                    ak.stock_board_industry_hist_em,
                    symbol=sector_name,
                    period=period,
                    adjust=adjust
                )
            else:
                df = self._safe_request(
                    ak.stock_board_concept_hist_em,
                    symbol=sector_name,
                    period=period,
                    adjust=adjust
                )

            if df is None or df.empty:
                return {"success": False, "data": [], "message": "无数据"}

            history = []
            for idx, row in df.iterrows():
                history.append({
                    "date": str(row.get('日期', '')),
                    "open": float(row.get('开盘', 0) or 0),
                    "close": float(row.get('收盘', 0) or 0),
                    "high": float(row.get('最高', 0) or 0),
                    "low": float(row.get('最低', 0) or 0),
                    "volume": float(row.get('成交量', 0) or 0),
                    "amount": float(row.get('成交额', 0) or 0),
                    "amplitude": float(row.get('振幅', 0) or 0),
                    "change_pct": float(row.get('涨跌幅', 0) or 0),
                    "change_amount": float(row.get('涨跌额', 0) or 0),
                    "turnover": float(row.get('换手率', 0) or 0)
                })

            result = {
                "success": True,
                "data": history,
                "count": len(history),
                "sector_name": sector_name,
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

            logger.info(f"[板块轮动] 获取到 {len(history)} 条历史数据")
            return result

        except Exception as e:
            logger.error(f"[板块轮动] 获取历史行情失败: {e}")
            return {"success": False, "data": [], "message": str(e)}

    def get_market_overview(self) -> Dict[str, Any]:
        """
        获取市场总体情况

        Returns:
            包含市场概况的字典
        """
        cache_key = "market_overview"
        cached = self._get_cached(cache_key)
        if cached:
            return cached

        try:
            logger.info("[板块轮动] 获取市场概况...")
            overview = {}

            # 获取A股市场统计
            try:
                df_stat = self._safe_request(ak.stock_zh_a_spot_em)
                if df_stat is not None and not df_stat.empty:
                    total_count = len(df_stat)
                    up_count = len(df_stat[df_stat['涨跌幅'] > 0])
                    down_count = len(df_stat[df_stat['涨跌幅'] < 0])
                    flat_count = total_count - up_count - down_count

                    overview["total_stocks"] = total_count
                    overview["up_count"] = up_count
                    overview["down_count"] = down_count
                    overview["flat_count"] = flat_count
                    overview["up_ratio"] = round(up_count / total_count * 100, 2) if total_count > 0 else 0

                    # 涨停跌停
                    limit_up = len(df_stat[df_stat['涨跌幅'] >= 9.5])
                    limit_down = len(df_stat[df_stat['涨跌幅'] <= -9.5])
                    overview["limit_up"] = limit_up
                    overview["limit_down"] = limit_down
            except Exception as e:
                logger.warning(f"获取A股统计失败: {e}")
                # 设置默认值
                overview["total_stocks"] = 0
                overview["up_count"] = 0
                overview["down_count"] = 0
                overview["flat_count"] = 0
                overview["up_ratio"] = 0
                overview["limit_up"] = 0
                overview["limit_down"] = 0

            overview["indices"] = []
            
            # 方案1: 使用 stock_zh_index_spot_sina 获取指数实时行情
            indices_fetched = False
            try:
                logger.info("[板块轮动] 尝试方案1: stock_zh_index_spot_sina")
                df_indices = self._safe_request(ak.stock_zh_index_spot_sina)
                
                if df_indices is not None and not df_indices.empty:
                    logger.info(f"[板块轮动] 方案1成功，获取到 {len(df_indices)} 条指数数据")
                    logger.info(f"[板块轮动] 指数列名: {list(df_indices.columns)}")
                    
                    # 目标指数
                    target_indices = [
                        ("sh000001", "上证指数"),
                        ("sz399001", "深证成指"),
                        ("sz399006", "创业板指"),
                        ("sh000688", "科创50")
                    ]
                    
                    for symbol, name in target_indices:
                        try:
                            # 尝试通过代码匹配
                            matched = df_indices[df_indices['代码'].astype(str) == symbol]
                            if matched.empty:
                                # 尝试通过名称匹配
                                matched = df_indices[df_indices['名称'].str.contains(name.replace("指", ""), na=False)]
                            
                            if not matched.empty:
                                row = matched.iloc[0]
                                overview["indices"].append({
                                    "code": symbol[-6:],  # 提取纯数字代码
                                    "name": name,
                                    "close": float(row.get('最新价', 0) or 0),
                                    "change_pct": float(row.get('涨跌幅', 0) or 0),
                                    "change": float(row.get('涨跌额', 0) or 0),
                                    "volume": float(row.get('成交量', 0) or 0),
                                    "amount": float(row.get('成交额', 0) or 0)
                                })
                                indices_fetched = True
                            else:
                                logger.warning(f"[板块轮动] 方案1未找到指数: {name}")
                        except Exception as e:
                            logger.warning(f"[板块轮动] 方案1解析{name}失败: {e}")
                            
            except Exception as e:
                logger.warning(f"[板块轮动] 方案1失败: {e}")

            # 方案2: 使用 stock_zh_index_spot_em 获取指数
            if not indices_fetched or len(overview["indices"]) < 2:
                try:
                    logger.info("[板块轮动] 尝试方案2: stock_zh_index_spot_em")
                    overview["indices"] = []  # 重置
                    
                    # 获取上证系列指数
                    df_sh = None
                    df_sz = None
                    
                    try:
                        df_sh = self._safe_request(ak.stock_zh_index_spot_em, symbol="上证系列指数")
                        logger.info(f"[板块轮动] 上证系列指数: {len(df_sh) if df_sh is not None else 0} 条")
                    except Exception as e:
                        logger.warning(f"[板块轮动] 获取上证系列指数失败: {e}")
                    
                    try:
                        df_sz = self._safe_request(ak.stock_zh_index_spot_em, symbol="深证系列指数")
                        logger.info(f"[板块轮动] 深证系列指数: {len(df_sz) if df_sz is not None else 0} 条")
                    except Exception as e:
                        logger.warning(f"[板块轮动] 获取深证系列指数失败: {e}")
                    
                    # 合并数据
                    dfs = [df for df in [df_sh, df_sz] if df is not None and not df.empty]
                    if dfs:
                        df_all = pd.concat(dfs, ignore_index=True)
                        logger.info(f"[板块轮动] 合并后共 {len(df_all)} 条指数数据")
                        logger.info(f"[板块轮动] 列名: {list(df_all.columns)}")
                        
                        target_indices = [
                            ("000001", "上证指数"),
                            ("399001", "深证成指"),
                            ("399006", "创业板指"),
                            ("000688", "科创50")
                        ]
                        
                        for code, name in target_indices:
                            try:
                                matched = df_all[df_all['代码'].astype(str).str.contains(code)]
                                if matched.empty:
                                    matched = df_all[df_all['名称'].str.contains(name.replace("指", ""), na=False)]
                                
                                if not matched.empty:
                                    row = matched.iloc[0]
                                    overview["indices"].append({
                                        "code": code,
                                        "name": name,
                                        "close": float(row.get('最新价', 0) or 0),
                                        "change_pct": float(row.get('涨跌幅', 0) or 0),
                                        "change": float(row.get('涨跌额', 0) or 0),
                                        "volume": float(row.get('成交量', 0) or 0),
                                        "amount": float(row.get('成交额', 0) or 0)
                                    })
                                    indices_fetched = True
                            except Exception as e:
                                logger.warning(f"[板块轮动] 方案2解析{name}失败: {e}")
                                
                except Exception as e:
                    logger.warning(f"[板块轮动] 方案2失败: {e}")

            # 方案3: 使用 index_zh_a_hist 获取历史数据的最新一条
            if not indices_fetched or len(overview["indices"]) < 2:
                try:
                    logger.info("[板块轮动] 尝试方案3: index_zh_a_hist")
                    overview["indices"] = []  # 重置
                    
                    indices_backup = [
                        ("sh000001", "000001", "上证指数"),
                        ("sz399001", "399001", "深证成指"),
                        ("sz399006", "399006", "创业板指"),
                        ("sh000688", "000688", "科创50")
                    ]
                    
                    end_date = datetime.now().strftime("%Y%m%d")
                    start_date = (datetime.now() - timedelta(days=10)).strftime("%Y%m%d")
                    
                    for symbol, code, name in indices_backup:
                        try:
                            df_hist = ak.index_zh_a_hist(
                                symbol=symbol,
                                period="daily",
                                start_date=start_date,
                                end_date=end_date
                            )
                            
                            if df_hist is not None and not df_hist.empty:
                                latest = df_hist.iloc[-1]
                                prev_close = df_hist.iloc[-2]['收盘'] if len(df_hist) > 1 else latest['开盘']
                                change = latest['收盘'] - prev_close
                                change_pct = (change / prev_close * 100) if prev_close > 0 else 0
                                
                                overview["indices"].append({
                                    "code": code,
                                    "name": name,
                                    "close": float(latest['收盘']),
                                    "change_pct": round(change_pct, 2),
                                    "change": round(change, 2),
                                    "volume": float(latest.get('成交量', 0) or 0),
                                    "amount": float(latest.get('成交额', 0) or 0)
                                })
                                indices_fetched = True
                                logger.info(f"[板块轮动] 方案3成功获取{name}")
                        except Exception as e:
                            logger.warning(f"[板块轮动] 方案3获取{name}失败: {e}")
                            
                except Exception as e:
                    logger.warning(f"[板块轮动] 方案3失败: {e}")

            # 如果所有方案都失败，返回空数据但标记成功（避免前端报错）
            if not overview.get("indices"):
                logger.warning("[板块轮动] 所有指数获取方案均失败，返回空数据")
                overview["indices"] = []

            result = {
                "success": True,
                "data": overview,
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

            self._set_cache(cache_key, result)
            logger.info(f"[板块轮动] 市场概况获取完成，获取到 {len(overview.get('indices', []))} 个指数")
            return result

        except Exception as e:
            logger.error(f"[板块轮动] 获取市场概况失败: {e}", exc_info=True)
            return {
                "success": True,  # 返回 True 避免前端报错
                "data": {
                    "total_stocks": 0,
                    "up_count": 0,
                    "down_count": 0,
                    "flat_count": 0,
                    "up_ratio": 0,
                    "limit_up": 0,
                    "limit_down": 0,
                    "indices": []
                },
                "message": str(e),
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

    def get_north_money_flow(self) -> Dict[str, Any]:
        """
        获取北向资金流向

        Returns:
            包含北向资金数据的字典
        """
        cache_key = "north_money_flow"
        cached = self._get_cached(cache_key)
        if cached:
            return cached

        try:
            logger.info("[板块轮动] 获取北向资金流向...")
            df = self._safe_request(ak.stock_hsgt_fund_flow_summary_em)

            if df is None or df.empty:
                return {"success": False, "data": {}, "message": "无数据"}

            # 获取最新数据
            latest = df.iloc[0]

            north_flow = {
                "date": str(latest.get('日期', '')),
                "north_net_inflow": float(latest.get('北向资金-成交净买额', 0) or 0),
                "hgt_net_inflow": float(latest.get('沪股通-成交净买额', 0) or 0),
                "sgt_net_inflow": float(latest.get('深股通-成交净买额', 0) or 0),
                "north_total_amount": float(latest.get('北向资金-成交金额', 0) or 0)
            }

            # 获取历史趋势（最近20天）
            history = []
            for idx, row in df.head(20).iterrows():
                history.append({
                    "date": str(row.get('日期', '')),
                    "net_inflow": float(row.get('北向资金-成交净买额', 0) or 0)
                })
            north_flow["history"] = history

            result = {
                "success": True,
                "data": north_flow,
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

            self._set_cache(cache_key, result)
            logger.info("[板块轮动] 北向资金数据获取完成")
            return result

        except Exception as e:
            logger.error(f"[板块轮动] 获取北向资金失败: {e}")
            return {"success": False, "data": {}, "message": str(e)}

    def get_comprehensive_data(self) -> Dict[str, Any]:
        """
        获取综合板块数据（用于轮动分析）

        Returns:
            包含所有板块相关数据的字典
        """
        logger.info("[板块轮动] 开始获取综合数据...")

        data = {
            "success": False,
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "industry_sectors": {},
            "concept_sectors": {},
            "fund_flow": {},
            "market_overview": {},
            "north_flow": {}
        }

        try:
            # 1. 行业板块
            industry_result = self.get_industry_sectors()
            if industry_result.get("success"):
                data["industry_sectors"] = industry_result

            # 2. 概念板块
            concept_result = self.get_concept_sectors()
            if concept_result.get("success"):
                data["concept_sectors"] = concept_result

            # 3. 资金流向
            fund_flow_result = self.get_sector_fund_flow()
            if fund_flow_result.get("success"):
                data["fund_flow"] = fund_flow_result

            # 4. 市场概况
            market_result = self.get_market_overview()
            if market_result.get("success"):
                data["market_overview"] = market_result

            # 5. 北向资金
            north_result = self.get_north_money_flow()
            if north_result.get("success"):
                data["north_flow"] = north_result

            data["success"] = True
            logger.info("[板块轮动] 综合数据获取完成")

        except Exception as e:
            logger.error(f"[板块轮动] 获取综合数据失败: {e}")
            data["error"] = str(e)

        return data


# 单例实例
sector_rotation_fetcher = SectorRotationDataFetcher()
