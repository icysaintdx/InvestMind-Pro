#!/usr/bin/env python3
"""
从 TradingAgents-CN-main 复制缺失的文件到 AlphaCouncil
"""

import shutil
from pathlib import Path

# 源项目路径（请根据实际情况修改）
SOURCE_PROJECT = Path(r"D:\AlphaCouncil\TradingAgents-CN-main\tradingagents")
TARGET_PROJECT = Path(r"D:\AlphaCouncil\backend\dataflows")

# 需要复制的文件映射
FILES_TO_COPY = {
    # 从 TradingAgents-CN-main/dataflows/ 复制到 AlphaCouncil/backend/dataflows/
    "dataflows": [
        "akshare_utils.py",
        "finnhub_utils.py",
        "googlenews_utils.py",
        "reddit_utils.py",
        "stockstats_utils.py",
        "interface.py",
        "cache_manager.py",
        "tushare_utils.py",
    ],
}

def copy_files():
    """复制文件"""
    print("=" * 80)
    print("📋 从 TradingAgents-CN-main 复制文件到 AlphaCouncil")
    print("=" * 80)
    print()
    
    # 检查源项目是否存在
    if not SOURCE_PROJECT.exists():
        print(f"❌ 源项目不存在: {SOURCE_PROJECT}")
        print(f"   请修改脚本中的 SOURCE_PROJECT 路径")
        return False
    
    print(f"✅ 源项目: {SOURCE_PROJECT}")
    print(f"✅ 目标项目: {TARGET_PROJECT}")
    print()
    
    success_count = 0
    fail_count = 0
    skip_count = 0
    
    # 复制 dataflows 文件
    print("📁 复制 dataflows 文件...")
    print("-" * 80)
    
    source_dataflows = SOURCE_PROJECT / "dataflows"
    target_dataflows = TARGET_PROJECT / "backend" / "dataflows"
    
    if not source_dataflows.exists():
        print(f"❌ 源目录不存在: {source_dataflows}")
        return False
    
    for filename in FILES_TO_COPY["dataflows"]:
        source_file = source_dataflows / filename
        target_file = target_dataflows / filename
        
        if not source_file.exists():
            print(f"⚠️ 源文件不存在: {filename}")
            fail_count += 1
            continue
        
        if target_file.exists():
            print(f"⏭️ 文件已存在，跳过: {filename}")
            skip_count += 1
            continue
        
        try:
            shutil.copy2(source_file, target_file)
            print(f"✅ 复制成功: {filename}")
            success_count += 1
        except Exception as e:
            print(f"❌ 复制失败: {filename} - {e}")
            fail_count += 1
    
    print()
    print("=" * 80)
    print("📊 复制统计")
    print("=" * 80)
    print(f"✅ 成功: {success_count} 个文件")
    print(f"⏭️ 跳过: {skip_count} 个文件")
    print(f"❌ 失败: {fail_count} 个文件")
    print()
    
    if success_count > 0:
        print("🎉 复制完成！请重新运行测试脚本验证。")
        print()
        print("下一步:")
        print("  python backend\\test_news_simple.py")
    
    return True

if __name__ == '__main__':
    print()
    print("⚠️ 重要提示:")
    print("   请确保 TradingAgents-CN-main 项目在正确的位置")
    print(f"   当前配置的路径: {SOURCE_PROJECT}")
    print()
    
    input("按 Enter 键开始复制...")
    print()
    
    copy_files()
