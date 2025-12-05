#!/usr/bin/env python3
"""
股票数据适配器
统一不同数据源的返回格式，确保一致性
"""

import re
from typing import Dict, Optional
from backend.utils.logging_config import get_logger

logger = get_logger("dataflow")


class StockDataAdapter:
    """股票数据适配器 - 统一不同数据源的格式"""
    
    @staticmethod
    def parse_text_data(text: str, symbol: str) -> Dict:
        """
        从文本数据中提取结构化信息
        支持所有5种数据源格式：
        1. AKShare - DataFrame表格格式
        2. Tushare - Emoji格式（📊、💰、📈）
        3. 新浪财经 - 简单键值对格式
        4. 聚合数据 - JSON风格格式
        5. BaoStock - 表格格式
        
        Args:
            text: 数据源返回的文本
            symbol: 股票代码
            
        Returns:
            统一格式的字典
        """
        result = {
            "symbol": symbol,
            "name": f"股票{symbol}",
            "price": "N/A",
            "change": "N/A",
            "change_amount": "N/A",
            "open": "N/A",
            "close": "N/A",
            "high": "N/A",
            "low": "N/A",
            "volume": "N/A",
            "amount": "N/A",
            "data_source": "unknown",
            "raw_data": text
        }
        
        logger.info(f"[StockDataAdapter] 开始解析数据，文本长度: {len(text)}")
        
        try:
            # ✅ 步骤1：识别数据源
            if "新浪财经" in text or "Sina" in text:
                result["data_source"] = "sina"
                logger.info(f"[StockDataAdapter] 识别为新浪财经数据")
            elif "聚合数据" in text or "Juhe" in text:
                result["data_source"] = "juhe"
                logger.info(f"[StockDataAdapter] 识别为聚合数据")
            elif "Tushare" in text or "📊" in text:
                result["data_source"] = "tushare"
                logger.info(f"[StockDataAdapter] 识别为Tushare数据")
            elif "BaoStock" in text or "baostock" in text:
                result["data_source"] = "baostock"
                logger.info(f"[StockDataAdapter] 识别为BaoStock数据")
            elif "最新3天数据" in text or "最新数据" in text:
                result["data_source"] = "akshare"
                logger.info(f"[StockDataAdapter] 识别为AKShare数据")
            
            # ✅ 步骤2：根据数据源类型调用不同的解析方法
            if result["data_source"] == "tushare":
                StockDataAdapter._parse_tushare_format(text, result)
            elif result["data_source"] == "akshare":
                StockDataAdapter._parse_akshare_format(text, result)
            elif result["data_source"] == "sina":
                StockDataAdapter._parse_sina_format(text, result)
            elif result["data_source"] == "juhe":
                StockDataAdapter._parse_juhe_format(text, result)
            elif result["data_source"] == "baostock":
                StockDataAdapter._parse_baostock_format(text, result)
            else:
                # 通用解析（兼容所有格式）
                logger.warning(f"[StockDataAdapter] 未识别数据源，使用通用解析")
                StockDataAdapter._parse_generic_format(text, result)
            
            # 提取股票名称
            name_patterns = [
                r'📊 (.+?)\(',
                r'股票名称[：:]\s*(.+?)[\n\r]',
                r'名称[：:]\s*(.+?)[\n\r]'
            ]
            for pattern in name_patterns:
                match = re.search(pattern, text)
                if match:
                    result["name"] = match.group(1).strip()
                    break
            
            # ✅ 关键修复：从表格中提取最新数据
            # 尝试从表格中提取最后一行数据
            if '最新3天数据' in text or '最新数据' in text:
                # 提取表格最后一行
                lines = text.split('\n')
                for i, line in enumerate(lines):
                    if '最新3天数据' in line or '最新数据' in line:
                        # 找到表格数据行（跳过表头）
                        data_lines = []
                        for j in range(i+2, min(i+10, len(lines))):
                            if lines[j].strip() and not lines[j].startswith('📊'):
                                # 提取数字
                                numbers = re.findall(r'[\d.]+', lines[j])
                                if len(numbers) >= 8:  # 至少有8个数字（日期+价格数据）
                                    data_lines.append(numbers)
                        
                        # 使用最后一行数据（最新数据）
                        if data_lines:
                            last_data = data_lines[-1]
                            try:
                                # 假设格式：日期 代码 开盘 收盘 最高 最低 成交量 成交额 振幅 涨跌幅 涨跌额 换手率
                                if len(last_data) >= 4:
                                    result["open"] = last_data[2] if len(last_data) > 2 else "N/A"
                                    result["close"] = last_data[3] if len(last_data) > 3 else "N/A"
                                    result["price"] = last_data[3] if len(last_data) > 3 else "N/A"  # 收盘价=最新价
                                    result["high"] = last_data[4] if len(last_data) > 4 else "N/A"
                                    result["low"] = last_data[5] if len(last_data) > 5 else "N/A"
                                    
                                    # 涨跌幅和涨跌额
                                    if len(last_data) > 9:
                                        result["change"] = f"{last_data[9]}%"
                                    if len(last_data) > 10:
                                        result["change_amount"] = last_data[10]
                                    
                                    logger.info(f"[StockDataAdapter] ✅ 从表格提取数据: 价格={result['price']}, 涨跌幅={result['change']}")
                            except Exception as e:
                                logger.warning(f"[StockDataAdapter] 解析表格数据失败: {e}")
                        break
            
            # 如果表格解析失败，尝试使用原有的正则表达式
            if result["price"] == "N/A":
                price_patterns = [
                    r'💰 最新价格[：:]\s*¥?([\d.]+)',
                    r'最新价格[：:]\s*¥?([\d.]+)',
                    r'现价[：:]\s*¥?([\d.]+)',
                    r'当前价格[：:]\s*¥?([\d.]+)',
                    r'价格[：:]\s*¥?([\d.]+)'
                ]
                for pattern in price_patterns:
                    match = re.search(pattern, text)
                    if match:
                        result["price"] = match.group(1)
                        break
            
            # 提取涨跌幅
            change_patterns = [
                r'📈 涨跌幅[：:]\s*([+-]?[\d.]+)%',
                r'涨跌幅[：:]\s*([+-]?[\d.]+)%',
                r'涨跌[：:]\s*([+-]?[\d.]+)%'
            ]
            for pattern in change_patterns:
                match = re.search(pattern, text)
                if match:
                    result["change"] = match.group(1) + '%'
                    break
            
            # 提取涨跌额
            change_amount_patterns = [
                r'📉 涨跌额[：:]\s*¥?([+-]?[\d.]+)',
                r'涨跌额[：:]\s*¥?([+-]?[\d.]+)'
            ]
            for pattern in change_amount_patterns:
                match = re.search(pattern, text)
                if match:
                    result["change_amount"] = match.group(1)
                    break
            
            # 提取今开
            open_patterns = [
                r'🔺 今开[：:]\s*¥?([\d.]+)',
                r'今开[：:]\s*¥?([\d.]+)',
                r'开盘[：:]\s*¥?([\d.]+)'
            ]
            for pattern in open_patterns:
                match = re.search(pattern, text)
                if match:
                    result["open"] = match.group(1)
                    break
            
            # 提取昨收
            close_patterns = [
                r'🔺 昨收[：:]\s*¥?([\d.]+)',
                r'昨收[：:]\s*¥?([\d.]+)',
                r'前收[：:]\s*¥?([\d.]+)'
            ]
            for pattern in close_patterns:
                match = re.search(pattern, text)
                if match:
                    result["close"] = match.group(1)
                    break
            
            # 提取最高价
            high_patterns = [
                r'🔼 最高[：:]\s*¥?([\d.]+)',
                r'最高[：:]\s*¥?([\d.]+)',
                r'最高价[：:]\s*¥?([\d.]+)'
            ]
            for pattern in high_patterns:
                match = re.search(pattern, text)
                if match:
                    result["high"] = match.group(1)
                    break
            
            # 提取最低价
            low_patterns = [
                r'🔽 最低[：:]\s*¥?([\d.]+)',
                r'最低[：:]\s*¥?([\d.]+)',
                r'最低价[：:]\s*¥?([\d.]+)'
            ]
            for pattern in low_patterns:
                match = re.search(pattern, text)
                if match:
                    result["low"] = match.group(1)
                    break
            
            # 提取成交量
            volume_patterns = [
                r'📊 成交量[：:]\s*([\d.]+)(万手|手|股)',
                r'成交量[：:]\s*([\d.]+)(万手|手|股)',
                r'成交[：:]\s*([\d.]+)(万手|手|股)'
            ]
            for pattern in volume_patterns:
                match = re.search(pattern, text)
                if match:
                    result["volume"] = match.group(1) + match.group(2)
                    break
            
            # 提取成交额
            amount_patterns = [
                r'💵 成交额[：:]\s*([\d.]+)(亿元|亿|元)',
                r'成交额[：:]\s*([\d.]+)(亿元|亿|元)'
            ]
            for pattern in amount_patterns:
                match = re.search(pattern, text)
                if match:
                    result["amount"] = match.group(1) + match.group(2)
                    break
            
            logger.debug(f"[StockDataAdapter] 解析完成: {result['name']} {result['price']} {result['change']}")
            
        except Exception as e:
            logger.error(f"[StockDataAdapter] 解析失败: {e}")
        
        return result
    
    @staticmethod
    def validate_data(data: Dict) -> bool:
        """
        验证数据是否有效
        
        Args:
            data: 解析后的数据字典
            
        Returns:
            是否有效
        """
        # 至少要有价格信息
        if data.get("price") == "N/A" or not data.get("price"):
            logger.warning(f"[StockDataAdapter] 数据无效: 缺少价格信息")
            return False
        
        # 价格必须是有效数字
        try:
            float(data["price"])
        except (ValueError, TypeError):
            logger.warning(f"[StockDataAdapter] 数据无效: 价格格式错误 {data['price']}")
            return False
        
        return True
    
    @staticmethod
    def _parse_tushare_format(text: str, result: Dict) -> None:
        """解析Tushare格式（带emoji）"""
        logger.info(f"[StockDataAdapter] 使用Tushare解析器")
        
        # Tushare格式: 📊 股票名(000001) - Tushare数据
        # 💰 最新价格: ¥11.70
        # 📈 涨跌额: -0.25 (-2.09%)
        
        patterns = {
            'name': r'📊 (.+?)\(',
            'price': r'💰 最新价格[：:]\s*¥?([\d.]+)',
            'change': r'📈 涨跌额[：:]\s*[+-]?[\d.]+\s*\(([+-]?[\d.]+)%\)',
            'change_amount': r'📈 涨跌额[：:]\s*([+-]?[\d.]+)',
            'high': r'最高价[：:]\s*¥?([\d.]+)',
            'low': r'最低价[：:]\s*¥?([\d.]+)',
            'volume': r'成交量[：:]\s*([\d,.]+)'
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, text)
            if match:
                if key == 'change':
                    result[key] = match.group(1) + '%'
                else:
                    result[key] = match.group(1)
                logger.debug(f"[Tushare] 提取{key}: {result[key]}")
    
    @staticmethod
    def _parse_akshare_format(text: str, result: Dict) -> None:
        """解析AKShare格式（DataFrame表格）"""
        logger.info(f"[StockDataAdapter] 使用AKShare解析器")
        
        # AKShare返回DataFrame表格格式
        # 最新3天数据:
        #         日期   股票代码    开盘    收盘    最高    最低     成交量          成交额   振幅   涨跌幅   涨跌额  换手率
        # 2024-12-31 000001 11.93 11.70 11.99 11.70 1475367 1.747242e+09 2.43 -2.09 -0.25 0.76
        
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if '最新3天数据' in line or '最新数据' in line:
                # 找到表格数据行
                data_lines = []
                for j in range(i+2, min(i+10, len(lines))):
                    if lines[j].strip() and not lines[j].startswith('📊'):
                        numbers = re.findall(r'[\d.]+', lines[j])
                        if len(numbers) >= 8:
                            data_lines.append(numbers)
                
                if data_lines:
                    last_data = data_lines[-1]
                    try:
                        # 格式: 日期 代码 开盘 收盘 最高 最低 成交量 成交额 振幅 涨跌幅 涨跌额 换手率
                        result["open"] = last_data[2] if len(last_data) > 2 else "N/A"
                        result["close"] = last_data[3] if len(last_data) > 3 else "N/A"
                        result["price"] = last_data[3] if len(last_data) > 3 else "N/A"
                        result["high"] = last_data[4] if len(last_data) > 4 else "N/A"
                        result["low"] = last_data[5] if len(last_data) > 5 else "N/A"
                        
                        if len(last_data) > 9:
                            result["change"] = f"{last_data[9]}%"
                        if len(last_data) > 10:
                            result["change_amount"] = last_data[10]
                        
                        logger.info(f"[AKShare] ✅ 提取数据: 价格={result['price']}, 涨跌幅={result['change']}")
                    except Exception as e:
                        logger.warning(f"[AKShare] 解析失败: {e}")
                break
    
    @staticmethod
    def _parse_sina_format(text: str, result: Dict) -> None:
        """解析新浪财经格式（简单键值对）"""
        logger.info(f"[StockDataAdapter] 使用新浪财经解析器")
        
        # 新浪财经格式：
        # 股票名称: 平安银行
        # 最新价格: 11.70
        # 涨跌幅: -2.09%
        
        patterns = {
            'name': r'股票名称[：:]\s*(.+)',
            'price': r'最新价格[：:]\s*([\d.]+)',
            'change': r'涨跌幅[：:]\s*([+-]?[\d.]+)%',
            'open': r'开盘价[：:]\s*([\d.]+)',
            'high': r'最高价[：:]\s*([\d.]+)',
            'low': r'最低价[：:]\s*([\d.]+)',
            'volume': r'成交量[：:]\s*([\d.]+)'
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, text)
            if match:
                if key == 'change':
                    result[key] = match.group(1) + '%'
                else:
                    result[key] = match.group(1)
                logger.debug(f"[Sina] 提取{key}: {result[key]}")
    
    @staticmethod
    def _parse_juhe_format(text: str, result: Dict) -> None:
        """解析聚合数据JSON风格格式"""
        logger.info(f"[StockDataAdapter] 使用聚合数据解析器")
        
        # 聚合数据格式：
        # {
        #   "name": "平安银行",
        #   "nowpri": "11.70",
        #   "changepercent": "-2.09",
        #   "openpri": "11.93",
        #   "maxpri": "11.99",
        #   "minpri": "11.70"
        # }
        
        patterns = {
            'name': r'"name"\s*:\s*"(.+?)"',
            'price': r'"nowpri"\s*:\s*"([\d.]+)"',
            'change': r'"changepercent"\s*:\s*"([+-]?[\d.]+)"',
            'open': r'"openpri"\s*:\s*"([\d.]+)"',
            'high': r'"maxpri"\s*:\s*"([\d.]+)"',
            'low': r'"minpri"\s*:\s*"([\d.]+)"',
            'volume': r'"traNumber"\s*:\s*"([\d.]+)"'
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, text)
            if match:
                if key == 'change':
                    result[key] = match.group(1) + '%'
                else:
                    result[key] = match.group(1)
                logger.debug(f"[Juhe] 提取{key}: {result[key]}")
    
    @staticmethod
    def _parse_baostock_format(text: str, result: Dict) -> None:
        """解析BaoStock表格格式"""
        logger.info(f"[StockDataAdapter] 使用BaoStock解析器")
        
        # BaoStock返回表格格式，类似AKShare
        # 最新数据:
        # date       code      open   close   high   low    volume
        # 2024-12-31 sz.000001 11.93  11.70   11.99  11.70  1475367
        
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if '最新数据' in line or 'date' in line.lower():
                # 找到表格数据行
                data_lines = []
                for j in range(i+1, min(i+10, len(lines))):
                    if lines[j].strip():
                        parts = lines[j].split()
                        if len(parts) >= 6:
                            data_lines.append(parts)
                
                if data_lines:
                    last_data = data_lines[-1]
                    try:
                        # 格式: date code open close high low volume
                        result["open"] = last_data[2] if len(last_data) > 2 else "N/A"
                        result["close"] = last_data[3] if len(last_data) > 3 else "N/A"
                        result["price"] = last_data[3] if len(last_data) > 3 else "N/A"
                        result["high"] = last_data[4] if len(last_data) > 4 else "N/A"
                        result["low"] = last_data[5] if len(last_data) > 5 else "N/A"
                        
                        logger.info(f"[BaoStock] ✅ 提取数据: 价格={result['price']}")
                    except Exception as e:
                        logger.warning(f"[BaoStock] 解析失败: {e}")
                break
    
    @staticmethod
    def _parse_generic_format(text: str, result: Dict) -> None:
        """通用解析器（兼容所有格式）"""
        logger.info(f"[StockDataAdapter] 使用通用解析器")
        
        # 尝试所有可能的格式
        StockDataAdapter._parse_tushare_format(text, result)
        if result["price"] == "N/A":
            StockDataAdapter._parse_akshare_format(text, result)
        if result["price"] == "N/A":
            StockDataAdapter._parse_sina_format(text, result)
        if result["price"] == "N/A":
            StockDataAdapter._parse_juhe_format(text, result)
        if result["price"] == "N/A":
            StockDataAdapter._parse_baostock_format(text, result)
