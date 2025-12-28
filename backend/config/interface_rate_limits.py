"""
接口频率限制配置
基于 Tushare 和 AKShare 文档设置合理的刷新间隔

Tushare 限制说明:
- 120积分: 50次/分钟, 8000次/天
- 2000积分: 200次/分钟, 100000次/天
- 5000积分: 500次/分钟, 无限制
- 10000积分: 1000次/分钟, 无限制

AKShare 限制说明:
- 大部分接口无严格限制
- 但大量抓取容易封IP
- 建议控制频率，避免短时间大量请求
"""

from enum import Enum
from typing import Dict, Any


class DataSource(Enum):
    """数据源枚举"""
    TUSHARE = "tushare"
    AKSHARE = "akshare"
    MIXED = "mixed"


class UpdateFrequency(Enum):
    """更新频率枚举"""
    REALTIME = 60          # 实时数据: 1分钟
    HIGH = 300             # 高频数据: 5分钟
    MEDIUM = 1800          # 中频数据: 30分钟
    LOW = 3600             # 低频数据: 1小时
    DAILY = 86400          # 日频数据: 24小时
    WEEKLY = 604800        # 周频数据: 7天


# 接口频率限制配置
INTERFACE_RATE_LIMITS: Dict[str, Dict[str, Any]] = {
    # ==================== Tushare 接口 ====================

    # 基础信息类 - 变化频率低，每天更新一次即可
    "company_info": {
        "source": DataSource.TUSHARE,
        "min_interval": UpdateFrequency.DAILY.value,
        "description": "上市公司基本信息",
        "update_time": "每日更新",
        "rate_limit": "200次/分钟(2000积分)",
    },
    "managers": {
        "source": DataSource.TUSHARE,
        "min_interval": UpdateFrequency.DAILY.value,
        "description": "上市公司管理层",
        "update_time": "不定期更新",
        "rate_limit": "200次/分钟(2000积分)",
    },
    "manager_rewards": {
        "source": DataSource.TUSHARE,
        "min_interval": UpdateFrequency.DAILY.value,
        "description": "管理层薪酬和持股",
        "update_time": "年报更新",
        "rate_limit": "200次/分钟(2000积分)",
    },
    "main_business": {
        "source": DataSource.TUSHARE,
        "min_interval": UpdateFrequency.DAILY.value,
        "description": "主营业务构成",
        "update_time": "季报更新",
        "rate_limit": "200次/分钟(2000积分)",
    },

    # 行情数据类 - 交易时段高频更新
    "realtime": {
        "source": DataSource.TUSHARE,
        "min_interval": UpdateFrequency.REALTIME.value,
        "description": "实时盘口TICK快照",
        "update_time": "交易时段实时",
        "rate_limit": "50次/分钟(实时权限)",
        "trading_hours_only": True,
    },
    "realtime_tick": {
        "source": DataSource.TUSHARE,
        "min_interval": UpdateFrequency.REALTIME.value,
        "description": "实时成交数据",
        "update_time": "交易时段实时",
        "rate_limit": "50次/分钟(实时权限)",
        "trading_hours_only": True,
    },
    "realtime_list": {
        "source": DataSource.TUSHARE,
        "min_interval": UpdateFrequency.HIGH.value,
        "description": "实时涨跌幅排名",
        "update_time": "交易时段实时",
        "rate_limit": "200次/分钟(2000积分)",
        "trading_hours_only": True,
    },
    "limit_list": {
        "source": DataSource.TUSHARE,
        "min_interval": UpdateFrequency.MEDIUM.value,
        "description": "涨跌停列表",
        "update_time": "交易日9点更新",
        "rate_limit": "200次/分钟(2000积分)",
    },
    "dragon_tiger": {
        "source": DataSource.TUSHARE,
        "min_interval": UpdateFrequency.DAILY.value,
        "description": "龙虎榜每日明细",
        "update_time": "每日晚8点更新",
        "rate_limit": "200次/分钟(2000积分)",
    },
    "top_inst": {
        "source": DataSource.TUSHARE,
        "min_interval": UpdateFrequency.DAILY.value,
        "description": "龙虎榜机构明细",
        "update_time": "每日晚8点更新",
        "rate_limit": "200次/分钟(2000积分)",
    },

    # 财务数据类 - 季报/年报更新，低频
    "income": {
        "source": DataSource.TUSHARE,
        "min_interval": UpdateFrequency.DAILY.value,
        "description": "利润表",
        "update_time": "随财报实时更新",
        "rate_limit": "200次/分钟(2000积分)",
    },
    "balancesheet": {
        "source": DataSource.TUSHARE,
        "min_interval": UpdateFrequency.DAILY.value,
        "description": "资产负债表",
        "update_time": "随财报实时更新",
        "rate_limit": "200次/分钟(2000积分)",
    },
    "cashflow": {
        "source": DataSource.TUSHARE,
        "min_interval": UpdateFrequency.DAILY.value,
        "description": "现金流量表",
        "update_time": "随财报实时更新",
        "rate_limit": "200次/分钟(2000积分)",
    },
    "forecast": {
        "source": DataSource.TUSHARE,
        "min_interval": UpdateFrequency.DAILY.value,
        "description": "业绩预告",
        "update_time": "随财报实时更新",
        "rate_limit": "200次/分钟(2000积分)",
    },
    "express": {
        "source": DataSource.TUSHARE,
        "min_interval": UpdateFrequency.DAILY.value,
        "description": "业绩快报",
        "update_time": "随财报实时更新",
        "rate_limit": "200次/分钟(2000积分)",
    },
    "dividend": {
        "source": DataSource.TUSHARE,
        "min_interval": UpdateFrequency.DAILY.value,
        "description": "分红送股数据",
        "update_time": "随财报实时更新",
        "rate_limit": "200次/分钟(2000积分)",
    },
    "audit": {
        "source": DataSource.TUSHARE,
        "min_interval": UpdateFrequency.DAILY.value,
        "description": "财务审计意见",
        "update_time": "随财报实时更新",
        "rate_limit": "200次/分钟(2000积分)",
    },

    # 资金流向类 - 日频更新
    "margin": {
        "source": DataSource.TUSHARE,
        "min_interval": UpdateFrequency.DAILY.value,
        "description": "融资融券交易汇总",
        "update_time": "每日9点更新",
        "rate_limit": "200次/分钟(2000积分)",
    },
    "margin_detail": {
        "source": DataSource.TUSHARE,
        "min_interval": UpdateFrequency.DAILY.value,
        "description": "融资融券明细",
        "update_time": "每日9点更新",
        "rate_limit": "200次/分钟(2000积分)",
    },
    "moneyflow": {
        "source": DataSource.TUSHARE,
        "min_interval": UpdateFrequency.DAILY.value,
        "description": "个股资金流向",
        "update_time": "交易日19点更新",
        "rate_limit": "200次/分钟(2000积分)",
    },
    "hk_hold": {
        "source": DataSource.TUSHARE,
        "min_interval": UpdateFrequency.DAILY.value,
        "description": "沪深股通持股明细",
        "update_time": "下个交易日8点更新",
        "rate_limit": "200次/分钟(2000积分)",
    },
    "stk_holdertrade": {
        "source": DataSource.TUSHARE,
        "min_interval": UpdateFrequency.DAILY.value,
        "description": "股东增减持",
        "update_time": "交易日19点更新",
        "rate_limit": "200次/分钟(2000积分)",
    },

    # 风险监控类 - 日频更新
    "pledge_stat": {
        "source": DataSource.TUSHARE,
        "min_interval": UpdateFrequency.DAILY.value,
        "description": "股权质押统计",
        "update_time": "每日晚9点更新",
        "rate_limit": "200次/分钟(2000积分)",
    },
    "pledge_detail": {
        "source": DataSource.TUSHARE,
        "min_interval": UpdateFrequency.DAILY.value,
        "description": "股权质押明细",
        "update_time": "每日晚9点更新",
        "rate_limit": "200次/分钟(2000积分)",
    },
    "share_float": {
        "source": DataSource.TUSHARE,
        "min_interval": UpdateFrequency.WEEKLY.value,
        "description": "限售股解禁",
        "update_time": "定期更新",
        "rate_limit": "200次/分钟(3000积分)",
    },
    "block_trade": {
        "source": DataSource.TUSHARE,
        "min_interval": UpdateFrequency.DAILY.value,
        "description": "大宗交易",
        "update_time": "每日晚9点更新",
        "rate_limit": "200次/分钟(2000积分)",
    },

    # ==================== AKShare 接口 ====================

    # 新闻舆情类 - 中频更新，避免封IP
    "news_sina": {
        "source": DataSource.AKSHARE,
        "min_interval": UpdateFrequency.MEDIUM.value,
        "description": "新浪财经新闻",
        "update_time": "实时",
        "rate_limit": "无严格限制，建议30分钟/次",
        "warning": "大量抓取容易封IP",
    },
    "news_em": {
        "source": DataSource.AKSHARE,
        "min_interval": UpdateFrequency.MEDIUM.value,
        "description": "东方财富新闻",
        "update_time": "实时",
        "rate_limit": "无严格限制，建议30分钟/次",
        "warning": "大量抓取容易封IP",
    },
    "stock_news_em": {
        "source": DataSource.AKSHARE,
        "min_interval": UpdateFrequency.MEDIUM.value,
        "description": "个股新闻(东财)",
        "update_time": "实时，最多返回100条",
        "rate_limit": "无严格限制，建议30分钟/次",
        "warning": "内部约802次子请求，大量抓取容易封IP",
    },

    # AKShare 行情数据
    "stock_zh_a_spot_em": {
        "source": DataSource.AKSHARE,
        "min_interval": UpdateFrequency.HIGH.value,
        "description": "A股实时行情(东财)",
        "update_time": "交易时段实时",
        "rate_limit": "无严格限制，建议5分钟/次",
        "trading_hours_only": True,
    },
    "stock_individual_info_em": {
        "source": DataSource.AKSHARE,
        "min_interval": UpdateFrequency.DAILY.value,
        "description": "个股信息(东财)",
        "update_time": "每日更新",
        "rate_limit": "无严格限制",
    },

    # AKShare 龙虎榜
    "dragon_tiger_ak": {
        "source": DataSource.AKSHARE,
        "min_interval": UpdateFrequency.DAILY.value,
        "description": "龙虎榜(AKShare)",
        "update_time": "每日晚间更新",
        "rate_limit": "无严格限制",
    },

    # AKShare 财务风险
    "financial_risk": {
        "source": DataSource.AKSHARE,
        "min_interval": UpdateFrequency.DAILY.value,
        "description": "财务风险预警",
        "update_time": "不定期更新",
        "rate_limit": "无严格限制",
    },

    # 科创板数据 - 特别注意频率
    "stock_kc_a_spot_em": {
        "source": DataSource.AKSHARE,
        "min_interval": UpdateFrequency.MEDIUM.value,
        "description": "科创板实时行情",
        "update_time": "交易时段实时",
        "rate_limit": "请控制频率，大量抓取容易封IP",
        "warning": "大量抓取容易封IP",
        "trading_hours_only": True,
    },
    "stock_kc_a_hist": {
        "source": DataSource.AKSHARE,
        "min_interval": UpdateFrequency.DAILY.value,
        "description": "科创板历史行情",
        "update_time": "每日更新",
        "rate_limit": "请控制频率，大量抓取容易封IP",
        "warning": "大量抓取容易封IP",
    },
}


