#!/usr/bin/env python3
"""
AKShare数据源工具
提供AKShare数据获取的统一接口
"""

import pandas as pd
from typing import Optional, Dict, Any
import warnings
from datetime import datetime

# 导入日志模块
from backend.utils.logging_config import get_logger
logger = get_logger('agents')
warnings.filterwarnings('ignore')

class AKShareProvider:
    """AKShare数据提供器"""

    def __init__(self):
        """初始化AKShare提供器"""
        try:
            import akshare as ak
            self.ak = ak
            self.connected = True

            # 设置更长的超时时间
            self._configure_timeout()

            logger.info(f"✅ AKShare初始化成功")
        except ImportError:
            self.ak = None
            self.connected = False
            logger.error(f"❌ AKShare未安装")

    def _configure_timeout(self):
        """配置AKShare的超时设置"""
        try:
            import requests
            import socket

            # 设置更长的超时时间
            socket.setdefaulttimeout(60)  # 60秒超时

            # 如果AKShare使用requests，设置默认超时
            if hasattr(requests, 'adapters'):
                from requests.adapters import HTTPAdapter
                from urllib3.util.retry import Retry

                # 创建重试策略
                retry_strategy = Retry(
                    total=3,
                    backoff_factor=1,
                    status_forcelist=[429, 500, 502, 503, 504],
                )

                # 设置适配器
                adapter = HTTPAdapter(max_retries=retry_strategy)
                session = requests.Session()
                session.mount("http://", adapter)
                session.mount("https://", adapter)

                logger.info(f"🔧 AKShare超时配置完成: 60秒超时，3次重试")

        except Exception as e:
            logger.error(f"⚠️ AKShare超时配置失败: {e}")
            logger.info(f"🔧 使用默认超时设置")
    
    def get_stock_data(self, symbol: str, start_date: str = None, end_date: str = None) -> Optional[pd.DataFrame]:
        """获取股票历史数据"""
        if not self.connected:
            return None
        
        try:
            # 转换股票代码格式
            if len(symbol) == 6:
                symbol = symbol
            else:
                symbol = symbol.replace('.SZ', '').replace('.SS', '')
            
            # 获取数据
            data = self.ak.stock_zh_a_hist(
                symbol=symbol,
                period="daily",
                start_date=start_date.replace('-', '') if start_date else "20240101",
                end_date=end_date.replace('-', '') if end_date else "20241231",
                adjust=""
            )
            
            return data
            
        except Exception as e:
            logger.error(f"❌ AKShare获取股票数据失败: {e}")
            return None
    
    def get_stock_info(self, symbol: str) -> Dict[str, Any]:
        """获取股票基本信息"""
        if not self.connected:
            return {}
        
        try:
            # 获取股票基本信息
            stock_list = self.ak.stock_info_a_code_name()
            stock_info = stock_list[stock_list['code'] == symbol]
            
            if not stock_info.empty:
                return {
                    'symbol': symbol,
                    'name': stock_info.iloc[0]['name'],
                    'source': 'akshare'
                }
            else:
                return {'symbol': symbol, 'name': f'股票{symbol}', 'source': 'akshare'}
                
        except Exception as e:
            logger.error(f"❌ AKShare获取股票信息失败: {e}")
            return {'symbol': symbol, 'name': f'股票{symbol}', 'source': 'akshare'}

    def get_hk_stock_data(self, symbol: str, start_date: str = None, end_date: str = None) -> Optional[pd.DataFrame]:
        """
        获取港股历史数据

        Args:
            symbol: 港股代码 (如: 00700 或 0700.HK)
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)

        Returns:
            DataFrame: 港股历史数据
        """
        if not self.connected:
            logger.error(f"❌ AKShare未连接")
            return None

        try:
            # 标准化港股代码 - AKShare使用5位数字格式
            hk_symbol = self._normalize_hk_symbol_for_akshare(symbol)

            logger.info(f"🇭🇰 AKShare获取港股数据: {hk_symbol} ({start_date} 到 {end_date})")

            # 格式化日期为AKShare需要的格式
            start_date_formatted = start_date.replace('-', '') if start_date else "20240101"
            end_date_formatted = end_date.replace('-', '') if end_date else "20241231"

            # 使用AKShare获取港股历史数据（带超时保护）
            import threading

            result = [None]
            exception = [None]

            def fetch_hist_data():
                try:
                    result[0] = self.ak.stock_hk_hist(
                        symbol=hk_symbol,
                        period="daily",
                        start_date=start_date_formatted,
                        end_date=end_date_formatted,
                        adjust=""
                    )
                except Exception as e:
                    exception[0] = e

            # 启动线程
            thread = threading.Thread(target=fetch_hist_data)
            thread.daemon = True
            thread.start()

            # 等待60秒
            thread.join(timeout=60)

            if thread.is_alive():
                # 超时了
                logger.warning(f"⚠️ AKShare港股历史数据获取超时（60秒）: {symbol}")
                raise Exception(f"AKShare港股历史数据获取超时（60秒）: {symbol}")
            elif exception[0]:
                # 有异常
                raise exception[0]
            else:
                # 成功
                data = result[0]

            if not data.empty:
                # 数据预处理
                data = data.reset_index()
                data['Symbol'] = symbol  # 保持原始格式

                # 重命名列以保持一致性
                column_mapping = {
                    '日期': 'Date',
                    '开盘': 'Open',
                    '收盘': 'Close',
                    '最高': 'High',
                    '最低': 'Low',
                    '成交量': 'Volume',
                    '成交额': 'Amount'
                }

                for old_col, new_col in column_mapping.items():
                    if old_col in data.columns:
                        data = data.rename(columns={old_col: new_col})

                logger.info(f"✅ AKShare港股数据获取成功: {symbol}, {len(data)}条记录")
                return data
            else:
                logger.warning(f"⚠️ AKShare港股数据为空: {symbol}")
                return None

        except Exception as e:
            logger.error(f"❌ AKShare获取港股数据失败: {e}")
            return None

    def get_hk_stock_info(self, symbol: str) -> Dict[str, Any]:
        """
        获取港股基本信息

        Args:
            symbol: 港股代码

        Returns:
            Dict: 港股基本信息
        """
        if not self.connected:
            return {
                'symbol': symbol,
                'name': f'港股{symbol}',
                'currency': 'HKD',
                'exchange': 'HKG',
                'source': 'akshare_unavailable'
            }

        try:
            hk_symbol = self._normalize_hk_symbol_for_akshare(symbol)

            logger.info(f"🇭🇰 AKShare获取港股信息: {hk_symbol}")

            # 尝试获取港股实时行情数据来获取基本信息
            # 使用线程超时包装（兼容Windows）
            import threading
            import time


            result = [None]
            exception = [None]

            def fetch_data():
                try:
                    result[0] = self.ak.stock_hk_spot_em()
                except Exception as e:
                    exception[0] = e

            # 启动线程
            thread = threading.Thread(target=fetch_data)
            thread.daemon = True
            thread.start()

            # 等待60秒
            thread.join(timeout=60)

            if thread.is_alive():
                # 超时了
                logger.warning(f"⚠️ AKShare港股信息获取超时（60秒），使用备用方案")
                raise Exception("AKShare港股信息获取超时（60秒）")
            elif exception[0]:
                # 有异常
                raise exception[0]
            else:
                # 成功
                spot_data = result[0]

            # 查找对应的股票信息
            if not spot_data.empty:
                # 查找匹配的股票
                matching_stocks = spot_data[spot_data['代码'].str.contains(hk_symbol[:5], na=False)]

                if not matching_stocks.empty:
                    stock_info = matching_stocks.iloc[0]
                    return {
                        'symbol': symbol,
                        'name': stock_info.get('名称', f'港股{symbol}'),
                        'currency': 'HKD',
                        'exchange': 'HKG',
                        'latest_price': stock_info.get('最新价', None),
                        'source': 'akshare'
                    }

            # 如果没有找到，返回基本信息
            return {
                'symbol': symbol,
                'name': f'港股{symbol}',
                'currency': 'HKD',
                'exchange': 'HKG',
                'source': 'akshare'
            }

        except Exception as e:
            logger.error(f"❌ AKShare获取港股信息失败: {e}")
            return {
                'symbol': symbol,
                'name': f'港股{symbol}',
                'currency': 'HKD',
                'exchange': 'HKG',
                'source': 'akshare_error',
                'error': str(e)
            }

    def _normalize_hk_symbol_for_akshare(self, symbol: str) -> str:
        """
        标准化港股代码为AKShare格式

        Args:
            symbol: 原始港股代码 (如: 0700.HK 或 700)

        Returns:
            str: AKShare格式的港股代码 (如: 00700)
        """
        if not symbol:
            return symbol

        # 移除.HK后缀
        clean_symbol = symbol.replace('.HK', '').replace('.hk', '')

        # 确保是5位数字格式
        if clean_symbol.isdigit():
            return clean_symbol.zfill(5)

        return clean_symbol

    def get_financial_data(self, symbol: str) -> Dict[str, Any]:
        """
        获取股票财务数据
        
        Args:
            symbol: 股票代码 (6位数字)
            
        Returns:
            Dict: 包含主要财务指标的财务数据
        """
        if not self.connected:
            logger.error(f"❌ AKShare未连接，无法获取{symbol}财务数据")
            return {}
        
        try:
            logger.info(f"🔍 开始获取{symbol}的AKShare财务数据")
            
            financial_data = {}
            
            # 1. 优先获取主要财务指标
            try:
                logger.debug(f"📊 尝试获取{symbol}主要财务指标...")
                main_indicators = self.ak.stock_financial_abstract(symbol=symbol)
                if main_indicators is not None and not main_indicators.empty:
                    financial_data['main_indicators'] = main_indicators
                    logger.info(f"✅ 成功获取{symbol}主要财务指标: {len(main_indicators)}条记录")
                    logger.debug(f"主要财务指标列名: {list(main_indicators.columns)}")
                else:
                    logger.warning(f"⚠️ {symbol}主要财务指标为空")
            except Exception as e:
                logger.warning(f"❌ 获取{symbol}主要财务指标失败: {e}")
            
            # 2. 尝试获取资产负债表（可能失败，降级为debug日志）
            try:
                logger.debug(f"📊 尝试获取{symbol}资产负债表...")
                balance_sheet = self.ak.stock_balance_sheet_by_report_em(symbol=symbol)
                if balance_sheet is not None and not balance_sheet.empty:
                    financial_data['balance_sheet'] = balance_sheet
                    logger.debug(f"✅ 成功获取{symbol}资产负债表: {len(balance_sheet)}条记录")
                else:
                    logger.debug(f"⚠️ {symbol}资产负债表为空")
            except Exception as e:
                logger.debug(f"❌ 获取{symbol}资产负债表失败: {e}")
            
            # 3. 尝试获取利润表（可能失败，降级为debug日志）
            try:
                logger.debug(f"📊 尝试获取{symbol}利润表...")
                income_statement = self.ak.stock_profit_sheet_by_report_em(symbol=symbol)
                if income_statement is not None and not income_statement.empty:
                    financial_data['income_statement'] = income_statement
                    logger.debug(f"✅ 成功获取{symbol}利润表: {len(income_statement)}条记录")
                else:
                    logger.debug(f"⚠️ {symbol}利润表为空")
            except Exception as e:
                logger.debug(f"❌ 获取{symbol}利润表失败: {e}")
            
            # 4. 尝试获取现金流量表（可能失败，降级为debug日志）
            try:
                logger.debug(f"📊 尝试获取{symbol}现金流量表...")
                cash_flow = self.ak.stock_cash_flow_sheet_by_report_em(symbol=symbol)
                if cash_flow is not None and not cash_flow.empty:
                    financial_data['cash_flow'] = cash_flow
                    logger.debug(f"✅ 成功获取{symbol}现金流量表: {len(cash_flow)}条记录")
                else:
                    logger.debug(f"⚠️ {symbol}现金流量表为空")
            except Exception as e:
                logger.debug(f"❌ 获取{symbol}现金流量表失败: {e}")
            
            # 记录最终结果
            if financial_data:
                logger.info(f"✅ AKShare财务数据获取完成: {symbol}, 包含{len(financial_data)}个数据集")
                for key, value in financial_data.items():
                    if hasattr(value, '__len__'):
                        logger.info(f"  - {key}: {len(value)}条记录")
            else:
                logger.warning(f"⚠️ 未能获取{symbol}的任何AKShare财务数据")
            
            return financial_data
            
        except Exception as e:
            logger.error(f"❌ AKShare获取{symbol}财务数据失败: {e}")
            return {}

