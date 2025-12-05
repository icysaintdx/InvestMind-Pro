#!/usr/bin/env python3
"""
测试新闻API，查看真实的数据源键名
"""
import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.dataflows.news.unified_news_api import UnifiedNewsAPI

async def test_news_sources():
    """测试并打印所有数据源的键名"""
    print("=" * 80)
    print("测试新闻API - 查看真实数据源键名")
    print("=" * 80)
    
    api = UnifiedNewsAPI()
    
    # 测试股票代码
    test_ticker = "600519"  # 贵州茅台
    
    print(f"\n正在获取股票 {test_ticker} 的新闻数据...\n")
    
    try:
        result = await api.get_stock_news_comprehensive(test_ticker)
        
        if result and 'sources' in result:
            sources = result['sources']
            
            print(f"✅ 成功获取数据，共 {len(sources)} 个数据源\n")
            print("=" * 80)
            print("真实的数据源键名列表：")
            print("=" * 80)
            
            for i, (source_key, source_data) in enumerate(sources.items(), 1):
                status = source_data.get('status', 'unknown')
                count = source_data.get('count', 0)
                source_name = source_data.get('source', 'Unknown')
                
                status_icon = "✅" if status == "success" else "❌"
                
                print(f"\n{i}. 键名: '{source_key}'")
                print(f"   状态: {status_icon} {status}")
                print(f"   数量: {count} 条")
                print(f"   后端source字段: {source_name}")
                
            print("\n" + "=" * 80)
            print("前端映射配置建议：")
            print("=" * 80)
            print("\nconst SOURCE_NAME_MAP = {")
            
            for source_key, source_data in sources.items():
                source_name = source_data.get('source', source_key)
                print(f"  '{source_key}': '{source_name}',")
            
            print("}")
            
            print("\n" + "=" * 80)
            print("数据源详细信息：")
            print("=" * 80)
            
            for source_key, source_data in sources.items():
                print(f"\n【{source_key}】")
                print(f"  完整数据: {source_data}")
                
        else:
            print("❌ 未能获取到数据源信息")
            print(f"返回结果: {result}")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_news_sources())