# 数据类型到接口的映射
DATA_TYPE_INTERFACES = {
    "comprehensive": [
        "company_info", "realtime", "income", "balancesheet", "cashflow",
        "margin", "moneyflow", "pledge_stat", "news_sina"
    ],
    "basic_info": ["company_info", "managers", "main_business"],
    "market_data": ["realtime", "realtime_list", "limit_list", "dragon_tiger"],
    "financial": ["income", "balancesheet", "cashflow", "forecast", "dividend"],
    "capital_flow": ["margin", "moneyflow", "hk_hold", "stk_holdertrade"],
    "risk": ["pledge_stat", "pledge_detail", "share_float", "block_trade"],
    "news": ["news_sina", "news_em", "stock_news_em"],
}


def get_interface_config(interface_id: str) -> Dict[str, Any]:
    """获取接口配置"""
    return INTERFACE_RATE_LIMITS.get(interface_id, {
        "source": DataSource.MIXED,
        "min_interval": UpdateFrequency.MEDIUM.value,
        "description": "未知接口",
        "rate_limit": "未知",
    })


def get_min_interval(interface_id: str) -> int:
    """获取接口最小刷新间隔(秒)"""
    config = get_interface_config(interface_id)
    return config.get("min_interval", UpdateFrequency.MEDIUM.value)


