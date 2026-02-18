#!/usr/bin/env python3
"""
数据源管理器
统一管理中国股票数据源的选择和切换
支持TDX(通达信)、AKShare、Tushare、聚合数据等

优先级: TDX > AKShare > Tushare > 聚合数据
（新闻类数据TDX不支持，优先级为: AKShare > Tushare）
"""

import os
import time
from typing import Dict, List, Optional, Any
from enum import Enum
import warnings
import pandas as pd
from pathlib import Path

# 加载环境变量
try:
    from dotenv import load_dotenv
    # 查找 .env 文件
    env_path = Path(__file__).parent.parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"[数据源管理器] 已加载环境变量: {env_path}")
except ImportError:
    print("[数据源管理器] 警告: python-dotenv 未安装，无法加载 .env 文件")

# 导入统一日志系统
from backend.utils.logging_config import get_logger
logger = get_logger("dataflow")
warnings.filterwarnings('ignore')


class ChinaDataSource(Enum):
    """中国股票数据源枚举"""
    TDX = "tdx"           # 通达信 - 最高优先级
    AKSHARE = "akshare"
    JUHE = "juhe"
    SINA = "sina"
    TUSHARE = "tushare"
    BAOSTOCK = "baostock"





class DataSourceManager:
    """数据源管理器"""

    def __init__(self):
        """初始化数据源管理器"""
        self.default_source = self._get_default_source()
        self.available_sources = self._check_available_sources()
        self.current_source = self.default_source

        # 初始化断路器
        self._init_circuit_breakers()

        logger.info(f"📊 数据源管理器初始化完成")
        logger.info(f"   默认数据源: {self.default_source.value}")
        logger.info(f"   可用数据源: {[s.value for s in self.available_sources]}")

    def _init_circuit_breakers(self):
        """初始化各数据源的断路器"""
        try:
            from backend.dataflows.utils.circuit_breaker import get_data_source_breaker
            self._breakers = {
                ChinaDataSource.TDX: get_data_source_breaker("tdx"),
                ChinaDataSource.AKSHARE: get_data_source_breaker("akshare"),
                ChinaDataSource.TUSHARE: get_data_source_breaker("tushare"),
                ChinaDataSource.SINA: get_data_source_breaker("sina"),
                ChinaDataSource.JUHE: get_data_source_breaker("juhe"),
                ChinaDataSource.BAOSTOCK: get_data_source_breaker("baostock"),
            }
            logger.debug("断路器初始化完成")
        except Exception as e:
            logger.warning(f"断路器初始化失败，将不使用断路器保护: {e}")
            self._breakers = {}

    def _can_use_source(self, source: ChinaDataSource) -> bool:
        """检查数据源是否可用（断路器未熔断）"""
        if not self._breakers:
            return True
        breaker = self._breakers.get(source)
        if breaker:
            return breaker.can_execute()
        return True

    def _record_source_success(self, source: ChinaDataSource):
        """记录数据源调用成功"""
        if self._breakers:
            breaker = self._breakers.get(source)
            if breaker:
                breaker.record_success()

    def _record_source_failure(self, source: ChinaDataSource):
        """记录数据源调用失败"""
        if self._breakers:
            breaker = self._breakers.get(source)
            if breaker:
                breaker.record_failure()

    def _get_default_source(self) -> ChinaDataSource:
        """获取默认数据源"""
        # 从环境变量获取，默认使用TDX作为第一优先级数据源
        env_source = os.getenv('DEFAULT_CHINA_DATA_SOURCE', 'tdx').lower()

        # 映射到枚举
        source_mapping = {
            'tdx': ChinaDataSource.TDX,
            'akshare': ChinaDataSource.AKSHARE,
            'juhe': ChinaDataSource.JUHE,
            'sina': ChinaDataSource.SINA,
            'tushare': ChinaDataSource.TUSHARE,
            'baostock': ChinaDataSource.BAOSTOCK
        }

        return source_mapping.get(env_source, ChinaDataSource.TDX)

    # ==================== Tushare数据接口 ====================

    def get_china_stock_data_tushare(self, symbol: str, start_date: str, end_date: str) -> str:
        """
        使用Tushare获取中国A股历史数据

        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            str: 格式化的股票数据报告
        """
        # 临时切换到Tushare数据源
        original_source = self.current_source
        self.current_source = ChinaDataSource.TUSHARE

        try:
            result = self._get_tushare_data(symbol, start_date, end_date)
            return result
        finally:
            # 恢复原始数据源
            self.current_source = original_source

    def search_china_stocks_tushare(self, keyword: str) -> str:
        """
        使用Tushare搜索中国股票

        Args:
            keyword: 搜索关键词

        Returns:
            str: 搜索结果
        """
        try:
            from .tushare_adapter import get_tushare_adapter

            logger.debug(f"🔍 [Tushare] 搜索股票: {keyword}")

            adapter = get_tushare_adapter()
            results = adapter.search_stocks(keyword)

            if results is not None and not results.empty:
                result = f"搜索关键词: {keyword}\n"
                result += f"找到 {len(results)} 只股票:\n\n"

                # 显示前10个结果
                for idx, row in results.head(10).iterrows():
                    result += f"代码: {row.get('symbol', '')}\n"
                    result += f"名称: {row.get('name', '未知')}\n"
                    result += f"行业: {row.get('industry', '未知')}\n"
                    result += f"地区: {row.get('area', '未知')}\n"
                    result += f"上市日期: {row.get('list_date', '未知')}\n"
                    result += "-" * 30 + "\n"

                return result
            else:
                return f"❌ 未找到匹配'{keyword}'的股票"

        except Exception as e:
            logger.error(f"❌ [Tushare] 搜索股票失败: {e}")
            return f"❌ 搜索股票失败: {e}"

    def get_china_stock_fundamentals_tushare(self, symbol: str) -> str:
        """
        使用Tushare获取中国股票基本面数据

        Args:
            symbol: 股票代码

        Returns:
            str: 基本面分析报告
        """
        try:
            from .tushare_adapter import get_tushare_adapter

            logger.debug(f"📊 [Tushare] 获取{symbol}基本面数据...")

            adapter = get_tushare_adapter()
            fundamentals = adapter.get_fundamentals(symbol)

            if fundamentals:
                return fundamentals
            else:
                return f"❌ 未获取到{symbol}的基本面数据"

        except Exception as e:
            logger.error(f"❌ [Tushare] 获取基本面数据失败: {e}")
            return f"❌ 获取{symbol}基本面数据失败: {e}"

    def get_china_stock_info_tushare(self, symbol: str) -> str:
        """
        使用Tushare获取中国股票基本信息

        Args:
            symbol: 股票代码

        Returns:
            str: 股票基本信息
        """
        try:
            from .tushare_adapter import get_tushare_adapter

            logger.debug(f"📊 [Tushare] 获取{symbol}股票信息...")

            adapter = get_tushare_adapter()
            stock_info = adapter.get_stock_info(symbol)

            if stock_info:
                result = f"📊 {stock_info.get('name', '未知')}({symbol}) - 股票信息\n"
                result += f"股票代码: {stock_info.get('symbol', symbol)}\n"
                result += f"股票名称: {stock_info.get('name', '未知')}\n"
                result += f"所属行业: {stock_info.get('industry', '未知')}\n"
                result += f"所属地区: {stock_info.get('area', '未知')}\n"
                result += f"上市日期: {stock_info.get('list_date', '未知')}\n"
                result += f"市场类型: {stock_info.get('market', '未知')}\n"
                result += f"交易所: {stock_info.get('exchange', '未知')}\n"
                result += f"货币单位: {stock_info.get('curr_type', 'CNY')}\n"

                return result
            else:
                return f"❌ 未获取到{symbol}的股票信息"

        except Exception as e:
            logger.error(f"❌ [Tushare] 获取股票信息失败: {e}", exc_info=True)
            return f"❌ 获取{symbol}股票信息失败: {e}"
    
    def _check_available_sources(self) -> List[ChinaDataSource]:
        """检查可用的数据源"""
        available = []

        # 检查TDX（通达信）- 最高优先级
        # 优先检查 TDX Native Provider（纯Python，无需Docker）
        tdx_available = False
        try:
            from .providers.tdx_native_provider import get_tdx_native_provider
            native_provider = get_tdx_native_provider()
            if native_provider.is_available():
                tdx_available = True
                available.append(ChinaDataSource.TDX)
                logger.info("✅ TDX Native(通达信纯Python)数据源可用 - 最高优先级")
        except ImportError as e:
            logger.debug(f"TDX Native Provider不可用: {e}")
        except Exception as e:
            logger.debug(f"TDX Native Provider检查失败: {e}")

        # 如果Native不可用，降级到HTTP Provider
        if not tdx_available:
            try:
                from .providers.tdx_provider import get_tdx_provider, is_tdx_available
                if is_tdx_available():
                    available.append(ChinaDataSource.TDX)
                    logger.info("✅ TDX HTTP(通达信Docker服务)数据源可用 - 最高优先级")
                else:
                    logger.warning("⚠️ TDX(通达信)数据源不可用: 服务未启动或无法连接")
            except ImportError as e:
                logger.warning(f"⚠️ TDX(通达信)数据源不可用: 模块导入失败 - {e}")
            except Exception as e:
                logger.warning(f"⚠️ TDX(通达信)数据源不可用: {e}")

        # 检查Tushare
        try:
            import tushare as ts
            token = os.getenv('TUSHARE_TOKEN')
            if token:
                available.append(ChinaDataSource.TUSHARE)
                logger.info("✅ Tushare数据源可用")
            else:
                logger.warning("⚠️ Tushare数据源不可用: 未设置TUSHARE_TOKEN")
        except ImportError:
            logger.warning("⚠️ Tushare数据源不可用: 库未安装")

        # 检查AKShare
        try:
            import akshare as ak
            available.append(ChinaDataSource.AKSHARE)
            logger.info("✅ AKShare数据源可用")
        except ImportError:
            logger.warning("⚠️ AKShare数据源不可用: 库未安装")

        # 检查聚合数据
        juhe_key = os.getenv('JUHE_API_KEY', '')
        if juhe_key:
            available.append(ChinaDataSource.JUHE)
            logger.info("✅ 聚合数据源可用（免费版每天50次）")
        else:
            logger.warning("⚠️ 聚合数据源不可用: 未设置JUHE_API_KEY")

        # 检查新浪财经
        try:
            # 新浪财经不需要 API Key，直接可用
            available.append(ChinaDataSource.SINA)
            logger.info("✅ 新浪财经数据源可用（免费、无限制）")
        except Exception as e:
            logger.warning(f"⚠️ 新浪财经数据源不可用: {e}")

        # 检查BaoStock
        try:
            import baostock as bs
            available.append(ChinaDataSource.BAOSTOCK)
            logger.info(f"✅ BaoStock数据源可用")
        except ImportError:
            logger.warning(f"⚠️ BaoStock数据源不可用: 库未安装")

        return available
    
    def get_current_source(self) -> ChinaDataSource:
        """获取当前数据源"""
        return self.current_source
    
    def set_current_source(self, source: ChinaDataSource) -> bool:
        """设置当前数据源"""
        if source in self.available_sources:
            self.current_source = source
            logger.info(f"✅ 数据源已切换到: {source.value}")
            return True
        else:
            logger.error(f"❌ 数据源不可用: {source.value}")
            return False
    
    def get_data_adapter(self):
        """获取当前数据源的适配器"""
        if self.current_source == ChinaDataSource.TDX:
            return self._get_tdx_adapter()
        elif self.current_source == ChinaDataSource.TUSHARE:
            return self._get_tushare_adapter()
        elif self.current_source == ChinaDataSource.AKSHARE:
            return self._get_akshare_adapter()
        elif self.current_source == ChinaDataSource.BAOSTOCK:
            return self._get_baostock_adapter()
        else:
            raise ValueError(f"不支持的数据源: {self.current_source}")

    def _get_tdx_adapter(self):
        """获取TDX适配器 - 优先使用Native Provider"""
        # 优先尝试 Native Provider
        try:
            from .providers.tdx_native_provider import get_tdx_native_provider
            provider = get_tdx_native_provider()
            if provider.is_available():
                return provider
        except ImportError:
            pass
        except Exception as e:
            logger.debug(f"TDX Native Provider获取失败: {e}")

        # 降级到 HTTP Provider
        try:
            from .providers.tdx_provider import get_tdx_provider
            return get_tdx_provider()
        except ImportError as e:
            logger.error(f"❌ TDX适配器导入失败: {e}")
            return None
    
    def _get_tushare_adapter(self):
        """获取Tushare适配器"""
        try:
            from .tushare_adapter import get_tushare_adapter
            return get_tushare_adapter()
        except ImportError as e:
            logger.error(f"❌ Tushare适配器导入失败: {e}")
            return None
    
    def _get_akshare_adapter(self):
        """获取AKShare适配器"""
        try:
            from .stock.akshare_utils import get_akshare_provider
            return get_akshare_provider()
        except ImportError as e:
            logger.error(f"[FAIL] AKShare适配器导入失败: {e}")
            return None
    
    def _get_baostock_adapter(self):
        """获取BaoStock适配器"""
        try:
            from .baostock_utils import get_baostock_provider
            return get_baostock_provider()
        except ImportError as e:
            logger.error(f"❌ BaoStock适配器导入失败: {e}")
            return None
    
    def get_stock_data(self, symbol: str, start_date: str = None, end_date: str = None) -> str:
        """
        获取股票数据的统一接口

        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            str: 格式化的股票数据
        """
        # 记录详细的输入参数
        logger.info(f"📊 [数据获取] 开始获取股票数据",
                   extra={
                       'symbol': symbol,
                       'start_date': start_date,
                       'end_date': end_date,
                       'data_source': self.current_source.value,
                       'event_type': 'data_fetch_start'
                   })

        # 添加详细的股票代码追踪日志
        logger.info(f"🔍 [股票代码追踪] DataSourceManager.get_stock_data 接收到的股票代码: '{symbol}' (类型: {type(symbol)})")
        logger.info(f"🔍 [股票代码追踪] 股票代码长度: {len(str(symbol))}")
        logger.info(f"🔍 [股票代码追踪] 股票代码字符: {list(str(symbol))}")
        logger.info(f"🔍 [股票代码追踪] 当前数据源: {self.current_source.value}")

        start_time = time.time()

        try:
            # 根据数据源调用相应的获取方法
            if self.current_source == ChinaDataSource.TDX:
                logger.info(f"🔍 [股票代码追踪] 调用 TDX 数据源，传入参数: symbol='{symbol}'")
                result = self._get_tdx_data(symbol, start_date, end_date)
            elif self.current_source == ChinaDataSource.AKSHARE:
                result = self._get_akshare_data(symbol, start_date, end_date)
            elif self.current_source == ChinaDataSource.JUHE:
                result = self._get_juhe_data(symbol, start_date, end_date)
            elif self.current_source == ChinaDataSource.SINA:
                result = self._get_sina_data(symbol, start_date, end_date)
            elif self.current_source == ChinaDataSource.TUSHARE:
                logger.info(f"🔍 [股票代码追踪] 调用 Tushare 数据源，传入参数: symbol='{symbol}'")
                result = self._get_tushare_data(symbol, start_date, end_date)
            elif self.current_source == ChinaDataSource.BAOSTOCK:
                result = self._get_baostock_data(symbol, start_date, end_date)
            else:
                result = f"❌ 不支持的数据源: {self.current_source.value}"

            # 记录详细的输出结果
            duration = time.time() - start_time
            result_length = len(result) if result else 0
            is_success = result and "❌" not in result and "错误" not in result

            if is_success:
                logger.info(f"✅ [数据获取] 成功获取股票数据",
                           extra={
                               'symbol': symbol,
                               'start_date': start_date,
                               'end_date': end_date,
                               'data_source': self.current_source.value,
                               'duration': duration,
                               'result_length': result_length,
                               'result_preview': result[:200] + '...' if result_length > 200 else result,
                               'event_type': 'data_fetch_success'
                           })
                return result
            else:
                logger.warning(f"⚠️ [数据获取] 数据质量异常，尝试降级到其他数据源",
                              extra={
                                  'symbol': symbol,
                                  'start_date': start_date,
                                  'end_date': end_date,
                                  'data_source': self.current_source.value,
                                  'duration': duration,
                                  'result_length': result_length,
                                  'result_preview': result[:200] + '...' if result_length > 200 else result,
                                  'event_type': 'data_fetch_warning'
                              })

                # 数据质量异常时也尝试降级到其他数据源
                fallback_result = self._try_fallback_sources(symbol, start_date, end_date)
                if fallback_result and "❌" not in fallback_result and "错误" not in fallback_result:
                    logger.info(f"✅ [数据获取] 降级成功获取数据")
                    return fallback_result
                else:
                    logger.error(f"❌ [数据获取] 所有数据源都无法获取有效数据")
                    return result  # 返回原始结果（包含错误信息）

        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"❌ [数据获取] 异常失败: {e}",
                        extra={
                            'symbol': symbol,
                            'start_date': start_date,
                            'end_date': end_date,
                            'data_source': self.current_source.value,
                            'duration': duration,
                            'error': str(e),
                            'event_type': 'data_fetch_exception'
                        }, exc_info=True)
            return self._try_fallback_sources(symbol, start_date, end_date)

    def _get_tdx_data(self, symbol: str, start_date: str, end_date: str) -> str:
        """使用TDX(通达信)获取数据 - 最高优先级数据源，优先使用Native Provider"""
        logger.debug(f"📊 [TDX] 调用参数: symbol={symbol}, start_date={start_date}, end_date={end_date}")

        start_time = time.time()

        # 优先尝试 Native Provider
        try:
            from .providers.tdx_native_provider import get_tdx_native_provider
            native_provider = get_tdx_native_provider()

            if native_provider.is_available():
                logger.debug("📊 [TDX] 使用 Native Provider")

                # 获取K线数据
                kline_data = native_provider.get_kline_by_date(symbol, start_date, end_date, kline_type=9)

                if kline_data:
                    import pandas as pd
                    df = pd.DataFrame(kline_data)

                    # 获取股票名称
                    search_results = native_provider.search_stock(symbol, limit=1)
                    stock_name = search_results[0].get('name', f'股票{symbol}') if search_results else f'股票{symbol}'

                    # 计算最新价格和涨跌幅
                    latest_data = df.iloc[-1]
                    latest_price = latest_data.get('close', 0)
                    prev_close = df.iloc[-2].get('close', latest_price) if len(df) > 1 else latest_price
                    change = latest_price - prev_close
                    change_pct = (change / prev_close * 100) if prev_close != 0 else 0

                    # 格式化数据报告
                    result = f"📊 {stock_name}({symbol}) - TDX Native数据\n"
                    result += f"数据期间: {start_date} 至 {end_date}\n"
                    result += f"数据条数: {len(df)}条\n\n"

                    result += f"💰 最新价格: ¥{latest_price:.2f}\n"
                    result += f"📈 涨跌额: {change:+.2f} ({change_pct:+.2f}%)\n\n"

                    # 添加统计信息
                    result += f"📊 价格统计:\n"
                    result += f"   最高价: ¥{df['high'].max():.2f}\n"
                    result += f"   最低价: ¥{df['low'].min():.2f}\n"
                    result += f"   平均价: ¥{df['close'].mean():.2f}\n"

                    # 安全获取成交量
                    if 'volume' in df.columns:
                        result += f"   成交量: {df['volume'].sum():,.0f}股\n"

                    duration = time.time() - start_time
                    logger.info(f"✅ [TDX Native] 获取成功: 耗时={duration:.2f}s, 数据条数={len(df)}")
                    return result
                else:
                    logger.debug("📊 [TDX Native] 数据为空，降级到HTTP Provider")

        except ImportError:
            logger.debug("📊 [TDX Native] 模块不可用，降级到HTTP Provider")
        except Exception as e:
            logger.debug(f"📊 [TDX Native] 获取失败: {e}，降级到HTTP Provider")

        # 降级到 HTTP Provider
        try:
            from .providers.tdx_provider import get_tdx_provider

            provider = get_tdx_provider()

            if not provider.is_available():
                logger.warning("⚠️ [TDX] 服务不可用，将降级到其他数据源")
                return f"❌ TDX服务不可用"

            # 获取K线数据
            df = provider.get_kline_by_date_range(symbol, start_date, end_date, 'day')

            if df is not None and not df.empty:
                # 获取股票名称
                search_results = provider.search_stock(symbol, limit=1)
                stock_name = search_results[0].get('name', f'股票{symbol}') if search_results else f'股票{symbol}'

                # 计算最新价格和涨跌幅
                latest_data = df.iloc[-1]
                latest_price = latest_data.get('close', 0)
                prev_close = df.iloc[-2].get('close', latest_price) if len(df) > 1 else latest_price
                change = latest_price - prev_close
                change_pct = (change / prev_close * 100) if prev_close != 0 else 0

                # 格式化数据报告
                result = f"📊 {stock_name}({symbol}) - TDX HTTP数据\n"
                result += f"数据期间: {start_date} 至 {end_date}\n"
                result += f"数据条数: {len(df)}条\n\n"

                result += f"💰 最新价格: ¥{latest_price:.2f}\n"
                result += f"📈 涨跌额: {change:+.2f} ({change_pct:+.2f}%)\n\n"

                # 添加统计信息
                result += f"📊 价格统计:\n"
                result += f"   最高价: ¥{df['high'].max():.2f}\n"
                result += f"   最低价: ¥{df['low'].min():.2f}\n"
                result += f"   平均价: ¥{df['close'].mean():.2f}\n"

                # 安全获取成交量
                if 'volume' in df.columns:
                    result += f"   成交量: {df['volume'].sum():,.0f}股\n"

                duration = time.time() - start_time
                logger.info(f"✅ [TDX HTTP] 获取成功: 耗时={duration:.2f}s, 数据条数={len(df)}")
                return result
            else:
                result = f"❌ 未获取到{symbol}的有效数据"
                duration = time.time() - start_time
                logger.warning(f"⚠️ [TDX] 数据为空: 耗时={duration:.2f}s")
                return result

        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"❌ [TDX] 调用失败: {e}, 耗时={duration:.2f}s", exc_info=True)
            return f"❌ TDX获取{symbol}数据失败: {e}"

    def _get_tushare_data(self, symbol: str, start_date: str, end_date: str) -> str:
        """使用Tushare获取数据 - 直接调用适配器，避免循环调用"""
        logger.debug(f"📊 [Tushare] 调用参数: symbol={symbol}, start_date={start_date}, end_date={end_date}")

        # 添加详细的股票代码追踪日志
        logger.info(f"🔍 [股票代码追踪] _get_tushare_data 接收到的股票代码: '{symbol}' (类型: {type(symbol)})")
        logger.info(f"🔍 [股票代码追踪] 股票代码长度: {len(str(symbol))}")
        logger.info(f"🔍 [股票代码追踪] 股票代码字符: {list(str(symbol))}")
        logger.info(f"🔍 [DataSourceManager详细日志] _get_tushare_data 开始执行")
        logger.info(f"🔍 [DataSourceManager详细日志] 当前数据源: {self.current_source.value}")

        start_time = time.time()
        try:
            # 直接调用适配器，避免循环调用interface
            from .tushare_adapter import get_tushare_adapter
            logger.info(f"🔍 [股票代码追踪] 调用 tushare_adapter，传入参数: symbol='{symbol}'")
            logger.info(f"🔍 [DataSourceManager详细日志] 开始调用tushare_adapter...")

            adapter = get_tushare_adapter()
            data = adapter.get_stock_data(symbol, start_date, end_date)

            if data is not None and not data.empty:
                # 获取股票基本信息
                stock_info = adapter.get_stock_info(symbol)
                stock_name = stock_info.get('name', f'股票{symbol}') if stock_info else f'股票{symbol}'

                # 计算最新价格和涨跌幅
                latest_data = data.iloc[-1]
                latest_price = latest_data.get('close', 0)
                prev_close = data.iloc[-2].get('close', latest_price) if len(data) > 1 else latest_price
                change = latest_price - prev_close
                change_pct = (change / prev_close * 100) if prev_close != 0 else 0

                # 格式化数据报告
                result = f"📊 {stock_name}({symbol}) - Tushare数据\n"
                result += f"数据期间: {start_date} 至 {end_date}\n"
                result += f"数据条数: {len(data)}条\n\n"

                result += f"💰 最新价格: ¥{latest_price:.2f}\n"
                result += f"📈 涨跌额: {change:+.2f} ({change_pct:+.2f}%)\n\n"

                # 添加统计信息
                result += f"📊 价格统计:\n"
                result += f"   最高价: ¥{data['high'].max():.2f}\n"
                result += f"   最低价: ¥{data['low'].min():.2f}\n"
                result += f"   平均价: ¥{data['close'].mean():.2f}\n"
                # 防御性获取成交量数据
                volume_value = self._get_volume_safely(data)
                result += f"   成交量: {volume_value:,.0f}股\n"

                return result
            else:
                result = f"❌ 未获取到{symbol}的有效数据"

            duration = time.time() - start_time
            logger.info(f"🔍 [DataSourceManager详细日志] interface调用完成，耗时: {duration:.3f}秒")
            logger.info(f"🔍 [股票代码追踪] get_china_stock_data_tushare 返回结果前200字符: {result[:200] if result else 'None'}")
            logger.info(f"🔍 [DataSourceManager详细日志] 返回结果类型: {type(result)}")
            logger.info(f"🔍 [DataSourceManager详细日志] 返回结果长度: {len(result) if result else 0}")

            logger.debug(f"📊 [Tushare] 调用完成: 耗时={duration:.2f}s, 结果长度={len(result) if result else 0}")

            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"❌ [Tushare] 调用失败: {e}, 耗时={duration:.2f}s", exc_info=True)
            logger.error(f"❌ [DataSourceManager详细日志] 异常类型: {type(e).__name__}")
            logger.error(f"❌ [DataSourceManager详细日志] 异常信息: {str(e)}")
            import traceback
            logger.error(f"❌ [DataSourceManager详细日志] 异常堆栈: {traceback.format_exc()}")
            raise
    
    def _get_akshare_data(self, symbol: str, start_date: str, end_date: str) -> str:
        """使用AKShare获取数据"""
        logger.debug(f"📊 [AKShare] 调用参数: symbol={symbol}, start_date={start_date}, end_date={end_date}")

        start_time = time.time()
        try:
            # 这里需要实现AKShare的统一接口
            from backend.dataflows.stock.akshare_utils import get_akshare_provider
            provider = get_akshare_provider()
            data = provider.get_stock_data(symbol, start_date, end_date)

            duration = time.time() - start_time

            if data is not None and not data.empty:
                result = f"股票代码: {symbol}\n"
                result += f"数据期间: {start_date} 至 {end_date}\n"
                result += f"数据条数: {len(data)}条\n\n"

                # 显示最新3天数据，确保在各种显示环境下都能完整显示
                display_rows = min(3, len(data))
                result += f"最新{display_rows}天数据:\n"

                # 使用pandas选项确保显示完整数据
                with pd.option_context('display.max_rows', None,
                                     'display.max_columns', None,
                                     'display.width', None,
                                     'display.max_colwidth', None):
                    result += data.tail(display_rows).to_string(index=False)

                # 如果数据超过3天，也显示一些统计信息
                if len(data) > 3:
                    latest_price = data.iloc[-1]['收盘'] if '收盘' in data.columns else data.iloc[-1].get('close', 'N/A')
                    first_price = data.iloc[0]['收盘'] if '收盘' in data.columns else data.iloc[0].get('close', 'N/A')
                    if latest_price != 'N/A' and first_price != 'N/A':
                        try:
                            change = float(latest_price) - float(first_price)
                            change_pct = (change / float(first_price)) * 100
                            result += f"\n\n📊 期间统计:\n"
                            result += f"期间涨跌: {change:+.2f} ({change_pct:+.2f}%)\n"
                            result += f"最高价: {data['最高'].max() if '最高' in data.columns else data.get('high', pd.Series()).max():.2f}\n"
                            result += f"最低价: {data['最低'].min() if '最低' in data.columns else data.get('low', pd.Series()).min():.2f}"
                        except (ValueError, TypeError):
                            pass

                logger.debug(f"📊 [AKShare] 调用成功: 耗时={duration:.2f}s, 数据条数={len(data)}, 结果长度={len(result)}")
                return result
            else:
                result = f"❌ 未能获取{symbol}的股票数据"
                logger.warning(f"⚠️ [AKShare] 数据为空: 耗时={duration:.2f}s")
                return result

        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"❌ [AKShare] 调用失败: {e}, 耗时={duration:.2f}s", exc_info=True)
            return f"❌ AKShare获取{symbol}数据失败: {e}"
    
    def _get_juhe_data(self, symbol: str, start_date: str = None, end_date: str = None) -> str:
        """使用聚合数据获取股票实时行情（免费版每天50次）"""
        logger.debug(f"📊 [聚合数据] 调用参数: symbol={symbol}")
        
        start_time = time.time()
        try:
            import httpx
            
            # 获取 API Key
            api_key = os.getenv('JUHE_API_KEY', '')
            if not api_key:
                return "❌ 聚合数据 API Key 未配置"
            
            # 格式化股票代码（添加 sh/sz 前缀）
            formatted_symbol = symbol.lower()
            if not formatted_symbol.startswith(("sh", "sz")):
                first_digit = formatted_symbol[0]
                if first_digit in ['6', '9']:
                    formatted_symbol = 'sh' + formatted_symbol
                elif first_digit in ['0', '2', '3']:
                    formatted_symbol = 'sz' + formatted_symbol
            
            # 调用聚合数据 API
            url = "http://web.juhe.cn/finance/stock/hs"
            params = {
                "gid": formatted_symbol,
                "key": api_key
            }
            
            with httpx.Client(timeout=10.0) as client:
                response = client.get(url, params=params)
                
            if response.status_code != 200:
                return f"❌ 聚合数据 API 请求失败: HTTP {response.status_code}"
            
            data = response.json()
            
            # 检查错误
            if data.get("error_code") and data["error_code"] != 0:
                error_msg = data.get("reason", "未知错误")
                logger.warning(f"⚠️ [聚合数据] API返回错误: {error_msg}")
                return f"❌ 聚合数据错误: {error_msg}"
            
            # 提取数据
            if data.get("result") and len(data["result"]) > 0:
                result_data = data["result"][0]
                
                # 根据文档，数据在 'data' 字段中
                if 'data' in result_data:
                    stock_data = result_data['data']
                else:
                    stock_data = result_data
                
                # 调试：输出股票数据字段
                logger.info(f"[聚合数据] 股票数据字段: {list(stock_data.keys())}")
                
                # 根据文档的实际字段名
                field_map = {
                    'nowPri': ['nowPri'],  # 当前价格
                    'increPer': ['increPer'],  # 涨跌百分比
                    'increase': ['increase'],  # 涨跌额
                    'todayStartPri': ['todayStartPri'],  # 今日开盘价
                    'yestodEndPri': ['yestodEndPri'],  # 昨日收盘价
                    'todayMax': ['todayMax'],  # 今日最高价
                    'todayMin': ['todayMin'],  # 今日最低价
                    'traNumber': ['traNumber'],  # 成交量
                    'traAmount': ['traAmount']  # 成交金额
                }
                
                def get_field_value(data, field_names):
                    """尝试多个字段名获取值"""
                    for name in field_names:
                        if name in data and data[name] not in [None, '', 'N/A']:
                            return data[name]
                    return 'N/A'
                
                # 获取各个字段
                name = stock_data.get('name', symbol)
                now_pri = get_field_value(stock_data, field_map['nowPri'])
                incre_per = get_field_value(stock_data, field_map['increPer'])  # 涨跌百分比
                increase = get_field_value(stock_data, field_map['increase'])  # 涨跌额
                today_start = get_field_value(stock_data, field_map['todayStartPri'])
                yestod_end = get_field_value(stock_data, field_map['yestodEndPri'])
                today_max = get_field_value(stock_data, field_map['todayMax'])
                today_min = get_field_value(stock_data, field_map['todayMin'])
                tra_number = get_field_value(stock_data, field_map['traNumber'])  # 成交量
                tra_amount = get_field_value(stock_data, field_map['traAmount'])  # 成交金额
                
                # 调试输出
                logger.info(f"[聚合数据] 解析结果: 现价={now_pri}, 涨跌幅={incre_per}%, 涨跌额={increase}")
                
                # 格式化输出
                result = f"📊 {name}({symbol}) - 聚合数据\n"
                result += f"实时行情数据\n\n"
                
                result += f"💰 最新价格: ¥{now_pri}\n"
                result += f"📈 涨跌幅: {incre_per}%\n"
                result += f"📉 涨跌额: {increase}\n"
                result += f"🔺 今开: ¥{today_start}\n"
                result += f"🔺 昨收: ¥{yestod_end}\n"
                result += f"🔼 最高: ¥{today_max}\n"
                result += f"🔽 最低: ¥{today_min}\n"
                result += f"📊 成交量: {tra_number}\n"
                result += f"💵 成交额: {tra_amount}\n"
                
                duration = time.time() - start_time
                logger.info(f"✅ [聚合数据] 获取成功: 耗时={duration:.2f}s")
                return result
            else:
                logger.warning(f"[聚合数据] API返回空结果: {data}")
                return f"❌ 未找到{symbol}的股票数据"
        
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"❌ [聚合数据] 调用失败: {e}, 耗时={duration:.2f}s", exc_info=True)
            return f"❌ 聚合数据获取{symbol}数据失败: {e}"
    
    def _get_sina_data(self, symbol: str, start_date: str = None, end_date: str = None) -> str:
        """使用新浪财经获取股票实时行情（免费、无限制）"""
        logger.debug(f"📊 [新浪财经] 调用参数: symbol={symbol}")
        
        start_time = time.time()
        try:
            import httpx
            import re
            
            # 格式化股票代码（新浪财经格式: sh600519 或 sz000001）
            formatted_symbol = symbol.lower()
            if not formatted_symbol.startswith(("sh", "sz")):
                first_digit = formatted_symbol[0]
                if first_digit in ['6', '9']:
                    formatted_symbol = 'sh' + formatted_symbol
                elif first_digit in ['0', '2', '3']:
                    formatted_symbol = 'sz' + formatted_symbol
            
            # 新浪财经实时行情 API
            url = f"http://hq.sinajs.cn/list={formatted_symbol}"
            
            # 添加更完整的请求头以避免403
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': 'http://finance.sina.com.cn',
                'Accept': '*/*',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive'
            }
            
            with httpx.Client(timeout=10.0, headers=headers, follow_redirects=True) as client:
                response = client.get(url)
            
            if response.status_code != 200:
                return f"❌ 新浪财经 API 请求失败: HTTP {response.status_code}"
            
            # 解析数据
            content = response.text
            if not content or '=""' in content:
                return f"❌ 未找到{symbol}的股票数据"
            
            # 提取数据（格式: var hq_str_sh600519="..."）
            match = re.search(r'"(.+?)"', content)
            if not match:
                return f"❌ 新浪财经数据格式错误"
            
            data_str = match.group(1)
            data_parts = data_str.split(',')
            
            if len(data_parts) < 32:
                return f"❌ 新浪财经数据不完整"
            
            # 解析字段
            stock_name = data_parts[0]
            open_price = float(data_parts[1]) if data_parts[1] else 0
            yesterday_close = float(data_parts[2]) if data_parts[2] else 0
            current_price = float(data_parts[3]) if data_parts[3] else 0
            high_price = float(data_parts[4]) if data_parts[4] else 0
            low_price = float(data_parts[5]) if data_parts[5] else 0
            volume = float(data_parts[8]) if data_parts[8] else 0  # 成交量（股）
            amount = float(data_parts[9]) if data_parts[9] else 0  # 成交额（元）
            date = data_parts[30]
            time_str = data_parts[31]  # 重命名以避免与time模块冲突
            
            # 计算涨跌
            change = current_price - yesterday_close
            change_pct = (change / yesterday_close * 100) if yesterday_close != 0 else 0
            
            # 格式化输出
            result = f"📊 {stock_name}({symbol}) - 新浪财经\n"
            result += f"实时行情数据 ({date} {time_str})\n\n"
            
            result += f"💰 最新价格: ¥{current_price:.2f}\n"
            result += f"📈 涨跌幅: {change_pct:+.2f}%\n"
            result += f"📉 涨跌额: ¥{change:+.2f}\n"
            result += f"🔺 今开: ¥{open_price:.2f}\n"
            result += f"🔺 昨收: ¥{yesterday_close:.2f}\n"
            result += f"🔼 最高: ¥{high_price:.2f}\n"
            result += f"🔽 最低: ¥{low_price:.2f}\n"
            result += f"📊 成交量: {volume/100:.2f}万手\n"
            result += f"💵 成交额: {amount/100000000:.2f}亿元\n"
            
            duration = time.time() - start_time
            logger.info(f"✅ [新浪财经] 获取成功: 耗时={duration:.2f}s")
            return result
        
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"❌ [新浪财经] 调用失败: {e}, 耗时={duration:.2f}s", exc_info=True)
            return f"❌ 新浪财经获取{symbol}数据失败: {e}"
    
    def _get_baostock_data(self, symbol: str, start_date: str, end_date: str) -> str:
        """使用BaoStock获取数据"""
        # 这里需要实现BaoStock的统一接口
        from .baostock_utils import get_baostock_provider
        provider = get_baostock_provider()
        data = provider.get_stock_data(symbol, start_date, end_date)
        
        if data is not None and not data.empty:
            result = f"股票代码: {symbol}\n"
            result += f"数据期间: {start_date} 至 {end_date}\n"
            result += f"数据条数: {len(data)}条\n\n"

            # 显示最新3天数据，确保在各种显示环境下都能完整显示
            display_rows = min(3, len(data))
            result += f"最新{display_rows}天数据:\n"

            # 使用pandas选项确保显示完整数据
            with pd.option_context('display.max_rows', None,
                                 'display.max_columns', None,
                                 'display.width', None,
                                 'display.max_colwidth', None):
                result += data.tail(display_rows).to_string(index=False)
            return result
        else:
            return f"❌ 未能获取{symbol}的股票数据"
    
    def _get_volume_safely(self, data) -> float:
        """安全地获取成交量数据，支持多种列名"""
        try:
            # 支持多种可能的成交量列名
            volume_columns = ['volume', 'vol', 'turnover', 'trade_volume']

            for col in volume_columns:
                if col in data.columns:
                    logger.info(f"✅ 找到成交量列: {col}")
                    return data[col].sum()

            # 如果都没找到，记录警告并返回0
            logger.warning(f"⚠️ 未找到成交量列，可用列: {list(data.columns)}")
            return 0

        except Exception as e:
            logger.error(f"❌ 获取成交量失败: {e}")
            return 0

    def _try_fallback_sources(self, symbol: str, start_date: str, end_date: str) -> str:
        """尝试备用数据源 - 使用断路器保护"""
        # 记录当前数据源失败
        self._record_source_failure(self.current_source)
        logger.warning(f"🔄 {self.current_source.value}失败，尝试备用数据源...")

        # 备用数据源优先级: TDX > AKShare > Tushare > 聚合数据 > 新浪财经 > BaoStock
        fallback_order = [
            ChinaDataSource.TDX,
            ChinaDataSource.AKSHARE,
            ChinaDataSource.TUSHARE,
            ChinaDataSource.JUHE,
            ChinaDataSource.SINA,
            ChinaDataSource.BAOSTOCK
        ]

        for source in fallback_order:
            if source != self.current_source and source in self.available_sources:
                # 检查断路器状态
                if not self._can_use_source(source):
                    logger.debug(f"⏸️ 数据源{source.value}断路器已熔断，跳过")
                    continue

                try:
                    logger.info(f"🔄 尝试备用数据源: {source.value}")

                    # 直接调用具体的数据源方法，避免递归
                    if source == ChinaDataSource.TDX:
                        result = self._get_tdx_data(symbol, start_date, end_date)
                    elif source == ChinaDataSource.AKSHARE:
                        result = self._get_akshare_data(symbol, start_date, end_date)
                    elif source == ChinaDataSource.JUHE:
                        result = self._get_juhe_data(symbol, start_date, end_date)
                    elif source == ChinaDataSource.SINA:
                        result = self._get_sina_data(symbol, start_date, end_date)
                    elif source == ChinaDataSource.TUSHARE:
                        result = self._get_tushare_data(symbol, start_date, end_date)
                    elif source == ChinaDataSource.BAOSTOCK:
                        result = self._get_baostock_data(symbol, start_date, end_date)
                    else:
                        logger.warning(f"⚠️ 未知数据源: {source.value}")
                        continue

                    if "❌" not in result:
                        # 记录成功
                        self._record_source_success(source)
                        logger.info(f"✅ 备用数据源{source.value}获取成功")
                        return result
                    else:
                        # 记录失败
                        self._record_source_failure(source)
                        logger.warning(f"⚠️ 备用数据源{source.value}返回错误结果")

                except Exception as e:
                    # 记录失败
                    self._record_source_failure(source)
                    logger.error(f"❌ 备用数据源{source.value}也失败: {e}")
                    continue

        return f"❌ 所有数据源都无法获取{symbol}的数据"
    
    def get_stock_info(self, symbol: str) -> Dict:
        """获取股票基本信息，支持降级机制"""
        logger.info(f"📊 [股票信息] 开始获取{symbol}基本信息...")

        # 首先尝试当前数据源
        try:
            if self.current_source == ChinaDataSource.TUSHARE:
                from .interface import get_china_stock_info_tushare
                info_str = get_china_stock_info_tushare(symbol)
                result = self._parse_stock_info_string(info_str, symbol)

                # 检查是否获取到有效信息
                if result.get('name') and result['name'] != f'股票{symbol}':
                    logger.info(f"✅ [股票信息] Tushare成功获取{symbol}信息")
                    return result
                else:
                    logger.warning(f"⚠️ [股票信息] Tushare返回无效信息，尝试降级...")
                    return self._try_fallback_stock_info(symbol)
            else:
                adapter = self.get_data_adapter()
                if adapter and hasattr(adapter, 'get_stock_info'):
                    result = adapter.get_stock_info(symbol)
                    if result.get('name') and result['name'] != f'股票{symbol}':
                        logger.info(f"✅ [股票信息] {self.current_source.value}成功获取{symbol}信息")
                        return result
                    else:
                        logger.warning(f"⚠️ [股票信息] {self.current_source.value}返回无效信息，尝试降级...")
                        return self._try_fallback_stock_info(symbol)
                else:
                    logger.warning(f"⚠️ [股票信息] {self.current_source.value}不支持股票信息获取，尝试降级...")
                    return self._try_fallback_stock_info(symbol)

        except Exception as e:
            logger.error(f"❌ [股票信息] {self.current_source.value}获取失败: {e}")
            return self._try_fallback_stock_info(symbol)

    def _try_fallback_stock_info(self, symbol: str) -> Dict:
        """尝试使用备用数据源获取股票基本信息"""
        logger.info(f"🔄 [股票信息] {self.current_source.value}失败，尝试备用数据源...")

        # 获取所有可用数据源
        available_sources = self.available_sources.copy()

        # 移除当前数据源
        if self.current_source.value in available_sources:
            available_sources.remove(self.current_source.value)

        # 尝试所有备用数据源
        for source_name in available_sources:
            try:
                source = ChinaDataSource(source_name)
                logger.info(f"🔄 [股票信息] 尝试备用数据源: {source_name}")

                # 根据数据源类型获取股票信息
                if source == ChinaDataSource.TUSHARE:
                    from .interface import get_china_stock_info_tushare
                    info_str = get_china_stock_info_tushare(symbol)
                    result = self._parse_stock_info_string(info_str, symbol)
                elif source == ChinaDataSource.AKSHARE:
                    result = self._get_akshare_stock_info(symbol)
                elif source == ChinaDataSource.BAOSTOCK:
                    result = self._get_baostock_stock_info(symbol)
                else:
                    # 尝试通用适配器
                    original_source = self.current_source
                    self.current_source = source
                    adapter = self.get_data_adapter()
                    self.current_source = original_source

                    if adapter and hasattr(adapter, 'get_stock_info'):
                        result = adapter.get_stock_info(symbol)
                    else:
                        logger.warning(f"⚠️ [股票信息] {source_name}不支持股票信息获取")
                        continue

                # 检查是否获取到有效信息
                if result.get('name') and result['name'] != f'股票{symbol}':
                    logger.info(f"✅ [股票信息] 备用数据源{source_name}成功获取{symbol}信息")
                    return result
                else:
                    logger.warning(f"⚠️ [股票信息] 备用数据源{source_name}返回无效信息")

            except Exception as e:
                logger.error(f"❌ [股票信息] 备用数据源{source_name}失败: {e}")
                continue

        # 所有数据源都失败，返回默认值
        logger.error(f"❌ [股票信息] 所有数据源都无法获取{symbol}的基本信息")
        return {'symbol': symbol, 'name': f'股票{symbol}', 'source': 'unknown'}

    def _get_akshare_stock_info(self, symbol: str) -> Dict:
        """使用AKShare获取股票基本信息"""
        try:
            import akshare as ak

            # 去除后缀（如 600252.SH -> 600252）
            pure_symbol = symbol.split('.')[0] if '.' in symbol else symbol

            # 去除前缀（如 SH600252 -> 600252）
            if pure_symbol.upper().startswith(('SH', 'SZ')):
                pure_symbol = pure_symbol[2:]

            # 尝试获取个股信息
            stock_info = ak.stock_individual_info_em(symbol=pure_symbol)

            if stock_info is not None and not stock_info.empty:
                # 转换为字典格式
                info = {'symbol': symbol, 'source': 'akshare'}

                # 提取股票名称
                name_row = stock_info[stock_info['item'] == '股票简称']
                if not name_row.empty:
                    info['name'] = name_row['value'].iloc[0]
                else:
                    info['name'] = f'股票{symbol}'

                # 提取其他信息
                info['area'] = '未知'  # AKShare没有地区信息
                info['industry'] = '未知'  # 可以通过其他API获取
                info['market'] = '未知'  # 可以根据股票代码推断
                info['list_date'] = '未知'  # 可以通过其他API获取

                return info
            else:
                return {'symbol': symbol, 'name': f'股票{symbol}', 'source': 'akshare'}

        except Exception as e:
            logger.error(f"❌ [股票信息] AKShare获取失败: {e}")
            return {'symbol': symbol, 'name': f'股票{symbol}', 'source': 'akshare', 'error': str(e)}

    def _get_baostock_stock_info(self, symbol: str) -> Dict:
        """使用BaoStock获取股票基本信息"""
        try:
            import baostock as bs

            # 去除后缀（如 600252.SH -> 600252）
            pure_symbol = symbol.split('.')[0] if '.' in symbol else symbol

            # 去除前缀（如 SH600252 -> 600252）
            if pure_symbol.upper().startswith(('SH', 'SZ')):
                pure_symbol = pure_symbol[2:]

            # 转换股票代码格式
            if pure_symbol.startswith('6'):
                bs_code = f"sh.{pure_symbol}"
            else:
                bs_code = f"sz.{pure_symbol}"

            # 登录BaoStock
            lg = bs.login()
            if lg.error_code != '0':
                logger.error(f"❌ [股票信息] BaoStock登录失败: {lg.error_msg}")
                return {'symbol': symbol, 'name': f'股票{symbol}', 'source': 'baostock'}

            # 查询股票基本信息
            rs = bs.query_stock_basic(code=bs_code)
            if rs.error_code != '0':
                bs.logout()
                logger.error(f"❌ [股票信息] BaoStock查询失败: {rs.error_msg}")
                return {'symbol': symbol, 'name': f'股票{symbol}', 'source': 'baostock'}

            # 解析结果
            data_list = []
            while (rs.error_code == '0') & rs.next():
                data_list.append(rs.get_row_data())

            # 登出
            bs.logout()

            if data_list:
                # BaoStock返回格式: [code, code_name, ipoDate, outDate, type, status]
                info = {'symbol': symbol, 'source': 'baostock'}
                info['name'] = data_list[0][1]  # code_name
                info['area'] = '未知'  # BaoStock没有地区信息
                info['industry'] = '未知'  # BaoStock没有行业信息
                info['market'] = '未知'  # 可以根据股票代码推断
                info['list_date'] = data_list[0][2]  # ipoDate

                return info
            else:
                return {'symbol': symbol, 'name': f'股票{symbol}', 'source': 'baostock'}

        except Exception as e:
            logger.error(f"❌ [股票信息] BaoStock获取失败: {e}")
            return {'symbol': symbol, 'name': f'股票{symbol}', 'source': 'baostock', 'error': str(e)}

    def _parse_stock_info_string(self, info_str: str, symbol: str) -> Dict:
        """解析股票信息字符串为字典"""
        try:
            info = {'symbol': symbol, 'source': self.current_source.value}
            lines = info_str.split('\n')
            
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    if '股票名称' in key:
                        info['name'] = value
                    elif '所属行业' in key:
                        info['industry'] = value
                    elif '所属地区' in key:
                        info['area'] = value
                    elif '上市市场' in key:
                        info['market'] = value
                    elif '上市日期' in key:
                        info['list_date'] = value
            
            return info
            
        except Exception as e:
            logger.error(f"⚠️ 解析股票信息失败: {e}")
            return {'symbol': symbol, 'name': f'股票{symbol}', 'source': self.current_source.value}