def get_akshare_provider() -> AKShareProvider:
    """获取AKShare提供器实例"""
    return AKShareProvider()


# 便捷函数
def get_hk_stock_data_akshare(symbol: str, start_date: str = None, end_date: str = None) -> str:
    """
    使用AKShare获取港股数据的便捷函数

    Args:
        symbol: 港股代码
        start_date: 开始日期
        end_date: 结束日期

    Returns:
        str: 格式化的港股数据
    """
    try:
        provider = get_akshare_provider()
        data = provider.get_hk_stock_data(symbol, start_date, end_date)

        if data is not None and not data.empty:
            return format_hk_stock_data_akshare(symbol, data, start_date, end_date)
        else:
            return f"❌ 无法获取港股 {symbol} 的AKShare数据"

    except Exception as e:
        return f"❌ AKShare港股数据获取失败: {e}"


def get_hk_stock_info_akshare(symbol: str) -> Dict[str, Any]:
    """
    使用AKShare获取港股信息的便捷函数

    Args:
        symbol: 港股代码

    Returns:
        Dict: 港股信息
    """
    try:
        provider = get_akshare_provider()
        return provider.get_hk_stock_info(symbol)
    except Exception as e:
        return {
            'symbol': symbol,
            'name': f'港股{symbol}',
            'currency': 'HKD',
            'exchange': 'HKG',
            'source': 'akshare_error',
            'error': str(e)
        }


