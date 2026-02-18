#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TDX 原生 Python Provider - 使用 pytdx 直接连接通达信服务器
无需任何外部服务，随 Python 后端一起启动

优点：
1. 纯 Python 实现，无需 Docker 或外部服务
2. 直接连接通达信行情服务器，速度快
3. 支持实时行情、K线、分时等数据
4. 自动选择最快的服务器

支持的接口（对标 Go TDX API 32个接口）：
1. get_realtime_quote - 单只股票实时行情
2. get_realtime_quotes - 批量实时行情
3. get_kline - K线数据（日/周/月/分钟）
4. get_minute_data - 当日分时数据
5. get_history_minute_data - 历史分时数据
6. get_transaction_data - 逐笔成交数据
7. get_history_transaction_data - 历史逐笔成交
8. search_stock - 股票搜索
9. get_stock_info - 股票基本信息
10. get_stock_list - 股票代码列表
11. get_index_bars - 指数K线
12. get_index_list - 指数列表
13. get_market_count - 市场股票数量
14. get_finance_info - 财务数据
15. get_company_info - 公司信息
16. is_trading_day - 交易日判断
17. get_block_info - 板块信息
18. get_block_stocks - 板块成分股

使用方法：
    from backend.dataflows.providers.tdx_native_provider import get_tdx_native_provider
    provider = get_tdx_native_provider()
    quote = provider.get_realtime_quote("000001")
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import threading
import re

try:
    from backend.utils.logging_config import get_logger

    logger = get_logger("tdx_native")
except ImportError:
    logger = logging.getLogger(__name__)


