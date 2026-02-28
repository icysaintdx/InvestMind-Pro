#!/usr/bin/env python3
"""
短线回测分析 - 基于已有回测结果和新闻情绪
使用本地数据和新闻数据库进行短线分析
"""

import json
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class ShortTermAnalyzer:
    """短线分析器 - 结合新闻情绪"""
    
    def __init__(self, news_db_path: str = "data/news_storage/news_database.db"):
        self.news_db_path = news_db_path
        self.news_stats = self._analyze_news_database()
        
    def _analyze_news_database(self) -> Dict:
        """分析新闻数据库统计"""
        if not os.path.exists(self.news_db_path):
            return {}
        
        try:
            conn = sqlite3.connect(self.news_db_path)
            cursor = conn.cursor()
            
            # 总体统计
            cursor.execute('SELECT COUNT(*) FROM news_articles')
            total = cursor.fetchone()[0]
            
            # 时间范围
            cursor.execute('SELECT MIN(publish_time), MAX(publish_time) FROM news_articles')
            min_time, max_time = cursor.fetchone()
            
            # 按日期统计
            cursor.execute("""
                SELECT DATE(publish_time) as date, COUNT(*) as cnt,
                       AVG(sentiment_score) as avg_sentiment,
                       AVG(urgency_score) as avg_urgency,
                       AVG(impact_score) as avg_impact
                FROM news_articles
                WHERE publish_time IS NOT NULL
                GROUP BY DATE(publish_time)
                ORDER BY date DESC
                LIMIT 14
            """)
            daily_stats = cursor.fetchall()
            
            # 按股票统计
            cursor.execute("""
                SELECT related_stocks, COUNT(*) as cnt,
                       AVG(sentiment_score) as avg_sentiment,
                       AVG(expected_return) as avg_expected_return
                FROM news_articles
                WHERE related_stocks IS NOT NULL AND related_stocks != ''
                GROUP BY related_stocks
                ORDER BY cnt DESC
                LIMIT 20
            """)
            stock_news = cursor.fetchall()
            
            # P0重要新闻
            cursor.execute("""
                SELECT title, related_stocks, sentiment_score, expected_return, publish_time
                FROM news_articles
                WHERE priority = 'P0'
                ORDER BY publish_time DESC
                LIMIT 10
            """)
            p0_news = cursor.fetchall()
            
            conn.close()
            
            return {
                'total_news': total,
                'time_range': f"{min_time} to {max_time}",
                'daily_stats': daily_stats,
                'stock_news': stock_news,
                'p0_news': p0_news
            }
        except Exception as e:
            print(f"Error analyzing news: {e}")
            return {}
    
    def get_stock_sentiment_timeline(self, stock_code: str) -> pd.DataFrame:
        """获取股票的情绪时间线"""
        if not os.path.exists(self.news_db_path):
            return pd.DataFrame()
        
        try:
            conn = sqlite3.connect(self.news_db_path)
            query = """
                SELECT 
                    DATE(publish_time) as date,
                    COUNT(*) as news_count,
                    AVG(sentiment_score) as avg_sentiment,
                    AVG(urgency_score) as avg_urgency,
                    AVG(impact_score) as avg_impact,
                    AVG(expected_return) as avg_expected_return,
                    MAX(sentiment_score) as max_sentiment,
                    MIN(sentiment_score) as min_sentiment
                FROM news_articles
                WHERE related_stocks LIKE ? AND publish_time IS NOT NULL
                GROUP BY DATE(publish_time)
                ORDER BY date
            """
            df = pd.read_sql_query(query, conn, params=(f'%"{stock_code}"%',))
            conn.close()
            return df
        except Exception as e:
            print(f"Error getting sentiment timeline: {e}")
            return pd.DataFrame()
    
    def analyze_short_term_opportunities(self) -> List[Dict]:
        """分析短线机会 - 基于新闻情绪"""
        print("\n" + "="*60)
        print("📊 短线机会分析 - 基于新闻情绪")
        print("="*60)
        
        if not self.news_stats:
            print("❌ 无法获取新闻统计")
            return []
        
        print(f"\n📰 新闻数据库概况:")
        print(f"   总新闻数: {self.news_stats.get('total_news', 0):,}")
        print(f"   时间范围: {self.news_stats.get('time_range', 'N/A')}")
        
        opportunities = []
        
        # 分析每只股票的近期新闻
        stock_news = self.news_stats.get('stock_news', [])
        print(f"\n🔍 分析 {len(stock_news)} 只股票的近期新闻情绪...")
        
        for row in stock_news[:10]:  # 分析前10
            related_stocks, count, avg_sentiment, avg_expected_return = row
            
            try:
                stocks = json.loads(related_stocks)
            except:
                stocks = [related_stocks.strip('[]"\'')]
            
            for stock_code in stocks:
                # 获取时间线
                timeline = self.get_stock_sentiment_timeline(stock_code)
                
                if not timeline.empty and len(timeline) >= 3:
                    # 计算情绪趋势
                    recent_sentiment = timeline['avg_sentiment'].iloc[-3:].mean()
                    sentiment_trend = timeline['avg_sentiment'].iloc[-1] - timeline['avg_sentiment'].iloc[0]
                    
                    # 获取最新情绪
                    latest = timeline.iloc[-1]
                    
                    # 评估机会
                    score = 0
                    reasons = []
                    
                    if recent_sentiment > 0.5:
                        score += 2
                        reasons.append("情绪积极")
                    if sentiment_trend > 0:
                        score += 1
                        reasons.append("情绪上升")
                    if latest['news_count'] >= 5:
                        score += 1
                        reasons.append("新闻热度高")
                    if avg_expected_return and avg_expected_return > 3:
                        score += 2
                        reasons.append(f"预期收益高({avg_expected_return:.1f}%)")
                    
                    if score >= 3:
                        opportunities.append({
                            'stock_code': stock_code,
                            'score': score,
                            'sentiment': recent_sentiment,
                            'trend': sentiment_trend,
                            'news_count': int(latest['news_count']),
                            'expected_return': avg_expected_return or 0,
                            'reasons': reasons,
                            'latest_date': latest['date']
                        })
        
        # 按评分排序
        opportunities.sort(key=lambda x: x['score'], reverse=True)
        
        return opportunities
    
    def generate_short_term_report(self, opportunities: List[Dict]):
        """生成短线分析报告"""
        print("\n" + "="*60)
        print("📈 短线交易机会排名")
        print("="*60)
        
        if not opportunities:
            print("⚠️ 未发现明显短线机会")
            return
        
        for i, opp in enumerate(opportunities[:10], 1):
            print(f"\n{i}. {opp['stock_code']} (评分: {opp['score']}/6)")
            print(f"   情绪分数: {opp['sentiment']:.2f}")
            print(f"   情绪趋势: {'↑' if opp['trend'] > 0 else '↓'} {opp['trend']:.2f}")
            print(f"   新闻数量: {opp['news_count']}条")
            print(f"   预期收益: {opp['expected_return']:.1f}%")
            print(f"   关键信号: {', '.join(opp['reasons'])}")
            print(f"   最新数据: {opp['latest_date']}")
        
        # 保存报告
        report = {
            'generated_at': datetime.now().isoformat(),
            'analysis_period': self.news_stats.get('time_range', 'N/A'),
            'total_news': self.news_stats.get('total_news', 0),
            'opportunities': opportunities
        }
        
        report_file = f"results/short_term_opportunities_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 报告已保存: {report_file}")
    
    def analyze_p0_alerts(self):
        """分析P0级重要新闻警报"""
        p0_news = self.news_stats.get('p0_news', [])
        
        if not p0_news:
            return
        
        print("\n" + "="*60)
        print("🚨 P0级重要新闻警报 (最近10条)")
        print("="*60)
        
        for row in p0_news:
            title, related_stocks, sentiment, expected_return, pub_time = row
            print(f"\n📰 {title[:40]}...")
            print(f"   相关股票: {related_stocks}")
            print(f"   情绪: {sentiment:.2f} | 预期收益: {expected_return:.1f}%")
            print(f"   发布时间: {pub_time}")


def main():
    print("="*60)
    print("📊 InvestMindPro 短线情绪分析")
    print("="*60)
    
    analyzer = ShortTermAnalyzer()
    
    # 分析短线机会
    opportunities = analyzer.analyze_short_term_opportunities()
    analyzer.generate_short_term_report(opportunities)
    
    # 分析P0警报
    analyzer.analyze_p0_alerts()
    
    print("\n" + "="*60)
    print("✅ 分析完成")
    print("="*60)


if __name__ == "__main__":
    main()
