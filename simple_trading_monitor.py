#!/usr/bin/env python3
"""
模拟盘交易监控 - 简化版
实时监控市场，触发交易信号时下单
"""

import time
import json
import requests
from datetime import datetime

API_BASE = "http://localhost:8000"
ACCOUNT_ID = "451dbe53-4307-42e3-a457-a9bead155986"
POLL_INTERVAL = 30  # 30秒检查一次

STOCK_POOL = [
    "600519", "000858", "601318", "000333", "600036",
    "002594", "601899", "600900", "000001", "002475",
    "601012", "600276", "000568", "002714", "600809"
]

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

def get_realtime_price(stock_code):
    """获取实时价格"""
    try:
        url = f"{API_BASE}/api/market-data/realtime/{stock_code}"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data.get('success'):
                return data.get('data', {}).get('current_price', 0)
    except Exception as e:
        log(f"获取{stock_code}价格失败: {e}")
    return 0

def check_signals():
    """检查所有股票的信号"""
    signals = []
    for code in STOCK_POOL:
        try:
            url = f"{API_BASE}/api/strategy-center/signal/generate"
            payload = {
                "stock_code": code,
                "strategy_id": "ema_breakout",  # EMA策略
                "include_chart": False,
                "timeframe": "daily"
            }
            r = requests.post(url, json=payload, timeout=30)
            if r.status_code == 200:
                data = r.json()
                if data.get('success'):
                    signal = data.get('data', {})
                    signal_type = signal.get('signal_type', 'HOLD')
                    confidence = signal.get('confidence', 0)
                    if signal_type in ['BUY', 'SELL'] and confidence >= 0.55:
                        signals.append({
                            'code': code,
                            'name': signal.get('market_data_summary', {}).get('name', code),
                            'direction': signal_type,
                            'confidence': confidence,
                            'price': signal.get('market_data_summary', {}).get('current_price', 0),
                            'reasoning': signal.get('reasoning', '')[:50]
                        })
        except Exception as e:
            log(f"检查{code}信号失败: {e}")
        time.sleep(0.5)  # 避免限流
    return signals

def place_order(stock_code, direction, price, quantity=100):
    """下单"""
    try:
        url = f"{API_BASE}/api/paper-trading/order"
        payload = {
            "account_id": ACCOUNT_ID,
            "stock_code": stock_code,
            "direction": direction,  # BUY/SELL
            "quantity": quantity,
            "order_type": "MARKET"
        }
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data.get('success'):
                return True, data.get('order', {})
    except Exception as e:
        log(f"下单失败: {e}")
    return False, {}

def main():
    log("="*60)
    log("🚀 模拟盘交易监控启动")
    log(f"账户ID: {ACCOUNT_ID}")
    log(f"监控股票: {len(STOCK_POOL)}只")
    log(f"轮询间隔: {POLL_INTERVAL}秒")
    log("="*60)
    
    cycle = 0
    while True:
        cycle += 1
        log(f"\n--- 第{cycle}轮检查 ---")
        
        # 检查信号
        signals = check_signals()
        log(f"发现信号数量: {len(signals)}")
        
        for sig in signals:
            log(f"📊 {sig['name']}({sig['code']}): {sig['direction']} 置信度={sig['confidence']:.2f} 价格={sig['price']}")
            log(f"   理由: {sig['reasoning']}...")
            
            # 执行交易
            if sig['direction'] == 'BUY':
                success, order = place_order(sig['code'], 'BUY', sig['price'])
                if success:
                    log(f"   ✅ 买入成功: {order}")
                else:
                    log(f"   ❌ 买入失败")
        
        # 显示账户状态
        try:
            url = f"{API_BASE}/api/paper-trading/account/{ACCOUNT_ID}"
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                data = r.json()
                if data.get('success'):
                    account = data.get('account', {})
                    log(f"💰 账户: 总资产={account.get('total_assets',0):,.0f} 可用={account.get('available_cash',0):,.0f} 盈亏={account.get('total_profit',0):,.0f}")
        except:
            pass
        
        log(f"等待{POLL_INTERVAL}秒...")
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
