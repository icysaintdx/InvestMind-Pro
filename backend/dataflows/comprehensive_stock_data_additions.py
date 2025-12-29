"""
综合股票数据服务的补充模块
包含 CATEGORY_TASKS、get_all_categories、get_category_data 等函数
以及 ComprehensiveStockDataService 的扩展方法
"""

from datetime import datetime
from typing import Dict, List

from backend.utils.logging_config import get_logger

logger = get_logger("dataflows.comprehensive_additions")


# ==================== 数据分类任务定义 ====================
CATEGORY_TASKS = {
    'realtime': {
        'name': '实时行情',
        'description': '实时股价、涨跌幅、成交量等',
        'interfaces': ['realtime', 'realtime_tick', 'realtime_list'],
        'priority': 1
    },
    'financial': {
        'name': '财务数据',
        'description': '利润表、资产负债表、现金流量表',
        'interfaces': ['financial', 'audit', 'forecast'],
        'priority': 2
    },
    'risk': {
        'name': '风险数据',
        'description': 'ST状态、停复牌、股权质押等',
        'interfaces': ['st_status', 'suspend', 'pledge', 'pledge_detail', 'restricted'],
        'priority': 3
    },
    'trading': {
        'name': '交易数据',
        'description': '龙虎榜、大宗交易、涨跌停等',
        'interfaces': ['dragon_tiger', 'top_inst', 'block_trade', 'limit_list', 'limit_list_ths'],
        'priority': 4
    },
    'holder': {
        'name': '股东数据',
        'description': '股东增减持、分红送股等',
        'interfaces': ['holder_trade', 'dividend'],
        'priority': 5
    },
    'margin': {
        'name': '融资融券',
        'description': '融资融券数据',
        'interfaces': ['margin', 'margin_detail'],
        'priority': 6
    },
    'northbound': {
        'name': '北向资金',
        'description': '沪深港通持股、资金流向',
        'interfaces': ['hsgt_holding', 'ggt_top10', 'hk_hold', 'moneyflow_hsgt'],
        'priority': 7
    },
    'company': {
        'name': '公司信息',
        'description': '公司基本信息、管理层、主营业务',
        'interfaces': ['company_info', 'managers', 'manager_rewards', 'main_business'],
        'priority': 8
    },
    'news': {
        'name': '新闻资讯',
        'description': '个股新闻、公告、市场快讯',
        'interfaces': ['news', 'news_sina', 'news_em', 'announcements', 'market_news', 'industry_policy'],
        'priority': 9
    }
}


def get_all_categories() -> Dict:
    """获取所有数据分类"""
    return {
        'categories': list(CATEGORY_TASKS.keys()),
        'details': CATEGORY_TASKS,
        'total': len(CATEGORY_TASKS)
    }


def get_category_data(ts_code: str, category: str) -> Dict:
    """
    获取指定分类的数据
    
    Args:
        ts_code: 股票代码
        category: 分类名称
        
    Returns:
        该分类下所有接口的数据
    """
    from backend.dataflows.comprehensive_stock_data import get_comprehensive_service
    
    if category not in CATEGORY_TASKS:
        return {
            'status': 'error',
            'message': f'未知分类: {category}',
            'available_categories': list(CATEGORY_TASKS.keys())
        }
    
    service = get_comprehensive_service()
    category_info = CATEGORY_TASKS[category]
    interfaces = category_info['interfaces']
    
    result = {
        'ts_code': ts_code,
        'category': category,
        'category_name': category_info['name'],
        'description': category_info['description'],
        'timestamp': datetime.now().isoformat(),
        'data': {}
    }
    
    # 获取每个接口的数据
    for interface in interfaces:
        method_name = f'_get_{interface}'
        if hasattr(service, method_name):
            try:
                method = getattr(service, method_name)
                # 某些方法不需要ts_code参数
                if interface in ['realtime_list', 'moneyflow_hsgt', 'market_news', 'industry_policy']:
                    result['data'][interface] = method()
                else:
                    result['data'][interface] = method(ts_code)
            except Exception as e:
                result['data'][interface] = {
                    'status': 'error',
                    'message': str(e)
                }
        else:
            result['data'][interface] = {
                'status': 'not_implemented',
                'message': f'接口 {interface} 未实现'
            }
    
    # 统计成功率
    success_count = sum(1 for v in result['data'].values() 
                       if isinstance(v, dict) and v.get('status') == 'success')
    result['summary'] = {
        'total_interfaces': len(interfaces),
        'success_count': success_count,
        'success_rate': f'{success_count}/{len(interfaces)}'
    }
    
    return result


