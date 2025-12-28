"""
数据持久化服务
处理数据流数据的保存、更新、删除逻辑
"""

import hashlib
from datetime import datetime
from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from backend.database.services import (
    MonitoredStockService,
    StockDataService,
    StockNewsService,
    DataFlowStatsService
)


class DataPersistenceManager:
    """数据持久化管理器"""
    
    @staticmethod
    def save_comprehensive_data(
        db: Session,
        ts_code: str,
        comprehensive_data: Dict,
        source: str = 'mixed'
    ):
        """
        保存综合数据（替换更新模式）

        Args:
            db: 数据库会话
            ts_code: 股票代码
            comprehensive_data: 综合数据字典（来自 get_all_stock_data 或 get_category_data）
            source: 数据来源
        """
        today = datetime.utcnow().strftime('%Y-%m-%d')
        saved_count = 0

        # 辅助函数：安全保存数据
        def safe_save(data_type: str, data: Dict, data_source: str = 'mixed'):
            nonlocal saved_count
            if data and isinstance(data, dict):
                # 检查是否有有效状态
                status = data.get('status', '')
                if status in ['success', 'normal', 'has_suspend', 'st_stock', 'no_data']:
                    # 提取实际数据
                    actual_data = data.get('data', data)
                    if actual_data:
                        StockDataService.save_or_update(
                            db, ts_code, data_type,
                            actual_data,
                            source=data_source,
                            data_date=today
                        )
                        saved_count += 1
                        return True
            return False

        # 1. 保存公司基本信息
        if 'company_info' in comprehensive_data:
            safe_save('company_info', comprehensive_data['company_info'], 'tushare')

        # 2. 保存实时行情
        if 'realtime' in comprehensive_data:
            safe_save('realtime', comprehensive_data['realtime'], 'akshare')

        # 3. 保存实时成交
        if 'realtime_tick' in comprehensive_data:
            safe_save('realtime_tick', comprehensive_data['realtime_tick'], 'akshare')

        # 4. 保存财务数据（处理嵌套结构）
        if 'financial' in comprehensive_data:
            financial_data = comprehensive_data['financial']
            if isinstance(financial_data, dict):
                if financial_data.get('status') == 'success':
                    # 保存整个财务数据
                    StockDataService.save_or_update(
                        db, ts_code, 'financial',
                        financial_data,
                        source='tushare',
                        data_date=today
                    )
                    saved_count += 1
                    # 分别保存各项
                    if 'income' in financial_data:
                        StockDataService.save_or_update(
                            db, ts_code, 'financial_income',
                            financial_data['income'],
                            source='tushare',
                            data_date=today
                        )
                    if 'balance' in financial_data:
                        StockDataService.save_or_update(
                            db, ts_code, 'financial_balance_sheet',
                            financial_data['balance'],
                            source='tushare',
                            data_date=today
                        )
                    if 'cashflow' in financial_data:
                        StockDataService.save_or_update(
                            db, ts_code, 'financial_cashflow',
                            financial_data['cashflow'],
                            source='tushare',
                            data_date=today
                        )

        # 5. 保存审计意见
        if 'audit' in comprehensive_data:
            safe_save('audit', comprehensive_data['audit'], 'tushare')

        # 6. 保存业绩预告
        if 'forecast' in comprehensive_data:
            safe_save('forecast', comprehensive_data['forecast'], 'tushare')

        # 7. 保存分红数据
        if 'dividend' in comprehensive_data:
            safe_save('dividend', comprehensive_data['dividend'], 'tushare')

        # 8. 保存风险数据
        risk_keys = ['st_status', 'suspend', 'restricted', 'st_status_ak', 'st_info_ak', 'suspend_ak', 'restricted_ak']
        for key in risk_keys:
            if key in comprehensive_data:
                safe_save(f'risk_{key}', comprehensive_data[key], 'mixed')

        # 9. 保存资金流数据
        capital_keys = ['margin', 'margin_detail', 'hsgt_holding', 'ggt_top10', 'hk_hold',
                       'moneyflow_hsgt', 'holder_trade', 'pledge', 'pledge_detail',
                       'margin_ak', 'holder_trade_ak', 'pledge_detail_ak']
        for key in capital_keys:
            if key in comprehensive_data:
                safe_save(f'capital_{key}', comprehensive_data[key], 'mixed')

        # 10. 保存行情数据
        market_keys = ['limit_list', 'limit_list_ths', 'dragon_tiger', 'top_inst',
                      'dragon_tiger_ak', 'block_trade', 'realtime_list']
        for key in market_keys:
            if key in comprehensive_data:
                safe_save(f'market_{key}', comprehensive_data[key], 'mixed')

        # 11. 保存基础信息
        basic_keys = ['managers', 'manager_rewards', 'main_business']
        for key in basic_keys:
            if key in comprehensive_data:
                safe_save(f'basic_{key}', comprehensive_data[key], 'tushare')

        # 12. 保存AKShare扩展数据
        akshare_keys = ['audit_ak', 'forecast_ak', 'financial_risk']
        for key in akshare_keys:
            if key in comprehensive_data:
                safe_save(f'akshare_{key}', comprehensive_data[key], 'akshare')

        # 13. 保存新闻数据（增量更新模式）
        news_keys = ['news_sina', 'news_em', 'market_news', 'cninfo_news',
                     'industry_policy', 'announcements', 'announcements_ak']
        news_count = 0
        for key in news_keys:
            if key in comprehensive_data:
                news_data = comprehensive_data[key]
                if isinstance(news_data, dict) and news_data.get('status') == 'success':
                    news_list = news_data.get('data', [])
                    if isinstance(news_list, list):
                        for news_item in news_list:
                            news_count += DataPersistenceManager._save_single_news(
                                db, ts_code, news_item, source=key
                            )

        # 14. 保存综合新闻列表
        if 'news' in comprehensive_data:
            news_data = comprehensive_data['news']
            if isinstance(news_data, list):
                for news_item in news_data:
                    news_count += DataPersistenceManager._save_single_news(
                        db, ts_code, news_item, source='aggregated'
                    )

        # 15. 更新每日统计
        if news_count > 0:
            DataFlowStatsService.update_daily_stats(
                db, stat_date=today, news_count_inc=news_count
            )

        # 16. 更新监控股票的最后更新时间
        MonitoredStockService.update_last_update(db, ts_code)

        print(f"[持久化] {ts_code} 数据保存完成，保存{saved_count}项数据，新增新闻{news_count}条")
    
    @staticmethod
    def _save_single_news(
        db: Session,
        ts_code: str,
        news_item: Dict,
        source: str
    ) -> int:
        """
        保存单条新闻（增量更新）
        
        Returns:
            1 if added, 0 if skipped
        """
        # 生成唯一新闻ID
        title = news_item.get('title', '')
        pub_time = news_item.get('time') or news_item.get('pub_time') or datetime.utcnow().isoformat()
        
        news_id = hashlib.md5(f"{title}{pub_time}".encode()).hexdigest()
        
        # 解析发布时间
        if isinstance(pub_time, str):
            try:
                pub_time_dt = datetime.fromisoformat(pub_time.replace('Z', '+00:00'))
            except:
                pub_time_dt = datetime.utcnow()
        else:
            pub_time_dt = pub_time
        
        # 添加新闻
        result = StockNewsService.add_news(
            db=db,
            ts_code=ts_code,
            news_id=news_id,
            title=title,
            content=news_item.get('content'),
            summary=news_item.get('summary'),
            source=source,
            url=news_item.get('url'),
            pub_time=pub_time_dt,
            sentiment=news_item.get('sentiment'),
            sentiment_score=news_item.get('sentiment_score'),
            urgency=news_item.get('urgency'),
            report_type=news_item.get('type') or news_item.get('category'),
            keywords=news_item.get('keywords', [])
        )
        
        return 1 if result else 0
    
    @staticmethod
    def load_stock_data(
        db: Session,
        ts_code: str,
        data_type: Optional[str] = None,
        days: int = 1
    ) -> Dict:
        """
        加载股票数据

        Args:
            db: 数据库会话
            ts_code: 股票代码
            data_type: 数据类型，None表示加载所有
            days: 加载最近N天的数据

        Returns:
            数据字典（与 get_all_stock_data 返回格式兼容）
        """
        result = {}
        today = datetime.utcnow().strftime('%Y-%m-%d')

        # 辅助函数：加载并格式化数据
        def load_and_format(db_type: str, result_key: str = None):
            record = StockDataService.get_latest(db, ts_code, db_type)
            if record:
                key = result_key or db_type
                # 检查原始数据是否已经包含status字段
                if isinstance(record.data, dict) and 'status' in record.data:
                    # 如果原始数据已经有status，直接使用原始数据
                    result[key] = record.data.copy()
                    result[key]['fetch_time'] = record.fetch_time.isoformat() if record.fetch_time else None
                    result[key]['source'] = record.source
                else:
                    # 否则包装成标准格式
                    result[key] = {
                        'status': 'success',
                        'data': record.data,
                        'fetch_time': record.fetch_time.isoformat() if record.fetch_time else None,
                        'source': record.source
                    }
                return True
            return False

        if data_type:
            # 加载特定类型
            load_and_format(data_type)
        else:
            # 加载所有类型的综合数据

            # 1. 基础信息
            load_and_format('company_info')
            load_and_format('basic_managers', 'managers')
            load_and_format('basic_manager_rewards', 'manager_rewards')
            load_and_format('basic_main_business', 'main_business')

            # 2. 实时行情
            load_and_format('realtime')
            load_and_format('realtime_tick')

            # 3. 财务数据
            load_and_format('financial')
            load_and_format('financial_income', 'income')
            load_and_format('financial_balance_sheet', 'balance_sheet')
            load_and_format('financial_cashflow', 'cashflow')
            load_and_format('audit')
            load_and_format('forecast')
            load_and_format('dividend')

            # 4. 风险数据
            risk_keys = ['st_status', 'suspend', 'restricted', 'st_status_ak', 'st_info_ak', 'suspend_ak', 'restricted_ak']
            for key in risk_keys:
                load_and_format(f'risk_{key}', key)

            # 5. 资金流数据
            capital_keys = ['margin', 'margin_detail', 'hsgt_holding', 'ggt_top10', 'hk_hold',
                           'moneyflow_hsgt', 'holder_trade', 'pledge', 'pledge_detail',
                           'margin_ak', 'holder_trade_ak', 'pledge_detail_ak']
            for key in capital_keys:
                load_and_format(f'capital_{key}', key)

            # 6. 行情数据
            market_keys = ['limit_list', 'limit_list_ths', 'dragon_tiger', 'top_inst',
                          'dragon_tiger_ak', 'block_trade', 'realtime_list']
            for key in market_keys:
                load_and_format(f'market_{key}', key)

            # 7. AKShare扩展数据
            akshare_keys = ['audit_ak', 'forecast_ak', 'financial_risk']
            for key in akshare_keys:
                load_and_format(f'akshare_{key}', key)

            # 8. 新闻相关数据
            news_keys = ['news_sina', 'news_em', 'market_news', 'cninfo_news',
                        'industry_policy', 'announcements', 'announcements_ak']
            for key in news_keys:
                load_and_format(key)

        # 加载新闻（增量数据）- 加载最近50条
        news_records = StockNewsService.get_latest_news(db, ts_code, limit=50)
        result['news'] = [news.to_dict() for news in news_records]

        # 添加数据加载时间戳
        result['_loaded_at'] = datetime.utcnow().isoformat()
        result['_from_database'] = True
        result['ts_code'] = ts_code

        return result
    
    @staticmethod
    def clean_old_data(db: Session, ts_code: str, retention_days: int):
        """
        清理旧数据
        
        Args:
            db: 数据库会话
            ts_code: 股票代码
            retention_days: 保留天数
        """
        # 清理旧的数据记录
        data_count = StockDataService.clean_old_data(db, ts_code, retention_days)
        
        # 清理旧新闻
        news_count = StockNewsService.clean_old_news(db, ts_code, retention_days)
        
        print(f"[清理] {ts_code} 清理完成：数据{data_count}条，新闻{news_count}条")
        
        return {
            'data_cleaned': data_count,
            'news_cleaned': news_count
        }
    
    @staticmethod
    def batch_clean_all_stocks(db: Session):
        """批量清理所有监控股票的旧数据"""
        stocks = MonitoredStockService.get_all_active(db)
        
        total_cleaned = {'data': 0, 'news': 0}
        for stock in stocks:
            result = DataPersistenceManager.clean_old_data(
                db, stock.ts_code, stock.retention_days
            )
            total_cleaned['data'] += result['data_cleaned']
            total_cleaned['news'] += result['news_cleaned']
        
        print(f"[批量清理] 完成，共清理数据{total_cleaned['data']}条，新闻{total_cleaned['news']}条")
        return total_cleaned
