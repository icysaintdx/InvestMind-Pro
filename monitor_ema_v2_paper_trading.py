#!/usr/bin/env python3
"""
模拟盘交易监控 - EMA V2策略
实时监控市场，触发交易信号时下单
"""

import time
import json
import requests
from datetime import datetime

API_BASE = "http://localhost:8000"
ACCOUNT_ID = "b0897c95-6201-4f24-9208-f56ce6fa9b45"
POLL_INTERVAL = 60  # 60秒检查一次

# EMA V2 Top 5 股票池
STOCK_POOL = [
    "601888",  # 中国中免 (EMA V2表现最佳 +35.95%)
    "600519",  # 贵州茅台
    "000858",  # 五粮液
    "000333",  # 美的集团
    "000651",  # 格力电器
]

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

def check_signals():
    """检查所有股票的信号"""
    signals = []
    for code in STOCK_POOL:
        try:
            url = f"{API_BASE}/api/strategy-center/signal/generate"
            payload = {
                "stock_code": code,
                "strategy_id": "ema_breakout_v2",  # EMA V2策略
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
                    if signal_type in ['BUY', 'SELL'] and confidence >= 0.6:
                        signals.append({
                            'code': code,
                            'name': signal.get('market_data_summary', {}).get('name', code),
                            'direction': signal_type,
                            'confidence': confidence,
                            'price': signal.get('market_data_summary', {}).get('current_price', 0),
                            'reasoning': signal.get('reasoning', '')[:80]
                        })
        except Exception as e:
            log(f"检查{code}信号失败: {e}")
        time.sleep(0.5)
    return signals

def place_order(stock_code, direction, quantity=100):
    """下单"""
    try:
        url = f"{API_BASE}/api/paper-trading/order/place"
        payload = {
            "account_id": ACCOUNT_ID,
            "stock_code": stock_code,
            "direction": direction,
            "quantity": quantity,
            "order_type": "MARKET"
        }
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data.get('success'):
                return True, data.get('order', {})
            else:
                return False, data.get('message', 'Unknown error')
    except Exception as e:
        log(f"下单失败: {e}")
    return False, str(e)

def get_account_status():
    """获取账户状态"""
    try:
        url = f"{API_BASE}/api/paper-trading/account/{ACCOUNT_ID}"
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            data = r.json()
            if data.get('success'):
                return data.get('account', {})
    except:
        pass
    return {}

def main():
    log("="*60)
    log("🚀 EMA V2 模拟盘交易监控启动")
    log(f"账户ID: {ACCOUNT_ID}")
    log(f"监控股票: {len(STOCK_POOL)}只 (Top 5 EMA V2)")
    log(f"轮询间隔: {POLL_INTERVAL}秒")
    log("="*60)
    
    cycle = 0
    while True:
        cycle += 1
        now = datetime.now()
        
        # 只在交易时间执行 (9:30-11:30, 13:00-15:00)
        if not (9 <= now.hour <= 15):
            log(f"非交易时间，跳过第{cycle}轮")
            time.sleep(POLL_INTERVAL)
            continue
        if now.hour == 11 and now.minute > 30:
            log(f"午间休市，跳过第{cycle}轮")
            time.sleep(POLL_INTERVAL)
            continue
        if now.hour == 12:
            log(f"午间休市，跳过第{cycle}轮")
            time.sleep(POLL_INTERVAL)
            continue
        if now.hour == 15 and now.minute > 0:
            log(f"收盘后，跳过第{cycle}轮")
            time.sleep(POLL_INTERVAL)
            continue
        
        log(f"\n--- 第{cycle}轮检查 [{now.strftime('%H:%M')}] ---")
        
        # 检查信号
        signals = check_signals()
        log(f"发现信号数量: {len(signals)}")
        
        for sig in signals:
            log(f"📊 {sig['name']}({sig['code']}): {sig['direction']} 置信度={sig['confidence']:.2f}")
            log(f"   理由: {sig['reasoning']}...")
            
            # 执行交易
            qty = 100 if sig['direction'] == 'BUY' else 100  # 每次100股
            success, result = place_order(sig['code'], sig['direction'], qty)
            if success:
                log(f"   ✅ 下单成功: {result.get('order_id', 'N/A')}")
            else:
                log(f"   ❌ 下单失败: {result}")
        
        # 显示账户状态
        account = get_account_status()
        if account:
            log(f"💰 账户: 总资产={account.get('total_assets',0):,.0f} "
                f"可用={account.get('available_cash',0):,.0f} "
                f"盈亏={account.get('total_profit',0):,.0f} "
                f"持仓={len(account.get('positions',[]))}只")
        
        log(f"等待{POLL_INTERVAL}秒...")
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
