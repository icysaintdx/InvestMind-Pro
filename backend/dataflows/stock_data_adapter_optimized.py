#!/usr/bin/env python3
"""
股票数据适配器 - 优化版
使用更高效的接口，避免下载全市场数据
数据源优先级：TDX Native > AKShare > 新浪财经 > 聚合数据 > Tushare > BaoStock
"""

import re
import asyncio
import requests
import os
from typing import Dict, Optional
from datetime import datetime, timedelta
from backend.utils.logging_config import get_logger

logger = get_logger("dataflow")


class StockDataAdapter:
    """股票数据适配器 - 统一不同数据源的格式"""

    def __init__(self):
        self._tdx_provider = None

    def _get_tdx_provider(self):
        """获取TDX Native Provider（懒加载）"""
        if self._tdx_provider is None:
            try:
                from backend.dataflows.providers.tdx_native_provider import get_tdx_native_provider
                self._tdx_provider = get_tdx_native_provider()
            except Exception as e:
                logger.debug(f"TDX Native Provider初始化失败: {e}")
        return self._tdx_provider

    def get_stock_data(self, symbol: str) -> Dict:
        """同步版本 - 兼容现有代码"""
        # 创建新的事件循环来运行异步方法
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.get_stock_data_async(symbol))
        finally:
            loop.close()

    async def get_stock_data_async(self, symbol: str) -> Dict:
        """
        获取股票实时数据 - 优化版
        优先级：TDX Native > AKShare > 新浪财经

        Args:
            symbol: 股票代码（如 '000001'）

        Returns:
            统一格式的数据字典
        """
        result = {
            'success': False,
            'symbol': symbol,
            'name': 'N/A',
            'price': 0,
            'change': 0,
            'change_amount': 0,
            'open': 0,
            'close': 0,
            'high': 0,
            'low': 0,
            'volume': 0,
            'amount': 0,
            'data_source': 'unknown',
            'raw_text': ''
        }

        logger.info(f"[StockDataAdapter] 开始获取股票 {symbol} 的数据")

        # 最高优先级：TDX Native Provider（最快，直接获取单只股票）
        try:
            tdx = self._get_tdx_provider()
            if tdx and tdx.is_available():
                quote = tdx.get_realtime_quote(symbol)
                if quote:
                    result['success'] = True
                    # 获取股票名称，如果TDX返回空则尝试其他方式获取
                    stock_name = quote.get('name', '') or ''
                    if not stock_name or stock_name == symbol:
                        # TDX返回的名称为空或就是代码本身，尝试从AKShare获取
                        try:
                            import akshare as ak
                            info_df = ak.stock_individual_info_em(symbol=symbol)
                            if info_df is not None and not info_df.empty:
                                name_row = info_df[info_df['item'] == '股票简称']
                                if not name_row.empty:
                                    stock_name = str(name_row['value'].iloc[0])
                                    logger.info(f"[StockDataAdapter] 从AKShare获取股票名称: {stock_name}")
                        except Exception as name_err:
                            logger.debug(f"[StockDataAdapter] 获取股票名称失败: {name_err}")

                    result['name'] = stock_name if stock_name else f'股票{symbol}'
                    result['price'] = float(quote.get('price', 0))
                    result['change'] = float(quote.get('change_pct', 0))
                    result['change_amount'] = float(quote.get('change', 0))
                    result['open'] = float(quote.get('open', 0))
                    result['close'] = float(quote.get('pre_close', 0))
                    result['high'] = float(quote.get('high', 0))
                    result['low'] = float(quote.get('low', 0))
                    result['volume'] = float(quote.get('volume', 0))
                    result['amount'] = float(quote.get('amount', 0))
                    result['data_source'] = 'tdx_native'
                    result['raw_text'] = self._format_as_text(result)
                    logger.info(f"[StockDataAdapter] ✅ TDX Native 获取成功, 股票名称: {result['name']}")
                    return result
        except Exception as e:
            logger.debug(f"[StockDataAdapter] TDX Native 失败: {e}")

        # 第一优先级：AKShare（使用更高效的接口）
        try:
            logger.info(f"[StockDataAdapter] 尝试使用 AKShare (优化版)...")
            import akshare as ak

            # 方法1：使用stock_bid_ask_em获取实时行情
            try:
                bid_ask_df = ak.stock_bid_ask_em(symbol=symbol)
                if bid_ask_df is not None and not bid_ask_df.empty:
                    # 解析数据
                    data_dict = dict(zip(bid_ask_df['item'], bid_ask_df['value']))
                    logger.info(f"[StockDataAdapter] 获取到的数据: {data_dict}")

                    # 获取股票名称（从 stock_individual_info_em 获取）
                    stock_name = 'N/A'
                    try:
                        info_df = ak.stock_individual_info_em(symbol=symbol)
                        if info_df is not None and not info_df.empty:
                            name_row = info_df[info_df['item'] == '股票简称']
                            if not name_row.empty:
                                stock_name = str(name_row['value'].iloc[0])
                                logger.info(f"[StockDataAdapter] 获取到股票名称: {stock_name}")
                    except Exception as name_err:
                        logger.warning(f"[StockDataAdapter] 获取股票名称失败: {name_err}")
                        # 尝试从全市场数据获取名称
                        try:
                            spot_df = ak.stock_zh_a_spot_em()
                            if spot_df is not None and not spot_df.empty:
                                stock_row = spot_df[spot_df['代码'] == symbol]
                                if not stock_row.empty:
                                    stock_name = str(stock_row.iloc[0].get('名称', f'股票{symbol}'))
                                    logger.info(f"[StockDataAdapter] 从全市场数据获取到股票名称: {stock_name}")
                        except:
                            pass
                    
                    result['success'] = True
                    result['name'] = stock_name
                    result['price'] = float(data_dict.get('最新', 0))
                    result['change'] = float(data_dict.get('涨幅', 0))
                    result['change_amount'] = float(data_dict.get('涨跌', 0))
                    result['open'] = float(data_dict.get('今开', 0))
                    result['close'] = float(data_dict.get('昨收', 0))
                    result['high'] = float(data_dict.get('最高', 0))
                    result['low'] = float(data_dict.get('最低', 0))
                    result['volume'] = int(data_dict.get('总手', 0)) * 100  # 手转股
                    result['amount'] = float(data_dict.get('金额', 0))
                    result['data_source'] = 'akshare'
                    result['raw_text'] = self._format_as_text(result)
                    
                    logger.info(f"[StockDataAdapter] ✅ AKShare stock_bid_ask_em 成功")
                    return result
            except Exception as e:
                logger.warning(f"[StockDataAdapter] stock_bid_ask_em 失败: {e}")
                pass
            
            # 方法2：使用历史数据接口（包含最新数据）
            try:
                # 获取日K线数据（最后一条是最新的）
                hist_df = ak.stock_zh_a_hist(symbol=symbol, period="daily", adjust="")
                if hist_df is not None and not hist_df.empty:
                    latest = hist_df.iloc[-1]

                    # 尝试获取股票名称
                    stock_name = f'股票{symbol}'
                    try:
                        info_df = ak.stock_individual_info_em(symbol=symbol)
                        if info_df is not None and not info_df.empty:
                            name_row = info_df[info_df['item'] == '股票简称']
                            if not name_row.empty:
                                stock_name = str(name_row['value'].iloc[0])
                    except:
                        pass

                    result['success'] = True
                    result['name'] = stock_name
                    result['price'] = float(latest.get('收盘', 0))
                    result['change'] = float(latest.get('涨跌幅', 0))
                    result['change_amount'] = float(latest.get('涨跌额', 0))
                    result['open'] = float(latest.get('开盘', 0))
                    result['close'] = result['price']  # 收盘价作为当前价
                    result['high'] = float(latest.get('最高', 0))
                    result['low'] = float(latest.get('最低', 0))
                    result['volume'] = float(latest.get('成交量', 0))
                    result['amount'] = float(latest.get('成交额', 0))
                    result['data_source'] = 'akshare'
                    result['raw_text'] = self._format_as_text(result)

                    logger.info(f"[StockDataAdapter] ✅ AKShare stock_zh_a_hist 成功")
                    return result
            except:
                pass
            
            # 方法3：如果前两个方法都失败，才使用全市场数据（最后手段）
            try:
                df = ak.stock_zh_a_spot_em()
                if df is not None and not df.empty:
                    stock = df[df['代码'] == symbol]
                    if not stock.empty:
                        row = stock.iloc[0]
                        result['success'] = True
                        result['name'] = str(row.get('名称', 'N/A'))
                        result['price'] = float(row.get('最新价', 0))
                        result['change'] = float(row.get('涨跌幅', 0))
                        result['change_amount'] = float(row.get('涨跌额', 0))
                        result['open'] = float(row.get('今开', 0))
                        result['close'] = float(row.get('昨收', 0))
                        result['high'] = float(row.get('最高', 0))
                        result['low'] = float(row.get('最低', 0))
                        result['volume'] = float(row.get('成交量', 0))
                        result['amount'] = float(row.get('成交额', 0))
                        result['data_source'] = 'akshare'
                        result['raw_text'] = self._format_as_text(result)
                        logger.info(f"[StockDataAdapter] ✅ AKShare stock_zh_a_spot_em 成功")
                        return result
            except:
                pass
                
        except Exception as e:
            logger.warning(f"[StockDataAdapter] AKShare 所有方法失败: {str(e)}")
        
        # 第二优先级：新浪财经（稳定性好）
        try:
            logger.info(f"[StockDataAdapter] 尝试使用 新浪财经...")
            # 格式化股票代码
            sina_code = symbol
            if symbol.startswith('6'):
                sina_code = 'sh' + symbol
            elif symbol.startswith(('0', '3')):
                sina_code = 'sz' + symbol
            
            url = f"https://hq.sinajs.cn/list={sina_code}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://finance.sina.com.cn'
            }
            
            resp = requests.get(url, headers=headers, timeout=5)
            if resp.status_code == 200 and f'hq_str_{sina_code}' in resp.text:
                data = resp.text.split('=')[1].strip('";')
                parts = data.split(',')
                if len(parts) >= 32:
                    result['success'] = True
                    result['name'] = parts[0]
                    result['price'] = float(parts[3])
                    result['change_amount'] = float(parts[3]) - float(parts[2]) if parts[2] else 0
                    result['change'] = (result['change_amount'] / float(parts[2]) * 100) if parts[2] and float(parts[2]) != 0 else 0
                    result['open'] = float(parts[1])
                    result['close'] = float(parts[2])
                    result['high'] = float(parts[4])
                    result['low'] = float(parts[5])
                    result['volume'] = float(parts[8])
                    result['amount'] = float(parts[9])
                    result['data_source'] = 'sina'
                    result['raw_text'] = self._format_as_text(result)
                    logger.info(f"[StockDataAdapter] ✅ 新浪财经 成功")
                    return result
        except Exception as e:
            logger.warning(f"[StockDataAdapter] 新浪财经 失败: {str(e)}")
        
        # 第三优先级：聚合数据（需要API Key）
        try:
            api_key = os.getenv('JUHE_API_KEY', '')
            if api_key:
                logger.info(f"[StockDataAdapter] 尝试使用 聚合数据...")
                # 暂时跳过聚合数据
                pass
        except Exception as e:
            pass
        
        # 第四优先级：Tushare（有积分限制）
        try:
            logger.info(f"[StockDataAdapter] 尝试使用 Tushare...")
            import tushare as ts
            df = ts.get_realtime_quotes(symbol)
            
            if df is not None and not df.empty:
                row = df.iloc[0]
                result['success'] = True
                result['name'] = str(row.get('name', 'N/A'))
                result['price'] = float(row.get('price', 0))
                # Tushare 免费接口可能没有涨跌幅
                result['change'] = 0
                result['change_amount'] = 0
                result['open'] = float(row.get('open', 0))
                result['close'] = float(row.get('pre_close', 0))
                result['high'] = float(row.get('high', 0))
                result['low'] = float(row.get('low', 0))
                result['volume'] = float(row.get('volume', 0))
                result['amount'] = float(row.get('amount', 0))
                result['data_source'] = 'tushare'
                result['raw_text'] = self._format_as_text(result)
                logger.info(f"[StockDataAdapter] ✅ Tushare 成功")
                return result
        except Exception as e:
            logger.warning(f"[StockDataAdapter] Tushare 失败: {str(e)}")
        
        # 第五优先级：BaoStock
        try:
            logger.info(f"[StockDataAdapter] 尝试使用 BaoStock...")
            import baostock as bs
            
            # 登录系统
            lg = bs.login()
            if lg.error_code == '0':
                # 格式化股票代码
                bs_code = symbol
                if symbol.startswith('6'):
                    bs_code = 'sh.' + symbol
                elif symbol.startswith(('0', '3')):
                    bs_code = 'sz.' + symbol
                
                # 获取最新数据
                from datetime import datetime
                today = datetime.now().strftime('%Y-%m-%d')
                rs = bs.query_history_k_data_plus(bs_code,
                    "date,code,open,high,low,close,volume,amount,pctChg",
                    start_date=today, end_date=today, frequency="d")
                
                if rs.error_code == '0':
                    data_list = []
                    while rs.next():
                        data_list.append(rs.get_row_data())
                    
                    if data_list:
                        latest = data_list[-1]
                        result['success'] = True
                        result['name'] = f'股票{symbol}'
                        result['price'] = float(latest[5])  # close
                        result['change'] = float(latest[8])  # pctChg
                        result['open'] = float(latest[2])
                        result['high'] = float(latest[3])
                        result['low'] = float(latest[4])
                        result['close'] = float(latest[5])
                        result['volume'] = float(latest[6])
                        result['amount'] = float(latest[7])
                        result['data_source'] = 'baostock'
                        result['raw_text'] = self._format_as_text(result)
                        
                        bs.logout()
                        logger.info(f"[StockDataAdapter] ✅ BaoStock 成功")
                        return result
                
                bs.logout()
        except Exception as e:
            logger.warning(f"[StockDataAdapter] BaoStock 失败: {str(e)}")
        
        # 最终降级：使用模拟数据
        logger.info(f"[StockDataAdapter] 所有数据源失败，使用模拟数据")
        result['success'] = True
        result['name'] = f'股票{symbol}'
        result['price'] = 10.00
        result['change'] = 1.5
        result['data_source'] = 'mock'
        result['raw_text'] = self._format_as_text(result)
        return result
    
    def _format_as_text(self, data: Dict) -> str:
        """将数据格式化为文本格式"""
        text = f"📊 {data['name']}({data['symbol']}) - {data['data_source'].upper()}数据\n"
        text += f"💰 最新价格: ¥{data['price']:.2f}\n"
        text += f"📈 涨跌幅: {data['change']:+.2f}%\n"
        text += f"📉 涨跌额: ¥{data['change_amount']:+.2f}\n"
        text += f"🔺 今开: ¥{data['open']:.2f}\n"
        text += f"🔺 昨收: ¥{data['close']:.2f}\n"
        text += f"📊 最高: ¥{data['high']:.2f}\n"
        text += f"📊 最低: ¥{data['low']:.2f}\n"
        text += f"📊 成交量: {data['volume']:.0f}手\n"
        text += f"💰 成交额: ¥{data['amount']:.2f}万"
        return text
    
    @staticmethod
    def parse_text_data(text: str, symbol: str) -> Dict:
        """
        从文本数据中提取结构化信息（保持兼容性）
        """
        result = {
            "symbol": symbol,
            "price": "N/A",
            "change": "N/A",
            "change_amount": "N/A",
            "open": "N/A",
            "close": "N/A",
            "high": "N/A",
            "low": "N/A",
            "volume": "N/A",
            "amount": "N/A",
            "name": "N/A",
            "data_source": "unknown"
        }
        
        # 识别数据源
        if "AKSHARE" in text.upper():
            result["data_source"] = "akshare"
        elif "SINA" in text.upper() or "新浪" in text:
            result["data_source"] = "sina"
        elif "TUSHARE" in text.upper():
            result["data_source"] = "tushare"
        elif "BAOSTOCK" in text.upper():
            result["data_source"] = "baostock"
        elif "MOCK" in text.upper():
            result["data_source"] = "mock"
        
        # 提取价格
        price_match = re.search(r'最新价格[：:]\s*¥?([\d.]+)', text)
        if price_match:
            result["price"] = price_match.group(1)
        
        # 提取涨跌幅
        change_match = re.search(r'涨跌幅[：:]\s*([+-]?[\d.]+)%', text)
        if change_match:
            result["change"] = change_match.group(1)
        
        # 提取名称
        name_match = re.search(r'📊\s*(.+?)\(', text)
        if name_match:
            result["name"] = name_match.group(1)
        
        return result
    
    @staticmethod
    def validate_data(data: Dict) -> bool:
        """验证数据有效性"""
        required_fields = ['price', 'change', 'name']
        for field in required_fields:
            if data.get(field) in [None, 'N/A', '', 0]:
                return False
        return True
