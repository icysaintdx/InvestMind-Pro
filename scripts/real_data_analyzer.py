#!/usr/bin/env python3
"""
纯净版短线分析 - 只使用系统真实抓取的新闻数据
排除所有批量导入的数据源
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import os

class RealDataAnalyzer:
    """真实数据分析师 - 只使用系统实际抓取的数据"""
    
    # 批量导入的数据源（需要排除）
    BULK_SOURCES = ['微博热议', '东财公告', '巨潮状态变动', '新闻联播']
    
    # 真实每日抓取的数据源
    REAL_SOURCES = [
        '巨潮公告',      # 每日公告抓取
        '新浪财经',      # 新浪财经新闻
        '东方财富',      # 东财新闻
        '财联社',        # 财联社快讯
        '同花顺',        # 同花顺新闻
        '富途牛牛',      # 富途新闻
        '百度财经',      # 百度财经
        '新浪个股',      # 新浪个股新闻
        '东财个股',      # 东财个股
        '财经早餐',      # 财经早餐
    ]
    
    def __init__(self, db_path: str = "data/news_storage/news_database.db"):
        self.db_path = db_path
        self.real_news_count = 0
        self.bulk_news_count = 0
        
    def get_real_news_stats(self) -> Dict:
        """获取真实新闻数据统计"""
        if not os.path.exists(self.db_path):
            return {}
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 真实数据按天统计
        real_sources_str = ','.join([f"'{s}'" for s in self.REAL_SOURCES])
        
        cursor.execute(f"""
            SELECT 
                DATE(publish_time) as date,
                COUNT(*) as cnt,
                COUNT(DISTINCT source) as sources,
                GROUP_CONCAT(DISTINCT source) as source_list,
                AVG(sentiment_score) as avg_sentiment,
                SUM(CASE WHEN priority='P0' THEN 1 ELSE 0 END) as p0_count
            FROM news_articles
            WHERE publish_time IS NOT NULL 
            AND publish_time != ''
            AND source IN ({real_sources_str})
            GROUP BY DATE(publish_time)
            ORDER BY date DESC
            LIMIT 30
        """)
        daily_stats = cursor.fetchall()
        
        # 统计真实数据vs批量数据
        cursor.execute(f"""
            SELECT 
                CASE 
                    WHEN source IN ({real_sources_str}) THEN '真实抓取'
                    ELSE '批量导入'
                END as data_type,
                COUNT(*) as cnt,
                COUNT(DISTINCT source) as sources
            FROM news_articles
            GROUP BY data_type
        """)
        type_stats = cursor.fetchall()
        
        # 最近7天每小时的抓取分布（检查是否是均匀的）
        cursor.execute(f"""
            SELECT 
                DATE(crawl_time) as date,
                strftime('%H', crawl_time) as hour,
                COUNT(*) as cnt
            FROM news_articles
            WHERE source IN ({real_sources_str})
            AND DATE(crawl_time) >= DATE('now', '-7 days')
            GROUP BY date, hour
            ORDER BY date DESC, hour
        """)
        hourly_dist = cursor.fetchall()
        
        conn.close()
        
        return {
            'daily_stats': daily_stats,
            'type_stats': type_stats,
            'hourly_distribution': hourly_dist
        }
    
    def get_stock_real_sentiment(self, stock_code: str, days: int = 7) -> pd.DataFrame:
        """获取股票的真实情绪数据（排除批量）"""
        if not os.path.exists(self.db_path):
            return pd.DataFrame()
        
        real_sources_str = ','.join([f"'{s}'" for s in self.REAL_SOURCES])
        
        conn = sqlite3.connect(self.db_path)
        query = f"""
            SELECT 
                DATE(publish_time) as date,
                COUNT(*) as news_count,
                AVG(sentiment_score) as avg_sentiment,
                AVG(urgency_score) as avg_urgency,
                AVG(impact_score) as avg_impact,
                AVG(expected_return) as avg_expected_return,
                MAX(sentiment_score) as max_sentiment,
                MIN(sentiment_score) as min_sentiment,
                SUM(CASE WHEN priority='P0' THEN 1 ELSE 0 END) as p0_count,
                GROUP_CONCAT(DISTINCT source) as sources
            FROM news_articles
            WHERE related_stocks LIKE ? 
            AND publish_time IS NOT NULL
            AND source IN ({real_sources_str})
            AND DATE(publish_time) >= DATE('now', '-{days} days')
            GROUP BY DATE(publish_time)
            ORDER BY date
        """
        df = pd.read_sql_query(query, conn, params=(f'%"{stock_code}"%',))
        conn.close()
        return df
    
    def analyze_real_short_term_opportunities(self) -> List[Dict]:
        """基于真实数据的短线机会分析"""
        print("="*60)
        print("📊 纯净版短线分析 - 只使用真实抓取数据")
        print("="*60)
        
        stats = self.get_real_news_stats()
        
        print("\n【数据质量统计】")
        for row in stats.get('type_stats', []):
            data_type, cnt, sources = row
            print(f"  {data_type}: {cnt:,}条 ({sources}个来源)")
        
        print("\n【真实数据每日分布（最近15天）】")
        for row in stats.get('daily_stats', [])[:15]:
            date, cnt, sources, source_list, avg_sent, p0 = row
            print(f"  {date}: {cnt:>4}条 | {sources}来源 | P0:{p0:>2} | 情绪:{avg_sent:.2f}")
        
        # 分析股票机会（基于真实数据）
        print("\n【分析真实数据中的股票情绪】")
        
        conn = sqlite3.connect(self.db_path)
        real_sources_str = ','.join([f"'{s}'" for s in self.REAL_SOURCES])
        
        # 获取有真实新闻的股票
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT 
                related_stocks,
                COUNT(*) as cnt,
                AVG(sentiment_score) as avg_sentiment,
                AVG(expected_return) as avg_expected_return,
                MAX(DATE(publish_time)) as latest_date
            FROM news_articles
            WHERE related_stocks IS NOT NULL 
            AND related_stocks != ''
            AND source IN ({real_sources_str})
            AND DATE(publish_time) >= DATE('now', '-7 days')
            GROUP BY related_stocks
            HAVING cnt >= 2
            ORDER BY cnt DESC
            LIMIT 20
        """)
        stock_news = cursor.fetchall()
        conn.close()
        
        opportunities = []
        
        for row in stock_news:
            related_stocks, count, avg_sentiment, avg_expected, latest = row
            
            try:
                stocks = json.loads(related_stocks)
            except:
                stocks = [related_stocks.strip('[]"\'')]
            
            for stock_code in stocks[:1]:  # 只取第一个股票
                # 获取该股票的详细情绪时间线
                timeline = self.get_stock_real_sentiment(stock_code, days=7)
                
                if not timeline.empty:
                    recent_sentiment = timeline['avg_sentiment'].mean()
                    total_news = timeline['news_count'].sum()
                    p0_count = timeline['p0_count'].sum()
                    
                    # 评分逻辑
                    score = 0
                    reasons = []
                    
                    if recent_sentiment > 0.6:
                        score += 2
                        reasons.append(f"情绪积极({recent_sentiment:.2f})")
                    elif recent_sentiment > 0.4:
                        score += 1
                        reasons.append(f"情绪中性偏暖({recent_sentiment:.2f})")
                    
                    if total_news >= 5:
                        score += 1
                        reasons.append(f"关注度高({total_news}条)")
                    
                    if p0_count > 0:
                        score += 2
                        reasons.append(f"重要新闻({p0_count}条P0)")
                    
                    if avg_expected and avg_expected > 2:
                        score += 1
                        reasons.append(f"预期收益{avg_expected:.1f}%")
                    
                    if score >= 3:
                        opportunities.append({
                            'stock_code': stock_code,
                            'score': score,
                            'sentiment': recent_sentiment,
                            'news_count': int(total_news),
                            'p0_count': int(p0_count),
                            'expected_return': avg_expected or 0,
                            'reasons': reasons,
                            'latest_date': latest
                        })
        
        opportunities.sort(key=lambda x: x['score'], reverse=True)
        return opportunities
    
    def generate_real_data_report(self, opportunities: List[Dict]):
        """生成真实数据分析报告"""
        print("\n" + "="*60)
        print("📈 基于真实数据的短线机会")
        print("="*60)
        
        if not opportunities:
            print("\n⚠️ 未发现明显的短线机会")
            return
        
        for i, opp in enumerate(opportunities[:10], 1):
            print(f"\n{i}. {opp['stock_code']} (评分:{opp['score']}/6)")
            print(f"   情绪: {opp['sentiment']:.2f} | 新闻:{opp['news_count']}条 | P0:{opp['p0_count']}条")
            print(f"   预期收益: {opp['expected_return']:.1f}%")
            print(f"   关键信号: {' | '.join(opp['reasons'])}")
            print(f"   最新数据: {opp['latest_date']}")
        
        # 保存报告
        report = {
            'generated_at': datetime.now().isoformat(),
            'data_source': 'real_only',
            'excluded_sources': self.BULK_SOURCES,
            'included_sources': self.REAL_SOURCES,
            'opportunities': opportunities
        }
        
        os.makedirs('results', exist_ok=True)
        report_file = f"results/real_data_opportunities_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 纯净版报告已保存: {report_file}")


def main():
    analyzer = RealDataAnalyzer()
    
    print("\n" + "="*60)
    print("🔍 开始使用纯净数据进行分析")
    print("="*60)
    print("\n✅ 包含的真实数据源:")
    for src in analyzer.REAL_SOURCES:
        print(f"   • {src}")
    print("\n❌ 排除的批量数据源:")
    for src in analyzer.BULK_SOURCES:
        print(f"   • {src}")
    
    opportunities = analyzer.analyze_real_short_term_opportunities()
    analyzer.generate_real_data_report(opportunities)


if __name__ == "__main__":
    main()