# 全局数据源管理器实例
_data_source_manager = None

def get_data_source_manager() -> DataSourceManager:
    """获取全局数据源管理器实例"""
    global _data_source_manager
    if _data_source_manager is None:
        _data_source_manager = DataSourceManager()
    return _data_source_manager


def get_china_stock_data_unified(symbol: str, start_date: str, end_date: str) -> str:
    """
    统一的中国股票数据获取接口
    自动使用配置的数据源，支持备用数据源

    Args:
        symbol: 股票代码
        start_date: 开始日期
        end_date: 结束日期

    Returns:
        str: 格式化的股票数据
    """
    # 简化日志，避免过多输出
    logger.debug(f"[数据源] 获取股票数据: {symbol}, {start_date} - {end_date}")

    manager = get_data_source_manager()
    result = manager.get_stock_data(symbol, start_date, end_date)

    if result:
        lines = result.split('\n')
        logger.debug(f"[数据源] 返回 {len(lines)} 行数据")
    else:
        logger.warning(f"[数据源] 未获取到数据: {symbol}")
    return result


def get_china_stock_info_unified(symbol: str) -> Dict:
    """
    统一的中国股票信息获取接口

    Args:
        symbol: 股票代码

    Returns:
        Dict: 股票基本信息
    """
    manager = get_data_source_manager()
    return manager.get_stock_info(symbol)
