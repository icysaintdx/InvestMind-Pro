"""
测试P1和P2新增功能
- P1-1: 多源新闻聚合
- P1-2: 情绪分析引擎
- P2-1: 任务调度器
- P2-2: 数据持久化
"""

import sys
import os
import asyncio
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def test_news_aggregation():
    """测试多源新闻聚合"""
    print("\n" + "="*60)
    print("【P1-1】测试多源新闻聚合")
    print("="*60)
    
    from backend.dataflows.news.multi_source_news_aggregator import get_news_aggregator
    
    test_code = '600519.SH'
    
    try:
        print(f"\n📰 获取{test_code}的新闻...")
        aggregator = get_news_aggregator()
        
        news_data = aggregator.aggregate_news(
            test_code,
            include_tushare=False,  # Tushare新闻需要5000积分
            include_akshare=True,
            limit_per_source=5
        )
        
        print(f"✅ 新闻聚合成功:")
        print(f"   总计: {news_data.get('total_count')}条")
        
        sources = news_data.get('sources', {})
        for source_name, news_list in sources.items():
            print(f"   - {source_name}: {len(news_list)}条")
        
        # 显示前3条新闻
        merged_news = news_data.get('merged_news', [])
        if merged_news:
            print(f"\n📋 最新新闻(前3条):")
            for i, news in enumerate(merged_news[:3], 1):
                print(f"\n[{i}] {news.get('title', 'Unknown')}")
                print(f"    来源: {news.get('source', 'Unknown')}")
                print(f"    时间: {news.get('pub_time', 'Unknown')}")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


def test_sentiment_analysis():
    """测试情绪分析"""
    print("\n" + "="*60)
    print("【P1-2】测试情绪分析引擎")
    print("="*60)
    
    from backend.dataflows.news.multi_source_news_aggregator import get_news_aggregator
    from backend.dataflows.news.sentiment_engine import get_sentiment_engine
    
    test_code = '600519.SH'
    
    try:
        # 1. 先获取新闻
        print(f"\n📰 获取{test_code}的新闻...")
        aggregator = get_news_aggregator()
        news_data = aggregator.aggregate_news(
            test_code,
            include_tushare=False,
            include_akshare=True,
            limit_per_source=10
        )
        
        news_list = news_data.get('merged_news', [])
        print(f"✅ 获取到{len(news_list)}条新闻")
        
        if not news_list:
            print("⚠️ 无新闻数据，跳过情绪分析")
            return
        
        # 2. 情绪分析
        print(f"\n💭 分析情绪...")
        sentiment_engine = get_sentiment_engine()
        sentiment_result = sentiment_engine.analyze_news_list(news_list)
        
        print(f"✅ 情绪分析完成:")
        print(f"   总体得分: {sentiment_result.get('overall_score')}/100")
        print(f"   总体情绪: {sentiment_result.get('overall_sentiment')}")
        print(f"   正面新闻: {sentiment_result.get('positive_count')}条")
        print(f"   中性新闻: {sentiment_result.get('neutral_count')}条")
        print(f"   负面新闻: {sentiment_result.get('negative_count')}条")
        
        # 显示部分新闻情绪
        news_sentiments = sentiment_result.get('news_sentiments', [])
        if news_sentiments:
            print(f"\n📊 新闻情绪详情(前3条):")
            for i, item in enumerate(news_sentiments[:3], 1):
                sentiment = item['sentiment']
                emoji_map = {'positive': '😊', 'neutral': '😐', 'negative': '😟'}
                emoji = emoji_map.get(sentiment['sentiment'], '😐')
                
                print(f"\n[{i}] {emoji} {sentiment['sentiment']} (得分: {sentiment['score']})")
                print(f"    标题: {item['title'][:40]}...")
                if sentiment['keywords']:
                    print(f"    关键词: {', '.join(sentiment['keywords'][:3])}")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


