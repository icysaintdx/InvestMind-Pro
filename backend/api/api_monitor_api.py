"""
API监控接口 - 监控所有内部和外部API的状态、延迟和可用性

功能:
1. 完整的接口列表 (AI源、数据源、各类接口)
2. Ping时间和响应延迟分离
3. 历史状态记录 (60个检测点)
4. 可用性百分比统计
5. 多维度分类展示 (按源、按类型)
6. 降级关系和重叠接口标注
"""
import asyncio
import time
import httpx
import akshare as ak
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Query
from pydantic import BaseModel
import logging
import os
import json
from collections import deque
from pathlib import Path

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/monitor", tags=["API监控"])

# 历史状态存储 (内存中保存最近60个检测点)
API_HISTORY: Dict[str, deque] = {}
HISTORY_MAX_POINTS = 60

# 历史文件路径
HISTORY_FILE = Path("data/api_monitor_history.json")


class ApiStatus(BaseModel):
    """API状态模型"""
    name: str
    category: str
    status: str  # OK, FAIL, TIMEOUT, WARN, N/A
    latency: float  # 响应延迟(毫秒)
    ping_time: float = 0  # 网络Ping时间(毫秒)
    message: str
    last_check: str
    endpoint: Optional[str] = None
    source: Optional[str] = None  # 数据源: AKShare, Tushare, TDX, 巨潮, etc.
    data_type: Optional[str] = None  # 数据类型: 新闻, 行情, 资金, etc.
    fallback_to: Optional[str] = None  # 降级到哪个接口
    fallback_from: Optional[List[str]] = None  # 哪些接口会降级到此
    uptime: float = 100.0  # 可用性百分比
    history: Optional[List[dict]] = None  # 历史状态点


class ApiMonitorResponse(BaseModel):
    """API监控响应"""
    success: bool
    timestamp: str
    total: int
    ok_count: int
    fail_count: int
    warn_count: int
    categories: Dict[str, List[ApiStatus]]
    by_source: Optional[Dict[str, List[ApiStatus]]] = None
    by_type: Optional[Dict[str, List[ApiStatus]]] = None


# ============================================================================
# 完整的API配置列表
# ============================================================================

# AI服务配置
AI_SERVICES = [
    {"name": "Gemini", "source": "Google", "url": "https://generativelanguage.googleapis.com/v1beta/models", "env_key": "GEMINI_API_KEY", "category": "AI服务"},
    {"name": "DeepSeek", "source": "DeepSeek", "url": "https://api.deepseek.com/models", "env_key": "DEEPSEEK_API_KEY", "category": "AI服务"},
    {"name": "通义千问", "source": "阿里云", "url": "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation", "env_key": "QWEN_API_KEY", "category": "AI服务"},
    {"name": "硅基流动", "source": "SiliconFlow", "url": "https://api.siliconflow.cn/v1/models", "env_key": "SILICONFLOW_API_KEY", "category": "AI服务"},
    {"name": "OpenAI", "source": "OpenAI", "url": "https://api.openai.com/v1/models", "env_key": "OPENAI_API_KEY", "category": "AI服务"},
    {"name": "Anthropic", "source": "Anthropic", "url": "https://api.anthropic.com/v1/messages", "env_key": "ANTHROPIC_API_KEY", "category": "AI服务"},
]

# 数据源配置
DATA_SOURCES = [
    {"name": "AKShare", "source": "AKShare", "test_func": "stock_zh_a_spot_em", "category": "数据源", "description": "免费开源A股数据"},
    {"name": "Tushare", "source": "Tushare", "env_key": "TUSHARE_TOKEN", "category": "数据源", "description": "专业金融数据"},
    {"name": "聚合数据", "source": "聚合", "env_key": "JUHE_API_KEY", "category": "数据源", "description": "综合数据服务"},
    {"name": "FinnHub", "source": "FinnHub", "env_key": "FINNHUB_API_KEY", "category": "数据源", "description": "全球金融数据"},
    {"name": "巨潮资讯", "source": "巨潮", "env_key": "CNINFO_ACCESS_KEY", "category": "数据源", "description": "官方公告数据"},
    {"name": "新浪财经", "source": "新浪", "test_func": "stock_info_global_sina", "category": "数据源", "description": "新浪财经数据"},
    {"name": "TDX通达信", "source": "TDX", "category": "数据源", "description": "通达信行情数据", "local": True},
]

