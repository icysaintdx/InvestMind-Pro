#!/usr/bin/env python3
"""检查财务数据的实际字段名"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from dataflows.akshare.financial_data import get_financial_data

print("="*60)
print("检查财务数据字段名")
print("="*60)

financial = get_financial_data()

# 获取贵州茅台的数据
print("\n1. 资产负债表字段:")
balance = financial.get_balance_sheet_by_report("600519")
if balance:
    print(f"   共 {len(balance[0])} 个字段")
    print("   关键字段:")
    for key in balance[0].keys():
        if any(x in key.upper() for x in ['ASSET', 'LIAB', 'EQUITY', 'RATIO']):
            print(f"   - {key}: {balance[0][key]}")

print("\n2. 利润表字段:")
profit = financial.get_profit_sheet_by_report("600519")
if profit:
    print(f"   共 {len(profit[0])} 个字段")
    print("   关键字段:")
    for key in profit[0].keys():
        if any(x in key.upper() for x in ['INCOME', 'PROFIT', 'RATIO', 'GROSS']):
            print(f"   - {key}: {profit[0][key]}")

print("\n3. 现金流量表字段:")
cash_flow = financial.get_cash_flow_sheet_by_report("600519")
if cash_flow:
    print(f"   共 {len(cash_flow[0])} 个字段")
    print("   关键字段:")
    for key in cash_flow[0].keys():
        if any(x in key.upper() for x in ['CASH', 'FLOW', 'OPERATE', 'INVEST', 'FINANCE']):
            print(f"   - {key}: {cash_flow[0][key]}")

print("\n" + "="*60)
print("完成")
print("="*60)
