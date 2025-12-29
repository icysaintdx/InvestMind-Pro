#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tushare Token 验证脚本
检测 Tushare Token 的有效性和积分情况

功能：
1. 验证 Token 是否有效
2. 获取账户积分信息
3. 检测各接口的权限
4. 如果 Tushare 不可用，自动提示使用 AKShare 替代

使用方法：
    python backend/scripts/check_tushare_status.py
"""

import os
import sys
import io
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

# 设置 stdout 编码为 utf-8，解决 Windows 控制台编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# 尝试加载环境变量
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(project_root, '.env'))
except ImportError:
    pass


def check_tushare_availability() -> Tuple[bool, str]:
    """检查 Tushare 库是否可用"""
    try:
        import tushare as ts
        return True, f"Tushare 版本: {ts.__version__}"
    except ImportError:
        return False, "Tushare 库未安装，请运行: pip install tushare"


def get_tushare_token() -> Optional[str]:
    """获取 Tushare Token"""
    # 优先从环境变量获取
    token = os.getenv('TUSHARE_TOKEN', '')

    if token and not token.startswith('your_'):
        return token

    return None


def validate_token(token: str) -> Tuple[bool, str, Optional[Dict]]:
    """
    验证 Token 有效性并获取账户信息

    Returns:
        (is_valid, message, account_info)
    """
    import tushare as ts

    try:
        ts.set_token(token)
        api = ts.pro_api()

        # 测试基础接口
        test_data = api.stock_basic(list_status='L', limit=1)

        if test_data is None or test_data.empty:
            return False, "Token 无效或已过期", None

        # 获取账户信息（积分等）
        # 注意：Tushare 没有直接的积分查询接口，需要通过测试各接口来判断
        account_info = {
            'token_valid': True,
            'basic_access': True,
            'token_preview': f"{token[:8]}...{token[-4:]}" if len(token) > 12 else "***"
        }

        return True, "Token 验证成功", account_info

    except Exception as e:
        error_msg = str(e)
        if "积分" in error_msg or "point" in error_msg.lower():
            return False, f"积分不足: {error_msg}", None
        elif "token" in error_msg.lower() or "认证" in error_msg:
            return False, f"Token 无效: {error_msg}", None
        else:
            return False, f"验证失败: {error_msg}", None


def check_api_permissions(api) -> Dict[str, Dict]:
    """
    检测各接口的权限

    Returns:
        {接口名: {'available': bool, 'message': str, 'points_required': int}}
    """
    from datetime import datetime, timedelta

    # 定义要检测的接口及其所需积分
    interfaces = {
        'stock_basic': {'points': 0, 'desc': '股票列表'},
        'daily': {'points': 0, 'desc': '日线行情'},
        'daily_basic': {'points': 120, 'desc': '每日指标'},
        'income': {'points': 500, 'desc': '利润表'},
        'balancesheet': {'points': 500, 'desc': '资产负债表'},
        'cashflow': {'points': 500, 'desc': '现金流量表'},
        'fina_indicator': {'points': 500, 'desc': '财务指标'},
        'fina_mainbz': {'points': 500, 'desc': '主营业务'},
        'forecast': {'points': 500, 'desc': '业绩预告'},
        'express': {'points': 500, 'desc': '业绩快报'},
        'pledge_detail': {'points': 2000, 'desc': '质押明细'},
        'stk_holdertrade': {'points': 2000, 'desc': '股东增减持'},
        'top_inst': {'points': 2000, 'desc': '机构龙虎榜'},
        'limit_list_d': {'points': 2000, 'desc': '涨跌停列表'},
        'margin_detail': {'points': 2000, 'desc': '融资融券明细'},
        'stk_rewards': {'points': 5000, 'desc': '管理层薪酬'},
    }

    results = {}
    today = datetime.now().strftime('%Y%m%d')
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')

    for interface, info in interfaces.items():
        try:
            # 根据接口类型构建测试参数
            if interface == 'stock_basic':
                data = api.stock_basic(list_status='L', limit=1)
            elif interface == 'daily':
                data = api.daily(ts_code='000001.SZ', start_date=yesterday, end_date=today)
            elif interface == 'daily_basic':
                data = api.daily_basic(trade_date=yesterday, limit=1)
            elif interface in ['income', 'balancesheet', 'cashflow', 'fina_indicator', 'fina_mainbz']:
                data = getattr(api, interface)(ts_code='000001.SZ', limit=1)
            elif interface in ['forecast', 'express']:
                data = getattr(api, interface)(ts_code='000001.SZ')
            elif interface == 'pledge_detail':
                data = api.pledge_detail(ts_code='000001.SZ')
            elif interface == 'stk_holdertrade':
                data = api.stk_holdertrade(ts_code='000001.SZ', start_date='20240101', end_date=today)
            elif interface == 'top_inst':
                data = api.top_inst(trade_date=yesterday)
            elif interface == 'limit_list_d':
                data = api.limit_list_d(trade_date=yesterday)
            elif interface == 'margin_detail':
                data = api.margin_detail(ts_code='000001.SZ', start_date='20240101', end_date=today)
            elif interface == 'stk_rewards':
                data = api.stk_rewards(ts_code='000001.SZ', end_date='20231231')
            else:
                data = None

            if data is not None:
                results[interface] = {
                    'available': True,
                    'message': f"✅ {info['desc']} - 可用",
                    'points_required': info['points'],
                    'data_count': len(data) if hasattr(data, '__len__') else 0
                }
            else:
                results[interface] = {
                    'available': False,
                    'message': f"⚠️ {info['desc']} - 返回空数据",
                    'points_required': info['points']
                }

        except Exception as e:
            error_msg = str(e)
            if "积分" in error_msg or "point" in error_msg.lower():
                results[interface] = {
                    'available': False,
                    'message': f"❌ {info['desc']} - 积分不足 (需要 {info['points']} 积分)",
                    'points_required': info['points'],
                    'error': error_msg
                }
            elif "权限" in error_msg or "permission" in error_msg.lower():
                results[interface] = {
                    'available': False,
                    'message': f"❌ {info['desc']} - 无权限 (需要 {info['points']} 积分)",
                    'points_required': info['points'],
                    'error': error_msg
                }
            else:
                results[interface] = {
                    'available': False,
                    'message': f"❌ {info['desc']} - 错误: {error_msg[:50]}",
                    'points_required': info['points'],
                    'error': error_msg
                }

    return results


def get_akshare_alternatives() -> Dict[str, str]:
    """获取 AKShare 替代接口映射"""
    return {
        'realtime_list': 'ak.stock_zh_a_spot_em() - 全市场实时行情',
        'realtime_tick': 'ak.stock_zh_a_tick_tx_js(symbol) - 分时成交',
        'pledge_detail': 'ak.stock_gpzy_pledge_ratio_em() - 质押比例',
        'stk_holdertrade': 'ak.stock_zh_a_gdhs(symbol) - 股东户数变化',
        'top_inst': 'ak.stock_lhb_jgstatistic_em(symbol="近一月") - 机构龙虎榜统计',
        'stock_dzjy': 'ak.stock_dzjy_sctj() / ak.stock_dzjy_mrtj() - 大宗交易',
        'limit_list_d': 'ak.stock_zt_pool_em(date) / ak.stock_dt_pool_em(date) - 涨跌停池',
        'limit_list_ths': 'ak.stock_zt_pool_em(date) - 涨停池',
        'margin_detail': 'ak.stock_margin_detail_sse(date) / ak.stock_margin_detail_szse(date) - 融资融券',
        'fina_mainbz': 'ak.stock_zygc_ym(symbol) - 主营构成',
        'forecast': 'ak.stock_yjyg_em(date) - 业绩预告',
        'express': 'ak.stock_yjkb_em(date) - 业绩快报',
        'stk_rewards': '❌ AKShare 无直接对应接口',
    }


def estimate_points_from_permissions(results: Dict) -> int:
    """根据可用接口估算账户积分"""
    # 积分阈值映射
    thresholds = [
        (5000, ['stk_rewards']),
        (2000, ['pledge_detail', 'stk_holdertrade', 'top_inst', 'limit_list_d', 'margin_detail']),
        (500, ['income', 'balancesheet', 'cashflow', 'fina_indicator', 'fina_mainbz', 'forecast', 'express']),
        (120, ['daily_basic']),
        (0, ['stock_basic', 'daily']),
    ]

    estimated_points = 0

    for points, interfaces in thresholds:
        for interface in interfaces:
            if interface in results and results[interface].get('available'):
                estimated_points = max(estimated_points, points)

    return estimated_points


def main():
    """主函数"""
    print("=" * 60)
    print("🔍 Tushare Token 验证工具")
    print("=" * 60)
    print()

    # 1. 检查 Tushare 库
    print("📦 检查 Tushare 库...")
    available, msg = check_tushare_availability()
    print(f"   {msg}")

    if not available:
        print("\n❌ Tushare 库不可用，请先安装")
        print("   pip install tushare")
        return 1

    print()

    # 2. 获取 Token
    print("🔑 获取 Tushare Token...")
    token = get_tushare_token()

    if not token:
        print("   ❌ 未找到有效的 TUSHARE_TOKEN")
        print("   请在 .env 文件中配置 TUSHARE_TOKEN=your_token")
        print("\n💡 建议：使用 AKShare 作为替代数据源")
        return 1

    print(f"   Token: {token[:8]}...{token[-4:]}")
    print()

    # 3. 验证 Token
    print("🔐 验证 Token 有效性...")
    is_valid, msg, account_info = validate_token(token)
    print(f"   {msg}")

    if not is_valid:
        print("\n❌ Token 验证失败")
        print("\n💡 建议：")
        print("   1. 检查 Token 是否正确")
        print("   2. 登录 Tushare 官网查看账户状态")
        print("   3. 使用 AKShare 作为替代数据源")
        return 1

    print()

    # 4. 检测接口权限
    print("📊 检测接口权限...")
    print("-" * 60)

    import tushare as ts
    ts.set_token(token)
    api = ts.pro_api()

    results = check_api_permissions(api)

    # 按积分要求分组显示
    groups = {
        '基础接口 (0 积分)': ['stock_basic', 'daily'],
        '进阶接口 (120 积分)': ['daily_basic'],
        '财务接口 (500 积分)': ['income', 'balancesheet', 'cashflow', 'fina_indicator', 'fina_mainbz', 'forecast', 'express'],
        '高级接口 (2000 积分)': ['pledge_detail', 'stk_holdertrade', 'top_inst', 'limit_list_d', 'margin_detail'],
        'VIP接口 (5000 积分)': ['stk_rewards'],
    }

    for group_name, interfaces in groups.items():
        print(f"\n{group_name}:")
        for interface in interfaces:
            if interface in results:
                print(f"   {results[interface]['message']}")

    print()

    # 5. 估算积分
    estimated_points = estimate_points_from_permissions(results)
    print("-" * 60)
    print(f"📈 估算账户积分: >= {estimated_points} 积分")

    # 6. 统计可用/不可用接口
    available_count = sum(1 for r in results.values() if r.get('available'))
    total_count = len(results)
    print(f"📊 接口可用率: {available_count}/{total_count} ({available_count/total_count*100:.1f}%)")

    print()

    # 7. 显示不可用接口的 AKShare 替代方案
    unavailable = [k for k, v in results.items() if not v.get('available')]

    if unavailable:
        print("=" * 60)
        print("💡 AKShare 替代方案")
        print("=" * 60)

        alternatives = get_akshare_alternatives()

        for interface in unavailable:
            if interface in alternatives:
                print(f"\n{interface}:")
                print(f"   {alternatives[interface]}")

        print("\n📝 建议：")
        print("   对于 Tushare 不可用的接口，系统会自动尝试使用 AKShare 替代")
        print("   AKShare 是免费的，无需积分，但部分高级数据可能不如 Tushare 完整")

    print()
    print("=" * 60)
    print("✅ 检测完成")
    print("=" * 60)

    return 0


if __name__ == '__main__':
    sys.exit(main())