def is_trading_hours_only(interface_id: str) -> bool:
    """判断接口是否仅在交易时段更新"""
    config = get_interface_config(interface_id)
    return config.get("trading_hours_only", False)


def get_rate_limit_info() -> Dict[str, Any]:
    """获取所有接口的频率限制信息（用于前端展示）"""
    result = {
        "tushare": {
            "name": "Tushare Pro",
            "description": "专业金融数据接口",
            "tier_limits": {
                "120积分": "50次/分钟, 8000次/天",
                "2000积分": "200次/分钟, 100000次/天",
                "5000积分": "500次/分钟, 无限制",
                "10000积分": "1000次/分钟, 无限制",
            },
            "interfaces": {}
        },
        "akshare": {
            "name": "AKShare",
            "description": "开源金融数据接口",
            "tier_limits": {
                "默认": "无严格限制，但大量抓取容易封IP",
            },
            "interfaces": {}
        }
    }

    for interface_id, config in INTERFACE_RATE_LIMITS.items():
        source = config["source"].value
        if source in result:
            result[source]["interfaces"][interface_id] = {
                "description": config.get("description", ""),
                "update_time": config.get("update_time", ""),
                "rate_limit": config.get("rate_limit", ""),
                "min_interval": config.get("min_interval", 1800),
                "warning": config.get("warning", None),
            }

    return result
