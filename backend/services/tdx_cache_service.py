"""
TDX数据后台缓存服务
独立后台线程定时获取TDX数据，缓存到服务器端文件
所有API请求直接读取缓存，不阻塞用户请求

缓存策略：
- 市场统计（涨跌家数）: 交易时段每5分钟更新
- 板块数据: 交易时段每10分钟更新
- 股票列表: 每天开盘前更新一次
- 日K线数据: 每天收盘后更新
- 龙虎榜: 每天18:00后更新
"""

import json
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List
import schedule
import pandas as pd

from backend.utils.logging_config import get_logger

logger = get_logger("services.tdx_cache")

# 缓存目录
CACHE_DIR = Path("data/tdx_cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# 缓存文件路径
CACHE_FILES = {
    "market_stats": CACHE_DIR / "market_stats.json",
    "stock_list": CACHE_DIR / "stock_list.json",
    "industry_sectors": CACHE_DIR / "industry_sectors.json",
    "concept_sectors": CACHE_DIR / "concept_sectors.json",
    "sector_fund_flow": CACHE_DIR / "sector_fund_flow.json",
    "limit_up_down": CACHE_DIR / "limit_up_down.json",
}


class TDXCacheService:
    """TDX数据缓存服务"""

    def __init__(self):
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._tdx_provider = None
        self._last_update_times: Dict[str, datetime] = {}

        # 更新间隔配置（秒）
        self._update_intervals = {
            "market_stats": 300,      # 5分钟
            "industry_sectors": 600,  # 10分钟
            "concept_sectors": 600,   # 10分钟
            "sector_fund_flow": 600,  # 10分钟
            "limit_up_down": 300,     # 5分钟
            "stock_list": 86400,      # 24小时
        }

        logger.info("[TDX缓存] 服务初始化完成")

    def _get_tdx_provider(self):
        """获取TDX Provider（延迟初始化）"""
        if self._tdx_provider is None:
            try:
                from backend.dataflows.providers.tdx_native_provider import get_tdx_native_provider
                self._tdx_provider = get_tdx_native_provider()
            except Exception as e:
                logger.error(f"[TDX缓存] 获取TDX Provider失败: {e}")
        return self._tdx_provider

    def _is_trading_time(self) -> bool:
        """判断是否为交易时段"""
        now = datetime.now()
        weekday = now.weekday()

        # 周末不交易
        if weekday >= 5:
            return False

        # 交易时段: 9:15-11:30, 13:00-15:00
        current_time = now.time()
        morning_start = datetime.strptime("09:15", "%H:%M").time()
        morning_end = datetime.strptime("11:30", "%H:%M").time()
        afternoon_start = datetime.strptime("13:00", "%H:%M").time()
        afternoon_end = datetime.strptime("15:00", "%H:%M").time()

        if morning_start <= current_time <= morning_end:
            return True
        if afternoon_start <= current_time <= afternoon_end:
            return True

        return False

    def _is_after_market_close(self) -> bool:
        """判断是否为收盘后（15:00-23:59）"""
        now = datetime.now()
        weekday = now.weekday()

        if weekday >= 5:
            return False

        current_time = now.time()
        close_time = datetime.strptime("15:00", "%H:%M").time()

        return current_time >= close_time

    def _should_update(self, cache_type: str) -> bool:
        """判断是否需要更新缓存"""
        # 检查上次更新时间
        last_update = self._last_update_times.get(cache_type)
        if last_update is None:
            return True

        interval = self._update_intervals.get(cache_type, 300)
        elapsed = (datetime.now() - last_update).total_seconds()

        if elapsed < interval:
            return False

        # 根据数据类型判断是否在合适的时间更新
        if cache_type in ["market_stats", "industry_sectors", "concept_sectors",
                         "sector_fund_flow", "limit_up_down"]:
            # 这些数据只在交易时段更新
            return self._is_trading_time()

        if cache_type == "stock_list":
            # 股票列表每天更新一次，在开盘前
            now = datetime.now()
            if last_update.date() < now.date():
                return True
            return False

        return True

    def _save_cache(self, cache_type: str, data: Any) -> bool:
        """保存缓存到文件"""
        try:
            cache_file = CACHE_FILES.get(cache_type)
            if not cache_file:
                return False

            cache_data = {
                "data": data,
                "update_time": datetime.now().isoformat(),
                "cache_type": cache_type
            }

            with self._lock:
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(cache_data, f, ensure_ascii=False, indent=2)

            self._last_update_times[cache_type] = datetime.now()
            logger.debug(f"[TDX缓存] {cache_type} 缓存已更新")
            return True

        except Exception as e:
            logger.error(f"[TDX缓存] 保存缓存失败 {cache_type}: {e}")
            return False

    def read_cache(self, cache_type: str) -> Optional[Dict]:
        """读取缓存（供API调用）"""
        try:
            cache_file = CACHE_FILES.get(cache_type)
            if not cache_file or not cache_file.exists():
                return None

            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)

            return cache_data

        except Exception as e:
            logger.error(f"[TDX缓存] 读取缓存失败 {cache_type}: {e}")
            return None

    def get_cache_status(self) -> Dict[str, Any]:
        """获取缓存状态"""
        status = {
            "running": self._running,
            "is_trading_time": self._is_trading_time(),
            "caches": {}
        }

        for cache_type, cache_file in CACHE_FILES.items():
            cache_info = {
                "exists": cache_file.exists(),
                "last_update": None,
                "file_size": 0,
                "next_update_in": None
            }

            if cache_file.exists():
                cache_info["file_size"] = cache_file.stat().st_size
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        cache_info["last_update"] = data.get("update_time")
                except:
                    pass

            # 计算下次更新时间
            last_update = self._last_update_times.get(cache_type)
            if last_update:
                interval = self._update_intervals.get(cache_type, 300)
                next_update = interval - (datetime.now() - last_update).total_seconds()
                cache_info["next_update_in"] = max(0, int(next_update))

            status["caches"][cache_type] = cache_info

        return status

    def _update_market_stats(self):
        """更新市场统计数据（优先使用AKShare，TDX作为补充）"""
        if not self._should_update("market_stats"):
            return

        try:
            import akshare as ak

            logger.info("[TDX缓存] 开始更新市场统计...")
            start_time = time.time()

            stats = {
                "total_stocks": 0,
                "up_count": 0,
                "down_count": 0,
                "flat_count": 0,
                "up_ratio": 0,
                "limit_up": 0,
                "limit_down": 0,
                "up_5_pct": 0,
                "up_3_pct": 0,
                "down_3_pct": 0,
                "down_5_pct": 0,
                "sentiment_score": 0,
                "sentiment_level": "中性",
                "shanghai_count": 0,
                "shenzhen_count": 0,
                "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            # 方法1: 使用AKShare获取涨跌统计
            try:
                # 获取A股实时行情
                df = ak.stock_zh_a_spot_em()
                if df is not None and not df.empty:
                    # 过滤A股
                    df = df[df['代码'].str.match(r'^(00|30|60|68)')]

                    stats["total_stocks"] = len(df)
                    stats["shanghai_count"] = len(df[df['代码'].str.startswith(('60', '68'))])
                    stats["shenzhen_count"] = len(df[df['代码'].str.startswith(('00', '30'))])

                    # 统计涨跌
                    change_col = '涨跌幅'
                    if change_col in df.columns:
                        df[change_col] = pd.to_numeric(df[change_col], errors='coerce')
                        stats["up_count"] = len(df[df[change_col] > 0])
                        stats["down_count"] = len(df[df[change_col] < 0])
                        stats["flat_count"] = len(df[df[change_col] == 0])
                        stats["up_ratio"] = round(stats["up_count"] / stats["total_stocks"] * 100, 2) if stats["total_stocks"] > 0 else 0

                        # 涨跌停统计
                        stats["limit_up"] = len(df[df[change_col] >= 9.9])
                        stats["limit_down"] = len(df[df[change_col] <= -9.9])

                        # 涨跌幅区间统计
                        stats["up_5_pct"] = len(df[df[change_col] >= 5])
                        stats["up_3_pct"] = len(df[(df[change_col] >= 3) & (df[change_col] < 5)])
                        stats["down_3_pct"] = len(df[(df[change_col] <= -3) & (df[change_col] > -5)])
                        stats["down_5_pct"] = len(df[df[change_col] <= -5])

                        # 计算情绪分数
                        sentiment_score = (stats["up_count"] - stats["down_count"]) / stats["total_stocks"] * 100 if stats["total_stocks"] > 0 else 0
                        stats["sentiment_score"] = round(sentiment_score, 2)

                        if sentiment_score > 20:
                            stats["sentiment_level"] = "极度乐观"
                        elif sentiment_score > 10:
                            stats["sentiment_level"] = "乐观"
                        elif sentiment_score > 0:
                            stats["sentiment_level"] = "偏多"
                        elif sentiment_score > -10:
                            stats["sentiment_level"] = "偏空"
                        elif sentiment_score > -20:
                            stats["sentiment_level"] = "悲观"
                        else:
                            stats["sentiment_level"] = "极度悲观"

                    logger.info(f"[TDX缓存] AKShare获取市场统计成功: {stats['total_stocks']}只股票")

            except Exception as e:
                logger.warning(f"[TDX缓存] AKShare获取市场统计失败: {e}")

                # 方法2: 使用TDX作为备用
                provider = self._get_tdx_provider()
                if provider and provider.is_available():
                    tdx_stats = provider.get_market_stats(use_cache=False)
                    if tdx_stats and tdx_stats.get('total_stocks', 0) > 0:
                        stats = tdx_stats
                        stats["update_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        logger.info(f"[TDX缓存] TDX获取市场统计成功: {stats['total_stocks']}只股票")

            if stats.get('total_stocks', 0) > 0:
                self._save_cache("market_stats", stats)
                elapsed = time.time() - start_time
                logger.info(f"[TDX缓存] 市场统计更新完成 (耗时{elapsed:.1f}秒)")
            else:
                logger.warning("[TDX缓存] 市场统计数据为空")

        except Exception as e:
            logger.error(f"[TDX缓存] 更新市场统计失败: {e}")

    def _update_stock_list(self):
        """更新股票列表（使用AKShare获取完整列表）"""
        if not self._should_update("stock_list"):
            return

        try:
            import akshare as ak

            logger.info("[TDX缓存] 开始更新股票列表（使用AKShare）...")

            all_stocks = []

            # 使用AKShare获取A股列表
            try:
                df = ak.stock_info_a_code_name()
                if df is not None and not df.empty:
                    for _, row in df.iterrows():
                        code = str(row.get('code', ''))
                        name = row.get('name', '')
                        if code.startswith(('00', '30', '60', '68')):
                            market = '上海' if code.startswith(('60', '68')) else '深圳'
                            all_stocks.append({
                                'code': code,
                                'name': name,
                                'market': market
                            })
                    logger.info(f"[TDX缓存] AKShare获取到 {len(all_stocks)} 只A股")
            except Exception as e:
                logger.error(f"[TDX缓存] AKShare获取股票列表失败: {e}")

            # 如果AKShare失败，尝试TDX（只能获取深圳）
            if not all_stocks or len(all_stocks) < 100:
                provider = self._get_tdx_provider()
                if provider and provider.is_available():
                    tdx_stocks = provider.get_all_stock_codes()
                    if tdx_stocks and len(tdx_stocks) > 100:
                        all_stocks = [s for s in tdx_stocks
                                    if s.get('code', '').startswith(('00', '30', '60', '68'))]
                        logger.info(f"[TDX缓存] TDX获取到 {len(all_stocks)} 只A股")

            if all_stocks and len(all_stocks) > 100:
                self._save_cache("stock_list", all_stocks)
                sh_count = len([s for s in all_stocks if s.get('code', '').startswith(('60', '68'))])
                sz_count = len([s for s in all_stocks if s.get('code', '').startswith(('00', '30'))])
                logger.info(f"[TDX缓存] 股票列表更新完成: 共{len(all_stocks)}只 (上海:{sh_count}, 深圳:{sz_count})")
            else:
                logger.warning(f"[TDX缓存] 股票列表数据不足: {len(all_stocks)}")

        except Exception as e:
            logger.error(f"[TDX缓存] 更新股票列表失败: {e}")

    def _update_sector_data(self):
        """更新板块数据（使用AKShare）"""
        if not self._is_trading_time():
            return

        try:
            import akshare as ak

            # 更新行业板块
            if self._should_update("industry_sectors"):
                logger.info("[TDX缓存] 开始更新行业板块...")
                try:
                    df = ak.stock_board_industry_name_em()
                    if df is not None and not df.empty:
                        sectors = []
                        for _, row in df.iterrows():
                            sectors.append({
                                "name": row.get('板块名称', ''),
                                "code": row.get('板块代码', ''),
                                "change_pct": float(row.get('涨跌幅', 0) or 0),
                                "turnover": float(row.get('换手率', 0) or 0),
                                "top_stock": row.get('领涨股票', ''),
                                "up_count": int(row.get('上涨家数', 0) or 0),
                                "down_count": int(row.get('下跌家数', 0) or 0),
                            })
                        self._save_cache("industry_sectors", sectors)
                        logger.info(f"[TDX缓存] 行业板块更新完成: {len(sectors)}个")
                except Exception as e:
                    logger.error(f"[TDX缓存] 更新行业板块失败: {e}")

            # 更新概念板块
            if self._should_update("concept_sectors"):
                logger.info("[TDX缓存] 开始更新概念板块...")
                try:
                    df = ak.stock_board_concept_name_em()
                    if df is not None and not df.empty:
                        concepts = []
                        for _, row in df.iterrows():
                            concepts.append({
                                "name": row.get('板块名称', ''),
                                "code": row.get('板块代码', ''),
                                "change_pct": float(row.get('涨跌幅', 0) or 0),
                                "turnover": float(row.get('换手率', 0) or 0),
                                "top_stock": row.get('领涨股票', ''),
                                "up_count": int(row.get('上涨家数', 0) or 0),
                                "down_count": int(row.get('下跌家数', 0) or 0),
                            })
                        self._save_cache("concept_sectors", concepts)
                        logger.info(f"[TDX缓存] 概念板块更新完成: {len(concepts)}个")
                except Exception as e:
                    logger.error(f"[TDX缓存] 更新概念板块失败: {e}")

            # 更新资金流向
            if self._should_update("sector_fund_flow"):
                logger.info("[TDX缓存] 开始更新资金流向...")
                try:
                    df = ak.stock_sector_fund_flow_rank(indicator="今日")
                    if df is not None and not df.empty:
                        fund_flow = []
                        for _, row in df.iterrows():
                            fund_flow.append({
                                "sector": row.get('名称', ''),
                                "change_pct": float(row.get('今日涨跌幅', 0) or 0),
                                "main_net_inflow": float(row.get('今日主力净流入-净额', 0) or 0),
                                "main_net_inflow_pct": float(row.get('今日主力净流入-净占比', 0) or 0),
                            })
                        self._save_cache("sector_fund_flow", fund_flow)
                        logger.info(f"[TDX缓存] 资金流向更新完成: {len(fund_flow)}条")
                except Exception as e:
                    logger.error(f"[TDX缓存] 更新资金流向失败: {e}")

        except ImportError:
            logger.error("[TDX缓存] AKShare未安装")
        except Exception as e:
            logger.error(f"[TDX缓存] 更新板块数据失败: {e}")

    def _update_limit_up_down(self):
        """更新涨跌停数据"""
        if not self._should_update("limit_up_down"):
            return

        try:
            import akshare as ak

            logger.info("[TDX缓存] 开始更新涨跌停数据...")
            today = datetime.now().strftime('%Y%m%d')

            result = {
                "date": today,
                "limit_up": [],
                "limit_down": [],
                "limit_up_count": 0,
                "limit_down_count": 0
            }

            # 获取涨停
            try:
                df_up = ak.stock_zt_pool_em(date=today)
                if df_up is not None and not df_up.empty:
                    result["limit_up_count"] = len(df_up)
                    for _, row in df_up.head(20).iterrows():
                        result["limit_up"].append({
                            "code": row.get('代码', ''),
                            "name": row.get('名称', ''),
                            "change_pct": float(row.get('涨跌幅', 0) or 0),
                        })
            except:
                pass

            # 获取跌停
            try:
                df_down = ak.stock_zt_pool_dtgc_em(date=today)
                if df_down is not None and not df_down.empty:
                    result["limit_down_count"] = len(df_down)
                    for _, row in df_down.head(20).iterrows():
                        result["limit_down"].append({
                            "code": row.get('代码', ''),
                            "name": row.get('名称', ''),
                            "change_pct": float(row.get('涨跌幅', 0) or 0),
                        })
            except:
                pass

            self._save_cache("limit_up_down", result)
            logger.info(f"[TDX缓存] 涨跌停更新完成: 涨停{result['limit_up_count']}, 跌停{result['limit_down_count']}")

        except Exception as e:
            logger.error(f"[TDX缓存] 更新涨跌停失败: {e}")

    def _run_update_loop(self):
        """后台更新循环"""
        logger.info("[TDX缓存] 后台更新线程启动")

        # 启动时立即更新一次
        self._update_stock_list()
        self._update_market_stats()
        self._update_sector_data()
        self._update_limit_up_down()

        while self._running:
            try:
                # 每分钟检查一次是否需要更新
                time.sleep(60)

                if not self._running:
                    break

                # 检查并更新各类数据
                self._update_market_stats()
                self._update_sector_data()
                self._update_limit_up_down()

                # 股票列表每天更新一次
                self._update_stock_list()

            except Exception as e:
                logger.error(f"[TDX缓存] 更新循环异常: {e}")
                time.sleep(60)

        logger.info("[TDX缓存] 后台更新线程停止")

    def start(self):
        """启动缓存服务"""
        if self._running:
            logger.warning("[TDX缓存] 服务已在运行")
            return

        self._running = True
        self._thread = threading.Thread(target=self._run_update_loop, daemon=True)
        self._thread.start()
        logger.info("[TDX缓存] 服务已启动")

    def stop(self):
        """停止缓存服务"""
        if not self._running:
            return

        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("[TDX缓存] 服务已停止")

    def force_update(self, cache_type: str = None):
        """强制更新缓存"""
        if cache_type:
            # 清除上次更新时间，强制更新
            self._last_update_times.pop(cache_type, None)

            if cache_type == "market_stats":
                self._update_market_stats()
            elif cache_type == "stock_list":
                self._update_stock_list()
            elif cache_type in ["industry_sectors", "concept_sectors", "sector_fund_flow"]:
                self._update_sector_data()
            elif cache_type == "limit_up_down":
                self._update_limit_up_down()
        else:
            # 更新所有
            self._last_update_times.clear()
            self._update_stock_list()
            self._update_market_stats()
            self._update_sector_data()
            self._update_limit_up_down()


# 全局单例
_tdx_cache_service: Optional[TDXCacheService] = None
_service_lock = threading.Lock()


def get_tdx_cache_service() -> TDXCacheService:
    """获取TDX缓存服务单例"""
    global _tdx_cache_service

    if _tdx_cache_service is None:
        with _service_lock:
            if _tdx_cache_service is None:
                _tdx_cache_service = TDXCacheService()

    return _tdx_cache_service


def read_market_stats() -> Optional[Dict]:
    """读取市场统计缓存（便捷函数）"""
    service = get_tdx_cache_service()
    cache = service.read_cache("market_stats")
    if cache:
        return cache.get("data")
    return None


def read_stock_list() -> Optional[List]:
    """读取股票列表缓存（便捷函数）"""
    service = get_tdx_cache_service()
    cache = service.read_cache("stock_list")
    if cache:
        return cache.get("data")
    return None


def read_industry_sectors() -> Optional[List]:
    """读取行业板块缓存（便捷函数）"""
    service = get_tdx_cache_service()
    cache = service.read_cache("industry_sectors")
    if cache:
        return cache.get("data")
    return None


def read_concept_sectors() -> Optional[List]:
    """读取概念板块缓存（便捷函数）"""
    service = get_tdx_cache_service()
    cache = service.read_cache("concept_sectors")
    if cache:
        return cache.get("data")
    return None
