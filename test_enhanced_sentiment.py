"""
测试增强版情绪分析引擎

包括：
- 情感词典完整性测试
- 紧急度评估测试
- 报告类型识别测试
- 综合情绪分析测试
"""

from backend.dataflows.news.sentiment_engine import SentimentEngine


def test_sentiment_dictionary():
    """测试情感词典"""
    print("=" * 80)
    print("【测试1】情感词典完整性检查")
    print("=" * 80)
    
    engine = SentimentEngine()
    
    print(f"\n✅ 正面词汇总数: {len(engine.positive_words)}")
    print(f"   - 业绩利好类: {len(engine.positive_performance)}")
    print(f"   - 市场情绪类: {len(engine.positive_market)}")
    print(f"   - 公司运营类: {len(engine.positive_operation)}")
    print(f"   - 行业政策类: {len(engine.positive_policy)}")
    print(f"   - 技术创新类: {len(engine.positive_innovation)}")
    
    print(f"\n✅ 负面词汇总数: {len(engine.negative_words)}")
    print(f"   - 业绩利空类: {len(engine.negative_performance)}")
    print(f"   - 市场情绪类: {len(engine.negative_market)}")
    print(f"   - 公司问题类: {len(engine.negative_operation)}")
    print(f"   - 监管风险类: {len(engine.negative_regulation)}")
    
    print(f"\n✅ 强化词总数: {len(engine.intensifiers)}")
    print(f"✅ 否定词总数: {len(engine.negation_words)}")
    
    # 抽样展示
    print(f"\n📝 正面词汇示例: {list(engine.positive_words)[:20]}")
    print(f"📝 负面词汇示例: {list(engine.negative_words)[:20]}")


def test_urgency_assessment():
    """测试紧急度评估"""
    print("\n" + "=" * 80)
    print("【测试2】紧急度评估功能")
    print("=" * 80)
    
    engine = SentimentEngine()
    
    test_cases = [
        ("公司发布特别重大事项公告，紧急停牌", "critical"),
        ("重大资产重组预案公布", "high"),
        ("公司业绩较大幅度下滑", "medium"),
        ("日常经营公告", "low")
    ]
    
    for text, expected in test_cases:
        result = engine.analyze_text(text)
        urgency = result['urgency']
        status = "✅" if urgency == expected else "❌"
        print(f"\n{status} 文本: {text}")
        print(f"   预期紧急度: {expected}")
        print(f"   实际紧急度: {urgency}")


def test_report_type_recognition():
    """测试报告类型识别"""
    print("\n" + "=" * 80)
    print("【测试3】报告类型识别功能")
    print("=" * 80)
    
    engine = SentimentEngine()
    
    test_cases = [
        ("公司发布2024年年报，净利润大幅增长", "financial"),
        ("某券商分析师给予买入评级", "research"),
        ("公司发布风险提示公告", "announcement"),
        ("新闻快讯：科技股集体上涨", "news"),
        ("国务院发布产业政策支持意见", "policy")
    ]
    
    for text, expected in test_cases:
        result = engine.analyze_text(text)
        report_type = result['report_type']
        status = "✅" if report_type == expected else "⚠️"
        print(f"\n{status} 文本: {text}")
        print(f"   预期类型: {expected}")
        print(f"   实际类型: {report_type}")


def test_comprehensive_sentiment():
    """测试综合情绪分析"""
    print("\n" + "=" * 80)
    print("【测试4】综合情绪分析")
    print("=" * 80)
    
    engine = SentimentEngine()
    
    test_cases = [
        {
            "title": "某公司业绩大幅增长超预期，获机构看好",
            "expected_sentiment": "positive"
        },
        {
            "title": "某公司因违规被证监会立案调查，股价暴跌",
            "expected_sentiment": "negative"
        },
        {
            "title": "某公司发布日常经营公告",
            "expected_sentiment": "neutral"
        },
        {
            "title": "不是利空！公司澄清市场传言",
            "expected_sentiment": "positive"  # 测试否定词
        },
        {
            "title": "显著改善！业绩持续大幅增长",
            "expected_sentiment": "positive"  # 测试强化词
        }
    ]
    
    for case in test_cases:
        result = engine.analyze_text(case['title'], weight_title=True)
        sentiment = result['sentiment']
        status = "✅" if sentiment == case['expected_sentiment'] else "⚠️"
        
        print(f"\n{status} 标题: {case['title']}")
        print(f"   预期情绪: {case['expected_sentiment']}")
        print(f"   实际情绪: {sentiment} (得分: {result['score']})")
        print(f"   关键词: {result['keywords'][:5]}")
        print(f"   紧急度: {result['urgency']}")
        print(f"   报告类型: {result['report_type']}")


def test_news_list_analysis():
    """测试新闻列表分析"""
    print("\n" + "=" * 80)
    print("【测试5】新闻列表情绪分析")
    print("=" * 80)
    
    engine = SentimentEngine()
    
    news_list = [
        {
            "title": "某公司中标重大项目",
            "content": "公司成功中标某重大基建项目，订单金额超10亿元，业绩有望大幅提升",
            "pub_time": "2024-12-17 10:00:00",
            "source": "东方财富"
        },
        {
            "title": "某公司发布业绩预告",
            "content": "公司预计2024年净利润同比增长50%以上",
            "pub_time": "2024-12-17 11:00:00",
            "source": "AKShare"
        },
        {
            "title": "某公司收到问询函",
            "content": "公司因股价异常波动收到交易所问询函，要求说明相关情况",
            "pub_time": "2024-12-17 12:00:00",
            "source": "证券时报"
        }
    ]
    
    result = engine.analyze_news_list(news_list)
    
    print(f"\n📊 总体情绪分析结果:")
    print(f"   总体得分: {result['overall_score']} ({result['overall_sentiment']})")
    print(f"   正面新闻: {result['positive_count']}")
    print(f"   负面新闻: {result['negative_count']}")
    print(f"   中性新闻: {result['neutral_count']}")
    
    print(f"\n📈 紧急度统计:")
    for level, count in result['urgency_stats'].items():
        if count > 0:
            print(f"   {level}: {count}")
    
    print(f"\n📋 报告类型统计:")
    for rtype, count in result['report_type_stats'].items():
        if count > 0:
            print(f"   {rtype}: {count}")
    
    print(f"\n📰 各条新闻详情:")
    for i, news in enumerate(result['news_sentiments'], 1):
        print(f"\n   {i}. {news['title']}")
        print(f"      情绪: {news['sentiment']} (得分: {news['score']})")
        print(f"      紧急度: {news['urgency']}")
        print(f"      类型: {news['report_type']}")


def main():
    """主测试函数"""
    print("\n")
    print("=" * 80)
    print(" 增强版情绪分析引擎 - 完整测试")
    print("=" * 80)
    print()
    
    # 运行所有测试
    test_sentiment_dictionary()
    test_urgency_assessment()
    test_report_type_recognition()
    test_comprehensive_sentiment()
    test_news_list_analysis()
    
    print("\n" + "=" * 80)
    print("✅ 所有测试完成！")
    print("=" * 80)


if __name__ == "__main__":
    main()
