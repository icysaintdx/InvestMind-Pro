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
        
        try:
            # 识别数据源
            if "新浪财经" in text:
                result["data_source"] = "sina"
            elif "聚合数据" in text:
                result["data_source"] = "juhe"
            elif "AKShare" in text:
                result["data_source"] = "akshare"
            elif "Tushare" in text:
                result["data_source"] = "tushare"
            
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
            
            # 提取价格（最新价格/现价）
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
