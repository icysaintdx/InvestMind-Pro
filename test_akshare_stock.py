#!/usr/bin/env python3
"""
测试AKShare股票数据
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.dataflows.akshare.stock_data import get_stock_data
from backend.utils.logging_config import get_logger

logger = get_logger("test_akshare_stock")


def test_realtime_quotes():
    """测试实时行情"""
    logger.info("=" * 60)
    logger.info("测试1: A股实时行情")
    logger.info("=" * 60)
    
    stock_data = get_stock_data()
    
    try:
        quotes = stock_data.get_realtime_quotes()
        
        if quotes:
            logger.info(f"✅ 获取到{len(quotes)}条实时行情")
            
            # 显示前5条
            logger.info("\n前5条数据:")
            for i, quote in enumerate(quotes[:5], 1):
                logger.info(f"\n{i}. {quote.get('名称', 'N/A')} ({quote.get('代码', 'N/A')})")
                logger.info(f"   最新价: {quote.get('最新价', 0)}")
                logger.info(f"   涨跌幅: {quote.get('涨跌幅', 0)}%")
                logger.info(f"   成交量: {quote.get('成交量', 0)}")
                logger.info(f"   成交额: {quote.get('成交额', 0)}")
        else:
            logger.warning("⚠️ 未获取到实时行情")
            
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


def test_stock_quote():
    """测试个股行情"""
    logger.info("\n" + "=" * 60)
    logger.info("测试2: 个股实时行情")
    logger.info("=" * 60)
    
    stock_data = get_stock_data()
    
    test_stocks = [
        "600519",  # 贵州茅台
        "000001",  # 平安银行
        "300750",  # 宁德时代
    ]
    
    for symbol in test_stocks:
        logger.info(f"\n{'='*50}")
        logger.info(f"测试股票: {symbol}")
        logger.info(f"{'='*50}")
        
        try:
            quote = stock_data.get_stock_quote(symbol)
            
            if quote:
                logger.info(f"✅ 获取成功")
                logger.info(f"  名称: {quote.get('名称', 'N/A')}")
                logger.info(f"  最新价: {quote.get('最新价', 0)}")
                logger.info(f"  涨跌幅: {quote.get('涨跌幅', 0)}%")
                logger.info(f"  涨跌额: {quote.get('涨跌额', 0)}")
                logger.info(f"  成交量: {quote.get('成交量', 0)}")
                logger.info(f"  成交额: {quote.get('成交额', 0)}")
                logger.info(f"  换手率: {quote.get('换手率', 0)}%")
                logger.info(f"  市盈率: {quote.get('市盈率-动态', 0)}")
                logger.info(f"  市净率: {quote.get('市净率', 0)}")
            else:
                logger.warning(f"⚠️ 未获取到{symbol}的行情")
                
        except Exception as e:
            logger.error(f"❌ 测试失败: {e}")


def test_stock_hist():
    """测试历史行情"""
    logger.info("\n" + "=" * 60)
    logger.info("测试3: 历史行情")
    logger.info("=" * 60)
    
    stock_data = get_stock_data()
    
    try:
        # 获取最近30天数据
        from datetime import datetime, timedelta
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
        
        hist_data = stock_data.get_stock_hist(
            symbol="600519",
            period="daily",
            start_date=start_date,
            end_date=end_date
        )
        
        if hist_data:
            logger.info(f"✅ 获取到{len(hist_data)}条历史数据")
            
            # 显示最近3天
            logger.info("\n最近3天数据:")
            for i, data in enumerate(hist_data[-3:], 1):
                logger.info(f"\n{i}. {data.get('日期', 'N/A')}")
                logger.info(f"   开盘: {data.get('开盘', 0)}")
                logger.info(f"   收盘: {data.get('收盘', 0)}")
                logger.info(f"   最高: {data.get('最高', 0)}")
                logger.info(f"   最低: {data.get('最低', 0)}")
                logger.info(f"   成交量: {data.get('成交量', 0)}")
        else:
            logger.warning("⚠️ 未获取到历史数据")
            
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


def test_stock_info():
    """测试股票信息"""
    logger.info("\n" + "=" * 60)
    logger.info("测试4: 股票基本信息")
    logger.info("=" * 60)
    
    stock_data = get_stock_data()
    
    try:
        info = stock_data.get_stock_info("600519")
        
        if info:
            logger.info(f"✅ 获取成功")
            logger.info(f"\n股票信息:")
            for key, value in info.items():
                logger.info(f"  {key}: {value}")
        else:
            logger.warning("⚠️ 未获取到股票信息")
            
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")


def test_search_stock():
    """测试股票搜索"""
    logger.info("\n" + "=" * 60)
    logger.info("测试5: 股票搜索")
    logger.info("=" * 60)
    
    stock_data = get_stock_data()
    
    keywords = ["茅台", "平安", "600519"]
    
    for keyword in keywords:
        logger.info(f"\n{'='*50}")
        logger.info(f"搜索关键词: {keyword}")
        logger.info(f"{'='*50}")
        
        try:
            results = stock_data.search_stock(keyword)
            
            if results:
                logger.info(f"✅ 找到{len(results)}个结果")
                
                # 显示前3个
                for i, stock in enumerate(results[:3], 1):
                    logger.info(f"\n{i}. {stock.get('名称', 'N/A')} ({stock.get('代码', 'N/A')})")
                    logger.info(f"   最新价: {stock.get('最新价', 0)}")
                    logger.info(f"   涨跌幅: {stock.get('涨跌幅', 0)}%")
            else:
                logger.warning(f"⚠️ 未找到匹配结果")
                
        except Exception as e:
            logger.error(f"❌ 测试失败: {e}")


def main():
    """主函数"""
    logger.info("🚀 开始测试AKShare股票数据")
    logger.info("=" * 60)
    
    try:
        # 运行所有测试
        test_realtime_quotes()
        test_stock_quote()
        test_stock_hist()
        test_stock_info()
        test_search_stock()
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ 所有测试完成")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ 测试过程出错: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
