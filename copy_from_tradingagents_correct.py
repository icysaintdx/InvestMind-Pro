#!/usr/bin/env python3
"""
从 TradingAgents-CN-main 复制正确的文件到 InvestMindPro
基于实际的项目结构
"""

import shutil
from pathlib import Path

# 源项目路径
SOURCE_BASE = Path(r"D:\InvestMindPro\TradingAgents-CN-main\tradingagents")
TARGET_BASE = Path(r"D:\InvestMindPro\backend")

print("=" * 80)
print("📋 从 TradingAgents-CN-main 复制文件（正确版本）")
print("=" * 80)
print()
print(f"源路径: {SOURCE_BASE}")
print(f"目标路径: {TARGET_BASE}")
print()

# 检查源路径
if not SOURCE_BASE.exists():
    print(f"❌ 源路径不存在: {SOURCE_BASE}")
    exit(1)

success_count = 0
fail_count = 0
skip_count = 0

# ==================== 1. 复制核心文件 ====================
print("📁 第1步: 复制核心 dataflows 文件")
print("-" * 80)

core_files = [
    ("dataflows/interface.py", "dataflows/interface.py"),
    ("dataflows/data_source_manager.py", "dataflows/data_source_manager_new.py"),  # 备份，不覆盖现有的
    ("dataflows/optimized_china_data.py", "dataflows/optimized_china_data.py"),
    ("dataflows/stock_api.py", "dataflows/stock_api_tradingagents.py"),
    ("dataflows/stock_data_service.py", "dataflows/stock_data_service.py"),
    ("dataflows/data_completeness_checker.py", "dataflows/data_completeness_checker.py"),
    ("dataflows/realtime_metrics.py", "dataflows/realtime_metrics.py"),
]

for src_rel, dst_rel in core_files:
    src = SOURCE_BASE / src_rel
    dst = TARGET_BASE / dst_rel
    
    if not src.exists():
        print(f"⚠️ 源文件不存在: {src_rel}")
        fail_count += 1
        continue
    
    if dst.exists():
        print(f"⏭️ 文件已存在，跳过: {dst_rel}")
        skip_count += 1
        continue
    
    try:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        print(f"✅ 复制: {src_rel} -> {dst_rel}")
        success_count += 1
    except Exception as e:
        print(f"❌ 失败: {src_rel} - {e}")
        fail_count += 1

print()

# ==================== 2. 复制 providers ====================
print("📁 第2步: 复制 providers 目录")
print("-" * 80)

# 创建 providers 目录结构
(TARGET_BASE / "dataflows" / "providers").mkdir(parents=True, exist_ok=True)
(TARGET_BASE / "dataflows" / "providers" / "china").mkdir(parents=True, exist_ok=True)
(TARGET_BASE / "dataflows" / "providers" / "us").mkdir(parents=True, exist_ok=True)
(TARGET_BASE / "dataflows" / "providers" / "hk").mkdir(parents=True, exist_ok=True)

provider_files = [
    ("dataflows/providers/__init__.py", "dataflows/providers/__init__.py"),
    ("dataflows/providers/base_provider.py", "dataflows/providers/base_provider.py"),
    ("dataflows/providers/china/__init__.py", "dataflows/providers/china/__init__.py"),
    ("dataflows/providers/china/akshare.py", "dataflows/providers/china/akshare.py"),
    ("dataflows/providers/china/tushare.py", "dataflows/providers/china/tushare.py"),
    ("dataflows/providers/china/baostock.py", "dataflows/providers/china/baostock.py"),
]

for src_rel, dst_rel in provider_files:
    src = SOURCE_BASE / src_rel
    dst = TARGET_BASE / dst_rel
    
    if not src.exists():
        print(f"⚠️ 源文件不存在: {src_rel}")
        fail_count += 1
        continue
    
    if dst.exists():
        print(f"⏭️ 文件已存在，跳过: {dst_rel}")
        skip_count += 1
        continue
    
    try:
        shutil.copy2(src, dst)
        print(f"✅ 复制: {src_rel}")
        success_count += 1
    except Exception as e:
        print(f"❌ 失败: {src_rel} - {e}")
        fail_count += 1

print()

# ==================== 3. 复制 news 目录（不覆盖已有的）====================
print("📁 第3步: 复制 news 目录")
print("-" * 80)

news_files = [
    ("dataflows/news/__init__.py", "dataflows/news/__init__.py"),
    ("dataflows/news/google_news.py", "dataflows/news/google_news.py"),
    ("dataflows/news/reddit.py", "dataflows/news/reddit.py"),
    # chinese_finance.py 和 realtime_news.py 已存在，不复制
]