class TDXNativeProvider:
    """
    TDX 原生 Python Provider
    使用 pytdx 库直接连接通达信服务器
    """

    # 通达信行情服务器列表（公共服务器）
    # 按地区分组，支持自动优选最快服务器
    # 端口统一为 7709

    # 上海服务器
    HOSTS_SHANGHAI = [
        ("124.71.187.122", 7709, "上海(华为)"),
        ("122.51.120.217", 7709, "上海(腾讯)"),
        ("111.229.247.189", 7709, "上海(腾讯)"),
        ("124.70.176.52", 7709, "上海(华为)"),
        ("123.60.186.45", 7709, "上海(华为)"),
        ("122.51.232.182", 7709, "上海(腾讯)"),
        ("118.25.98.114", 7709, "上海(腾讯)"),
        ("124.70.199.56", 7709, "上海(华为)"),
        ("121.36.225.169", 7709, "上海(华为)"),
        ("123.60.70.228", 7709, "上海(华为)"),
        ("123.60.73.44", 7709, "上海(华为)"),
        ("124.70.133.119", 7709, "上海(华为)"),
        ("124.71.187.72", 7709, "上海(华为)"),
        ("123.60.84.66", 7709, "上海(华为)"),
    ]

    # 北京服务器
    HOSTS_BEIJING = [
        ("121.36.54.217", 7709, "北京(华为)"),
        ("121.36.81.195", 7709, "北京(华为)"),
        ("123.249.15.60", 7709, "北京(华为)"),
        ("124.70.75.113", 7709, "北京(华为)"),
        ("120.46.186.223", 7709, "北京(华为)"),
        ("124.70.22.210", 7709, "北京(华为)"),
        ("139.9.133.247", 7709, "北京(华为)"),
    ]

    # 广州服务器
    HOSTS_GUANGZHOU = [
        ("124.71.85.110", 7709, "广州(华为)"),
        ("139.9.51.18", 7709, "广州(华为)"),
        ("139.159.239.163", 7709, "广州(华为)"),
        ("124.71.9.153", 7709, "广州(华为)"),
        ("116.205.163.254", 7709, "广州(华为)"),
        ("116.205.171.132", 7709, "广州(华为)"),
        ("116.205.183.150", 7709, "广州(华为)"),
        ("111.230.186.52", 7709, "广州(腾讯)"),
        ("110.41.4.4", 7709, "广州(华为)"),
        ("110.41.2.72", 7709, "广州(华为)"),
        ("110.41.154.219", 7709, "广州(华为)"),
        ("110.41.147.114", 7709, "广州(华为)"),
    ]

    # 武汉服务器
    HOSTS_WUHAN = [
        ("119.97.185.59", 7709, "武汉(电信)"),
    ]

    # 旧版服务器列表（备用）
    HOSTS_LEGACY = [
        ("218.75.126.9", 7709, "杭州主站"),
        ("119.147.212.81", 7709, "深圳双线主站1"),
        ("112.95.140.74", 7709, "深圳双线主站2"),
        ("112.95.140.92", 7709, "深圳双线主站3"),
        ("117.184.140.156", 7709, "上海双线主站1"),
        ("117.184.140.157", 7709, "上海双线主站2"),
        ("221.194.181.176", 7709, "北京主站"),
        ("124.74.236.94", 7721, "上海主站"),
        ("180.153.39.51", 7709, "上海备用1"),
        ("101.227.73.20", 7709, "上海备用2"),
        ("101.227.77.254", 7709, "上海备用3"),
        ("14.215.128.18", 7709, "广州备用"),
        ("59.173.18.140", 7709, "武汉备用"),
        ("60.28.23.80", 7709, "天津备用"),
        ("218.60.29.136", 7709, "大连备用"),
    ]

    # 合并所有服务器（优先使用新服务器）
    HOSTS = (
        [(h[0], h[1]) for h in HOSTS_SHANGHAI[:4]]  # 上海前4个
        + [(h[0], h[1]) for h in HOSTS_BEIJING[:2]]  # 北京前2个
        + [(h[0], h[1]) for h in HOSTS_GUANGZHOU[:2]]  # 广州前2个
        + [(h[0], h[1]) for h in HOSTS_SHANGHAI[4:]]  # 上海剩余
        + [(h[0], h[1]) for h in HOSTS_BEIJING[2:]]  # 北京剩余
        + [(h[0], h[1]) for h in HOSTS_GUANGZHOU[2:]]  # 广州剩余
        + [(h[0], h[1]) for h in HOSTS_WUHAN]  # 武汉
        + [(h[0], h[1]) for h in HOSTS_LEGACY]  # 旧版备用
    )

    # 连接超时设置（秒）- 增加到8秒以提高成功率
    CONNECT_TIMEOUT = 8

    # 连接保活间隔（秒）- 每隔这么长时间发送一次心跳
    KEEPALIVE_INTERVAL = 30

    # 连接空闲超时（秒）- 超过此时间未使用则重新验证连接
    IDLE_TIMEOUT = 120  # 从60秒增加到120秒

    # 可用性缓存时间（秒）- 成功时缓存较长，失败时缓存较短
    AVAILABILITY_CACHE_SUCCESS = 180  # 成功时缓存3分钟
    AVAILABILITY_CACHE_FAIL = 5  # 失败时只缓存5秒，快速重试

    # 最大重试次数
    MAX_RETRY = 3

    # 服务器测速缓存
    _server_latency_cache = {}
    _server_latency_cache_time = None
    _server_latency_cache_ttl = 3600  # 1小时缓存

    def __init__(self):
        self._api = None
        self._connected = False
        self._lock = threading.Lock()
        self._available = None  # 缓存可用性检查结果
        self._last_check_time = None  # 上次检查时间
        self._last_use_time = None  # 上次使用时间
        self._current_host = None  # 当前连接的服务器
        self._fail_count = 0  # 连续失败次数
        self._last_success_host = None  # 上次成功的服务器
        # 市场统计缓存
        self._market_stats_cache = None
        self._market_stats_cache_time = None
        self._market_stats_cache_ttl = 300  # 5分钟缓存

    def _ensure_connection(self) -> bool:
        """确保连接到通达信服务器（带重连机制和重试）"""
        now = datetime.now()

        # 先检查现有连接是否有效
        if self._connected and self._api:
            # 检查连接是否超时（超过IDLE_TIMEOUT秒未使用则重新验证）
            if (
                self._last_use_time
                and (now - self._last_use_time).total_seconds() > self.IDLE_TIMEOUT
            ):
                try:
                    # 发送一个简单请求测试连接是否有效
                    test_data = self._api.get_security_count(0)  # 获取深圳市场股票数量
                    if test_data is not None:
                        self._last_use_time = now
                        return True
                except Exception:
                    # 连接已断开，需要重连
                    logger.debug("TDX连接已断开（超时），尝试重连...")
                    self._connected = False
                    try:
                        self._api.disconnect()
                    except:
                        pass
                    self._api = None
            else:
                # 连接仍在活跃期内，直接返回
                self._last_use_time = now
                return True

        with self._lock:
            # 双重检查
            if self._connected and self._api:
                self._last_use_time = now
                return True

            try:
                from pytdx.hq import TdxHq_API

                # 构建服务器列表，优先使用上次成功的服务器
                hosts_to_try = list(self.HOSTS)
                if self._last_success_host and self._last_success_host in hosts_to_try:
                    hosts_to_try.remove(self._last_success_host)
                    hosts_to_try.insert(0, self._last_success_host)

                # 多次重试
                for retry in range(self.MAX_RETRY):
                    self._api = TdxHq_API()

                    # 尝试连接服务器（带超时控制）
                    for host, port in hosts_to_try:
                        try:
                            # pytdx connect 支持 time_out 参数
                            if self._api.connect(
                                host, port, time_out=self.CONNECT_TIMEOUT
                            ):
                                # 验证连接是否真正可用
                                test_result = self._api.get_security_count(0)
                                if test_result is not None and test_result > 0:
                                    self._connected = True
                                    self._current_host = (host, port)
                                    self._last_success_host = (host, port)
                                    self._last_use_time = now
                                    self._fail_count = 0
                                    logger.info(f"TDX连接成功: {host}:{port}")
                                    return True
                                else:
                                    # 连接成功但数据无效，断开重试
                                    try:
                                        self._api.disconnect()
                                    except:
                                        pass
                        except Exception as e:
                            logger.debug(
                                f"TDX连接失败 {host}:{port} (重试{retry + 1}): {e}"
                            )
                            continue

                    # 本轮所有服务器都失败，等待一小段时间后重试
                    if retry < self.MAX_RETRY - 1:
                        import time

                        time.sleep(0.5)

                self._fail_count += 1
                logger.warning(f"所有TDX服务器连接失败 (连续失败{self._fail_count}次)")
                return False

            except ImportError:
                logger.warning("pytdx 未安装，请运行: pip install pytdx")
                return False
            except Exception as e:
                logger.error(f"TDX初始化失败: {e}")
                return False

    def is_available(self) -> bool:
        """检查 TDX 是否可用（带缓存，成功和失败使用不同缓存时间）"""
        now = datetime.now()

        # 检查缓存是否有效
        if self._available is not None and self._last_check_time is not None:
            elapsed = (now - self._last_check_time).total_seconds()
            # 成功时缓存较长，失败时缓存较短以便快速重试
            cache_time = (
                self.AVAILABILITY_CACHE_SUCCESS
                if self._available
                else self.AVAILABILITY_CACHE_FAIL
            )
            if elapsed < cache_time:
                # 缓存有效，直接返回
                return self._available

        try:
            from pytdx.hq import TdxHq_API

            result = self._ensure_connection()
            self._available = result
            self._last_check_time = now
            return result
        except ImportError:
            logger.debug("pytdx 未安装")
            self._available = False
            self._last_check_time = now
            return False
        except Exception as e:
            logger.debug(f"TDX 不可用: {e}")
            self._available = False
            self._last_check_time = now
            return False

    def ensure_available_with_retry(self, max_retries: int = 3) -> bool:
        """
        带重试的可用性检查，失败时自动重置连接并重试

        Args:
            max_retries: 最大重试次数

        Returns:
            是否可用
        """
        for attempt in range(max_retries):
            if self.is_available():
                return True

            # 如果不可用，重置连接状态并重试
            if attempt < max_retries - 1:
                logger.info(f"TDX 连接失败，尝试重连 ({attempt + 1}/{max_retries})...")
                self.reset_connection()
                import time

                time.sleep(0.5)  # 短暂等待后重试

        return False

    def get_kline_with_retry(
        self, code: str, kline_type: int = 9, count: int = 100, max_retries: int = 2
    ) -> List[Dict]:
        """
        带重试的 K 线数据获取

        Args:
            code: 股票代码
            kline_type: K线类型
            count: 获取数量
            max_retries: 最大重试次数

        Returns:
            K线数据列表
        """
        for attempt in range(max_retries):
            # 确保连接可用
            if not self._ensure_connection():
                if attempt < max_retries - 1:
                    logger.debug(f"TDX 连接失败，重试 ({attempt + 1}/{max_retries})...")
                    self.reset_connection()
                    import time

                    time.sleep(0.3)
                    continue
                return []

            try:
                market = self._get_market(code)
                data = self._api.get_security_bars(kline_type, market, code, 0, count)

                if data:
                    results = []
                    for item in data:
                        results.append(
                            {
                                "date": item.get("datetime", ""),
                                "open": item.get("open", 0),
                                "high": item.get("high", 0),
                                "low": item.get("low", 0),
                                "close": item.get("close", 0),
                                "volume": item.get("vol", 0),
                                "amount": item.get("amount", 0),
                            }
                        )
                    return results

            except Exception as e:
                logger.debug(f"TDX 获取 K 线失败 {code} (尝试 {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    # 连接可能已断开，重置后重试
                    self._connected = False
                    import time

                    time.sleep(0.3)
                    continue

        return []

    def reset_connection(self):
        """重置连接状态，强制重新连接"""
        with self._lock:
            if self._api:
                try:
                    self._api.disconnect()
                except:
                    pass
            self._api = None
            self._connected = False
            self._available = None
            self._last_check_time = None
            self._last_use_time = None
            self._fail_count = 0
            # 保留 _last_success_host 以便下次优先尝试
            logger.info("TDX连接已重置")

    def get_connection_status(self) -> Dict:
        """获取连接状态信息（用于调试和监控）"""
        return {
            "connected": self._connected,
            "available": self._available,
            "current_host": self._current_host,
            "last_success_host": self._last_success_host,
            "fail_count": self._fail_count,
            "last_check_time": self._last_check_time.isoformat()
            if self._last_check_time
            else None,
            "last_use_time": self._last_use_time.isoformat()
            if self._last_use_time
            else None,
        }

    def _get_market(self, code: str) -> int:
        """根据股票代码判断市场（0=深圳，1=上海）"""
        if code.startswith(("6", "5", "9")):
            return 1  # 上海
        return 0  # 深圳

    def get_realtime_quote(self, code: str) -> Optional[Dict]:
        """
        获取单只股票实时行情

        Args:
            code: 股票代码，如 "000001"

        Returns:
            行情数据字典，包含 price, change, change_pct, volume 等
        """
        if not self._ensure_connection():
            return None

        try:
            market = self._get_market(code)
            data = self._api.get_security_quotes([(market, code)])

            if not data or len(data) == 0:
                return None

            item = data[0]

            # 计算涨跌幅
            price = item.get("price", 0) or 0
            last_close = item.get("last_close", 0) or 0
            change = price - last_close if last_close else 0
            change_pct = (change / last_close * 100) if last_close else 0

            return {
                "code": code,
                "name": item.get("name", ""),
                "price": price,
                "pre_close": last_close,
                "open": item.get("open", 0) or 0,
                "high": item.get("high", 0) or 0,
                "low": item.get("low", 0) or 0,
                "change": round(change, 2),
                "change_pct": round(change_pct, 2),
                "volume": item.get("vol", 0) or 0,
                "amount": item.get("amount", 0) or 0,
                "bid1": item.get("bid1", 0) or 0,
                "ask1": item.get("ask1", 0) or 0,
                "bid1_vol": item.get("bid_vol1", 0) or 0,
                "ask1_vol": item.get("ask_vol1", 0) or 0,
                "time": datetime.now().strftime("%H:%M:%S"),
                "date": datetime.now().strftime("%Y-%m-%d"),
            }

        except Exception as e:
            logger.error(f"❌ TDX获取行情失败 {code}: {e}")
            return None

    def get_realtime_quotes(self, codes: List[str]) -> List[Dict]:
        """
        批量获取实时行情

        Args:
            codes: 股票代码列表

        Returns:
            行情数据列表
        """
        if not self._ensure_connection():
            return []

        try:
            # 构建查询参数
            params = [(self._get_market(code), code) for code in codes]
            data = self._api.get_security_quotes(params)

            if not data:
                return []

            results = []
            for item in data:
                code = item.get("code", "")
                price = item.get("price", 0) or 0
                last_close = item.get("last_close", 0) or 0
                change = price - last_close if last_close else 0
                change_pct = (change / last_close * 100) if last_close else 0

                results.append(
                    {
                        "code": code,
                        "name": item.get("name", ""),
                        "price": price,
                        "pre_close": last_close,
                        "open": item.get("open", 0) or 0,
                        "high": item.get("high", 0) or 0,
                        "low": item.get("low", 0) or 0,
                        "change": round(change, 2),
                        "change_pct": round(change_pct, 2),
                        "volume": item.get("vol", 0) or 0,
                        "amount": item.get("amount", 0) or 0,
                        "time": datetime.now().strftime("%H:%M:%S"),
                        "date": datetime.now().strftime("%Y-%m-%d"),
                    }
                )

            return results

        except Exception as e:
            logger.error(f"❌ TDX批量获取行情失败: {e}")
            return []

    def get_kline(self, code: str, kline_type: int = 9, count: int = 100) -> List[Dict]:
        """
        获取K线数据

        Args:
            code: 股票代码
            kline_type: K线类型
                0: 5分钟K线
                1: 15分钟K线
                2: 30分钟K线
                3: 1小时K线
                4: 日K线
                5: 周K线
                6: 月K线
                7: 1分钟K线
                8: 1分钟K线
                9: 日K线
                10: 季K线
                11: 年K线
            count: 获取数量

        Returns:
            K线数据列表
        """
        if not self._ensure_connection():
            return []

        try:
            market = self._get_market(code)
            data = self._api.get_security_bars(kline_type, market, code, 0, count)

            if not data:
                return []

            results = []
            for item in data:
                results.append(
                    {
                        "date": item.get("datetime", ""),
                        "open": item.get("open", 0),
                        "high": item.get("high", 0),
                        "low": item.get("low", 0),
                        "close": item.get("close", 0),
                        "volume": item.get("vol", 0),
                        "amount": item.get("amount", 0),
                    }
                )

            return results

        except Exception as e:
            logger.error(f"❌ TDX获取K线失败 {code}: {e}")
            return []

    def get_minute_data(self, code: str) -> List[Dict]:
        """
        获取当日分时数据

        Args:
            code: 股票代码

        Returns:
            分时数据列表
        """
        if not self._ensure_connection():
            return []

        try:
            market = self._get_market(code)
            data = self._api.get_minute_time_data(market, code)

            if not data:
                return []

            results = []
            for item in data:
                results.append(
                    {
                        "time": item.get("time", ""),
                        "price": item.get("price", 0),
                        "volume": item.get("vol", 0),
                    }
                )

            return results

        except Exception as e:
            logger.error(f"❌ TDX获取分时失败 {code}: {e}")
            return []

    def get_history_minute_data(self, code: str, date: str) -> List[Dict]:
        """
        获取历史分时数据

        Args:
            code: 股票代码
            date: 日期，格式 YYYYMMDD

        Returns:
            历史分时数据列表
        """
        if not self._ensure_connection():
            return []

        try:
            market = self._get_market(code)
            # pytdx 使用 get_history_minute_time_data
            data = self._api.get_history_minute_time_data(market, code, int(date))

            if not data:
                return []

            results = []
            for item in data:
                results.append(
                    {
                        "time": item.get("time", ""),
                        "price": item.get("price", 0),
                        "volume": item.get("vol", 0),
                        "date": date,
                    }
                )

            return results

        except Exception as e:
            logger.error(f"❌ TDX获取历史分时失败 {code}: {e}")
            return []

    def get_transaction_data(
        self, code: str, start: int = 0, count: int = 1000
    ) -> List[Dict]:
        """
        获取逐笔成交数据（当日）

        Args:
            code: 股票代码
            start: 起始位置
            count: 获取数量

        Returns:
            逐笔成交数据列表
        """
        if not self._ensure_connection():
            return []

        try:
            market = self._get_market(code)
            data = self._api.get_transaction_data(market, code, start, count)

            if not data:
                return []

            results = []
            for item in data:
                results.append(
                    {
                        "time": item.get("time", ""),
                        "price": item.get("price", 0),
                        "volume": item.get("vol", 0),
                        "num": item.get("num", 0),
                        "buyorsell": item.get("buyorsell", 0),  # 0=买入 1=卖出 2=中性
                    }
                )

            return results

        except Exception as e:
            logger.error(f"❌ TDX获取逐笔成交失败 {code}: {e}")
            return []

    def get_history_transaction_data(
        self, code: str, date: str, start: int = 0, count: int = 1000
    ) -> List[Dict]:
        """
        获取历史逐笔成交数据

        Args:
            code: 股票代码
            date: 日期，格式 YYYYMMDD
            start: 起始位置
            count: 获取数量

        Returns:
            历史逐笔成交数据列表
        """
        if not self._ensure_connection():
            return []

        try:
            market = self._get_market(code)
            data = self._api.get_history_transaction_data(
                market, code, start, count, int(date)
            )

            if not data:
                return []

            results = []
            for item in data:
                results.append(
                    {
                        "time": item.get("time", ""),
                        "price": item.get("price", 0),
                        "volume": item.get("vol", 0),
                        "num": item.get("num", 0),
                        "buyorsell": item.get("buyorsell", 0),
                        "date": date,
                    }
                )

            return results

        except Exception as e:
            logger.error(f"❌ TDX获取历史逐笔成交失败 {code}: {e}")
            return []

    def search_stock(self, keyword: str, limit: int = 50) -> List[Dict]:
        """
        股票搜索（按代码或名称）

        Args:
            keyword: 搜索关键词（代码或名称拼音首字母）
            limit: 最大返回数量，默认50

        Returns:
            匹配的股票列表
        """
        if not self._ensure_connection():
            return []

        try:
            # 获取所有股票列表然后过滤
            results = []

            # 搜索深圳市场
            for market in [0, 1]:  # 0=深圳, 1=上海
                stock_list = self.get_stock_list(market)
                for stock in stock_list:
                    code = stock.get("code", "")
                    name = stock.get("name", "")
                    # 匹配代码或名称
                    if (
                        keyword.lower() in code.lower()
                        or keyword.lower() in name.lower()
                    ):
                        results.append(stock)
                        if len(results) >= limit:  # 最多返回limit条
                            break
                if len(results) >= limit:
                    break

            return results

        except Exception as e:
            logger.error(f"❌ TDX股票搜索失败 {keyword}: {e}")
            return []

    def get_stock_info(self, code: str) -> Optional[Dict]:
        """
        获取股票基本信息

        Args:
            code: 股票代码

        Returns:
            股票基本信息
        """
        if not self._ensure_connection():
            return None

        try:
            market = self._get_market(code)

            # 获取实时行情作为基本信息
            quote = self.get_realtime_quote(code)
            if not quote:
                return None

            # 获取财务信息
            finance = self.get_finance_info(code)

            result = {
                "code": code,
                "name": quote.get("name", ""),
                "market": "上海" if market == 1 else "深圳",
                "price": quote.get("price", 0),
                "pre_close": quote.get("pre_close", 0),
                "open": quote.get("open", 0),
                "high": quote.get("high", 0),
                "low": quote.get("low", 0),
                "volume": quote.get("volume", 0),
                "amount": quote.get("amount", 0),
            }

            # 合并财务信息
            if finance:
                result.update(finance)

            return result

        except Exception as e:
            logger.error(f"❌ TDX获取股票信息失败 {code}: {e}")
            return None

    def get_stock_list(self, market: int = 0, start: int = 0) -> List[Dict]:
        """
        获取股票代码列表

        Args:
            market: 市场（0=深圳，1=上海）
            start: 起始位置

        Returns:
            股票列表
        """
        if not self._ensure_connection():
            return []

        try:
            data = self._api.get_security_list(market, start)

            if not data:
                return []

            results = []
            for item in data:
                code = item.get("code", "")
                # 过滤掉非股票代码
                if not code:
                    continue

                results.append(
                    {
                        "code": code,
                        "name": item.get("name", ""),
                        "market": "上海" if market == 1 else "深圳",
                        "volunit": item.get("volunit", 100),
                        "decimal_point": item.get("decimal_point", 2),
                        "pre_close": item.get("pre_close", 0),
                    }
                )

            return results

        except Exception as e:
            logger.error(f"❌ TDX获取股票列表失败: {e}")
            return []

    def get_all_stock_codes(self) -> List[Dict]:
        """
        获取所有股票代码（深圳+上海）

        Returns:
            所有股票代码列表
        """
        all_stocks = []

        # 深圳市场
        for start in range(0, 10000, 1000):
            stocks = self.get_stock_list(0, start)
            if not stocks:
                break
            all_stocks.extend(stocks)
            if len(stocks) < 1000:
                break

        # 上海市场
        for start in range(0, 10000, 1000):
            stocks = self.get_stock_list(1, start)
            if not stocks:
                break
            all_stocks.extend(stocks)
            if len(stocks) < 1000:
                break

        return all_stocks

    def get_index_bars(
        self, code: str, kline_type: int = 9, count: int = 100
    ) -> List[Dict]:
        """
        获取指数K线数据

        Args:
            code: 指数代码（如 000001=上证指数, 399001=深证成指）
            kline_type: K线类型（同 get_kline）
            count: 获取数量

        Returns:
            指数K线数据列表
        """
        if not self._ensure_connection():
            return []

        try:
            # 指数市场判断
            if code.startswith("399"):
                market = 0  # 深圳指数
            else:
                market = 1  # 上海指数

            data = self._api.get_index_bars(kline_type, market, code, 0, count)

            if not data:
                return []

            results = []
            for item in data:
                results.append(
                    {
                        "date": item.get("datetime", ""),
                        "open": item.get("open", 0),
                        "high": item.get("high", 0),
                        "low": item.get("low", 0),
                        "close": item.get("close", 0),
                        "volume": item.get("vol", 0),
                        "amount": item.get("amount", 0),
                        "up_count": item.get("up_count", 0),
                        "down_count": item.get("down_count", 0),
                    }
                )

            return results

        except Exception as e:
            logger.error(f"❌ TDX获取指数K线失败 {code}: {e}")
            return []

    def get_market_count(self, market: int = 0) -> int:
        """
        获取市场股票数量

        Args:
            market: 市场（0=深圳，1=上海）

        Returns:
            股票数量
        """
        if not self._ensure_connection():
            return 0

        try:
            count = self._api.get_security_count(market)
            return count or 0

        except Exception as e:
            logger.error(f"❌ TDX获取市场数量失败: {e}")
            return 0

    def get_finance_info(self, code: str) -> Optional[Dict]:
        """
        获取财务数据

        Args:
            code: 股票代码

        Returns:
            财务数据字典
        """
        if not self._ensure_connection():
            return None

        try:
            market = self._get_market(code)
            data = self._api.get_finance_info(market, code)

            if not data:
                return None

            return {
                "liutongguben": data.get("liutongguben", 0),  # 流通股本
                "province": data.get("province", 0),  # 省份
                "industry": data.get("industry", 0),  # 行业
                "updated_date": data.get("updated_date", 0),  # 更新日期
                "ipo_date": data.get("ipo_date", 0),  # 上市日期
                "zongguben": data.get("zongguben", 0),  # 总股本
                "guojiagu": data.get("guojiagu", 0),  # 国家股
                "faqirenfarengu": data.get("faqirenfarengu", 0),  # 发起人法人股
                "farengu": data.get("farengu", 0),  # 法人股
                "bgu": data.get("bgu", 0),  # B股
                "hgu": data.get("hgu", 0),  # H股
                "zhigonggu": data.get("zhigonggu", 0),  # 职工股
                "zongzichan": data.get("zongzichan", 0),  # 总资产
                "liudongzichan": data.get("liudongzichan", 0),  # 流动资产
                "gudingzichan": data.get("gudingzichan", 0),  # 固定资产
                "wuxingzichan": data.get("wuxingzichan", 0),  # 无形资产
                "gudongrenshu": data.get("gudongrenshu", 0),  # 股东人数
                "liudongfuzhai": data.get("liudongfuzhai", 0),  # 流动负债
                "changqifuzhai": data.get("changqifuzhai", 0),  # 长期负债
                "zibengongjijin": data.get("zibengongjijin", 0),  # 资本公积金
                "jingzichan": data.get("jingzichan", 0),  # 净资产
                "zhuyingshouru": data.get("zhuyingshouru", 0),  # 主营收入
                "zhuyinglirun": data.get("zhuyinglirun", 0),  # 主营利润
                "yingshouzhangkuan": data.get("yingshouzhangkuan", 0),  # 应收账款
                "yingyelirun": data.get("yingyelirun", 0),  # 营业利润
                "taborunlirun": data.get("taborunlirun", 0),  # 投资收益
                "jinglirun": data.get("jinglirun", 0),  # 净利润
                "weifenlirun": data.get("weifenlirun", 0),  # 未分配利润
                "meigujingzichan": data.get("meigujingzichan", 0),  # 每股净资产
                "baoliu2": data.get("baoliu2", 0),  # 保留
            }

        except Exception as e:
            logger.error(f"❌ TDX获取财务数据失败 {code}: {e}")
            return None

    def get_company_info(self, code: str, info_type: int = 0) -> Optional[str]:
        """
        获取公司信息

        Args:
            code: 股票代码
            info_type: 信息类型
                0: 公司信息
                1: 股本结构
                2: 财务信息
                3: 股东信息
                4: 公司公告

        Returns:
            公司信息文本
        """
        if not self._ensure_connection():
            return None

        try:
            market = self._get_market(code)

            # 获取公司信息文件列表
            file_list = self._api.get_company_info_category(market, code)
            if not file_list:
                return None

            # 根据类型选择文件
            if info_type < len(file_list):
                file_info = file_list[info_type]
                content = self._api.get_company_info_content(
                    market,
                    code,
                    file_info.get("filename", ""),
                    file_info.get("start", 0),
                    file_info.get("length", 0),
                )
                return content

            return None

        except Exception as e:
            logger.error(f"❌ TDX获取公司信息失败 {code}: {e}")
            return None

    def is_trading_day(self, date: str = None) -> bool:
        """
        判断是否为交易日

        Args:
            date: 日期，格式 YYYYMMDD，默认为今天

        Returns:
            是否为交易日
        """
        if date is None:
            date = datetime.now().strftime("%Y%m%d")

        # 周末不是交易日
        try:
            dt = datetime.strptime(date, "%Y%m%d")
            if dt.weekday() >= 5:  # 周六日
                return False
        except:
            return False

        # 尝试获取当日数据来判断
        try:
            # 使用上证指数判断
            kline = self.get_index_bars("000001", 9, 10)
            if kline:
                for bar in kline:
                    bar_date = bar.get("date", "")[:10].replace("-", "")
                    if bar_date == date:
                        return True
            return False
        except:
            # 如果无法判断，假设工作日是交易日
            return True

    def get_block_info(self, block_type: int = 0) -> List[Dict]:
        """
        获取板块信息

        Args:
            block_type: 板块类型
                0: 指数板块
                1: 行业板块
                2: 地区板块
                3: 概念板块

        Returns:
            板块列表
        """
        if not self._ensure_connection():
            return []

        try:
            # pytdx 的板块信息需要通过扩展接口获取
            # 这里使用基础方法
            from pytdx.reader import BlockReader

            # 板块文件路径（需要本地通达信安装）
            # 如果没有本地文件，返回空
            return []

        except Exception as e:
            logger.debug(f"TDX获取板块信息失败: {e}")
            return []

    def get_xdxr_info(self, code: str) -> List[Dict]:
        """
        获取除权除息信息

        Args:
            code: 股票代码

        Returns:
            除权除息信息列表
        """
        if not self._ensure_connection():
            return []

        try:
            market = self._get_market(code)
            data = self._api.get_xdxr_info(market, code)

            if not data:
                return []

            results = []
            for item in data:
                results.append(
                    {
                        "date": item.get("date", ""),
                        "category": item.get("category", 0),  # 1=除权 2=送股 3=分红
                        "fenhong": item.get("fenhong", 0),  # 分红（每10股）
                        "peigujia": item.get("peigujia", 0),  # 配股价
                        "songzhuangu": item.get("songzhuangu", 0),  # 送转股（每10股）
                        "peigu": item.get("peigu", 0),  # 配股（每10股）
                        "suogu": item.get("suogu", 0),  # 缩股
                        "panqianliutong": item.get("panqianliutong", 0),  # 盘前流通
                        "panhouliutong": item.get("panhouliutong", 0),  # 盘后流通
                        "qianzongguben": item.get("qianzongguben", 0),  # 前总股本
                        "houzongguben": item.get("houzongguben", 0),  # 后总股本
                    }
                )

            return results

        except Exception as e:
            logger.error(f"❌ TDX获取除权除息失败 {code}: {e}")
            return []

    def get_kline_by_date(
        self, code: str, start_date: str, end_date: str, kline_type: int = 9
    ) -> List[Dict]:
        """
        按日期范围获取K线数据

        Args:
            code: 股票代码
            start_date: 开始日期 YYYYMMDD
            end_date: 结束日期 YYYYMMDD
            kline_type: K线类型

        Returns:
            K线数据列表
        """
        # 先获取足够多的数据
        all_data = self.get_kline(code, kline_type, 1000)

        if not all_data:
            return []

        # 过滤日期范围
        results = []
        for item in all_data:
            date_str = item.get("date", "")[:10].replace("-", "")
            if start_date <= date_str <= end_date:
                results.append(item)

        return results

    def get_market_stats(self, use_cache: bool = True) -> Dict:
        """
        获取市场统计信息（包含涨跌统计，带缓存）

        Args:
            use_cache: 是否使用缓存，默认True

        Returns:
            市场统计数据，包含涨跌家数、涨跌停等
        """
        import time as time_module

        # 检查缓存
        if use_cache and self._market_stats_cache is not None:
            if self._market_stats_cache_time is not None:
                elapsed = time_module.time() - self._market_stats_cache_time
                if elapsed < self._market_stats_cache_ttl:
                    logger.debug(
                        f"TDX市场统计使用缓存 (剩余{int(self._market_stats_cache_ttl - elapsed)}秒)"
                    )
                    return self._market_stats_cache

        if not self._ensure_connection():
            return {}

        try:
            start_time = time_module.time()

            # 直接使用pytdx的底层API获取股票列表
            all_stocks = []

            # 深圳市场（A股在前面，从0开始）
            for start in range(0, 6000, 1000):
                try:
                    stocks = self._api.get_security_list(0, start)
                    if not stocks:
                        break
                    for s in stocks:
                        code = s.get("code", "")
                        if code.startswith(("00", "30")):
                            all_stocks.append((0, code))
                    if len(stocks) < 1000:
                        break
                except Exception:
                    break

            sz_count = len(all_stocks)

            # 上海市场（A股在较后位置，从0开始遍历，但60/68开头的在后面）
            # pytdx的上海市场股票列表中，A股（60/68开头）在较后的位置
            for start in range(0, 6000, 1000):
                try:
                    stocks = self._api.get_security_list(1, start)
                    if not stocks:
                        break
                    for s in stocks:
                        code = s.get("code", "")
                        if code.startswith(("60", "68")):
                            all_stocks.append((1, code))
                    if len(stocks) < 1000:
                        break
                except Exception:
                    break

            if not all_stocks or len(all_stocks) < 100:
                logger.warning(f"TDX获取股票列表异常: {len(all_stocks)}")
                return {}

            logger.debug(
                f"TDX获取到 {len(all_stocks)} 只A股 (深圳:{sz_count}, 上海:{len(all_stocks) - sz_count})"
            )

            # 批量获取行情统计涨跌 - 直接使用底层API
            up_count = 0
            down_count = 0
            flat_count = 0
            limit_up = 0
            limit_down = 0
            up_5_pct = 0
            up_3_pct = 0
            down_3_pct = 0
            down_5_pct = 0
            total_count = 0

            batch_size = 80  # pytdx最大支持80只
            for i in range(0, len(all_stocks), batch_size):
                batch = all_stocks[i : i + batch_size]
                stock_list = [(m, c) for m, c in batch]

                try:
                    quotes = self._api.get_security_quotes(stock_list)
                    if not quotes:
                        continue

                    for q in quotes:
                        if not q or q.get("last_close", 0) <= 0:
                            continue

                        last_close = q["last_close"]
                        price = q.get("price", 0) or 0
                        if price <= 0:
                            continue

                        change_pct = (price - last_close) / last_close * 100
                        total_count += 1

                        if change_pct > 0.01:
                            up_count += 1
                            if change_pct >= 5:
                                up_5_pct += 1
                            elif change_pct >= 3:
                                up_3_pct += 1
                        elif change_pct < -0.01:
                            down_count += 1
                            if change_pct <= -5:
                                down_5_pct += 1
                            elif change_pct <= -3:
                                down_3_pct += 1
                        else:
                            flat_count += 1

                        # 涨停跌停判断
                        code = q.get("code", "")
                        if code.startswith(("30", "68")):
                            limit_threshold = 19.5
                        else:
                            limit_threshold = 9.5

                        if change_pct >= limit_threshold:
                            limit_up += 1
                        elif change_pct <= -limit_threshold:
                            limit_down += 1

                except Exception as e:
                    logger.debug(f"TDX批量获取行情失败: {e}")
                    continue

            if total_count == 0:
                return {}

            # 计算市场情绪得分
            sentiment_score = round((up_count - down_count) / total_count * 100, 2)

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

            result = {
                "total_stocks": total_count,
                "up_count": up_count,
                "down_count": down_count,
                "flat_count": flat_count,
                "up_ratio": round(up_count / total_count * 100, 2)
                if total_count > 0
                else 0,
                "limit_up": limit_up,
                "limit_down": limit_down,
                "up_5_pct": up_5_pct,
                "up_3_pct": up_3_pct,
                "down_3_pct": down_3_pct,
                "down_5_pct": down_5_pct,
                "sentiment_score": sentiment_score,
                "sentiment_level": sentiment_level,
                "shanghai_count": len(all_stocks) - sz_count,
                "shenzhen_count": sz_count,
                "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }

            elapsed = time_module.time() - start_time
            logger.info(
                f"TDX市场统计: 总{total_count}, 涨{up_count}, 跌{down_count}, 涨停{limit_up}, 跌停{limit_down} (耗时{elapsed:.1f}秒)"
            )

            # 更新缓存
            self._market_stats_cache = result
            self._market_stats_cache_time = time_module.time()

            return result

        except Exception as e:
            logger.error(f"❌ TDX获取市场统计失败: {e}")
            return {}

    def test_server_latency(
        self, host: str, port: int, timeout: float = 3.0
    ) -> Optional[float]:
        """
        测试单个服务器的延迟

        Args:
            host: 服务器IP
            port: 端口
            timeout: 超时时间（秒）

        Returns:
            延迟时间（毫秒），失败返回 None
        """
        import time as time_module
        import socket

        try:
            start = time_module.time()
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            sock.connect((host, port))
            sock.close()
            latency = (time_module.time() - start) * 1000  # 转换为毫秒
            return round(latency, 2)
        except Exception:
            return None

    def get_best_servers(
        self, top_n: int = 5, force_refresh: bool = False
    ) -> List[Dict]:
        """
        获取最快的服务器列表（带缓存）

        Args:
            top_n: 返回前N个最快的服务器
            force_refresh: 是否强制刷新缓存

        Returns:
            服务器列表，按延迟排序
        """
        import time as time_module
        import concurrent.futures

        now = time_module.time()

        # 检查缓存
        if not force_refresh and TDXNativeProvider._server_latency_cache:
            if TDXNativeProvider._server_latency_cache_time:
                elapsed = now - TDXNativeProvider._server_latency_cache_time
                if elapsed < TDXNativeProvider._server_latency_cache_ttl:
                    cached = TDXNativeProvider._server_latency_cache
                    return sorted(cached, key=lambda x: x.get("latency", 9999))[:top_n]

        # 收集所有服务器
        all_servers = []
        for h in self.HOSTS_SHANGHAI:
            all_servers.append({"ip": h[0], "port": h[1], "region": h[2]})
        for h in self.HOSTS_BEIJING:
            all_servers.append({"ip": h[0], "port": h[1], "region": h[2]})
        for h in self.HOSTS_GUANGZHOU:
            all_servers.append({"ip": h[0], "port": h[1], "region": h[2]})
        for h in self.HOSTS_WUHAN:
            all_servers.append({"ip": h[0], "port": h[1], "region": h[2]})

        # 并发测试所有服务器
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            future_to_server = {
                executor.submit(self.test_server_latency, s["ip"], s["port"]): s
                for s in all_servers
            }
            for future in concurrent.futures.as_completed(future_to_server, timeout=10):
                server = future_to_server[future]
                try:
                    latency = future.result()
                    if latency is not None:
                        results.append(
                            {
                                "ip": server["ip"],
                                "port": server["port"],
                                "region": server["region"],
                                "latency": latency,
                                "status": "ok",
                            }
                        )
                    else:
                        results.append(
                            {
                                "ip": server["ip"],
                                "port": server["port"],
                                "region": server["region"],
                                "latency": 9999,
                                "status": "timeout",
                            }
                        )
                except Exception:
                    results.append(
                        {
                            "ip": server["ip"],
                            "port": server["port"],
                            "region": server["region"],
                            "latency": 9999,
                            "status": "error",
                        }
                    )

        # 更新缓存
        TDXNativeProvider._server_latency_cache = results
        TDXNativeProvider._server_latency_cache_time = now

        # 按延迟排序返回
        sorted_results = sorted(results, key=lambda x: x.get("latency", 9999))
        logger.info(
            f"TDX服务器测速完成: {len([r for r in results if r['status'] == 'ok'])}/{len(results)} 可用"
        )

        return sorted_results[:top_n]

    def switch_to_best_server(self) -> bool:
        """
        切换到最快的服务器

        Returns:
            是否切换成功
        """
        best_servers = self.get_best_servers(top_n=3, force_refresh=True)

        if not best_servers or best_servers[0].get("status") != "ok":
            logger.warning("没有可用的TDX服务器")
            return False

        best = best_servers[0]
        new_host = (best["ip"], best["port"])

        # 如果已经是最快的服务器，不需要切换
        if self._current_host == new_host:
            logger.info(
                f"当前已连接最快服务器: {best['ip']}:{best['port']} ({best['region']}) - {best['latency']}ms"
            )
            return True

        # 断开当前连接
        self.disconnect()

        # 设置优先服务器
        self._last_success_host = new_host

        # 重新连接
        if self._ensure_connection():
            logger.info(
                f"已切换到最快服务器: {best['ip']}:{best['port']} ({best['region']}) - {best['latency']}ms"
            )
            return True

        return False

    def get_server_list(self) -> Dict:
        """
        获取所有服务器列表（按地区分组）

        Returns:
            服务器列表字典
        """
        return {
            "shanghai": [
                {"ip": h[0], "port": h[1], "name": h[2]} for h in self.HOSTS_SHANGHAI
            ],
            "beijing": [
                {"ip": h[0], "port": h[1], "name": h[2]} for h in self.HOSTS_BEIJING
            ],
            "guangzhou": [
                {"ip": h[0], "port": h[1], "name": h[2]} for h in self.HOSTS_GUANGZHOU
            ],
            "wuhan": [
                {"ip": h[0], "port": h[1], "name": h[2]} for h in self.HOSTS_WUHAN
            ],
            "legacy": [
                {"ip": h[0], "port": h[1], "name": h[2]} for h in self.HOSTS_LEGACY
            ],
            "total_count": len(self.HOSTS_SHANGHAI)
            + len(self.HOSTS_BEIJING)
            + len(self.HOSTS_GUANGZHOU)
            + len(self.HOSTS_WUHAN)
            + len(self.HOSTS_LEGACY),
        }

    def calculate_technical_indicators(
        self, code: str, kline_type: int = 9, count: int = 200
    ) -> Optional[Dict]:
        """
        计算技术指标

        Args:
            code: 股票代码
            kline_type: K线类型（9=日K线）
            count: K线数量

        Returns:
            技术指标字典
        """
        try:
            import pandas as pd

            # 获取K线数据
            kline_data = self.get_kline(code, kline_type, count)

            if not kline_data or len(kline_data) < 60:
                logger.warning(f"K线数据不足，无法计算技术指标: {code}")
                return None

            df = pd.DataFrame(kline_data)

            # 计算均线
            df["ma5"] = df["close"].rolling(window=5).mean()
            df["ma10"] = df["close"].rolling(window=10).mean()
            df["ma20"] = df["close"].rolling(window=20).mean()
            df["ma60"] = df["close"].rolling(window=60).mean()

            # 计算MACD
            df = self._calculate_macd(df)

            # 计算RSI
            df = self._calculate_rsi(df)

            # 计算KDJ
            df = self._calculate_kdj(df)

            # 计算布林带
            df = self._calculate_bollinger(df)

            # 计算量能均线
            df["vol_ma5"] = df["volume"].rolling(window=5).mean()
            df["vol_ma10"] = df["volume"].rolling(window=10).mean()

            # 取最新数据
            latest = df.iloc[-1]

            # 判断趋势
            current_price = float(latest["close"])
            ma5 = float(latest["ma5"]) if pd.notna(latest["ma5"]) else current_price
            ma20 = float(latest["ma20"]) if pd.notna(latest["ma20"]) else current_price
            ma60 = float(latest["ma60"]) if pd.notna(latest["ma60"]) else current_price

            if current_price > ma5 > ma20 > ma60:
                trend = "up"
            elif current_price < ma5 < ma20 < ma60:
                trend = "down"
            else:
                trend = "sideways"

            return {
                "code": code,
                "ma5": round(ma5, 2),
                "ma10": round(float(latest["ma10"]), 2)
                if pd.notna(latest["ma10"])
                else None,
                "ma20": round(ma20, 2),
                "ma60": round(ma60, 2) if pd.notna(latest["ma60"]) else None,
                "trend": trend,
                "macd_dif": round(float(latest["dif"]), 4)
                if pd.notna(latest.get("dif"))
                else None,
                "macd_dea": round(float(latest["dea"]), 4)
                if pd.notna(latest.get("dea"))
                else None,
                "macd": round(float(latest["macd"]), 4)
                if pd.notna(latest.get("macd"))
                else None,
                "rsi6": round(float(latest["rsi6"]), 2)
                if pd.notna(latest.get("rsi6"))
                else None,
                "rsi12": round(float(latest["rsi12"]), 2)
                if pd.notna(latest.get("rsi12"))
                else None,
                "rsi24": round(float(latest["rsi24"]), 2)
                if pd.notna(latest.get("rsi24"))
                else None,
                "kdj_k": round(float(latest["kdj_k"]), 2)
                if pd.notna(latest.get("kdj_k"))
                else None,
                "kdj_d": round(float(latest["kdj_d"]), 2)
                if pd.notna(latest.get("kdj_d"))
                else None,
                "kdj_j": round(float(latest["kdj_j"]), 2)
                if pd.notna(latest.get("kdj_j"))
                else None,
                "boll_upper": round(float(latest["boll_upper"]), 2)
                if pd.notna(latest.get("boll_upper"))
                else None,
                "boll_mid": round(float(latest["boll_mid"]), 2)
                if pd.notna(latest.get("boll_mid"))
                else None,
                "boll_lower": round(float(latest["boll_lower"]), 2)
                if pd.notna(latest.get("boll_lower"))
                else None,
                "vol_ma5": round(float(latest["vol_ma5"]), 0)
                if pd.notna(latest.get("vol_ma5"))
                else None,
                "vol_ma10": round(float(latest["vol_ma10"]), 0)
                if pd.notna(latest.get("vol_ma10"))
                else None,
                "volume_ratio": round(
                    float(latest["volume"]) / float(latest["vol_ma5"]), 2
                )
                if latest.get("vol_ma5") and latest["vol_ma5"] > 0
                else 1.0,
                "data_source": "tdx_native",
            }

        except Exception as e:
            logger.error(f"❌ TDX计算技术指标失败 {code}: {e}")
            return None

    def _calculate_macd(self, df, fast: int = 12, slow: int = 26, signal: int = 9):
        """计算MACD"""
        import pandas as pd

        ema_fast = df["close"].ewm(span=fast, adjust=False).mean()
        ema_slow = df["close"].ewm(span=slow, adjust=False).mean()
        df["dif"] = ema_fast - ema_slow
        df["dea"] = df["dif"].ewm(span=signal, adjust=False).mean()
        df["macd"] = (df["dif"] - df["dea"]) * 2
        return df

    def _calculate_rsi(self, df, periods: List[int] = None):
        """计算RSI"""
        import pandas as pd

        if periods is None:
            periods = [6, 12, 24]
        for period in periods:
            delta = df["close"].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            df[f"rsi{period}"] = 100 - (100 / (1 + rs))
        return df

    def _calculate_kdj(self, df, n: int = 9, m1: int = 3, m2: int = 3):
        """计算KDJ"""
        import pandas as pd

        low_list = df["low"].rolling(window=n).min()
        high_list = df["high"].rolling(window=n).max()
        rsv = (df["close"] - low_list) / (high_list - low_list) * 100
        df["kdj_k"] = rsv.ewm(com=m1 - 1, adjust=False).mean()
        df["kdj_d"] = df["kdj_k"].ewm(com=m2 - 1, adjust=False).mean()
        df["kdj_j"] = 3 * df["kdj_k"] - 2 * df["kdj_d"]
        return df

    def _calculate_bollinger(self, df, period: int = 20, std_num: int = 2):
        """计算布林带"""
        import pandas as pd

        df["boll_mid"] = df["close"].rolling(window=period).mean()
        std = df["close"].rolling(window=period).std()
        df["boll_upper"] = df["boll_mid"] + std_num * std
        df["boll_lower"] = df["boll_mid"] - std_num * std
        return df

    def disconnect(self):
        """断开连接"""
        if self._api and self._connected:
            try:
                self._api.disconnect()
            except:
                pass
            self._connected = False
            self._api = None
            logger.info("TDX连接已断开")

    def __del__(self):
        """析构时断开连接"""
        self.disconnect()


# 全局单例
_tdx_native_provider = None
_provider_lock = threading.Lock()


def get_tdx_native_provider() -> TDXNativeProvider:
    """获取 TDX Native Provider 单例"""
    global _tdx_native_provider

    if _tdx_native_provider is None:
        with _provider_lock:
            if _tdx_native_provider is None:
                _tdx_native_provider = TDXNativeProvider()

    return _tdx_native_provider


def get_tdx_provider() -> TDXNativeProvider:
    """
    获取TDX Provider的统一入口（兼容旧代码）

    直接返回Native Provider，不再使用HTTP Provider。
    Native Provider使用pytdx直接连接通达信服务器，无需外部服务。

    Returns:
        TDXNativeProvider: TDX Native Provider实例
    """
    return get_tdx_native_provider()


def is_tdx_available() -> bool:
    """
    检查TDX服务是否可用

    Returns:
        bool: TDX Native Provider是否可用
    """
    try:
        provider = get_tdx_native_provider()
        return provider.is_available()
    except Exception:
        return False
