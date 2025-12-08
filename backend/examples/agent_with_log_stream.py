"""
智能体日志流使用示例
展示如何在智能体中集成实时日志流功能
"""
import logging
from backend.utils.log_stream_handler import attach_log_stream, detach_log_stream
from backend.api.agent_logs_api import end_agent_log_stream

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def analyze_news_with_log_stream(stock_code: str, agent_id: str = "news_analyst"):
    """
    新闻分析示例 - 带日志流
    
    Args:
        stock_code: 股票代码
        agent_id: 智能体ID（用于日志流）
    """
    # 1. 附加日志流处理器
    handler = attach_log_stream(__name__, agent_id)
    
    try:
        logger.info(f"收到股票新闻请求: {stock_code}")
        logger.info(f"开始获取{stock_code}的综合新闻数据...")
        
        # 2. 数据获取阶段 - 每个步骤都会推送日志
        logger.info("[数据源1] 实时新闻聚合器...")
        # 模拟数据获取
        import time
        time.sleep(0.5)
        logger.info("✅ 实时新闻聚合器成功: 10条")
        
        logger.info("[数据源2] AKShare个股新闻...")
        time.sleep(0.5)
        logger.info("✅ AKShare个股新闻成功: 10条")
        
        logger.info("[数据源3] 财联社快讯...")
        time.sleep(0.5)
        logger.info("✅ 财联社快讯成功: 10条")
        
        logger.info("[数据源4] 微博热议...")
        time.sleep(0.5)
        logger.info("✅ 微博热议成功: 50条")
        
        logger.info("[数据源5] 财经早餐...")
        time.sleep(0.5)
        logger.info("✅ 财经早餐成功: 400条")
        
        logger.info("[情绪分析] 开始分析...")
        time.sleep(0.3)
        logger.info("✅ 情绪分析完成: 偏积极")
        
        logger.info("✅ 综合新闻数据获取完成: 5/5 个数据源成功")
        
        # 3. 结束日志流
        end_agent_log_stream(agent_id)
        
        return {
            "success": True,
            "data_sources": 5,
            "total_news": 480
        }
        
    except Exception as e:
        logger.error(f"❌ 新闻分析失败: {str(e)}")
        end_agent_log_stream(agent_id)
        raise
    finally:
        # 4. 移除日志流处理器
        detach_log_stream(__name__, handler)


def analyze_fund_flow_with_log_stream(stock_code: str, agent_id: str = "funds"):
    """
    资金流向分析示例 - 带日志流
    
    Args:
        stock_code: 股票代码
        agent_id: 智能体ID
    """
    handler = attach_log_stream(__name__, agent_id)
    
    try:
        logger.info("获取北向资金实时资金流向...")
        import time
        time.sleep(1.0)
        logger.info("✅ 获取到241条北向资金实时数据")
        
        logger.info("获取北向资金历史资金流向...")
        time.sleep(2.0)
        logger.info("✅ 获取到2570条北向资金历史数据")
        
        logger.info("获取北向持股排名(今日排行)...")
        time.sleep(1.5)
        logger.info("✅ 获取到2767条持股排名")
        
        logger.info("获取行业资金流向(即时)...")
        time.sleep(0.5)
        logger.info("✅ 获取到90条行业资金流向")
        
        logger.info("获取概念资金流向(即时)...")
        time.sleep(2.0)
        logger.info("✅ 获取到386条概念资金流向")
        
        logger.info("获取个股资金流向(即时)...")
        time.sleep(3.0)
        logger.info("✅ 获取到5153条个股资金流向")
        
        logger.info("获取融资融券汇总...")
        time.sleep(0.5)
        logger.info("✅ 获取到20条融资融券汇总")
        
        logger.info(f"获取{stock_code}的资金流向详情...")
        time.sleep(1.0)
        logger.info(f"✅ 找到{stock_code}的资金流向")
        
        end_agent_log_stream(agent_id)
        
        return {
            "success": True,
            "total_records": 11227
        }
        
    except Exception as e:
        logger.error(f"❌ 资金流向分析失败: {str(e)}")
        end_agent_log_stream(agent_id)
        raise
    finally:
        detach_log_stream(__name__, handler)


# 使用示例
if __name__ == "__main__":
    print("=" * 60)
    print("智能体日志流使用示例")
    print("=" * 60)
    
    # 示例1: 新闻分析
    print("\n[示例1] 新闻分析")
    result1 = analyze_news_with_log_stream("603211", "news_analyst")
    print(f"结果: {result1}")
    
    # 示例2: 资金流向分析
    print("\n[示例2] 资金流向分析")
    result2 = analyze_fund_flow_with_log_stream("603211", "funds")
    print(f"结果: {result2}")
    
    print("\n" + "=" * 60)
    print("示例完成！")
    print("=" * 60)