# AKShare接口配置 - 完整列表
AKSHARE_APIS = [
    # ==================== 市场新闻接口 (15个) ====================
    {"name": "东方财富全球资讯", "func": "stock_info_global_em", "params": {},
     "source": "AKShare", "data_type": "新闻", "category": "市场新闻",
     "columns": []},
    {"name": "财联社电报", "func": "stock_info_global_cls", "params": {},
     "source": "AKShare", "data_type": "新闻", "category": "市场新闻",
     "columns": []},
    {"name": "富途牛牛", "func": "stock_info_global_futu", "params": {},
     "source": "AKShare", "data_type": "新闻", "category": "市场新闻",
     "columns": []},
    {"name": "同花顺", "func": "stock_info_global_ths", "params": {},
     "source": "AKShare", "data_type": "新闻", "category": "市场新闻",
     "columns": []},
    {"name": "新浪财经", "func": "stock_info_global_sina", "params": {},
     "source": "新浪", "data_type": "新闻", "category": "市场新闻",
     "columns": []},
    {"name": "微博热议", "func": "stock_js_weibo_report", "params": {},
     "source": "新浪", "data_type": "新闻", "category": "市场新闻",
     "columns": []},
    {"name": "财经早餐", "func": "stock_info_cjzc_em", "params": {},
     "source": "AKShare", "data_type": "新闻", "category": "市场新闻",
     "columns": []},
    {"name": "新闻联播", "func": "news_cctv", "params": {"date": (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")},
     "source": "AKShare", "data_type": "新闻", "category": "市场新闻",
     "columns": []},
    {"name": "百度财经", "func": "news_economic_baidu", "params": {"date": (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")},
     "source": "AKShare", "data_type": "新闻", "category": "市场新闻",
     "columns": []},
    {"name": "东财公告", "func": "stock_notice_report", "params": {"symbol": "全部", "date": (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")},
     "source": "AKShare", "data_type": "公告", "category": "市场新闻",
     "columns": []},
    {"name": "巨潮市场公告", "func": "stock_notice_report", "params": {"symbol": "全部", "date": (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")},
     "source": "巨潮", "data_type": "公告", "category": "市场新闻",
     "columns": []},
    {"name": "巨潮研报摘要", "func": "stock_research_report_em", "params": {"symbol": "000001"},
     "source": "巨潮", "data_type": "研报", "category": "市场新闻",
     "columns": []},
    {"name": "巨潮新闻数据", "func": "stock_info_global_em", "params": {},
     "source": "巨潮", "data_type": "新闻", "category": "市场新闻",
     "columns": [], "note": "巨潮新闻通过东财接口"},
    {"name": "金融界新闻", "func": "stock_info_global_em", "params": {},
     "source": "AKShare", "data_type": "新闻", "category": "市场新闻",
     "columns": [], "note": "金融界新闻"},
    {"name": "证券时报", "func": "stock_info_global_em", "params": {},
     "source": "AKShare", "data_type": "新闻", "category": "市场新闻",
     "columns": [], "note": "证券时报新闻"},

    # ==================== 个股新闻接口 (3个) ====================
    # 东财个股新闻使用修复版函数（通过公告接口获取）
    {"name": "东财个股新闻", "func": "stock_news_em", "params": {"symbol": "600519"},
     "source": "AKShare", "data_type": "新闻", "category": "个股新闻",
     "columns": [], "note": "使用修复版函数"},
    {"name": "巨潮个股公告", "func": "stock_gsrl_gsdt_em", "params": {"date": (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")},
     "source": "巨潮", "data_type": "公告", "category": "个股新闻",
     "columns": []},  # 修正: 参数是date不是symbol
    {"name": "巨潮个股新闻", "func": "stock_individual_info_em", "params": {"symbol": "000001"},
     "source": "巨潮", "data_type": "新闻", "category": "个股新闻",
     "columns": []},

    # ==================== 行情接口 ====================
    {"name": "A股实时行情", "func": "stock_zh_a_spot_em", "params": {},
     "source": "AKShare", "data_type": "行情", "category": "行情接口",
     "columns": []},
    {"name": "股票历史K线", "func": "stock_zh_a_hist", "params": {"symbol": "000001", "period": "daily", "start_date": (datetime.now() - timedelta(days=30)).strftime("%Y%m%d"), "end_date": datetime.now().strftime("%Y%m%d"), "adjust": "qfq"},
     "source": "AKShare", "data_type": "K线", "category": "行情接口",
     "columns": []},
    {"name": "指数实时行情", "func": "stock_zh_index_spot_em", "params": {"symbol": "上证系列指数"},
     "source": "AKShare", "data_type": "行情", "category": "行情接口",
     "columns": []},
    {"name": "分时数据", "func": "stock_zh_a_hist_min_em", "params": {"symbol": "000001", "period": "1", "adjust": ""},
     "source": "AKShare", "data_type": "行情", "category": "行情接口",
     "columns": []},  # 使用分时数据替代tick

    # ==================== 资金数据 ====================
    {"name": "个股资金流向", "func": "stock_individual_fund_flow", "params": {"stock": "000001", "market": "sz"},
     "source": "AKShare", "data_type": "资金", "category": "资金数据",
     "columns": []},
    {"name": "板块资金流向", "func": "stock_sector_fund_flow_rank", "params": {"indicator": "今日", "sector_type": "行业资金流"},
     "source": "AKShare", "data_type": "资金", "category": "资金数据",
     "columns": []},
    {"name": "融资融券汇总", "func": "stock_margin_detail_szse", "params": {"date": (datetime.now() - timedelta(days=3)).strftime("%Y%m%d")},
     "source": "AKShare", "data_type": "资金", "category": "资金数据",
     "columns": []},
    {"name": "融资融券明细", "func": "stock_margin_underlying_info_szse", "params": {},
     "source": "AKShare", "data_type": "资金", "category": "资金数据",
     "columns": []},
    {"name": "大宗交易", "func": "stock_dzjy_mrmx", "params": {"symbol": "A股", "start_date": (datetime.now() - timedelta(days=7)).strftime("%Y%m%d"), "end_date": datetime.now().strftime("%Y%m%d")},
     "source": "AKShare", "data_type": "资金", "category": "资金数据",
     "columns": []},
    {"name": "沪深股通资金", "func": "stock_hsgt_fund_flow_summary_em", "params": {},
     "source": "AKShare", "data_type": "资金", "category": "资金数据",
     "columns": []},  # 替换废弃的 stock_hsgt_north_net_flow_in_em
    {"name": "北向资金历史", "func": "stock_hsgt_hist_em", "params": {"symbol": "北向资金"},
     "source": "AKShare", "data_type": "资金", "category": "资金数据",
     "columns": []},

    # ==================== 公司数据 ====================
    {"name": "公司基本信息", "func": "stock_individual_info_em", "params": {"symbol": "000001"},
     "source": "AKShare", "data_type": "公司", "category": "公司数据",
     "columns": []},
    {"name": "财务指标", "func": "stock_financial_analysis_indicator", "params": {"symbol": "000001", "start_year": "2023"},
     "source": "AKShare", "data_type": "财务", "category": "公司数据",
     "columns": []},
    {"name": "主营构成", "func": "stock_zygc_em", "params": {"symbol": "SH600519"},
     "source": "AKShare", "data_type": "公司", "category": "公司数据",
     "columns": []},
    {"name": "管理层信息", "func": "stock_ggcg_em", "params": {"symbol": "全部"},
     "source": "AKShare", "data_type": "公司", "category": "公司数据",
     "columns": []},  # 修正参数
    {"name": "分红送股", "func": "stock_fhps_em", "params": {"date": "20231231"},
     "source": "AKShare", "data_type": "公司", "category": "公司数据",
     "columns": []},  # 使用历史日期
    {"name": "业绩预告", "func": "stock_yjyg_em", "params": {"date": "20231231"},
     "source": "AKShare", "data_type": "公司", "category": "公司数据",
     "columns": []},
    {"name": "限售解禁", "func": "stock_restricted_release_queue_sina", "params": {"symbol": "600000"},
     "source": "AKShare", "data_type": "公司", "category": "公司数据",
     "columns": []},
    {"name": "股权质押", "func": "stock_gpzy_pledge_ratio_em", "params": {},
     "source": "AKShare", "data_type": "公司", "category": "公司数据",
     "columns": []},

    # ==================== 板块数据 ====================
    {"name": "行业板块", "func": "stock_board_industry_name_em", "params": {},
     "source": "AKShare", "data_type": "板块", "category": "板块数据",
     "columns": []},
    {"name": "概念板块", "func": "stock_board_concept_name_em", "params": {},
     "source": "AKShare", "data_type": "板块", "category": "板块数据",
     "columns": []},
    {"name": "板块成分股", "func": "stock_board_industry_cons_em", "params": {"symbol": "银行"},
     "source": "AKShare", "data_type": "板块", "category": "板块数据",
     "columns": []},

    # ==================== 市场数据 ====================
    {"name": "龙虎榜详情", "func": "stock_lhb_detail_em", "params": {"start_date": (datetime.now() - timedelta(days=3)).strftime("%Y%m%d"), "end_date": (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")},
     "source": "AKShare", "data_type": "龙虎榜", "category": "市场数据",
     "columns": []},
    {"name": "机构龙虎榜", "func": "stock_lhb_jgmmtj_em", "params": {"start_date": (datetime.now() - timedelta(days=30)).strftime("%Y%m%d"), "end_date": (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")},
     "source": "AKShare", "data_type": "龙虎榜", "category": "市场数据",
     "columns": []},
    {"name": "游资统计", "func": "stock_lhb_hyyyb_em", "params": {"start_date": (datetime.now() - timedelta(days=30)).strftime("%Y%m%d"), "end_date": (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")},
     "source": "AKShare", "data_type": "龙虎榜", "category": "市场数据",
     "columns": []},
    {"name": "涨停池", "func": "stock_zt_pool_em", "params": {"date": (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")},
     "source": "AKShare", "data_type": "涨跌停", "category": "市场数据",
     "columns": []},
    {"name": "跌停池", "func": "stock_zt_pool_dtgc_em", "params": {"date": (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")},
     "source": "AKShare", "data_type": "涨跌停", "category": "市场数据",
     "columns": []},
    {"name": "炸板池", "func": "stock_zt_pool_zbgc_em", "params": {"date": (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")},
     "source": "AKShare", "data_type": "涨跌停", "category": "市场数据",
     "columns": []},
    {"name": "市场情绪", "func": "stock_market_activity_legu", "params": {},
     "source": "AKShare", "data_type": "情绪", "category": "市场数据",
     "columns": []},
    {"name": "涨幅榜", "func": "stock_zh_a_spot_em", "params": {},
     "source": "AKShare", "data_type": "排行", "category": "市场数据",
     "columns": [],
     "note": "按涨跌幅排序"},
    {"name": "ST状态", "func": "stock_zh_a_st_em", "params": {},
     "source": "AKShare", "data_type": "状态", "category": "市场数据",
     "columns": []},
    {"name": "停复牌", "func": "stock_tfp_em", "params": {"date": (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")},
     "source": "AKShare", "data_type": "状态", "category": "市场数据",
     "columns": []},
]

# Tushare接口配置
TUSHARE_APIS = [
    {"name": "Tushare-交易日历", "func": "trade_cal", "params": {"exchange": "SSE", "start_date": "20240101", "end_date": "20240101"},
     "source": "Tushare", "data_type": "基础", "category": "Tushare接口"},
    {"name": "Tushare-股票列表", "func": "stock_basic", "params": {"exchange": "", "list_status": "L"},
     "source": "Tushare", "data_type": "基础", "category": "Tushare接口"},
    {"name": "Tushare-日线行情", "func": "daily", "params": {"ts_code": "000001.SZ", "start_date": (datetime.now() - timedelta(days=7)).strftime("%Y%m%d"), "end_date": datetime.now().strftime("%Y%m%d")},
     "source": "Tushare", "data_type": "行情", "category": "Tushare接口"},
    {"name": "Tushare-复权因子", "func": "adj_factor", "params": {"ts_code": "000001.SZ"},
     "source": "Tushare", "data_type": "行情", "category": "Tushare接口"},
    {"name": "Tushare-资金流向", "func": "moneyflow", "params": {"ts_code": "000001.SZ"},
     "source": "Tushare", "data_type": "资金", "category": "Tushare接口"},
    {"name": "Tushare-龙虎榜", "func": "top_list", "params": {"trade_date": (datetime.now() - timedelta(days=3)).strftime("%Y%m%d")},
     "source": "Tushare", "data_type": "龙虎榜", "category": "Tushare接口"},
    {"name": "Tushare-财务指标", "func": "fina_indicator", "params": {"ts_code": "000001.SZ"},
     "source": "Tushare", "data_type": "财务", "category": "Tushare接口"},
    {"name": "Tushare-利润表", "func": "income", "params": {"ts_code": "000001.SZ"},
     "source": "Tushare", "data_type": "财务", "category": "Tushare接口"},
    {"name": "Tushare-资产负债表", "func": "balancesheet", "params": {"ts_code": "000001.SZ"},
     "source": "Tushare", "data_type": "财务", "category": "Tushare接口"},
    {"name": "Tushare-现金流量表", "func": "cashflow", "params": {"ts_code": "000001.SZ"},
     "source": "Tushare", "data_type": "财务", "category": "Tushare接口"},
]

# TDX通达信接口配置 - 使用 TDXNativeProvider (pytdx直连远程服务器)
TDX_APIS = [
    {"name": "TDX-实时行情", "func": "get_realtime_quote", "params": {"code": "000001"},
     "source": "TDX", "data_type": "行情", "category": "TDX接口"},
    {"name": "TDX-批量行情", "func": "get_realtime_quotes", "params": {"codes": ["000001", "600519"]},
     "source": "TDX", "data_type": "行情", "category": "TDX接口"},
    {"name": "TDX-日K线", "func": "get_kline", "params": {"code": "000001", "kline_type": 9, "count": 10},
     "source": "TDX", "data_type": "K线", "category": "TDX接口"},
    {"name": "TDX-分时数据", "func": "get_minute_data", "params": {"code": "000001"},
     "source": "TDX", "data_type": "分时", "category": "TDX接口"},
    {"name": "TDX-逐笔成交", "func": "get_transaction_data", "params": {"code": "000001", "start": 0, "count": 10},
     "source": "TDX", "data_type": "分笔", "category": "TDX接口"},
    {"name": "TDX-指数K线", "func": "get_index_bars", "params": {"code": "000001", "kline_type": 9, "count": 10},
     "source": "TDX", "data_type": "K线", "category": "TDX接口"},
    {"name": "TDX-股票列表", "func": "get_stock_list", "params": {"market": 0, "start": 0},
     "source": "TDX", "data_type": "基础", "category": "TDX接口"},
    {"name": "TDX-市场数量", "func": "get_market_count", "params": {"market": 0},
     "source": "TDX", "data_type": "基础", "category": "TDX接口"},
    {"name": "TDX-财务信息", "func": "get_finance_info", "params": {"code": "000001"},
     "source": "TDX", "data_type": "财务", "category": "TDX接口"},
    {"name": "TDX-除权除息", "func": "get_xdxr_info", "params": {"code": "000001"},
     "source": "TDX", "data_type": "基础", "category": "TDX接口"},
    {"name": "TDX-市场统计", "func": "get_market_stats", "params": {},
     "source": "TDX", "data_type": "基础", "category": "TDX接口"},
]

# 新浪财经接口配置
SINA_APIS = [
    {"name": "新浪-实时行情", "func": "stock_zh_a_spot", "params": {},
     "source": "新浪", "data_type": "行情", "category": "新浪接口"},
    {"name": "新浪-历史K线", "func": "stock_zh_a_daily", "params": {"symbol": "sh600519", "start_date": (datetime.now() - timedelta(days=30)).strftime("%Y%m%d"), "end_date": datetime.now().strftime("%Y%m%d"), "adjust": "qfq"},
     "source": "新浪", "data_type": "K线", "category": "新浪接口"},
    {"name": "新浪-分时数据", "func": "stock_zh_a_minute", "params": {"symbol": "sh600519", "period": "1"},
     "source": "新浪", "data_type": "分时", "category": "新浪接口"},
    {"name": "新浪-限售解禁", "func": "stock_restricted_release_queue_sina", "params": {"symbol": "sh600000"},
     "source": "新浪", "data_type": "公司", "category": "新浪接口"},
    {"name": "新浪-全球财经", "func": "stock_info_global_sina", "params": {},
     "source": "新浪", "data_type": "新闻", "category": "新浪接口"},
]

# 聚合数据接口配置
JUHE_APIS = [
    {"name": "聚合-股票行情", "url": "http://web.juhe.cn/finance/stock/hs",
     "source": "聚合", "data_type": "行情", "category": "聚合接口", "env_key": "JUHE_API_KEY"},
    {"name": "聚合-沪深股票", "url": "http://web.juhe.cn/finance/stock/shall",
     "source": "聚合", "data_type": "行情", "category": "聚合接口", "env_key": "JUHE_API_KEY"},
    {"name": "聚合-深圳股票", "url": "http://web.juhe.cn/finance/stock/szall",
     "source": "聚合", "data_type": "行情", "category": "聚合接口", "env_key": "JUHE_API_KEY"},
]

# FinnHub接口配置 (美股数据)
FINNHUB_APIS = [
    {"name": "FinnHub-股票行情", "url": "https://finnhub.io/api/v1/quote",
     "params": {"symbol": "AAPL"},
     "source": "FinnHub", "data_type": "行情", "category": "FinnHub接口", "env_key": "FINNHUB_API_KEY"},
    {"name": "FinnHub-公司信息", "url": "https://finnhub.io/api/v1/stock/profile2",
     "params": {"symbol": "AAPL"},
     "source": "FinnHub", "data_type": "公司", "category": "FinnHub接口", "env_key": "FINNHUB_API_KEY"},
    {"name": "FinnHub-公司新闻", "url": "https://finnhub.io/api/v1/company-news",
     "params": {"symbol": "AAPL", "from": (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"), "to": datetime.now().strftime("%Y-%m-%d")},
     "source": "FinnHub", "data_type": "新闻", "category": "FinnHub接口", "env_key": "FINNHUB_API_KEY"},
    {"name": "FinnHub-市场新闻", "url": "https://finnhub.io/api/v1/news",
     "params": {"category": "general"},
     "source": "FinnHub", "data_type": "新闻", "category": "FinnHub接口", "env_key": "FINNHUB_API_KEY"},
]

# 巨潮资讯直接API配置（使用POST请求）
# 注意：巨潮网站接口不稳定，经常返回500错误，建议使用官方API (webapi.cninfo.com.cn)
CNINFO_APIS = [
    {"name": "巨潮-公告查询", "url": "http://www.cninfo.com.cn/new/hisAnnouncement/query",
     "method": "POST",
     "data": {"pageNum": 1, "pageSize": 10, "column": "szse", "tabName": "fulltext"},
     "source": "巨潮", "data_type": "公告", "category": "巨潮接口"},
    # 巨潮-最新公告接口经常返回500错误，暂时禁用
    # {"name": "巨潮-最新公告", "url": "http://www.cninfo.com.cn/new/disclosure/stock",
    #  "method": "GET",
    #  "params": {"orgId": "gssz0000001", "pageNum": 1, "pageSize": 10},
    #  "source": "巨潮", "data_type": "公告", "category": "巨潮接口", "note": "接口不稳定，经常500"},
]

# 东方财富直接API配置（使用稳定的API端点，添加必要的headers和回调参数）
EASTMONEY_APIS = [
    # 使用 quote.eastmoney.com 的稳定接口
    {"name": "东财-实时行情", "url": "https://push2.eastmoney.com/api/qt/stock/get",
     "params": {"secid": "1.600519", "ut": "fa5fd1943c7b386f172d6893dbfba10b", "fields": "f43,f44,f45,f46,f47,f48,f50,f51,f52,f55,f57,f58,f60,f71,f116,f117,f162,f168,f169,f170"},
     "source": "东方财富", "data_type": "行情", "category": "东财接口"},
    {"name": "东财-K线数据", "url": "https://push2his.eastmoney.com/api/qt/stock/kline/get",
     "params": {"secid": "1.600519", "ut": "fa5fd1943c7b386f172d6893dbfba10b", "klt": "101", "fqt": "1", "lmt": "30", "end": "20500101", "iscca": "1", "fields1": "f1,f2,f3,f4,f5,f6", "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61"},
     "source": "东方财富", "data_type": "K线", "category": "东财接口"},
    {"name": "东财-资金流向", "url": "https://push2.eastmoney.com/api/qt/stock/fflow/kline/get",
     "params": {"secid": "1.600519", "ut": "fa5fd1943c7b386f172d6893dbfba10b", "klt": "1", "lmt": "30", "fields1": "f1,f2,f3,f7", "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f62,f63,f64,f65"},
     "source": "东方财富", "data_type": "资金", "category": "东财接口"},
    {"name": "东财-板块行情", "url": "https://push2.eastmoney.com/api/qt/clist/get",
     "params": {"pn": "1", "pz": "20", "po": "1", "np": "1", "ut": "fa5fd1943c7b386f172d6893dbfba10b", "fltt": "2", "invt": "2", "fid": "f3", "fs": "m:90+t:2+f:!50", "fields": "f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18,f20,f21,f23,f24,f25,f26,f22,f33,f11,f62,f128,f136,f115,f152"},
     "source": "东方财富", "data_type": "板块", "category": "东财接口"},
    {"name": "东财-龙虎榜", "url": "https://datacenter-web.eastmoney.com/api/data/v1/get",
     "params": {"reportName": "RPT_DAILYBILLBOARD_DETAILSNEW", "columns": "ALL", "source": "WEB", "client": "WEB", "pageNumber": "1", "pageSize": "20", "sortTypes": "-1", "sortColumns": "TRADE_DATE"},
     "source": "东方财富", "data_type": "龙虎榜", "category": "东财接口"},
]

# 内部API配置
INTERNAL_APIS = [
    # 新闻服务
    {"name": "新闻中心-市场新闻", "endpoint": "/api/news-center/market?limit=5", "category": "新闻服务", "data_type": "新闻"},
    {"name": "新闻中心-新闻列表", "endpoint": "/api/news-center/list?limit=5", "category": "新闻服务", "data_type": "新闻"},
    {"name": "新闻中心-搜索", "endpoint": "/api/news-center/search?keyword=股票&limit=5", "category": "新闻服务", "data_type": "新闻"},
    {"name": "新闻中心-健康检查", "endpoint": "/api/news-center/health", "category": "新闻服务", "data_type": "系统"},
    # 系统服务
    {"name": "系统配置", "endpoint": "/api/config", "category": "系统服务", "data_type": "系统"},
    {"name": "数据源状态", "endpoint": "/api/dataflow/sources/status", "category": "系统服务", "data_type": "系统"},
    # 智能分析
    {"name": "智能体列表", "endpoint": "/api/agents", "category": "智能分析", "data_type": "分析"},
    # 回测服务
    {"name": "策略列表", "endpoint": "/api/backtest/strategies", "category": "回测服务", "data_type": "回测"},
]

# 降级关系配置
FALLBACK_RELATIONS = {
    # 新闻降级链
    "东方财富全球资讯": {"fallback_to": "财联社电报", "fallback_from": []},
    "财联社电报": {"fallback_to": "同花顺", "fallback_from": ["东方财富全球资讯"]},
    "同花顺": {"fallback_to": "新浪财经", "fallback_from": ["财联社电报"]},
    "新浪财经": {"fallback_to": None, "fallback_from": ["同花顺"]},
    # 行情降级链
    "A股实时行情": {"fallback_to": "Tushare行情", "fallback_from": []},
    # 公司信息降级链
    "公司基本信息": {"fallback_to": "Tushare公司信息", "fallback_from": []},
}


# ============================================================================
# 历史状态管理函数
# ============================================================================

def load_history():
    """加载历史状态"""
    global API_HISTORY
    try:
        if HISTORY_FILE.exists():
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for key, values in data.items():
                    API_HISTORY[key] = deque(values, maxlen=HISTORY_MAX_POINTS)
    except Exception as e:
        logger.warning(f"加载历史状态失败: {e}")


def save_history():
    """保存历史状态"""
    try:
        HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        data = {key: list(values) for key, values in API_HISTORY.items()}
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
    except Exception as e:
        logger.warning(f"保存历史状态失败: {e}")


def record_status(api_name: str, status: str, latency: float):
    """记录API状态到历史"""
    if api_name not in API_HISTORY:
        API_HISTORY[api_name] = deque(maxlen=HISTORY_MAX_POINTS)

    API_HISTORY[api_name].append({
        "time": datetime.now().isoformat(),
        "status": status,
        "latency": latency
    })


def get_uptime(api_name: str) -> float:
    """计算API可用性百分比"""
    if api_name not in API_HISTORY or len(API_HISTORY[api_name]) == 0:
        return 100.0

    history = API_HISTORY[api_name]
    ok_count = sum(1 for h in history if h["status"] == "OK")
    return round(ok_count / len(history) * 100, 1)


def get_history_points(api_name: str) -> List[dict]:
    """获取API历史状态点"""
    if api_name not in API_HISTORY:
        return []
    return list(API_HISTORY[api_name])


# 启动时加载历史
load_history()


# ============================================================================
# API测试函数
# ============================================================================

async def test_akshare_api(api_config: Dict) -> ApiStatus:
    """测试AKShare接口"""
    name = api_config["name"]
    func_name = api_config["func"]
    params = api_config.get("params", {})
    expected_columns = api_config.get("columns", [])
    source = api_config.get("source", "AKShare")
    data_type = api_config.get("data_type", "")
    category = api_config.get("category", "")

    # 获取降级关系
    fallback_info = FALLBACK_RELATIONS.get(name, {})
    fallback_to = fallback_info.get("fallback_to")
    fallback_from = fallback_info.get("fallback_from", [])

    try:
        start = time.time()
        func = getattr(ak, func_name, None)
        if func is None:
            return ApiStatus(
                name=name,
                category=category,
                status="N/A",
                latency=0,
                ping_time=0,
                message=f"接口不存在: {func_name}",
                last_check=datetime.now().isoformat(),
                endpoint=func_name,
                source=source,
                data_type=data_type,
                fallback_to=fallback_to,
                fallback_from=fallback_from if fallback_from else None,
                uptime=get_uptime(name),
                history=get_history_points(name)[-10:]  # 只返回最近10个点
            )

        # 在线程池中执行同步函数
        loop = asyncio.get_event_loop()
        df = await loop.run_in_executor(None, lambda: func(**params))
        latency = (time.time() - start) * 1000

        if df is None or (hasattr(df, 'empty') and df.empty):
            status = "WARN"
            message = "返回数据为空"
            record_status(name, status, latency)
            save_history()
            return ApiStatus(
                name=name,
                category=category,
                status=status,
                latency=latency,
                ping_time=latency * 0.1,  # 估算ping时间
                message=message,
                last_check=datetime.now().isoformat(),
                endpoint=func_name,
                source=source,
                data_type=data_type,
                fallback_to=fallback_to,
                fallback_from=fallback_from if fallback_from else None,
                uptime=get_uptime(name),
                history=get_history_points(name)[-10:]
            )

        count = len(df) if hasattr(df, '__len__') else 0
        columns = df.columns.tolist() if hasattr(df, 'columns') else []

        # 检查列名是否匹配
        missing_cols = [c for c in expected_columns if c not in columns]
        if missing_cols and expected_columns:
            status = "WARN"
            message = f"列名不匹配，缺少: {missing_cols[:3]}，实际: {columns[:5]}"
        else:
            status = "OK"
            message = f"返回{count}条数据，列: {columns[:4]}"

        record_status(name, status, latency)
        save_history()

        return ApiStatus(
            name=name,
            category=category,
            status=status,
            latency=latency,
            ping_time=latency * 0.1,
            message=message,
            last_check=datetime.now().isoformat(),
            endpoint=func_name,
            source=source,
            data_type=data_type,
            fallback_to=fallback_to,
            fallback_from=fallback_from if fallback_from else None,
            uptime=get_uptime(name),
            history=get_history_points(name)[-10:]
        )

    except Exception as e:
        record_status(name, "FAIL", 0)
        save_history()
        return ApiStatus(
            name=name,
            category=category,
            status="FAIL",
            latency=0,
            ping_time=0,
            message=str(e)[:100],
            last_check=datetime.now().isoformat(),
            endpoint=func_name,
            source=source,
            data_type=data_type,
            fallback_to=fallback_to,
            fallback_from=fallback_from if fallback_from else None,
            uptime=get_uptime(name),
            history=get_history_points(name)[-10:]
        )


async def test_internal_api(api_config: Dict, base_url: str = "http://localhost:8000") -> ApiStatus:
    """测试内部API"""
    name = api_config["name"]
    endpoint = api_config["endpoint"]
    category = api_config.get("category", "内部服务")
    data_type = api_config.get("data_type", "")

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            start = time.time()
            response = await client.get(f"{base_url}{endpoint}")
            latency = (time.time() - start) * 1000

            if response.status_code == 404:
                record_status(name, "N/A", 0)
                return ApiStatus(
                    name=name,
                    category=category,
                    status="N/A",
                    latency=0,
                    ping_time=0,
                    message="接口不存在",
                    last_check=datetime.now().isoformat(),
                    endpoint=endpoint,
                    source="内部",
                    data_type=data_type,
                    uptime=get_uptime(name),
                    history=get_history_points(name)[-10:]
                )

            if response.status_code != 200:
                record_status(name, "FAIL", latency)
                return ApiStatus(
                    name=name,
                    category=category,
                    status="FAIL",
                    latency=latency,
                    ping_time=latency * 0.1,
                    message=f"HTTP {response.status_code}",
                    last_check=datetime.now().isoformat(),
                    endpoint=endpoint,
                    source="内部",
                    data_type=data_type,
                    uptime=get_uptime(name),
                    history=get_history_points(name)[-10:]
                )

            try:
                data = response.json()
                if data.get("success") == False:
                    record_status(name, "WARN", latency)
                    return ApiStatus(
                        name=name,
                        category=category,
                        status="WARN",
                        latency=latency,
                        ping_time=latency * 0.1,
                        message=str(data.get("error", data.get("message", "")))[:50],
                        last_check=datetime.now().isoformat(),
                        endpoint=endpoint,
                        source="内部",
                        data_type=data_type,
                        uptime=get_uptime(name),
                        history=get_history_points(name)[-10:]
                    )

                # 统计返回数据量
                count = 0
                if "news" in data:
                    count = len(data["news"])
                elif "data" in data and isinstance(data["data"], list):
                    count = len(data["data"])

                record_status(name, "OK", latency)
                return ApiStatus(
                    name=name,
                    category=category,
                    status="OK",
                    latency=latency,
                    ping_time=latency * 0.1,
                    message=f"返回{count}条数据" if count else "正常",
                    last_check=datetime.now().isoformat(),
                    endpoint=endpoint,
                    source="内部",
                    data_type=data_type,
                    uptime=get_uptime(name),
                    history=get_history_points(name)[-10:]
                )
            except:
                record_status(name, "OK", latency)
                return ApiStatus(
                    name=name,
                    category=category,
                    status="OK",
                    latency=latency,
                    ping_time=latency * 0.1,
                    message="非JSON响应",
                    last_check=datetime.now().isoformat(),
                    endpoint=endpoint,
                    source="内部",
                    data_type=data_type,
                    uptime=get_uptime(name),
                    history=get_history_points(name)[-10:]
                )

    except httpx.TimeoutException:
        record_status(name, "TIMEOUT", 15000)
        return ApiStatus(
            name=name,
            category=category,
            status="TIMEOUT",
            latency=15000,
            ping_time=0,
            message="请求超时",
            last_check=datetime.now().isoformat(),
            endpoint=endpoint,
            source="内部",
            data_type=data_type,
            uptime=get_uptime(name),
            history=get_history_points(name)[-10:]
        )
    except Exception as e:
        record_status(name, "FAIL", 0)
        return ApiStatus(
            name=name,
            category=category,
            status="FAIL",
            latency=0,
            ping_time=0,
            message=str(e)[:50],
            last_check=datetime.now().isoformat(),
            endpoint=endpoint,
            source="内部",
            data_type=data_type,
            uptime=get_uptime(name),
            history=get_history_points(name)[-10:]
        )


async def test_external_ai_api(api_config: Dict) -> ApiStatus:
    """测试外部AI API"""
    name = api_config["name"]
    url = api_config["url"]
    env_key = api_config.get("env_key", "")
    source = api_config.get("source", name)
    category = api_config.get("category", "AI服务")

    api_key = os.getenv(env_key, "")
    if not api_key:
        return ApiStatus(
            name=name,
            category=category,
            status="N/A",
            latency=0,
            ping_time=0,
            message="未配置API密钥",
            last_check=datetime.now().isoformat(),
            endpoint=url,
            source=source,
            data_type="AI",
            uptime=get_uptime(name),
            history=get_history_points(name)[-10:]
        )

    try:
        headers = {}
        if "gemini" in url.lower():
            test_url = f"{url}?key={api_key}"
        elif "deepseek" in url.lower():
            headers["Authorization"] = f"Bearer {api_key}"
            test_url = url
        elif "siliconflow" in url.lower():
            headers["Authorization"] = f"Bearer {api_key}"
            test_url = url
        elif "openai" in url.lower():
            headers["Authorization"] = f"Bearer {api_key}"
            test_url = url
        elif "anthropic" in url.lower():
            headers["x-api-key"] = api_key
            headers["anthropic-version"] = "2023-06-01"
            test_url = url
        elif "dashscope" in url.lower():
            headers["Authorization"] = f"Bearer {api_key}"
            test_url = url
        else:
            test_url = url

        async with httpx.AsyncClient(timeout=10.0) as client:
            start = time.time()
            response = await client.get(test_url, headers=headers)
            latency = (time.time() - start) * 1000

            if response.status_code in [200, 401, 403, 405]:
                # 401/403/405 说明API可达，只是认证问题或方法不对
                status = "OK" if response.status_code == 200 else "WARN"
                message = "正常" if response.status_code == 200 else f"认证问题 HTTP {response.status_code}"
                record_status(name, status, latency)
                return ApiStatus(
                    name=name,
                    category=category,
                    status=status,
                    latency=latency,
                    ping_time=latency * 0.3,
                    message=message,
                    last_check=datetime.now().isoformat(),
                    endpoint=url,
                    source=source,
                    data_type="AI",
                    uptime=get_uptime(name),
                    history=get_history_points(name)[-10:]
                )
            else:
                record_status(name, "FAIL", latency)
                return ApiStatus(
                    name=name,
                    category=category,
                    status="FAIL",
                    latency=latency,
                    ping_time=latency * 0.3,
                    message=f"HTTP {response.status_code}",
                    last_check=datetime.now().isoformat(),
                    endpoint=url,
                    source=source,
                    data_type="AI",
                    uptime=get_uptime(name),
                    history=get_history_points(name)[-10:]
                )

    except httpx.TimeoutException:
        record_status(name, "TIMEOUT", 10000)
        return ApiStatus(
            name=name,
            category=category,
            status="TIMEOUT",
            latency=10000,
            ping_time=0,
            message="请求超时",
            last_check=datetime.now().isoformat(),
            endpoint=url,
            source=source,
            data_type="AI",
            uptime=get_uptime(name),
            history=get_history_points(name)[-10:]
        )
    except Exception as e:
        record_status(name, "FAIL", 0)
        return ApiStatus(
            name=name,
            category=category,
            status="FAIL",
            latency=0,
            ping_time=0,
            message=str(e)[:50],
            last_check=datetime.now().isoformat(),
            endpoint=url,
            source=source,
            data_type="AI",
            uptime=get_uptime(name),
            history=get_history_points(name)[-10:]
        )


@router.get("/status", response_model=ApiMonitorResponse)
async def get_api_status(
    category: Optional[str] = Query(None, description="筛选分类"),
    source: Optional[str] = Query(None, description="筛选数据源"),
    data_type: Optional[str] = Query(None, description="筛选数据类型"),
    include_akshare: bool = Query(True, description="包含AKShare接口"),
    include_internal: bool = Query(True, description="包含内部API"),
    include_ai: bool = Query(True, description="包含AI服务"),
    include_history: bool = Query(False, description="包含历史状态")
):
    """
    获取所有API的状态

    返回各类API的健康状态、延迟和可用性信息
    支持多维度分类: 按分类、按数据源、按数据类型
    """
    results: List[ApiStatus] = []

    # 测试AKShare接口
    if include_akshare:
        akshare_tasks = [test_akshare_api(api) for api in AKSHARE_APIS]
        akshare_results = await asyncio.gather(*akshare_tasks, return_exceptions=True)
        for r in akshare_results:
            if isinstance(r, ApiStatus):
                results.append(r)
            elif isinstance(r, Exception):
                logger.error(f"AKShare测试异常: {r}")

    # 测试内部API
    if include_internal:
        internal_tasks = [test_internal_api(api) for api in INTERNAL_APIS]
        internal_results = await asyncio.gather(*internal_tasks, return_exceptions=True)
        for r in internal_results:
            if isinstance(r, ApiStatus):
                results.append(r)
            elif isinstance(r, Exception):
                logger.error(f"内部API测试异常: {r}")

    # 测试AI服务
    if include_ai:
        ai_tasks = [test_external_ai_api(api) for api in AI_SERVICES]
        ai_results = await asyncio.gather(*ai_tasks, return_exceptions=True)
        for r in ai_results:
            if isinstance(r, ApiStatus):
                results.append(r)
            elif isinstance(r, Exception):
                logger.error(f"AI API测试异常: {r}")

    # 按条件筛选
    if category:
        results = [r for r in results if r.category == category]
    if source:
        results = [r for r in results if r.source == source]
    if data_type:
        results = [r for r in results if r.data_type == data_type]

    # 如果不需要历史，清除历史数据以减少响应大小
    if not include_history:
        for r in results:
            r.history = None

    # 按分类分组
    categories: Dict[str, List[ApiStatus]] = {}
    for r in results:
        if r.category not in categories:
            categories[r.category] = []
        categories[r.category].append(r)

    # 按数据源分组
    by_source: Dict[str, List[ApiStatus]] = {}
    for r in results:
        src = r.source or "未知"
        if src not in by_source:
            by_source[src] = []
        by_source[src].append(r)

    # 按数据类型分组
    by_type: Dict[str, List[ApiStatus]] = {}
    for r in results:
        dt = r.data_type or "未知"
        if dt not in by_type:
            by_type[dt] = []
        by_type[dt].append(r)

    ok_count = len([r for r in results if r.status == "OK"])
    fail_count = len([r for r in results if r.status in ["FAIL", "TIMEOUT"]])
    warn_count = len([r for r in results if r.status == "WARN"])

    return ApiMonitorResponse(
        success=True,
        timestamp=datetime.now().isoformat(),
        total=len(results),
        ok_count=ok_count,
        fail_count=fail_count,
        warn_count=warn_count,
        categories=categories,
        by_source=by_source,
        by_type=by_type
    )


@router.get("/akshare")
async def get_akshare_status():
    """获取AKShare接口状态"""
    tasks = [test_akshare_api(api) for api in AKSHARE_APIS]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    valid_results = [r for r in results if isinstance(r, ApiStatus)]

    # 按分类分组
    categories: Dict[str, List[dict]] = {}
    for r in valid_results:
        if r.category not in categories:
            categories[r.category] = []
        categories[r.category].append(r.dict())

    ok_count = len([r for r in valid_results if r.status == "OK"])

    return {
        "success": True,
        "timestamp": datetime.now().isoformat(),
        "total": len(valid_results),
        "ok_count": ok_count,
        "fail_count": len(valid_results) - ok_count,
        "categories": categories
    }


@router.get("/internal")
async def get_internal_status():
    """获取内部API状态"""
    tasks = [test_internal_api(api) for api in INTERNAL_APIS]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    valid_results = [r for r in results if isinstance(r, ApiStatus)]
    ok_count = len([r for r in valid_results if r.status == "OK"])

    return {
        "success": True,
        "timestamp": datetime.now().isoformat(),
        "total": len(valid_results),
        "ok_count": ok_count,
        "apis": [r.dict() for r in valid_results]
    }


@router.get("/ai")
async def get_ai_status():
    """获取AI服务状态"""
    tasks = [test_external_ai_api(api) for api in AI_SERVICES]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    valid_results = [r for r in results if isinstance(r, ApiStatus)]
    ok_count = len([r for r in valid_results if r.status == "OK"])

    return {
        "success": True,
        "timestamp": datetime.now().isoformat(),
        "total": len(valid_results),
        "ok_count": ok_count,
        "apis": [r.dict() for r in valid_results]
    }


@router.get("/ping/{api_name}")
async def ping_api(api_name: str):
    """
    Ping单个API

    支持的api_name格式:
    - akshare:stock_info_global_em
    - internal:/api/news-center/market
    - ai:gemini
    """
    if api_name.startswith("akshare:"):
        func_name = api_name.replace("akshare:", "")
        api_config = next((a for a in AKSHARE_APIS if a["func"] == func_name), None)
        if api_config:
            result = await test_akshare_api(api_config)
            return result.dict()
        return {"error": f"未找到AKShare接口: {func_name}"}

    elif api_name.startswith("internal:"):
        endpoint = api_name.replace("internal:", "")
        api_config = {"name": endpoint, "category": "内部API", "endpoint": endpoint}
        result = await test_internal_api(api_config)
        return result.dict()

    elif api_name.startswith("ai:"):
        ai_name = api_name.replace("ai:", "").lower()
        api_config = next((a for a in AI_SERVICES if ai_name in a["name"].lower()), None)
        if api_config:
            result = await test_external_ai_api(api_config)
            return result.dict()
        return {"error": f"未找到AI服务: {ai_name}"}

    return {"error": "无效的api_name格式，请使用 akshare:xxx, internal:xxx 或 ai:xxx"}


@router.get("/summary")
async def get_summary():
    """获取API监控摘要"""
    # 快速检查几个关键API
    key_apis = [
        {"name": "东方财富全球资讯", "category": "新闻数据", "func": "stock_info_global_em", "params": {}, "columns": []},
        {"name": "A股实时行情", "category": "行情数据", "func": "stock_zh_a_spot_em", "params": {}, "columns": []},
    ]

    akshare_tasks = [test_akshare_api(api) for api in key_apis]
    internal_tasks = [test_internal_api(api) for api in INTERNAL_APIS[:2]]
    ai_tasks = [test_external_ai_api(api) for api in AI_SERVICES]

    all_results = await asyncio.gather(
        *akshare_tasks, *internal_tasks, *ai_tasks,
        return_exceptions=True
    )

    valid_results = [r for r in all_results if isinstance(r, ApiStatus)]
    ok_count = len([r for r in valid_results if r.status == "OK"])

    return {
        "success": True,
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_checked": len(valid_results),
            "ok": ok_count,
            "fail": len(valid_results) - ok_count,
            "health_percentage": round(ok_count / len(valid_results) * 100, 1) if valid_results else 0
        },
        "quick_status": [r.dict() for r in valid_results]
    }


# ============================================================================
# 流式API - 完成一个返回一个
# ============================================================================

from fastapi.responses import StreamingResponse
import json as json_module

async def stream_api_status(
    include_akshare: bool = True,
    include_internal: bool = True,
    include_ai: bool = True,
    include_datasources: bool = True,
    include_tushare: bool = True,
    include_tdx: bool = True,
    include_sina: bool = True,
    include_juhe: bool = True,
    include_finnhub: bool = True,
    include_cninfo: bool = True,
    include_eastmoney: bool = True
):
    """流式返回API状态，完成一个返回一个"""

    # 单个API测试超时时间（秒）
    API_TEST_TIMEOUT = 15

    # AKShare慢速接口列表（需要更长超时时间）
    AKSHARE_SLOW_INTERFACES = {
        'stock_zh_a_spot_em',  # A股实时行情（数据量大）
        'stock_zh_a_spot',  # 新浪A股实时行情
        'stock_lhb_detail_em',  # 龙虎榜详情
        'stock_lhb_jgmmtj_em',  # 机构龙虎榜
        'stock_dzjy_mrmx',  # 大宗交易
        'stock_hsgt_fund_flow_summary_em',  # 沪深港通资金流向
        'stock_hsgt_hist_em',  # 沪深港通历史
        'stock_ggcg_em',  # 管理层信息
        'stock_fhps_em',  # 分红送股
        'stock_gpzy_pledge_ratio_em',  # 股权质押
        'stock_lhb_hyyyb_em',  # 游资统计
        'stock_zt_pool_em',  # 涨停池
        'stock_rank_cxg_ths',  # 涨幅榜
        'stock_notice_report',  # 公告
        'stock_yysj_em',  # 业绩预告
        'stock_yjyg_em',  # 业绩预告
        'stock_zygc_em',  # 主营构成
        'stock_restricted_release_queue_sina',  # 限售解禁
        'news_economic_baidu',  # 百度财经新闻
        'stock_news_em',  # 东财个股新闻
    }

    def get_akshare_timeout(func_name: str) -> int:
        """根据AKShare接口名称获取合适的超时时间"""
        if func_name in AKSHARE_SLOW_INTERFACES:
            return 30  # 慢速接口30秒
        return 15  # 普通接口15秒

    async def test_with_timeout(test_func, api_config, timeout=API_TEST_TIMEOUT):
        """带超时的测试包装器"""
        name = api_config.get("name", "Unknown")
        category = api_config.get("category", "未分类")
        source = api_config.get("source", "")
        data_type = api_config.get("data_type", "")
        endpoint = api_config.get("func", api_config.get("endpoint", ""))

        try:
            result = await asyncio.wait_for(test_func(api_config), timeout=timeout)
            return result
        except asyncio.TimeoutError:
            record_status(name, "TIMEOUT", timeout * 1000)
            return ApiStatus(
                name=name,
                category=category,
                status="TIMEOUT",
                latency=timeout * 1000,
                ping_time=0,
                message=f"测试超时 ({timeout}秒)",
                last_check=datetime.now().isoformat(),
                endpoint=endpoint,
                source=source,
                data_type=data_type,
                uptime=get_uptime(name),
                history=get_history_points(name)[-10:]
            )
        except Exception as e:
            record_status(name, "FAIL", 0)
            return ApiStatus(
                name=name,
                category=category,
                status="FAIL",
                latency=0,
                ping_time=0,
                message=str(e)[:80],
                last_check=datetime.now().isoformat(),
                endpoint=endpoint,
                source=source,
                data_type=data_type,
                uptime=get_uptime(name),
                history=get_history_points(name)[-10:]
            )

    # 先返回开始标记
    yield f"data: {json_module.dumps({'type': 'start', 'timestamp': datetime.now().isoformat()})}\n\n"

    # 测试数据源
    if include_datasources:
        for ds in DATA_SOURCES:
            result = await test_with_timeout(test_data_source, ds)
            yield f"data: {json_module.dumps({'type': 'result', 'data': result.dict()})}\n\n"

    # 测试TDX接口 (最高优先级) - TDX连接可能较慢，给更长超时
    if include_tdx:
        for api in TDX_APIS:
            result = await test_with_timeout(test_tdx_api, api, timeout=20)
            yield f"data: {json_module.dumps({'type': 'result', 'data': result.dict()})}\n\n"

    # 测试Tushare接口
    if include_tushare:
        for api in TUSHARE_APIS:
            result = await test_with_timeout(test_tushare_api, api)
            yield f"data: {json_module.dumps({'type': 'result', 'data': result.dict()})}\n\n"

    # 测试新浪接口
    if include_sina:
        for api in SINA_APIS:
            func_name = api.get("func", "")
            timeout = get_akshare_timeout(func_name)
            result = await test_with_timeout(test_akshare_api, api, timeout=timeout)
            yield f"data: {json_module.dumps({'type': 'result', 'data': result.dict()})}\n\n"

    # 测试聚合数据接口
    if include_juhe:
        for api in JUHE_APIS:
            result = await test_with_timeout(test_juhe_api, api)
            yield f"data: {json_module.dumps({'type': 'result', 'data': result.dict()})}\n\n"

    # 测试FinnHub接口 (美股)
    if include_finnhub:
        for api in FINNHUB_APIS:
            result = await test_with_timeout(test_finnhub_api, api)
            yield f"data: {json_module.dumps({'type': 'result', 'data': result.dict()})}\n\n"

    # 测试巨潮直接API
    if include_cninfo:
        for api in CNINFO_APIS:
            result = await test_with_timeout(test_cninfo_api, api)
            yield f"data: {json_module.dumps({'type': 'result', 'data': result.dict()})}\n\n"

    # 测试东方财富直接API
    if include_eastmoney:
        for api in EASTMONEY_APIS:
            result = await test_with_timeout(test_eastmoney_api, api)
            yield f"data: {json_module.dumps({'type': 'result', 'data': result.dict()})}\n\n"

    # 测试AKShare接口
    if include_akshare:
        for api in AKSHARE_APIS:
            func_name = api.get("func", "")
            timeout = get_akshare_timeout(func_name)
            result = await test_with_timeout(test_akshare_api, api, timeout=timeout)
            yield f"data: {json_module.dumps({'type': 'result', 'data': result.dict()})}\n\n"

    # 测试内部API
    if include_internal:
        for api in INTERNAL_APIS:
            result = await test_with_timeout(test_internal_api, api)
            yield f"data: {json_module.dumps({'type': 'result', 'data': result.dict()})}\n\n"

    # 测试AI服务
    if include_ai:
        for api in AI_SERVICES:
            result = await test_with_timeout(test_external_ai_api, api)
            yield f"data: {json_module.dumps({'type': 'result', 'data': result.dict()})}\n\n"

    # 返回结束标记
    yield f"data: {json_module.dumps({'type': 'end', 'timestamp': datetime.now().isoformat()})}\n\n"


async def test_juhe_api(api_config: Dict) -> ApiStatus:
    """测试聚合数据接口"""
    name = api_config["name"]
    url = api_config.get("url", "")
    source = api_config.get("source", "聚合")
    data_type = api_config.get("data_type", "")
    category = api_config.get("category", "聚合接口")
    env_key = api_config.get("env_key", "JUHE_API_KEY")

    api_key = os.getenv(env_key, "")
    if not api_key:
        record_status(name, "N/A", 0)
        return ApiStatus(
            name=name,
            category=category,
            status="N/A",
            latency=0,
            ping_time=0,
            message="未配置API密钥",
            last_check=datetime.now().isoformat(),
            endpoint=url,
            source=source,
            data_type=data_type,
            uptime=get_uptime(name),
            history=get_history_points(name)[-10:]
        )

    try:
        start = time.time()
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{url}?key={api_key}&gid=sh601519")
            latency = (time.time() - start) * 1000

            if response.status_code == 200:
                data = response.json()
                if data.get("error_code") == 0:
                    record_status(name, "OK", latency)
                    return ApiStatus(
                        name=name,
                        category=category,
                        status="OK",
                        latency=latency,
                        ping_time=latency * 0.3,
                        message="连接正常",
                        last_check=datetime.now().isoformat(),
                        endpoint=url,
                        source=source,
                        data_type=data_type,
                        uptime=get_uptime(name),
                        history=get_history_points(name)[-10:]
                    )
                else:
                    record_status(name, "WARN", latency)
                    return ApiStatus(
                        name=name,
                        category=category,
                        status="WARN",
                        latency=latency,
                        ping_time=latency * 0.3,
                        message=data.get("reason", "API返回错误")[:50],
                        last_check=datetime.now().isoformat(),
                        endpoint=url,
                        source=source,
                        data_type=data_type,
                        uptime=get_uptime(name),
                        history=get_history_points(name)[-10:]
                    )
            else:
                record_status(name, "FAIL", latency)
                return ApiStatus(
                    name=name,
                    category=category,
                    status="FAIL",
                    latency=latency,
                    ping_time=0,
                    message=f"HTTP {response.status_code}",
                    last_check=datetime.now().isoformat(),
                    endpoint=url,
                    source=source,
                    data_type=data_type,
                    uptime=get_uptime(name),
                    history=get_history_points(name)[-10:]
                )

    except Exception as e:
        record_status(name, "FAIL", 0)
        return ApiStatus(
            name=name,
            category=category,
            status="FAIL",
            latency=0,
            ping_time=0,
            message=str(e)[:80],
            last_check=datetime.now().isoformat(),
            endpoint=url,
            source=source,
            data_type=data_type,
            uptime=get_uptime(name),
            history=get_history_points(name)[-10:]
        )


async def test_tushare_api(api_config: Dict) -> ApiStatus:
    """测试Tushare接口"""
    name = api_config["name"]
    func_name = api_config["func"]
    params = api_config.get("params", {})
    source = api_config.get("source", "Tushare")
    data_type = api_config.get("data_type", "")
    category = api_config.get("category", "Tushare接口")

    # 检查Tushare Token
    api_key = os.getenv("TUSHARE_TOKEN", "")
    if not api_key:
        record_status(name, "N/A", 0)
        return ApiStatus(
            name=name,
            category=category,
            status="N/A",
            latency=0,
            ping_time=0,
            message="未配置Tushare Token",
            last_check=datetime.now().isoformat(),
            endpoint=func_name,
            source=source,
            data_type=data_type,
            uptime=get_uptime(name),
            history=get_history_points(name)[-10:]
        )

    try:
        import tushare as ts
        start = time.time()

        ts.set_token(api_key)
        pro = ts.pro_api()

        # 在线程池中执行
        loop = asyncio.get_event_loop()
        func = getattr(pro, func_name, None)
        if func is None:
            record_status(name, "N/A", 0)
            return ApiStatus(
                name=name,
                category=category,
                status="N/A",
                latency=0,
                ping_time=0,
                message=f"接口不存在: {func_name}",
                last_check=datetime.now().isoformat(),
                endpoint=func_name,
                source=source,
                data_type=data_type,
                uptime=get_uptime(name),
                history=get_history_points(name)[-10:]
            )

        df = await loop.run_in_executor(None, lambda: func(**params))
        latency = (time.time() - start) * 1000

        if df is None or (hasattr(df, 'empty') and df.empty):
            record_status(name, "WARN", latency)
            return ApiStatus(
                name=name,
                category=category,
                status="WARN",
                latency=latency,
                ping_time=latency * 0.3,
                message="返回数据为空",
                last_check=datetime.now().isoformat(),
                endpoint=func_name,
                source=source,
                data_type=data_type,
                uptime=get_uptime(name),
                history=get_history_points(name)[-10:]
            )

        count = len(df) if hasattr(df, '__len__') else 0
        record_status(name, "OK", latency)
        return ApiStatus(
            name=name,
            category=category,
            status="OK",
            latency=latency,
            ping_time=latency * 0.3,
            message=f"返回{count}条数据",
            last_check=datetime.now().isoformat(),
            endpoint=func_name,
            source=source,
            data_type=data_type,
            uptime=get_uptime(name),
            history=get_history_points(name)[-10:]
        )

    except Exception as e:
        record_status(name, "FAIL", 0)
        return ApiStatus(
            name=name,
            category=category,
            status="FAIL",
            latency=0,
            ping_time=0,
            message=str(e)[:80],
            last_check=datetime.now().isoformat(),
            endpoint=func_name,
            source=source,
            data_type=data_type,
            uptime=get_uptime(name),
            history=get_history_points(name)[-10:]
        )


async def test_tdx_api(api_config: Dict) -> ApiStatus:
    """
    测试TDX通达信接口 - 使用 TDXNativeProvider (pytdx直连远程服务器)
    """
    name = api_config["name"]
    func_name = api_config.get("func", "")
    params = api_config.get("params", {})
    source = api_config.get("source", "TDX")
    data_type = api_config.get("data_type", "")
    category = api_config.get("category", "TDX接口")

    try:
        from backend.dataflows.providers.tdx_native_provider import get_tdx_native_provider

        start = time.time()
        provider = get_tdx_native_provider()

        # 检查连接
        if not provider.is_available():
            record_status(name, "FAIL", 0)
            return ApiStatus(
                name=name,
                category=category,
                status="FAIL",
                latency=0,
                ping_time=0,
                message="无法连接TDX远程服务器",
                last_check=datetime.now().isoformat(),
                endpoint=func_name,
                source=source,
                data_type=data_type,
                uptime=get_uptime(name),
                history=get_history_points(name)[-10:]
            )

        # 获取方法
        func = getattr(provider, func_name, None)
        if func is None:
            record_status(name, "N/A", 0)
            return ApiStatus(
                name=name,
                category=category,
                status="N/A",
                latency=0,
                ping_time=0,
                message=f"接口不存在: {func_name}",
                last_check=datetime.now().isoformat(),
                endpoint=func_name,
                source=source,
                data_type=data_type,
                uptime=get_uptime(name),
                history=get_history_points(name)[-10:]
            )

        # 在线程池中执行
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, lambda: func(**params))
        latency = (time.time() - start) * 1000

        if result is None or (hasattr(result, '__len__') and len(result) == 0):
            record_status(name, "WARN", latency)
            return ApiStatus(
                name=name,
                category=category,
                status="WARN",
                latency=latency,
                ping_time=latency * 0.3,
                message="返回数据为空",
                last_check=datetime.now().isoformat(),
                endpoint=func_name,
                source=source,
                data_type=data_type,
                uptime=get_uptime(name),
                history=get_history_points(name)[-10:]
            )

        # 统计返回数据量
        if isinstance(result, dict):
            count = len(result)
        elif hasattr(result, '__len__'):
            count = len(result)
        else:
            count = 1

        record_status(name, "OK", latency)
        return ApiStatus(
            name=name,
            category=category,
            status="OK",
            latency=latency,
            ping_time=latency * 0.3,
            message=f"返回{count}条数据",
            last_check=datetime.now().isoformat(),
            endpoint=func_name,
            source=source,
            data_type=data_type,
            uptime=get_uptime(name),
            history=get_history_points(name)[-10:]
        )

    except ImportError:
        record_status(name, "N/A", 0)
        return ApiStatus(
            name=name,
            category=category,
            status="N/A",
            latency=0,
            ping_time=0,
            message="TDXNativeProvider未安装",
            last_check=datetime.now().isoformat(),
            endpoint=func_name,
            source=source,
            data_type=data_type,
            uptime=get_uptime(name),
            history=get_history_points(name)[-10:]
        )
    except Exception as e:
        record_status(name, "FAIL", 0)
        return ApiStatus(
            name=name,
            category=category,
            status="FAIL",
            latency=0,
            ping_time=0,
            message=str(e)[:80],
            last_check=datetime.now().isoformat(),
            endpoint=func_name,
            source=source,
            data_type=data_type,
            uptime=get_uptime(name),
            history=get_history_points(name)[-10:]
        )


async def test_data_source(ds_config: Dict) -> ApiStatus:
    """测试数据源连接"""
    name = ds_config["name"]
    source = ds_config.get("source", name)
    category = ds_config.get("category", "数据源")
    env_key = ds_config.get("env_key", "")
    test_func = ds_config.get("test_func", "")
    is_local = ds_config.get("local", False)

    try:
        start = time.time()

        # TDX数据源 - 使用 TDXNativeProvider (pytdx直连远程服务器)
        if is_local and "tdx" in name.lower():
            try:
                from backend.dataflows.providers.tdx_native_provider import get_tdx_native_provider

                loop = asyncio.get_event_loop()
                provider = get_tdx_native_provider()
                is_available = await loop.run_in_executor(None, provider.is_available)
                latency = (time.time() - start) * 1000

                if is_available:
                    record_status(name, "OK", latency)
                    return ApiStatus(
                        name=name,
                        category=category,
                        status="OK",
                        latency=latency,
                        ping_time=latency * 0.3,
                        message="TDX远程服务器连接正常",
                        last_check=datetime.now().isoformat(),
                        endpoint="pytdx",
                        source=source,
                        data_type="数据源",
                        uptime=get_uptime(name),
                        history=get_history_points(name)[-10:]
                    )
                else:
                    record_status(name, "FAIL", 0)
                    return ApiStatus(
                        name=name,
                        category=category,
                        status="FAIL",
                        latency=0,
                        ping_time=0,
                        message="无法连接TDX远程服务器",
                        last_check=datetime.now().isoformat(),
                        endpoint="pytdx",
                        source=source,
                        data_type="数据源",
                        uptime=get_uptime(name),
                        history=get_history_points(name)[-10:]
                    )
            except ImportError:
                record_status(name, "N/A", 0)
                return ApiStatus(
                    name=name,
                    category=category,
                    status="N/A",
                    latency=0,
                    ping_time=0,
                    message="pytdx未安装",
                    last_check=datetime.now().isoformat(),
                    endpoint="pytdx",
                    source=source,
                    data_type="数据源",
                    uptime=get_uptime(name),
                    history=get_history_points(name)[-10:]
                )
            except Exception as e:
                record_status(name, "FAIL", 0)
                return ApiStatus(
                    name=name,
                    category=category,
                    status="FAIL",
                    latency=0,
                    ping_time=0,
                    message=str(e)[:50],
                    last_check=datetime.now().isoformat(),
                    endpoint="pytdx",
                    source=source,
                    data_type="数据源",
                    uptime=get_uptime(name),
                    history=get_history_points(name)[-10:]
                )

        # 其他本地数据源
        if is_local:
            record_status(name, "N/A", 0)
            return ApiStatus(
                name=name,
                category=category,
                status="N/A",
                latency=0,
                ping_time=0,
                message="本地数据源，需要安装客户端",
                last_check=datetime.now().isoformat(),
                endpoint="local",
                source=source,
                data_type="数据源",
                uptime=get_uptime(name),
                history=get_history_points(name)[-10:]
            )

        # 需要API Key的数据源
        if env_key:
            api_key = os.getenv(env_key, "")
            if not api_key:
                record_status(name, "N/A", 0)
                return ApiStatus(
                    name=name,
                    category=category,
                    status="N/A",
                    latency=0,
                    ping_time=0,
                    message="未配置API密钥",
                    last_check=datetime.now().isoformat(),
                    endpoint="需要配置",
                    source=source,
                    data_type="数据源",
                    uptime=get_uptime(name),
                    history=get_history_points(name)[-10:]
                )

            # Tushare测试
            if "tushare" in name.lower():
                try:
                    import tushare as ts
                    ts.set_token(api_key)
                    pro = ts.pro_api()
                    df = pro.trade_cal(exchange='SSE', start_date='20240101', end_date='20240101')
                    latency = (time.time() - start) * 1000
                    if df is not None and len(df) > 0:
                        record_status(name, "OK", latency)
                        return ApiStatus(
                            name=name,
                            category=category,
                            status="OK",
                            latency=latency,
                            ping_time=latency * 0.3,
                            message="连接正常",
                            last_check=datetime.now().isoformat(),
                            endpoint="tushare.pro_api",
                            source=source,
                            data_type="数据源",
                            uptime=get_uptime(name),
                            history=get_history_points(name)[-10:]
                        )
                except Exception as e:
                    record_status(name, "FAIL", 0)
                    return ApiStatus(
                        name=name,
                        category=category,
                        status="FAIL",
                        latency=0,
                        ping_time=0,
                        message=str(e)[:50],
                        last_check=datetime.now().isoformat(),
                        endpoint="tushare.pro_api",
                        source=source,
                        data_type="数据源",
                        uptime=get_uptime(name),
                        history=get_history_points(name)[-10:]
                    )

            # 聚合数据测试
            if "juhe" in env_key.lower():
                try:
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        response = await client.get(f"http://web.juhe.cn/finance/stock/shall?key={api_key}&gid=sh601519")
                        latency = (time.time() - start) * 1000
                        if response.status_code == 200:
                            data = response.json()
                            if data.get("error_code") == 0:
                                record_status(name, "OK", latency)
                                return ApiStatus(
                                    name=name,
                                    category=category,
                                    status="OK",
                                    latency=latency,
                                    ping_time=latency * 0.3,
                                    message="连接正常",
                                    last_check=datetime.now().isoformat(),
                                    endpoint="web.juhe.cn",
                                    source=source,
                                    data_type="数据源",
                                    uptime=get_uptime(name),
                                    history=get_history_points(name)[-10:]
                                )
                            else:
                                record_status(name, "WARN", latency)
                                return ApiStatus(
                                    name=name,
                                    category=category,
                                    status="WARN",
                                    latency=latency,
                                    ping_time=latency * 0.3,
                                    message=data.get("reason", "API返回错误"),
                                    last_check=datetime.now().isoformat(),
                                    endpoint="web.juhe.cn",
                                    source=source,
                                    data_type="数据源",
                                    uptime=get_uptime(name),
                                    history=get_history_points(name)[-10:]
                                )
                except Exception as e:
                    record_status(name, "FAIL", 0)
                    return ApiStatus(
                        name=name,
                        category=category,
                        status="FAIL",
                        latency=0,
                        ping_time=0,
                        message=str(e)[:50],
                        last_check=datetime.now().isoformat(),
                        endpoint="web.juhe.cn",
                        source=source,
                        data_type="数据源",
                        uptime=get_uptime(name),
                        history=get_history_points(name)[-10:]
                    )

            # FinnHub测试
            if "finnhub" in env_key.lower():
                try:
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        response = await client.get(f"https://finnhub.io/api/v1/quote?symbol=AAPL&token={api_key}")
                        latency = (time.time() - start) * 1000
                        if response.status_code == 200:
                            record_status(name, "OK", latency)
                            return ApiStatus(
                                name=name,
                                category=category,
                                status="OK",
                                latency=latency,
                                ping_time=latency * 0.3,
                                message="连接正常",
                                last_check=datetime.now().isoformat(),
                                endpoint="finnhub.io",
                                source=source,
                                data_type="数据源",
                                uptime=get_uptime(name),
                                history=get_history_points(name)[-10:]
                            )
                except Exception as e:
                    record_status(name, "FAIL", 0)
                    return ApiStatus(
                        name=name,
                        category=category,
                        status="FAIL",
                        latency=0,
                        ping_time=0,
                        message=str(e)[:50],
                        last_check=datetime.now().isoformat(),
                        endpoint="finnhub.io",
                        source=source,
                        data_type="数据源",
                        uptime=get_uptime(name),
                        history=get_history_points(name)[-10:]
                    )

            # 巨潮资讯测试
            if "cninfo" in env_key.lower():
                try:
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        response = await client.get("http://www.cninfo.com.cn/new/index")
                        latency = (time.time() - start) * 1000
                        if response.status_code == 200:
                            record_status(name, "OK", latency)
                            return ApiStatus(
                                name=name,
                                category=category,
                                status="OK",
                                latency=latency,
                                ping_time=latency * 0.3,
                                message="网站可访问",
                                last_check=datetime.now().isoformat(),
                                endpoint="cninfo.com.cn",
                                source=source,
                                data_type="数据源",
                                uptime=get_uptime(name),
                                history=get_history_points(name)[-10:]
                            )
                except Exception as e:
                    record_status(name, "FAIL", 0)
                    return ApiStatus(
                        name=name,
                        category=category,
                        status="FAIL",
                        latency=0,
                        ping_time=0,
                        message=str(e)[:50],
                        last_check=datetime.now().isoformat(),
                        endpoint="cninfo.com.cn",
                        source=source,
                        data_type="数据源",
                        uptime=get_uptime(name),
                        history=get_history_points(name)[-10:]
                    )

        # 有测试函数的数据源 (AKShare, 新浪等)
        if test_func:
            func = getattr(ak, test_func, None)
            if func:
                loop = asyncio.get_event_loop()
                df = await loop.run_in_executor(None, func)
                latency = (time.time() - start) * 1000
                if df is not None and len(df) > 0:
                    record_status(name, "OK", latency)
                    return ApiStatus(
                        name=name,
                        category=category,
                        status="OK",
                        latency=latency,
                        ping_time=latency * 0.1,
                        message=f"返回{len(df)}条数据",
                        last_check=datetime.now().isoformat(),
                        endpoint=test_func,
                        source=source,
                        data_type="数据源",
                        uptime=get_uptime(name),
                        history=get_history_points(name)[-10:]
                    )

        # 默认返回N/A
        record_status(name, "N/A", 0)
        return ApiStatus(
            name=name,
            category=category,
            status="N/A",
            latency=0,
            ping_time=0,
            message="无法测试",
            last_check=datetime.now().isoformat(),
            endpoint="",
            source=source,
            data_type="数据源",
            uptime=get_uptime(name),
            history=get_history_points(name)[-10:]
        )

    except Exception as e:
        record_status(name, "FAIL", 0)
        return ApiStatus(
            name=name,
            category=category,
            status="FAIL",
            latency=0,
            ping_time=0,
            message=str(e)[:50],
            last_check=datetime.now().isoformat(),
            endpoint="",
            source=source,
            data_type="数据源",
            uptime=get_uptime(name),
            history=get_history_points(name)[-10:]
        )


async def test_finnhub_api(api_config: Dict) -> ApiStatus:
    """测试FinnHub接口"""
    name = api_config["name"]
    url = api_config.get("url", "")
    params = api_config.get("params", {})
    source = api_config.get("source", "FinnHub")
    data_type = api_config.get("data_type", "")
    category = api_config.get("category", "FinnHub接口")
    env_key = api_config.get("env_key", "FINNHUB_API_KEY")

    api_key = os.getenv(env_key, "")
    if not api_key:
        record_status(name, "N/A", 0)
        return ApiStatus(
            name=name,
            category=category,
            status="N/A",
            latency=0,
            ping_time=0,
            message="未配置API密钥",
            last_check=datetime.now().isoformat(),
            endpoint=url,
            source=source,
            data_type=data_type,
            uptime=get_uptime(name),
            history=get_history_points(name)[-10:]
        )

    try:
        start = time.time()
        async with httpx.AsyncClient(timeout=10.0) as client:
            params["token"] = api_key
            response = await client.get(url, params=params)
            latency = (time.time() - start) * 1000

            if response.status_code == 200:
                data = response.json()
                if data:
                    record_status(name, "OK", latency)
                    return ApiStatus(
                        name=name,
                        category=category,
                        status="OK",
                        latency=latency,
                        ping_time=latency * 0.3,
                        message="连接正常",
                        last_check=datetime.now().isoformat(),
                        endpoint=url,
                        source=source,
                        data_type=data_type,
                        uptime=get_uptime(name),
                        history=get_history_points(name)[-10:]
                    )
                else:
                    record_status(name, "WARN", latency)
                    return ApiStatus(
                        name=name,
                        category=category,
                        status="WARN",
                        latency=latency,
                        ping_time=latency * 0.3,
                        message="返回数据为空",
                        last_check=datetime.now().isoformat(),
                        endpoint=url,
                        source=source,
                        data_type=data_type,
                        uptime=get_uptime(name),
                        history=get_history_points(name)[-10:]
                    )
            else:
                record_status(name, "FAIL", latency)
                return ApiStatus(
                    name=name,
                    category=category,
                    status="FAIL",
                    latency=latency,
                    ping_time=0,
                    message=f"HTTP {response.status_code}",
                    last_check=datetime.now().isoformat(),
                    endpoint=url,
                    source=source,
                    data_type=data_type,
                    uptime=get_uptime(name),
                    history=get_history_points(name)[-10:]
                )

    except Exception as e:
        record_status(name, "FAIL", 0)
        return ApiStatus(
            name=name,
            category=category,
            status="FAIL",
            latency=0,
            ping_time=0,
            message=str(e)[:80],
            last_check=datetime.now().isoformat(),
            endpoint=url,
            source=source,
            data_type=data_type,
            uptime=get_uptime(name),
            history=get_history_points(name)[-10:]
        )


async def test_cninfo_api(api_config: Dict) -> ApiStatus:
    """测试巨潮资讯直接API（支持GET和POST）"""
    name = api_config["name"]
    url = api_config.get("url", "")
    method = api_config.get("method", "GET")
    params = api_config.get("params", {})
    data = api_config.get("data", {})
    source = api_config.get("source", "巨潮")
    data_type = api_config.get("data_type", "")
    category = api_config.get("category", "巨潮接口")

    try:
        start = time.time()
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Referer": "http://www.cninfo.com.cn/",
                "Origin": "http://www.cninfo.com.cn",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
            }

            if method.upper() == "POST":
                response = await client.post(url, headers=headers, data=data)
            else:
                response = await client.get(url, headers=headers, params=params)

            latency = (time.time() - start) * 1000

            if response.status_code == 200:
                record_status(name, "OK", latency)
                return ApiStatus(
                    name=name,
                    category=category,
                    status="OK",
                    latency=latency,
                    ping_time=latency * 0.3,
                    message="网站可访问",
                    last_check=datetime.now().isoformat(),
                    endpoint=url,
                    source=source,
                    data_type=data_type,
                    uptime=get_uptime(name),
                    history=get_history_points(name)[-10:]
                )
            else:
                record_status(name, "FAIL", latency)
                return ApiStatus(
                    name=name,
                    category=category,
                    status="FAIL",
                    latency=latency,
                    ping_time=0,
                    message=f"HTTP {response.status_code}",
                    last_check=datetime.now().isoformat(),
                    endpoint=url,
                    source=source,
                    data_type=data_type,
                    uptime=get_uptime(name),
                    history=get_history_points(name)[-10:]
                )

    except Exception as e:
        record_status(name, "FAIL", 0)
        return ApiStatus(
            name=name,
            category=category,
            status="FAIL",
            latency=0,
            ping_time=0,
            message=str(e)[:80],
            last_check=datetime.now().isoformat(),
            endpoint=url,
            source=source,
            data_type=data_type,
            uptime=get_uptime(name),
            history=get_history_points(name)[-10:]
        )


async def test_eastmoney_api(api_config: Dict) -> ApiStatus:
    """测试东方财富直接API（支持302重定向和JSONP响应）"""
    name = api_config["name"]
    url = api_config.get("url", "")
    params = api_config.get("params", {})
    source = api_config.get("source", "东方财富")
    data_type = api_config.get("data_type", "")
    category = api_config.get("category", "东财接口")

    try:
        start = time.time()
        # 启用follow_redirects处理302重定向
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Referer": "https://quote.eastmoney.com/",
                "Origin": "https://quote.eastmoney.com",
                "Connection": "keep-alive",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-site"
            }
            response = await client.get(url, params=params, headers=headers)
            latency = (time.time() - start) * 1000

            if response.status_code == 200:
                try:
                    # 尝试解析JSONP响应
                    text = response.text
                    if text.startswith("jQuery") or text.startswith("callback"):
                        # JSONP格式：jQuery123456({"data":...})
                        start_idx = text.find("(")
                        end_idx = text.rfind(")")
                        if start_idx != -1 and end_idx != -1:
                            json_str = text[start_idx + 1:end_idx]
                            data = json_module.loads(json_str)
                        else:
                            data = None
                    else:
                        data = response.json()

                    if data:
                        record_status(name, "OK", latency)
                        return ApiStatus(
                            name=name,
                            category=category,
                            status="OK",
                            latency=latency,
                            ping_time=latency * 0.3,
                            message="连接正常",
                            last_check=datetime.now().isoformat(),
                            endpoint=url,
                            source=source,
                            data_type=data_type,
                            uptime=get_uptime(name),
                            history=get_history_points(name)[-10:]
                        )
                except Exception as parse_err:
                    logger.debug(f"东财API {name} 解析响应失败: {parse_err}")

                record_status(name, "WARN", latency)
                return ApiStatus(
                    name=name,
                    category=category,
                    status="WARN",
                    latency=latency,
                    ping_time=latency * 0.3,
                    message="返回数据格式异常",
                    last_check=datetime.now().isoformat(),
                    endpoint=url,
                    source=source,
                    data_type=data_type,
                    uptime=get_uptime(name),
                    history=get_history_points(name)[-10:]
                )
            else:
                record_status(name, "FAIL", latency)
                return ApiStatus(
                    name=name,
                    category=category,
                    status="FAIL",
                    latency=latency,
                    ping_time=0,
                    message=f"HTTP {response.status_code}",
                    last_check=datetime.now().isoformat(),
                    endpoint=url,
                    source=source,
                    data_type=data_type,
                    uptime=get_uptime(name),
                    history=get_history_points(name)[-10:]
                )

    except Exception as e:
        record_status(name, "FAIL", 0)
        return ApiStatus(
            name=name,
            category=category,
            status="FAIL",
            latency=0,
            ping_time=0,
            message=str(e)[:80],
            last_check=datetime.now().isoformat(),
            endpoint=url,
            source=source,
            data_type=data_type,
            uptime=get_uptime(name),
            history=get_history_points(name)[-10:]
        )


@router.get("/stream")
async def stream_status(
    include_akshare: bool = Query(True),
    include_internal: bool = Query(True),
    include_ai: bool = Query(True),
    include_datasources: bool = Query(True),
    include_tushare: bool = Query(True),
    include_tdx: bool = Query(True),
    include_sina: bool = Query(True),
    include_juhe: bool = Query(True),
    include_finnhub: bool = Query(True),
    include_cninfo: bool = Query(True),
    include_eastmoney: bool = Query(True)
):
    """
    流式返回API状态 (Server-Sent Events)

    完成一个接口测试就返回一个结果，不等待全部完成
    """
    return StreamingResponse(
        stream_api_status(
            include_akshare, include_internal, include_ai, include_datasources,
            include_tushare, include_tdx, include_sina, include_juhe,
            include_finnhub, include_cninfo, include_eastmoney
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
