#!/usr/bin/env python3
"""
数据下载工具 - 使用baostock获取A股历史数据
"""

import sys
import baostock as bs
import pandas as pd
from datetime import datetime
from pathlib import Path

# 股票列表
STOCKS = {
    # 高波动
    '002460': {'name': '赣锋锂业', 'type': 'high_volatility'},
    '002594': {'name': '比亚迪', 'type': 'high_volatility'},
    '300014': {'name': '亿纬锂能', 'type': 'high_volatility'},
    '300750': {'name': '宁德时代', 'type': 'high_volatility'},
    '300124': {'name': '汇川技术', 'type': 'high_volatility'},
    '601888': {'name': '中国中免', 'type': 'high_volatility'},
    
    # 中波动
    '000568': {'name': '泸州老窖', 'type': 'medium_volatility'},
    '002415': {'name': '海康威视', 'type': 'medium_volatility'},
    '000333': {'name': '美的集团', 'type': 'medium_volatility'},
    '000858': {'name': '五粮液', 'type': 'medium_volatility'},
    '600276': {'name': '恒瑞医药', 'type': 'medium_volatility'},
    '000651': {'name': '格力电器', 'type': 'medium_volatility'},
    '600887': {'name': '伊利股份', 'type': 'medium_volatility'},
    
    # 低波动
    '600519': {'name': '贵州茅台', 'type': 'low_volatility'},
    '601398': {'name': '工商银行', 'type': 'low_volatility'},
    '601318': {'name': '中国平安', 'type': 'low_volatility'},
    '000001': {'name': '平安银行', 'type': 'low_volatility'},
    '600036': {'name': '招商银行', 'type': 'low_volatility'},
    '600900': {'name': '长江电力', 'type': 'low_volatility'},
    '601288': {'name': '农业银行', 'type': 'low_volatility'},
}

def format_baostock_code(symbol: str) -> str:
    """转换为baostock格式: sh.600000 或 sz.000001"""
    if symbol.startswith('6'):
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
    
    # 下载日K线数据
    fields = "date,code,open,high,low,close,volume,amount,turn,pctChg"
    rs = bs.query_history_k_data_plus(bs_code, fields, start_date, end_date, frequency="d", adjustflag="3")
    
    data_list = []
    while (rs.error_code == '0') & rs.next():
        data_list.append(rs.get_row_data())
    
    bs.logout()
    
    if not data_list:
        print("❌ 无数据")
        return False
    
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
    
    # 保存CSV
    output_file = data_dir / f"{symbol}.csv"
    df.to_csv(output_file, index=False)
    print(f"✅ {len(df)}条记录")
    return True

def download_index(symbol: str = "sh.000300", name: str = "沪深300", data_dir: Path = None):
    """下载指数数据"""
    if data_dir is None:
        data_dir = Path(__file__).parent.parent / "data"
    
    start_date = "2020-01-01"
    end_date = datetime.now().strftime("%Y-%m-%d")
    
    print(f"📥 下载 {name} 指数 ...", end=" ")
    
    bs.login()
    fields = "date,code,open,high,low,close,volume,amount,pctChg"
    rs = bs.query_history_k_data_plus(symbol, fields, start_date, end_date, frequency="d")
    
    data_list = []
    while (rs.error_code == '0') & rs.next():
        data_list.append(rs.get_row_data())
    
    bs.logout()
    
    if data_list:
        df = pd.DataFrame(data_list, columns=rs.fields)
        df = df.rename(columns={
            'date': 'date',
            'open': 'open',
            'high': 'high',
            'low': 'low',
            'close': 'close',
            'volume': 'volume',
            'amount': 'amount',
            'pctChg': 'pct_change'
        })
        
        for col in ['open', 'high', 'low', 'close', 'volume', 'amount', 'pct_change']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        output_file = data_dir / "000300.csv"
        df.to_csv(output_file, index=False)
        print(f"✅ {len(df)}条记录")
        return True
    
    print("❌ 失败")
    return False

def main():
    """主函数"""
    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(exist_ok=True)
    
    print(f"📂 数据目录: {data_dir}")
    print(f"📊 共 {len(STOCKS)} 只股票待下载\n")
    
    success_count = 0
    
    # 下载股票数据
    for symbol, info in STOCKS.items():
        if download_stock(symbol, info['name'], data_dir):
            success_count += 1
    
    # 下载沪深300指数
    print()
    download_index(data_dir=data_dir)
    
    print(f"\n✅ 完成: {success_count}/{len(STOCKS)} 只股票")

if __name__ == "__main__":
    main()