def generate_interface_status(data: Dict) -> Dict:
    """
    生成接口状态报告（按分类组织，匹配前端期望格式）

    Args:
        data: 完整的股票数据字典

    Returns:
        按分类组织的接口状态字典，格式：
        {
            'market': {
                'icon': '📈',
                'name': '行情数据',
                'success': 2,
                'failed': 0,
                'no_data': 1,
                'interfaces': {
                    'realtime': {'status': 'success', 'status_label': '成功', 'message': '...'},
                    ...
                }
            },
            ...
        }
    """
    # 定义接口分类
    categories = {
        'market': {
            'icon': '📈',
            'name': '行情数据',
            'interfaces': ['realtime', 'realtime_tick', 'realtime_list', 'suspend', 'st_status']
        },
        'financial': {
            'icon': '💰',
            'name': '财务数据',
            'interfaces': ['financial', 'audit', 'forecast', 'dividend']
        },
        'risk': {
            'icon': '⚠️',
            'name': '风险数据',
            'interfaces': ['restricted', 'pledge', 'pledge_detail', 'holder_trade']
        },
        'trading': {
            'icon': '📊',
            'name': '交易数据',
            'interfaces': ['dragon_tiger', 'top_inst', 'block_trade', 'limit_list', 'limit_list_ths', 'margin', 'margin_detail']
        },
        'company': {
            'icon': '🏢',
            'name': '公司信息',
            'interfaces': ['company_info', 'managers', 'manager_rewards', 'main_business']
        },
        'capital': {
            'icon': '🌐',
            'name': '资金流向',
            'interfaces': ['hsgt_holding', 'ggt_top10', 'hk_hold', 'moneyflow_hsgt']
        },
        'news': {
            'icon': '📰',
            'name': '新闻资讯',
            'interfaces': ['announcements', 'news_sina', 'news_em', 'market_news', 'industry_policy', 'news']
        }
    }

    # 接口名称映射
    interface_names = {
        'realtime': '实时行情',
        'realtime_tick': '实时成交',
        'realtime_list': '行情列表',
        'suspend': '停复牌',
        'st_status': 'ST状态',
        'financial': '财务数据',
        'audit': '审计意见',
        'forecast': '业绩预告',
        'dividend': '分红送股',
        'restricted': '限售解禁',
        'pledge': '股权质押',
        'pledge_detail': '质押明细',
        'holder_trade': '股东增减持',
        'dragon_tiger': '龙虎榜',
        'top_inst': '机构明细',
        'block_trade': '大宗交易',
        'limit_list': '涨跌停',
        'limit_list_ths': '同花顺涨跌停',
        'margin': '融资融券',
        'margin_detail': '融资融券明细',
        'company_info': '公司信息',
        'managers': '管理层',
        'manager_rewards': '管理层薪酬',
        'main_business': '主营业务',
        'hsgt_holding': '沪深港通持股',
        'ggt_top10': '港股通十大',
        'hk_hold': '港资持股',
        'moneyflow_hsgt': '北向资金',
        'announcements': '公告',
        'news_sina': '新浪新闻',
        'news_em': '东方财富新闻',
        'market_news': '市场快讯',
        'industry_policy': '行业政策',
        'news': '综合新闻'
    }

    result = {}

    for cat_key, cat_info in categories.items():
        cat_result = {
            'icon': cat_info['icon'],
            'name': cat_info['name'],
            'success': 0,
            'failed': 0,
            'no_data': 0,
            'deferred': 0,
            'total': len(cat_info['interfaces']),
            'interfaces': {}
        }

        for interface in cat_info['interfaces']:
            interface_data = data.get(interface, {})

            if isinstance(interface_data, dict):
                status = interface_data.get('status', 'unknown')
                if status == 'success':
                    cat_result['success'] += 1
                    cat_result['interfaces'][interface] = {
                        'status': 'success',
                        'status_label': '✅ 成功',
                        'message': interface_data.get('message', '数据获取成功'),
                        'count': len(interface_data.get('data', [])) if isinstance(interface_data.get('data'), list) else 0
                    }
                elif status == 'deferred':
                    cat_result['deferred'] += 1
                    cat_result['interfaces'][interface] = {
                        'status': 'deferred',
                        'status_label': '⏳ 按需加载',
                        'message': '按需加载',
                        'count': 0
                    }
                elif status == 'no_data':
                    cat_result['no_data'] += 1
                    cat_result['interfaces'][interface] = {
                        'status': 'no_data',
                        'status_label': '📭 无数据',
                        'message': interface_data.get('message', '无数据'),
                        'count': 0
                    }
                elif status in ['normal', 'has_suspend', 'st_stock']:
                    cat_result['success'] += 1
                    cat_result['interfaces'][interface] = {
                        'status': 'success',
                        'status_label': '✅ 正常',
                        'message': interface_data.get('message', '状态正常'),
                        'count': 0
                    }
                else:
                    cat_result['failed'] += 1
                    cat_result['interfaces'][interface] = {
                        'status': 'failed',
                        'status_label': '❌ 失败',
                        'message': interface_data.get('message', str(interface_data.get('error', '获取失败'))),
                        'count': 0
                    }
            elif isinstance(interface_data, list):
                if interface_data:
                    cat_result['success'] += 1
                    cat_result['interfaces'][interface] = {
                        'status': 'success',
                        'status_label': '✅ 成功',
                        'message': f'获取到 {len(interface_data)} 条数据',
                        'count': len(interface_data)
                    }
                else:
                    cat_result['no_data'] += 1
                    cat_result['interfaces'][interface] = {
                        'status': 'no_data',
                        'status_label': '📭 无数据',
                        'message': '无数据',
                        'count': 0
                    }
            else:
                cat_result['failed'] += 1
                cat_result['interfaces'][interface] = {
                    'status': 'unknown',
                    'status_label': '❓ 未知',
                    'message': '未知状态',
                    'count': 0
                }

        result[cat_key] = cat_result

    return result