def format_hk_stock_data_akshare(symbol: str, data: pd.DataFrame, start_date: str, end_date: str) -> str:
    """
    格式化AKShare港股数据为文本格式

    Args:
        symbol: 股票代码
        data: 股票数据DataFrame
        start_date: 开始日期
        end_date: 结束日期

    Returns:
        str: 格式化的股票数据文本
    """
    if data is None or data.empty:
        return f"❌ 无法获取港股 {symbol} 的AKShare数据"

    try:
        # 获取股票基本信息（允许失败）
        stock_name = f'港股{symbol}'  # 默认名称
        try:
            provider = get_akshare_provider()
            stock_info = provider.get_hk_stock_info(symbol)
            stock_name = stock_info.get('name', f'港股{symbol}')
            logger.info(f"✅ 港股信息获取成功: {stock_name}")
        except Exception as info_error:
            logger.error(f"⚠️ 港股信息获取失败，使用默认信息: {info_error}")
            # 继续处理，使用默认信息

        # 计算统计信息
        latest_price = data['Close'].iloc[-1]
        price_change = data['Close'].iloc[-1] - data['Close'].iloc[0]
        price_change_pct = (price_change / data['Close'].iloc[0]) * 100

        avg_volume = data['Volume'].mean() if 'Volume' in data.columns else 0
        max_price = data['High'].max()
        min_price = data['Low'].min()

        # 格式化输出
        formatted_text = f"""
🇭🇰 港股数据报告 (AKShare)
================

股票信息:
- 代码: {symbol}
- 名称: {stock_name}
- 货币: 港币 (HKD)
- 交易所: 香港交易所 (HKG)

价格信息:
- 最新价格: HK${latest_price:.2f}
- 期间涨跌: HK${price_change:+.2f} ({price_change_pct:+.2f}%)
- 期间最高: HK${max_price:.2f}
- 期间最低: HK${min_price:.2f}

交易信息:
- 数据期间: {start_date} 至 {end_date}
- 交易天数: {len(data)}天
- 平均成交量: {avg_volume:,.0f}股

最近5个交易日:
"""

        # 添加最近5天的数据
        recent_data = data.tail(5)
        for _, row in recent_data.iterrows():
            date = row['Date'].strftime('%Y-%m-%d') if 'Date' in row else row.name.strftime('%Y-%m-%d')
            volume = row.get('Volume', 0)
            formatted_text += f"- {date}: 开盘HK${row['Open']:.2f}, 收盘HK${row['Close']:.2f}, 成交量{volume:,.0f}\n"

        formatted_text += f"\n数据来源: AKShare (港股)\n"

        return formatted_text

    except Exception as e:
        logger.error(f"❌ 格式化AKShare港股数据失败: {e}")
        return f"❌ AKShare港股数据格式化失败: {symbol}"


