#!/usr/bin/env python3
"""
整理 dataflows 目录结构
将脚本分类到 stock/ 和 news/ 目录
"""

import shutil
from pathlib import Path

# 定义分类规则
STOCK_FILES = [
    'akshare_utils.py',
    'tushare_utils.py',
    'stockstats_utils.py',
    'stock_data_service.py',
    'stock_api.py',
    'hk_stock_utils.py',
    'improved_hk_utils.py',
    'finnhub_utils.py',
    'optimized_us_data.py',
    'optimized_china_data.py',
    'data_source_manager.py',  # 保留在根目录，但也复制到 stock/
    'stock_data_adapter.py',   # 新增的适配器
]

NEWS_FILES = [
    'realtime_news_utils.py',
    'googlenews_utils.py',
    'reddit_utils.py',
    'social_media_crawler.py',
    'china_market_crawler.py',
    'chinese_finance_utils.py',
]

CACHE_FILES = [
    'cache_manager.py',
    'adaptive_cache.py',
    'integrated_cache.py',
]

UTILS_FILES = [
    'agent_utils.py',
    'config.py',
    'config_utils.py',
    'interface.py',
    'data_sources.py',
    'data_completeness_checker.py',
]

def organize_files():
    """整理文件"""
    base_dir = Path(__file__).parent / 'dataflows'
    
    print("=" * 80)
    print("📁 开始整理 dataflows 目录")
    print("=" * 80)
    print()
    
    # 创建目录
    (base_dir / 'stock').mkdir(exist_ok=True)
    (base_dir / 'news').mkdir(exist_ok=True)
    (base_dir / 'cache').mkdir(exist_ok=True)
    (base_dir / 'utils').mkdir(exist_ok=True)
    
    print("✅ 已创建目录结构:")
    print("  - dataflows/stock/")
    print("  - dataflows/news/")
    print("  - dataflows/cache/")
    print("  - dataflows/utils/")
    print()
    
    # 移动股票相关文件
    print("📊 整理股票相关文件...")
    for filename in STOCK_FILES:
        src = base_dir / filename
        if src.exists():
            # data_source_manager 保留在根目录，只复制
            if filename == 'data_source_manager.py':
                dst = base_dir / 'stock' / filename
                shutil.copy2(src, dst)
                print(f"  📋 复制: {filename} -> stock/")
            else:
                dst = base_dir / 'stock' / filename
                if not dst.exists():
                    shutil.move(str(src), str(dst))
                    print(f"  ✅ 移动: {filename} -> stock/")
        else:
            print(f"  ⚠️ 未找到: {filename}")
    print()
    
    # 移动新闻相关文件
    print("📰 整理新闻相关文件...")
    for filename in NEWS_FILES:
        src = base_dir / filename
        if src.exists():
            dst = base_dir / 'news' / filename
            if not dst.exists():
                shutil.move(str(src), str(dst))
                print(f"  ✅ 移动: {filename} -> news/")
        else:
            print(f"  ⚠️ 未找到: {filename}")
    print()
    
    # 移动缓存相关文件
    print("💾 整理缓存相关文件...")
    for filename in CACHE_FILES:
        src = base_dir / filename
        if src.exists():
            dst = base_dir / 'cache' / filename
            if not dst.exists():
                shutil.move(str(src), str(dst))
                print(f"  ✅ 移动: {filename} -> cache/")
        else:
            print(f"  ⚠️ 未找到: {filename}")
    print()
    
    # 移动工具相关文件
    print("🔧 整理工具相关文件...")
    for filename in UTILS_FILES:
        src = base_dir / filename
        if src.exists():
            dst = base_dir / 'utils' / filename
            if not dst.exists():
                shutil.move(str(src), str(dst))
                print(f"  ✅ 移动: {filename} -> utils/")
        else:
            print(f"  ⚠️ 未找到: {filename}")
    print()
    
    print("=" * 80)
    print("✅ 目录整理完成！")
    print("=" * 80)
    print()
    print("📋 整理后的目录结构:")
    print("  dataflows/")
    print("  ├── stock/          # 股票数据相关")
    print("  ├── news/           # 新闻舆情相关")
    print("  ├── cache/          # 缓存管理相关")
    print("  ├── utils/          # 工具函数相关")
    print("  └── data_source_manager.py  # 核心管理器（保留在根目录）")
    print()
    print("⚠️ 注意: 移动文件后，需要更新相关导入路径！")
    print()

if __name__ == '__main__':
    organize_files()