async def test_task_scheduler():
    """测试任务调度器"""
    print("\n" + "="*60)
    print("【P2-1】测试任务调度器")
    print("="*60)
    
    from backend.dataflows.scheduler import get_scheduler, schedule_task
    
    try:
        # 1. 定义测试任务
        task_count = 0
        
        async def test_task(name: str):
            nonlocal task_count
            task_count += 1
            print(f"   ▶️ 执行任务: {name} (第{task_count}次)")
            await asyncio.sleep(1)
            print(f"   ✅ 任务完成: {name}")
        
        # 2. 调度任务
        print("\n➕ 添加测试任务...")
        scheduler = get_scheduler()
        
        schedule_task(
            task_id='test_task_1',
            name='测试任务1',
            func=test_task,
            interval_minutes=1,  # 1分钟间隔
            args=('任务1',),
            retry_count=2
        )
        
        schedule_task(
            task_id='test_task_2',
            name='测试任务2',
            func=test_task,
            interval_minutes=2,
            args=('任务2',)
        )
        
        print(f"✅ 添加了2个任务")
        
        # 3. 启动调度器
        print("\n🚀 启动调度器...")
        await scheduler.start()
        
        # 4. 运行5秒
        print("⏳ 运行5秒...")
        await asyncio.sleep(5)
        
        # 5. 检查状态
        print("\n📊 任务状态:")
        all_tasks = scheduler.get_all_tasks_status()
        for task_info in all_tasks:
            print(f"\n任务: {task_info['name']}")
            print(f"  状态: {task_info['status']}")
            print(f"  执行次数: {task_info['attempts']}")
            if task_info['last_run']:
                print(f"  最后执行: {task_info['last_run']}")
        
        # 6. 停止调度器
        print("\n🛑 停止调度器...")
        await scheduler.stop()
        
        print(f"\n✅ 调度器测试完成 (共执行{task_count}次任务)")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


def test_persistence():
    """测试数据持久化"""
    print("\n" + "="*60)
    print("【P2-2】测试数据持久化")
    print("="*60)
    
    from backend.dataflows.persistence import (
        get_monitor_storage,
        save_config,
        load_config,
        add_stock,
        remove_stock
    )
    
    try:
        storage = get_monitor_storage()
        
        # 1. 测试添加监控
        print("\n➕ 添加监控股票...")
        add_stock('600519.SH', '贵州茅台', frequency='1h', items={
            'news': True,
            'risk': True,
            'sentiment': True,
            'suspend': False
        })
        add_stock('000001.SZ', '平安银行', frequency='30m')
        
        # 2. 加载配置
        print("\n📖 加载监控配置...")
        config = load_config()
        stocks = config.get('stocks', {})
        print(f"✅ 当前监控{len(stocks)}只股票:")
        for code, info in stocks.items():
            print(f"   - {info['name']}({code}): {info['frequency']}")
        
        # 3. 测试历史数据保存
        print("\n💾 保存历史数据...")
        storage.save_stock_history('600519.SH', {
            'risk_level': 'low',
            'sentiment_score': 65.5,
            'news_count': 10
        })
        print("✅ 历史数据保存成功")
        
        # 4. 加载历史数据
        print("\n📚 加载历史数据...")
        history = storage.load_stock_history('600519.SH')
        print(f"✅ 加载了{len(history)}条历史记录")
        if history:
            latest = history[-1]
            print(f"   最新记录: {latest['timestamp']}")
            print(f"   数据: {latest['data']}")
        
        # 5. 测试移除
        print("\n➖ 移除监控股票...")
        remove_stock('000001.SZ')
        
        config = load_config()
        print(f"✅ 当前监控{len(config.get('stocks', {}))}只股票")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("P1 & P2 功能测试")
    print("="*60)
    
    try:
        # P1测试
        test_news_aggregation()
        test_sentiment_analysis()
        
        # P2测试
        await test_task_scheduler()
        test_persistence()
        
        print("\n" + "="*60)
        print("✅ 所有测试完成!")
        print("="*60)
        
    except KeyboardInterrupt:
        print("\n\n⚠️ 测试已中断")
    except Exception as e:
        print(f"\n\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