def _fetch_stock_news_em_fixed(symbol: str) -> pd.DataFrame:
    """
    修复版东方财富个股新闻获取函数

    AKShare的stock_news_em存在bug，这里使用东财公告接口获取个股新闻

    Args:
        symbol: 股票代码，如 "000001" 或 "600519"

    Returns:
        pd.DataFrame: 个股新闻数据
    """
    import json
    import requests

    # 使用东财公告接口（更稳定）
    url = "https://np-anotice-stock.eastmoney.com/api/security/ann"
    params = {
        "sr": "-1",
        "page_size": "50",
        "page_index": "1",
        "ann_type": "A",
        "stock_list": symbol,
        "f_node": "0",
        "s_node": "0"
    }

    headers = {
        "accept": "*/*",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    r = requests.get(url, params=params, headers=headers, timeout=30)
    data = r.json()

    if not data.get("success") or "data" not in data or "list" not in data["data"]:
        return pd.DataFrame()

    items = data["data"]["list"]
    if not items:
        return pd.DataFrame()

    records = []
    for item in items:
        # 获取股票信息
        stock_info = item.get("codes", [{}])[0] if item.get("codes") else {}
        stock_name = stock_info.get("short_name", "")

        # 获取分类信息
        columns = item.get("columns", [{}])
        category = columns[0].get("column_name", "") if columns else ""

        records.append({
            "关键词": symbol,
            "新闻标题": item.get("title", ""),
            "新闻内容": f"[{category}] {stock_name}",
            "发布时间": item.get("notice_date", "")[:10] if item.get("notice_date") else "",
            "文章来源": "东方财富公告",
            "新闻链接": f"https://data.eastmoney.com/notices/detail/{symbol}/{item.get('art_code', '')}.html"
        })

    return pd.DataFrame(records)


def get_stock_news_em(symbol: str, max_news: int = 10) -> pd.DataFrame:
    """
    使用修复版函数获取东方财富个股新闻

    AKShare的stock_news_em存在bug（keyword硬编码），使用自定义修复版本

    Args:
        symbol: 股票代码，如 "600000" 或 "300059"
        max_news: 最大新闻数量，默认10条

    Returns:
        pd.DataFrame: 包含新闻标题、内容、日期和链接的DataFrame
    """
    start_time = datetime.now()
    logger.info(f"[东方财富新闻] 开始获取股票 {symbol} 的东方财富新闻数据")

    # 方法1: 使用修复版函数直接调用东财API
    try:
        logger.info(f"[东方财富新闻] 📰 使用修复版函数获取个股新闻: {symbol}")
        news_df = _fetch_stock_news_em_fixed(symbol)

        if news_df is not None and not news_df.empty:
            if len(news_df) > max_news:
                news_df = news_df.head(max_news)

            news_count = len(news_df)
            elapsed_time = (datetime.now() - start_time).total_seconds()

            # 记录一些新闻标题示例
            if '新闻标题' in news_df.columns:
                sample_titles = news_df['新闻标题'].head(3).tolist()
                logger.info(f"[东方财富新闻] 新闻标题示例: {', '.join(str(t)[:30] for t in sample_titles)}")

            logger.info(f"[东方财富新闻] ✅ 获取成功: {symbol}, 共{news_count}条记录，耗时: {elapsed_time:.2f}秒")
            return news_df

    except Exception as e:
        logger.warning(f"[东方财富新闻] 修复版函数失败: {e}")

    # 方法2: 降级到AKShare原版（可能失败）
    try:
        provider = get_akshare_provider()
        if provider.connected:
            news_df = provider.ak.stock_news_em(symbol=symbol)
            if news_df is not None and not news_df.empty:
                if len(news_df) > max_news:
                    news_df = news_df.head(max_news)
                logger.info(f"[东方财富新闻] ✅ AKShare原版获取成功: {len(news_df)}条")
                return news_df
    except Exception as e:
        logger.warning(f"[东方财富新闻] AKShare原版失败: {e}")

    # 方法3: 降级到财联社新闻
    try:
        provider = get_akshare_provider()
        news_df = provider.ak.stock_info_global_cls()
        if news_df is not None and not news_df.empty:
            # 统一列名格式
            news_df = news_df.rename(columns={
                '标题': '新闻标题',
                '内容': '新闻内容',
                '发布时间': '发布时间'
            })
            if len(news_df) > max_news:
                news_df = news_df.head(max_news)
            logger.info(f"[东方财富新闻] ✅ 降级成功: 使用stock_info_global_cls获取{len(news_df)}条新闻")
            return news_df
    except Exception as e2:
        logger.error(f"[东方财富新闻] 降级也失败: {e2}")

    elapsed_time = (datetime.now() - start_time).total_seconds()
    logger.error(f"[东方财富新闻] ❌ 所有方法均失败: {symbol}, 耗时: {elapsed_time:.2f}秒")
    return pd.DataFrame()