def generate_alerts(data: Dict) -> List[Dict]:
    """
    生成风险预警信息
    
    Args:
        data: 完整的股票数据字典
        
    Returns:
        预警信息列表
    """
    alerts = []
    
    # 1. ST状态预警
    st_status = data.get('st_status', {})
    if st_status.get('is_st') or st_status.get('status') == 'st_stock':
        alerts.append({
            'level': 'high',
            'type': 'st_warning',
            'icon': '⚠️',
            'title': 'ST风险警示',
            'message': st_status.get('message', '该股票为ST股票，存在退市风险'),
            'suggestion': '建议谨慎投资，关注公司基本面改善情况'
        })
    
    # 2. 停牌预警
    suspend = data.get('suspend', {})
    if suspend.get('status') == 'has_suspend':
        alerts.append({
            'level': 'medium',
            'type': 'suspend_warning',
            'icon': '🔒',
            'title': '停牌提醒',
            'message': suspend.get('message', '该股票近期有停牌记录'),
            'suggestion': '关注停牌原因及复牌时间'
        })
    
    # 3. 高质押比例预警
    pledge = data.get('pledge', {})
    pledge_ratio = pledge.get('pledge_ratio', 0)
    if pledge_ratio > 50:
        alerts.append({
            'level': 'high',
            'type': 'pledge_warning',
            'icon': '📊',
            'title': '高质押风险',
            'message': f'股权质押比例达 {pledge_ratio}%，存在平仓风险',
            'suggestion': '关注大股东资金状况，警惕强制平仓风险'
        })
    elif pledge_ratio > 30:
        alerts.append({
            'level': 'medium',
            'type': 'pledge_warning',
            'icon': '📊',
            'title': '质押比例较高',
            'message': f'股权质押比例为 {pledge_ratio}%',
            'suggestion': '持续关注质押情况变化'
        })
    
    # 4. 业绩预警
    forecast = data.get('forecast', {})
    if forecast.get('status') == 'success':
        forecast_data = forecast.get('forecast', [])
        if forecast_data:
            latest = forecast_data[0]
            forecast_type = latest.get('type', '')
            if '亏损' in forecast_type or '下降' in forecast_type:
                alerts.append({
                    'level': 'medium',
                    'type': 'performance_warning',
                    'icon': '📉',
                    'title': '业绩预警',
                    'message': f'业绩预告类型: {forecast_type}',
                    'suggestion': '关注公司经营状况，评估业绩下滑原因'
                })
    
    # 5. 审计意见预警
    audit = data.get('audit', {})
    if audit.get('status') == 'success':
        opinion = audit.get('opinion', '')
        if opinion and ('保留' in opinion or '否定' in opinion or '无法表示' in opinion):
            alerts.append({
                'level': 'high',
                'type': 'audit_warning',
                'icon': '📋',
                'title': '审计意见异常',
                'message': f'审计意见: {opinion}',
                'suggestion': '非标准审计意见可能暗示财务问题，建议深入研究'
            })
    
    # 6. 股东减持预警
    holder_trade = data.get('holder_trade', {})
    if holder_trade.get('status') == 'success':
        records = holder_trade.get('records', [])
        # 检查是否有大额减持
        for record in records[:5]:
            volume = record.get('volume', 0)
            if volume < 0 and abs(volume) > 1000000:  # 减持超过100万股
                alerts.append({
                    'level': 'medium',
                    'type': 'holder_reduce_warning',
                    'icon': '👤',
                    'title': '股东减持',
                    'message': f'{record.get("holder", "股东")} 减持 {abs(volume)/10000:.2f} 万股',
                    'suggestion': '关注减持原因，评估对股价的影响'
                })
                break
    
    # 7. 涨跌幅预警
    realtime = data.get('realtime', {})
    if realtime.get('status') == 'success':
        pct_change = realtime.get('data', {}).get('pct_change', 0)
        if pct_change >= 9.9:
            alerts.append({
                'level': 'info',
                'type': 'limit_up',
                'icon': '🔥',
                'title': '涨停提醒',
                'message': f'当前涨幅 {pct_change}%，接近或已涨停',
                'suggestion': '注意追高风险，关注成交量变化'
            })
        elif pct_change <= -9.9:
            alerts.append({
                'level': 'high',
                'type': 'limit_down',
                'icon': '💔',
                'title': '跌停提醒',
                'message': f'当前跌幅 {pct_change}%，接近或已跌停',
                'suggestion': '关注下跌原因，评估是否需要止损'
            })
    
    # 按风险等级排序
    level_order = {'high': 0, 'medium': 1, 'low': 2, 'info': 3}
    alerts.sort(key=lambda x: level_order.get(x.get('level', 'info'), 99))
    
    return alerts


# 为了兼容性，也导出这些函数的别名
_generate_interface_status = generate_interface_status
_generate_alerts = generate_alerts