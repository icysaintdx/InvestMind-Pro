#!/usr/bin/env python3
"""
更新负收益股票优化参数到主配置
只为效果良好的股票更新参数
"""

import json
from pathlib import Path
from datetime import datetime

# 需要更新的股票及其新参数 (效果良好的)
PARAM_UPDATES = {
    '603288': {
        'fast_ema': 10,
        'slow_ema': 40,
        'atr_period': 14,
        'atr_multiplier': 2.0,
        'market_filter': True,
        'improvement': 33.92,
        'old_return': -10.84,
        'new_return': 23.08
    },
    '688981': {
        'fast_ema': 5,
        'slow_ema': 35,
        'atr_period': 14,
        'atr_multiplier': 3.0,
        'market_filter': True,
        'improvement': 28.14,
        'old_return': -27.84,
        'new_return': 0.31
    }
}

def update_main_config():
    """更新主参数配置文件"""
    config_path = Path('/home/icysaintdx/.openclaw/workspace/InvestMindPro/results/param_optimization_full_20260227_140832.json')
    
    if not config_path.exists():
        print(f"[ERROR] 配置文件不存在: {config_path}")
        return False
    
    # 读取现有配置
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    print("="*80)
    print("更新主参数配置文件")
    print("="*80)
    
    updated_count = 0
    
    for symbol, new_params in PARAM_UPDATES.items():
        if symbol in config:
            print(f"\n📊 更新股票: {symbol}")
            print(f"  原收益: {new_params['old_return']:+.2f}% → 新收益: {new_params['new_return']:+.2f}%")
            print(f"  改进: +{new_params['improvement']:.2f}%")
            
            # 保存旧参数用于记录
            old_best_params = config[symbol]['best_params'].copy()
            
            # 更新参数
            config[symbol]['best_params'] = {
                'fast_ema': new_params['fast_ema'],
                'slow_ema': new_params['slow_ema'],
                'atr_period': new_params['atr_period'],
                'atr_multiplier': new_params['atr_multiplier'],
                'market_filter': new_params['market_filter']
            }
            
            # 更新结果
            config[symbol]['best_result']['return'] = new_params['new_return']
            
            # 添加优化历史记录
            if 'optimization_history' not in config[symbol]:
                config[symbol]['optimization_history'] = []
            
            config[symbol]['optimization_history'].append({
                'date': datetime.now().strftime('%Y-%m-%d'),
                'old_params': old_best_params,
                'new_params': config[symbol]['best_params'],
                'old_return': new_params['old_return'],
                'new_return': new_params['new_return'],
                'improvement': new_params['improvement'],
                'reason': 'negative_stock_retest_20260228'
            })
            
            # 添加标签
            config[symbol]['negative_stock_optimized'] = True
            config[symbol]['last_optimized'] = datetime.now().strftime('%Y-%m-%d')
            
            print(f"  ✅ 参数已更新")
            print(f"     新参数: fast_ema={new_params['fast_ema']}, "
                  f"slow_ema={new_params['slow_ema']}, "
                  f"atr_multiplier={new_params['atr_multiplier']}")
            updated_count += 1
        else:
            print(f"\n⚠️ 股票 {symbol} 不在主配置中，将添加新条目")
            config[symbol] = {
                'symbol': symbol,
                'best_params': {
                    'fast_ema': new_params['fast_ema'],
                    'slow_ema': new_params['slow_ema'],
                    'atr_period': new_params['atr_period'],
                    'atr_multiplier': new_params['atr_multiplier'],
                    'market_filter': new_params['market_filter']
                },
                'best_result': {
                    'return': new_params['new_return'],
                    'win_rate': 0,  # 需要重新回测获取
                    'trades': 0,
                    'max_drawdown': 0,
                    'sharpe': 0
                },
                'negative_stock_optimized': True,
                'last_optimized': datetime.now().strftime('%Y-%m-%d'),
                'all_results': []
            }
            updated_count += 1
    
    # 保存更新后的配置
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    print(f"\n" + "="*80)
    print(f"✅ 成功更新 {updated_count} 只股票的参数")
    print(f"📄 配置文件: {config_path}")
    print("="*80)
    
    return True


def generate_update_summary():
    """生成参数更新摘要"""
    print("\n" + "="*80)
    print("参数更新摘要")
    print("="*80)
    print("\n以下股票的参数已更新到主配置:\n")
    print(f"{'代码':<10} {'名称':<10} {'原收益':>10} {'新收益':>10} {'改进':>10}")
    print("-"*60)
    
    stock_names = {'603288': '海天味业', '688981': '中芯国际'}
    
    for symbol, params in PARAM_UPDATES.items():
        name = stock_names.get(symbol, 'Unknown')
        print(f"{symbol:<10} {name:<10} {params['old_return']:>+9.2f}% {params['new_return']:>+9.2f}% "
              f"{params['improvement']:>+9.2f}%")
    
    print("\n" + "="*80)
    print("注意：其他3只股票（牧原股份、格力电器、同花顺）需要进一步优化")
    print("="*80)


if __name__ == '__main__':
    if update_main_config():
        generate_update_summary()
