# -*- coding: utf-8 -*-
"""股票关联分析器 - 从新闻中提取关联股票"""
import re
import logging
from typing import List, Dict, Set, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class StockMatch:
    """股票匹配结果"""
    code: str           # 股票代码
    name: str           # 股票名称
    match_type: str     # 匹配类型: code/name/keyword
    confidence: float   # 置信度 0-1


class StockRelationAnalyzer:
    """股票关联分析器"""
    
    def __init__(self):
        # 股票代码正则
        self._code_pattern = re.compile(r"[（(]?([036]\d{5})[)）]?")
        self._code_with_suffix = re.compile(r"([036]\d{5})\.(SH|SZ|sh|sz)")
        
        # 股票名称缓存 (需要从数据库加载)
        self._stock_names: Dict[str, str] = {}  # name -> code
        self._stock_codes: Dict[str, str] = {}  # code -> name
        
        # 行业关键词映射
        self._industry_keywords = {
            "新能源": ["宁德时代", "比亚迪", "隆基绿能", "阳光电源"],
            "半导体": ["中芯国际", "韦尔股份", "北方华创", "中微公司"],
            "白酒": ["贵州茅台", "五粮液", "泸州老窖", "山西汾酒"],
            "银行": ["招商银行", "工商银行", "建设银行", "农业银行"],
            "医药": ["恒瑞医药", "药明康德", "迈瑞医疗", "片仔癀"],
            "互联网": ["腾讯", "阿里巴巴", "美团", "京东"],
            "房地产": ["万科", "保利发展", "招商蛇口", "金地集团"],
            "汽车": ["比亚迪", "长城汽车", "上汽集团", "广汽集团"],
        }
        
        # 加载股票列表
        self._load_stock_list()
        
        logger.info(f"StockRelationAnalyzer initialized with {len(self._stock_names)} stocks")
    
    def _load_stock_list(self):
        """加载股票列表"""
        try:
            # 尝试从数据库或缓存加载
            from backend.database.database import get_db
            from backend.database.models import MonitoredStock
            
            db = next(get_db())
            stocks = db.query(MonitoredStock).all()
            for stock in stocks:
                if stock.ts_code and stock.name:
                    code = stock.ts_code.split(".")[0]
                    self._stock_names[stock.name] = code
                    self._stock_codes[code] = stock.name
            db.close()
        except Exception as e:
            logger.warning(f"Failed to load stock list from DB: {e}")
            # 使用默认的热门股票
            self._load_default_stocks()
    
    def _load_default_stocks(self):
        """加载默认热门股票"""
        default_stocks = {
            "贵州茅台": "600519", "中国平安": "601318", "招商银行": "600036",
            "宁德时代": "300750", "比亚迪": "002594", "隆基绿能": "601012",
            "五粮液": "000858", "美的集团": "000333", "格力电器": "000651",
            "中芯国际": "688981", "药明康德": "603259", "迈瑞医疗": "300760",
            "恒瑞医药": "600276", "海天味业": "603288", "伊利股份": "600887",
            "万科A": "000002", "保利发展": "600048", "中国建筑": "601668",
            "工商银行": "601398", "建设银行": "601939", "农业银行": "601288",
            "中国银行": "601988", "交通银行": "601328", "邮储银行": "601658",
            "长城汽车": "601633", "上汽集团": "600104", "广汽集团": "601238",
            "中国中免": "601888", "海尔智家": "600690", "三一重工": "600031",
        }
        for name, code in default_stocks.items():
            self._stock_names[name] = code
            self._stock_codes[code] = name
    
    def analyze(self, title: str, content: str = "") -> List[StockMatch]:
        """
        分析新闻文本，提取关联股票
        
        Args:
            title: 新闻标题
            content: 新闻内容
            
        Returns:
            关联股票列表
        """
        text = f"{title} {content}"
        matches: List[StockMatch] = []
        seen_codes: Set[str] = set()
        
        # 1. 匹配股票代码
        for pattern in [self._code_with_suffix, self._code_pattern]:
            for match in pattern.finditer(text):
                code = match.group(1)
                if code not in seen_codes:
                    name = self._stock_codes.get(code, "")
                    matches.append(StockMatch(
                        code=code, name=name,
                        match_type="code",
                        confidence=0.95 if name else 0.7
                    ))
                    seen_codes.add(code)
        
        # 2. 匹配股票名称
        for name, code in self._stock_names.items():
            if name in text and code not in seen_codes:
                # 标题中出现置信度更高
                confidence = 0.9 if name in title else 0.7
                matches.append(StockMatch(
                    code=code, name=name,
                    match_type="name",
                    confidence=confidence
                ))
                seen_codes.add(code)
        
        # 3. 行业关键词关联
        for industry, stocks in self._industry_keywords.items():
            if industry in text:
                for stock_name in stocks:
                    code = self._stock_names.get(stock_name)
                    if code and code not in seen_codes:
                        matches.append(StockMatch(
                            code=code, name=stock_name,
                            match_type="keyword",
                            confidence=0.5
                        ))
                        seen_codes.add(code)
        
        # 按置信度排序
        matches.sort(key=lambda x: x.confidence, reverse=True)
        return matches[:10]  # 最多返回10个
    
    def get_related_codes(self, title: str, content: str = "") -> List[str]:
        """获取关联股票代码列表"""
        matches = self.analyze(title, content)
        return [m.code for m in matches]
    
    def add_stock(self, code: str, name: str):
        """添加股票到缓存"""
        self._stock_names[name] = code
        self._stock_codes[code] = name


# 全局实例
_analyzer = None

def get_stock_relation_analyzer() -> StockRelationAnalyzer:
    global _analyzer
    if _analyzer is None:
        _analyzer = StockRelationAnalyzer()
    return _analyzer