for src_rel, dst_rel in news_files:
    src = SOURCE_BASE / src_rel
    dst = TARGET_BASE / dst_rel
    
    if not src.exists():
        print(f"⚠️ 源文件不存在: {src_rel}")
        fail_count += 1
        continue
    
    if dst.exists():
        print(f"⏭️ 文件已存在，跳过: {dst_rel}")
        skip_count += 1
        continue
    
    try:
        shutil.copy2(src, dst)
        print(f"✅ 复制: {src_rel}")
        success_count += 1
    except Exception as e:
        print(f"❌ 失败: {src_rel} - {e}")
        fail_count += 1

print()

# ==================== 4. 复制 cache 目录 ====================
print("📁 第4步: 复制 cache 目录")
print("-" * 80)

(TARGET_BASE / "dataflows" / "cache").mkdir(parents=True, exist_ok=True)

cache_files = [
    ("dataflows/cache/__init__.py", "dataflows/cache/__init__.py"),
    ("dataflows/cache/file_cache.py", "dataflows/cache/file_cache.py"),
    ("dataflows/cache/adaptive.py", "dataflows/cache/adaptive.py"),
    ("dataflows/cache/integrated.py", "dataflows/cache/integrated.py"),
]

for src_rel, dst_rel in cache_files:
    src = SOURCE_BASE / src_rel
    dst = TARGET_BASE / dst_rel
    
    if not src.exists():
        print(f"⚠️ 源文件不存在: {src_rel}")
        fail_count += 1
        continue
    
    if dst.exists():
        print(f"⏭️ 文件已存在，跳过: {dst_rel}")
        skip_count += 1
        continue
    
    try:
        shutil.copy2(src, dst)
        print(f"✅ 复制: {src_rel}")
        success_count += 1
    except Exception as e:
        print(f"❌ 失败: {src_rel} - {e}")
        fail_count += 1

print()

# ==================== 5. 复制 technical 目录 ====================
print("📁 第5步: 复制 technical 目录")
print("-" * 80)

(TARGET_BASE / "dataflows" / "technical").mkdir(parents=True, exist_ok=True)

technical_files = [
    ("dataflows/technical/__init__.py", "dataflows/technical/__init__.py"),
    ("dataflows/technical/stockstats.py", "dataflows/technical/stockstats.py"),
]

for src_rel, dst_rel in technical_files:
    src = SOURCE_BASE / src_rel
    dst = TARGET_BASE / dst_rel
    
    if not src.exists():
        print(f"⚠️ 源文件不存在: {src_rel}")
        fail_count += 1
        continue
    
    if dst.exists():
        print(f"⏭️ 文件已存在，跳过: {dst_rel}")
        skip_count += 1
        continue
    
    try:
        shutil.copy2(src, dst)
        print(f"✅ 复制: {src_rel}")
        success_count += 1
    except Exception as e:
        print(f"❌ 失败: {src_rel} - {e}")
        fail_count += 1

print()

# ==================== 总结 ====================
print("=" * 80)
print("📊 复制统计")
print("=" * 80)
print(f"✅ 成功: {success_count} 个文件")
print(f"⏭️ 跳过: {skip_count} 个文件")
print(f"❌ 失败: {fail_count} 个文件")
print()

if success_count > 0:
    print("🎉 复制完成！")
    print()
    print("📋 已复制的目录结构:")
    print("  backend/dataflows/")
    print("  ├── interface.py              # 统一接口")
    print("  ├── optimized_china_data.py   # 优化的中国数据")
    print("  ├── stock_data_service.py     # 股票数据服务")
    print("  ├── providers/                # 数据提供者")
    print("  │   ├── china/")
    print("  │   │   ├── akshare.py")
    print("  │   │   ├── tushare.py")
    print("  │   │   └── baostock.py")
    print("  ├── news/                     # 新闻模块")
    print("  │   ├── google_news.py")
    print("  │   └── reddit.py")
    print("  ├── cache/                    # 缓存模块")
    print("  │   ├── file_cache.py")
    print("  │   ├── adaptive.py")
    print("  │   └── integrated.py")
    print("  └── technical/                # 技术分析")
    print("      └── stockstats.py")
    print()
    print("下一步:")
    print("  1. 检查导入路径是否需要修改")
    print("  2. 运行测试: python backend\\test_news_simple.py")
    print()

print("✅ 脚本执行完成")
