#!/usr/bin/env python3
"""
扩展股票池数据下载 - 新增12只A股
使用baostock获取历史数据
"""

import sys
import baostock as bs
import pandas as pd
from datetime import datetime
from pathlib import Path

# 新增12只股票 - 按板块和波动率分类
EXTENDED_STOCKS = {
    # === 半导体 (高波动) ===
    '688981': {'name': '中芯国际', 'type': 'high_volatility', 'sector': '半导体'},
    '603501': {'name': '韦尔股份', 'type': 'high_volatility', 'sector': '半导体'},
    
    # === 医药 (中波动) ===
    '300760': {'name': '迈瑞医疗', 'type': 'medium_volatility', 'sector': '医药'},
    '603259': {'name': '药明康德', 'type': 'medium_volatility', 'sector': '医药'},
    
    # === 新能源 (高波动) ===
    '300274': {'name': '阳光电源', 'type': 'high_volatility', 'sector': '新能源'},
    '600438': {'name': '通威股份', 'type': 'high_volatility', 'sector': '新能源'},
    
    # === 消费 (中波动) ===
    '603288': {'name': '海天味业', 'type': 'medium_volatility', 'sector': '消费'},
    
    # === 军工 (高波动) ===
    '600893': {'name': '航发动力', 'type': 'high_volatility', 'sector': '军工'},
    '600760': {'name': '中航沈飞', 'type': 'high_volatility', 'sector': '军工'},
    
    # === 有色 (高波动) ===
    '601899': {'name': '紫金矿业', 'type': 'high_volatility', 'sector': '有色'},
    '603993': {'name': '洛阳钼业', 'type': 'high_volatility', 'sector': '有色'},
    
    # === 电子/科技 (中波动) ===
    '002475': {'name': '立讯精密', 'type': 'medium_volatility', 'sector': '电子'},
}

def format_baostock_code(symbol: str) -> str:
    """转换为baostock格式: sh.600000 或 sz.000001"""
    if symbol.startswith('6') or symbol.startswith('68'):
        return f"sh.{symbol}"
    else:
        return f"sz.{symbol}"

def download_stock(symbol: str, name: str, data_dir: Path, start_date: str = "2020-01-01", end_date: str = None):
    """下载单只股票数据"""
    if end_date is None:
        end_date = datetime.now().strftime("%Y-%m-%d")
    
    print(f"📥 下载 {symbol} {name} ...", end=" ")
    
    # 转换为baostock格式
    bs_code = format_baostock_code(symbol)
    
    # 登录baostock
    bs.login()
    
    # 下载日K线数据 (前复权)
    fields = "date,code,open,high,low,close,volume,amount,turn,pctChg"
    rs = bs.query_history_k_data_plus(bs_code, fields, start_date, end_date, frequency="d", adjustflag="2")
    
    data_list = []
    while (rs.error_code == '0') & rs.next():
        data_list.append(rs.get_row_data())
    
    bs.logout()
    
    if not data_list:
        print("❌ 无数据")
        return False, 0
    
    # 转换为DataFrame
    df = pd.DataFrame(data_list, columns=rs.fields)
    df = df.rename(columns={
        'date': 'date',
        'open': 'open',
        'high': 'high',
        'low': 'low',
        'close': 'close',
        'volume': 'volume',
        'amount': 'amount',
        'turn': 'turnover',
        'pctChg': 'pct_change'
    })
    
    # 转换数值类型
    for col in ['open', 'high', 'low', 'close', 'volume', 'amount', 'turnover', 'pct_change']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # 设置日期索引
    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date')
    
    # 保存CSV
    output_file = data_dir / f"{symbol}.csv"
    df.to_csv(output_file)
    print(f"✅ {len(df)}条记录")
    return True, len(df)

def main():
    """主函数"""
    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(exist_ok=True)
    
    print(f"📂 数据目录: {data_dir}")
    print(f"📊 共 {len(EXTENDED_STOCKS)} 只新增股票待下载\n")
    
    success_count = 0
    results = {}
    
    # 下载股票数据
    for symbol, info in EXTENDED_STOCKS.items():
        success, rows = download_stock(symbol, info['name'], data_dir)
        results[symbol] = {
            'name': info['name'],
            'success': success,
            'rows': rows,
            'type': info['type'],
            'sector': info['sector']
        }
        if success:
            success_count += 1
    
    print(f"\n✅ 完成: {success_count}/{len(EXTENDED_STOCKS)} 只股票")
    
    # 打印摘要
    print("\n📋 下载摘要:")
    for symbol, result in results.items():
        status = "✅" if result['success'] else "❌"
        print(f"  {status} {symbol} {result['name']} ({result['sector']}) - {result['rows']}条")
    
    return results

if __name__ == "__main__":
    main()
